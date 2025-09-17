#!/bin/bash

# Monitor server logs
cd "$(dirname "$0")"

LOG_FILE="logs/server_complete.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "💡 Make sure the server is running with './start_complete.sh'"
    exit 1
fi

echo "📋 Monitoring logs from: $LOG_FILE"
echo "📊 Press Ctrl+C to stop monitoring"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Follow the log file
tail -f "$LOG_FILE"