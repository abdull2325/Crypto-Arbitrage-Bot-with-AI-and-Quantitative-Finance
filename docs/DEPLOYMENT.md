# 🚀 Deployment Guide

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Docker (optional)

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required Settings:**
- Exchange API keys (Binance, Coinbase, etc.)
- Database connection string
- Redis connection string
- Trading parameters

### 3. Database Setup

```bash
# Run setup script
python scripts/setup_database.py

# Or manually setup PostgreSQL
createdb arbitrage_bot
```

### 4. Start the Bot

```bash
# Paper trading mode (recommended for testing)
python main.py --paper

# Live trading mode (use with caution!)
python main.py --live

# API server only
python main.py --api-only
```

### 5. Dashboard Setup

```bash
cd dashboard
npm install
npm run dev
```

Access dashboard at: http://localhost:3000

## Docker Deployment

### Quick Docker Setup

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

### Production Docker

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

## Cloud Deployment

### AWS Deployment

1. **EC2 Instance Setup:**
   ```bash
   # t3.large or larger recommended
   # Ubuntu 20.04 LTS
   sudo apt update && sudo apt install docker.io docker-compose
   ```

2. **RDS Database:**
   - Create PostgreSQL RDS instance
   - Update DATABASE_URL in .env

3. **ElastiCache Redis:**
   - Create Redis cluster
   - Update REDIS_URL in .env

4. **Deploy:**
   ```bash
   git clone <repository-url>
   cd bot
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Google Cloud Platform

1. **Cloud Run Deployment:**
   ```bash
   # Build and push image
   gcloud builds submit --tag gcr.io/PROJECT-ID/arbitrage-bot
   
   # Deploy to Cloud Run
   gcloud run deploy --image gcr.io/PROJECT-ID/arbitrage-bot --platform managed
   ```

2. **Cloud SQL:**
   - Create PostgreSQL instance
   - Configure connection

## Monitoring & Alerting

### Grafana Dashboard
- Access: http://localhost:3001
- Default login: admin/admin
- Pre-configured dashboards for bot metrics

### Prometheus Metrics
- Access: http://localhost:9090
- Metrics endpoint: http://localhost:8000/metrics

### Log Monitoring
```bash
# View real-time logs
tail -f logs/bot.log

# Search for errors
grep "ERROR" logs/bot.log
```

## Security Best Practices

### API Key Management
- Store API keys in environment variables
- Use separate keys for paper/live trading
- Rotate keys regularly
- Restrict IP access where possible

### Network Security
```bash
# Firewall configuration (Ubuntu)
sudo ufw allow 22    # SSH
sudo ufw allow 8000  # Bot API
sudo ufw allow 3000  # Dashboard
sudo ufw enable
```

### Database Security
- Use strong passwords
- Enable SSL connections
- Restrict database access
- Regular backups

## Performance Optimization

### Bot Performance
- Use SSD storage for logs/data
- Minimum 4GB RAM recommended
- Consider multiple exchange API keys for rate limiting
- Monitor latency metrics

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_opportunities_symbol ON opportunities(symbol);
```

### Redis Configuration
```redis
# Memory optimization
maxmemory 512mb
maxmemory-policy allkeys-lru
```

## Troubleshooting

### Common Issues

1. **Bot won't start:**
   ```bash
   # Check logs
   python main.py --paper 2>&1 | tee startup.log
   
   # Verify dependencies
   pip check
   ```

2. **API connection errors:**
   ```bash
   # Test exchange connectivity
   python -c "import ccxt; print(ccxt.exchanges)"
   
   # Verify API keys
   python scripts/test_exchanges.py
   ```

3. **Database connection:**
   ```bash
   # Test database connection
   python -c "
   from config.settings import settings
   print(settings.database.url)
   "
   ```

4. **Memory issues:**
   ```bash
   # Monitor memory usage
   htop
   
   # Clear Redis cache
   redis-cli flushall
   ```

### Performance Issues

1. **High latency:**
   - Check network connectivity
   - Monitor exchange API limits
   - Consider co-location near exchanges

2. **High CPU usage:**
   - Reduce analysis frequency
   - Optimize ML models
   - Use async operations

### Log Analysis

```bash
# Error analysis
grep -n "ERROR\|EXCEPTION" logs/bot.log | tail -20

# Performance metrics
grep "METRICS" logs/performance.log | tail -10

# Trade analysis
grep "TRADE" logs/trades.log | tail -20
```

## Backup & Recovery

### Database Backup
```bash
# Create backup
pg_dump arbitrage_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql arbitrage_bot < backup_file.sql
```

### Configuration Backup
```bash
# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env config/ models/
```

### Automated Backups
```bash
# Add to crontab
0 2 * * * /path/to/backup_script.sh
```

## Scaling

### Horizontal Scaling
- Run multiple bot instances with different trading pairs
- Use load balancer for API endpoints
- Separate ML training from trading execution

### Vertical Scaling
- Increase instance size for better performance
- Add more CPU cores for parallel processing
- Increase memory for larger datasets

## Support

### Health Checks
- Bot status: http://localhost:8000/health
- Database: Connection test in admin panel
- Redis: redis-cli ping

### Monitoring Endpoints
- `/bot/status` - Bot operational status
- `/portfolio/metrics` - Portfolio performance
- `/risk/status` - Risk management status
- `/trading/metrics` - Trading statistics

### Emergency Procedures

1. **Emergency Stop:**
   ```bash
   curl -X POST http://localhost:8000/risk/emergency_stop
   ```

2. **Close All Positions:**
   ```bash
   curl -X POST http://localhost:8000/trading/close_all
   ```

3. **Manual Intervention:**
   - Access exchange websites directly
   - Close positions manually if needed
   - Contact exchange support if required

For additional support, check the documentation or open an issue in the repository.
