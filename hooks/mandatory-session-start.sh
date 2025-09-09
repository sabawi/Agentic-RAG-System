#!/bin/bash

# Claude Code Session Start Hook
# Automatically triggers mandatory procedures for development sessions
# This hook NEVER FAILS and ensures proper project architecture understanding

set -euo pipefail

PROJECT_ROOT="$(pwd)"
LOG_FILE="$PROJECT_ROOT/hooks/session-start.log"

# Ensure log file exists
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1" >&2  # Also output to stderr for visibility
}

# Function that never fails
safe_execute() {
    local description="$1"
    shift
    log_message "EXECUTING: $description"
    
    if "$@" 2>&1 | tee -a "$LOG_FILE"; then
        log_message "SUCCESS: $description"
        return 0
    else
        log_message "WARNING: $description failed, but continuing..."
        return 0  # Always return success to never fail
    fi
}

# Main execution
main() {
    log_message "========== MANDATORY SESSION START PROCEDURES =========="
    log_message "Project: $PROJECT_ROOT"
    log_message "Hook triggered for session start"
    
    # Check if this is a development project
    if [[ -f "fastapi_server_complete.py" || -d "user_tools" || -d "docs" ]]; then
        log_message "DETECTED: Development project - triggering mandatory procedures"
        
        # Create context that will be injected into Claude
        cat > "$PROJECT_ROOT/hooks/session-context.md" << 'EOF'
# 🚨 MANDATORY SESSION START PROCEDURES TRIGGERED

## Required Actions Before Any Code Changes:

1. **LAUNCH project-architect-coder agent FIRST**
   - Use: Task tool with subagent_type: "project-architect-coder" 
   - Purpose: Understand current project architecture and design
   - Required before ANY development work begins

2. **READ Architecture Documentation**
   - Read ALL files in /docs/ directory, especially:
     - /docs/ARBITRATOR_ARCHITECTURE.md
     - Any other .md files in docs/
   - Understand system design before making changes

3. **ANALYZE Current System State**
   - Review recent commits with git log
   - Understand what was modified recently
   - Check git status for current changes

## Project Context:
- FastAPI/Flask server with LLM integration
- PDF generation and email functionality
- Arbitrator system for tool validation
- Complex multi-tool calling architecture

## Critical Reminder:
**NEVER make code changes without first understanding the full system architecture through the project-architect-coder agent**

This ensures compliance with project directives and prevents architectural violations.

---
*Generated automatically by mandatory session-start hook*
EOF
        
        log_message "Generated session context file"
        
        # Output JSON with additional context for Claude
        cat << EOF
{
  "additionalContext": "🚨 MANDATORY PROCEDURES ACTIVE: Session-start hook detected development project. Before making ANY code changes, you MUST: 1) Launch project-architect-coder agent to understand architecture, 2) Read /docs/ARBITRATOR_ARCHITECTURE.md and other docs, 3) Analyze current system state. See hooks/session-context.md for details. This is automatically enforced to prevent architectural violations.",
  "success": true
}
EOF
        
    else
        log_message "Non-development project - skipping mandatory procedures"
        echo '{"success": true}'
    fi
    
    log_message "========== HOOK COMPLETED SUCCESSFULLY =========="
}

# Execute main function
main "$@"

# Always exit with success to never fail
exit 0