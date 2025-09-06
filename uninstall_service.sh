#!/bin/bash
# Agentic-RAG Server Service Uninstaller
# This script removes the systemd service

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="agentic-rag-server"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo -e "${BLUE}🗑️  Agentic-RAG Server Service Uninstaller${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Please do not run this script as root${NC}"
    echo -e "${YELLOW}💡 Run as regular user: ./uninstall_service.sh${NC}"
    exit 1
fi

# Check if service file exists
if [ ! -f "${SERVICE_FILE}" ]; then
    echo -e "${YELLOW}⚠️  Service file not found: ${SERVICE_FILE}${NC}"
    echo -e "${BLUE}Service may already be uninstalled.${NC}"
    exit 0
fi

echo -e "${BLUE}🔍 Found service: ${SERVICE_NAME}${NC}"

# Check service status
if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo -e "${YELLOW}⚠️  Service is currently running${NC}"
    echo -e "${BLUE}🛑 Stopping service...${NC}"
    sudo systemctl stop ${SERVICE_NAME}
    echo -e "${GREEN}✅ Service stopped${NC}"
fi

# Disable the service
if sudo systemctl is-enabled --quiet ${SERVICE_NAME}; then
    echo -e "${BLUE}⚡ Disabling service...${NC}"
    sudo systemctl disable ${SERVICE_NAME}
    echo -e "${GREEN}✅ Service disabled${NC}"
fi

# Remove service file
echo -e "${BLUE}🗑️  Removing service file...${NC}"
sudo rm -f ${SERVICE_FILE}

# Reload systemd daemon
echo -e "${BLUE}🔄 Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload

# Reset failed state if any
sudo systemctl reset-failed ${SERVICE_NAME} 2>/dev/null || true

echo -e "${GREEN}✅ Service uninstallation complete!${NC}"
echo ""
echo -e "${BLUE}📋 The following commands are no longer available:${NC}"
echo -e "${YELLOW}sudo systemctl start ${SERVICE_NAME}${NC}"
echo -e "${YELLOW}sudo systemctl stop ${SERVICE_NAME}${NC}"
echo -e "${YELLOW}sudo systemctl restart ${SERVICE_NAME}${NC}"
echo -e "${YELLOW}sudo systemctl status ${SERVICE_NAME}${NC}"
echo -e "${YELLOW}sudo journalctl -u ${SERVICE_NAME}${NC}"
echo ""
echo -e "${BLUE}💡 You can still run the server manually with:${NC}"
echo -e "${YELLOW}./start_complete.sh${NC}"
echo ""
echo -e "${GREEN}🎉 Uninstallation complete!${NC}"