#!/usr/bin/env python3
"""
Test for Email Body Content Retrieval Fix
==========================================

Tests that email formatting correctly extracts body_text and body_html
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_tools.email_retriever import EmailRetrieverTool


class MockEmailMessage:
    """Mock EmailMessage object with body_text and body_html"""
    def __init__(self):
        self.subject = "Test Email Subject"
        self.sender = "test@example.com"
        self.date = datetime.now()
        self.is_read = True
        self.body_text = "This is the plain text body content for testing email retrieval."
        self.body_html = "<html><body><p>This is the HTML body content for testing.</p></body></html>"
        self.id = "test_email_id"
        self.attachments = []
        self.size = 1024


def test_body_content_formatting():
    """Test that _format_email_results correctly extracts body content"""
    print("🧪 Testing email body content formatting...")

    # Create tool instance
    tool = EmailRetrieverTool()

    # Create mock email with body_text and body_html
    mock_email = MockEmailMessage()

    # Test the formatting function
    formatted_results = tool._format_email_results([mock_email])

    if len(formatted_results) == 0:
        print("❌ FAILED: No formatted results returned")
        return False

    email_result = formatted_results[0]

    # Check that body_content is populated
    if 'body_content' not in email_result:
        print("❌ FAILED: body_content field missing")
        print(f"Available fields: {list(email_result.keys())}")
        return False

    body_content = email_result['body_content']

    if not body_content:
        print("❌ FAILED: body_content is empty")
        return False

    # Should prefer body_text over body_html
    if body_content != mock_email.body_text:
        print(f"❌ FAILED: Expected body_text, got: {body_content[:50]}...")
        return False

    # Check preview is also populated
    preview = email_result.get('preview', '')
    if not preview:
        print("❌ FAILED: preview is empty")
        return False

    print("✅ SUCCESS: Body content correctly extracted!")
    print(f"Body content: {body_content}")
    print(f"Preview: {preview}")

    return True


def test_html_only_email():
    """Test email with only HTML body (no plain text)"""
    print("\n🧪 Testing HTML-only email formatting...")

    tool = EmailRetrieverTool()

    # Create mock email with only HTML body
    mock_email = MockEmailMessage()
    mock_email.body_text = None  # No plain text
    mock_email.body_html = "<html><body><h1>HTML Only Email</h1><p>This email only has HTML content.</p></body></html>"

    formatted_results = tool._format_email_results([mock_email])

    if len(formatted_results) == 0:
        print("❌ FAILED: No formatted results returned")
        return False

    email_result = formatted_results[0]
    body_content = email_result.get('body_content', '')

    if not body_content:
        print("❌ FAILED: body_content is empty for HTML-only email")
        return False

    # Should convert HTML to clean text when no plain text available
    if "**HTML Only Email**" not in body_content or "This email only has HTML content." not in body_content:
        print(f"❌ FAILED: Expected clean text elements not found in body_content")
        print(f"Got: {body_content}")
        return False

    print("✅ SUCCESS: HTML-only email correctly handled!")
    print(f"Body content: {body_content[:100]}...")

    return True


def test_empty_body_email():
    """Test email with no body content"""
    print("\n🧪 Testing empty body email...")

    tool = EmailRetrieverTool()

    # Create mock email with no body content
    mock_email = MockEmailMessage()
    mock_email.body_text = ""
    mock_email.body_html = ""

    formatted_results = tool._format_email_results([mock_email])

    if len(formatted_results) == 0:
        print("❌ FAILED: No formatted results returned")
        return False

    email_result = formatted_results[0]
    body_content = email_result.get('body_content', None)

    # Should handle empty body gracefully
    if body_content is None:
        print("❌ FAILED: body_content field missing")
        return False

    # Empty body should result in empty string
    if body_content != "":
        print(f"❌ FAILED: Expected empty string, got: '{body_content}'")
        return False

    print("✅ SUCCESS: Empty body email correctly handled!")

    return True


def main():
    """Run all body content tests"""
    print("🚀 STARTING EMAIL BODY CONTENT RETRIEVAL TESTS")
    print("=" * 50)

    tests = [
        test_body_content_formatting,
        test_html_only_email,
        test_empty_body_email,
    ]

    failed_tests = []
    for test in tests:
        try:
            if not test():
                failed_tests.append(test.__name__)
        except Exception as e:
            print(f"❌ FAILED: {test.__name__} - {e}")
            failed_tests.append(test.__name__)

    print("\n" + "=" * 50)
    if failed_tests:
        print(f"❌ FAILED TESTS: {', '.join(failed_tests)}")
        return False
    else:
        print("🎉 ALL EMAIL BODY CONTENT TESTS PASSED!")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)