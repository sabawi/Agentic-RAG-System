# PROJECT CONFIGURATION DIRECTIVE
## MANDATORY CONFIGURATION MANAGEMENT RULES

**STATUS: ACTIVE PROJECT DIRECTIVE - MANDATORY COMPLIANCE**
**VERSION: 1.0.2.81**
**EFFECTIVE DATE: 2025-09-28**

---

## 🚨 CORE CONFIGURATION RULES - NO EXCEPTIONS

### **RULE 1: ZERO HARDCODED CONFIGURATION VALUES**
```
❌ FORBIDDEN: Any hardcoded configuration values in code
❌ FORBIDDEN: Hardcoded fallback configurations in code
❌ FORBIDDEN: Constants files with configuration values
✅ REQUIRED: All configuration values in llm_config.yaml
✅ REQUIRED: Fail-fast when configuration is missing
```

**Examples of FORBIDDEN code:**
```python
# ❌ NEVER DO THIS
DEFAULT_MODEL = 'qwen3:8b'
FALLBACK_URL = 'http://localhost:11434'
if not config:
    return {'model': 'qwen3:8b', 'url': 'http://localhost:11434'}
```

**Examples of CORRECT code:**
```python
# ✅ CORRECT - Fail fast, force proper configuration
if not config or 'model' not in config:
    raise ValueError("Configuration required in llm_config.yaml")
return config
```

### **RULE 2: .env FILE RESTRICTIONS**
```
✅ ALLOWED in .env: User/account/installation secrets ONLY
  - Email addresses
  - Passwords
  - API keys
  - User IDs
  - Authentication tokens
  - Installation-specific secrets

❌ FORBIDDEN in .env: Any configuration values
  - Model names
  - URLs
  - Timeouts
  - Port numbers
  - File paths
  - Feature toggles
```

**Example .env file (CORRECT):**
```bash
# ✅ CORRECT - Only secrets and user-specific data
GMAIL_PRIMARY_EMAIL="user@example.com"
GMAIL_PRIMARY_APP_PASSWORD="your_app_password_here"
OPENAI_API_KEY="your_openai_key_here"
QWEN_API_KEY="your_qwen_key_here"
```

### **RULE 3: CONFIGURATION FILE ARCHITECTURE**
```
📁 SINGLE SOURCE OF TRUTH: config/llm_config.yaml
  ├── All model configurations
  ├── All timeout values
  ├── All URL endpoints
  ├── All feature toggles
  ├── All fallback configurations
  └── Environment variable references (${VAR_NAME})

❌ ELIMINATED: config/llm_constants.py
❌ ELIMINATED: Multiple config files
❌ ELIMINATED: Hardcoded defaults in code
```

### **RULE 4: CONFIGURATION PRECEDENCE (FINAL)**
```
1. Request-level parameters (highest priority)
2. Environment variables (secrets only: ${OPENAI_API_KEY})
3. config/llm_config.yaml (main configuration)
4. FAILURE - No hardcoded fallbacks allowed
```

---

## 📋 IMPLEMENTATION REQUIREMENTS

### **For All Developers:**
1. **BEFORE writing ANY configuration code:**
   - Check if the value belongs in llm_config.yaml
   - Never create constants files
   - Never hardcode fallback values

2. **Code Review Checklist:**
   - [ ] No hardcoded configuration values
   - [ ] No constants imports for config
   - [ ] All config comes from llm_config.yaml
   - [ ] .env contains only secrets

3. **When Adding New Configuration:**
   - Add to `config/llm_config.yaml` ONLY
   - Document in this file's schema section
   - Update config_loader.py if needed
   - Test failure modes (missing config)

### **For Configuration Changes:**
1. Edit `config/llm_config.yaml`
2. Restart server to load changes
3. Verify in logs: "✅ Configuration loaded from config/llm_config.yaml"

---

## 🛡️ ENFORCEMENT GUIDELINES

### **Automated Checks:**
- [ ] Pre-commit hooks to scan for hardcoded config
- [ ] CI/CD pipeline configuration validation
- [ ] Automated tests for missing config scenarios

### **Manual Review Points:**
- Any new `.py` files with configuration
- Any changes to existing configuration logic
- Any new environment variables
- Any new constant definitions

### **Violation Response:**
1. **IMMEDIATE**: Reject code with hardcoded config
2. **REMEDIATION**: Move values to llm_config.yaml
3. **DOCUMENTATION**: Update this directive if needed

---

## 📖 CONFIGURATION SCHEMA

### **llm_config.yaml Structure:**
```yaml
llm:
  primary:
    type: ollama
    config:
      model: qwen3:8b              # ✅ In YAML
      base_url: http://localhost   # ✅ In YAML
      timeout: 3600               # ✅ In YAML

  fallback:                       # ✅ Fallbacks in YAML
    enabled: true
    order: [ollama, openai]

providers:
  openai:
    api_key: ${OPENAI_API_KEY}    # ✅ Secret from env
    base_url: https://api.openai.com/v1  # ✅ Config in YAML
```

### **.env Structure:**
```bash
# ✅ ONLY secrets and user-specific data
OPENAI_API_KEY=your_openai_key_here
GMAIL_PRIMARY_EMAIL=user@example.com
GMAIL_PRIMARY_APP_PASSWORD=your_app_password_here
```

---

## 🔧 MIGRATION GUIDE

### **From Old System:**
1. **Identify hardcoded values** in your code
2. **Move to llm_config.yaml** under appropriate section
3. **Update code** to read from config_loader
4. **Test failure scenarios** (missing config)
5. **Remove constants files** and hardcoded fallbacks

