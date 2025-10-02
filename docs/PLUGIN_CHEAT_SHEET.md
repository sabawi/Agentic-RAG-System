# Plugin System Cheat Sheet - One Page Reference

**Quick access to everything you need to create and manage plugins**

---

## 🚀 Create a Plugin in 4 Steps

```bash
# 1. Copy template
cd /home/sabawi/Development/flaskserver/plugins
cp fortune_message.yaml my_plugin.yaml
cp handlers/fortune_message.py handlers/my_plugin.py

# 2. Edit YAML (change name, description, parameters)
nano my_plugin.yaml

# 3. Edit handler (modify execute function)
nano handlers/my_plugin.py

# 4. Test and deploy
echo '{"param": "value"}' | python3 handlers/my_plugin.py
./stop_complete.sh && ./start_complete.sh
```

---

## 📋 YAML Template (Minimal)

```yaml
metadata:
  name: "my_plugin"
  version: "1.0.0"
  category: "productivity"
  author: "Your Name"
  description: "What it does and when to use it"

execution:
  type: "python"
  handler: "handlers/my_plugin.py"
  entrypoint: "execute"

parameters:
  type: "object"
  properties:
    param1:
      type: "string"
      description: "Parameter description"
  required: ["param1"]
```

---

## 🐍 Python Handler Template (Minimal)

```python
#!/usr/bin/env python3
import sys
import json
import asyncio
from typing import Dict, Any

async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    # Get parameters
    param1 = parameters['param1']

    # Your code here
    result = f"Processed: {param1}"

    # Return result
    return {
        "success": True,
        "result": result,
        "error": None
    }

# Boilerplate (don't change)
if __name__ == "__main__":
    try:
        input_data = sys.stdin.read()
        parameters = json.loads(input_data)
        result = asyncio.run(execute(parameters))
        print(json.dumps(result))
        sys.exit(0 if result['success'] else 1)
    except Exception as e:
        print(json.dumps({"success": False, "result": None, "error": str(e)}))
        sys.exit(1)
```

---

## 🔧 Common Code Patterns

### External Command
```python
result = subprocess.run(['command', 'arg'], capture_output=True, text=True, timeout=10)
return {"success": True, "result": result.stdout, "error": None}
```

### API Call
```python
response = requests.get('https://api.example.com/data', timeout=10)
data = response.json()
return {"success": True, "result": data, "error": None}
```

### Read File
```python
with open(filepath, 'r') as f:
    content = f.read()
return {"success": True, "result": content, "error": None}
```

### Error Handling
```python
try:
    # your code
    return {"success": True, "result": result, "error": None}
except Exception as e:
    return {"success": False, "result": None, "error": str(e)}
```

---

## 🔒 Security Settings

### Enable Network
```yaml
security:
  network:
    enabled: true
    allowed_domains: ["api.example.com"]
    allowed_ports: [443]
```

### Restrict Filesystem
```yaml
security:
  filesystem:
    read_only: true
    allowed_paths: ["/home/user/data"]
    blocked_paths: ["/etc", "/root"]
```

---

## 🧪 Testing Commands

```bash
# Test handler standalone
echo '{"param": "value"}' | python3 handlers/my_plugin.py

# Validate JSON output
echo '{"param": "value"}' | python3 handlers/my_plugin.py | python3 -m json.tool

# Check exit code
echo '{"param": "value"}' | python3 handlers/my_plugin.py
echo $?  # Should be 0 for success

# Make executable
chmod +x handlers/my_plugin.py

# Check plugin loaded
tail -f logs/server_complete.log | grep "🔌"
```

---

## 📊 File Locations

```
/plugins/
├── my_plugin.yaml              # Your plugin definition
├── handlers/
│   └── my_plugin.py            # Your plugin code
├── config/
│   └── plugin_defaults.yaml    # System defaults (don't edit)
├── plugin_manager.py           # System (don't edit)
├── plugin_registry.py          # System (don't edit)
├── plugin_executor.py          # System (don't edit)
└── security_validator.py       # System (don't edit)
```

---

## 🐛 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Plugin not found | Check YAML file exists in `/plugins/` |
| Handler not found | Check `handler:` path in YAML matches filename |
| Invalid JSON | Add `python3 -m json.tool` to test command |
| Permission denied | Run `chmod +x handlers/my_plugin.py` |
| Module not found | Activate venv: `source venv/bin/activate` |
| Plugin not called by LLM | Improve `description` - LLM uses it to decide |

---

## 📈 Working Examples

```bash
# Fortune message (external command)
echo '{"format_style": "boxed"}' | python3 handlers/fortune_message.py

# Weather info (API call)
echo '{"city": "Tokyo"}' | python3 handlers/weather_info.py

# File stats (filesystem)
echo '{"path": "/tmp"}' | python3 handlers/file_stats.py

# System monitor (libraries)
echo '{"metric": "cpu"}' | python3 handlers/system_monitor.py

# Text analyzer (data processing)
echo '{"text": "Hello world", "analysis_type": "basic"}' | python3 handlers/text_analyzer.py
```

---

## 🎯 Categories

- `productivity` - General tools, utilities
- `system` - System operations, monitoring
- `data` - Data processing, analysis
- `iot` - IoT devices, smart home
- `communications` - Email, messaging
- `ai_ml` - AI/ML services

---

## 🚦 Server Commands

```bash
# Start server
./start_complete.sh

# Stop server
./stop_complete.sh

# Restart (after plugin changes)
./stop_complete.sh && ./start_complete.sh

# Monitor logs
tail -f logs/server_complete.log

# Filter plugin logs only
tail -f logs/server_complete.log | grep "🔌"

# Check server status
ps aux | grep fastapi_server_complete
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `QUICK_PLUGIN_GUIDE.md` | 5-minute tutorial |
| `PLUGIN_CHEAT_SHEET.md` | This file - quick reference |
| `/plugins/README.md` | Plugin system overview |
| `PLUGIN_USER_GUIDE.md` | Complete user manual |
| `FORTUNE_PLUGIN_EXAMPLE.md` | Detailed example walkthrough |
| `PLUGIN_SYSTEM_COMPLETE.md` | System status & architecture |

---

## ⚙️ Configuration (Optional)

Add to `/config/llm_config.yaml`:

```yaml
plugins:
  plugin_defaults:
    execution:
      timeout: 60
      memory_limit: 256
      cpu_limit: 1.0
    security:
      input_validation:
        max_string_length: 102400
    error_handling:
      retry:
        enabled: true
        max_attempts: 3
      degraded_mode:
        enabled: true
        disable_after_failures: 5
```

---

## 🎯 Best Practices Checklist

- [ ] Clear, descriptive plugin name
- [ ] Description explains WHEN to use it (LLM reads this)
- [ ] All parameters documented
- [ ] Error handling in place
- [ ] Returns proper JSON format
- [ ] Tested standalone before deployment
- [ ] Network security configured if needed
- [ ] Timeout appropriate for task (10s simple, 60s API, 120s processing)

---

## 💡 Pro Tips

1. **Copy working examples** - Don't start from scratch
2. **Test standalone first** - Debug before deploying
3. **Use clear descriptions** - LLM decides based on description
4. **Log everything** - Helps debugging: `logger.info("Step X complete")`
5. **Start simple** - Get basic version working, then enhance

---

## 🎓 Remember

- Plugin = **2 files** (YAML + Python)
- Communication = **JSON in/out**
- Execution = **Isolated subprocess**
- Security = **6 layers protection**
- Crashes = **Don't affect server**

---

**📞 Need more help?** Check `/docs/QUICK_PLUGIN_GUIDE.md` for detailed walkthrough!
