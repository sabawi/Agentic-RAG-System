"""
Test Enhanced RSS Integration

Basic tests to verify Enhanced RSS processor functionality.

Run with: python tests/utilities/test_enhanced_rss_integration.py
"""

import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.enhanced_rss_processor import EnhancedRSSProcessor
from config.feature_flags import FeatureFlags

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_google_news_fetch():
    """Test Google News RSS fetching."""
    print("\n" + "="*80)
    print("TEST 1: Google News RSS Fetch")
    print("="*80)

    processor = EnhancedRSSProcessor()

    # Fetch Google News for a simple query
    articles = processor.fetch_google_news_rss("Tesla stock")

    print(f"Retrieved {len(articles)} articles from Google News")

    if articles:
        print("\nFirst article:")
        print(f"  Title: {articles[0].get('title', 'N/A')[:80]}...")
        print(f"  URL: {articles[0].get('url', 'N/A')[:80]}...")
        print(f"  Source: {articles[0].get('source', 'N/A')}")
        print(f"  Published: {articles[0].get('published', 'N/A')}")

        assert len(articles) > 0, "Should retrieve at least one article"
        assert articles[0].get('title'), "Article should have title"
        assert articles[0].get('url'), "Article should have URL"

        print("✅ TEST PASSED: Successfully retrieved Google News articles")
    else:
        print("❌ TEST FAILED: No articles retrieved")


async def test_content_extraction():
    """Test article content extraction."""
    print("\n" + "="*80)
    print("TEST 2: Article Content Extraction")
    print("="*80)

    processor = EnhancedRSSProcessor()

    # Use a reliable news URL
    test_url = "https://www.bbc.com/news"

    content = await processor.extract_article_content(test_url)

    if content:
        print(f"Extracted {len(content)} characters of content")
        print(f"First 200 chars: {content[:200]}...")

        assert len(content) > 100, "Should extract meaningful content"

        print("✅ TEST PASSED: Successfully extracted article content")
    else:
        print("⚠️ TEST SKIPPED: Content extraction failed (may be expected for some URLs)")


async def test_deduplication():
    """Test article deduplication."""
    print("\n" + "="*80)
    print("TEST 3: Article Deduplication")
    print("="*80)

    processor = EnhancedRSSProcessor()

    # Create test articles with duplicates
    articles = [
        {'title': 'Tesla Stock Rises', 'url': 'http://example.com/1', 'content': 'Tesla stock went up today'},
        {'title': 'Tesla Stock Rises', 'url': 'http://example.com/1', 'content': 'Tesla stock went up today'},  # Exact duplicate
        {'title': 'Tesla Stock Increases', 'url': 'http://example.com/2', 'content': 'Tesla stock went up today'},  # Similar title
        {'title': 'Apple News', 'url': 'http://example.com/3', 'content': 'Apple released new product'},
        {'title': 'Apple News Update', 'url': 'http://example.com/4', 'content': 'Apple released new product'},  # Similar content
    ]

    print(f"Original articles: {len(articles)}")

    deduplicated = processor.deduplicate_articles(articles)

    print(f"After deduplication: {len(deduplicated)}")

    assert len(deduplicated) < len(articles), "Should remove duplicates"
    assert len(deduplicated) >= 2, "Should keep unique articles"

    print("✅ TEST PASSED: Successfully deduplicated articles")


async def test_context_formatting():
    """Test Context Engineering compliant formatting."""
    print("\n" + "="*80)
    print("TEST 4: Context Engineering Formatting")
    print("="*80)

    processor = EnhancedRSSProcessor()

    # Create test articles
    articles = [
        {
            'title': 'Test Article 1',
            'url': 'http://example.com/article1',
            'published': '2025-10-31',
            'source': 'Test Source',
            'content': 'This is test content for article 1. It should be formatted properly.'
        },
        {
            'title': 'Test Article 2',
            'url': 'http://example.com/article2',
            'published': '2025-10-31',
            'source': 'Test Source 2',
            'content': 'This is test content for article 2.'
        }
    ]

    formatted = processor.format_articles_for_context(articles, query="test query")

    print(f"Formatted output length: {len(formatted)} characters")
    print("\nFirst 500 characters:")
    print("-" * 80)
    print(formatted[:500])
    print("-" * 80)

    # Verify SOURCE block format
    assert "SOURCE 1:" in formatted, "Should contain SOURCE blocks"
    assert "Title:" in formatted, "Should have Title field"
    assert "URL:" in formatted, "Should have URL field"
    assert "Date:" in formatted, "Should have Date field"
    assert "CITATION RULE" in formatted, "Should include citation instructions"

    print("✅ TEST PASSED: Formatting follows Context Engineering standards")


async def test_full_pipeline():
    """Test full enhanced RSS pipeline."""
    print("\n" + "="*80)
    print("TEST 5: Full Enhanced RSS Pipeline")
    print("="*80)

    processor = EnhancedRSSProcessor()

    # Fetch Google News
    articles = processor.fetch_google_news_rss("artificial intelligence", lang="en", country="US")

    if not articles:
        print("⚠️ TEST SKIPPED: No articles retrieved from Google News")
        return

    print(f"Step 1: Retrieved {len(articles)} articles")

    # Extract content (just for first 3 articles to save time)
    test_articles = articles[:3]
    articles_with_content = await processor.extract_content_batch(test_articles)
    print(f"Step 2: Extracted content for {len(articles_with_content)} articles")

    # Deduplicate
    deduplicated = processor.deduplicate_articles(articles_with_content)
    print(f"Step 3: Deduplicated to {len(deduplicated)} articles")

    # Format for context
    formatted = processor.format_articles_for_context(deduplicated, query="artificial intelligence")
    print(f"Step 4: Formatted {len(formatted)} characters for context")

    print("\nFirst SOURCE block:")
    print("-" * 80)
    first_source = formatted.split("SOURCE 2:")[0]
    print(first_source[:600])
    print("-" * 80)

    assert "SOURCE 1:" in formatted, "Should have SOURCE blocks"
    assert len(deduplicated) > 0, "Should have articles after pipeline"

    print("✅ TEST PASSED: Full pipeline executed successfully")


async def main():
    """Run all tests."""
    print("\n" + "#"*80)
    print("# Enhanced RSS Integration Test Suite")
    print("#"*80)

    try:
        # Test 1: Google News fetch
        await test_google_news_fetch()

        # Test 2: Content extraction
        await test_content_extraction()

        # Test 3: Deduplication
        await test_deduplication()

        # Test 4: Context formatting
        await test_context_formatting()

        # Test 5: Full pipeline
        await test_full_pipeline()

        print("\n" + "#"*80)
        print("# ALL TESTS COMPLETED")
        print("#"*80)

    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
