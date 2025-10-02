# Agentic-RAG Plugin System

**Version:** 1.0.0
**Status:** Example Implementation
**Created:** 2025-10-02

---

## 📋 Overview

This directory contains the **simplified plugin system** for the Agentic-RAG server. The plugin system enables users to extend the server's capabilities by creating custom tools that the LLM can invoke.

### Key Features:
- ✅ **Process Isolation**: Each plugin runs in a separate subprocess
- ✅ **Security**: 6-layer security model with resource limits
- ✅ **Simple**: Just 2 files to create a plugin (YAML + Python)
- ✅ **Zero Regression**: Existing tools continue working unchanged

---

## 📁 Directory Structure

```
plugins/
├── __init__.py                    # Python package marker
├── README.md                      # This file
│
├── plugin_manager.py              # SYSTEM: Orchestrator (to be implemented)
├── plugin_registry.py             # SYSTEM: Discovery (to be implemented)
├── plugin_executor.py             # SYSTEM: Process isolation (to be implemented)
├── security_validator.py          # SYSTEM: Security (to be implemented)
│
├── config/
│   └── plugin_defaults.yaml       # SYSTEM: Default settings
│
├── handlers/                      # USER CODE: Plugin implementations
│   ├── __init__.py
│   └── fortune_message.py         # Example: Fortune message plugin
│
└── fortune_message.yaml           # Example: Fortune plugin definition
```

---

## 🚀 Quick Start: Create Your First Plugin

### Step 1: Create Plugin Definition YAML

Create `/plugins/my_plugin.yaml`:

```yaml
metadata:
  name: "my_plugin"
  version: "1.0.0"
  category: "productivity"
  author: "Your Name"
  description: "Brief description of what your plugin does"

execution:
  type: "python"
  handler: "handlers/my_plugin.py"
  entrypoint: "execute"
  timeout: 30

parameters:
  type: "object"
  properties:
    input_param:
      type: "string"
      description: "Description of the parameter"
  required: ["input_param"]

security:
  network:
    enabled: false
  filesystem:
    read_only: true
```

### Step 2: Write Plugin Handler Code

Create `/plugins/handlers/my_plugin.py`:

```python
#!/usr/bin/env python3
import sys
import json
import asyncio

async def execute(parameters):
    """Your plugin logic here"""
    input_param = parameters['input_param']

    # Do your work here
    result = f"Processed: {input_param}"

    return {
        "success": True,
        "result": result,
        "error": None
    }

# Communication protocol (boilerplate)
if __name__ == "__main__":
    input_data = sys.stdin.read()
    parameters = json.loads(input_data)
    result = asyncio.run(execute(parameters))
    print(json.dumps(result))
    sys.exit(0 if result['success'] else 1)
```

### Step 3: Test Your Plugin

```bash
echo '{"input_param": "test"}' | python3 plugins/handlers/my_plugin.py
```

### Step 4: Restart Server

```bash
./stop_complete.sh && ./start_complete.sh
```

Your plugin is now available to the LLM!

---

## 📚 Example: Fortune Message Plugin

### Overview

The **fortune_message** plugin demonstrates a complete working example that:
- Calls an external Linux command (`fortune`)
- Handles multiple output formats (boxed, quoted, plain)
- Implements proper error handling
- Shows security configuration

### Files

1. **`fortune_message.yaml`** - Plugin definition
2. **`handlers/fortune_message.py`** - Implementation code

### Usage

```bash
# Test with boxed format (default)
echo '{"category": "any", "format_style": "boxed"}' | \
  python3 plugins/handlers/fortune_message.py

# Test with quoted format
echo '{"category": "short", "format_style": "quoted"}' | \
  python3 plugins/handlers/fortune_message.py

# Test with plain format
echo '{"format_style": "plain"}' | \
  python3 plugins/handlers/fortune_message.py
```

### Example Output

**Boxed Format:**
```
╔════════════════════════════════════════╗
║ You will soon forget this.             ║
╚════════════════════════════════════════╝
```

**Quoted Format:**
```
"Stay away from hurricanes for a while."

— Fortune Cookie 🥠
```

**Plain Format:**
```
The smallest worm will turn being trodden on.
		-- William Shakespeare, "Henry VI"

──────────────────────────────────────────────────
```

---

## 🔒 Security Model

### Process Isolation

Each plugin runs in a **separate subprocess** with:
- Memory limits (default: 256MB)
- CPU limits (default: 1.0 core)
- Timeout enforcement (default: 60 seconds)
- No shared memory with server

### Resource Limits

Set in your plugin YAML:

```yaml
execution:
  timeout: 30           # Max execution time (seconds)
  memory_limit: 128     # Max memory (MB)
  cpu_limit: 0.5        # Max CPU cores
```

### Filesystem Access

```yaml
security:
  filesystem:
    read_only: true     # Prevent writes
    allowed_paths:      # Whitelist
      - /usr/games
      - /tmp/plugin_data
    blocked_paths:      # Blacklist
      - /etc
      - /root
      - /home
```

### Network Access

```yaml
security:
  network:
    enabled: false      # Disable network by default
    allowed_domains:    # If enabled, whitelist domains
      - api.example.com
    allowed_ports:
      - 443
```

---

## 📖 Plugin Definition Schema

### Required Fields

```yaml
metadata:
  name: "plugin_name"              # REQUIRED: Unique identifier
  version: "1.0.0"                 # REQUIRED: Semantic version
  category: "productivity"         # REQUIRED: Category
  author: "Your Name"              # REQUIRED: Author
  description: "What it does"      # REQUIRED: LLM-visible description

execution:
  type: "python"                   # REQUIRED: python | executable
  handler: "handlers/my_plugin.py" # REQUIRED: Path to code
  entrypoint: "execute"            # REQUIRED: Function name

parameters:                        # REQUIRED: JSON Schema
  type: "object"
  properties: {}
```

