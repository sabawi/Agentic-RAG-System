# LLM Configuration Guide v1.0.2.57
## Hybrid Architecture & Advanced Tool Calling System

**Last Updated**: September 21, 2025
**Version**: 1.0.2.57 - Ollama Tool Calling Critical Fix & Hybrid Architecture Implementation

---

## 🎯 Overview

The Agentic RAG System now features a **Hybrid LLM Architecture** that combines the benefits of local Ollama models with reliable cloud-based tool calling. This document covers all LLM configuration aspects for administrators, users, and developers.

### Architecture Summary
```
User Request → Tool Calling LLM (OpenAI) → Multi-Tool Execution → Primary LLM (Ollama) → Response
                     ↓                            ↓                        ↓
              [Reliable Tool Calls]        [19 AI Tools]         [Local Processing + Thinking]
```

---

## 🔧 Configuration File Structure

### Primary Configuration: `config/llm_config.yaml`

```yaml
# =============================================================================
# LLM Configuration File - Hybrid Architecture
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

llm:
  # =========================================================================
  # PRIMARY LLM - Handles main conversation and response generation
  # Uses LOCAL Ollama models for privacy, speed, and thinking capabilities
  # =========================================================================
  primary:
    type: ollama
    config:
      model: qwen3:8b                    # Primary conversation model
      timeout: 3600                     # 60 minutes for large contexts
      context_window_size: 8192         # Ollama num_ctx parameter
      temperature: 0.7                  # Creative responses
      num_predict: 16384                # Ollama output token limit
      max_tokens: 8192                  # Ignored for Ollama
      base_url: http://127.0.0.1:11434  # Local Ollama instance
      api_key: null                     # Not needed for local
      stream: true                      # Enable streaming responses
      think: false                      # Enable/disable thinking mode

  # =========================================================================
  # TOOL CALLING LLM - Handles tool orchestration and function calls
  # Uses CLOUD OpenAI for reliable, accurate tool calling
  # =========================================================================
  tool_calling:
    type: openai
    config:
      model: gpt-4o-mini               # Reliable tool calling model
      timeout: 60                     # Quick tool decisions
      context_window_size: 4096       # Sufficient for tool contexts
      temperature: 0.1                # Low for precise tool calling
      max_tokens: 1024                # Limited tool responses
      stream: false                   # Non-streaming for tools
      api_key: ${OPENAI_API_KEY}      # Required environment variable

  # =========================================================================
  # VISION PROCESSING - Handles image analysis and OCR
  # Uses LOCAL Ollama vision models for privacy
  # =========================================================================
  vision:
    type: ollama
    config:
      model: qwen2.5vl:3b             # Vision analysis model
      timeout: 3600                   # 60 minutes for vision processing
      base_url: http://127.0.0.1:11434
      fallback_model: bakllava:latest # Backup vision model
      think: false                    # Usually disabled for vision

  # =========================================================================
  # ARBITRATOR - Handles decision arbitration between conflicting results
  # Uses CLOUD OpenAI for neutral decision making
  # =========================================================================
  arbitrator:
    enabled: true
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

  # =========================================================================
  # FALLBACK CONFIGURATION - Auto-switching when primary fails
  # =========================================================================
  fallback:
    auto_switch: true
    enabled: true
    order:
      - ollama                        # Try local first
      - openai                        # Then cloud
      - qwen                          # Alternative cloud
      - gemini                        # Final fallback

  # =========================================================================
  # PROVIDER CONFIGURATIONS
  # =========================================================================
  providers:
    ollama:
      health_check_url: http://127.0.0.1:11434/api/tags
      retry_attempts: 3
      retry_delay: 2
    openai:
      api_key: ${OPENAI_API_KEY}
      base_url: https://api.openai.com/v1
      organization: null
      retry_attempts: 3
      retry_delay: 1
      models:
        primary: gpt-4o
        tool_calling: gpt-4o-mini
```

---

## 🚀 Key Features & Improvements

