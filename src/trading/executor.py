"""
Trade execution engine for automated arbitrage trading.
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from config.settings import settings


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


@dataclass
class Order:
    """Represents a trading order."""
    id: str
    symbol: str
    exchange: str
    side: str  # 'buy' or 'sell'
    order_type: OrderType
    amount: float
    price: Optional[float]
    status: OrderStatus
    timestamp: datetime
    filled_amount: float = 0.0
    fees: float = 0.0
    average_price: float = 0.0
    exchange_order_id: Optional[str] = None


@dataclass
class TradeResult:
    """Result of trade execution."""
    success: bool
    opportunity_id: str
    buy_order: Optional[Order]
    sell_order: Optional[Order]
    profit: float
    fees: float
    execution_time: float
    reason: str = ""
    slippage: float = 0.0


class PaperTradingExecutor:
    """Paper trading executor for simulation."""
    
    def __init__(self, portfolio=None):
        """Initialize paper trading executor."""
        self.portfolio = portfolio
        self.orders = {}
        self.simulated_latency = 0.1  # 100ms simulated latency
        self.simulated_slippage = 0.0005  # 0.05% simulated slippage
        
    async def place_order(self, symbol: str, exchange: str, side: str, 
                         amount: float, order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None) -> Order:
        """Place a simulated order."""
        order = Order(
            id=str(uuid.uuid4()),
            symbol=symbol,
            exchange=exchange,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            status=OrderStatus.PENDING,
            timestamp=datetime.utcnow()
        )
        
        self.orders[order.id] = order
        
        # Simulate order processing delay
        await asyncio.sleep(self.simulated_latency)
        
        # Simulate order execution
        await self._simulate_order_execution(order)
        
        return order
    
    async def _simulate_order_execution(self, order: Order):
        """Simulate order execution with realistic conditions."""
        try:
            # Simulate market order execution
            if order.order_type == OrderType.MARKET:
                # Simulate slippage
                if order.side == 'buy':
                    execution_price = (order.price or 0) * (1 + self.simulated_slippage)
                else:
                    execution_price = (order.price or 0) * (1 - self.simulated_slippage)
                
                # Mark as filled
                order.status = OrderStatus.FILLED
                order.filled_amount = order.amount
                order.average_price = execution_price
                order.fees = order.amount * execution_price * 0.001  # 0.1% fee
                
                # Update portfolio if available
                if self.portfolio:
                    await self._update_portfolio_from_order(order)
            
            # Limit orders would require market data to determine if they're filled
            elif order.order_type == OrderType.LIMIT:
                # For now, assume limit orders are filled immediately (simplified)
                order.status = OrderStatus.FILLED
                order.filled_amount = order.amount
                order.average_price = order.price or 0
                order.fees = order.amount * order.average_price * 0.001
                
                if self.portfolio:
                    await self._update_portfolio_from_order(order)
        
        except Exception as e:
            print(f"Error simulating order execution: {e}")
            order.status = OrderStatus.FAILED
    
    async def _update_portfolio_from_order(self, order: Order):
        """Update portfolio based on executed order."""
        if order.status != OrderStatus.FILLED:
            return
        
        if order.side == 'buy':
            # Buying: decrease USD balance, increase position
            cost = order.filled_amount * order.average_price + order.fees
            current_balance = await self.portfolio.get_balance('USD')
            
            if current_balance >= cost:
                self.portfolio.balances['USD'] -= cost
                
                # Add position (simplified - in real implementation would handle position averaging)
                from src.core.portfolio import Position
                position = Position(
                    symbol=order.symbol,
                    exchange=order.exchange,
                    side='buy',
                    amount=order.filled_amount,
                    entry_price=order.average_price,
                    fees_paid=order.fees
                )
                await self.portfolio.add_position(position)
        
        else:  # sell
            # Selling: increase USD balance, close position
            proceeds = order.filled_amount * order.average_price - order.fees
            self.portfolio.balances['USD'] += proceeds
            
            # Close position (simplified)
            await self.portfolio.close_position(
                order.symbol, 
                order.exchange, 
                'buy',  # Closing buy position with sell order
                order.average_price
            )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                return True
        return False
    
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status."""
        return self.orders.get(order_id)


class LiveTradingExecutor:
    """Live trading executor for real exchanges."""
    
    def __init__(self, portfolio=None):
        """Initialize live trading executor."""
        self.portfolio = portfolio
        self.exchange_clients = {}
        self.orders = {}
        
        # This would initialize real exchange clients
        # For now, just placeholder
        print("Live trading executor initialized (placeholder)")
    
    async def place_order(self, symbol: str, exchange: str, side: str, 
                         amount: float, order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None) -> Order:
        """Place a real order on exchange."""
        # This would place real orders using exchange APIs
        # For now, return a placeholder order
        order = Order(
            id=str(uuid.uuid4()),
            symbol=symbol,
            exchange=exchange,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            status=OrderStatus.PENDING,
            timestamp=datetime.utcnow()
        )
        
        print(f"Live order placed (placeholder): {order}")
        return order


