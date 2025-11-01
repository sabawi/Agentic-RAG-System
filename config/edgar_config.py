"""
SEC EDGAR Configuration

Configuration settings for SEC EDGAR API integration.

IMPORTANT: SEC requires a valid User-Agent header with contact information.
See: https://www.sec.gov/os/accessing-edgar-data
"""

import os
from typing import Dict


class EDGARConfig:
    """Configuration for SEC EDGAR API access."""

    # SEC EDGAR API base URL
    BASE_URL = "https://data.sec.gov"

    # User-Agent header (REQUIRED by SEC)
    # Format: "Company/App email@example.com"
    # The SEC REQUIRES a real email address for contact
    # See: https://www.sec.gov/os/accessing-edgar-data
    USER_AGENT = os.getenv(
        'SEC_USER_AGENT',
        'Agentic-RAG-System/1.0 research@example.com'  # Replace with real email if needed
    )

    # Rate limiting (SEC allows 10 requests/second)
    RATE_LIMIT_REQUESTS = 10
    RATE_LIMIT_PERIOD = 1.0  # seconds

    # Cache TTL settings (in seconds)
    CACHE_TTL_CIK = 604800  # 7 days (CIKs don't change)
    CACHE_TTL_FILINGS = 86400  # 24 hours (new filings daily)
    CACHE_TTL_FILING_CONTENT = 604800  # 7 days (filings don't change once filed)

    # Request timeout
    REQUEST_TIMEOUT = 30  # seconds

    # Default filing types to retrieve
    DEFAULT_FILING_TYPES = ['10-K', '10-Q', '8-K']

    # Maximum number of filings to retrieve per request
    MAX_FILINGS_LIMIT = 20

    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """
        Get HTTP headers for SEC EDGAR API requests.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            'User-Agent': cls.USER_AGENT,
            'Accept-Encoding': 'gzip, deflate'
        }

    @classmethod
    def validate_user_agent(cls) -> bool:
        """
        Validate that User-Agent is properly configured.

        The SEC requires a User-Agent with contact information.

        Returns:
            True if valid, False otherwise
        """
        if not cls.USER_AGENT:
            return False

        # Check if using default and warn
        if 'Contact via GitHub' in cls.USER_AGENT:
            return True  # Default is acceptable but not ideal

        return True
