#!/bin/bash

# =============================================================================
# Agentic RAG System - Comprehensive Installation, Verification & Upgrade Script
# =============================================================================
# 
# Usage:
#   ./install.sh                    - Fresh installation
#   ./install.sh upgrade            - Pull latest changes from GitHub (interactive)
#   ./install.sh upgrade --auto-safe      - Auto upgrade with safe mode (preserves databases)
#   ./install.sh upgrade --auto-stash     - Auto upgrade with stash mode (preserves all changes)
#   ./install.sh verify             - Verify existing installation
#   ./install.sh --dry-run          - Show what would be done without executing
#
# Repository: https://github.com/sabawi/Agentic-RAG-System
# =============================================================================

set -e  # Exit on any error

# Script configuration
SCRIPT_VERSION="1.1.0"
REPO_URL="https://github.com/sabawi/Agentic-RAG-System.git"
REQUIRED_PYTHON_VERSION="3.8"
DRY_RUN=false
UPGRADE_MODE=false
VERIFY_MODE=false
AUTO_UPGRADE=false  # For non-interactive upgrades
UPGRADE_STRATEGY=""  # "safe" or "stash" for automated upgrades

# Required Ollama models
REQUIRED_MODELS=("qwen3:8b" "qwen2.5vl:3b" "bakllava:latest")

# System dependencies
SYSTEM_DEPS=("tesseract-ocr" "wkhtmltopdf" "build-essential" "python3-dev" "python3-venv" "curl" "git")

# Version tracking
FROM_VERSION=""
TO_VERSION=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Version management functions
get_current_version() {
    # Use centralized version system from version.py (authoritative source)
    if [ -f "version.py" ]; then
        python3 -c "import sys; sys.path.append('.'); from version import VERSION; print(VERSION)" 2>/dev/null || {
            # Fallback to old VERSION file if version.py import fails
            if [ -f "VERSION" ]; then
                cat VERSION | tr -d '\n\r'
            else
                echo "unknown"
            fi
        }
    elif [ -f "VERSION" ]; then
        # Legacy fallback for older installations
        cat VERSION | tr -d '\n\r'
    else
        echo "unknown"
    fi
}

show_upgrade_summary() {
    if [ "$UPGRADE_MODE" = true ] && [ -n "$FROM_VERSION" ] && [ -n "$TO_VERSION" ]; then
        echo ""
        log_header "Upgrade Summary"
        echo -e "${GREEN}🎉 Successfully upgraded from version ${CYAN}${FROM_VERSION}${GREEN} to ${CYAN}${TO_VERSION}${GREEN}${NC}"
        
        # Show what changed based on version comparison
        if [ "$FROM_VERSION" != "$TO_VERSION" ]; then
            echo -e "${BLUE}📋 Changes may include new features, bug fixes, and improvements${NC}"
        else
            echo -e "${YELLOW}⚠️  Same version detected - dependencies and configuration updated${NC}"
        fi
        echo ""
    fi
}

log_header() {
    echo -e "\n${CYAN}============================================${NC}"
    echo -e "${CYAN} $1${NC}"
    echo -e "${CYAN}============================================${NC}\n"
}

# Check if running in dry-run mode
execute_command() {
    local cmd="$1"
    local description="$2"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN] Would execute: $description${NC}"
        echo -e "${YELLOW}          Command: $cmd${NC}"
    else
        log_step "$description"
        eval "$cmd"
    fi
}

