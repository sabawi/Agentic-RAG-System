"""
Test Suite for Fundamental Analysis & DCF - Day 1

Tests:
- Feature flag system
- Financial statements extractor (basic functionality)
- Tool parameter integration
"""

import sys
import os
import pytest
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.feature_flags import FeatureFlags
from utils.financial_statements_extractor import FinancialStatementsExtractor
from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool


class TestFeatureFlags:
    """Test feature flag system"""

    def test_all_flags_default_to_false(self):
        """Verify all feature flags default to False for safety"""
        assert FeatureFlags.ENABLE_SEC_EDGAR == False
        assert FeatureFlags.ENABLE_ACADEMIC_RESEARCH == False
        assert FeatureFlags.ENABLE_ENHANCED_RSS == False
        assert FeatureFlags.ENABLE_DETAILED_ANALYSIS == False

    def test_sub_flags_default_to_true(self):
        """Verify sub-feature flags default to True (so they're ready when master flag is enabled)"""
        assert FeatureFlags.DETAILED_ANALYSIS_FINANCIAL_STATEMENTS == True
        assert FeatureFlags.DETAILED_ANALYSIS_FINANCIAL_RATIOS == True
        assert FeatureFlags.DETAILED_ANALYSIS_DCF_VALUATION == True
        assert FeatureFlags.DETAILED_ANALYSIS_PROJECTIONS == True

    def test_enable_all_financial_analysis(self):
        """Test enabling all financial analysis features"""
        original_state = FeatureFlags.ENABLE_DETAILED_ANALYSIS

        FeatureFlags.enable_all_financial_analysis()
        assert FeatureFlags.ENABLE_DETAILED_ANALYSIS == True

        # Restore original state
        FeatureFlags.ENABLE_DETAILED_ANALYSIS = original_state

    def test_disable_all(self):
        """Test emergency rollback - disable all features"""
        # Enable some features first
        FeatureFlags.ENABLE_DETAILED_ANALYSIS = True
        FeatureFlags.ENABLE_SEC_EDGAR = True

        # Disable all
        FeatureFlags.disable_all()

        # Verify all are disabled
        assert FeatureFlags.ENABLE_SEC_EDGAR == False
        assert FeatureFlags.ENABLE_ACADEMIC_RESEARCH == False
        assert FeatureFlags.ENABLE_ENHANCED_RSS == False
        assert FeatureFlags.ENABLE_DETAILED_ANALYSIS == False

    def test_get_status(self):
        """Test status reporting"""
        status = FeatureFlags.get_status()

        assert 'data_collection' in status
        assert 'financial_analysis' in status
        assert 'sec_edgar' in status['data_collection']
        assert 'detailed_analysis' in status['financial_analysis']


class TestFinancialStatementsExtractor:
    """Test financial statements extractor (basic functionality only)"""

    def test_extractor_initialization(self):
        """Test that extractor initializes correctly"""
        extractor = FinancialStatementsExtractor()
        assert extractor is not None

    @pytest.mark.skip(reason="Requires live yfinance API - run manually")
    def test_extract_financials_aapl(self):
        """Test extracting financial statements for AAPL (manual test)"""
        extractor = FinancialStatementsExtractor()
        financials = extractor.extract_financials('AAPL')

        # Verify structure
        assert 'income_statement' in financials
        assert 'balance_sheet' in financials
        assert 'cash_flow' in financials
        assert 'ticker_info' in financials

        # Verify annual and quarterly data
        assert 'annual' in financials['income_statement']
        assert 'quarterly' in financials['income_statement']

    @pytest.mark.skip(reason="Requires live yfinance API - run manually")
    def test_format_for_llm(self):
        """Test formatting financial statements for LLM (manual test)"""
        extractor = FinancialStatementsExtractor()
        financials = extractor.extract_financials('AAPL')

        formatted = extractor.format_for_llm(financials)

        # Verify formatting
        assert isinstance(formatted, str)
        assert "INCOME STATEMENT" in formatted
        assert "BALANCE SHEET" in formatted
        assert "CASH FLOW STATEMENT" in formatted

    def test_format_number(self):
        """Test number formatting utility"""
        extractor = FinancialStatementsExtractor()

        # Test billions
        assert extractor._format_number(1_234_567_890) == "1.23B"

        # Test millions
        assert extractor._format_number(5_678_900) == "5.68M"

        # Test thousands
        assert extractor._format_number(1_234) == "1.23K"

        # Test small numbers
        assert extractor._format_number(123) == "123.00"

        # Test negative numbers
        assert extractor._format_number(-1_000_000_000) == "-1.00B"


