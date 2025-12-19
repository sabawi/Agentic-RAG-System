#!/usr/bin/env python3
"""
Agent Configuration Loader
==========================

Centralized configuration loader for all autonomous agents.
Loads configuration from config/agents_config.yaml with environment variable expansion.

This loader is SEPARATE from the server's config loader to allow:
  - Agents to run on different hosts than the server
  - Independent agent configuration management
  - Clear separation of concerns

Usage:
    from common.config_loader import AgentConfigLoader

    # Load configuration for a specific agent
    config = AgentConfigLoader.get_agent_config("system_tuner")

    # Access configuration values
    server_url = config.get_server_url()
    model = config.get_llm_setting("model")
    max_retries = config.get_execution_setting("max_retries")

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

import os
import re
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

logger = logging.getLogger(__name__)


class AgentConfigError(Exception):
    """Raised when agent configuration is invalid or missing."""
    pass


class AgentConfigLoader:
    """
    Centralized configuration loader for autonomous agents.

    Loads configuration from config/agents_config.yaml and provides
    convenient access methods with proper defaults handling.
    """

    _config: Optional[Dict] = None
    _config_path: Optional[Path] = None

    # Environment variable pattern: ${VAR_NAME} or ${VAR_NAME:default}
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}:]+)(?::([^}]*))?\}')

    @classmethod
    def _find_config_file(cls) -> Path:
        """
        Find the agents_config.yaml file.

        Searches in order:
        1. AGENTS_CONFIG_PATH environment variable
        2. ./config/agents_config.yaml (relative to project root)
        3. ../config/agents_config.yaml (from agents directory)
        4. ../../config/agents_config.yaml (from agents/common directory)

        Returns:
            Path to configuration file

        Raises:
            AgentConfigError: If configuration file not found
        """
        # Check environment variable first
        env_path = os.environ.get('AGENTS_CONFIG_PATH')
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
            logger.warning(f"AGENTS_CONFIG_PATH set but file not found: {env_path}")

        # Search paths relative to this file's location
        this_file = Path(__file__).resolve()
        search_paths = [
            this_file.parent.parent.parent / "config" / "agents_config.yaml",  # From agents/common/
            Path.cwd() / "config" / "agents_config.yaml",  # From project root
        ]

        for path in search_paths:
            if path.exists():
                return path

        # If not found, provide helpful error message
        searched = "\n  - ".join(str(p) for p in search_paths)
        raise AgentConfigError(
            f"agents_config.yaml not found. Searched:\n  - {searched}\n"
            f"Set AGENTS_CONFIG_PATH environment variable or ensure file exists."
        )

    @classmethod
    def _expand_env_vars(cls, value: Any) -> Any:
        """
        Recursively expand environment variables in configuration values.

        Supports ${VAR_NAME} and ${VAR_NAME:default} syntax.

        Args:
            value: Configuration value (string, dict, list, or other)

        Returns:
            Value with environment variables expanded
        """
        if isinstance(value, str):
            def replace_env_var(match):
                var_name = match.group(1)
                default = match.group(2)
                env_value = os.environ.get(var_name)
                if env_value is not None:
                    return env_value
                if default is not None:
                    return default
                # Return original if no value and no default
                return match.group(0)

            return cls.ENV_VAR_PATTERN.sub(replace_env_var, value)

        elif isinstance(value, dict):
            return {k: cls._expand_env_vars(v) for k, v in value.items()}

        elif isinstance(value, list):
            return [cls._expand_env_vars(item) for item in value]

        return value

    @classmethod
    def load_config(cls, force_reload: bool = False) -> Dict:
        """
        Load the agents configuration file.

        Caches the configuration for subsequent calls.

        Args:
            force_reload: If True, reload even if already cached

        Returns:
            Complete configuration dictionary

        Raises:
            AgentConfigError: If configuration file is invalid
        """
        if cls._config is not None and not force_reload:
            return cls._config

        config_path = cls._find_config_file()
        cls._config_path = config_path

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise AgentConfigError(f"Invalid YAML in {config_path}: {e}")
        except Exception as e:
            raise AgentConfigError(f"Failed to read {config_path}: {e}")

        if not raw_config:
            raise AgentConfigError(f"Empty configuration file: {config_path}")

        # Expand environment variables
        cls._config = cls._expand_env_vars(raw_config)

        logger.info(f"✅ Agent configuration loaded from {config_path}")
        return cls._config

    @classmethod
    def get_defaults(cls) -> Dict:
        """
        Get global default settings.

        Returns:
            Dictionary of default settings
        """
        config = cls.load_config()
        return config.get('defaults', {})

    @classmethod
    def get_agent_config(cls, agent_name: str) -> 'AgentConfig':
        """
        Get configuration for a specific agent.

        Args:
            agent_name: Name of the agent (e.g., 'system_tuner', 'business_intelligence')

        Returns:
            AgentConfig object for the specified agent

        Raises:
            AgentConfigError: If agent configuration is missing or disabled
        """
        config = cls.load_config()

        agents = config.get('agents', {})
        if agent_name not in agents:
            available = list(agents.keys())
            raise AgentConfigError(
                f"No configuration found for agent '{agent_name}'. "
                f"Available agents: {available}"
            )

        agent_config = agents[agent_name]

        # Check if agent is enabled
        if not agent_config.get('enabled', True):
            raise AgentConfigError(f"Agent '{agent_name}' is disabled in configuration")

        defaults = cls.get_defaults()
        return AgentConfig(agent_name, agent_config, defaults)

    @classmethod
    def get_config_path(cls) -> Optional[Path]:
        """Get the path to the loaded configuration file."""
        if cls._config_path is None:
            cls.load_config()
        return cls._config_path

    @classmethod
    def list_agents(cls) -> list:
        """
        List all configured agents.

        Returns:
            List of agent names
        """
        config = cls.load_config()
        return list(config.get('agents', {}).keys())


class AgentConfig:
    """
    Configuration wrapper for a specific agent.

    Provides convenient access to agent configuration with proper
    defaults handling and fail-fast behavior for missing required values.
    """

    def __init__(self, agent_name: str, agent_config: Dict, defaults: Dict):
        """
        Initialize agent configuration.

        Args:
            agent_name: Name of the agent
            agent_config: Agent-specific configuration
            defaults: Global default configuration
        """
        self.agent_name = agent_name
        self._config = agent_config
        self._defaults = defaults

    def _get_nested(self, config: Dict, *keys: str, default: Any = None) -> Any:
        """
        Get a nested value from configuration dictionary.

        Args:
            config: Configuration dictionary
            *keys: Keys to traverse
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        current = config
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
            if current is None:
                return default
        return current

    def get(self, *keys: str, default: Any = None, required: bool = False) -> Any:
        """
        Get a configuration value with defaults fallback.

        First checks agent-specific config, then falls back to defaults.

        Args:
            *keys: Configuration path (e.g., 'llm', 'temperature')
            default: Default value if not found anywhere
            required: If True, raise error when value is missing

        Returns:
            Configuration value

        Raises:
            AgentConfigError: If required=True and value is missing
        """
        # Try agent-specific config first
        value = self._get_nested(self._config, *keys)
        if value is not None:
            return value

        # Try defaults
        value = self._get_nested(self._defaults, *keys)
        if value is not None:
            return value

        # Use provided default
        if default is not None:
            return default

        # Check if required
        if required:
            path = '.'.join(keys)
            raise AgentConfigError(
                f"Required configuration '{path}' not found for agent '{self.agent_name}'"
            )

        return None

    # Convenience methods for common configuration values

    def get_server_url(self) -> str:
        """Get server base URL."""
        return self.get('server', 'base_url', required=True)

    def get_api_key(self) -> str:
        """Get API key for server authentication."""
        return self.get('server', 'api_key', default='not-required')

    def get_health_check_timeout(self) -> int:
        """Get health check timeout in seconds."""
        return self.get('server', 'health_check_timeout', default=10)

    def get_llm_model(self) -> str:
        """Get LLM model name."""
        return self.get('llm', 'model', required=True)

    def get_llm_setting(self, setting: str, default: Any = None) -> Any:
        """Get an LLM setting (temperature, max_tokens, timeout, etc.)."""
        return self.get('llm', setting, default=default)

    def get_execution_setting(self, setting: str, default: Any = None) -> Any:
        """Get an execution setting (max_retries, retry_base_delay, etc.)."""
        return self.get('execution', setting, default=default)

    def get_output_directory(self) -> Optional[str]:
        """Get output directory path."""
        return self.get('output', 'directory')

    def get_log_file(self) -> Optional[str]:
        """Get log file path."""
        return self.get('output', 'log_file') or self.get('logging', 'log_file')

    def get_log_level(self) -> str:
        """Get logging level."""
        return self.get('logging', 'level', default='INFO')

    def is_enabled(self) -> bool:
        """Check if the agent is enabled."""
        return self._config.get('enabled', True)

    def get_safety_setting(self, setting: str, default: Any = None) -> Any:
        """Get a safety setting (for system_tuner agent)."""
        return self.get('safety', setting, default=default)

    def get_backup_setting(self, setting: str, default: Any = None) -> Any:
        """Get a backup setting (for system_tuner agent)."""
        return self.get('backup', setting, default=default)

    def to_dict(self) -> Dict:
        """
        Get complete merged configuration as dictionary.

        Returns:
            Merged configuration (agent-specific + defaults)
        """
        # Deep merge defaults with agent config
        import copy
        merged = copy.deepcopy(self._defaults)
        self._deep_merge(merged, self._config)
        return merged

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge override into base dictionary."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value


# Convenience function for quick access
def get_agent_config(agent_name: str) -> AgentConfig:
    """
    Convenience function to get agent configuration.

    Args:
        agent_name: Name of the agent

    Returns:
        AgentConfig object for the specified agent
    """
    return AgentConfigLoader.get_agent_config(agent_name)