### 1. **Hybrid Architecture Benefits**
- **Local Privacy**: Primary conversations handled by local Ollama models
- **Reliable Tools**: Cloud OpenAI ensures consistent tool calling
- **Cost Effective**: Expensive reasoning on local, cheap tools on cloud
- **Thinking Mode**: Support for Open-WebUI compatible thinking tags

### 2. **Critical Bug Fixes Applied**
- **✅ FIXED**: Missing system prompt in Ollama tool calling requests
- **✅ FIXED**: Tool call format normalization across providers
- **✅ ENHANCED**: Thinking parameter support with proper tagging
- **✅ IMPROVED**: Timeout and parameter handling for large contexts

### 3. **Tool Call Format Normalization**
The system now automatically normalizes tool calls from different providers:

```python
# OpenAI Format (Target)
{
    'id': 'call_123',
    'type': 'function',
    'function': {'name': 'tool_name', 'arguments': {...}}
}

# Ollama Format (Normalized to OpenAI)
{
    'function': {'name': 'tool_name', 'arguments': {...}}
}
# → Automatically converted to OpenAI format
```

---

## 🛠️ Installation & Setup

### 1. **Required Models**

```bash
# Download required Ollama models
ollama pull qwen3:8b          # Primary conversation (8GB)
ollama pull qwen2.5vl:3b      # Vision processing (2.3GB)
ollama pull bakllava:latest   # Vision fallback (4.7GB)
```

### 2. **Environment Variables**

```bash
# Required for hybrid architecture
OPENAI_API_KEY=your_openai_api_key_here

# Optional cloud providers
GOOGLE_API_KEY=your_google_api_key
GEMINI_API_KEY=your_gemini_api_key
QWEN_API_KEY=your_qwen_api_key
```

### 3. **Verification Commands**

```bash
# Test Ollama models
ollama run qwen3:8b "Hello, test the primary model"
ollama run qwen2.5vl:3b "Describe this image: /path/to/image.jpg"

# Test OpenAI connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models | head -20

# Test hybrid setup
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "primary",
    "messages": [{"role": "user", "content": "Search for AI news and summarize"}],
    "tools": [{"type": "function", "function": {"name": "search_web", "description": "Search web"}}]
  }'
```

---

## ⚙️ Advanced Configuration

### 1. **Thinking Mode Configuration**

Enable thinking mode for detailed reasoning visibility:

```yaml
primary:
  config:
    think: true  # Enable thinking mode
```

When enabled, responses include `<think>` tags compatible with Open-WebUI:
```
<think>
User is asking about machine learning. I should search for recent information...
</think>

Based on recent research, machine learning has evolved significantly...
```

### 2. **Performance Tuning**

```yaml
# For high-performance setups
primary:
  config:
    timeout: 7200                    # 2 hours for complex tasks
    context_window_size: 32768       # Large context if model supports
    num_predict: 32768               # Extended outputs

# For resource-constrained environments
primary:
  config:
    timeout: 1800                    # 30 minutes
    context_window_size: 4096        # Smaller context
    num_predict: 8192                # Limited outputs
```

### 3. **Provider Priority Configuration**

```yaml
fallback:
  order:
    - ollama      # Always try local first
    - openai      # Reliable cloud backup
    - qwen        # Alternative cloud
    - gemini      # Final fallback
```

---

## 🔍 Troubleshooting

### 1. **Tool Calling Issues**

**Problem**: Tools not being called reliably
```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# Test tool calling endpoint directly
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Search for AI news"}],
    "tools": [{"type": "function", "function": {"name": "search_web"}}]
  }'
```

### 2. **Ollama Connection Issues**

**Problem**: Primary LLM not responding
```bash
# Check Ollama service
sudo systemctl status ollama

# Restart if needed
sudo systemctl restart ollama

# Check available models
ollama list

# Test model directly
ollama run qwen3:8b "Hello"
```

### 3. **Thinking Mode Not Working**

**Problem**: `<think>` tags not appearing
```yaml
# Ensure think parameter is enabled
primary:
  config:
    think: true
```

### 4. **Performance Issues**

