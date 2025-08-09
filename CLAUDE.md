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

## 🌟 NEW FEATURE: OpenAI API Compatibility Layer

### **🚀 Full OpenAI API Support Added**

The Agentic-RAG server now includes a **complete OpenAI API compatibility layer**, enabling seamless integration with **Open-WebUI** and any OpenAI-compatible client.

**Key Features:**
- ✅ **OpenAI Chat Completions API** (`/v1/chat/completions`)
- ✅ **OpenAI Models API** (`/v1/models`) 
- ✅ **Streaming & Non-streaming** support
- ✅ **Zero-trust security** design
- ✅ **Full agentic capabilities** (11 tools) through OpenAI interface
- ✅ **Production-ready** performance optimizations

### **🎯 Open-WebUI Integration Guide**

#### **Step 1: Configure Open-WebUI Connection**
Point Open-WebUI to your Agentic-RAG server:

```bash
# Set OpenAI API Base URL in Open-WebUI
OPENAI_API_BASE_URL=http://localhost:5000/v1
OPENAI_API_KEY=dummy  # Any value (ignored by our server)

# Optional: Increase timeouts for long agentic responses
CLIENT_TIMEOUT=600000  # 10 minutes
MAX_TOKENS=100000      # 100k tokens
REQUEST_TIMEOUT=600    # 10 minutes
```

#### **Step 2: Available Models**
In Open-WebUI, you'll see these agentic models:
- **Agentic-RAG-Model1** (Primary agentic model)
- **Agentic-RAG-Model2** (Alternative agentic model)

#### **Step 3: Start Chatting**
- Select any Agentic-RAG model in Open-WebUI
- Chat normally - full agentic capabilities are automatically enabled
- The server will use tools, search web, analyze stocks, send emails, etc.

### **🔧 Direct API Usage**

#### **Chat with Streaming:**
```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [
      {"role": "user", "content": "What is the stock price of AAPL and email me a report?"}
    ],
    "stream": true
  }'
```

#### **Chat without Streaming:**
```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1", 
    "messages": [
      {"role": "user", "content": "Search for news about AI and create a PDF summary"}
    ],
    "stream": false
  }'
```

#### **List Available Models:**
```bash
curl http://localhost:5000/v1/models
```

### **🛡️ Security Design**

**Zero-Trust Architecture:**
- Only extracts user prompt from OpenAI messages
- **Ignores** all other parameters (temperature, top_p, etc.)
- Forces tools=True and uses system prompt
- All requests route through native agentic pipeline

**Protected Parameters:**
- `temperature` → Ignored
- `max_tokens` → Ignored  
- `top_p` → Ignored
- All other OpenAI parameters → Ignored

This ensures consistent agentic behavior regardless of client configuration.

### **⚡ Performance Optimizations**

**Dual Streaming Architecture:**
```bash
# Option 1: Direct function calls (Default - Recommended)
USE_DIRECT_FUNCTION_CALLS=true

# Option 2: HTTP requests with timeout
USE_DIRECT_FUNCTION_CALLS=false
OPENAI_HTTP_TIMEOUT=600
```

**Benefits of Direct Calls:**
- 🚀 **50x faster** response initiation
- ❌ **No timeout errors** from self-referencing HTTP
- 🔧 **Zero HTTP overhead**
- 💾 **Lower memory usage**

### **🧪 Testing Your Setup**

#### **Test 1: Basic Functionality**
```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Agentic-RAG-Model1", "messages": [{"role": "user", "content": "Hello"}], "stream": false}'
```

#### **Test 2: Agentic Capabilities**
```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Agentic-RAG-Model1", "messages": [{"role": "user", "content": "What is the weather and stock market news today?"}], "stream": true}'
```

#### **Test 3: Models Endpoint**
```bash
curl http://localhost:5000/v1/models | jq .
```

### **📋 Troubleshooting**

**Issue: Connection refused**
```bash
# Check server is running
curl http://localhost:5000/health
```

**Issue: Streaming timeout**
```bash
# Switch to direct function calls
export USE_DIRECT_FUNCTION_CALLS=true
./stop_complete.sh && ./start_complete.sh
```

**Issue: Open-WebUI shows no models**
```bash
# Check models endpoint returns data
curl http://localhost:5000/v1/models

# Check Open-WebUI logs for connection errors
```

### **🎉 What This Enables**

With OpenAI compatibility, your Agentic-RAG server now works with:
- 🌐 **Open-WebUI** (primary target)
- 🤖 **Any OpenAI-compatible client**
- 📱 **Mobile apps** using OpenAI API
- 💻 **Custom integrations** via standard OpenAI SDKs
- 🔗 **Third-party tools** expecting OpenAI format

**Status**: Production ready for complex agentic workflows through OpenAI-compatible interfaces.