### **Example Migration:**
```python
# ❌ OLD - Hardcoded
def get_model():
    return config.get('model', 'qwen3:8b')  # Hardcoded fallback

# ✅ NEW - Fail fast
def get_model():
    if 'model' not in config:
        raise ValueError("Model must be configured in llm_config.yaml")
    return config['model']
```

---

## 📝 COMPLIANCE VERIFICATION

To verify compliance in your code:

```bash
# Check for hardcoded config patterns
grep -r "DEFAULT_" --include="*.py" .
grep -r "FALLBACK" --include="*.py" .
grep -r "localhost" --include="*.py" .
grep -r "3600\|8192\|11434" --include="*.py" .

# Should return ZERO results in application code
```

---

## 🎯 SUCCESS CRITERIA

✅ **Configuration is compliant when:**
- No hardcoded configuration values in any .py file
- All fallbacks defined in llm_config.yaml
- .env contains only secrets and user data
- Server fails fast with clear error if config missing
- Single source of truth: llm_config.yaml

❌ **Configuration violations:**
- Any hardcoded model names, URLs, timeouts
- Constants files with configuration values
- Fallback logic with hardcoded defaults
- Configuration values in .env file
- Multiple configuration sources

---

## 🔌 PLUGIN CONFIGURATION (SEPARATE SYSTEM)

**IMPORTANT:** Plugins use a **separate configuration architecture** from LLM configuration documented above.

### Plugin Configuration Model

- **Auto-discovery:** Plugins in `/plugins/*.yaml` are automatically loaded on server startup
- **Optional configuration:** Add `plugins:` section to `llm_config.yaml` for customization only if needed
- **Default behavior:** Sensible defaults (60s timeout, 256MB memory limit, 1.0 CPU limit)
- **Process isolation:** Plugins run in separate processes with resource limits

### Current Plugin Status

Check server logs on startup:
```bash
tail logs/server_complete.log | grep "🔌"
# Output example: 🔌 Loaded 8 plugins in 0.048s
```

### Plugin Documentation

See dedicated plugin documentation for detailed information:

- **📖 User Guide:** `/docs/PLUGIN_USER_GUIDE.md` (Start here!)
- **🏗️ Architecture Design:** `/docs/PLUGIN_ARCHITECTURE_DESIGN.md`
- **⚡ Quick Start:** `/docs/QUICK_PLUGIN_GUIDE.md`
- **📝 Cheat Sheet:** `/docs/PLUGIN_CHEAT_SHEET.md`
- **🎯 Example Plugin:** `/docs/FORTUNE_PLUGIN_EXAMPLE.md`

### When to Add `plugins:` to llm_config.yaml

You only need to add plugin configuration if you want to:
1. **Override resource limits** (increase timeouts, memory, CPU)
2. **Customize security settings** (string length, array limits)
3. **Explicitly disable plugin system** (not recommended)
4. **Set per-plugin overrides** (different settings for specific plugins)

### Example Plugin Configuration (Optional)

```yaml
plugins:
  enabled: true  # Optional: explicitly enable/disable plugin system

  plugin_defaults:
    execution:
      timeout: 120  # Override default 60s
      memory_limit: 512  # Override default 256MB (in MB)
      cpu_limit: 2.0  # Override default 1.0 (number of CPU cores)
      max_timeout: 600  # Maximum allowed timeout
      max_memory_limit: 4096  # Maximum allowed memory

    security:
      input_validation:
        max_string_length: 204800  # Double default (102400)
        max_array_length: 2000  # Double default (1000)
      output_validation:
        max_result_size: 2097152  # 2MB max result

  # Optional: Per-plugin overrides
  social_media_twitter_test:
    execution:
      timeout: 180  # Social media operations may need more time
```

### Plugin vs LLM Configuration

| Aspect | LLM Configuration | Plugin Configuration |
|--------|-------------------|----------------------|
| **Purpose** | Core LLM behavior | Tool extensions |
| **Location** | `llm_config.yaml` (required) | `llm_config.yaml` (optional) |
| **Discovery** | Explicit configuration | Auto-discovery from `/plugins/` |
| **Defaults** | Must be configured | Sensible defaults provided |
| **Failure Mode** | Fail-fast if missing | Use defaults if missing |
| **This Directive** | Fully applies | Separate architecture |

### Key Differences

1. **LLM config is mandatory** - server fails without it
2. **Plugin config is optional** - system works with sensible defaults
3. **Plugins auto-discover** - just drop YAML + handler in `/plugins/`
4. **Different paradigm** - plugins are "drop-in extensions" not core infrastructure

### Plugin Configuration Compliance

✅ **Plugin configuration is compliant when:**
- Plugin YAML files are in `/plugins/` directory
- Plugin handlers are in `/plugins/handlers/` directory
- Optional `plugins:` section in llm_config.yaml if custom settings needed
- Plugins load successfully on server startup (check logs)

❌ **Plugin configuration issues:**
- Hardcoded plugin settings in server code
- Plugin logic embedded in main server file
- Missing plugin handler files
- Invalid YAML syntax in plugin definitions

**NOTE:** This directive focuses on LLM configuration. For comprehensive plugin documentation, see the dedicated plugin guides listed above.

---

**DIRECTIVE AUTHORITY:** Project Architecture Team
**ENFORCEMENT:** Mandatory for all developers
**REVIEW CYCLE:** Quarterly or as needed
**LAST UPDATED:** 2025-09-28 v1.0.2.81