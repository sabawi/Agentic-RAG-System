"""
LLM Manager - Coordinates provider instances and requests
"""

import asyncio
import logging
from typing import AsyncIterator, List, Dict, Any, Optional, Tuple
from .base import LLMProvider
from .factory import LLMProviderFactory
from utils.config_loader import config_loader

logger = logging.getLogger(__name__)

class LLMManager:
    """Manages LLM providers and coordinates requests"""
    
    def __init__(self):
        """Initialize LLM manager"""
        self.primary_provider: Optional[LLMProvider] = None
        self.tool_calling_provider: Optional[LLMProvider] = None
        self.arbitrator_provider: Optional[LLMProvider] = None
        self.config = None
        self._initialized = False
        logger.info("🎛️ LLM Manager initialized")
    
    async def initialize(self):
        """Initialize providers from configuration"""
        if self._initialized:
            return
        
        try:
            self.config = config_loader.load_config()
            
            # Initialize primary LLM provider
            primary_config = config_loader.get_llm_config('primary')
            self.primary_provider = await self._create_provider(
                'primary', 
                primary_config
            )
            
            # Initialize tool calling LLM provider
            tool_config = config_loader.get_llm_config('tool_calling')
            self.tool_calling_provider = await self._create_provider(
                'tool_calling',
                tool_config
            )
            
            # Initialize arbitrator LLM provider if enabled
            arbitrator_config = self.config.get('arbitrator', {})
            if arbitrator_config.get('enabled', False):
                logger.info("🧠 Arbitrator enabled - initializing arbitrator provider")
                self.arbitrator_provider = await self._create_provider(
                    'arbitrator',
                    arbitrator_config
                )
            else:
                logger.info("🧠 Arbitrator disabled - skipping arbitrator provider")
            
            self._initialized = True
            logger.info("✅ LLM Manager initialization complete")
            
        except Exception as e:
            logger.error(f"❌ LLM Manager initialization failed: {e}")
            raise
    
    async def _create_provider(self, provider_name: str, config: Dict[str, Any]) -> LLMProvider:
        """Create and validate a provider instance
        
        Args:
            provider_name: Name for logging (primary, tool_calling)
            config: Provider configuration
            
        Returns:
            Initialized and validated provider
        """
        provider_type = config.get('type', 'ollama')
        provider_config = config.get('config', {})
        
        logger.info(f"🏗️ Creating {provider_name} provider: {provider_type}")
        
        try:
            provider = LLMProviderFactory.create_provider(provider_type, provider_config)
            
            # Health check
            is_healthy = await provider.health_check()
            if not is_healthy:
                logger.warning(f"⚠️ Health check failed for {provider_name} provider")
                # In production, might want to try fallback providers here
            
            logger.info(f"✅ {provider_name} provider ready: {provider.get_provider_info()['name']}")
            return provider
            
        except Exception as e:
            logger.error(f"❌ Failed to create {provider_name} provider: {e}")
            raise
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Generate streaming response using primary LLM
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Yields:
            str: Response chunks
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.primary_provider:
            raise Exception("Primary LLM provider not available")
        
        model = kwargs.get('model') or self.primary_provider.get_model()
        
        logger.info(f"📡 Streaming request to primary LLM: {model}")
        
        # Remove model from kwargs to avoid duplicate parameter conflict
        kwargs_clean = {k: v for k, v in kwargs.items() if k != 'model'}
        
        try:
            async for chunk in self.primary_provider.generate_stream(prompt, model, **kwargs_clean):
                yield chunk
        except Exception as e:
            logger.error(f"❌ Primary LLM streaming failed: {e}")
            # Try fallback if configured
            if await self._should_try_fallback('primary'):
                logger.info("🔄 Attempting fallback for primary LLM")
                # Fallback logic would go here
            raise
    
    async def generate_tools(self, prompt: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """Generate tool calls using tool calling LLM
        
        Args:
            prompt: Input prompt
            tools: List of tool definitions
            **kwargs: Additional parameters
            
        Returns:
            Dict with tool calls and response
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.tool_calling_provider:
            raise Exception("Tool calling LLM provider not available")
        
        model_from_kwargs = kwargs.get('model')
        model_from_provider = self.tool_calling_provider.get_model('tool_calling')
        
        # For OpenAI provider, always use configured model to prevent sending wrong model
        provider_type = getattr(self.tool_calling_provider, 'config', {}).get('type', 'unknown')
        if hasattr(self.tool_calling_provider, 'get_provider_info'):
            provider_info = self.tool_calling_provider.get_provider_info()
            provider_type = provider_info.get('type', provider_type)
            
        if provider_type == 'openai':
            model = model_from_provider  # Force OpenAI to use configured model
            # logger.info(f"🔍 MANAGER TRACE 2.5: OpenAI provider detected - forcing configured model")
        else:
            model = model_from_kwargs or model_from_provider
        
        # logger.info(f"🔍 MANAGER TRACE 1: model from kwargs = {model_from_kwargs}")
        # logger.info(f"🔍 MANAGER TRACE 2: model from provider = {model_from_provider}")
        # logger.info(f"🔍 MANAGER TRACE 3: Final model selected = {model}")
        logger.info(f"🔧 Tool calling request: {model}, tools={len(tools)}")
        
        # Remove model from kwargs to avoid duplicate parameter conflict
        kwargs_clean = {k: v for k, v in kwargs.items() if k != 'model'}
        # logger.info(f"🔍 MANAGER TRACE 4: Cleaned kwargs = {kwargs_clean}")
        
        # CRITICAL DEBUGGING: Check if system_prompt is being passed
        logger.info(f"🚨 MANAGER DEBUG: kwargs_clean keys = {list(kwargs_clean.keys())}")
        system_prompt_in_kwargs = kwargs_clean.get('system_prompt', '')
        logger.info(f"🚨 MANAGER DEBUG: system_prompt length = {len(system_prompt_in_kwargs)} chars")
        if system_prompt_in_kwargs:
            logger.info(f"🚨 MANAGER DEBUG: system_prompt preview = {system_prompt_in_kwargs[:100]}...")
        else:
            logger.info(f"🚨 MANAGER DEBUG: NO system_prompt in kwargs - CRITICAL!")
        
        try:
            result = await self.tool_calling_provider.generate_tools(prompt, model, tools, **kwargs_clean)
            
            # Log tool calls for debugging
            tool_calls = result.get('tool_calls', [])
            if tool_calls:
                tool_names = [tc.get('function', {}).get('name') for tc in tool_calls]
                logger.info(f"🎯 Generated tool calls: {tool_names}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Tool calling LLM failed: {e}")
            # Try fallback if configured
            if await self._should_try_fallback('tool_calling'):
                logger.info("🔄 Attempting fallback for tool calling LLM")
                # Fallback logic would go here
            raise
    
    async def call_arbitrator(self, prompt: str, system_prompt: str, **kwargs) -> str:
        """Call arbitrator LLM for task validation
        
        Args:
            prompt: Task validation request (JSON format)
            system_prompt: Arbitrator system prompt
            **kwargs: Additional parameters
            
        Returns:
            str: Arbitrator response (JSON format)
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.arbitrator_provider:
            raise Exception("Arbitrator LLM provider not available - ensure arbitrator is enabled in configuration")
        
        try:
            logger.info("🧠 Calling arbitrator LLM for task validation")
            
            # Prepare arbitrator-specific parameters
            arbitrator_kwargs = {
                'system_prompt': system_prompt,
                'temperature': 0.1,  # Low temperature for consistent decisions
                'max_tokens': 1024,  # Compact JSON responses
                'stream': False,     # Structured output doesn't need streaming
                **kwargs
            }
            
            # Call arbitrator provider using streaming interface and collect full response
            response_chunks = []
            async for chunk in self.arbitrator_provider.generate_stream(
                prompt,
                self.arbitrator_provider.get_model(),
                **arbitrator_kwargs
            ):
                response_chunks.append(chunk)
            
            result = "".join(response_chunks)
            
            logger.info(f"✅ Arbitrator LLM response received: {len(result)} chars")
            return result
            
        except Exception as e:
            logger.error(f"❌ Arbitrator LLM failed: {e}")
            # For arbitrator failures, we should fail fast rather than fallback
            # This ensures system integrity and prevents silent failures
            raise Exception(f"Arbitrator LLM call failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers
        
        Returns:
            Dict with health status of each provider
        """
        if not self._initialized:
            await self.initialize()
        
        results = {}
        
        if self.primary_provider:
            try:
                results['primary'] = await self.primary_provider.health_check()
            except Exception as e:
                logger.error(f"❌ Primary provider health check failed: {e}")
                results['primary'] = False
        
        if self.tool_calling_provider:
            try:
                results['tool_calling'] = await self.tool_calling_provider.health_check()
            except Exception as e:
                logger.error(f"❌ Tool calling provider health check failed: {e}")
                results['tool_calling'] = False
        
        if self.arbitrator_provider:
            try:
                results['arbitrator'] = await self.arbitrator_provider.health_check()
            except Exception as e:
                logger.error(f"❌ Arbitrator provider health check failed: {e}")
                results['arbitrator'] = False
        
        return results
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about configured providers
        
        Returns:
            Dict with provider information
        """
        info = {
            'initialized': self._initialized,
            'providers': {},
            'factory_info': LLMProviderFactory.get_provider_info()
        }
        
        if self.primary_provider:
            info['providers']['primary'] = self.primary_provider.get_provider_info()
        
        if self.tool_calling_provider:
            info['providers']['tool_calling'] = self.tool_calling_provider.get_provider_info()
        
        return info
    
    async def _should_try_fallback(self, provider_type: str) -> bool:
        """Check if fallback should be attempted
        
        Args:
            provider_type: Type of provider (primary, tool_calling)
            
        Returns:
            bool: True if fallback should be attempted
        """
        if not self.config:
            return False
        
        fallback_config = self.config.get('llm', {}).get('fallback', {})
        return fallback_config.get('enabled', False)
    
    async def shutdown(self):
        """Shutdown all providers and cleanup resources"""
        logger.info("🛑 Shutting down LLM Manager")
        
        if self.primary_provider:
            try:
                await self.primary_provider.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"❌ Error shutting down primary provider: {e}")
        
        if self.tool_calling_provider:
            try:
                await self.tool_calling_provider.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"❌ Error shutting down tool calling provider: {e}")
        
        self._initialized = False
        logger.info("✅ LLM Manager shutdown complete")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()

# Global LLM manager instance
llm_manager = LLMManager()