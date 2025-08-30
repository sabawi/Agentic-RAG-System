#!/bin/bash

# 🚨 MANDATORY SECURITY CHECKPOINT SCRIPT 🚨
# This script MUST be run before ANY git commit operations
# BLOCKS commits containing personal information

set -e

echo "🔒 MANDATORY SECURITY GATE ACTIVATED"
echo "=====================================".

echo "🔍 Scanning for personal information patterns..."

# Scan for personal data patterns in staged files only
PERSONAL_DATA_FOUND=false

# Check staged files for personal information
git diff --cached --name-only 2>/dev/null | while read -r file; do
    if [[ -n "$file" && -f "$file" ]]; then
        # Check for personal data patterns
        if grep -qi -E "(resume|curriculum vitae|cv|cover.?letter|dear (mr|ms|mrs)|sincerely|phone:?\s*[0-9-()+ ]+|email:?\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})" "$file" 2>/dev/null; then
            echo "🔴 SECURITY BREACH: Personal data pattern detected in $file"
            PERSONAL_DATA_FOUND=true
        fi
        
        # Check for personal file patterns
        if [[ "$file" == *resume* ]] || [[ "$file" == *cv* ]] || [[ "$file" == *cover_letter* ]]; then
            echo "🔴 SECURITY BREACH: Personal file detected: $file"
            PERSONAL_DATA_FOUND=true
        fi
    fi
done

# Check for sandbox_workspace commits (CRITICAL)
if git diff --cached --name-only 2>/dev/null | grep -q "^sandbox_workspace/"; then
    echo "🚨 CRITICAL VIOLATION: Attempting to commit sandbox_workspace content!"
    echo "🔴 COMMIT BLOCKED - Personal data protection violation"
    echo ""
    echo "Files being committed from sandbox_workspace:"
    git diff --cached --name-only | grep "^sandbox_workspace/" || true
    exit 1
fi

# Check for credentials and sensitive data
if git diff --cached --name-only 2>/dev/null | xargs grep -l -i -E "(password|secret|token|api.?key|private.?key)" 2>/dev/null; then
    echo "🔴 SECURITY BREACH: Potential credentials detected!"
    echo "🚨 COMMIT BLOCKED - Credential protection violation"
    exit 1
fi

if [[ "$PERSONAL_DATA_FOUND" == "true" ]]; then
    echo ""
    echo "🚨 COMMIT BLOCKED - Remove personal data first"
    echo "🔒 Review files and remove personal information before committing"
    exit 1
fi

echo "✅ SECURITY SCAN PASSED - No personal data detected"
echo "🔒 Safe to proceed with commit"
exit 0