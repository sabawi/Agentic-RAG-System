# Agent Model CLI Tool - Quick Reference Guide

## Overview

The `agent_model.py` CLI tool provides easy management of LLM model configurations through named aliases. Instead of manually editing YAML files, you can quickly switch between different model configurations using simple commands.

## Features

- **Create model aliases** with full configuration (provider, model, timeout, temperature, etc.)
- **List all configured aliases** with active status indicators
- **Switch models** for primary, tool_calling, or arbitrator roles
- **Update/delete aliases** as needed
- **View current active models** at a glance
- **Color-coded output** for better readability

## Quick Start

### 1. Check Current Active Models
```bash
./agent_model.py status
```

### 2. List All Aliases
```bash
./agent_model.py ls
```

### 3. Create Your First Alias
```bash
# Local Ollama model
./agent_model.py add --alias my_local_qwen \
  --provider ollama \
  --model qwen3:8b \
  --description "My local Qwen model"

# OpenRouter model
./agent_model.py add --alias my_deepseek \
  --provider openrouter \
  --model deepseek/deepseek-r1 \
  --timeout 3600 \
  --temperature 0.7

# OpenAI model
./agent_model.py add --alias gpt4_mini \
  --provider openai \
  --model gpt-4o-mini \
  --timeout 120 \
  --temperature 0.1
```

### 4. Set an Alias as Active
```bash
# Set as primary LLM
./agent_model.py set --alias my_local_qwen --as primary

# Set as tool calling LLM
./agent_model.py set --alias gpt4_mini --as tool_calling

# Set as arbitrator
./agent_model.py set --alias gpt4_mini --as arbitrator
```

## Command Reference

### `ls` - List All Aliases
```bash
./agent_model.py ls
```
Shows all configured model aliases with:
- Provider and model name
- Configuration parameters (timeout, temperature, max tokens)
- Active status (PRIMARY, TOOL_CALLING, ARBITRATOR)
- Creation date

### `add` - Create New Alias
```bash
./agent_model.py add --alias NAME --provider TYPE --model MODEL [OPTIONS]
```

**Required Parameters:**
- `--alias NAME` - Unique name for this alias
- `--provider TYPE` - Provider type: `ollama`, `openai`, `openrouter`, `qwen`
- `--model MODEL` - Model identifier

**Optional Parameters:**
- `--timeout N` - Timeout in seconds (default: provider-specific)
- `--temperature N` - Temperature 0.0-2.0 (default: provider-specific)
- `--max-tokens N` - Max tokens to generate (default: provider-specific)
- `--context-window N` - Context window size
- `--think` - Enable think mode (Ollama reasoning models like DeepSeek)
- `--no-think` - Disable think mode (Ollama reasoning models)
- `--description TEXT` - Human-readable description

**Examples:**
```bash
# Minimal Ollama alias
./agent_model.py add --alias local_llama \
  --provider ollama \
  --model llama3.2:3b

# Full OpenRouter configuration
./agent_model.py add --alias cloud_deepseek \
  --provider openrouter \
  --model deepseek/deepseek-r1 \
  --timeout 3600 \
  --temperature 0.7 \
  --max-tokens 16384 \
  --context-window 32768 \
  --description "DeepSeek R1 for reasoning tasks"

# OpenAI with custom settings
./agent_model.py add --alias gpt4_turbo \
  --provider openai \
  --model gpt-4-turbo-preview \
  --timeout 300 \
  --temperature 0.3 \
  --max-tokens 4096

# DeepSeek reasoning model with think mode disabled
./agent_model.py add --alias deepseek_cloud \
  --provider ollama \
  --model deepseek-v3.1:671b-cloud \
  --timeout 600 \
  --max-tokens 16384 \
  --no-think \
  --description "DeepSeek V3.1 via Ollama without reasoning display"
```

### `update` - Update Existing Alias
```bash
./agent_model.py update --alias NAME [OPTIONS]
```

Update any parameter of an existing alias:
```bash
# Change model version
./agent_model.py update --alias local_llama --model llama3.2:7b

# Adjust timeout and temperature
./agent_model.py update --alias cloud_deepseek \
  --timeout 1800 \
  --temperature 0.5

# Update description
./agent_model.py update --alias gpt4_turbo \
  --description "GPT-4 Turbo for complex tasks"
```

### `delete` - Remove Alias
```bash
./agent_model.py delete --alias NAME [--force]
```

- Prevents deletion if alias is currently active (unless `--force` used)
- Permanently removes alias from configuration

**Examples:**
```bash
# Safe delete (fails if in use)
./agent_model.py delete --alias old_model

# Force delete (even if active)
./agent_model.py delete --alias old_model --force
```

### `show` - Show Alias Details
```bash
./agent_model.py show --alias NAME
```

Displays complete configuration for an alias:
```bash
./agent_model.py show --alias my_local_qwen
```

Output shows all parameters including timestamps and provider-specific settings.

### `set` - Set Active Model
```bash
./agent_model.py set --alias NAME --as ROLE
```

**Roles:**
- `primary` - Main LLM for user queries
- `tool_calling` - LLM that decides which tools to call
- `arbitrator` - LLM that analyzes tool execution and optimizes

**Examples:**
```bash
# Switch primary to local model
./agent_model.py set --alias local_llama --as primary

# Use GPT-4 mini for tool calling
./agent_model.py set --alias gpt4_mini --as tool_calling

# Set arbitrator
./agent_model.py set --alias gpt4_mini --as arbitrator
```

