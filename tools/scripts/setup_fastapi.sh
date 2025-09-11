#!/bin/bash

# Setup script for FastAPI server with all dependencies
# Run this script to set up the development environment

set -e  # Exit on any error

echo "🚀 Setting up FastAPI server environment..."

# Navigate to the project root directory
cd "$(dirname "$0")/../.."

# Check if we're in the right directory
if [ ! -f "fastapi_server_complete.py" ]; then
    echo "❌ Error: Cannot find project root directory"
    echo "Expected to find fastapi_server_complete.py in project root"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv_fastapi" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv_fastapi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv_fastapi/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing FastAPI dependencies..."
pip install -r requirements_fastapi.txt

echo "✅ Dependencies installed successfully!"

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker is available"
    
    # Ask if user wants to start services
    read -p "🤔 Do you want to start MySQL and Redis with Docker? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting MySQL and Redis containers..."
        docker-compose up -d mysql-db redis-cache
        
        # Wait for services to be ready
        echo "⏳ Waiting for services to be ready..."
        sleep 10
        
        # Test MySQL connection
        echo "🔍 Testing MySQL connection..."
        docker-compose exec mysql-db mysqladmin ping -h localhost -u root -pDown2earth! || echo "⚠️ MySQL not ready yet"
        
        # Test Redis connection
        echo "🔍 Testing Redis connection..."
        docker-compose exec redis-cache redis-cli ping || echo "⚠️ Redis not ready yet"
    fi
else
    echo "⚠️ Docker not found. You'll need to set up MySQL and Redis manually"
    echo "📋 Manual setup instructions:"
    echo "   - Install MySQL 8.0 and create database 'mystocks'"
    echo "   - Install Redis server"
    echo "   - Update connection settings in .env file"
fi

# Create .env file from example
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✏️ Please edit .env file with your actual configuration"
fi

# Test basic import
echo "🧪 Testing FastAPI import..."
python -c "
import sys
sys.path.append('.')
try:
    from fastapi import FastAPI
    print('✅ FastAPI imported successfully')
except ImportError as e:
    print(f'❌ FastAPI import failed: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 FastAPI environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with your database credentials"
echo "   2. Run migration: python tools/migrate_data.py"
echo "   3. Start the server: python fastapi_server_complete.py"
echo "   4. Run tests: python -m pytest test_fastapi.py"
echo ""
echo "🌐 Server will be available at: http://localhost:8000"
echo "📊 Health check: http://localhost:8000/health"
echo "📈 Metrics: http://localhost:8000/metrics"
echo "📚 API docs: http://localhost:8000/docs"