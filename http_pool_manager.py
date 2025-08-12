"""
HTTP Connection Pool Manager for FastAPI Agentic RAG Server
Provides optimized connection pooling for all external HTTP requests
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class HTTPPoolManager:
    """
    Global HTTP connection pool manager for optimized external API calls.
    Provides both async and sync interfaces with connection reuse.
    """
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
        self._initialized = False
        
        # Connection pool configuration
        self.connector_config = {
            'limit': 100,  # Total connection limit
            'limit_per_host': 30,  # Per-host connection limit
            'ttl_dns_cache': 300,  # DNS cache TTL in seconds
            'use_dns_cache': True,
            'keepalive_timeout': 300,  # Keep connections alive for 5 minutes
            'enable_cleanup_closed': True
        }
        
        # Request timeout configuration
        self.timeout_config = aiohttp.ClientTimeout(
            total=30,  # Total request timeout
            connect=5,  # Connection timeout
            sock_read=10  # Socket read timeout
        )
        
        # Default headers for all requests
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    async def initialize(self):
        """Initialize the connection pool"""
        async with self._lock:
            if not self._initialized:
                connector = aiohttp.TCPConnector(**self.connector_config)
                self._session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=self.timeout_config,
                    headers=self.default_headers
                )
                self._initialized = True
                logger.info("🔗 HTTP Connection Pool initialized with optimized settings")
    
    async def cleanup(self):
        """Cleanup the connection pool"""
        async with self._lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._initialized = False
                logger.info("🔗 HTTP Connection Pool cleaned up")
    
    @asynccontextmanager
    async def get_session(self):
        """Get the shared session with automatic initialization"""
        if not self._initialized:
            await self.initialize()
        
        if self._session and not self._session.closed:
            yield self._session
        else:
            # Reinitialize if session was closed
            await self.initialize()
            yield self._session
    
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, 
                  timeout: Optional[float] = None, **kwargs) -> aiohttp.ClientResponse:
        """
        Perform GET request using connection pool
        
        Args:
            url: Target URL
            headers: Additional headers (merged with defaults)
            timeout: Request timeout override
            **kwargs: Additional aiohttp arguments
        """
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        timeout_override = None
        if timeout:
            try:
                timeout_override = aiohttp.ClientTimeout(total=timeout)
            except RuntimeError:
                # Handle event loop context issues  
                timeout_override = aiohttp.ClientTimeout(total=timeout)
        
        async with self.get_session() as session:
            async with session.get(
                url, 
                headers=request_headers,
                timeout=timeout_override,
                **kwargs
            ) as response:
                # Read response content to ensure connection can be reused
                await response.read()
                return response
    
    async def post(self, url: str, data: Optional[Any] = None, 
                   json: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   timeout: Optional[float] = None, **kwargs) -> aiohttp.ClientResponse:
        """
        Perform POST request using connection pool
        
        Args:
            url: Target URL
            data: Form data
            json: JSON data
            headers: Additional headers (merged with defaults)  
            timeout: Request timeout override
            **kwargs: Additional aiohttp arguments
        """
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        timeout_override = None
        if timeout:
            try:
                timeout_override = aiohttp.ClientTimeout(total=timeout)
            except RuntimeError:
                # Handle event loop context issues  
                timeout_override = aiohttp.ClientTimeout(total=timeout)
        
        async with self.get_session() as session:
            async with session.post(
                url,
                data=data,
                json=json,
                headers=request_headers,
                timeout=timeout_override,
                **kwargs
            ) as response:
                # Read response content to ensure connection can be reused
                await response.read()
                return response
    
    async def get_text(self, url: str, headers: Optional[Dict[str, str]] = None,
                       timeout: Optional[float] = None, **kwargs) -> str:
        """Get response text content using connection pool"""
        async with self.get_session() as session:
            request_headers = self.default_headers.copy()
            if headers:
                request_headers.update(headers)
            
            timeout_override = None
            if timeout:
                try:
                    timeout_override = aiohttp.ClientTimeout(total=timeout)
                except RuntimeError:
                    # Handle event loop context issues
                    timeout_override = aiohttp.ClientTimeout(total=timeout)
            
            async with session.get(
                url,
                headers=request_headers, 
                timeout=timeout_override,
                **kwargs
            ) as response:
                return await response.text()
    
    async def get_content(self, url: str, headers: Optional[Dict[str, str]] = None,
                          timeout: Optional[float] = None, **kwargs) -> bytes:
        """Get response binary content using connection pool"""
        async with self.get_session() as session:
            request_headers = self.default_headers.copy()
            if headers:
                request_headers.update(headers)
            
            timeout_override = None
            if timeout:
                try:
                    timeout_override = aiohttp.ClientTimeout(total=timeout)
                except RuntimeError:
                    # Handle event loop context issues
                    timeout_override = aiohttp.ClientTimeout(total=timeout)
            
            async with session.get(
                url,
                headers=request_headers,
                timeout=timeout_override,
                **kwargs
            ) as response:
                return await response.read()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self._session or not self._session.connector:
            return {"status": "not_initialized"}
        
        connector = self._session.connector
        return {
            "status": "active",
            "total_connections": len(connector._conns),
            "acquired_connections": len(connector._acquired),
            "available_connections": len(connector._available_connections(None)),
            "connector_limit": connector.limit,
            "per_host_limit": connector.limit_per_host
        }


# Global connection pool instance
http_pool = HTTPPoolManager()


async def init_http_pool():
    """Initialize the global HTTP connection pool"""
    await http_pool.initialize()


async def cleanup_http_pool():
    """Cleanup the global HTTP connection pool"""
    await http_pool.cleanup()