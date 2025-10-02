"""
Configuration loader for LLM providers and cross-platform settings
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from .platform import platform_paths, EnvironmentManager

# Constants moved from llm_constants.py - these are ONLY emergency fallbacks
# All real configuration should come from llm_config.yaml
EMERGENCY_FALLBACK_BASE_URL = 'http://127.0.0.1:11434'
EMERGENCY_FALLBACK_TIMEOUT = 600

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Loads and manages configuration for LLM providers and platform settings"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize config loader
        
        Args:
            config_file: Path to config file, defaults to config/llm_config.yaml
        """
        if config_file:
            self.config_file = Path(config_file)
        else:
            # Look for config file in multiple locations
            possible_locations = [
                Path("config/llm_config.yaml"),
                Path(__file__).parent.parent / "config" / "llm_config.yaml",
                platform_paths.get_config_dir() / "llm_config.yaml"
            ]
            
            self.config_file = None
            for location in possible_locations:
                if location.exists():
                    self.config_file = location
                    break
            
            if not self.config_file:
                # Default to the first location for creation
                self.config_file = possible_locations[0]
        
        self._config_cache = None
        logger.info(f"🔧 Config loader initialized with file: {self.config_file}")
    
    def load_config(self, reload: bool = False) -> Dict[str, Any]:
        """Load configuration from YAML file
        
        Args:
            reload: Force reload from disk even if cached
            
        Returns:
            Dict containing full configuration
        """
        if self._config_cache and not reload:
            return self._config_cache
        
        if not self.config_file.exists():
            logger.error(f"❌ Config file not found: {self.config_file}")
            raise FileNotFoundError(f"Configuration file required: {self.config_file}. No hardcoded fallbacks allowed.")
        
        try:
            with open(self.config_file, 'r') as f:
                config_text = f.read()
                
            # Expand environment variables
            expanded_text = EnvironmentManager.expand_env_vars(config_text)
            
            # Parse YAML
            config = yaml.safe_load(expanded_text)
            
            # Validate and process config
            config = self._process_config(config)
            
            self._config_cache = config
            logger.info(f"✅ Configuration loaded from {self.config_file}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load config from {self.config_file}: {e}")
            raise ValueError(f"Configuration file is invalid: {self.config_file}. Please fix the YAML syntax.")
    
    def get_llm_config(self, llm_type: str = 'primary') -> Dict[str, Any]:
        """Get LLM configuration for specific type
        
        Args:
            llm_type: Type of LLM (primary, tool_calling, image_processing)
            
        Returns:
            Dict with LLM configuration
        """
        config = self.load_config()
        llm_config = config.get('llm', {})
        
        import logging
        logger = logging.getLogger(__name__)
        # logger.info(f"🔍 CONFIG TRACE 1: Requested llm_type = {llm_type}")
        # logger.info(f"🔍 CONFIG TRACE 2: Full llm_config = {llm_config}")
        
        if llm_type in llm_config:
            type_config = llm_config[llm_type].copy()
            # logger.info(f"🔍 CONFIG TRACE 3: type_config for {llm_type} = {type_config}")
            
            provider_type = type_config.get('type', 'ollama')
            # logger.info(f"🔍 CONFIG TRACE 4: provider_type = {provider_type}")
            
            # Merge with provider-specific config
            providers_config = llm_config.get('providers', {})
            if provider_type in providers_config:
                provider_config = providers_config[provider_type].copy()
                # logger.info(f"🔍 CONFIG TRACE 5: provider_config = {provider_config}")
                # Type-specific config overrides provider defaults
                provider_config.update(type_config.get('config', {}))
                type_config['config'] = provider_config
                # logger.info(f"🔍 CONFIG TRACE 6: merged type_config = {type_config}")
            
            # logger.info(f"🔍 CONFIG TRACE 7: Final returned config = {type_config}")
            return type_config
        
        # No hardcoded fallback! All configuration must come from llm_config.yaml
        raise ValueError(f"LLM type '{llm_type}' not found in configuration. Please check your llm_config.yaml file.")
    
    def get_platform_config(self) -> Dict[str, Any]:
        """Get platform-specific configuration
        
        Returns:
            Dict with platform settings
        """
        config = self.load_config()
        return config.get('platform', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration
        
        Returns:
            Dict with security settings
        """
        config = self.load_config()
        return config.get('security', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration
        
        Returns:
            Dict with performance settings
        """
        config = self.load_config()
        return config.get('performance', {})
    
    def _process_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate configuration
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            Processed configuration
        """
        # Validate required sections
        if 'llm' not in config:
            config['llm'] = {}
        
        # Ensure required LLM sections exist
        llm_config = config['llm']
        if 'primary' not in llm_config:
            llm_config['primary'] = {'type': 'ollama', 'config': {}}
        if 'tool_calling' not in llm_config:
            llm_config['tool_calling'] = {'type': 'ollama', 'config': {}}
        if 'image_processing' not in llm_config:
            llm_config['image_processing'] = {'type': 'ollama', 'config': {}}
        
        return config
    
    # _get_default_config method removed - no hardcoded fallbacks allowed!
    # All configuration must come from llm_config.yaml
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file
        
        Args:
            config: Configuration dictionary to save
        """
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            # Clear cache to force reload
            self._config_cache = None
            
            logger.info(f"✅ Configuration saved to {self.config_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save config to {self.config_file}: {e}")
            raise

    def get_plugin_config(self) -> Dict[str, Any]:
        """🔌 Get plugin system configuration

        Returns:
            Dict with plugin configuration including defaults
        """
        config = self.load_config()

        # Get plugin configuration or use fallback
        plugin_config = config.get('plugins', {})

        # Ensure required structure
        if 'plugin_defaults' not in plugin_config:
            # Provide minimal fallback configuration
            logger.warning("⚠️  No plugin configuration found in llm_config.yaml, using defaults")
            plugin_config = {
                'plugin_defaults': {
                    'execution': {
                        'timeout': 60,
                        'memory_limit': 256,
                        'cpu_limit': 1.0,
                        'max_timeout': 300,
                        'max_memory_limit': 2048
                    },
                    'security': {
                        'input_validation': {
                            'max_string_length': 102400,
                            'max_array_length': 1000
                        },
                        'output_validation': {
                            'max_output_size': 10485760
                        }
                    },
                    'error_handling': {
                        'retry': {
                            'enabled': True,
                            'max_attempts': 3
                        },
                        'degraded_mode': {
                            'enabled': True,
                            'disable_after_failures': 5
                        }
                    }
                },
                'python_executable': 'python3'
            }

        return plugin_config

# Global config loader instance
config_loader = ConfigLoader()