#!/bin/bash

# Automated setup script for the Crypto Arbitrage Bot
# This script will set up the entire development environment

set -e  # Exit on any error

echo "🚀 Setting up Crypto Arbitrage Bot..."
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_step "Checking prerequisites..."

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | grep -oE '[0-9]+\.[0-9]+')
    if [ "$(echo "$PYTHON_VERSION >= 3.9" | bc)" -eq 1 ] 2>/dev/null; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.9+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version | grep -oE '[0-9]+')
    if [ "$NODE_VERSION" -ge 16 ]; then
        print_success "Node.js v$NODE_VERSION found"
    else
        print_warning "Node.js 16+ recommended, found v$NODE_VERSION"
    fi
else
    print_warning "Node.js not found. Dashboard won't be available."
fi

# Check npm
if command_exists npm; then
    print_success "npm found"
else
    print_warning "npm not found. Dashboard won't be available."
fi

# Check Docker (optional)
if command_exists docker; then
    print_success "Docker found"
    DOCKER_AVAILABLE=true
else
    print_warning "Docker not found. Manual setup required."
    DOCKER_AVAILABLE=false
fi

# Ask for setup type
echo ""
echo "Choose setup type:"
echo "1) Quick setup (Docker - recommended)"
echo "2) Manual setup"
echo "3) Development setup"
read -p "Enter choice [1-3]: " SETUP_TYPE

case $SETUP_TYPE in
    1)
        if [ "$DOCKER_AVAILABLE" = false ]; then
            print_error "Docker not available. Please choose manual setup."
            exit 1
        fi
        ;;
    2|3)
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Create directory structure
print_step "Creating directory structure..."
mkdir -p logs data models config/backups
print_success "Directories created"

# Setup environment file
print_step "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Environment file created (.env)"
    print_warning "Please edit .env file with your API keys and settings"
else
    print_warning ".env file already exists, skipping..."
fi

if [ "$SETUP_TYPE" = "1" ]; then
    # Docker setup
    print_step "Setting up with Docker..."
    
    # Check docker-compose
    if command_exists docker-compose; then
        COMPOSE_CMD="docker-compose"
    elif command_exists docker && docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose not found"
        exit 1
    fi
    
    print_step "Building Docker images..."
    $COMPOSE_CMD build
    
    print_step "Starting services..."
    $COMPOSE_CMD up -d postgres redis
    
    # Wait for services to be ready
    print_step "Waiting for services to start..."
    sleep 10
    
    print_step "Running database setup..."
    $COMPOSE_CMD run --rm bot python scripts/setup_database.py
    
    print_step "Starting bot and dashboard..."
    $COMPOSE_CMD up -d
    
    print_success "Docker setup complete!"
    echo ""
    echo "🌐 Services running at:"
    echo "  • Bot API: http://localhost:8000"
    echo "  • Dashboard: http://localhost:3000"
    echo "  • Grafana: http://localhost:3001 (admin/admin)"
    echo ""
    echo "📋 Useful commands:"
    echo "  • View logs: $COMPOSE_CMD logs -f bot"
    echo "  • Stop services: $COMPOSE_CMD down"
    echo "  • Restart bot: $COMPOSE_CMD restart bot"

else
    # Manual setup
    print_step "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    print_step "Activating virtual environment..."
    source venv/bin/activate
    
    print_step "Installing Python dependencies..."
    pip install -r requirements.txt
    print_success "Python dependencies installed"
    
    # Setup database (if PostgreSQL is available)
    if command_exists psql; then
        print_step "Setting up database..."
        python scripts/setup_database.py
        print_success "Database setup complete"
    else
        print_warning "PostgreSQL not found. Please install and configure manually."
    fi
    
    # Setup dashboard (if Node.js is available)
    if [ "$NODE_VERSION" -ge 16 ] && command_exists npm; then
        print_step "Setting up dashboard..."
        cd dashboard
        npm install
        print_success "Dashboard dependencies installed"
        cd ..
    else
        print_warning "Skipping dashboard setup (Node.js/npm not available)"
    fi
    
    print_success "Manual setup complete!"
    echo ""
    echo "🚀 To start the bot:"
    echo "  source venv/bin/activate"
    echo "  python main.py --paper"
    echo ""
    if command_exists npm; then
        echo "🌐 To start the dashboard:"
        echo "  cd dashboard && npm run dev"
        echo ""
    fi
fi

# Development setup additions
if [ "$SETUP_TYPE" = "3" ]; then
    print_step "Setting up development tools..."
    
    # Install development dependencies
    pip install pytest black flake8 mypy pre-commit
    
    # Setup pre-commit hooks
    pre-commit install
    
    print_success "Development tools installed"
    
    echo ""
    echo "🛠️ Development commands:"
    echo "  • Run tests: pytest"
    echo "  • Format code: black ."
    echo "  • Lint code: flake8 ."
    echo "  • Type check: mypy ."
fi

# Final instructions
echo ""
print_step "Setup Summary"
echo "============="
echo ""

if [ ! -f .env ] || grep -q "your_" .env; then
    print_warning "Important: Configure your .env file with:"
    echo "  • Exchange API keys"
    echo "  • Database connection"
    echo "  • Trading parameters"
    echo ""
fi

echo "📚 Documentation:"
echo "  • README.md - Getting started guide"
echo "  • docs/DEPLOYMENT.md - Deployment instructions"
echo "  • config/settings.py - Configuration options"
echo ""

echo "🔒 Security reminders:"
echo "  • Start with paper trading mode"
echo "  • Use separate API keys for testing"
echo "  • Monitor your trades regularly"
echo "  • Set appropriate risk limits"
echo ""

print_success "Setup complete! Happy trading! 🎉"

# Ask if user wants to start the bot now
if [ "$SETUP_TYPE" != "1" ]; then
    echo ""
    read -p "Start the bot in paper trading mode now? [y/N]: " START_NOW
    if [[ $START_NOW =~ ^[Yy]$ ]]; then
        print_step "Starting bot in paper trading mode..."
        source venv/bin/activate
        python main.py --paper
    fi
fi
