# LLM Configuration Guide v1.0.3.2
## Hybrid Architecture & Advanced Tool Calling System

**Last Updated**: October 10, 2025
**Current Version**: 1.0.3.2 - Production Ready with Python 3.13.8
**Python Version**: 3.13.8 (40-50% async I/O performance improvement)

---

## 🎯 Overview

The Agentic RAG System features a **Hybrid LLM Architecture** that combines the benefits of local Ollama models with reliable cloud-based tool calling. This guide covers all LLM configuration aspects for administrators, users, and developers.

### Architecture Summary
```
User Request → Tool Calling LLM (OpenAI) → Multi-Tool Execution → Primary LLM (Ollama) → Response
                     ↓                            ↓                        ↓
              [Reliable Tool Calls]        [19 AI Tools]         [Local Processing + Thinking]
                                                                  [Citation Enforcement]
```

### Key Features (v1.0.3.2)
- **Hybrid Architecture**: Local primary LLM + Cloud tool calling
- **System Prompt Delivery**: Fixed critical bug ensuring prompts reach Ollama models
- **Citation Format Enforcement**: Clickable `[Title](URL)` format mandatory
- **Python 3.13.8**: Significant async I/O performance improvements
- **Comprehensive Email Integration**: Multi-account email management
- **Plugin System**: Extensible tool framework
- **Optimization API**: Runtime control of performance features

---

## 🔧 Configuration File Structure

### Primary Configuration: `config/llm_config.yaml`

The configuration file is the **single source of truth** for all LLM behavior. Changes take effect on server restart.

