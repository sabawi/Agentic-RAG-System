# Claude Code Agent Memory

## 🚨 CRITICAL MULTI-TOOL CALLING PROTECTION 🚨

**NEVER MODIFY TOOL DESCRIPTIONS WITHOUT EXPLICIT AUTHORIZATION**

The multi-tool calling capability (2-4+ tools per request) has been successfully achieved after extensive debugging.
BREAKING THIS WILL CAUSE CATASTROPHIC REGRESSION TO SINGLE-TOOL LIMITATION.

**Protected Components:**
- Tool descriptions in fastapi_server_complete.py (lines 287-385)
- User tool descriptions in user_tools/*.py files 
- Disabled conflicting tool: _disabled_stock_analyzer.py (KEEP DISABLED)

**Verification Required:** After ANY tool changes, run verification commands in CRITICAL_MULTI_TOOL_CALLING_PROTECTION.md

## Critical Debugging and Fix Procedures

### EMAIL ATTACHMENT DEBUG PROCEDURE
**FUNDAMENTAL RULE**: When debugging email attachment or file generation issues, ALWAYS follow this end-to-end testing methodology:

1. **Server Restart**: Always restart server before testing
   ```bash
   ./stop_complete.sh && ./start_complete.sh
   ```

2. **Controlled Testing**: Use curl for isolated testing
   ```bash
   # Simple test (direct tool calls)
   curl -X POST http://localhost:5000/llama3_1b/stream \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Create a PDF file called test.pdf with content Hello World and email it to sabawi@gmail.com", "model": "qwen3:8b", "stream": false}'
   
   # Complex test (post-LLM execution)
   curl -X POST http://localhost:5000/llama3_1b/stream \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Look up news and create a PDF report and email it to sabawi@gmail.com", "model": "qwen3:8b", "stream": false}'
   ```

3. **Verification Steps**:
   - Check file creation: `file /path/to/file.pdf` (must show "PDF document")
   - Check email debug files: `/tmp/email_debug_*.eml`
   - Check server logs: `tail -f server_complete.log`
   - Verify MIME encoding in email (base64 for binary)

### RACE CONDITION ARCHITECTURE
**Two-stage LLM Processing**:
- Stage 1: Tool calling model (qwen3:8b) generates tool calls
- Stage 2: Primary LLM processes results and generates response
- **CRITICAL**: File creation must happen AFTER Primary LLM completion

### PDF GENERATION REQUIREMENTS
- Use `convert_to_pdf=True` for binary PDF generation
- Files must use reportlab library
- Verify with `file` command - must show "PDF document, version 1.4"

### NEVER ASSUME FIXES WORK
- **MANDATORY**: Test every fix end-to-end with server restart
- **NO THEORETICAL FIXES**: Always verify with actual curl tests
- **FULL WORKFLOW**: Test from tool call → file creation → email delivery

This procedure prevented a 2-day debugging cycle and ensures robust system operation.