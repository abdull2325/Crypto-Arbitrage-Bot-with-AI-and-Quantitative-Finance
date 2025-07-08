"""
Metrics collection and Prometheus integration for the arbitrage bot.
"""
import time
from typing import Dict, List
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime

# Define Prometheus metrics
# Trading metrics
trades_total = Counter('arbitrage_trades_total', 'Total number of trades executed', ['exchange', 'symbol', 'status'])
profit_total = Counter('arbitrage_profit_total', 'Total profit in USD', ['exchange', 'symbol'])
fees_total = Counter('arbitrage_fees_total', 'Total fees paid in USD', ['exchange', 'symbol'])

# Execution metrics
execution_time = Histogram('arbitrage_execution_time_seconds', 'Trade execution time in seconds')
api_response_time = Histogram('arbitrage_api_response_time_seconds', 'API response time in seconds', ['exchange', 'endpoint'])

# Portfolio metrics
portfolio_value = Gauge('arbitrage_portfolio_value_usd', 'Current portfolio value in USD')
portfolio_pnl_daily = Gauge('arbitrage_portfolio_pnl_daily_usd', 'Daily P&L in USD')
portfolio_drawdown = Gauge('arbitrage_portfolio_drawdown_pct', 'Current drawdown percentage')
portfolio_sharpe_ratio = Gauge('arbitrage_portfolio_sharpe_ratio', 'Current Sharpe ratio')

# Opportunity metrics
opportunities_detected = Counter('arbitrage_opportunities_detected_total', 'Total opportunities detected', ['symbol', 'strategy'])
opportunities_executed = Counter('arbitrage_opportunities_executed_total', 'Total opportunities executed', ['symbol', 'strategy'])
opportunity_profit_pct = Histogram('arbitrage_opportunity_profit_pct', 'Opportunity profit percentage', ['symbol'])

# Risk metrics
risk_events = Counter('arbitrage_risk_events_total', 'Total risk events', ['event_type', 'severity'])
position_risk = Gauge('arbitrage_position_risk_pct', 'Current position risk percentage')
var_95 = Gauge('arbitrage_var_95_usd', 'Value at Risk 95% confidence in USD')

# System metrics
bot_uptime = Gauge('arbitrage_bot_uptime_seconds', 'Bot uptime in seconds')
data_updates = Counter('arbitrage_data_updates_total', 'Total data updates received', ['exchange', 'data_type'])
api_errors = Counter('arbitrage_api_errors_total', 'Total API errors', ['exchange', 'error_type'])

# ML metrics
ml_predictions = Counter('arbitrage_ml_predictions_total', 'Total ML predictions made', ['model_name'])
ml_accuracy = Gauge('arbitrage_ml_accuracy', 'Current ML model accuracy', ['model_name'])
ml_confidence = Histogram('arbitrage_ml_confidence', 'ML prediction confidence scores', ['model_name'])


