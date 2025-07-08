"""
Risk management system for controlling trading exposure and managing portfolio risk.
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np

from config.settings import settings


@dataclass
class RiskLimit:
    """Risk limit definition."""
    name: str
    limit_type: str  # 'absolute', 'percentage', 'volatility'
    threshold: float
    current_value: float
    breach_action: str  # 'stop_trading', 'reduce_position', 'alert'
    active: bool = True


class RiskManager:
    """
    Comprehensive risk management system for the arbitrage bot.
    """
    
    def __init__(self, portfolio=None):
        """Initialize risk manager."""
        self.portfolio = portfolio
        
        # Risk limits
        self.risk_limits = {}
        self.circuit_breakers = {}
        
        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.max_daily_trades = 100
        
        # Position tracking
        self.total_exposure = 0.0
        self.position_risks = {}
        
        # Risk metrics
        self.var_95 = 0.0
        self.expected_shortfall = 0.0
        self.correlation_matrix = {}
        
        # Emergency controls
        self.emergency_stop = False
        self.trading_halted = False
        
        # Initialize default risk limits
        self._initialize_risk_limits()
    
    def _initialize_risk_limits(self):
        """Initialize default risk limits."""
        # Daily loss limit
        self.risk_limits['daily_loss'] = RiskLimit(
            name='Daily Loss Limit',
            limit_type='absolute',
            threshold=settings.risk.max_daily_loss,
            current_value=0.0,
            breach_action='stop_trading'
        )
        
        # Maximum drawdown
        self.risk_limits['max_drawdown'] = RiskLimit(
            name='Maximum Drawdown',
            limit_type='percentage',
            threshold=settings.risk.max_drawdown_threshold,
            current_value=0.0,
            breach_action='reduce_position'
        )
        
        # Position risk
        self.risk_limits['position_risk'] = RiskLimit(
            name='Position Risk',
            limit_type='percentage',
            threshold=settings.risk.max_position_risk,
            current_value=0.0,
            breach_action='alert'
        )
        
        # VaR limit
        self.risk_limits['var_limit'] = RiskLimit(
            name='Value at Risk',
            limit_type='percentage',
            threshold=0.05,  # 5% VaR limit
            current_value=0.0,
            breach_action='reduce_position'
        )
    
    async def can_execute_trade(self, opportunity: Dict) -> bool:
        """
        Check if a trade can be executed based on risk limits.
        
        Args:
            opportunity: The trading opportunity to evaluate
            
        Returns:
            bool: True if trade can be executed, False otherwise
        """
        try:
            # Check emergency stops
            if self.emergency_stop or self.trading_halted:
                return False
            
            # Check daily limits
            if not await self._check_daily_limits(opportunity):
                return False
            
            # Check position limits
            if not await self._check_position_limits(opportunity):
                return False
            
            # Check exposure limits
            if not await self._check_exposure_limits(opportunity):
                return False
            
            # Check correlation limits
            if not await self._check_correlation_limits(opportunity):
                return False
            
            # Check volatility limits
            if not await self._check_volatility_limits(opportunity):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error checking trade execution: {e}")
            return False
    
    async def _check_daily_limits(self, opportunity: Dict) -> bool:
        """Check daily trading limits."""
        # Check daily loss limit
        daily_loss_limit = self.risk_limits['daily_loss']
        if abs(self.daily_pnl) >= daily_loss_limit.threshold:
            print("Daily loss limit exceeded")
            return False
        
        # Check daily trade count
        if self.daily_trades >= self.max_daily_trades:
            print("Daily trade limit exceeded")
            return False
        
        # Check if additional loss would breach limit
        potential_loss = opportunity.get('estimated_fees', 0) + opportunity.get('max_loss', 0)
        if self.daily_pnl - potential_loss <= -daily_loss_limit.threshold:
            print("Trade would breach daily loss limit")
            return False
        
        return True
    
    async def _check_position_limits(self, opportunity: Dict) -> bool:
        """Check position size limits."""
        if not self.portfolio:
            return True
        
        symbol = opportunity.get('symbol', '')
        trade_size = opportunity.get('profit_abs', 0) * 10  # Estimate position size
        
        # Check if portfolio has available balance
        available_balance = await self.portfolio.get_available_balance()
        if trade_size > available_balance * settings.trading.max_position_size:
            print("Trade size exceeds position limit")
            return False
        
        # Check maximum position risk
        total_value = await self.portfolio.get_total_value()
        if trade_size > total_value * settings.risk.max_position_risk:
            print("Trade would exceed position risk limit")
            return False
        
        return True
    
    async def _check_exposure_limits(self, opportunity: Dict) -> bool:
        """Check total exposure limits."""
        symbol = opportunity.get('symbol', '')
        trade_value = opportunity.get('profit_abs', 0) * 10  # Estimate
        
        # Calculate current exposure for this symbol
        current_exposure = self.position_risks.get(symbol, 0.0)
        new_exposure = current_exposure + trade_value
        
        # Check single symbol exposure
        if self.portfolio:
            total_value = await self.portfolio.get_total_value()
            if new_exposure > total_value * 0.2:  # Max 20% in single symbol
                print(f"Symbol exposure limit exceeded for {symbol}")
                return False
        
        return True
    
    async def _check_correlation_limits(self, opportunity: Dict) -> bool:
        """Check correlation-based risk limits."""
        # Placeholder for correlation analysis
        # In a real implementation, this would check correlations between positions
        return True
    
    async def _check_volatility_limits(self, opportunity: Dict) -> bool:
        """Check volatility-based risk limits."""
        # Placeholder for volatility analysis
        # In a real implementation, this would check if market volatility is too high
        return True
    
    async def filter_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Filter opportunities based on risk criteria.
        
        Args:
            opportunities: List of opportunities to filter
            
        Returns:
            List of filtered opportunities
        """
        filtered = []
        
        for opportunity in opportunities:
            try:
                # Basic risk scoring
                risk_score = await self._calculate_risk_score(opportunity)
                opportunity['risk_score'] = risk_score
                
                # Filter by risk threshold
                if risk_score <= 0.7:  # Accept low to medium risk
                    if await self.can_execute_trade(opportunity):
                        filtered.append(opportunity)
                    
            except Exception as e:
                print(f"Error filtering opportunity: {e}")
                continue
        
        # Sort by risk-adjusted return
        filtered.sort(
            key=lambda x: x.get('profit_pct', 0) / max(x.get('risk_score', 1), 0.1),
            reverse=True
        )
        
        return filtered
    
    async def _calculate_risk_score(self, opportunity: Dict) -> float:
        """
        Calculate risk score for an opportunity.
        
        Returns:
            float: Risk score between 0 (low risk) and 1 (high risk)
        """
        risk_factors = []
        
        # Profit margin risk (lower profit = higher risk)
        profit_pct = opportunity.get('profit_pct', 0)
        profit_risk = max(0, 1 - (profit_pct / 5.0))  # Risk decreases as profit increases
        risk_factors.append(profit_risk * 0.3)
        
        # Exchange risk (some exchanges are riskier)
        buy_exchange = opportunity.get('buy_exchange', '')
        sell_exchange = opportunity.get('sell_exchange', '')
        exchange_risk = self._get_exchange_risk(buy_exchange, sell_exchange)
        risk_factors.append(exchange_risk * 0.2)
        
        # Volume risk (low volume = higher risk)
        volume = opportunity.get('volume_available', 0)
        volume_risk = max(0, 1 - np.log1p(volume) / 10.0)
        risk_factors.append(volume_risk * 0.2)
        
        # Time risk (opportunities that have been available longer are riskier)
        # This would require tracking opportunity age
        time_risk = 0.3  # Placeholder
        risk_factors.append(time_risk * 0.1)
        
        # Market condition risk
        market_risk = await self._get_market_risk()
        risk_factors.append(market_risk * 0.2)
        
        return sum(risk_factors)
    
    def _get_exchange_risk(self, buy_exchange: str, sell_exchange: str) -> float:
        """Get risk score for exchange pair."""
        # Exchange risk scores (0 = low risk, 1 = high risk)
        exchange_risks = {
            'binance': 0.1,
            'coinbase': 0.2,
            'kraken': 0.3,
            'bitfinex': 0.4
        }
        
        buy_risk = exchange_risks.get(buy_exchange.lower(), 0.5)
        sell_risk = exchange_risks.get(sell_exchange.lower(), 0.5)
        
        return (buy_risk + sell_risk) / 2
    
    async def _get_market_risk(self) -> float:
        """Get current market risk level."""
        # Placeholder for market risk assessment
        # This would analyze market volatility, liquidity, etc.
        return 0.5
    
    async def check_circuit_breakers(self, portfolio_metrics: Dict):
        """Check if circuit breakers should be triggered."""
        try:
            # Update current values
            self.daily_pnl = portfolio_metrics.get('realized_pnl', 0)
            current_drawdown = portfolio_metrics.get('max_drawdown', 0)
            
            # Check circuit breakers
            if abs(self.daily_pnl) >= settings.risk.circuit_breaker_threshold * 1000:
                await self._trigger_circuit_breaker('daily_loss')
            
            if current_drawdown >= settings.risk.circuit_breaker_threshold:
                await self._trigger_circuit_breaker('drawdown')
            
            # Update risk limit values
            self.risk_limits['daily_loss'].current_value = abs(self.daily_pnl)
            self.risk_limits['max_drawdown'].current_value = current_drawdown
            
        except Exception as e:
            print(f"Error checking circuit breakers: {e}")
    
    async def _trigger_circuit_breaker(self, breaker_type: str):
        """Trigger a circuit breaker."""
        print(f"CIRCUIT BREAKER TRIGGERED: {breaker_type}")
        
        if breaker_type == 'daily_loss':
            self.trading_halted = True
            print("Trading halted due to daily loss limit")
        elif breaker_type == 'drawdown':
            self.emergency_stop = True
            print("Emergency stop triggered due to drawdown")
        
        # Log the event
        await self._log_risk_event('circuit_breaker', breaker_type)
    
    async def update_position_risk(self, symbol: str, new_exposure: float):
        """Update position risk tracking."""
        self.position_risks[symbol] = new_exposure
        
        # Update total exposure
        self.total_exposure = sum(self.position_risks.values())
    
    async def calculate_var(self, confidence: float = 0.95, 
                          holding_period: int = 1) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            confidence: Confidence level (e.g., 0.95 for 95% VaR)
            holding_period: Holding period in days
            
        Returns:
            float: VaR estimate
        """
        if not self.portfolio:
            return 0.0
        
        try:
            # Get portfolio returns
            portfolio_value = await self.portfolio.get_total_value()
            daily_returns = self.portfolio.daily_returns
            
            if len(daily_returns) < 20:
                return portfolio_value * 0.05  # Default 5% VaR
            
            # Calculate VaR using historical simulation
            returns_array = np.array(daily_returns)
            var_percentile = (1 - confidence) * 100
            var_return = np.percentile(returns_array, var_percentile)
            
            # Scale for holding period
            var_scaled = var_return * np.sqrt(holding_period)
            
            # Convert to dollar amount
            self.var_95 = abs(var_scaled * portfolio_value)
            
            return self.var_95
            
        except Exception as e:
            print(f"Error calculating VaR: {e}")
            return 0.0
    
    async def calculate_expected_shortfall(self, confidence: float = 0.95) -> float:
        """Calculate Expected Shortfall (Conditional VaR)."""
        if not self.portfolio:
            return 0.0
        
        try:
            daily_returns = self.portfolio.daily_returns
            portfolio_value = await self.portfolio.get_total_value()
            
            if len(daily_returns) < 20:
                return portfolio_value * 0.07  # Default 7% ES
            
            returns_array = np.array(daily_returns)
            var_percentile = (1 - confidence) * 100
            var_threshold = np.percentile(returns_array, var_percentile)
            
            # Expected shortfall is mean of returns below VaR
            tail_returns = returns_array[returns_array <= var_threshold]
            
            if len(tail_returns) > 0:
                expected_shortfall_return = np.mean(tail_returns)
                self.expected_shortfall = abs(expected_shortfall_return * portfolio_value)
            else:
                self.expected_shortfall = self.var_95
            
            return self.expected_shortfall
            
        except Exception as e:
            print(f"Error calculating Expected Shortfall: {e}")
            return 0.0
    
    async def get_risk_report(self) -> Dict:
        """Generate comprehensive risk report."""
        try:
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'emergency_stop': self.emergency_stop,
                'trading_halted': self.trading_halted,
                'daily_pnl': self.daily_pnl,
                'daily_trades': self.daily_trades,
                'total_exposure': self.total_exposure,
                'var_95': self.var_95,
                'expected_shortfall': self.expected_shortfall,
                'risk_limits': {
                    name: {
                        'threshold': limit.threshold,
                        'current_value': limit.current_value,
                        'utilization_pct': (limit.current_value / limit.threshold) * 100 if limit.threshold > 0 else 0,
                        'active': limit.active
                    }
                    for name, limit in self.risk_limits.items()
                },
                'position_risks': self.position_risks.copy()
            }
            
            # Add portfolio metrics if available
            if self.portfolio:
                portfolio_metrics = await self.portfolio.get_metrics()
                report['portfolio_metrics'] = portfolio_metrics
            
            return report
            
        except Exception as e:
            print(f"Error generating risk report: {e}")
            return {'error': str(e)}
    
    async def reset_daily_limits(self):
        """Reset daily limits (should be called at start of each day)."""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.trading_halted = False
        
        # Reset daily risk limit values
        self.risk_limits['daily_loss'].current_value = 0.0
        
        print("Daily risk limits reset")
    
    async def emergency_shutdown(self, reason: str):
        """Trigger emergency shutdown of trading."""
        self.emergency_stop = True
        self.trading_halted = True
        
        print(f"EMERGENCY SHUTDOWN: {reason}")
        await self._log_risk_event('emergency_shutdown', reason)
    
    async def resume_trading(self):
        """Resume trading after halt (manual override)."""
        self.trading_halted = False
        print("Trading resumed manually")
        await self._log_risk_event('trading_resumed', 'manual')
    
    async def _log_risk_event(self, event_type: str, details: str):
        """Log risk management events."""
        # Placeholder for logging risk events
        # In real implementation, this would log to database or file
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details,
            'portfolio_value': await self.portfolio.get_total_value() if self.portfolio else 0
        }
        print(f"Risk event logged: {log_entry}")
    
    async def get_status(self) -> Dict:
        """Get risk manager status."""
        return {
            'emergency_stop': self.emergency_stop,
            'trading_halted': self.trading_halted,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'total_exposure': self.total_exposure,
            'active_limits': len([l for l in self.risk_limits.values() if l.active]),
            'var_95': self.var_95,
            'expected_shortfall': self.expected_shortfall
        }
