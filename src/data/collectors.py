"""
Data collection system for gathering real-time and historical market data.
"""
import asyncio
import time
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import json
import websockets
import ccxt.async_support as ccxt

from config.settings import settings


class ExchangeClient:
    """Individual exchange client for data collection."""
    
    def __init__(self, exchange_name: str):
        """Initialize exchange client."""
        self.name = exchange_name
        self.exchange = None
        self.websocket = None
        self.connected = False
        self.last_prices = {}
        self.order_books = {}
        
        self._initialize_exchange()
    
    def _initialize_exchange(self):
        """Initialize the exchange instance with API credentials."""
        try:
            if self.name == 'binance':
                self.exchange = ccxt.binance({
                    'apiKey': settings.exchanges.binance_api_key,
                    'secret': settings.exchanges.binance_secret_key,
                    'sandbox': settings.exchanges.binance_sandbox,
                    'enableRateLimit': True,
                })
            elif self.name == 'coinbase':
                self.exchange = ccxt.coinbasepro({
                    'apiKey': settings.exchanges.coinbase_api_key,
                    'secret': settings.exchanges.coinbase_secret_key,
                    'passphrase': settings.exchanges.coinbase_passphrase,
                    'sandbox': settings.exchanges.coinbase_sandbox,
                    'enableRateLimit': True,
                })
            elif self.name == 'kraken':
                self.exchange = ccxt.kraken({
                    'apiKey': settings.exchanges.kraken_api_key,
                    'secret': settings.exchanges.kraken_secret_key,
                    'enableRateLimit': True,
                })
            elif self.name == 'bitfinex':
                self.exchange = ccxt.bitfinex({
                    'apiKey': settings.exchanges.bitfinex_api_key,
                    'secret': settings.exchanges.bitfinex_secret_key,
                    'enableRateLimit': True,
                })
            else:
                raise ValueError(f"Unsupported exchange: {self.name}")
            
        except Exception as e:
            print(f"Error initializing {self.name} exchange: {e}")
            self.exchange = None
    
    async def connect(self):
        """Connect to the exchange."""
        if not self.exchange:
            return False
        
        try:
            await self.exchange.load_markets()
            self.connected = True
            return True
        except Exception as e:
            print(f"Error connecting to {self.name}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the exchange."""
        if self.exchange:
            await self.exchange.close()
        self.connected = False
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """Fetch current ticker data for a symbol."""
        if not self.connected or not self.exchange:
            return None
        
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            self.last_prices[symbol] = {
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'last': ticker['last'],
                'timestamp': ticker['timestamp'],
                'volume': ticker['baseVolume']
            }
            return self.last_prices[symbol]
        except Exception as e:
            print(f"Error fetching ticker for {symbol} on {self.name}: {e}")
            return None
    
    async def fetch_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Fetch order book for a symbol."""
        if not self.connected or not self.exchange:
            return None
        
        try:
            order_book = await self.exchange.fetch_order_book(symbol, limit)
            self.order_books[symbol] = {
                'bids': order_book['bids'][:limit],
                'asks': order_book['asks'][:limit],
                'timestamp': order_book['timestamp']
            }
            return self.order_books[symbol]
        except Exception as e:
            print(f"Error fetching order book for {symbol} on {self.name}: {e}")
            return None
    
    async def fetch_trades(self, symbol: str, limit: int = 100) -> Optional[List]:
        """Fetch recent trades for a symbol."""
        if not self.connected or not self.exchange:
            return None
        
        try:
            trades = await self.exchange.fetch_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            print(f"Error fetching trades for {symbol} on {self.name}: {e}")
            return None
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', 
                         limit: int = 100) -> Optional[List]:
        """Fetch OHLCV data for technical analysis."""
        if not self.connected or not self.exchange:
            return None
        
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol} on {self.name}: {e}")
            return None


class DataCollector:
    """
    Main data collection orchestrator that manages multiple exchange clients.
    """
    
    def __init__(self, exchanges: List[str], symbols: List[str]):
        """Initialize data collector."""
        self.exchanges = exchanges
        self.symbols = symbols
        self.clients = {}
        self.running = False
        
        # Data storage
        self.latest_data = {}
        self.historical_data = {}
        
        # Performance tracking
        self.data_updates = 0
        self.last_update = time.time()
        
        # Initialize exchange clients
        for exchange in exchanges:
            self.clients[exchange] = ExchangeClient(exchange)
    
    async def start(self):
        """Start data collection from all exchanges."""
        if self.running:
            return
        
        print("Starting data collection...")
        self.running = True
        
        # Connect to all exchanges
        connected_exchanges = []
        for name, client in self.clients.items():
            if await client.connect():
                connected_exchanges.append(name)
                print(f"Connected to {name}")
            else:
                print(f"Failed to connect to {name}")
        
        if not connected_exchanges:
            print("No exchanges connected, stopping data collection")
            self.running = False
            return
        
        # Start data collection tasks
        tasks = [
            asyncio.create_task(self._collect_ticker_data()),
            asyncio.create_task(self._collect_order_book_data()),
            asyncio.create_task(self._collect_historical_data()),
            asyncio.create_task(self._performance_monitor())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"Error in data collection: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop data collection."""
        if not self.running:
            return
        
        print("Stopping data collection...")
        self.running = False
        
        # Disconnect from all exchanges
        for client in self.clients.values():
            await client.disconnect()
        
        print("Data collection stopped")
    
    async def _collect_ticker_data(self):
        """Continuously collect ticker data."""
        while self.running:
            try:
                for exchange_name, client in self.clients.items():
                    if not client.connected:
                        continue
                    
                    for symbol in self.symbols:
                        ticker = await client.fetch_ticker(symbol)
                        if ticker:
                            key = f"{exchange_name}_{symbol}"
                            self.latest_data[key] = {
                                'exchange': exchange_name,
                                'symbol': symbol,
                                'type': 'ticker',
                                'data': ticker,
                                'timestamp': time.time()
                            }
                            self.data_updates += 1
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                print(f"Error collecting ticker data: {e}")
                await asyncio.sleep(5)
    
    async def _collect_order_book_data(self):
        """Continuously collect order book data."""
        while self.running:
            try:
                for exchange_name, client in self.clients.items():
                    if not client.connected:
                        continue
                    
                    for symbol in self.symbols:
                        order_book = await client.fetch_order_book(symbol)
                        if order_book:
                            key = f"{exchange_name}_{symbol}_orderbook"
                            self.latest_data[key] = {
                                'exchange': exchange_name,
                                'symbol': symbol,
                                'type': 'orderbook',
                                'data': order_book,
                                'timestamp': time.time()
                            }
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                print(f"Error collecting order book data: {e}")
                await asyncio.sleep(5)
    
    async def _collect_historical_data(self):
        """Collect historical OHLCV data for analysis."""
        while self.running:
            try:
                for exchange_name, client in self.clients.items():
                    if not client.connected:
                        continue
                    
                    for symbol in self.symbols:
                        ohlcv = await client.fetch_ohlcv(symbol, '1m', 100)
                        if ohlcv:
                            key = f"{exchange_name}_{symbol}_ohlcv"
                            self.historical_data[key] = {
                                'exchange': exchange_name,
                                'symbol': symbol,
                                'type': 'ohlcv',
                                'data': ohlcv,
                                'timestamp': time.time()
                            }
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                print(f"Error collecting historical data: {e}")
                await asyncio.sleep(30)
    
    async def _performance_monitor(self):
        """Monitor data collection performance."""
        while self.running:
            try:
                current_time = time.time()
                time_diff = current_time - self.last_update
                
                if time_diff >= 60:  # Log every minute
                    updates_per_second = self.data_updates / time_diff
                    print(f"Data collection rate: {updates_per_second:.2f} updates/second")
                    
                    self.data_updates = 0
                    self.last_update = current_time
                
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"Error in performance monitor: {e}")
    
    async def get_latest_data(self) -> Dict:
        """Get the latest market data."""
        return self.latest_data.copy()
    
    async def get_historical_data(self) -> Dict:
        """Get historical market data."""
        return self.historical_data.copy()
    
    async def get_ticker(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Get latest ticker for specific exchange and symbol."""
        key = f"{exchange}_{symbol}"
        return self.latest_data.get(key)
    
    async def get_order_book(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Get latest order book for specific exchange and symbol."""
        key = f"{exchange}_{symbol}_orderbook"
        return self.latest_data.get(key)
    
    async def get_spread(self, exchange: str, symbol: str) -> Optional[float]:
        """Calculate spread for a symbol on an exchange."""
        ticker = await self.get_ticker(exchange, symbol)
        if ticker and ticker['data']['bid'] and ticker['data']['ask']:
            bid = ticker['data']['bid']
            ask = ticker['data']['ask']
            return (ask - bid) / ask if ask > 0 else None
        return None
    
    async def get_cross_exchange_spreads(self, symbol: str) -> Dict:
        """Get spreads across all exchanges for a symbol."""
        spreads = {}
        
        for exchange in self.exchanges:
            client = self.clients.get(exchange)
            if client and client.connected:
                spread = await self.get_spread(exchange, symbol)
                if spread is not None:
                    spreads[exchange] = spread
        
        return spreads
    
    async def get_arbitrage_opportunities(self, symbol: str) -> List[Dict]:
        """Find potential arbitrage opportunities for a symbol."""
        opportunities = []
        
        # Get tickers from all exchanges
        tickers = {}
        for exchange in self.exchanges:
            ticker = await self.get_ticker(exchange, symbol)
            if ticker:
                tickers[exchange] = ticker['data']
        
        # Find arbitrage opportunities
        for exchange1 in tickers:
            for exchange2 in tickers:
                if exchange1 == exchange2:
                    continue
                
                ticker1 = tickers[exchange1]
                ticker2 = tickers[exchange2]
                
                if not all(key in ticker1 and key in ticker2 
                          for key in ['bid', 'ask']):
                    continue
                
                # Check if we can buy on exchange1 and sell on exchange2
                buy_price = ticker1['ask']
                sell_price = ticker2['bid']
                
                if sell_price > buy_price:
                    profit_abs = sell_price - buy_price
                    profit_pct = (profit_abs / buy_price) * 100
                    
                    if profit_pct >= settings.trading.min_profit_threshold * 100:
                        opportunities.append({
                            'symbol': symbol,
                            'buy_exchange': exchange1,
                            'sell_exchange': exchange2,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'profit_abs': profit_abs,
                            'profit_pct': profit_pct,
                            'timestamp': time.time()
                        })
        
        return opportunities
    
    async def get_status(self) -> Dict:
        """Get data collector status."""
        connected_exchanges = [
            name for name, client in self.clients.items() 
            if client.connected
        ]
        
        return {
            'running': self.running,
            'connected_exchanges': connected_exchanges,
            'total_exchanges': len(self.clients),
            'symbols': self.symbols,
            'data_points': len(self.latest_data),
            'updates_count': self.data_updates,
            'last_update': self.last_update
        }
