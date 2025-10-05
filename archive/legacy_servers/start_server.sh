#!/bin/bash

# Start the FastAPI server with proper environment

set -e

echo "🚀 Starting FastAPI Server..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables if .env exists
if [ -f ".env" ]; then
    echo "📝 Loading environment from .env file"
    export $(grep -v '^#' .env | xargs)
fi

# Start the server
echo "🌐 Server starting at http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python fastapi_server_simple.py