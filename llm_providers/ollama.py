"""
Ollama Provider Implementation

Handles local Ollama model interactions for both streaming and tool calling.
"""

import asyncio
import aiohttp
import json
import logging
from typing import AsyncIterator, List, Dict, Any, Optional
from .base import LLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    """Ollama provider for local model inference"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Ollama provider
        
        Args:
            config: Configuration dictionary with base_url, model, etc.
        """
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://127.0.0.1:11434')
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.get_timeout())
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def generate_stream(self, prompt: str, model: str, **kwargs) -> AsyncIterator[str]:
        """Generate streaming response from Ollama
        
        Args:
            prompt: Input prompt
            model: Model name
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Yields:
            str: Response chunks
        """
        session = await self._get_session()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": kwargs.get('temperature', self.get_temperature()),
                "num_ctx": kwargs.get('context_window_size', self.get_context_window_size()),
                "num_predict": kwargs.get('num_predict', self.get_num_predict())
            }
        }
        
        logger.info(f"🦙 Ollama streaming request: model={model}, prompt_len={len(prompt)}, num_ctx={payload['options']['num_ctx']}, num_predict={payload['options']['num_predict']}")
        
        try:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Ollama API error {response.status}: {error_text}")
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
                
                async for line in response.content:
                    if line.strip():
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                yield data['response']
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Invalid JSON from Ollama: {line}")
                            continue
                            
        except asyncio.TimeoutError:
            logger.error("⏰ Ollama request timeout")
            raise Exception("Ollama request timed out")
        except Exception as e:
            logger.error(f"❌ Ollama streaming error: {e}")
            raise
    
    async def generate_tools(self, prompt: str, model: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """Generate tool calls from Ollama
        
        Args:
            prompt: Input prompt
            model: Model name
            tools: List of tool definitions
            **kwargs: Additional parameters
            
        Returns:
            Dict with tool calls and/or response text
        """
        session = await self._get_session()
        
        # Format tools for Ollama
        formatted_tools = []
        for tool in tools:
            formatted_tools.append({
                "type": "function",
                "function": tool
            })
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "tools": formatted_tools,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', 0.1),  # Lower for tool calling
                "num_ctx": kwargs.get('context_window_size', self.get_context_window_size()),
                "num_predict": kwargs.get('num_predict', self.get_num_predict())
            }
        }
        
        logger.info(f"🔧 Ollama tool request: model={model}, tools={len(tools)}, num_ctx={payload['options']['num_ctx']}, num_predict={payload['options']['num_predict']}")
        
        try:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Ollama tool API error {response.status}: {error_text}")
                    raise Exception(f"Ollama tool API error: {response.status} - {error_text}")
                
                response_data = await response.json()
                
                # Extract tool calls and content
                message = response_data.get('message', {})
                tool_calls = message.get('tool_calls', [])
                content = message.get('content', '')
                
                return {
                    'tool_calls': tool_calls,
                    'content': content,
                    'usage': response_data.get('usage', {}),
                    'model': model
                }
                
        except asyncio.TimeoutError:
            logger.error("⏰ Ollama tool request timeout")
            raise Exception("Ollama tool request timed out")
        except Exception as e:
            logger.error(f"❌ Ollama tool calling error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Ollama health
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"❌ Ollama health check failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available Ollama models
        
        Returns:
            List[str]: Available model names
        """
        # This would typically make an async call to /api/tags
        # For now, return configured model as fallback
        configured_model = self.config.get('model')
        if configured_model:
            return [configured_model]
        return []
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get Ollama provider information
        
        Returns:
            Dict with provider metadata
        """
        return {
            'name': 'Ollama',
            'type': 'ollama',
            'base_url': self.base_url,
            'configured_model': self.config.get('model'),
            'supports_streaming': True,
            'supports_function_calling': True,
            'timeout': self.get_timeout(),
            'max_tokens': self.get_max_tokens(),
            'temperature': self.get_temperature()
        }
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up session on exit"""
        if self.session:
            await self.session.close()
            self.session = None