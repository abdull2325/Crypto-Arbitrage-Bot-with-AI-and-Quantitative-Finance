#!/bin/bash

# Comprehensive setup script for Crypto Arbitrage Bot
# This script handles all the final integration and setup steps

set -e  # Exit on any error

echo "🚀 Starting Crypto Arbitrage Bot Complete Setup..."

# Function to print colored output
print_step() {
    echo -e "\n\033[1;34m==== $1 ====\033[0m"
}

print_success() {
    echo -e "\033[1;32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m❌ $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

# Check if Python is installed
print_step "Checking Python Installation"
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python $python_version found"

# Check if Node.js is installed
print_step "Checking Node.js Installation"
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

node_version=$(node --version)
print_success "Node.js $node_version found"

# Create Python virtual environment
print_step "Setting Up Python Environment"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Python dependencies
print_step "Installing Python Dependencies"
pip install -r requirements.txt
print_success "Python dependencies installed"

# Create .env file if it doesn't exist
print_step "Setting Up Environment Configuration"
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success ".env file created from template"
    print_warning "Please edit .env file with your actual configuration before running the bot"
else
    print_warning ".env file already exists"
fi

# Create necessary directories
print_step "Creating Directory Structure"
mkdir -p logs data models monitoring/grafana/dashboards
print_success "Directory structure created"

# Set up database (PostgreSQL)
print_step "Database Setup"
echo "Checking PostgreSQL connection..."

# Check if PostgreSQL is running
if command -v pg_isready &> /dev/null; then
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        print_success "PostgreSQL is running"
        
        # Run database initialization
        echo "Initializing database..."
        python scripts/setup_database.py
        print_success "Database initialized"
    else
        print_warning "PostgreSQL is not running. Please start PostgreSQL service."
        print_warning "On macOS: brew services start postgresql"
        print_warning "On Ubuntu: sudo systemctl start postgresql"
    fi
else
    print_warning "PostgreSQL not found. Installing via Docker is recommended."
fi

# Setup Redis (check if running)
print_step "Redis Setup"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        print_success "Redis is running"
    else
        print_warning "Redis is not running. Please start Redis service."
        print_warning "On macOS: brew services start redis"
        print_warning "On Ubuntu: sudo systemctl start redis"
    fi
else
    print_warning "Redis not found. Installing via Docker is recommended."
fi

# Set up frontend dashboard
print_step "Setting Up Frontend Dashboard"
cd dashboard

# Install Node.js dependencies
if [ ! -d "node_modules" ]; then
    npm install
    print_success "Dashboard dependencies installed"
else
    print_warning "Dashboard dependencies already installed"
fi

# Build the dashboard
npm run build
print_success "Dashboard built successfully"

cd ..

# Docker setup
print_step "Docker Configuration"
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        print_success "Docker is running"
        
        # Build Docker images
        echo "Building Docker images..."
        docker build -t arbitrage-bot:latest .
        docker build -t arbitrage-dashboard:latest ./dashboard/
        print_success "Docker images built"
        
        print_warning "You can now run: docker-compose up -d"
    else
        print_warning "Docker daemon is not running"
    fi
else
    print_warning "Docker not installed. Manual setup required."
fi

# Create systemd service (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_step "Creating Systemd Service (Optional)"
    cat > arbitrage-bot.service << EOF
[Unit]
Description=Crypto Arbitrage Bot
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py --paper
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    print_success "Systemd service file created (arbitrage-bot.service)"
    print_warning "To install: sudo cp arbitrage-bot.service /etc/systemd/system/"
    print_warning "To enable: sudo systemctl enable arbitrage-bot"
fi

# Test installation
print_step "Testing Installation"
echo "Running basic import tests..."

python3 -c "
import sys
sys.path.append('.')
try:
    from src.core.bot import ArbitrageBot
    from src.api.main import app
    from config.settings import settings
    print('✅ Core imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

print_success "Installation test passed"

# Final setup summary
print_step "Setup Complete!"
echo ""
echo "🎉 Crypto Arbitrage Bot setup is complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit .env file with your actual configuration"
echo "2. Ensure PostgreSQL and Redis are running"
echo "3. Start the bot:"
echo "   • Paper trading: python main.py --paper"
echo "   • API only: python main.py --api-only"
echo "   • Full Docker stack: docker-compose up -d"
echo ""
echo "📊 Access Points:"
echo "   • Dashboard: http://localhost:3000"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Grafana: http://localhost:3001 (admin/admin)"
echo "   • Prometheus: http://localhost:9090"
echo ""
echo "📖 Documentation:"
echo "   • README.md - General usage"
echo "   • docs/DEPLOYMENT.md - Deployment guide"
echo ""
echo "⚠️  Important Notes:"
echo "   • This is for educational purposes only"
echo "   • Start with paper trading mode"
echo "   • Test thoroughly before live trading"
echo "   • Monitor risk management settings"
echo ""
print_success "Happy trading! 🚀"
