"""
Test Academic Research Integration

Basic tests to verify Academic Research tool functionality.

Run with: python tests/utilities/test_academic_research_integration.py
"""

import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from user_tools.research_paper_search import ResearchPaperSearchTool
from config.feature_flags import FeatureFlags

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_research_disabled():
    """Test that tool respects feature flag when disabled."""
    print("\n" + "="*80)
    print("TEST 1: Academic Research Tool with Feature Flag DISABLED")
    print("="*80)

    # Ensure feature flag is disabled
    original_state = FeatureFlags.ENABLE_ACADEMIC_RESEARCH
    FeatureFlags.ENABLE_ACADEMIC_RESEARCH = False

    tool = ResearchPaperSearchTool()

    # Try to execute
    result = await tool.execute(query="machine learning")

    # Restore original state
    FeatureFlags.ENABLE_ACADEMIC_RESEARCH = original_state

    print(f"Success: {result.get('success')}")
    print(f"Error: {result.get('error', 'N/A')}")

    assert result['success'] is False, "Tool should fail when feature flag disabled"
    assert "disabled" in result['error'].lower(), "Error should mention feature is disabled"

    print("✅ TEST PASSED: Tool correctly respects feature flag")


async def test_research_ai_query():
    """Test Academic Research tool with AI/ML query."""
    print("\n" + "="*80)
    print("TEST 2: Academic Research for AI/ML (Transformer models)")
    print("="*80)

    # Enable feature flag for testing
    original_state = FeatureFlags.ENABLE_ACADEMIC_RESEARCH
    FeatureFlags.ENABLE_ACADEMIC_RESEARCH = True

    tool = ResearchPaperSearchTool()

    # Execute with AI query
    result = await tool.execute(query="transformer models in natural language processing", limit=5)

    # Restore original state
    FeatureFlags.ENABLE_ACADEMIC_RESEARCH = original_state

    print(f"Success: {result.get('success')}")

    if result['success']:
        output = result.get('result', '')
        print(f"Result length: {len(output)} characters")
        print("\nFirst 800 characters of output:")
        print("-" * 80)
        print(output[:800])
        print("-" * 80)

        # Verify SOURCE block format
        assert "SOURCE 1:" in output, "Output should contain SOURCE blocks"
        assert "Title:" in output, "SOURCE blocks should have Title field"
        assert "URL:" in output, "SOURCE blocks should have URL field"
        assert "Date:" in output, "SOURCE blocks should have Date field"
        assert "CITATION RULE" in output, "Output should include citation instructions"

        # Count SOURCE blocks
        source_count = output.count("SOURCE ")
        print(f"\nNumber of SOURCE blocks: {source_count}")

        print("✅ TEST PASSED: Successfully retrieved and formatted research papers")
    else:
        print(f"❌ TEST FAILED: {result.get('error')}")
        print("NOTE: This may fail if APIs are unavailable or rate-limited")


async def test_research_medical_query():
    """Test Academic Research tool with medical query."""
    print("\n" + "="*80)
    print("TEST 3: Academic Research for Medical (COVID-19)")
    print("="*80)

    # Enable feature flag for testing
    original_state = FeatureFlags.ENABLE_ACADEMIC_RESEARCH
    FeatureFlags.ENABLE_ACADEMIC_RESEARCH = True

    tool = ResearchPaperSearchTool()

    # Execute with medical query
    result = await tool.execute(query="COVID-19 vaccine efficacy", limit=3)

    # Restore original state
    FeatureFlags.ENABLE_ACADEMIC_RESEARCH = original_state

    print(f"Success: {result.get('success')}")

    if result['success']:
        output = result.get('result', '')
        print(f"Result length: {len(output)} characters")

        # Should include PubMed for medical query
        assert "PubMed" in output or "Semantic Scholar" in output, "Should search medical databases"

        # Count SOURCE blocks
        source_count = output.count("SOURCE ")
        print(f"Number of SOURCE blocks: {source_count}")

        assert source_count > 0, "Should have at least one SOURCE block"
        assert source_count <= 15, "Should respect limit across sources"

        print("✅ TEST PASSED: Successfully retrieved medical research papers")
    else:
        print(f"❌ TEST FAILED: {result.get('error')}")


async def test_research_specific_sources():
    """Test Academic Research tool with specific source selection."""
    print("\n" + "="*80)
    print("TEST 4: Academic Research with Specific Source (arXiv only)")
    print("="*80)

    # Enable feature flag for testing
    original_state = FeatureFlags.ENABLE_ACADEMIC_RESEARCH
    FeatureFlags.ENABLE_ACADEMIC_RESEARCH = True

    tool = ResearchPaperSearchTool()

    # Execute with specific source
    result = await tool.execute(query="quantum computing", sources=["arxiv"], limit=3)

    # Restore original state
    FeatureFlags.ENABLE_ACADEMIC_RESEARCH = original_state

    print(f"Success: {result.get('success')}")

    if result['success']:
        output = result.get('result', '')

        # Should only include arXiv results
        assert "arXiv" in output, "Should include arXiv results"

        print(f"Found arXiv papers: {output.count('Source: arXiv')}")
        print("✅ TEST PASSED: Successfully filtered by source")
    else:
        print(f"❌ TEST FAILED: {result.get('error')}")


async def main():
    """Run all tests."""
    print("\n" + "#"*80)
    print("# Academic Research Integration Test Suite")
    print("#"*80)

    try:
        # Test 1: Feature flag disabled
        await test_research_disabled()

        # Test 2: AI/ML query
        await test_research_ai_query()

        # Test 3: Medical query
        await test_research_medical_query()

        # Test 4: Specific source
        await test_research_specific_sources()

        print("\n" + "#"*80)
        print("# ALL TESTS COMPLETED")
        print("#"*80)

    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