### `status` - Show Active Models
```bash
./agent_model.py status
```

Displays currently active models for each role:
- PRIMARY - Main LLM
- TOOL_CALLING - Tool selection LLM
- ARBITRATOR - Optimization LLM

## Provider-Specific Defaults

### Ollama
- **Base URL:** `http://127.0.0.1:11434`
- **Timeout:** 600s
- **Temperature:** 0.7
- **Max Tokens:** 4096
- **No API key required**

### OpenAI
- **Base URL:** `https://api.openai.com/v1`
- **Timeout:** 120s
- **Temperature:** 0.1
- **Max Tokens:** 2048
- **API Key:** Reads from `$OPENAI_API_KEY`

### OpenRouter
- **Base URL:** `https://openrouter.ai/api/v1`
- **Timeout:** 600s
- **Temperature:** 0.7
- **Max Tokens:** 4096
- **API Key:** Reads from `$OPENROUTER_API_KEY`
- **Custom Headers:** HTTP-Referer, X-Title for rankings

### Qwen (Alibaba Cloud)
- **Base URL:** `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **Timeout:** 300s
- **Temperature:** 0.7
- **Max Tokens:** 4096
- **API Key:** Reads from `$DASHSCOPE_API_KEY`

## Common Workflows

### Switching from Cloud to Local
```bash
# Check current setup
./agent_model.py status

# Create local alias if not exists
./agent_model.py add --alias qwen_local_fast \
  --provider ollama \
  --model qwen3:8b

# Switch primary to local
./agent_model.py set --alias qwen_local_fast --as primary

# Verify change
./agent_model.py status
```

### Creating a New OpenRouter Model
```bash
# Add alias with full configuration
./agent_model.py add --alias my_claude \
  --provider openrouter \
  --model anthropic/claude-3.5-sonnet \
  --timeout 600 \
  --temperature 0.8 \
  --max-tokens 8192 \
  --description "Claude 3.5 Sonnet via OpenRouter"

# Set as primary
./agent_model.py set --alias my_claude --as primary
```

### Testing Different Temperatures
```bash
# Create multiple aliases with same model, different temps
./agent_model.py add --alias gpt4_creative \
  --provider openai \
  --model gpt-4o \
  --temperature 1.2

./agent_model.py add --alias gpt4_precise \
  --provider openai \
  --model gpt-4o \
  --temperature 0.1

# Switch between them as needed
./agent_model.py set --alias gpt4_creative --as primary
./agent_model.py set --alias gpt4_precise --as primary
```

## Configuration Files

### Model Aliases Database
- **Location:** `config/model_aliases.json`
- **Format:** JSON
- **Backup:** Recommended before major changes
- **Manual Edit:** Possible but not recommended

### LLM Configuration
- **Location:** `config/llm_config.yaml`
- **Modified by:** `set` command
- **Preserved:** Comments and other sections
- **Format:** YAML

## Tips and Best Practices

1. **Use Descriptive Alias Names**
   ```bash
   # Good
   ./agent_model.py add --alias local_qwen_8b_reasoning ...

   # Less clear
   ./agent_model.py add --alias model1 ...
   ```

2. **Add Descriptions**
   - Helps remember what each alias is for
   - Shows in `ls` output
   ```bash
   --description "Fast local model for quick queries"
   ```

3. **Check Status Regularly**
   ```bash
   ./agent_model.py status
   ```
   Know which models are active before testing

4. **List Before Switching**
   ```bash
   ./agent_model.py ls
   ```
   See what's available and their configurations

5. **Backup Aliases**
   ```bash
   cp config/model_aliases.json config/model_aliases.backup.json
   ```

6. **Test After Switching**
   - Restart server after changing models
   - Test with simple query first
   ```bash
   ./stop_complete.sh && ./start_complete.sh
   ```

## Troubleshooting

### Alias Already Exists
```bash
Error: Alias 'my_model' already exists.
Use './agent_model.py update --alias my_model' to modify it.
```
**Solution:** Use `update` instead of `add`, or choose a different name

### Alias Not Found
```bash
Error: Alias 'nonexistent' not found.
```
**Solution:** Check spelling, use `./agent_model.py ls` to see available aliases

### Cannot Delete Active Alias
```bash
Warning: Alias 'my_model' is currently active for: primary
Use --force to delete anyway.
```
**Solution:** Switch to different model first, or use `--force`

### Provider Not Supported
```bash
Error: Unknown provider 'custom'
Supported providers: ollama, openai, openrouter, qwen
```
**Solution:** Use one of the supported providers

## Integration with Server

After changing model configurations:

1. **Stop the server:**
   ```bash
   ./stop_complete.sh
   ```

2. **Verify configuration:**
   ```bash
   ./agent_model.py status
   ```

3. **Start the server:**
   ```bash
   ./start_complete.sh
   ```

4. **Test with a simple query:**
   ```bash
   curl -X POST http://localhost:5000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "primary", "messages": [{"role": "user", "content": "Hello"}]}'
   ```

## Version Information

- **Version:** 1.0.0
- **Last Updated:** 2025-10-12
- **Compatibility:** Agentic-RAG Server v1.0.3.5+
- **Python:** 3.8+
- **Dependencies:** PyYAML

## See Also

- [LLM Configuration Guide](LLM_CONFIGURATION_GUIDE.md) - Detailed configuration documentation
- [Administrator Guide](production/ADMINISTRATOR_GUIDE.md) - Server management
- [Project Configuration Directive](PROJECT_CONFIGURATION_DIRECTIVE.md) - Configuration rules
