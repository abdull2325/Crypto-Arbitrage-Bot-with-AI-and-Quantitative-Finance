-- Database initialization script for the arbitrage bot
-- This script creates the necessary tables and initial data

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id VARCHAR(255),
    symbol VARCHAR(50) NOT NULL,
    buy_exchange VARCHAR(50) NOT NULL,
    sell_exchange VARCHAR(50) NOT NULL,
    buy_price DECIMAL(20, 8) NOT NULL,
    sell_price DECIMAL(20, 8) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    profit_abs DECIMAL(20, 8),
    profit_pct DECIMAL(10, 6),
    fees DECIMAL(20, 8),
    slippage DECIMAL(10, 6),
    execution_time DECIMAL(10, 3),
    status VARCHAR(20) DEFAULT 'pending',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Opportunities table
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL,
    buy_exchange VARCHAR(50) NOT NULL,
    sell_exchange VARCHAR(50) NOT NULL,
    buy_price DECIMAL(20, 8) NOT NULL,
    sell_price DECIMAL(20, 8) NOT NULL,
    profit_abs DECIMAL(20, 8),
    profit_pct DECIMAL(10, 6),
    confidence_score DECIMAL(5, 4),
    volume_available DECIMAL(20, 8),
    strategy VARCHAR(50),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    expired_at TIMESTAMPTZ,
    executed BOOLEAN DEFAULT FALSE
);

-- Portfolio snapshots table
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    total_value DECIMAL(20, 8) NOT NULL,
    usd_balance DECIMAL(20, 8) NOT NULL,
    positions JSONB,
    daily_pnl DECIMAL(20, 8),
    total_pnl DECIMAL(20, 8),
    max_drawdown DECIMAL(10, 6),
    sharpe_ratio DECIMAL(10, 6),
    total_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5, 2),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Risk events table
CREATE TABLE IF NOT EXISTS risk_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    details JSONB,
    portfolio_value DECIMAL(20, 8),
    action_taken VARCHAR(100),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Market data table
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    data_type VARCHAR(20) NOT NULL, -- 'ticker', 'orderbook', 'trades'
    data JSONB NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- ML model performance table
CREATE TABLE IF NOT EXISTS ml_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    predictions_made INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    training_date TIMESTAMPTZ,
    evaluation_date TIMESTAMPTZ DEFAULT NOW()
);

-- Bot status table
CREATE TABLE IF NOT EXISTS bot_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status VARCHAR(20) NOT NULL, -- 'running', 'stopped', 'error'
    paper_trading BOOLEAN DEFAULT TRUE,
    active_exchanges TEXT[],
    active_symbols TEXT[],
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT,
    uptime_seconds INTEGER DEFAULT 0,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_opportunities_symbol ON opportunities(symbol);
CREATE INDEX IF NOT EXISTS idx_opportunities_detected_at ON opportunities(detected_at);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_timestamp ON portfolio_snapshots(timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_exchange_symbol ON market_data(exchange, symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial bot status
INSERT INTO bot_status (status, paper_trading, active_exchanges, active_symbols)
VALUES ('stopped', TRUE, ARRAY['binance', 'coinbase'], ARRAY['BTC/USDT', 'ETH/USDT'])
ON CONFLICT DO NOTHING;

-- Create a view for recent performance metrics
CREATE OR REPLACE VIEW recent_performance AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as trades_count,
    AVG(profit_pct) as avg_profit_pct,
    SUM(profit_abs) as total_profit,
    SUM(fees) as total_fees,
    AVG(execution_time) as avg_execution_time
FROM trades 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
AND status = 'completed'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- Create a view for opportunity statistics
CREATE OR REPLACE VIEW opportunity_stats AS
SELECT 
    symbol,
    COUNT(*) as opportunities_detected,
    AVG(profit_pct) as avg_profit_pct,
    MAX(profit_pct) as max_profit_pct,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN executed THEN 1 END) as executed_count
FROM opportunities 
WHERE detected_at >= NOW() - INTERVAL '7 days'
GROUP BY symbol
ORDER BY opportunities_detected DESC;

COMMIT;
