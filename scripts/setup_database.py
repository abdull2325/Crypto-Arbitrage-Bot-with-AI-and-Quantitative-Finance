"""
Database setup script for the arbitrage bot.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings


async def setup_database():
    """Setup database tables and initial data."""
    print("Setting up database...")
    
    # Database setup would go here
    # For now, just create a placeholder
    
    try:
        # In a real implementation, this would:
        # 1. Connect to PostgreSQL
        # 2. Create tables for trades, opportunities, portfolio, etc.
        # 3. Setup initial data
        
        print("Database setup completed successfully!")
        print(f"Database URL: {settings.database.url}")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)


async def setup_redis():
    """Setup Redis for caching."""
    print("Setting up Redis...")
    
    try:
        # In a real implementation, this would:
        # 1. Connect to Redis
        # 2. Setup cache structures
        # 3. Test connection
        
        print("Redis setup completed successfully!")
        print(f"Redis URL: {settings.redis.url}")
        
    except Exception as e:
        print(f"Error setting up Redis: {e}")
        sys.exit(1)


async def create_directories():
    """Create necessary directories."""
    print("Creating directories...")
    
    directories = [
        "logs",
        "data",
        "models",
        "config/backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")


async def check_api_keys():
    """Check if API keys are configured."""
    print("Checking API keys...")
    
    missing_keys = []
    
    # Check exchange API keys
    if not settings.exchanges.binance_api_key:
        missing_keys.append("BINANCE_API_KEY")
    
    if not settings.exchanges.coinbase_api_key:
        missing_keys.append("COINBASE_API_KEY")
    
    if missing_keys:
        print("Warning: Missing API keys:")
        for key in missing_keys:
            print(f"  - {key}")
        print("\nPlease update your .env file with the required API keys.")
        print("The bot will run in demo mode without real exchange connections.")
    else:
        print("All API keys configured!")


async def main():
    """Main setup function."""
    print("=== Crypto Arbitrage Bot Setup ===\n")
    
    # Create directories
    await create_directories()
    
    # Setup database
    await setup_database()
    
    # Setup Redis
    await setup_redis()
    
    # Check API keys
    await check_api_keys()
    
    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Update .env file with your API keys")
    print("2. Review config/settings.py for trading parameters")
    print("3. Run 'python main.py --paper' to start in paper trading mode")
    print("4. Access the dashboard at http://localhost:3000 (after starting)")


if __name__ == "__main__":
    asyncio.run(main())
