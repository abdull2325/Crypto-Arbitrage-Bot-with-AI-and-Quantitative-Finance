"""
FastAPI backend for the arbitrage bot.
Provides REST API endpoints for monitoring and control.
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from src.core.bot import get_bot
from src.database.models import get_db, db_manager, Trade, Opportunity, PortfolioSnapshot
from src.utils.metrics import get_prometheus_metrics
from config.settings import settings


# Pydantic models for API requests/responses
class BotStatus(BaseModel):
    """Bot status response model."""
    running: bool
    paper_trading: bool
    total_value: float
    daily_pnl: float
    total_trades: int
    active_opportunities: int
    last_update: str


class OpportunityResponse(BaseModel):
    """Arbitrage opportunity response model."""
    id: str
    symbol: str
    buy_exchange: str
    sell_exchange: str
    profit_pct: float
    confidence_score: float
    timestamp: str


class TradeRequest(BaseModel):
    """Trade execution request model."""
    opportunity_id: str
    override_risk_checks: bool = False


class SettingsUpdate(BaseModel):
    """Settings update request model."""
    min_profit_threshold: Optional[float] = None
    max_position_size: Optional[float] = None
    paper_trading: Optional[bool] = None


# Initialize FastAPI app
app = FastAPI(
    title="Crypto Arbitrage Bot API",
    description="REST API for monitoring and controlling the crypto arbitrage bot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup."""
    print("API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("API shutting down...")
    bot = get_bot()
    await bot.stop()


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Crypto Arbitrage Bot API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    bot = get_bot()
    status = await bot.get_status()
    
    return {
        "status": "healthy" if status.get("running", False) else "stopped",
        "timestamp": datetime.utcnow().isoformat(),
        "bot_status": status
    }


# Bot control endpoints
@app.post("/bot/start")
async def start_bot(background_tasks: BackgroundTasks):
    """Start the arbitrage bot."""
    try:
        bot = get_bot()
        if bot.running:
            raise HTTPException(status_code=400, detail="Bot is already running")
        
        # Start bot in background
        background_tasks.add_task(bot.start)
        
        return {"message": "Bot starting", "timestamp": datetime.utcnow().isoformat()}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bot/stop")
async def stop_bot():
    """Stop the arbitrage bot."""
    try:
        bot = get_bot()
        await bot.stop()
        
        return {"message": "Bot stopped", "timestamp": datetime.utcnow().isoformat()}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bot/status", response_model=BotStatus)
async def get_bot_status():
    """Get current bot status."""
    try:
        bot = get_bot()
        status = await bot.get_status()
        
        portfolio_metrics = status.get("metrics", {})
        
        return BotStatus(
            running=status.get("running", False),
            paper_trading=status.get("paper_trading", True),
            total_value=portfolio_metrics.get("total_value", 0.0),
            daily_pnl=portfolio_metrics.get("realized_pnl", 0.0),
            total_trades=portfolio_metrics.get("total_trades", 0),
            active_opportunities=0,  # Would get from opportunity tracker
            last_update=status.get("timestamp", datetime.utcnow().isoformat())
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Portfolio endpoints
@app.get("/portfolio")
async def get_portfolio():
    """Get current portfolio state."""
    try:
        bot = get_bot()
        status = await bot.get_status()
        
        return {
            "portfolio": status.get("portfolio", {}),
            "metrics": status.get("metrics", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio/metrics")
async def get_portfolio_metrics():
    """Get detailed portfolio metrics."""
    try:
        bot = get_bot()
        
        if not bot.portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not available")
        
        metrics = await bot.portfolio.get_metrics()
        
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio/positions")
async def get_positions():
    """Get current open positions."""
    try:
        bot = get_bot()
        
        if not bot.portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not available")
        
        state = await bot.portfolio.get_state()
        
        return {
            "positions": state.get("positions", {}),
            "balances": state.get("balances", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Data endpoints
@app.get("/data/market")
async def get_market_data():
    """Get current market data."""
    try:
        bot = get_bot()
        
        if not bot.data_collector:
            raise HTTPException(status_code=404, detail="Data collector not available")
        
        latest_data = await bot.data_collector.get_latest_data()
        
        return {
            "data": latest_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/opportunities")
async def get_opportunities():
    """Get current arbitrage opportunities."""
    try:
        bot = get_bot()
        
        # Get market data
        market_data = await bot.data_collector.get_latest_data()
        
        if not market_data:
            return {"opportunities": [], "timestamp": datetime.utcnow().isoformat()}
        
        # Analyze opportunities
        opportunities = await bot._analyze_opportunities(market_data)
        
        # Convert to response format
        opportunity_responses = []
        for opp in opportunities[:10]:  # Return top 10
            opportunity_responses.append(OpportunityResponse(
                id=opp.get('id', 'unknown'),
                symbol=opp.get('symbol', ''),
                buy_exchange=opp.get('buy_exchange', ''),
                sell_exchange=opp.get('sell_exchange', ''),
                profit_pct=opp.get('profit_pct', 0.0),
                confidence_score=opp.get('ml_score', 0.0),
                timestamp=datetime.utcnow().isoformat()
            ))
        
        return {
            "opportunities": opportunity_responses,
            "count": len(opportunity_responses),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Risk management endpoints
@app.get("/risk/status")
async def get_risk_status():
    """Get risk management status."""
    try:
        bot = get_bot()
        
        if not bot.risk_manager:
            raise HTTPException(status_code=404, detail="Risk manager not available")
        
        risk_report = await bot.risk_manager.get_risk_report()
        
        return {
            "risk_report": risk_report,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/risk/emergency_stop")
async def emergency_stop():
    """Trigger emergency stop."""
    try:
        bot = get_bot()
        
        if not bot.risk_manager:
            raise HTTPException(status_code=404, detail="Risk manager not available")
        
        await bot.risk_manager.emergency_shutdown("Manual emergency stop via API")
        
        return {
            "message": "Emergency stop triggered",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/risk/resume")
async def resume_trading():
    """Resume trading after halt."""
    try:
        bot = get_bot()
        
        if not bot.risk_manager:
            raise HTTPException(status_code=404, detail="Risk manager not available")
        
        await bot.risk_manager.resume_trading()
        
        return {
            "message": "Trading resumed",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Trading endpoints
@app.post("/trading/execute")
async def execute_trade(trade_request: TradeRequest):
    """Execute a specific trade opportunity."""
    try:
        bot = get_bot()
        
        if not bot.trade_executor:
            raise HTTPException(status_code=404, detail="Trade executor not available")
        
        # This would require storing opportunities and retrieving by ID
        # For now, return placeholder
        return {
            "message": f"Trade execution requested for opportunity {trade_request.opportunity_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trading/metrics")
async def get_trading_metrics():
    """Get trading execution metrics."""
    try:
        bot = get_bot()
        
        if not bot.trade_executor:
            raise HTTPException(status_code=404, detail="Trade executor not available")
        
        metrics = await bot.trade_executor.get_execution_metrics()
        
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ML endpoints
@app.get("/ml/status")
async def get_ml_status():
    """Get ML predictor status."""
    try:
        bot = get_bot()
        
        if not bot.ml_predictor:
            raise HTTPException(status_code=404, detail="ML predictor not available")
        
        status = await bot.ml_predictor.get_status()
        performance = await bot.ml_predictor.get_model_performance()
        
        return {
            "status": status,
            "performance": performance,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/features")
async def get_feature_importance():
    """Get ML model feature importance."""
    try:
        bot = get_bot()
        
        if not bot.ml_predictor:
            raise HTTPException(status_code=404, detail="ML predictor not available")
        
        features = await bot.ml_predictor.get_feature_importance()
        
        return {
            "features": features,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Settings endpoints
@app.get("/settings")
async def get_settings():
    """Get current bot settings."""
    return {
        "trading": {
            "paper_trading": settings.trading.paper_trading,
            "min_profit_threshold": settings.trading.min_profit_threshold,
            "max_position_size": settings.trading.max_position_size,
            "trading_pairs": settings.trading.trading_pairs,
            "supported_exchanges": settings.trading.supported_exchanges
        },
        "risk": {
            "max_daily_loss": settings.risk.max_daily_loss,
            "max_position_risk": settings.risk.max_position_risk,
            "stop_loss_percentage": settings.risk.stop_loss_percentage
        },
        "ml": {
            "prediction_threshold": settings.ml.prediction_threshold,
            "model_retrain_interval": settings.ml.model_retrain_interval
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/settings/update")
async def update_settings(settings_update: SettingsUpdate):
    """Update bot settings."""
    try:
        # Update settings (in a real implementation, this would persist changes)
        updated_fields = []
        
        if settings_update.min_profit_threshold is not None:
            settings.trading.min_profit_threshold = settings_update.min_profit_threshold
            updated_fields.append("min_profit_threshold")
        
        if settings_update.max_position_size is not None:
            settings.trading.max_position_size = settings_update.max_position_size
            updated_fields.append("max_position_size")
        
        if settings_update.paper_trading is not None:
            settings.trading.paper_trading = settings_update.paper_trading
            updated_fields.append("paper_trading")
        
        return {
            "message": f"Settings updated: {', '.join(updated_fields)}",
            "updated_fields": updated_fields,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Database endpoints
@app.get("/database/trades")
async def get_recent_trades(db: Session = Depends(get_db), limit: int = 50):
    """Get recent trades from database."""
    try:
        trades = db.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
        
        return {
            "trades": [
                {
                    "id": str(trade.id),
                    "symbol": trade.symbol,
                    "buy_exchange": trade.buy_exchange,
                    "sell_exchange": trade.sell_exchange,
                    "buy_price": float(trade.buy_price),
                    "sell_price": float(trade.sell_price),
                    "amount": float(trade.amount),
                    "profit_abs": float(trade.profit_abs) if trade.profit_abs else 0,
                    "profit_pct": float(trade.profit_pct) if trade.profit_pct else 0,
                    "status": trade.status,
                    "timestamp": trade.timestamp.isoformat()
                }
                for trade in trades
            ],
            "count": len(trades),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/database/opportunities")
async def get_opportunities_history(db: Session = Depends(get_db), limit: int = 100):
    """Get opportunity history from database."""
    try:
        opportunities = db.query(Opportunity).order_by(Opportunity.timestamp.desc()).limit(limit).all()
        
        return {
            "opportunities": [
                {
                    "id": str(opp.id),
                    "symbol": opp.symbol,
                    "buy_exchange": opp.buy_exchange,
                    "sell_exchange": opp.sell_exchange,
                    "buy_price": float(opp.buy_price),
                    "sell_price": float(opp.sell_price),
                    "profit_pct": float(opp.profit_pct),
                    "volume_available": float(opp.volume_available) if opp.volume_available else 0,
                    "confidence_score": float(opp.confidence_score) if opp.confidence_score else 0,
                    "executed": opp.executed,
                    "timestamp": opp.timestamp.isoformat()
                }
                for opp in opportunities
            ],
            "count": len(opportunities),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/database/portfolio/snapshots")
async def get_portfolio_snapshots(db: Session = Depends(get_db), limit: int = 100):
    """Get portfolio snapshots from database."""
    try:
        snapshots = db.query(PortfolioSnapshot).order_by(PortfolioSnapshot.timestamp.desc()).limit(limit).all()
        
        return {
            "snapshots": [
                {
                    "id": str(snap.id),
                    "total_value": float(snap.total_value),
                    "usd_balance": float(snap.usd_balance),
                    "daily_pnl": float(snap.daily_pnl) if snap.daily_pnl else 0,
                    "total_pnl": float(snap.total_pnl) if snap.total_pnl else 0,
                    "max_drawdown": float(snap.max_drawdown) if snap.max_drawdown else 0,
                    "sharpe_ratio": float(snap.sharpe_ratio) if snap.sharpe_ratio else 0,
                    "total_trades": snap.total_trades,
                    "win_rate": float(snap.win_rate) if snap.win_rate else 0,
                    "timestamp": snap.timestamp.isoformat()
                }
                for snap in snapshots
            ],
            "count": len(snapshots),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Database management endpoints
@app.post("/database/initialize")
async def initialize_database():
    """Initialize database tables."""
    try:
        db_manager.create_tables()
        
        return {
            "message": "Database initialized successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/database/status")
async def get_database_status():
    """Get database connection status."""
    try:
        # Test database connection
        db = db_manager.get_session()
        db.execute("SELECT 1")
        db_manager.close_session(db)
        
        return {
            "status": "connected",
            "message": "Database connection healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


# WebSocket endpoint for real-time updates (placeholder)
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time data."""
    await websocket.accept()
    try:
        while True:
            # Send periodic updates
            bot = get_bot()
            status = await bot.get_status()
            
            await websocket.send_json({
                "type": "status_update",
                "data": status,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await asyncio.sleep(5)  # Update every 5 seconds
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# Metrics endpoint
@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    try:
        metrics_data = await get_prometheus_metrics()
        return JSONResponse(
            content=metrics_data[0],
            headers=metrics_data[1]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@app.get("/analytics/performance")
async def get_performance_analytics(
    db: Session = Depends(get_db),
    days: int = 30
):
    """Get performance analytics for the specified period."""
    try:
        from datetime import timedelta
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get trade statistics
        trades = db.query(Trade).filter(Trade.timestamp >= start_date).all()
        
        if not trades:
            return {
                "performance": {
                    "total_trades": 0,
                    "total_profit": 0,
                    "avg_profit_per_trade": 0,
                    "win_rate": 0,
                    "best_trade": 0,
                    "worst_trade": 0
                },
                "period_days": days,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        total_profit = sum(float(t.profit_abs) for t in trades if t.profit_abs)
        profitable_trades = [t for t in trades if t.profit_abs and float(t.profit_abs) > 0]
        
        analytics = {
            "total_trades": len(trades),
            "total_profit": total_profit,
            "avg_profit_per_trade": total_profit / len(trades) if trades else 0,
            "win_rate": len(profitable_trades) / len(trades) if trades else 0,
            "best_trade": max((float(t.profit_abs) for t in trades if t.profit_abs), default=0),
            "worst_trade": min((float(t.profit_abs) for t in trades if t.profit_abs), default=0),
            "daily_breakdown": {}
        }
        
        # Daily breakdown
        from collections import defaultdict
        daily_profits = defaultdict(float)
        daily_counts = defaultdict(int)
        
        for trade in trades:
            day = trade.timestamp.date().isoformat()
            daily_profits[day] += float(trade.profit_abs) if trade.profit_abs else 0
            daily_counts[day] += 1
        
        analytics["daily_breakdown"] = {
            "profits": dict(daily_profits),
            "trade_counts": dict(daily_counts)
        }
        
        return {
            "performance": analytics,
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/symbols")
async def get_symbol_analytics(db: Session = Depends(get_db)):
    """Get analytics by trading symbol."""
    try:
        from sqlalchemy import func
        
        # Symbol performance
        symbol_stats = db.query(
            Trade.symbol,
            func.count(Trade.id).label('trade_count'),
            func.sum(Trade.profit_abs).label('total_profit'),
            func.avg(Trade.profit_abs).label('avg_profit')
        ).group_by(Trade.symbol).all()
        
        return {
            "symbol_performance": [
                {
                    "symbol": stat.symbol,
                    "trade_count": stat.trade_count,
                    "total_profit": float(stat.total_profit) if stat.total_profit else 0,
                    "avg_profit": float(stat.avg_profit) if stat.avg_profit else 0
                }
                for stat in symbol_stats
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/exchanges")
async def get_exchange_analytics(db: Session = Depends(get_db)):
    """Get analytics by exchange pair."""
    try:
        from sqlalchemy import func
        
        # Exchange pair performance
        exchange_stats = db.query(
            Trade.buy_exchange,
            Trade.sell_exchange,
            func.count(Trade.id).label('trade_count'),
            func.sum(Trade.profit_abs).label('total_profit')
        ).group_by(Trade.buy_exchange, Trade.sell_exchange).all()
        
        return {
            "exchange_performance": [
                {
                    "buy_exchange": stat.buy_exchange,
                    "sell_exchange": stat.sell_exchange,
                    "trade_count": stat.trade_count,
                    "total_profit": float(stat.total_profit) if stat.total_profit else 0
                }
                for stat in exchange_stats
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.debug,
        workers=1  # Single worker for development
    )