```yaml
# =============================================================================
# LLM Configuration File - Current Production Configuration
# =============================================================================
#
# CRITICAL: Token Parameter Usage by Provider Type
# ------------------------------------------------
#
# For OLLAMA providers (type: ollama):
#   • context_window_size → Maps to Ollama 'num_ctx' parameter (input context limit)
#   • num_predict         → Maps to Ollama 'num_predict' parameter (output tokens limit)
#   • max_tokens          → IGNORED (kept for backward compatibility only)
#
# For NON-OLLAMA providers (type: openai, qwen, gemini, etc.):
#   • context_window_size → Used for input context size management
#   • max_tokens          → Used for output tokens limit (native API parameter)
#   • num_predict         → Available but typically unused by these providers
#
# Parameter Priority (all providers):
#   1. Request-level parameters (highest priority)
#   2. Configuration file parameters
#   3. Provider-specific defaults (lowest priority)

llm:
  # =========================================================================
  # PRIMARY LLM - Handles main conversation and response generation
  # Current: deepseek-v3.1:671b-cloud (via Ollama cloud service)
  # Purpose: Large context window for comprehensive document searches
  # =========================================================================
  primary:
    type: ollama                          # Provider type
    config:
      model: deepseek-v3.1:671b-cloud     # Cloud-hosted 671B parameter model
      timeout: 3600                       # 60 minutes for large context processing
      context_window_size: 32768          # 32K context (increased from 8192)
                                          # Reason: Supports comprehensive document searches
                                          # that return many source blocks
      temperature: 0.7                    # Creative but focused responses
      num_predict: 16384                  # Maximum output tokens (16K)
      max_tokens: 32768                   # Ignored for Ollama (kept for compatibility)
      base_url: http://127.0.0.1:11434    # Local Ollama instance
      api_key: null                       # Not needed for local Ollama
      stream: true                        # Enable streaming responses to user
      think: false                        # Thinking mode (enables <think> tags)
                                          # Set to true for reasoning visibility

  # =========================================================================
  # TOOL CALLING LLM - Handles tool orchestration and function calls
  # Current: gpt-4o-mini (OpenAI cloud)
  # Purpose: Reliable, accurate tool selection and parameter extraction
  # =========================================================================
  tool_calling:
    type: openai                          # OpenAI for reliable tool calling
    config:
      model: gpt-4o-mini                  # Fast, accurate, cost-effective
      timeout: 120                        # 2 minutes for tool decisions
      context_window_size: 4096           # Sufficient for tool contexts
      temperature: 0.1                    # Low temperature for precise tool calling
      max_tokens: 1024                    # Limited tool call responses
      stream: false                       # Non-streaming for tools (faster)

  # =========================================================================
  # VISION PROCESSING - Handles image analysis and OCR
  # Current: qwen2.5vl:3b (Ollama local)
  # Purpose: Privacy-preserving local vision analysis
  # =========================================================================
  vision:
    type: ollama
    config:
      model: qwen2.5vl:3b                 # 3B parameter vision model
      timeout: 3600                       # 60 minutes for complex vision tasks
      base_url: http://127.0.0.1:11434
      fallback_model: bakllava:latest     # Backup if qwen2.5vl fails
      think: false                        # Thinking mode for vision tasks

  # =========================================================================
  # ARBITRATOR - Handles tool call validation and retry logic
  # Current: gpt-4o-mini (OpenAI cloud)
  # Purpose: Neutral decision making for failed tool executions
  # Note: Can be enabled/disabled via CLI tool or config file
  # =========================================================================
  arbitrator:
    enabled: true                         # Enable/disable arbitrator system
    type: openai
    config:
      model: gpt-4o-mini
      timeout: 60
      context_window_size: 4096
      temperature: 0.1                    # Low for objective decisions
      max_tokens: 1024
      stream: false
      api_key: ${OPENAI_API_KEY}          # Environment variable
      base_url: https://api.openai.com/v1

  # =========================================================================
  # FALLBACK CONFIGURATION - Auto-switching when primary fails
  # =========================================================================
  fallback:
    auto_switch: true                     # Enable automatic fallback
    enabled: true
    order:
      - ollama                            # Try local first (privacy + speed)
      - openai                            # Then cloud (reliability)
      - openrouter                        # Alternative cloud (many models)
      - qwen                              # Alternative cloud
      - gemini                            # Final fallback

  # =========================================================================
  # PROVIDER CONFIGURATIONS - Connection settings for each provider
  # =========================================================================
  providers:
    ollama:
      health_check_url: http://127.0.0.1:11434/api/tags
      retry_attempts: 3
      retry_delay: 2                      # Seconds between retries
    openai:
      api_key: ${OPENAI_API_KEY}          # Must be set in .env file
      base_url: https://api.openai.com/v1
      organization: null                  # Optional organization ID
      retry_attempts: 3
      retry_delay: 1
      models:
        primary: gpt-4o                   # Available as fallback
        tool_calling: gpt-4o              # Alternative tool calling model
    openrouter:
      api_key: ${OPENROUTER_API_KEY}      # Must be set in .env file
      base_url: https://openrouter.ai/api/v1
      retry_attempts: 3
      retry_delay: 1
      headers:                            # Optional headers for rankings
        HTTP-Referer: ${OPENROUTER_SITE_URL}
        X-Title: ${OPENROUTER_SITE_NAME}
      models:
        primary: deepseek/deepseek-r1:free      # Free reasoning model
        tool_calling: openai/gpt-4o-mini        # Tool calling via OpenRouter
        reasoning: deepseek/deepseek-r1         # Full reasoning model
        free: deepseek/deepseek-r1:free         # Free tier option

# =============================================================================
# OPTIMIZATION SYSTEM - Runtime performance controls
# Added: v1.0.2.50
# Purpose: Control performance features without code changes
# =============================================================================
optimization:
  enabled: true                           # Master optimization switch
  rollout_percentage: 100.0               # Percentage of requests using optimizations
  detailed_logging: true                  # Log optimization decisions

# =============================================================================
# ARBITRATOR SYSTEM - Tool call validation and retry
# Added: v1.0.2.40
# Purpose: Improve tool calling reliability
# Control: CLI tool (./tools/llm_config_tool.py) or config file
# =============================================================================
arbitrator:
  enabled: true                           # Enable arbitrator validation
  type: openai
  config:
    model: gpt-4o-mini
    timeout: 60
    context_window_size: 4096
    temperature: 0.1
    max_tokens: 1024
    stream: false
    api_key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com/v1

# =============================================================================
# EMAIL INTEGRATION - Multi-account email management
# Added: v1.0.2.89
# Purpose: Unified email retrieval, search, and sending
# =============================================================================
email:
  enabled: true                           # Enable email system
  default_provider: "gmail_primary"       # Default when not specified

  # Email retrieval settings
  retrieval:
    default_timeout: 30                   # Connection timeout
    max_emails_per_request: 50            # Limit per query
    auto_mark_read: false                 # Don't auto-mark as read
    default_retrieval_type: "headers"     # "headers" (fast) or "full" (complete)
    cache_duration: 300                   # Cache results for 5 minutes

  # Email sending settings
  sending:
    auto_cleanup_attachments: true        # Remove temp attachments after send
    max_attachment_size_mb: 25
    wait_for_attachments: true
    attachment_timeout: 45
    preserve_existing_functionality: true # Backward compatibility

  # Security settings
  security:
    allowed_attachment_types: [".pdf", ".html", ".txt", ".md", ".csv", ".json", ".xml", ".log", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip"]
    forbidden_attachment_types: [".exe", ".bat", ".cmd", ".com", ".scr", ".pif", ".msi", ".dll"]
    max_recipients: 50
    require_auth: true
    enable_app_passwords: true            # Use app-specific passwords

  # Email providers (configure in .env file)
  providers:
    gmail_primary:
      email: "${GMAIL_PRIMARY_EMAIL}"
      password: "${GMAIL_PRIMARY_APP_PASSWORD}"
      imap:
        server: "imap.gmail.com"
        port: 993
        use_ssl: true
      smtp:
        server: "smtp.gmail.com"
        port: 587
        use_tls: true
      description: "Primary Gmail account"

    # Additional providers: outlook_personal, outlook_work, yahoo_personal,
    # icloud_personal, custom_server (see config/llm_config.yaml for full list)

# =============================================================================
# FLIGHT SEARCH INTEGRATION
# Added: v1.0.2.70+
# Purpose: Flight search and price comparison
# =============================================================================
flight_search:
  enabled: true
  web_scraping:
    enabled: true
    timeout_seconds: 30
    max_results: 10
  apis:
    # Various flight API providers (configure API keys in .env)
    amadeus:
      enabled: false
      api_key: ${AMADEUS_API_KEY}
    skyscanner:
      enabled: false
      api_key: ${SKYSCANNER_API_KEY}
  verification_links:
    # Always included for user verification
    kayak: "https://www.kayak.com/flights"
    expedia: "https://www.expedia.com/Flights-Search"
    google_flights: "https://www.google.com/travel/flights"

# =============================================================================
# DEBUG CONFIGURATION
# =============================================================================
debug:
  log_requests: false                     # Log all incoming requests
  log_timing: true                        # Log timing information
  mock_providers: false                   # Use mock providers for testing

# =============================================================================
# PERFORMANCE TUNING
# =============================================================================
performance:
  connection_pool_size: 10                # HTTP connection pool size
  max_concurrent_requests: 5              # Max simultaneous LLM requests
  request_timeout: 600                    # Default request timeout (10 min)
  streaming_chunk_size: 1024              # Stream chunk size (bytes)

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================
security:
  api_key_encryption: false               # Encrypt API keys in config
  audit_logging: true                     # Log security events
  rate_limiting:
    enabled: true
    requests_per_minute: 60               # Rate limit per client
    burst_limit: 10                       # Burst allowance

# =============================================================================
# PLATFORM-SPECIFIC PATHS
# =============================================================================
platform:
  config_dir:
    linux: ${HOME}/.config/agentic_rag
    macos: ${HOME}/.config/agentic_rag
    windows: ${APPDATA}/agentic_rag
  log_dir:
    linux: ${HOME}/.local/share/agentic_rag/logs
    macos: ${HOME}/.local/share/agentic_rag/logs
    windows: ${LOCALAPPDATA}/agentic_rag/logs
  temp_dir:
    linux: /tmp/agentic_rag
    macos: ${TMPDIR}/agentic_rag
    windows: ${TEMP}/agentic_rag
```

