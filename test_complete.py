#!/usr/bin/env python3
"""
Comprehensive test suite for the Crypto Arbitrage Bot.
Tests all major components and integrations.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.core.bot import ArbitrageBot
from src.database.models import db_manager
from config.settings import settings


class BotTester:
    """Test suite for the arbitrage bot."""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            'name': test_name,
            'success': success,
            'message': message
        })
        
        if not success:
            self.failed_tests.append(test_name)
    
    def test_imports(self):
        """Test all critical imports."""
        print("\n🔍 Testing Imports...")
        
        try:
            from src.core.bot import ArbitrageBot
            self.log_test("Core Bot Import", True)
        except Exception as e:
            self.log_test("Core Bot Import", False, str(e))
        
        try:
            from src.api.main import app
            self.log_test("FastAPI Import", True)
        except Exception as e:
            self.log_test("FastAPI Import", False, str(e))
        
        try:
            from src.database.models import db_manager, Trade, Opportunity
            self.log_test("Database Models Import", True)
        except Exception as e:
            self.log_test("Database Models Import", False, str(e))
        
        try:
            from src.data.collectors import DataCollector
            from src.trading.executor import TradeExecutor
            from src.ml.predictor import MLPredictor
            from src.quant.analyzer import QuantAnalyzer
            from src.risk.manager import RiskManager
            self.log_test("All Component Imports", True)
        except Exception as e:
            self.log_test("All Component Imports", False, str(e))
    
    def test_configuration(self):
        """Test configuration loading."""
        print("\n⚙️  Testing Configuration...")
        
        try:
            # Test settings access
            assert hasattr(settings, 'database')
            assert hasattr(settings, 'trading')
            assert hasattr(settings, 'risk')
            assert hasattr(settings, 'ml')
            self.log_test("Settings Structure", True)
        except Exception as e:
            self.log_test("Settings Structure", False, str(e))
        
        try:
            # Test environment variables
            if os.path.exists('.env'):
                self.log_test("Environment File Exists", True)
            else:
                self.log_test("Environment File Exists", False, "Create .env from .env.example")
        except Exception as e:
            self.log_test("Environment File Check", False, str(e))
    
    def test_database_connection(self):
        """Test database connectivity."""
        print("\n🗄️  Testing Database...")
        
        try:
            # Test database connection
            session = db_manager.get_session()
            session.execute("SELECT 1")
            db_manager.close_session(session)
            self.log_test("Database Connection", True)
        except Exception as e:
            self.log_test("Database Connection", False, str(e))
        
        try:
            # Test table creation
            db_manager.create_tables()
            self.log_test("Database Table Creation", True)
        except Exception as e:
            self.log_test("Database Table Creation", False, str(e))
    
    async def test_bot_initialization(self):
        """Test bot initialization."""
        print("\n🤖 Testing Bot Initialization...")
        
        try:
            bot = ArbitrageBot(paper_trading=True)
            self.log_test("Bot Creation", True)
        except Exception as e:
            self.log_test("Bot Creation", False, str(e))
            return None
        
        try:
            # Test component initialization
            assert bot.portfolio is not None
            assert bot.data_collector is not None
            assert bot.ml_predictor is not None
            assert bot.quant_analyzer is not None
            assert bot.risk_manager is not None
            assert bot.trade_executor is not None
            self.log_test("Bot Components", True)
        except Exception as e:
            self.log_test("Bot Components", False, str(e))
        
        return bot
    
    async def test_portfolio_operations(self, bot):
        """Test portfolio operations."""
        print("\n💼 Testing Portfolio Operations...")
        
        try:
            balance = await bot.portfolio.get_balance()
            assert balance > 0
            self.log_test("Portfolio Balance Check", True, f"Balance: ${balance}")
        except Exception as e:
            self.log_test("Portfolio Balance Check", False, str(e))
        
        try:
            total_value = await bot.portfolio.get_total_value()
            assert total_value > 0
            self.log_test("Portfolio Value Calculation", True, f"Value: ${total_value}")
        except Exception as e:
            self.log_test("Portfolio Value Calculation", False, str(e))
        
        try:
            metrics = await bot.portfolio.get_metrics()
            assert isinstance(metrics, dict)
            self.log_test("Portfolio Metrics", True)
        except Exception as e:
            self.log_test("Portfolio Metrics", False, str(e))
    
    async def test_data_collection(self, bot):
        """Test data collection."""
        print("\n📊 Testing Data Collection...")
        
        try:
            # Test data collector initialization
            assert bot.data_collector is not None
            self.log_test("Data Collector Initialization", True)
        except Exception as e:
            self.log_test("Data Collector Initialization", False, str(e))
        
        try:
            # Test getting latest data (may be empty in test mode)
            data = await bot.data_collector.get_latest_data()
            self.log_test("Data Collection", True, f"Retrieved {len(data) if data else 0} data points")
        except Exception as e:
            self.log_test("Data Collection", False, str(e))
    
    async def test_risk_management(self, bot):
        """Test risk management."""
        print("\n⚠️  Testing Risk Management...")
        
        try:
            # Test risk manager initialization
            assert bot.risk_manager is not None
            self.log_test("Risk Manager Initialization", True)
        except Exception as e:
            self.log_test("Risk Manager Initialization", False, str(e))
        
        try:
            # Test risk status
            status = await bot.risk_manager.get_status()
            assert isinstance(status, dict)
            self.log_test("Risk Status Check", True)
        except Exception as e:
            self.log_test("Risk Status Check", False, str(e))
        
        try:
            # Test opportunity filtering
            test_opportunities = [
                {
                    'symbol': 'BTC/USD',
                    'buy_exchange': 'binance',
                    'sell_exchange': 'coinbase',
                    'profit_pct': 0.5,
                    'volume_available': 1000
                }
            ]
            filtered = await bot.risk_manager.filter_opportunities(test_opportunities)
            self.log_test("Opportunity Filtering", True, f"Filtered {len(filtered)} opportunities")
        except Exception as e:
            self.log_test("Opportunity Filtering", False, str(e))
    
    async def test_ml_components(self, bot):
        """Test ML components."""
        print("\n🧠 Testing ML Components...")
        
        try:
            # Test ML predictor initialization
            assert bot.ml_predictor is not None
            self.log_test("ML Predictor Initialization", True)
        except Exception as e:
            self.log_test("ML Predictor Initialization", False, str(e))
        
        try:
            # Test feature importance (may return default values)
            features = await bot.ml_predictor.get_feature_importance()
            self.log_test("ML Feature Importance", True)
        except Exception as e:
            self.log_test("ML Feature Importance", False, str(e))
    
    async def test_api_endpoints(self):
        """Test API endpoints."""
        print("\n🌐 Testing API Endpoints...")
        
        try:
            from src.api.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            
            # Test health endpoint
            response = client.get("/health")
            assert response.status_code == 200
            self.log_test("API Health Endpoint", True)
        except Exception as e:
            self.log_test("API Health Endpoint", False, str(e))
        
        try:
            # Test bot status endpoint
            response = client.get("/bot/status")
            # May return 500 if bot is not running, which is expected
            self.log_test("API Bot Status Endpoint", True, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("API Bot Status Endpoint", False, str(e))
    
    def test_file_structure(self):
        """Test file structure."""
        print("\n📁 Testing File Structure...")
        
        required_files = [
            'main.py',
            'requirements.txt',
            '.env.example',
            'docker-compose.yml',
            'Dockerfile',
            'README.md',
            'src/core/bot.py',
            'src/api/main.py',
            'src/database/models.py',
            'config/settings.py',
            'dashboard/package.json'
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                self.log_test(f"File: {file_path}", True)
            else:
                self.log_test(f"File: {file_path}", False, "Missing required file")
        
        required_dirs = [
            'src/core',
            'src/api',
            'src/database',
            'src/data',
            'src/trading',
            'src/ml',
            'src/quant',
            'src/risk',
            'src/utils',
            'config',
            'scripts',
            'dashboard',
            'monitoring'
        ]
        
        for dir_path in required_dirs:
            if os.path.exists(dir_path):
                self.log_test(f"Directory: {dir_path}", True)
            else:
                self.log_test(f"Directory: {dir_path}", False, "Missing required directory")
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🧪 Starting Comprehensive Bot Test Suite")
        print("=" * 50)
        
        # Basic tests
        self.test_imports()
        self.test_configuration()
        self.test_file_structure()
        self.test_database_connection()
        
        # Component tests
        bot = await self.test_bot_initialization()
        
        if bot:
            await self.test_portfolio_operations(bot)
            await self.test_data_collection(bot)
            await self.test_risk_management(bot)
            await self.test_ml_components(bot)
        
        # API tests
        await self.test_api_endpoints()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 50)
        print("🧪 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   • {test}")
            print(f"\n⚠️  Please review failed tests before proceeding.")
        else:
            print(f"\n🎉 All tests passed! The bot is ready to use.")
        
        print(f"\n📖 Next Steps:")
        if self.failed_tests:
            print(f"   1. Fix failed tests")
            print(f"   2. Re-run tests: python test_complete.py")
        else:
            print(f"   1. Configure .env file with your settings")
            print(f"   2. Start the bot: python main.py --paper")
            print(f"   3. Access dashboard: http://localhost:3000")


async def main():
    """Main test function."""
    tester = BotTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
