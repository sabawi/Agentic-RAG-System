# Quick Plugin Creation Guide - 5 Minutes to Your First Plugin

**Status:** ✅ Production Ready
**Time Required:** 5 minutes
**Difficulty:** Beginner-friendly

---

## 🎯 What You'll Create

A working plugin that the LLM can call, just like the built-in tools.

**Example:** A plugin that gets weather information, analyzes files, or calls any external service.

---

## ⚡ Quick Start (Copy-Paste Method)

### Step 1: Copy Template Files (30 seconds)

```bash
cd /home/sabawi/Development/flaskserver/plugins

# Copy the fortune plugin as your template
cp fortune_message.yaml my_plugin.yaml
cp handlers/fortune_message.py handlers/my_plugin.py
```

### Step 2: Edit YAML Definition (2 minutes)

Open `my_plugin.yaml` and change these 4 things:

```yaml
metadata:
  name: "my_plugin"                    # ← CHANGE: Your plugin name
  description: |                       # ← CHANGE: What it does (LLM reads this!)
    Get weather information for a city.
    Use this when user asks about weather or temperature.

execution:
  handler: "handlers/my_plugin.py"     # ← CHANGE: Your handler filename

parameters:
  properties:
    city:                              # ← CHANGE: Your parameter name
      type: "string"
      description: "City name"
  required:
    - city                             # ← CHANGE: Required parameters
```

**That's it for the YAML!** Everything else uses smart defaults.

### Step 3: Edit Handler Code (2 minutes)

Open `handlers/my_plugin.py` and find the `execute` function (around line 20):

```python
async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Your plugin logic here"""

    # 1. Get parameters
    city = parameters['city']

    # 2. Do your work (call API, run command, process data, etc.)
    result = f"Weather in {city}: Sunny, 72°F"

    # 3. Return result
    return {
        "success": True,
        "result": result,        # ← Your data goes here
        "error": None
    }
```

**Don't change anything below the execute function!** (The boilerplate handles communication)

### Step 4: Test It (30 seconds)

```bash
echo '{"city": "London"}' | python3 handlers/my_plugin.py
```

**Expected output:**
```json
{
  "success": true,
  "result": "Weather in London: Sunny, 72°F",
  "error": null
}
```

### Step 5: Deploy (restart server)

```bash
./stop_complete.sh && ./start_complete.sh
```

**Done!** Your plugin is now available to the LLM.

---

## 🧪 Test With LLM

Ask the LLM:
```
"Get me weather for Tokyo"
```

The LLM will automatically:
1. See your plugin in the tools list
2. Call `my_plugin` with `{"city": "Tokyo"}`
3. Return the result to the user

---

## 📋 Common Plugin Patterns

### Pattern 1: Call External Command

```python
async def execute(parameters):
    city = parameters['city']

    # Run external command
    result = subprocess.run(
        ['curl', f'wttr.in/{city}?format=3'],
        capture_output=True,
        text=True,
        timeout=10
    )

    return {
        "success": True,
        "result": result.stdout,
        "error": None
    }
```

### Pattern 2: Call External API

```python
async def execute(parameters):
    city = parameters['city']

    # Call API
    response = requests.get(
        f'https://api.weather.com/v1/weather?city={city}',
        timeout=10
    )

    data = response.json()

    return {
        "success": True,
        "result": f"Temperature: {data['temp']}°F",
        "error": None
    }
```

### Pattern 3: Process Data

```python
async def execute(parameters):
    text = parameters['text']

    # Analyze text
    word_count = len(text.split())
    char_count = len(text)

    result = f"Words: {word_count}, Characters: {char_count}"

    return {
        "success": True,
        "result": result,
        "error": None
    }
```

### Pattern 4: Read Files

```python
async def execute(parameters):
    filepath = parameters['path']

    # Read file
    with open(filepath, 'r') as f:
        content = f.read()

    return {
        "success": True,
        "result": f"File has {len(content)} characters",
        "error": None
    }
```

---

## 🔒 Security Settings (Optional)

### Enable Network Access

In your YAML, add:

```yaml
security:
  network:
    enabled: true
    allowed_domains:
      - api.weather.com     # Only allow specific domains
    allowed_ports:
      - 443                 # Only HTTPS
```

### Restrict File Access

```yaml
security:
  filesystem:
    read_only: true         # Prevent writes
    allowed_paths:
      - /home/user/data     # Only allow specific directories
    blocked_paths:
      - /etc                # Block sensitive directories
      - /root
```

---

## 🐛 Troubleshooting

### "Plugin not found"

**Check:**
```bash
ls plugins/my_plugin.yaml          # YAML exists?
ls plugins/handlers/my_plugin.py   # Handler exists?
```

**Fix:** Make sure filenames match what's in the YAML `handler:` field.

### "Invalid JSON"