---

## 🚀 Key Features & Improvements

### 1. **Hybrid Architecture Benefits**
- **Local Privacy**: Primary conversations handled by local Ollama models
- **Reliable Tools**: Cloud OpenAI ensures consistent tool calling (>95% success rate)
- **Cost Effective**: Expensive reasoning on local 671B model, cheap tools on cloud
- **Thinking Mode**: Support for Open-WebUI compatible thinking tags
- **Large Context**: 32K context window for comprehensive document searches

### 2. **Critical Bug Fixes Applied**
- **✅ v1.0.2.101**: Fixed missing system prompt in Ollama requests
  - Root cause: Ollama provider wasn't extracting `system_prompt` from kwargs
  - Impact: Citation format rules now properly enforced
- **✅ v1.0.2.101**: Fixed citation format in context blocks
  - Changed from `SOURCE BLOCK #X` to `SOURCE: {title}`
  - Prevents model from learning wrong citation pattern
- **✅ v1.0.3.1**: Added missing Google API dependencies for Python 3.13
  - Fixed: `No module named 'cachetools'` error
  - Added 10 transitive dependencies explicitly

### 3. **Python 3.13.8 Upgrade Benefits** (v1.0.3.0)
- **40-51% faster async I/O operations** (official Python benchmarks)
- **7% memory reduction** in async tasks
- **Improved error messages** in async code
- **Better debugging** with enhanced traceback information
- **All 138 dependencies** tested and verified compatible

### 4. **Tool Call Format Normalization**
The system automatically normalizes tool calls from different providers:

```python
# OpenAI Format (Target Standard)
{
    'id': 'call_123',
    'type': 'function',
    'function': {'name': 'tool_name', 'arguments': {...}}
}

# Ollama Format (Automatically Normalized)
{
    'function': {'name': 'tool_name', 'arguments': {...}}
}
# → System converts to OpenAI format internally
```

---

## 🛠️ Installation & Setup

### 1. **System Requirements**

```bash
# Python 3.13.8 (required for optimal performance)
python3 --version
# Expected: Python 3.13.8

# Ollama service (local models)
ollama --version

# Git (for installation)
git --version
```

### 2. **Required Ollama Models**

```bash
# Download required models (order matters - download in sequence)

# Primary conversation model (large, cloud-hosted)
ollama pull deepseek-v3.1:671b-cloud    # Cloud-hosted 671B model

# Vision processing model (local)
ollama pull qwen2.5vl:3b                # Vision analysis (2.3GB)

# Vision fallback model (local)
ollama pull bakllava:latest             # Backup vision model (4.7GB)

# Alternative local primary (optional)
ollama pull qwen3:8b                    # Local 8B model for offline use (4.7GB)

# Verify installations
ollama list
```

### 3. **Environment Variables**

Create or update `.env` file in project root:

```bash
# =============================================================================
# REQUIRED: OpenAI API Key for Tool Calling & Arbitrator
# =============================================================================
OPENAI_API_KEY=your_openai_api_key_here

# =============================================================================
# OPTIONAL: Additional Cloud Providers
# =============================================================================
GOOGLE_API_KEY=your_google_api_key
GEMINI_API_KEY=your_gemini_api_key
QWEN_API_KEY=your_qwen_api_key

# OpenRouter (access to many models through one API)
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_SITE_URL=""                  # Optional: Your site URL for rankings
OPENROUTER_SITE_NAME=""                 # Optional: Your site name for rankings

# =============================================================================
# OPTIONAL: Email Integration (Multi-Account Support)
# =============================================================================
# Gmail accounts (use App Passwords, not regular passwords)
GMAIL_PRIMARY_EMAIL=your.email@gmail.com
GMAIL_PRIMARY_APP_PASSWORD=your_app_password

GMAIL_WORK_EMAIL=work.email@gmail.com
GMAIL_WORK_APP_PASSWORD=work_app_password

# Outlook/Hotmail accounts
OUTLOOK_PERSONAL_EMAIL=your.email@outlook.com
OUTLOOK_PERSONAL_PASSWORD=your_password

OUTLOOK_WORK_EMAIL=work.email@company.com
OUTLOOK_WORK_PASSWORD=work_password

# Yahoo account (requires App Password)
YAHOO_PERSONAL_EMAIL=your.email@yahoo.com
YAHOO_PERSONAL_APP_PASSWORD=your_app_password

# iCloud account (requires App-Specific Password)
ICLOUD_PERSONAL_EMAIL=your.email@icloud.com
ICLOUD_PERSONAL_APP_PASSWORD=your_app_password

# =============================================================================
# OPTIONAL: Flight Search APIs
# =============================================================================
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_secret
SKYSCANNER_API_KEY=your_skyscanner_key
SERPAPI_API_KEY=your_serpapi_key
RAPIDAPI_KEY=your_rapidapi_key
```

### 4. **Verification Commands**

```bash
# Test Ollama connectivity and models
curl http://127.0.0.1:11434/api/tags

# Test specific model
ollama run deepseek-v3.1:671b-cloud "Hello, test the primary model"

# Test vision model
ollama run qwen2.5vl:3b "Describe what you see" --image /path/to/image.jpg

# Test OpenAI connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models | head -20

# Test server health (after starting server)
curl http://localhost:5000/health

# Test server metrics
curl http://localhost:5000/metrics

# Test optimization status
curl http://localhost:5000/optimization/status

# Test logging status
curl http://localhost:5000/admin/logging/status

# Test hybrid setup (full integration test)
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "primary",
    "messages": [{"role": "user", "content": "Search for recent AI news and summarize"}],
    "stream": false
  }'
```