# Parse command line arguments
parse_arguments() {
    for arg in "$@"; do
        case $arg in
            upgrade)
                UPGRADE_MODE=true
                ;;
            verify)
                VERIFY_MODE=true
                ;;
            --auto-safe)
                AUTO_UPGRADE=true
                UPGRADE_STRATEGY="safe"
                UPGRADE_MODE=true
                log_info "Auto-upgrade enabled: SAFE mode (preserves databases, overwrites code)"
                ;;
            --auto-stash)
                AUTO_UPGRADE=true
                UPGRADE_STRATEGY="stash"
                UPGRADE_MODE=true
                log_info "Auto-upgrade enabled: STASH mode (preserves all changes, attempts merge)"
                ;;
            --dry-run)
                DRY_RUN=true
                log_warning "Running in DRY-RUN mode - no actual changes will be made"
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown argument: $arg"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    echo "Agentic RAG System Installation Script v$SCRIPT_VERSION"
    echo ""
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  (none)     Fresh installation"
    echo "  upgrade    Pull latest changes from GitHub and update dependencies (interactive)"
    echo "  verify     Verify existing installation"
    echo ""
    echo "Options:"
    echo "  --auto-safe   Auto upgrade with SAFE mode (preserves databases, overwrites code)"
    echo "  --auto-stash  Auto upgrade with STASH mode (preserves all changes, attempts merge)"
    echo "  --dry-run     Show what would be done without executing"
    echo "  --help        Show this help message"
    echo ""
    echo "Upgrade Strategies:"
    echo "  SAFE:   Backs up databases/configs, force-overwrites code, restores data"
    echo "  STASH:  Preserves all local changes, attempts automatic merge"
    echo ""
    echo "Examples:"
    echo "  $0                       # Fresh installation"
    echo "  $0 upgrade               # Interactive upgrade (choose strategy)"
    echo "  $0 upgrade --auto-safe   # Non-interactive safe upgrade"
    echo "  $0 upgrade --auto-stash  # Non-interactive stash upgrade"
    echo "  $0 verify --dry-run      # Check what verification would do"
}

# System requirements check
check_system_requirements() {
    log_header "System Requirements Check"
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_success "Operating System: Linux (supported)"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_success "Operating System: macOS (supported)"
        # Adjust system dependencies for macOS
        SYSTEM_DEPS=("tesseract" "wkhtmltopdf" "python3")
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            log_success "Python version: $PYTHON_VERSION (✓ >= $REQUIRED_PYTHON_VERSION)"
        else
            log_error "Python version $PYTHON_VERSION is too old (required >= $REQUIRED_PYTHON_VERSION)"
            exit 1
        fi
    else
        log_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        log_success "Git: Available"
    else
        log_error "Git not found. Please install Git."
        exit 1
    fi
    
    # Check curl
    if command -v curl &> /dev/null; then
        log_success "curl: Available"
    else
        log_error "curl not found. Please install curl."
        exit 1
    fi
}

# Install system dependencies
install_system_dependencies() {
    log_header "System Dependencies Installation"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Update package list
        execute_command "sudo apt-get update" "Updating package list"
        
        # Install dependencies
        for dep in "${SYSTEM_DEPS[@]}"; do
            if dpkg -l | grep -q "^ii  $dep "; then
                log_success "$dep: Already installed"
            else
                execute_command "sudo apt-get install -y $dep" "Installing $dep"
            fi
        done
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            log_warning "Homebrew not found. Please install Homebrew first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        
        # Install dependencies with Homebrew
        for dep in "${SYSTEM_DEPS[@]}"; do
            if brew list "$dep" &> /dev/null; then
                log_success "$dep: Already installed"
            else
                execute_command "brew install $dep" "Installing $dep"
            fi
        done
    fi
}

# Clear Python caches to prevent import issues
clear_python_caches() {
    log_step "Clearing Python caches"
    
    if [ "$DRY_RUN" = false ]; then
        # Remove __pycache__ directories
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        
        # Remove .pyc files
        find . -name "*.pyc" -delete 2>/dev/null || true
        
        # Remove .pyo files  
        find . -name "*.pyo" -delete 2>/dev/null || true
        
        log_success "Python caches cleared"
    else
        log_info "[DRY-RUN] Would clear Python cache files (__pycache__, *.pyc, *.pyo)"
    fi
}