class MetricsCollector:
    """Metrics collector for the arbitrage bot."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.start_time = time.time()
        self.last_update = time.time()
    
    def record_trade(self, trade_data: Dict):
        """Record a trade execution."""
        try:
            exchange = f"{trade_data.get('buy_exchange', '')}-{trade_data.get('sell_exchange', '')}"
            symbol = trade_data.get('symbol', '')
            status = 'success' if trade_data.get('success', False) else 'failed'
            
            trades_total.labels(exchange=exchange, symbol=symbol, status=status).inc()
            
            if trade_data.get('success', False):
                profit = trade_data.get('profit', 0)
                fees = trade_data.get('fees', 0)
                exec_time = trade_data.get('execution_time', 0)
                
                profit_total.labels(exchange=exchange, symbol=symbol).inc(profit)
                fees_total.labels(exchange=exchange, symbol=symbol).inc(fees)
                execution_time.observe(exec_time)
                
        except Exception as e:
            print(f"Error recording trade metrics: {e}")
    
    def record_opportunity(self, opportunity_data: Dict):
        """Record an opportunity detection."""
        try:
            symbol = opportunity_data.get('symbol', '')
            strategy = opportunity_data.get('strategy', 'unknown')
            profit_pct = opportunity_data.get('profit_pct', 0)
            
            opportunities_detected.labels(symbol=symbol, strategy=strategy).inc()
            opportunity_profit_pct.labels(symbol=symbol).observe(profit_pct)
            
        except Exception as e:
            print(f"Error recording opportunity metrics: {e}")
    
    def record_opportunity_execution(self, opportunity_data: Dict):
        """Record an opportunity execution."""
        try:
            symbol = opportunity_data.get('symbol', '')
            strategy = opportunity_data.get('strategy', 'unknown')
            
            opportunities_executed.labels(symbol=symbol, strategy=strategy).inc()
            
        except Exception as e:
            print(f"Error recording opportunity execution metrics: {e}")
    
    def update_portfolio_metrics(self, portfolio_data: Dict):
        """Update portfolio metrics."""
        try:
            portfolio_value.set(portfolio_data.get('total_value', 0))
            portfolio_pnl_daily.set(portfolio_data.get('daily_pnl', 0))
            portfolio_drawdown.set(portfolio_data.get('max_drawdown_pct', 0))
            portfolio_sharpe_ratio.set(portfolio_data.get('sharpe_ratio', 0))
            
        except Exception as e:
            print(f"Error updating portfolio metrics: {e}")
    
    def update_risk_metrics(self, risk_data: Dict):
        """Update risk metrics."""
        try:
            position_risk.set(risk_data.get('position_risk_pct', 0))
            var_95.set(risk_data.get('var_95', 0))
            
        except Exception as e:
            print(f"Error updating risk metrics: {e}")
    
    def record_risk_event(self, event_type: str, severity: str):
        """Record a risk event."""
        try:
            risk_events.labels(event_type=event_type, severity=severity).inc()
        except Exception as e:
            print(f"Error recording risk event: {e}")
    
    def record_api_call(self, exchange: str, endpoint: str, response_time: float, error: str = None):
        """Record an API call."""
        try:
            api_response_time.labels(exchange=exchange, endpoint=endpoint).observe(response_time)
            
            if error:
                api_errors.labels(exchange=exchange, error_type=error).inc()
                
        except Exception as e:
            print(f"Error recording API call metrics: {e}")
    
    def record_data_update(self, exchange: str, data_type: str):
        """Record a data update."""
        try:
            data_updates.labels(exchange=exchange, data_type=data_type).inc()
        except Exception as e:
            print(f"Error recording data update: {e}")
    
    def record_ml_prediction(self, model_name: str, confidence: float, accuracy: float = None):
        """Record ML prediction."""
        try:
            ml_predictions.labels(model_name=model_name).inc()
            ml_confidence.labels(model_name=model_name).observe(confidence)
            
            if accuracy is not None:
                ml_accuracy.labels(model_name=model_name).set(accuracy)
                
        except Exception as e:
            print(f"Error recording ML prediction: {e}")
    
    def update_system_metrics(self):
        """Update system-level metrics."""
        try:
            current_time = time.time()
            uptime = current_time - self.start_time
            bot_uptime.set(uptime)
            
            self.last_update = current_time
            
        except Exception as e:
            print(f"Error updating system metrics: {e}")
    
    def get_metrics_summary(self) -> Dict:
        """Get a summary of current metrics."""
        try:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            return {
                'uptime_seconds': uptime,
                'last_update': self.last_update,
                'metrics_enabled': True
            }
        except Exception as e:
            print(f"Error getting metrics summary: {e}")
            return {'error': str(e)}
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        try:
            self.update_system_metrics()
            return generate_latest()
        except Exception as e:
            print(f"Error exporting metrics: {e}")
            return f"# Error exporting metrics: {e}\n"


# Global metrics collector instance
metrics_collector = MetricsCollector()


# FastAPI endpoint function
async def get_prometheus_metrics():
    """FastAPI endpoint to return Prometheus metrics."""
    metrics_data = metrics_collector.export_metrics()
    return metrics_data, {'Content-Type': CONTENT_TYPE_LATEST}
