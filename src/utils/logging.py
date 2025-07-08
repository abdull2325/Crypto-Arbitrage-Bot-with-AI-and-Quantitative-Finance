"""
Logging configuration and utilities for the arbitrage bot.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime

from config.settings import settings


def setup_logging():
    """Setup logging configuration."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.logging.level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.logging.file_path,
        maxBytes=settings.logging.max_file_size,
        backupCount=settings.logging.backup_count
    )
    file_handler.setLevel(getattr(logging, settings.logging.level.upper()))
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename="logs/error.log",
        maxBytes=settings.logging.max_file_size,
        backupCount=settings.logging.backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    logger.addHandler(error_handler)
    
    # Log startup
    logger.info("Logging system initialized")
    logger.info(f"Log level: {settings.logging.level}")
    logger.info(f"Log file: {settings.logging.file_path}")


def get_logger(name: str):
    """Get a logger with the specified name."""
    return logging.getLogger(name)


class TradeLogger:
    """Specialized logger for trade events."""
    
    def __init__(self):
        """Initialize trade logger."""
        self.logger = logging.getLogger("trade")
        
        # Create trade-specific log file
        trade_handler = logging.handlers.RotatingFileHandler(
            filename="logs/trades.log",
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        
        trade_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        trade_handler.setFormatter(trade_format)
        self.logger.addHandler(trade_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_opportunity(self, opportunity: dict):
        """Log an arbitrage opportunity."""
        self.logger.info(f"OPPORTUNITY: {opportunity}")
    
    def log_trade_execution(self, trade_result: dict):
        """Log trade execution result."""
        if trade_result.get('success'):
            self.logger.info(f"TRADE_SUCCESS: {trade_result}")
        else:
            self.logger.warning(f"TRADE_FAILED: {trade_result}")
    
    def log_risk_event(self, event: dict):
        """Log risk management event."""
        self.logger.warning(f"RISK_EVENT: {event}")


class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self):
        """Initialize performance logger."""
        self.logger = logging.getLogger("performance")
        
        # Create performance log file
        perf_handler = logging.handlers.RotatingFileHandler(
            filename="logs/performance.log",
            maxBytes=5242880,  # 5MB
            backupCount=5
        )
        
        perf_format = logging.Formatter(
            '%(asctime)s - %(message)s'
        )
        perf_handler.setFormatter(perf_format)
        self.logger.addHandler(perf_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_metrics(self, metrics: dict):
        """Log performance metrics."""
        self.logger.info(f"METRICS: {metrics}")
    
    def log_latency(self, operation: str, latency_ms: float):
        """Log operation latency."""
        self.logger.info(f"LATENCY: {operation}={latency_ms:.2f}ms")


# Global logger instances
trade_logger = TradeLogger()
performance_logger = PerformanceLogger()