class TradeExecutor:
    """
    Main trade execution orchestrator that handles arbitrage trade execution.
    """
    
    def __init__(self, portfolio=None, paper_trading: bool = True):
        """Initialize trade executor."""
        self.portfolio = portfolio
        self.paper_trading = paper_trading
        
        # Initialize appropriate executor
        if paper_trading:
            self.executor = PaperTradingExecutor(portfolio)
        else:
            self.executor = LiveTradingExecutor(portfolio)
        
        # Execution tracking
        self.executed_trades = []
        self.active_arbitrages = {}
        
        # Performance metrics
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = 0.0
        self.total_fees = 0.0
        
        # Risk controls
        self.max_concurrent_trades = 5
        self.max_trade_size = 1000.0
    
    async def execute_arbitrage(self, opportunity: Dict) -> TradeResult:
        """
        Execute an arbitrage opportunity.
        
        Args:
            opportunity: The arbitrage opportunity to execute
            
        Returns:
            TradeResult: Result of the trade execution
        """
        start_time = datetime.utcnow()
        opportunity_id = opportunity.get('id', str(uuid.uuid4()))
        
        try:
            # Pre-execution checks
            if not await self._pre_execution_checks(opportunity):
                return TradeResult(
                    success=False,
                    opportunity_id=opportunity_id,
                    buy_order=None,
                    sell_order=None,
                    profit=0.0,
                    fees=0.0,
                    execution_time=0.0,
                    reason="Pre-execution checks failed"
                )
            
            # Calculate trade parameters
            trade_params = await self._calculate_trade_parameters(opportunity)
            
            # Execute the arbitrage trade
            result = await self._execute_simultaneous_trades(opportunity, trade_params)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # Update metrics
            await self._update_execution_metrics(result)
            
            # Log the trade
            await self._log_trade(result)
            
            return result
            
        except Exception as e:
            print(f"Error executing arbitrage: {e}")
            return TradeResult(
                success=False,
                opportunity_id=opportunity_id,
                buy_order=None,
                sell_order=None,
                profit=0.0,
                fees=0.0,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                reason=f"Execution error: {str(e)}"
            )
    
    async def _pre_execution_checks(self, opportunity: Dict) -> bool:
        """Perform pre-execution validation checks."""
        try:
            # Check if we have too many concurrent trades
            if len(self.active_arbitrages) >= self.max_concurrent_trades:
                print("Too many concurrent trades")
                return False
            
            # Check trade size limits
            trade_size = opportunity.get('profit_abs', 0) * 10  # Estimate
            if trade_size > self.max_trade_size:
                print("Trade size exceeds limit")
                return False
            
            # Check minimum profit threshold
            profit_pct = opportunity.get('profit_pct', 0)
            if profit_pct < settings.trading.min_profit_threshold * 100:
                print("Profit below minimum threshold")
                return False
            
            # Check portfolio balance if available
            if self.portfolio:
                available_balance = await self.portfolio.get_available_balance()
                if trade_size > available_balance:
                    print("Insufficient balance")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error in pre-execution checks: {e}")
            return False
    
    async def _calculate_trade_parameters(self, opportunity: Dict) -> Dict:
        """Calculate optimal trade parameters."""
        # Basic trade sizing (would be more sophisticated in real implementation)
        base_amount = 100.0  # Base trade amount in USD
        
        # Adjust based on opportunity confidence and profit
        profit_pct = opportunity.get('profit_pct', 0)
        confidence = opportunity.get('ml_score', 0.5)
        
        # Size based on Kelly criterion (simplified)
        win_rate = confidence
        avg_win = profit_pct / 100
        avg_loss = 0.01  # Assume 1% average loss
        
        if win_rate > 0 and avg_win > 0:
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
        else:
            kelly_fraction = 0.1  # Default 10%
        
        # Calculate trade amount
        if self.portfolio:
            total_value = await self.portfolio.get_total_value()
            trade_amount = total_value * kelly_fraction
        else:
            trade_amount = base_amount
        
        # Convert to crypto amount (simplified)
        buy_price = opportunity.get('buy_price', 1.0)
        crypto_amount = trade_amount / buy_price
        
        return {
            'crypto_amount': crypto_amount,
            'usd_amount': trade_amount,
            'buy_price': buy_price,
            'sell_price': opportunity.get('sell_price', 1.0),
            'buy_exchange': opportunity.get('buy_exchange', ''),
            'sell_exchange': opportunity.get('sell_exchange', ''),
            'symbol': opportunity.get('symbol', '')
        }
    
    async def _execute_simultaneous_trades(self, opportunity: Dict, 
                                         trade_params: Dict) -> TradeResult:
        """Execute buy and sell orders simultaneously."""
        opportunity_id = opportunity.get('id')
        
        try:
            # Start both orders simultaneously
            buy_task = asyncio.create_task(
                self.executor.place_order(
                    symbol=trade_params['symbol'],
                    exchange=trade_params['buy_exchange'],
                    side='buy',
                    amount=trade_params['crypto_amount'],
                    order_type=OrderType.MARKET,
                    price=trade_params['buy_price']
                )
            )
            
            sell_task = asyncio.create_task(
                self.executor.place_order(
                    symbol=trade_params['symbol'],
                    exchange=trade_params['sell_exchange'],
                    side='sell',
                    amount=trade_params['crypto_amount'],
                    order_type=OrderType.MARKET,
                    price=trade_params['sell_price']
                )
            )
            
            # Wait for both orders to complete
            buy_order, sell_order = await asyncio.gather(buy_task, sell_task)
            
            # Calculate results
            if (buy_order.status == OrderStatus.FILLED and 
                sell_order.status == OrderStatus.FILLED):
                
                # Calculate profit
                buy_cost = buy_order.filled_amount * buy_order.average_price
                sell_proceeds = sell_order.filled_amount * sell_order.average_price
                total_fees = buy_order.fees + sell_order.fees
                net_profit = sell_proceeds - buy_cost - total_fees
                
                # Calculate slippage
                expected_buy_cost = trade_params['crypto_amount'] * trade_params['buy_price']
                expected_sell_proceeds = trade_params['crypto_amount'] * trade_params['sell_price']
                expected_profit = expected_sell_proceeds - expected_buy_cost
                
                slippage = (expected_profit - net_profit) / max(expected_profit, 1.0)
                
                return TradeResult(
                    success=True,
                    opportunity_id=opportunity_id,
                    buy_order=buy_order,
                    sell_order=sell_order,
                    profit=net_profit,
                    fees=total_fees,
                    execution_time=0.0,  # Will be set by caller
                    slippage=slippage
                )
            
            else:
                # One or both orders failed
                return TradeResult(
                    success=False,
                    opportunity_id=opportunity_id,
                    buy_order=buy_order,
                    sell_order=sell_order,
                    profit=0.0,
                    fees=buy_order.fees + sell_order.fees,
                    execution_time=0.0,
                    reason="Order execution failed"
                )
                
        except Exception as e:
            print(f"Error executing simultaneous trades: {e}")
            return TradeResult(
                success=False,
                opportunity_id=opportunity_id,
                buy_order=None,
                sell_order=None,
                profit=0.0,
                fees=0.0,
                execution_time=0.0,
                reason=f"Trade execution error: {str(e)}"
            )
    
    async def _update_execution_metrics(self, result: TradeResult):
        """Update execution performance metrics."""
        self.total_trades += 1
        
        if result.success:
            self.successful_trades += 1
            self.total_profit += result.profit
        
        self.total_fees += result.fees
    
    async def _log_trade(self, result: TradeResult):
        """Log trade execution details."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'opportunity_id': result.opportunity_id,
            'success': result.success,
            'profit': result.profit,
            'fees': result.fees,
            'execution_time': result.execution_time,
            'slippage': result.slippage,
            'reason': result.reason
        }
        
        print(f"Trade logged: {log_entry}")
        # In real implementation, would save to database
    
    async def close_all_positions(self):
        """Close all open positions (emergency function)."""
        try:
            if self.portfolio:
                positions = self.portfolio.positions.copy()
                
                for position_key, position in positions.items():
                    # Create market sell order to close position
                    close_order = await self.executor.place_order(
                        symbol=position.symbol,
                        exchange=position.exchange,
                        side='sell' if position.side == 'buy' else 'buy',
                        amount=position.amount,
                        order_type=OrderType.MARKET
                    )
                    
                    if close_order.status == OrderStatus.FILLED:
                        await self.portfolio.close_position(
                            position.symbol,
                            position.exchange,
                            position.side,
                            close_order.average_price
                        )
            
            print("All positions closed")
            
        except Exception as e:
            print(f"Error closing positions: {e}")
    
    async def get_execution_metrics(self) -> Dict:
        """Get execution performance metrics."""
        success_rate = (self.successful_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        avg_profit = (self.total_profit / self.successful_trades) if self.successful_trades > 0 else 0
        
        return {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'success_rate': success_rate,
            'total_profit': self.total_profit,
            'total_fees': self.total_fees,
            'net_profit': self.total_profit - self.total_fees,
            'average_profit_per_trade': avg_profit,
            'active_arbitrages': len(self.active_arbitrages)
        }
    
    async def get_status(self) -> Dict:
        """Get trade executor status."""
        return {
            'paper_trading': self.paper_trading,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'active_arbitrages': len(self.active_arbitrages),
            'total_profit': self.total_profit,
            'total_fees': self.total_fees
        }