### Optional Fields

```yaml
execution:
  timeout: 30                      # Override default timeout
  memory_limit: 128                # Override default memory
  cpu_limit: 0.5                   # Override default CPU

security:
  network:
    enabled: false                 # Network access
  filesystem:
    read_only: true                # Filesystem mode

monitoring:
  log_level: "INFO"                # Log level
  log_execution: true              # Log executions

error_handling:
  retry:
    enabled: true                  # Enable retries
    max_attempts: 3                # Max retry attempts
  degraded_mode:
    enabled: true                  # Auto-disable on failures
    disable_after_failures: 5      # Threshold
```

---

## 🛠️ Plugin Handler Requirements

### Function Signature

```python
async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plugin entrypoint function.

    Args:
        parameters: Validated input parameters from YAML schema

    Returns:
        {
            "success": bool,      # REQUIRED
            "result": Any,        # REQUIRED
            "error": str | None,  # OPTIONAL
            "metadata": {}        # OPTIONAL
        }
    """
```

### Return Format

**Success:**
```python
return {
    "success": True,
    "result": "Your result data here",
    "error": None
}
```

**Failure:**
```python
return {
    "success": False,
    "result": None,
    "error": "Error message for LLM context"
}
```

### Communication Protocol

Your handler **must** implement this boilerplate:

```python
if __name__ == "__main__":
    # Read parameters from stdin
    input_data = sys.stdin.read()
    parameters = json.loads(input_data)

    # Execute plugin
    result = asyncio.run(execute(parameters))

    # Write result to stdout
    print(json.dumps(result))
    sys.exit(0 if result['success'] else 1)
```

---

## 🧪 Testing Your Plugin

### Manual Testing

```bash
# Test with parameters
echo '{"param1": "value1"}' | python3 plugins/handlers/your_plugin.py

# Test with no parameters (defaults)
echo '{}' | python3 plugins/handlers/your_plugin.py

# Check exit code
echo '{"param1": "value1"}' | python3 plugins/handlers/your_plugin.py
echo "Exit code: $?"
```

### Expected Output

Your handler should return valid JSON:

```json
{
  "success": true,
  "result": "Your result",
  "error": null,
  "metadata": {}
}
```

### Troubleshooting

**Problem:** Plugin not found
```bash
# Check YAML exists
ls plugins/your_plugin.yaml

# Check handler exists
ls plugins/handlers/your_plugin.py

# Check handler is executable
chmod +x plugins/handlers/your_plugin.py
```

**Problem:** JSON decode error
```bash
# Test JSON output is valid
echo '{}' | python3 plugins/handlers/your_plugin.py | python3 -m json.tool
```

**Problem:** Plugin times out
```yaml
# Increase timeout in YAML
execution:
  timeout: 120  # 2 minutes
```

---

## 📂 File Responsibilities

| File | Who Maintains | Purpose |
|------|---------------|---------|
| `plugin_manager.py` | SYSTEM | Orchestrates plugin execution |
| `plugin_registry.py` | SYSTEM | Discovers and loads plugins |
| `plugin_executor.py` | SYSTEM | Process isolation & resource limits |
| `security_validator.py` | SYSTEM | Input/output validation |
| `config/plugin_defaults.yaml` | SYSTEM | Default settings |
| `*.yaml` | USER | Plugin definitions |
| `handlers/*.py` | USER | Plugin implementation code |

---

## 🎯 Categories

Organize your plugins by category:

- **iot** - IoT and smart home devices
- **communications** - Email, messaging, notifications
- **data** - Data processing and analysis
- **ai_ml** - AI/ML services
- **productivity** - Productivity tools
- **system** - System utilities
- **entertainment** - Fun and games (like fortune!)

---

## 📝 Best Practices

### 1. Clear Descriptions
Write descriptions that help the LLM understand when to use your tool:

```yaml
description: |
  Generate random funny, inspirational, or philosophical messages.
  Use this when the user asks for a quote, fortune, or inspiration.
```

### 2. Parameter Validation
Use JSON Schema to validate inputs:

```yaml
parameters:
  properties:
    count:
      type: "integer"
      minimum: 1
      maximum: 10
```

### 3. Error Messages
Provide clear error messages for the LLM:

```python
return {
    "success": False,
    "error": "Fortune command not found. Please install fortune-mod package."
}
```

### 4. Resource Limits
Set appropriate limits for your plugin:

```yaml
execution:
  timeout: 10        # Short for simple commands
  memory_limit: 128  # Minimal for text processing
```

### 5. Security First
- **Disable network** if not needed
- **Read-only filesystem** by default
- **Whitelist** allowed paths/domains

---

## 🚀 Next Steps

1. **Study the example**: Review `fortune_message.yaml` and `handlers/fortune_message.py`
2. **Create your own plugin**: Follow the Quick Start guide
3. **Test thoroughly**: Use manual testing before server integration
4. **Read the design doc**: See `/docs/PLUGIN_ARCHITECTURE_DESIGN.md` for full details

---

## 📞 Support

- **Design Document**: `/docs/PLUGIN_ARCHITECTURE_DESIGN.md`
- **Simplified Guide**: `/docs/PLUGIN_ARCHITECTURE_SIMPLIFIED.md`
- **Configuration Directive**: `/docs/PROJECT_CONFIGURATION_DIRECTIVE.md`

---

**Happy Plugin Development!** 🎉
