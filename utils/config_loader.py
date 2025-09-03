"""
Configuration loader for LLM providers and cross-platform settings
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from .platform import platform_paths, EnvironmentManager

# Import constants to avoid hardcoded values
import sys
config_dir = Path(__file__).parent.parent / "config"
sys.path.insert(0, str(config_dir))
from llm_constants import (
    DEFAULT_PRIMARY_TIMEOUT, DEFAULT_SECONDARY_TIMEOUT,
    DEFAULT_PRIMARY_TEMPERATURE, DEFAULT_SECONDARY_TEMPERATURE,
    DEFAULT_CONTEXT_WINDOW_SIZE, DEFAULT_IMAGE_PROCESSING_MAX_TOKENS,
    OLLAMA_DEFAULT_BASE_URL, DEFAULT_IMAGE_PROCESSING_MODEL,
    DEFAULT_TOOL_CALLING_MODEL, DEFAULT_PRIMARY_MODEL
)

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
            logger.warning(f"⚠️ Config file not found: {self.config_file}")
            return self._get_default_config()
        
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
            logger.info("📋 Using default configuration")
            return self._get_default_config()
    
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
        
        # Fallback to default Ollama config
        return {
            'type': 'ollama',
            'config': {
                'base_url': OLLAMA_DEFAULT_BASE_URL,
                'model': DEFAULT_PRIMARY_MODEL,
                'timeout': DEFAULT_SECONDARY_TIMEOUT
            }
        }
    
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
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when no config file exists
        
        Returns:
            Default configuration dictionary
        """
        return {
            'llm': {
                'primary': {
                    'type': 'ollama',
                    'config': {
                        'base_url': OLLAMA_DEFAULT_BASE_URL,
                        'model': DEFAULT_PRIMARY_MODEL,
                        'timeout': DEFAULT_PRIMARY_TIMEOUT,
                        'temperature': DEFAULT_PRIMARY_TEMPERATURE,
                        'stream': True
                    }
                },
                'tool_calling': {
                    'type': 'ollama',
                    'config': {
                        'base_url': OLLAMA_DEFAULT_BASE_URL,
                        'model': DEFAULT_TOOL_CALLING_MODEL,
                        'timeout': DEFAULT_SECONDARY_TIMEOUT,
                        'temperature': DEFAULT_SECONDARY_TEMPERATURE,
                        'stream': False
                    }
                },
                'image_processing': {
                    'type': 'ollama',
                    'config': {
                        'base_url': OLLAMA_DEFAULT_BASE_URL,
                        'model': DEFAULT_IMAGE_PROCESSING_MODEL,
                        'timeout': DEFAULT_SECONDARY_TIMEOUT,
                        'temperature': DEFAULT_SECONDARY_TEMPERATURE,
                        'stream': False,
                        'context_window_size': DEFAULT_CONTEXT_WINDOW_SIZE,
                        'max_tokens': DEFAULT_IMAGE_PROCESSING_MAX_TOKENS
                    }
                },
                'fallback': {
                    'enabled': False,
                    'order': ['ollama']
                }
            },
            'platform': {
                'temp_dir': str(platform_paths.get_temp_dir()),
                'config_dir': str(platform_paths.get_config_dir()),
                'log_dir': str(platform_paths.get_log_dir())
            },
            'security': {
                'api_key_encryption': False,
                'audit_logging': True
            },
            'performance': {
                'connection_pool_size': 10,
                'request_timeout': 600,
                'max_concurrent_requests': 5
            }
        }
    
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

# Global config loader instance
config_loader = ConfigLoader()