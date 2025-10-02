# Plugin System User Guide

**Created:** 2025-10-02
**Version:** 1.0.0
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start (5 Minutes)](#quick-start)
3. [Plugin Examples](#plugin-examples)
4. [Creating Your Own Plugin](#creating-your-own-plugin)
5. [Testing Plugins](#testing-plugins)
6. [Security Guidelines](#security-guidelines)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## 🎯 Overview

The Agentic-RAG Plugin System allows you to extend the LLM's capabilities by creating custom tools. Each plugin:

- **Runs in isolation** - Plugin crashes don't affect the server
- **Has resource limits** - Memory, CPU, and timeout controls
- **Is security-validated** - Input/output validation, injection detection
- **Auto-disables on failure** - Degraded mode protects system health

### What You Need

- **2 files**: YAML definition + Python handler
- **5 minutes**: Copy example, customize, test
- **No coding in server**: Plugins are completely separate

---

## 🚀 Quick Start

### Step 1: Copy an Example (2 minutes)

```bash
cd /home/sabawi/Development/flaskserver/plugins

# Copy the fortune plugin as template
cp fortune_message.yaml my_plugin.yaml
cp handlers/fortune_message.py handlers/my_plugin.py
```

### Step 2: Customize the YAML (2 minutes)

Edit `my_plugin.yaml`:

```yaml
metadata:
  name: "my_plugin"  # ← Change this
  version: "1.0.0"
  category: "productivity"  # productivity | system | data | iot | communications
  author: "Your Name"
  description: "What your plugin does"  # ← LLM sees this

execution:
  handler: "handlers/my_plugin.py"  # ← Point to your handler
  timeout: 30  # seconds

parameters:
  properties:
    your_param:  # ← Your parameters
      type: "string"
      description: "What this parameter does"
  required:
    - your_param
```

### Step 3: Write Handler Code (1 minute)

Edit `handlers/my_plugin.py`:

```python
async def execute(parameters):
    your_param = parameters['your_param']

    # Your logic here
    result = f"Processed: {your_param}"

    return {
        "success": True,
        "result": result,
        "error": None
    }
```

### Step 4: Test It!

```bash
echo '{"your_param": "test"}' | python3 handlers/my_plugin.py
```

### Step 5: Deploy

```bash
./stop_complete.sh && ./start_complete.sh
```

**Done!** Your plugin is now available to the LLM.

---

## 📚 Plugin Examples

### Example 1: Fortune Message (Beginner)

**What it does:** Returns random fortune cookie messages
**Category:** Productivity
**External dependency:** Linux `fortune` command

**Files:**
- `fortune_message.yaml` - Definition
- `handlers/fortune_message.py` - Implementation

**Key features:**
- External command execution (`fortune`)
- Multiple output formats (boxed, quoted, plain)
- Simple parameters (enum validation)

**Use case:** "Give me an inspiring quote"

---

### Example 2: Weather Info (API Integration)

**What it does:** Gets current weather for any city
**Category:** Productivity
**External dependency:** wttr.in API (via curl)

**Files:**
- `weather_info.yaml` - Definition
- `handlers/weather_info.py` - Implementation

**Key features:**
- Network access (whitelisted domain)
- External API calls
- Error handling (city not found, timeout)

**Use case:** "What's the weather in Tokyo?"

---

### Example 3: File Stats (Filesystem Access)

**What it does:** Analyzes files and directories
**Category:** System
**External dependency:** None (uses Python stdlib)

**Files:**
- `file_stats.yaml` - Definition
- `handlers/file_stats.py` - Implementation

**Key features:**
- Filesystem access (read-only, whitelisted paths)
- Directory traversal (optional recursive)
- Size calculations, file counts

**Use case:** "How big is the /plugins directory?"

---

### Example 4: System Monitor (Resource Monitoring)

**What it does:** Monitors CPU, memory, disk, processes
**Category:** System
**External dependency:** psutil library

**Files:**
- `system_monitor.yaml` - Definition
- `handlers/system_monitor.py` - Implementation

**Key features:**
- System metrics collection
- Top processes by CPU/memory
- Multiple metric types

**Use case:** "What's the CPU usage?"

---

### Example 5: Text Analyzer (Data Processing)

**What it does:** Analyzes text for statistics and sentiment
**Category:** Data
**External dependency:** None (uses Python stdlib)

**Files:**
- `text_analyzer.yaml` - Definition
- `handlers/text_analyzer.py` - Implementation

**Key features:**
- Text statistics (word count, reading time)
- Word frequency analysis
- Sentiment analysis (simple)
- Readability metrics (Flesch score)

**Use case:** "Analyze this essay for readability"

---

## 🛠️ Creating Your Own Plugin

### Plugin Architecture

```
User Request
     ↓
LLM decides to call plugin
     ↓
PluginManager.execute_plugin()
     ↓
SecurityValidator.validate_inputs()
     ↓
PluginExecutor (subprocess)
     ├─→ Read stdin (JSON parameters)
     ├─→ Execute your handler
     ├─→ Write stdout (JSON result)
     └─→ Exit
     ↓
SecurityValidator.validate_outputs()
     ↓
Return result to LLM
```

### YAML Definition Structure

```yaml
metadata:
  name: "plugin_name"              # REQUIRED: unique ID
  version: "1.0.0"                 # REQUIRED: semantic version
  category: "productivity"         # REQUIRED: category
  author: "Your Name"              # REQUIRED
  description: |                   # REQUIRED: LLM sees this
    Detailed description of what the plugin does.
    Use this when user asks about...
  tags:                           # OPTIONAL
    - keyword1
    - keyword2

execution:
  type: "python"                   # REQUIRED: python | executable
  handler: "handlers/my_plugin.py" # REQUIRED: path to code
  entrypoint: "execute"            # REQUIRED: function name
  timeout: 30                      # OPTIONAL: default 60s
  memory_limit: 256                # OPTIONAL: default 256MB
  cpu_limit: 1.0                   # OPTIONAL: default 1.0 core
  environment:                     # OPTIONAL: env vars
    API_KEY: "${MY_API_KEY}"      # Expands from .env

parameters:                        # REQUIRED: JSON Schema
  type: "object"
  properties:
    param1:
      type: "string"
      description: "What this does"
      enum: ["option1", "option2"] # OPTIONAL: restrict values
    param2:
      type: "integer"
      minimum: 1
      maximum: 100
  required:
    - param1                       # List required params

security:                          # OPTIONAL: defaults from plugin_defaults.yaml
  network:
    enabled: false                 # true to allow network
    allowed_domains:               # Whitelist
      - api.example.com
    allowed_ports:
      - 443
  filesystem:
    read_only: true                # false to allow writes
    allowed_paths:                 # Whitelist
      - /tmp
      - /var/data
    blocked_paths:                 # Blacklist
      - /etc
      - /root

monitoring:
  log_level: "INFO"                # DEBUG | INFO | WARNING | ERROR
  log_execution: true              # Log each execution
  log_parameters: true             # Log input parameters

error_handling:
  retry:
    enabled: true
    max_attempts: 3
  degraded_mode:
    enabled: true
    disable_after_failures: 5      # Auto-disable threshold
```

### Python Handler Structure

```python
#!/usr/bin/env python3
import sys
import json
import asyncio
from typing import Dict, Any

async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plugin entrypoint.

    Args:
        parameters: Validated input from YAML schema

    Returns:
        {
            "success": bool,      # REQUIRED
            "result": Any,        # REQUIRED (your data)
            "error": str | None,  # OPTIONAL (error message)
            "metadata": dict      # OPTIONAL (extra info)
        }
    """
    try:
        # 1. Extract parameters
        param1 = parameters['param1']
        param2 = parameters.get('param2', 'default')

        # 2. Do your work
        result = your_function(param1, param2)

        # 3. Return success
        return {
            "success": True,
            "result": result,
            "error": None,
            "metadata": {
                "param1": param1,
                "processed": True
            }
        }

    except Exception as e:
        # 4. Return failure
        return {
            "success": False,
            "result": None,
            "error": f"Error: {str(e)}",
            "metadata": {"error_type": type(e).__name__}
        }

# Communication protocol (REQUIRED - don't change this)
if __name__ == "__main__":
    try:
        input_data = sys.stdin.read()
        parameters = json.loads(input_data)
        result = asyncio.run(execute(parameters))
        print(json.dumps(result))
        sys.exit(0 if result['success'] else 1)
    except Exception as e:
        error_result = {
            "success": False,
            "result": None,
            "error": f"Plugin error: {str(e)}",
            "metadata": {}
        }
        print(json.dumps(error_result))
        sys.exit(1)
```

---

## 🧪 Testing Plugins

### Manual Testing (Before Deployment)

```bash
# Test with valid input
echo '{"param1": "value1"}' | python3 handlers/my_plugin.py

# Test with invalid input
echo '{"invalid": "data"}' | python3 handlers/my_plugin.py

# Test with edge cases
echo '{"param1": ""}' | python3 handlers/my_plugin.py

# Check exit code
echo '{"param1": "test"}' | python3 handlers/my_plugin.py
echo "Exit code: $?"  # Should be 0 for success, 1 for failure
```

### Validate JSON Output

```bash
echo '{"param1": "test"}' | python3 handlers/my_plugin.py | python3 -m json.tool
```

### Test via PluginManager (After Deployment)

```python
from plugins.plugin_manager import PluginManager

manager = PluginManager(plugins_dir, config)
await manager.initialize()

result = await manager.execute_plugin(
    'my_plugin',
    {'param1': 'test'}
)

print(result)
```

### Integration Test Script

See `/tests/utilities/test_all_plugins.py` for comprehensive examples.

---

## 🔒 Security Guidelines

### 1. Network Access

**Default:** Network is DISABLED

**Enable only if needed:**

```yaml
security:
  network:
    enabled: true
    allowed_domains:
      - api.example.com      # Only allow specific domains
    allowed_ports:
      - 443                   # Only allow HTTPS
```

**⚠️ Never enable network without whitelisting domains!**

### 2. Filesystem Access

**Default:** Read-only, no restrictions

**Restrict paths:**

```yaml
security:
  filesystem:
    read_only: true           # Prevent writes
    allowed_paths:            # Whitelist allowed directories
      - /tmp/plugin_data
      - /var/app_data
    blocked_paths:            # Blacklist sensitive directories
      - /etc/shadow
      - /root
      - /home/user/.ssh
```

**⚠️ Never allow write access to system directories!**

### 3. Input Validation

**Use JSON Schema:**

```yaml
parameters:
  properties:
    count:
      type: "integer"
      minimum: 1
      maximum: 100          # Prevent resource exhaustion
    text:
      type: "string"
      maxLength: 10000      # Prevent large inputs
```

**Injection detection is automatic:**
- SQL injection
- Command injection
- XSS attacks
- Path traversal

### 4. Resource Limits

**Set appropriate limits:**

```yaml
execution:
  timeout: 30               # Short for simple tasks
  memory_limit: 128         # Match task requirements
  cpu_limit: 0.5            # Limit CPU usage
```

**Guidelines:**
- Simple text processing: 10-30s timeout, 128MB memory
- API calls: 30-60s timeout, 256MB memory
- Data processing: 60-120s timeout, 512MB memory

### 5. Environment Variables

**Store secrets in .env:**

```bash
# In .env file
WEATHER_API_KEY=abc123xyz
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

**Reference in YAML:**

```yaml
execution:
  environment:
    API_KEY: "${WEATHER_API_KEY}"
```

**⚠️ Never hardcode secrets in YAML or Python!**

---

## 🐛 Troubleshooting

### Problem: Plugin not discovered

**Check:**
1. YAML file is in `/plugins/` root (not in subdirectories)
2. File extension is `.yaml` or `.yml`
3. YAML syntax is valid: `python3 -m yaml plugins/my_plugin.yaml`

### Problem: "Plugin handler not found"

**Check:**
1. Handler path in YAML matches actual file location
2. Handler file exists: `ls -la plugins/handlers/my_plugin.py`
3. Handler is executable: `chmod +x plugins/handlers/my_plugin.py`

### Problem: JSON decode error

**Check:**
1. Handler outputs valid JSON: `echo '{}' | python3 handlers/my_plugin.py | python3 -m json.tool`
2. No print statements before JSON output
3. Result dictionary has required fields

### Problem: Input validation failed

**Check:**
1. Required parameters are provided
2. Parameter types match schema (string vs integer)
3. Enum values are valid
4. Value constraints met (min, max, minLength, maxLength)

### Problem: Plugin times out

**Solutions:**
1. Increase timeout in YAML: `timeout: 120`
2. Optimize handler code
3. Break into multiple smaller plugins

### Problem: Permission denied

**Check:**
1. Path is in `allowed_paths` list
2. Path is not in `blocked_paths` list
3. File permissions allow read access

### Problem: Network request fails

**Check:**
1. Network is enabled: `enabled: true`
2. Domain is whitelisted: `allowed_domains`
3. Port is whitelisted: `allowed_ports`
4. curl/requests works manually

---

## ✅ Best Practices

### 1. Plugin Design

**Single Responsibility:**
- ✅ One plugin, one task
- ❌ Don't combine unrelated functions

**Clear Descriptions:**
```yaml
description: |
  Get current weather for a city using wttr.in API.
  Use this when user asks about weather, temperature, or conditions.
```

### 2. Parameters

**Descriptive Names:**
- ✅ `city`, `temperature_unit`, `format_style`
- ❌ `p1`, `param`, `data`

**Sensible Defaults:**
```yaml
format_style:
  default: "brief"
  enum: ["brief", "detailed"]
```

**Constraints:**
```yaml
count:
  type: "integer"
  minimum: 1
  maximum: 100  # Prevent abuse
```

### 3. Error Handling

**Informative Errors:**
```python
return {
    "success": False,
    "error": "City 'XYZ' not found. Please check spelling.",
    "metadata": {"city": city, "available": False}
}
```

**Not:**
```python
return {
    "success": False,
    "error": "Error",  # Too vague!
    "metadata": {}
}
```

### 4. Output Formatting

**User-Friendly:**
```python
result = f"""
🌤️  Weather for {city}:
  Temperature: {temp}°F
  Conditions: {conditions}
  Humidity: {humidity}%
"""
```

**Rich Metadata:**
```python
"metadata": {
    "city": city,
    "temperature": temp,
    "units": "fahrenheit",
    "data_source": "wttr.in",
    "timestamp": datetime.now().isoformat()
}
```

### 5. Testing

**Test All Paths:**
- ✅ Valid inputs
- ✅ Invalid inputs
- ✅ Edge cases (empty, max length)
- ✅ Error conditions

**Manual Test First:**
```bash
echo '{"param": "test"}' | python3 handlers/my_plugin.py
```

**Then Integration Test:**
```bash
./stop_complete.sh && ./start_complete.sh
# Test via LLM
```

### 6. Documentation

**In-Code Comments:**
```python
def execute(parameters):
    """
    Execute weather lookup.

    Args:
        parameters: {"city": str, "units": str}

    Returns:
        Weather data or error
    """
```

**Metadata in YAML:**
```yaml
metadata:
  description: |
    Detailed explanation of what this does.
    When to use it.
    What it returns.
```

---

## 📊 Plugin Categories

| Category | Use For | Examples |
|----------|---------|----------|
| **productivity** | General tools, information | Weather, fortune, calendar |
| **system** | System operations, monitoring | File stats, system monitor |
| **data** | Data processing, analysis | Text analyzer, CSV processor |
| **iot** | IoT devices, smart home | Lights, sensors, thermostats |
| **communications** | Messaging, notifications | Email, Slack, SMS |
| **ai_ml** | AI/ML services | Image recognition, translation |

---

## 🎓 Learning Path

### Level 1: Beginner (30 minutes)
1. Copy `fortune_message` plugin
2. Modify description and parameters
3. Test manually
4. Deploy and test with LLM

### Level 2: Intermediate (1-2 hours)
1. Study `weather_info` plugin (API calls)
2. Create plugin that calls external API
3. Add error handling for API failures
4. Test network security restrictions

### Level 3: Advanced (2-4 hours)
1. Study `system_monitor` plugin (library usage)
2. Create plugin with Python dependencies
3. Implement complex logic (multiple steps)
4. Add comprehensive error handling

### Level 4: Expert (4+ hours)
1. Create multi-function plugin family
2. Implement caching for performance
3. Add metrics and monitoring
4. Contribute to plugin ecosystem

---

## 📞 Support

- **Main Documentation:** `/docs/PLUGIN_ARCHITECTURE_DESIGN.md`
- **Example Code:** `/plugins/fortune_message.yaml` and handlers
- **Test Suite:** `/tests/utilities/test_all_plugins.py`
- **Configuration:** `/plugins/config/plugin_defaults.yaml`

---

**Happy Plugin Development!** 🎉

*For questions or issues, check the troubleshooting section or review the working examples.*
