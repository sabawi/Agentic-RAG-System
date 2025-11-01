"""
SEC EDGAR API Client

Handles all communication with SEC EDGAR APIs with caching and error handling.

The SEC EDGAR API provides:
- Company filings (10-K, 10-Q, 8-K, etc.)
- Insider trading data (Form 4)
- Institutional holdings (13-F)
- All data is PUBLIC and FREE

Rate Limit: 10 requests/second
Documentation: https://www.sec.gov/edgar/sec-api-documentation
"""

import aiohttp
import asyncio
import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.sec_filing_cache import SECFilingCache
from config.edgar_config import EDGARConfig
import logging

logger = logging.getLogger(__name__)


class SECEdgarClient:
    """
    Client for interacting with SEC EDGAR APIs.

    Features:
    - CIK (Central Index Key) lookup by ticker
    - Filings retrieval with automatic caching
    - Rate limiting compliance (10 req/sec max)
    - Graceful error handling
    """

    def __init__(self):
        self.base_url = EDGARConfig.BASE_URL
        self.headers = EDGARConfig.get_headers()
        self.cache = SECFilingCache()
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.min_request_interval = 0.15  # 150ms between requests = ~6.6 req/sec (well under 10 req/sec limit)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=EDGARConfig.REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )
        return self.session

    async def _close_session(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _rate_limit(self):
        """Enforce rate limiting to comply with SEC's 10 req/sec limit."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_company_filings(self, ticker: str, filing_types: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get company filings (synchronous wrapper for async implementation).

        Args:
            ticker: Stock ticker symbol
            filing_types: List of form types (e.g., ['10-K', '10-Q'])
            limit: Maximum number of filings to return

        Returns:
            List of filing dictionaries
        """
        try:
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # Already in an async context - create a new loop in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._get_company_filings_async(ticker, filing_types, limit)
                    )
                    return future.result()
            except RuntimeError:
                # No event loop running, safe to use asyncio.run
                return asyncio.run(self._get_company_filings_async(ticker, filing_types, limit))
        except Exception as e:
            logger.error(f"Error in get_company_filings: {e}")
            raise

    async def _get_company_filings_async(self, ticker: str, filing_types: List[str], limit: int) -> List[Dict[str, Any]]:
        """
        Async implementation of filings retrieval.
        """
        try:
            # Step 1: Get CIK for ticker
            cik = await self._get_company_cik(ticker)
            if not cik:
                logger.warning(f"Could not find CIK for ticker: {ticker}")
                return []

            # Step 2: Get filings for CIK
            filings = await self._get_filings_by_cik(cik, filing_types, limit)

            return filings

        finally:
            await self._close_session()

    async def _get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get CIK (Central Index Key) for a company ticker.

        The CIK is a unique identifier assigned by the SEC to companies and individuals.

        Args:
            ticker: Stock ticker symbol

        Returns:
            CIK string or None if not found
        """
        # Check cache first
        cache_key = f"cik:{ticker.upper()}"
        cached_cik = self.cache.get(cache_key)
        if cached_cik:
            logger.debug(f"CIK cache hit for {ticker}")
            return cached_cik

        try:
            session = await self._get_session()

            # Method 1: Try direct ticker to CIK mapping file
            # SEC provides a mapping at this endpoint
            try:
                await self._rate_limit()  # Rate limiting
                tickers_url = "https://www.sec.gov/files/company_tickers.json"

                async with session.get(tickers_url) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Search for ticker in the data
                        # The JSON structure is: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
                        for entry in data.values():
                            if entry.get('ticker', '').upper() == ticker.upper():
                                cik = str(entry.get('cik_str', ''))
                                if cik:
                                    # Cache the CIK (TTL: 7 days - CIKs don't change)
                                    self.cache.set(cache_key, cik, ttl=EDGARConfig.CACHE_TTL_CIK)
                                    logger.info(f"Found CIK for {ticker} via tickers.json: {cik}")
                                    return cik
            except Exception as e:
                logger.debug(f"Method 1 (tickers.json) failed: {e}")

            # Method 2: Fallback to browse-edgar search (slower, parses HTML)
            logger.debug(f"Trying browse-edgar fallback for {ticker}")
            await self._rate_limit()  # Rate limiting
            search_url = f"{self.base_url}/cgi-bin/browse-edgar"
            params = {'CIK': ticker, 'owner': 'exclude', 'match': 'ticker'}

            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    # Extract CIK from HTML (format: CIK=XXXXXXXXXX where X is a digit)
                    cik_match = re.search(r'CIK=(\d+)', content)
                    if cik_match:
                        cik = cik_match.group(1)
                        # Cache the CIK (TTL: 7 days)
                        self.cache.set(cache_key, cik, ttl=EDGARConfig.CACHE_TTL_CIK)
                        logger.info(f"Found CIK for {ticker} via browse: {cik}")
                        return cik

            logger.warning(f"Could not find CIK for ticker: {ticker}")
            return None

        except Exception as e:
            logger.error(f"Error fetching CIK for {ticker}: {e}")
            return None

    async def _get_filings_by_cik(self, cik: str, filing_types: List[str], limit: int) -> List[Dict[str, Any]]:
        """
        Get filings for a CIK.

        Args:
            cik: Central Index Key
            filing_types: List of form types to retrieve
            limit: Maximum number of filings

        Returns:
            List of filing dictionaries
        """
        # Check cache first
        cache_key = f"filings:{cik}:{':'.join(sorted(filing_types))}:{limit}"
        cached_filings = self.cache.get(cache_key)
        if cached_filings:
            logger.debug(f"Filings cache hit for CIK {cik}")
            return cached_filings

        try:
            session = await self._get_session()

            # Pad CIK to 10 digits (SEC requirement)
            cik_padded = cik.zfill(10)

            # Get company submissions
            # This endpoint provides all filings for a company
            await self._rate_limit()  # Rate limiting
            submissions_url = f"{self.base_url}/submissions/CIK{cik_padded}.json"

            async with session.get(submissions_url) as response:
                if response.status != 200:
                    logger.error(f"SEC EDGAR API returned status {response.status} for CIK {cik}")
                    return []

                data = await response.json()

                # Extract recent filings
                # Structure: {"filings": {"recent": {"form": [...], "filingDate": [...], ...}}}
                recent_filings = data.get('filings', {}).get('recent', {})

                if not recent_filings:
                    logger.warning(f"No recent filings found for CIK {cik}")
                    return []

                # Build filings list
                filings = []
                forms = recent_filings.get('form', [])

                for i in range(len(forms)):
                    form_type = forms[i]

                    # Filter by requested filing types
                    if form_type in filing_types:
                        filing = {
                            'form': form_type,
                            'filing_date': recent_filings.get('filingDate', [])[i] if i < len(recent_filings.get('filingDate', [])) else None,
                            'accession_number': recent_filings.get('accessionNumber', [])[i] if i < len(recent_filings.get('accessionNumber', [])) else None,
                            'report_date': recent_filings.get('reportDate', [])[i] if i < len(recent_filings.get('reportDate', [])) else None,
                            'description': recent_filings.get('primaryDocDescription', [])[i] if i < len(recent_filings.get('primaryDocDescription', [])) else None,
                            'items': recent_filings.get('items', [])[i] if i < len(recent_filings.get('items', [])) else None,
                            'size': recent_filings.get('size', [])[i] if i < len(recent_filings.get('size', [])) else None,
                        }

                        filings.append(filing)

                        # Stop when we have enough
                        if len(filings) >= limit:
                            break

                # Cache the filings list (TTL: 24 hours - new filings daily)
                self.cache.set(cache_key, filings, ttl=EDGARConfig.CACHE_TTL_FILINGS)

                logger.info(f"Retrieved {len(filings)} filings for CIK {cik}")
                return filings

        except Exception as e:
            logger.error(f"Error fetching filings for CIK {cik}: {e}")
            return []