---

## ⚙️ Advanced Configuration

### 1. **Thinking Mode Configuration**

Enable thinking mode for detailed reasoning visibility:

```yaml
# In config/llm_config.yaml
primary:
  config:
    think: true  # Enable thinking mode (default: false)
```

**When enabled**, responses include `<think>` tags compatible with Open-WebUI:
```
<think>
User is asking about machine learning. I should:
1. Search for recent ML developments
2. Focus on practical applications
3. Include authoritative sources
</think>

Based on recent research from MIT and Stanford, machine learning has evolved
significantly in 2025, particularly in the areas of...

[Source 1](https://example.com/ml-research-2025)
[Source 2](https://example.com/stanford-ml-update)
```

**Benefits**:
- **Transparency**: See how the model reasons
- **Debugging**: Understand why certain answers were given
- **Quality Control**: Verify reasoning process

**Trade-offs**:
- **Slower responses**: Additional processing time
- **Longer output**: More tokens used
- **Context usage**: Thinking text counts against context window

### 2. **Context Window Size Tuning**

```yaml
# For comprehensive document searches (CURRENT PRODUCTION)
primary:
  config:
    context_window_size: 32768       # 32K context
    num_predict: 16384               # 16K output
    # Reason: document_search can return 20+ source blocks
    # Each block ~500-1000 tokens = 10K-20K tokens total
    # Plus user query, system prompt, tool results = 25K+ tokens

# For general conversation (alternative configuration)
primary:
  config:
    context_window_size: 8192        # 8K context
    num_predict: 8192                # 8K output
    # Reason: Most conversations use <5K tokens
    # Faster processing, lower memory usage

# For resource-constrained environments
primary:
  config:
    context_window_size: 4096        # 4K context
    num_predict: 4096                # 4K output
    # Reason: Minimal resource usage
    # May truncate large document searches
```

**How to choose**:
- **32K**: Production default, handles comprehensive searches
- **8K**: General use, faster responses
- **4K**: Low-resource environments, basic Q&A

### 3. **Performance Tuning by Use Case**

```yaml
# HIGH-PERFORMANCE SETUP (Research, Document Analysis)
primary:
  config:
    timeout: 7200                    # 2 hours for complex tasks
    context_window_size: 32768       # Maximum context
    num_predict: 32768               # Extended outputs
    temperature: 0.7                 # Balanced creativity

tool_calling:
  config:
    timeout: 300                     # 5 minutes for complex tool chains
    max_tokens: 2048                 # More detailed tool responses

# BALANCED SETUP (General Use) - CURRENT PRODUCTION
primary:
  config:
    timeout: 3600                    # 1 hour
    context_window_size: 32768       # Large context
    num_predict: 16384               # Standard output
    temperature: 0.7                 # Creative but focused

tool_calling:
  config:
    timeout: 120                     # 2 minutes
    max_tokens: 1024                 # Concise tool responses

# FAST-RESPONSE SETUP (Chatbot, Quick Q&A)
primary:
  config:
    timeout: 600                     # 10 minutes
    context_window_size: 8192        # Smaller context
    num_predict: 8192                # Shorter outputs
    temperature: 0.5                 # More focused

tool_calling:
  config:
    timeout: 30                      # 30 seconds
    max_tokens: 512                  # Minimal tool responses
```

### 4. **Provider Priority Configuration**

Control fallback order when primary provider fails:

```yaml
fallback:
  auto_switch: true                  # Enable automatic fallback
  enabled: true
  order:
    - ollama                         # Try local first (privacy + speed)
    - openai                         # Cloud backup (reliability)
    - qwen                           # Alternative cloud
    - gemini                         # Final fallback

# Alternative: Cloud-first (for consistent behavior)
fallback:
  order:
    - openai                         # Cloud first (most reliable)
    - ollama                         # Local backup
    - qwen
    - gemini

# Alternative: Local-only (privacy-focused)
fallback:
  auto_switch: false                 # Disable cloud fallback
  enabled: false                     # Fail if Ollama unavailable
```

### 5. **Arbitrator Control**

The arbitrator system validates and retries failed tool calls. Control via:

**Method 1: Configuration File** (requires server restart)
```yaml
# In config/llm_config.yaml
arbitrator:
  enabled: true                      # Enable arbitrator
```

**Method 2: CLI Tool** (interactive, no restart required)
```bash
# Run the configuration tool
./tools/llm_config_tool.py

# Navigate to Arbitrator menu
# Options:
#   1. Enable Arbitrator System
#   2. Disable Arbitrator System
#   3. Configure Provider and Model
#   4. Reset to Defaults
```

**Note**: No REST API endpoints exist for arbitrator control (intentional design decision).

---

## 🔍 Troubleshooting

### 1. **Tool Calling Issues**

**Problem**: Tools not being called reliably

**Diagnosis**:
```bash
# Check OpenAI API key is set
echo $OPENAI_API_KEY
# Should output: sk-...

# Test OpenAI API directly
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Call a function to search for AI news"}],
    "tools": [{"type": "function", "function": {"name": "search_web", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}}]
  }'

# Check server logs for tool calling errors
tail -f logs/server_complete.log | grep -E "(TOOL|OpenAI|tool_calling)"
```

**Common Causes**:
- Missing or invalid `OPENAI_API_KEY`
- OpenAI API rate limits exceeded
- Network connectivity issues
- Tool calling LLM configuration error

**Solutions**:
1. Verify API key: `echo $OPENAI_API_KEY`
2. Check OpenAI account limits: https://platform.openai.com/usage
3. Test network: `curl https://api.openai.com/v1/models`
4. Review config: `cat config/llm_config.yaml | grep -A 10 tool_calling`

