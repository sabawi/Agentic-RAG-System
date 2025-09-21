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
        # Initialize state variables for thinking/response formatting
        self._thinking_started = False
        self._response_started = False

        session = await self._get_session()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": kwargs.get('think', self.config.get('think', False)),
            "options": {
                "temperature": kwargs.get('temperature', self.get_temperature()),
                "num_ctx": kwargs.get('context_window_size', self.get_context_window_size()),
                "num_predict": kwargs.get('num_predict', self.get_num_predict())
            }
        }
        
        think_enabled = payload.get('think', False)
        think_status = "🧠 THINK ON" if think_enabled else "⚡ THINK OFF"
        logger.info(f"🦙 Ollama streaming request: model={model}, prompt_len={len(prompt)}, num_ctx={payload['options']['num_ctx']}, num_predict={payload['options']['num_predict']}, {think_status}")

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

                            # Yield content with proper Open-WebUI thinking tags
                            if 'thinking' in data and data['thinking']:
                                # Wrap thinking content in Open-WebUI compatible <think> tags
                                thinking_content = data['thinking']
                                if hasattr(self, '_thinking_started') and not self._thinking_started:
                                    yield '<think>\n'
                                    self._thinking_started = True
                                yield thinking_content

                            if 'response' in data and data['response']:
                                # Close thinking section if it was open
                                if hasattr(self, '_thinking_started') and self._thinking_started:
                                    yield '\n</think>\n\n'
                                    self._thinking_started = False
                                    self._response_started = True
                                # Yield response content exactly as received (preserve all whitespace)
                                response_content = data['response']
                                yield response_content

                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Invalid JSON from Ollama: {line}")
                            continue

                # Close thinking section if still open at the end
                if hasattr(self, '_thinking_started') and self._thinking_started:
                    yield '\n</think>\n\n'

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
        
        # Build messages array with system prompt if available
        messages = []
        system_prompt = kwargs.get('system_prompt')
        if system_prompt:
            # OLLAMA FIX: Modify system prompt to be more flexible with tool calling
            # Based on research: Ollama forces function calls, but we need to allow natural responses
            ollama_enhanced_prompt = system_prompt + """

CRITICAL OLLAMA TOOL CALLING INSTRUCTIONS:
- You MUST provide valid function names when calling tools
- The 'name' field cannot be empty or blank
- For document searches, use function name: "document_search"
- For web searches, use function name: "search_web"
- For published papers, use function name: "published_papers_search"

EXAMPLE CORRECT TOOL CALL:
{
  "name": "document_search",
  "arguments": {"q": "machine learning", "scope": "documents"}
}

EXAMPLE WRONG TOOL CALL (NEVER DO THIS):
{
  "name": "",
  "arguments": {"q": "machine learning", "scope": "documents"}
}

Remember: Always include a valid function name that matches available tools exactly.
"""
            messages.append({"role": "system", "content": ollama_enhanced_prompt})
            logger.info(f"🔧 OLLAMA TOOL CALLING: Added enhanced system prompt ({len(ollama_enhanced_prompt)} chars)")
        else:
            logger.warning(f"🚨 OLLAMA TOOL CALLING: NO system prompt provided - this could cause poor tool calling!")
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "tools": formatted_tools,
            "stream": False,
            "think": kwargs.get('think', self.config.get('think', False)),
            "options": {
                "temperature": kwargs.get('temperature', 0.1),  # Lower for tool calling
                "num_ctx": kwargs.get('context_window_size', self.get_context_window_size()),
                "num_predict": kwargs.get('num_predict', self.get_num_predict())
            }
        }
        
        think_enabled = payload.get('think', False)
        think_status = "🧠 THINK ON" if think_enabled else "⚡ THINK OFF"
        logger.info(f"🔧 Ollama tool request: model={model}, tools={len(tools)}, num_ctx={payload['options']['num_ctx']}, num_predict={payload['options']['num_predict']}, {think_status}")
        
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

                # DEBUG: Log the raw response to see what we're getting
                logger.info(f"🔍 OLLAMA RAW RESPONSE: {response_data}")
                logger.info(f"🔍 OLLAMA MESSAGE: {message}")
                logger.info(f"🔍 OLLAMA TOOL CALLS: {tool_calls}")

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