"""
Main entry point for the crypto arbitrage bot.
"""
import asyncio
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.core.bot import ArbitrageBot
from config.settings import settings


async def main():
    """Main function to run the arbitrage bot."""
    parser = argparse.ArgumentParser(description='Crypto Arbitrage Bot')
    parser.add_argument('--paper', action='store_true', 
                       help='Run in paper trading mode')
    parser.add_argument('--live', action='store_true', 
                       help='Run in live trading mode')
    parser.add_argument('--api-only', action='store_true',
                       help='Run only the API server')
    
    args = parser.parse_args()
    
    # Determine trading mode
    if args.live:
        paper_trading = False
        print("Starting in LIVE TRADING mode")
        print("WARNING: This will use real money!")
        
        # Confirmation for live trading
        confirm = input("Are you sure you want to proceed with live trading? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return
    else:
        paper_trading = True
        print("Starting in PAPER TRADING mode")
    
    # Initialize bot
    bot = ArbitrageBot(paper_trading=paper_trading)
    
    try:
        if args.api_only:
            print("Starting API server only...")
            # Start API server
            import uvicorn
            uvicorn.run(
                "src.api.main:app",
                host=settings.api.host,
                port=settings.api.port,
                reload=settings.debug
            )
        else:
            print("Starting arbitrage bot...")
            # Start the bot
            await bot.start()
    
    except KeyboardInterrupt:
        print("\nShutdown signal received...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Stopping bot...")
        await bot.stop()
        print("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
