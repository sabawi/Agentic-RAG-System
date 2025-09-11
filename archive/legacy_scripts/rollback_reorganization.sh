#!/bin/bash
# 🛡️ Emergency Rollback Script for Project Reorganization
# Safely restores previous project state if reorganization fails

set -e  # Exit on any error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "🛡️ ================================================"
    echo "   EMERGENCY PROJECT REORGANIZATION ROLLBACK"
    echo "================================================${NC}"
}

stop_server() {
    print_status "Stopping server before rollback..."
    
    if [ -f "./stop_complete.sh" ]; then
        ./stop_complete.sh || true
        print_success "Server stopped"
    else
        print_warning "stop_complete.sh not found, attempting manual stop"
        # Try to kill any running server processes
        pkill -f "fastapi_server_complete.py" || true
        pkill -f "python.*server" || true
        sleep 2
    fi
}

find_latest_backup() {
    print_status "Searching for backup directories..."
    
    # Look for backup directories with timestamp pattern
    BACKUP_DIRS=($(find . -maxdepth 1 -name "*_backup_*" -type d | sort -r))
    
    if [ ${#BACKUP_DIRS[@]} -eq 0 ]; then
        print_error "No backup directories found!"
        print_error "Expected pattern: *_backup_YYYYMMDD_HHMMSS"
        return 1
    fi
    
    echo "Found ${#BACKUP_DIRS[@]} backup directories:"
    for i in "${!BACKUP_DIRS[@]}"; do
        echo "  $((i+1)). ${BACKUP_DIRS[i]}"
    done
    
    # Use the most recent backup by default
    LATEST_BACKUP="${BACKUP_DIRS[0]}"
    print_success "Using latest backup: $LATEST_BACKUP"
    echo "$LATEST_BACKUP"
}

restore_from_backup() {
    local BACKUP_DIR="$1"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "Backup directory does not exist: $BACKUP_DIR"
        return 1
    fi
    
    print_status "Restoring from backup: $BACKUP_DIR"
    
    # Create emergency backup of current state
    EMERGENCY_BACKUP="emergency_backup_$(date +%Y%m%d_%H%M%S)"
    print_status "Creating emergency backup of current state: $EMERGENCY_BACKUP"
    
    mkdir -p "$EMERGENCY_BACKUP"
    
    # Backup critical files that might have been modified
    CRITICAL_FILES=(
        "fastapi_server_complete.py"
        "config/llm_config.yaml"
        "user_tools/"
        "CLAUDE.md"
        "start_complete.sh"
        "stop_complete.sh"
    )
    
    for file in "${CRITICAL_FILES[@]}"; do
        if [ -e "$file" ]; then
            cp -r "$file" "$EMERGENCY_BACKUP/" 2>/dev/null || true
        fi
    done
    
    print_success "Emergency backup created"
    
    # Restore from backup
    print_status "Restoring files from backup..."
    
    # Remove current files (except backups and git)
    find . -maxdepth 1 -type f \( ! -name "*_backup_*" ! -name ".git*" ! -name "*.md" \) -delete 2>/dev/null || true
    find . -maxdepth 1 -type d \( ! -name "*_backup_*" ! -name ".git" ! -name "$EMERGENCY_BACKUP" \) -exec rm -rf {} + 2>/dev/null || true
    
    # Copy files from backup
    cp -r "$BACKUP_DIR"/* . 2>/dev/null || {
        print_error "Failed to restore from backup!"
        print_error "Emergency backup is available at: $EMERGENCY_BACKUP"
        return 1
    }
    
    print_success "Files restored from backup"
}

restore_git_state() {
    print_status "Attempting to restore git state..."
    
    # Check if we have a pre-reorganization git tag
    if git tag | grep -q "pre-reorganization-backup"; then
        print_status "Found pre-reorganization git tag, resetting..."
        git reset --hard pre-reorganization-backup 2>/dev/null || {
            print_warning "Git reset failed, continuing with file restoration"
            return 1
        }
        print_success "Git state restored to pre-reorganization"
    else
        print_warning "No pre-reorganization git tag found"
        # Try to restore from git stash
        if git stash list | grep -q "pre-reorganization"; then
            print_status "Found pre-reorganization stash, applying..."
            git stash apply "$(git stash list | grep "pre-reorganization" | head -n1 | cut -d: -f1)" 2>/dev/null || {
                print_warning "Git stash apply failed"
                return 1
            }
            print_success "Git stash applied"
        else
            print_warning "No git restore options available"
            return 1
        fi
    fi
}

validate_restoration() {
    print_status "Validating restoration..."
    
    # Check critical files exist
    CRITICAL_FILES=(
        "fastapi_server_complete.py"
        "config/llm_config.yaml"
        "user_tools/sandboxed_executor.py"
        "start_complete.sh"
        "stop_complete.sh"
    )
    
    local validation_failed=false
    
    for file in "${CRITICAL_FILES[@]}"; do
        if [ ! -e "$file" ]; then
            print_error "Critical file missing after restoration: $file"
            validation_failed=true
        else
            print_success "Found: $file"
        fi
    done
    
    if [ "$validation_failed" = true ]; then
        print_error "Restoration validation failed!"
        return 1
    fi
    
    # Test Python syntax for main server
    print_status "Testing server file syntax..."
    python -m py_compile fastapi_server_complete.py || {
        print_error "Server file has syntax errors after restoration!"
        return 1
    }
    
    print_success "Restoration validation passed"
}

test_server_startup() {
    print_status "Testing server startup after restoration..."
    
    # Test server can start
    if [ -f "./start_complete.sh" ]; then
        # Make sure script is executable
        chmod +x ./start_complete.sh
        chmod +x ./stop_complete.sh
        
        print_status "Starting server for validation..."
        ./start_complete.sh &
        SERVER_PID=$!
        
        # Wait a bit for server to start
        sleep 10
        
        # Test if server is responding
        if curl -s http://localhost:5000/health >/dev/null 2>&1; then
            print_success "Server started successfully after restoration"
            
            # Stop the test server
            ./stop_complete.sh || kill $SERVER_PID 2>/dev/null || true
            
            return 0
        else
            print_error "Server failed to start after restoration"
            
            # Stop the failed server
            ./stop_complete.sh || kill $SERVER_PID 2>/dev/null || true
            
            return 1
        fi
    else
        print_warning "Cannot test server startup - start_complete.sh not found"
        return 1
    fi
}

main() {
    print_header
    
    print_status "Starting emergency rollback procedure..."
    
    # Stop server first
    stop_server
    
    # Find backup to restore from
    BACKUP_DIR=$(find_latest_backup) || {
        print_error "Cannot proceed without backup directory"
        exit 1
    }
    
    # Confirm rollback
    echo
    print_warning "This will restore your project to the state in: $BACKUP_DIR"
    print_warning "Current changes will be backed up to an emergency backup directory"
    echo
    read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Rollback cancelled by user"
        exit 0
    fi
    
    # Perform restoration
    restore_from_backup "$BACKUP_DIR" || {
        print_error "File restoration failed!"
        exit 1
    }
    
    # Try to restore git state
    restore_git_state || {
        print_warning "Git restoration failed, but file restoration completed"
    }
    
    # Validate restoration
    validate_restoration || {
        print_error "Restoration validation failed!"
        print_error "Manual intervention required"
        exit 1
    }
    
    # Test server startup
    test_server_startup || {
        print_warning "Server startup test failed, but restoration appears complete"
        print_warning "Manual server testing may be required"
    }
    
    print_header
    print_success "ROLLBACK COMPLETED SUCCESSFULLY"
    print_success "Project restored to backup state: $BACKUP_DIR"
    echo
    print_status "Next steps:"
    echo "  1. Test server functionality manually: ./start_complete.sh"
    echo "  2. Run regression tests to verify system works"
    echo "  3. Review emergency backup if needed: emergency_backup_*"
    echo
    print_status "If issues persist, check the emergency backup directories"
}

# Handle script interruption
trap 'print_error "Rollback interrupted! Check system state manually."; exit 1' INT TERM

# Run main function
main "$@"