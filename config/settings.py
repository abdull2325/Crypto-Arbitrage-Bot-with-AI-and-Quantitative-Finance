"""
Main configuration module for the arbitrage bot.
Handles all environment variables and settings.
"""
from typing import List, Optional
from pydantic import BaseSettings, Field
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    url: str = Field(default="postgresql://postgres:password@localhost:5432/arbitrage_bot")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    echo: bool = Field(default=False)

    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    url: str = Field(default="redis://localhost:6379/0")
    password: Optional[str] = Field(default=None)
    decode_responses: bool = Field(default=True)

    class Config:
        env_prefix = "REDIS_"


class ExchangeSettings(BaseSettings):
    """Exchange API configuration."""
    
    # Binance
    binance_api_key: Optional[str] = Field(default=None)
    binance_secret_key: Optional[str] = Field(default=None)
    binance_sandbox: bool = Field(default=True)
    
    # Coinbase
    coinbase_api_key: Optional[str] = Field(default=None)
    coinbase_secret_key: Optional[str] = Field(default=None)
    coinbase_passphrase: Optional[str] = Field(default=None)
    coinbase_sandbox: bool = Field(default=True)
    
    # Kraken
    kraken_api_key: Optional[str] = Field(default=None)
    kraken_secret_key: Optional[str] = Field(default=None)
    
    # Bitfinex
    bitfinex_api_key: Optional[str] = Field(default=None)
    bitfinex_secret_key: Optional[str] = Field(default=None)

    class Config:
        env_file = ".env"


class TradingSettings(BaseSettings):
    """Trading configuration settings."""
    paper_trading: bool = Field(default=True)
    initial_balance_usd: float = Field(default=10000.0)
    max_position_size: float = Field(default=0.1)
    min_profit_threshold: float = Field(default=0.002)
    max_slippage: float = Field(default=0.001)
    
    # Supported trading pairs
    trading_pairs: List[str] = Field(default=[
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", 
        "SOL/USDT", "XRP/USDT", "DOT/USDT", "AVAX/USDT"
    ])
    
    # Supported exchanges
    supported_exchanges: List[str] = Field(default=[
        "binance", "coinbase", "kraken", "bitfinex"
    ])

    class Config:
        env_prefix = "TRADING_"


class RiskSettings(BaseSettings):
    """Risk management settings."""
    max_daily_loss: float = Field(default=500.0)
    max_position_risk: float = Field(default=0.05)
    stop_loss_percentage: float = Field(default=0.02)
    circuit_breaker_threshold: float = Field(default=0.1)
    max_drawdown_threshold: float = Field(default=0.15)
    var_confidence_level: float = Field(default=0.95)

    class Config:
        env_prefix = "RISK_"


class MLSettings(BaseSettings):
    """Machine learning model settings."""
    model_retrain_interval: int = Field(default=24)  # hours
    feature_window_size: int = Field(default=100)
    prediction_threshold: float = Field(default=0.7)
    model_path: str = Field(default="models/")
    
    # Feature engineering
    technical_indicators: List[str] = Field(default=[
        "rsi", "macd", "bollinger_bands", "sma", "ema", "volume_profile"
    ])
    
    # Model types
    models: List[str] = Field(default=[
        "xgboost", "random_forest", "lstm", "transformer"
    ])

    class Config:
        env_prefix = "ML_"


class APISettings(BaseSettings):
    """API server settings."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)
    reload: bool = Field(default=False)
    
    # Security
    secret_key: str = Field(default="your-secret-key-here")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    class Config:
        env_prefix = "API_"


class MonitoringSettings(BaseSettings):
    """Monitoring and alerting settings."""
    prometheus_port: int = Field(default=8001)
    grafana_port: int = Field(default=3001)
    
    # Notification settings
    discord_webhook_url: Optional[str] = Field(default=None)
    slack_webhook_url: Optional[str] = Field(default=None)
    email_smtp_server: Optional[str] = Field(default=None)
    email_username: Optional[str] = Field(default=None)
    email_password: Optional[str] = Field(default=None)

    class Config:
        env_prefix = "MONITORING_"


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_path: str = Field(default="logs/bot.log")
    max_file_size: int = Field(default=10485760)  # 10MB
    backup_count: int = Field(default=5)

    class Config:
        env_prefix = "LOG_"


class Settings(BaseSettings):
    """Main settings class that combines all configuration."""
    
    debug: bool = Field(default=True)
    
    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    exchanges: ExchangeSettings = ExchangeSettings()
    trading: TradingSettings = TradingSettings()
    risk: RiskSettings = RiskSettings()
    ml: MLSettings = MLSettings()
    api: APISettings = APISettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    logging: LoggingSettings = LoggingSettings()
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
