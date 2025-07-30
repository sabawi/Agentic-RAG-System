#!/bin/bash

# Start FastAPI complete server in background with logging
cd "$(dirname "$0")"

# Check if server is already running
if pgrep -f "python3 fastapi_server_complete.py" > /dev/null; then
    echo "❌ Server is already running!"
    echo "Use './stop_complete.sh' to stop it first."
    exit 1
fi

echo "🚀 Starting FastAPI Complete Server..."

# Activate virtual environment and start server
source venv_fastapi/bin/activate
nohup python3 fastapi_server_complete.py > server_complete.log 2>&1 &

# Get the PID
SERVER_PID=$!
echo $SERVER_PID > server_complete.pid

echo "✅ Server started with PID: $SERVER_PID"
echo "📋 Logs: tail -f server_complete.log"
echo "🛑 Stop: ./stop_complete.sh"
echo "🌐 Server: http://localhost:5000"
echo "📚 API Docs: http://localhost:5000/docs"

# Wait a moment and check if it started successfully
sleep 3
if ps -p $SERVER_PID > /dev/null; then
    echo "🎯 Server is running successfully!"
    echo ""
    echo "📊 To monitor logs in real-time:"
    echo "   tail -f server_complete.log"
else
    echo "❌ Server failed to start. Check server_complete.log for details."
    echo "Last 10 lines of log:"
    tail -10 server_complete.log 2>/dev/null || echo "No log file found"
fi