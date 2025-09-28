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

**DIRECTIVE AUTHORITY:** Project Architecture Team
**ENFORCEMENT:** Mandatory for all developers
**REVIEW CYCLE:** Quarterly or as needed
**LAST UPDATED:** 2025-09-28 v1.0.2.81