**Problem**: Slow responses or timeouts
```bash
# Check system resources
free -h
nvidia-smi  # If using GPU

# Monitor Ollama processes
ps aux | grep ollama

# Check server logs
tail -f logs/server_complete.log | grep -E "(OLLAMA|TIMEOUT)"
```

---

## 📊 Monitoring & Metrics

### 1. **Health Check Endpoints**

```bash
# Overall system health
curl http://localhost:8000/health

# Provider-specific health
curl http://localhost:8000/health/ollama
curl http://localhost:8000/health/openai
```

### 2. **Log Monitoring**

```bash
# Tool calling logs
tail -f logs/server_complete.log | grep -E "(TOOL|OpenAI)"

# Ollama thinking logs
tail -f logs/server_complete.log | grep -E "(THINK|🧠)"

# Performance logs
tail -f logs/server_complete.log | grep -E "(timeout|error|failed)"
```

### 3. **Performance Metrics**

Key metrics to monitor:
- **Tool calling success rate**: Should be >95% with OpenAI
- **Response times**: Primary <30s, Tools <10s
- **Error rates**: Should be <1% overall
- **Memory usage**: Monitor Ollama model loading

---

## 🔐 Security Considerations

### 1. **API Key Management**
- Store OpenAI API keys in environment variables only
- Never commit API keys to version control
- Use separate keys for development/production
- Monitor API usage and costs

### 2. **Local vs Cloud Data**
- **Local Ollama**: All conversation data stays local
- **Cloud OpenAI**: Only tool calling decisions sent to cloud
- **Minimize exposure**: Tool calls contain minimal user data

### 3. **Network Security**
- Restrict external access to Ollama (port 11434)
- Use HTTPS for all external API calls
- Monitor outbound connections to OpenAI

---

## 📚 Developer Reference

### 1. **Provider Factory Pattern**

```python
from llm_providers.manager import LLMManager

# Initialize with hybrid config
llm_manager = LLMManager(config_path="config/llm_config.yaml")

# Use for different purposes
primary_response = await llm_manager.generate_stream("Hello", "primary")
tool_calls = await llm_manager.generate_tools("Search web", "tool_calling", tools)
vision_result = await llm_manager.analyze_image("image.jpg", "vision")
```

### 2. **Tool Call Normalization**

```python
from llm_providers.manager import normalize_tool_call

# Automatically handles different formats
normalized = normalize_tool_call(ollama_tool_call)
# Returns OpenAI-compatible format regardless of input
```

### 3. **Configuration Validation**

```python
# Built-in validation for all provider configs
if not llm_manager.validate_config():
    raise ConfigurationError("Invalid LLM configuration")
```

---

## 🎯 Version History

### v1.0.2.57 (Current)
- **CRITICAL FIX**: Resolved missing system prompt in Ollama tool calling
- **NEW**: Hybrid architecture (Ollama + OpenAI)
- **ENHANCED**: Tool call format normalization
- **IMPROVED**: Thinking mode with Open-WebUI compatibility
- **UPDATED**: Configuration parameter handling

### v1.0.2.56
- **RESEARCH**: Extensive model testing (llama3.2:3b, qwen2.5:7b-instruct)
- **DEBUG**: Tool calling empty function name analysis
- **PROTOTYPE**: Enhanced prompting strategies

### Previous Versions
- See `docs/PROJECT_CHANGELOG.md` for complete history

---

## 🚨 Migration Notes

### Upgrading from v1.0.2.55 and earlier:

1. **Update configuration file** with new hybrid settings
2. **Download required models** (qwen3:8b, qwen2.5vl:3b)
3. **Set OpenAI API key** in environment variables
4. **Test hybrid functionality** with tool calling
5. **Monitor logs** for any migration issues

### Breaking Changes:
- Tool calling now requires OpenAI API key
- Configuration parameter names standardized
- Some legacy model references may need updating

---

*This guide represents the comprehensive configuration documentation for the Hybrid LLM Architecture. The system now provides the reliability of cloud-based tool calling combined with the privacy and performance of local conversation models.*