# Changelog v1.0.3.121

**Release Date:** 2025-12-19
**Type:** Feature Enhancement + Bug Fixes

## Summary

This release introduces a centralized configuration system for all autonomous agents, separating agent configuration from server configuration. This allows agents to run on different hosts than the server and provides a single source of truth for all agent settings.

---

## New Features

### 1. Centralized Agent Configuration System
- **New file:** `config/agents_config.yaml` - Single configuration file for all agents
- **New module:** `agents/common/config_loader.py` - Shared configuration loader
- Agents can now be deployed on different hosts than the server
- Configuration supports environment variable expansion (`${VAR_NAME}` syntax)
- Fail-fast behavior when required configuration is missing

### 2. System Tuner Agent Improvements
- Updated to use centralized configuration system (v1.1.0)
- New `--show-config` flag to display merged configuration
- New `--execute` flag (opposite of `--dry-run`)
- Configuration-driven settings for all parameters:
  - Server URL, model, temperature, max_tokens
  - Safety settings (dry_run_default, forbidden_patterns)
  - Execution settings (max_iterations, command_timeout)
  - Backup directory location

### 3. Agent Configuration Features
- Global defaults section for common settings
- Agent-specific overrides
- Safety patterns configuration (forbidden command patterns)
- Support for all 10 agents in the system

---

## Bug Fixes

### System Tuner Agent
1. **Baseline Metrics Overwrite Bug (CRITICAL)** - Fixed issue where `validate_improvements()` was calling `collect_baseline_metrics()` which overwrote the initial baseline, causing invalid comparisons. Now uses separate `initial_baseline_metrics` storage.

2. **Bare Except Clauses** - Replaced all bare `except:` clauses with specific exception types for better error handling and debugging.

3. **Import Location** - Moved `shutil` import to module level (was inside `_backup_file()` function).

4. **Command Timeout** - Now uses configurable timeout instead of hardcoded 30 seconds.

5. **Forbidden Patterns Check** - Added safety check to reject commands containing forbidden patterns before execution.

---

## Files Changed

### New Files
- `config/agents_config.yaml` - Agent configuration file
- `agents/common/config_loader.py` - Configuration loader module
- `docs/AGENT_CONFIGURATION_GUIDE.md` - Configuration documentation

### Modified Files
- `agents/common/__init__.py` - Added config loader exports
- `agents/common/agent_utils.py` - Added config-based client creation, updated functions to accept config parameter
- `agents/system_tuner/autonomous_system_tuner.py` - Full refactor to use config system
- `agents/system_tuner/README.md` - Updated documentation

---

## Configuration Structure

```yaml
# Global defaults
defaults:
  server:
    base_url: "http://localhost:5000/v1"
  llm:
    model: "Agentic-RAG-Model1"
    temperature: 0.7
  execution:
    max_retries: 3

# Agent-specific settings
agents:
  system_tuner:
    enabled: true
    llm:
      temperature: 0.3  # Override for factual responses
    safety:
      dry_run_default: true
      forbidden_patterns:
        - "rm -rf"
        - "mkfs"
```

---

## Dependencies

No new dependencies added. Uses existing:
- `pyyaml` - Already in requirements.txt for YAML parsing
- `openai` - Already in requirements.txt for API client

---

## Breaking Changes

None. All changes are backward compatible:
- Existing agents continue to work with command-line arguments
- Configuration file provides defaults that can be overridden

---

## Migration Guide

### For Existing Agents
No immediate changes required. Agents will:
1. Load configuration from `config/agents_config.yaml`
2. Fall back to command-line arguments if provided
3. Use sensible defaults if neither is available

### To Update an Agent to Use Config System

1. Import the config loader:
```python
from common.config_loader import get_agent_config
config = get_agent_config("my_agent")
```

2. Use config values:
```python
server_url = config.get_server_url()
model = config.get_llm_model()
```

3. Add agent section to `config/agents_config.yaml`

---

## Testing

- [x] Config loader unit tests pass
- [x] System tuner `--show-config` works correctly
- [x] System tuner `--help` shows config defaults
- [x] All 10 agents listed in configuration

---

## Documentation

- Created `docs/AGENT_CONFIGURATION_GUIDE.md` with full usage instructions
- Updated `agents/system_tuner/README.md` with configuration section
- Added inline documentation in `config_loader.py`

---

## Version Information

- **Previous Version:** 1.0.3.120
- **Current Version:** 1.0.3.121
- **Commit Message:** `🔧 FEATURE v1.0.3.121: Centralized agent configuration system + system_tuner improvements`
