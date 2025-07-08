"""
Quantitative analysis module for detecting arbitrage opportunities using statistical models.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from config.settings import settings


@dataclass
class ArbitrageOpportunity:
    """Represents a detected arbitrage opportunity."""
    id: str
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    profit_abs: float
    profit_pct: float
    confidence_score: float
    volume_available: float
    estimated_fees: float
    net_profit: float
    timestamp: datetime
    strategy: str = "statistical_arbitrage"


class QuantAnalyzer:
    """
    Quantitative analyzer for detecting arbitrage opportunities using 
    advanced statistical and mathematical models.
    """
    
    def __init__(self):
        """Initialize the quantitative analyzer."""
        self.price_history = {}
        self.spread_history = {}
        self.volume_history = {}
        
        # Statistical parameters
        self.lookback_window = 100
        self.min_observations = 20
        self.z_score_threshold = 2.0
        
        # Cointegration parameters
        self.cointegration_window = 200
        self.half_life_threshold = 50
        
        # Mean reversion parameters
        self.bollinger_period = 20
        self.bollinger_std = 2
        
        # Initialize technical indicators
        self.indicators = {}
    
    async def find_arbitrage(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """
        Main method to find arbitrage opportunities using multiple strategies.
        """
        opportunities = []
        
        # Update internal data structures
        await self._update_data(market_data)
        
        # Run different arbitrage detection strategies
        strategies = [
            self._simple_arbitrage,
            self._statistical_arbitrage,
            self._mean_reversion_arbitrage,
            self._cointegration_arbitrage,
            self._volume_weighted_arbitrage
        ]
        
        for strategy in strategies:
            try:
                strategy_opportunities = await strategy(market_data)
                opportunities.extend(strategy_opportunities)
            except Exception as e:
                print(f"Error in strategy {strategy.__name__}: {e}")
        
        # Remove duplicates and rank opportunities
        opportunities = await self._rank_opportunities(opportunities)
        
        return opportunities
    
    async def _update_data(self, market_data: Dict):
        """Update internal data structures with new market data."""
        current_time = datetime.utcnow()
        
        for key, data in market_data.items():
            if data['type'] == 'ticker':
                exchange = data['exchange']
                symbol = data['symbol']
                ticker = data['data']
                
                # Update price history
                if symbol not in self.price_history:
                    self.price_history[symbol] = {}
                
                if exchange not in self.price_history[symbol]:
                    self.price_history[symbol][exchange] = []
                
                self.price_history[symbol][exchange].append({
                    'timestamp': current_time,
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'last': ticker['last'],
                    'volume': ticker.get('volume', 0)
                })
                
                # Keep only recent data
                cutoff = current_time - timedelta(hours=24)
                self.price_history[symbol][exchange] = [
                    p for p in self.price_history[symbol][exchange] 
                    if p['timestamp'] > cutoff
                ]
    
    async def _simple_arbitrage(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """Detect simple price arbitrage opportunities."""
        opportunities = []
        
        # Group data by symbol
        symbol_data = {}
        for key, data in market_data.items():
            if data['type'] == 'ticker':
                symbol = data['symbol']
                if symbol not in symbol_data:
                    symbol_data[symbol] = {}
                symbol_data[symbol][data['exchange']] = data['data']
        
        # Find arbitrage for each symbol
        for symbol, exchanges in symbol_data.items():
            if len(exchanges) < 2:
                continue
            
            exchange_list = list(exchanges.keys())
            
            for i in range(len(exchange_list)):
                for j in range(i + 1, len(exchange_list)):
                    exchange1 = exchange_list[i]
                    exchange2 = exchange_list[j]
                    
                    ticker1 = exchanges[exchange1]
                    ticker2 = exchanges[exchange2]
                    
                    # Check both directions
                    for buy_ex, sell_ex, buy_ticker, sell_ticker in [
                        (exchange1, exchange2, ticker1, ticker2),
                        (exchange2, exchange1, ticker2, ticker1)
                    ]:
                        if not all(key in buy_ticker and key in sell_ticker 
                                 for key in ['bid', 'ask']):
                            continue
                        
                        buy_price = buy_ticker['ask']
                        sell_price = sell_ticker['bid']
                        
                        if sell_price > buy_price:
                            profit_abs = sell_price - buy_price
                            profit_pct = (profit_abs / buy_price) * 100
                            
                            # Estimate fees (simplified)
                            estimated_fees = (buy_price + sell_price) * 0.001  # 0.1% each side
                            net_profit = profit_abs - estimated_fees
                            
                            if net_profit > 0 and profit_pct >= settings.trading.min_profit_threshold * 100:
                                opportunity = ArbitrageOpportunity(
                                    id=f"simple_{symbol}_{buy_ex}_{sell_ex}_{int(datetime.utcnow().timestamp())}",
                                    symbol=symbol,
                                    buy_exchange=buy_ex,
                                    sell_exchange=sell_ex,
                                    buy_price=buy_price,
                                    sell_price=sell_price,
                                    profit_abs=profit_abs,
                                    profit_pct=profit_pct,
                                    confidence_score=0.8,  # Base confidence for simple arbitrage
                                    volume_available=min(buy_ticker.get('volume', 0), 
                                                       sell_ticker.get('volume', 0)),
                                    estimated_fees=estimated_fees,
                                    net_profit=net_profit,
                                    timestamp=datetime.utcnow(),
                                    strategy="simple_arbitrage"
                                )
                                opportunities.append(opportunity)
        
        return opportunities
    
    async def _statistical_arbitrage(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """Detect arbitrage using statistical analysis of price spreads."""
        opportunities = []
        
        for symbol in settings.trading.trading_pairs:
            if symbol not in self.price_history:
                continue
            
            exchanges = list(self.price_history[symbol].keys())
            if len(exchanges) < 2:
                continue
            
            # Calculate spreads between all exchange pairs
            for i in range(len(exchanges)):
                for j in range(i + 1, len(exchanges)):
                    exchange1, exchange2 = exchanges[i], exchanges[j]
                    
                    # Get recent price data
                    data1 = self.price_history[symbol][exchange1][-self.lookback_window:]
                    data2 = self.price_history[symbol][exchange2][-self.lookback_window:]
                    
                    if len(data1) < self.min_observations or len(data2) < self.min_observations:
                        continue
                    
                    # Align timestamps and calculate spreads
                    spreads = await self._calculate_aligned_spreads(data1, data2)
                    
                    if len(spreads) < self.min_observations:
                        continue
                    
                    # Statistical analysis
                    spread_mean = np.mean(spreads)
                    spread_std = np.std(spreads)
                    current_spread = spreads[-1] if spreads else 0
                    
                    # Z-score analysis
                    z_score = (current_spread - spread_mean) / spread_std if spread_std > 0 else 0
                    
                    # Check for mean reversion opportunity
                    if abs(z_score) > self.z_score_threshold:
                        # Determine direction
                        if z_score > 0:
                            # Spread is high, expect reversion
                            buy_exchange = exchange2
                            sell_exchange = exchange1
                        else:
                            # Spread is low, expect expansion
                            buy_exchange = exchange1
                            sell_exchange = exchange2
                        
                        # Get current prices
                        current_data1 = data1[-1] if data1 else None
                        current_data2 = data2[-1] if data2 else None
                        
                        if current_data1 and current_data2:
                            buy_price = current_data1['ask'] if buy_exchange == exchange1 else current_data2['ask']
                            sell_price = current_data1['bid'] if sell_exchange == exchange1 else current_data2['bid']
                            
                            profit_abs = sell_price - buy_price
                            profit_pct = (profit_abs / buy_price) * 100 if buy_price > 0 else 0
                            
                            if profit_abs > 0:
                                estimated_fees = (buy_price + sell_price) * 0.001
                                net_profit = profit_abs - estimated_fees
                                
                                confidence_score = min(abs(z_score) / 5.0, 1.0)  # Normalize confidence
                                
                                opportunity = ArbitrageOpportunity(
                                    id=f"stat_{symbol}_{buy_exchange}_{sell_exchange}_{int(datetime.utcnow().timestamp())}",
                                    symbol=symbol,
                                    buy_exchange=buy_exchange,
                                    sell_exchange=sell_exchange,
                                    buy_price=buy_price,
                                    sell_price=sell_price,
                                    profit_abs=profit_abs,
                                    profit_pct=profit_pct,
                                    confidence_score=confidence_score,
                                    volume_available=1000,  # Placeholder
                                    estimated_fees=estimated_fees,
                                    net_profit=net_profit,
                                    timestamp=datetime.utcnow(),
                                    strategy="statistical_arbitrage"
                                )
                                opportunities.append(opportunity)
        
        return opportunities
    
    async def _mean_reversion_arbitrage(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """Detect arbitrage using Bollinger Bands and mean reversion."""
        opportunities = []
        
        for symbol in settings.trading.trading_pairs:
            if symbol not in self.price_history:
                continue
            
            exchanges = list(self.price_history[symbol].keys())
            
            for exchange in exchanges:
                data = self.price_history[symbol][exchange]
                
                if len(data) < self.bollinger_period:
                    continue
                
                # Calculate Bollinger Bands
                prices = [d['last'] for d in data[-self.bollinger_period:]]
                mean_price = np.mean(prices)
                std_price = np.std(prices)
                
                upper_band = mean_price + (self.bollinger_std * std_price)
                lower_band = mean_price - (self.bollinger_std * std_price)
                
                current_price = prices[-1]
                
                # Check for mean reversion signals
                if current_price > upper_band:
                    # Price is above upper band, expect reversion down
                    # Look for arbitrage selling opportunity
                    pass
                elif current_price < lower_band:
                    # Price is below lower band, expect reversion up
                    # Look for arbitrage buying opportunity
                    pass
        
        return opportunities
    
    async def _cointegration_arbitrage(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """Detect arbitrage using cointegration analysis."""
        opportunities = []
        
        # This would implement pairs trading based on cointegration
        # For now, return empty list as this requires more sophisticated implementation
        
        return opportunities
    
    async def _volume_weighted_arbitrage(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """Detect arbitrage considering volume and liquidity."""
        opportunities = []
        
        # This would implement volume-weighted arbitrage detection
        # For now, return empty list
        
        return opportunities
    
    async def _calculate_aligned_spreads(self, data1: List[Dict], data2: List[Dict]) -> List[float]:
        """Calculate time-aligned spreads between two price series."""
        spreads = []
        
        # Simple implementation - assumes data is already aligned
        min_len = min(len(data1), len(data2))
        
        for i in range(min_len):
            price1 = data1[i]['last']
            price2 = data2[i]['last']
            
            if price1 > 0 and price2 > 0:
                spread = (price1 - price2) / price2
                spreads.append(spread)
        
        return spreads
    
    async def _rank_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """Rank and filter opportunities by various criteria."""
        if not opportunities:
            return []
        
        # Remove duplicates
        unique_opportunities = {}
        for opp in opportunities:
            key = f"{opp.symbol}_{opp.buy_exchange}_{opp.sell_exchange}"
            if key not in unique_opportunities or opp.net_profit > unique_opportunities[key].net_profit:
                unique_opportunities[key] = opp
        
        # Sort by net profit and confidence
        sorted_opportunities = sorted(
            unique_opportunities.values(),
            key=lambda x: x.net_profit * x.confidence_score,
            reverse=True
        )
        
        # Filter by minimum thresholds
        filtered_opportunities = [
            opp for opp in sorted_opportunities
            if opp.net_profit > 0 and opp.confidence_score > 0.5
        ]
        
        return filtered_opportunities[:10]  # Return top 10
    
    async def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio for a series of returns."""
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        return (mean_return - risk_free_rate) / std_return
    
    async def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown from equity curve."""
        if not equity_curve:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd
    
    async def calculate_var(self, returns: List[float], confidence: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)."""
        if not returns:
            return 0.0
        
        return np.percentile(returns, (1 - confidence) * 100)
    
    async def get_technical_indicators(self, symbol: str, exchange: str) -> Dict:
        """Calculate technical indicators for a symbol on an exchange."""
        if symbol not in self.price_history or exchange not in self.price_history[symbol]:
            return {}
        
        data = self.price_history[symbol][exchange]
        if len(data) < 20:
            return {}
        
        prices = [d['last'] for d in data]
        volumes = [d['volume'] for d in data]
        
        indicators = {}
        
        # Simple Moving Average
        if len(prices) >= 20:
            indicators['sma_20'] = np.mean(prices[-20:])
        
        # Exponential Moving Average
        if len(prices) >= 12:
            indicators['ema_12'] = self._calculate_ema(prices, 12)
        
        # RSI
        if len(prices) >= 14:
            indicators['rsi'] = self._calculate_rsi(prices, 14)
        
        # Bollinger Bands
        if len(prices) >= 20:
            bb = self._calculate_bollinger_bands(prices, 20, 2)
            indicators.update(bb)
        
        return indicators
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Dict:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return {}
        
        recent_prices = prices[-period:]
        mean_price = np.mean(recent_prices)
        std_price = np.std(recent_prices)
        
        return {
            'bb_upper': mean_price + (std_dev * std_price),
            'bb_middle': mean_price,
            'bb_lower': mean_price - (std_dev * std_price)
        }
