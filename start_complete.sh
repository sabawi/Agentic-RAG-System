#!/bin/bash

# 🚀 FastAPI Complete Server Startup Script
# Enhanced with optimizations, API-controllable features, and streamlined logging
cd "$(dirname "$0")"

# Check if server is already running
if pgrep -f "python3 fastapi_server_complete.py" > /dev/null; then
    echo "❌ Server is already running!"
    echo "Use './stop_complete.sh' to stop it first."
    exit 1
fi

echo "🚀 Starting FastAPI Complete Server with Optimizations..."

# Activate virtual environment and start server
source venv/bin/activate

# 🎯 DEFAULT OPTIMIZATIONS ENABLED
# These optimizations are enabled by default for production performance
ENV_VARS=""

# ⚡ PERFORMANCE OPTIMIZATIONS (ENABLED BY DEFAULT)
ENV_VARS="$ENV_VARS USE_DIRECT_FUNCTION_CALLS=true"       # 50x faster response initiation
ENV_VARS="$ENV_VARS PARALLEL_TOOL_EXECUTION=true"         # Concurrent tool execution
ENV_VARS="$ENV_VARS STRING_OPTIMIZATION=true"             # O(n) string concatenation
ENV_VARS="$ENV_VARS META_TASK_BYPASS=true"                # Skip tools for title/tag generation

# 🧹 STREAMLINED LOGGING (ENABLED BY DEFAULT)  
ENV_VARS="$ENV_VARS CONCISE_LOGGING=true"                 # Summary-based logging vs full dumps
ENV_VARS="$ENV_VARS BUFFER_SIZE_LOGGING=true"             # Log data sizes instead of content

# 🔧 API-CONTROLLABLE FEATURES (Configure via HTTP calls after startup)
# Examples:
#   curl -X POST http://localhost:5000/admin/logging/enable           # Enable logging
#   curl -X POST http://localhost:5000/admin/logging/disable          # Disable logging
#   curl -X POST http://localhost:5000/optimization/enable            # Enable optimizations
#   curl -X GET  http://localhost:5000/admin/logging/status           # View logging status

# Pass through any manual environment overrides
if [ ! -z "$LOG_REQUESTS" ]; then
    ENV_VARS="$ENV_VARS LOG_REQUESTS=$LOG_REQUESTS"
fi
if [ ! -z "$LOG_TIMING" ]; then
    ENV_VARS="$ENV_VARS LOG_TIMING=$LOG_TIMING"
fi
if [ ! -z "$DEBUG_MODE" ]; then
    ENV_VARS="$ENV_VARS DEBUG_MODE=$DEBUG_MODE"
fi

# Start server with optimized environment variables
echo "🔧 Starting server with optimizations: Performance ✅ Streamlined Logging ✅ API Control ✅"
nohup env $ENV_VARS python3 fastapi_server_complete.py > logs/server_complete.log 2>&1 &

# Get the PID
SERVER_PID=$!
echo $SERVER_PID > runtime/server_complete.pid

echo "✅ Server started with PID: $SERVER_PID"
echo "📋 Logs: tail -f logs/server_complete.log"
echo "🛑 Stop: ./stop_complete.sh"
echo "🌐 Server: http://localhost:5000"
echo "📚 API Docs: http://localhost:5000/docs"

# Wait a moment and check if it started successfully
sleep 3
if ps -p $SERVER_PID > /dev/null; then
    echo "🎯 Server is running successfully with optimizations!"

    # 🔄 RESTORE PERSISTENT LOGGING SETTINGS
    if [ -f "config/logging_config.json" ]; then
        echo "🔄 Restoring persistent logging settings..."
        sleep 2  # Give server time to fully initialize
        ./server_logs restore 2>/dev/null && echo "✅ Logging settings restored" || echo "⚠️  Logging restore skipped (server not ready)"
    fi
    echo ""
    
    # 🎛️ ADMIN API: Control server behavior
    echo "🎛️ ADMIN API CONTROLS:"
    echo ""
    echo "   📋 Check status:"
    echo "      curl -X GET http://localhost:5000/admin/logging/status           # Logging status"
    echo "      curl -X GET http://localhost:5000/optimization/status            # Optimization status"
    echo ""
    echo "   🔧 Logging controls:"
    echo "      curl -X POST http://localhost:5000/admin/logging/enable          # Enable logging"
    echo "      curl -X POST http://localhost:5000/admin/logging/disable         # Disable logging"
    echo "      curl -X POST http://localhost:5000/admin/logging/level/INFO      # Set log level (DEBUG/INFO/WARNING/ERROR)"
    echo "      curl -X POST http://localhost:5000/admin/logging/requests/toggle # Toggle request logging"
    echo "      curl -X POST http://localhost:5000/admin/logging/timing/toggle   # Toggle timing logs"
    echo ""
    echo "   ⚡ Optimization controls:"
    echo "      curl -X POST http://localhost:5000/optimization/enable           # Enable optimizations"
    echo "      curl -X POST http://localhost:5000/optimization/disable          # Disable optimizations"
    echo "      curl -X POST -H 'Content-Type: application/json' -d '{\"percentage\":50}' http://localhost:5000/optimization/rollout  # Set rollout %"
    echo "      curl -X POST http://localhost:5000/optimization/emergency-rollback  # Emergency rollback"
    echo ""
    
    echo "📊 Monitor logs in real-time:"
    echo "   tail -f logs/server_complete.log                    # All logs"
    echo "   tail -f logs/server_complete.log | grep -E 'TOOL.*:.*chars'  # Tool summaries only"
    echo "   tail -f logs/server_complete.log | grep -E '🎯.*chars'       # Context summaries only"
else
    echo "❌ Server failed to start. Check logs/server_complete.log for details."
    echo "Last 10 lines of log:"
    tail -10 logs/server_complete.log 2>/dev/null || echo "No log file found"
fi