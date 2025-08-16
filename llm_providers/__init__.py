"""
LLM Provider Abstraction Layer v0.9.0

Provides unified interface for multiple LLM providers:
- Ollama (local models)
- OpenAI (GPT-4+, cloud)
- Qwen (cloud API)

Supports both streaming and function calling across all providers.
"""

from .base import LLMProvider
from .factory import LLMProviderFactory
from .ollama import OllamaProvider

__all__ = [
    'LLMProvider',
    'LLMProviderFactory', 
    'OllamaProvider'
]

__version__ = "0.9.0"