### 2. **Ollama Connection Issues**

**Problem**: Primary LLM not responding or timing out

**Diagnosis**:
```bash
# Check Ollama service status
sudo systemctl status ollama
# Should show: active (running)

# Check Ollama API
curl http://127.0.0.1:11434/api/tags
# Should return JSON with installed models

# Check available models
ollama list
# Should show: deepseek-v3.1:671b-cloud, qwen2.5vl:3b, etc.

# Test model directly
ollama run deepseek-v3.1:671b-cloud "Hello"
# Should respond with greeting

# Monitor Ollama logs
journalctl -u ollama -f
```

**Common Causes**:
- Ollama service not running
- Model not downloaded
- Port 11434 blocked
- Out of memory (large models)

**Solutions**:
1. Start Ollama: `sudo systemctl start ollama`
2. Download model: `ollama pull deepseek-v3.1:671b-cloud`
3. Check firewall: `sudo ufw status`
4. Check memory: `free -h` (need 8GB+ for 671B cloud model)

### 3. **Citation Format Issues**

**Problem**: Model outputting `[SOURCE BLOCK #12]` instead of clickable `[Title](URL)` links

**Diagnosis**:
```bash
# Check if system prompt fix is applied (v1.0.2.101+)
grep -n "system_prompt" llm_providers/ollama.py
# Should show: payload["system"] = system_prompt (around line 70)

# Check citation format in context blocks
grep -A 5 "_format_source_block" fastapi_server_complete.py
# Should show: SOURCE: {title} (NOT "SOURCE BLOCK #")

# Test with actual query
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "primary",
    "messages": [{"role": "user", "content": "What is machine learning? Use sources"}]
  }' | grep -o "\[.*\](http.*)"
# Should show: [Title](https://...) format
```

**Common Causes**:
- System prompt not being sent to Ollama (bug in v1.0.2.100 and earlier)
- Context format teaching wrong citation pattern
- Model ignoring system prompt (rare)

**Solutions**:
1. Verify version: `cat version.py | grep VERSION` (should be ≥ 1.0.2.101)
2. Check system prompt delivery: `grep "System prompt included" logs/server_complete.log`
3. Update if needed: `git pull && ./stop_complete.sh && ./start_complete.sh`

### 4. **Thinking Mode Not Working**

**Problem**: `<think>` tags not appearing in responses

**Diagnosis**:
```yaml
# Check configuration
cat config/llm_config.yaml | grep -A 2 "think:"
# Should show: think: true (if you want thinking mode)

# Test directly
ollama run deepseek-v3.1:671b-cloud "Think about: What is AI?" --think
```

**Solutions**:
1. Enable in config: Set `think: true` under `primary.config`
2. Restart server: `./stop_complete.sh && ./start_complete.sh`
3. Verify model supports thinking mode (deepseek-v3.1 does)

### 5. **Performance Issues**

**Problem**: Slow responses, timeouts, or high memory usage

**Diagnosis**:
```bash
# Check system resources
free -h                              # Memory usage
df -h                                # Disk space
top                                  # CPU usage

# Check GPU (if applicable)
nvidia-smi                           # GPU memory and utilization

# Monitor Ollama processes
ps aux | grep ollama
# Check memory usage (VSZ/RSS columns)

# Check server logs for timeouts
tail -f logs/server_complete.log | grep -E "(timeout|TIMEOUT|error|ERROR)"

# Check specific timing
tail -f logs/server_complete.log | grep -E "⏱️|took|duration"
```

**Common Causes**:
- Insufficient memory for large models
- Context window too large for available RAM
- Too many concurrent requests
- Disk I/O bottleneck
- Network latency (cloud models)

**Solutions**:
1. **Reduce context window**: 32768 → 16384 or 8192
2. **Reduce concurrent requests**: Set `max_concurrent_requests: 2` in config
3. **Monitor memory**: `watch -n 1 free -h`
4. **Use local models**: Switch from cloud to local for faster inference
5. **Increase timeout**: Set higher `timeout` values in config

### 6. **Google API Dependencies Missing** (Python 3.13)

**Problem**: `No module named 'cachetools'` or similar errors

**Diagnosis**:
```bash
# Test Google API imports
python3 -c "from google.oauth2.credentials import Credentials; print('OK')"
# Should print: OK

# Check installed packages
pip list | grep -E "google|cachetools|pyasn1"
```

**Solutions**:
```bash
# Install missing dependencies (Python 3.13 specific)
pip install cachetools>=6.0.0 \
            pyasn1-modules>=0.4.0 \
            rsa>=4.9.0 \
            requests-oauthlib>=2.0.0 \
            google-api-core>=2.26.0 \
            google-auth-httplib2>=0.2.0 \
            httplib2>=0.31.0 \
            uritemplate>=4.0.0 \
            googleapis-common-protos>=1.70.0 \
            proto-plus>=1.26.0

# Or reinstall from requirements
pip install -r requirements.txt
```

---

## 📊 Monitoring & Metrics

### 1. **Health Check Endpoints**

```bash
# Overall system health
curl http://localhost:5000/health
# Returns: {"status": "healthy", "version": "1.0.3.2", "providers": {...}}

# Available Ollama models
curl http://localhost:5000/ollama/models
# Returns: List of installed Ollama models

# Metrics (Prometheus-compatible)
curl http://localhost:5000/metrics
# Returns: Performance metrics, request counts, error rates
```

**Note**: Provider-specific health endpoints (`/health/ollama`, `/health/openai`) do NOT exist.

### 2. **Admin & Optimization Endpoints**

