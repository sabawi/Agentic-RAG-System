"""
LLM Provider Factory for creating and managing provider instances
"""

import logging
from typing import Dict, Any, Optional
from .base import LLMProvider

logger = logging.getLogger(__name__)

class LLMProviderFactory:
    """Factory class for creating LLM provider instances"""
    
    _providers = {}  # Registry of available providers
    
    @classmethod
    def register_provider(cls, provider_type: str, provider_class):
        """Register a new provider type
        
        Args:
            provider_type: String identifier for the provider
            provider_class: Provider class that inherits from LLMProvider
        """
        cls._providers[provider_type] = provider_class
        logger.info(f"🔧 Registered provider: {provider_type}")
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> LLMProvider:
        """Create a provider instance
        
        Args:
            provider_type: Type of provider to create (ollama, openai, qwen)
            config: Configuration dictionary for the provider
            
        Returns:
            LLMProvider: Configured provider instance
            
        Raises:
            ValueError: If provider_type is not supported
        """
        if provider_type not in cls._providers:
            # Try to import provider dynamically
            cls._import_provider(provider_type)
        
        if provider_type not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(f"Unsupported provider type: {provider_type}. Available: {available}")
        
        provider_class = cls._providers[provider_type]
        logger.info(f"🏭 Creating {provider_type} provider instance")
        
        try:
            return provider_class(config)
        except Exception as e:
            logger.error(f"❌ Failed to create {provider_type} provider: {e}")
            raise
    
    @classmethod
    def _import_provider(cls, provider_type: str):
        """Dynamically import a provider module

        Args:
            provider_type: Provider type to import
        """
        try:
            if provider_type == 'ollama':
                from .ollama import OllamaProvider
                cls.register_provider('ollama', OllamaProvider)
            elif provider_type == 'openai':
                from .openai import OpenAIProvider
                cls.register_provider('openai', OpenAIProvider)
            elif provider_type == 'openrouter':
                # OpenRouter uses OpenAI-compatible API
                from .openai import OpenAIProvider
                cls.register_provider('openrouter', OpenAIProvider)
            elif provider_type == 'qwen':
                from .qwen import QwenProvider
                cls.register_provider('qwen', QwenProvider)
            else:
                logger.warning(f"⚠️ Unknown provider type for import: {provider_type}")
        except ImportError as e:
            logger.error(f"❌ Failed to import {provider_type} provider: {e}")
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider types
        
        Returns:
            List of available provider type strings
        """
        # Try to import all known providers
        for provider_type in ['ollama', 'openai', 'openrouter', 'qwen']:
            if provider_type not in cls._providers:
                cls._import_provider(provider_type)

        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_info(cls) -> Dict[str, Any]:
        """Get information about all available providers
        
        Returns:
            Dict with provider information
        """
        available = cls.get_available_providers()
        return {
            'available_providers': available,
            'total_count': len(available),
            'factory_version': '0.9.0'
        }

# Auto-register known providers on module import
def _auto_register_providers():
    """Automatically register known providers"""
    factory = LLMProviderFactory()
    
    # Register providers that are available
    for provider_type in ['ollama', 'openai', 'openrouter', 'qwen']:
        try:
            factory._import_provider(provider_type)
        except Exception as e:
            logger.debug(f"Provider {provider_type} not available: {e}")

# Auto-register on import
_auto_register_providers()