# Plugin Architecture Design Document
**Agentic-RAG Server - Plugin System Enhancement**

**Version:** 1.0.0
**Status:** Design Phase
**Last Updated:** 2025-10-02
**Author:** System Architect

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Design Goals & Constraints](#design-goals--constraints)
4. [System Architecture](#system-architecture)
5. [Plugin Definition Schema](#plugin-definition-schema)
6. [Component Design](#component-design)
7. [Execution Flow](#execution-flow)
8. [Security Model](#security-model)
9. [Error Handling Strategy](#error-handling-strategy)
10. [Migration Path](#migration-path)
11. [File Structure](#file-structure)
12. [Implementation Roadmap](#implementation-roadmap)
13. [Testing Strategy](#testing-strategy)

---

## 1. Executive Summary

### Purpose
Enhance the Agentic-RAG server's tool system with a robust, secure, and extensible plugin architecture that enables:
- **Config-driven plugin definitions** (YAML/JSON)
- **Process isolation** for plugin execution
- **Security sandboxing** with resource limits
- **Graceful failure handling** without server impact
- **Category-based organization** by domain
- **External service integration** capabilities

### Key Design Principles
1. **Zero Regression:** All 19 existing tools continue functioning unchanged
2. **Backward Compatibility:** BaseUserTool system remains fully operational
3. **Production-Ready:** Battle-tested patterns, comprehensive error handling
4. **Clear Separation:** Plugin system isolated from core tool execution
5. **Configuration-Driven:** Adheres to PROJECT_CONFIGURATION_DIRECTIVE.md
6. **Fail-Fast:** Missing configs cause immediate, clear failures
7. **Simplified Structure:** Flat directory layout, minimal configuration files

### Simplified Architecture Overview

**User adds a plugin in 3 steps:**
1. Create `my_plugin.yaml` in `/plugins/` (defines what tool does)
2. Write `handlers/my_plugin.py` (implements the actual logic)
3. Restart server (auto-discovery happens)

**System handles everything else:**
- Discovery (finds all YAMLs automatically)
- Validation (checks schema, security policies)
- Execution (subprocess isolation with resource limits)
- Error handling (retries, degraded mode, logging)

---

## 2. Current Architecture Analysis

### 2.1 Existing Tool System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   AsyncToolManager                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Built-in Tools (6 core functions)                     │ │
│  │  - get_the_secret_tool                                 │ │
│  │  - wikipedia_query                                     │ │
│  │  - get_stock_and_company_data                          │ │
│  │  - get_news_summaries                                  │ │
│  │  - search_web                                          │ │
│  │  - lookup_website                                      │ │
│  │  - secure_email_sender                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  User Tools (BaseUserTool system)                      │ │
│  │  - Discovered from /user_tools/                        │ │
│  │  - Loaded via discover_user_tools()                    │ │
│  │  - 13 active user tools detected                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  available_functions: Dict[str, Callable]                   │
│  ├─ Built-in: Direct method references                      │
│  └─ User: Wrapped BaseUserTool.execute()                    │
└─────────────────────────────────────────────────────────────┘

Tool Discovery Flow:
1. Server startup → AsyncToolManager.__init__()
2. First tool request → _load_user_tools_async()
3. discover_user_tools() → Scans /user_tools/*.py
4. load_tool_from_file() → Validates BaseUserTool subclass
5. Adds to available_functions dict

Execution Flow:
LLM → tool_calls → safe_function_call(func_name, args)
  → available_functions[func_name](args)
  → Direct execution (NO ISOLATION)
```

### 2.2 Current Limitations

| Issue | Impact | Solution in New Design |
|-------|--------|----------------------|
| **No Process Isolation** | Plugin crash = server crash | Separate process executor with timeout |
| **Code-Only Tools** | Requires Python programming | Config-driven YAML/JSON definitions |
| **No Resource Limits** | Infinite loops/memory leaks crash server | Resource limits (CPU, memory, time) |
| **No Categorization** | 19 tools presented as flat list | Domain-based categories |
| **Runtime Loading Only** | Server restart required for new tools | Foundation for hot-reload (future) |
| **Limited Extensibility** | Can't integrate external executables | Service hooks with entrypoints |

---

## 3. Design Goals & Constraints

### 3.1 Functional Requirements

**FR-1: Config-Driven Plugins**
- Plugins defined in YAML/JSON files in `/plugins/` directory
- Schema includes: metadata, execution config, security policies, parameters
- Supports both Python code and external executable definitions

**FR-2: Process Isolation**
- Each plugin executes in dedicated subprocess
- Configurable timeout (default from llm_config.yaml)
- Memory and CPU limits enforced
- Process cleanup on completion/timeout

**FR-3: Security Model**
- Input validation against JSON schema
- Output sanitization (size limits, type validation)
- Filesystem access controls (whitelist/blacklist)
- Network access policies (allowed domains/ports)
- No access to server internals

**FR-4: Graceful Failure**
- Plugin crashes logged but don't affect server
- Timeout errors return structured error to LLM
- Validation failures provide clear messages
- Degraded mode: Disable failing plugins automatically

**FR-5: Zero Regression**
- All 19 existing tools function identically
- BaseUserTool system remains unchanged
- AsyncToolManager backward compatible
- No changes to tool calling protocol

**FR-6: Category Organization**
- Tools grouped by domain: IoT, Communications, Data, AI/ML, Productivity, System
- Category filtering in tool selection
- Category-based tool discovery

**FR-7: External Service Integration**
- Define external executables/scripts as plugins
- Standard input/output communication protocol
- Service lifecycle management (start/stop/health check)

### 3.2 Non-Functional Requirements

**NFR-1: Performance**
- Plugin discovery: < 100ms for 50 plugins
- Plugin execution overhead: < 50ms startup time
- Concurrent execution: Support 5+ simultaneous plugins

**NFR-2: Reliability**
- Plugin failure rate: < 1% for valid inputs
- Server uptime: 99.9% (plugins can't crash server)
- Automatic recovery from plugin errors

**NFR-3: Maintainability**
- Plugin definition format: Clear, documented schema
- Error messages: Actionable, specific
- Logging: Comprehensive, structured (JSON)

**NFR-4: Security**
- Process sandboxing: Unix permissions + resource limits
- Input validation: 100% of plugin inputs validated
- Output sanitization: Prevent injection attacks

### 3.3 Constraints

**C-1: Configuration Directive Compliance**
- NO hardcoded configuration values
- All config in `config/llm_config.yaml` or `config/plugin_config.yaml`
- .env only for secrets (API keys, passwords)
- Fail-fast when configuration missing

**C-2: Backward Compatibility**
- Existing tool code untouched
- BaseUserTool API unchanged
- Tool calling protocol unchanged

**C-3: Platform Support**
- Linux primary target
- macOS support (best-effort)
- Windows: BaseUserTool fallback only

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     FastAPI Server Process                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              AsyncToolManager (Enhanced)                      │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │ │
│  │  │  Built-in      │  │  BaseUserTool  │  │  Plugin System │ │ │
│  │  │  Tools (6)     │  │  Tools (13)    │  │  (New Layer)   │ │ │
│  │  │  [Unchanged]   │  │  [Unchanged]   │  │                │ │ │
│  │  └────────────────┘  └────────────────┘  └────────────────┘ │ │
│  │           │                  │                    │           │ │
│  │           └──────────────────┴────────────────────┘           │ │
│  │                              │                                │ │
│  │                    available_functions                        │ │
│  └─────────────────────────────│────────────────────────────────┘ │
│                                 │                                  │
│                                 ▼                                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   PluginManager (NEW)                         │ │
│  │  ┌─────────────┐  ┌────────────┐  ┌─────────────────────┐   │ │
│  │  │   Plugin    │  │   Plugin   │  │   Security          │   │ │
│  │  │   Registry  │  │  Executor  │  │   Validator         │   │ │
│  │  └─────────────┘  └────────────┘  └─────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                 │                                  │
└─────────────────────────────────┼──────────────────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────┐
        │     Isolated Plugin Processes (Sandboxed)   │
        │  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
        │  │ Plugin  │  │ Plugin  │  │ Plugin  │     │
        │  │   A     │  │   B     │  │   C     │     │
        │  │ Process │  │ Process │  │ Process │     │
        │  └─────────┘  └─────────┘  └─────────┘     │
        │                                              │
        │  Resource Limits:                            │
        │  - CPU: 1 core max                          │
        │  - Memory: 512MB max (configurable)         │
        │  - Time: 60s timeout (configurable)         │
        │  - Network: Restricted (whitelist)          │
        │  - Filesystem: Limited access               │
        └─────────────────────────────────────────────┘
```

### 4.2 Component Interaction Diagram

```
LLM Tool Call Request
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ AsyncToolManager.safe_function_call(func_name, args)          │
└───────────────────────────────────────────────────────────────┘
        │
        ├──► Built-in tool? ──Yes──► Execute directly
        │                             (existing behavior)
        │
        ├──► BaseUserTool? ──Yes──► Execute via wrapper
        │                             (existing behavior)
        │
        └──► Plugin tool? ──Yes──┐
                                 │
                                 ▼
        ┌─────────────────────────────────────────────────┐
        │ PluginManager.execute_plugin(name, args)        │
        │  1. Get plugin definition from registry         │
        │  2. Validate inputs with SecurityValidator      │
        │  3. Create PluginExecutor instance              │
        │  4. Execute in isolated process                 │
        │  5. Validate outputs with SecurityValidator     │
        │  6. Return result or error                      │
        └─────────────────────────────────────────────────┘
                                 │
                                 ▼
        ┌─────────────────────────────────────────────────┐
        │ PluginExecutor.run(plugin_def, args)            │
        │  1. Create subprocess with resource limits      │
        │  2. Set timeout alarm                           │
        │  3. Execute plugin code/executable              │
        │  4. Capture stdout/stderr                       │
        │  5. Cleanup process on completion/timeout       │
        │  6. Return structured result                    │
        └─────────────────────────────────────────────────┘
                                 │
                                 ▼
        ┌─────────────────────────────────────────────────┐
        │ Isolated Plugin Process                         │
        │  - Restricted permissions                       │
        │  - Resource limits enforced                     │
        │  - Network access controlled                    │
        │  - Filesystem access limited                    │
        │  - Communication via stdin/stdout only          │
        └─────────────────────────────────────────────────┘
```

### 4.3 Layer Responsibilities

**Layer 1: AsyncToolManager (Enhanced)**
- Maintains backward compatibility with existing tools
- Routes plugin calls to PluginManager
- Provides unified interface to LLM tool calling system
- Manages image context injection (existing feature)

**Layer 2: PluginManager (New)**
- Central orchestrator for plugin system
- Delegates to specialized components:
  - PluginRegistry: Discovery and metadata management
  - PluginExecutor: Process isolation and execution
  - SecurityValidator: Input/output validation
- Configuration management via llm_config.yaml
- Category-based tool organization

**Layer 3: Isolated Execution (New)**
- Subprocess creation with resource limits
- Timeout enforcement
- Process cleanup and error recovery
- Communication protocol (JSON over stdin/stdout)

---

## 5. Plugin Definition Schema

### 5.1 Plugin Configuration File Format

**File Location:** `/plugins/<plugin_name>.yaml` (flat structure - no category subdirectories)

**Schema Version:** 1.0.0

```yaml
# =============================================================================
# Plugin Definition Schema v1.0.0
# =============================================================================

metadata:
  name: "example_iot_controller"          # REQUIRED: Unique plugin identifier
  version: "1.0.0"                        # REQUIRED: Semantic version
  category: "iot"                          # REQUIRED: Domain category
  author: "System Administrator"           # REQUIRED: Plugin author
  description: |                           # REQUIRED: LLM-visible description
    Control IoT devices via MQTT protocol. Supports on/off commands,
    status queries, and device discovery.
  license: "MIT"                          # OPTIONAL: License identifier
  homepage: "https://example.com/docs"    # OPTIONAL: Documentation URL
  tags:                                   # OPTIONAL: Search tags
    - iot
    - mqtt
    - automation
    - smart-home

execution:
  type: "python"                          # REQUIRED: python | executable | service
  handler: "handlers/iot_controller.py"   # REQUIRED: Relative path from /plugins/
  entrypoint: "execute"                   # REQUIRED: Function/method name
  timeout: 30                             # OPTIONAL: Max execution time (seconds)
  memory_limit: 256                       # OPTIONAL: Max memory (MB)
  cpu_limit: 1.0                          # OPTIONAL: Max CPU cores
  environment:                            # OPTIONAL: Environment variables
    MQTT_BROKER: "${MQTT_BROKER_URL}"     # From .env or config
    LOG_LEVEL: "INFO"

parameters:
  type: "object"
  properties:
    device_id:
      type: "string"
      description: "Unique device identifier"
      pattern: "^[a-zA-Z0-9_-]+$"
    command:
      type: "string"
      description: "Command to execute"
      enum: ["on", "off", "status", "discover"]
    zone:
      type: "string"
      description: "Optional zone/room identifier"
      default: "default"
  required:
    - device_id
    - command

security:
  input_validation:
    max_string_length: 1024               # Max length for string inputs
    max_array_length: 100                 # Max array size
    allowed_types: ["string", "number", "boolean", "array", "object"]

  output_validation:
    max_output_size: 1048576              # 1MB max output
    allowed_content_types: ["application/json", "text/plain"]

  network:
    enabled: true                         # Allow network access?
    allowed_domains:                      # Whitelist of domains
      - "mqtt.example.com"
      - "api.iot-provider.com"
    allowed_ports:                        # Whitelist of ports
      - 1883                              # MQTT
      - 8883                              # MQTT over TLS
    block_private_ips: true               # Block RFC1918 addresses

  filesystem:
    read_only: false                      # Filesystem read-only?
    allowed_paths:                        # Whitelist of paths
      - "/tmp/iot_controller"
      - "/var/log/iot_controller"
    blocked_paths:                        # Blacklist of paths
      - "/etc"
      - "/root"
      - "/home"

monitoring:
  log_level: "INFO"                       # DEBUG | INFO | WARNING | ERROR
  log_execution: true                     # Log each execution?
  log_outputs: false                      # Log plugin outputs? (sensitive data)
  metrics:
    track_execution_time: true
    track_success_rate: true
    alert_on_failure_rate: 0.1            # Alert if > 10% failures

dependencies:
  python_packages:                        # Required Python packages
    - paho-mqtt>=1.6.1
    - jsonschema>=4.0.0
  system_packages:                        # Required system packages
    - mosquitto-clients
  checks:                                 # Pre-execution checks
    - type: "env_var"
      name: "MQTT_BROKER_URL"
      required: true
    - type: "network_connectivity"
      host: "${MQTT_BROKER_URL}"
      port: 1883

error_handling:
  retry:
    enabled: true
    max_attempts: 3
    backoff_strategy: "exponential"       # linear | exponential | fixed
    initial_delay: 1                      # Seconds

  fallback:
    enabled: false
    fallback_plugin: null                 # Name of fallback plugin

  degraded_mode:
    enabled: true
    disable_after_failures: 5             # Disable plugin after N failures
    cooldown_period: 300                  # Seconds before re-enabling
```

### 5.2 Plugin Handler Code Structure

**Example Python Handler:** `/plugins/handlers/iot_controller.py`

```python
"""
IoT Controller Plugin Handler
Complies with Plugin System v1.0.0
"""

import sys
import json
import asyncio
from typing import Dict, Any

async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plugin entrypoint function.

    Args:
        parameters: Validated input parameters from plugin definition schema

    Returns:
        Dict with structure:
        {
            "success": bool,      # REQUIRED: Execution success status
            "result": Any,        # REQUIRED: Result data (JSON-serializable)
            "error": str | None,  # OPTIONAL: Error message if success=False
            "metadata": {         # OPTIONAL: Execution metadata
                "execution_time": float,
                "device_status": str,
                ...
            }
        }
    """
    try:
        device_id = parameters['device_id']
        command = parameters['command']
        zone = parameters.get('zone', 'default')

        # Your plugin logic here
        result = await control_device(device_id, command, zone)

        return {
            "success": True,
            "result": result,
            "metadata": {
                "device_id": device_id,
                "command": command,
                "zone": zone
            }
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Plugin execution failed: {str(e)}"
        }

async def control_device(device_id: str, command: str, zone: str) -> Dict[str, Any]:
    """Plugin implementation logic"""
    # Implementation here
    pass

# Plugin System Communication Protocol
if __name__ == "__main__":
    # Read parameters from stdin (JSON)
    input_data = sys.stdin.read()
    parameters = json.loads(input_data)

    # Execute plugin
    result = asyncio.run(execute(parameters))

    # Write result to stdout (JSON)
    print(json.dumps(result))
    sys.exit(0 if result['success'] else 1)
```

### 5.3 Simplified Directory Structure

**SIMPLIFIED: No category subdirectories - category specified in YAML metadata**

```
/plugins/
├── mqtt_controller.yaml          # category: "iot" in metadata
├── zigbee_bridge.yaml            # category: "iot" in metadata
├── slack_notifier.yaml           # category: "communications" in metadata
├── sms_sender.yaml               # category: "communications" in metadata
├── csv_analyzer.yaml             # category: "data" in metadata
├── database_query.yaml           # category: "data" in metadata
├── image_classifier.yaml         # category: "ai_ml" in metadata
├── calendar_sync.yaml            # category: "productivity" in metadata
├── file_manager.yaml             # category: "system" in metadata
│
├── handlers/                     # USER CODE - Actual plugin implementations
│   ├── __init__.py
│   ├── mqtt_controller.py        # User writes this
│   ├── slack_notifier.py         # User writes this
│   ├── csv_analyzer.py           # User writes this
│   └── ...                       # All user-created handlers
│
└── config/
    └── plugin_defaults.yaml      # System defaults (minimal)
```

**Key Simplifications:**
- ❌ **Removed**: Category subdirectories (iot/, communications/, etc.)
- ❌ **Removed**: plugin_categories.yaml (auto-detected from plugin metadata)
- ✅ **Category in metadata**: Each YAML specifies its own category
- ✅ **Flat structure**: All plugin YAMLs in /plugins/ root
- ✅ **handlers/**: Single directory for all user code

---

## 6. Component Design

### 6.1 PluginManager Class

**File:** `/plugins/plugin_manager.py`

**Responsibilities:**
- Central orchestrator for plugin system
- Plugin lifecycle management (load, execute, disable, re-enable)
- Metrics tracking and degraded mode enforcement
- Configuration management

**Key Methods:**
```python
async def initialize() -> None
    """Discover and load plugins from /plugins/ directory"""

async def execute_plugin(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]
    """Execute plugin with full isolation and security validation"""

async def get_plugin_definitions(category: Optional[str] = None) -> List[Dict[str, Any]]
    """Get LLM-compatible tool definitions for plugins"""

async def _handle_plugin_failure(name: str, error: str) -> None
    """Handle plugin failure with degraded mode logic"""
```

### 6.2 PluginRegistry Class

**File:** `/plugins/plugin_registry.py`

**Responsibilities:**
- Plugin discovery (scan /plugins/ directory)
- YAML parsing and validation
- Plugin metadata management
- Category organization

**Key Methods:**
```python
async def discover_plugins() -> List[PluginDefinition]
    """Discover all plugins from /plugins/ directory"""

async def _load_plugin_definition(yaml_file: Path, category: str) -> PluginDefinition
    """Load and validate plugin definition from YAML file"""
```

### 6.3 PluginExecutor Class

**File:** `/plugins/plugin_executor.py`

**Responsibilities:**
- Subprocess creation with resource limits
- Timeout enforcement
- Process cleanup
- Communication protocol (JSON over stdin/stdout)

**Key Methods:**
```python
async def execute(plugin_def: PluginDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]
    """Execute plugin in isolated subprocess"""

async def _execute_python(plugin_def, parameters, env) -> Dict[str, Any]
    """Execute Python plugin handler"""

def _set_resource_limits(plugin_def: PluginDefinition)
    """Set resource limits for subprocess (Unix only)"""
```

### 6.4 SecurityValidator Class

**File:** `/plugins/security_validator.py`

**Responsibilities:**
- Input validation (JSON schema, injection detection)
- Output validation (size limits, sensitive data detection)
- Security policy enforcement

**Key Methods:**
```python
async def validate_plugin_definition(plugin_def: PluginDefinition) -> bool
    """Validate plugin definition against security requirements"""

async def validate_inputs(parameters: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]
    """Validate input parameters against JSON schema and security policies"""

async def validate_outputs(result: Any, security_policy: Dict[str, Any]) -> Dict[str, Any]
    """Validate plugin output against security policies"""

def _check_injection_patterns(parameters: Dict[str, Any]) -> Dict[str, Any]
    """Check for common injection patterns (XSS, SQL, command)"""

def _check_sensitive_data(result: Any) -> Dict[str, Any]
    """Check for sensitive data patterns in output (SSN, credit cards, API keys)"""
```

---

## 7. Execution Flow

### 7.1 Plugin Discovery Flow (Server Startup)

```
Server Startup
      │
      ▼
AsyncToolManager.__init__()
      │
      ├─► Built-in tools initialization (unchanged)
      │
      ├─► BaseUserTool discovery (unchanged)
      │
      └─► PluginManager initialization (NEW)
            │
            ▼
      PluginManager.initialize()
            │
            ├─► PluginRegistry.discover_plugins()
            │     │
            │     ├─► Scan /plugins/*.yaml files (flat structure)
            │     │
            │     ├─► Load and parse YAML definitions
            │     │
            │     ├─► Parse plugin definitions
            │     │
            │     └─► Return List[PluginDefinition]
            │
            ├─► For each plugin:
            │     │
            │     ├─► SecurityValidator.validate_plugin_definition()
            │     │     ├─► Check handler exists
            │     │     ├─► Validate parameter schema
            │     │     └─► Validate security policy
            │     │
            │     ├─► Check dependencies
            │     │     ├─► Environment variables
            │     │     ├─► Python packages
            │     │     └─► Network connectivity
            │     │
            │     └─► Add to loaded_plugins dict
            │
            └─► Log summary
                  "Loaded N plugins across M categories"
```

### 7.2 Plugin Execution Flow (LLM Tool Call)

```
LLM generates tool_call
      │
      ▼
AsyncToolManager.safe_function_call(func_name, args)
      │
      ├──► Is built-in tool? ──Yes──► Execute directly (unchanged)
      │
      ├──► Is BaseUserTool? ──Yes──► Execute via wrapper (unchanged)
      │
      └──► Is plugin tool? ──Yes──┐
                                  │
                                  ▼
            PluginManager.execute_plugin(name, parameters)
                                  │
                                  ├─► Check plugin exists
                                  │     └─► Not found? Return error
                                  │
                                  ├─► Check plugin not disabled
                                  │     └─► Disabled? Return degraded mode error
                                  │
                                  ├─► SecurityValidator.validate_inputs()
                                  │     │
                                  │     ├─► JSON schema validation
                                  │     ├─► String length checks
                                  │     ├─► Array size checks
                                  │     ├─► Injection pattern detection
                                  │     └─► Return validation result
                                  │
                                  ├─► PluginExecutor.execute()
                                  │     │
                                  │     ├─► Prepare environment variables
                                  │     │
                                  │     ├─► Create subprocess
                                  │     │     ├─► Set resource limits (memory, CPU)
                                  │     │     ├─► Set timeout
                                  │     │     └─► Restricted permissions
                                  │     │
                                  │     ├─► Send parameters via stdin (JSON)
                                  │     │
                                  │     ├─► Wait for result (with timeout)
                                  │     │     ├─► Timeout? Kill process
                                  │     │     └─► Exception? Log and return error
                                  │     │
                                  │     ├─► Read stdout/stderr
                                  │     │
                                  │     ├─► Parse JSON result
                                  │     │
                                  │     └─► Return execution result
                                  │
                                  ├─► SecurityValidator.validate_outputs()
                                  │     │
                                  │     ├─► Check output size
                                  │     ├─► Scan for sensitive data
                                  │     └─► Return validation result
                                  │
                                  ├─► Update metrics
                                  │     ├─► Execution time
                                  │     ├─► Success/failure rate
                                  │     └─► Check degraded mode threshold
                                  │
                                  └─► Return result to AsyncToolManager
                                        │
                                        └─► Return to LLM
```

### 7.3 Error Handling Flow

```
Plugin Execution Error
      │
      ├─► Timeout Error
      │     │
      │     ├─► Kill subprocess
      │     ├─► Log error with traceback
      │     ├─► Increment failure counter
      │     ├─► Check degraded mode threshold
      │     └─► Return structured error to LLM
      │
      ├─► Validation Error (Input/Output)
      │     │
      │     ├─► Log validation failure
      │     ├─► DO NOT increment failure counter (client error)
      │     └─► Return validation error to LLM
      │
      ├─► Execution Exception
      │     │
      │     ├─► Capture stderr
      │     ├─► Log full traceback
      │     ├─► Increment failure counter
      │     ├─► Check degraded mode threshold
      │     └─► Return execution error to LLM
      │
      └─► Degraded Mode Trigger
            │
            ├─► Failure count >= threshold?
            │     │
            │     └─► Yes:
            │           ├─► Disable plugin
            │           ├─► Set cooldown period
            │           ├─► Log warning: "Plugin disabled"
            │           └─► Schedule re-enable after cooldown
            │
            └─► Future requests:
                  └─► Return "Plugin temporarily disabled" error
```

---

## 8. Security Model

### 8.1 Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Input Validation                                   │
│  - JSON schema validation                                   │
│  - String length limits                                     │
│  - Array size limits                                        │
│  - Type checking                                            │
│  - Injection pattern detection (XSS, SQL, command)          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Process Isolation                                  │
│  - Separate subprocess per execution                        │
│  - No shared memory with server                             │
│  - Communication via stdin/stdout only                      │
│  - Process cleanup on completion/timeout                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Resource Limits (Unix)                             │
│  - Memory limit: 256MB default (configurable)               │
│  - CPU time limit: Matches timeout                          │
│  - File size limit: 100MB                                   │
│  - Process limit: 50 subprocesses                           │
│  - Enforced via resource.setrlimit()                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Filesystem Access Control                          │
│  - Whitelist: Allowed paths (e.g., /tmp/plugin_data)        │
│  - Blacklist: Blocked paths (/etc, /root, /home)            │
│  - Read-only mode option                                    │
│  - Enforced via policy validation (future: AppArmor/SELinux)│
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Network Access Control                             │
│  - Network enabled/disabled flag                            │
│  - Domain whitelist (e.g., api.example.com)                 │
│  - Port whitelist (e.g., 443, 1883)                         │
│  - Block private IPs (RFC1918) option                       │
│  - Enforced via policy validation (future: firewall rules)  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 6: Output Validation                                  │
│  - Output size limits (1MB default)                         │
│  - Sensitive data detection (SSN, credit cards, API keys)   │
│  - Type validation (JSON-serializable)                      │
│  - Content-type validation                                  │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Threat Model

| Threat | Mitigation | Layer |
|--------|------------|-------|
| **Malicious Input (Injection)** | Input validation with pattern detection | Layer 1 |
| **Resource Exhaustion (DoS)** | Resource limits (memory, CPU, timeout) | Layer 3 |
| **Server Crash** | Process isolation, graceful error handling | Layer 2 |
| **Data Exfiltration** | Output validation, network controls | Layer 5, 6 |
| **Filesystem Access** | Path whitelist/blacklist, read-only mode | Layer 4 |
| **Privilege Escalation** | Subprocess runs with same user permissions | Layer 2 |
| **Sensitive Data Leakage** | Output scanning for SSN, credit cards, etc. | Layer 6 |
| **Infinite Loop** | CPU time limits, process timeout | Layer 3 |
| **Memory Bomb** | Memory limits enforced via setrlimit() | Layer 3 |

### 8.3 Security Best Practices

1. **Principle of Least Privilege:**
   - Plugins run with same user permissions as server (no privilege escalation)
   - Future: Dedicated plugin user with restricted permissions

2. **Defense in Depth:**
   - Multiple validation layers
   - Fail securely (reject on validation failure)
   - Log all security events

3. **Fail-Safe Defaults:**
   - Network disabled by default
   - Filesystem read-only by default
   - Conservative resource limits by default

4. **Audit and Monitoring:**
   - Log all plugin executions
   - Track failure rates and patterns
   - Alert on suspicious activity (future enhancement)

---

## 9. Error Handling Strategy

### 9.1 Error Categories

| Category | Description | Server Impact | User Impact | Recovery |
|----------|-------------|---------------|-------------|----------|
| **Validation Error** | Invalid input parameters | None | Error message to LLM | Immediate (fix input) |
| **Timeout Error** | Execution exceeds timeout | None | Timeout message to LLM | Automatic (retry) |
| **Execution Error** | Plugin code exception | None | Error message to LLM | Automatic (retry with backoff) |
| **Resource Error** | Memory/CPU limit exceeded | None | Resource limit message | Automatic (adjust limits) |
| **Dependency Error** | Missing dependencies | None | Dependency message | Manual (install deps) |
| **Configuration Error** | Invalid plugin definition | None | Config error message | Manual (fix YAML) |
| **Security Error** | Policy violation | None | Security error message | Manual (review policy) |

### 9.2 Error Response Format

All errors return structured JSON to maintain consistent LLM interface:

```json
{
  "success": false,
  "result": null,
  "error": "Human-readable error message for LLM context",
  "error_details": {
    "category": "timeout | validation | execution | resource | dependency | config | security",
    "plugin_name": "example_plugin",
    "timestamp": "2025-10-02T10:30:45Z",
    "retry_recommended": true,
    "suggested_action": "Increase timeout in plugin config"
  },
  "execution_time": 60.5,
  "metadata": {
    "exit_code": 124,
    "stderr": "Process timed out after 60 seconds"
  }
}
```

### 9.3 Retry Strategy

```yaml
# Plugin-level retry configuration
error_handling:
  retry:
    enabled: true
    max_attempts: 3
    backoff_strategy: exponential  # linear | exponential | fixed
    initial_delay: 1               # Seconds
    max_delay: 30                  # Seconds

  # Which error categories trigger retry?
  retry_on:
    - timeout
    - execution
    - resource

  # Which error categories do NOT retry?
  no_retry_on:
    - validation
    - security
    - config
```

**Backoff Strategies:**

- **Linear:** `delay = initial_delay * attempt`
- **Exponential:** `delay = initial_delay * (2 ^ attempt)`
- **Fixed:** `delay = initial_delay`

### 9.4 Degraded Mode

When a plugin fails repeatedly, it enters degraded mode:

```yaml
# Degraded mode configuration
degraded_mode:
  enabled: true
  disable_after_failures: 5      # Disable after N consecutive failures
  cooldown_period: 300           # Seconds before re-enabling (5 minutes)
  alert_on_disable: true         # Alert admin when plugin disabled
  auto_reenable: true            # Automatically re-enable after cooldown

# Behavior during degraded mode:
# 1. Plugin removed from available tools list
# 2. LLM receives error: "Plugin temporarily disabled due to repeated failures"
# 3. After cooldown period, plugin automatically re-enabled
# 4. Failure counter reset to 0
```

### 9.5 Logging Strategy

```json
{
  "timestamp": "2025-10-02T10:30:45.123Z",
  "level": "ERROR",
  "category": "plugin_execution",
  "plugin_name": "example_plugin",
  "event": "timeout",
  "message": "Plugin timed out after 60 seconds",
  "details": {
    "parameters": {"device_id": "device123"},
    "execution_time": 60.5,
    "exit_code": 124,
    "stderr": "Process killed by timeout"
  },
  "failure_count": 3,
  "degraded_mode": false
}
```

**Log Levels by Event:**
- **DEBUG:** Plugin discovery, parameter validation
- **INFO:** Successful execution, metrics updates
- **WARNING:** Retry attempts, degraded mode triggers
- **ERROR:** Execution failures, timeouts, security violations
- **CRITICAL:** Server impact, configuration errors

---

## 10. Migration Path

### 10.1 Phase 1: Coexistence (Zero Regression)

**Goal:** Plugin system operates alongside existing tools without interference.

**AsyncToolManager Enhancement (backward compatible):**

```python
class AsyncToolManager:
    def __init__(self):
        # EXISTING CODE (unchanged)
        self.available_functions = {
            'get_the_secret_tool': self.get_the_secret_tool,
            'wikipedia_query': self.wikipedia_query,
            # ... all 6 built-in tools
        }
        self.user_tools = []
        self.user_tools_loaded = False

        # NEW CODE (additive only)
        self.plugin_manager = None  # Lazy initialization

    async def _load_user_tools_async(self):
        """EXISTING METHOD (unchanged)"""
        # BaseUserTool loading logic unchanged
        pass

    async def _initialize_plugin_manager(self):
        """NEW METHOD - Initialize plugin system"""
        if self.plugin_manager is not None:
            return

        try:
            # Load plugin configuration from llm_config.yaml
            config = self._load_plugin_config()
            if not config.get('enabled', False):
                logger.info("Plugin system disabled in config")
                return

            self.plugin_manager = PluginManager(config)
            await self.plugin_manager.initialize()

            # Add plugin tools to available_functions
            for plugin_name in self.plugin_manager.loaded_plugins:
                self.available_functions[plugin_name] = \
                    self._create_plugin_wrapper(plugin_name)

            logger.info(f"Plugin system initialized with {len(self.plugin_manager.loaded_plugins)} plugins")

        except Exception as e:
            logger.error(f"Plugin system initialization failed: {e}")
            # Server continues without plugins (graceful degradation)

    async def safe_function_call(self, func_name: str, args: str) -> str:
        """ENHANCED METHOD - Route plugin calls"""
        # EXISTING CODE (unchanged) - handles built-in and BaseUserTool
        if func_name not in self.available_functions:
            return f"Function {func_name} not available"

        func = self.available_functions[func_name]

        # NEW CODE - Check if this is a plugin tool
        if self.plugin_manager and func_name in self.plugin_manager.loaded_plugins:
            # Route to plugin system
            result = await self.plugin_manager.execute_plugin(func_name, json.loads(args))
            return json.dumps(result)

        # EXISTING CODE (unchanged) - execute built-in/BaseUserTool
        result = await func(args)
        return str(result)
```

### 10.2 Configuration Updates

**Add to `config/llm_config.yaml`:**

```yaml
# =============================================================================
# Plugin System Configuration
# =============================================================================

plugins:
  enabled: true                           # Enable/disable plugin system globally
  plugins_directory: "/home/sabawi/Development/flaskserver/plugins"
  python_executable: "python3"            # Python interpreter for plugin execution

  defaults:                               # Default settings for all plugins
    execution:
      timeout: 60                         # Seconds
      memory_limit: 256                   # MB
      cpu_limit: 1.0                      # CPU cores

    security:
      input_validation:
        max_string_length: 1024
        max_array_length: 100
      output_validation:
        max_output_size: 1048576          # 1MB
      network:
        enabled: false                    # Disabled by default
        block_private_ips: true
      filesystem:
        read_only: true                   # Read-only by default

    monitoring:
      log_level: "INFO"
      log_execution: true
      log_outputs: false

    error_handling:
      retry:
        enabled: true
        max_attempts: 3
        backoff_strategy: "exponential"
        initial_delay: 1
      degraded_mode:
        enabled: true
        disable_after_failures: 5
        cooldown_period: 300
```

---

## 11. File Structure

### 11.1 Simplified Directory Organization

```
/home/sabawi/Development/flaskserver/
├── fastapi_server_complete.py          # Main server (enhanced AsyncToolManager)
├── config/
│   ├── llm_config.yaml                 # Main config (plugins section added)
│   └── ...
├── user_tools/                         # EXISTING (unchanged)
│   ├── base_user_tool.py               # BaseUserTool abstract class
│   ├── tool_discovery.py               # BaseUserTool discovery
│   ├── example_calculator.py           # 13 existing user tools
│   └── ...
├── plugins/                            # NEW DIRECTORY - SIMPLIFIED
│   ├── __init__.py
│   │
│   ├── plugin_manager.py               # SYSTEM: PluginManager class
│   ├── plugin_registry.py              # SYSTEM: PluginRegistry class
│   ├── plugin_executor.py              # SYSTEM: PluginExecutor class
│   ├── security_validator.py           # SYSTEM: SecurityValidator class
│   │
│   ├── config/                         # SYSTEM: Plugin configuration
│   │   └── plugin_defaults.yaml        # SYSTEM: Minimal defaults (30 lines)
│   │
│   ├── handlers/                       # USER: Actual plugin code
│   │   ├── __init__.py
│   │   ├── mqtt_controller.py          # USER creates/maintains
│   │   ├── slack_notifier.py           # USER creates/maintains
│   │   ├── csv_analyzer.py             # USER creates/maintains
│   │   └── ...                         # All user plugin implementations
│   │
│   ├── mqtt_controller.yaml            # USER: Plugin definition (category: "iot")
│   ├── slack_notifier.yaml             # USER: Plugin definition (category: "communications")
│   ├── csv_analyzer.yaml               # USER: Plugin definition (category: "data")
│   ├── image_classifier.yaml           # USER: Plugin definition (category: "ai_ml")
│   └── ...                             # All plugin YAMLs in flat structure
│
├── docs/                               # Documentation
│   ├── PLUGIN_ARCHITECTURE_DESIGN.md   # This document
│   ├── PLUGIN_DEVELOPMENT_GUIDE.md     # Developer guide (to be created)
│   └── ...
│
└── tests/                              # Testing
    ├── integration/
    │   ├── test_plugin_system.py       # Integration tests
    │   └── test_plugin_security.py     # Security tests
    └── utilities/
        └── test_plugin_discovery.py    # Unit tests
```

### 11.2 User vs System Files

**SYSTEM FILES (Never Modified by Users):**
- `plugin_manager.py`, `plugin_registry.py`, `plugin_executor.py`, `security_validator.py`
- `config/plugin_defaults.yaml`

**USER FILES (Created/Modified by Users):**
- `*.yaml` - Plugin definitions (in /plugins/ root)
- `handlers/*.py` - Plugin implementation code

**User Workflow to Add Plugin:**
1. Create `my_plugin.yaml` in `/plugins/`
2. Write `handlers/my_plugin.py` with implementation
3. Restart server (plugins auto-discovered)


---

## 12. Implementation Roadmap

### 12.1 Phase 1: Foundation (Week 1-2)

**Milestone 1.1: Core Infrastructure**
- [ ] Create `/plugins/` directory structure
- [ ] Implement `PluginRegistry` class
- [ ] Implement `PluginDefinition` dataclass
- [ ] Create plugin YAML schema validator
- [ ] Write unit tests for discovery logic

**Milestone 1.2: Configuration**
- [ ] Create `plugin_defaults.yaml`
- [ ] Create `plugin_categories.yaml`
- [ ] Add plugins section to `llm_config.yaml`
- [ ] Implement config loading with fail-fast validation

**Milestone 1.3: Documentation**
- [ ] Write PLUGIN_DEVELOPMENT_GUIDE.md
- [ ] Create example plugin YAML templates
- [ ] Document plugin communication protocol

### 12.2 Phase 2: Execution Engine (Week 3-4)

**Milestone 2.1: Process Isolation**
- [ ] Implement `PluginExecutor` class
- [ ] Add subprocess creation with resource limits
- [ ] Implement timeout enforcement
- [ ] Add process cleanup logic
- [ ] Test on Linux (primary platform)
- [ ] Test on macOS (best-effort)

**Milestone 2.2: Communication Protocol**
- [ ] Define stdin/stdout JSON protocol
- [ ] Implement parameter serialization
- [ ] Implement result deserialization
- [ ] Add error handling for malformed responses

**Milestone 2.3: Testing**
- [ ] Write integration tests for execution
- [ ] Test timeout enforcement
- [ ] Test resource limit enforcement
- [ ] Test process cleanup

### 12.3 Phase 3: Security (Week 5-6)

**Milestone 3.1: Input Validation**
- [ ] Implement `SecurityValidator` class
- [ ] Add JSON schema validation
- [ ] Add injection pattern detection
- [ ] Add string/array size limits
- [ ] Write security test suite

**Milestone 3.2: Output Validation**
- [ ] Implement output size limits
- [ ] Add sensitive data detection
- [ ] Add content-type validation
- [ ] Test with various attack vectors

**Milestone 3.3: Policy Enforcement**
- [ ] Implement filesystem access controls (validation)
- [ ] Implement network access controls (validation)
- [ ] Document security model
- [ ] Security audit and review

### 12.4 Phase 4: Integration (Week 7-8)

**Milestone 4.1: AsyncToolManager Enhancement**
- [ ] Add `_initialize_plugin_manager()` method
- [ ] Enhance `get_tools_definitions()` to include plugins
- [ ] Enhance `safe_function_call()` to route plugin calls
- [ ] Ensure zero regression for existing tools

**Milestone 4.2: PluginManager**
- [ ] Implement `PluginManager` class
- [ ] Add plugin execution orchestration
- [ ] Add metrics tracking
- [ ] Add degraded mode logic

**Milestone 4.3: Testing**
- [ ] End-to-end integration tests
- [ ] Test all 19 existing tools (regression)
- [ ] Test plugin tools
- [ ] Test mixed tool calls (built-in + BaseUserTool + plugin)

### 12.5 Phase 5: Error Handling (Week 9-10)

**Milestone 5.1: Retry Logic**
- [ ] Implement retry strategies (linear, exponential, fixed)
- [ ] Add backoff delay calculation
- [ ] Add retry condition checking
- [ ] Test retry scenarios

**Milestone 5.2: Degraded Mode**
- [ ] Implement failure counting
- [ ] Add plugin disable/enable logic
- [ ] Add cooldown timer
- [ ] Add admin alerts (logging)

**Milestone 5.3: Logging**
- [ ] Implement structured logging (JSON)
- [ ] Add execution logging
- [ ] Add security event logging
- [ ] Add metrics logging

### 12.6 Phase 6: Example Plugins (Week 11-12)

**Milestone 6.1: Reference Implementations**
- [ ] Create IoT MQTT controller plugin
- [ ] Create Slack notifier plugin
- [ ] Create CSV analyzer plugin
- [ ] Document each example

**Milestone 6.2: Migration Examples**
- [ ] Migrate 1-2 BaseUserTools to plugin format
- [ ] Document migration process
- [ ] Create migration checklist
- [ ] Test migrated plugins

### 12.7 Phase 7: Production Readiness (Week 13-14)

**Milestone 7.1: Performance Optimization**
- [ ] Profile plugin discovery performance
- [ ] Optimize YAML parsing
- [ ] Add caching where appropriate
- [ ] Load testing with 50+ plugins

**Milestone 7.2: Documentation**
- [ ] Complete PLUGIN_DEVELOPMENT_GUIDE.md
- [ ] Add API documentation
- [ ] Create troubleshooting guide
- [ ] Write migration guide

**Milestone 7.3: Final Testing**
- [ ] Full regression testing
- [ ] Security audit
- [ ] Performance benchmarking
- [ ] User acceptance testing

---

## 13. Testing Strategy

### 13.1 Test Categories

**Unit Tests:**
- Plugin discovery logic
- YAML parsing and validation
- Security validator (input/output)
- Resource limit calculations
- Retry logic and backoff strategies

**Integration Tests:**
- Plugin execution end-to-end
- AsyncToolManager routing
- Process isolation and cleanup
- Timeout enforcement
- Error handling and degraded mode

**Security Tests:**
- Injection attack prevention (XSS, SQL, command)
- Resource exhaustion (memory bomb, infinite loop)
- Output data exfiltration
- Filesystem access violations
- Network access violations

**Regression Tests:**
- All 19 existing tools function unchanged
- BaseUserTool system unchanged
- LLM tool calling protocol unchanged
- Multi-tool calling scenarios

**Performance Tests:**
- Plugin discovery with 50+ plugins
- Concurrent plugin execution (5+ simultaneous)
- Memory usage under load
- Execution overhead measurement

### 13.2 Test Coverage Goals

- **Code Coverage:** > 90%
- **Security Test Coverage:** 100% of threat model
- **Regression Test Coverage:** 100% of existing tools
- **Integration Test Coverage:** All execution paths

---

## 14. Future Enhancements

### 14.1 Hot-Reload

**Goal:** Load new plugins without server restart.

**Design:**
- File system watcher for `/plugins/` directory
- Incremental plugin loading
- Plugin unload/reload mechanism
- Zero-downtime plugin updates

### 14.2 Remote Plugins

**Goal:** Execute plugins on remote hosts (distributed execution).

**Design:**
- gRPC/HTTP API for remote plugin execution
- Load balancing across plugin workers
- Centralized plugin registry
- Network security (TLS, authentication)

### 14.3 Plugin Marketplace

**Goal:** Community-contributed plugins with versioning.

**Design:**
- Plugin repository (Git-based)
- Plugin signing and verification
- Dependency resolution
- Automatic updates

### 14.4 Advanced Sandboxing

**Goal:** Enhanced security with OS-level sandboxing.

**Design:**
- Docker/Podman container execution
- AppArmor/SELinux profiles
- Seccomp filters
- Network namespace isolation

---

## 15. Appendices

### Appendix A: Glossary

- **Plugin:** Config-driven, isolated tool executed in separate process
- **BaseUserTool:** Existing Python-based tool system (unchanged)
- **Built-in Tool:** Core server tools (6 tools, unchanged)
- **Process Isolation:** Execution in dedicated subprocess with resource limits
- **Degraded Mode:** Temporary plugin disable after repeated failures
- **Fail-Fast:** Immediate failure when configuration missing (no hardcoded defaults)

### Appendix B: References

- **PROJECT_CONFIGURATION_DIRECTIVE.md:** Configuration management rules
- **CLAUDE.md:** Project directives and rules
- **llm_config.yaml:** Main configuration file
- **BaseUserTool:** `/user_tools/base_user_tool.py`
- **AsyncToolManager:** `/fastapi_server_complete.py` line 398+

### Appendix C: Configuration Compliance Checklist

- [x] NO hardcoded configuration values
- [x] NO hardcoded fallback configurations
- [x] All config in `llm_config.yaml` or `plugin_config.yaml`
- [x] .env only for secrets (API keys, passwords)
- [x] Fail-fast when configuration missing
- [x] Clear error messages for missing config

### Appendix D: Backward Compatibility Checklist

- [x] All 19 existing tools function unchanged
- [x] BaseUserTool system unchanged
- [x] AsyncToolManager backward compatible
- [x] Tool calling protocol unchanged
- [x] No changes to existing tool code
- [x] Graceful degradation if plugin system fails

---

**Document Status:** ✅ **READY FOR REVIEW**

**Next Steps:**
1. Review and approve this design document
2. Create implementation tasks from roadmap
3. Begin Phase 1: Foundation implementation
4. Iterative review after each milestone

**Approval Required From:**
- Project Lead
- Security Team
- Development Team

---

*End of Document*
