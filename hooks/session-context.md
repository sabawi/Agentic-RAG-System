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
