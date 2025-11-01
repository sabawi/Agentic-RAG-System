"""
Test SEC EDGAR Integration

Basic tests to verify SEC EDGAR tool functionality.

Run with: python tests/utilities/test_sec_edgar_integration.py
"""

import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from user_tools.sec_edgar_tool import SECEdgarTool
from config.feature_flags import FeatureFlags

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_sec_edgar_disabled():
    """Test that tool respects feature flag when disabled."""
    print("\n" + "="*80)
    print("TEST 1: SEC EDGAR Tool with Feature Flag DISABLED")
    print("="*80)

    # Ensure feature flag is disabled
    original_state = FeatureFlags.ENABLE_SEC_EDGAR
    FeatureFlags.ENABLE_SEC_EDGAR = False

    tool = SECEdgarTool()

    # Try to execute
    result = await tool.execute(ticker="AAPL")

    # Restore original state
    FeatureFlags.ENABLE_SEC_EDGAR = original_state

    print(f"Success: {result.get('success')}")
    print(f"Error: {result.get('error', 'N/A')}")

    assert result['success'] is False, "Tool should fail when feature flag disabled"
    assert "disabled" in result['error'].lower(), "Error should mention feature is disabled"

    print("✅ TEST PASSED: Tool correctly respects feature flag")


async def test_sec_edgar_enabled_tesla():
    """Test SEC EDGAR tool with Tesla (TSLA)."""
    print("\n" + "="*80)
    print("TEST 2: SEC EDGAR Tool for TSLA (Tesla)")
    print("="*80)

    # Enable feature flag for testing
    original_state = FeatureFlags.ENABLE_SEC_EDGAR
    FeatureFlags.ENABLE_SEC_EDGAR = True

    tool = SECEdgarTool()

    # Execute with TSLA
    result = await tool.execute(ticker="TSLA", filing_types=["10-K", "10-Q"], limit=3)

    # Restore original state
    FeatureFlags.ENABLE_SEC_EDGAR = original_state

    print(f"Success: {result.get('success')}")

    if result['success']:
        output = result.get('result', '')
        print(f"Result length: {len(output)} characters")
        print("\nFirst 500 characters of output:")
        print("-" * 80)
        print(output[:500])
        print("-" * 80)

        # Verify SOURCE block format
        assert "SOURCE 1:" in output, "Output should contain SOURCE blocks"
        assert "Title:" in output, "SOURCE blocks should have Title field"
        assert "URL:" in output, "SOURCE blocks should have URL field"
        assert "Date:" in output, "SOURCE blocks should have Date field"
        assert "CITATION RULE" in output, "Output should include citation instructions"

        print("✅ TEST PASSED: Successfully retrieved and formatted TSLA filings")
    else:
        print(f"❌ TEST FAILED: {result.get('error')}")
        print("NOTE: This may fail if SEC API is unavailable or ticker is invalid")


async def test_sec_edgar_enabled_apple():
    """Test SEC EDGAR tool with Apple (AAPL)."""
    print("\n" + "="*80)
    print("TEST 3: SEC EDGAR Tool for AAPL (Apple)")
    print("="*80)

    # Enable feature flag for testing
    original_state = FeatureFlags.ENABLE_SEC_EDGAR
    FeatureFlags.ENABLE_SEC_EDGAR = True

    tool = SECEdgarTool()

    # Execute with AAPL
    result = await tool.execute(ticker="AAPL", limit=5)

    # Restore original state
    FeatureFlags.ENABLE_SEC_EDGAR = original_state

    print(f"Success: {result.get('success')}")

    if result['success']:
        output = result.get('result', '')
        print(f"Result length: {len(output)} characters")

        # Count SOURCE blocks
        source_count = output.count("SOURCE ")
        print(f"Number of SOURCE blocks: {source_count}")

        assert source_count > 0, "Should have at least one SOURCE block"
        assert source_count <= 5, "Should respect limit parameter"

        print("✅ TEST PASSED: Successfully retrieved and formatted AAPL filings")
    else:
        print(f"❌ TEST FAILED: {result.get('error')}")


async def test_sec_edgar_invalid_ticker():
    """Test SEC EDGAR tool with invalid ticker."""
    print("\n" + "="*80)
    print("TEST 4: SEC EDGAR Tool with Invalid Ticker")
    print("="*80)

    # Enable feature flag for testing
    original_state = FeatureFlags.ENABLE_SEC_EDGAR
    FeatureFlags.ENABLE_SEC_EDGAR = True

    tool = SECEdgarTool()

    # Execute with invalid ticker
    result = await tool.execute(ticker="INVALIDTICKER123", limit=3)

    # Restore original state
    FeatureFlags.ENABLE_SEC_EDGAR = original_state

    print(f"Success: {result.get('success')}")
    if not result['success']:
        print(f"Error (expected): {result.get('error')}")

    # Invalid ticker should fail gracefully
    assert result['success'] is False, "Invalid ticker should fail"

    print("✅ TEST PASSED: Invalid ticker handled gracefully")


async def main():
    """Run all tests."""
    print("\n" + "#"*80)
    print("# SEC EDGAR Integration Test Suite")
    print("#"*80)

    try:
        # Test 1: Feature flag disabled
        await test_sec_edgar_disabled()

        # Test 2: TSLA filings
        await test_sec_edgar_enabled_tesla()

        # Test 3: AAPL filings
        await test_sec_edgar_enabled_apple()

        # Test 4: Invalid ticker
        await test_sec_edgar_invalid_ticker()

        print("\n" + "#"*80)
        print("# ALL TESTS COMPLETED")
        print("#"*80)

    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
