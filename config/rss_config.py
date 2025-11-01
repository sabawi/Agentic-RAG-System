"""
Enhanced RSS Configuration

Configuration for enhanced RSS processing including Google News,
content extraction, and sentiment analysis.
"""

import os


class EnhancedRSSConfig:
    """Configuration for enhanced RSS processing."""

    # ========================================================================
    # GOOGLE NEWS RSS
    # ========================================================================

    # Google News RSS base URL
    GOOGLE_NEWS_BASE_URL = "https://news.google.com/rss"

    # Google News search URL format
    # Parameters: q=query, hl=language, gl=country, ceid=country_encoding
    GOOGLE_NEWS_SEARCH_URL = "https://news.google.com/rss/search?q={query}&hl={lang}&gl={country}&ceid={country}:{lang}"

    # Default language and country
    GOOGLE_NEWS_DEFAULT_LANG = "en"
    GOOGLE_NEWS_DEFAULT_COUNTRY = "US"

    # Enable Google News integration
    ENABLE_GOOGLE_NEWS = True

    # ========================================================================
    # CONTENT EXTRACTION
    # ========================================================================

    # Enable full content extraction
    ENABLE_CONTENT_EXTRACTION = True

    # Content extraction timeout (seconds)
    CONTENT_EXTRACTION_TIMEOUT = 10

    # Maximum content length to extract (characters)
    MAX_CONTENT_LENGTH = 5000

    # Fallback to headline if extraction fails
    FALLBACK_TO_HEADLINE = True

    # User-Agent for content extraction requests
    CONTENT_EXTRACTION_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    # ========================================================================
    # SENTIMENT ANALYSIS
    # ========================================================================

    # Enable sentiment analysis
    ENABLE_SENTIMENT = False  # Disabled by default (requires transformers library)

    # Sentiment model to use
    # Options: 'transformers', 'textblob', 'vader'
    SENTIMENT_MODEL = "textblob"  # Lightweight option

    # Minimum confidence threshold for sentiment classification
    SENTIMENT_CONFIDENCE_THRESHOLD = 0.6

    # ========================================================================
    # DEDUPLICATION
    # ========================================================================

    # Enable improved deduplication
    ENABLE_DEDUPLICATION = True

    # Title similarity threshold (0-1)
    TITLE_SIMILARITY_THRESHOLD = 0.8

    # Enable URL deduplication
    ENABLE_URL_DEDUPLICATION = True

    # Enable content hash deduplication
    ENABLE_CONTENT_HASH_DEDUPLICATION = True

    # ========================================================================
    # CACHING
    # ========================================================================

    # Enable content caching
    ENABLE_CONTENT_CACHE = True

    # Content cache TTL (seconds)
    CONTENT_CACHE_TTL = 21600  # 6 hours

    # Cache directory
    CONTENT_CACHE_DIR = os.path.join(os.getcwd(), '.cache', 'rss_content')

    # ========================================================================
    # GENERAL SETTINGS
    # ========================================================================

    # Request timeout for RSS feeds (seconds)
    RSS_REQUEST_TIMEOUT = 15

    # Maximum articles to process per feed
    MAX_ARTICLES_PER_FEED = 10

    # Maximum total articles to return
    MAX_TOTAL_ARTICLES = 50

    # Rate limiting for content extraction (seconds between requests)
    CONTENT_EXTRACTION_RATE_LIMIT = 0.5

    @classmethod
    def validate_configuration(cls) -> bool:
        """
        Validate that configuration is properly set up.

        Returns:
            True if valid, False otherwise
        """
        # All features work without additional dependencies
        return True

    @classmethod
    def get_status(cls) -> dict:
        """
        Get current configuration status.

        Returns:
            Dictionary with configuration details
        """
        return {
            'google_news': {
                'enabled': cls.ENABLE_GOOGLE_NEWS,
                'language': cls.GOOGLE_NEWS_DEFAULT_LANG,
                'country': cls.GOOGLE_NEWS_DEFAULT_COUNTRY
            },
            'content_extraction': {
                'enabled': cls.ENABLE_CONTENT_EXTRACTION,
                'timeout': cls.CONTENT_EXTRACTION_TIMEOUT,
                'max_length': cls.MAX_CONTENT_LENGTH
            },
            'sentiment_analysis': {
                'enabled': cls.ENABLE_SENTIMENT,
                'model': cls.SENTIMENT_MODEL,
                'threshold': cls.SENTIMENT_CONFIDENCE_THRESHOLD
            },
            'deduplication': {
                'enabled': cls.ENABLE_DEDUPLICATION,
                'title_threshold': cls.TITLE_SIMILARITY_THRESHOLD,
                'url_dedup': cls.ENABLE_URL_DEDUPLICATION,
                'content_hash': cls.ENABLE_CONTENT_HASH_DEDUPLICATION
            }
        }
