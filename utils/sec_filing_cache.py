"""
SEC Filing Cache

Simple file-based caching for SEC EDGAR data with TTL-based expiration.

This cache is CRITICAL for performance - SEC filings don't change once filed,
so aggressive caching (7 days for CIKs, 24 hours for filings lists) is safe
and dramatically improves response times.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SECFilingCache:
    """
    File-based cache for SEC EDGAR data.

    Uses JSON files in a cache directory with TTL-based expiration.
    Designed for high performance with minimal disk I/O.
    """

    def __init__(self, cache_dir: str = None):
        """
        Initialize cache.

        Args:
            cache_dir: Directory for cache files. Defaults to .cache/sec_edgar/
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.getcwd(), '.cache', 'sec_edgar')

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"SEC filing cache initialized at: {self.cache_dir}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        cache_file = self._get_cache_file_path(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_entry = json.load(f)

            # Check if expired
            expires_at = datetime.fromisoformat(cache_entry['expires_at'])
            if datetime.now() > expires_at:
                logger.debug(f"Cache expired for key: {key}")
                # Delete expired cache file
                cache_file.unlink()
                return None

            logger.debug(f"Cache hit for key: {key}")
            return cache_entry['data']

        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {e}")
            # Delete corrupted cache file
            try:
                cache_file.unlink()
            except:
                pass
            return None

    def set(self, key: str, data: Any, ttl: int = 3600):
        """
        Set value in cache.

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        cache_file = self._get_cache_file_path(key)

        try:
            expires_at = datetime.now() + timedelta(seconds=ttl)

            cache_entry = {
                'data': data,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.now().isoformat()
            }

            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f, indent=2)

            logger.debug(f"Cache set for key: {key} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Error writing cache for key {key}: {e}")

    def delete(self, key: str):
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        cache_file = self._get_cache_file_path(key)

        if cache_file.exists():
            try:
                cache_file.unlink()
                logger.debug(f"Cache deleted for key: {key}")
            except Exception as e:
                logger.warning(f"Error deleting cache for key {key}: {e}")

    def clear(self):
        """Clear all cache files."""
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
            logger.info("SEC filing cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def _get_cache_file_path(self, key: str) -> Path:
        """
        Get cache file path for a key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        # Sanitize key for filesystem (replace special chars with underscores)
        safe_key = key.replace(':', '_').replace('/', '_').replace('\\', '_')
        return self.cache_dir / f"{safe_key}.json"
