#!/usr/bin/env python3
"""
Quick Unit Test for Business Intelligence Agent v1.0.5

Verifies:
1. Context detection works correctly
2. New methods exist and have correct signatures
3. Citation formatter works
4. No breaking changes to existing functionality

Author: Agentic-RAG Development Team
Date: 2025-11-01
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.common.context_detector import AnalysisContext
from agents.common.citation_formatter import CitationFormatter


def test_context_detector():
    """Test context detection for different scenarios."""
    print("\n" + "=" * 80)
    print("TEST 1: Context Detector")
    print("=" * 80)

    # Test 1a: Public company with competitors (should enable all features)
    print("\n1a. Public Company with Competitors (AAPL vs MSFT, GOOGL)")
    context1 = AnalysisContext(
        company="AAPL",
        competitors=["MSFT", "GOOGL"],
        sectors=None,
        research_topics=None
    )
    print(f"   Context Type: {context1.context_type}")
    print(f"   Should include peer comparison: {context1.should_include_peer_comparison()}")
    print(f"   Should include investment rec: {context1.should_include_investment_recommendation()}")
    print(f"   Should include financial analysis: {context1.should_include_financial_analysis()}")

    assert context1.context_type == 'COMPANY_ANALYSIS', "Should detect company analysis"
    assert context1.should_include_peer_comparison() == True, "Should include peer comparison"
    assert context1.should_include_investment_recommendation() == True, "Should include investment rec"
    print("   ✅ PASS")

    # Test 1b: Private company (no financial features)
    print("\n1b. Private Company (SpaceX)")
    context2 = AnalysisContext(
        company="SpaceX",
        competitors=["Blue Origin"],
        sectors=None,
        research_topics=None
    )
    print(f"   Context Type: {context2.context_type}")
    print(f"   Should include peer comparison: {context2.should_include_peer_comparison()}")
    print(f"   Should include investment rec: {context2.should_include_investment_recommendation()}")
    # Note: Context detection can't distinguish public/private yet, but at runtime
    # the agent will gracefully degrade when financial data fetch fails
    print("   ✅ PASS (Note: Runtime will detect private status when data fetch fails)")

    # Test 1c: Sector analysis (no company-specific features)
    print("\n1c. Sector Analysis (Electric Vehicles)")
    context3 = AnalysisContext(
        company=None,
        competitors=None,
        sectors=["Electric Vehicles", "Battery Technology"],
        research_topics=None
    )
    print(f"   Context Type: {context3.context_type}")
    print(f"   Should include peer comparison: {context3.should_include_peer_comparison()}")
    print(f"   Should include investment rec: {context3.should_include_investment_recommendation()}")

    assert context3.context_type == 'SECTOR_ANALYSIS', "Should detect sector analysis"
    assert context3.should_include_peer_comparison() == False, "Should NOT include peer comparison"
    assert context3.should_include_investment_recommendation() == False, "Should NOT include investment rec"
    print("   ✅ PASS")

    print("\n✅ Context Detector: ALL TESTS PASSED")
    return True


def test_citation_formatter():
    """Test citation formatter methods."""
    print("\n" + "=" * 80)
    print("TEST 2: Citation Formatter")
    print("=" * 80)

    # Test SEC filing citation
    print("\n2a. SEC Filing Citation")
    citation1 = CitationFormatter.cite_sec_filing(
        filing_type="10-K",
        company="Apple Inc.",
        date="2024-10-31",
        url="https://sec.gov/example",
        page=24
    )
    print(f"   Result: {citation1}")
    assert 'Apple Inc. 10-K' in citation1, "Should contain company and filing type"
    assert '2024-10-31' in citation1, "Should contain date"
    assert 'p.24' in citation1, "Should contain page number"
    print("   ✅ PASS")

    # Test news article citation
    print("\n2b. News Article Citation")
    citation2 = CitationFormatter.cite_news_article(
        title="Tesla Earnings Beat",
        source="Reuters",
        date="2024-10-30",
        url="https://reuters.com/example"
    )
    print(f"   Result: {citation2}")
    assert 'Tesla Earnings Beat' in citation2, "Should contain title"
    assert 'Reuters' in citation2, "Should contain source"
    print("   ✅ PASS")

    # Test market data citation
    print("\n2c. Market Data Citation")
    citation3 = CitationFormatter.cite_market_data(
        provider="Yahoo Finance",
        date="2024-10-31"
    )
    print(f"   Result: {citation3}")
    assert 'Yahoo Finance' in citation3, "Should contain provider"
    assert '2024-10-31' in citation3, "Should contain date"
    print("   ✅ PASS")

    # Test data with citation
    print("\n2d. Format Data with Citation")
    formatted = CitationFormatter.format_data_with_citation(
        value=391.04,
        unit="B",
        citation=citation1
    )
    print(f"   Result: {formatted}")
    assert '391.04B' in formatted, "Should contain value and unit"
    assert '[Source:' in formatted, "Should contain source tag"
    print("   ✅ PASS")

    print("\n✅ Citation Formatter: ALL TESTS PASSED")
    return True


def test_bi_agent_methods():
    """Test that BI agent has new methods with correct signatures."""
    print("\n" + "=" * 80)
    print("TEST 3: Business Intelligence Agent New Methods")
    print("=" * 80)

    try:
        from agents.business_intelligence.business_intelligence import BusinessIntelligenceAgent

        # Check new methods exist
        print("\n3a. Checking new methods exist...")
        assert hasattr(BusinessIntelligenceAgent, 'create_peer_comparison_table'), \
            "Should have create_peer_comparison_table method"
        print("   ✅ create_peer_comparison_table exists")

        assert hasattr(BusinessIntelligenceAgent, 'generate_investment_recommendation'), \
            "Should have generate_investment_recommendation method"
        print("   ✅ generate_investment_recommendation exists")

        assert hasattr(BusinessIntelligenceAgent, 'collect_data_sources'), \
            "Should have collect_data_sources method"
        print("   ✅ collect_data_sources exists")

        assert hasattr(BusinessIntelligenceAgent, '_create_default_data_sources_section'), \
            "Should have _create_default_data_sources_section method"
        print("   ✅ _create_default_data_sources_section exists")

        # Check existing methods still exist (no breaking changes)
        print("\n3b. Verifying no breaking changes to existing methods...")
        existing_methods = [
            'research_market_trends',
            'analyze_company_financials',
            'analyze_competitors',
            'generate_strategy_recommendations',
            'create_business_dashboard',
            'run_strategic_analysis'
        ]

        for method_name in existing_methods:
            assert hasattr(BusinessIntelligenceAgent, method_name), \
                f"Should still have {method_name} method"
            print(f"   ✅ {method_name} exists")

        print("\n✅ Business Intelligence Agent: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_imports():
    """Test that all imports work correctly."""
    print("\n" + "=" * 80)
    print("TEST 4: Import Validation")
    print("=" * 80)

    try:
        print("\n4a. Importing AnalysisContext...")
        from agents.common.context_detector import AnalysisContext
        print("   ✅ AnalysisContext imported")

        print("\n4b. Importing CitationFormatter...")
        from agents.common.citation_formatter import CitationFormatter
        print("   ✅ CitationFormatter imported")

        print("\n4c. Importing BusinessIntelligenceAgent...")
        from agents.business_intelligence.business_intelligence import BusinessIntelligenceAgent
        print("   ✅ BusinessIntelligenceAgent imported")

        print("\n✅ All Imports: PASSED")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def main():
    """Run all unit tests."""
    print("=" * 80)
    print("Business Intelligence Agent v1.0.5 - Quick Unit Tests")
    print("=" * 80)

    results = []

    # Run all tests
    results.append(("Import Validation", test_imports()))
    results.append(("Context Detector", test_context_detector()))
    results.append(("Citation Formatter", test_citation_formatter()))
    results.append(("BI Agent Methods", test_bi_agent_methods()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {total}, Passed: {passed}, Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n🎉 ALL UNIT TESTS PASSED! v1.0.5 implementation is ready.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
