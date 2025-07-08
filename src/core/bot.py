"""
Core arbitrage bot implementation.
Main entry point for the trading system.
"""
import asyncio
import signal
import sys
from typing import Dict, List, Optional
import structlog
from datetime import datetime

from src.data.collectors import DataCollector
from src.core.portfolio import Portfolio
from src.trading.executor import TradeExecutor
from src.ml.predictor import MLPredictor
from src.quant.analyzer import QuantAnalyzer
from src.risk.manager import RiskManager
from config.settings import settings

logger = structlog.get_logger(__name__)


class ArbitrageBot:
    """
    Main arbitrage bot class that orchestrates all components.
    """
    
    def __init__(self, paper_trading: bool = True):
        """Initialize the arbitrage bot."""
        self.paper_trading = paper_trading
        self.running = False
        self.components = {}
        
        # Initialize core components
        self._initialize_components()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("ArbitrageBot initialized", paper_trading=paper_trading)
    
    def _initialize_components(self):
        """Initialize all bot components."""
        try:
            # Core components
            self.portfolio = Portfolio(
                initial_balance=settings.trading.initial_balance_usd,
                paper_trading=self.paper_trading
            )
            
            self.data_collector = DataCollector(
                exchanges=settings.trading.supported_exchanges,
                symbols=settings.trading.trading_pairs
            )
            
            self.ml_predictor = MLPredictor()
            self.quant_analyzer = QuantAnalyzer()
            self.risk_manager = RiskManager(portfolio=self.portfolio)
            
            self.trade_executor = TradeExecutor(
                portfolio=self.portfolio,
                paper_trading=self.paper_trading
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize components", error=str(e))
            raise
    
    async def start(self):
        """Start the arbitrage bot."""
        if self.running:
            logger.warning("Bot is already running")
            return
        
        try:
            self.running = True
            logger.info("Starting arbitrage bot")
            
            # Start data collection
            await self.data_collector.start()
            
            # Start main trading loop
            await self._main_loop()
            
        except Exception as e:
            logger.error("Error starting bot", error=str(e))
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the arbitrage bot gracefully."""
        if not self.running:
            return
        
        logger.info("Stopping arbitrage bot")
        self.running = False
        
        try:
            # Stop data collection
            await self.data_collector.stop()
            
            # Close any open positions
            await self.trade_executor.close_all_positions()
            
            # Save final state
            await self._save_state()
            
            logger.info("Arbitrage bot stopped successfully")
            
        except Exception as e:
            logger.error("Error stopping bot", error=str(e))
    
    async def _main_loop(self):
        """Main trading loop."""
        logger.info("Starting main trading loop")
        
        while self.running:
            try:
                # Get latest market data
                market_data = await self.data_collector.get_latest_data()
                
                if not market_data:
                    await asyncio.sleep(1)
                    continue
                
                # Analyze arbitrage opportunities
                opportunities = await self._analyze_opportunities(market_data)
                
                # Save opportunities to database
                for opp in opportunities:
                    await self.save_opportunity_to_db(opp)
                
                # Filter opportunities through risk management
                filtered_opportunities = await self.risk_manager.filter_opportunities(
                    opportunities
                )
                
                # Execute trades for viable opportunities
                if filtered_opportunities:
                    await self._execute_opportunities(filtered_opportunities)
                
                # Update portfolio and metrics
                await self._update_metrics()
                
                # Save portfolio snapshot periodically
                if not hasattr(self, '_iteration_count'):
                    self._iteration_count = 0
                    self._last_snapshot = datetime.utcnow()
                
                self._iteration_count += 1
                
                # Save snapshot every 50 iterations
                if self._iteration_count % 50 == 0:
                    await self.save_portfolio_snapshot()
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error("Error in main loop", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _analyze_opportunities(self, market_data: Dict) -> List[Dict]:
        """Analyze market data for arbitrage opportunities."""
        opportunities = []
        
        try:
            # Quantitative analysis
            quant_opportunities = await self.quant_analyzer.find_arbitrage(market_data)
            
            # ML prediction and scoring
            for opportunity in quant_opportunities:
                # Get ML prediction
                prediction = await self.ml_predictor.predict_opportunity(opportunity)
                
                # Add prediction score to opportunity
                opportunity['ml_score'] = prediction['confidence']
                opportunity['predicted_profit'] = prediction['expected_profit']
                
                # Filter by minimum threshold
                if prediction['confidence'] >= settings.ml.prediction_threshold:
                    opportunities.append(opportunity)
            
            logger.debug(f"Found {len(opportunities)} viable opportunities")
            return opportunities
            
        except Exception as e:
            logger.error("Error analyzing opportunities", error=str(e))
            return []
    
    async def _execute_opportunities(self, opportunities: List[Dict]):
        """Execute trading opportunities."""
        for opportunity in opportunities:
            try:
                # Final risk check
                if await self.risk_manager.can_execute_trade(opportunity):
                    # Execute the trade
                    result = await self.trade_executor.execute_arbitrage(opportunity)
                    
                    if result['success']:
                        logger.info(
                            "Trade executed successfully",
                            opportunity_id=opportunity['id'],
                            profit=result['profit']
                        )
                        
                        # Save trade and opportunity to database
                        await self.save_trade_to_db(opportunity, result)
                        await self.save_opportunity_to_db(opportunity)
                        
                    else:
                        logger.warning(
                            "Trade execution failed",
                            opportunity_id=opportunity['id'],
                            reason=result['reason']
                        )
                
            except Exception as e:
                logger.error(
                    "Error executing opportunity",
                    opportunity_id=opportunity.get('id'),
                    error=str(e)
                )
    
    async def _update_metrics(self):
        """Update portfolio metrics and performance tracking."""
        try:
            # Update portfolio value
            await self.portfolio.update_value()
            
            # Log performance metrics
            metrics = await self.portfolio.get_metrics()
            logger.debug("Portfolio metrics", **metrics)
            
            # Check for circuit breakers
            await self.risk_manager.check_circuit_breakers(metrics)
            
        except Exception as e:
            logger.error("Error updating metrics", error=str(e))
    
    async def _save_state(self):
        """Save current bot state for persistence."""
        try:
            state = {
                'timestamp': datetime.utcnow().isoformat(),
                'portfolio': await self.portfolio.get_state(),
                'metrics': await self.portfolio.get_metrics(),
                'running': self.running
            }
            
            # Save to database or file
            # This would be implemented based on your persistence strategy
            logger.info("Bot state saved")
            
        except Exception as e:
            logger.error("Error saving state", error=str(e))
    
    async def save_trade_to_db(self, opportunity: Dict, trade_result: Dict):
        """Save executed trade to database."""
        try:
            from src.database.models import db_manager, Trade
            from datetime import datetime
            
            session = db_manager.get_session()
            
            trade = Trade(
                opportunity_id=opportunity.get('id', ''),
                symbol=opportunity.get('symbol', ''),
                buy_exchange=opportunity.get('buy_exchange', ''),
                sell_exchange=opportunity.get('sell_exchange', ''),
                buy_price=opportunity.get('buy_price', 0),
                sell_price=opportunity.get('sell_price', 0),
                amount=trade_result.get('amount', 0),
                profit_abs=trade_result.get('profit_abs', 0),
                profit_pct=trade_result.get('profit_pct', 0),
                fees=trade_result.get('fees', 0),
                slippage=trade_result.get('slippage', 0),
                execution_time=trade_result.get('execution_time', 0),
                status=trade_result.get('status', 'completed'),
                timestamp=datetime.utcnow()
            )
            
            session.add(trade)
            session.commit()
            db_manager.close_session(session)
            
            logger.info("Trade saved to database", trade_id=str(trade.id))
            
        except Exception as e:
            logger.error("Failed to save trade to database", error=str(e))

    async def save_opportunity_to_db(self, opportunity: Dict):
        """Save detected opportunity to database."""
        try:
            from src.database.models import db_manager, Opportunity
            from datetime import datetime
            
            session = db_manager.get_session()
            
            opp = Opportunity(
                symbol=opportunity.get('symbol', ''),
                buy_exchange=opportunity.get('buy_exchange', ''),
                sell_exchange=opportunity.get('sell_exchange', ''),
                buy_price=opportunity.get('buy_price', 0),
                sell_price=opportunity.get('sell_price', 0),
                profit_pct=opportunity.get('profit_pct', 0),
                volume_available=opportunity.get('volume_available', 0),
                confidence_score=opportunity.get('confidence_score', 0),
                executed=False,
                timestamp=datetime.utcnow()
            )
            
            session.add(opp)
            session.commit()
            opportunity['db_id'] = str(opp.id)
            db_manager.close_session(session)
            
        except Exception as e:
            logger.error("Failed to save opportunity to database", error=str(e))

    async def save_portfolio_snapshot(self):
        """Save current portfolio state to database."""
        try:
            from src.database.models import db_manager, PortfolioSnapshot
            from datetime import datetime
            
            session = db_manager.get_session()
            metrics = await self.portfolio.get_metrics()
            
            snapshot = PortfolioSnapshot(
                total_value=metrics.get('total_value', 0),
                usd_balance=self.portfolio.balances.get('USD', 0),
                positions=dict(self.portfolio.positions),
                daily_pnl=metrics.get('daily_pnl', 0),
                total_pnl=metrics.get('realized_pnl', 0),
                max_drawdown=metrics.get('max_drawdown', 0),
                sharpe_ratio=metrics.get('sharpe_ratio', 0),
                total_trades=len(self.portfolio.trades),
                win_rate=metrics.get('win_rate', 0),
                timestamp=datetime.utcnow()
            )
            
            session.add(snapshot)
            session.commit()
            db_manager.close_session(session)
            
        except Exception as e:
            logger.error("Failed to save portfolio snapshot", error=str(e))
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully")
        asyncio.create_task(self.stop())
    
    async def get_status(self) -> Dict:
        """Get current bot status."""
        try:
            return {
                'running': self.running,
                'paper_trading': self.paper_trading,
                'portfolio': await self.portfolio.get_state(),
                'metrics': await self.portfolio.get_metrics(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error("Error getting status", error=str(e))
            return {'error': str(e)}


# Global bot instance
bot_instance: Optional[ArbitrageBot] = None


def get_bot() -> ArbitrageBot:
    """Get the global bot instance."""
    global bot_instance
    if bot_instance is None:
        bot_instance = ArbitrageBot(paper_trading=settings.trading.paper_trading)
    return bot_instance
