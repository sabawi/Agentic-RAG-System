"""
Academic Research APIs Configuration

Configuration settings for Semantic Scholar, arXiv, and PubMed APIs.

All APIs are FREE with generous rate limits.
"""

import os


class AcademicConfig:
    """Configuration for academic research APIs."""

    # ========================================================================
    # SEMANTIC SCHOLAR API
    # ========================================================================
    # Docs: https://api.semanticscholar.org/api-docs/

    SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"
    SEMANTIC_SCHOLAR_API_KEY = os.getenv('SEMANTIC_SCHOLAR_API_KEY')  # Optional but increases rate limit

    # Rate limits:
    # - Without API key: 100 requests per 5 minutes
    # - With API key: 1 request per second (higher limits available)
    SEMANTIC_SCHOLAR_RATE_LIMIT = 1.0  # seconds between requests

    # Default fields to retrieve
    SEMANTIC_SCHOLAR_FIELDS = [
        'paperId',
        'title',
        'abstract',
        'year',
        'authors',
        'citationCount',
        'influentialCitationCount',
        'url',
        'openAccessPdf',
        'publicationDate',
        'journal',
        'publicationTypes'
    ]

    # Default result limit
    SEMANTIC_SCHOLAR_DEFAULT_LIMIT = 10

    # ========================================================================
    # ARXIV API
    # ========================================================================
    # Docs: https://info.arxiv.org/help/api/index.html

    ARXIV_BASE_URL = "http://export.arxiv.org/api/query"

    # Rate limits: No official limit, but be respectful (recommended: 1 req/3 sec)
    ARXIV_RATE_LIMIT = 3.0  # seconds between requests

    # Default result limit
    ARXIV_DEFAULT_LIMIT = 10

    # Sort order: relevance, lastUpdatedDate, submittedDate
    ARXIV_DEFAULT_SORT = "relevance"

    # ========================================================================
    # PUBMED API (E-utilities)
    # ========================================================================
    # Docs: https://www.ncbi.nlm.nih.gov/books/NBK25501/

    PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    PUBMED_API_KEY = os.getenv('PUBMED_API_KEY')  # Optional but increases rate limit

    # Rate limits:
    # - Without API key: 3 requests per second
    # - With API key: 10 requests per second
    PUBMED_RATE_LIMIT = 0.35 if PUBMED_API_KEY else 0.4  # seconds between requests

    # Default result limit
    PUBMED_DEFAULT_LIMIT = 10

    # Database to search (usually pubmed)
    PUBMED_DATABASE = "pubmed"

    # Return format
    PUBMED_RETURN_MODE = "xml"

    # ========================================================================
    # GENERAL SETTINGS
    # ========================================================================

    # Request timeout (seconds)
    REQUEST_TIMEOUT = 30

    # Cache TTL for search results (in seconds)
    CACHE_TTL_SEARCH_RESULTS = 3600  # 1 hour (results change frequently)

    # Maximum results to return per source
    MAX_RESULTS_PER_SOURCE = 20

    # User-Agent for API requests
    USER_AGENT = "Agentic-RAG-System/1.0 (Academic Research; research@example.com)"

    @classmethod
    def get_headers(cls, api: str = None) -> dict:
        """
        Get HTTP headers for API requests.

        Args:
            api: API name ('semantic_scholar', 'arxiv', 'pubmed')

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            'User-Agent': cls.USER_AGENT,
            'Accept': 'application/json'
        }

        # Add API-specific headers
        if api == 'semantic_scholar' and cls.SEMANTIC_SCHOLAR_API_KEY:
            headers['x-api-key'] = cls.SEMANTIC_SCHOLAR_API_KEY
        elif api == 'arxiv':
            headers['Accept'] = 'application/atom+xml'
        elif api == 'pubmed':
            headers['Accept'] = 'application/xml'

        return headers

    @classmethod
    def validate_configuration(cls) -> bool:
        """
        Validate that configuration is properly set up.

        Returns:
            True if valid, False otherwise
        """
        # All APIs work without API keys, so always valid
        return True

    @classmethod
    def get_status(cls) -> dict:
        """
        Get current configuration status.

        Returns:
            Dictionary with configuration details
        """
        return {
            'semantic_scholar': {
                'api_key_configured': bool(cls.SEMANTIC_SCHOLAR_API_KEY),
                'rate_limit': cls.SEMANTIC_SCHOLAR_RATE_LIMIT,
                'default_limit': cls.SEMANTIC_SCHOLAR_DEFAULT_LIMIT
            },
            'arxiv': {
                'rate_limit': cls.ARXIV_RATE_LIMIT,
                'default_limit': cls.ARXIV_DEFAULT_LIMIT
            },
            'pubmed': {
                'api_key_configured': bool(cls.PUBMED_API_KEY),
                'rate_limit': cls.PUBMED_RATE_LIMIT,
                'default_limit': cls.PUBMED_DEFAULT_LIMIT
            }
        }
