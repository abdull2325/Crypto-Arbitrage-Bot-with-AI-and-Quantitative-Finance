"""
Database models and ORM setup for the arbitrage bot.
"""
from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer, Boolean, JSON, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from config.settings import settings

Base = declarative_base()


class Trade(Base):
    """Trade model for storing executed trades."""
    __tablename__ = 'trades'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(String(255))
    symbol = Column(String(50), nullable=False)
    buy_exchange = Column(String(50), nullable=False)
    sell_exchange = Column(String(50), nullable=False)
    buy_price = Column(DECIMAL(20, 8), nullable=False)
    sell_price = Column(DECIMAL(20, 8), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False)
    profit_abs = Column(DECIMAL(20, 8))
    profit_pct = Column(DECIMAL(10, 6))
    fees = Column(DECIMAL(20, 8))
    slippage = Column(DECIMAL(10, 6))
    execution_time = Column(DECIMAL(10, 3))
    status = Column(String(20), default='pending')
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Opportunity(Base):
    """Opportunity model for storing detected arbitrage opportunities."""
    __tablename__ = 'opportunities'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(50), nullable=False)
    buy_exchange = Column(String(50), nullable=False)
    sell_exchange = Column(String(50), nullable=False)
    buy_price = Column(DECIMAL(20, 8), nullable=False)
    sell_price = Column(DECIMAL(20, 8), nullable=False)
    profit_abs = Column(DECIMAL(20, 8))
    profit_pct = Column(DECIMAL(10, 6))
    confidence_score = Column(DECIMAL(5, 4))
    volume_available = Column(DECIMAL(20, 8))
    strategy = Column(String(50))
    detected_at = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime)
    executed = Column(Boolean, default=False)


class PortfolioSnapshot(Base):
    """Portfolio snapshot model for tracking portfolio state over time."""
    __tablename__ = 'portfolio_snapshots'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    total_value = Column(DECIMAL(20, 8), nullable=False)
    usd_balance = Column(DECIMAL(20, 8), nullable=False)
    positions = Column(JSON)
    daily_pnl = Column(DECIMAL(20, 8))
    total_pnl = Column(DECIMAL(20, 8))
    max_drawdown = Column(DECIMAL(10, 6))
    sharpe_ratio = Column(DECIMAL(10, 6))
    total_trades = Column(Integer, default=0)
    win_rate = Column(DECIMAL(5, 2))
    timestamp = Column(DateTime, default=datetime.utcnow)


class RiskEvent(Base):
    """Risk event model for storing risk management events."""
    __tablename__ = 'risk_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text)
    details = Column(JSON)
    portfolio_value = Column(DECIMAL(20, 8))
    action_taken = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)


class MarketData(Base):
    """Market data model for storing historical market data."""
    __tablename__ = 'market_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    data_type = Column(String(20), nullable=False)  # 'ticker', 'orderbook', 'trades'
    data = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class MLPerformance(Base):
    """ML performance model for tracking model performance."""
    __tablename__ = 'ml_performance'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    accuracy = Column(DECIMAL(5, 4))
    precision_score = Column(DECIMAL(5, 4))
    recall = Column(DECIMAL(5, 4))
    f1_score = Column(DECIMAL(5, 4))
    predictions_made = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    training_date = Column(DateTime)
    evaluation_date = Column(DateTime, default=datetime.utcnow)


class BotStatus(Base):
    """Bot status model for tracking bot operational state."""
    __tablename__ = 'bot_status'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False)  # 'running', 'stopped', 'error'
    paper_trading = Column(Boolean, default=True)
    active_exchanges = Column(JSON)
    active_symbols = Column(JSON)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)
    uptime_seconds = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Database connection and session management
class DatabaseManager:
    """Database manager for handling connections and sessions."""
    
    def __init__(self):
        """Initialize database manager."""
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine."""
        try:
            self.engine = create_engine(
                settings.database.url,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.max_overflow,
                echo=settings.database.echo
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            print("Database engine initialized successfully")
            
        except Exception as e:
            print(f"Error initializing database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise
    
    def get_session(self):
        """Get database session."""
        try:
            session = self.SessionLocal()
            return session
        except Exception as e:
            print(f"Error getting database session: {e}")
            raise
    
    def close_session(self, session):
        """Close database session."""
        try:
            session.close()
        except Exception as e:
            print(f"Error closing database session: {e}")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI
def get_db():
    """Database dependency for FastAPI."""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db_manager.close_session(db)
