# Agent Configuration Guide

## Overview

All autonomous agents in the Agentic-RAG system use a centralized configuration file located at `config/agents_config.yaml`. This configuration is **separate** from the server's `llm_config.yaml` to allow:

- Agents to run on different hosts than the server
- Independent agent deployment and configuration
- Clear separation of concerns between server and agent configs

## Configuration File Location

```
config/agents_config.yaml
```

Agents can also find the config via the `AGENTS_CONFIG_PATH` environment variable.

## Configuration Structure

### Global Defaults

The `defaults` section contains settings that apply to all agents unless overridden:

```yaml
defaults:
  server:
    base_url: "http://localhost:5000/v1"
    health_check_timeout: 10
    api_key: "not-required"

  llm:
    model: "Agentic-RAG-Model1"
    temperature: 0.7
    max_tokens: 4096
    timeout: 600

  execution:
    max_retries: 3
    retry_base_delay: 2.0
    command_timeout: 30

  logging:
    level: "INFO"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Agent-Specific Configuration

Each agent has its own section under `agents:` that can override defaults and add agent-specific settings:

```yaml
agents:
  system_tuner:
    enabled: true

    llm:
      temperature: 0.3  # Override default for more factual responses

    safety:
      dry_run_default: true
      forbidden_patterns:
        - "rm -rf"
        - "mkfs"
```

## Using Configuration in Agent Code

### Import the Config Loader

```python
from common.config_loader import get_agent_config, AgentConfigError

# Load configuration for your agent
try:
    config = get_agent_config("my_agent_name")
except AgentConfigError as e:
    print(f"Failed to load config: {e}")
    sys.exit(1)
```

### Access Configuration Values

```python
# Server settings
server_url = config.get_server_url()
api_key = config.get_api_key()

# LLM settings
model = config.get_llm_model()
temperature = config.get_llm_setting('temperature', default=0.7)
max_tokens = config.get_llm_setting('max_tokens', default=4096)

# Execution settings
max_retries = config.get_execution_setting('max_retries', default=3)

# Agent-specific settings (use generic get method)
my_setting = config.get('custom_section', 'setting_name', default='value')

# Required settings (fail-fast if missing)
required_value = config.get('section', 'key', required=True)
```

### Create OpenAI Client from Config

```python
from common.agent_utils import create_client_from_config

client = create_client_from_config(config)
```

## Environment Variable Support

Configuration values can reference environment variables using `${VAR_NAME}` or `${VAR_NAME:default}` syntax:

```yaml
server:
  api_key: "${AGENT_API_KEY:not-required}"
  base_url: "${AGENT_SERVER_URL:http://localhost:5000/v1}"
```

## Configuration Precedence

1. **Command-line arguments** (highest priority)
2. **Agent-specific config** in `agents_config.yaml`
3. **Global defaults** in `agents_config.yaml`

## Adding a New Agent

1. Add a new section under `agents:` in `config/agents_config.yaml`:

```yaml
agents:
  my_new_agent:
    enabled: true

    llm:
      temperature: 0.5

    output:
      directory: "agents/my_new_agent/output"
```

2. In your agent code, load the config:

```python
from common.config_loader import get_agent_config

AGENT_NAME = "my_new_agent"
config = get_agent_config(AGENT_NAME)
```

## Validation

The config loader validates:
- Configuration file exists and is valid YAML
- Agent is defined and enabled
- Required values are present when `required=True` is specified

Missing configuration will cause fail-fast behavior to prevent runtime errors.

## Listing Available Agents

```python
from common.config_loader import AgentConfigLoader

agents = AgentConfigLoader.list_agents()
print(agents)  # ['system_tuner', 'business_intelligence', ...]
```

## Debugging Configuration

Use the `--show-config` flag (if implemented by the agent) to see the merged configuration:

```bash
python agents/system_tuner/autonomous_system_tuner.py --show-config
```

Or programmatically:

```python
config = get_agent_config("system_tuner")
print(config.to_dict())
```
