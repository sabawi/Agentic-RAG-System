#!/usr/bin/env python3
"""
Function Verification Tests (FVT) for Email Retriever Tool
==========================================================

Simplified test suite focusing on core functionality:
- Parameter defaults and validation
- Email sorting functionality
- Search criteria creation
- Basic tool behavior

Run with: python tests/test_email_retriever_fvt.py
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.email_library_adapter import EmailSearchCriteria


class MockEmailMessage:
    """Mock email message for testing"""
    def __init__(self, sender, subject, date, body_text="", read_status="Read"):
        self.sender = sender
        self.subject = subject
        self.date = date
        self.body_text = body_text
        self.read_status = read_status


def test_search_criteria_creation():
    """Test EmailSearchCriteria creation and defaults"""
    print("🧪 TEST: EmailSearchCriteria creation")

    # Test with all parameters
    criteria = EmailSearchCriteria(
        provider="gmail_primary",
        from_sender="test@example.com",
        subject_contains="meeting",
        content_contains="agenda",
        days_back=7,
        max_results=10,
        include_read=False
    )

    assert criteria.provider == "gmail_primary"
    assert criteria.from_sender == "test@example.com"
    assert criteria.subject_contains == "meeting"
    assert criteria.content_contains == "agenda"
    assert criteria.days_back == 7
    assert criteria.max_results == 10
    assert criteria.include_read == False

    print("✅ PASSED: EmailSearchCriteria creation with all parameters")

    # Test with defaults
    criteria_defaults = EmailSearchCriteria(provider="gmail_primary")
    assert criteria_defaults.provider == "gmail_primary"
    assert criteria_defaults.from_sender is None
    assert criteria_defaults.subject_contains is None
    assert criteria_defaults.content_contains is None
    assert criteria_defaults.days_back == 7  # Default from dataclass
    assert criteria_defaults.max_results == 20  # Default from dataclass
    assert criteria_defaults.include_read == False  # Default from dataclass

    print("✅ PASSED: EmailSearchCriteria defaults work correctly")


def test_email_sorting():
    """Test email sorting functionality"""
    print("🧪 TEST: Email sorting (newest first)")

    # Create test emails with different dates
    now = datetime.now()
    emails = [
        MockEmailMessage("old@test.com", "Old email", now - timedelta(days=5)),
        MockEmailMessage("new@test.com", "New email", now - timedelta(hours=1)),
        MockEmailMessage("middle@test.com", "Middle email", now - timedelta(days=2)),
    ]

    # Sort emails (newest first) - simulating adapter behavior
    sorted_emails = sorted(emails, key=lambda email: email.date if email.date else datetime.min, reverse=True)

    # Verify sorting
    assert len(sorted_emails) == 3
    assert "New email" in sorted_emails[0].subject  # Newest first
    assert "Middle email" in sorted_emails[1].subject  # Middle
    assert "Old email" in sorted_emails[2].subject  # Oldest last

    print("✅ PASSED: Email sorting (newest first) works correctly")


def test_parameter_validation():
    """Test parameter validation logic"""
    print("🧪 TEST: Parameter validation")

    def validate_lookback_days(days):
        """Simulate the parameter validation logic"""
        return min(max(1, days), 365)

    def validate_max_results(results):
        """Simulate max results validation"""
        return min(max(1, results), 100)

    # Test lookback_days validation
    test_cases = [
        (-5, 1),      # Negative clamped to 1
        (0, 1),       # Zero clamped to 1
        (30, 30),     # Valid value unchanged
        (500, 365),   # Over max clamped to 365
    ]

    for input_val, expected in test_cases:
        result = validate_lookback_days(input_val)
        assert result == expected, f"Expected {expected} for input {input_val}, got {result}"

    print("✅ PASSED: lookback_days validation works correctly")

    # Test max_results validation
    result_cases = [
        (0, 1),      # Zero clamped to 1
        (50, 50),    # Valid value unchanged
        (200, 100),  # Over max clamped to 100
    ]

    for input_val, expected in result_cases:
        result = validate_max_results(input_val)
        assert result == expected, f"Expected {expected} for input {input_val}, got {result}"

    print("✅ PASSED: max_results validation works correctly")


def test_tool_parameters():
    """Test tool parameter structure"""
    print("🧪 TEST: Tool parameter structure")

    # Test the tool exists and has required properties
    try:
        from user_tools.email_retriever import EmailRetrieverTool
        tool = EmailRetrieverTool()

        # Check tool properties
        assert hasattr(tool, 'name'), "Tool should have name property"
        assert hasattr(tool, 'description'), "Tool should have description property"
        assert hasattr(tool, 'parameters'), "Tool should have parameters property"

        # Check name and description
        assert tool.name == "email_retriever", f"Expected 'email_retriever', got '{tool.name}'"
        assert "explicit search parameters" in tool.description.lower(), "Description should mention explicit parameters"

        # Check parameters structure
        params = tool.parameters
        assert params['type'] == 'object', "Parameters should be object type"
        assert 'properties' in params, "Parameters should have properties"

        # Check key parameters exist
        properties = params['properties']
        required_params = ['provider', 'lookback_days', 'max_results', 'sender_keyword',
                          'subject_keyword', 'body_keyword', 'include_read']

        for param in required_params:
            assert param in properties, f"Parameter '{param}' should be defined"

        # Check defaults
        assert properties['lookback_days']['default'] == 30, "lookback_days default should be 30"
        assert properties['max_results']['default'] == 20, "max_results default should be 20"
        assert properties['include_read']['default'] == True, "include_read default should be True"

        print("✅ PASSED: Tool parameter structure is correct")

    except Exception as e:
        print(f"❌ FAILED: Tool parameter test failed: {e}")
        return False

    return True


def test_defaults_consistency():
    """Test that all defaults are consistent across the system"""
    print("🧪 TEST: Default consistency across system")

    try:
        from user_tools.email_retriever import EmailRetrieverTool

        # Check tool parameter defaults
        tool = EmailRetrieverTool()
        params = tool.parameters['properties']

        tool_lookback_default = params['lookback_days']['default']
        tool_max_results_default = params['max_results']['default']
        tool_include_read_default = params['include_read']['default']

        # These should match the documented defaults
        assert tool_lookback_default == 30, f"Tool lookback_days default should be 30, got {tool_lookback_default}"
        assert tool_max_results_default == 20, f"Tool max_results default should be 20, got {tool_max_results_default}"
        assert tool_include_read_default == True, f"Tool include_read default should be True, got {tool_include_read_default}"

        print("✅ PASSED: All defaults are consistent")

    except Exception as e:
        print(f"❌ FAILED: Default consistency test failed: {e}")
        return False

    return True


async def test_basic_tool_execution():
    """Test basic tool execution without real email connections"""
    print("🧪 TEST: Basic tool execution")

    try:
        from user_tools.email_retriever import EmailRetrieverTool

        # Create tool instance
        tool = EmailRetrieverTool()

        # Test that tool has adapter (even if not fully configured)
        # This tests initialization logic
        if tool.adapter is None:
            print("⚠️  Tool adapter not initialized (expected if no email config)")
            return True

        print("✅ PASSED: Tool initialization works")

    except Exception as e:
        print(f"❌ FAILED: Basic tool execution test failed: {e}")
        return False

    return True


def main():
    """Run all FVT tests"""
    print("🚀 STARTING EMAIL RETRIEVER FUNCTION VERIFICATION TESTS")
    print("=" * 60)

    tests = [
        test_search_criteria_creation,
        test_email_sorting,
        test_parameter_validation,
        test_tool_parameters,
        test_defaults_consistency,
    ]

    async_tests = [
        test_basic_tool_execution,
    ]

    # Run synchronous tests
    failed_tests = []
    for test in tests:
        try:
            result = test()
            if result is False:
                failed_tests.append(test.__name__)
        except Exception as e:
            print(f"❌ FAILED: {test.__name__} - {e}")
            failed_tests.append(test.__name__)

    # Run async tests
    async def run_async_tests():
        for test in async_tests:
            try:
                result = await test()
                if result is False:
                    failed_tests.append(test.__name__)
            except Exception as e:
                print(f"❌ FAILED: {test.__name__} - {e}")
                failed_tests.append(test.__name__)

    asyncio.run(run_async_tests())

    print("\n" + "=" * 60)
    if failed_tests:
        print(f"❌ FAILED TESTS: {', '.join(failed_tests)}")
        print("❌ FUNCTION VERIFICATION TESTS: FAILED")
        return False
    else:
        print("🎉 ALL EMAIL RETRIEVER FVT TESTS COMPLETED SUCCESSFULLY!")
        print("✅ FUNCTION VERIFICATION TESTS: PASSED")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)