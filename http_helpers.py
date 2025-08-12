"""
HTTP Helper Functions for Connection Pool Integration
Provides sync-compatible wrappers for async HTTP operations
"""

import asyncio
import requests
from typing import Optional, Dict, Any
from http_pool_manager import http_pool
import threading

# Thread-safe persistent session for sync operations
_sync_session_lock = threading.Lock()
_sync_session = None

def get_persistent_sync_session():
    """Get or create a persistent requests session with connection pooling"""
    global _sync_session
    
    if _sync_session is None:
        with _sync_session_lock:
            if _sync_session is None:
                _sync_session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=10,
                    pool_maxsize=30,
                    max_retries=3
                )
                _sync_session.mount('http://', adapter)
                _sync_session.mount('https://', adapter)
                print("📡 Created persistent sync HTTP session with connection pooling")
    
    return _sync_session


async def pooled_get(url: str, headers: Optional[Dict[str, str]] = None, 
                     timeout: Optional[float] = None, **kwargs) -> Dict[str, Any]:
    """
    Async GET request using connection pool with requests-like response
    
    Returns:
        Dict containing status_code, text, content, headers, etc.
    """
    try:
        async with http_pool.get_session() as session:
            request_headers = session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            timeout_config = None
            if timeout:
                import aiohttp
                try:
                    timeout_config = aiohttp.ClientTimeout(total=timeout)
                except RuntimeError:
                    # Handle event loop context issues
                    timeout_config = timeout  # fallback to numeric timeout
            
            async with session.get(
                url, 
                headers=request_headers,
                timeout=timeout_config,
                **kwargs
            ) as response:
                content = await response.read()
                text = await response.text()
                
                return {
                    'status_code': response.status,
                    'text': text,
                    'content': content,
                    'headers': dict(response.headers),
                    'url': str(response.url),
                    'ok': response.status < 400
                }
    except Exception as e:
        # Return error response similar to requests
        return {
            'status_code': 0,
            'text': '',
            'content': b'',
            'headers': {},
            'url': url,
            'ok': False,
            'error': str(e)
        }


async def pooled_post(url: str, data: Optional[Any] = None,
                      json: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None,
                      timeout: Optional[float] = None, **kwargs) -> Dict[str, Any]:
    """
    Async POST request using connection pool with requests-like response
    """
    try:
        async with http_pool.get_session() as session:
            request_headers = session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            timeout_config = None
            if timeout:
                import aiohttp
                try:
                    timeout_config = aiohttp.ClientTimeout(total=timeout)
                except RuntimeError:
                    # Handle event loop context issues
                    timeout_config = timeout  # fallback to numeric timeout
            
            async with session.post(
                url,
                data=data,
                json=json,
                headers=request_headers,
                timeout=timeout_config,
                **kwargs
            ) as response:
                content = await response.read()
                text = await response.text()
                
                return {
                    'status_code': response.status,
                    'text': text,
                    'content': content,
                    'headers': dict(response.headers),
                    'url': str(response.url),
                    'ok': response.status < 400
                }
    except Exception as e:
        return {
            'status_code': 0,
            'text': '',
            'content': b'',
            'headers': {},
            'url': url,
            'ok': False,
            'error': str(e)
        }


def sync_pooled_get(url: str, headers: Optional[Dict[str, str]] = None,
                    timeout: Optional[float] = None, **kwargs) -> Dict[str, Any]:
    """
    Synchronous wrapper for pooled_get - uses persistent session for all sync contexts
    Compatible with requests.get() interface
    """
    try:
        # ALWAYS use persistent sync session for sync calls
        # This avoids event loop context issues completely
        session = get_persistent_sync_session()
        
        response = session.get(url, headers=headers, timeout=timeout, **kwargs)
        return {
            'status_code': response.status_code,
            'text': response.text,
            'content': response.content,
            'headers': dict(response.headers),
            'url': str(response.url),
            'ok': response.ok
        }
            
    except Exception as e:
        return {
            'status_code': 0,
            'text': '',
            'content': b'',
            'headers': {},
            'url': url,
            'ok': False,
            'error': str(e)
        }


def sync_pooled_post(url: str, data: Optional[Any] = None,
                     json: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None,
                     timeout: Optional[float] = None, **kwargs) -> Dict[str, Any]:
    """
    Synchronous wrapper for pooled_post - uses persistent session for all sync contexts
    Compatible with requests.post() interface
    """
    try:
        # ALWAYS use persistent sync session for sync calls
        # This avoids event loop context issues completely
        session = get_persistent_sync_session()
        
        response = session.post(url, data=data, json=json, headers=headers, timeout=timeout, **kwargs)
        return {
            'status_code': response.status_code,
            'text': response.text,
            'content': response.content,
            'headers': dict(response.headers),
            'url': str(response.url),
            'ok': response.ok
        }
            
    except Exception as e:
        return {
            'status_code': 0,
            'text': '',
            'content': b'',
            'headers': {},
            'url': url,
            'ok': False,
            'error': str(e)
        }


class PooledResponse:
    """
    Requests-compatible response object for pooled HTTP calls
    """
    def __init__(self, response_data: Dict[str, Any]):
        self.status_code = response_data.get('status_code', 0)
        self.text = response_data.get('text', '')
        self.content = response_data.get('content', b'')
        self.headers = response_data.get('headers', {})
        self.url = response_data.get('url', '')
        self.ok = response_data.get('ok', False)
        self._error = response_data.get('error')
    
    def json(self):
        """Parse JSON response"""
        import json
        try:
            return json.loads(self.text)
        except (json.JSONDecodeError, ValueError):
            return None
    
    def raise_for_status(self):
        """Raise exception for HTTP error status"""
        if not self.ok and self.status_code > 0:
            raise Exception(f"HTTP {self.status_code} Error for url: {self.url}")
        elif self._error:
            raise Exception(f"Request failed: {self._error}")


def requests_compatible_get(url: str, headers: Optional[Dict[str, str]] = None,
                           timeout: Optional[float] = None, **kwargs) -> PooledResponse:
    """
    Drop-in replacement for requests.get() using connection pool
    """
    response_data = sync_pooled_get(url, headers, timeout, **kwargs)
    return PooledResponse(response_data)


def requests_compatible_post(url: str, data: Optional[Any] = None,
                            json: Optional[Dict[str, Any]] = None,
                            headers: Optional[Dict[str, str]] = None,
                            timeout: Optional[float] = None, **kwargs) -> PooledResponse:
    """
    Drop-in replacement for requests.post() using connection pool
    """
    response_data = sync_pooled_post(url, data, json, headers, timeout, **kwargs)
    return PooledResponse(response_data)