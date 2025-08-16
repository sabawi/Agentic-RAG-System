"""
Abstract base class for LLM providers
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.name = self.__class__.__name__
        logger.info(f"🤖 Initializing {self.name} with config: {self._safe_config()}")
    
    def _safe_config(self) -> Dict[str, Any]:
        """Return config with sensitive data masked"""
        safe_config = self.config.copy()
        # Mask API keys and sensitive data
        for key in ['api_key', 'secret', 'token', 'password']:
            if key in safe_config and safe_config[key]:
                safe_config[key] = "***MASKED***"
        return safe_config
    
    @abstractmethod
    async def generate_stream(self, prompt: str, model: str, **kwargs) -> AsyncIterator[str]:
        """Generate streaming response from LLM
        
        Args:
            prompt: Input prompt for the model
            model: Model name to use
            **kwargs: Additional provider-specific parameters
            
        Yields:
            str: Streaming response chunks
        """
        pass
    
    @abstractmethod
    async def generate_tools(self, prompt: str, model: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """Generate tool calls from LLM
        
        Args:
            prompt: Input prompt for the model
            model: Model name to use  
            tools: List of available tool definitions
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dict containing tool calls and/or text response
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and accessible
        
        Returns:
            bool: True if provider is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider
        
        Returns:
            List[str]: Available model names
        """
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and capabilities
        
        Returns:
            Dict containing provider metadata
        """
        pass
    
    def get_base_url(self) -> Optional[str]:
        """Get provider base URL"""
        return self.config.get('base_url')
    
    def get_model(self, model_type: str = 'default') -> str:
        """Get model name for specific use case
        
        Args:
            model_type: Type of model (default, tool_calling, etc.)
            
        Returns:
            str: Model name
        """
        if model_type == 'tool_calling' and 'tool_calling_model' in self.config:
            return self.config['tool_calling_model']
        return self.config.get('model', 'default')
    
    def get_timeout(self) -> int:
        """Get request timeout in seconds"""
        return self.config.get('timeout', 300)
    
    def get_max_tokens(self) -> int:
        """Get maximum tokens setting"""
        return self.config.get('max_tokens', 4096)
    
    def get_temperature(self) -> float:
        """Get temperature setting"""
        return self.config.get('temperature', 0.7)
    
    def supports_streaming(self) -> bool:
        """Check if provider supports streaming"""
        return True  # Most providers support streaming
    
    def supports_function_calling(self) -> bool:
        """Check if provider supports function calling"""
        return True  # Most modern providers support function calling
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass