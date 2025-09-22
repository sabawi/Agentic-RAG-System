#!/bin/bash
"""
Server Logs CLI Demo Script
============================

Comprehensive demonstration of the server_logs CLI tool functionality.
Shows all commands, features, and persistent logging capabilities.
"""

echo "🚀 Server Logs Management CLI - Comprehensive Demo"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

demo_step() {
    echo -e "${BLUE}➤ $1${NC}"
    echo "Command: ${CYAN}$2${NC}"
    echo "----------------------------------------"
    eval $2
    echo ""
    sleep 2
}

echo -e "${YELLOW}This demo will show all server_logs CLI functionality${NC}"
echo -e "${YELLOW}Press Ctrl+C at any time to exit${NC}"
echo ""
read -p "Press Enter to start the demo..."
echo ""

# Step 1: Show help
demo_step "1. Display help information" "./server_logs help | head -30"

# Step 2: Check initial status
demo_step "2. Check current logging status" "./server_logs status"

# Step 3: Enable logging
demo_step "3. Enable logging" "./server_logs enable"

# Step 4: Set different log levels
demo_step "4. Set log level to INFO" "./server_logs level INFO"
demo_step "5. Set log level to WARNING" "./server_logs level WARNING"
demo_step "6. Set log level to DEBUG" "./server_logs level DEBUG"

# Step 5: Control specific logging features
demo_step "7. Turn ON request logging" "./server_logs requests on"
demo_step "8. Turn OFF timing logging" "./server_logs timing off"

# Step 6: Check status after changes
demo_step "9. Check status after changes" "./server_logs status"

# Step 7: Save current settings
demo_step "10. Save current settings as defaults" "./server_logs save"

# Step 8: Show saved configuration file
demo_step "11. View saved configuration file" "cat config/logging_config.json"

# Step 9: Disable logging
demo_step "12. Disable all logging" "./server_logs disable"

# Step 10: Restore from saved settings
demo_step "13. Restore persistent settings" "./server_logs restore"

# Step 11: Final status check
demo_step "14. Final status check" "./server_logs status"

# Step 12: Test invalid command
demo_step "15. Test error handling (invalid log level)" "./server_logs level INVALID"

echo ""
echo -e "${GREEN}🎉 Demo Complete!${NC}"
echo ""
echo -e "${YELLOW}Key Features Demonstrated:${NC}"
echo "✅ Real-time logging control"
echo "✅ Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
echo "✅ Granular control (requests, timing)"
echo "✅ Persistent settings across restarts"
echo "✅ Comprehensive status reporting"
echo "✅ Error handling and validation"
echo "✅ Colorized terminal output"
echo "✅ Intuitive command interface"
echo ""
echo -e "${CYAN}Configuration saved to: config/logging_config.json${NC}"
echo -e "${CYAN}Use './server_logs help' for full command reference${NC}"
echo ""
echo -e "${YELLOW}Quick Commands:${NC}"
echo "  ./server_logs status          # Check current status"
echo "  ./server_logs enable          # Enable logging"
echo "  ./server_logs level DEBUG     # Set debug level"
echo "  ./server_logs save            # Save current settings"
echo "  ./server_logs monitor         # Live log monitoring"
echo ""