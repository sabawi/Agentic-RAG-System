#!/bin/bash

# Claude Code Session Start Hook
# Automatically displays mandatory project directive at session start
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
}

# Main execution
main() {
    log_message "========== SESSION START HOOK TRIGGERED =========="
    log_message "Project: $PROJECT_ROOT"

    # Check if this is the Agentic-RAG development project
    if [[ -f "fastapi_server_complete.py" || -f "CLAUDE.md" || -d "docs" ]]; then
        log_message "DETECTED: Agentic-RAG project - displaying mandatory directive"

        # Output the mandatory directive message
        cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                    🚨 MANDATORY PROJECT DIRECTIVE 🚨                       ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 READ, UNDERSTAND, AND ADHERE TO THE CURRENT PROJECT ARCHITECTURE,
   RESTRICTIONS, REQUIREMENTS, DOCUMENTATIONS, RULES, AND DIRECTIVES IN:

   • ./docs/*/* (all documentation subdirectories)
   • CLAUDE.md (project directives and rules)

⚠️  CRITICAL REQUIREMENTS BEFORE ANY CODE CHANGES:

   1. Read CLAUDE.md fully
   2. Read ALL architecture and design documents in /docs/
   3. Understand the system architecture BEFORE attempting changes
   4. Follow all configuration rules (NO hardcoded values)
   5. Increment version.py after ANY code change
   6. Test end-to-end before claiming fix works
   7. Never assume - investigate and verify first

📁 KEY DOCUMENTATION LOCATIONS:
   • /docs/DEVELOPER_TECHNICAL_IMPLEMENTATION_*.md
   • /docs/LLM_CONFIGURATION_GUIDE.md
   • /docs/PROJECT_CONFIGURATION_DIRECTIVE.md
   • /docs/POST_LLM_EXECUTION_ARCHITECTURE.md
   • /docs/HTML_EMAIL_CONVERSION_SYSTEM.md
   • /docs/PLUGIN_SYSTEM_COMPLETE.md
   • /docs/VERSION_MANAGEMENT.md
   • CLAUDE.md (ROOT DIRECTORY)

🔒 THIS MESSAGE IS AUTOMATICALLY ENFORCED AT EVERY SESSION START

╔════════════════════════════════════════════════════════════════════════════╗
║           Failure to comply may result in architectural violations         ║
╚════════════════════════════════════════════════════════════════════════════╝

EOF

        log_message "Mandatory directive displayed to user"

        # Return success (no JSON needed, message is displayed directly)
        echo ""

    else
        log_message "Non-Agentic-RAG project - skipping directive"
    fi

    log_message "========== HOOK COMPLETED SUCCESSFULLY =========="
}

# Execute main function
main "$@"

# Always exit with success to never fail
exit 0