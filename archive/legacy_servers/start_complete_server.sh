#!/bin/bash

# Start the complete FastAPI server with Ollama integration

set -e

echo "🚀 Starting Complete FastAPI Server with Ollama Integration..."

# Check if we're in the right directory
if [ ! -f "fastapi_server_complete.py" ]; then
    echo "❌ Error: Please run this script from the flaskserver directory"
    exit 1
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Run ./setup_fastapi.sh first"
    exit 1
fi

source venv/bin/activate

# Check if Ollama is running
echo "🔍 Checking Ollama service..."
if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama service is running"
else
    echo "⚠️ Ollama service not detected"
    echo "💡 To start Ollama service:"
    echo "   ollama serve"
    echo ""
    echo "💡 To install a model:"
    echo "   ollama pull llama3.2:3b"
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set environment variables if .env exists
if [ -f ".env" ]; then
    echo "📝 Loading environment from .env file"
    export $(grep -v '^#' .env | xargs)
fi

# Start the server
echo ""
echo "🌐 Server starting at http://localhost:5000"
echo "📚 API Documentation: http://localhost:5000/docs"
echo "🏥 Health Check: http://localhost:5000/health"
echo "🧠 Ollama Models: http://localhost:5000/ollama/models"
echo "📊 Metrics: http://localhost:5000/metrics"
echo ""
echo "🔧 Key Endpoints:"
echo "   POST /llama3_1b/prompt - Simple Ollama prompts"
echo "   POST /llama3_1b/stream - Streaming with tools"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 fastapi_server_complete.py