"""
Portfolio management system for tracking positions, balances, and performance.
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

from config.settings import settings


@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    exchange: str
    side: str  # 'buy' or 'sell'
    amount: float
    entry_price: float
    current_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    fees_paid: float = 0.0
    
    @property
    def market_value(self) -> float:
        """Current market value of the position."""
        return self.amount * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        if self.side == 'buy':
            return (self.current_price - self.entry_price) * self.amount
        else:  # sell/short
            return (self.entry_price - self.current_price) * self.amount
    
    @property
    def unrealized_pnl_percentage(self) -> float:
        """Unrealized PnL as percentage."""
        if self.entry_price == 0:
            return 0.0
        return (self.unrealized_pnl / (self.entry_price * self.amount)) * 100


@dataclass
class Trade:
    """Represents a completed trade."""
    id: str
    symbol: str
    exchange: str
    side: str
    amount: float
    price: float
    fees: float
    timestamp: datetime
    pnl: float = 0.0
    strategy: str = ""


class Portfolio:
    """
    Portfolio management class for tracking balances, positions, and performance.
    """
    
    def __init__(self, initial_balance: float = 10000.0, paper_trading: bool = True):
        """Initialize portfolio."""
        self.initial_balance = initial_balance
        self.paper_trading = paper_trading
        
        # Balances by currency
        self.balances: Dict[str, float] = {'USD': initial_balance}
        
        # Active positions
        self.positions: Dict[str, Position] = {}
        
        # Trade history
        self.trades: List[Trade] = []
        
        # Performance tracking
        self.daily_returns: List[float] = []
        self.daily_values: List[Tuple[datetime, float]] = []
        self.max_value = initial_balance
        self.max_drawdown = 0.0
        
        # Risk metrics
        self.var_95 = 0.0
        self.sharpe_ratio = 0.0
        self.sortino_ratio = 0.0
        
        # Initialize daily tracking
        self._last_update = datetime.utcnow().date()
        self.daily_values.append((datetime.utcnow(), initial_balance))
    
    async def get_balance(self, currency: str = 'USD') -> float:
        """Get balance for a specific currency."""
        return self.balances.get(currency, 0.0)
    
    async def get_total_value(self) -> float:
        """Get total portfolio value including positions."""
        total = sum(self.balances.values())
        
        # Add market value of all positions
        for position in self.positions.values():
            total += position.market_value
        
        return total
    
    async def update_value(self):
        """Update portfolio value and performance metrics."""
        current_value = await self.get_total_value()
        current_date = datetime.utcnow().date()
        
        # Track daily values
        self.daily_values.append((datetime.utcnow(), current_value))
        
        # Calculate daily return if new day
        if current_date != self._last_update:
            if len(self.daily_values) >= 2:
                prev_value = self.daily_values[-2][1]
                daily_return = (current_value - prev_value) / prev_value
                self.daily_returns.append(daily_return)
            
            self._last_update = current_date
        
        # Update max value and drawdown
        if current_value > self.max_value:
            self.max_value = current_value
        
        current_drawdown = (self.max_value - current_value) / self.max_value
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # Update risk metrics
        await self._update_risk_metrics()
    
    async def add_position(self, position: Position):
        """Add a new position to the portfolio."""
        position_key = f"{position.symbol}_{position.exchange}_{position.side}"
        
        if position_key in self.positions:
            # Update existing position (average price)
            existing = self.positions[position_key]
            total_amount = existing.amount + position.amount
            avg_price = (
                (existing.entry_price * existing.amount) + 
                (position.entry_price * position.amount)
            ) / total_amount
            
            existing.amount = total_amount
            existing.entry_price = avg_price
            existing.fees_paid += position.fees_paid
        else:
            self.positions[position_key] = position
    
    async def close_position(self, symbol: str, exchange: str, side: str, 
                           close_price: float) -> Optional[Trade]:
        """Close a position and record the trade."""
        position_key = f"{symbol}_{exchange}_{side}"
        
        if position_key not in self.positions:
            return None
        
        position = self.positions[position_key]
        
        # Calculate PnL
        if side == 'buy':
            pnl = (close_price - position.entry_price) * position.amount
        else:
            pnl = (position.entry_price - close_price) * position.amount
        
        pnl -= position.fees_paid  # Subtract fees
        
        # Create trade record
        trade = Trade(
            id=f"trade_{len(self.trades) + 1}",
            symbol=symbol,
            exchange=exchange,
            side=side,
            amount=position.amount,
            price=close_price,
            fees=position.fees_paid,
            timestamp=datetime.utcnow(),
            pnl=pnl
        )
        
        self.trades.append(trade)
        
        # Update balances
        if side == 'buy':
            # Selling, add to USD balance
            self.balances['USD'] += position.amount * close_price + pnl
        else:
            # Covering short, subtract from USD balance
            self.balances['USD'] -= position.amount * close_price - pnl
        
        # Remove position
        del self.positions[position_key]
        
        return trade
    
    async def update_position_prices(self, prices: Dict[str, Dict[str, float]]):
        """Update current prices for all positions."""
        for position_key, position in self.positions.items():
            exchange_prices = prices.get(position.exchange, {})
            if position.symbol in exchange_prices:
                position.current_price = exchange_prices[position.symbol]
    
    async def get_metrics(self) -> Dict:
        """Get portfolio performance metrics."""
        current_value = await self.get_total_value()
        total_return = (current_value - self.initial_balance) / self.initial_balance
        
        # Calculate win rate
        profitable_trades = len([t for t in self.trades if t.pnl > 0])
        total_trades = len(self.trades)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        # Calculate profit factor
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            'total_value': current_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'unrealized_pnl': sum(p.unrealized_pnl for p in self.positions.values()),
            'realized_pnl': sum(t.pnl for t in self.trades),
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown * 100,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'var_95': self.var_95,
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'open_positions': len(self.positions),
            'daily_returns_std': np.std(self.daily_returns) if self.daily_returns else 0,
            'calmar_ratio': (total_return * 365) / (self.max_drawdown * 100) if self.max_drawdown > 0 else 0
        }
    
    async def _update_risk_metrics(self):
        """Update risk metrics like Sharpe ratio, VaR, etc."""
        if len(self.daily_returns) < 2:
            return
        
        returns_array = np.array(self.daily_returns)
        
        # Sharpe Ratio (assuming 0% risk-free rate)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)
        self.sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns_array[returns_array < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        self.sortino_ratio = (mean_return / downside_std) * np.sqrt(252) if downside_std > 0 else 0
        
        # Value at Risk (95% confidence)
        if len(returns_array) >= 20:
            self.var_95 = np.percentile(returns_array, 5)
    
    async def get_state(self) -> Dict:
        """Get current portfolio state."""
        return {
            'balances': self.balances.copy(),
            'positions': {
                key: {
                    'symbol': pos.symbol,
                    'exchange': pos.exchange,
                    'side': pos.side,
                    'amount': pos.amount,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'market_value': pos.market_value
                }
                for key, pos in self.positions.items()
            },
            'recent_trades': [
                {
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'exchange': trade.exchange,
                    'side': trade.side,
                    'amount': trade.amount,
                    'price': trade.price,
                    'pnl': trade.pnl,
                    'timestamp': trade.timestamp.isoformat()
                }
                for trade in self.trades[-10:]  # Last 10 trades
            ]
        }
    
    async def check_position_limits(self, symbol: str, amount: float) -> bool:
        """Check if a new position would exceed limits."""
        current_value = await self.get_total_value()
        position_value = amount * 1000  # Approximate value (would use current price)
        
        # Check maximum position size
        if position_value > current_value * settings.trading.max_position_size:
            return False
        
        # Check maximum position risk
        if position_value > current_value * settings.risk.max_position_risk:
            return False
        
        return True
    
    async def get_available_balance(self, currency: str = 'USD') -> float:
        """Get available balance for trading (excluding margin requirements)."""
        total_balance = self.balances.get(currency, 0.0)
        
        # Reserve some balance for margin requirements
        reserved = sum(pos.market_value * 0.1 for pos in self.positions.values())
        
        return max(0.0, total_balance - reserved)