# Helper function for safe upgrade (preserves databases, overwrites everything else)
perform_safe_upgrade() {
    local branch="$1"

    log_info "Creating timestamp-based backup directory"
    BACKUP_DIR="upgrade_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Backup critical data that must be preserved
    log_info "🛡️ Backing up databases and FAISS indexes..."

    # Backup document store and databases
    [ -d "document_store" ] && cp -r document_store/ "$BACKUP_DIR/" 2>/dev/null || true
    [ -f "faiss.index" ] && cp faiss.index "$BACKUP_DIR/" 2>/dev/null || true
    find . -name "*.db" -maxdepth 1 -exec cp {} "$BACKUP_DIR/" \; 2>/dev/null || true
    find . -name "faiss_*" -maxdepth 1 -exec cp {} "$BACKUP_DIR/" \; 2>/dev/null || true

    # Also backup config files that user might have customized
    [ -f "credentials.json" ] && cp credentials.json "$BACKUP_DIR/" 2>/dev/null || true
    [ -f ".env" ] && cp .env "$BACKUP_DIR/" 2>/dev/null || true
    [ -f "watched_directories.json" ] && cp watched_directories.json "$BACKUP_DIR/" 2>/dev/null || true

    log_success "Backup completed to: $BACKUP_DIR"

    # Force clean upgrade
    log_info "🔄 Performing force upgrade (overwrites local changes)"
    execute_command "git reset --hard HEAD" "Resetting local changes"
    execute_command "git clean -fd" "Cleaning untracked files"
    execute_command "git pull origin $branch" "Pulling latest changes"

    # Restore critical data
    log_info "📊 Restoring databases and user data..."
    [ -d "$BACKUP_DIR/document_store" ] && cp -r "$BACKUP_DIR/document_store"/* document_store/ 2>/dev/null || true
    [ -f "$BACKUP_DIR/faiss.index" ] && cp "$BACKUP_DIR/faiss.index" . 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.db" -exec cp {} . \; 2>/dev/null || true
    find "$BACKUP_DIR" -name "faiss_*" -exec cp {} . \; 2>/dev/null || true

    # Restore user configs if they exist
    [ -f "$BACKUP_DIR/credentials.json" ] && cp "$BACKUP_DIR/credentials.json" . 2>/dev/null || true
    [ -f "$BACKUP_DIR/.env" ] && cp "$BACKUP_DIR/.env" . 2>/dev/null || true
    [ -f "$BACKUP_DIR/watched_directories.json" ] && cp "$BACKUP_DIR/watched_directories.json" . 2>/dev/null || true

    log_success "✅ Safe upgrade completed! Your databases and user data have been preserved."
    log_info "📁 Backup available at: $BACKUP_DIR (you can delete this later if upgrade was successful)"
}

# Helper function for stash upgrade (preserves all changes, attempts to merge)
perform_stash_upgrade() {
    local branch="$1"

    log_info "📦 Stashing local changes..."
    STASH_NAME="pre-upgrade-$(date +%Y%m%d_%H%M%S)"
    execute_command "git stash push -m '$STASH_NAME'" "Stashing changes"

    # Pull latest changes
    execute_command "git pull origin $branch" "Pulling latest changes"

    # Attempt to restore stashed changes
    log_info "🔄 Attempting to restore your local changes..."
    if git stash pop; then
        log_success "✅ Successfully merged your local changes with the upgrade"

        # Check if there are any merge conflicts
        if git diff --name-only --diff-filter=U | grep -q .; then
            log_warning "⚠️ Merge conflicts detected in the following files:"
            git diff --name-only --diff-filter=U
            echo ""
            log_warning "Please resolve conflicts manually and then run:"
            echo "  git add <resolved-files>"
            echo "  git commit -m 'Resolved upgrade conflicts'"
        fi
    else
        log_warning "⚠️ Could not automatically merge your changes"
        echo "Your changes are still available in stash: $STASH_NAME"
        echo "To view stashed changes: git stash show"
        echo "To apply manually later: git stash apply"
    fi
}

# Project directory setup
setup_project_directory() {
    log_header "Project Directory Setup"
    
    if [ "$UPGRADE_MODE" = true ]; then
        log_step "Upgrading existing installation"
        if [ ! -f "fastapi_server_complete.py" ]; then
            log_error "Not in a valid Agentic RAG System directory"
            exit 1
        fi
        
        # Capture current version before upgrade
        FROM_VERSION=$(get_current_version)
        log_info "Current version: $FROM_VERSION"
        
        # Auto-detect the default branch and handle upgrade conflicts intelligently
        DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "master")

        # Check for local changes that might conflict
        if ! git diff-index --quiet HEAD --; then
            log_warning "Local changes detected that may conflict with upgrade"

            # Show user what will be affected
            echo -e "${YELLOW}"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "   UPGRADE CONFLICT DETECTED"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "The following files have local changes that may conflict:"
            git diff --name-only HEAD
            echo ""
            echo "Choose upgrade strategy:"
            echo "  [1] 🛡️  SAFE: Backup & preserve databases, overwrite everything else (RECOMMENDED)"
            echo "  [2] 🔄 STASH: Temporarily stash changes, upgrade, then restore"
            echo "  [3] ❌ ABORT: Cancel upgrade and resolve manually"
            echo -e "${NC}"

            # Handle automated vs interactive upgrade
            if [ "$AUTO_UPGRADE" = true ]; then
                # Automated upgrade mode
                case "$UPGRADE_STRATEGY" in
                    "safe")
                        log_step "🤖 Automated SAFE upgrade (preserving databases)"
                        perform_safe_upgrade "$DEFAULT_BRANCH"
                        ;;
                    "stash")
                        log_step "🤖 Automated STASH upgrade (preserving all changes)"
                        perform_stash_upgrade "$DEFAULT_BRANCH"
                        ;;
                    *)
                        log_error "Invalid automated upgrade strategy: $UPGRADE_STRATEGY"
                        exit 1
                        ;;
                esac
            else
                # Interactive upgrade mode
                read -p "Enter choice [1-3]: " choice

                case $choice in
                    1)
                        log_step "🛡️ Performing SAFE upgrade (preserving databases)"
                        perform_safe_upgrade "$DEFAULT_BRANCH"
                        ;;
                    2)
                        log_step "🔄 Performing STASH upgrade"
                        perform_stash_upgrade "$DEFAULT_BRANCH"
                        ;;
                    3)
                        log_error "Upgrade cancelled by user"
                        echo "To resolve manually:"
                        echo "  git stash push -m 'before-upgrade'"
                        echo "  git pull origin $DEFAULT_BRANCH"
                        echo "  git stash pop  # (if you want to restore changes)"
                        exit 1
                        ;;
                    *)
                        log_error "Invalid choice. Aborting upgrade."
                        exit 1
                        ;;
                esac
            fi
        else
            # No conflicts, proceed normally
            execute_command "git pull origin $DEFAULT_BRANCH" "Pulling latest changes from GitHub"
        fi
        clear_python_caches
        
        # Capture new version after upgrade
        TO_VERSION=$(get_current_version)
        
        # Ensure required directories exist for upgraded installations
        log_step "Ensuring required directories exist"
        PROJECT_DIRS=("logs" "runtime" "tests/results")
        for dir in "${PROJECT_DIRS[@]}"; do
            if [ ! -d "$dir" ]; then
                execute_command "mkdir -p \"$dir\"" "Creating directory: $dir"
            else
                log_success "Directory already exists: $dir"
            fi
        done
    else
        # Fresh installation
        log_step "Setting up project directory"
        
        if [ -f "fastapi_server_complete.py" ]; then
            log_info "Already in Agentic RAG System directory"
        else
            log_error "Please run this script from the Agentic RAG System project directory"
            echo "If you need to clone the repository:"
            echo "  git clone $REPO_URL"
            echo "  cd Agentic-RAG-System"
            echo "  ./install.sh"
            exit 1
        fi
    fi
}

# Virtual environment setup
setup_virtual_environment() {
    log_header "Virtual Environment Setup"
    
    # Find existing virtual environment or create new one
    VENV_NAMES=("venv_fastapi" "venv" ".venv" "env")
    VENV_DIR=""
    
    for venv_name in "${VENV_NAMES[@]}"; do
        if [ -d "$venv_name" ] && [ -f "$venv_name/bin/activate" ]; then
            VENV_DIR="$venv_name"
            log_success "Found existing virtual environment: $VENV_DIR"
            break
        fi
    done
    
    if [ -z "$VENV_DIR" ]; then
        VENV_DIR="venv_fastapi"
        execute_command "python3 -m venv $VENV_DIR" "Creating virtual environment: $VENV_DIR"
    fi
    
    # Activate virtual environment
    if [ "$DRY_RUN" = false ]; then
        source "$VENV_DIR/bin/activate"
        log_success "Virtual environment activated: $VENV_DIR"
    fi
    
    # Upgrade pip
    execute_command "python -m pip install --upgrade pip" "Upgrading pip"
}

# Install Python dependencies
install_python_dependencies() {
    log_header "Python Dependencies Installation"
    
    if [ -f "requirements.txt" ]; then
        execute_command "pip install -r requirements.txt" "Installing Python dependencies"
        log_success "Python dependencies installed"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
}

# Ollama verification and setup
setup_ollama() {
    log_header "Ollama Configuration"
    
    # Get Ollama API URL from user
    read -p "🔗 Enter Ollama API URL (default: http://127.0.0.1:11434): " OLLAMA_URL
    OLLAMA_URL=${OLLAMA_URL:-"http://127.0.0.1:11434"}
    
    # Test Ollama connectivity
    log_step "Testing Ollama API connectivity"
    if [ "$DRY_RUN" = false ]; then
        if curl -s -f "$OLLAMA_URL/api/tags" > /dev/null; then
            log_success "Ollama API is accessible at $OLLAMA_URL"
        else
            log_warning "Ollama API not accessible at $OLLAMA_URL"
            echo ""
            echo "To install Ollama locally:"
            echo "  curl -fsSL https://ollama.ai/install.sh | sh"
            echo "  ollama serve"
            echo ""
            echo "Or use a remote Ollama instance and provide its URL."
            
            read -p "Continue anyway? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    # Check required models
    log_step "Checking required Ollama models"
    if [ "$DRY_RUN" = false ]; then
        AVAILABLE_MODELS=$(curl -s "$OLLAMA_URL/api/tags" | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    models = [model['name'] for model in data.get('models', [])]
    print(','.join(models))
except:
    print('')
" 2>/dev/null || echo "")
        
        for model in "${REQUIRED_MODELS[@]}"; do
            if echo "$AVAILABLE_MODELS" | grep -q "$model"; then
                log_success "Model available: $model"
            else
                log_warning "Model not found: $model"
                echo "To install: ollama pull $model"
            fi
        done
    fi
    
    # Update config with Ollama URL
    if [ -f "config/llm_config.yaml" ] && [ "$DRY_RUN" = false ]; then
        # Create backup
        cp config/llm_config.yaml config/llm_config.yaml.bak
        
        # Update the base_url in the config
        sed -i.tmp "s|base_url: http://127.0.0.1:11434|base_url: $OLLAMA_URL|g" config/llm_config.yaml
        rm -f config/llm_config.yaml.tmp
        
        log_success "Updated Ollama URL in config: $OLLAMA_URL"
    fi
}

# Environment configuration
setup_environment() {
    log_header "Environment Configuration"
    
    # Create or update .env file
    ENV_FILE=".env"
    
    if [ ! -f "$ENV_FILE" ]; then
        execute_command "touch $ENV_FILE" "Creating .env file"
    fi
    
    # Setup RAG Documents directory
    setup_rag_documents() {
        log_step "Setting up RAG Documents directory"
        
        # Create required project directories
        log_step "Creating required project directories"
        
        # Create directories for organized file structure
        PROJECT_DIRS=("logs" "runtime" "tests/results")
        for dir in "${PROJECT_DIRS[@]}"; do
            if [ ! -d "$dir" ]; then
                execute_command "mkdir -p \"$dir\"" "Creating directory: $dir"
            else
                log_success "Directory already exists: $dir"
            fi
        done
        
        # Create user RAG documents directory in home directory
        USER_RAG_DIR="$HOME/Agentic_RAG_Documents"
        if [ ! -d "$USER_RAG_DIR" ]; then
            execute_command "mkdir -p \"$USER_RAG_DIR\"" "Creating RAG documents directory: $USER_RAG_DIR"
        else
            log_success "RAG documents directory already exists: $USER_RAG_DIR"
        fi
        
        # Copy server documentation to RAG directory
        DOCS_DIR="$(pwd)/docs"
        if [ -d "$DOCS_DIR" ] && [ "$DRY_RUN" = false ]; then
            log_step "Copying server documentation to RAG directory"
            cp -r "$DOCS_DIR"/* "$USER_RAG_DIR/" 2>/dev/null || true
            
            # Also copy README files
            find "$(pwd)" -name "README*.md" -maxdepth 2 -exec cp {} "$USER_RAG_DIR/" \; 2>/dev/null || true
            
            log_success "Server documentation copied to RAG directory"
        fi
        
        # Create personalized watched_directories.json from template
        if [ -f "watched_directories.json.template" ]; then
            log_step "Creating personalized watched_directories.json"
            
            # Get current timestamp
            CURRENT_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S")
            
            # Replace placeholders in template
            if [ "$DRY_RUN" = false ]; then
                sed -e "s|{SERVER_DOCS_PATH}|$(pwd)/docs|g" \
                    -e "s|{USER_RAG_DOCUMENTS_PATH}|$USER_RAG_DIR|g" \
                    -e "s|{INSTALL_TIMESTAMP}|$CURRENT_TIMESTAMP|g" \
                    watched_directories.json.template > watched_directories.json
                
                log_success "Created personalized watched_directories.json"
                log_info "  Server docs: $(pwd)/docs"
                log_info "  User RAG dir: $USER_RAG_DIR"
            else
                log_info "[DRY-RUN] Would create watched_directories.json from template"
                log_info "  Server docs path: $(pwd)/docs"
                log_info "  User RAG directory: $USER_RAG_DIR"
            fi
        else
            log_warning "watched_directories.json.template not found, keeping existing config"
        fi
    }
    
    # Call the RAG setup function
    setup_rag_documents
    
    # API Keys configuration
    configure_api_keys() {
        local service="$1"
        local env_var="$2"
        local current_value=""
        
        if [ -f "$ENV_FILE" ] && [ "$DRY_RUN" = false ]; then
            current_value=$(grep "^$env_var=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | tr -d '"' || echo "")
        fi
        
        if [ -n "$current_value" ] && [ "$current_value" != "your_${service,,}_api_key_here" ]; then
            log_success "$service API Key: Already configured"
        else
            echo ""
            read -p "🔑 Enter your $service API Key (press Enter to skip): " api_key
            if [ -n "$api_key" ]; then
                if [ "$DRY_RUN" = false ]; then
                    # Remove existing line if present
                    sed -i "/^$env_var=/d" "$ENV_FILE"
                    # Add new line
                    echo "$env_var=\"$api_key\"" >> "$ENV_FILE"
                fi
                log_success "$service API Key: Configured"
            else
                log_warning "$service API Key: Skipped"
            fi
        fi
    }
    
    # Configure API keys for cloud services
    configure_api_keys "OpenAI" "OPENAI_API_KEY"
    configure_api_keys "Gemini" "GEMINI_API_KEY"
    configure_api_keys "Qwen" "QWEN_API_KEY"
    
    # Set executable permissions on scripts
    if [ "$DRY_RUN" = false ]; then
        find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true
        log_success "Script permissions updated"
    fi
}

# Verify installation
verify_installation() {
    log_header "Installation Verification"
    
    local verification_failed=false
    
    # Check virtual environment
    if [ -n "$VIRTUAL_ENV" ] || [ -d "venv_fastapi" ] || [ -d "venv" ]; then
        log_success "Virtual environment: OK"
    else
        log_error "Virtual environment: Missing"
        verification_failed=true
    fi
    
    # Check key files
    local key_files=("fastapi_server_complete.py" "requirements.txt" "config/llm_config.yaml")
    for file in "${key_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "File exists: $file"
        else
            log_error "File missing: $file"
            verification_failed=true
        fi
    done
    
    # Check Python imports
    if [ "$DRY_RUN" = false ]; then
        log_step "Testing Python imports"
        python3 -c "
import sys
sys.path.append('.')

try:
    import fastapi
    import uvicorn
    import yaml
    import requests
    import numpy
    import pandas
    print('✅ Core Python packages: OK')
except ImportError as e:
    print(f'❌ Python import failed: {e}')
    sys.exit(1)

try:
    import faiss
    print('✅ FAISS: OK')
except ImportError as e:
    print(f'❌ FAISS import failed: {e}')
    sys.exit(1)

try:
    import pytesseract
    print('✅ Tesseract OCR: OK')
except ImportError as e:
    print(f'❌ Tesseract import failed: {e}')
    sys.exit(1)
" || verification_failed=true
    fi
    
    # Check system commands
    for cmd in tesseract wkhtmltopdf; do
        if command -v $cmd &> /dev/null; then
            log_success "System command: $cmd"
        else
            log_error "System command missing: $cmd"
            verification_failed=true
        fi
    done
    
    if [ "$verification_failed" = true ]; then
        log_error "Installation verification failed"
        return 1
    else
        log_success "Installation verification passed"
        return 0
    fi
}

# Test server connectivity
test_server() {
    log_header "Server Connectivity Test"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "Would start server and test 'Hello World!' connectivity"
        return 0
    fi
    
    log_step "Starting server for connectivity test"
    
    # Start server in background
    python3 fastapi_server_complete.py &
    SERVER_PID=$!
    
    # Wait for server to start (5 minutes max for all modes)
    local max_wait_time=300  # 5 minutes for all modes
    log_step "Waiting for server to start (5 minutes max)"
    
    local wait_time=0
    local last_status_time=0
    while [ $wait_time -lt $max_wait_time ]; do
        # Check if server process is still alive
        if ! kill -0 $SERVER_PID 2>/dev/null; then
            log_error "Server process died unexpectedly"
            return 1
        fi
        
        if curl -s -f http://localhost:5000/health > /dev/null 2>&1; then
            log_success "Server started successfully"
            break
        fi
        
        # Show progress every 30 seconds
        if [ $((wait_time % 30)) -eq 0 ] && [ $wait_time -gt $last_status_time ]; then
            log_info "Still waiting... (${wait_time}s elapsed, may be rebuilding document index)"
            last_status_time=$wait_time
        fi
        
        sleep 1
        wait_time=$((wait_time + 1))
    done
    
    if [ $wait_time -eq $max_wait_time ]; then
        local timeout_msg="5 minutes"
        # Always 5 minutes now
        log_error "Server failed to start within $timeout_msg"
        kill $SERVER_PID 2>/dev/null || true
        return 1
    fi
    
    # Test Hello World prompt with proper OpenAI format
    log_step "Testing 'Hello World!' prompt"
    local response=$(curl -s -X POST http://localhost:5000/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"model": "Agentic-RAG-Model1", "messages": [{"role": "user", "content": "Hello World!"}]}' \
        --max-time 60 2>/dev/null || echo "")
    
    if [ -n "$response" ]; then
        log_success "Hello World test: SUCCESS"
        echo "Response preview: $(echo "$response" | head -c 100)..."
    else
        log_error "Hello World test: FAILED"
    fi
    
    # Clean up
    log_step "Stopping test server"
    kill $SERVER_PID 2>/dev/null || true
    sleep 2
    
    # Force kill if still running
    kill -9 $SERVER_PID 2>/dev/null || true
    
    log_success "Server connectivity test completed"
}

# Main installation flow
main() {
    log_header "Agentic RAG System Installer v$SCRIPT_VERSION"
    
    parse_arguments "$@"
    
    if [ "$VERIFY_MODE" = true ]; then
        # Verification mode
        verify_installation
        exit $?
    fi
    
    # Main installation/upgrade flow
    check_system_requirements
    
    if [ "$UPGRADE_MODE" = false ]; then
        install_system_dependencies
    fi
    
    setup_project_directory
    setup_virtual_environment
    install_python_dependencies
    clear_python_caches
    
    if [ "$UPGRADE_MODE" = false ]; then
        setup_ollama
        setup_environment
    fi
    
    # Verification
    if verify_installation; then
        log_success "Installation completed successfully!"
        
        # Show upgrade summary for upgrades
        show_upgrade_summary
        
        # Test server connectivity
        echo ""
        read -p "🧪 Test server connectivity with 'Hello World!' prompt? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            test_server
        fi
        
        # Final instructions
        log_header "Next Steps"
        echo "1. 🚀 Start the server:"
        echo "   ./start_complete.sh"
        echo ""
        echo "2. 🌐 Access the server:"
        echo "   • API: http://localhost:8000"
        echo "   • Health: http://localhost:8000/health" 
        echo "   • Docs: http://localhost:8000/docs"
        echo ""
        echo "3. 📚 Read the documentation:"
        echo "   • Admin Guide: docs/production/ADMINISTRATOR_GUIDE.md"
        echo "   • User Guide: docs/production/USER_GUIDE.md"
        echo "   • Developer Guide: docs/production/DEVELOPER_GUIDE.md"
        echo ""
        echo "4. 🔧 Configuration:"
        echo "   • LLM Config: config/llm_config.yaml"
        echo "   • Environment: .env"
        
    else
        log_error "Installation verification failed. Please check the errors above."
        exit 1
    fi
}

# Trap to clean up on script exit
cleanup() {
    if [ -n "$SERVER_PID" ]; then
        kill -9 $SERVER_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Run main function
main "$@"