**Check:**
```bash
echo '{"city": "test"}' | python3 handlers/my_plugin.py | python3 -m json.tool
```

**Fix:** Make sure your `execute()` function returns a dictionary with `success`, `result`, and `error`.

### "Permission denied"

**Check:**
```bash
chmod +x handlers/my_plugin.py
```

### "Module not found"

**Check:** Did you activate the virtual environment?
```bash
source venv/bin/activate
pip install requests  # or whatever library you need
```

---

## 📝 Complete Example: Weather Plugin

**File: `plugins/weather.yaml`**

```yaml
metadata:
  name: "weather"
  version: "1.0.0"
  category: "productivity"
  author: "Your Name"
  description: |
    Get current weather for any city.
    Use when user asks about weather, temperature, or conditions.

execution:
  type: "python"
  handler: "handlers/weather.py"
  entrypoint: "execute"
  timeout: 15

parameters:
  type: "object"
  properties:
    city:
      type: "string"
      description: "City name (e.g., London, Tokyo, New York)"
  required:
    - city

security:
  network:
    enabled: true
    allowed_domains:
      - wttr.in
    allowed_ports:
      - 80
      - 443
```

**File: `plugins/handlers/weather.py`**

```python
#!/usr/bin/env python3
import sys
import json
import asyncio
import subprocess
from typing import Dict, Any

async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Get weather for a city"""
    city = parameters['city']

    try:
        # Call wttr.in weather service
        result = subprocess.run(
            ['curl', '-s', f'wttr.in/{city}?format=3'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {
                "success": False,
                "result": None,
                "error": "Failed to fetch weather data"
            }

        weather_data = result.stdout.strip()

        return {
            "success": True,
            "result": f"🌤️ Weather for {city}: {weather_data}",
            "error": None
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "result": None,
            "error": "Weather service timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Error: {str(e)}"
        }

# ============================================
# DO NOT MODIFY BELOW THIS LINE
# ============================================
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

**Test it:**

```bash
echo '{"city": "Tokyo"}' | python3 plugins/handlers/weather.py
```

**Expected output:**
```json
{
  "success": true,
  "result": "🌤️ Weather for Tokyo: Tokyo: ⛅️  +77°F",
  "error": null
}
```

---

## 🎓 What You've Learned

✅ **Plugin = 2 files**: YAML definition + Python handler
✅ **YAML defines**: What the tool does (LLM reads this)
✅ **Handler implements**: How it works (your code)
✅ **Communication**: JSON in via stdin, JSON out via stdout
✅ **Security**: Network/filesystem controls optional

---

## 🚀 Next Steps

1. **Try the working examples:**
   - `fortune_message` - External command
   - `weather_info` - API calls
   - `file_stats` - File operations
   - `system_monitor` - System metrics
   - `text_analyzer` - Data processing

2. **Read detailed docs:**
   - `/plugins/README.md` - Full plugin system guide
   - `/docs/PLUGIN_USER_GUIDE.md` - Comprehensive manual
   - `/docs/FORTUNE_PLUGIN_EXAMPLE.md` - Detailed walkthrough

3. **Check your plugin status:**
   ```bash
   tail -f logs/server_complete.log | grep "🔌"
   ```

---

## 💡 Tips for Success

1. **Start simple**: Copy an existing plugin and modify it
2. **Test standalone first**: Run handler with `echo '{...}' | python3 handler.py`
3. **Check the logs**: `tail -f logs/server_complete.log`
4. **Use clear descriptions**: The LLM reads your description to decide when to call your plugin
5. **Handle errors gracefully**: Always return `{"success": false, "error": "..."}` on failures

---

## 📞 Need Help?

**Check these files:**
- Working examples: `/plugins/fortune_message.yaml` and `/plugins/handlers/fortune_message.py`
- Full documentation: `/docs/PLUGIN_USER_GUIDE.md`
- Troubleshooting: `/docs/PLUGIN_USER_GUIDE.md#troubleshooting`

**Common issues:**
- Plugin not loading? Check YAML syntax
- Plugin not called? Improve description (LLM uses it to decide)
- Errors? Check `logs/server_complete.log`

---

## ✅ Checklist

Before deploying your plugin:

- [ ] YAML file in `/plugins/` directory
- [ ] Handler file in `/plugins/handlers/` directory
- [ ] `name` in YAML is unique
- [ ] `description` clearly explains what it does
- [ ] `handler` path matches actual filename
- [ ] Handler returns proper JSON format
- [ ] Tested standalone with `echo '{}' | python3 handler.py`
- [ ] No errors in test output
- [ ] Restarted server with `./stop_complete.sh && ./start_complete.sh`

---

**🎉 You're now a plugin developer! Your custom tool is available to the LLM.**

*Remember: Plugins run in isolated processes, so they can't crash the server. Experiment freely!*
