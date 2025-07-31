#!/usr/bin/env python3
"""
Complete FastAPI Server with Ollama LLM Integration
=================================================

FastAPI server with all original Flask functionality including:
- Ollama LLM endpoints with streaming
- Tool calling system (RAG, web search, stock data, etc.)
- Async processing for performance
- Database connection pooling
- Caching layer
"""

import asyncio
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

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
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
    from webcrawler import SeleniumCrawler
    from text_chunker import TextChunker
    import PyPDF2
    import magic
    import trafilatura
    from urllib.parse import urlparse
    TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Some tools not available: {e}")
    TOOLS_AVAILABLE = False

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
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'llama3.2:3b')
    
    # Server configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Performance configuration
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))
    TASK_TIMEOUT = int(os.getenv('TASK_TIMEOUT', '300'))
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
    tools_calling_model: Optional[str] = Field(default="qwen3:8b", description="Model for tool calls")
    
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

# ==============================================================================
# GLOBAL VARIABLES
# ==============================================================================

db_pool: Optional[Pool] = None
thread_pool = ThreadPoolExecutor(max_workers=ServerConfig.MAX_WORKERS)
simple_cache = {}

# ==============================================================================
# LOGGING SETUP
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fastapi_complete.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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
            'get_stock_and_company_data': self.get_stock_and_company_data,
            'get_news_summaries': self.get_news_summaries,
            'search_web': self.search_web,
            'lookup_website': self.lookup_website
        }
        
        # Load user-defined tools - defer to async initialization
        self.user_tools = []
        self.user_tools_loaded = False
            
        logger.info(f"AsyncToolManager initialized with {len(self.available_functions)} tools")
    
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
    
    async def get_tools_definitions(self) -> list:
        """Get tools definitions for Ollama tool calling"""
        # Load user tools if not already loaded
        await self._load_user_tools_async()
        
        # Always return tools for testing (even if TOOLS_AVAILABLE is False)
        # The individual functions will handle missing dependencies gracefully
        
        # Return all 6 tool functions with timeout/race condition fixes applied
        tools_definitions = [
            {
                "type": "function",
                "function": {
                    "name": "get_the_secret_tool",
                    "description": "Must call this function to get the current date and time from the system.",
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
                    "description": "Returns time-sensitive News with full article content! Tag all news items with Date, Time, and Source in response! This function takes a keyword string as input as a possible filter for news headlines and returns today's news headlines with detailed content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "The input filter is a string type that helps narrow down the choices of headlines. Examples: \"National\", \"Middle East\", \"World\", \"Technology\""
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
                    "description": "This function takes a query string as input and searches the web for information using the query verbatim. It returns links and URLs if found with a brief description, or an error message if no information is available.",
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
                    "description": "Retrieves concise factual information from Wikipedia about a specific topic based on a user-provided query. This function processes the query to identify the main topic and searches Wikipedia using the topic as a reference.",
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
                    "description": "Calls a financial data provider to get latest stock and company data. Returns description, financial information, news, stock prices, analysts sentiments, and forward earnings estimates.",
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
        for tool in self.user_tools:
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
        
        return tools_definitions
    
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
                    # Format the successful result
                    tool_result = result.get("result", {})
                    if isinstance(tool_result, dict):
                        # Convert dict result to readable string
                        return json.dumps(tool_result, indent=2)
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
                query = data.get('query', args) if isinstance(data, dict) else str(args)
            except (json.JSONDecodeError, AttributeError):
                query = str(args)
            
            def sync_wikipedia_query():
                wiki = wikipediaapi.Wikipedia(
                    language='en',
                    user_agent='FastAPIServer/1.0 (https://github.com/user/project)'
                )
                page = wiki.page(query)
                if page.exists():
                    return page.summary[:1000] + "..." if len(page.summary) > 1000 else page.summary
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
                
                # Original news category mapping and URLs
                NEWS_URLS = {
                    "world": [
                        "https://apnews.com/world-news",
                        "https://www.aljazeera.com/europe/",
                        "https://www.reuters.com/world/"
                    ],
                    "national": [
                        "https://apnews.com/us-news",
                        "https://www.reuters.com/world/us/",
                        "https://www.npr.org/sections/national/"
                    ],
                    "business": [
                        "https://www.npr.org/sections/business/",
                        "https://www.reuters.com/business/"
                    ],
                    "finance": [
                        "https://www.reuters.com/markets/global-market-data/",
                        "https://www.cnbc.com/economy/",
                        "https://finance.yahoo.com/topic/stock-market-news/",
                        "https://www.reuters.com/markets/us/",
                        "https://finance.yahoo.com/topic/latest-news/"
                    ],
                    "science": [
                        "https://www.reuters.com/technology/",
                        "https://www.sciencenews.org/all-stories",
                        "https://www.npr.org/sections/science/"
                    ],
                    "news": [        
                        "https://apnews.com/hub/ap-top-news",
                        "https://www.reuters.com/",
                        "https://www.npr.org/sections/news/"
                    ],
                    "default": [
                        "https://apnews.com/hub/ap-top-news",
                        "https://www.reuters.com/"
                    ]
                }
                
                # Original synonyms mapping
                SYNONYMS = {
                    "world": {"world", "global", "international"},
                    "national": {"national", "nation", "domestic", "us", "usa", "american"},
                    "business": {"business", "trade", "commerce", "commercial", "retail"},
                    "financial": {"financial", "trade", "commerce", "commercial", "retail", "macroeconomics", "microeconomics", "business cycle"},
                    "finance": {"finance", "financial","stocks" ,"market" ,"markets", "stock" ,"stock market", "securities", "inflation", "financing", "stock trading", "bonds", "interest rates", "fed rates", "us economy", "economy","economic","federal reserve"},
                    "science": {"science","scientific","physics","chemistry","biology","technology","nasa", "space"}
                }
                
                # Find category function (from original)
                def find_category(newsFilter):
                    import re
                    filter_words = re.split(r'[,\.;:!?\-]+', newsFilter.lower())
                    for category, synonyms in SYNONYMS.items():
                        if any(word in synonyms for word in filter_words):
                            return category
                    return "default"
                
                # Enhanced Google News function with FULL ARTICLE CONTENT
                def get_news_from_google(keyword):
                    res = ''
                    articlesLimit = 8  # Reduced slightly to account for more content per article
                    try:
                        google_news = GNews(language='en', country='US', max_results=articlesLimit)
                        keyword_news = google_news.get_news(keyword)
                        
                        for i in range(min(len(keyword_news), articlesLimit)):
                            article = keyword_news[i]
                            title = article.get('title', 'No title')
                            description = article.get('description', 'No description')
                            published_date = article.get('published date', 'N/A')
                            
                            # Try to get full article content
                            full_content = ""
                            try:
                                # Check if newspaper3k is available
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
                                    article_url = article.get('url', '')
                                    if article_url:
                                        enhanced_content = get_text_from_url(article_url)
                                        if len(enhanced_content) > len(description):
                                            full_content = enhanced_content[:800] + "..." if len(enhanced_content) > 800 else enhanced_content
                                except Exception as url_error:
                                    pass  # Keep original description
                            except Exception as content_error:
                                # Fallback to description if full content extraction fails
                                full_content = description
                                
                            res += f"Published on: {published_date} -- Title: {title}\nContent: {full_content}\nSource: {article.get('publisher', {}).get('title', 'Unknown')}\n---\n"
                            
                    except Exception as e:
                        res += f"Error from Google news: {e}\n"
                    return res
                
                # Web content extraction (simplified version)
                def get_text_from_url(url):
                    try:
                        response = requests.get(url, timeout=10, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        response.raise_for_status()
                        
                        from bs4 import BeautifulSoup
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
                
                # Find the corresponding category using the synonyms dictionary
                category = find_category(newsFilter)
                
                # Get the list of URLs based on the category
                urls = NEWS_URLS.get(category, NEWS_URLS["default"])
                
                # Initialize result string with timestamp
                res = f'\nFROM EXTERNAL SOURCES as of [Current Date and Time: {todayStr}]. Here is the News Summary you requested, use the summary to compose your response to the user\'s prompt:\n\n'
                
                # Get Google News results first
                google_results = get_news_from_google(newsFilter)
                res += google_results
                
                # Fetch content from each URL (limit to 2 URLs to avoid timeout)
                for newsURL in urls[:2]:
                    try:
                        url_content = get_text_from_url(newsURL)
                        res += f"\n\nFrom Source: {newsURL}\n{url_content}\n\n"
                    except Exception as e:
                        res += f"Error fetching {newsURL}: {e}\n"
                
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
                                res += f"\nResult {i}:\nTitle: {title}\nURL: {href}\nDescription: {body}\n"
                                
                                # Extract content from each URL
                                if href != 'No URL':
                                    try:
                                        content = get_text_from_url_simplified(href)
                                        res += f"Content: {content}\n"
                                    except Exception as e:
                                        res += f"Error extracting content from {href}: {str(e)}\n"
                            return res
                    except Exception as e:
                        print(f"DuckDuckGo Error: {e}", flush=True)
                        return f"An error occurred during the web search query '{query}'."
                
                # Simplified URL content extraction (to avoid Selenium dependency issues)
                def get_text_from_url_simplified(url):
                    try:
                        response = requests.get(url, timeout=10, headers={
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
                            full_response = requests.get(url, stream=True, timeout=10)
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
                        response = requests.get(url, timeout=30)
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
            response = requests.get(url, headers=headers, timeout=30)
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

                # Format response similar to original but cleaner
                response_parts = [
                    f"\nAs of [Current Date and Time: {todayStr}] here are the website lookup results:",
                    f"Title: {result['title']}",
                    f"URL: {url}",
                    f"Type: {content_type}",
                    f"Content:\n{content}"
                ]

                if result.get('author'):
                    response_parts.insert(-1, f"Author: {result['author']}")
                
                if result.get('date'):
                    response_parts.insert(-1, f"Published: {result['date']}")

                final_response = '\n'.join(response_parts)
                
                print(f"Website extraction completed: {len(final_response)} chars", flush=True)
                return final_response
            
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool, sync_website_extraction
            )
        except Exception as e:
            return f"Website extraction error: {str(e)}"
    
    async def safe_function_call(self, func_name: str, args: str) -> str:
        """Safely execute a function"""
        if func_name not in self.available_functions:
            return f"Function {func_name} not available"
        
        try:
            func = self.available_functions[func_name]
            result = await func(args)
            return str(result)
        except Exception as e:
            logger.error(f"Error calling {func_name}: {e}")
            return f"Error calling {func_name}: {str(e)}"

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
    
    # Test Ollama connection
    try:
        response = requests.get('http://127.0.0.1:11434/api/tags', timeout=5)
        if response.status_code == 200:
            logger.info("Ollama service is available")
        else:
            logger.warning("Ollama service test failed")
    except Exception as e:
        logger.warning(f"Ollama service not available: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_db_pool()
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

# Initialize tool manager
tool_manager = AsyncToolManager()

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
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
    """Check if Ollama service is healthy"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://127.0.0.1:11434/api/tags', timeout=5) as response:
                return response.status == 200
    except:
        return False

def _build_enhanced_primary_system_prompt(original_system, tools_were_executed=False, tools_results_summary=""):
    """
    Build enhanced system prompt for primary LLM when tools have been executed.
    This prevents the primary LLM from redoing work already completed by tool calling model.
    """
    if not tools_were_executed:
        return original_system
    
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
    
    return original_system + enhanced_instructions

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
            "stream": request.stream,
            "think": False  # Disable thinking like the original version
        }
        
        if request.system:
            payload["system"] = request.system
        if request.context:
            payload["context"] = request.context
        
        # Use async HTTP client
        async with aiohttp.ClientSession() as session:
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

@app.post("/llama3_1b/stream")
async def llama_stream(request: Request):
    """
    Main Ollama streaming endpoint with tool calling
    Equivalent to the original /llama3_1b/stream endpoint
    """
    # Parse JSON data manually like the original Flask version
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Extract parameters with defaults (exactly like Flask version)
    user_prompt = data['prompt']  # Use direct access like original for required field
    logger.info(f"\n\nUser prompt : {data['prompt']}\n\n")
    
    prompt_context = data.get('prompt_context', '')  # Using data['prompt_context'] like original
    
    #################################################################################
    ##                  CONTEXT MANAGEMENT WITH and WITHOUT TOOLS                  ##            
    #################################################################################
    
    # Handle toolsInUse exactly like original
    tools_in_use = True  # Default like original
    if "toolsInUse" in data:
        tools_in_use = data["toolsInUse"]
    logger.info(f"\n\n##### toolsInUse from the client = {tools_in_use}\n\n")
    
    # Handle searchWebInUse exactly like original
    search_web_in_use = False  # Default like original
    if "searchWebInUse" in data:
        search_web_in_use = data["searchWebInUse"]
    
    # Other parameters
    model = data.get('model', ServerConfig.DEFAULT_MODEL)
    images = data.get('images', ['noimage'])
    tools_calling_model = data.get('tools_calling_model', 'qwen3:8b')
    
    # Handle images exactly like original
    image_exists = False
    if "images" in data:
        if data["images"][0] != "noimage":
            logger.info("Request has Image ......")
            image_exists = True
    
    async def generate_stream():
        try:
            tools_results = ""
            
            # ###########################################################################
            # TWO-STAGE TOOL CALLING ALGORITHM (exactly like original Flask implementation)
            if (tools_in_use):
                logger.info("---> Tools are in use")
                
                # STAGE 1: Call tool calling model to generate JSON function calls
                # Using the exact system prompt from the original, with user's system prompt integration
                user_system_prompt = data.get('system', '').strip()
                system_content = """BEFORE YOU MAKE FUNCTION CALLS, FOLLOW THIS GUIDELINE:
                        Tool Call Generation Guidelines -->:
                    DO NOT USE MORE THAN THREE (3) DIFFERENT FUNCTIONS. YOU CAN CALL THE SAME FUNCTION MULTIPLE TIMES WIth DIFFERENT PARAMETERS  :
                    
                    Execution Strategy:
                    - Analyze the entire input comprehensively
                    - Select only the tools needed and most relevant to the prompt in most logical sequence
                    - Prioritize precision and relevance
                    - Avoid redundant or unnecessary tool calls.
                    - Ensure each function is called with relevant and required parameters
                    - Use exact proper nouns or specific topics as parameters
                    
                    1. Initial Context Retrieval:
                    - Always begin by calling get_the_secret_tool() to obtain the current date and time
                    - This ensures all subsequent tool calls have accurate temporal context
                    - Depending on the information needed, select a maximum of 2 tools out of the list and call them with more than once if needed with relevant parameters

                    2. Stock and Financial Information:
                    - For stock data, call get_stock_and_company_data() 
                        * One distinct call per stock symbol
                        * Use exact stock ticker as parameter
                    - For additional market context, use get_news_summaries() 
                        * Apply relevant keyword as parameter
                        * Focus on financial keywords related to the stock/sector

                    3. Website Content and URL Analysis:
                    - When the user provides a specific URL or web address, ALWAYS call lookup_website() with that exact URL
                    - Use lookup_website() for:
                        * Academic papers (arXiv, research papers)
                        * Documentation and technical content
                        * Articles and blog posts
                        * Any specific webpage the user wants analyzed
                        * PDFs linked via URL
                    - Example: If user says "Explain this paper: URL: https://arxiv.org/html/..." -> call lookup_website({'url': 'https://arxiv.org/html/...'})
                    - CRITICAL: Never guess or hallucinate content when a URL is provided - always fetch it first

                    4. Current Events, Up-to-date Data, and Local Information
                    - Use search_web() for:
                        * Local events
                        * Current business information
                        * Addresses
                        * Contact details
                        * Real-time local context
                    - For deeper and current news context, supplement with get_news_summaries()

                    5. News and Current Affairs:
                    - Use get_news_summaries() for:
                        * Latest developments in major topics
                        * Global/national events
                        * Specific sectors (economy, politics, military)
                    - When local news is needed, include location specifics 
                        (city, state, country) in the parameter

                    6. Travel and Lifestyle Information:
                    - Employ search_web() for comprehensive queries about:
                        * Flight details
                        * Hotel availability
                        * Vacation destinations
                        * Rental information
                        * Tourist attractions
                    - Use full, detailed query strings
                    
                    7. Encyclopedia and Factual Information: 
                    - Divide the question into partial questions. Use wikipedia_query() only if needed. Call wikipedia_query() once per question as parameter for the following cases:
                        * Historical events
                        * Academic facts
                        * Biographical information
                        * Geographical details
                        * Definitional content
                        * Example Prompt: "Compare the Roman Empire with the Persian Empire and describe their strength and weaknesses." 
                            --> Respond with : tool_calls : wikipedia_query() with {'question'='roman empire'} then call wikipedia_query() again with {'question' : 'persian empire'} 
                        
                        
                    7. Ambiguous or Undefined Requests:
                    - If the input lacks clear actionable context or the need for external data, then
                        * Do NOT generate unnecessary function calls
                        * Return an empty list of function calls
                        * Ask user for clarification
                    
                    8. CRITICAL: Do NOT use wikipedia_query() for:
                        * Current news
                        * Recent events
                        * Breaking stories
                    
                    """
                
                # Add user's system prompt if provided, especially for math operations
                if user_system_prompt:
                    system_content += f"\n\nADDITIONAL USER INSTRUCTIONS:\n{user_system_prompt}"
                
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
                    tools_model = data.get('tools_calling_model', 'qwen3:8b').strip()
                    logger.info(f"Calling Tools Model ==> {tools_model}")
                    logger.info(f"Tools available count: {len(data.get('tools', []))}")
                    logger.info(f"Using endpoint: {ServerConfig.OLLAMA_CHAT_URL}")
                    
                    # Call the tool calling model to get JSON function calls
                    tools_array = await tool_manager.get_tools_definitions()
                    tool_request = {
                        "model": tools_model,
                        "messages": messages,
                        "options": {"temperature": 0},
                        "tools": tools_array,
                        "stream": False,
                        "think": False
                    }
                    logger.info(f"Generated tools array length: {len(tools_array)}")
                    if len(tools_array) == 0:
                        logger.error("❌ Tools array is empty! This will cause timeout.")
                    else:
                        tool_names = [tool['function']['name'] for tool in tools_array]
                        logger.info(f"Available tools: {tool_names}")
                    
                    tool_request["tools"] = tools_array
                    logger.info(f"Sending tool calling request with {len(tool_request['tools'])} tools")
                    
                    response = requests.post(
                        ServerConfig.OLLAMA_CHAT_URL,
                        json=tool_request,
                        timeout=300  # 5 minutes timeout for comprehensive tool operations
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        logger.info(f"Tool calling response status: SUCCESS")
                        logger.info(f"Response keys: {list(response_data.keys())}")
                        
                        if 'message' in response_data:
                            message_keys = list(response_data['message'].keys())
                            logger.info(f"Message keys: {message_keys}")
                            logger.info(f"ollama.chat() response content: {json.dumps(response_data.get('message', {}).get('content', ''))}")
                        
                        # STAGE 2: Process tool calls if present
                        if 'message' in response_data and 'tool_calls' in response_data['message']:
                            tool_calls = response_data['message']['tool_calls']
                            logger.info(f"✅ TOOL CALLS DETECTED! Found {len(tool_calls)} tool calls")
                            
                            # Process each tool call
                            for i, tool_call in enumerate(tool_calls):
                                function_name = tool_call['function']['name']
                                function_args = tool_call['function']['arguments']
                                
                                logger.info(f"Tool Call {i+1}: {function_name} with args: {function_args}")
                                
                                # Add image if applicable
                                if "image" in function_args and image_exists:
                                    function_args["image"] = data.get("images", [None])[0]
                                
                                # Execute the function with timing
                                import time
                                start_time = time.time()
                                logger.info(f"🔧 Executing tool: {function_name} - START")
                                result = await tool_manager.safe_function_call(function_name, function_args)
                                end_time = time.time()
                                execution_time = end_time - start_time
                                logger.info(f"🔧 Tool {function_name} COMPLETED in {execution_time:.2f}s - result length: {len(str(result))} chars")
                                tools_results += f"Tool: {function_name}\nResult: {result}\n\n"
                        
                        else:
                            # No tool calls generated - this is normal for some prompts
                            logger.info("❌ No tool calls generated by the tool calling model")
                            if 'message' in response_data:
                                logger.info(f"Raw message: {json.dumps(response_data['message'], indent=2)}")
                    
                    else:
                        logger.error(f"❌ Tool calling model failed with status: {response.status_code}")
                        logger.error(f"Response: {response.text}")
                        # Fallback: just get current time
                        result = await tool_manager.get_the_secret_tool()
                        tools_results += f"Tool: get_the_secret_tool\nResult: {result}\n\n"
                        
                except Exception as e:
                    logger.error(f"❌ Tool calling exception: {e}")
                    logger.error(f"Exception type: {type(e).__name__}")
                    # Fallback: just get current time
                    result = await tool_manager.get_the_secret_tool()
                    tools_results += f"Tool: get_the_secret_tool\nResult: {result}\n\n"
            
            # CRITICAL: Log when ALL tool execution is complete
            logger.info(f"🎯 ALL TOOL EXECUTION COMPLETED - Starting context management")
            logger.info(f"🎯 Total tools_results length: {len(tools_results)} chars")
            
            # Context management with text chunking (exactly like original implementation)
            context_size = len(prompt_context) if prompt_context else 0
            tool_results_size = len(tools_results)
            system_prompt_size = len(data.get('system', ''))
            max_context_window = 65536  # 64k bytes
            max_context_tokens = max_context_window / 4  # estimating 4 bytes per token
            full_tools_text = (prompt_context or "") + ".\n" + tools_results
            
            # If total context size with tool results exceeds max_context_window then try to shorten it
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
                except Exception as e:
                    logger.error(f"Error: exception in TextChunker.summary_by_semantics() call. Function returned message: {e}")
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
            
            # Build final prompt in exact original format: "Context: " + context + " \n" + user_prompt
            in_prompt = "Context: " + tools_results_summary + " \n" + user_prompt
            logger.info(f"in_prompt size = {len(in_prompt)} bytes")
            
            # Enhanced system prompt for primary LLM when tools have been executed
            original_system = data.get('system', '')
            enhanced_system = _build_enhanced_primary_system_prompt(
                original_system, 
                tools_were_executed=(len(tools_results.strip()) > 0),
                tools_results_summary=tools_results_summary
            )
            
            # Stream response from Ollama  
            async with aiohttp.ClientSession() as session:
                stream_payload = {
                    "model": model,
                    "prompt": in_prompt,
                    "system": enhanced_system,
                    "options": {
                        "temperature": data.get('temperature', 0.7),
                        "top_k": data.get('top_k', 40),
                        "top_p": data.get('top_p', 0.9),
                        "num_ctx": data.get('num_ctx', 4096),
                        "low_vram": data.get('low_vram', False)
                    },
                    "think": False,  # Set to False to disable thinking
                    "stream": True
                }
                
                # Add images if they exist
                if image_exists:
                    stream_payload["images"] = data.get("images")
                
                logger.info(f"🚀 STARTING Primary LLM Call ==> {model}")
                logger.info(f"🚀 Context ready - in_prompt size: {len(in_prompt)} bytes")
                
                async with session.post(ServerConfig.OLLAMA_URL, json=stream_payload, timeout=None) as response:
                    if response.status == 200:
                        async for chunk in response.content.iter_chunked(1024):
                            if chunk:
                                yield chunk
                    else:
                        error_msg = f"Ollama error: {response.status}"
                        yield json.dumps({"error": error_msg}).encode() + b'\n'
        
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
        "services": services,
        "cache_size": len(simple_cache),
        "tools_available": TOOLS_AVAILABLE
    }

@app.get("/ollama/models")
async def list_ollama_models():
    """List available Ollama models"""
    try:
        async with aiohttp.ClientSession() as session:
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
# MAIN APPLICATION RUNNER
# ==============================================================================

if __name__ == "__main__":
    logger.info(f"Starting complete server on {ServerConfig.HOST}:{ServerConfig.PORT}")
    
    uvicorn.run(
        "fastapi_server_complete:app",
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        reload=ServerConfig.DEBUG,
        access_log=True,
        log_level="info"
    )