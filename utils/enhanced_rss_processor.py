"""
Enhanced RSS Processor

Processes RSS feeds with enhanced capabilities:
- Google News RSS integration
- Full article content extraction
- Improved deduplication
- Optional sentiment analysis

All output follows Context Engineering standards for perfect citations.
"""

import feedparser
import aiohttp
import asyncio
import hashlib
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from newspaper import Article
from config.rss_config import EnhancedRSSConfig
import logging
import re

logger = logging.getLogger(__name__)


class EnhancedRSSProcessor:
    """
    Enhanced RSS processor with Google News, content extraction, and deduplication.
    """

    def __init__(self):
        self.config = EnhancedRSSConfig
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.seen_urls: Set[str] = set()
        self.seen_content_hashes: Set[str] = set()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.CONTENT_EXTRACTION_TIMEOUT)
            headers = {
                'User-Agent': self.config.CONTENT_EXTRACTION_USER_AGENT
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session

    async def _close_session(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _rate_limit(self):
        """Enforce rate limiting for content extraction."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.config.CONTENT_EXTRACTION_RATE_LIMIT:
            sleep_time = self.config.CONTENT_EXTRACTION_RATE_LIMIT - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    def fetch_google_news_rss(self, query: str, lang: str = None, country: str = None) -> List[Dict[str, Any]]:
        """
        Fetch articles from Google News RSS.

        Args:
            query: Search query
            lang: Language code (default: en)
            country: Country code (default: US)

        Returns:
            List of article dictionaries
        """
        try:
            lang = lang or self.config.GOOGLE_NEWS_DEFAULT_LANG
            country = country or self.config.GOOGLE_NEWS_DEFAULT_COUNTRY

            # URL-encode the query
            encoded_query = quote_plus(query)

            # Build Google News RSS URL
            url = self.config.GOOGLE_NEWS_SEARCH_URL.format(
                query=encoded_query,
                lang=lang,
                country=country
            )

            logger.info(f"Fetching Google News RSS for query: {query}")

            # Parse RSS feed
            feed = feedparser.parse(url)

            articles = []
            for entry in feed.entries[:self.config.MAX_ARTICLES_PER_FEED]:
                article = {
                    'title': entry.get('title', 'Untitled'),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'published_parsed': entry.get('published_parsed'),
                    'summary': entry.get('summary', ''),
                    'source': entry.get('source', {}).get('title', 'Google News'),
                    'content': '',  # Will be extracted later if enabled
                    'sentiment': None  # Will be analyzed later if enabled
                }
                articles.append(article)

            logger.info(f"Google News: Retrieved {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"Error fetching Google News RSS: {e}")
            return []

    async def extract_article_content(self, url: str) -> Optional[str]:
        """
        Extract full article content from URL.

        Args:
            url: Article URL

        Returns:
            Article content text or None if extraction fails
        """
        if not self.config.ENABLE_CONTENT_EXTRACTION:
            return None

        try:
            await self._rate_limit()

            # Try newspaper3k first (best for news articles)
            try:
                article = Article(url)
                article.download()
                article.parse()

                content = article.text

                # Limit content length
                if len(content) > self.config.MAX_CONTENT_LENGTH:
                    content = content[:self.config.MAX_CONTENT_LENGTH] + "..."

                logger.debug(f"Extracted {len(content)} chars from {url}")
                return content

            except Exception as e:
                logger.debug(f"newspaper3k failed for {url}: {e}")

                # Fallback to BeautifulSoup
                session = await self._get_session()
                async with session.get(url) as response:
                    if response.status != 200:
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Get text
                    text = soup.get_text()

                    # Clean up text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)

                    # Limit length
                    if len(text) > self.config.MAX_CONTENT_LENGTH:
                        text = text[:self.config.MAX_CONTENT_LENGTH] + "..."

                    logger.debug(f"Extracted {len(text)} chars with BeautifulSoup from {url}")
                    return text

        except Exception as e:
            logger.warning(f"Content extraction failed for {url}: {e}")
            return None

    async def extract_content_batch(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract content for multiple articles in parallel.

        Args:
            articles: List of article dictionaries

        Returns:
            Articles with extracted content
        """
        if not self.config.ENABLE_CONTENT_EXTRACTION:
            return articles

        try:
            # Extract content in parallel (with rate limiting)
            tasks = []
            for article in articles:
                if article.get('url'):
                    tasks.append(self.extract_article_content(article['url']))
                else:
                    tasks.append(asyncio.coroutine(lambda: None)())

            contents = await asyncio.gather(*tasks, return_exceptions=True)

            # Update articles with extracted content
            for i, article in enumerate(articles):
                if isinstance(contents[i], str) and contents[i]:
                    article['content'] = contents[i]
                elif self.config.FALLBACK_TO_HEADLINE:
                    article['content'] = article.get('summary', article.get('title', ''))

            return articles

        except Exception as e:
            logger.error(f"Batch content extraction error: {e}")
            return articles
        finally:
            await self._close_session()

    def analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Dict with sentiment, score, and confidence
        """
        if not self.config.ENABLE_SENTIMENT or not text:
            return None

        try:
            if self.config.SENTIMENT_MODEL == 'textblob':
                # Use TextBlob (lightweight)
                try:
                    from textblob import TextBlob
                    blob = TextBlob(text)
                    polarity = blob.sentiment.polarity  # -1 to 1

                    if polarity > 0.1:
                        sentiment = 'positive'
                    elif polarity < -0.1:
                        sentiment = 'negative'
                    else:
                        sentiment = 'neutral'

                    return {
                        'sentiment': sentiment,
                        'score': polarity,
                        'confidence': abs(polarity)
                    }
                except ImportError:
                    logger.warning("textblob not installed, skipping sentiment analysis")
                    return None

            elif self.config.SENTIMENT_MODEL == 'vader':
                # Use VADER (good for social media)
                try:
                    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                    analyzer = SentimentIntensityAnalyzer()
                    scores = analyzer.polarity_scores(text)

                    compound = scores['compound']
                    if compound >= 0.05:
                        sentiment = 'positive'
                    elif compound <= -0.05:
                        sentiment = 'negative'
                    else:
                        sentiment = 'neutral'

                    return {
                        'sentiment': sentiment,
                        'score': compound,
                        'confidence': abs(compound)
                    }
                except ImportError:
                    logger.warning("vaderSentiment not installed, skipping sentiment analysis")
                    return None

        except Exception as e:
            logger.warning(f"Sentiment analysis error: {e}")
            return None

    def deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate articles using multiple methods.

        Args:
            articles: List of article dictionaries

        Returns:
            Deduplicated list of articles
        """
        if not self.config.ENABLE_DEDUPLICATION or not articles:
            return articles

        unique_articles = []
        seen_urls = set()
        seen_titles = set()
        seen_hashes = set()

        for article in articles:
            # URL deduplication
            url = article.get('url', '')
            if self.config.ENABLE_URL_DEDUPLICATION and url:
                # Normalize URL
                normalized_url = url.split('?')[0].lower()  # Remove query params
                if normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url)

            # Title similarity deduplication
            title = article.get('title', '').lower().strip()
            if title:
                # Check against seen titles
                is_duplicate = False
                for seen_title in seen_titles:
                    similarity = SequenceMatcher(None, title, seen_title).ratio()
                    if similarity >= self.config.TITLE_SIMILARITY_THRESHOLD:
                        is_duplicate = True
                        break

                if is_duplicate:
                    continue

                seen_titles.add(title)

            # Content hash deduplication
            content = article.get('content', article.get('summary', ''))
            if self.config.ENABLE_CONTENT_HASH_DEDUPLICATION and content:
                content_hash = hashlib.md5(content.encode()).hexdigest()
                if content_hash in seen_hashes:
                    continue
                seen_hashes.add(content_hash)

            unique_articles.append(article)

        logger.info(f"Deduplication: {len(articles)} -> {len(unique_articles)} articles")
        return unique_articles

    def format_articles_for_context(self, articles: List[Dict[str, Any]], query: str = None) -> str:
        """
        Format articles using Context Engineering standards (SOURCE blocks).

        Args:
            articles: List of article dictionaries
            query: Original search query (optional)

        Returns:
            Formatted string with SOURCE blocks
        """
        output_parts = []

        if query:
            output_parts.append(f"# News Articles for: {query}\n")

        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Untitled')
            url = article.get('url', '')
            published = article.get('published', 'Unknown')
            source = article.get('source', 'Unknown')
            content = article.get('content', article.get('summary', ''))
            sentiment = article.get('sentiment')

            # Build content
            content_parts = []

            if content:
                # Truncate to 500 characters (Context Engineering standard)
                if len(content) > 500:
                    content = content[:497] + "..."
                content_parts.append(content)

            # Add source
            content_parts.append(f"Source: {source}")

            # Add sentiment if available
            if sentiment:
                sentiment_str = f"Sentiment: {sentiment['sentiment'].title()}"
                if sentiment.get('confidence'):
                    sentiment_str += f" (confidence: {sentiment['confidence']:.2f})"
                content_parts.append(sentiment_str)

            formatted_content = "\n".join(content_parts)

            # Format as SOURCE block
            source_block = f"""SOURCE {i}:
Title: {title}
URL: {url}
Date: {published}
{formatted_content}


"""
            output_parts.append(source_block)

        # Add footer
        output_parts.append(f"\nTotal articles: {len(articles)}")
        output_parts.append("\n🔗 CITATION RULE: Use exact Title and URL from each SOURCE block in format [Title](URL)")

        return '\n'.join(output_parts)
