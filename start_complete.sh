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
    
    # TESTING MODE: DISABLED - Phase 2B features cause infinite streaming loops
    # echo "🧪 TESTING MODE: Enabling all Phase 2B features..."
    # sleep 2  # Give server time to fully initialize
    
    # # Clear any emergency fallback first
    # curl -s -X POST http://localhost:5000/phase2b/rollback/clear-emergency > /dev/null 2>&1
    
    # # Enable all Phase 2B features
    # echo "  🔄 Enabling response_classification..."
    # curl -s -X POST http://localhost:5000/phase2b/feature/response_classification/enable > /dev/null 2>&1
    
    # echo "  🔄 Enabling buffer_optimization..." 
    # curl -s -X POST http://localhost:5000/phase2b/feature/buffer_optimization/enable > /dev/null 2>&1
    
    # echo "  🔄 Enabling streaming_fallback..."
    # curl -s -X POST http://localhost:5000/phase2b/feature/streaming_fallback/enable > /dev/null 2>&1
    
    # # Verify features are enabled
    # STATUS=$(curl -s http://localhost:5000/phase2b/status 2>/dev/null)
    # if echo "$STATUS" | grep -q '"success":true'; then
    #     echo "  ✅ All Phase 2B features enabled successfully!"
    #     echo "  📊 Active features: response_classification, buffer_optimization, streaming_fallback"
    # else
    #     echo "  ⚠️  Feature enablement may have issues - check server logs"
    # fi
    
    echo "🚨 Phase 2B features DISABLED due to infinite streaming bug"
    echo "   Server running in Phase 2A safe mode only"
    echo ""
    
    echo "📊 To monitor logs in real-time:"
    echo "   tail -f server_complete.log"
    echo ""
    echo "💡 To disable testing mode, comment out the Phase 2B auto-enable section in start_complete.sh"
else
    echo "❌ Server failed to start. Check server_complete.log for details."
    echo "Last 10 lines of log:"
    tail -10 server_complete.log 2>/dev/null || echo "No log file found"
fi