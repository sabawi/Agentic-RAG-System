#!/bin/bash

# Check server status
cd "$(dirname "$0")"

echo "🔍 FastAPI Complete Server Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if PID file exists
if [ -f "server_complete.pid" ]; then
    SERVER_PID=$(cat server_complete.pid)
    echo "📄 PID file found: $SERVER_PID"
    
    # Check if process is actually running
    if ps -p $SERVER_PID > /dev/null; then
        echo "✅ Server is running (PID: $SERVER_PID)"
        
        # Get process info
        echo "📊 Process info:"
        ps -p $SERVER_PID -o pid,ppid,cmd,%cpu,%mem,etime
        
        # Test server health
        echo ""
        echo "🏥 Testing server health..."
        if curl -s http://localhost:5000/health > /dev/null; then
            echo "✅ Server is responding at http://localhost:5000"
        else
            echo "❌ Server not responding at http://localhost:5000"
        fi
        
    else
        echo "❌ PID file exists but process is not running"
        echo "🧹 Cleaning up stale PID file..."
        rm -f server_complete.pid
    fi
else
    echo "📄 No PID file found"
    
    # Check for any running processes
    PIDS=$(pgrep -f "python3 fastapi_server_complete.py")
    if [ ! -z "$PIDS" ]; then
        echo "⚠️  Found running server processes without PID file:"
        ps -p $PIDS -o pid,ppid,cmd,%cpu,%mem,etime
    else
        echo "ℹ️  No server processes found"
    fi
fi

echo ""
echo "📋 Log file status:"
if [ -f "server_complete.log" ]; then
    LOG_SIZE=$(stat -c%s "server_complete.log")
    LOG_LINES=$(wc -l < "server_complete.log")
    echo "✅ Log file exists: server_complete.log ($LOG_SIZE bytes, $LOG_LINES lines)"
    echo "📝 Last 3 log entries:"
    tail -3 "server_complete.log" 2>/dev/null || echo "   (empty log)"
else
    echo "❌ No log file found: server_complete.log"
fi

echo ""
echo "🛠️  Available commands:"
echo "   ./start_complete.sh  - Start the server"
echo "   ./stop_complete.sh   - Stop the server"
echo "   ./logs.sh           - Monitor logs"
echo "   ./status.sh         - Show this status"