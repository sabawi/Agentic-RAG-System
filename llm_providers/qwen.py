"""
Qwen Provider Implementation

Handles Qwen API interactions for both streaming and tool calling.
"""

import asyncio
import aiohttp
import json
import logging
from typing import AsyncIterator, List, Dict, Any, Optional
from .base import LLMProvider

logger = logging.getLogger(__name__)

class QwenProvider(LLMProvider):
    """Qwen provider for Qwen cloud models"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Qwen provider
        
        Args:
            config: Configuration dictionary with api_key, base_url, model, etc.
        """
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://dashscope.aliyuncs.com/api/v1')
        self.session = None
        
        if not self.api_key:
            raise ValueError("Qwen API key is required")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with auth headers"""
        if self.session is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
                
            timeout = aiohttp.ClientTimeout(total=self.get_timeout())
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def generate_stream(self, prompt: str, model: str, **kwargs) -> AsyncIterator[str]:
        """Generate streaming response from Qwen
        
        Args:
            prompt: Input prompt
            model: Model name (qwen-plus, qwen-max, etc.)
            **kwargs: Additional parameters
            
        Yields:
            str: Response chunks
        """
        session = await self._get_session()
        
        payload = {
            "model": model,
            "input": {
                "messages": [{"role": "user", "content": prompt}]
            },
            "parameters": {
                "result_format": "message",
                "incremental_output": True,
                "temperature": kwargs.get('temperature', self.get_temperature()),
                "max_tokens": kwargs.get('max_tokens', self.get_max_tokens())
            }
        }
        
        logger.info(f"🔮 Qwen streaming request: model={model}, prompt_len={len(prompt)}")
        
        try:
            async with session.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Qwen API error {response.status}: {error_text}")
                    raise Exception(f"Qwen API error: {response.status} - {error_text}")
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            output = data.get('output', {})
                            choices = output.get('choices', [])
                            if choices:
                                message = choices[0].get('message', {})
                                content = message.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue  # Skip invalid JSON
                            
        except asyncio.TimeoutError:
            logger.error("⏰ Qwen request timeout")
            raise Exception("Qwen request timed out")
        except Exception as e:
            logger.error(f"❌ Qwen streaming error: {e}")
            raise
    
    async def generate_tools(self, prompt: str, model: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """Generate tool calls from Qwen
        
        Args:
            prompt: Input prompt
            model: Model name
            tools: List of tool definitions
            **kwargs: Additional parameters
            
        Returns:
            Dict with tool calls and/or response text
        """
        session = await self._get_session()
        
        # Format tools for Qwen API
        formatted_tools = []
        for tool in tools:
            formatted_tools.append({
                "type": "function",
                "function": tool
            })
        
        payload = {
            "model": model,
            "input": {
                "messages": [{"role": "user", "content": prompt}],
                "tools": formatted_tools
            },
            "parameters": {
                "result_format": "message",
                "temperature": kwargs.get('temperature', 0.1),
                "max_tokens": kwargs.get('max_tokens', 2048)
            }
        }
        
        logger.info(f"🔧 Qwen tool request: model={model}, tools={len(tools)}")
        
        try:
            async with session.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Qwen tool API error {response.status}: {error_text}")
                    raise Exception(f"Qwen tool API error: {response.status} - {error_text}")
                
                response_data = await response.json()
                
                # Extract tool calls and content from Qwen response
                output = response_data.get('output', {})
                choices = output.get('choices', [])
                if not choices:
                    raise Exception("No choices in Qwen response")
                
                message = choices[0].get('message', {})
                tool_calls = message.get('tool_calls', [])
                content = message.get('content', '')
                
                # Convert Qwen format to our standard format
                formatted_tool_calls = []
                for tool_call in tool_calls:
                    function = tool_call.get('function', {})
                    formatted_tool_calls.append({
                        'id': tool_call.get('id'),
                        'type': 'function',
                        'function': {
                            'name': function.get('name'),
                            'arguments': function.get('arguments')
                        }
                    })
                
                usage = response_data.get('usage', {})
                
                return {
                    'tool_calls': formatted_tool_calls,
                    'content': content,
                    'usage': usage,
                    'model': model
                }
                
        except asyncio.TimeoutError:
            logger.error("⏰ Qwen tool request timeout")
            raise Exception("Qwen tool request timed out")
        except Exception as e:
            logger.error(f"❌ Qwen tool calling error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Qwen API health
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            session = await self._get_session()
            # Qwen doesn't have a dedicated health endpoint, so we make a minimal request
            test_payload = {
                "model": self.config.get('model', 'qwen-plus'),
                "input": {
                    "messages": [{"role": "user", "content": "test"}]
                },
                "parameters": {
                    "max_tokens": 1
                }
            }
            async with session.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=test_payload
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"❌ Qwen health check failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available Qwen models
        
        Returns:
            List[str]: Available model names
        """
        # Common Qwen models
        return [
            "qwen-plus",
            "qwen-max",
            "qwen-max-longcontext",
            "qwen-turbo"
        ]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get Qwen provider information
        
        Returns:
            Dict with provider metadata
        """
        return {
            'name': 'Qwen',
            'type': 'qwen',
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