#!/bin/bash
# Agentic-RAG Server Service Installer
# This script installs the server as a systemd service

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
CURRENT_DIR="$(pwd)"
CURRENT_USER="$(whoami)"
CURRENT_GROUP="$(id -gn)"

echo -e "${BLUE}🚀 Agentic-RAG Server Service Installer${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Please do not run this script as root${NC}"
    echo -e "${YELLOW}💡 Run as regular user: ./install_service.sh${NC}"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "fastapi_server_complete.py" ]; then
    echo -e "${RED}❌ Error: fastapi_server_complete.py not found${NC}"
    echo -e "${YELLOW}💡 Please run this script from the Agentic-RAG server directory${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Error: Virtual environment 'venv' not found${NC}"
    echo -e "${YELLOW}💡 Please create virtual environment first:${NC}"
    echo -e "${YELLOW}   python3 -m venv venv${NC}"
    echo -e "${YELLOW}   source venv/bin/activate${NC}"
    echo -e "${YELLOW}   pip install -r requirements.txt${NC}"
    exit 1
fi

# Check if dependencies are installed
echo -e "${BLUE}🔍 Checking dependencies...${NC}"
if ! ./venv/bin/python tests/test_dependencies.py > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Dependencies not properly installed${NC}"
    echo -e "${YELLOW}💡 Please install dependencies first:${NC}"
    echo -e "${YELLOW}   source venv/bin/activate${NC}"
    echo -e "${YELLOW}   pip install -r requirements.txt${NC}"
    echo -e "${YELLOW}   python tests/test_dependencies.py${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dependencies check passed${NC}"

# Create systemd service file
echo -e "${BLUE}📝 Creating systemd service file...${NC}"

cat > /tmp/${SERVICE_NAME}.service << EOF
[Unit]
Description=Agentic-RAG Server - AI-powered multi-LLM orchestration server
Documentation=file://${CURRENT_DIR}/README.md
After=network.target ollama.service
Wants=ollama.service
Requires=network.target

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_GROUP}
WorkingDirectory=${CURRENT_DIR}
Environment=PATH=${CURRENT_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=VIRTUAL_ENV=${CURRENT_DIR}/venv
Environment=PYTHONPATH=${CURRENT_DIR}
EnvironmentFile=-${CURRENT_DIR}/.env

# Main command
ExecStart=${CURRENT_DIR}/venv/bin/python fastapi_server_complete.py

# Restart configuration
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Process management
KillMode=mixed
KillSignal=SIGINT
TimeoutStartSec=60
TimeoutStopSec=30

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${CURRENT_DIR}
ReadWritePaths=/tmp

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Logging - all output goes to systemd journal
StandardOutput=journal
StandardError=journal
SyslogIdentifier=agentic-rag-server

[Install]
WantedBy=multi-user.target
EOF

# Install the service file
echo -e "${BLUE}🔧 Installing service file...${NC}"
sudo cp /tmp/${SERVICE_NAME}.service ${SERVICE_FILE}
sudo rm /tmp/${SERVICE_NAME}.service

# Set proper permissions
sudo chmod 644 ${SERVICE_FILE}

# Reload systemd daemon
echo -e "${BLUE}🔄 Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload

# Enable the service
echo -e "${BLUE}⚡ Enabling service...${NC}"
sudo systemctl enable ${SERVICE_NAME}

echo -e "${GREEN}✅ Service installation complete!${NC}"
echo ""
echo -e "${BLUE}📋 Service Management Commands:${NC}"
echo -e "${YELLOW}Start:    ${NC}sudo systemctl start ${SERVICE_NAME}"
echo -e "${YELLOW}Stop:     ${NC}sudo systemctl stop ${SERVICE_NAME}"
echo -e "${YELLOW}Restart:  ${NC}sudo systemctl restart ${SERVICE_NAME}"
echo -e "${YELLOW}Status:   ${NC}sudo systemctl status ${SERVICE_NAME}"
echo -e "${YELLOW}Logs:     ${NC}sudo journalctl -u ${SERVICE_NAME} -f"
echo -e "${YELLOW}Disable:  ${NC}sudo systemctl disable ${SERVICE_NAME}"
echo ""

# Ask user if they want to start the service now
echo -e "${BLUE}🚀 Would you like to start the service now? [y/N]${NC}"
read -r response
case "$response" in
    [yY][eE][sS]|[yY]) 
        echo -e "${BLUE}🔄 Starting service...${NC}"
        
        # Stop any existing manual processes first
        if pgrep -f "fastapi_server_complete.py" > /dev/null; then
            echo -e "${YELLOW}⚠️  Stopping existing manual server process...${NC}"
            pkill -f "fastapi_server_complete.py" || true
            sleep 2
        fi
        
        sudo systemctl start ${SERVICE_NAME}
        
        # Check if service started successfully
        sleep 3
        if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
            echo -e "${GREEN}✅ Service started successfully!${NC}"
            echo -e "${BLUE}📊 Service status:${NC}"
            sudo systemctl status ${SERVICE_NAME} --no-pager -l
            echo ""
            echo -e "${BLUE}🔍 View logs with:${NC}"
            echo -e "${YELLOW}sudo journalctl -u ${SERVICE_NAME} -f${NC}"
        else
            echo -e "${RED}❌ Service failed to start${NC}"
            echo -e "${YELLOW}🔍 Check logs with:${NC}"
            echo -e "${YELLOW}sudo journalctl -u ${SERVICE_NAME} -n 20${NC}"
            exit 1
        fi
        ;;
    *)
        echo -e "${YELLOW}⏭️  Service installed but not started${NC}"
        echo -e "${BLUE}Start manually with: ${YELLOW}sudo systemctl start ${SERVICE_NAME}${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo -e "${BLUE}The Agentic-RAG server is now configured as a system service.${NC}"