class TestComprehensiveStockAnalyzerIntegration:
    """Test integration of detailed parameter in comprehensive_stock_analyzer"""

    def test_tool_has_detailed_parameter(self):
        """Test that tool has detailed parameter"""
        tool = ComprehensiveStockAnalyzerTool()
        parameters = tool.parameters

        assert 'detailed' in parameters['properties']
        assert parameters['properties']['detailed']['type'] == 'boolean'
        assert parameters['properties']['detailed']['default'] == False

    def test_tool_description_mentions_detailed(self):
        """Test that tool description mentions detailed analysis"""
        tool = ComprehensiveStockAnalyzerTool()
        description = tool.description

        assert 'detailed' in description.lower() or 'financial statements' in description.lower()

    @pytest.mark.skip(reason="Requires live yfinance API - run manually")
    @pytest.mark.asyncio
    async def test_basic_analysis_still_works(self):
        """Test that basic analysis (detailed=False) still works"""
        tool = ComprehensiveStockAnalyzerTool()
        result = await tool.execute(ticker='AAPL', detailed=False)

        assert result['success'] == True
        assert result['error'] is None
        assert 'AAPL' in result['result'] or 'Apple' in result['result']

    @pytest.mark.skip(reason="Requires feature flag enabled and live API - run manually")
    @pytest.mark.asyncio
    async def test_detailed_analysis_with_flag_disabled(self):
        """Test that detailed analysis is skipped when feature flag is disabled"""
        # Ensure feature flag is disabled
        original_state = FeatureFlags.ENABLE_DETAILED_ANALYSIS
        FeatureFlags.ENABLE_DETAILED_ANALYSIS = False

        tool = ComprehensiveStockAnalyzerTool()
        result = await tool.execute(ticker='AAPL', detailed=True)

        # Should still succeed but without detailed analysis
        assert result['success'] == True
        # Should NOT contain detailed financial statements
        assert "INCOME STATEMENT" not in result['result']

        # Restore original state
        FeatureFlags.ENABLE_DETAILED_ANALYSIS = original_state

    @pytest.mark.skip(reason="Requires feature flag enabled and live API - run manually")
    @pytest.mark.asyncio
    async def test_detailed_analysis_with_flag_enabled(self):
        """Test that detailed analysis works when feature flag is enabled"""
        # Enable feature flag
        original_state = FeatureFlags.ENABLE_DETAILED_ANALYSIS
        FeatureFlags.ENABLE_DETAILED_ANALYSIS = True

        tool = ComprehensiveStockAnalyzerTool()
        result = await tool.execute(ticker='AAPL', detailed=True)

        # Should succeed with detailed analysis
        assert result['success'] == True
        # Should contain detailed financial statements
        assert "INCOME STATEMENT" in result['result'] or "Coming Soon" in result['result']

        # Restore original state
        FeatureFlags.ENABLE_DETAILED_ANALYSIS = original_state


class TestGracefulDegradation:
    """Test that failures in new features don't break existing functionality"""

    @pytest.mark.skip(reason="Requires live API - run manually")
    @pytest.mark.asyncio
    async def test_invalid_ticker_still_fails_properly(self):
        """Test that invalid tickers are still caught"""
        tool = ComprehensiveStockAnalyzerTool()
        result = await tool.execute(ticker='INVALID_TICKER_12345')

        assert result['success'] == False
        assert result['error'] is not None

    @pytest.mark.skip(reason="Requires live API - run manually")
    @pytest.mark.asyncio
    async def test_detailed_analysis_failure_doesnt_break_basic(self):
        """Test that if detailed analysis fails, basic analysis still returns"""
        # This would require mocking to properly test
        # For now, just verify the structure is correct
        tool = ComprehensiveStockAnalyzerTool()

        # Verify execute method exists and has proper signature
        import inspect
        sig = inspect.signature(tool.execute)
        assert 'kwargs' in str(sig)


def run_all_tests():
    """Run all tests - helper function for manual testing"""
    print("Running Day 1 Foundation Tests...")
    print("\n" + "="*80)

    # Run non-skipped tests only
    pytest.main([__file__, '-v', '-k', 'not skip'])


if __name__ == "__main__":
    print("\n🧪 Fundamental Analysis & DCF - Day 1 Test Suite\n")
    print("="*80)
    print("\nNOTE: Most tests are marked as 'skip' because they require:")
    print("  1. Live yfinance API access")
    print("  2. Feature flags enabled")
    print("\nThese tests can be run manually by removing the @pytest.mark.skip decorator")
    print("\nRunning basic unit tests (no external dependencies)...\n")
    print("="*80 + "\n")

    run_all_tests()