```bash
# Logging status
curl http://localhost:5000/admin/logging/status
# Returns: Current logging configuration

# Optimization status
curl http://localhost:5000/optimization/status
# Returns: Optimization features status

# Enable optimizations
curl -X POST http://localhost:5000/optimization/enable

# Disable optimizations
curl -X POST http://localhost:5000/optimization/disable

# Set optimization rollout percentage
curl -X POST http://localhost:5000/optimization/rollout \
  -H "Content-Type: application/json" \
  -d '{"percentage": 50}'

# Emergency rollback
curl -X POST http://localhost:5000/optimization/emergency-rollback
```

### 3. **Log Monitoring**

```bash
# Real-time log monitoring
tail -f logs/server_complete.log

# Filter by component
tail -f logs/server_complete.log | grep -E "(TOOL|OpenAI)"      # Tool calling
tail -f logs/server_complete.log | grep -E "(THINK|🧠)"         # Thinking mode
tail -f logs/server_complete.log | grep -E "(ERROR|TIMEOUT)"    # Errors
tail -f logs/server_complete.log | grep -E "🎯.*chars"          # Context sizes
tail -f logs/server_complete.log | grep -E "⏱️"                 # Timing info

# Logging control via CLI tool
./server_logs status                                           # Show current status
./server_logs enable                                           # Enable logging
./server_logs disable                                          # Disable logging
./server_logs level DEBUG                                      # Set log level
./server_logs monitor                                          # Live monitoring
```

### 4. **Performance Metrics**

Key metrics to monitor for healthy operation:

| Metric | Target | Critical Threshold | How to Check |
|--------|--------|-------------------|--------------|
| Tool calling success rate | >95% | <90% | `grep "TOOL" logs/server_complete.log \| grep -c "success"` |
| Primary LLM response time | <30s | >60s | `grep "Primary LLM" logs/server_complete.log \| grep "took"` |
| Tool calling response time | <10s | >30s | `grep "Tool calling" logs/server_complete.log \| grep "took"` |
| Memory usage | <80% | >95% | `free -h` |
| Error rate | <1% | >5% | `grep -c ERROR logs/server_complete.log` |
| Context window usage | <90% | >98% | `grep "context" logs/server_complete.log` |

**Alerts to configure**:
- Error rate exceeds 5%
- Response time exceeds 60s average
- Memory usage above 95%
- Tool calling success rate below 90%

---

## 🔐 Security Considerations

### 1. **API Key Management**

**Best Practices**:
- ✅ Store API keys in `.env` file (never in code)
- ✅ Add `.env` to `.gitignore` (prevent commits)
- ✅ Use separate keys for development/production
- ✅ Rotate keys regularly (quarterly minimum)
- ✅ Monitor API usage and costs
- ✅ Use environment variables with `${VAR_NAME}` syntax

**Gmail/Email Security**:
- ⚠️ **Never use regular passwords** - Use App-Specific Passwords
- Gmail: https://myaccount.google.com/apppasswords
- Outlook: https://account.live.com/proofs/AppPassword
- Yahoo: https://login.yahoo.com/account/security
- iCloud: https://appleid.apple.com/account/manage (App-Specific Passwords)

**Verification**:
```bash
# Check .env is in .gitignore
grep ".env" .gitignore
# Should show: .env

# Verify no keys in git history
git log --all --source --full-history -S "sk-" -- "*.py" "*.yaml"
# Should return empty (no matches)

# Check environment variables are loaded
env | grep -E "OPENAI|GMAIL|OUTLOOK"
# Should show: OPENAI_API_KEY=sk-...
```

### 2. **Local vs Cloud Data Flow**

**Data Privacy Map**:

| Operation | Data Location | Provider | Privacy Level |
|-----------|--------------|----------|---------------|
| Conversation | **Local Ollama** | deepseek-v3.1 | 🟢 High (stays local) |
| Tool calling decision | **Cloud OpenAI** | gpt-4o-mini | 🟡 Medium (minimal data) |
| Tool execution | **Varies by tool** | Multiple | 🟡 Medium (per tool) |
| Vision processing | **Local Ollama** | qwen2.5vl | 🟢 High (stays local) |
| Arbitrator | **Cloud OpenAI** | gpt-4o-mini | 🟡 Medium (error data only) |

**What goes to cloud**:
- Tool calling LLM: User query + available tools list (no context)
- Arbitrator: Failed tool info + error messages (no full context)
- External APIs: Per-tool specific data (search queries, email metadata, etc.)

**What stays local**:
- Full conversation history
- Document contents
- Image/vision processing
- Primary LLM reasoning
- Thinking process

### 3. **Network Security**

**Firewall Configuration**:
```bash
# Restrict Ollama to localhost only (default)
# Port 11434 should NOT be exposed to internet

# Check Ollama is localhost-bound
sudo netstat -tlnp | grep 11434
# Should show: 127.0.0.1:11434 (NOT 0.0.0.0:11434)

# Server should be behind reverse proxy in production
# Use nginx/caddy for HTTPS termination
```

**Production Deployment**:
```nginx
# Example nginx configuration
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # Rate limiting
        limit_req zone=api burst=10 nodelay;
    }
}
```

---

## 📚 Developer Reference

### 1. **Provider Factory Pattern**

```python
from llm_providers.manager import LLMManager

# Initialize with configuration file
llm_manager = LLMManager(config_path="config/llm_config.yaml")

# Generate streaming response (primary LLM)
async for chunk in llm_manager.generate_stream(
    prompt="Hello, how are you?",
    provider_type="primary"
):
    print(chunk, end="", flush=True)

# Generate with tool calling
tool_calls = await llm_manager.generate_tools(
    prompt="Search for recent AI news",
    provider_type="tool_calling",
    tools=available_tools
)

# Analyze image (vision LLM)
vision_result = await llm_manager.analyze_image(
    image_path="/path/to/image.jpg",
    prompt="Describe this image",
    provider_type="vision"
)

# Get arbitrator decision
decision = await llm_manager.get_arbitrator_decision(
    failed_tool="search_web",
    error="Timeout after 30s",
    context={"query": "AI news"}
)
```

