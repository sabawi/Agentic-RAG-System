#!/usr/bin/env python3
"""
LLM Configuration Constants
Centralized constants for LLM configuration to avoid hardcoded values
"""

# Default timeout values (seconds)
DEFAULT_PRIMARY_TIMEOUT = 600
DEFAULT_SECONDARY_TIMEOUT = 300

# Default temperature values
DEFAULT_PRIMARY_TEMPERATURE = 0.7
DEFAULT_SECONDARY_TEMPERATURE = 0.1

# Default token limits
DEFAULT_CONTEXT_WINDOW_SIZE = 8192
DEFAULT_PRIMARY_MAX_TOKENS = 8192
DEFAULT_SECONDARY_MAX_TOKENS = 4096
DEFAULT_IMAGE_PROCESSING_MAX_TOKENS = 2048

# Ollama configuration
OLLAMA_DEFAULT_BASE_URL = 'http://127.0.0.1:11434'
OLLAMA_HEALTH_CHECK_URL = 'http://127.0.0.1:11434/api/tags'
OLLAMA_DEFAULT_NUM_PREDICT_PRIMARY = 16384
OLLAMA_DEFAULT_NUM_PREDICT_SECONDARY = 4096

# Provider API endpoints
OPENAI_BASE_URL = 'https://api.openai.com/v1'
QWEN_BASE_URL = 'https://dashscope.aliyuncs.com/api/v1'
GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'

# Default models
DEFAULT_PRIMARY_MODEL = 'llama3.2:3b'
DEFAULT_TOOL_CALLING_MODEL = 'qwen3:8b'
DEFAULT_IMAGE_PROCESSING_MODEL = 'llava:7b'

# Vision models
VISION_MODELS_OLLAMA = {
    'llava:7b': 'LLaVA 7B (Vision)',
    'llava:13b': 'LLaVA 13B (Vision)', 
    'bakllava': 'BakLLaVA (Vision)',
    'moondream': 'Moondream (Vision)'
}

VISION_MODELS_OPENAI = {
    'gpt-4-vision-preview': 'GPT-4 Vision (Image Analysis)'
}

# Environment variable names
# Environment variable references (not actual credentials)
ENV_VAR_OPENAI = '${OPENAI_API_KEY}'
ENV_VAR_QWEN = '${QWEN_API_KEY}' 
ENV_VAR_GOOGLE = '${GOOGLE_API_KEY}'

# Retry configuration
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 2
DEFAULT_OPENAI_RETRY_DELAY = 1

# Performance defaults
DEFAULT_CONNECTION_POOL_SIZE = 10
DEFAULT_MAX_CONCURRENT_REQUESTS = 5
DEFAULT_REQUEST_TIMEOUT = 600
DEFAULT_STREAMING_CHUNK_SIZE = 1024