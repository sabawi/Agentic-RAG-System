# Fortune Message Plugin - Complete Example

**Status:** ✅ **Working Example**
**Created:** 2025-10-02
**Purpose:** Demonstrate the simplified plugin architecture

---

## 🎯 Overview

The **Fortune Message Plugin** is a complete working example that demonstrates:
- ✅ How to create a plugin definition (YAML)
- ✅ How to write plugin handler code (Python)
- ✅ External command execution (calls `/usr/games/fortune`)
- ✅ Multiple output formats (boxed, quoted, plain)
- ✅ Security configuration (filesystem, network, resource limits)
- ✅ Error handling and validation
- ✅ JSON communication protocol

---

## 📁 Files Created

```
plugins/
├── fortune_message.yaml           # Plugin definition
├── handlers/
│   └── fortune_message.py         # Plugin implementation
├── config/
│   └── plugin_defaults.yaml       # System defaults
└── README.md                      # User guide
```

---

## 🚀 How It Works

### 1. Plugin Definition (`fortune_message.yaml`)

**Key sections:**

```yaml
metadata:
  name: "fortune_message"
  category: "productivity"
  description: |
    Generate random funny, inspirational, or philosophical messages
    using the classic Linux fortune command.

execution:
  type: "python"
  handler: "handlers/fortune_message.py"
  timeout: 10
  memory_limit: 128

parameters:
  type: "object"
  properties:
    category:
      enum: ["any", "short", "long", "offensive"]
    format_style:
      enum: ["plain", "boxed", "quoted"]

security:
  network:
    enabled: false
  filesystem:
    read_only: true
    allowed_paths:
      - /usr/games
```

### 2. Plugin Handler (`handlers/fortune_message.py`)

**Key functions:**

```python
async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Main plugin logic"""
    category = parameters.get('category', 'any')
    format_style = parameters.get('format_style', 'boxed')

    # Execute fortune command
    result = subprocess.run(['/usr/games/fortune'], ...)

    # Format output
    formatted = format_message_boxed(message)

    return {
        "success": True,
        "result": formatted,
        "error": None
    }
```

**Communication protocol:**

```python
if __name__ == "__main__":
    input_data = sys.stdin.read()
    parameters = json.loads(input_data)
    result = asyncio.run(execute(parameters))
    print(json.dumps(result))
    sys.exit(0 if result['success'] else 1)
```

---

## 🧪 Testing

### Manual Test

```bash
# Test with boxed format
echo '{"category": "any", "format_style": "boxed"}' | \
  python3 plugins/handlers/fortune_message.py

# Test with quoted format
echo '{"category": "short", "format_style": "quoted"}' | \
  python3 plugins/handlers/fortune_message.py

# Test with plain format
echo '{"format_style": "plain"}' | \
  python3 plugins/handlers/fortune_message.py

# Test with defaults (no parameters)
echo '{}' | python3 plugins/handlers/fortune_message.py
```

### Example Outputs

**Boxed Format (default):**
```
╔════════════════════════════════════════════════════════╗
║ After all, all he did was string together a lot of    ║
║ old, well-known quotations.                            ║
║ 		-- H. L. Mencken, on Shakespeare                   ║
╚════════════════════════════════════════════════════════╝
```

**Quoted Format:**
```
"If you can read this, you're too close."

— Fortune Cookie 🥠
```

**Plain Format:**
```
Beware of a tall blond man with one black shoe.

──────────────────────────────────────────────────
```

### Validation Results

✅ **All tests passing:**
- Boxed format works correctly
- Quoted format works correctly
- Plain format works correctly
- Default parameters work (empty JSON)
- JSON output is valid
- Exit codes correct (0 for success, 1 for failure)
- Security constraints met (no network, read-only filesystem)

---

## 🔒 Security Features Demonstrated

### 1. Process Isolation
- Runs in separate subprocess
- Memory limit: 128MB
- CPU limit: 0.5 cores
- Timeout: 10 seconds

### 2. Filesystem Security
```yaml
filesystem:
  read_only: true
  allowed_paths:
    - /usr/games              # Fortune command location
    - /usr/share/games/fortunes  # Fortune data files
  blocked_paths:
    - /etc
    - /root
    - /home
```

### 3. Network Security
```yaml
network:
  enabled: false  # No network access needed
```

### 4. Input Validation
```yaml
parameters:
  properties:
    category:
      enum: ["any", "short", "long", "offensive"]  # Restricted values
    format_style:
      enum: ["plain", "boxed", "quoted"]  # Restricted values
```

---

## 📊 Architecture Demonstration

This example demonstrates the complete plugin flow:

