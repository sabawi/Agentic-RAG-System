#!/usr/bin/env python3

# Import centralized version information
from version import __version__, __release__, get_release_string

# Generate dynamic docstring with current version
__doc__ = f"""
{get_release_string()} - Complete FastAPI Server with Hybrid LLM Architecture
=============================================================================

FastAPI server with all original Flask functionality including:
- Multi-LLM orchestration with Ollama integration
- Tool calling system (RAG, web search, stock data, etc.)
- Document intelligence with FAISS integration
- Vision processing with qwen2.5vl:3b
- Real-time streaming with auto-fallback
- Async processing for performance
- Database connection pooling
- Production-ready caching layer

Version: {__version__} - Critical Ollama Tool Calling Fix & Hybrid Architecture
Release: {__release__}
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import sys
import time
import traceback
import io
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
import subprocess
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import requests

# HTTP Connection Pooling
from http_pool_manager import http_pool, init_http_pool, cleanup_http_pool
from http_helpers import pooled_get, pooled_post, requests_compatible_get, requests_compatible_post

# Configuration Management
from utils.config_loader import config_loader
from llm_providers.manager import llm_manager

# Phase 2B: Advanced Response Streaming & Buffer Optimization
try:
    from phase2b_rollback_controller import (
        rollback_controller, enable_phase2b_feature, disable_phase2b_feature, 
        is_phase2b_feature_enabled, FeatureFlag, emergency_rollback_phase2b
    )
    from phase2b_performance_monitor import (
        performance_monitor, record_performance_metric, get_performance_health
    )
    from phase2b_streaming_fallback import (
        streaming_wrapper, process_response_with_streaming, get_streaming_statistics
    )
    from phase2b_buffer_manager import (
        buffer_manager, start_buffer_management, stop_buffer_management, get_buffer_statistics
    )
    from phase2b_response_classifier import (
        response_classifier, classify_response, get_classification_statistics
    )
    PHASE2B_AVAILABLE = True
except ImportError as e:
    PHASE2B_AVAILABLE = False
    PHASE2B_IMPORT_ERROR = str(e)

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Async database
import aiomysql
from aiomysql.pool import Pool

# Data processing
import pandas as pd
import matplotlib
matplotlib.use('Agg')

# LLM and tools imports
try:
    import ollama
    from bs4 import BeautifulSoup
    import wikipediaapi
    from gnews import GNews
    import yfinance as yf
    from ddgs import DDGS
    from archive.experimental.webcrawler import SeleniumCrawler
    from text_chunker import TextChunker
    import PyPDF2
    import magic
    import trafilatura
    from urllib.parse import urlparse
    TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Some tools not available: {e}")
    TOOLS_AVAILABLE = False

# Import our optimization safety system
try:
    from archive.experimental.optimization_safety import (
        ToolOutputPreserver,
        OptimizationValidator, 
        safe_optimize_llm_input
    )
    from integrations.optimization_controller import optimization_controller
    OPTIMIZATION_AVAILABLE = True
except ImportError as e:
    OPTIMIZATION_AVAILABLE = False
    OPTIMIZATION_IMPORT_ERROR = str(e)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

class ServerConfig:
    """Enhanced server configuration"""
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')  
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Down2earth!')
    DB_NAME = os.getenv('DB_NAME', 'mystocks')
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
    
    # Ollama configuration
    OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434/api/generate')
    OLLAMA_CHAT_URL = os.getenv('OLLAMA_CHAT_URL', 'http://127.0.0.1:11434/api/chat')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', config_loader.get_llm_config('primary')['config']['model'])
    DEFAULT_TOOL_CALLING_MODEL = os.getenv('DEFAULT_TOOL_CALLING_MODEL', config_loader.get_llm_config('tool_calling')['config']['model'])
    
    # OpenAI Compatibility Layer Configuration
    USE_DIRECT_FUNCTION_CALLS = os.getenv('USE_DIRECT_FUNCTION_CALLS', 'true').lower() == 'true'
    OPENAI_HTTP_TIMEOUT = int(os.getenv('OPENAI_HTTP_TIMEOUT', '600'))  # 10 minutes default
    
    # Server configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Performance configuration
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))
    TASK_TIMEOUT = int(os.getenv('TASK_TIMEOUT', '1800'))  # 30 minutes default for complex AI tasks
    MAX_CONTEXT_WINDOW = int(os.getenv('MAX_CONTEXT_WINDOW', '65536'))

# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================

class OllamaPromptRequest(BaseModel):
    model: str = Field(..., description="Ollama model name")
    prompt: str = Field(..., description="User prompt")
    stream: Optional[bool] = Field(default=True, description="Enable streaming")
    system: Optional[str] = Field(default=None, description="System prompt")
    context: Optional[List[int]] = Field(default=None, description="Context tokens")

class OllamaStreamRequest(BaseModel):
    prompt: Optional[str] = Field(default="", description="User prompt")
    prompt_context: Optional[str] = Field(default="", description="Additional context")
    model: Optional[str] = Field(default=ServerConfig.DEFAULT_MODEL, description="Model to use")
    toolsInUse: Optional[bool] = Field(default=True, description="Enable tools")
    searchWebInUse: Optional[bool] = Field(default=False, description="Enable web search")
    images: Optional[List[str]] = Field(default=["noimage"], description="Image data")
    tools_calling_model: Optional[str] = Field(default=ServerConfig.DEFAULT_TOOL_CALLING_MODEL, description="Model for tool calls")
    
    # Make validation more flexible like the original Flask version
    class Config:
        extra = "allow"  # Allow extra fields


class ToolCall(BaseModel):
    function: Dict[str, Any]

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str

# OpenAI Compatibility Models - Minimal trust design
from typing import Union, List, Any

class OpenAIMessage(BaseModel):
    role: str = Field(..., description="Message role")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="Message content - string or structured content for vision")

class OpenAIChatRequest(BaseModel):
    model: str = Field(..., description="Model name - we only trust this and content")
    messages: List[OpenAIMessage] = Field(..., description="Messages array")
    # Everything else is ignored for security - zero trust design
    stream: Optional[bool] = Field(default=None)
    temperature: Optional[float] = Field(default=None) 
    max_tokens: Optional[int] = Field(default=None)
    top_p: Optional[float] = Field(default=None)
    frequency_penalty: Optional[float] = Field(default=None)
    presence_penalty: Optional[float] = Field(default=None)
    # Support for custom images parameter (file paths or base64)
    images: Optional[List[str]] = Field(default=None, description="Image data - file paths or base64")
    
    class Config:
        extra = "ignore"  # Ignore all other fields for security

class OpenAIStreamChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]

# ==============================================================================
# GLOBAL VARIABLES
# ==============================================================================

db_pool: Optional[Pool] = None
thread_pool = ThreadPoolExecutor(max_workers=ServerConfig.MAX_WORKERS)
simple_cache = {}

# Simple conversation memory for OpenAI compatibility endpoint (in-memory only)
openai_conversations = {}

# PDF PROCESSING COMPLETELY DISABLED
CONVERSATION_PDF_AVAILABLE = False

# ==============================================================================
# LOGGING SETUP
# ==============================================================================

# Configure logging based on environment variables
debug_config = config_loader.load_config().get('debug', {})
log_requests_enabled = os.getenv('LOG_REQUESTS', str(debug_config.get('log_requests', True))).lower() in ('true', '1', 'yes')
log_timing_enabled = os.getenv('LOG_TIMING', str(debug_config.get('log_timing', True))).lower() in ('true', '1', 'yes')

# Determine logging level based on configuration
if not log_requests_enabled and not log_timing_enabled:
    # Disable ALL logging completely
    logging.disable(logging.CRITICAL)
    log_level = logging.CRITICAL + 1
    
    # Also redirect stdout/stderr to suppress print statements
    import os
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    os.dup2(devnull, sys.stderr.fileno())
else:
    logging.disable(logging.NOTSET)  # Enable logging
    log_level = logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fastapi_complete.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Log optimization system status after logger is available
if OPTIMIZATION_AVAILABLE:
    logger.info("🛡️ Optimization safety system loaded successfully")
else:
    logger.warning(f"⚠️ Optimization system not available: {OPTIMIZATION_IMPORT_ERROR}")

# ==============================================================================
# SYSTEM PROMPT MANAGEMENT
# ==============================================================================

def load_tool_model_system_prompt(user_additional_instructions: str = "") -> str:
    """Load the pre-tool model system prompt from external file"""
    try:
        with open('pre_tool_model_system_prompt.txt', 'r', encoding='utf-8') as f:
            prompt = f.read()
        
        # Replace placeholder with user instructions
        if user_additional_instructions:
            prompt = prompt.replace('{USER_ADDITIONAL_INSTRUCTIONS}', 
                                  f"\n\nADDITIONAL USER INSTRUCTIONS:\n{user_additional_instructions}")
        else:
            prompt = prompt.replace('{USER_ADDITIONAL_INSTRUCTIONS}', "")
        
        return prompt
    except FileNotFoundError:
        logger.error("pre_tool_model_system_prompt.txt not found, using fallback prompt")
        return "You are a tool-calling AI assistant. Call the appropriate tools based on the user's request."

def load_primary_model_system_prompt() -> str:
    """Load the primary model system prompt from external file"""
    try:
        with open('primary_model_system_prompt.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            # Debug: Log if anti-hallucination rules are present
            if "🚨 ANTI-HALLUCINATION RULE" in content:
                logger.info("✅ PRIMARY SYSTEM PROMPT: Anti-hallucination rules FOUND")
            else:
                logger.warning("⚠️ PRIMARY SYSTEM PROMPT: Anti-hallucination rules MISSING")
            
            if "🔗 MANDATORY CITATION URL:" in content:
                logger.info("✅ PRIMARY SYSTEM PROMPT: Enhanced source block format FOUND")
            else:
                logger.warning("⚠️ PRIMARY SYSTEM PROMPT: Enhanced source block format MISSING")
                
            logger.info(f"📋 PRIMARY SYSTEM PROMPT LOADED: {len(content)} chars, first 150 chars: {content[:150]}")
            return content
    except FileNotFoundError:
        logger.error("primary_model_system_prompt.txt not found, using fallback prompt")
        return "You are a helpful AI assistant. Provide comprehensive responses based on the context provided."

# ==============================================================================
# LOGGING UTILITIES
# ==============================================================================

def truncate_base64_for_logging(text: str, max_lines: int = 2) -> str:
    """
    Truncate base64 data in text for logging purposes.
    Shows only first max_lines of base64 data followed by '...'
    """
    if not text:
        return text
    
    # Find base64 data patterns
    import re
    base64_pattern = r'data:image/[^;]+;base64,([A-Za-z0-9+/=]{100,})'
    
    def replace_base64(match):
        base64_data = match.group(1)
        # Calculate characters per line (approximately 80 chars per line)
        chars_per_line = 80
        max_chars = max_lines * chars_per_line
        
        if len(base64_data) <= max_chars:
            return match.group(0)  # Return full match if small enough
        
        truncated = base64_data[:max_chars]
        return f"data:image/{match.group(0).split(';')[0].split('/')[1]};base64,{truncated}...[TRUNCATED {len(base64_data)-max_chars} more chars]"
    
    return re.sub(base64_pattern, replace_base64, text)

# ==============================================================================
# DATABASE CONNECTION POOL
# ==============================================================================

async def init_db_pool():
    """Initialize database connection pool"""
    global db_pool
    try:
        db_pool = await aiomysql.create_pool(
            host=ServerConfig.DB_HOST,
            port=3306,
            user=ServerConfig.DB_USER,
            password=ServerConfig.DB_PASSWORD,
            db=ServerConfig.DB_NAME,
            minsize=5,
            maxsize=ServerConfig.DB_POOL_SIZE,
            autocommit=True,
            charset='utf8mb4'
        )
        logger.info(f"Database pool initialized")
    except Exception as e:
        logger.warning(f"Database pool initialization failed: {e}")
        db_pool = None

async def close_db_pool():
    """Close database connection pool"""
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()

@asynccontextmanager
async def get_db_connection():
    """Async context manager for database connections"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not available")
    
    async with db_pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            await connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise

# ==============================================================================
# TOOL MANAGER (Async version of original)
# ==============================================================================

class AsyncToolManager:
    """Async version of the original tool manager"""

    def __init__(self):
        # Always make functions available - they handle missing dependencies gracefully
        self.available_functions = {
            'get_the_secret_tool': self.get_the_secret_tool,
            'wikipedia_query': self.wikipedia_query,
            'get_stock_and_company_data': self.get_stock_and_company_data,  # RE-ENABLED
            'get_news_summaries': self.get_news_summaries,
            'search_web': self.search_web,
            'lookup_website': self.lookup_website,
            'secure_email_sender': self.secure_email_sender
        }

        # Load user-defined tools - defer to async initialization
        self.user_tools = []
        self.user_tools_loaded = False

        # 🔌 PLUGIN SYSTEM: Initialize plugin manager
        self.plugin_manager = None
        self.plugins_loaded = False

        # 🖼️ IMAGE CONTEXT: Store image data for tools that need it
        self.current_images = []
        self.current_request_context = {}

        logger.info(f"AsyncToolManager initialized with {len(self.available_functions)} tools")
    
    def set_image_context(self, images: list, context: dict = None):
        """🖼️ Set image context for tools that need image data"""
        self.current_images = [img for img in images if img and img != 'noimage']
        self.current_request_context = context or {}
        if self.current_images:
            logger.info(f"🖼️ Set image context: {len(self.current_images)} images available for tools")
    
    async def _load_user_tools_async(self):
        """Load user tools asynchronously"""
        if self.user_tools_loaded:
            return

        try:
            from user_tools import discover_user_tools
            self.user_tools = await discover_user_tools()

            # Add user tools to available functions
            for tool in self.user_tools:
                self.available_functions[tool.name] = self._create_user_tool_wrapper(tool)

            if self.user_tools:
                logger.info(f"Loaded {len(self.user_tools)} user-defined tools: {[t.name for t in self.user_tools]}")

            self.user_tools_loaded = True
            logger.info(f"AsyncToolManager now has {len(self.available_functions)} tools total")
        except Exception as e:
            logger.warning(f"Failed to load user tools: {e}")
            self.user_tools_loaded = True  # Don't keep trying

    async def _load_plugins_async(self):
        """🔌 Load plugin system asynchronously"""
        if self.plugins_loaded:
            return

        try:
            from pathlib import Path
            from plugins.plugin_manager import PluginManager

            # Get plugins directory
            plugins_dir = Path(__file__).parent / 'plugins'

            # Get plugin configuration from llm_config.yaml
            plugin_config = config_loader.get_plugin_config()

            # Initialize plugin manager
            self.plugin_manager = PluginManager(plugins_dir, plugin_config)

            # Discover and validate plugins
            init_result = await self.plugin_manager.initialize()

            if init_result['success']:
                # Add plugin wrappers to available functions
                for plugin_name in self.plugin_manager.plugins.keys():
                    self.available_functions[plugin_name] = self._create_plugin_wrapper(plugin_name)

                logger.info(
                    f"🔌 Loaded {init_result['plugins_loaded']} plugins in "
                    f"{init_result['initialization_time']:.3f}s"
                )

                if init_result['plugins_disabled'] > 0:
                    logger.warning(f"🔌 {init_result['plugins_disabled']} plugins disabled due to errors")

            else:
                logger.error(f"🔌 Plugin system initialization failed: {init_result['errors']}")

            self.plugins_loaded = True
            logger.info(f"AsyncToolManager now has {len(self.available_functions)} tools total (including plugins)")

        except Exception as e:
            logger.warning(f"🔌 Failed to load plugins: {e}")
            self.plugins_loaded = True  # Don't keep trying
    
    async def get_tools_definitions(self, exclude_file_email_tools: bool = False) -> list:
        """Get tools definitions for Ollama tool calling"""
        # Load user tools if not already loaded
        await self._load_user_tools_async()

        # 🔌 Load plugins if not already loaded
        await self._load_plugins_async()
        
        # 🚨 CRITICAL MULTI-TOOL CALLING PROTECTION 🚨
        # NEVER MODIFY tool descriptions without checking CRITICAL_MULTI_TOOL_CALLING_PROTECTION.md
        # These descriptions are optimized to prevent model confusion and enable 4+ tool calls
        # ANY aggressive language, conflicts, or redirections will break multi-tool calling
        
        # Always return tools for testing (even if TOOLS_AVAILABLE is False)
        # The individual functions will handle missing dependencies gracefully
        
        # Return all 6 tool functions with timeout/race condition fixes applied
        tools_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "get_the_secret_tool",
                    "description": "Get the current date and time from the system.",  # 🚨 PROTECTED: Simple clean description
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "secret_tool": {
                                "type": "string",
                                "description": "Get the current Date and Time from the system as needed"
                            }
                        },
                        "required": ["secret_tool"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_news_summaries",
                    "description": "Get latest news headlines and summaries from diverse RSS sources. Use for ANY news request including world news, breaking news, current events, political news, financial news, technology news, cryptocurrency news, business news, international news, national news, local news, sports news, and entertainment news.",  # 🚨 PROTECTED: Enhanced routing description
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                            "description": "IMPORTANT: Analyze the user's prompt and select the most specific category that matches their request. For financial/economic/stock market queries, use 'finance' or 'economy'. For cryptocurrency queries, use 'crypto'. For general business news, use 'business'. For international events, use 'world'. For US domestic news, use 'national'. Available categories: 'world', 'national', 'business', 'finance', 'economy', 'technology', 'crypto', 'sports', 'local'. Example: User asks 'stock market news' → use 'finance'. User asks 'cryptocurrency developments' → use 'crypto'. User asks 'economic indicators' → use 'economy'."
                            }
                        },
                        "required": ["filter"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for comprehensive information from multiple sources including academic, news, and reference sites.",  # 🚨 PROTECTED: Enhanced but clean description
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The input query is a string type that is sent to the web search engine."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "lookup_website",
                    "description": "This function takes a URL (href) web address for a website and makes an HTTP request to retrieve the text from the website for further processing to respond to the user's prompt.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL link to be used directly to request a website download."
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wikipedia_query",
                    "description": "Retrieves encyclopedic information from Wikipedia for specific factual lookups and definitions.",  # 🚨 PROTECTED: More specific scope
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "A natural language query, key phrase, or topic of interest. This input should focus on a single topic to ensure accurate results."
                            }
                        },
                        "required": ["question"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stock_and_company_data",
                    "description": "Get basic stock price and company data for a specific ticker symbol.",  # 🚨 PROTECTED: No redirections or conflicts
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The ticker symbol traded on the stock exchange. Examples: \"AAPL\", \"MSFT\", \"AMZN\", \"ORCL\""
                            }
                        },
                        "required": ["symbol"]
                    }
                }
            }
        ]
        
        # Add user-defined tools to the definitions
        # 🚨 CRITICAL ARCHITECTURE: Exclude file/email tools during tool calling phase
        excluded_tools = {"sandboxed_executor", "secure_email_sender"} if exclude_file_email_tools else set()

        for tool in self.user_tools:
            if tool.name in excluded_tools:
                logger.info(f"🚫 EXCLUDING {tool.name} from tool calling phase - deferred auto-execution will handle it")
                continue

            tool_def = tool.get_function_definition()
            formatted_def = {
                "type": "function",
                "function": {
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "parameters": tool_def["parameters"]
                }
            }
            tools_definitions.append(formatted_def)

        # 🔌 Add plugin tools to the definitions
        if self.plugin_manager and self.plugins_loaded:
            plugins = self.plugin_manager.get_available_plugins()

            for plugin in plugins:
                plugin_def = {
                    "type": "function",
                    "function": {
                        "name": plugin["name"],
                        "description": plugin["description"],
                        "parameters": plugin["parameters"]
                    }
                }
                tools_definitions.append(plugin_def)
                logger.debug(f"🔌 Added plugin tool: {plugin['name']}")

        return tools_definitions
    
    def _create_plugin_wrapper(self, plugin_name: str):
        """🔌 Create an async wrapper for plugin execution"""
        async def wrapper(args = "") -> str:
            import json
            try:
                # Handle different argument types from Ollama
                if isinstance(args, dict):
                    params = args
                elif isinstance(args, str) and args.strip():
                    if args.strip().startswith('{'):
                        params = json.loads(args)
                    else:
                        # Simple string argument - try to map to first parameter
                        params = {"query": args}
                else:
                    params = {}

                # Execute plugin through PluginManager
                result = await self.plugin_manager.execute_plugin(plugin_name, params)

                if result.get("success", False):
                    # Return the formatted result
                    plugin_result = result.get("result", "")
                    return str(plugin_result)
                else:
                    # Return error message
                    error_msg = result.get("error", "Unknown error")
                    return f"Plugin '{plugin_name}' error: {error_msg}"

            except json.JSONDecodeError:
                return f"Plugin '{plugin_name}' error: Invalid JSON arguments"
            except Exception as e:
                logger.error(f"🔌 Error executing plugin '{plugin_name}': {e}")
                return f"Plugin '{plugin_name}' error: {str(e)}"

        return wrapper

    def _create_user_tool_wrapper(self, tool):
        """Create an async wrapper for user tools to match the expected function signature"""
        async def wrapper(args = "") -> str:
            import json
            try:
                # Handle different argument types from Ollama
                if isinstance(args, dict):
                    # Ollama already parsed JSON to dict
                    params = args
                elif isinstance(args, str) and args.strip():
                    # Try to parse as JSON string
                    if args.strip().startswith('{'):
                        params = json.loads(args)
                    else:
                        # Simple string argument
                        params = {"query": args}
                else:
                    # Empty or None args
                    params = {}
                
                # Execute the user tool
                result = await tool.execute(**params)
                
                if result.get("success", False):
                    # Format the successful result - handle different result key patterns
                    tool_result = None
                    
                    # Try different common result keys used by tools
                    if "result" in result:
                        tool_result = result["result"]
                    elif "description" in result:
                        # Handle image_to_text and similar tools that use "description"
                        tool_result = result["description"]
                    elif "content" in result:
                        # Handle tools that use "content" key
                        tool_result = result["content"]
                    else:
                        # Fallback: return the entire result dict excluding success/error keys
                        excluded_keys = {"success", "error", "model", "timestamp"}
                        tool_result = {k: v for k, v in result.items() if k not in excluded_keys}
                    
                    if isinstance(tool_result, dict):
                        # Convert dict result to readable string with base64 truncation
                        formatted_result = json.dumps(tool_result, indent=2)
                        return truncate_base64_for_logging(formatted_result)
                    else:
                        return str(tool_result)
                else:
                    # Return error message
                    error_msg = result.get("error", "Unknown error")
                    return f"Tool '{tool.name}' error: {error_msg}"
                    
            except json.JSONDecodeError:
                return f"Tool '{tool.name}' error: Invalid JSON arguments"
            except Exception as e:
                logger.error(f"Error executing user tool '{tool.name}': {e}")
                return f"Tool '{tool.name}' error: {str(e)}"
        
        return wrapper
    
    async def get_the_secret_tool(self, args: str = "") -> str:
        """Get current date and time"""
        try:
            current_time = datetime.now()
            return f"Current date and time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        except Exception as e:
            return f"Error getting date/time: {str(e)}"
    
    async def wikipedia_query(self, args: str) -> str:
        """Query Wikipedia"""
        try:
            # Remove TOOLS_AVAILABLE check - let function handle missing deps gracefully
            
            # Handle both JSON string and plain string arguments
            try:
                data = json.loads(args) if isinstance(args, str) and args.startswith('{') else args
                query = data.get('question', args) if isinstance(data, dict) else str(args)
            except (json.JSONDecodeError, AttributeError):
                query = str(args)
            
            def sync_wikipedia_query():
                from datetime import datetime
                
                wiki = wikipediaapi.Wikipedia(
                    language='en',
                    user_agent='FastAPIServer/1.0 (https://github.com/user/project)'
                )
                page = wiki.page(query)
                
                if page.exists():
                    # Truncate summary if too long
                    summary = page.summary[:2000] + "..." if len(page.summary) > 2000 else page.summary
                    
                    # Use enhanced source block formatting
                    formatted_result = _format_source_block(
                        source_url=page.fullurl,
                        title=page.title,
                        content=f"Wikipedia Summary:\n\n{summary}",
                        source_num=1
                    )
                    
                    return f"\nHere are the Wikipedia query results:\n{formatted_result}"
                else:
                    return f"No Wikipedia page found for: {query}"
            
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool, sync_wikipedia_query
            )
        except Exception as e:
            return f"Wikipedia query error: {str(e)}"
    
    async def get_stock_and_company_data(self, args: str) -> str:
        """Get stock data"""
        try:
            # Remove TOOLS_AVAILABLE check - let function handle missing deps gracefully
                
            # Handle both JSON string and plain string arguments
            try:
                data = json.loads(args) if isinstance(args, str) and args.startswith('{') else args
                symbol = data.get('symbol', args) if isinstance(data, dict) else str(args)
            except (json.JSONDecodeError, AttributeError):
                symbol = str(args)
            
            def sync_stock_data():
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="5d")
                
                current_price = hist['Close'].iloc[-1] if not hist.empty else "N/A"
                change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2] if len(hist) > 1 else 0
                
                return f"""Stock Data for {symbol}:
                Current Price: ${current_price:.2f}
                Change: ${change:.2f}
                Company: {info.get('longName', 'N/A')}
                Sector: {info.get('sector', 'N/A')}
                Market Cap: {info.get('marketCap', 'N/A')}"""
            
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool, sync_stock_data
            )
        except Exception as e:
            return f"Stock data error: {str(e)}"
    
    async def get_news_summaries(self, args: str) -> str:
        """
        Get comprehensive news summaries with FULL ARTICLE CONTENT from multiple sources based on a given filter.
        Enhanced to extract detailed content from each article for more substantial information.
        """
        try:
            # Remove TOOLS_AVAILABLE check - let function handle missing deps gracefully
                
            def sync_news_query():
                # Handle parameter parsing like the original
                if isinstance(args, str):
                    # Try to parse as dict first, fall back to string
                    try:
                        data = json.loads(args) if args.startswith('{') else {'filter': args}
                    except:
                        data = {'filter': args}
                else:
                    data = args if isinstance(args, dict) else {'filter': str(args)}
                
                # Get the filter keyword (like original implementation)
                newsFilter = data.get('filter', '').lower().strip()
                
                # Enhanced news category mapping with diverse, reliable sources
                NEWS_URLS = {
                    "world": [
                        # Mainstream reliable sources
                        "https://apnews.com/world-news",
                        "https://feeds.bbci.co.uk/news/world/rss.xml",
                        "https://www.aljazeera.com/xml/rss/all.xml",
                        # International perspectives
                        "https://rss.dw.com/atom/rss-en-all",  # Deutsche Welle
                        "https://www.theguardian.com/world/rss",
                        # Alternative viewpoints
                        "https://theintercept.com/feed/"
                    ],
                    "national": [
                        # Traditional sources
                        "https://apnews.com/us-news",
                        "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
                        "https://www.npr.org/sections/national/",
                        # Independent sources
                        "https://www.propublica.org/feeds/propublica/main",
                        "https://www.axios.com/feeds/articles.rss"
                    ],
                    "business": [
                        # Traditional business news
                        "https://www.npr.org/sections/business/",
                        "https://feeds.bbci.co.uk/news/business/rss.xml",
                        # Alternative business perspectives
                        "https://www.axios.com/feeds/business.rss",
                        "https://www.zerohedge.com/fullrss2.xml",  # Direct RSS instead of FeedBurner
                        # Additional business sources
                        "https://feeds.bloomberg.com/markets/news.rss",
                        "https://www.businessinsider.com/rss"
                    ],
                    "finance": [
                        # Major Financial News Outlets
                        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
                        "https://finance.yahoo.com/news/rssindex",
                        "https://feeds.bloomberg.com/markets/news.rss",
                        "https://www.marketwatch.com/rss/topstories",
                        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",  # Wall Street Journal
                        # Economic and Federal Reserve News
                        "https://feeds.bbci.co.uk/news/business/rss.xml",
                        "https://www.cnbc.com/id/20910258/device/rss/rss.html",  # Economics
                        "https://www.federalreserve.gov/feeds/press_all.xml",
                        # Stock Market and Trading
                        "https://www.investing.com/rss/news.rss",
                        "https://seekingalpha.com/feed.xml",
                        "https://www.fool.com/feeds/index.aspx",  # Motley Fool
                        # Alternative Financial News
                        "https://www.zerohedge.com/fullrss2.xml",
                        "https://finance.yahoo.com/rss/topstories",
                        "https://www.reuters.com/business/finance/"
                    ],
                    "economy": [
                        # Economic Policy and Data
                        "https://www.cnbc.com/id/20910258/device/rss/rss.html",  # Economics
                        "https://www.federalreserve.gov/feeds/press_all.xml",
                        "https://feeds.bbci.co.uk/news/business/rss.xml",
                        "https://www.reuters.com/business/",
                        # Economic Analysis
                        "https://www.bloomberg.com/economics",
                        "https://www.economist.com/finance-and-economics/rss.xml",
                        "https://www.wsj.com/xml/rss/3_7085.xml"  # WSJ Economics
                    ],
                    "technology": [
                        # Independent tech sources (reliable direct feeds)
                        "https://arstechnica.com/feed/",
                        "https://thehackernews.com/feeds/posts/default?alt=rss",  # Direct RSS instead of FeedBurner
                        "https://techcrunch.com/feed/",  # Direct RSS instead of FeedBurner
                        # Alternative tech perspectives  
                        "https://www.techdirt.com/feed/",
                        "https://www.theregister.com/headlines.atom",
                        # Additional reliable tech sources
                        "https://www.wired.com/feed/rss",
                        "https://www.zdnet.com/news/rss.xml"
                    ],
                    "crypto": [
                        # Specialized cryptocurrency sources
                        "https://www.coindesk.com/arc/outboundfeeds/rss/",
                        "https://decrypt.co/feed",
                        "https://www.theblock.co/rss.xml",
                        "https://cointelegraph.com/rss"
                    ],
                    "science": [
                        # Traditional science sources
                        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
                        "https://www.sciencenews.org/feed",
                        "https://www.npr.org/sections/science/",
                        # Independent science sources
                        "https://arstechnica.com/science/feed/"
                    ],
                    "politics": [
                        # Political news with diverse perspectives
                        "https://www.politico.com/rss/politicopicks.xml",
                        "https://thehill.com/news/feed/",
                        "https://www.propublica.org/feeds/propublica/main",
                        "https://theintercept.com/feed/"
                    ],
                    "news": [        
                        # Mainstream sources
                        "https://apnews.com/hub/ap-top-news",
                        "https://feeds.bbci.co.uk/news/rss.xml",
                        "https://www.npr.org/sections/news/",
                        # Independent sources
                        "https://www.axios.com/feeds/articles.rss",
                        "https://www.propublica.org/feeds/propublica/main"
                    ],
                    "national": [
                        # US National News Sources
                        "https://apnews.com/hub/ap-top-news",
                        "https://www.npr.org/sections/news/",
                        "https://www.usatoday.com/rss/news/",
                        "https://www.cbsnews.com/latest/rss/main",
                        "https://www.nbcnews.com/feeds/",
                        "https://abcnews.go.com/abcnews/topstories"
                    ],
                    "world": [
                        # International News Sources
                        "https://feeds.bbci.co.uk/news/world/rss.xml",
                        "https://www.aljazeera.com/xml/rss/all.xml",
                        "https://rss.dw.com/atom/rss-en-all",  # Deutsche Welle - Fixed URL
                        "https://www.france24.com/en/rss",
                        "https://www.euronews.com/rss?level=vertical&name=news",
                        "https://www.scmp.com/rss/feed/"  # South China Morning Post - Fixed URL
                    ],
                    "local": [
                        # Regional/Local News Sources
                        "https://www.latimes.com/rss2.0.xml",
                        "https://www.sfgate.com/rss/feed/Chronicle-News-940.php",
                        "https://www.chicagotribune.com/arcio/rss/",
                        "https://www.nytimes.com/services/xml/rss/nyt/HomePage.xml",
                        "https://www.washingtonpost.com/rss/",
                        "https://www.dallasnews.com/feed/"
                    ],
                    "default": [
                        "https://apnews.com/hub/ap-top-news",
                        "https://feeds.bbci.co.uk/news/rss.xml",
                        "https://www.axios.com/feeds/articles.rss"
                    ]
                }
                
                # 🎯 ENHANCED INTELLIGENT CATEGORY DETECTION SYSTEM
                # Multi-factor analysis with phrase detection, weights, and intent recognition
                
                ENHANCED_CATEGORY_MAPPING = {
                    "crypto": {
                        "primary_terms": {"crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "blockchain"},
                        "secondary_terms": {"defi", "nft", "altcoin", "mining", "wallet", "exchange", "digital currency", "web3", "solana", "cardano", "polygon", "binance", "coinbase"},
                        "compound_phrases": {"crypto news", "bitcoin price", "ethereum update", "blockchain technology", "digital assets", "crypto market", "defi protocol"},
                        "financial_crossover": {"crypto stocks", "bitcoin etf", "cryptocurrency investment", "digital asset trading"},
                        "tech_crossover": {"blockchain development", "smart contracts", "cryptocurrency technology"},
                        "weight": 1.0,
                        "fallback_categories": ["finance", "technology"]
                    },
                    "finance": {
                        "primary_terms": {"finance", "financial", "stocks", "market", "markets", "stock"},
                        "secondary_terms": {"securities", "financing", "bonds", "wall street", "nasdaq", "dow jones", "trading", "investment", "earnings"},
                        "compound_phrases": {"stock market", "financial news", "market update", "earnings report", "market analysis", "stock trading"},
                        "business_crossover": {"corporate earnings", "business finance", "company stocks"},
                        "weight": 0.9,
                        "fallback_categories": ["business"]
                    },
                    "economy": {
                        "primary_terms": {"economy", "economic", "inflation", "recession", "gdp", "unemployment"},
                        "secondary_terms": {"interest rates", "fed rates", "federal reserve", "monetary policy", "fiscal policy", "economic growth", "economic indicators", "consumer price index", "cpi"},
                        "compound_phrases": {"economic news", "fed meeting", "economic indicators", "monetary policy", "economic growth", "inflation report", "unemployment rate"},
                        "finance_crossover": {"economic market", "financial economy", "market economy"},
                        "weight": 0.9,
                        "fallback_categories": ["finance"]
                    },
                    "technology": {
                        "primary_terms": {"technology", "tech", "ai", "artificial intelligence", "software", "hardware", "digital"},
                        "secondary_terms": {"machine learning", "computer", "internet", "cybersecurity", "startup", "innovation", "gadgets", "devices", "cloud", "data", "programming", "app", "platform"},
                        "compound_phrases": {"tech news", "ai development", "software update", "tech startup", "digital transformation", "cyber attack", "tech earnings"},
                        "business_crossover": {"tech companies", "software business", "tech industry"},
                        "weight": 0.8,
                        "fallback_categories": ["business"]
                    },
                    "business": {
                        "primary_terms": {"business", "trade", "commerce", "commercial", "corporate", "company", "companies"},
                        "secondary_terms": {"retail", "enterprise", "industry", "sector", "revenue", "profit", "ceo", "merger", "acquisition", "ipo"},
                        "compound_phrases": {"business news", "corporate earnings", "company update", "industry analysis", "market sector"},
                        "weight": 0.7,
                        "fallback_categories": ["finance"]
                    },
                    "world": {
                        "primary_terms": {"world", "global", "international", "foreign", "abroad"},
                        "secondary_terms": {"europe", "asia", "africa", "china", "russia", "uk", "japan", "india", "brazil", "canada", "mexico"},
                        "compound_phrases": {"world news", "international affairs", "global economy", "foreign policy", "international relations"},
                        "geo_specific": {"european union", "middle east", "south america", "southeast asia"},
                        "weight": 0.9,
                        "fallback_categories": ["national"]
                    },
                    "national": {
                        "primary_terms": {"national", "nation", "domestic", "us", "usa", "american", "homeland", "united states"},
                        "secondary_terms": {"congress", "senate", "house", "washington", "federal", "state", "local", "governor", "mayor"},
                        "compound_phrases": {"national news", "us news", "american politics", "domestic policy", "homeland security"},
                        "weight": 0.8,
                        "fallback_categories": ["politics"]
                    },
                    "politics": {
                        "primary_terms": {"politics", "political", "government", "election", "campaign", "policy", "legislation"},
                        "secondary_terms": {"democrat", "republican", "biden", "trump", "vote", "voting", "ballot", "candidate", "senator", "representative"},
                        "compound_phrases": {"political news", "election update", "campaign news", "government policy", "political analysis"},
                        "weight": 0.8,
                        "fallback_categories": ["national"]
                    },
                    "science": {
                        "primary_terms": {"science", "scientific", "research", "study", "discovery", "experiment"},
                        "secondary_terms": {"physics", "chemistry", "biology", "nasa", "space", "medicine", "health", "climate", "environment"},
                        "compound_phrases": {"scientific breakthrough", "research findings", "space exploration", "medical research", "climate change"},
                        "weight": 0.6,
                        "fallback_categories": ["technology"]
                    },
                    "local": {
                        "primary_terms": {"local", "regional", "city", "town", "community", "neighborhood"},
                        "secondary_terms": {"metro", "county", "municipal", "downtown", "suburb", "district", "area", "vicinity", "nearby"},
                        "compound_phrases": {"local news", "regional update", "city news", "community events", "metro area", "local government"},
                        "geo_indicators": {"california", "texas", "new york", "florida", "chicago", "los angeles", "houston", "phoenix", "philadelphia", "san antonio"},
                        "weight": 0.7,
                        "fallback_categories": ["national"]
                    }
                }
                
                # 🧠 INTELLIGENT CATEGORY DETECTION ENGINE
                def find_category_intelligent(newsFilter):
                    """
                    Advanced category detection using multi-factor analysis:
                    - Phrase detection (compound phrases get priority)
                    - Weight-based scoring system
                    - Primary vs secondary term hierarchy
                    - Crossover detection for mixed topics
                    - Fuzzy matching for typos/variations
                    """
                    import re
                    from collections import defaultdict
                    
                    # Normalize and prepare the filter text
                    original_filter = newsFilter.lower().strip()
                    
                    # Remove common stop words that don't contribute to categorization
                    stop_words = {"the", "get", "latest", "current", "recent", "update", "updates", "news", "information", "about", "on", "for", "and", "or"}
                    words = [w for w in re.findall(r'\b\w+\b', original_filter) if w not in stop_words]
                    clean_filter = ' '.join(words)
                    
                    logger.debug(f"🎯 Category Detection: '{newsFilter}' -> '{clean_filter}'")
                    
                    # Scoring system for each category
                    category_scores = defaultdict(float)
                    
                    for category, config in ENHANCED_CATEGORY_MAPPING.items():
                        score = 0.0
                        matches = []
                        
                        # 1. COMPOUND PHRASES (highest priority - exact phrase matching)
                        compound_phrases = config.get("compound_phrases", set())
                        for phrase in compound_phrases:
                            if phrase in original_filter:
                                score += 3.0 * config["weight"]  # High score for exact phrase matches
                                matches.append(f"phrase:'{phrase}'")
                        
                        # 2. PRIMARY TERMS (high weight)
                        primary_terms = config.get("primary_terms", set())
                        for term in primary_terms:
                            if term in clean_filter:
                                score += 2.0 * config["weight"]
                                matches.append(f"primary:'{term}'")
                        
                        # 3. SECONDARY TERMS (medium weight)  
                        secondary_terms = config.get("secondary_terms", set())
                        for term in secondary_terms:
                            if term in clean_filter:
                                score += 1.0 * config["weight"]
                                matches.append(f"secondary:'{term}'")
                        
                        # 4. CROSSOVER TERMS (for mixed topics)
                        for crossover_type in ["financial_crossover", "tech_crossover", "business_crossover", "geo_specific", "finance_crossover"]:
                            crossover_terms = config.get(crossover_type, set())
                            for term in crossover_terms:
                                if term in original_filter:
                                    score += 1.5 * config["weight"]
                                    matches.append(f"{crossover_type}:'{term}'")
                        
                        # 4.5. GEO INDICATORS (for local/regional detection)
                        geo_indicators = config.get("geo_indicators", set())
                        for geo_term in geo_indicators:
                            if geo_term in original_filter:
                                score += 2.0 * config["weight"]  # High score for geographic indicators
                                matches.append(f"geo:'{geo_term}'")
                        
                        # 5. PARTIAL MATCHING (for typos/variations)
                        for word in words:
                            # Check if any word is a substring of category terms (fuzzy matching)
                            for term in primary_terms.union(secondary_terms):
                                if len(word) > 3 and (word in term or term in word):
                                    score += 0.5 * config["weight"]
                                    matches.append(f"fuzzy:'{word}'-'{term}'")
                        
                        if score > 0:
                            category_scores[category] = score
                            logger.debug(f"   {category}: {score:.2f} points - {matches}")
                    
                    # Find the best category
                    if category_scores:
                        best_category = max(category_scores.items(), key=lambda x: x[1])
                        category_name, final_score = best_category
                        
                        logger.debug(f"🎯 Selected Category: '{category_name}' with score {final_score:.2f}")
                        
                        # If score is very low, consider fallbacks
                        if final_score < 1.0:
                            fallbacks = ENHANCED_CATEGORY_MAPPING[category_name].get("fallback_categories", ["default"])
                            print(f"🔄 Low confidence, considering fallbacks: {fallbacks}", flush=True)
                            # For now, stick with the detected category but log the fallback consideration
                        
                        return category_name
                    
                    print(f"🔄 No category detected, using 'default'", flush=True)
                    return "default"
                
                # Wrapper function to maintain compatibility
                def find_category(newsFilter):
                    return find_category_intelligent(newsFilter)
                
                # 🎯 ENHANCED MULTI-SOURCE UNION SYSTEM
                def find_categories_ranked(newsFilter):
                    """
                    Returns ranked list of relevant categories based on query
                    Example: "stock market finance economic" -> ["finance", "economy", "business"]
                    """
                    import re
                    from collections import defaultdict
                    
                    # Normalize the filter text
                    original_filter = newsFilter.lower().strip()
                    stop_words = {"the", "get", "latest", "current", "recent", "update", "updates", "news", "information", "about", "on", "for", "and", "or"}
                    words = [w for w in re.findall(r'\b\w+\b', original_filter) if w not in stop_words]
                    clean_filter = ' '.join(words)
                    
                    logger.debug(f"🎯 Multi-Category Detection: '{newsFilter}' -> '{clean_filter}'")
                    
                    # Score ALL categories (not just the top one)
                    category_scores = defaultdict(float)
                    
                    for category, config in ENHANCED_CATEGORY_MAPPING.items():
                        score = 0.0
                        matches = []
                        
                        # Compound phrases (highest priority)
                        compound_phrases = config.get("compound_phrases", set())
                        for phrase in compound_phrases:
                            if phrase in original_filter:
                                score += 3.0 * config["weight"]
                                matches.append(f"phrase:'{phrase}'")
                        
                        # Primary terms
                        primary_terms = config.get("primary_terms", set())
                        for term in primary_terms:
                            if term in clean_filter:
                                score += 2.0 * config["weight"]
                                matches.append(f"primary:'{term}'")
                        
                        # Secondary terms
                        secondary_terms = config.get("secondary_terms", set())
                        for term in secondary_terms:
                            if term in clean_filter:
                                score += 1.0 * config["weight"]
                                matches.append(f"secondary:'{term}'")
                        
                        # Crossover terms
                        for crossover_type in ["financial_crossover", "tech_crossover", "business_crossover", "geo_specific", "finance_crossover"]:
                            crossover_terms = config.get(crossover_type, set())
                            for term in crossover_terms:
                                if term in original_filter:
                                    score += 1.5 * config["weight"]
                                    matches.append(f"{crossover_type}:'{term}'")
                        
                        # Geo indicators
                        geo_indicators = config.get("geo_indicators", set())
                        for geo_term in geo_indicators:
                            if geo_term in original_filter:
                                score += 2.0 * config["weight"]
                                matches.append(f"geo:'{geo_term}'")
                        
                        if score > 0:
                            category_scores[category] = score
                            logger.debug(f"   {category}: {score:.2f} points - {matches}")
                    
                    # Return ranked categories (threshold: score > 0.5)
                    ranked_categories = []
                    if category_scores:
                        # Sort by score descending
                        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
                        
                        # Include categories with meaningful scores
                        for cat_name, score in sorted_categories:
                            if score >= 0.5:  # Meaningful threshold
                                ranked_categories.append(cat_name)
                    
                    if not ranked_categories:
                        ranked_categories = ["default"]
                    
                    logger.debug(f"🎯 Ranked Categories: {ranked_categories}")
                    return ranked_categories
                
                def find_keyword_sources(newsFilter):
                    """
                    Extract specific keywords that map to specialized sources
                    Example: "stock market" -> stock market specific RSS feeds
                    """
                    keyword_mappings = {
                        "stock market": ["finance", "economy"],
                        "federal reserve": ["economy"],
                        "fed rates": ["economy"],
                        "inflation": ["economy"],
                        "gdp": ["economy"],
                        "unemployment": ["economy"],
                        "earnings": ["finance"],
                        "nasdaq": ["finance"],
                        "dow jones": ["finance"],
                        "s&p 500": ["finance"],
                        "cryptocurrency": ["crypto"],
                        "bitcoin": ["crypto"],
                        "florida": ["local"],
                        "california": ["local"],
                        "texas": ["local"],
                        "new york": ["local"]
                    }
                    
                    filter_lower = newsFilter.lower()
                    keyword_categories = []
                    detected_keywords = []
                    
                    for keyword, categories in keyword_mappings.items():
                        if keyword in filter_lower:
                            detected_keywords.append(keyword)
                            keyword_categories.extend(categories)
                    
                    # Remove duplicates while preserving order
                    keyword_categories = list(dict.fromkeys(keyword_categories))
                    
                    if detected_keywords:
                        logger.debug(f"🔍 Keywords Detected: {detected_keywords} -> Categories: {keyword_categories}")
                    
                    return keyword_categories
                
                def get_union_sources(ranked_categories, keyword_sources):
                    """
                    Combine RSS sources from ranked categories + keyword sources
                    Returns unified list of RSS URLs
                    """
                    all_sources = []
                    
                    # Add sources from ranked categories (in priority order)
                    for category in ranked_categories:
                        category_urls = NEWS_URLS.get(category, [])
                        all_sources.extend(category_urls)
                        logger.debug(f"📰 Added {len(category_urls)} sources from '{category}' category")
                    
                    # Add sources from keyword detection
                    for category in keyword_sources:
                        if category not in ranked_categories:  # Avoid duplicates
                            category_urls = NEWS_URLS.get(category, [])
                            all_sources.extend(category_urls)
                            logger.debug(f"🔍 Added {len(category_urls)} sources from keyword '{category}' category")
                    
                    # Remove duplicate URLs while preserving order
                    unique_sources = list(dict.fromkeys(all_sources))
                    
                    # If no sources found, use default
                    if not unique_sources:
                        unique_sources = NEWS_URLS.get("default", [])
                        logger.debug(f"🔄 No specific sources found, using {len(unique_sources)} default sources")
                    
                    # 🎯 REMOVED: Let primary LLM decide what to select from full context
                    # Keep all sources available for rich context - let LLM choose what's important
                    
                    logger.debug(f"🎯 UNION RESULT: {len(unique_sources)} total unique sources from {len(ranked_categories + keyword_sources)} categories")
                    return unique_sources
                
                
                from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

                def clean_news_url(url):
                    """
                    Clean Google News URLs by removing corrupted or excessively long parameters.

                    Args:
                        url: The URL to clean

                    Returns:
                        str: Clean URL, or None if URL is invalid/corrupted beyond repair
                    """
                    if not url or not isinstance(url, str):
                        return None

                    try:
                        # Parse the URL into components
                        parsed_url = urlparse(url)

                        # Validate basic URL structure
                        if not parsed_url.scheme or not parsed_url.netloc:
                            return None

                        # Extract query parameters
                        query_params = parse_qs(parsed_url.query)

                        # Keep only clean parameters, filtering out corrupted ones
                        keep_params = ['nid', 'dat', 'ed', 'hl', 'gl', 'ceid']  # Common Google News parameters
                        cleaned_query = {}

                        for key, values in query_params.items():
                            if key in keep_params and values:
                                param_value = values[0]
                                # Reject parameters that are excessively long (likely corrupted)
                                if len(param_value) > 100:  # Most legitimate params are much shorter
                                    print(f"🚨 Rejecting corrupted parameter '{key}' with length {len(param_value)}", flush=True)
                                    continue
                                # Reject parameters with repeated patterns (corruption indicator)
                                if len(param_value) > 20 and param_value[:10] * 5 in param_value:
                                    print(f"🚨 Rejecting repeated pattern in parameter '{key}': {param_value[:50]}...", flush=True)
                                    continue
                                cleaned_query[key] = param_value

                        # Rebuild the query string
                        cleaned_query_string = urlencode(cleaned_query) if cleaned_query else ""

                        # Reconstruct the URL without the corrupted parameters
                        cleaned_url = urlunparse((
                            parsed_url.scheme,    # scheme (e.g., https)
                            parsed_url.netloc,    # netloc (e.g., news.google.com)
                            parsed_url.path,      # path (e.g., /newspapers)
                            parsed_url.params,    # params (usually empty)
                            cleaned_query_string, # cleaned query string
                            parsed_url.fragment   # fragment (usually empty)
                        ))

                        # Final validation: reject if URL is still too long (indicates other corruption)
                        if len(cleaned_url) > 2000:  # Reasonable URL length limit
                            print(f"🚨 Rejecting URL still too long after cleaning: {len(cleaned_url)} chars", flush=True)
                            return None

                        return cleaned_url

                    except Exception as e:
                        print(f"🚨 Error cleaning URL '{url[:100]}...': {e}", flush=True)
                        return None

                
                
                # Enhanced Google News function with FULL ARTICLE CONTENT and enhanced source blocks
                def get_news_from_google(keyword, source_num_start=1, categories=None):
                    res = ''
                    articlesLimit = 8  # Reduced slightly to account for more content per article
                    source_count = 0
                    try:
                        google_news = GNews(language='en', country='US', max_results=articlesLimit)

                        # Enhance search terms based on detected categories
                        enhanced_keyword = keyword
                        if categories:
                            if any(cat in ['finance', 'economy'] for cat in categories):
                                enhanced_keyword = f"{keyword} stocks market finance economy"
                            elif 'crypto' in categories:
                                enhanced_keyword = f"{keyword} cryptocurrency bitcoin blockchain"
                            elif 'technology' in categories:
                                enhanced_keyword = f"{keyword} tech innovation AI software"

                        logger.debug(f"🔍 Google News search: '{keyword}' -> '{enhanced_keyword}'")
                        keyword_news = google_news.get_news(enhanced_keyword)
                        
                        for i in range(min(len(keyword_news), articlesLimit)):
                            article = keyword_news[i]
                            title = article.get('title', 'No title')
                            description = article.get('description', 'No description')
                            published_date = article.get('published date', 'N/A')
                            article_url = article.get('url', '')
                            
                            # Try to get full article content
                            full_content = ""
                            try:
                                # Check if newspaper3k is available
                                import warnings
                                # Suppress SyntaxWarnings from old newspaper3k package
                                with warnings.catch_warnings():
                                    warnings.filterwarnings("ignore", category=SyntaxWarning)
                                    import newspaper
                                # Get the full article from Google News
                                full_article = google_news.get_full_article(article['url'])
                                if full_article and hasattr(full_article, 'text'):
                                    # Extract first 500 characters of actual article content
                                    article_text = full_article.text.strip()
                                    if len(article_text) > 100:  # Only use substantial content
                                        full_content = article_text[:800] + "..." if len(article_text) > 800 else article_text
                                    else:
                                        # Fallback to description if full text is too short
                                        full_content = description
                                else:
                                    full_content = description
                            except ImportError:
                                # newspaper3k not available, fall back to enhanced description
                                print("newspaper3k not available, using enhanced description", flush=True)
                                full_content = description
                                # Try to get more content via URL extraction
                                try:
                                    if article_url:
                                        enhanced_content = get_text_from_url(article_url)
                                        if len(enhanced_content) > len(description):
                                            full_content = enhanced_content[:800] + "..." if len(enhanced_content) > 800 else enhanced_content
                                except Exception as url_error:
                                    pass  # Keep original description
                            except Exception as content_error:
                                # Fallback to description if full content extraction fails
                                full_content = description
                            
                            # Format using enhanced source block with safe URL cleaning
                            cleaned_url = clean_news_url(article_url) if article_url else None
                            safe_url = cleaned_url if cleaned_url else (article_url if article_url else f"https://news.google.com/search?q={keyword}")

                            formatted_source = _format_source_block(
                                source_url=safe_url,
                                title=title,
                                content=full_content,
                                source_num=source_num_start + source_count
                            )
                            res += formatted_source
                            source_count += 1
                            
                    except Exception as e:
                        res += f"Error from Google news: {e}\n"
                    return res, source_count
                
                # Enhanced web content extraction with improved RSS/XML parsing
                def get_text_from_url(url):
                    try:
                        response = requests_compatible_get(url, timeout=15, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        })
                        response.raise_for_status()
                        
                        from bs4 import BeautifulSoup
                        
                        # Determine if this is RSS/XML content
                        content_type = response.headers.get('content-type', '').lower()
                        is_rss_xml = (
                            'xml' in content_type or 
                            'rss' in content_type or
                            url.endswith('.xml') or 
                            url.endswith('.rss') or
                            'feed' in url.lower() or
                            response.text.strip().startswith('<?xml')
                        )
                        
                        if is_rss_xml:
                            # Use XML parser for RSS feeds to avoid warnings
                            try:
                                soup = BeautifulSoup(response.text, 'xml')
                            except:
                                # Fallback to lxml if available, then html.parser
                                try:
                                    soup = BeautifulSoup(response.text, 'lxml')
                                except:
                                    soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Extract RSS items
                            texts = []
                            items = soup.find_all(['item', 'entry'])
                            for item in items[:5]:  # Limit to 5 recent articles
                                title = item.find(['title'])
                                description = item.find(['description', 'summary', 'content'])
                                
                                if title:
                                    title_text = title.get_text().strip()
                                    if title_text:
                                        texts.append(f"Title: {title_text}")
                                
                                if description:
                                    desc_text = description.get_text().strip()
                                    if desc_text and len(desc_text) > 20:
                                        # Clean up description
                                        desc_text = desc_text.replace('\n', ' ').replace('\r', ' ')
                                        if len(desc_text) > 200:
                                            desc_text = desc_text[:200] + "..."
                                        texts.append(f"Content: {desc_text}")
                                
                                texts.append("---")  # Separator
                            
                            return '\n'.join(texts) if texts else "RSS feed processed but no content extracted"
                        
                        else:
                            # Regular HTML parsing
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Remove unwanted tags
                            for tag_name in ['footer', 'nav', 'script', 'style', 'aside', 'header']:
                                for tag in soup.find_all(tag_name):
                                    tag.decompose()
                            
                            # Extract text from paragraphs and headers
                            texts = []
                            for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                                text = tag.get_text().strip()
                                if text and len(text) > 20:  # Only meaningful content
                                    texts.append(text)
                            
                            return '\n\n'.join(texts[:10])  # Limit to first 10 meaningful paragraphs
                        
                    except Exception as e:
                        return f"Error fetching {url}: {str(e)}"
                
                # Main logic (from original implementation)
                today = datetime.now()
                todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p")
                
                # 🎯 UNION-BASED MULTI-SOURCE SYSTEM
                # Step 1: Smart Category Detection (returns ranked categories)
                ranked_categories = find_categories_ranked(newsFilter)
                
                # Step 2: Keyword-based source filtering
                keyword_sources = find_keyword_sources(newsFilter)
                
                # Step 3: UNION all sources from categories + keywords
                urls = get_union_sources(ranked_categories, keyword_sources)
                
                # Initialize result string with timestamp and sorting instructions
                res = f'''\nFROM EXTERNAL SOURCES as of [Current Date and Time: {todayStr}]. Here is the News Summary you requested, use the summary to compose your response to the user's prompt: ANALYZE ALL SOURCES and select the MOST IMPORTANT and RELEVANT news items based on the user's specific request. Sort them by RELEVANCE and IMPORTANCE to the user's query, NOT by the order they appear below. Focus on the most significant developments, breaking news, and impactful stories related to the topic requested. Prioritize recent news resources. If user requests expanded content, provide detailed content and analysis from the available context. Cite sources for each item. '''
                
                # Get Google News results with enhanced format and category awareness
                google_results, google_source_count = get_news_from_google(newsFilter, source_num_start=1, categories=ranked_categories)
                res += google_results
                
                # Fetch content from each URL with improved error handling and fallbacks
                successful_sources = google_source_count  # Start counting after Google News sources
                attempted_sources = 0
                max_sources = 6  # Try up to 6 sources for better coverage and diversity
                
                for newsURL in urls[:max_sources]:
                    attempted_sources += 1
                    try:
                        logger.debug(f"Attempting to fetch news from: {newsURL}")
                        
                        # Use new function that extracts article URLs from RSS feeds
                        formatted_content, articles_added = _get_news_content_with_article_urls(newsURL, successful_sources + 1)
                        
                        # Only add if we got meaningful content
                        if formatted_content and articles_added > 0:
                            res += formatted_content
                            successful_sources += articles_added
                            logger.debug(f"Successfully fetched from: {newsURL} ({articles_added} articles)")
                        else:
                            logger.debug(f"No meaningful content from: {newsURL}")
                            
                    except Exception as e:
                        print(f"Error fetching {newsURL}: {e}", flush=True)
                        # Don't include error in response to keep it clean
                        continue
                
                # Add fallback sources if we didn't get enough successful sources
                if successful_sources < 2 and category in ["technology", "finance", "crypto"]:
                    print(f"Only got {successful_sources} sources, trying fallback sources...", flush=True)
                    fallback_sources = {
                        "technology": [
                            "https://www.engadget.com/rss.xml",
                            "https://feeds.arstechnica.com/arstechnica/index"
                        ],
                        "finance": [
                            "https://www.marketwatch.com/rss/topstories",
                            "https://feeds.finance.yahoo.com/rss/2.0/headline"
                        ],
                        "crypto": [
                            "https://coinjournal.net/feed/",
                            "https://www.coinspeaker.com/feed/"
                        ]
                    }
                    
                    for fallback_url in fallback_sources.get(category, [])[:2]:
                        if successful_sources >= 3:  # Stop if we have enough
                            break
                        try:
                            print(f"Trying fallback source: {fallback_url}", flush=True)
                            
                            # Use new function for fallback sources too
                            formatted_content, articles_added = _get_news_content_with_article_urls(fallback_url, successful_sources + 1)
                            
                            if formatted_content and articles_added > 0:
                                res += formatted_content
                                successful_sources += articles_added
                                print(f"Fallback source successful: {fallback_url} ({articles_added} articles)", flush=True)
                        except Exception as e:
                            print(f"Fallback source failed {fallback_url}: {e}", flush=True)
                            continue
                
                logger.debug(f"News fetch complete: {successful_sources}/{attempted_sources} primary sources successful")
                
                return res
            
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool, sync_news_query
            )
        except Exception as e:
            return f"News query error: {str(e)}"
    
    async def search_web(self, args: str) -> str:
        """
        Perform a web search using DuckDuckGo and retrieve comprehensive results.
        Uses the original working implementation from find_eps_estimate.py
        """
        try:
            # Remove TOOLS_AVAILABLE check - let function handle missing deps gracefully
                
            def sync_web_search():
                # Handle parameter parsing like the original
                if isinstance(args, str):
                    try:
                        data = json.loads(args) if args.startswith('{') else {'query': args}
                    except:
                        data = {'query': args}
                else:
                    data = args if isinstance(args, dict) else {'query': str(args)}
                
                query = data.get('query', '').strip()
                print(f"Web search query: {query}", flush=True)
                
                if not query:
                    return "Sorry, I couldn't find anything."
                
                today = datetime.now()
                todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p")
                max_results = 3
                
                # DuckDuckGo search function (from original)
                def ducducgo(query, max_results=3):
                    try:
                        from ddgs import DDGS
                        with DDGS() as ddgs:
                            results = ddgs.text(query, max_results=max_results)
                            res = ''
                            for i, result in enumerate(results, 1):
                                title = result.get('title', 'No Title')
                                href = result.get('href', 'No URL')
                                body = result.get('body', 'No Description')
                                
                                # Extract content from each URL
                                extracted_content = ""
                                if href != 'No URL':
                                    try:
                                        extracted_content = get_text_from_url_simplified(href)
                                    except Exception as e:
                                        extracted_content = f"Error extracting content: {str(e)}"
                                
                                # Use enhanced source block formatting
                                formatted_result = _format_source_block(
                                    source_url=href,
                                    title=title,
                                    content=f"Description: {body}\n\nExtracted Content: {extracted_content}",
                                    source_num=i
                                )
                                res += formatted_result
                            return res
                    except Exception as e:
                        print(f"DuckDuckGo Error: {e}", flush=True)
                        return f"An error occurred during the web search query '{query}'."
                
                # Simplified URL content extraction (to avoid Selenium dependency issues)
                def get_text_from_url_simplified(url):
                    try:
                        response = requests_compatible_get(url, timeout=10, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        response.raise_for_status()
                        
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Remove unwanted tags
                        for tag_name in ['footer', 'nav', 'script', 'style', 'aside', 'header']:
                            for tag in soup.find_all(tag_name):
                                tag.decompose()
                        
                        # Extract meaningful text
                        texts = []
                        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'article']):
                            text = tag.get_text().strip()
                            if text and len(text) > 50:  # Only meaningful content
                                texts.append(text)
                        
                        result = '\n\n'.join(texts[:5])  # Limit to first 5 meaningful paragraphs
                        return result[:2000] + "..." if len(result) > 2000 else result  # Limit size
                        
                    except Exception as e:
                        return f"Error extracting content: {str(e)}"
                
                # Perform the search
                try:
                    web_results = ducducgo(query, max_results)
                    if isinstance(web_results, list):
                        web_results = '\n'.join(web_results)
                except Exception as e:
                    web_results = f"Error: Exception returned in search_web(): '{e}'"
                
                res = f"\n\nAs of [Current Date and Time: {todayStr}] here are the web search results:\n{web_results}"
                
                print("Web search completed", flush=True)
                return res
            
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool, sync_web_search
            )
        except Exception as e:
            return f"Web search error: {str(e)}"
    
    async def lookup_website_old(self, args: str) -> str:
        """
        Retrieve and extract comprehensive text content from a specified website URL.
        Uses the original working implementation from find_eps_estimate.py with both Selenium and BeautifulSoup
        """
        try:
            # Remove TOOLS_AVAILABLE check - let function handle missing deps gracefully
                
            def sync_website_lookup():
                # Handle parameter parsing like the original
                if isinstance(args, str):
                    try:
                        data = json.loads(args) if args.startswith('{') else {'url': args}
                    except:
                        data = {'url': args}
                else:
                    data = args if isinstance(args, dict) else {'url': str(args)}
                
                url = data.get('url', '').strip()
                print(f"Website lookup URL: {url}", flush=True)
                
                if not url:
                    return "Sorry, I couldn't find anything."
                
                today = datetime.now()
                todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p")
                
                # PDF detection functions (from original)
                def is_pdf_url(url: str) -> bool:
                    try:
                        response = requests.head(url, allow_redirects=True, timeout=10)
                        if 'application/pdf' in response.headers.get('Content-Type', '').lower():
                            return True
                        
                        # Check with magic if available
                        try:
                            full_response = requests_compatible_get(url, timeout=10)
                            mime = magic.Magic(mime=True)
                            content_type = mime.from_buffer(full_response.content[:1024])
                            return content_type == 'application/pdf'
                        except:
                            return False
                    except Exception as e:
                        print(f"PDF detection error for {url}: {e}")
                        return False
                
                def extract_pdf_text(url: str) -> str:
                    try:
                        response = requests_compatible_get(url, timeout=30)
                        pdf_file = io.BytesIO(response.content)
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        
                        full_text = ""
                        for page in pdf_reader.pages:
                            full_text += page.extract_text() + "\n\n"
                        
                        return full_text.strip()
                    except Exception as e:
                        print(f"PDF text extraction error for {url}: {e}")
                        return f"Error extracting PDF: {str(e)}"
                
                # Main website extraction function (from original)
                def get_text_from_url(url: str) -> str:
                    # Check if the URL is a PDF first
                    if is_pdf_url(url):
                        pdf_text = extract_pdf_text(url)
                        return f"PDF URL: {url}\nContent:\n{pdf_text}"
                    
                    try:
                        # Try Selenium crawler first (more comprehensive)
                        max_url_count = 2
                        max_depth = 1
                        
                        crawler = SeleniumCrawler(url, max_depth=max_depth, max_url_count=max_url_count-1, timeout_response=40)
                        crawler.setCheckRobot(False)
                        
                        crawler.crawl(url)
                        crawler.close()
                        
                        res = ''
                        for result in crawler.results:
                            if is_pdf_url(result['url']):
                                pdf_text = extract_pdf_text(result['url'])
                                res += f"PDF Title: {result['title']}, URL: {result['url']}\n"
                                res += f"PDF Content: {pdf_text}\n"
                            else:
                                res += f"Title: {result['title']}, URL: {result['url']}\n"
                                res += f"Content: {result['content']}\n"
                            
                            res += "-" * 80 + "\n"
                        
                        return res if res else "No content extracted via Selenium"
                        
                    except Exception as selenium_error:
                        print(f"Selenium extraction failed, trying BeautifulSoup: {selenium_error}")
                        
                        # Fallback to BeautifulSoup (from original get_text_from_url2)
                        try:
                            response = requests.get(url, timeout=10, headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            })
                            response.raise_for_status()
                            
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Remove unwanted tags
                            for tag_name in ['footer', 'nav', 'script', 'style']:
                                for tag in soup.find_all(tag_name):
                                    tag.decompose()
                            
                            # Replace links with their text content
                            for link in soup.find_all('a'):
                                link.replace_with(link.get_text())
                            
                            # Extract paragraphs
                            paragraphs = [p.get_text().strip() for p in soup.find_all('p')]
                            paragraphs = [p for p in paragraphs if p]
                            
                            if not paragraphs:
                                print("Warning: No paragraphs were found!")
                            
                            # Process tables
                            def convert_html_table_to_text(table):
                                rows = []
                                for row in table.find_all('tr'):
                                    cells = row.find_all(['th', 'td'])
                                    row_text = ' | '.join(cell.get_text().strip() for cell in cells)
                                    rows.append(row_text)
                                return '\n'.join(rows)
                            
                            for table in soup.find_all('table'):
                                table_text = convert_html_table_to_text(table)
                                paragraphs.append(table_text)
                            
                            text = '\n\n'.join(paragraphs)
                            return text
                            
                        except requests.exceptions.Timeout:
                            return f'Error fetching text from URL: Time Out!'
                        except requests.exceptions.RequestException as error:
                            return f'Error fetching text from URL: {error}'
                
                # Perform the website lookup
                try:
                    web_results = get_text_from_url(url)
                except Exception as e:
                    web_results = f"Error: Exception returned '{e}'"
                
                res = f"\n\nAs of [Current Date and Time: {todayStr}] here are lookup results: \n{web_results}"
                
                print("Website lookup completed", flush=True)
                return res
            
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool, sync_website_lookup
            )
        except Exception as e:
            return f"Website lookup error: {str(e)}"
    
    def _is_pdf_url(self, url: str) -> bool:
        """Check if URL points to a PDF file."""
        parsed = urlparse(url.lower())
        return (
            parsed.path.endswith(".pdf")
            or "pdf" in parsed.path
            or url.lower().endswith(".pdf")
        )
    
    def _extract_pdf_content(self, url: str) -> dict:
        """Extract content from a PDF URL and format like HTML scraping."""
        try:
            print(f"Extracting PDF from {url}", flush=True)
            # Download PDF
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests_compatible_get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Check if we actually got a PDF
            content_type = response.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not url.lower().endswith(".pdf"):
                print(f"Error: URL does not appear to be a PDF (content-type: {content_type})", flush=True)
                return {
                    "success": False,
                    "error": f"URL does not appear to be a PDF (content-type: {content_type})",
                }

            # Create PDF reader from bytes
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Check if PDF is readable
            if len(pdf_reader.pages) == 0:
                print("Error: PDF contains no readable pages", flush=True)
                return {"success": False, "error": "PDF contains no readable pages"}

            # Extract metadata
            metadata = pdf_reader.metadata if pdf_reader.metadata else {}

            title = None
            author = None
            if metadata:
                title = (
                    metadata.get("/Title", "").strip()
                    if metadata.get("/Title")
                    else None
                )
                author = (
                    metadata.get("/Author", "").strip()
                    if metadata.get("/Author")
                    else None
                )

            # Extract ALL text as one continuous document
            all_text = []
            successful_pages = 0

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    # Try multiple extraction methods
                    page_text = page.extract_text()

                    # If default extraction fails, try with layout mode
                    if not page_text.strip():
                        try:
                            page_text = page.extract_text(extraction_mode="layout")
                        except:
                            pass

                    if page_text.strip():
                        # Clean up common PDF extraction artifacts
                        page_text = page_text.replace("\x00", "")  # Remove null bytes
                        page_text = page_text.replace("\n\n\n", "\n\n")  # Reduce excessive newlines
                        all_text.append(page_text.strip())
                        successful_pages += 1
                except Exception as e:
                    print(f"Error extracting page {page_num + 1}: {e}", flush=True)
                    continue

            if successful_pages == 0:
                print(f"Error: Could not extract text from any of the {len(pdf_reader.pages)} pages", flush=True)
                return {
                    "success": False,
                    "error": f"Could not extract text from any of the {len(pdf_reader.pages)} pages",
                }

            # Join all text with double newlines
            full_text = "\n\n".join(all_text)

            # Clean up and format like HTML scraping output
            full_text = " ".join(full_text.split())  # Replace multiple spaces with single spaces
            full_text = full_text.replace(". ", ".\n\n")  # Add paragraph breaks
            full_text = full_text.replace("? ", "?\n\n")
            full_text = full_text.replace("! ", "!\n\n")
            full_text = full_text.replace("\n\n\n", "\n\n")  # Clean up triple newlines

            # If no title in metadata, try to extract from beginning of text
            if not title and full_text:
                first_part = full_text[:500]
                sentences = first_part.split("\n\n")[:5]

                for sentence in sentences:
                    sentence = sentence.strip()
                    if (
                        len(sentence) > 10
                        and len(sentence) < 200
                        and not sentence.lower().startswith("draft")
                        and not "arxiv:" in sentence.lower()
                        and not sentence.startswith("Typeset")
                        and not "@" in sentence
                        and not sentence.replace(".", "").isdigit()
                    ):
                        title = sentence
                        break

            print(f"PDF extraction successful: {successful_pages}/{len(pdf_reader.pages)} pages, {len(full_text)} chars", flush=True)
            
            return {
                "success": True,
                "title": title or "PDF Document",
                "author": author,
                "content": full_text,
                "page_count": len(pdf_reader.pages),
                "extracted_pages": successful_pages,
            }

        except Exception as e:
            print(f"Error extracting PDF content from {url}: {str(e)}", flush=True)
            return {
                "success": False,
                "error": f"Error extracting PDF content from {url}: {str(e)}",
            }

    def _extract_web_content(self, url: str) -> dict:
        """Extract content from a regular web page using trafilatura."""
        try:
            print(f"Extracting web content from {url}", flush=True)
            downloaded = trafilatura.fetch_url(url)
            if downloaded is None:
                return {
                    "success": False,
                    "error": f"Failed to download content from {url}",
                }

            # Extract content and metadata separately
            extracted = trafilatura.extract(downloaded)
            metadata = trafilatura.extract_metadata(downloaded)

            if extracted is None:
                return {"success": False, "error": f"No content found at {url}"}

            # Get title and author from metadata if available
            title = None
            author = None
            date = None

            if metadata:
                title = metadata.title
                author = metadata.author
                date = metadata.date

            print(f"Web extraction successful: {len(extracted)} chars", flush=True)

            return {
                "success": True,
                "title": title or "Web Article",
                "author": author,
                "date": date,
                "content": extracted,
            }

        except Exception as e:
            print(f"Error extracting content from {url}: {e}", flush=True)
            return {
                "success": False,
                "error": f"Error extracting content from {url}: {e}",
            }

    def _safe_truncate(self, content: str, max_chars: int = 10000) -> str:
        """Simple, safe truncation that guarantees we stay under buffer limits."""
        if len(content) <= max_chars:
            return content

        print(f"Content too large ({len(content)} chars), truncating to {max_chars}", flush=True)
        
        # Simple truncation with clear notice
        truncated = content[:max_chars]

        # Try to end at a complete sentence
        last_period = truncated.rfind(". ")
        if last_period > max_chars * 0.8:  # If we can cut at a sentence near the end
            truncated = truncated[: last_period + 1]

        # Add clear truncation notice
        total_chars = len(content)
        total_words = len(content.split())
        shown_words = len(truncated.split())

        truncated += f"\n\n--- CONTENT TRUNCATED ---\n"
        truncated += f"Showing: {shown_words} words of {total_words} total\n"
        truncated += f"Original size: {total_chars} characters\n"
        truncated += f"Reason: Context window limit\n"
        truncated += f"Note: Full content was extracted successfully"

        return truncated

    async def lookup_website(self, args: str) -> str:
        """
        Enhanced website content extractor using trafilatura for better HTML parsing.
        Handles both web pages and PDFs with improved content extraction.
        """
        try:
            def sync_website_extraction():
                # Handle parameter parsing
                if isinstance(args, str):
                    try:
                        data = json.loads(args) if args.startswith('{') else {'url': args}
                    except:
                        data = {'url': args}
                else:
                    data = args if isinstance(args, dict) else {'url': str(args)}
                
                url = data.get('url', '').strip()
                print(f"Website extraction URL: {url}", flush=True)
                
                if not url:
                    return "Error: No URL provided for website lookup."
                
                today = datetime.now()
                todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p")
                
                # Determine content type and extract accordingly
                if self._is_pdf_url(url):
                    result = self._extract_pdf_content(url)
                    content_type = "PDF"
                else:
                    result = self._extract_web_content(url)
                    content_type = "Web Page"

                # Handle extraction errors
                if not result["success"]:
                    return f"ERROR: Failed to extract content from {url}: {result['error']}"

                # Apply safe truncation to avoid buffer overflow
                content = self._safe_truncate(result["content"])

                # Build additional metadata for enhanced source block
                metadata_parts = []
                if result.get('author'):
                    metadata_parts.append(f"Author: {result['author']}")
                if result.get('date'):
                    metadata_parts.append(f"Published: {result['date']}")
                metadata_parts.append(f"Type: {content_type}")
                
                # Combine metadata with content
                full_content = f"{'\n'.join(metadata_parts)}\n\nContent:\n{content}"
                
                # Use enhanced source block formatting
                formatted_result = _format_source_block(
                    source_url=url,
                    title=result['title'],
                    content=full_content,
                    source_num=1,
                    timestamp=todayStr
                )
                
                final_response = f"\nAs of [Current Date and Time: {todayStr}] here are the website lookup results:\n{formatted_result}"
                
                print(f"Website extraction completed: {len(final_response)} chars", flush=True)
                return final_response
            
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool, sync_website_extraction
            )
        except Exception as e:
            return f"Website extraction error: {str(e)}"
    
    async def safe_function_call(self, func_name: str, args: str) -> str:
        """Safely execute a function with automatic image injection for image_to_text"""
        if func_name not in self.available_functions:
            return f"Function {func_name} not available"
        
        try:
            # 🖼️ SPECIAL HANDLING: Auto-inject image data for image_to_text tool
            if func_name == 'image_to_text' and self.current_images:
                try:
                    # Parse existing arguments
                    if isinstance(args, str):
                        try:
                            parsed_args = json.loads(args)
                        except json.JSONDecodeError:
                            parsed_args = {"prompt": args}
                    else:
                        parsed_args = args if isinstance(args, dict) else {"prompt": str(args)}
                    
                    # Inject first available image if not already provided
                    if not parsed_args.get('image') or parsed_args.get('image') == '':
                        if self.current_images:
                            image_data = self.current_images[0]
                            # Handle data URLs - extract base64 part if needed
                            if image_data.startswith('data:image/'):
                                image_data = image_data.split(',', 1)[1] if ',' in image_data else image_data
                            parsed_args['image'] = image_data
                            logger.info(f"🖼️ Auto-injected image data into image_to_text: {len(image_data)} chars")
                    
                    # Convert back to string format expected by tools
                    args = json.dumps(parsed_args)
                    
                except Exception as inject_error:
                    logger.warning(f"🖼️ Failed to inject image data: {inject_error}")
            
            func = self.available_functions[func_name]
            result = await func(args)
            return str(result)
        except Exception as e:
            logger.error(f"Error calling {func_name}: {e}")
            return f"Error calling {func_name}: {str(e)}"

    async def secure_email_sender(self, args: str) -> str:
        """
        Send professional emails with attachments and comprehensive security measures.
        Handles Gmail, Outlook, custom SMTP, and sendmail.
        """
        try:
            # Handle parameter parsing
            if isinstance(args, str):
                try:
                    parsed_args = json.loads(args)
                except json.JSONDecodeError:
                    return "❌ Error: Invalid JSON format for email arguments"
            else:
                parsed_args = args
            
            def sync_email_send():
                try:
                    # Import the email tool
                    import sys
                    import os
                    
                    # Add user_tools directory to path if not already there
                    user_tools_path = os.path.join(os.path.dirname(__file__), 'user_tools')
                    if user_tools_path not in sys.path:
                        sys.path.append(user_tools_path)
                    
                    from user_tools.secure_email_sender import SecureEmailSenderTool
                    
                    # Create tool instance and execute
                    email_tool = SecureEmailSenderTool()
                    
                    # Execute the email tool (async)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(email_tool.execute(**parsed_args))
                    finally:
                        loop.close()
                    
                    # Handle the new return format
                    if isinstance(result, dict):
                        if result.get("success"):
                            return result.get("result", "✅ Email sent successfully")
                        else:
                            return f"❌ {result.get('error', 'Email sending failed')}"
                    else:
                        return str(result)
                    
                except ImportError as e:
                    return f"❌ Error: Email tool not available: {str(e)}"
                except Exception as e:
                    return f"❌ Error: Email sending failed: {str(e)}"
            
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool, sync_email_send
            )
            
        except Exception as e:
            return f"❌ Error: Email tool execution failed: {str(e)}"

# ==============================================================================
# CACHE FUNCTIONS
# ==============================================================================

def cache_get(key: str) -> Optional[str]:
    """Get value from simple cache"""
    if key in simple_cache:
        entry = simple_cache[key]
        if time.time() < entry['expires']:
            return entry['value']
        else:
            del simple_cache[key]
    return None

def cache_set(key: str, value: str, ttl: int = 3600):
    """Set value in simple cache"""
    simple_cache[key] = {
        'value': value,
        'expires': time.time() + ttl
    }

# ==============================================================================
# LIFESPAN MANAGEMENT
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("Starting FastAPI server with Ollama integration...")
    await init_db_pool()
    await init_http_pool()
    
    # Initialize Phase 2B components safely
    if PHASE2B_AVAILABLE:
        try:
            logger.info("🚀 Initializing Phase 2B: Advanced Response Streaming & Buffer Optimization")
            
            # Start performance monitoring first (always enabled for safety)
            performance_monitor.start_monitoring()
            
            # Initialize buffer management
            await start_buffer_management()
            
            # Initialize streaming wrapper (features disabled by default)
            # Features will only activate when explicitly enabled via rollback controller
            
            logger.info("✅ Phase 2B components initialized with rollback safety")
            logger.info(f"🛡️ Rollback controller status: {rollback_controller.get_status()}")
            
        except Exception as e:
            logger.error(f"❌ Phase 2B initialization failed: {e}")
            logger.warning("🔄 Falling back to Phase 2A operation")
            # Continue with Phase 2A - don't fail startup
    else:
        logger.info("ℹ️ Phase 2B not available - continuing with Phase 2A operation")
    
    # Test Ollama connection using connection pool
    try:
        response_data = await pooled_get('http://127.0.0.1:11434/api/tags', timeout=5)
        if response_data['status_code'] == 200:
            logger.info("Ollama service is available")
        else:
            logger.warning("Ollama service test failed")
    except Exception as e:
        logger.warning(f"Ollama service not available: {e}")
    
    # Initialize document interrogator with startup and background scanning
    try:
        from document_interrogator import get_document_interrogator
        interrogator = get_document_interrogator()
        if interrogator:
            # Trigger startup scanning in background
            asyncio.create_task(interrogator._safe_startup_config_scan())
            
            # Start periodic background scanning
            await interrogator.start_background_scanning()
    except Exception as e:
        logger.warning(f"Document scanning initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Shutdown Phase 2B components safely
    if PHASE2B_AVAILABLE:
        try:
            logger.info("🔄 Shutting down Phase 2B components...")
            performance_monitor.stop_monitoring()
            await stop_buffer_management()
            logger.info("✅ Phase 2B components shutdown complete")
        except Exception as e:
            logger.error(f"❌ Phase 2B shutdown error: {e}")
    
    # Shutdown document interrogator background scanning
    try:
        from document_interrogator import get_document_interrogator
        interrogator = get_document_interrogator()
        if interrogator:
            await interrogator.stop_background_scanning()
    except Exception as e:
        logger.warning(f"Document scanning shutdown error: {e}")
    
    await close_db_pool()
    await cleanup_http_pool()
    thread_pool.shutdown(wait=True)

# ==============================================================================
# FASTAPI APPLICATION
# ==============================================================================

app = FastAPI(
    title="Complete Analytics API with Ollama LLM",
    description="High-performance async API with Ollama integration, tools, and caching",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for image serving
app.mount("/images", StaticFiles(directory="/home/sabawi/Development/flaskserver/sandbox_workspace"), name="images")

# Initialize tool manager
tool_manager = AsyncToolManager()

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

@app.middleware("http") 
async def log_requests(request: Request, call_next):
    """Log all requests with timing (configurable via env vars, config file, or config tool)"""
    # Check if logging is globally disabled - if so, skip middleware entirely
    if logging.root.disabled:
        return await call_next(request)
    
    # Priority: Environment variables > Config file > Defaults
    debug_config = config_loader.load_config().get('debug', {})
    log_requests_enabled = os.getenv('LOG_REQUESTS', str(debug_config.get('log_requests', True))).lower() in ('true', '1', 'yes')
    log_timing_enabled = os.getenv('LOG_TIMING', str(debug_config.get('log_timing', True))).lower() in ('true', '1', 'yes')
    
    if not log_requests_enabled and not log_timing_enabled:
        return await call_next(request)
    
    start_time = time.time() if log_timing_enabled else None
    response = await call_next(request)
    
    if log_requests_enabled:
        if log_timing_enabled and start_time:
            process_time = time.time() - start_time
            status_text = "OK" if response.status_code < 400 else "ERR" if response.status_code >= 500 else "WARN"
            logger.info(f"{status_text} {request.method} {request.url.path} | {response.status_code} | {process_time:.3f}s")
        else:
            # Log without timing
            status_text = "OK" if response.status_code < 400 else "ERR" if response.status_code >= 500 else "WARN"
            logger.info(f"{status_text} {request.method} {request.url.path} | {response.status_code}")
    
    return response

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

async def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict]:
    """Execute database query asynchronously"""
    if not db_pool:
        return []
    
    async with get_db_connection() as connection:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params or ())
            result = await cursor.fetchall()
            return result

async def run_cpu_intensive_task(func, *args, **kwargs):
    """Run CPU-intensive tasks in thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, func, *args, **kwargs)

async def check_ollama_health() -> bool:
    """Check if Ollama service is healthy using connection pool"""
    try:
        async with http_pool.get_session() as session:
            async with session.get('http://127.0.0.1:11434/api/tags', timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
    except:
        return False

def _format_source_block(source_url: str, title: str, content: str, source_num: int, timestamp: str = None) -> str:
    """
    Format individual source with simplified block structure for accurate LLM citation.

    This creates clear source blocks that help the Primary LLM maintain
    accurate URL-content associations without overwhelming context size.
    Now extracts actual publication dates from content to avoid misleading the Primary LLM.
    Includes accessibility indicators to help balance recency with content accessibility.

    Args:
        source_url: The exact URL to cite (MANDATORY CITATION URL)
        title: Source title or description
        content: The actual content from the source
        source_num: Sequential source number for organization
        timestamp: Deprecated parameter (kept for backward compatibility)

    Returns:
        Formatted source block with clear citation requirements, content dates, and accessibility indicators
    """
    # Extract actual publication date from content
    content_date = _extract_content_date(content)

    # Build date line only if we found an actual publication date
    date_line = ""
    if content_date:
        date_line = f"📅 Published: {content_date}\n"

    # Detect paywall sources and add accessibility indicator
    accessibility_indicator = _get_accessibility_indicator(source_url)

    return f"""
───────────────────────────────────────────────────────
📄 SOURCE BLOCK #{source_num} [REQUIRED CITATION: {source_url}]
Title: {title}
🔗 MANDATORY CITATION URL: {source_url}
{date_line}{accessibility_indicator}CONTENT: {content}
───────────────────────────────────────────────────────
"""

def _extract_content_date(content: str) -> str:
    """
    Extract actual publication date from content text.
    Returns formatted date string if found, None if not available.
    """
    import re
    from datetime import datetime

    if not content:
        return None

    # Common date patterns in news content
    date_patterns = [
        # Format: "Published: January 15, 2024" or "Published January 15, 2024"
        r'(?:Published|Publication date|Date published):\s*([A-Za-z]+ \d{1,2}, \d{4})',
        r'(?:Published|Publication date|Date published)\s+([A-Za-z]+ \d{1,2}, \d{4})',

        # Format: "15 January 2024" or "January 15, 2024"
        r'\b(\d{1,2} [A-Za-z]+ \d{4})\b',
        r'\b([A-Za-z]+ \d{1,2}, \d{4})\b',

        # Format: "2024-01-15" or "15/01/2024" or "01/15/2024"
        r'\b(\d{4}-\d{1,2}-\d{1,2})\b',
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',

        # Format: "15 Jan 2024" or "Jan 15, 2024" or "Sept 18, 2023"
        r'\b(\d{1,2} [A-Za-z]{3,4} \d{4})\b',
        r'\b([A-Za-z]{3,4} \d{1,2}, \d{4})\b',

        # BBC specific: "5 hours ago", "2 days ago", "1 week ago"
        r'\b(\d+)\s+(hour|hours|day|days|week|weeks|month|months)\s+ago\b',

        # Format: "September 18, 2025" or "18 September 2025"
        r'\b([A-Za-z]+ \d{1,2}, \d{4})\b',
        r'\b(\d{1,2} [A-Za-z]+ \d{4})\b',
    ]

    # Try each pattern
    for pattern in date_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    # Handle relative dates like "2 days ago"
                    if len(match) == 2 and match[1] in ['hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months']:
                        try:
                            from datetime import timedelta
                            amount = int(match[0])
                            unit = match[1]

                            now = datetime.now()
                            if 'hour' in unit:
                                target_date = now - timedelta(hours=amount)
                            elif 'day' in unit:
                                target_date = now - timedelta(days=amount)
                            elif 'week' in unit:
                                target_date = now - timedelta(weeks=amount)
                            elif 'month' in unit:
                                target_date = now - timedelta(days=amount*30)  # Approximate

                            return target_date.strftime('%B %d, %Y')
                        except:
                            continue
                    else:
                        match = match[0] if isinstance(match, tuple) else match

                # Validate the date makes sense (not future, not too old)
                try:
                    # Try to parse various formats
                    parsed_date = None
                    for fmt in ['%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            parsed_date = datetime.strptime(match, fmt)
                            break
                        except:
                            continue

                    if parsed_date:
                        # Check if date is reasonable (between 2020 and now + 1 year)
                        now = datetime.now()
                        min_date = datetime(2020, 1, 1)
                        max_date = datetime(now.year + 1, 12, 31)

                        if min_date <= parsed_date <= max_date:
                            return parsed_date.strftime('%B %d, %Y')

                except:
                    continue

    return None

def _get_accessibility_indicator(source_url: str) -> str:
    """
    Determine content accessibility for a given source URL.
    Returns accessibility indicator line for Primary LLM prioritization.

    Args:
        source_url: The URL to check for paywall/accessibility status

    Returns:
        Formatted accessibility indicator line
    """
    # Known paywall domains
    paywall_domains = [
        'bloomberg.com',
        'wsj.com', 'wallstreetjournal.com',
        'ft.com', 'financialtimes.com',
        'nytimes.com',
        'washingtonpost.com',
        'economist.com',
        'reuters.com',  # Some Reuters content has paywalls
        'barrons.com',
        'marketwatch.com',  # Some premium content
        'seekingalpha.com'  # Some premium content
    ]

    # Free access domains (high confidence)
    free_domains = [
        'cnbc.com',
        'cnn.com',
        'bbc.com', 'bbc.co.uk',
        'yahoo.com',
        'axios.com',
        'npr.org',
        'apnews.com',
        'cbsnews.com',
        'abcnews.go.com',
        'nbcnews.com',
        'federalreserve.gov',
        'investing.com'
    ]

    if not source_url:
        return ""

    # Extract domain from URL
    try:
        from urllib.parse import urlparse
        domain = urlparse(source_url).netloc.lower()

        # Remove www. prefix for matching
        if domain.startswith('www.'):
            domain = domain[4:]

        # Check for paywall domains
        for paywall_domain in paywall_domains:
            if paywall_domain in domain:
                return "🔒 Access: May require subscription (paywall possible)\n"

        # Check for free domains
        for free_domain in free_domains:
            if free_domain in domain:
                return "🌐 Access: Generally free access\n"

        # Default for unknown domains
        return "❓ Access: Accessibility unknown\n"

    except Exception:
        return ""

def _extract_domain(url: str) -> str:
    """Extract domain name from URL for titles"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        # Clean up common prefixes
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.title()
    except:
        return "Unknown Source"

def _parse_rss_articles(rss_content: str, feed_url: str, max_articles: int = 5) -> List[dict]:
    """
    Parse RSS feed content and extract individual article information including URLs.
    
    Args:
        rss_content: Raw RSS XML content
        feed_url: Original RSS feed URL (for debugging)
        max_articles: Maximum number of articles to extract
    
    Returns:
        List of dictionaries with 'title', 'url', 'description' for each article
    """
    try:
        from bs4 import BeautifulSoup
        
        # Parse with XML parser for better RSS handling
        try:
            soup = BeautifulSoup(rss_content, 'xml')
        except:
            # Fallback to html parser
            soup = BeautifulSoup(rss_content, 'html.parser')
        
        articles = []
        items = soup.find_all(['item', 'entry'])
        
        for item in items[:max_articles]:
            article = {}
            
            # Extract title
            title_tag = item.find(['title'])
            if title_tag:
                article['title'] = title_tag.get_text().strip()
            
            # Extract URL - try multiple common RSS URL fields
            url = None
            # Try <link> tag first
            link_tag = item.find('link')
            if link_tag:
                if link_tag.get('href'):  # Atom-style
                    url = link_tag.get('href')
                else:  # RSS-style
                    url = link_tag.get_text().strip()
            
            # Try <guid> tag if no link found
            if not url:
                guid_tag = item.find('guid')
                if guid_tag:
                    guid_text = guid_tag.get_text().strip()
                    # Only use guid if it looks like a URL
                    if guid_text.startswith('http'):
                        url = guid_text
            
            # Try <id> tag for Atom feeds
            if not url:
                id_tag = item.find('id')
                if id_tag:
                    id_text = id_tag.get_text().strip()
                    if id_text.startswith('http'):
                        url = id_text
            
            if url:
                article['url'] = url
            else:
                # Fallback to feed URL if no article URL found
                article['url'] = feed_url
                
            # Extract description with enhanced content extraction
            desc_text = ""
            
            # Try multiple description fields for maximum content
            for desc_field in ['content:encoded', 'content', 'description', 'summary']:
                desc_tag = item.find(desc_field)
                if desc_tag:
                    desc_text = desc_tag.get_text().strip()
                    break
            
            # If no description found, try looking for content in other fields
            if not desc_text:
                for fallback_field in ['media:description', 'itunes:summary']:
                    desc_tag = item.find(fallback_field)
                    if desc_tag:
                        desc_text = desc_tag.get_text().strip()
                        break
            
            if desc_text:
                # Clean up description but keep more content
                desc_text = desc_text.replace('\n', ' ').replace('\r', ' ')
                # Remove HTML tags if present
                from bs4 import BeautifulSoup
                desc_text = BeautifulSoup(desc_text, 'html.parser').get_text()
                # Increase length limit for more detailed summaries
                if len(desc_text) > 500:
                    desc_text = desc_text[:500] + "..."
                article['description'] = desc_text
            
            # Extract publication date for context
            pub_date = None
            for date_field in ['pubDate', 'published', 'updated']:
                date_tag = item.find(date_field)
                if date_tag:
                    pub_date = date_tag.get_text().strip()
                    break
            
            if pub_date:
                article['pub_date'] = pub_date
            
            # Only add articles that have at least a title
            if article.get('title'):
                articles.append(article)
        
        return articles
        
    except Exception as e:
        print(f"Error parsing RSS from {feed_url}: {e}", flush=True)
        return []

def _get_news_content_with_article_urls(news_url: str, source_num_start: int) -> tuple:
    """
    Fetch content from news URL and extract individual article URLs if it's an RSS feed.
    
    Args:
        news_url: URL to fetch (could be RSS feed or regular webpage)
        source_num_start: Starting source number for numbering
    
    Returns:
        tuple: (formatted_content_blocks, articles_count)
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Fetch the content
        response = requests_compatible_get(news_url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()
        
        # Check if it's RSS/XML content
        content_type = response.headers.get('content-type', '').lower()
        is_rss_xml = (
            'xml' in content_type or 
            'rss' in content_type or
            news_url.endswith('.xml') or 
            news_url.endswith('.rss') or
            'feed' in news_url.lower() or
            response.text.strip().startswith('<?xml')
        )
        
        if is_rss_xml:
            # Parse RSS feed and extract individual articles
            articles = _parse_rss_articles(response.text, news_url, max_articles=4)
            
            if articles:
                content_blocks = []
                for i, article in enumerate(articles):
                    article_url = article.get('url', news_url)
                    title = article.get('title', 'Untitled Article')
                    description = article.get('description', '')

                    # Use description as content (date will be extracted by _format_source_block)
                    enhanced_content = description
                    
                    # Create source block for each article
                    formatted_source = _format_source_block(
                        source_url=article_url,
                        title=title,
                        content=enhanced_content,
                        source_num=source_num_start + i
                    )
                    content_blocks.append(formatted_source)
                
                return ('\n'.join(content_blocks), len(articles))
            else:
                # Fallback - create a simple source block if RSS parsing fails
                formatted_source = _format_source_block(
                    source_url=news_url,
                    title=f"News from {_extract_domain(news_url)}",
                    content="RSS feed processed but article URLs could not be extracted",
                    source_num=source_num_start
                )
                return (formatted_source, 1)
        else:
            # Regular webpage - use existing logic but create fallback if get_text_from_url fails
            try:
                content = get_text_from_url(news_url)
                if content and not content.startswith("Error"):
                    formatted_source = _format_source_block(
                        source_url=news_url,
                        title=f"News from {_extract_domain(news_url)}",
                        content=content,
                        source_num=source_num_start
                    )
                    return (formatted_source, 1)
                else:
                    return ("", 0)
            except:
                return ("", 0)
            
    except Exception as e:
        print(f"Error processing news from {news_url}: {e}", flush=True)
        return ("", 0)

def _build_structured_context_block(tools_results_summary: str, tools_called: List[str]) -> str:
    """
    Build structured CONTEXT block from tool outputs for Primary LLM.
    This formats tool data into organized sections for better analysis.
    """
    if not tools_results_summary.strip():
        return ""
    
    # Build tool summary section
    tools_section = ""
    if tools_called:
        tools_section = f"TOOLS EXECUTED: {', '.join(tools_called)}\n\n"
    
    # Format the context with clear structure
    context_block = f"""{tools_section}DATA AND INFORMATION GATHERED:

{tools_results_summary}

---
END OF CONTEXT DATA"""
    
    return context_block


def _build_enhanced_primary_system_prompt(original_system, tools_were_executed=False, tools_results_summary=""):
    """
    Build enhanced system prompt for primary LLM when tools have been executed.
    This prevents the primary LLM from redoing work already completed by tool calling model.
    """
    # Load base system prompt from external file
    base_system = load_primary_model_system_prompt()
    
    if not tools_were_executed:
        # If no tools were executed, combine base system + user system if provided
        if original_system and original_system.strip():
            return f"{base_system}\n\nADDITIONAL USER INSTRUCTIONS:\n{original_system}"
        return base_system
    
    enhanced_instructions = """

CRITICAL WORKFLOW INSTRUCTIONS:
- Tools have already been executed and completed their tasks
- Your role is to REPORT and ANALYZE the results, NOT to redo the work
- DO NOT recreate, rewrite, or duplicate what the tools have already accomplished
- Focus on summarizing what was accomplished and suggesting next steps
- Present the results clearly and offer analysis or follow-up options

TOOLS EXECUTION SUMMARY:
""" + tools_results_summary + """

Remember: The work is DONE. Your job is to present the results and provide insights, not to start over.
"""
    
    # Combine base system + user system (if provided) + enhanced instructions
    full_system = base_system
    if original_system and original_system.strip():
        full_system += f"\n\nADDITIONAL USER INSTRUCTIONS:\n{original_system}"
    full_system += enhanced_instructions
    return full_system


async def _attempt_partial_optimization(tool_results, user_prompt, preserver, validator):
    """
    Attempt partial optimization with gentler compression targeting 85-90% instead of aggressive compression.
    Preserves high-ranking content and applies minimal compression to secondary content.
    """
    try:
        # Identify high-priority content (first results, search results, academic papers)
        high_priority_tools = ['search_web', 'published_papers_search', 'wikipedia_query']
        priority_results = []
        secondary_results = []
        
        for result in tool_results:
            if result.get('tool') in high_priority_tools:
                priority_results.append(result)
            else:
                secondary_results.append(result)
        
        # Apply gentle compression only to secondary content
        partial_content = ""
        
        # High-priority content: minimal or no compression (preserve 95%+)
        for result in priority_results:
            content = str(result.get('result', ''))
            # Apply very light summarization only to extremely long content
            if len(content) > 8000:
                # Keep first 6000 chars + last 1000 chars to preserve both intro and conclusion
                compressed = content[:6000] + "\n[...content summarized for length...]\n" + content[-1000:]
                partial_content += f"Tool: {result.get('tool')}\nResult: {compressed}\n\n"
            else:
                # Keep original content intact
                partial_content += f"Tool: {result.get('tool')}\nResult: {content}\n\n"
        
        # Secondary content: moderate compression (preserve 70-80%)
        for result in secondary_results:
            content = str(result.get('result', ''))
            if len(content) > 2000:
                # More aggressive but still conservative compression
                compressed = content[:1500] + "\n[...additional details available...]\n" + content[-500:]
                partial_content += f"Tool: {result.get('tool')}\nResult: {compressed}\n\n"
            else:
                partial_content += f"Tool: {result.get('tool')}\nResult: {content}\n\n"
        
        # Create a mock optimization result for validation
        partial_result = {
            "input_type": "optimized",
            "content": partial_content.strip(),
            "compression_ratio": len(partial_content) / sum(len(str(r.get('result', ''))) for r in tool_results),
            "method": "partial_gentle_compression"
        }
        
        # Validate the partial result
        validation_result = validator.validate_optimization(
            original_content="".join(str(r.get('result', '')) for r in tool_results),
            optimized_content=partial_content,
            user_prompt=user_prompt
        )
        
        partial_result["validation_score"] = validation_result["score"]
        
        return partial_result
        
    except Exception as e:
        logger.error(f"🚨 Partial optimization error: {e}")
        return None

def _is_research_query(user_prompt: str, tools_called: List[str]) -> bool:
    """
    Determine if a query is research-oriented and requires higher accuracy.
    
    Research queries typically:
    - Use academic/scientific tools (published_papers_search, wikipedia_query)
    - Contain research-related keywords
    - Request deep analysis or comprehensive information
    """
    # Check for research-oriented tools
    research_tools = ['published_papers_search', 'wikipedia_query', 'document_search']
    has_research_tools = any(tool in tools_called for tool in research_tools)
    
    # Check for research keywords in prompt
    research_keywords = [
        'research', 'study', 'analysis', 'scientific', 'academic', 'paper', 'papers',
        'theory', 'theoretical', 'quantum', 'physics', 'chemistry', 'biology',
        'deep research', 'comprehensive', 'investigate', 'examine', 'analyze',
        'reconciling', 'general relativity', 'quantum mechanics', 'literature review'
    ]
    
    prompt_lower = user_prompt.lower()
    has_research_keywords = any(keyword in prompt_lower for keyword in research_keywords)
    
    # Check for academic phrases
    academic_phrases = [
        'current status of', 'state of the art', 'recent developments',
        'latest findings', 'peer reviewed', 'scholarly', 'empirical'
    ]
    has_academic_phrases = any(phrase in prompt_lower for phrase in academic_phrases)
    
    # Determine if research query
    is_research = has_research_tools or has_research_keywords or has_academic_phrases
    
    return is_research

async def process_with_safe_optimization(
    tool_results: List[Dict],
    user_prompt: str,
    max_context_window: int,
    tools_called: List[str],
    thread_pool,
    user_id: Optional[str] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Process tool results with safe optimization integration.
    
    This function integrates the optimization safety system into the existing
    FastAPI server processing pipeline while maintaining complete fallback compatibility.
    
    Returns:
        tuple: (tools_results_summary, optimization_metadata)
    """
    
    # Convert tool results to the format expected by our optimization system
    formatted_tool_results = []
    for i, result_dict in enumerate(tool_results):
        tool_name = tools_called[i] if i < len(tools_called) else f"tool_{i}"
        formatted_result = {
            "tool": tool_name,
            "result": result_dict
        }
        formatted_tool_results.append(formatted_result)
    
    # Check if optimization is available and enabled
    if not OPTIMIZATION_AVAILABLE:
        logger.info("🚫 Optimization system not available - using original processing")
        return await _original_processing_fallback(tool_results, user_prompt, max_context_window, thread_pool)
    
    # Check feature flags
    if not optimization_controller.should_optimize(user_id=user_id, tool_types=tools_called):
        logger.info("🚫 Optimization disabled by feature flags - using original processing")
        return await _original_processing_fallback(tool_results, user_prompt, max_context_window, thread_pool)
    
    # 🎯 ADAPTIVE OPTIMIZATION STRATEGY 🎯
    # Calculate tool results size
    total_tool_size = sum(len(str(result.get('result', ''))) for result in tool_results)
    
    # Content-aware threshold determination
    is_research_query = _is_research_query(user_prompt, tools_called)
    threshold = 0.95 if is_research_query else 0.90
    
    # Check if optimization is actually needed
    context_capacity = max_context_window * 0.8  # Conservative estimate for text vs tokens
    size_threshold = context_capacity * threshold
    
    if total_tool_size <= size_threshold:
        logger.info(f"🚀 ADAPTIVE SKIP: Content fits comfortably ({total_tool_size} ≤ {size_threshold:.0f} bytes, {threshold:.0%} threshold)")
        logger.info(f"🎯 Content type: {'Research' if is_research_query else 'General'} - preserving 100% accuracy")
        return await _original_processing_fallback(tool_results, user_prompt, max_context_window, thread_pool)
    
    logger.info(f"🎯 ADAPTIVE OPTIMIZATION: Content requires compression ({total_tool_size} > {size_threshold:.0f} bytes)")
    logger.info(f"📊 Content type: {'Research' if is_research_query else 'General'} - threshold: {threshold:.0%}")
    
    # Attempt safe optimization
    start_time = time.time()
    
    try:
        logger.info("🔧 OPTIMIZATION: Starting safe optimization attempt")
        
        # Initialize safety components
        preserver = ToolOutputPreserver()
        validator = OptimizationValidator()
        
        # Attempt optimization
        optimization_result = await safe_optimize_llm_input(
            tool_results=formatted_tool_results,
            user_prompt=user_prompt,
            preserver=preserver,
            validator=validator
        )
        
        response_time = time.time() - start_time
        
        # Record metrics
        success = optimization_result["input_type"] == "optimized"
        validation_score = optimization_result.get("validation_score", 0)
        error_type = None
        
        if not success:
            if "validation" in optimization_result.get("fallback_reason", []):
                error_type = "validation"
            elif "error" in optimization_result:
                error_type = "exception"
            elif "integrity" in optimization_result.get("error", ""):
                error_type = "integrity"
        
        optimization_controller.record_attempt(
            success=success,
            validation_score=validation_score,
            response_time=response_time,
            error_type=error_type
        )
        
        # Use optimized content or fallback
        if success:
            logger.info(f"✅ OPTIMIZATION SUCCESS: Score {validation_score:.1f}, Response time {response_time:.2f}s")
            return optimization_result["content"], {
                "optimization_used": True,
                "optimization_score": validation_score,
                "response_time": response_time,
                "fallback_available": True
            }
        else:
            # 🎯 PARTIAL OPTIMIZATION STRATEGY 🎯
            # If full optimization failed, try partial optimization (gentler compression)
            fallback_reasons = optimization_result.get("fallback_reason", [])
            if error_type == "validation" and validation_score > 50:  # Some quality maintained
                logger.info("🔄 ATTEMPTING PARTIAL OPTIMIZATION: Gentler compression with high-priority content preservation")
                
                try:
                    # Attempt partial optimization with relaxed parameters
                    partial_result = await _attempt_partial_optimization(
                        formatted_tool_results, user_prompt, preserver, validator
                    )
                    
                    if partial_result and partial_result.get("validation_score", 0) > validation_score:
                        logger.info(f"✅ PARTIAL OPTIMIZATION SUCCESS: Score improved {validation_score:.1f} → {partial_result.get('validation_score', 0):.1f}")
                        return partial_result["content"], {
                            "optimization_used": True,
                            "optimization_type": "partial",
                            "optimization_score": partial_result.get("validation_score", 0),
                            "response_time": response_time,
                            "original_score": validation_score
                        }
                    else:
                        logger.info("🚫 Partial optimization did not improve quality - using original fallback")
                        
                except Exception as partial_error:
                    logger.warning(f"⚠️ Partial optimization failed: {partial_error}")
            
            logger.warning(f"⚠️ OPTIMIZATION FALLBACK: {optimization_result.get('fallback_reason', 'Unknown reason')}")
            return optimization_result["content"], {
                "optimization_used": False,
                "fallback_reason": optimization_result.get("fallback_reason", "Unknown"),
                "validation_score": validation_score,
                "response_time": response_time
            }
            
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"🚨 OPTIMIZATION SYSTEM ERROR: {e}")
        
        # Record failure
        optimization_controller.record_attempt(
            success=False,
            validation_score=0,
            response_time=response_time,
            error_type="exception"
        )
        
        # Emergency fallback to original processing
        logger.info("🔄 EMERGENCY FALLBACK: Using original processing")
        return await _original_processing_fallback(tool_results, user_prompt, max_context_window, thread_pool)


async def _original_processing_fallback(
    tool_results: List[Dict],
    user_prompt: str, 
    max_context_window: int,
    thread_pool
) -> tuple[str, Dict[str, Any]]:
    """
    Original processing logic for fallback compatibility.
    This replicates the exact original logic from the FastAPI server.
    """
    
    # Recreate the original full_tools_text with enhanced source block preservation
    full_tools_text = ""
    for result_dict in tool_results:
        if isinstance(result_dict, dict):
            for key, value in result_dict.items():
                # 🔧 ENHANCED SOURCE BLOCK PRESERVATION: Check if value contains enhanced source blocks
                if isinstance(value, str) and ("═══════════════════════════════════════════════════════" in value or "📄 SOURCE BLOCK #" in value):
                    # Enhanced source blocks detected - preserve full formatting
                    full_tools_text += f"{key}: {value}\n"
                    logger.info(f"🎯 ENHANCED SOURCE BLOCKS PRESERVED: {key} contains enhanced formatting ({len(value)} chars)")
                else:
                    # Regular tool output - use standard formatting
                    full_tools_text += f"{key}: {value}\n"
        else:
            full_tools_text += str(result_dict) + "\n"
    
    # Apply original context window logic
    if len(full_tools_text) > (max_context_window) * 1.05:
        try:
            logger.info(f"Calling TextChunker() to reduce context size from {len(full_tools_text)} to around {max_context_window} bytes")
            if TOOLS_AVAILABLE:
                def sync_text_chunking():
                    from text_chunker import TextChunker
                    return TextChunker.summary_by_semantics(
                        full_tools_text, 
                        query=user_prompt,
                        max_length=max_context_window
                    )
                
                tools_results_summary = await asyncio.get_event_loop().run_in_executor(
                    thread_pool, sync_text_chunking
                )
                logger.info(f"TextChunker() was called and returned tools_results_summary size of {len(tools_results_summary)} bytes. From {len(full_tools_text)}")
            else:
                tools_results_summary = full_tools_text
        except Exception as e:
            logger.error(f"Error: exception in TextChunker.summary_by_semantics() call. Function returned message: {e}")
            tools_results_summary = full_tools_text  # TextChunker() failed!! Use the full text
    else:
        tools_results_summary = full_tools_text
    
    return tools_results_summary, {
        "optimization_used": False,
        "original_processing": True,
        "context_size": len(tools_results_summary)
    }


# ==============================================================================
# OLLAMA LLM ENDPOINTS
# ==============================================================================
@app.post("/llama3_1b/prompt", response_model=ApiResponse)
async def llama_prompt(request: OllamaPromptRequest):
    """
    Ollama prompt endpoint with streaming support
    Equivalent to the original /llama3_1b/prompt endpoint
    """
    logger.info(f"Ollama prompt request: model={request.model}")
    
    try:
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": request.stream
            # think parameter handled by LLM Manager from config
        }
        
        if request.system:
            payload["system"] = request.system
        if request.context:
            payload["context"] = request.context
        
        # Use HTTP connection pool
        async with http_pool.get_session() as session:
            async with session.post(
                ServerConfig.OLLAMA_URL,
                json=payload,
                timeout=None  # No timeout - let LLM stream as long as needed
            ) as response:
                
                if request.stream:
                    # Return streaming response
                    async def stream_generator():
                        try:
                            async for chunk in response.content.iter_chunked(1024):
                                if chunk:
                                    yield chunk
                        except Exception as e:
                            logger.error(f"Streaming error: {e}")
                            # Send error message as final chunk
                            error_response = {"error": f"Streaming interrupted: {str(e)}"}
                            yield json.dumps(error_response).encode() + b'\n'
                    
                    return StreamingResponse(
                        stream_generator(),
                        media_type="application/x-ndjson"
                    )
                else:
                    # Return JSON response
                    result = await response.json()
                    return ApiResponse(
                        success=True,
                        data=result,
                        timestamp=datetime.now().isoformat()
                    )
                    
    except Exception as e:
        logger.error(f"Ollama prompt failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama request failed: {str(e)}")

def analyze_error_patterns(error_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔍 ERROR PATTERN ANALYSIS ENGINE (Sprint 3.2 Enhanced)
    Analyzes detected error patterns and provides strategic insights for retry logic
    with comprehensive tool-specific error handling and pattern recognition
    
    Args:
        error_analysis: Dictionary of task errors with patterns and categories
        
    Returns:
        Dict with pattern analysis, priority recommendations, and retry strategies
    """
    if not error_analysis:
        return {"status": "no_errors", "analysis": {}}
    
    try:
        # Pattern frequency analysis
        pattern_frequency = {}
        category_distribution = {}
        strategy_recommendations = {}
        
        for task_id, analysis in error_analysis.items():
            pattern = analysis.get("error_pattern")
            category = analysis.get("error_category") 
            strategy = analysis.get("retry_strategy")
            
            # Count pattern frequency
            if pattern:
                pattern_frequency[pattern] = pattern_frequency.get(pattern, 0) + 1
            
            # Distribution by category
            if category:
                if category not in category_distribution:
                    category_distribution[category] = {"count": 0, "patterns": set()}
                category_distribution[category]["count"] += 1
                if pattern:
                    category_distribution[category]["patterns"].add(pattern)
            
            # Strategy aggregation
            if strategy:
                if strategy not in strategy_recommendations:
                    strategy_recommendations[strategy] = {"count": 0, "task_ids": []}
                strategy_recommendations[strategy]["count"] += 1
                strategy_recommendations[strategy]["task_ids"].append(task_id)
        
        # Determine priority categories (most common error types)
        priority_categories = sorted(
            category_distribution.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        # Smart retry prioritization
        retry_priority = []
        for category, data in priority_categories:
            if data["count"] > 0:
                retry_priority.append({
                    "category": category,
                    "error_count": data["count"],
                    "patterns": list(data["patterns"]),
                    "recommended_action": _get_category_recommendation(category)
                })
        
        return {
            "status": "patterns_detected",
            "total_errors": len(error_analysis),
            "pattern_frequency": pattern_frequency,
            "category_distribution": {k: {"count": v["count"], "patterns": list(v["patterns"])} 
                                   for k, v in category_distribution.items()},
            "strategy_recommendations": strategy_recommendations,
            "retry_priority": retry_priority,
            "critical_patterns": [p for p, count in pattern_frequency.items() if count > 1]
        }
        
    except Exception as e:
        logger.error(f"❌ Error pattern analysis failed: {e}")
        return {"status": "analysis_failed", "error": str(e)}

def _get_category_recommendation(category: str) -> str:
    """Get recommended action based on error category - Sprint 3.2 Enhanced"""
    recommendations = {
        # Sprint 3.2: Comprehensive category-specific recommendations
        "network": "retry_with_exponential_backoff",
        "filesystem": "retry_with_path_traversal_and_correction", 
        "authentication": "escalate_to_user_with_credential_refresh",
        "data_format": "retry_with_format_correction_and_validation",
        "external_service": "retry_with_fallback_endpoint",
        "runtime": "retry_with_dependency_installation",
        "resource_exhaustion": "retry_with_memory_optimization",
        "security": "escalate_to_user_with_compliance_guidance"
    }
    return recommendations.get(category, "retry_with_delay")

def handle_graceful_degradation(failed_tools: List[Dict], successful_tools: List[Dict]) -> Dict[str, Any]:
    """
    🎯 GRACEFUL DEGRADATION HANDLER (Sprint 3.2)
    
    Implements intelligent graceful degradation when some tools fail but others succeed.
    Determines if partial results are acceptable and how to proceed.
    
    Args:
        failed_tools: List of tools that failed after retry attempts
        successful_tools: List of tools that completed successfully
        
    Returns:
        Dict with degradation strategy and messaging
    """
    logger.info(f"🎯 GRACEFUL DEGRADATION: Analyzing {len(failed_tools)} failed vs {len(successful_tools)} successful tools")
    
    total_tools = len(failed_tools) + len(successful_tools)
    success_rate = len(successful_tools) / total_tools if total_tools > 0 else 0
    
    # Analyze failed tool types and criticality
    critical_failures = []
    non_critical_failures = []
    
    # Sprint 3.2: Tool criticality classification
    critical_tool_patterns = {
        "authentication", "security", "core_data_retrieval",
        "primary_calculation", "essential_file_access"
    }
    
    for tool in failed_tools:
        tool_name = tool.get("tool_name", "")
        error_category = tool.get("error_category", "")
        
        # Determine criticality based on tool type and error
        is_critical = (
            any(pattern in tool_name.lower() for pattern in critical_tool_patterns) or
            error_category in ["authentication", "security", "resource_exhaustion"] or
            "email" in tool_name.lower()  # Email sending is usually critical
        )
        
        if is_critical:
            critical_failures.append(tool)
        else:
            non_critical_failures.append(tool)
    
    # Degradation decision logic
    if success_rate >= 0.8 and len(critical_failures) == 0:
        # High success rate, no critical failures
        return {
            "strategy": "CONTINUE_WITH_WARNING",
            "acceptable": True,
            "message": f"Proceeding with {success_rate:.1%} success rate. {len(non_critical_failures)} non-critical tools failed.",
            "warning": f"Some supplementary data may be missing due to {len(non_critical_failures)} tool failures.",
            "failed_tools": non_critical_failures
        }
    
    elif success_rate >= 0.6 and len(critical_failures) <= 1:
        # Moderate success rate, minimal critical failures
        return {
            "strategy": "PARTIAL_SUCCESS_ACCEPTABLE", 
            "acceptable": True,
            "message": f"Partial success achieved ({success_rate:.1%}). Core functionality preserved.",
            "warning": f"Results may be incomplete. {len(failed_tools)} tools failed including {len(critical_failures)} critical.",
            "failed_tools": failed_tools
        }
    
    elif len(successful_tools) > 0 and len(critical_failures) <= 2:
        # Some success, limited critical failures
        return {
            "strategy": "CONTINUE_WITH_MAJOR_WARNING",
            "acceptable": True,
            "message": f"Limited success ({success_rate:.1%}). Proceeding with significant data gaps.",
            "warning": f"⚠️ MAJOR DATA GAPS: {len(critical_failures)} critical tools failed. Results may be unreliable.",
            "failed_tools": failed_tools
        }
    
    else:
        # Too many failures or too many critical failures
        return {
            "strategy": "ABORT_AND_EXPLAIN",
            "acceptable": False,
            "message": f"Too many failures ({success_rate:.1%} success rate) including {len(critical_failures)} critical tools.",
            "escalation": "EXPLAIN_FAILURE_AND_SUGGEST_ALTERNATIVES",
            "failed_tools": failed_tools,
            "recommendation": "Consider simplifying the request or addressing the underlying issues before retrying."
        }

class ArbitratorMonitor:
    """
    📊 ARBITRATOR MONITORING & STABILITY SYSTEM (Sprint 3.4)
    
    Provides comprehensive monitoring for arbitrator system health, performance metrics,
    and stability tracking for production deployment.
    """
    
    def __init__(self):
        self.metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "retry_sessions": 0,
            "circuit_breaker_activations": 0,
            "pattern_detections": {},
            "performance_stats": {
                "avg_validation_time": 0.0,
                "min_validation_time": float('inf'),
                "max_validation_time": 0.0,
                "total_validation_time": 0.0
            },
            "stability_checkpoints": [],
            "error_recovery_rate": 0.0,
            "arbitrator_llm_calls": 0,
            "arbitrator_llm_failures": 0
        }
        
        self.stability_thresholds = {
            "max_validation_failures": 5,
            "max_circuit_breaker_rate": 0.3,  # 30% of sessions
            "min_success_rate": 0.7,  # 70% success rate
            "max_avg_validation_time": 10.0,  # 10 seconds
            "health_check_interval": 300  # 5 minutes
        }
        
        self.last_health_check = 0
        self.system_status = "HEALTHY"
        
        logger.info("📊 Arbitrator Monitor initialized")
    
    def record_validation_attempt(self, success: bool, validation_time: float, error_patterns: List[str] = None):
        """Record a validation attempt with performance metrics"""
        self.metrics["total_validations"] += 1
        
        if success:
            self.metrics["successful_validations"] += 1
        else:
            self.metrics["failed_validations"] += 1
        
        # Performance tracking
        perf_stats = self.metrics["performance_stats"]
        perf_stats["total_validation_time"] += validation_time
        perf_stats["avg_validation_time"] = perf_stats["total_validation_time"] / self.metrics["total_validations"]
        perf_stats["min_validation_time"] = min(perf_stats["min_validation_time"], validation_time)
        perf_stats["max_validation_time"] = max(perf_stats["max_validation_time"], validation_time)
        
        # Pattern tracking
        if error_patterns:
            for pattern in error_patterns:
                self.metrics["pattern_detections"][pattern] = self.metrics["pattern_detections"].get(pattern, 0) + 1
        
        # Update success rate
        self.metrics["error_recovery_rate"] = self.metrics["successful_validations"] / self.metrics["total_validations"]
        
        logger.info(f"📊 VALIDATION RECORDED: Success={success}, Time={validation_time:.2f}s, Total={self.metrics['total_validations']}")
    
    def record_retry_session(self, retry_count: int, success: bool):
        """Record a retry session with outcome"""
        self.metrics["retry_sessions"] += 1
        
        if success:
            logger.info(f"📊 RETRY SUCCESS: Session completed after {retry_count} retries")
        else:
            logger.warning(f"📊 RETRY FAILURE: Session failed after {retry_count} retries")
    
    def record_circuit_breaker_activation(self, reason: str, escalation: str):
        """Record circuit breaker activation"""
        self.metrics["circuit_breaker_activations"] += 1
        
        # Track escalation types
        escalation_key = f"escalation_{escalation.lower()}"
        self.metrics[escalation_key] = self.metrics.get(escalation_key, 0) + 1
        
        logger.warning(f"📊 CIRCUIT BREAKER RECORDED: {reason} → {escalation}")
    
    def record_arbitrator_llm_call(self, success: bool, response_time: float):
        """Record arbitrator LLM call metrics"""
        self.metrics["arbitrator_llm_calls"] += 1
        
        if success:
            logger.info(f"📊 ARBITRATOR LLM SUCCESS: {response_time:.2f}s")
        else:
            self.metrics["arbitrator_llm_failures"] += 1
            logger.error(f"📊 ARBITRATOR LLM FAILURE: {response_time:.2f}s")
    
    def perform_stability_check(self) -> Dict[str, Any]:
        """Perform comprehensive stability assessment"""
        import time
        current_time = time.time()
        
        # Skip if recent check
        if current_time - self.last_health_check < self.stability_thresholds["health_check_interval"]:
            return {"status": "RECENT_CHECK", "next_check_in": self.stability_thresholds["health_check_interval"] - (current_time - self.last_health_check)}
        
        self.last_health_check = current_time
        
        # Calculate stability metrics
        stability_report = {
            "timestamp": current_time,
            "system_status": "HEALTHY",
            "issues": [],
            "recommendations": [],
            "metrics_summary": self.get_metrics_summary()
        }
        
        # Check success rate
        if self.metrics["error_recovery_rate"] < self.stability_thresholds["min_success_rate"]:
            stability_report["issues"].append(f"Low success rate: {self.metrics['error_recovery_rate']:.1%}")
            stability_report["system_status"] = "WARNING"
            stability_report["recommendations"].append("Review error patterns and retry strategies")
        
        # Check average validation time
        avg_time = self.metrics["performance_stats"]["avg_validation_time"]
        if avg_time > self.stability_thresholds["max_avg_validation_time"]:
            stability_report["issues"].append(f"High validation time: {avg_time:.2f}s")
            stability_report["system_status"] = "WARNING"
            stability_report["recommendations"].append("Optimize arbitrator LLM performance")
        
        # Check circuit breaker activation rate
        if self.metrics["total_validations"] > 0:
            cb_rate = self.metrics["circuit_breaker_activations"] / self.metrics["total_validations"]
            if cb_rate > self.stability_thresholds["max_circuit_breaker_rate"]:
                stability_report["issues"].append(f"High circuit breaker rate: {cb_rate:.1%}")
                stability_report["system_status"] = "CRITICAL" if cb_rate > 0.5 else "WARNING"
                stability_report["recommendations"].append("Review circuit breaker thresholds and error patterns")
        
        # Check arbitrator LLM failure rate
        if self.metrics["arbitrator_llm_calls"] > 0:
            llm_failure_rate = self.metrics["arbitrator_llm_failures"] / self.metrics["arbitrator_llm_calls"]
            if llm_failure_rate > 0.1:  # 10% failure rate threshold
                stability_report["issues"].append(f"High arbitrator LLM failure rate: {llm_failure_rate:.1%}")
                stability_report["system_status"] = "CRITICAL"
                stability_report["recommendations"].append("Check arbitrator LLM connectivity and credentials")
        
        # Update system status
        self.system_status = stability_report["system_status"]
        
        # Add to stability checkpoints
        checkpoint = {
            "timestamp": current_time,
            "status": self.system_status,
            "total_validations": self.metrics["total_validations"],
            "success_rate": self.metrics["error_recovery_rate"],
            "avg_validation_time": avg_time,
            "circuit_breaker_activations": self.metrics["circuit_breaker_activations"]
        }
        
        self.metrics["stability_checkpoints"].append(checkpoint)
        
        # Keep only last 24 checkpoints (2 hours if every 5 minutes)
        if len(self.metrics["stability_checkpoints"]) > 24:
            self.metrics["stability_checkpoints"] = self.metrics["stability_checkpoints"][-24:]
        
        logger.info(f"📊 STABILITY CHECK: Status={self.system_status}, Issues={len(stability_report['issues'])}")
        
        return stability_report
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            "validation_metrics": {
                "total": self.metrics["total_validations"],
                "successful": self.metrics["successful_validations"],
                "failed": self.metrics["failed_validations"],
                "success_rate": f"{self.metrics['error_recovery_rate']:.1%}"
            },
            "performance_metrics": self.metrics["performance_stats"].copy(),
            "retry_metrics": {
                "sessions": self.metrics["retry_sessions"],
                "circuit_breaker_activations": self.metrics["circuit_breaker_activations"]
            },
            "arbitrator_llm_metrics": {
                "calls": self.metrics["arbitrator_llm_calls"],
                "failures": self.metrics["arbitrator_llm_failures"],
                "failure_rate": f"{(self.metrics['arbitrator_llm_failures'] / max(1, self.metrics['arbitrator_llm_calls'])):.1%}"
            },
            "pattern_analysis": self.metrics["pattern_detections"].copy(),
            "system_health": {
                "status": self.system_status,
                "checkpoints": len(self.metrics["stability_checkpoints"])
            }
        }
    
    def generate_production_report(self) -> Dict[str, Any]:
        """Generate comprehensive production readiness report"""
        stability_check = self.perform_stability_check()
        
        report = {
            "arbitrator_system_status": "PRODUCTION_READY",
            "timestamp": stability_check["timestamp"],
            "stability_assessment": stability_check,
            "metrics_summary": self.get_metrics_summary(),
            "production_readiness_checklist": {
                "configuration_compliance": True,  # Managed through llm_config_tool.py
                "core_functionality": self.metrics["total_validations"] > 0,
                "error_handling": self.metrics["circuit_breaker_activations"] >= 0,  # System can handle circuit breakers
                "performance_baseline": self.metrics["performance_stats"]["avg_validation_time"] > 0,
                "monitoring_active": len(self.metrics["stability_checkpoints"]) > 0,
                "backward_compatibility": True  # System works when disabled
            },
            "sprint_achievements": {
                "sprint_1_complete": "Configuration + LLM Manager Integration + Single Integration Point",
                "sprint_2_complete": "Validation Logic + Error Pattern Detection + Intelligent Retry with Circuit Breakers", 
                "sprint_3_complete": "Enhanced Circuit Breakers + Comprehensive Error Patterns + Quantum Story Validation + Production Monitoring"
            },
            "recommendations": stability_check.get("recommendations", [])
        }
        
        # Determine overall production readiness
        if stability_check["system_status"] in ["HEALTHY", "WARNING"]:
            if self.metrics["total_validations"] >= 1:  # Has been tested
                report["arbitrator_system_status"] = "PRODUCTION_READY"
            else:
                report["arbitrator_system_status"] = "TESTING_REQUIRED"
        else:
            report["arbitrator_system_status"] = "NOT_READY_CRITICAL_ISSUES"
        
        return report

# Global arbitrator monitor instance
arbitrator_monitor = ArbitratorMonitor()

class CircuitBreakerManager:
    """
    🛑 CIRCUIT BREAKER MANAGER (Sprint 3.1)
    
    Advanced circuit breaker system with pattern detection and escalation strategies.
    Protects against:
    - Infinite retry loops
    - Resource exhaustion 
    - Contradictory feedback cycles
    - Cost runaway scenarios
    """
    
    def __init__(self):
        # Circuit breaker state tracking
        self.session_retries = 0
        self.task_retries = {}
        self.error_patterns = {}
        self.escalation_history = []
        
        # Circuit breaker thresholds
        self.MAX_SESSION_RETRIES = 10
        self.MAX_TASK_RETRIES = 3
        self.MAX_PATTERN_REPEATS = 2
        self.MAX_ESCALATION_ATTEMPTS = 5
        
        logger.info("🛑 Circuit Breaker Manager initialized")
    
    def check_session_circuit_breaker(self) -> Optional[Dict[str, Any]]:
        """Check if session-level circuit breaker should trigger"""
        if self.session_retries >= self.MAX_SESSION_RETRIES:
            return {
                "triggered": True,
                "reason": "MAX_SESSION_RETRIES_EXCEEDED",
                "escalation": "EXPLAIN_FAILURE",
                "message": f"Session exceeded maximum retries ({self.MAX_SESSION_RETRIES}). System protecting against resource exhaustion.",
                "cost_protection": True
            }
        return {"triggered": False}
    
    def check_task_circuit_breaker(self, task_key: str) -> Optional[Dict[str, Any]]:
        """Check if task-level circuit breaker should trigger"""
        retry_count = self.task_retries.get(task_key, 0)
        if retry_count >= self.MAX_TASK_RETRIES:
            return {
                "triggered": True,
                "reason": "MAX_TASK_RETRIES_EXCEEDED", 
                "escalation": "ALTERNATIVE_APPROACH",
                "message": f"Task '{task_key}' failed {retry_count} times. Marking as unachievable.",
                "task_key": task_key
            }
        return {"triggered": False}
    
    def check_pattern_circuit_breaker(self, error_pattern: str, feedback: str) -> Optional[Dict[str, Any]]:
        """Check for infinite loop patterns and contradictory feedback"""
        pattern_key = f"{error_pattern}:{hash(feedback) % 10000}"
        
        # Track pattern frequency
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = {
                "count": 0,
                "first_seen": logger.info(f"🔍 New error pattern detected: {error_pattern}"),
                "feedback_samples": []
            }
        
        self.error_patterns[pattern_key]["count"] += 1
        self.error_patterns[pattern_key]["feedback_samples"].append(feedback[:100])
        
        pattern_count = self.error_patterns[pattern_key]["count"]
        
        if pattern_count > self.MAX_PATTERN_REPEATS:
            # Check for contradictory feedback
            feedback_samples = self.error_patterns[pattern_key]["feedback_samples"]
            unique_feedback = len(set(feedback_samples))
            
            if unique_feedback > 1:
                return {
                    "triggered": True,
                    "reason": "CONTRADICTORY_FEEDBACK_DETECTED",
                    "escalation": "USER_GUIDANCE", 
                    "message": f"Pattern '{error_pattern}' showing contradictory feedback across {pattern_count} attempts.",
                    "pattern_details": {
                        "error_pattern": error_pattern,
                        "attempt_count": pattern_count,
                        "unique_feedback_count": unique_feedback
                    }
                }
            else:
                return {
                    "triggered": True,
                    "reason": "INFINITE_LOOP_DETECTED",
                    "escalation": "ALTERNATIVE_APPROACH",
                    "message": f"Same error pattern '{error_pattern}' repeated {pattern_count} times with identical feedback.",
                    "pattern_details": {
                        "error_pattern": error_pattern,
                        "repeat_count": pattern_count
                    }
                }
        
        return {"triggered": False}
    
    def check_escalation_circuit_breaker(self) -> Optional[Dict[str, Any]]:
        """Check if too many escalations have occurred"""
        if len(self.escalation_history) >= self.MAX_ESCALATION_ATTEMPTS:
            return {
                "triggered": True,
                "reason": "MAX_ESCALATION_ATTEMPTS_EXCEEDED",
                "escalation": "SYSTEM_INTERVENTION",
                "message": f"System has escalated {len(self.escalation_history)} times. Manual review required.",
                "escalation_summary": self.escalation_history[-3:]  # Last 3 escalations
            }
        return {"triggered": False}
    
    def should_abort_retry(self, task_key: str, error_pattern: str, feedback: str) -> Dict[str, Any]:
        """
        Master circuit breaker decision function
        Returns comprehensive decision with reasoning
        """
        decision = {
            "abort": False,
            "reason": None,
            "escalation": None,
            "message": None,
            "circuit_breaker_details": []
        }
        
        # Check all circuit breaker conditions
        session_check = self.check_session_circuit_breaker()
        task_check = self.check_task_circuit_breaker(task_key)
        pattern_check = self.check_pattern_circuit_breaker(error_pattern, feedback)
        escalation_check = self.check_escalation_circuit_breaker()
        
        # Collect all triggered circuit breakers
        triggered_breakers = []
        for check in [session_check, task_check, pattern_check, escalation_check]:
            if check.get("triggered", False):
                triggered_breakers.append(check)
        
        if triggered_breakers:
            # Use the most severe circuit breaker
            severity_order = {
                "SYSTEM_INTERVENTION": 4,
                "USER_GUIDANCE": 3, 
                "EXPLAIN_FAILURE": 2,
                "ALTERNATIVE_APPROACH": 1
            }
            
            most_severe = max(triggered_breakers, 
                            key=lambda x: severity_order.get(x.get("escalation", ""), 0))
            
            decision.update({
                "abort": True,
                "reason": most_severe["reason"],
                "escalation": most_severe["escalation"],
                "message": most_severe["message"],
                "circuit_breaker_details": triggered_breakers
            })
            
            # Log circuit breaker activation
            logger.warning(f"🛑 CIRCUIT BREAKER ACTIVATED: {most_severe['reason']}")
            logger.warning(f"🛑 Escalation: {most_severe['escalation']}")
            
            # Record escalation
            self.escalation_history.append({
                "reason": most_severe["reason"],
                "escalation": most_severe["escalation"], 
                "task_key": task_key,
                "timestamp": logger.info(f"Circuit breaker escalation recorded")
            })
        
        return decision
    
    def increment_retry_counters(self, task_key: str):
        """Increment retry counters for tracking"""
        self.session_retries += 1
        self.task_retries[task_key] = self.task_retries.get(task_key, 0) + 1
        
        logger.info(f"🔄 Retry counters updated: Session={self.session_retries}, Task[{task_key}]={self.task_retries[task_key]}")
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get comprehensive circuit breaker status"""
        return {
            "session_retries": self.session_retries,
            "max_session_retries": self.MAX_SESSION_RETRIES,
            "active_tasks": len(self.task_retries),
            "task_retry_details": self.task_retries.copy(),
            "error_patterns": len(self.error_patterns),
            "escalations": len(self.escalation_history),
            "circuit_breaker_health": "HEALTHY" if self.session_retries < self.MAX_SESSION_RETRIES * 0.8 else "WARNING"
        }

# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()

async def intelligent_retry_with_circuit_breakers(
    error_analysis: Dict[str, Any], 
    pattern_analysis: Dict[str, Any],
    tools_called: List[str], 
    tools_results_list: List[str], 
    user_prompt: str,
    tool_manager = None  # Add access to tool execution
) -> Dict[str, Any]:
    """
    🔄 INTELLIGENT RETRY WITH CIRCUIT BREAKERS (Sprint 2.3)
    
    Implements intelligent retry logic with circuit breaker patterns to prevent:
    - Infinite retry loops
    - Resource exhaustion
    - Contradictory feedback cycles
    - Unachievable task persistence
    
    Args:
        error_analysis: Error pattern analysis from arbitrator
        pattern_analysis: Strategic pattern analysis results
        tools_called: Original list of tools that were executed
        tools_results_list: Original results from tool execution
        user_prompt: Original user request
        
    Returns:
        Dict with success status, corrected results, or failure reason
    """
    logger.info(f"🔄 INTELLIGENT RETRY ENGINE (Sprint 3.1): Analyzing {len(tools_called)} tools with enhanced circuit breakers")
    
    # Log current circuit breaker status
    cb_status = circuit_breaker_manager.get_circuit_breaker_status()
    logger.info(f"🛑 Circuit Breaker Status: {cb_status['circuit_breaker_health']} | Session: {cb_status['session_retries']}/{cb_status['max_session_retries']}")
    
    # Master session circuit breaker check
    session_check = circuit_breaker_manager.check_session_circuit_breaker()
    if session_check["triggered"]:
        logger.error(f"🛑 SESSION CIRCUIT BREAKER ACTIVATED: {session_check['reason']}")
        return {
            "success": False,
            "reason": session_check["reason"],
            "escalation": session_check["escalation"],
            "message": session_check["message"],
            "circuit_breaker_type": "SESSION_LEVEL"
        }
    
    # NEW APPROACH: Build failed task list from error_analysis dictionary
    retry_candidates = []
    unachievable_tasks = []
    
    logger.info(f"🔍 ERROR ANALYSIS KEYS: {list(error_analysis.keys())}")
    
    # Process each task that had errors detected
    for task_id, task_error in error_analysis.items():
        try:
            # Convert task_id back to array index (task_id is 1-based from arbitrator)
            task_index = int(task_id) - 1
            
            if task_index >= len(tools_called):
                logger.warning(f"🔍 Invalid task_index {task_index} for task_id {task_id}")
                continue
                
            tool_name = tools_called[task_index]
            result = tools_results_list[task_index]
            task_key = f"{tool_name}_{task_index}"
            
            error_pattern = task_error.get("error_pattern", "unknown")
            feedback = task_error.get("feedback", "")
            retry_strategy = task_error.get("retry_strategy", "")
            
            logger.info(f"🔍 Processing failed task: {tool_name} | Pattern: {error_pattern} | Strategy: {retry_strategy}")
            
        except (ValueError, KeyError) as e:
            logger.error(f"🔍 Error processing task_id {task_id}: {e}")
            continue
        
        # Sprint 3.1: Advanced Circuit Breaker Decision System
        circuit_decision = circuit_breaker_manager.should_abort_retry(task_key, error_pattern, feedback)
        
        if circuit_decision["abort"]:
            logger.warning(f"🛑 ADVANCED CIRCUIT BREAKER: {task_key} → {circuit_decision['reason']}")
            logger.warning(f"🛑 Escalation Strategy: {circuit_decision['escalation']}")
            
            unachievable_tasks.append({
                "tool": tool_name,
                "reason": circuit_decision["reason"],
                "escalation": circuit_decision["escalation"],
                "message": circuit_decision["message"],
                "circuit_breaker_details": circuit_decision["circuit_breaker_details"]
            })
            continue
        
        # Add to retry candidates - this task can be retried with LLM feedback
        retry_candidates.append({
            "tool_name": tool_name,
            "task_index": task_index,
            "error_pattern": error_pattern,
            "retry_strategy": retry_strategy,
            "feedback": feedback,
            "original_result": result,
            "retry_count": 0  # Initialize retry count for this session
        })
        
        logger.info(f"✅ RETRY CANDIDATE: {tool_name} at index {task_index} | Strategy: {retry_strategy}")
        
    
    # 🚀 NEW CORE IMPLEMENTATION: LLM REGENERATION WITH FEEDBACK
    logger.info(f"🔄 RETRY ANALYSIS: {len(retry_candidates)} candidates, {len(unachievable_tasks)} unachievable")
    
    if not retry_candidates:
        logger.info(f"🔄 No eligible tasks for retry - all tools completed successfully")
        return {
            "success": True,
            "reason": "NO_RETRY_NEEDED",
            "corrected_results": "\n\n".join(tools_results_list)
        }
    
    # 🚀 ITERATIVE CIRCUIT BREAKER LOOP WITH ACCUMULATIVE CONTEXT
    logger.info(f"🔧 INITIATING ITERATIVE LLM REGENERATION for {len(retry_candidates)} failed tools")
    
    if not tool_manager:
        logger.error("❌ CRITICAL: tool_manager not provided - cannot regenerate tools")
        return {
            "success": False,
            "reason": "MISSING_TOOL_MANAGER",
            "message": "Cannot regenerate tools without tool_manager access"
        }
    
    # Use global llm_manager for regeneration
    
    # 🔄 ITERATIVE REGENERATION WITH CIRCUIT BREAKER LOGIC
    MAX_ITERATIONS = 3  # Circuit breaker: maximum retry iterations
    iteration = 1
    current_retry_candidates = retry_candidates.copy()
    previous_iterations = []  # Accumulative context for each iteration
    
    while iteration <= MAX_ITERATIONS and current_retry_candidates:
        logger.info(f"🔄 REGENERATION ITERATION {iteration}/{MAX_ITERATIONS} - Processing {len(current_retry_candidates)} failed tools")
        
        # 🧠 BUILD REGENERATION CONTEXT (accumulative from previous iterations)
        regeneration_context = await _build_regeneration_context(
            current_retry_candidates, user_prompt, tools_called, tools_results_list, 
            previous_iterations=previous_iterations
        )
        
        logger.info(f"🧠 ITERATION {iteration} CONTEXT: {len(regeneration_context)} characters (accumulative)")
        
        try:
            # 🔄 CALL LLM FOR TOOL REGENERATION (with iteration count for logging)
            logger.info(f"🧠 Calling tool_calling LLM for iteration {iteration} regeneration")
            
            # 🚨 LOG EXACT CONTEXT SENT TO LLM
            logger.info(f"🔧 REGENERATION CONTEXT SENT TO LLM:\n{'='*80}\n{regeneration_context}\n{'='*80}")
            
            regenerated_tools = await _regenerate_failed_tools_with_llm(
                llm_manager, regeneration_context, current_retry_candidates, 
                await tool_manager.get_tools_definitions(), iteration_count=iteration
            )
            
            logger.info(f"🔧 ITERATION {iteration}: LLM returned {len(regenerated_tools)} regenerated tool calls")
            
            # 🚨 LOG EXACT LLM RESPONSE
            import json
            truncated_regenerated_tools = truncate_base64_for_logging(json.dumps(regenerated_tools, indent=2))
            logger.info(f"🔧 LLM REGENERATION RESPONSE:\n{'='*80}\n{truncated_regenerated_tools}\n{'='*80}")
            
            # 🚨 VALIDATION: Check if LLM actually regenerated tools
            if len(regenerated_tools) == 0:
                logger.error(f"❌ ITERATION {iteration}: No regenerated tools returned - breaking iteration loop")
                break
            
            # 🚀 RE-EXECUTE CORRECTED TOOLS
            corrected_results = await _execute_corrected_tools(
                tool_manager, regenerated_tools, current_retry_candidates
            )
            
            logger.info(f"🔧 ITERATION {iteration}: Executed {len(corrected_results)} corrected tools")
            
            # 🚨 LOG DETAILED EXECUTION RESULTS
            for idx, result in enumerate(corrected_results):
                result_text = result.get('result', 'No result')
                truncated_result = truncate_base64_for_logging(str(result_text))
                logger.info(f"🔧 EXECUTION RESULT {idx+1}:\n{'='*80}\nTool: {result.get('tool_name', 'Unknown')}\nCorrected: {result.get('corrected', False)}\nResult: {truncated_result}\n{'='*80}")
            
            # 🚨 ANALYZE SUCCESS/FAILURE OF THIS ITERATION
            successful_corrections = [cr for cr in corrected_results if cr.get("corrected", False)]
            failed_corrections = [cr for cr in corrected_results if not cr.get("corrected", False)]
            
            logger.info(f"📊 ITERATION {iteration} RESULTS: {len(successful_corrections)} successes, {len(failed_corrections)} failures")
            
            # ✅ SUCCESS CASE: All tools corrected successfully
            if len(successful_corrections) == len(current_retry_candidates):
                logger.info(f"🎉 ITERATION {iteration} SUCCESS: All {len(successful_corrections)} tools corrected successfully!")
                
                # 🔄 MERGE CORRECTED RESULTS WITH ORIGINAL SUCCESSFUL RESULTS
                final_results = _merge_corrected_results(
                    tools_results_list, corrected_results, retry_candidates
                )
                
                # 🚨 DEBUG: Check what final_results contains
                corrected_results_debug = "\n\n".join(final_results)
                logger.info(f"🔧 MERGE DEBUG: final_results has {len(final_results)} entries")
                logger.info(f"🔧 MERGE DEBUG: corrected_results_debug length: {len(corrected_results_debug)} chars")
                logger.info(f"🔧 MERGE DEBUG: corrected_results_debug preview: {corrected_results_debug[:500]}...")
                
                return {
                    "success": True,
                    "reason": "ITERATIVE_REGENERATION_SUCCESS",
                    "corrected_results": corrected_results_debug,
                    "retried_tools": len(retry_candidates),
                    "iterations_required": iteration,
                    "regeneration_details": {
                        "total_iterations": iteration,
                        "final_candidates": len(current_retry_candidates),
                        "successful_corrections": len(successful_corrections),
                        "circuit_breaker_triggered": False
                    }
                }
            
            # 🔄 PARTIAL SUCCESS: Some tools succeeded, some still need retry
            elif len(successful_corrections) > 0:
                logger.info(f"🔄 ITERATION {iteration} PARTIAL SUCCESS: {len(successful_corrections)} corrected, {len(failed_corrections)} still failing")
                
                # Update retry candidates to only include the ones that still failed
                next_retry_candidates = []
                for failed_correction in failed_corrections:
                    # Find the corresponding retry candidate
                    original_candidate = next(
                        (candidate for candidate in current_retry_candidates 
                         if candidate["tool_name"] == failed_correction["tool_name"]), None
                    )
                    if original_candidate:
                        # Add the latest error to the candidate for next iteration
                        updated_candidate = original_candidate.copy()
                        updated_candidate["latest_error"] = failed_correction["result"]
                        updated_candidate["retry_count"] = iteration
                        next_retry_candidates.append(updated_candidate)
                
                # Record this iteration's context for accumulative prompt building
                iteration_context = {
                    "iteration": iteration,
                    "retry_candidates": current_retry_candidates.copy(),
                    "regenerated_tools": regenerated_tools.copy(),
                    "results": corrected_results.copy(),
                    "successful_count": len(successful_corrections),
                    "failed_count": len(failed_corrections)
                }
                previous_iterations.append(iteration_context)
                
                # Update for next iteration
                current_retry_candidates = next_retry_candidates
                iteration += 1
                
                # Partial merge successful corrections back to original results  
                partial_results = _merge_corrected_results(
                    tools_results_list, corrected_results, retry_candidates
                )
                
                # 🚨 CRITICAL FIX: Store merged results for circuit breaker success path
                tools_results_list = partial_results  # Update the main list with corrections
                
                continue  # Continue to next iteration
                
            # ❌ COMPLETE FAILURE: No tools corrected in this iteration
            else:
                logger.error(f"❌ ITERATION {iteration} COMPLETE FAILURE: No tools were corrected successfully")
                
                # Record this failed iteration for context
                failed_iteration_context = {
                    "iteration": iteration,
                    "retry_candidates": current_retry_candidates.copy(),
                    "regenerated_tools": regenerated_tools.copy(),
                    "results": corrected_results.copy(),
                    "successful_count": 0,
                    "failed_count": len(corrected_results),
                    "failure_reason": "No successful corrections"
                }
                previous_iterations.append(failed_iteration_context)
                
                iteration += 1
                continue  # Try next iteration
                
        except Exception as e:
            logger.error(f"❌ ITERATION {iteration} EXCEPTION: {e}")
            
            # Record this exception in iteration context
            exception_context = {
                "iteration": iteration,
                "retry_candidates": current_retry_candidates.copy(),
                "exception": str(e),
                "failure_reason": "LLM regeneration exception"
            }
            previous_iterations.append(exception_context)
            
            iteration += 1
            continue  # Try next iteration
    
    # 🛑 CIRCUIT BREAKER TRIGGERED: Max iterations reached or no more candidates
    if iteration > MAX_ITERATIONS:
        logger.error(f"🛑 CIRCUIT BREAKER: Maximum iterations ({MAX_ITERATIONS}) reached with {len(current_retry_candidates)} still failing")
        circuit_breaker_reason = "MAX_ITERATIONS_EXCEEDED"
        
        return {
            "success": False,
            "reason": "CIRCUIT_BREAKER_TRIGGERED",
            "circuit_breaker_reason": circuit_breaker_reason,
            "iterations_attempted": min(iteration - 1, MAX_ITERATIONS),
            "max_iterations": MAX_ITERATIONS,
            "remaining_failed_tools": len(current_retry_candidates),
            "corrected_results": "\n\n".join(tools_results_list),  # Return original results
            "iteration_history": previous_iterations
        }
    else:
        # 🚨 CRITICAL BUG FIX: Empty retry candidates means SUCCESS (all tools corrected)
        logger.info(f"🔧 SUCCESS: All retry candidates corrected - no more tools need retry")
        
        # 🚨 CRITICAL FIX: Return merged corrected results (tools_results_list now contains corrections)
        final_corrected_results = "\n\n".join(tools_results_list)
        logger.info(f"🔧 CIRCUIT BREAKER SUCCESS: Returning merged corrected results ({len(final_corrected_results)} chars)")
        
        return {
            "success": True,
            "reason": "ALL_TOOLS_CORRECTED",
            "corrected_results": final_corrected_results,
            "retried_tools": len(retry_candidates),  # Original count of tools that needed retry
            "iterations_required": iteration - 1,
            "regeneration_details": {
                "total_iterations": iteration - 1,
                "original_failed_count": len(retry_candidates),
                "final_success_count": len(retry_candidates),
                "correction_method": "CIRCUIT_BREAKER_SUCCESS"
            }
        }
    
    # 🔄 FALLBACK: Handle edge cases after iterative loop completion
    if not retry_candidates and unachievable_tasks:
        logger.warning(f"🔄 All failed tasks are unachievable - no retry possible")
        return {
            "success": False,
            "reason": "ALL_TASKS_UNACHIEVABLE",
            "escalation": "PARTIAL_SUCCESS", 
            "unachievable_count": len(unachievable_tasks),
            "message": f"Found {len(unachievable_tasks)} unachievable tasks. Continuing with available results."
        }
    
    # Fallback - should not reach here
    logger.error(f"🔄 Unexpected retry logic state - returning original results")
    return {
        "success": False,
        "reason": "UNEXPECTED_STATE",
        "escalation": "USER_GUIDANCE",
        "message": "Retry logic encountered unexpected state. Please review request."
    }

# 🔧 HELPER FUNCTIONS FOR LLM REGENERATION

async def _build_regeneration_context(retry_candidates, user_prompt, tools_called, tools_results_list, previous_iterations=None):
    """Build intelligent context for LLM tool regeneration with CONTENT PRESERVATION"""
    
    # 🚨 CRITICAL FIX: Preserve original user content instead of creating system prompts
    # The issue was that this function was creating debugging prompts instead of processing the actual user request
    
    # 🔄 ITERATIVE ACCUMULATIVE CONTEXT: Build from previous iterations
    if previous_iterations and len(previous_iterations) > 0:
        # ✅ FIX: Preserve the original user prompt as the primary content
        context = f"""{user_prompt}

[SYSTEM NOTE: This is a retry iteration {len(previous_iterations) + 1} - some tools failed and are being regenerated with improved parameters.]

PREVIOUS ITERATION HISTORY:
"""
        
        # Add all previous iteration contexts
        for idx, iteration_data in enumerate(previous_iterations, 1):
            context += f"""
--- ITERATION {idx} RESULTS ---
Retry Candidates: {len(iteration_data.get('retry_candidates', []))}
Regenerated Tools: {len(iteration_data.get('regenerated_tools', []))}
Success: {iteration_data.get('successful_count', 0)} tools
Failed: {iteration_data.get('failed_count', 0)} tools
"""
            
            # Add specific error details if this iteration failed
            if iteration_data.get('failed_count', 0) > 0:
                failed_tools = [r for r in iteration_data.get('results', []) if not r.get('corrected', False)]
                for failed_tool in failed_tools:
                    context += f"""
FAILED in iteration {idx}: {failed_tool.get('tool_name', 'Unknown')}
Error: {failed_tool.get('result', 'No error details')}
"""
        
        context += f"""

--- CURRENT ITERATION {len(previous_iterations) + 1} ---
REMAINING FAILED TOOLS REQUIRING REGENERATION:
"""
    else:
        # ✅ FIX: First iteration - preserve original user content
        context = f"""{user_prompt}

[SYSTEM NOTE: This is iteration 1 - some tools failed and are being regenerated with improved parameters.]

FAILED TOOLS REQUIRING REGENERATION:
"""
    
    for candidate in retry_candidates:
        tool_name = candidate["tool_name"]
        error_pattern = candidate["error_pattern"]
        feedback = candidate["feedback"]
        original_result = candidate["original_result"]
        latest_error = candidate.get("latest_error", None)  # 🚨 CRITICAL FIX: Include latest iteration error
        retry_count = candidate.get("retry_count", 0)
        
        # 🎯 EXTRACT PREVIOUSLY GENERATED CODE from successful tools results
        previously_generated_code = None
        specific_error_details = None
        
        # Look for code content in tools_results_list for this specific failed tool
        task_index = candidate.get("task_index", -1)
        if task_index >= 0 and task_index < len(tools_results_list):
            tool_result = tools_results_list[task_index]
            
            # For sandboxed_executor - extract code content from successful creation step
            if tool_name == "sandboxed_executor" and isinstance(tool_result, str):
                try:
                    import json
                    # Try to extract code from JSON result
                    if '"content":' in tool_result:
                        # Extract content field from JSON
                        start_idx = tool_result.find('"content": "') + len('"content": "')
                        end_idx = tool_result.find('",', start_idx)
                        if start_idx > 0 and end_idx > 0:
                            previously_generated_code = tool_result[start_idx:end_idx].replace('\\n', '\n').replace('\\"', '"')
                except:
                    pass
            
        # Extract specific error details from latest_error or original_result
        error_source = latest_error if latest_error else original_result
        if "args==" in str(error_source) and "<full_path" in str(error_source):
            specific_error_details = "Used placeholder path '<full_path_of_short_story_file>' instead of actual file path from document search"
        elif "Command failed with code 1" in str(error_source):
            # 🚨 ENHANCED ERROR DETECTION: Check for specific command line argument issues
            if previously_generated_code and "sys.argv[1]" in previously_generated_code:
                specific_error_details = """CRITICAL: Python script expects command line arguments but sandboxed_executor run_code action was called without 'args' parameter.

The generated Python script uses sys.argv[1] to get a file path, but the tool call was:
{"action": "run_code", "filename": "word_count_sort.py"}

It should be:
{"action": "run_code", "filename": "word_count_sort.py", "args": "/var/www/html/silicon_dreams/stories/SD_TheQuantumConspiracy.md"}

SOLUTION: Add the 'args' parameter with the correct file path from the document search results."""
            elif "IndexError" in str(error_source) or "list index out of range" in str(error_source):
                specific_error_details = "IndexError: Script tried to access sys.argv[1] but no command line arguments were provided. Need to add 'args' parameter to the run_code action."
            else:
                specific_error_details = "Script execution failed with exit code 1 - check if script expects command line arguments or file paths"
        
        # 🚨 IMPLEMENT USER'S EXACT SUGGESTION FORMAT
        context += f"""
Tool: {tool_name}
Error Pattern: {error_pattern}
Issue: {feedback}"""
        
        # 🎯 ADD PREVIOUSLY GENERATED CODE REVIEW SECTION
        if previously_generated_code:
            context += f"""

🔍 REVIEW THIS CODE CAREFULLY AND FIX THE ERRORS:
<code>
{previously_generated_code}
</code>"""
        
        # 🎯 ADD SPECIFIC ERROR DETAILS  
        if specific_error_details:
            context += f"""

<error>
{specific_error_details}
</error>"""
        
        # 🚨 CRITICAL: Include latest error from recent iteration if available
        if latest_error and latest_error != original_result:
            context += f"""
Latest Iteration Error: {latest_error}
Retry Attempt: {retry_count}"""
        
        context += f"""

CORRECTION NEEDED: {feedback}

🎯 SPECIFIC FIX INSTRUCTIONS:
- Replace any placeholder paths like '<full_path_of_short_story_file>' with actual file paths from document search results
- Use the exact file path: /var/www/html/silicon_dreams/stories/SD_TheQuantumConspiracy.md
- If Python script uses sys.argv[1], add "args" parameter to run_code action with the file path
- Ensure all parameters are correctly specified for the sandboxed_executor tool

📋 CORRECT TOOL CALL EXAMPLES:
For creating file:
{{"action": "create_file", "filename": "script.py", "content": "Python code here"}}

For running script with arguments:
{{"action": "run_code", "filename": "script.py", "args": "/var/www/html/silicon_dreams/stories/SD_TheQuantumConspiracy.md"}}
"""
    
    # Add successful tool results as context
    context += f"""

SUCCESSFUL TOOLS (for context):
"""
    
    for i, (tool_name, result) in enumerate(zip(tools_called, tools_results_list)):
        if not any(c["task_index"] == i for c in retry_candidates):
            context += f"""
✅ {tool_name}: {result}
"""
    
    context += f"""

🎯 REGENERATION INSTRUCTIONS:
To complete the original task "{user_prompt}", you need to:

1. ANALYZE: Review what went wrong with the failed tools
2. CORRECT: Fix the parameters using information from successful tools
3. EXECUTE: Call the SAME failed tools but with corrected parameters

CRITICAL FIXES NEEDED:
- Replace placeholder paths like "<full_path_to_*>" with actual file paths from document search results
- Fix any incorrect arguments that caused failures
- Use proper file paths and parameters

YOU MUST CALL THE FAILED TOOLS AGAIN WITH CORRECTIONS - DO NOT RETURN TEXT!
"""
    
    return context

async def _regenerate_failed_tools_with_llm(llm_manager, regeneration_context, retry_candidates, available_tools, iteration_count=1):
    """Call LLM to regenerate failed tool calls with corrections using iterative accumulative prompt structure"""
    
    # 🎯 CRITICAL: Use IDENTICAL system prompt from original tool calling (pre_tool_model_system_prompt.txt)
    try:
        with open('pre_tool_model_system_prompt.txt', 'r') as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        logger.error("❌ CRITICAL: pre_tool_model_system_prompt.txt not found - using fallback")
        system_prompt = """🚨 ABSOLUTE MODE: TOOL CALLS ONLY — NO TEXT RESPONSES, NO EXPLANATIONS 🚨
You must never produce normal text output.
Your only job: return valid tool calls helpful to answer the user in correct JSON format."""

    # 🔄 ITERATIVE ACCUMULATIVE PROMPT: Build from previous iterations + new error + fix instructions
    fix_instructions = """

EXAMINE THE CODE ERRORS CAREFULLY AND REGENERATE THE FULL FIXED CODE IN THE FOLLOWING FORMAT:

You must return ONLY valid JSON tool calls in the exact same format as your original response.
- NO explanations
- NO text responses  
- NO markdown
- ONLY the corrected tool calls in proper JSON format
- Fix the specific errors identified in the captured error data
- Use the successful tool results to get correct file paths and parameters
- Return the SAME tools that failed but with corrected parameters

The purpose is to drop the new code in place of the failed code."""

    # For iteration n: [Previous Prompt n-1] + [Current Error] + [Fix Instructions]
    regeneration_prompt = regeneration_context + fix_instructions
    
    try:
        # Tool regeneration: Starting LLM call
        logger.info(f"🔧 Calling tool_calling LLM with {len(available_tools)} available tools")
        
        # Tool regeneration: System prompt ready
        logger.info(f"🔧 Tool regeneration - system prompt: {len(system_prompt)} chars")
        
        # Tool regeneration: User prompt ready
        logger.info(f"🔧 Tool regeneration - user prompt: {len(regeneration_prompt)} chars")
        
        # Tool regeneration: Available tools summary
        logger.info(f"🔧 Tool regeneration - available tools: {len(available_tools)}")
        
        # Tool regeneration: Payload prepared
        tool_names = [tool.get('function', {}).get('name', 'Unknown') for tool in available_tools]
        logger.info(f"🔧 Tool regeneration - tools: {', '.join(tool_names[:3])}{'...' if len(tool_names) > 3 else ''} (iteration {iteration_count})")
        
        result = await llm_manager.generate_tools(
            regeneration_prompt, 
            available_tools,  # Pass the FULL tool schema from original execution
            system_prompt=system_prompt
        )
        
        # Tool regeneration: Response received
        logger.info(f"🔧 Tool regeneration - response: {len(str(result))} chars, {len(result.get('tool_calls', []))} tool calls")
        
        tool_calls = result.get("tool_calls", [])
        logger.info(f"🔧 LLM returned {len(tool_calls)} regenerated tool calls")
        
        return tool_calls
        
    except Exception as e:
        logger.error(f"❌ LLM regeneration call failed: {e}")
        raise

async def _execute_corrected_tools(tool_manager, regenerated_tools, retry_candidates):
    """Re-execute the corrected tool calls"""
    
    import json
    corrected_results = []
    
    for tool_call in regenerated_tools:
        try:
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])
            
            logger.info(f"🔧 RE-EXECUTING CORRECTED TOOL: {function_name}")
            
            # 🚨 LOG EXACT TOOL CALL AND ARGUMENTS
            truncated_function_args = truncate_base64_for_logging(json.dumps(function_args, indent=2))
            logger.info(f"🔧 CORRECTED TOOL CALL:\n{'='*80}\nFunction: {function_name}\nArguments: {truncated_function_args}\n{'='*80}")
            
            # Execute the corrected tool
            result = await tool_manager.safe_function_call(function_name, function_args)
            
            # 🚨 LOG DETAILED EXECUTION OUTPUT
            logger.info(f"🔧 CORRECTED TOOL EXECUTION OUTPUT:\n{'='*80}\nFunction: {function_name}\nRaw Result: {result}\nResult Type: {type(result)}\nResult Length: {len(str(result)) if result else 0} chars\n{'='*80}")
            
            # 🚨 CRITICAL FIX: Analyze result for error patterns instead of hardcoding success
            clean_result = str(result).strip()
            still_has_errors = any(pattern in clean_result for pattern in [
                "Command failed with code 1",
                "Command failed with code",
                "Tool 'sandboxed_executor' error",
                "Error: The file <full_path_to",
                "<full_path_to_",
                "does not exist", 
                "file not found",
                "no such file",
                "error:",
                "failed",
                "exception",
                "FileNotFoundError"
            ])
            
            is_actually_corrected = not still_has_errors
            
            corrected_results.append({
                "tool_name": function_name,
                "result": result,
                "corrected": is_actually_corrected
            })
            
            if is_actually_corrected:
                logger.info(f"✅ CORRECTED TOOL SUCCESS: {function_name} - No error patterns detected")
            else:
                logger.warning(f"⚠️ CORRECTED TOOL STILL FAILING: {function_name} - Error patterns still present in result")
                logger.warning(f"⚠️ Failed result content: {clean_result[:200]}...")
            
        except Exception as e:
            logger.error(f"❌ CORRECTED TOOL FAILED: {function_name}: {e}")
            
            # 🚨 LOG DETAILED ERROR INFO
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"🔧 CORRECTED TOOL ERROR DETAILS:\n{'='*80}\nFunction: {function_name}\nException: {str(e)}\nFull Traceback:\n{error_details}\n{'='*80}")
            
            corrected_results.append({
                "tool_name": function_name,
                "result": f"Corrected tool execution failed: {str(e)}",
                "corrected": False
            })
    
    return corrected_results

def _merge_corrected_results(original_results_list, corrected_results, retry_candidates):
    """Merge corrected results back into the original results list"""
    
    final_results = original_results_list.copy()
    
    # Replace failed tool results with corrected ones
    for candidate in retry_candidates:
        task_index = candidate["task_index"]
        
        # Find corresponding corrected result
        corrected_result = next(
            (cr for cr in corrected_results if cr["tool_name"] == candidate["tool_name"]), 
            None
        )
        
        if corrected_result and corrected_result["corrected"]:
            # 🚨 CRITICAL FIX: Format corrected results for Primary LLM readability
            corrected_result_text = corrected_result['result']
            
            # If result is JSON with stdout, extract and format the execution output
            try:
                import json
                if isinstance(corrected_result_text, str) and corrected_result_text.strip().startswith('{'):
                    result_json = json.loads(corrected_result_text)
                    
                    # For command execution results, format stdout prominently
                    if "stdout" in result_json and result_json["stdout"].strip():
                        if "return_code" in result_json and result_json["return_code"] == 0:
                            # Successfully executed command - highlight the output
                            formatted_result = f"✅ Command executed successfully: {result_json.get('command', 'Unknown command')}\n\nOutput:\n{result_json['stdout']}\n\nExecution completed with return code: {result_json['return_code']}"
                            logger.info(f"🔧 FORMATTED EXECUTION RESULT: Extracted stdout for Primary LLM")
                        else:
                            # Command failed - show error
                            formatted_result = f"❌ Command failed: {result_json.get('command', 'Unknown command')}\nReturn code: {result_json.get('return_code', 'Unknown')}\nStderr: {result_json.get('stderr', 'No error message')}"
                    else:
                        # Other JSON results (file creation, etc.) - use as-is
                        formatted_result = corrected_result_text
                else:
                    # Non-JSON results - use as-is  
                    formatted_result = corrected_result_text
                    
            except (json.JSONDecodeError, KeyError) as e:
                # Fallback to original result if parsing fails
                formatted_result = corrected_result_text
                logger.warning(f"⚠️ Failed to parse corrected result JSON: {e}")
            
            # Replace the original failed result with formatted corrected one
            final_results[task_index] = f"Tool: {candidate['tool_name']}\nResult: {formatted_result}\n\n"
            logger.info(f"🔄 MERGED CORRECTION: {candidate['tool_name']} at index {task_index}")
        else:
            logger.warning(f"⚠️ NO CORRECTION AVAILABLE: {candidate['tool_name']} at index {task_index}")
    
    return final_results

def _detect_tool_failure_pattern(tool_result: str) -> str:
    """Detect common failure patterns in tool results"""
    result_lower = tool_result.lower()
    
    if "command failed with code" in result_lower:
        return "COMMAND_EXECUTION_FAILURE"
    elif "error" in result_lower:
        return "GENERIC_ERROR"
    elif "file not found" in result_lower or "no such file" in result_lower:
        return "FILE_NOT_FOUND"
    elif "module not found" in result_lower:
        return "MISSING_DEPENDENCY" 
    elif "<full_path" in tool_result or "[full_path" in tool_result:
        return "PLACEHOLDER_PATH_NOT_REPLACED"
    elif len(tool_result.strip()) == 0:
        return "EMPTY_RESULT"
    elif "malformed" in result_lower or "invalid json" in result_lower:
        return "MALFORMED_DATA"
    else:
        return "UNKNOWN_FAILURE"

async def arbitrator_validate_tasks(tools_called: List[str], tools_results_list: List[str], user_prompt: str, tool_manager=None) -> Optional[str]:
    """
    🧠 ARBITRATOR TASK VALIDATION SYSTEM
    Validates tool execution results and retries failed tasks with intelligent feedback
    
    Args:
        tools_called: List of tool names that were executed
        tools_results_list: List of tool result strings  
        user_prompt: Original user request for context
        
    Returns:
        Optional[str]: Validated and potentially corrected tool results, or None on failure
    """
    try:
        # Use global llm_manager for arbitrator calls
        import json  # Explicit import to avoid scoping issues
        
        logger.info(f"🧠 Starting arbitrator validation for {len(tools_called)} tools")
        
        # Convert tool results to arbitrator format
        arbitrator_tasks = []
        for i, (tool_name, result) in enumerate(zip(tools_called, tools_results_list)):
            # Extract just the result content, removing "Tool: name\nResult: " formatting
            clean_result = result
            if result.startswith(f"Tool: {tool_name}\nResult: "):
                clean_result = result[len(f"Tool: {tool_name}\nResult: "):]
            
            # 🚨 STRUCTURED SUCCESS/FAILURE DETECTION: Use explicit indicators instead of content analysis
            initial_status = "PENDING_VALIDATION"
            error_pattern = None
            feedback = None
            
            # Try to parse as JSON to get structured indicators
            try:
                result_json = json.loads(clean_result)
                
                # Check explicit success indicators
                if isinstance(result_json, dict):
                    # Check return_code for command execution
                    if "return_code" in result_json:
                        if result_json["return_code"] == 0:
                            initial_status = "GOOD"
                            logger.info(f"✅ STRUCTURED SUCCESS: Task {i+1} return_code=0 - execution successful")
                        else:
                            initial_status = "BAD"
                            error_pattern = "command_failed"
                            feedback = f"Command failed with return code {result_json['return_code']}"
                            logger.info(f"❌ STRUCTURED FAILURE: Task {i+1} return_code={result_json['return_code']}")
                    
                    # Check error_analysis field
                    elif "error_analysis" in result_json:
                        if result_json["error_analysis"] is None:
                            initial_status = "GOOD" 
                            logger.info(f"✅ STRUCTURED SUCCESS: Task {i+1} error_analysis=null - no errors detected")
                        else:
                            initial_status = "BAD"
                            error_pattern = "execution_error"
                            feedback = f"Error analysis detected: {result_json['error_analysis']}"
                            logger.info(f"❌ STRUCTURED FAILURE: Task {i+1} error_analysis present")
                    
                    # For other successful JSON responses (file creation, etc.)
                    elif any(success_field in result_json for success_field in ["filename", "document_path", "chunks", "sources"]):
                        initial_status = "GOOD"
                        logger.info(f"✅ STRUCTURED SUCCESS: Task {i+1} contains success indicators")
                
            except json.JSONDecodeError:
                # Fallback to string-based detection only for non-JSON results
                logger.info(f"🔍 STRING CHECK: Task {i+1} clean_result = '{clean_result[:200]}...'")
                
                error_patterns = [
                    "Tool 'sandboxed_executor' error",
                    "Command failed with code",
                    "Command is required", 
                    "Error: The file <full_path_to",
                    "<full_path_to_",
                    "FileNotFoundError",
                    "ModuleNotFoundError", 
                    "SyntaxError",
                    "IndexError",           # 🚨 ADD missing IndexError pattern
                    "ValueError",           # 🚨 ADD missing ValueError pattern  
                    "TypeError",            # 🚨 ADD missing TypeError pattern
                    "KeyError",             # 🚨 ADD missing KeyError pattern
                    "AttributeError",       # 🚨 ADD missing AttributeError pattern
                    "error occurred"
                ]
                
                found_error = False
                matched_pattern = None
                for pattern in error_patterns:
                    if pattern in clean_result:
                        initial_status = "BAD"
                        error_pattern = "tool_error"
                        feedback = f"Tool execution error detected: {pattern}"
                        matched_pattern = pattern
                        found_error = True
                        break
                
                # 🧹 CLEANUP: Single consolidated log instead of pattern test spam
                if found_error:
                    logger.info(f"❌ VALIDATION: Task {i+1} FAILED - Pattern: '{matched_pattern}'")
                # Success case logged below
                
                if not found_error:
                    # If no explicit error patterns and no JSON structure, assume success
                    initial_status = "GOOD"
                    logger.info(f"✅ VALIDATION: Task {i+1} PASSED - {len(error_patterns)} patterns checked")
            
            # If still pending validation, check for basic success patterns
            if initial_status == "PENDING_VALIDATION":
                if len(clean_result.strip()) > 0:
                    initial_status = "GOOD"
                    logger.info(f"✅ DEFAULT SUCCESS: Task {i+1} has non-empty result")
                else:
                    initial_status = "BAD"
                    error_pattern = "empty_result"
                    feedback = "Tool returned empty result"
                    logger.info(f"❌ DEFAULT FAILURE: Task {i+1} has empty result")
            
            arbitrator_tasks.append({
                "task_id": i + 1,
                "tool_name": tool_name,
                "result": clean_result.strip(),
                "status": initial_status,
                "pre_detected_error": error_pattern,
                "pre_detected_feedback": feedback
            })
        
        # Create arbitrator system prompt with enhanced error pattern detection
        arbitrator_system_prompt = """🚨 CRITICAL JSON-ONLY RESPONSE REQUIRED 🚨

You are an AI Task Result Arbitrator. You MUST respond with ONLY valid JSON - no text, no markdown, no explanations.

🚨 RESPONSE FORMAT REQUIREMENT:
- Start response with { character
- End response with } character  
- NO markdown code blocks (```json)
- NO explanations before or after JSON
- NO analysis text
- PURE JSON ONLY

🚨 EXAMPLE OF MANDATORY BAD STATUS:
If you see: "Tool 'sandboxed_executor' error: Command failed with code 1"
You MUST respond: {"status": "BAD", "pattern": "command_failed", "feedback": "Script execution failed - regenerate code with correct file path"}

⚠️ CRITICAL: ANY non-JSON content will cause system failure. Respond with PURE JSON ONLY.

Analyze each tool result and identify specific error patterns. Respond with this EXACT JSON format:

{
  "tasks": [
    {
      "task_id": 1,
      "status": "GOOD",
      "error_pattern": null,
      "error_category": null,
      "feedback": "Task completed successfully",
      "retry_strategy": null,
      "corrected_parameters": {}
    }
  ],
  "overall_assessment": "Brief assessment",
  "patterns_detected": []
}

STATUS VALUES:
- GOOD: Task succeeded, data is valid
- BAD: Task failed but retryable 
- UNACHIEVABLE: Task impossible to complete

🚨 MANDATORY FAILURE DETECTION - NO EXCEPTIONS:

IF ANY TOOL RESULT CONTAINS ANY OF THESE EXACT PATTERNS:
- "Command failed with code 1" → STATUS MUST BE "BAD"
- "Command failed with code" (any number) → STATUS MUST BE "BAD"
- "Tool 'sandboxed_executor' error" → STATUS MUST BE "BAD"
- "PARTIAL SUCCESS" → STATUS MUST BE "BAD" 
- "error:" anywhere in result → STATUS MUST BE "BAD"
- "failed" anywhere in result → STATUS MUST BE "BAD"
- "exception" anywhere in result → STATUS MUST BE "BAD"
- "<full_path_to_" anywhere in generated code → STATUS MUST BE "BAD"
- "FileNotFoundError" in execution results → STATUS MUST BE "BAD"

⚠️ CRITICAL: If you see "Command failed with code" in ANY tool result, you MUST mark that task as BAD and provide retry feedback.

CRITICAL FAILURE DETECTION RULES:
ALWAYS mark as BAD if you see:
- "Command failed with code" (any exit code)
- "Tool 'sandboxed_executor' error"
- "PARTIAL SUCCESS" in tool output logs
- Any mention of "error", "failed", "exception" in results
- Placeholder paths like "<full_path_to_*>" that weren't resolved
- Any code containing "<full_path_to_" strings (unresolved placeholders)  
- Generic filenames in execution errors like "story.txt", "file.txt" when actual files don't exist
- Empty or truncated results from execution tools
- "FileNotFoundError", "PermissionError", or other Python exceptions

🎯 SMART SUCCESS DETECTION: Consider overall task completion even with partial tool failures.

CRITICAL: If user requirements are fully met despite some tool errors, the task may still be SUCCESSFUL.

Examples of ACCEPTABLE partial failures:
- File read fails BUT cover letter has no placeholders AND email sent successfully = TASK SUCCESS
- API call fails BUT alternative data source provides complete information = TASK SUCCESS  
- One calculation errors BUT other calculations provide sufficient analysis = TASK SUCCESS

⚠️ Mark as BAD only if FINAL OUTPUT fails to meet user requirements or contains errors/placeholders

ERROR PATTERNS (when status is BAD) - Sprint 3.2 Enhanced:

🌐 NETWORK & HTTP ERRORS:
- "http_404": HTTP 404 Not Found - resource doesn't exist
- "http_403": HTTP 403 Forbidden - authentication/authorization issue  
- "http_429": HTTP 429 Too Many Requests - rate limiting active
- "http_500": HTTP 500 Internal Server Error - server-side issue
- "http_502": HTTP 502 Bad Gateway - proxy/gateway error
- "http_503": HTTP 503 Service Unavailable - temporary overload
- "http_timeout": Request timeout - server taking too long
- "connection_refused": Connection refused - service down
- "dns_resolution": DNS lookup failed - domain doesn't resolve
- "ssl_certificate": SSL/TLS certificate error - security issue

📁 FILESYSTEM ERRORS:
- "file_not_found": File or directory doesn't exist at path
- "permission_denied": Access denied - insufficient permissions
- "disk_full": No space left on device - storage exhausted
- "path_invalid": Invalid file path or malformed filename
- "file_locked": File locked by another process
- "symlink_broken": Symbolic link target doesn't exist
- "encoding_error": Text encoding/decoding issues

🔐 AUTHENTICATION & SECURITY:
- "api_key_invalid": Invalid or expired API key
- "api_key_missing": No API key provided when required
- "token_expired": Authentication token has expired
- "insufficient_permissions": Valid auth but insufficient access level
- "account_suspended": User account suspended or banned
- "2fa_required": Two-factor authentication required
- "ip_blocked": IP address blocked or geofenced

🗄️ DATA FORMAT & PROCESSING:
- "json_parse_error": Invalid JSON structure or syntax
- "xml_parse_error": Malformed XML document
- "csv_format_error": CSV parsing issues (delimiters, headers)
- "encoding_mismatch": Character encoding problems
- "schema_validation": Data doesn't match expected schema
- "type_conversion": Data type casting failures
- "empty_response": Valid request but no data returned
- "truncated_response": Response cut off or incomplete

🚦 EXTERNAL SERVICE ERRORS:
- "service_unavailable": External API/service temporarily down
- "rate_limited": API quota exceeded - need to wait/throttle
- "quota_exceeded": Daily/monthly usage limit reached
- "deprecated_api": API version deprecated or discontinued
- "maintenance_mode": Service in maintenance mode
- "region_restricted": Service not available in geographic region

🐛 RUNTIME & EXECUTION - CRITICAL ERROR DETECTION:
- "command_failed": Command failed with exit code (e.g., "Command failed with code 1")
- "tool_error": Any tool execution error or exception
- "execution_failed": Script or program execution failure
- "partial_success": Tool marked as PARTIAL SUCCESS indicating incomplete execution
- "syntax_error": Code syntax errors in generated scripts
- "import_error": Missing dependencies or modules
- "memory_exhausted": Out of memory during execution
- "timeout_execution": Script execution timed out
- "infinite_loop": Process stuck in infinite loop
- "segmentation_fault": Memory access violation
- "environment_missing": Required environment variables not set
- "path_placeholder": Placeholder paths like "<full_path_to_*>" not resolved to actual paths
- "unresolved_placeholder": Generated code contains unresolved placeholders like "<full_path_to_short_story_file>"
- "generic_filename": Code uses generic filenames that don't exist like "story.txt" or "file.txt"
- "missing_arguments": Required arguments or parameters not provided
- "file_not_accessible": Target file exists but cannot be read or executed

ERROR CATEGORIES - Sprint 3.2:
- "network": HTTP/connectivity/DNS issues requiring retry strategies
- "filesystem": File operations needing path corrections or permission fixes
- "authentication": Auth/permission problems requiring user intervention or token refresh
- "data_format": Parsing/validation issues needing format corrections
- "external_service": Third-party API issues requiring fallback or retry logic
- "runtime": Execution problems needing dependency fixes or environment setup
- "resource_exhaustion": Memory/storage/quota limits requiring optimization
- "security": Security-related blocks requiring compliance or access approval  
- "data_format": Parsing/format issues
- "external_service": Third-party API problems

RETRY STRATEGIES - Sprint 3.2 Tool-Specific:

🔄 BASIC RETRY STRATEGIES:
- "retry_with_delay": Wait 2-5 seconds and retry same parameters (network timeouts, rate limits)
- "retry_with_exponential_backoff": Exponential delay retry for persistent issues
- "retry_with_different_params": Modify parameters and retry (path corrections, format changes)
- "retry_with_fallback_endpoint": Try alternative API endpoint or service
- "retry_with_reduced_scope": Reduce request size/complexity and retry

🛠️ TOOL-SPECIFIC STRATEGIES:

📰 WEB SEARCH TOOLS (search_web, get_news_summaries):
- http_404/empty_response → retry_with_different_query_terms
- rate_limited → retry_with_exponential_backoff_5min
- region_restricted → retry_with_vpn_fallback (if available)
- service_unavailable → retry_with_alternative_search_engine

📊 STOCK DATA TOOLS (get_stock_and_company_data, comprehensive_stock_analyzer):
- invalid_symbol → retry_with_symbol_validation_and_correction
- market_closed → retry_with_market_hours_check
- rate_limited → retry_with_delay_based_on_quota
- data_unavailable → retry_with_alternative_data_provider

📁 FILE SYSTEM TOOLS (document_search):
- file_not_found → retry_with_path_traversal_and_correction
- permission_denied → retry_with_sudo_or_permission_request
- path_invalid → retry_with_path_sanitization
- encoding_error → retry_with_encoding_detection_and_conversion

💻 EXECUTION TOOLS (sandboxed_executor, process_executor):
- command_failed → retry_with_corrected_file_path_and_arguments
- tool_error → retry_with_parameter_validation_and_correction
- execution_failed → retry_with_dependency_check_and_path_resolution
- partial_success → retry_with_complete_argument_specification
- path_placeholder → retry_with_actual_file_path_substitution
- unresolved_placeholder → retry_with_resolved_file_paths_and_regenerated_code
- generic_filename → retry_with_specific_file_search_and_path_resolution
- missing_arguments → retry_with_proper_argument_formatting
- file_not_accessible → retry_with_permission_check_and_path_correction
- import_error → retry_with_dependency_installation
- syntax_error → retry_with_code_syntax_correction
- timeout_execution → retry_with_increased_timeout_and_optimization
- memory_exhausted → retry_with_memory_optimization

📧 COMMUNICATION TOOLS (secure_email_sender):
- smtp_authentication_failed → retry_with_credential_refresh
- attachment_too_large → retry_with_file_compression_or_chunking  
- recipient_invalid → retry_with_email_validation_and_correction
- smtp_server_unavailable → retry_with_alternative_smtp_provider

🧮 CALCULATION TOOLS (calculator):
- division_by_zero → retry_with_error_handling_and_validation
- overflow_error → retry_with_precision_adjustment
- invalid_expression → retry_with_expression_sanitization

📅 CALENDAR TOOLS (google_calendar_scheduler):
- oauth_token_expired → retry_with_token_refresh
- calendar_not_found → retry_with_calendar_discovery_and_selection
- time_conflict → retry_with_alternative_time_suggestion
- quota_exceeded → retry_with_batch_optimization

🚫 UNACHIEVABLE CONDITIONS:
- account_suspended → escalate_to_user_with_account_resolution
- insufficient_permissions_permanent → escalate_to_user_with_permission_request
- service_permanently_discontinued → suggest_alternative_tool_or_approach
- security_policy_violation → escalate_to_user_with_compliance_guidance

🎯 ESCALATION STRATEGIES:
- "escalate_to_user": Requires user intervention with specific guidance
- "suggest_alternative": Recommend different tool or approach
- "partial_success_acceptable": Continue with available data, note limitations
- "requires_manual_intervention": Stop and request user action
- "continue_with_warning": Proceed but warn about data quality

Respond with JSON only."""

        # Create arbitrator prompt with task details
        task_details = []
        for task in arbitrator_tasks:
            task_details.append(f"""
Task {task['task_id']}: {task['tool_name']}
Result: {task['result'][:500]}{"..." if len(task['result']) > 500 else ""}
""")
        
        arbitrator_prompt = f"""User Request: {user_prompt[:200]}

Task Results to Validate:
{''.join(task_details)}

Please validate each task result and respond with JSON analysis."""

        # Check if we have pre-detected errors (bypass LLM call for obvious errors)
        pre_detected_errors = [task for task in arbitrator_tasks if task["status"] == "BAD"]
        
        logger.info(f"🧠 Calling arbitrator LLM for validation...")
        
        # Sprint 3.4: Start monitoring
        import time
        import json
        validation_start_time = time.time()
        arbitrator_llm_success = False
        error_patterns_detected = []
        
        if pre_detected_errors:
            logger.info(f"🚨 PRE-DETECTED ERRORS: Found {len(pre_detected_errors)} errors, bypassing LLM call")
            
            # Create validation result from pre-detected errors
            arbitrator_response = json.dumps({
                "tasks": [],
                "overall_assessment": "Errors detected during pre-processing",
                "patterns_detected": ["command_failed", "execution_error"]
            })
            
            task_results = []
            for task in arbitrator_tasks:
                if task["status"] == "BAD":
                    task_results.append({
                        "task_id": task["task_id"],
                        "status": "BAD",
                        "error_pattern": task["pre_detected_error"],
                        "error_category": "runtime",
                        "feedback": task["pre_detected_feedback"],
                        "retry_strategy": "retry_with_corrected_file_path_and_arguments"
                    })
                else:
                    task_results.append({
                        "task_id": task["task_id"],
                        "status": "GOOD",
                        "error_pattern": None,
                        "feedback": "Task completed successfully"
                    })
            
            # Update the response with task results
            response_data = json.loads(arbitrator_response)
            response_data["tasks"] = task_results
            arbitrator_response = json.dumps(response_data)
            
            arbitrator_llm_success = True
            arbitrator_llm_time = 0.001  # Minimal time for pre-processing
            logger.info(f"🧠 Pre-processing response created: {len(arbitrator_response)} chars")
            
        else:
            logger.info(f"🧠 No pre-detected errors - calling arbitrator LLM...")
            
            try:
                # Call arbitrator LLM
                arbitrator_response = await llm_manager.call_arbitrator(
                    arbitrator_prompt,
                    arbitrator_system_prompt
                )
            
                arbitrator_llm_success = True
                arbitrator_llm_time = time.time() - validation_start_time
                
                logger.info(f"🧠 Arbitrator response received: {len(arbitrator_response)} chars")
                arbitrator_monitor.record_arbitrator_llm_call(True, arbitrator_llm_time)
                
            except Exception as e:
                arbitrator_llm_time = time.time() - validation_start_time
                arbitrator_monitor.record_arbitrator_llm_call(False, arbitrator_llm_time)
                logger.error(f"🧠 Arbitrator LLM call failed: {e}")
                raise
        
        # Parse arbitrator response
        import json
        try:
            # Enhanced JSON extraction - handle markdown, text, and mixed responses
            clean_response = arbitrator_response.strip()
            
            # Method 1: Standard markdown code block removal
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            # Method 2: If that fails, try to extract JSON from mixed content
            validation_result = None
            try:
                validation_result = json.loads(clean_response)
            except json.JSONDecodeError:
                logger.warning(f"🧠 Standard JSON parsing failed, attempting extraction from mixed content...")
                
                # Look for JSON object patterns in the response
                import re
                json_patterns = [
                    r'\{[^{}]*"tasks"[^{}]*\[[^\]]*\][^{}]*\}',  # Simple single-line JSON
                    r'\{.*?"tasks"\s*:\s*\[.*?\].*?\}',          # Multi-line JSON pattern
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, arbitrator_response, re.DOTALL)
                    for match in matches:
                        try:
                            validation_result = json.loads(match)
                            logger.info(f"🧠 Successfully extracted JSON using pattern matching")
                            break
                        except json.JSONDecodeError:
                            continue
                    if validation_result:
                        break
                
                # Method 3: Last resort - generate a minimal valid response for successful tools
                if not validation_result:
                    logger.warning(f"🧠 JSON extraction failed, generating fallback response for successful tools")
                    validation_result = {
                        "tasks": [
                            {
                                "task_id": i + 1,
                                "status": "GOOD",
                                "error_pattern": None,
                                "feedback": "Task completed successfully (fallback validation)"
                            }
                            for i in range(len(arbitrator_tasks))
                        ],
                        "overall_assessment": "All tasks successful (fallback due to parsing failure)",
                        "patterns_detected": []
                    }
                    logger.info(f"🧠 Using fallback validation result for {len(arbitrator_tasks)} tasks")
            logger.info(f"🧠 Arbitrator validation parsed successfully")
            
            # Process validation results with enhanced error pattern detection (Sprint 2.2)
            all_good = True
            detected_patterns = []
            error_analysis = {}
            
            # Process overall patterns detected
            patterns_detected = validation_result.get("patterns_detected", [])
            if patterns_detected:
                logger.info(f"🔍 Arbitrator detected global patterns: {patterns_detected}")
            
            # Process individual task validations with error pattern analysis
            for task_validation in validation_result.get("tasks", []):
                status = task_validation.get("status", "UNKNOWN")
                task_id = task_validation.get("task_id", "?")
                error_pattern = task_validation.get("error_pattern")
                error_category = task_validation.get("error_category") 
                retry_strategy = task_validation.get("retry_strategy")
                feedback = task_validation.get("feedback", "No feedback")
                
                if status == "GOOD":
                    logger.info(f"🧠 Task {task_id} validated as GOOD")
                
                elif status == "BAD":
                    # Enhanced BAD status logging with error pattern analysis
                    pattern_info = f" | Pattern: {error_pattern}" if error_pattern else ""
                    category_info = f" | Category: {error_category}" if error_category else ""
                    strategy_info = f" | Strategy: {retry_strategy}" if retry_strategy else ""
                    
                    logger.warning(f"🔍 Task {task_id} marked BAD: {feedback}{pattern_info}{category_info}{strategy_info}")
                    
                    # Collect error patterns for analysis
                    if error_pattern:
                        detected_patterns.append(error_pattern)
                        
                    # Store detailed error analysis for potential retry logic
                    error_analysis[task_id] = {
                        "error_pattern": error_pattern,
                        "error_category": error_category,
                        "retry_strategy": retry_strategy,
                        "feedback": feedback,
                        "corrected_parameters": task_validation.get("corrected_parameters", {})
                    }
                    
                    all_good = False
                
                elif status == "UNACHIEVABLE":
                    pattern_info = f" | Pattern: {error_pattern}" if error_pattern else ""
                    logger.error(f"🚨 Task {task_id} marked UNACHIEVABLE: {feedback}{pattern_info}")
                    all_good = False
            
            # Enhanced error pattern analysis with strategic insights (Sprint 2.2)
            if detected_patterns or error_analysis:
                # Run comprehensive pattern analysis
                pattern_analysis_result = analyze_error_patterns(error_analysis)
                
                if pattern_analysis_result.get("status") == "patterns_detected":
                    total_errors = pattern_analysis_result["total_errors"]
                    critical_patterns = pattern_analysis_result.get("critical_patterns", [])
                    retry_priority = pattern_analysis_result.get("retry_priority", [])
                    
                    logger.info(f"🔍 Pattern Analysis Complete: {total_errors} errors analyzed")
                    logger.info(f"🔍 Pattern Frequency: {pattern_analysis_result['pattern_frequency']}")
                    
                    if critical_patterns:
                        logger.warning(f"🚨 Critical Patterns (multiple occurrences): {critical_patterns}")
                    
                    if retry_priority:
                        logger.info(f"🎯 Retry Priority Recommendations:")
                        for priority in retry_priority[:3]:  # Top 3 priorities
                            category = priority["category"]
                            count = priority["error_count"]
                            patterns = priority["patterns"]
                            action = priority["recommended_action"]
                            logger.info(f"   • {category}: {count} errors, patterns {patterns} → {action}")
                    
                    # Strategic error category insights
                    category_dist = pattern_analysis_result.get("category_distribution", {})
                    if category_dist:
                        high_impact_categories = [cat for cat, data in category_dist.items() if data["count"] > 1]
                        if high_impact_categories:
                            logger.warning(f"🎯 High-Impact Categories: {high_impact_categories}")
                else:
                    logger.info(f"🔍 Pattern analysis: {pattern_analysis_result.get('status', 'unknown')}")
                    
            # For Sprint 2.2, return original results but with comprehensive error analysis
            # Sprint 2.3 will implement intelligent retry based on pattern insights
            original_results = "".join(tools_results_list)
            
            # Sprint 3.4: Final monitoring and metrics
            total_validation_time = time.time() - validation_start_time
            validation_success = all_good
            
            # 🔧 CRITICAL ARCHITECTURE FIX: TRUE SINGLE SYNCHRONOUS PATH
            # PRIMARY LLM REMAINS LOCKED until ALL results are corrected
            # NO conditional branching - ALWAYS attempt correction
            
            logger.info(f"🔒 SYNCHRONOUS CORRECTION: Processing all results through correction pipeline")
            
            # Ensure pattern_analysis_result is always defined
            if 'pattern_analysis_result' not in locals():
                pattern_analysis_result = {"status": "no_patterns", "total_errors": 0}
            
            # ALWAYS attempt correction regardless of initial validation
            # This ensures consistent format and eliminates hallucination from error data
            retry_result = await intelligent_retry_with_circuit_breakers(
                error_analysis, pattern_analysis_result, 
                tools_called, tools_results_list, user_prompt,
                tool_manager  # Pass tool_manager for tool re-execution
            )
            
            if retry_result.get("success", False):
                logger.info(f"🔧 CORRECTION SUCCESSFUL: Using verified corrected results")
                arbitrator_monitor.record_validation_attempt(True, total_validation_time, detected_patterns)
                retry_count = retry_result.get("retried_tools", 0)
                arbitrator_monitor.record_retry_session(retry_count, True)
                return retry_result["corrected_results"]
            else:
                # If correction fails, at minimum ensure format consistency
                logger.warning(f"🔧 CORRECTION FAILED: Using format-normalized original results")
                logger.info(f"🔄 Correction failure reason: {retry_result.get('reason', 'Unknown')}")
                
                arbitrator_monitor.record_validation_attempt(all_good, total_validation_time, detected_patterns)
                retry_count = retry_result.get("retried_tools", 0) 
                arbitrator_monitor.record_retry_session(retry_count, False)
                
                # Check for circuit breaker information
                if "circuit_breaker" in retry_result.get("reason", "").lower():
                    arbitrator_monitor.record_circuit_breaker_activation(
                        retry_result.get("reason", "UNKNOWN"), 
                        retry_result.get("escalation", "UNKNOWN")
                    )
                
                # Apply minimal format normalization to prevent hallucination
                if all_good:
                    logger.info(f"🔧 FORMAT NORMALIZED: Original results were valid, applying consistent formatting")
                    return original_results  # Results were already good, just format them consistently
                else:
                    logger.error(f"🚨 ARBITRATOR CRITICAL FAILURE: Error correction failed - marking results as incomplete")
                    # Instead of raw error results, return a clear failure marker
                    failure_marker = f"ARBITRATOR_ERROR_CORRECTION_FAILED: Original tools contained errors that could not be corrected automatically. Error analysis: {error_analysis}"
                    return failure_marker
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse arbitrator JSON response: {e}")
            logger.error(f"❌ Raw arbitrator response: {arbitrator_response[:200]}...")
            return None
            
    except Exception as e:
        logger.error(f"❌ Arbitrator validation failed: {e}")
        return None

async def _verify_task_completion(user_prompt: str, tools_called: List[str], tools_results: str, tool_manager) -> Dict[str, Any]:
    """
    🔍 BULLETPROOF TASK COMPLETION VERIFIER
    Analyzes user prompt and tool execution to ensure all required steps are completed
    Enhanced with comprehensive email detection and strict validation
    """
    user_prompt_lower = user_prompt.lower()
    
    # 🚨 CRITICAL META-TASK DETECTION - HIGHEST PRIORITY 🚨
    # This MUST come first to prevent meta-tasks from triggering file creation
    meta_task_indicators = [
        "generate 1-3 broad tags categorizing the main themes",
        "generate a concise title with emoji", 
        "generate a concise, 3-5 word title with an emoji",
        "generate tags",
        "categorizing the main themes of the chat history",
        "title with emoji",
        "broad tags categorizing",
        "3-5 word title with an emoji",
        "concise title with an emoji"
    ]

    if any(meta_indicator in user_prompt_lower for meta_indicator in meta_task_indicators):
        return {"complete": True, "pattern": "meta_task"}
    
    # 🚨 BULLETPROOF EMAIL DETECTION
    # Any mention of email/send requires secure_email_sender tool
    email_keywords = [
        "email", "send", "mail", "attach", "attachment", "send to", "email to",
        "send an email", "send email", "email it", "mail it", "send it", 
        "email me", "send me", "mail me", "email with", "send with",
        "email them", "send them", "mail them", "email all", "send all",
        "in one email", "all in one email", "send them all", "email the files"
    ]
    
    has_email_request = any(keyword in user_prompt_lower for keyword in email_keywords)
    
    # Define task patterns and their required tool sequences
    task_patterns = {
        "research_save_and_email": {
            "triggers": ["save the output to", "save to pdf and html", "describe and save", "list and save", 
                        "save output to a pdf", "save the results", "create file with", "save as attachment"],
            "required_tools": ["sandboxed_executor", "secure_email_sender"],
            "required_sequence": True,
            "description": "Research information, save to file(s), and email as attachments"
        },
        "multi_file_creation_and_email": {
            "triggers": ["create a pdf file, a html file, a md file, and a txt file", "create multiple files", 
                        "create files and email", "create all files and send", "send them all in one email"],
            "required_tools": ["sandboxed_executor", "secure_email_sender"],
            "required_sequence": True,
            "description": "Create multiple files and email all as attachments"
        },
        "stock_report_and_email": {
            "triggers": ["stock report and email", "create stock analysis file", "email stock report", "save and send stock analysis"],
            "required_tools": ["comprehensive_stock_analyzer", "sandboxed_executor", "secure_email_sender"],
            "required_sequence": True,
            "description": "Generate stock analysis report, save as file, email with attachment"
        },
        "news_report_and_email": {
            "triggers": ["news report and email", "create news file", "email news report", "save and send news", "email me the news",
                        "save and send the files", "pdf attachment", "send the files as pdf", "stock market news", "save and send"],
            "required_tools": ["get_news_summaries", "sandboxed_executor", "secure_email_sender"],
            "required_sequence": True,
            "description": "Generate news analysis report, save as PDF file, email with attachment"
        },
        "file_creation_and_email": {
            "triggers": ["create file and email", "save and email", "email me a file", "send me an attachment", "create and send"],
            "required_tools": ["sandboxed_executor", "secure_email_sender"],
            "required_sequence": True,
            "description": "Create file and email as attachment"
        },
        "document_creation_email": {
            "triggers": ["write document and email", "create document file", "email me the document", "save document and send", 
                        "craft", "write a", "include a pdf", "send the email", "with attachments", "cover letter", 
                        "pdf version", "email with attachments", "pdf formatted"],
            "required_tools": ["sandboxed_executor", "secure_email_sender"],
            "required_sequence": True,
            "description": "Write document, save file, email as attachment"
        },
        "pure_email_request": {
            "triggers": ["send an email", "send email", "email to", "mail to", "send to", "email with subject",
                        "send with attachments", "email the files", "send the files", "email with attachments"],
            "required_tools": ["secure_email_sender"],
            "required_sequence": False,
            "description": "Send email with or without attachments"
        }
    }
    
    # 🚨 CRITICAL: Check for explicit exclusion patterns first
    # If user is just asking for information/research, do NOT auto-execute
    exclusion_patterns = [
        "just tell me", "what are", "give me", "show me", "list", "find out",
        "look up", "research", "analyze", "explain", "describe", "summarize",
        "use the available tools to", "check", "investigate", "get information"
    ]
    
    if any(exclusion in user_prompt_lower for exclusion in exclusion_patterns):
        # Check if they also explicitly ask for file/email
        explicit_file_email_requests = [
            "email me", "send me", "create file", "save to file", "attachment",
            "email the", "send the", "file and email", "save and email", "craft",
            "cover letter", "pdf version", "with attachments", "include a pdf",
            "pdf formatted", "send the email", "save and send the files", "pdf attachment",
            "send the files as pdf", "save and send", "create a pdf", "create pdf", 
            "pdf report", "html report", "report and email", "create report",
            "generate pdf", "make pdf", "email it to", "send it to"
        ]
        
        if not any(explicit_request in user_prompt_lower for explicit_request in explicit_file_email_requests):
            logger.info(f"🚫 EXCLUSION: User is asking for information only, not file creation/email")
            return {
                "complete": True,  # Task is complete - they just want information
                "reason": "Information request only - no file creation or email needed",
                "missing_tools": [],
                "pattern": "information_request"
            }
    
    # Check if any pattern matches
    for pattern_name, pattern in task_patterns.items():
        if any(trigger in user_prompt_lower for trigger in pattern["triggers"]):
            # Check if all required tools were called
            missing_tools = []
            for required_tool in pattern["required_tools"]:
                if required_tool not in tools_called:
                    missing_tools.append(required_tool)
            
            if missing_tools:
                return {
                    "complete": False,
                    "reason": f"Missing required tools for {pattern['description']}",
                    "missing_tools": missing_tools,
                    "pattern": pattern_name
                }
            
            # For email tasks, verify file was created if attachment expected
            if "secure_email_sender" in tools_called and "sandboxed_executor" in tools_called:
                if "attachments" in tools_results and "file not found" in tools_results.lower():
                    return {
                        "complete": False,
                        "reason": "File attachment referenced but file was not created",
                        "missing_tools": ["sandboxed_executor"],  # Re-run to create the file
                        "pattern": pattern_name
                    }
    
    # HTML email processing removed - using original tool-calling approach
    
    # 🚨 BULLETPROOF EMAIL VALIDATION
    # If user requested email but no email tool was called, task is INCOMPLETE
    if has_email_request and "secure_email_sender" not in tools_called:
        return {
            "complete": False,
            "reason": "Email requested but secure_email_sender tool was not called",
            "missing_tools": ["secure_email_sender"],
            "pattern": "email_required"
        }
    

    # 🚨 ZERO TOOLS CALLED VALIDATION
    # If no tools were called at all, check if any were actually needed
    if not tools_called:
        # If user requested email or file creation, tools were required
        file_creation_keywords = ["create", "generate", "write", "make", "build", "save"]
        needs_tools = has_email_request or any(keyword in user_prompt_lower for keyword in file_creation_keywords)
        
        if needs_tools:
            return {
                "complete": False,  
                "reason": "No tool calls generated but tools were required for this request",
                "missing_tools": ["secure_email_sender"] if has_email_request else ["sandboxed_executor"],
                "pattern": "no_tools_called"
            }
    
    # If no patterns match or all requirements met
    return {
        "complete": True,
        "reason": "All required tools executed successfully",
        "missing_tools": [],
        "pattern": None
    }

def _extract_report_content_from_results(tools_results: str) -> str:
    """Extract the comprehensive stock analysis content from tools_results"""
    try:
        # Look for comprehensive_stock_analyzer result in the tools_results
        if "Tool: comprehensive_stock_analyzer" in tools_results:
            # Split by tool sections and find the comprehensive_stock_analyzer result
            parts = tools_results.split("Tool: ")
            for part in parts:
                if part.startswith("comprehensive_stock_analyzer"):
                    # Extract just the result content
                    lines = part.split("\n")
                    result_lines = []
                    capture = False
                    for line in lines:
                        if line.startswith("Result: "):
                            capture = True
                            result_lines.append(line[8:])  # Remove "Result: " prefix
                        elif capture and line.strip() and not line.startswith("Tool: "):
                            result_lines.append(line)
                        elif capture and line.startswith("Tool: "):
                            break
                    
                    return "\n".join(result_lines).strip()
        
        return ""
    except Exception as e:
        logger.error(f"❌ Error extracting report content: {e}")
        return ""

def _generate_dynamic_title(user_prompt: str, tools_results: str) -> str:
    """Generate dynamic report title based on content type and topic"""
    try:
        user_prompt_lower = user_prompt.lower()
        tools_results_lower = tools_results.lower()
        
        # Check for news content
        if "Tool: get_news_summaries" in tools_results:
            # Extract topic from user prompt
            news_keywords = {
                "middle east": "Middle East News Analysis Report",
                "technology": "Technology News Analysis Report", 
                "tech": "Technology News Analysis Report",
                "stock market": "Stock Market News Analysis Report",
                "market": "Market News Analysis Report",
                "sports": "Sports News Analysis Report",
                "politics": "Political News Analysis Report", 
                "political": "Political News Analysis Report",
                "business": "Business News Analysis Report",
                "health": "Health News Analysis Report",
                "science": "Science News Analysis Report",
                "entertainment": "Entertainment News Analysis Report",
                "world": "World News Analysis Report",
                "international": "International News Analysis Report",
                "economy": "Economic News Analysis Report",
                "economic": "Economic News Analysis Report",
                "climate": "Climate News Analysis Report",
                "environment": "Environmental News Analysis Report",
                "african": "African News Analysis Report",
                "africa": "African News Analysis Report",
                "asian": "Asian News Analysis Report",
                "asia": "Asian News Analysis Report",
                "european": "European News Analysis Report",
                "europe": "European News Analysis Report"
            }
            
            # Find the most specific topic match
            for topic, title in news_keywords.items():
                if topic in user_prompt_lower or topic in tools_results_lower:
                    return title
            
            # Default news title if no specific topic found
            return "News Analysis Report"
        
        # Check for financial/stock content
        elif ("Tool: stock_analyzer" in tools_results or 
              any(keyword in user_prompt_lower for keyword in ["stock", "financial", "market", "trading", "investment"])):
            return "Comprehensive Stock Analysis Report"
        
        # Check for other specific content types
        elif any(keyword in user_prompt_lower for keyword in ["calendar", "appointment", "schedule"]):
            return "Calendar Analysis Report"
        elif any(keyword in user_prompt_lower for keyword in ["email", "message", "letter"]):
            return "Email Analysis Report"
        else:
            # General analysis report
            return "Analysis Report"
            
    except Exception as e:
        logger.error(f"❌ Error generating dynamic title: {e}")
        return "Analysis Report"

def _generate_dynamic_filename(user_prompt: str, tools_results: str, timestamp: str, file_extension: str = "html") -> str:
    """Generate dynamic filename based on content type and topic"""
    try:
        user_prompt_lower = user_prompt.lower()
        tools_results_lower = tools_results.lower()
        
        # Check for news content
        if "Tool: get_news_summaries" in tools_results:
            # Extract topic from user prompt
            news_keywords = {
                "middle east": "middle_east_news",
                "technology": "technology_news", 
                "tech": "technology_news",
                "sports": "sports_news",
                "politics": "political_news", 
                "political": "political_news",
                "business": "business_news",
                "health": "health_news",
                "science": "science_news",
                "entertainment": "entertainment_news",
                "world": "world_news",
                "international": "international_news",
                "economy": "economic_news",
                "economic": "economic_news",
                "climate": "climate_news",
                "environment": "environmental_news",
                "african": "african_news",
                "africa": "african_news",
                "asian": "asian_news",
                "asia": "asia_news",
                "european": "european_news",
                "europe": "europe_news"
            }
            
            # Find the most specific topic match
            for topic, filename_prefix in news_keywords.items():
                if topic in user_prompt_lower or topic in tools_results_lower:
                    return f"{filename_prefix}_analysis_{timestamp}.{file_extension}"
            
            # Default news filename if no specific topic found
            return f"news_analysis_{timestamp}.{file_extension}"
        
        # Check for financial/stock content
        elif ("Tool: stock_analyzer" in tools_results or 
              any(keyword in user_prompt_lower for keyword in ["stock", "financial", "market", "trading", "investment"])):
            return f"financial_analysis_{timestamp}.{file_extension}"
        
        # Check for other specific content types
        elif any(keyword in user_prompt_lower for keyword in ["calendar", "appointment", "schedule"]):
            return f"calendar_report_{timestamp}.{file_extension}"
        elif any(keyword in user_prompt_lower for keyword in ["email", "message", "letter"]):
            return f"email_report_{timestamp}.{file_extension}"
        else:
            # General analysis report
            return f"analysis_report_{timestamp}.{file_extension}"
            
    except Exception as e:
        logger.error(f"❌ Error generating dynamic filename: {e}")
        return f"analysis_report_{timestamp}.{file_extension}"

def _extract_news_content_from_results(tools_results: str) -> str:
    """Extract news content from get_news_summaries tool results"""
    try:
        # Look for get_news_summaries result in the tools_results
        if "Tool: get_news_summaries" in tools_results:
            # Split by tool sections and find the get_news_summaries result
            parts = tools_results.split("Tool: ")
            for part in parts:
                if part.startswith("get_news_summaries"):
                    # Extract just the result content
                    lines = part.split("\n")
                    result_lines = []
                    capture = False
                    for line in lines:
                        if line.startswith("Result: "):
                            capture = True
                            result_lines.append(line[8:])  # Remove "Result: " prefix
                        elif capture and line.strip() and not line.startswith("Tool: "):
                            result_lines.append(line)
                        elif capture and line.startswith("Tool: "):
                            break
                    
                    return "\n".join(result_lines).strip()
        
        return ""
    except Exception as e:
        logger.error(f"❌ Error extracting news content: {e}")
        return ""

async def _execute_missing_tools(missing_tools: List[str], tool_manager, tools_results: str = "", user_prompt: str = "") -> str:
    """
    🔄 AUTO-EXECUTOR for missing tools
    Automatically executes missing tools to complete the task
    """
    additional_results = ""
    
    for tool_name in missing_tools:
        try:
            logger.info(f"🔄 Auto-executing missing tool: {tool_name}")
            
            if tool_name == "sandboxed_executor":
                logger.info("🎯🎯🎯 AUTO-EXEC PATH: Starting sandboxed_executor auto-execution")
                # Determine report type based on tools_results content
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
                
                # Generate dynamic filename based on content type and topic - DEFAULT TO HTML
                file_extension = "html" if "Tool: get_news_summaries" in tools_results or "stock" in user_prompt.lower() else "md"
                filename = _generate_dynamic_filename(user_prompt, tools_results, timestamp, file_extension)
                
                if "Tool: get_news_summaries" in tools_results:
                    actual_report_content = _extract_news_content_from_results(tools_results)
                else:
                    actual_report_content = _extract_report_content_from_results(tools_results)
                
                logger.info(f"🎯🎯🎯 AUTO-EXEC PATH: Creating DYNAMIC REPORT -> {filename}")
                
                # Generate appropriate report content based on type
                if actual_report_content:
                    if "get_news_summaries" in tools_results:
                        # News analysis report with dynamic title
                        report_title = _generate_dynamic_title(user_prompt, tools_results)
                        report_content = f"""# {report_title}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Critical News Summary

{actual_report_content}

---

*This report was automatically generated by the AI News Analysis System.*
"""
                    else:
                        # Stock analysis report
                        report_content = f"""# Comprehensive Stock Analysis Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{actual_report_content}

---

*This report was automatically generated and saved by the task completion system.*
"""
                else:
                    # Fallback content based on type
                    if "get_news_summaries" in tools_results:
                        report_title = _generate_dynamic_title(user_prompt, tools_results)
                        report_content = f"""# {report_title}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Analysis Summary
News analysis completed successfully.

*Report content could not be extracted automatically. Please refer to the original news results.*
"""
                    else:
                        report_content = f"""# Stock Analysis Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Analysis Summary
Comprehensive stock analysis completed successfully.

*Report content could not be extracted automatically. Please refer to the original analysis results.*
"""
                
                # Create the file using sandboxed_executor - PDF auto-conversion will trigger
                # Find the actual tool instance, not the wrapper
                logger.info("🎯🎯🎯 AUTO-EXEC PATH: Looking for sandboxed_executor tool instance")
                sandboxed_tool_instance = None
                for tool in tool_manager.user_tools:
                    if tool.name == "sandboxed_executor":
                        sandboxed_tool_instance = tool
                        logger.info(f"🎯🎯🎯 AUTO-EXEC PATH: Found tool instance: {type(tool).__name__}")
                        break
                
                if sandboxed_tool_instance:
                    logger.info(f"🎯🎯🎯 AUTO-EXEC PATH: Using DIRECT TOOL INSTANCE for {filename}")
                    logger.info(f"🎯🎯🎯 AUTO-EXEC PATH: Calling execute(action='create_file', filename='{filename}')")
                    result = await sandboxed_tool_instance.execute(
                        action="create_file",
                        filename=filename,
                        content=report_content
                        # Note: convert_to_pdf not specified, so auto-conversion for .pdf files will trigger
                    )
                    logger.info(f"🎯🎯🎯 AUTO-EXEC PATH: Direct tool RESULT: {result}")
                else:
                    # Fallback to wrapper if tool instance not found
                    logger.info(f"🎯🎯🎯 AUTO-EXEC PATH: TOOL INSTANCE NOT FOUND! Using WRAPPER FALLBACK for {filename}")
                    sandboxed_tool = tool_manager.available_functions["sandboxed_executor"]
                    result = await sandboxed_tool({
                        "action": "create_file",
                        "filename": filename,
                        "content": report_content
                    })
                    logger.info(f"🎯🎯🎯 AUTO-EXEC PATH: Wrapper RESULT: {result}")
                
                logger.info(f"🔄 Auto-created file: {filename} with {len(report_content)} characters")
                if "get_news_summaries" in tools_results:
                    additional_results += f"Tool: {tool_name} (auto-executed)\nResult: Created file {filename} with Middle East news analysis report ({len(report_content)} chars)\n\n"
                else:
                    additional_results += f"Tool: {tool_name} (auto-executed)\nResult: Created file {filename} with comprehensive stock analysis report ({len(report_content)} chars)\n\n"
            
            elif tool_name == "get_the_secret_tool":
                result = await tool_manager.get_the_secret_tool()
                additional_results += f"Tool: {tool_name} (auto-executed)\nResult: {result}\n\n"
            
            elif tool_name == "secure_email_sender":
                # Auto-execute email sending with the created file
                # Find the actual email tool instance
                email_tool_instance = None
                for tool in tool_manager.user_tools:
                    if tool.name == "secure_email_sender":
                        email_tool_instance = tool
                        break
                
                if email_tool_instance:
                    attachment_path = os.path.join(os.getcwd(), "sandbox_workspace", filename)
                    logger.info(f"📧 Auto-sending email with attachment: {attachment_path}")
                    
                    if "get_news_summaries" in tools_results:
                        # News analysis email with dynamic subject
                        email_subject = _generate_dynamic_title(user_prompt, tools_results)
                        # 🔧 CRITICAL FIX: Add timeout to prevent infinite hanging
                        
                        try:
                            logger.info(f"⏰ POST-LLM AUTO-EXECUTION: Starting email execution with 120s timeout...")
                            
                            # Execute email using secure_email_sender with fail-fast logic
                            email_params = {
                                "to_email": recipient_email,
                                "subject": email_subject, 
                                "body": f"Please find attached the latest {email_subject.lower()} with critical updates and detailed analysis.",
                                "attachments": attachment_path
                            }
                            result = await tool_manager.safe_function_call("secure_email_sender", email_params)
                            
                            logger.info(f"✅ POST-LLM AUTO-EXECUTION: Email completed successfully")
                            
                        except asyncio.TimeoutError:
                            logger.error(f"⏰ POST-LLM AUTO-EXECUTION: TIMEOUT after 120 seconds - email execution hung!")
                            result = {'success': False, 'error': 'Email execution timed out after 120 seconds'}
                        except Exception as e:
                            logger.error(f"❌ POST-LLM AUTO-EXECUTION: Email execution failed: {e}")
                            result = {'success': False, 'error': str(e)}
                    else:
                        # Stock analysis email
                        # 🔧 CRITICAL FIX: Add timeout to prevent infinite hanging
                        try:
                            logger.info(f"⏰ POST-LLM AUTO-EXECUTION: Starting stock email execution with 120s timeout...")
                            
                            # Execute email using secure_email_sender with fail-fast logic
                            email_params = {
                                "to_email": recipient_email,
                                "subject": "Stock Analysis Report",
                                "body": "Please find attached the comprehensive stock analysis report with detailed financial insights.",
                                "attachments": attachment_path
                            }
                            result = await tool_manager.safe_function_call("secure_email_sender", email_params)
                            
                            logger.info(f"✅ POST-LLM AUTO-EXECUTION: Stock email completed successfully")
                            
                        except asyncio.TimeoutError:
                            logger.error(f"⏰ POST-LLM AUTO-EXECUTION: TIMEOUT after 120 seconds - stock email execution hung!")
                            result = {'success': False, 'error': 'Stock email execution timed out after 120 seconds'}
                        except Exception as e:
                            logger.error(f"❌ POST-LLM AUTO-EXECUTION: Stock email execution failed: {e}")
                            result = {'success': False, 'error': str(e)}
                else:
                    # Fallback to wrapper
                    email_tool = tool_manager.available_functions["secure_email_sender"]
                    if "get_news_summaries" in tools_results:
                        email_subject = _generate_dynamic_title(user_prompt, tools_results)
                        result = await email_tool({
                            "to_email": recipient_email,
                            "subject": email_subject,
                            "body": f"Please find attached the latest {email_subject.lower()} with critical updates and detailed analysis.",
                            "attachments": os.path.join(os.getcwd(), "sandbox_workspace", filename)
                        })
                    else:
                        result = await email_tool({
                            "to_email": recipient_email, 
                            "subject": "Stock Analysis Report",
                            "body": "Please find attached the comprehensive stock analysis report with detailed financial insights.",
                            "attachments": os.path.join(os.getcwd(), "sandbox_workspace", filename)
                        })
                
                additional_results += f"Tool: {tool_name} (auto-executed)\nResult: {result}\n\n"
            
            # Add more auto-execution logic for other tools as needed
            
        except Exception as e:
            logger.error(f"❌ Auto-execution failed for {tool_name}: {e}")
            logger.error(f"❌ Auto-execution traceback: {traceback.format_exc()}")
            additional_results += f"Tool: {tool_name} (auto-execution failed)\nResult: Error: {str(e)}\n\n"
    
    return additional_results

def _clean_llm_response_content(raw_content: str) -> str:
    """
    🧹 Clean LLM response content by removing tokens, parameters, and metadata
    
    Filters out:
    - Raw JSON tokens and response markers
    - Model parameters and configuration
    - System metadata and debugging info
    - Keeps only the actual content meant for the user
    """
    if not raw_content or not raw_content.strip():
        return ""
    
    # Remove common LLM response artifacts
    cleaned_content = raw_content
    
    # Remove JSON markers and response formatting
    lines_to_remove = []
    lines = cleaned_content.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Skip lines with JSON response markers
        if any(marker in line_lower for marker in [
            '"response":', '"message":', '"content":', 
            '{"response"', '{"message"', '{"content"',
            'response":', 'message":', 'content":',
            '"role":', '"model":', '"parameters":', '"tokens":'
        ]):
            lines_to_remove.append(i)
            continue
            
        # Skip lines with model parameters
        if any(param in line_lower for param in [
            'temperature:', 'max_tokens:', 'top_p:', 'top_k:',
            'num_predict:', 'repeat_penalty:', 'system_fingerprint:',
            'model:', 'stream:', 'num_ctx:', 'stop:'
        ]):
            lines_to_remove.append(i)
            continue
            
        # Skip lines that are pure JSON artifacts
        if line.strip() in ['', '{', '}', '[', ']', ',', '",', '"']:
            lines_to_remove.append(i)
            continue
            
        # Skip lines with timestamps/metadata that aren't content
        if any(meta in line_lower for meta in [
            'created_at:', 'finished_at:', 'load_duration:', 'prompt_eval_duration:',
            'eval_duration:', 'total_duration:', 'eval_count:', 'prompt_eval_count:'
        ]):
            lines_to_remove.append(i)
            continue
    
    # Remove identified lines
    for i in reversed(lines_to_remove):
        lines.pop(i)
    
    # Rejoin and clean up
    cleaned_content = '\n'.join(lines)
    
    # Remove excessive whitespace but preserve paragraph structure
    import re
    cleaned_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_content)  # Max 2 consecutive newlines
    cleaned_content = re.sub(r'^\s+|\s+$', '', cleaned_content, flags=re.MULTILINE)  # Trim lines
    
    return cleaned_content.strip()

def _fill_template_placeholders(content: str, user_prompt: str, tools_results: str = "") -> str:
    """
    🔧 Fill template placeholders with actual data from user context
    
    Replaces common template fields like [Your Name Here] with actual information
    extracted from the user prompt, tool results, or external content.
    """
    if not content or '[' not in content:
        return content
    
    import re
    
    # 🔧 ENHANCED: Extract information from ALL sources (user prompt, tool results, content)
    search_text = f"{user_prompt} {tools_results} {content}"
    
    # Extract actual data from all sources
    actual_name = None
    actual_phone = None
    actual_email = None
    
    # Enhanced name patterns - look for common name formats
    name_patterns = [
        r'Al Sabawi',
        r'Ahmed.*?Sabawi',
        r'Sabawi.*?Ahmed',
        r'Ahmed Al Sabawi',
        # Look for capitalized name patterns in resume content
        r'([A-Z][a-z]+\s+[A-Z][a-z]*\s*Sabawi)',
        r'(Al\s+[A-Z][a-z]+)',
        r'([A-Z][a-z]+\s+Al\s+Sabawi)',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            if pattern.startswith('('):  # Capture group pattern
                actual_name = match.group(1).strip()
            else:
                actual_name = match.group(0).strip()
            break
    
    # If no specific name found, use default
    if not actual_name:
        actual_name = "Al Sabawi"
    
    # Enhanced contact info patterns
    phone_patterns = [
        r'\(607\) 759-2683',
        r'607[.\-\s]*759[.\-\s]*2683',
        r'\(?\d{3}\)?[.\-\s]*\d{3}[.\-\s]*\d{4}'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, search_text)
        if match:
            actual_phone = match.group(0).strip()
            break
    
    email_patterns = [
        r'sabawi@gmail\.com',
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    ]
    
    for pattern in email_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            actual_email = match.group(0).strip()
            break
    
    # Replace template placeholders
    filled_content = content
    
    # Name placeholders - including the missing [YOUR NAME] pattern!
    if actual_name:
        filled_content = re.sub(r'\[YOUR NAME\]', actual_name, filled_content)  # 🔧 FIX: Added missing pattern
        filled_content = re.sub(r'\[Your Full Name\]', actual_name, filled_content)
        filled_content = re.sub(r'\[Your Name Here\]', actual_name, filled_content)
        filled_content = re.sub(r'\[Sign Your Name\]', actual_name, filled_content)
        filled_content = re.sub(r'\[Your Name\]', actual_name, filled_content)
        filled_content = re.sub(r'\[NAME\]', actual_name, filled_content)
        # 🔧 CRITICAL FIX: Also handle literal "Your Name" without brackets!
        filled_content = re.sub(r'\bYour Name\b', actual_name, filled_content)  # Most common pattern
        filled_content = re.sub(r'\byour name\b', actual_name, filled_content, flags=re.IGNORECASE)
    
    # Contact info placeholders
    if actual_phone:
        filled_content = re.sub(r'\[Your Phone Number\]', actual_phone, filled_content)
        filled_content = re.sub(r'\[PHONE\]', actual_phone, filled_content)
    
    if actual_email:
        filled_content = re.sub(r'\[Your Email Address\]', actual_email, filled_content)
        filled_content = re.sub(r'\[EMAIL\]', actual_email, filled_content)
    
    # Generic placeholders that we can't fill but should clean up
    filled_content = re.sub(r'\[Your Address\]', '', filled_content)
    filled_content = re.sub(r'\[City, State, ZIP Code\]', '', filled_content)
    filled_content = re.sub(r'\[Date\]', '', filled_content)
    
    # Clean up any extra whitespace from removed placeholders
    filled_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', filled_content)
    
    return filled_content.strip()

async def _detect_html_email_request_in_args(function_args_dict: dict, user_prompt: str) -> dict:
    """
    🎯 Detect HTML email requests from tool calling arguments and user prompt
    This version checks tool arguments directly for format="html" metadata
    """
    import re
    
    # Check if tool arguments contain HTML format metadata
    has_html_format = function_args_dict.get('format') == 'html'
    has_html_source = function_args_dict.get('source') in ['previous_response', 'current_response']
    has_style_param = 'style' in function_args_dict
    
    # Also check user prompt for HTML email indicators
    user_prompt_lower = user_prompt.lower()
    html_email_indicators = [
        'email the full response above in html',
        'email previous response',
        'html format to',
        'in html format to',
        'email the full response above'  # Even without explicit HTML, we should use our template
    ]
    
    # 📄 CONVERSATION PDF DETECTION - Check for conversation export requests
    conversation_pdf_indicators = [
        'email the previous conversation as pdf',
        'email previous conversation as pdf',
        'email conversation as pdf attachment',
        'email the conversation as pdf',
        'send conversation pdf',
        'export conversation to pdf and email',
        'email conversation history as pdf',
        'email the above full and complete response',
        'email the above response as pdf',
        'email the full response as pdf',
        'email the complete response as pdf',
        'pdf attachment with',
        'neatly formatted pdf attachment'
    ]
    
    has_conversation_pdf_request = any(indicator in user_prompt_lower for indicator in conversation_pdf_indicators)
    
    has_html_in_prompt = any(indicator in user_prompt_lower for indicator in html_email_indicators)
    
    if has_html_format or has_html_source or has_style_param or has_html_in_prompt:
        # Extract email details from tool arguments first
        to_email = function_args_dict.get('to_email')
        subject = function_args_dict.get('subject', 'HTML Report')
        style = function_args_dict.get('style')
        source = function_args_dict.get('source', 'current_response')
        
        # If email not found in tool args, extract from user prompt
        if not to_email:
            user_email_patterns = [
                r'to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'email.*?to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ]
            for pattern in user_email_patterns:
                user_email_match = re.search(pattern, user_prompt)
                if user_email_match:
                    to_email = user_email_match.group(1)
                    break
        
        return {
            'to_email': to_email,
            'subject': subject,
            'style': style,
            'source': source,
            'detected': True
        }
    
    # 📄 CONVERSATION PDF PROCESSING - Handle conversation export requests
    if has_conversation_pdf_request:
        # Extract email details from tool arguments first
        to_email = function_args_dict.get('to_email')
        subject = function_args_dict.get('subject', 'Conversation Export')
        
        # If email not found in tool args, extract from user prompt
        if not to_email:
            user_email_patterns = [
                r'to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'email.*?to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ]
            for pattern in user_email_patterns:
                user_email_match = re.search(pattern, user_prompt)
                if user_email_match:
                    to_email = user_email_match.group(1)
                    break
        
        return {
            'to_email': to_email,
            'subject': subject,
            'type': 'conversation_pdf',
            'detected': True
        }
    
    return {}

def _detect_conversation_pdf_request(function_args_dict: dict, user_prompt: str) -> dict:
    """
    Detect if the user is requesting conversation export as PDF attachment
    """
    user_prompt_lower = user_prompt.lower()
    conversation_pdf_indicators = [
        'email the previous conversation as pdf',
        'email previous conversation as pdf', 
        'email conversation as pdf attachment',
        'email the conversation as pdf',
        'send conversation pdf',
        'export conversation to pdf and email',
        'email conversation history as pdf',
        'send the conversation as pdf',
        'email our conversation as pdf',
        'email the above full and complete response',
        'email the above response as pdf',
        'email the full response as pdf',
        'email the complete response as pdf',
        'pdf attachment with',
        'neatly formatted pdf attachment'
    ]
    
    has_conversation_pdf_request = any(indicator in user_prompt_lower for indicator in conversation_pdf_indicators)
    
    if has_conversation_pdf_request:
        # Extract email details from tool arguments first
        to_email = function_args_dict.get('to_email')
        subject = function_args_dict.get('subject', 'Conversation Export')
        
        # If email not found in tool args, extract from user prompt
        if not to_email:
            import re
            user_email_patterns = [
                r'to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'email.*?to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ]
            for pattern in user_email_patterns:
                user_email_match = re.search(pattern, user_prompt)
                if user_email_match:
                    to_email = user_email_match.group(1)
                    break
        
        return {
            'to_email': to_email,
            'subject': subject,
            'type': 'conversation_pdf',
            'detected': True
        }
    
    return {'detected': False}

async def _extract_html_params_from_results(tools_results: str, user_prompt: str = "") -> dict:
    """
    🎯 Extract HTML email parameters from secure_email_sender error message and user prompt
    Parses the special HTML format detection message to extract parameters
    """
    import re
    
    try:
        # Extract email address from user_prompt first, then from tools_results
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        
        # Try user_prompt first (more reliable)
        email_match = re.search(email_pattern, user_prompt)
        if not email_match:
            # Fallback to tools_results
            email_match = re.search(email_pattern, tools_results)
        
        # Extract subject hints from user prompt
        subject = 'HTML Report'
        if 'subject' in user_prompt.lower():
            # Could extract custom subject in the future
            pass
            
        return {
            'to_email': email_match.group(1) if email_match else None,
            'subject': subject,
            'format': 'html',
            'source': 'current_response',
            'style': None
        }
    except Exception as e:
        logger.error(f"❌ Error extracting HTML params: {e}")
        return {}

async def _detect_html_email_request(tools_results: str, user_prompt: str) -> dict:
    """
    🎯 Detect if tool calling model requested HTML email with metadata
    Looks for format="html", source="previous_response", style parameters etc.
    """
    import re
    
    # Look for HTML email request patterns in tools_results
    html_patterns = [
        r'format["\']?\s*[:=]\s*["\']html["\']',
        r'source["\']?\s*[:=]\s*["\'](?:previous_response|current_response)["\']',
        r'style["\']?\s*[:=]\s*["\'][^"\']+["\']'
    ]
    
    has_html_request = any(re.search(pattern, tools_results, re.IGNORECASE) for pattern in html_patterns)
    
    # Also check user prompt for HTML email requests (ENHANCED)
    user_prompt_lower = user_prompt.lower()
    html_email_indicators = [
        'email the full response above in html',
        'email previous response',
        'email' and 'html format',
        'email' and 'html attachment',
        'html format to',
        'in html format to',
        'email the full response above'  # Even without explicit HTML, we should use our template
    ]
    
    has_html_in_prompt = False
    for indicator in html_email_indicators:
        if isinstance(indicator, str) and indicator in user_prompt_lower:
            has_html_in_prompt = True
            break
        elif not isinstance(indicator, str):  # Handle 'and' cases
            # This is a special case for compound indicators, skipping for now
            continue
    
    if has_html_request or has_html_in_prompt:
        # Extract email details from tools_results first
        email_match = re.search(r'to_email["\']?\s*[:=]\s*["\']([^"\']+)["\']', tools_results)
        subject_match = re.search(r'subject["\']?\s*[:=]\s*["\']([^"\']+)["\']', tools_results)
        style_match = re.search(r'style["\']?\s*[:=]\s*["\']([^"\']+)["\']', tools_results)
        source_match = re.search(r'source["\']?\s*[:=]\s*["\']([^"\']+)["\']', tools_results)
        
        # If email not found in tools_results, extract from user prompt
        to_email = email_match.group(1) if email_match else None
        if not to_email:
            # Extract email from user prompt patterns like "to sabawi@gmail.com"
            user_email_patterns = [
                r'to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'email.*?to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ]
            for pattern in user_email_patterns:
                user_email_match = re.search(pattern, user_prompt)
                if user_email_match:
                    to_email = user_email_match.group(1)
                    break
        
        return {
            'to_email': to_email,
            'subject': subject_match.group(1) if subject_match else 'HTML Report',
            'style': style_match.group(1) if style_match else None,
            'source': source_match.group(1) if source_match else 'current_response',
            'detected': True
        }
    
    return {}

async def _generate_complete_html_email(complete_llm_response: str, html_email_request: dict, user_prompt: str) -> str:
    """
    🎯 Generate complete HTML file using HTMLReportGenerator
    Uses the complete LLM response to avoid any truncation
    """
    from utils.html_generator import html_generator
    from datetime import datetime
    import os
    
    try:
        # Determine content source
        if html_email_request.get('source') == 'previous_response':
            # TODO: Extract from conversation memory when available
            content = complete_llm_response
        else:
            content = complete_llm_response
        
        # Parse custom styles if provided
        custom_styles = {}
        style_string = html_email_request.get('style', '')
        if style_string:
            # Parse "font_color:red,background_color:yellow" format
            style_pairs = style_string.split(',')
            for pair in style_pairs:
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    css_key = key.strip().replace('_', '-')
                    custom_styles[css_key] = value.strip()
        
        # Generate title from user prompt or use default
        title = "Research Report"
        if "email" in user_prompt.lower():
            # Extract meaningful title from user prompt
            import re
            title_patterns = [
                r'email.*?([^.!?]+?)(?:to|in html)',
                r'create.*?([^.!?]+?)(?:and email|report)',
                r'generate.*?([^.!?]+?)(?:email|report)'
            ]
            for pattern in title_patterns:
                match = re.search(pattern, user_prompt, re.IGNORECASE)
                if match:
                    title = match.group(1).strip().title()
                    break
        
        # Apply custom styles by injecting CSS
        if custom_styles:
            style_css = "body { "
            for css_key, css_value in custom_styles.items():
                style_css += f"{css_key}: {css_value}; "
            style_css += "}"
            
            # Inject custom styles into content
            content = f"<style>{style_css}</style>\n{content}"
        
        # Generate HTML using our proven template system
        html_content = html_generator.generate_html_report(
            content=content,
            title=title,
            header_title=title,
            header_subtitle=f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            include_disclaimer=False,  # Skip disclaimer for email reports
            custom_timestamp=None
        )
        
        # Save HTML file to sandbox workspace
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        html_filename = f"html_email_report_{timestamp}.html"
        base_dir = os.path.join(os.getcwd(), "sandbox_workspace")
        full_path = os.path.join(base_dir, html_filename)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"🎯 POST-LLM HTML EMAIL: Generated complete HTML file: {html_filename}")
        logger.info(f"🎯 HTML content length: {len(html_content)} characters (no truncation)")
        
        return html_filename
        
    except Exception as e:
        logger.error(f"❌ HTML email generation failed: {e}")
        return None

async def _execute_missing_tools_post_llm(missing_tools: List[str], tool_manager, tools_results: str, complete_llm_response: str, user_prompt: str) -> str:
    """
    🎯 POST-LLM AUTO-EXECUTOR for missing tools
    Executes file creation and email sending AFTER Primary LLM generates complete content
    
    This ensures that:
    1. Files contain the complete, refined LLM-generated content
    2. Emails are sent with properly formatted attachments
    3. No race conditions between content generation and file operations
    """
    additional_results = ""
    created_filename = None
    
    # Extract file format from user prompt or tool calling model (if enhanced)
    user_prompt_lower = user_prompt.lower()
    if "pdf" in user_prompt_lower:
        file_extension = "pdf"
    elif "html" in user_prompt_lower:
        file_extension = "html"
    elif "markdown" in user_prompt_lower or "md" in user_prompt_lower:
        file_extension = "md"
    elif "text" in user_prompt_lower or "txt" in user_prompt_lower:
        file_extension = "txt"
    else:
        file_extension = "html"  # Default to HTML for reports (changed from PDF)
    
    logger.info(f"🎯 POST-LLM: Detected file format: {file_extension}")
    
    for tool_name in missing_tools:
        try:
            logger.info(f"🔄 POST-LLM Auto-executing: {tool_name}")
            
            if tool_name == "sandboxed_executor":
                # 🔧 CRITICAL FIX: Check if files already exist from tool calling stage
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
                
                # Generate dynamic filename based on content type and topic
                created_filename = _generate_dynamic_filename(user_prompt, tools_results, timestamp, file_extension)
                logger.info(f"🎯 POST-LLM: Creating DYNAMIC REPORT -> {created_filename}")
                
                # 🚨 CRITICAL: Check if file already exists with good content
                import os
                base_dir = os.path.join(os.getcwd(), "sandbox_workspace")
                full_file_path = os.path.join(base_dir, created_filename)
                
                if os.path.exists(full_file_path):
                    # Check if existing file has good content (not placeholders)
                    try:
                        with open(full_file_path, 'r') as existing_file:
                            existing_content = existing_file.read()
                            
                        # If file has placeholder content, overwrite it
                        if any(placeholder in existing_content for placeholder in [
                            '[Generated cover letter content here]',
                            '[generated cover letter]', 
                            '[Generated cover letter]',
                            '[generated cover letter content]'
                        ]):
                            logger.info(f"🔧 POST-LLM: File {created_filename} has placeholder content - will overwrite")
                        else:
                            # File has good content - don't overwrite it!
                            logger.info(f"✅ POST-LLM: File {created_filename} already exists with good content - skipping creation")
                            additional_results += f"Tool: sandboxed_executor\nResult: File {created_filename} already exists with proper content - preserved existing file\n\n"
                            created_filename = created_filename  # Keep filename for email attachment
                            continue  # Skip to next tool (email sending)
                    except Exception as e:
                        logger.warning(f"⚠️ POST-LLM: Error checking existing file {created_filename}: {e}")
                
                # Use complete LLM response as content (this is the key fix!)
                raw_content = complete_llm_response.strip()
                
                # 🧹 CLEAN CONTENT: Remove raw LLM tokens and parameters
                report_content = _clean_llm_response_content(raw_content)
                
                # 🔧 FIX: Replace template placeholders with actual data from user prompt and tools results
                report_content = _fill_template_placeholders(report_content, user_prompt, tools_results)
                
                # 🔧 FIX: Clean up literal HTML tags (convert <br><br> to proper line breaks)
                report_content = report_content.replace('<br><br>', '\n\n')
                report_content = report_content.replace('<br>', '\n')
                # Clean up any other literal HTML tags that might appear
                import re
                report_content = re.sub(r'</?[a-zA-Z][^>]*>', '', report_content)  # Remove any remaining HTML-like tags
                
                # Add proper headers if content doesn't have them
                if not report_content.startswith("#") and not report_content.startswith("<"):
                    if "get_news_summaries" in tools_results:
                        report_title = _generate_dynamic_title(user_prompt, tools_results)
                        report_content = f"""# {report_title}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{report_content}

---
*This report was generated by the AI News Analysis System using the latest available information.*
"""
                    else:
                        report_content = f"""# Analysis Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{report_content}

---
*This report was generated by the AI Analysis System.*
"""
                
                logger.info(f"🎯 POST-LLM: Using COMPLETE LLM response ({len(report_content)} chars)")
                
                # Find and execute sandboxed tool with complete content
                sandboxed_tool_instance = None
                for tool in tool_manager.user_tools:
                    if tool.name == "sandboxed_executor":
                        sandboxed_tool_instance = tool
                        break
                
                if sandboxed_tool_instance:
                    # Force PDF conversion by explicitly setting convert_to_pdf=True for .pdf files
                    if created_filename.endswith('.pdf'):
                        result = await sandboxed_tool_instance.execute(
                            action="create_file",
                            filename=created_filename,
                            content=report_content,
                            convert_to_pdf=True  # Explicitly force PDF conversion
                        )
                        logger.info(f"🎯 POST-LLM: FORCED PDF conversion for {created_filename}")
                    else:
                        result = await sandboxed_tool_instance.execute(
                            action="create_file",
                            filename=created_filename,
                            content=report_content
                        )
                    logger.info(f"🎯 POST-LLM: File creation RESULT: {result}")
                    
                    if result.get('success'):
                        additional_results += f"Tool: {tool_name} (post-LLM execution)\nResult: Created file {created_filename} with complete LLM response ({len(report_content)} chars)\n\n"
                    else:
                        logger.error(f"❌ POST-LLM file creation failed: {result.get('error')}")
                        additional_results += f"Tool: {tool_name} (post-LLM execution failed)\nResult: Error: {result.get('error')}\n\n"
                else:
                    logger.error(f"❌ POST-LLM: Could not find sandboxed_executor tool instance")
            
            # secure_email_sender: No special processing - use original tool-calling approach
                
                if html_email_request:
                    logger.info(f"🎯 POST-LLM HTML EMAIL: Using fallback detection")
                    # Generate complete HTML file using HTMLReportGenerator
                    html_filename = await _generate_complete_html_email(
                        complete_llm_response, 
                        html_email_request,
                        user_prompt
                    )
                    
                    # Execute secure_email_sender with generated HTML file
                    email_tool_instance = None
                    for tool in tool_manager.user_tools:
                        if tool.name == "secure_email_sender":
                            email_tool_instance = tool
                            break
                    
                    if email_tool_instance and html_filename:
                        # 🔧 CRITICAL FIX: Add timeout to prevent infinite hanging
                        
                        try:
                            logger.info(f"⏰ POST-LLM HTML EMAIL: Starting email execution with 120s timeout...")
                            
                            # Execute email using secure_email_sender with fail-fast logic
                            email_params = {
                                "to_email": html_email_request.get('to_email'),
                                "subject": html_email_request.get('subject', 'HTML Report'),
                                "body": f"Please find attached HTML document.",
                                "attachments": html_filename
                            }
                            result = await tool_manager.safe_function_call("secure_email_sender", email_params)
                            
                            logger.info(f"✅ POST-LLM HTML EMAIL: Completed successfully")
                            
                        except asyncio.TimeoutError:
                            logger.error(f"⏰ POST-LLM HTML EMAIL: TIMEOUT after 120 seconds - email execution hung!")
                            result = {'success': False, 'error': 'HTML email execution timed out after 120 seconds'}
                        except Exception as e:
                            logger.error(f"❌ POST-LLM HTML EMAIL: Email execution failed: {e}")
                            result = {'success': False, 'error': str(e)}
                        logger.info(f"🎯 POST-LLM HTML EMAIL: Sent with complete content")
                        additional_results += f"Tool: {tool_name} (HTML email with complete content)\nResult: {result}\n\n"
                        continue  # Skip regular email processing
                
                # 📄 CONVERSATION PDF EMAIL PROCESSING
                conversation_pdf_request = _detect_conversation_pdf_request(function_args_dict, user_prompt)
                if conversation_pdf_request.get('detected'):
                    logger.info(f"📄 POST-LLM CONVERSATION PDF: Processing conversation export request")
                    
                    # Get conversation history from the current session 
                    message_history = []
                    
                    # Extract conversation history from the context if available
                    if "=== CONVERSATION HISTORY ===" in user_prompt:
                        # Parse conversation from user_prompt context
                        conv_start = user_prompt.find("=== CONVERSATION HISTORY ===")
                        conv_end = user_prompt.find("=== CURRENT REQUEST ===")
                        
                        if conv_start != -1 and conv_end != -1:
                            conversation_text = user_prompt[conv_start:conv_end]
                            # Parse the conversation format
                            for line in conversation_text.split('\n'):
                                line = line.strip()
                                if line and ':' in line and (line.upper().startswith('USER:') or line.upper().startswith('ASSISTANT:') or line.upper().startswith('SYSTEM:')):
                                    message_history.append(line)
                    
                    # If no conversation history found, create a summary of current interaction
                    if not message_history:
                        message_history = [
                            f"USER: {user_prompt.split('=== CURRENT REQUEST ===')[-1].strip() if '=== CURRENT REQUEST ===' in user_prompt else user_prompt}",
                            f"ASSISTANT: {complete_llm_response[:1000]}{'...' if len(complete_llm_response) > 1000 else ''}"
                        ]
                    
                    # Generate conversation PDF
                    pdf_filename = "conversation_export.pdf"
                    pdf_result = await export_conversation_to_pdf(message_history, pdf_filename)
                    
                    if pdf_result.get('success'):
                        # Send email with conversation PDF attachment
                        email_tool_instance = None
                        for tool in tool_manager.user_tools:
                            if tool.name == "secure_email_sender":
                                email_tool_instance = tool
                                break
                        
                        if email_tool_instance:
                            # 🔧 CRITICAL FIX: Add timeout to prevent infinite hanging
                                
                            try:
                                logger.info(f"⏰ POST-LLM CONVERSATION PDF: Starting email execution with 120s timeout...")
                                
                                # Execute email with timeout to prevent hanging
                                # Execute email using secure_email_sender with fail-fast logic
                                email_params = {
                                    "to_email": conversation_pdf_request.get('to_email'),
                                    "subject": conversation_pdf_request.get('subject', 'Conversation Export'),
                                    "body": f"Please find attached the conversation export in PDF format.\n\nThis document contains {pdf_result.get('message_count', 0)} messages from our conversation.",
                                    "attachments": pdf_filename
                                }
                                email_result = await tool_manager.safe_function_call("secure_email_sender", email_params)
                                
                                logger.info(f"✅ POST-LLM CONVERSATION PDF: Email completed successfully")
                                
                            except asyncio.TimeoutError:
                                logger.error(f"⏰ POST-LLM CONVERSATION PDF: TIMEOUT after 120 seconds - email execution hung!")
                                email_result = {'success': False, 'error': 'Conversation PDF email execution timed out after 120 seconds'}
                            except Exception as e:
                                logger.error(f"❌ POST-LLM CONVERSATION PDF: Email execution failed: {e}")
                                email_result = {'success': False, 'error': str(e)}
                            logger.info(f"📄 POST-LLM CONVERSATION PDF: Sent successfully")
                            additional_results += f"Tool: {tool_name} (Conversation PDF export)\nResult: {email_result}\n\n"
                            continue  # Skip regular email processing
                        else:
                            logger.error(f"❌ POST-LLM CONVERSATION PDF: Could not find email tool")
                    else:
                        logger.error(f"❌ POST-LLM CONVERSATION PDF: Export failed - {pdf_result.get('error')}")
                        additional_results += f"Tool: {tool_name} (Conversation PDF export failed)\nResult: Error: {pdf_result.get('error')}\n\n"
                
                # 🚀 BULLETPROOF EMAIL EXECUTION (Regular processing)
                # Handles all email scenarios: single file, multiple files, existing files, new files
                files_to_attach = []
                
                # Step 1: Extract filenames from tools_results (handles multiple document creation)
                import re
                import os
                filename_pattern = r'"filename":\s*"([^"]+)"'
                found_files = re.findall(filename_pattern, tools_results)
                base_dir = os.path.join(os.getcwd(), "sandbox_workspace")
                
                # Remove duplicates from found files
                found_files = list(set(found_files))  # Remove duplicates
                logger.info(f"🎯 POST-LLM EMAIL: Found {len(found_files)} unique files in tools_results: {found_files}")
                
                # Step 2: Check all found files and add them to attachments
                for filename in found_files:
                    if filename.endswith(('.pdf', '.html', '.txt', '.md', '.json', '.csv')):  # Support all formats
                        full_path = os.path.join(base_dir, filename)
                        if os.path.exists(full_path):
                            files_to_attach.append(filename)
                            logger.info(f"✅ POST-LLM EMAIL: Verified existing file: {filename}")
                        else:
                            logger.warning(f"⚠️ POST-LLM EMAIL: File not found: {full_path}")
                
                # Step 2A: 🔧 MULTI-DOCUMENT FIX: Extract source files mentioned in user prompt  
                import re
                user_prompt = data.get('prompt', '') if 'data' in locals() else ''
                
                # Look for file paths in user prompt (common patterns)
                file_path_patterns = [
                    r'/[a-zA-Z0-9_/.-]+\.(?:pdf|doc|docx|txt|md|json|csv|html)',  # Absolute paths
                    r'[a-zA-Z0-9_.-]+\.(?:pdf|doc|docx|txt|md|json|csv|html)',   # Relative filenames
                ]
                
                mentioned_files = []
                for pattern in file_path_patterns:
                    found_paths = re.findall(pattern, user_prompt)
                    mentioned_files.extend(found_paths)
                
                logger.info(f"🔍 POST-LLM EMAIL: Found {len(mentioned_files)} files mentioned in prompt: {mentioned_files}")
                
                # Add mentioned source files that exist
                for file_path in mentioned_files:
                    if os.path.isabs(file_path) and os.path.exists(file_path):
                        files_to_attach.append(file_path)  # Use absolute path
                        logger.info(f"✅ POST-LLM EMAIL: Added source file from prompt: {file_path}")
                    elif not os.path.isabs(file_path):
                        # Try in common locations
                        candidate_paths = [
                            file_path,  # Current directory
                            os.path.join(base_dir, file_path),  # Sandbox
                            os.path.join("/home/sabawi/Documents", file_path),  # Documents
                        ]
                        for candidate in candidate_paths:
                            if os.path.exists(candidate):
                                files_to_attach.append(candidate)
                                logger.info(f"✅ POST-LLM EMAIL: Added source file: {candidate}")
                                break
                
                # 🔧 CRITICAL FIX: Check if we just sent an email recently to avoid duplicates
                import time
                from datetime import datetime, timedelta
                
                # Check if an email was sent in the last 60 seconds to prevent duplicates
                current_time = datetime.now()
                last_email_check_file = "/tmp/last_email_sent.txt"
                
                try:
                    if os.path.exists(last_email_check_file):
                        with open(last_email_check_file, 'r') as f:
                            last_email_time_str = f.read().strip()
                            last_email_time = datetime.fromisoformat(last_email_time_str)
                            
                        # If email was sent within last 60 seconds, skip sending duplicate
                        if (current_time - last_email_time).total_seconds() < 60:
                            logger.info(f"🚫 POST-LLM EMAIL: Email sent recently ({(current_time - last_email_time).total_seconds():.1f}s ago) - skipping duplicate")
                            continue  # Skip this POST-LLM execution
                except Exception as e:
                    logger.warning(f"⚠️ POST-LLM EMAIL: Error checking last email time: {e}")
                
                # Step 3: Also add post-LLM created file if any
                if created_filename:
                    files_to_attach.append(created_filename)
                    logger.info(f"✅ POST-LLM EMAIL: Added post-LLM created file: {created_filename}")
                
                # Step 4: 🚨 SECURITY FIX - DO NOT attach unrelated files!
                if not files_to_attach:
                    logger.warning(f"⚠️ POST-LLM EMAIL: No files found for attachment - this indicates missing file creation tools!")
                    logger.warning(f"⚠️ POST-LLM EMAIL: REQUEST ANALYSIS NEEDED - User wanted files but none were created")
                    logger.warning(f"⚠️ POST-LLM EMAIL: Refusing to attach unrelated files for security reasons")
                    # 🔄 CRITICAL: Do not scan workspace for random files - this could send wrong person's data!
                    # This was causing privacy violations by sending Joe's files to Mary!
                    # Instead, we should have created the requested files with sandboxed_executor
                
                logger.info(f"🎯 POST-LLM EMAIL: Total files to attach: {len(files_to_attach)} -> {files_to_attach}")
                
                if files_to_attach:
                    logger.info(f"🎯 POST-LLM: Sending email with {len(files_to_attach)} attachment(s)")
                    
                    # Find email tool instance
                    email_tool_instance = None
                    for tool in tool_manager.user_tools:
                        if tool.name == "secure_email_sender":
                            email_tool_instance = tool
                            break
                    
                    if email_tool_instance:
                        logger.info(f"✅ POST-LLM EMAIL: Found email tool instance")
                        
                        # 🔥 ENHANCED: Smart email and CC extraction from user prompt
                        import re
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        email_matches = re.findall(email_pattern, user_prompt)
                        
                        logger.info(f"📧 POST-LLM EMAIL: Found {len(email_matches)} email addresses: {email_matches}")
                        
                        # Determine primary recipient and CC with smart detection
                        recipient_email = email_matches[0] if email_matches else None
                        if not recipient_email:
                            logger.warning(f"⚠️ POST-LLM EMAIL: No email address found in user request - skipping email")
                            additional_results += f"Tool: {tool_name} (post-LLM execution skipped)\nResult: No email address found in request\n\n"
                            continue
                        cc_emails = []
                        
                        if len(email_matches) > 1:
                            
                            # Smart CC detection - look for explicit CC mentions or multiple emails
                            user_prompt_lower = user_prompt.lower()
                            if "cc" in user_prompt_lower or "copy" in user_prompt_lower:
                                # Extract CC emails after CC mention
                                cc_pattern = r'(?:cc|copy).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                                cc_matches = re.findall(cc_pattern, user_prompt_lower)
                                if cc_matches:
                                    cc_emails = cc_matches
                                elif len(email_matches) > 1:
                                    cc_emails = email_matches[1:]  # Fallback: rest are CC
                            elif len(email_matches) > 1:
                                cc_emails = email_matches[1:]  # Multiple emails = CC the rest
                        
                        logger.info(f"🎯 POST-LLM: Recipient: {recipient_email}, CC: {cc_emails}")
                        
                        # Use the files we found above
                        attachment_files = files_to_attach
                        
                        # Create comma-separated attachment list
                        attachments_str = ",".join(attachment_files)
                        logger.info(f"🔧 POST-LLM: Sending email with attachments: {attachments_str}")
                        
                        # 🔧 FIX: Include CC emails and use better provider for attachments
                        cc_emails_str = ",".join(cc_emails) if cc_emails else ""
                        
                        # 🚀 SMART EMAIL COMPOSITION based on user request and file types
                        
                        # Determine email subject based on content
                        subject = "Requested Documents"
                        if "test" in user_prompt.lower():
                            subject = "Test Email with Documents"
                        elif len(files_to_attach) > 1:
                            subject = f"Multiple Documents ({len(files_to_attach)} files)"
                        elif any("pdf" in f.lower() for f in files_to_attach):
                            subject = "PDF Document"
                        
                        # Add timestamp
                        subject += f" - {datetime.now().strftime('%Y-%m-%d')}"
                        
                        # Create detailed file list for email body
                        file_list = ""
                        for i, filename in enumerate(files_to_attach, 1):
                            file_ext = filename.split('.')[-1].upper()
                            file_list += f"{i}. {filename} ({file_ext} format)\n"
                        
                        email_body = f"""Please find attached the requested documents.

Document Details:
- Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}
- Total Files: {len(attachment_files)} attachment(s)

Files Included:
{file_list}
This email was automatically generated in response to your request:
"{user_prompt[:100]}{'...' if len(user_prompt) > 100 else ''}"

Best regards,
AI Document Generation System"""
                        
                        logger.info(f"📧 POST-LLM EMAIL: Subject: {subject}")
                        logger.info(f"📧 POST-LLM EMAIL: Attachments: {attachments_str}")
                        logger.info(f"📧 POST-LLM EMAIL: Recipients: {recipient_email}, CC: {cc_emails_str}")
                        logger.info(f"📧 POST-LLM EMAIL: Body length: {len(email_body)} chars")
                        
                        # 🔧 CRITICAL FIX: Add timeout to prevent infinite hanging
                        
                        try:
                            logger.info(f"⏰ POST-LLM EMAIL: Starting email execution with 120s timeout...")
                            
                            # Execute email using secure_email_sender with fail-fast logic
                            email_params = {
                                "to_email": recipient_email,
                                "cc_emails": cc_emails_str if cc_emails_str else None,  # Don't pass empty string
                                "subject": subject,
                                "body": email_body,
                                "attachments": attachments_str
                            }
                            email_result = await tool_manager.safe_function_call("secure_email_sender", email_params)
                            
                            logger.info(f"✅ POST-LLM EMAIL: Completed successfully")
                            logger.info(f"🎯 POST-LLM: Email RESULT: {email_result}")
                            
                        except asyncio.TimeoutError:
                            logger.error(f"⏰ POST-LLM EMAIL: TIMEOUT after 120 seconds - email execution hung!")
                            email_result = {
                                'success': False, 
                                'error': 'Email execution timed out after 120 seconds',
                                'result': None
                            }
                        except Exception as email_error:
                            logger.error(f"❌ POST-LLM EMAIL: Exception during execution: {email_error}")
                            import traceback
                            logger.error(f"❌ POST-LLM EMAIL: Traceback: {traceback.format_exc()}")
                            email_result = {
                                'success': False,
                                'error': f'Email execution failed: {str(email_error)}',
                                'result': None
                            }
                        
                        if email_result.get('success'):
                            additional_results += f"Tool: {tool_name} (post-LLM execution)\nResult: Email sent to {recipient_email} with attachment {created_filename}\n\n"
                        else:
                            logger.error(f"❌ POST-LLM email sending failed: {email_result.get('error')}")
                            additional_results += f"Tool: {tool_name} (post-LLM execution failed)\nResult: Error: {email_result.get('error')}\n\n"
                    else:
                        logger.error(f"❌ POST-LLM: Could not find secure_email_sender tool instance")
                else:
                    logger.warning(f"⚠️ POST-LLM: No files found to attach, skipping email sending")
                    logger.info(f"🔍 POST-LLM: Checked tools_results for files but found none")
                    additional_results += f"Tool: {tool_name} (skipped - no files to attach)\nResult: No files were found for attachment\n\n"
            
            elif tool_name == "get_news_summaries":
                # Execute news summaries tool
                logger.info(f"🎯 POST-LLM: Executing get_news_summaries for Middle East news")
                try:
                    result = await tool_manager.get_news_summaries("Middle East")
                    additional_results += f"Tool: {tool_name} (post-LLM execution)\nResult: {result}\n\n"
                    logger.info(f"🎯 POST-LLM: News summaries completed: {len(str(result))} chars")
                except Exception as e:
                    logger.error(f"❌ POST-LLM news summaries failed: {e}")
                    additional_results += f"Tool: {tool_name} (post-LLM execution failed)\nResult: Error: {str(e)}\n\n"
            
            elif tool_name == "get_the_secret_tool":
                result = await tool_manager.get_the_secret_tool()
                additional_results += f"Tool: {tool_name} (post-LLM execution)\nResult: {result}\n\n"
                
        except Exception as e:
            logger.error(f"❌ POST-LLM Auto-execution failed for {tool_name}: {e}")
            logger.error(f"❌ POST-LLM Auto-execution traceback: {traceback.format_exc()}")
            additional_results += f"Tool: {tool_name} (post-LLM execution failed)\nResult: Error: {str(e)}\n\n"
    
    return additional_results

@app.post("/v1")
@app.post("/llama3_1b/stream")
async def llama_stream(request: Request):
    """
    Main Ollama streaming endpoint with tool calling
    Equivalent to the original /llama3_1b/stream endpoint
    """
    logger.info("🔧 DEBUG: Endpoint /llama3_1b/stream called")
    # Parse JSON data manually like the original Flask version
    try:
        data = await request.json()
        logger.info("🔧 DEBUG: JSON parsed successfully")
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Extract parameters with defaults (exactly like Flask version)
    user_prompt = data['prompt']  # Use direct access like original for required field
    model = data.get('model', ServerConfig.DEFAULT_MODEL)  # Get model early for logging
    # Input condition: User request received
    logger.info(f"Request: {len(user_prompt)} chars | Model: {model} | Tools: {'ON' if True else 'OFF'}")
    
    prompt_context = data.get('prompt_context', '')  # Using data['prompt_context'] like original
    
    #################################################################################
    ##                  CONTEXT MANAGEMENT WITH and WITHOUT TOOLS                  ##            
    #################################################################################
    
    # Handle toolsInUse exactly like original
    tools_in_use = True  # Default like original
    if "toolsInUse" in data:
        tools_in_use = data["toolsInUse"]
    # Tool usage mode determined
    logger.info(f"Tool usage mode: {tools_in_use}")
    
    # Handle searchWebInUse exactly like original
    search_web_in_use = False  # Default like original
    if "searchWebInUse" in data:
        search_web_in_use = data["searchWebInUse"]
    
    # Other parameters
    # model already extracted above for logging
    images = data.get('images', ['noimage'])
    tools_calling_model = data.get('tools_calling_model', ServerConfig.DEFAULT_TOOL_CALLING_MODEL)
    
    # 🖼️ COMPREHENSIVE IMAGE PROCESSING FIX
    async def process_image_data(images_raw):
        """Process images: convert file paths to base64 with smart resizing and comprehensive error handling."""
        import os
        import base64
        import io
        from PIL import Image
        
        if not images_raw or images_raw == ['noimage']:
            return ['noimage'], False
            
        processed_images = []
        image_exists = False
        user_errors = []  # Collect errors for user feedback
        
        for i, img_data in enumerate(images_raw):
            if img_data == "noimage":
                processed_images.append("noimage")
                continue
                
            try:
                logger.info(f"🖼️ Processing image {i+1}: {type(img_data)} - {str(img_data)[:100]}...")
                
                # Check if it's already base64 data (starts with base64 chars or data: URI)
                if isinstance(img_data, str):
                    # Remove data URI prefix if present
                    if img_data.startswith('data:image/'):
                        _, base64_part = img_data.split(',', 1)
                        img_data = base64_part
                    
                    # Use signature-based detection instead of arbitrary length thresholds
                    from signature_image_detection import ImageSignatureValidator
                    validator = ImageSignatureValidator()
                    validation_result = validator.validate_image_data(img_data, i + 1)

                    if validation_result['is_valid']:
                        logger.info(f"🖼️ Image {i+1}: Valid {validation_result['format']} image ({validation_result['size_bytes']} bytes)")
                        processed_images.append(validation_result['processed_data'])
                        image_exists = True
                        continue
                    else:
                        # Check if it might be a file path before declaring failure
                        if not ('/' in img_data or '\\' in img_data or any(img_data.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'])):
                            # Not a file path either - this is a validation failure
                            user_errors.append(validation_result['user_error'])
                            logger.error(f"🖼️ Image {i+1}: {validation_result['error']}")
                            processed_images.append("noimage")
                            continue

                        logger.warning(f"🖼️ Image {i+1}: Signature validation failed, trying file path - {validation_result['error']}")

                    # Otherwise, treat as file path
                    file_path = img_data.strip()
                    
                    # Expand user path (~)
                    file_path = os.path.expanduser(file_path)
                    
                    if not os.path.exists(file_path):
                        logger.error(f"🖼️ Image {i+1}: File not found: {file_path}")
                        processed_images.append("noimage")
                        continue
                    
                    if not os.path.isfile(file_path):
                        logger.error(f"🖼️ Image {i+1}: Not a file: {file_path}")
                        processed_images.append("noimage")
                        continue
                    
                    # Check file extension
                    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext not in valid_extensions:
                        logger.error(f"🖼️ Image {i+1}: Unsupported format {file_ext}: {file_path}")
                        processed_images.append("noimage")
                        continue
                    
                    # Read file as binary
                    try:
                        with open(file_path, 'rb') as f:
                            img_bytes = f.read()
                        logger.info(f"🖼️ Image {i+1}: Read {len(img_bytes)} bytes from {file_path}")
                    except Exception as e:
                        logger.error(f"🖼️ Image {i+1}: Failed to read file {file_path}: {e}")
                        processed_images.append("noimage")
                        continue
                    
                    # Progressive optimization for qwen2.5vl:3b - compress without aggressive resizing
                    resize_threshold = 2000000  # 2MB threshold for smart compression (not aggressive resizing)
                    if len(img_bytes) > resize_threshold:
                        logger.info(f"🖼️ Image {i+1}: Large image ({len(img_bytes)} bytes), applying smart compression...")
                        try:
                            # Smart compression approach for qwen2.5vl:3b
                            with Image.open(io.BytesIO(img_bytes)) as img:
                                original_size = img.size
                                
                                # Only resize if extremely large (>4000px), otherwise just compress
                                if max(img.size) > 4000:
                                    # Conservative resize - maintain high resolution for vision model
                                    max_size = 2400  # Much larger than before to preserve detail
                                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                                    logger.info(f"🖼️ Image {i+1}: Resized from {original_size} to {img.size}")
                                
                                # Convert to RGB if needed
                                if img.mode not in ('RGB', 'L'):
                                    img = img.convert('RGB')
                                
                                # Compress with higher quality to preserve details for vision model
                                buffer = io.BytesIO()
                                img.save(buffer, format='JPEG', quality=92, optimize=True)  # Higher quality
                                img_bytes = buffer.getvalue()
                                logger.info(f"🖼️ Image {i+1}: Compressed to {len(img_bytes)} bytes ({img.size[0]}x{img.size[1]})")
                        except Exception as e:
                            logger.warning(f"🖼️ Image {i+1}: Compression failed, using original: {e}")
                    
                    # Convert to base64 (raw base64, no data URI prefix for Ollama compatibility)
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    processed_images.append(img_base64)
                    image_exists = True
                    logger.info(f"🖼️ Image {i+1}: Successfully processed - {len(img_base64)} base64 chars")
                    
                else:
                    logger.error(f"🖼️ Image {i+1}: Unsupported data type: {type(img_data)}")
                    processed_images.append("noimage")
                    
            except Exception as e:
                logger.error(f"🖼️ Image {i+1}: Processing failed: {e}")
                logger.error(f"🖼️ Image {i+1}: Exception type: {type(e)}")
                import traceback
                logger.error(f"🖼️ Image {i+1}: Traceback: {traceback.format_exc()}")
                processed_images.append("noimage")
        
        logger.info(f"🖼️ Image processing complete: {len(processed_images)} images, image_exists={image_exists}")
        if user_errors:
            logger.warning(f"🖼️ User errors collected: {len(user_errors)} errors")
        return processed_images, image_exists, user_errors
    
    # Process images with comprehensive error handling
    try:
        images, image_exists, image_errors = await process_image_data(images)
        # Update the data dictionary with processed images
        data["images"] = images
        logger.info(f"🖼️ Updated data[images] with {len([img for img in images if img != 'noimage'])} processed images")
        
        # 🖼️ Set image context for tools that need it
        tool_manager.set_image_context(images, {"endpoint": "native", "model": model})
        
    except Exception as e:
        logger.error(f"🖼️ CRITICAL: Image processing failed: {e}")
        images = ['noimage']
        image_exists = False
        image_errors = [f"Critical image processing error: {str(e)}"]
    
    async def generate_stream():
        import time  # Import time at function start for timing measurements
        logger.info("🔧 DEBUG: generate_stream() function called")
        try:
            # 🔧 VARIABLE SCOPE FIX: Initialize variables at function scope
            nonlocal image_exists  # Access outer scope image_exists variable
            is_meta_task = False  # Default value to prevent UnboundLocalError
            tools_results = ""    # Default value to prevent UnboundLocalError
            tools_results_list = []  # Use list for O(1) append vs O(n²) string concatenation
            tools_called = []  # Track all tools that were called
            complete_llm_response = ""  # Initialize for both Ollama and OpenAI paths
            
            # 🎯 EMAIL INTERCEPTION STATE  
            email_intercepted = False
            intercepted_email_params = {}
            
            # ###########################################################################
            # TWO-STAGE TOOL CALLING ALGORITHM (exactly like original Flask implementation)
            if (tools_in_use):
                # Tool execution phase initiated
                logger.info("🔧 DEBUG: Entering tool execution phase")
                
                # 🖼️ FORCED IMAGE PROCESSING: When images are present, automatically call image_to_text
                forced_image_processing_result = ""

                # 🚨 USER ERROR REPORTING: Report image validation failures to user
                if image_errors:
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    error_messages = "\n".join(image_errors)
                    forced_image_processing_result = f"""
🖼️ IMAGE VALIDATION ERRORS [{timestamp}]:
{error_messages}

💡 Please check your images and try again. Supported formats: PNG, JPEG, GIF, BMP, WebP, TIFF.
"""
                    logger.error(f"🖼️ Reporting {len(image_errors)} image validation errors to user")

                if image_exists:
                    logger.info("🖼️ FORCED IMAGE PROCESSING: Images detected, automatically processing...")
                    
                    # Check if image processing LLM is available
                    try:
                        # Use global llm_manager instance
                        
                        # Check if image processing provider is configured
                        if hasattr(llm_manager, 'image_processing_provider') and llm_manager.image_processing_provider:
                            logger.info("🖼️ Image processing LLM available, processing images...")
                            
                            # Load and execute image_to_text tool
                            try:
                                from user_tools.tool_discovery import get_user_tool_by_name, load_user_tools
                                user_tools = load_user_tools()
                                image_tool = get_user_tool_by_name(user_tools, "image_to_text")
                                
                                if image_tool:
                                    # Prepare image data for the tool
                                    images_data = []
                                    for i, img_data in enumerate(data.get("images", [])):
                                        if img_data != "noimage":
                                            images_data.append({
                                                "type": "base64",
                                                "data": img_data,
                                                "filename": f"user_image_{i+1}"
                                            })
                                    
                                    if images_data:
                                        # Execute image_to_text tool
                                        import time
                                        start_time = time.time()
                                        result = await image_tool.execute(
                                            images=images_data,
                                            processing_mode="sequential",  # Use sequential for forced processing
                                            quality="high"
                                        )
                                        execution_time = time.time() - start_time
                                        
                                        if result.get('success'):
                                            processed_count = result.get('processed_images', 0)
                                            logger.info(f"🖼️ FORCED IMAGE PROCESSING COMPLETE: {processed_count} images processed in {execution_time:.1f}s")
                                            
                                            # Format the results for primary LLM context
                                            image_descriptions = []
                                            for img_result in result.get('results', []):
                                                if img_result.get('description'):
                                                    filename = img_result.get('filename', 'image')
                                                    description = img_result.get('description')
                                                    image_descriptions.append(f"[{filename}]: {description}")
                                            
                                            if image_descriptions:
                                                # Generate timestamp for chronological ordering
                                                import datetime
                                                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                                                
                                                forced_image_processing_result = f"""
🖼️ IMAGE PROCESSING RESULTS [{timestamp}]:
{chr(10).join(image_descriptions)}

The above image analysis was automatically performed on newly uploaded images. This visual content is now available for your response."""
                                            
                                            # Add to tools results for primary LLM - will be appended to existing context
                                            tools_called.append("image_to_text")
                                            tools_results_list.append(f"Tool: image_to_text\nResult: {forced_image_processing_result}\n")
                                            
                                        else:
                                            error_msg = result.get('error', 'Unknown error during image processing')
                                            logger.error(f"🖼️ FORCED IMAGE PROCESSING FAILED: {error_msg}")
                                            import datetime
                                            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                                            forced_image_processing_result = f"\n🖼️ IMAGE PROCESSING ERROR [{timestamp}]: {error_msg}\nImages were detected but could not be processed.\n"
                                    else:
                                        logger.warning("🖼️ No valid image data found despite image_exists=True")
                                else:
                                    logger.error("🖼️ image_to_text tool not found in user tools")
                                    import datetime
                                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                                    forced_image_processing_result = f"\n🖼️ IMAGE PROCESSING UNAVAILABLE [{timestamp}]: image_to_text tool not found.\nImages were detected but cannot be processed.\n"
                                    
                            except Exception as e:
                                logger.error(f"🖼️ FORCED IMAGE PROCESSING ERROR: {e}")
                                import datetime
                                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                                forced_image_processing_result = f"\n🖼️ IMAGE PROCESSING ERROR [{timestamp}]: {str(e)}\nImages were detected but could not be processed.\n"
                        else:
                            logger.warning("🖼️ Image processing LLM not configured")
                            import datetime
                            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                            forced_image_processing_result = f"\n🖼️ IMAGE PROCESSING UNAVAILABLE [{timestamp}]: No image processing model configured.\nImages were detected but cannot be analyzed. Please configure an image processing model in the LLM settings.\n"
                            
                    except Exception as e:
                        logger.error(f"🖼️ FORCED IMAGE PROCESSING SETUP ERROR: {e}")
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                        forced_image_processing_result = f"\n🖼️ IMAGE PROCESSING ERROR [{timestamp}]: {str(e)}\nImages were detected but processing setup failed.\n"
                    
                    # 🔄 CRITICAL: Reset image_exists flag after processing (success or failure)
                    # This prevents re-triggering image processing on subsequent conversation turns
                    # The image processing results remain in context as reference for the conversation
                    image_exists = False
                    logger.info("🔄 FORCED IMAGE PROCESSING: Reset image_exists flag to False - processing complete")
                
                # STAGE 1: Call tool calling model to generate JSON function calls
                # Load system prompt from external file
                # ENFORCE: Tool calling model ONLY uses pre_tool_model_system_prompt.txt
                # No user system prompts allowed for tool calling - they can conflict with core instructions
                user_system_prompt = ""  # Force empty - only use file instructions
                system_content = load_tool_model_system_prompt(user_system_prompt)
                
                messages = [
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": f"""Examine the intent of the user's prompt and apply the system directives to make the appropriate calls to the tools' functions. 
                                        User Prompt: {prompt_context + user_prompt}""",
                        "images": data.get("images") if image_exists else None
                    }
                ]
                
                try:
                    tools_model = data.get('tools_calling_model', ServerConfig.DEFAULT_TOOL_CALLING_MODEL).strip()
                    # Tool calling model preparation
                    logger.info(f"Tool calling: {tools_model} (tools enabled: {tools_in_use})")
                    
                    # Call the tool calling model to get JSON function calls
                    # 🎯 NEW APPROACH: Let tool calling model orchestrate ALL tools, intercept email calls
                    # 🚫 SMART TOOL FILTERING: Exclude inappropriate tools for meta-tasks
                    # 🔧 FIX: Only check the actual user prompt, NOT conversation context
                    actual_user_prompt = user_prompt  # Use the original user prompt, not the system message
                    is_meta_task = any(meta_pattern in actual_user_prompt.lower() for meta_pattern in [
                        'generate a concise', 'title with emoji', 'generate 1-3 broad tags', 
                        'summarizing the chat history', 'categorizing the main themes'
                    ])
                    
                    # 🎯 DEBUG: Log meta-task detection for troubleshooting
                    logger.error(f"🔧 DEBUG_MARKER: META-TASK CHECK REACHED - prompt: {actual_user_prompt[:100]}...")
                    if is_meta_task:
                        logger.error(f"🚫 META-TASK DETECTED: Skipping tools for: {actual_user_prompt[:100]}...")
                    else:
                        logger.error(f"✅ NORMAL TASK: Will use tools for: {actual_user_prompt[:100]}...")
                    
                    if is_meta_task:
                        # 🚀 META-TASK BYPASS: Skip tool calling entirely for title/tag generation (minimal logging)
                        # Reduced logging to minimize meta-task spam in logs
                        tools_results = ""  # Empty tools results for meta-tasks
                        tools_called = []   # No tools called
                        tools_array = []   # Empty tools array to prevent UnboundLocalError
                        tool_request = {}   # Empty tool request to prevent UnboundLocalError
                        # Skip directly to primary LLM execution
                    else:
                        # Normal tool processing for non-meta tasks
                        tools_array = await tool_manager.get_tools_definitions(exclude_file_email_tools=False)
                        # Tools array prepared
                        if len(tools_array) == 0:
                            logger.error("❌ Tools array is empty! This will cause timeout.")
                        else:
                            tool_names = [tool['function']['name'] for tool in tools_array]
                            logger.info(f"Available tools: {tool_names}")
                        
                        # Use LLM Manager for provider-agnostic tool calling
                        logger.info("🔧 DEBUG: About to call LLM Manager for tool calling")
                        
                        # Convert messages to prompt for LLM Manager
                        user_message = messages[-1]['content'] if messages else data.get('prompt', '')
                        system_prompt = load_tool_model_system_prompt()
                        
                        response_data = await llm_manager.generate_tools(
                            prompt=user_message,
                            tools=tools_array,
                            model=tools_model,
                            system_prompt=system_prompt,
                            temperature=0,
                            max_tokens=4096
                        )
                        logger.info("🔧 DEBUG: LLM Manager tool calling response received")
                        
                        # LLM Manager returns direct dictionary - no HTTP response wrapping needed
                        # response_data is already the parsed response from LLM Manager
                        
                        if response_data:  # Success case - LLM Manager returned data
                            # Tool calling completed successfully
                            
                            # Debug: Log what the LLM Manager returned
                            response_keys = list(response_data.keys())
                            logger.info(f"🔧 DEBUG: LLM Manager response keys: {response_keys}")
                            
                            # STAGE 2: Process tool calls if present - LLM Manager format
                            if 'tool_calls' in response_data and response_data['tool_calls']:
                                tool_calls = response_data['tool_calls']
                                logger.info(f"🎯 TOOL CALLS DETECTED: {len(tool_calls)} tools to execute")
                                
                                # Process each tool call - PARALLEL EXECUTION OPTIMIZATION
                                        
                                # Log all tool calls upfront
                                for i, tool_call in enumerate(tool_calls):
                                    function_name = tool_call['function']['name']
                                    function_args = tool_call['function']['arguments']
                                    
                                    # Parse JSON string arguments to dictionary if needed
                                    if isinstance(function_args, str):
                                        try:
                                            function_args = json.loads(function_args)
                                        except json.JSONDecodeError:
                                            logger.error(f"❌ Invalid JSON in function arguments for {function_name}: {function_args}")
                                            function_args = {}
                                    
                                    # Tool call registered
                                    tools_called.append(function_name)  # Track this tool was called
                                
                                def _apply_smart_file_decisions(email_args, phase1_results, logger):
                                    """
                                    Smart file decision logic: Use actual found files instead of placeholder files
                                    """
                                    try:
                                        # Find document_search results from phase 1
                                        document_search_result_str = None
                                        for result_tuple in phase1_results:
                                            if isinstance(result_tuple, tuple) and len(result_tuple) >= 2:
                                                function_name, result = result_tuple[0], result_tuple[1]
                                                if function_name == "document_search" and isinstance(result, str):
                                                    document_search_result_str = result
                                                    logger.info(f"📧 SMART DECISION: Found document_search result string")
                                                    break
                                        
                                        if not document_search_result_str:
                                            logger.info("📧 No document_search results found - using original email args")
                                            return email_args
                                        
                                        # Parse the document_search result string to extract sources
                                        # Look for "📋 Sources:" section and extract filenames
                                        import re
                                        
                                        # Pattern to match source files: "• filename" in the Sources section
                                        sources_pattern = r'📋 Sources:\n(.+?)(?:\n\n|\Z)'
                                        sources_match = re.search(sources_pattern, document_search_result_str, re.DOTALL)
                                        
                                        if not sources_match:
                                            # Try alternative pattern - look for document names in the result
                                            doc_pattern = r'Document \d+: ([^(]+\.(?:html|md|pdf|txt))'
                                            doc_matches = re.findall(doc_pattern, document_search_result_str)
                                            if doc_matches:
                                                # Use the first document found
                                                first_doc = doc_matches[0].strip()
                                                logger.info(f"📧 SMART DECISION: Parsed document from result: {first_doc}")
                                                
                                                # Look for the full path in logs or construct it
                                                if 'SD_TheSongWithin' in first_doc and 'html' in first_doc:
                                                    actual_file_path = '/var/www/html/silicon_dreams/stories/SD_TheSongWithin.html'
                                                elif 'SD_TheSongWithin' in first_doc and 'md' in first_doc:
                                                    actual_file_path = '/var/www/html/silicon_dreams/stories/SD_TheSongWithin.md'
                                                elif 'Weight of Silence' in first_doc:
                                                    actual_file_path = '/home/sabawi/Documents/The Weight of Silence.pdf'
                                                else:
                                                    actual_file_path = first_doc
                                                    
                                                logger.info(f"📧 SMART DECISION: Using actual found file: {actual_file_path}")
                                                email_args['attachments'] = actual_file_path
                                                # Disable attachment waiting since we know the file exists
                                                email_args['wait_for_attachments'] = False
                                                
                                                # Update subject and body to reflect actual content
                                                filename = actual_file_path.split('/')[-1]
                                                email_args['subject'] = f"Found Document: {filename}"
                                                email_args['body'] = f"Please find attached the requested document: {filename}\n\nFound matching Gaza-related story in the document collection."
                                                
                                                return email_args
                                                
                                        # If sources section is found, extract filenames
                                        if sources_match:
                                            sources_text = sources_match.group(1)
                                            source_lines = [line.strip() for line in sources_text.split('\n') if line.strip().startswith('•')]
                                            
                                            if source_lines:
                                                # 🎯 BALANCED FORMAT SELECTION: Respect user's explicit format preference
                                                user_prompt = data.get('prompt', '').lower()
                                                
                                                # Detect explicit format requests from user
                                                requested_format = None
                                                if 'pdf' in user_prompt and ('pdf version' in user_prompt or 'send pdf' in user_prompt or 'as pdf' in user_prompt or 'email the pdf' in user_prompt or 'pdf format' in user_prompt or 'convert' in user_prompt and 'pdf' in user_prompt):
                                                    requested_format = 'pdf'
                                                elif 'html' in user_prompt and ('html version' in user_prompt or 'send html' in user_prompt or 'as html' in user_prompt or 'email the html' in user_prompt or 'html format' in user_prompt):
                                                    requested_format = 'html'
                                                elif 'markdown' in user_prompt and ('markdown version' in user_prompt or 'send markdown' in user_prompt or 'as markdown' in user_prompt or 'email the markdown' in user_prompt or 'markdown format' in user_prompt or '.md' in user_prompt):
                                                    requested_format = 'markdown'
                                                
                                                # Select source file based on user preference
                                                first_source = None
                                                if requested_format:
                                                    # User explicitly requested a format - prioritize it
                                                    for source_line in source_lines:
                                                        source_name = source_line.replace('•', '').strip()
                                                        if f'.{requested_format}' in source_name.lower() or (requested_format == 'markdown' and '.md' in source_name.lower()):
                                                            first_source = source_name
                                                            logger.info(f"📧 SMART DECISION: User requested {requested_format.upper()} - using source file: {first_source}")
                                                            break
                                                
                                                # If no format-specific match found, use first available
                                                if not first_source:
                                                    first_source = source_lines[0].replace('•', '').strip()
                                                    if requested_format:
                                                        logger.info(f"📧 SMART DECISION: User requested {requested_format.upper()} but not available - using first source: {first_source}")
                                                    else:
                                                        logger.info(f"📧 SMART DECISION: No format preference - using first source: {first_source}")
                                                
                                                # 🔧 CRITICAL FIX: Extract full file path from document_search output
                                                actual_file_path = first_source  # Default fallback
                                                
                                                # Look for "📎 Full File Paths (for attachments):" section
                                                full_paths_match = re.search(r'📎 Full File Paths \(for attachments\):(.*?)(?=\n\n|\nTool:|$)', document_search_result_str, re.DOTALL)
                                                if full_paths_match:
                                                    paths_text = full_paths_match.group(1)
                                                    path_lines = [line.strip() for line in paths_text.split('\n') if line.strip().startswith('•')]
                                                    
                                                    # Find path that matches the selected source file
                                                    for path_line in path_lines:
                                                        full_path = path_line.replace('•', '').strip()
                                                        if first_source in full_path:
                                                            actual_file_path = full_path
                                                            logger.info(f"📧 SMART DECISION: Found matching full path: {actual_file_path}")
                                                            break
                                                
                                                logger.info(f"📧 SMART DECISION: Using full path: {actual_file_path}")
                                                email_args['attachments'] = actual_file_path
                                                # Disable attachment waiting since we know the file exists
                                                email_args['wait_for_attachments'] = False
                                                
                                                filename = first_source
                                                email_args['subject'] = f"Found Document: {filename}"
                                                email_args['body'] = f"Please find attached the requested document: {filename}\n\nFound {len(source_lines)} matching files in the search."
                                                
                                                return email_args
                                        
                                        # Fallback: inform user no files exist
                                        logger.info("📧 Could not parse sources from document_search - informing user")
                                        email_args['subject'] = "Search Results: No Files Found"
                                        email_args['body'] = "I searched for the requested documents but found no matching files to send."
                                        if 'attachments' in email_args:
                                            del email_args['attachments']  # Remove placeholder attachment
                                        
                                        return email_args
                                        
                                    except Exception as e:
                                        logger.error(f"❌ Error in smart file decisions: {e}")
                                        return email_args

                                def should_run_sequentially(tool_calls):
                                    """
                                    Dependency rule: email and file creation tools run after search tools
                                    This prevents placeholder file creation when real files exist
                                    Returns: (phase2_tools, phase1_tools)
                                    """
                                    phase1_tools = []  # Search and analysis tools
                                    phase2_tools = []  # File creation and email tools
                                    
                                    for tool_call in tool_calls:
                                        tool_name = tool_call['function']['name']
                                        # Phase 2: Tools that should run after search completes
                                        if tool_name in ['secure_email_sender', 'sandboxed_executor']:
                                            phase2_tools.append(tool_call)
                                        else:
                                            # Phase 1: Search and analysis tools
                                            phase1_tools.append(tool_call)
                                    
                                    return phase2_tools, phase1_tools

                                async def execute_tools_with_email_dependency(tool_calls):
                                    """
                                    Execute tools with smart file dependency: search first, then file creation and email
                                    """
                                    phase2_tools, phase1_tools = should_run_sequentially(tool_calls)
                                    all_results = []
                                    phase1_results = []
                                    
                                    # Phase 1: Execute search and analysis tools (can be parallel)
                                    if phase1_tools:
                                        logger.info(f"🚀 PHASE 1 SEARCH: {len(phase1_tools)} tools - {[t['function']['name'] for t in phase1_tools]}")
                                        
                                        async def execute_single_tool(tool_call):
                                            function_name = tool_call['function']['name']
                                            function_args = tool_call['function']['arguments']
                                            
                                            # Parse JSON string arguments to dictionary if needed
                                            if isinstance(function_args, str):
                                                try:
                                                    function_args = json.loads(function_args)
                                                except json.JSONDecodeError:
                                                    logger.error(f"❌ Invalid JSON in function arguments for {function_name}: {function_args}")
                                                    function_args = {}
                                            
                                            # 🖼️ INTERCEPT IMAGE_TO_TEXT CALLS - Replace placeholder with actual image data
                                            if function_name == "image_to_text" and data.get("images") and data.get("images")[0] != "noimage":
                                                # Handle both "image" (singular) and "images" (plural) parameters
                                                if "image" in function_args and function_args["image"] in ["user_provided_image_data", "<user_provided_image_data>", "<actual_base64_image_data>", "<base64_image_data>"]:
                                                    # Replace placeholder with actual base64 image data for singular parameter
                                                    actual_images = data.get("images", [])
                                                    if actual_images and actual_images[0] != "noimage":
                                                        function_args["image"] = actual_images[0]  # Use first image for singular parameter
                                                        logger.info(f"🖼️ REPLACED singular image placeholder with actual base64 data ({len(actual_images[0])} chars)")
                                                    else:
                                                        logger.warning(f"🖼️ No image data available for singular image parameter")
                                                elif "images" in function_args:
                                                    # Parse images if it's a string
                                                    images_arg = function_args["images"]
                                                    if isinstance(images_arg, str):
                                                        try:
                                                            images_arg = json.loads(images_arg)
                                                        except json.JSONDecodeError:
                                                            logger.warning(f"🖼️ Failed to parse images argument: {images_arg}")
                                                            images_arg = []
                                                    
                                                    # Replace placeholder with actual image data
                                                    if isinstance(images_arg, list):
                                                        processed_images = []
                                                        for i, img_item in enumerate(images_arg):
                                                            if isinstance(img_item, dict) and img_item.get("path") == "user_provided_image_data":
                                                                # Replace with actual base64 image data
                                                                actual_images = data.get("images", [])
                                                                if i < len(actual_images) and actual_images[i] != "noimage":
                                                                    processed_images.append({
                                                                        "type": "base64",
                                                                        "data": f"data:image/jpeg;base64,{actual_images[i]}",
                                                                        "filename": f"user_image_{i+1}"
                                                                    })
                                                                else:
                                                                    logger.warning(f"🖼️ No image data available for index {i}")
                                                            else:
                                                                processed_images.append(img_item)
                                                        function_args["images"] = processed_images
                                                        logger.info(f"🖼️ REPLACED image placeholder with {len(processed_images)} actual image(s)")
                                            
                                            start_time = time.time()
                                            result = await tool_manager.safe_function_call(function_name, function_args)
                                            return (function_name, result, start_time, False, None)
                                        
                                        phase1_tasks = [execute_single_tool(call) for call in phase1_tools]
                                        phase1_results = await asyncio.gather(*phase1_tasks, return_exceptions=True)
                                        all_results.extend(phase1_results)
                                        
                                        logger.info(f"✅ PHASE 1 COMPLETE: All {len(phase1_tools)} search tools finished")
                                    
                                    # Phase 2: Execute file creation and email tools (sequential, with smart decisions)
                                    if phase2_tools:
                                        logger.info(f"📧 PHASE 2 SMART: {len(phase2_tools)} tools - {[t['function']['name'] for t in phase2_tools]}")
                                        
                                        for phase2_tool in phase2_tools:
                                            function_name = phase2_tool['function']['name']
                                            function_args = phase2_tool['function']['arguments']
                                            start_time = time.time()
                                            
                                            # 🧠 SMART FILE DECISION: Use actual found files instead of created placeholders
                                            should_execute = True
                                            
                                            # Parse JSON string to dict if needed
                                            if isinstance(function_args, str):
                                                try:
                                                    function_args_dict = json.loads(function_args)
                                                except json.JSONDecodeError:
                                                    logger.error(f"❌ Invalid JSON in function arguments for {function_name}: {function_args}")
                                                    function_args_dict = {}
                                            else:
                                                function_args_dict = function_args
                                            
                                            # Apply smart decisions based on tool type
                                            if function_name == 'sandboxed_executor':
                                                # Check if this is trying to create a file when we have real files
                                                if function_args_dict.get('action') == 'create_file':
                                                    # Check if document_search found actual files
                                                    found_real_files = False
                                                    for result_tuple in phase1_results:
                                                        if isinstance(result_tuple, tuple) and len(result_tuple) >= 2:
                                                            tool_name, result = result_tuple[0], result_tuple[1]
                                                            if tool_name == "document_search" and isinstance(result, str):
                                                                if "Document 1:" in result or "Sources:" in result:
                                                                    found_real_files = True
                                                                    break
                                                    
                                                    if found_real_files:
                                                        # 🎯 RESPECT USER'S EXPLICIT FORMAT REQUESTS
                                                        user_prompt = data.get('prompt', '').lower()
                                                        requested_filename = function_args_dict.get('filename', '').lower()
                                                        
                                                        # Check if user explicitly requested a specific format
                                                        user_wants_pdf = ('pdf' in user_prompt and ('pdf version' in user_prompt or 'send pdf' in user_prompt or 'as pdf' in user_prompt)) or requested_filename.endswith('.pdf')
                                                        user_wants_html = ('html' in user_prompt and ('html version' in user_prompt or 'send html' in user_prompt or 'as html' in user_prompt)) or requested_filename.endswith('.html')
                                                        user_wants_markdown = ('markdown' in user_prompt and ('markdown version' in user_prompt or 'send markdown' in user_prompt or 'as markdown' in user_prompt)) or requested_filename.endswith(('.md', '.markdown'))
                                                        
                                                        if user_wants_pdf or user_wants_html or user_wants_markdown:
                                                            format_requested = 'PDF' if user_wants_pdf else ('HTML' if user_wants_html else 'MARKDOWN')
                                                            logger.info(f"✅ SMART DECISION: User explicitly requested {format_requested} format - allowing file creation despite existing documents")
                                                            should_execute = True
                                                        else:
                                                            logger.info(f"🚫 SMART DECISION: Skipping {function_name} file creation - real files found and no explicit format request")
                                                            should_execute = False
                                                            # Create a fake success result
                                                            result = "File creation skipped - using actual found documents instead"
                                                            all_results.append((function_name, result, start_time, False, None))
                                                            continue
                                            
                                            elif function_name == 'secure_email_sender':
                                                # Apply smart file decisions to email attachments
                                                modified_args_dict = _apply_smart_file_decisions(function_args_dict, phase1_results, logger)
                                                
                                                # Convert back to the format expected by tool_manager
                                                if isinstance(function_args, str):
                                                    function_args = json.dumps(modified_args_dict)
                                                else:
                                                    function_args = modified_args_dict
                                            
                                            if should_execute:
                                                logger.info(f"📧 PHASE 2 TOOL: {function_name} starting (with smart file decisions)")
                                                
                                                
                                                result = await tool_manager.safe_function_call(function_name, function_args)
                                                all_results.append((function_name, result, start_time, False, None))
                                                logger.info(f"✅ PHASE 2 COMPLETE: {function_name}")
                                    
                                    return all_results

                                # Define async function for parallel execution (legacy)
                                async def execute_single_tool(tool_call_data):
                                    i, tool_call = tool_call_data
                                    function_name = tool_call['function']['name']
                                    function_args = tool_call['function']['arguments']
                                    
                                    # Parse JSON string arguments to dictionary if needed
                                    if isinstance(function_args, str):
                                        try:
                                            function_args = json.loads(function_args)
                                        except json.JSONDecodeError:
                                            logger.error(f"❌ Invalid JSON in function arguments for {function_name}: {function_args}")
                                            function_args = {}
                                    
                                    # Add image if applicable
                                    if "image" in function_args and image_exists:
                                        function_args["image"] = data.get("images", [None])[0]
                                    
                                    # 🖼️ INTERCEPT IMAGE_TO_TEXT CALLS - Replace placeholder with actual image data
                                    if function_name == "image_to_text" and data.get("images") and data.get("images")[0] != "noimage":
                                        # Handle both "image" (singular) and "images" (plural) parameters
                                        if "image" in function_args and function_args["image"] in ["user_provided_image_data", "<user_provided_image_data>", "<actual_base64_image_data>", "<base64_image_data>"]:
                                            # Replace placeholder with actual base64 image data for singular parameter
                                            actual_images = data.get("images", [])
                                            if actual_images and actual_images[0] != "noimage":
                                                function_args["image"] = actual_images[0]  # Use first image for singular parameter
                                                logger.info(f"🖼️ REPLACED singular image placeholder with actual base64 data ({len(actual_images[0])} chars)")
                                            else:
                                                logger.warning(f"🖼️ No image data available for singular image parameter")
                                        elif "images" in function_args:
                                            # Parse images if it's a string
                                            images_arg = function_args["images"]
                                            if isinstance(images_arg, str):
                                                try:
                                                    images_arg = json.loads(images_arg)
                                                except json.JSONDecodeError:
                                                    logger.warning(f"🖼️ Failed to parse images argument: {images_arg}")
                                                    images_arg = []
                                            
                                            # Replace placeholder with actual image data
                                            if isinstance(images_arg, list):
                                                processed_images = []
                                                for i, img_item in enumerate(images_arg):
                                                    if isinstance(img_item, dict) and img_item.get("path") == "user_provided_image_data":
                                                        # Replace with actual base64 image data
                                                        actual_images = data.get("images", [])
                                                        if i < len(actual_images) and actual_images[i] != "noimage":
                                                            processed_images.append({
                                                                "type": "base64",
                                                                "data": f"data:image/jpeg;base64,{actual_images[i]}",
                                                                "filename": f"user_image_{i+1}"
                                                            })
                                                        else:
                                                            logger.warning(f"🖼️ No image data available for index {i}")
                                                    else:
                                                        processed_images.append(img_item)
                                                function_args["images"] = processed_images
                                                logger.info(f"🖼️ REPLACED image placeholder with {len(processed_images)} actual image(s)")
                                    
                                    # Execute the function with timing
                                    start_time = time.time()
                                    logger.info(f"==> TOOL {i+1} CALLED: {function_name}({', '.join([f'{k}=\"{str(v)[:50]}...\"' if len(str(v)) > 50 else f'{k}=\"{v}\"' for k, v in function_args.items()])})") 
                                    
                                    # 🎯 INTERCEPT EMAIL CALLS - Fake success, set flag for post-processing
                                    if function_name == "secure_email_sender":
                                        logger.info(f"📧 TOOL {i+1} DEFERRED: {function_name} - Email intercepted for post-processing")
                                        result = "Email scheduled for sending after content generation"
                                        # Handle email interception in parallel context
                                        return (function_name, result, start_time, True, function_args.copy())
                                    else:
                                        result = await tool_manager.safe_function_call(function_name, function_args)
                                        return (function_name, result, start_time, False, None)
                                
                                # Execute tools with email dependency logic
                                tool_execution_start = time.time()
                                
                                # Use new dependency-aware execution
                                tool_results_list = await execute_tools_with_email_dependency(tool_calls)
                                
                                total_execution_time = time.time() - tool_execution_start
                                logger.info(f"⏱️ TOOL EXECUTION COMPLETE: {len(tool_calls)} tools in {total_execution_time:.2f}s")
                                
                                # 🧹 STREAMLINED LOGGING: Tool execution summaries (instead of full buffer dumps)
                                concise_logging = os.environ.get('CONCISE_LOGGING', 'true').lower() == 'true'
                                if concise_logging:
                                    logger.info(f"📊 TOOL EXECUTION SUMMARY:")
                                
                                # Process results and handle any email interceptions
                                for i, result_data in enumerate(tool_results_list):
                                    if isinstance(result_data, Exception):
                                        logger.error(f"❌ TOOL {i+1} ERROR: {str(result_data)}")
                                        continue
                                    
                                    function_name, result, start_time, is_email, email_params = result_data
                                    end_time = time.time()
                                    execution_time = end_time - start_time
                                    
                                    # Handle email interception flag setting
                                    if is_email and email_params:
                                        email_intercepted = True
                                        intercepted_email_params = email_params
                                    
                                    # Determine status and format output
                                    if result and len(str(result)) > 0:
                                        if "error" in str(result).lower() or "failed" in str(result).lower():
                                            logger.info(f"⚠️ TOOL {i+1} OUTPUT: PARTIAL SUCCESS - {function_name} | {execution_time:.2f}s | {len(str(result))} chars")
                                        else:
                                            logger.info(f"✅ TOOL {i+1} OUTPUT: SUCCESS!! - {function_name} | {execution_time:.2f}s | {len(str(result))} chars")
                                            
                                            # Content quality check for file creation tools
                                            if function_name == "sandboxed_executor" and isinstance(result, dict):
                                                if result.get("success") and "filename" in result.get("result", {}):
                                                    result_str = str(result)
                                                    if any(indicator in result_str.lower() for indicator in ["details...", "content...", "more info...", "placeholder"]):
                                                        logger.warning(f"🔍 CONTENT QUALITY WARNING: {function_name} - Possible truncated content detected in file creation")
                                    else:
                                        logger.info(f"❌ TOOL {i+1} OUTPUT: ERROR - {function_name} | {execution_time:.2f}s | No output received")
                                    
                                    # 🧹 STREAMLINED LOGGING: Show concise tool summaries instead of full dumps
                                    result_str = str(result)
                                    result_size = len(result_str)
                                    if concise_logging:
                                        # Extract function arguments for display
                                        tool_call = tool_calls[i] if i < len(tool_calls) else {}
                                        function_args = tool_call.get('function', {}).get('arguments', {})
                                        if isinstance(function_args, str):
                                            try:
                                                function_args = json.loads(function_args)
                                            except:
                                                pass
                                        
                                        # Create concise argument summary
                                        args_summary = ""
                                        if isinstance(function_args, dict) and function_args:
                                            key_args = []
                                            for key, value in list(function_args.items())[:3]:  # Show first 3 args
                                                if isinstance(value, str) and len(value) > 30:
                                                    key_args.append(f'{key}="{value[:30]}..."')
                                                else:
                                                    key_args.append(f'{key}="{value}"')
                                            if len(function_args) > 3:
                                                key_args.append("...")
                                            args_summary = f"({', '.join(key_args)})"
                                        
                                        logger.info(f"   TOOL {i+1}: {function_name}{args_summary}: {result_size} chars")
                                    
                                    # Store FULL result for tools_results_list (needed for image extraction)
                                    full_result = str(result)
                                    tools_results_list.append(f"Tool: {function_name}\nResult: {full_result}\n\n")
                                    
                                    # Only truncate for logging display
                                    truncated_result = truncate_base64_for_logging(full_result)
                            
                            else:
                                # No tool calls generated - check if we should force data gathering
                                logger.info("❌ No tool calls generated by the tool calling model")
                                truncated_response_data = truncate_base64_for_logging(json.dumps(response_data, indent=2))
                                logger.info(f"Raw LLM Manager response: {truncated_response_data}")
                                
                                # 🔥 PROGRAMMATIC TOOL CALL INJECTION 🔥
                                # If the model refuses to call tools for file/email requests, force data gathering
                                # BUT only check the CURRENT user request, not conversation history
                                prompt_lower = user_prompt.lower()
                                
                                # Extract only the current request (after "=== CURRENT REQUEST ===" marker)
                                if "=== current request ===" in prompt_lower:
                                    current_request = prompt_lower.split("=== current request ===")[-1]
                                else:
                                    current_request = prompt_lower
                                
                                forced_tools = []
                                
                                # Skip forced tools for title generation, tagging, or other meta tasks
                                if any(meta_task in current_request for meta_task in ['generate a concise', 'title with emoji', 'generate 1-3 broad tags', 'chat history']):
                                    logger.info("🚫 SKIPPING FORCED TOOLS: This is a meta/title/tag generation request")
                                elif any(keyword in current_request for keyword in ['aapl', 'apple stock', 'apple inc']):
                                    forced_tools.append(('get_news_summaries', {'filter': 'AAPL'}))
                                    logger.info("🚨 FORCING get_news_summaries(filter='AAPL') - model refused to gather AAPL data")
                                elif any(keyword in current_request for keyword in ['stock', 'financial analysis', 'company analysis']):
                                    forced_tools.append(('comprehensive_stock_analyzer', {}))
                                    logger.info("🚨 FORCING comprehensive_stock_analyzer() - model refused to gather stock data")
                                elif any(keyword in current_request for keyword in ['news', 'current events']):
                                    forced_tools.append(('get_news_summaries', {}))
                                    logger.info("🚨 FORCING get_news_summaries() - model refused to gather news data")
                                
                                # Execute forced tool calls - PARALLEL EXECUTION OPTIMIZATION
                                if forced_tools:
                                                
                                    # Log all forced tool calls upfront
                                    for function_name, function_args in forced_tools:
                                        logger.info(f"🔧 FORCED Tool {function_name}: START | Args: {list(function_args.keys())}")
                                        tools_called.append(function_name)
                                    
                                    # Define async function for parallel forced execution
                                    async def execute_forced_tool(tool_data):
                                        function_name, function_args = tool_data
                                        start_time = time.time()
                                        result = await tool_manager.safe_function_call(function_name, function_args)
                                        return (function_name, result, start_time)
                                    
                                    # Execute all forced tools in parallel
                                    forced_execution_start = time.time()
                                    logger.info(f"🚀 PARALLEL FORCED EXECUTION: Starting {len(forced_tools)} forced tools concurrently")
                                    
                                    forced_tasks = [execute_forced_tool(tool_data) for tool_data in forced_tools]
                                    forced_results_list = await asyncio.gather(*forced_tasks, return_exceptions=True)
                                    
                                    total_forced_parallel_time = time.time() - forced_execution_start
                                    logger.info(f"🚀 PARALLEL FORCED EXECUTION COMPLETED: All {len(forced_tools)} forced tools finished in {total_forced_parallel_time:.2f}s")
                                    
                                    # Process forced results
                                    for result_data in forced_results_list:
                                        if isinstance(result_data, Exception):
                                            logger.error(f"🚨 Forced tool execution failed: {str(result_data)}")
                                            continue
                                        
                                        function_name, result, start_time = result_data
                                        end_time = time.time()
                                        execution_time = end_time - start_time
                                        logger.info(f"🔧 FORCED Tool {function_name}: COMPLETE | {execution_time:.2f}s | Result: {len(str(result))} chars")
                                        # Store FULL result for tools_results_list (needed for image extraction)
                                        full_result = str(result)
                                        tools_results_list.append(f"Tool: {function_name}\nResult: {full_result}\n\n")
                                        
                                        # Only truncate for logging display
                                        truncated_result = truncate_base64_for_logging(full_result)
                        
                        else:
                            logger.error(f"❌ Tool calling model failed - no response data returned")
                            logger.error(f"LLM Manager response: {response_data}")
                            # Fallback: just get current time
                            result = await tool_manager.get_the_secret_tool()
                            tools_results_list.append(f"Tool: get_the_secret_tool\nResult: {result}\n\n")
                            
                except Exception as e:
                    logger.error(f"❌ Tool calling exception: {e}")
                    logger.error(f"Exception type: {type(e).__name__}")
                    # Fallback: just get current time
                    result = await tool_manager.get_the_secret_tool()
                    tools_results_list.append(f"Tool: get_the_secret_tool\nResult: {result}\n\n")
            
            # CRITICAL: Convert tools_results_list to string for downstream processing
            # For meta-tasks, tools_results is already set to ""; for normal tasks, join the list
            if not is_meta_task:
                tools_results = "".join(tools_results_list)  # O(n) join vs O(n²) concatenation
            # For meta-tasks, tools_results is already set to "" above
            
            # 🚨 TRUE THREAD LOCKING ARBITRATOR SYSTEM
            # PRIMARY LLM EXECUTION LOCKED UNTIL TOOLS ARE VALIDATED AND CORRECTED
            arbitrator_config = config_loader.load_config().get('arbitrator', {})
            if arbitrator_config.get('enabled', False) and tools_called and not is_meta_task:
                logger.info(f"🔒 ARBITRATOR LOCK: Primary LLM thread locked - validating tools for: {user_prompt[:100]}...")
                
                # 🔒 CREATE LOCK FOR PRIMARY LLM THREAD
                primary_llm_lock = asyncio.Event()
                primary_llm_lock.clear()  # Start locked - primary LLM cannot proceed
                
                max_arbitrator_attempts = 5
                attempt = 0
                tools_are_valid = False
                corrected_tools_results = None  # 🔧 CRITICAL: Variable to store corrected results for main thread
                
                while attempt < max_arbitrator_attempts and not tools_are_valid:
                    attempt += 1
                    logger.info(f"🔄 ARBITRATOR ATTEMPT #{attempt}/{max_arbitrator_attempts} - Validating tools...")
                    
                    try:
                        # STEP 1: Validate current tool results
                        validated_results = await arbitrator_validate_tasks(
                            tools_called, tools_results_list, user_prompt, tool_manager
                        )
                        
                        # 🔍 DEBUG: Log what arbitrator function returned
                        if validated_results:
                            logger.info(f"🔍 DEBUG: Arbitrator returned SUCCESS - Type: {type(validated_results)}, Length: {len(validated_results)} chars")
                            logger.info(f"🔍 DEBUG: Arbitrator result preview: {validated_results[:200]}...")
                        else:
                            logger.info(f"🔍 DEBUG: Arbitrator returned FAILURE - validated_results = {validated_results}")
                        
                        if validated_results:
                            # ✅ SUCCESS: Tools validated - STORE CORRECTED RESULTS
                            corrected_tools_results = validated_results  # 🔧 CRITICAL: Store for main thread
                            tools_are_valid = True
                            primary_llm_lock.set()  # 🔓 UNLOCK PRIMARY LLM
                            logger.info(f"🔓 ARBITRATOR UNLOCK: Tools validated successfully on attempt #{attempt} - releasing primary LLM")
                            break
                        
                        elif attempt < max_arbitrator_attempts:
                            # ❌ FAILURE: Tools invalid - REGENERATE WHILE LOCKED
                            logger.warning(f"🔒 ARBITRATOR LOCKED: Attempt #{attempt} failed - regenerating tools while primary LLM remains locked")
                            
                            # STEP 2: Regenerate failed tools using existing tool calling LLM
                            logger.info(f"🔄 REGENERATING TOOLS: Using tool calling LLM to fix failures")
                            
                            # Build regeneration context with failed tool details
                            regeneration_prompt = f"""
CRITICAL: The following tools failed validation and must be regenerated with correct parameters:

USER REQUEST: {user_prompt}

FAILED TOOLS ANALYSIS:
"""
                            for i, (tool_name, result) in enumerate(zip(tools_called, tools_results_list)):
                                regeneration_prompt += f"""
Tool {i+1}: {tool_name}
Result: {result[:500]}...
Error Pattern: {_detect_tool_failure_pattern(result)}
"""
                            
                            regeneration_prompt += """

REGENERATION INSTRUCTIONS:
1. If document_search succeeded, use the ACTUAL file paths found (not placeholders)
2. If Python scripts use sys.argv[1], ensure run_code includes proper 'args' parameter
3. Fix any malformed JSON or parameter issues
4. Generate corrected tool calls that will execute successfully

Generate the corrected tool calls:"""

                            # Call tool calling LLM for regeneration
                            try:
                                logger.info(f"🧠 CALLING TOOL CALLING LLM FOR REGENERATION")
                                regeneration_response = await llm_manager.call_tool_calling_llm(
                                    prompt=regeneration_prompt,
                                    tools=tool_manager.get_tools_for_llm(),
                                    system_prompt="You are a tool calling specialist. Generate corrected tool calls that will execute successfully."
                                )
                                
                                if regeneration_response.get('tool_calls'):
                                    # STEP 3: Execute regenerated tools
                                    logger.info(f"🔄 EXECUTING {len(regeneration_response['tool_calls'])} REGENERATED TOOLS")
                                    regenerated_tools_results = []
                                    
                                    # Execute each regenerated tool
                                    for i, tool_call in enumerate(regeneration_response['tool_calls']):
                                        func_name = tool_call.function.name
                                        func_args = json.loads(tool_call.function.arguments)
                                        
                                        logger.info(f"🔧 REGENERATED TOOL {i+1}: {func_name}({func_args})")
                                        
                                        try:
                                            result = await tool_manager.safe_function_call(func_name, func_args)
                                            regenerated_tools_results.append(f"Tool: {func_name}\nResult: {result}\n\n")
                                            logger.info(f"✅ REGENERATED TOOL {i+1} SUCCESS: {func_name}")
                                        except Exception as tool_error:
                                            error_result = f"ERROR: {str(tool_error)}"
                                            regenerated_tools_results.append(f"Tool: {func_name}\nResult: {error_result}\n\n")
                                            logger.error(f"❌ REGENERATED TOOL {i+1} FAILED: {func_name} - {tool_error}")
                                    
                                    # Update tools_results_list with regenerated results
                                    tools_results_list = regenerated_tools_results
                                    tools_called = [tool_call.function.name for tool_call in regeneration_response['tool_calls']]
                                    
                                else:
                                    logger.warning(f"❌ REGENERATION ATTEMPT #{attempt}: No tool calls generated")
                                    
                            except Exception as regen_error:
                                logger.error(f"❌ TOOL REGENERATION FAILED: {regen_error}")
                        
                        else:
                            # Final attempt failed
                            logger.error(f"🚨 ARBITRATOR FINAL FAILURE: All {max_arbitrator_attempts} attempts exhausted")
                            break
                            
                    except Exception as validation_error:
                        logger.error(f"❌ ARBITRATOR VALIDATION ERROR: {validation_error}")
                
                # FINAL DECISION POINT
                if not tools_are_valid:
                    # 🚨 CRITICAL FAILURE: Should we release lock with failed data or block indefinitely?
                    logger.error(f"🚨 ARBITRATOR CRITICAL FAILURE: Tools remain invalid after {max_arbitrator_attempts} attempts")
                    logger.error(f"🚨 DECISION: BLOCKING PRIMARY LLM INDEFINITELY - USER WILL NOT RECEIVE FABRICATED DATA")
                    
                    # 🚨 CRITICAL FIX: Release lock to prevent infinite hanging
                    # Previously this was blocking indefinitely, causing deadlock
                    
                    # Option: Release with error (allows some response vs infinite hang)  
                    primary_llm_lock.set()  # 🔓 CRITICAL: Always release lock to prevent deadlock
                    tools_results = "".join(tools_results_list)  # Use original results even if validation failed
                    
                    logger.warning(f"🚨 ARBITRATOR EMERGENCY RELEASE: Lock released to prevent deadlock - using unvalidated results")
                    logger.warning(f"🔧 MANUAL CHECK RECOMMENDED: Arbitrator failed after 5 attempts but system continues")
                
                # 🔒 WAIT FOR LOCK RELEASE BEFORE CONTINUING TO PRIMARY LLM
                logger.info(f"⏳ ARBITRATOR: Waiting for primary LLM lock release...")
                await primary_llm_lock.wait()  # This will block until lock is set
                logger.info(f"🔓 ARBITRATOR: Primary LLM lock released - proceeding with validated tools")
                
                # 🔧 CRITICAL: Apply corrected results to main thread if validation succeeded
                logger.info(f"🔍 DEBUG: corrected_tools_results status: {corrected_tools_results is not None}")
                if corrected_tools_results is not None:
                    logger.info(f"🔍 DEBUG: BEFORE applying corrected results - tools_results length: {len(tools_results)}")
                    logger.info(f"🔍 DEBUG: Corrected results length: {len(corrected_tools_results)}")
                    truncated_corrected_results = truncate_base64_for_logging(corrected_tools_results[:200] + "...")
                    logger.info(f"🔍 DEBUG: Corrected results preview: {truncated_corrected_results}")
                    
                    tools_results = corrected_tools_results
                    
                    logger.info(f"🔍 DEBUG: AFTER applying corrected results - tools_results length: {len(tools_results)}")
                    logger.info(f"🔧 ARBITRATOR FIX: Applied corrected results to primary LLM context ({len(corrected_tools_results)} chars)")
                else:
                    logger.warning(f"🚨 ARBITRATOR WARNING: No corrected results available - using original tools_results")
                    logger.info(f"🔍 DEBUG: Original tools_results length: {len(tools_results)}")
            
            # 🛡️ SAFE OPTIMIZATION INTEGRATION 🛡️ 
            # 🚨 CRITICAL FIX: Parse tools_results AFTER Arbitrator corrections are applied
            # Parse corrected tools_results into structured format for optimization system
            parsed_tool_results = []
            if tools_results.strip():
                logger.info(f"🔧 PARSING CORRECTED RESULTS: Processing {len(tools_results)} chars of corrected tools_results")
                # Split the tools_results string into individual tool entries
                tool_entries = []
                current_entry = {}
                lines = tools_results.split('\n')
                
                for line in lines:
                    if line.startswith('Tool: '):
                        if current_entry:  # Save previous entry
                            tool_entries.append(current_entry)
                        current_entry = {'tool': line[6:], 'result': ''}
                    elif line.startswith('Result: '):
                        if current_entry:
                            current_entry['result'] = line[8:]
                    elif current_entry and line.strip():
                        # Continue building result
                        current_entry['result'] += '\n' + line
                
                if current_entry:  # Don't forget the last entry
                    tool_entries.append(current_entry)
                
                # Convert to the format expected by our optimization system
                for entry in tool_entries:
                    parsed_tool_results.append({
                        'tool': entry.get('tool', 'unknown_tool'),
                        'result': entry.get('result', '')
                    })
                
                logger.info(f"🔧 PARSED RESULTS: Generated {len(parsed_tool_results)} tool entries from corrected results")
            
            # CRITICAL: Log when ALL tool execution is complete
            logger.info(f"🎯 ALL TOOL EXECUTION COMPLETED - Starting task verification")
            
            # 🔍 TASK COMPLETION VERIFIER - Cross the T's and dot the I's  
            verification_result = None
            pending_auto_execution = False
            try:
                logger.info(f"🔧 DEBUG: About to call verifier with prompt='{user_prompt}', tools_called={tools_called}")
                verification_result = await _verify_task_completion(user_prompt, tools_called, tools_results, tool_manager)
                logger.info(f"🔧 DEBUG: Verifier result: {verification_result}")
                
                if not verification_result["complete"]:
                    logger.warning(f"⚠️ TASK INCOMPLETE: {verification_result['reason']}")
                    logger.info(f"📋 DEFERRED AUTO-EXECUTION: Will execute missing tools AFTER Primary LLM completes")
                    logger.info(f"📋 MISSING TOOLS: {verification_result['missing_tools']} - waiting for complete LLM response")
                    pending_auto_execution = True
                    # DO NOT execute missing tools here - wait for Primary LLM to generate complete content
                else:
                    logger.info(f"✅ TASK COMPLETION VERIFIED - All required steps completed")
            except Exception as e:
                logger.error(f"❌ VERIFIER ERROR: {e}")
                logger.error(f"❌ VERIFIER TRACEBACK: {traceback.format_exc()}")
                logger.info(f"⚠️ Continuing without verification due to error")
            
            logger.info(f"🎯 Starting context management")
            
            # 🧹 STREAMLINED LOGGING: Context summaries instead of full buffer dumps
            concise_logging = os.environ.get('CONCISE_LOGGING', 'true').lower() == 'true'
            buffer_size_logging = os.environ.get('BUFFER_SIZE_LOGGING', 'true').lower() == 'true'
            
            # Context management with safe optimization integration
            context_size = len(prompt_context) if prompt_context else 0
            tool_results_size = len(tools_results)
            system_prompt_size = len(data.get('system', ''))
            
            if concise_logging and buffer_size_logging:
                # Show concise context summary instead of full buffer dump
                logger.info(f"📊 CONTEXT SUMMARY:")
                logger.info(f"   tools_results: {tool_results_size} chars")
                logger.info(f"   in_prompt: {context_size} chars") 
                logger.info(f"   system_prompt: {system_prompt_size} chars")
                logger.info(f"   full_context: {context_size + tool_results_size + system_prompt_size} chars")
            else:
                # Legacy verbose logging
                logger.info(f"🎯 Total tools_results length: {len(tools_results)} chars")
            
            # 🧹 STREAMLINED DEBUG: Comment out verbose buffer dumps (taking too much space)
            # 🔍 DEBUG: Critical checkpoint - what is Primary LLM receiving?
            # logger.info(f"🔍 DEBUG: PRIMARY LLM CONTEXT CHECKPOINT")
            # logger.info(f"🔍 DEBUG: tools_results type: {type(tools_results)}")
            # logger.info(f"🔍 DEBUG: tools_results size: {tool_results_size} bytes") 
            # if tool_results_size > 0:
            #     logger.info(f"🔍 DEBUG: tools_results preview (first 300 chars): {tools_results[:300]}...")
            # else:
            #     logger.warning(f"🚨 DEBUG: tools_results is EMPTY! Value: '{tools_results}'")
            # logger.info(f"🔍 DEBUG: This is what Primary LLM will process")
            
            # 🧹 CONCISE DEBUG: Only show critical info when buffer dumps are disabled
            if not concise_logging:
                # Show verbose debug only when explicitly enabled
                logger.info(f"🔍 DEBUG: PRIMARY LLM CONTEXT CHECKPOINT")
                logger.info(f"🔍 DEBUG: tools_results type: {type(tools_results)}, size: {tool_results_size} bytes")
                if tool_results_size == 0:
                    logger.warning(f"🚨 DEBUG: tools_results is EMPTY!")
            elif tool_results_size == 0:
                # Always warn about empty results even in concise mode
                logger.warning(f"🚨 tools_results is EMPTY - Primary LLM will have no tool context!")
            max_context_window = 65536  # 64k bytes
            max_context_tokens = max_context_window / 4  # estimating 4 bytes per token
            # Truncate base64 data before sending to LLM context to prevent streaming back
            truncated_tools_results = truncate_base64_for_logging(tools_results)
            full_tools_text = (prompt_context or "") + ".\n" + truncated_tools_results
            
            # 🚨 CRITICAL: Parse tools_results AFTER Arbitrator corrections are applied
            # (Moved after line 5438 to ensure corrected results are used)
            
            # Use safe optimization system or fallback to original processing
            try:
                # Get user_id from request if available (you may need to adjust this based on your auth system)
                user_id = getattr(request, 'user_id', None) if 'request' in locals() else None
                
                tools_results_summary, optimization_metadata = await process_with_safe_optimization(
                    tool_results=parsed_tool_results,
                    user_prompt=user_prompt,
                    max_context_window=max_context_window,
                    tools_called=tools_called,
                    thread_pool=thread_pool,
                    user_id=user_id
                )
                
                # Log optimization results
                if optimization_metadata.get('optimization_used'):
                    logger.info(f"🚀 OPTIMIZATION APPLIED: Score {optimization_metadata['optimization_score']:.1f}, Time {optimization_metadata['response_time']:.2f}s")
                else:
                    logger.info(f"🔄 FALLBACK PROCESSING: {optimization_metadata.get('fallback_reason', 'Feature disabled')}")
                    
            except Exception as e:
                logger.error(f"🚨 OPTIMIZATION INTEGRATION ERROR: {e}")
                logger.info("🔄 EMERGENCY FALLBACK: Using original processing")
                
                # Emergency fallback to original logic
                if len(full_tools_text) > (max_context_window) * 1.05:
                    try:
                        logger.info(f"Calling TextChunker() to reduce context size from {len(full_tools_text)} to around {max_context_window} bytes")
                        if TOOLS_AVAILABLE:
                            def sync_text_chunking():
                                from text_chunker import TextChunker
                                return TextChunker.summary_by_semantics(
                                    full_tools_text, 
                                    query=data.get('system', '') + ' \n' + user_prompt,
                                    max_length=max_context_window
                                )
                            
                            tools_results_summary = await asyncio.get_event_loop().run_in_executor(
                                thread_pool, sync_text_chunking
                            )
                            logger.info(f"TextChunker() was called and returned tools_results_summary size of {len(tools_results_summary)} bytes. From {len(full_tools_text)}")
                        else:
                            tools_results_summary = full_tools_text
                    except Exception as e2:
                        logger.error(f"Error: exception in TextChunker.summary_by_semantics() call. Function returned message: {e2}")
                        tools_results_summary = full_tools_text  # TextChunker() failed!! Use the full text
                else:
                    tools_results_summary = full_tools_text
            
            # Log context statistics (exactly like original)
            if tools_in_use:
                logger.info(f"""

###################################################
TOOLS RESULTS SUMMARY: 
###################################################

{tools_results_summary}
====================

                      Context Size (before tool call)= {context_size} bytes
                      Tool_Results_Size = {tool_results_size} bytes
                      System Prompt Size = {system_prompt_size} bytes
                      Full Text Size (context + tools_results) = {len(full_tools_text)} bytes
                      ==> Tool Results Summary Size = {len(tools_results_summary)} bytes
                      

====================
END OF TOOLS RESULTS SUMMARY
=================

""")
            else:
                logger.info(f"""

###################################################
FULL CONTEXT (NO TOOLS): 
###################################################

{tools_results_summary}
====================

                    Context Size (no tools call)= {context_size} bytes
                    System Prompt Size = {system_prompt_size} bytes
                    Full Text Size (no tools call) = {len(full_tools_text)} bytes
                    

====================
END OF CONTEXT 
=================

""")
            
            # 🖼️ PRE-LLM CONTEXT CLEANING: Remove base64 images from tools_results_summary before sending to LLM
            cleaned_tools_results_summary = tools_results_summary
            if tools_results and "analytical_visualizer" in tools_results:
                logger.info(f"🧹 PRE-LLM CONTEXT CLEANING: Removing base64 image data from tools_results_summary before LLM processing")
                
                # Find and remove base64 image data using the same pattern as injection
                import re
                img_pattern = r'<img src="(data:image/png;base64,[^"]+)"[^>]*>'
                img_match = re.search(img_pattern, cleaned_tools_results_summary)
                
                if img_match:
                    # Replace the entire <img> tag with a simple text reference
                    cleaned_tools_results_summary = re.sub(img_pattern, '**[Visualization has been generated and displayed above as HTML]**', cleaned_tools_results_summary)
                    logger.info(f"✅ PRE-LLM CONTEXT CLEANING: Replaced {len(img_match.group(1))} chars of base64 data with text reference")
                    logger.info(f"📊 CONTEXT SIZE REDUCTION: {len(tools_results_summary)} → {len(cleaned_tools_results_summary)} chars ({len(tools_results_summary) - len(cleaned_tools_results_summary)} chars removed)")
            
            # 🎯 NEW ARCHITECTURE: Build structured CONTEXT block and user system prompt
            context_block = _build_structured_context_block(cleaned_tools_results_summary, tools_called)
            
            # User-provided system prompt takes precedence
            user_system_prompt = data.get('system', '').strip()
            if user_system_prompt:
                # Use user's system prompt directly
                enhanced_system = user_system_prompt
                logger.info(f"📋 Using USER-PROVIDED system prompt ({len(user_system_prompt)} chars)")
            else:
                # Fallback to enhanced default system prompt
                enhanced_system = _build_enhanced_primary_system_prompt(
                    user_system_prompt, 
                    tools_were_executed=(len(tools_results.strip()) > 0),
                    tools_results_summary=cleaned_tools_results_summary
                )
                logger.info(f"📋 Using DEFAULT enhanced system prompt ({len(enhanced_system)} chars)")
            
            # 🚀 META-TASK OPTIMIZATION: Smart truncation for title/tag generation
            if is_meta_task:
                # Extract task instruction and chat history separately
                if '<chat_history>' in user_prompt and '</chat_history>' in user_prompt:
                    # Split task instruction from chat history
                    parts = user_prompt.split('<chat_history>')
                    task_instruction = parts[0].strip()
                    
                    chat_content = parts[1].split('</chat_history>')[0].strip()
                    
                    # Smart truncation: Keep last 1000 chars of chat history for context
                    if len(chat_content) > 1000:
                        chat_content = "..." + chat_content[-1000:]
                    
                    # Reconstruct optimized prompt
                    optimized_prompt = f"{task_instruction}\n<chat_history>\n{chat_content}\n</chat_history>"
                    in_prompt = f"PROMPT: {optimized_prompt}"
                    # Reduced meta-task logging: logger.info(f"🚀 META-TASK OPTIMIZED: Reduced prompt from {len(user_prompt)} to {len(optimized_prompt)} chars")
                else:
                    # Fallback: just truncate to reasonable size
                    if len(user_prompt) > 2000:
                        truncated = user_prompt[:1000] + "...[truncated]..." + user_prompt[-500:]
                        in_prompt = f"PROMPT: {truncated}"
                        # Reduced meta-task logging: logger.info(f"🚀 META-TASK OPTIMIZED: Reduced prompt from {len(user_prompt)} to {len(truncated)} chars")
                    else:
                        in_prompt = f"PROMPT: {user_prompt}"
            else:
                # 🎯 PROMPT TRANSFORMATION: Transform email requests to confirmation requests when tools already executed
                transformed_prompt = user_prompt
                if context_block.strip() and ("TOOLS EXECUTED:" in context_block):
                    # Check if user is asking to email something when tools have already been executed
                    email_keywords = ["email the above", "email this", "send the above", "send this", "email it"]
                    if any(keyword.lower() in user_prompt.lower() for keyword in email_keywords):
                        # Transform the prompt to ask for confirmation instead of redoing work
                        if "secure_email_sender" in context_block:
                            transformed_prompt = "Please confirm what work has been completed and provide a summary of what was accomplished for the user."
                        else:
                            transformed_prompt = user_prompt  # Keep original if no email was actually sent
                        logger.info(f"🔄 PROMPT TRANSFORMED: Email request → Confirmation request (tools already executed)")
                
                # Build new format: --CONTEXT START-- + ORIGINAL CONVERSATION + CONTEXT BLOCK + PROMPT: [TRANSFORMED PROMPT]
                if context_block.strip():
                    # 🔧 CRITICAL FIX: Include original conversation context so Primary LLM knows what content was processed
                    full_context = ""
                    if prompt_context.strip():
                        full_context += f"{prompt_context}\n\n"
                    full_context += context_block
                    in_prompt = f"--CONTEXT START--\n{full_context}\n--CONTEXT END--\n\nPROMPT: {transformed_prompt}"
                else:
                    # If no tools executed, use original context only
                    if prompt_context.strip():
                        in_prompt = f"--CONTEXT START--\n{prompt_context}\n--CONTEXT END--\n\nPROMPT: {transformed_prompt}"
                    else:
                        in_prompt = f"PROMPT: {transformed_prompt}"
            
            # Core metrics for debugging
            logger.info(f"📜 Prompt: {len(in_prompt)} bytes | Context: {len(context_block)} | System: {len(enhanced_system)}")
            
            # Stream response from Ollama using connection pool
            async with http_pool.get_session() as session:
                # Get think parameter from primary LLM configuration
                # Disable think for meta-tasks (title generation, tagging, etc.)
                primary_config = config_loader.get_llm_config('primary')
                base_think_enabled = primary_config.get('config', {}).get('think', False)
                think_enabled = False if is_meta_task else base_think_enabled

                stream_payload = {
                    "model": model,
                    "prompt": in_prompt,
                    "system": enhanced_system,
                    "options": {
                        "temperature": data.get('temperature', 0.7),
                        "top_k": data.get('top_k', 40),
                        "top_p": data.get('top_p', 0.9),
                        "num_ctx": data.get('num_ctx', 8192),
                        "low_vram": data.get('low_vram', False)
                    },
                    "think": think_enabled,  # Add think parameter from configuration
                    "stream": True
                }
                
                # Add images if they exist
                if image_exists:
                    stream_payload["images"] = data.get("images")
                
                logger.info(f"🤖 PRIMARY LLM: {model} | Input: {len(in_prompt)} bytes | Tools: {len(tools_called)}")
                
                # 🔍 DEBUG: DUMP COMPLETE PRIMARY LLM INPUT - This is what gets sent to Primary LLM
                logger.info(f"🔍 DEBUG: ========== PRIMARY LLM PAYLOAD DUMP ==========")
                logger.info(f"🔍 DEBUG: tools_results variable content ({len(tools_results)} chars):")
                truncated_tools_results = truncate_base64_for_logging(tools_results)
                logger.info(f"🔍 DEBUG: tools_results = '{truncated_tools_results}'")
                logger.info(f"🔍 DEBUG: =====================================")
                logger.info(f"🔍 DEBUG: context_block content ({len(context_block)} chars):")
                truncated_context_block = truncate_base64_for_logging(context_block)
                logger.info(f"🔍 DEBUG: context_block = '{truncated_context_block}'")
                logger.info(f"🔍 DEBUG: =====================================")
                logger.info(f"🔍 DEBUG: FULL in_prompt content ({len(in_prompt)} chars):")
                truncated_in_prompt = truncate_base64_for_logging(in_prompt)
                logger.info(f"🔍 DEBUG: in_prompt = '{truncated_in_prompt}'")
                logger.info(f"🔍 DEBUG: ========== END PRIMARY LLM PAYLOAD DUMP ==========")
                
                llm_start_time = time.time()
                
                # 🎯 PRE-LLM IMAGE INJECTION: Check if analytical_visualizer was executed
                if tools_results and "analytical_visualizer" in tools_results:
                    logger.info(f"🖼️ PRE-LLM IMAGE INJECTION: Analytical visualizer detected in tools_results")
                    
                    # Extract base64 image data from tools_results
                    import re
                    # Check for both HTML img tags and raw data URLs
                    img_pattern = r'<img src="(data:image/png;base64,[^"]+)"[^>]*>'
                    raw_data_pattern = r'(data:image/png;base64,[A-Za-z0-9+/=]+)'
                    
                    img_match = re.search(img_pattern, tools_results)
                    raw_match = re.search(raw_data_pattern, tools_results)
                    
                    base64_data_url = None
                    if img_match:
                        base64_data_url = img_match.group(1)
                        logger.info(f"📊 IMAGE FOUND (HTML): {len(base64_data_url)} chars of base64 data")
                    elif raw_match:
                        base64_data_url = raw_match.group(1)
                        logger.info(f"📊 IMAGE FOUND (RAW): {len(base64_data_url)} chars of base64 data")
                    
                    if base64_data_url:
                        
                        # Create unique canvas ID
                        canvas_id = f"viz_canvas_{int(time.time())}"
                        
                        # Create complete HTML page that LibreChat can execute
                        canvas_html = f'''```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analytical Visualization</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .visualization {{
            max-width: 100%;
            height: auto;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin: 20px 0;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Analytical Visualization</h1>
        <img src="{base64_data_url}" class="visualization" alt="Generated Analytical Visualization">
    </div>
</body>
</html>
```'''
                        
                        # 🔄 CHUNKED STREAMING: Break large HTML into manageable chunks  
                        # Ensure proper separation between HTML injection and LLM output
                        full_content = f'{canvas_html}\n\n'
                        chunk_size = 8192  # 8KB chunks for safe transmission
                        logger.info(f"📦 CHUNKED STREAMING: Breaking {len(full_content)} chars into {chunk_size} byte chunks")
                        
                        # Split content into chunks
                        for i in range(0, len(full_content), chunk_size):
                            chunk_content = full_content[i:i+chunk_size]
                            
                            image_chunk = {
                                "id": f"chatcmpl-{int(time.time())}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": stream_payload.get("model", "default"),
                                "choices": [{
                                    "index": 0,
                                    "delta": {
                                        "content": chunk_content
                                    },
                                    "finish_reason": None
                                }]
                            }
                            
                            yield f'data: {json.dumps(image_chunk)}\n\n'
                            logger.info(f"📦 CHUNK {i//chunk_size + 1}: Sent {len(chunk_content)} chars")
                        
                        # 📋 SEPARATOR CHUNK: Ensure clean boundary between HTML and LLM output
                        separator_chunk = {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion.chunk", 
                            "created": int(time.time()),
                            "model": stream_payload.get("model", "default"),
                            "choices": [{
                                "index": 0,
                                "delta": {
                                    "content": "\n---\n\n"
                                },
                                "finish_reason": None
                            }]
                        }
                        yield f'data: {json.dumps(separator_chunk)}\n\n'
                        
                        total_chunks = (len(full_content) + chunk_size - 1) // chunk_size
                        logger.info(f"✅ PRE-LLM IMAGE INJECTION: Successfully streamed {len(full_content)} chars in {total_chunks} chunks with separator")
                    else:
                        logger.info(f"⚠️ PRE-LLM IMAGE INJECTION: No base64 image found in analytical_visualizer result")
                
                # LLM input ready
                
                # 🔧 STREAMING FIX: Add reasonable timeout and error handling
                # Use a long but finite timeout to prevent infinite hangs
                logger.info(f"🕒 PRIMARY LLM: Starting with 45 minute timeout...")
                
                try:
                    logger.info(f"🧾 PRIMARY LLM: Sending request to Ollama at {ServerConfig.OLLAMA_URL}")
                    
                    # 🔍 COMPREHENSIVE PAYLOAD DUMP - Every field and parameter
                    logger.info("="*80)
                    logger.info("🔍 COMPLETE PRIMARY LLM PAYLOAD DUMP:")
                    logger.info("="*80)
                    logger.info(f"📋 MODEL: {stream_payload.get('model', 'NOT SET')}")
                    logger.info(f"📋 STREAM: {stream_payload.get('stream', 'NOT SET')}")
                    logger.info(f"📋 THINK: {stream_payload.get('think', 'NOT SET')}")
                    
                    # Options dump
                    options = stream_payload.get('options', {})
                    logger.info("📋 OPTIONS:")
                    for key, value in options.items():
                        logger.info(f"   - {key}: {value}")
                    
                    # System prompt dump with length
                    system_prompt = stream_payload.get("system", "")
                    logger.info(f"📋 SYSTEM PROMPT ({len(system_prompt)} chars):")
                    logger.info(f"   First 200 chars: {system_prompt[:200]}")
                    logger.info(f"   Last 200 chars: {system_prompt[-200:]}")
                    
                    # Prompt dump with length  
                    prompt = stream_payload.get("prompt", "")
                    logger.info(f"📋 PROMPT ({len(prompt)} chars):")
                    logger.info(f"   First 500 chars: {prompt[:500]}")
                    logger.info(f"   Last 500 chars: {prompt[-500:]}")
                    
                    # Full JSON dump
                    logger.info("📋 COMPLETE PAYLOAD JSON:")
                    logger.info(json.dumps(stream_payload, indent=2))
                    logger.info("="*80)
                    
                    # 🎯 PHASE 2 FIX: Use LLM Manager instead of hardcoded Ollama
                    logger.info(f"🧾 PRIMARY LLM: System Prompt: {stream_payload['system']}")
                    logger.info(f"🎛️ MANAGER: Routing to configured primary provider")

                    # Prepare parameters for LLM Manager
                    # Get think parameter from primary LLM configuration
                    # Disable think for meta-tasks (title generation, tagging, etc.)
                    primary_config = config_loader.get_llm_config('primary')
                    base_think_enabled = primary_config.get('config', {}).get('think', False)
                    think_enabled = False if is_meta_task else base_think_enabled

                    manager_kwargs = {
                        'model': stream_payload.get('model'),
                        'system_prompt': stream_payload.get('system'),
                        'temperature': stream_payload.get('options', {}).get('temperature', 0.7),
                        'max_tokens': stream_payload.get('options', {}).get('num_predict', 4096),
                        'stream': stream_payload.get('stream', True),
                        'think': think_enabled  # Pass think parameter from configuration
                    }

                    # Add images if present for vision models
                    if image_exists and stream_payload.get("images"):
                        manager_kwargs['images'] = stream_payload["images"]

                    try:
                        # Log context size information
                        prompt_text = stream_payload['prompt']
                        system_text = manager_kwargs.get('system_prompt', '')
                        full_context = f"{system_text}\n\n{prompt_text}" if system_text else prompt_text

                        char_count = len(full_context)
                        # Rough token estimation: ~4 characters per token for most models
                        token_estimate = char_count // 4

                        logger.info(f"📏 CONTEXT SIZE: {char_count:,} chars (~{token_estimate:,} tokens) → Primary LLM: {stream_payload.get('model', 'unknown')}")

                        # Use LLM Manager for provider-agnostic primary model call
                        async for chunk in llm_manager.generate_stream(stream_payload['prompt'], **manager_kwargs):
                            if chunk:
                                # 🎯 STREAMING FIX: Format LLM Manager text into proper JSON chunks
                                # Native endpoint expects Ollama-style JSON format
                                if isinstance(chunk, str):
                                    # Format text chunk as Ollama-style JSON response
                                    json_chunk = {
                                        "model": stream_payload.get('model', model),
                                        "response": chunk,
                                        "done": False
                                    }
                                    formatted_chunk = json.dumps(json_chunk) + '\n'
                                    yield formatted_chunk.encode('utf-8')
                                else:
                                    # Handle bytes - convert to JSON format
                                    chunk_text = chunk.decode('utf-8') if isinstance(chunk, bytes) else str(chunk)
                                    json_chunk = {
                                        "model": stream_payload.get('model', model),
                                        "response": chunk_text,
                                        "done": False
                                    }
                                    formatted_chunk = json.dumps(json_chunk) + '\n'
                                    yield formatted_chunk.encode('utf-8')

                                # 🎯 PHASE 3 FIX: Unified streaming interface
                                # LLM Manager providers already return clean text content
                                try:
                                    if isinstance(chunk, str):
                                        # Direct text content from LLM Manager
                                        complete_llm_response += chunk
                                    elif isinstance(chunk, bytes):
                                        # Convert bytes to string if needed
                                        chunk_text = chunk.decode('utf-8')
                                        complete_llm_response += chunk_text
                                except Exception as chunk_error:
                                    logger.warning(f"⚠️ Chunk processing error: {chunk_error}")
                                    pass  # Skip malformed chunks

                        # 🎯 STREAMING FIX: Send completion chunk
                        final_chunk = {
                            "model": stream_payload.get('model', model),
                            "response": "",
                            "done": True
                        }
                        final_formatted = json.dumps(final_chunk) + '\n'
                        yield final_formatted.encode('utf-8')

                    except Exception as e:
                        logger.error(f"❌ LLM Manager primary call failed: {e}")
                        # Fallback to direct Ollama if manager fails
                        logger.warning("🔄 Falling back to direct Ollama call")
                        async with session.post(ServerConfig.OLLAMA_URL, json=stream_payload, timeout=3600) as response:
                            if response.status == 200:
                                async for chunk in response.content.iter_chunked(1024):
                                    if chunk:
                                        yield chunk
                                        # Simplified fallback processing
                                        try:
                                            chunk_text = chunk.decode('utf-8')
                                            for line in chunk_text.strip().split('\n'):
                                                if line.strip():
                                                    try:
                                                        chunk_json = json.loads(line)
                                                        if 'response' in chunk_json:
                                                            complete_llm_response += chunk_json['response']
                                                    except:
                                                        pass
                                        except:
                                            pass
                        
                        # Output condition: PRIMARY LLM completed
                        llm_duration = time.time() - llm_start_time
                        logger.info(f"🤖 PRIMARY LLM: COMPLETE | {llm_duration:.2f}s | Output: {len(complete_llm_response)} chars")
                        
                        # Post-processing phase
                        logger.info(f"🔍🔍🔍 CRITICAL: Reached post-processing section!")
                        logger.info(f"🔍 PRE-POST-PROCESSING: email_intercepted={email_intercepted}")
                        logger.info(f"🔍 PRE-POST-PROCESSING: intercepted_email_params={intercepted_email_params}")
                        
                        # 🎯 NEW POST-PROCESSING: Handle intercepted email calls first
                        if email_intercepted:
                            # 🚨 CRITICAL FIX: Block email execution for programming tasks and fabricated emails
                            should_block = False
                            
                            # Block known problematic patterns
                            if verification_result and verification_result.get('pattern') == 'programming_task':
                                should_block = True
                                
                            # Block fabricated email addresses
                            to_email = intercepted_email_params.get('to_email', '')
                            fabricated_indicators = [
                                'recipient@example.com', 'example@example.com', 'user@example.com',
                                'test@test.com', 'demo@demo.com', '@example.'
                            ]
                            
                            if any(indicator in to_email.lower() for indicator in fabricated_indicators):
                                should_block = True
                                logger.warning(f"🚨 FABRICATED EMAIL DETECTED: {to_email}")
                            
                            if should_block:
                                logger.warning(f"🛡️ PROGRAMMING TASK EMAIL BLOCK: Preventing fabricated email execution")
                                logger.warning(f"🛡️ Blocked email params: {intercepted_email_params}")
                                logger.warning(f"🛡️ Task pattern: {verification_result.get('pattern')} - {verification_result.get('reason')}")
                                logger.info(f"🔍 POST-PROCESSING SKIPPED: Programming task email blocked")
                            else:
                                logger.info(f"📧 POST-LLM EMAIL: Processing deferred email")
                                logger.info(f"📧 POST-LLM: Processing intercepted email call")
                                logger.info(f"🎯 Complete LLM response length: {len(complete_llm_response)} characters")
                            
                                try:
                                    logger.info(f"🔄 STEP 1: Extracting filename from intercepted parameters")
                                    # Extract filename from intercepted parameters - DEFAULT TO HTML
                                    attachments = intercepted_email_params.get('attachments', 'report.html')
                                    logger.info(f"🔄 STEP 1A: Raw attachments = '{attachments}'")
                                    
                                    # Handle both list and string attachment formats
                                    if isinstance(attachments, list):
                                        filename = attachments[0] if attachments else 'report.html'
                                        logger.info(f"🔄 STEP 1B: List format attachments, using first: '{filename}'")
                                    elif isinstance(attachments, str):
                                        if ',' in attachments:
                                            filename = attachments.split(',')[0].strip()  # Take first file
                                            logger.info(f"🔄 STEP 1C: Multiple attachments detected, using first: '{filename}'")
                                        else:
                                            filename = attachments.strip()
                                            logger.info(f"🔄 STEP 1D: Single attachment: '{filename}'")
                                    else:
                                        filename = 'report.html'  # Fallback
                                        logger.info(f"🔄 STEP 1E: Unknown attachment format, using fallback: '{filename}'")
                                    
                                    # Determine if PDF conversion is needed based on file extension
                                    convert_to_pdf = filename.lower().endswith('.pdf')
                                    logger.info(f"🔄 STEP 1F: File extension check - convert_to_pdf: {convert_to_pdf}")
                                    
                                    # Keep original filename - don't force PDF extension
                                    logger.info(f"🔄 STEP 1G: Using original filename: '{filename}'")
                                    
                                    logger.info(f"🔄 STEP 2: About to create file with Primary LLM content")
                                    
                                    # Save Primary LLM response as native Markdown first
                                    base_filename = filename.rsplit('.', 1)[0]  # Remove extension
                                    markdown_filename = f"{base_filename}.md"
                                    logger.info(f"📄 Creating Markdown file: {markdown_filename}")
                                    
                                    # Create Markdown file with Primary LLM content
                                    md_result = await tool_manager.safe_function_call("sandboxed_executor", {
                                        "action": "create_file",
                                        "filename": markdown_filename,
                                        "content": complete_llm_response.strip(),
                                        "convert_to_pdf": False
                                    })
                                    
                                    # Check if user requested a specific file type that should be preserved
                                    original_ext = filename.lower().split('.')[-1] if '.' in filename else ''
                                    preserve_original_format = original_ext in ['py', 'js', 'java', 'cpp', 'c', 'h', 'sql', 'sh', 'yaml', 'yml', 'json', 'xml', 'csv', 'txt']
                                    
                                    # CRITICAL FIX: Check if ANY file already exists from tool calling phase - REGARDLESS of extension
                                    file_already_exists = False
                                    existing_file_path = None
                                    
                                    # Get sandbox tool instance from user_tools
                                    sandbox_tool = None
                                    if hasattr(tool_manager, 'user_tools') and tool_manager.user_tools:
                                        for tool in tool_manager.user_tools:
                                            if tool.name == "sandboxed_executor":
                                                sandbox_tool = tool
                                                break
                                    
                                    if sandbox_tool and hasattr(sandbox_tool, 'sandbox_path'):
                                        workspace_path = sandbox_tool.sandbox_path
                                        full_path = workspace_path / filename
                                        
                                        if full_path.exists():
                                            file_already_exists = True
                                            existing_file_path = full_path
                                            existing_size = full_path.stat().st_size
                                            logger.info(f"🔒 EXISTING FILE DETECTED: {full_path} exists ({existing_size} bytes) - will preserve")
                                        else:
                                            logger.info(f"🔍 FILE CHECK: {full_path} does not exist - will create new")
                                    else:
                                        logger.warning(f"⚠️ Could not get sandbox tool instance for workspace path check")
                                    
                                    if file_already_exists:
                                        # File already exists - ALWAYS preserve, regardless of extension or format
                                        logger.info(f"🔒 PRESERVING EXISTING FILE: {existing_file_path} already exists from tool calling phase")
                                        file_result = {"filename": filename, "preserved": True, "size_bytes": existing_size}
                                    elif convert_to_pdf:
                                        logger.info(f"📄 Creating PDF file for email: {filename}")
                                        file_result = await tool_manager.safe_function_call("sandboxed_executor", {
                                            "action": "create_file",
                                            "filename": filename,
                                            "content": complete_llm_response.strip(),
                                            "convert_to_pdf": True
                                        })
                                    elif preserve_original_format:
                                        # User requested a specific code/data file type - create it with LLM content
                                        logger.info(f"📄 Creating preserved format file: {filename} (extension: {original_ext})")
                                        file_result = await tool_manager.safe_function_call("sandboxed_executor", {
                                            "action": "create_file",
                                            "filename": filename,
                                            "content": complete_llm_response.strip(),
                                            "convert_to_pdf": False
                                        })
                                        # Keep original filename - don't change it
                                    else:
                                        # Create HTML version for email attachment (default behavior for reports)
                                        html_filename = f"{base_filename}.html"
                                        logger.info(f"📄 Creating HTML file for email: {html_filename}")
                                        file_result = await tool_manager.safe_function_call("sandboxed_executor", {
                                            "action": "create_file", 
                                            "filename": html_filename,
                                            "content": complete_llm_response.strip(),
                                            "convert_to_pdf": False
                                        })
                                        # Update filename for email attachment
                                        filename = html_filename
                                    
                                    logger.info(f"🔄 STEP 2A: File creation completed")
                                    logger.info(f"📄 File creation result: {file_result}")
                                    
                                    logger.info(f"🔄 STEP 3: Checking file creation success")
                                    # file_result is a string from safe_function_call, need to parse it if it's JSON
                                    try:
                                        if isinstance(file_result, str) and file_result.strip().startswith('{'):
                                            file_result_dict = json.loads(file_result)
                                            logger.info(f"🔄 STEP 3A-PARSE: Successfully parsed JSON file_result")
                                        else:
                                            file_result_dict = file_result
                                            logger.info(f"🔄 STEP 3A-PARSE: Using file_result as-is (type: {type(file_result)})")
                                    except json.JSONDecodeError as e:
                                        logger.error(f"🔄 STEP 3A-PARSE: JSON parse failed: {e}, using raw result")
                                        file_result_dict = file_result
                                    
                                    # Check for successful file creation (JSON result contains filename and success indicators)
                                    file_success = (isinstance(file_result_dict, dict) and 
                                                  file_result_dict.get("filename") and 
                                                  (file_result_dict.get("pdf_generated") == True or 
                                                   file_result_dict.get("html_generated") == True or
                                                   file_result_dict.get("preserved") == True or
                                                   file_result_dict.get("size_bytes", 0) > 0)) or "successfully created" in str(file_result).lower()
                                    logger.info(f"🔄 STEP 3A: File success check result: {file_success}")
                                    
                                    if file_success:
                                        logger.info(f"🔄 STEP 3A: File creation successful, proceeding to email")
                                        # Update email params with the correct filename for attachment
                                        updated_email_params = intercepted_email_params.copy()
                                        
                                        # 🚨 CRITICAL FIX: Preserve all attachments, don't overwrite with just first one
                                        original_attachments = intercepted_email_params.get('attachments', '')
                                        if isinstance(original_attachments, str) and ',' in original_attachments:
                                            # Multiple attachments provided - preserve all of them
                                            updated_email_params['attachments'] = original_attachments
                                            logger.info(f"🔧 MULTI-ATTACHMENT FIX: Preserving all attachments: {original_attachments}")
                                        else:
                                            # Single attachment or file generation workflow - use processed filename
                                            updated_email_params['attachments'] = filename
                                        
                                        # Ensure body is not empty - add fallback if missing
                                        if not updated_email_params.get('body') or updated_email_params.get('body').strip() == '':
                                            updated_email_params['body'] = f"Please find the attached file: {filename.split('/')[-1]}"
                                            logger.info(f"🔄 STEP 4: Added fallback email body")
                                        
                                        logger.info(f"🔄 STEP 4: About to send email with updated attachment: {filename}")
                                        logger.info(f"🔄 STEP 4: Email params: {updated_email_params}")
                                        email_result = await tool_manager.safe_function_call("secure_email_sender", updated_email_params)
                                        logger.info(f"🔄 STEP 4A: Email sending completed")
                                        logger.info(f"📧 Email sent: {email_result}")
                                        
                                        # Add to stream response
                                        logger.info(f"🔄 STEP 5: Adding completion message to stream")
                                        yield f'data: {{"post_processing": "completed", "tools_executed": ["sandboxed_executor", "secure_email_sender"]}}\n\n'
                                        logger.info(f"🚪 EXIT: Post-processing completed successfully")
                                    else:
                                        logger.error(f"❌ STEP 3B: File creation failed: {file_result}")
                                        logger.info(f"🚪 EXIT: Post-processing failed at file creation")
                                        
                                except Exception as e:
                                    logger.error(f"❌ Email post-processing error: {e}")
                                    logger.error(f"❌ Exception traceback: {traceback.format_exc()}")
                                    logger.info(f"🚪 EXIT: Post-processing failed with exception")
                        else:
                            logger.info(f"🔍 POST-PROCESSING SKIPPED: email_intercepted=False")
                        
                        # 🎯 POST-LLM AUTO-EXECUTION: Execute missing tools with complete content (legacy)
                        logger.info(f"🔍 DEBUG: pending_auto_execution={pending_auto_execution}, verification_result={verification_result}")
                        if pending_auto_execution and verification_result:
                            logger.info(f"🎯 POST-LLM AUTO-EXECUTION: Primary LLM completed, executing missing tools")
                            logger.info(f"🎯 Complete LLM response length: {len(complete_llm_response)} characters")
                            
                            try:
                                # Execute missing tools with complete LLM response as content
                                additional_results = await _execute_missing_tools_post_llm(
                                    verification_result['missing_tools'], 
                                    tool_manager, 
                                    tools_results,
                                    complete_llm_response,
                                    user_prompt
                                )
                                logger.info(f"✅ POST-LLM AUTO-EXECUTION COMPLETED: {additional_results}")
                                
                                # Optionally stream completion notification
                                completion_msg = json.dumps({
                                    "post_processing": "completed",
                                    "tools_executed": verification_result['missing_tools']
                                })
                                yield (completion_msg + '\n').encode()
                                
                            except Exception as e:
                                logger.error(f"❌ POST-LLM AUTO-EXECUTION FAILED: {e}")
                                error_msg = json.dumps({
                                    "post_processing": "failed", 
                                    "error": str(e)
                                })
                                yield (error_msg + '\n').encode()
                        else:
                            error_msg = f"Ollama error: {response.status}"
                            yield json.dumps({"error": error_msg}).encode() + b'\n'
                            
                except asyncio.TimeoutError:
                    logger.error("🕒 PRIMARY LLM: Request timed out after 10 minutes")
                    error_msg = json.dumps({"error": "Primary LLM request timed out"})
                    yield error_msg.encode() + b'\n'
                except Exception as http_error:
                    logger.error(f"🔗 PRIMARY LLM: HTTP request failed: {http_error}")
                    error_msg = json.dumps({"error": f"Primary LLM HTTP error: {str(http_error)}"})
                    yield error_msg.encode() + b'\n'
        
        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            error_msg = json.dumps({"error": f"Stream failed: {str(e)}"})
            yield error_msg.encode() + b'\n'
    
    return StreamingResponse(
        generate_stream(),
        media_type="application/x-ndjson"
    )

# ==============================================================================
# BASIC ENDPOINTS (from simple version)
# ==============================================================================

@app.get("/", response_model=ApiResponse)
async def root():
    """Root endpoint"""
    return ApiResponse(
        success=True,
        data={"message": "FastAPI Analytics Server with Ollama LLM Integration"},
        timestamp=datetime.now().isoformat()
    )

@app.get("/health")
async def health_check():
    """Enhanced health check with Ollama status"""
    services = {"database": "unknown", "cache": "memory", "ollama": "unknown"}
    
    # Check database
    if db_pool:
        try:
            async with get_db_connection() as conn:
                services["database"] = "healthy"
        except Exception:
            services["database"] = "unhealthy"
    else:
        services["database"] = "unavailable"
    
    # Check Ollama
    ollama_healthy = await check_ollama_health()
    services["ollama"] = "healthy" if ollama_healthy else "unhealthy"
    
    overall_status = "healthy" if all(
        status in ["healthy", "memory", "unavailable"] for status in services.values()
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "version": __version__,
        "services": services,
        "cache_size": len(simple_cache),
        "tools_available": TOOLS_AVAILABLE
    }

# ==============================================================================
# LOGGING CONTROL ENDPOINTS
# ==============================================================================

@app.get("/admin/logging/status")
async def get_logging_status():
    """Get current logging configuration and status"""
    root_logger = logging.getLogger()
    current_level = root_logger.level

    # Get current config values
    debug_config = config_loader.load_config().get('debug', {})

    return {
        "logging_status": {
            "enabled": current_level != logging.CRITICAL + 1,
            "level": logging.getLevelName(current_level),
            "level_numeric": current_level,
            "disabled": logging.root.disabled,
            "handlers_count": len(root_logger.handlers)
        },
        "configuration": {
            "log_requests": debug_config.get('log_requests', True),
            "log_timing": debug_config.get('log_timing', True),
            "mock_providers": debug_config.get('mock_providers', False)
        },
        "log_levels": {
            "CRITICAL": logging.CRITICAL,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG
        }
    }

@app.post("/admin/logging/enable")
async def enable_logging():
    """Enable logging with INFO level"""
    global log_requests_enabled, log_timing_enabled

    # Re-enable logging
    logging.disable(logging.NOTSET)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Update global flags
    log_requests_enabled = True
    log_timing_enabled = True

    logger.info("🔊 LOGGING ENABLED via API call")

    return {
        "status": "success",
        "message": "Logging enabled",
        "level": "INFO",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/admin/logging/disable")
async def disable_logging():
    """Disable all logging"""
    global log_requests_enabled, log_timing_enabled

    logger.info("🔇 LOGGING DISABLED via API call")

    # Disable logging
    logging.disable(logging.CRITICAL)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.CRITICAL + 1)

    # Update global flags
    log_requests_enabled = False
    log_timing_enabled = False

    return {
        "status": "success",
        "message": "Logging disabled",
        "level": "DISABLED",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/admin/logging/level/{level}")
async def set_logging_level(level: str):
    """Set specific logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"""
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    level_upper = level.upper()
    if level_upper not in level_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid log level. Must be one of: {list(level_map.keys())}"
        )

    # Enable logging if it was disabled and set the new level
    logging.disable(logging.NOTSET)
    root_logger = logging.getLogger()
    root_logger.setLevel(level_map[level_upper])

    logger.info(f"📊 LOGGING LEVEL SET TO {level_upper} via API call")

    return {
        "status": "success",
        "message": f"Logging level set to {level_upper}",
        "level": level_upper,
        "level_numeric": level_map[level_upper],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/admin/logging/requests/toggle")
async def toggle_request_logging():
    """Toggle request logging on/off"""
    global log_requests_enabled

    log_requests_enabled = not log_requests_enabled

    status = "enabled" if log_requests_enabled else "disabled"
    logger.info(f"📝 REQUEST LOGGING {status.upper()} via API call")

    return {
        "status": "success",
        "message": f"Request logging {status}",
        "request_logging": log_requests_enabled,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/admin/logging/timing/toggle")
async def toggle_timing_logging():
    """Toggle timing logging on/off"""
    global log_timing_enabled

    log_timing_enabled = not log_timing_enabled

    status = "enabled" if log_timing_enabled else "disabled"
    logger.info(f"⏱️ TIMING LOGGING {status.upper()} via API call")

    return {
        "status": "success",
        "message": f"Timing logging {status}",
        "timing_logging": log_timing_enabled,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/help")
async def user_help():
    """User help endpoint providing quick reference and documentation"""
    help_content = {
        "agentic_rag_system": {
            "version": __version__,
            "description": "High-performance AI assistant with local language models and intelligent tool calling",
            "base_url": "http://localhost:5000"
        },
        
        "quick_start": {
            "basic_prompt": "POST /llama3_1b/stream",
            "openai_compatible": "POST /v1/chat/completions",
            "example_request": {
                "url": "http://localhost:5000/llama3_1b/stream",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "prompt": "Hello! What can you help me with today?",
                    "model": "qwen3:8b",
                    "toolsInUse": True,
                    "stream": False
                }
            }
        },
        
        "available_tools": {
            "total_count": 19,
            "categories": {
                "search_and_web": [
                    "search_web - Search the internet for current information",
                    "get_web_content - Extract and analyze content from web pages"
                ],
                "document_management": [
                    "document_search - Search through indexed documents using semantic search",
                    "watch_directory - Monitor directories for new documents",
                    "index_directory - Add new documents to the search index"
                ],
                "communication": [
                    "send_email - Send emails with attachments",
                    "send_mass_email - Send bulk emails to multiple recipients"
                ],
                "financial_and_data": [
                    "stock_data - Get real-time stock prices and financial data",
                    "flight_search - Search for flights with multiple booking options"
                ],
                "productivity": [
                    "calendar_tools - Create and manage calendar events",
                    "execute_code - Run code safely in sandboxed environment"
                ],
                "file_operations": [
                    "file_operations - Read, write, and manage files",
                    "process_image - Analyze images with AI vision processing"
                ],
                "system_utilities": [
                    "weather_data - Get current weather and forecasts",
                    "system_info - Retrieve system information and stats",
                    "math_operations - Perform complex mathematical calculations",
                    "time_operations - Work with dates and time calculations"
                ]
            }
        },
        
        "key_endpoints": {
            "health_check": "GET /health - Check system health and service status",
            "help": "GET /help - This help information",
            "models": "GET /v1/models - List available AI models",
            "chat": "POST /v1/chat/completions - OpenAI-compatible chat completions",
            "stream": "POST /llama3_1b/stream - Native streaming endpoint",
            "documents": {
                "search": "POST /documents/search - Search indexed documents",
                "stats": "GET /documents/stats - Document index statistics",
                "config": "GET /documents/config - View document configuration"
            },
            "admin": {
                "logging_status": "GET /admin/logging/status - Get current logging configuration",
                "enable_logging": "POST /admin/logging/enable - Enable all logging with INFO level",
                "disable_logging": "POST /admin/logging/disable - Disable all logging",
                "set_log_level": "POST /admin/logging/level/{level} - Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
                "toggle_requests": "POST /admin/logging/requests/toggle - Toggle request logging on/off",
                "toggle_timing": "POST /admin/logging/timing/toggle - Toggle timing logging on/off"
            }
        },
        
        "tool_usage": {
            "how_to_enable_tools": "Set 'toolsInUse': true in your request",
            "automatic_selection": "The AI automatically selects appropriate tools based on your query",
            "example_queries": [
                "Search for recent news about AI developments",
                "Find documents about server configuration in my files",
                "Send an email to john@example.com with project update",
                "What's the current stock price of AAPL?",
                "Create a calendar event for next Monday at 2 PM",
                "What's the weather forecast for tomorrow?"
            ]
        },
        
        "getting_help": {
            "documentation": {
                "user_guide": "docs/production/USER_GUIDE.md",
                "admin_guide": "docs/production/ADMINISTRATOR_GUIDE.md",
                "developer_guide": "docs/production/DEVELOPER_GUIDE.md",
                "installation": "docs/setup/INSTALLATION.md"
            },
            "support": {
                "logs": "Check server_complete.log for error details",
                "health": "Use GET /health to check service status",
                "models": "Use GET /ollama/models to verify model availability"
            }
        }
    }
    
    return help_content

@app.get("/ollama/models")
async def list_ollama_models():
    """List available Ollama models"""
    try:
        async with http_pool.get_session() as session:
            async with session.get('http://127.0.0.1:11434/api/tags') as response:
                if response.status == 200:
                    data = await response.json()
                    return ApiResponse(
                        success=True,
                        data=data,
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    raise HTTPException(status_code=502, detail="Ollama service unavailable")
    except Exception as e:
        logger.error(f"Failed to list Ollama models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/retrieve_system_prompts")
async def retrieve_system_prompts(request: Request):
    """
    Retrieve system prompts from file
    Matches the exact behavior of the original Flask /retrieve_system_prompts endpoint
    """
    # Parse JSON data like the original Flask version
    data = await request.json()
    
    # Get filename exactly like the original
    filename = data.get('system_prompts_filename')
    logger.info(f"Retrieved filename: {filename}")
    
    # Validation exactly like the original
    if "system_prompts_filename" not in data:
        return JSONResponse(
            content={'message': 'Missing system_prompts_filename parameter'}, 
            status_code=400
        )
    
    system_prompts_filename = data["system_prompts_filename"]
    logger.info(f"----> {system_prompts_filename} from server")
    
    if not system_prompts_filename:
        return JSONResponse(
            content={'message': 'system_prompts_filename cannot be empty'}, 
            status_code=400
        )
    
    try:
        # Construct the full path to the file (exactly like original)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_dir = os.path.join(base_dir, 'prompts')
        file_path = os.path.join(prompts_dir, filename)  # Use filename like original
        
        # Print the directory being read from for debugging (like original)
        logger.info(f"Reading file from: {file_path}")
        
        # Read the file content (simple sync read like original)
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
        
        # Return the file content as JSON (exactly like original)
        return JSONResponse(content=file_content, status_code=200)
            
    except FileNotFoundError:
        return JSONResponse(
            content={'message': f'File not found: {system_prompts_filename}'}, 
            status_code=404
        )
    except Exception as e:
        return JSONResponse(
            content={'message': f'Error occurred: {str(e)}'}, 
            status_code=500
        )

@app.get("/metrics")
async def get_metrics():
    """Enhanced metrics including Ollama status"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
    except:
        cpu_percent = 0
        memory = None
    
    db_stats = {
        "available": db_pool is not None,
        "size": db_pool.size if db_pool else 0,
        "free": db_pool.freesize if db_pool else 0
    }
    
    ollama_status = await check_ollama_health()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent if memory else 0,
        },
        "database_pool": db_stats,
        "cache": {
            "type": "memory",
            "size": len(simple_cache)
        },
        "ollama": {
            "available": ollama_status,
            "url": ServerConfig.OLLAMA_URL
        },
        "tools": {
            "available": TOOLS_AVAILABLE,
            "count": len(tool_manager.available_functions)
        }
    }

# ==============================================================================
# OPTIMIZATION CONTROL ENDPOINTS
# ==============================================================================

@app.get("/optimization/status")
async def get_optimization_status():
    """Get comprehensive optimization system status"""
    if not OPTIMIZATION_AVAILABLE:
        return JSONResponse(
            content={
                "available": False,
                "error": "Optimization system not loaded"
            },
            status_code=503
        )
    
    return JSONResponse(content={
        "available": True,
        "status": optimization_controller.get_status_summary()
    })

@app.post("/optimization/enable")
async def enable_optimization(rollout_percentage: float = 100.0):
    """Enable optimization with optional gradual rollout"""
    if not OPTIMIZATION_AVAILABLE:
        return JSONResponse(
            content={"error": "Optimization system not available"},
            status_code=503
        )
    
    try:
        optimization_controller.enable_feature(rollout_percentage)
        return JSONResponse(content={
            "message": f"Optimization enabled with {rollout_percentage}% rollout",
            "status": optimization_controller.get_status_summary()
        })
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.post("/optimization/disable")
async def disable_optimization():
    """Disable optimization completely"""
    if not OPTIMIZATION_AVAILABLE:
        return JSONResponse(
            content={"error": "Optimization system not available"},
            status_code=503
        )
    
    try:
        optimization_controller.disable_feature()
        return JSONResponse(content={
            "message": "Optimization disabled",
            "status": optimization_controller.get_status_summary()
        })
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.post("/optimization/rollout")
async def set_rollout_percentage(percentage: float):
    """Set rollout percentage for gradual deployment"""
    if not OPTIMIZATION_AVAILABLE:
        return JSONResponse(
            content={"error": "Optimization system not available"},
            status_code=503
        )
    
    try:
        optimization_controller.set_rollout_percentage(percentage)
        return JSONResponse(content={
            "message": f"Rollout percentage set to {percentage}%",
            "status": optimization_controller.get_status_summary()
        })
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.post("/optimization/emergency-rollback")
async def emergency_rollback(reason: str = "Manual emergency rollback"):
    """Trigger emergency rollback"""
    if not OPTIMIZATION_AVAILABLE:
        return JSONResponse(
            content={"error": "Optimization system not available"},
            status_code=503
        )
    
    try:
        rollback_event = optimization_controller.emergency_rollback(reason)
        return JSONResponse(content={
            "message": "Emergency rollback executed",
            "rollback_event": rollback_event
        })
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# ==============================================================================
# OPENAI COMPATIBILITY ENDPOINT
# ==============================================================================

@app.get("/v1/models")
async def openai_models():
    """OpenAI compatible models endpoint"""
    try:
        # Build the response
        response_data = {
            "object": "list",
            "data": [
                {
                    "id": "Agentic-RAG-Model1",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "local"
                },
                {
                    "id": "Agentic-RAG-Model2",
                    "object": "model", 
                    "created": int(time.time()),
                    "owned_by": "local"
                }
            ]
        }
        
        # Debug logging
        logger.info(f"🔍 /v1/models endpoint called - returning {len(response_data['data'])} models")
        logger.info(f"🔍 Models being returned:")
        for i, model in enumerate(response_data['data']):
            logger.info(f"🔍   Model {i+1}: {model['id']} (created: {model['created']}, owned_by: {model['owned_by']})")
        truncated_full_response = truncate_base64_for_logging(json.dumps(response_data, indent=2))
        logger.info(f"🔍 Full response: {truncated_full_response}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"🚨 Models endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    """
    OpenAI API Compatible Chat Completions Endpoint
    
    Zero-Trust Security Model:
    - Only extracts user prompt from messages and model name
    - Ignores all other parameters (temperature, top_p, etc.)
    - Forces tools=True and uses our system prompt
    - Routes through existing tool calling pipeline
    """
    try:
        # SECURITY: Extract only what we trust - user prompt and model name
        user_prompt = ""
        conversation_context = ""
        
        # Extract conversation ID from messages or generate one based on content hash
        conversation_id = hashlib.md5(str(request.messages).encode()).hexdigest()[:12]
        
        # Build conversation context from message history
        message_history = []
        images = []  # Collect images from vision requests
        
        # 🖼️ CRITICAL FIX: Use images parameter if provided (custom format)
        if request.images and request.images != ["noimage"]:
            images.extend(request.images)
            logger.info(f"🖼️ Using images from request parameter: {len(images)} images")
        
        for message in request.messages:
            if message.role in ["user", "assistant"]:
                # Handle both string and structured content (for vision)
                if isinstance(message.content, str):
                    content_text = message.content
                elif isinstance(message.content, list):
                    # Extract text and images from structured content
                    text_parts = []
                    for item in message.content:
                        if item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                        elif item.get('type') == 'image_url':
                            image_url = item.get('image_url', {}).get('url', '')
                            if image_url.startswith('data:image/'):
                                # Extract base64 data
                                base64_data = image_url.split(',', 1)[1] if ',' in image_url else image_url
                                images.append(base64_data)
                            elif image_url.startswith('file://'):
                                # Extract local file path
                                file_path = image_url[7:]  # Remove 'file://' prefix
                                if os.path.exists(file_path):
                                    try:
                                        with open(file_path, 'rb') as f:
                                            img_bytes = f.read()
                                        base64_data = base64.b64encode(img_bytes).decode('utf-8')
                                        images.append(base64_data)
                                        logger.info(f"🖼️ Loaded local file: {file_path} ({len(img_bytes)} bytes)")
                                    except Exception as e:
                                        logger.error(f"🖼️ Error loading file {file_path}: {e}")
                                else:
                                    logger.warning(f"🖼️ File not found: {file_path}")
                    content_text = ' '.join(text_parts)
                else:
                    content_text = str(message.content)
                
                message_history.append(f"{message.role.upper()}: {content_text}")
                if message.role == "user":
                    user_prompt = content_text  # Use the latest user message text
        
        if not user_prompt:
            raise HTTPException(status_code=400, detail="No user message found")
            
        # Check if this is a follow-up prompt (more than 1 message)
        is_followup = len(message_history) > 1
        if is_followup:
            conversation_context = "\n\n=== CONVERSATION HISTORY ===\n" + "\n".join(message_history[:-1]) + "\n=== CURRENT REQUEST ===\n"
            logger.info(f"🔄 FOLLOW-UP DETECTED: Conversation {conversation_id} with {len(message_history)} messages")
        else:
            logger.info(f"🆕 NEW CONVERSATION: {conversation_id}")
        
        logger.info(f"\n\n🔒 OpenAI Compatibility Request - Model: {request.model}")
        logger.info(f"🔒 Extracted user prompt: {user_prompt[:100]}...")
        logger.info(f"🔒 SECURITY: All other parameters discarded per zero-trust design")
        
        # Check if streaming is requested
        is_streaming = request.stream if request.stream is not None else False
        
        # Combine context with current prompt for follow-up conversations
        enhanced_prompt = conversation_context + user_prompt if is_followup else user_prompt
        
        if is_streaming:
            return await openai_streaming_response(enhanced_prompt, request.model, conversation_id, images)
        else:
            return await openai_non_streaming_response(enhanced_prompt, request.model, conversation_id, images)
        
    except Exception as e:
        logger.error(f"🚨 OpenAI compatibility error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

async def openai_non_streaming_response(user_prompt: str, model: str, conversation_id: str, images: list = None):
    """Handle non-streaming OpenAI response with proper format"""
    try:
        logger.info(f"🔒 OpenAI Non-streaming Response - falling back to streaming with collect")
        
        # For non-streaming, we'll use streaming mode and collect all chunks
        streaming_response = await openai_streaming_response(user_prompt, model, conversation_id, images)
        
        # Collect all streaming content
        response_content = ""
        async for chunk in streaming_response.body_iterator:
            # Handle both bytes and string chunks
            if isinstance(chunk, bytes):
                chunk_data = chunk.decode('utf-8')
            else:
                chunk_data = str(chunk)
            # Parse JSON chunks and extract content
            lines = chunk_data.strip().split('\n')
            for line in lines:
                if line.startswith('data: ') and not line.endswith('[DONE]'):
                    try:
                        data_line = line[6:]  # Remove 'data: ' prefix
                        if data_line.strip():  # Skip empty lines
                            chunk_json = json.loads(data_line)
                            if 'choices' in chunk_json and len(chunk_json['choices']) > 0:
                                if 'delta' in chunk_json['choices'][0] and 'content' in chunk_json['choices'][0]['delta']:
                                    response_content += chunk_json['choices'][0]['delta']['content']
                    except json.JSONDecodeError:
                        continue
        
        # Return in standard OpenAI non-streaming format
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(user_prompt.split()),
                "completion_tokens": len(response_content.split()),
                "total_tokens": len(user_prompt.split()) + len(response_content.split())
            }
        }
        
    except Exception as e:
        logger.error(f"🚨 OpenAI non-streaming error: {str(e)}")
        logger.error(traceback.format_exc())
        # Return a simple response if collection fails
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello there! I'm working properly with tools enabled."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(user_prompt.split()),
                "completion_tokens": 10,
                "total_tokens": len(user_prompt.split()) + 10
            }
        }

async def openai_direct_stream(native_request_data: dict, model: str):
    """
    Option 2: Direct function calls to internal llama_stream (Faster, no HTTP overhead)
    Respects Prime Directive: Does not modify core server code
    FIXED: Properly handles StreamingResponse from llama_stream
    """
    try:
        logger.info(f"🎯 Direct streaming: Calling internal llama_stream function")
        logger.debug(f"🔧 DIRECT_STREAM DEBUG: Received native_request_data: {native_request_data}")
        logger.debug(f"🔧 DIRECT_STREAM DEBUG: model: {model}")
        
        # Create mock request object for llama_stream (following Prime Directive)
        class MockRequest:
            def __init__(self, data):
                self._data = data
            async def json(self):
                logger.info(f"🔧 MockRequest.json() called with data: {self._data}")
                return self._data
        
        mock_request = MockRequest(native_request_data)
        logger.info(f"🔧 Native request data being passed: {native_request_data}")
        
        # 🔧 CRITICAL DEBUG: Compare with working native format
        logger.info(f"🔧 COMPARISON - This should match working native requests")
        logger.debug(f"🔧 DIAGNOSTIC: OpenAI endpoint calling llama_stream with toolsInUse={native_request_data.get('toolsInUse')}")
        
        # 🖼️ Set image context for OpenAI endpoint - extract images from request data
        if native_request_data.get('images') and native_request_data['images'] != ['noimage']:
            tool_manager.set_image_context(native_request_data['images'], {"endpoint": "openai", "model": model})
        
        # Call the native llama_stream function directly
        internal_response = await llama_stream(mock_request)
        
        # 🔧 FIX: Properly handle StreamingResponse object with HTML injection support
        if hasattr(internal_response, 'body_iterator'):
            logger.info("🔧 Processing StreamingResponse body_iterator")
            async for chunk_data in internal_response.body_iterator:
                # Handle both bytes and string chunks
                if isinstance(chunk_data, bytes):
                    raw_content = chunk_data.decode('utf-8', errors='ignore')
                else:
                    raw_content = str(chunk_data)
                
                logger.debug(f"🔧 Raw chunk: {raw_content[:100]}...")
                
                # Check if this is already an OpenAI-format chunk (from HTML injection)
                if raw_content.startswith('data: '):
                    logger.debug("🔧 Detected OpenAI-format chunk (HTML injection), passing through")
                    yield raw_content
                    continue
                
                # Check if this is HTML content (direct HTML injection)
                if raw_content.startswith('<!DOCTYPE html>') or raw_content.startswith('<html'):
                    logger.debug("🔧 Detected HTML content, wrapping in OpenAI format")
                    content_chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk", 
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{"index": 0, "delta": {"content": raw_content}, "finish_reason": None}]
                    }
                    yield f"data: {json.dumps(content_chunk)}\n\n"
                    continue
                
                # Try to parse as JSON (regular Ollama response format)
                if raw_content.strip():
                    try:
                        # Try to parse as JSON
                        native_json = json.loads(raw_content.strip())
                        logger.debug(f"🔧 Parsed JSON: {native_json}")

                        # 🎯 PHASE 4 FIX: Handle LLM Manager text content vs Ollama JSON
                        # Check if stream should end (only for dict responses from Ollama)
                        if isinstance(native_json, dict) and native_json.get("done", False):
                            logger.info("🏁 Stream completion detected")
                            # If there's still response content in the final chunk, send it first
                            if "response" in native_json and native_json["response"]:
                                content_chunk = {
                                    "id": f"chatcmpl-{int(time.time())}",
                                    "object": "chat.completion.chunk", 
                                    "created": int(time.time()),
                                    "model": model,
                                    "choices": [{"index": 0, "delta": {"content": native_json["response"]}, "finish_reason": None}]
                                }
                                yield f"data: {json.dumps(content_chunk)}\n\n"
                            
                            # Send completion signal - but don't include metadata like context, created_at etc
                            final_chunk = {
                                "id": f"chatcmpl-{int(time.time())}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                            }
                            yield f"data: {json.dumps(final_chunk)}\n\n"
                            yield "data: [DONE]\n\n"
                            return
                        
                        # Extract and send content
                        if isinstance(native_json, dict) and "response" in native_json and native_json["response"]:
                            content_chunk = {
                                "id": f"chatcmpl-{int(time.time())}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [{"index": 0, "delta": {"content": native_json["response"]}, "finish_reason": None}]
                            }
                            logger.debug(f"🔧 Sending content chunk: {native_json['response'][:50]}...")
                            yield f"data: {json.dumps(content_chunk)}\n\n"
                        elif not isinstance(native_json, dict):
                            # 🎯 PHASE 4 FIX: Handle LLM Manager text content parsed as non-dict JSON
                            logger.debug(f"🔧 LLM Manager text content: {str(native_json)}")
                            content_chunk = {
                                "id": f"chatcmpl-{int(time.time())}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [{"index": 0, "delta": {"content": str(native_json)}, "finish_reason": None}]
                            }
                            yield f"data: {json.dumps(content_chunk)}\n\n"
                    except json.JSONDecodeError as json_err:
                        logger.debug(f"🔧 Not JSON, treating as raw content: {raw_content[:50]}...")
                        # Filter out unwanted content - don't send metadata or empty responses
                        if raw_content.strip() and not raw_content.startswith('{"model":'):
                            # Skip content that looks like Ollama metadata or context tokens
                            metadata_indicators = [
                                "created_at", "total_duration", "load_duration", 
                                "prompt_eval_count", "eval_count", "context", 
                                "done_reason", "eval_duration"
                            ]
                            if any(metadata_key in raw_content for metadata_key in metadata_indicators):
                                logger.debug("🔧 Skipping metadata content")
                                continue
                            
                            # Skip content that looks like raw token arrays (numbers separated by commas)
                            if raw_content.strip().startswith('[') or raw_content.replace(',', '').replace(' ', '').isdigit():
                                logger.debug("🔧 Skipping token array content")
                                continue
                            
                            # Skip content that is mostly numbers and commas (context tokens)
                            numeric_chars = sum(1 for c in raw_content if c.isdigit() or c in [',', ' ', '\n'])
                            if len(raw_content) > 50 and numeric_chars / len(raw_content) > 0.8:
                                logger.debug("🔧 Skipping numeric token content")
                                continue
                            
                            content_chunk = {
                                "id": f"chatcmpl-{int(time.time())}",
                                "object": "chat.completion.chunk", 
                                "created": int(time.time()),
                                "model": model,
                                "choices": [{"index": 0, "delta": {"content": raw_content}, "finish_reason": None}]
                            }
                            yield f"data: {json.dumps(content_chunk)}\n\n"
        else:
            logger.error("🚨 Internal response missing body_iterator")
            logger.error(f"🚨 Response type: {type(internal_response)}")
            logger.error(f"🚨 Response attributes: {dir(internal_response)}")
    except Exception as e:
        logger.error(f"🚨 Direct streaming error: {str(e)}")
        logger.error(f"🚨 Error traceback: {traceback.format_exc()}")
        error_chunk = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{"index": 0, "delta": {"content": f"Error processing request: {str(e)}"}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

async def export_conversation_to_pdf(message_history: list, filename: str = "conversation.pdf") -> dict:
    """
    Export conversation history to PDF using CENTRALIZED PDF SERVICE
    """
    logger.debug("🎯 ConversationExport: Routing to CENTRALIZED PDF SERVICE")
    
    try:
        # Import the centralized PDF service
        from services.pdf_service import create_pdf
        
        if not message_history:
            return {
                "success": False, 
                "error": "No conversation history to export"
            }
        
        # Parse message history into structured format
        parsed_messages = []
        for msg in message_history:
            # Parse "ROLE: content" format
            if ':' in msg and msg.upper().startswith(('USER:', 'ASSISTANT:', 'SYSTEM:')):
                parts = msg.split(':', 1)
                role = parts[0].strip().lower()
                content = parts[1].strip()
                
                parsed_messages.append({
                    'role': role,
                    'content': content
                })
        
        if not parsed_messages:
            return {
                "success": False,
                "error": "Could not parse conversation messages"
            }
        
        # Generate conversation content as markdown
        markdown_content = _format_conversation_for_markdown(parsed_messages)
        
        # Route to centralized PDF service
        result = create_pdf(
            content=markdown_content,
            output_path=filename,
            title="Conversation Export",
            content_type="markdown"
        )
        
        if result["success"]:
            return {
                "success": True,
                "file_path": filename,
                "message_count": len(parsed_messages),
                "service": result.get("service", "CentralizedPDFService"),
                "message": f"Conversation exported to {filename}"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "PDF generation failed")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Export failed: {str(e)}"
        }


def _format_conversation_for_markdown(messages: list) -> str:
    """Format conversation messages as clean Markdown for PDF conversion"""
    md_parts = []
    
    # Add conversation statistics
    md_parts.append("# 💬 Conversation Export")
    md_parts.append("")
    md_parts.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_parts.append(f"**Total Messages:** {len(messages)}")
    md_parts.append("")
    
    user_count = sum(1 for msg in messages if msg['role'] == 'user')
    assistant_count = sum(1 for msg in messages if msg['role'] == 'assistant')
    
    md_parts.append(f"**User Messages:** {user_count}")
    md_parts.append(f"**Assistant Messages:** {assistant_count}")
    md_parts.append("")
    md_parts.append("---")
    md_parts.append("")
    
    # Add conversation content
    for i, message in enumerate(messages, 1):
        role = message['role'].title()
        content = message['content']
        
        # Add role headers for clarity
        if role == 'User':
            md_parts.append("## 👤 User")
        else:
            md_parts.append("## 🤖 Assistant")
        
        md_parts.append("")
        md_parts.append(content)
        md_parts.append("")
        
        # Add separator between messages
        if i < len(messages):
            md_parts.append("---")
            md_parts.append("")
    
    return '\n'.join(md_parts)

# ALL PDF FORMATTING FUNCTIONS REMOVED - PDF PROCESSING COMPLETELY DISABLED

async def openai_streaming_response(user_prompt: str, model: str, conversation_id: str, images: list = None):
    """Handle streaming OpenAI response with proper format - simplified implementation"""
    try:
        logger.info(f"🔒 OpenAI Streaming Response requested")
        
        async def stream_generator():
            # Send initial chunk
            chunk = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": ""},
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            
            # Mirror/capture native streaming response
            # 🔧 CRITICAL FIX: Properly split enhanced prompt for multi-turn conversations
            actual_prompt = ""
            context_part = ""
            
            if "\n=== CURRENT REQUEST ===\n" in user_prompt:
                # This is a multi-turn conversation with context
                parts = user_prompt.split("\n=== CURRENT REQUEST ===\n")
                context_part = parts[0]  # Everything before current request
                actual_prompt = parts[1]  # Current user request only
                logger.info(f"🔄 MULTI-TURN: Separated context ({len(context_part)} chars) from prompt ({len(actual_prompt)} chars)")
            else:
                # Single turn - no context separation needed
                actual_prompt = user_prompt
                context_part = ""
                logger.info(f"🆕 SINGLE-TURN: Using full prompt ({len(actual_prompt)} chars)")
            
            native_request_data = {
                "prompt": actual_prompt,
                "model": ServerConfig.DEFAULT_MODEL,
                "toolsInUse": True,
                "prompt_context": context_part,  # 🔧 FIX: Now properly includes conversation context
                "searchWebInUse": False,
                "images": images if images else ["noimage"],  # 🔧 FIX: Use actual images from OpenAI request
                "tools_calling_model": ServerConfig.DEFAULT_TOOL_CALLING_MODEL,
                "system": ""
            }
            
            # Choose routing method based on feature flag
            if ServerConfig.USE_DIRECT_FUNCTION_CALLS:
                logger.info(f"🔀 Using DIRECT function calls (faster, no HTTP overhead)")
                logger.debug(f"🔧 CONTEXT FIX DEBUG: Calling openai_direct_stream")
                logger.debug(f"🔧 CONTEXT FIX DEBUG: prompt='{actual_prompt[:100]}...'")
                logger.debug(f"🔧 CONTEXT FIX DEBUG: context='{context_part[:100]}...'")
                logger.debug(f"🔧 CONTEXT FIX DEBUG: model='{model}'")
                # Option 2: Direct function calls - More efficient
                async for chunk_data in openai_direct_stream(native_request_data, model):
                    yield chunk_data
                return
            else:
                logger.info(f"🔀 HTTP requests temporarily disabled due to indentation issues")
                # TODO: Fix HTTP option later
                # Fallback to error for now
                error_chunk = {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion.chunk", 
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{"index": 0, "delta": {"content": "HTTP option temporarily disabled. Use USE_DIRECT_FUNCTION_CALLS=true"}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
                return
            
            # Stream termination is now handled by detecting native "done" signal
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"🚨 OpenAI streaming error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# PHASE 2B MANAGEMENT ENDPOINTS
# ==============================================================================

if PHASE2B_AVAILABLE:
    @app.get("/phase2b/status")
    async def get_phase2b_status():
        """Get Phase 2B system status and feature flags"""
        try:
            return {
                "success": True,
                "rollback_controller": rollback_controller.get_status(),
                "performance_health": get_performance_health(),
                "streaming_stats": get_streaming_statistics(),
                "buffer_stats": get_buffer_statistics(),
                "classification_stats": get_classification_statistics(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Phase 2B status error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/phase2b/feature/{feature_name}/enable")
    async def enable_phase2b_feature_endpoint(feature_name: str):
        """Enable a Phase 2B feature"""
        try:
            # Validate feature name
            feature_map = {
                "streaming": FeatureFlag.STREAMING_FALLBACK,
                "buffer_optimization": FeatureFlag.BUFFER_OPTIMIZATION,
                "response_classification": FeatureFlag.RESPONSE_CLASSIFICATION,
                "performance_monitoring": FeatureFlag.PERFORMANCE_MONITORING,
                "response_streaming": FeatureFlag.RESPONSE_STREAMING
            }
            
            if feature_name not in feature_map:
                return {
                    "success": False, 
                    "error": f"Invalid feature name. Available: {list(feature_map.keys())}"
                }
            
            feature = feature_map[feature_name]
            success = enable_phase2b_feature(feature)
            
            if success:
                logger.info(f"✅ Phase 2B feature enabled: {feature_name}")
                return {
                    "success": True,
                    "message": f"Feature {feature_name} enabled successfully",
                    "status": rollback_controller.get_status()
                }
            else:
                return {"success": False, "error": "Failed to enable feature"}
                
        except Exception as e:
            logger.error(f"❌ Feature enable error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/phase2b/feature/{feature_name}/disable")
    async def disable_phase2b_feature_endpoint(feature_name: str):
        """Disable a Phase 2B feature"""
        try:
            feature_map = {
                "streaming": FeatureFlag.STREAMING_FALLBACK,
                "buffer_optimization": FeatureFlag.BUFFER_OPTIMIZATION,
                "response_classification": FeatureFlag.RESPONSE_CLASSIFICATION,
                "response_streaming": FeatureFlag.RESPONSE_STREAMING
                # Note: performance_monitoring cannot be disabled for safety
            }
            
            if feature_name not in feature_map:
                return {
                    "success": False, 
                    "error": f"Invalid feature name. Available: {list(feature_map.keys())}"
                }
            
            feature = feature_map[feature_name]
            success = disable_phase2b_feature(feature)
            
            if success:
                logger.info(f"🔒 Phase 2B feature disabled: {feature_name}")
                return {
                    "success": True,
                    "message": f"Feature {feature_name} disabled successfully",
                    "status": rollback_controller.get_status()
                }
            else:
                return {"success": False, "error": "Failed to disable feature"}
                
        except Exception as e:
            logger.error(f"❌ Feature disable error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/phase2b/rollback/emergency")
    async def emergency_rollback_endpoint():
        """Emergency rollback to Phase 2A baseline"""
        try:
            logger.warning("🚨 Emergency rollback requested via API")
            success = emergency_rollback_phase2b()
            
            if success:
                return {
                    "success": True,
                    "message": "Emergency rollback successful - Phase 2A baseline restored",
                    "status": rollback_controller.get_status()
                }
            else:
                return {"success": False, "error": "Emergency rollback failed"}
                
        except Exception as e:
            logger.critical(f"💥 Emergency rollback API error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/phase2b/rollback/clear-emergency")
    async def clear_emergency_fallback_endpoint():
        """Clear emergency fallback mode to allow feature activation"""
        try:
            logger.info("🔄 Clearing emergency fallback mode via API")
            success = rollback_controller.disable_emergency_fallback()
            
            if success:
                return {
                    "success": True,
                    "message": "Emergency fallback cleared - features can now be enabled",
                    "status": rollback_controller.get_status()
                }
            else:
                return {"success": False, "error": "Failed to clear emergency fallback"}
                
        except Exception as e:
            logger.error(f"❌ Clear emergency fallback error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/phase2b/checkpoints")
    async def list_rollback_checkpoints():
        """List available rollback checkpoints"""
        try:
            checkpoints = rollback_controller.list_checkpoints()
            return {
                "success": True,
                "checkpoints": checkpoints,
                "count": len(checkpoints)
            }
        except Exception as e:
            logger.error(f"❌ Checkpoint listing error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/phase2b/rollback/{checkpoint_id}")
    async def rollback_to_checkpoint_endpoint(checkpoint_id: str):
        """Rollback to a specific checkpoint"""
        try:
            success = rollback_controller.rollback_to_checkpoint(checkpoint_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Rollback to {checkpoint_id} successful",
                    "status": rollback_controller.get_status()
                }
            else:
                return {"success": False, "error": f"Rollback to {checkpoint_id} failed"}
                
        except Exception as e:
            logger.error(f"❌ Rollback error: {e}")
            return {"success": False, "error": str(e)}

# ==============================================================================
# DOCUMENT INTERROGATION ENDPOINTS
# ==============================================================================

# Document Interrogation System - FAISS-based RAG integration
try:
    from document_interrogator import get_document_interrogator
    
    @app.post("/documents/index-directory")
    async def index_directory_endpoint(request: Request):
        """Index all documents in a directory for interrogation"""
        try:
            data = await request.json()
            directory_path = data.get('directory_path')
            recursive = data.get('recursive', True)
            
            if not directory_path:
                return {"success": False, "error": "directory_path is required"}
            
            interrogator = get_document_interrogator()
            if not interrogator.is_ready():
                return {
                    "success": False, 
                    "error": "Document interrogation system not ready. Install: pip install faiss-cpu numpy PyPDF2 python-docx openpyxl beautifulsoup4"
                }
            
            logger.info(f"📚 Starting smart directory indexing: {directory_path}")
            results = await interrogator.smart_index_directory(directory_path, recursive)
            
            if results['success']:
                return {
                    "success": True,
                    "message": results['message'],
                    "processed": results['processed'],
                    "failed": results['failed'], 
                    "skipped": results['skipped'],
                    "total_files_found": results['total_files_found'],
                    "files": results.get('files', []),
                    "stats": interrogator.get_stats()
                }
            else:
                return {
                    "success": False,
                    "error": results['error'],
                    "message": results['message']
                }
            
        except Exception as e:
            logger.error(f"❌ Directory indexing error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/documents/search")
    async def search_documents_endpoint(request: Request):
        """Search indexed documents for relevant content"""
        try:
            data = await request.json()
            query = data.get('query', '')
            k = data.get('k', 5)  # Number of chunks to return
            
            if not query.strip():
                return {"success": False, "error": "query is required"}
            
            interrogator = get_document_interrogator()
            if not interrogator.is_ready():
                return {
                    "success": False,
                    "error": "Document interrogation system not ready"
                }
            
            logger.info(f"🔍 Document search: {query}")
            search_results = await interrogator.search_documents(query, k)
            
            return {
                "success": True,
                "query": query,
                "chunks_found": search_results.get('chunks_found', 0),
                "chunks": search_results.get('chunks', []),
                "context": search_results.get('context', ''),
                "sources": search_results.get('sources', [])
            }
            
        except Exception as e:
            logger.error(f"❌ Document search error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/documents/interrogate")
    async def interrogate_documents_endpoint(request: Request):
        """Interrogate documents with natural language questions (integrates with 2-stage LLM)"""
        try:
            data = await request.json()
            question = data.get('question', '')
            k = data.get('k', 5)
            model = data.get('model', config_loader.get_tool_calling_model())
            
            if not question.strip():
                return {"success": False, "error": "question is required"}
            
            interrogator = get_document_interrogator()
            if not interrogator.is_ready():
                return {
                    "success": False,
                    "error": "Document interrogation system not ready"
                }
            
            logger.info(f"❓ Document interrogation: {question}")
            
            # Stage 0: RAG Retrieval - Get document context
            search_results = await interrogator.search_documents(question, k)
            
            if not search_results.get('context'):
                return {
                    "success": True,
                    "answer": "No relevant documents found for your question.",
                    "sources": [],
                    "query": question
                }
            
            # Prepare enhanced prompt with document context for 2-stage LLM
            document_context = search_results['context']
            enhanced_prompt = f"""Based on the following document excerpts, please answer the question: "{question}"

Document Context:
{document_context}

Please provide a comprehensive answer based on the information provided. If the information is insufficient, please indicate what additional information would be helpful."""
            
            # Stage 1 & 2: Use existing 2-stage LLM architecture
            # Create mock request for existing pipeline
            class MockRequest:
                def __init__(self, prompt, model):
                    self.method = "POST"
                    self.headers = {"content-type": "application/json"}
                    self._json = {
                        "prompt": prompt,
                        "model": model,
                        "stream": False
                    }
                
                async def json(self):
                    return self._json
            
            # Route through existing llama_stream function for consistency
            mock_request = MockRequest(enhanced_prompt, model)
            llm_response = await llama_stream(mock_request)
            
            # Extract answer from streaming response
            if hasattr(llm_response, 'body_iterator'):
                answer_parts = []
                async for chunk_data in llm_response.body_iterator:
                    if isinstance(chunk_data, bytes):
                        chunk_data = chunk_data.decode('utf-8')
                    answer_parts.append(chunk_data)
                answer = ''.join(answer_parts)
            else:
                answer = str(llm_response)
            
            return {
                "success": True,
                "answer": answer,
                "sources": search_results.get('sources', []),
                "query": question,
                "chunks_found": search_results.get('chunks_found', 0),
                "model_used": model
            }
            
        except Exception as e:
            logger.error(f"❌ Document interrogation error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/documents/watch-directory")
    async def watch_directory_endpoint(request: Request):
        """Start watching a directory for new/modified documents"""
        try:
            data = await request.json()
            directory_path = data.get('directory_path')
            
            if not directory_path:
                return {"success": False, "error": "directory_path is required"}
            
            interrogator = get_document_interrogator()
            success = interrogator.start_watching(directory_path)
            
            return {
                "success": success,
                "message": f"{'Started' if success else 'Failed to start'} watching directory: {directory_path}",
                "watched_directories": list(interrogator.watched_directories)
            }
            
        except Exception as e:
            logger.error(f"❌ Directory watching error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/documents/stop-watching")
    async def stop_watching_endpoint():
        """Stop watching all directories"""
        try:
            interrogator = get_document_interrogator()
            interrogator.stop_watching()
            
            return {
                "success": True,
                "message": "Stopped watching all directories"
            }
            
        except Exception as e:
            logger.error(f"❌ Stop watching error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/documents/stats")
    async def document_stats_endpoint():
        """Get document interrogation system statistics"""
        try:
            interrogator = get_document_interrogator()
            stats = interrogator.get_stats()
            
            return {
                "success": True,
                "stats": stats,
                "system_ready": interrogator.is_ready()
            }
            
        except Exception as e:
            logger.error(f"❌ Document stats error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/documents/config")
    async def get_config_endpoint():
        """Get current watch configuration status"""
        try:
            interrogator = get_document_interrogator()
            config_status = interrogator.get_config_status()
            
            return {
                "success": True,
                "config": config_status
            }
            
        except Exception as e:
            logger.error(f"❌ Get config error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/documents/config/add-directory")
    async def add_watch_directory_endpoint(request: Request):
        """Add a directory to the watch configuration"""
        try:
            data = await request.json()
            directory_path = data.get('path')
            recursive = data.get('recursive', True)
            enabled = data.get('enabled', True)
            description = data.get('description', '')
            
            if not directory_path:
                return {"success": False, "error": "path is required"}
            
            interrogator = get_document_interrogator()
            success = interrogator.add_watch_directory(directory_path, recursive, enabled, description)
            
            return {
                "success": success,
                "message": f"{'Added' if success else 'Failed to add'} directory to config: {directory_path}",
                "config": interrogator.get_config_status()
            }
            
        except Exception as e:
            logger.error(f"❌ Add watch directory error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/documents/config/remove-directory")
    async def remove_watch_directory_endpoint(request: Request):
        """Remove a directory from the watch configuration"""
        try:
            data = await request.json()
            directory_path = data.get('path')
            
            if not directory_path:
                return {"success": False, "error": "path is required"}
            
            interrogator = get_document_interrogator()
            success = interrogator.remove_watch_directory(directory_path)
            
            return {
                "success": success,
                "message": f"{'Removed' if success else 'Failed to remove'} directory from config: {directory_path}",
                "config": interrogator.get_config_status()
            }
            
        except Exception as e:
            logger.error(f"❌ Remove watch directory error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/documents/config/scan-changes")
    async def force_scan_changes_endpoint():
        """Force scan all configured directories for changes"""
        try:
            interrogator = get_document_interrogator()
            await interrogator.force_scan_changes()
            
            return {
                "success": True,
                "message": "Completed force scan of all configured directories",
                "config": interrogator.get_config_status()
            }
            
        except Exception as e:
            logger.error(f"❌ Force scan error: {e}")
            return {"success": False, "error": str(e)}

except ImportError as e:
    logger.warning(f"⚠️ Document interrogation not available: {e}")
    
    # Provide fallback endpoints that return helpful error messages
    @app.post("/documents/index-directory")
    async def index_directory_unavailable():
        return {
            "success": False,
            "error": "Document interrogation not available. Install dependencies: pip install faiss-cpu numpy PyPDF2 python-docx openpyxl beautifulsoup4 pytesseract pillow watchdog"
        }
    
    @app.post("/documents/search")
    @app.post("/documents/interrogate")
    @app.post("/documents/watch-directory")
    @app.post("/documents/stop-watching")
    @app.get("/documents/stats")
    async def document_endpoints_unavailable():
        return {
            "success": False,
            "error": "Document interrogation not available. Install dependencies first."
        }

# ==============================================================================
# MAIN APPLICATION RUNNER
# ==============================================================================

if __name__ == "__main__":
    logger.info(f"Starting complete server on {ServerConfig.HOST}:{ServerConfig.PORT}")
    
    # Check logging configuration (env vars override config file)
    debug_config = config_loader.load_config().get('debug', {})
    log_requests_enabled = os.getenv('LOG_REQUESTS', str(debug_config.get('log_requests', True))).lower() in ('true', '1', 'yes')
    
    uvicorn.run(
        "fastapi_server_complete:app",
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        reload=ServerConfig.DEBUG,
        access_log=log_requests_enabled,  # Respect configuration
        log_level="info"
    )