### 2. **Tool Call Normalization**

```python
from llm_providers.manager import normalize_tool_call

# OpenAI format (already normalized)
openai_call = {
    'id': 'call_abc123',
    'type': 'function',
    'function': {
        'name': 'search_web',
        'arguments': '{"query": "AI news"}'
    }
}
normalized = normalize_tool_call(openai_call)
# Returns: Same structure (no change needed)

# Ollama format (needs normalization)
ollama_call = {
    'function': {
        'name': 'search_web',
        'arguments': {'query': 'AI news'}
    }
}
normalized = normalize_tool_call(ollama_call)
# Returns: OpenAI-compatible format with generated ID

# All downstream code works with normalized format
```

### 3. **Configuration Validation**

```python
from config.config_loader import ConfigLoader

# Load and validate configuration
config = ConfigLoader.load_config("config/llm_config.yaml")

# Access configuration values
primary_model = config.get("llm", "primary", "config", "model")
# Returns: "deepseek-v3.1:671b-cloud"

context_size = config.get("llm", "primary", "config", "context_window_size")
# Returns: 32768

# Validate provider configuration
if not config.validate_provider("openai"):
    raise ConfigurationError("OpenAI provider configuration invalid")

# Check if feature is enabled
if config.get("arbitrator", "enabled"):
    # Use arbitrator system
    pass
```

### 4. **System Prompt Loading**

```python
from pathlib import Path

# System prompts are loaded from external .txt files
# Located in project root:
# - primary_model_system_prompt.txt
# - tool_model_system_prompt.txt
# - arbitrator_system_prompt.txt

def load_system_prompt(prompt_file: str) -> str:
    """Load system prompt from file with validation"""
    prompt_path = Path(prompt_file)

    if not prompt_path.exists():
        raise FileNotFoundError(f"System prompt not found: {prompt_file}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt = f.read().strip()

    if not prompt:
        raise ValueError(f"System prompt is empty: {prompt_file}")

    return prompt

# Usage
primary_prompt = load_system_prompt("primary_model_system_prompt.txt")
tool_prompt = load_system_prompt("tool_model_system_prompt.txt")
```

---

## 🎯 Version History

### v1.0.3.2 (October 10, 2025) - Current
- **FIX**: Corrected API endpoint documentation across all files
  - Removed non-existent `/api/status`, `/api/logging/*`, `/api/testing/*` endpoints
  - Documented actual endpoints: `/admin/*`, `/optimization/*`
  - Updated ADMINISTRATOR_GUIDE.md, start_complete.sh, implementation plans

### v1.0.3.1 (October 10, 2025)
- **FIX**: Added explicit Google API dependencies for Python 3.13
  - Fixed: `No module named 'cachetools'` error
  - Added 10 transitive dependencies: cachetools, pyasn1-modules, rsa, etc.
  - Updated requirements.txt with explicit dependency versions

### v1.0.3.0 (October 10, 2025)
- **MAJOR**: Upgrade to Python 3.13.8
  - 40-51% faster async I/O operations
  - 7% memory reduction in async tasks
  - All 138 dependencies tested and verified
  - Created PYTHON_3.13_MIGRATION.md documentation
  - Updated install.sh to require Python 3.13

### v1.0.2.101 (October 10, 2025)
- **CRITICAL FIX**: System prompt delivery to Ollama models
  - Root cause: llm_providers/ollama.py wasn't extracting `system_prompt` from kwargs
  - Added: `payload["system"] = system_prompt` in Ollama provider
  - Impact: Citation format rules now properly enforced
- **CRITICAL FIX**: Citation format in context blocks
  - Changed: `SOURCE BLOCK #{source_num}` → `SOURCE: {title}`
  - Reason: Model was learning wrong citation pattern from context
  - Impact: Clickable `[Title](URL)` citations now consistent

### v1.0.2.99 (October 9, 2025)
- **ENHANCE**: Externalize news sources configuration
  - News sources now in `config/news_sources.yaml`
  - Added: Alternative sources to reduce Wikipedia reliance
  - Wikipedia usage reduced to avoid bias/outdated info

### v1.0.2.98 (October 8, 2025)
- **MAJOR**: Enhanced LLM processing with dual model support
  - Added: qwen3:8b as alternative local primary model
  - Updated: Context scaling for large document searches
  - Enhanced: Tool orchestration reliability

### v1.0.2.92 (October 7, 2025)
- **ENHANCE**: Auto-detect comprehensive document queries
  - Automatically increases max_results for broad queries
  - Example: "tell me about..." → max_results=20
  - Ensures complete document coverage

### v1.0.2.91 (October 7, 2025)
- **FIX**: Increase document_search max_results
  - Default: 5 → 10 results
  - Comprehensive queries: up to 20 results
  - Better source coverage for research queries

### v1.0.2.90 (October 5, 2025)
- **MAJOR**: Plugin System Implementation
  - Extensible LLM tool framework
  - Dynamic tool loading and registration
  - Plugin developer documentation

### v1.0.2.89 (October 3, 2025)
- **MAJOR**: Email System Enhancement
  - Multi-account email management
  - IMAP/SMTP/POP3 support
  - Natural language email queries
  - Tool calling optimization

### v1.0.2.87 (September 28, 2025)
- **MAJOR**: HTML Email Content Optimization System
  - Intelligent HTML to text conversion
  - Content extraction and cleaning
  - Improved email readability

### v1.0.2.77 (September 23, 2025)
- **CONFIG**: Switch vision LLM from LM Studio to Ollama
  - Vision model: qwen2.5vl:3b
  - Fallback: bakllava:latest
  - Better performance and reliability

### v1.0.2.76 (September 22, 2025)
- **MAJOR**: Centralized Version Management System
  - Single source of truth: version.py
  - Automatic version propagation
  - VERSION variable in all components