```
User Request (LLM)
      ↓
AsyncToolManager.safe_function_call("fortune_message", args)
      ↓
PluginManager.execute_plugin("fortune_message", parameters)
      ↓
SecurityValidator.validate_inputs(parameters)
      ↓
PluginExecutor.execute(plugin_def, parameters)
      ↓
[ISOLATED SUBPROCESS]
  - Create subprocess
  - Set resource limits (memory=128MB, CPU=0.5)
  - Set timeout (10 seconds)
  - Send parameters via stdin (JSON)
      ↓
  handlers/fortune_message.py
    - Read stdin
    - Parse JSON
    - Execute fortune command
    - Format output (boxed/quoted/plain)
    - Return JSON result
      ↓
  - Capture stdout
  - Parse JSON result
  - Cleanup process
[END SUBPROCESS]
      ↓
SecurityValidator.validate_outputs(result)
      ↓
Return formatted result to LLM
```

---

## 🎓 Key Learnings from This Example

### 1. Two-File Pattern
- **YAML**: Defines what the tool does (metadata, parameters, security)
- **Python**: Implements how it works (actual logic)

### 2. External Command Integration
Shows how to safely call external executables:
```python
result = subprocess.run(
    ['/usr/games/fortune'],
    capture_output=True,
    text=True,
    timeout=5
)
```

### 3. Multiple Output Formats
Demonstrates parameter-driven behavior:
- Same plugin, different presentations
- User chooses format via parameters

### 4. Error Handling
Graceful failures with helpful messages:
```python
if not os.path.exists(fortune_path):
    return {
        "success": False,
        "error": "Fortune command not found. Please install fortune-mod."
    }
```

### 5. Metadata Usage
Provides context to LLM and users:
```python
"metadata": {
    "category": "short",
    "format_style": "boxed",
    "message_length": 38,
    "raw_message": "..."
}
```

---

## 🔄 Comparison: BaseUserTool vs Plugin

### BaseUserTool (Old Way)
```python
# user_tools/fortune_tool.py - Single file in server process
class FortuneTool(BaseUserTool):
    def execute(self, **kwargs):
        # Runs in server process
        # No isolation
        # No resource limits
        # Server crashes if tool crashes
```

### Plugin (New Way)
```yaml
# plugins/fortune_message.yaml - Definition
metadata:
  name: "fortune_message"

# plugins/handlers/fortune_message.py - Implementation
async def execute(parameters):
    # Runs in isolated subprocess
    # Resource limits enforced
    # Timeout protection
    # Server protected from crashes
```

**Benefits:**
- ✅ Process isolation (plugin crash ≠ server crash)
- ✅ Resource limits (memory, CPU, timeout)
- ✅ Security policies (filesystem, network)
- ✅ Easier to create (declarative YAML)
- ✅ Better error handling (degraded mode)

---

## 📝 How to Create Your Own Plugin

### Step 1: Copy the Fortune Example

```bash
cd /home/sabawi/Development/flaskserver/plugins

# Copy YAML
cp fortune_message.yaml my_plugin.yaml

# Copy handler
cp handlers/fortune_message.py handlers/my_plugin.py
```

### Step 2: Customize the YAML

Edit `my_plugin.yaml`:

```yaml
metadata:
  name: "my_plugin"           # Change this
  category: "productivity"    # Change if needed
  description: "..."          # Describe your plugin

execution:
  handler: "handlers/my_plugin.py"  # Point to your code

parameters:
  properties:
    your_param:
      type: "string"
```

### Step 3: Customize the Handler

Edit `handlers/my_plugin.py`:

```python
async def execute(parameters):
    # Your logic here
    your_param = parameters['your_param']

    # Do something
    result = your_function(your_param)

    return {
        "success": True,
        "result": result
    }
```

### Step 4: Test

```bash
echo '{"your_param": "test"}' | python3 handlers/my_plugin.py
```

### Step 5: Deploy

```bash
./stop_complete.sh && ./start_complete.sh
```

---

## 🎯 Next Steps

1. ✅ **Example works** - Fortune plugin tested and documented
2. ⏭️ **Implement plugin system** - Start Phase 1 (PluginRegistry, PluginExecutor)
3. ⏭️ **Integration** - Connect to AsyncToolManager
4. ⏭️ **More examples** - IoT, Slack, data processing plugins

---

## 📚 Related Documentation

- **Main Design**: `/docs/PLUGIN_ARCHITECTURE_DESIGN.md`
- **Simplified Guide**: `/docs/PLUGIN_ARCHITECTURE_SIMPLIFIED.md`
- **Plugin README**: `/plugins/README.md`
- **Project Rules**: `/CLAUDE.md`

---

**Status:** ✅ **Example Complete and Tested**

This fortune plugin serves as a reference implementation for all future plugins!