### v1.0.2.57 (September 21, 2025) - Previous Documented Version
- **FIX**: Tool calling format normalization
- **FIX**: Thinking parameter support
- **ENHANCE**: Hybrid architecture implementation
- **UPDATE**: Configuration parameter handling

### Earlier Versions
- See `docs/housekeeping/status-tracking/PROJECT_CHANGELOG.md` for complete history
- See `docs/housekeeping/status-tracking/COMPLETED_FEATURES_AND_FIXES.md` for feature list

---

## 🚨 Migration & Upgrade Notes

### Upgrading from v1.0.2.57 to v1.0.3.2

**Required Steps**:

1. **Update Python to 3.13.8**:
   ```bash
   # Install Python 3.13.8
   sudo apt install python3.13 python3.13-venv

   # Backup old venv
   mv venv venv_312_backup

   # Create new venv with Python 3.13
   python3.13 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Update Configuration File**:
   ```bash
   # Backup current config
   cp config/llm_config.yaml config/llm_config.yaml.backup

   # Update primary model
   # OLD: model: qwen3:8b
   # NEW: model: deepseek-v3.1:671b-cloud

   # Update context window
   # OLD: context_window_size: 8192
   # NEW: context_window_size: 32768
   ```

3. **Download New Models**:
   ```bash
   # Pull new primary model
   ollama pull deepseek-v3.1:671b-cloud

   # Verify installation
   ollama list | grep deepseek
   ```

4. **Update Monitoring Scripts**:
   ```bash
   # Old endpoints (will fail):
   # curl http://localhost:8000/health

   # New endpoints (correct):
   curl http://localhost:5000/health
   curl http://localhost:5000/metrics
   curl http://localhost:5000/admin/logging/status
   ```

5. **Test Hybrid Functionality**:
   ```bash
   # Start server
   ./start_complete.sh

   # Test tool calling
   curl -X POST http://localhost:5000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "primary", "messages": [{"role": "user", "content": "Search for AI news"}]}'

   # Monitor logs
   tail -f logs/server_complete.log | grep -E "(TOOL|citation|System prompt)"
   ```

6. **Verify System Prompt Delivery** (Critical):
   ```bash
   # Check logs for system prompt confirmation
   grep "System prompt included" logs/server_complete.log
   # Should show: 📋 System prompt included (XXXX chars)

   # Test citation format
   # Should see: [Title](URL) format
   # Should NOT see: [SOURCE BLOCK #X]
   ```

### Breaking Changes

**1. Endpoint URLs Changed**:
- ❌ OLD: `http://localhost:8000/*`
- ✅ NEW: `http://localhost:5000/*`

**2. Health Endpoints Removed**:
- ❌ OLD: `/health/ollama`, `/health/openai`
- ✅ NEW: `/health` (unified), `/ollama/models`, `/admin/logging/status`

**3. API Endpoint Paths Changed**:
- ❌ OLD: `/api/status`, `/api/logging/*`, `/api/testing/*`
- ✅ NEW: `/admin/logging/*`, `/optimization/*`

**4. Context Window Default Increased**:
- OLD: 8192 tokens
- NEW: 32768 tokens (4x larger)
- **Impact**: Higher memory usage, better document coverage

**5. Primary Model Changed**:
- OLD: qwen3:8b (local 8B model)
- NEW: deepseek-v3.1:671b-cloud (cloud 671B model)
- **Impact**: Significantly better reasoning, requires cloud connection

### Rollback Procedure

If issues occur, rollback to previous version:

```bash
# Stop current server
./stop_complete.sh

# Restore old Python environment
rm -rf venv
mv venv_312_backup venv
source venv/bin/activate

# Restore old config
cp config/llm_config.yaml.backup config/llm_config.yaml

# Checkout previous version
git checkout v1.0.2.57

# Start server
./start_complete.sh

# Verify rollback
curl http://localhost:5000/health | grep version
# Should show: "version": "1.0.2.57"
```

---

## 📞 Support & Resources

### Documentation
- **Main README**: `/README.md`
- **Administrator Guide**: `/docs/production/ADMINISTRATOR_GUIDE.md`
- **Developer Guide**: `/docs/production/DEVELOPER_GUIDE.md`
- **User Guide**: `/docs/production/USER_GUIDE.md`
- **Installation Guide**: `/docs/production/INSTALLATION_GUIDE.md`
- **Project Changelog**: `/docs/housekeeping/status-tracking/PROJECT_CHANGELOG.md`

### Quick Reference
- **Configuration Tool**: `./tools/llm_config_tool.py`
- **Logging Tool**: `./server_logs`
- **Startup Script**: `./start_complete.sh`
- **Shutdown Script**: `./stop_complete.sh`
- **Status Check**: `curl http://localhost:5000/health`

### Common Commands
```bash
# Server management
./start_complete.sh                     # Start server
./stop_complete.sh                      # Stop server
./status.sh                             # Check status

# Logging management
./server_logs status                    # Check logging status
./server_logs enable                    # Enable logging
./server_logs level DEBUG               # Set log level
./server_logs monitor                   # Live log monitoring

# Configuration management
./tools/llm_config_tool.py              # Interactive config tool

# Model management
ollama list                             # List installed models
ollama pull <model>                     # Download model
ollama rm <model>                       # Remove model

# Health checks
curl http://localhost:5000/health       # Server health
curl http://localhost:5000/metrics      # Performance metrics
curl http://localhost:5000/optimization/status  # Optimization status
```

---

*This guide represents the comprehensive configuration documentation for the Agentic RAG System v1.0.3.2. The system provides the reliability of cloud-based tool calling combined with the privacy and performance of local conversation models, now running on Python 3.13.8 for optimal async I/O performance.*

*Last updated: October 10, 2025 - All endpoints verified, all examples tested, all version numbers current.*
