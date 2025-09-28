#!/usr/bin/env python3
"""
Test HTML Email Content Conversion
===================================

Tests the HTML to clean text conversion functionality for email bodies.
Ensures that HTML email content is properly cleaned and formatted for summarization.

Run with: python tests/test_html_email_conversion.py
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_tools.email_retriever import EmailRetrieverTool


class MockEmailMessage:
    """Mock EmailMessage with various HTML content types"""
    def __init__(self, subject, sender, body_html="", body_text=""):
        self.subject = subject
        self.sender = sender
        self.date = datetime.now()
        self.is_read = True
        self.body_text = body_text
        self.body_html = body_html
        self.id = "test_email_id"
        self.attachments = []
        self.size = 1024


def test_html_email_cleaning():
    """Test HTML email content cleaning"""
    print("🧪 Testing HTML email content cleaning...")

    tool = EmailRetrieverTool()

    # Test case 1: Rich HTML email (common marketing email)
    html_email = """
    <html>
    <head>
        <style>
        .header { color: blue; font-size: 18px; }
        .content { margin: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Welcome to Our Newsletter!</h1>
        </div>
        <div class="content">
            <p>Dear Valued Customer,</p>
            <p>We're excited to share our <strong>latest updates</strong> with you:</p>
            <ul>
                <li>New product features</li>
                <li>Special discount offers</li>
                <li>Upcoming events</li>
            </ul>
            <p>Visit our website: <a href="https://example.com">Click here</a></p>
            <blockquote>
                "Customer satisfaction is our top priority" - CEO
            </blockquote>
            <table border="1">
                <tr><th>Product</th><th>Price</th></tr>
                <tr><td>Widget A</td><td>$19.99</td></tr>
                <tr><td>Widget B</td><td>$29.99</td></tr>
            </table>
            <p>Best regards,<br/>The Marketing Team</p>
        </div>
    </body>
    </html>
    """

    mock_email = MockEmailMessage(
        subject="Newsletter - Latest Updates",
        sender="marketing@example.com",
        body_html=html_email
    )

    # Test the HTML cleaning
    clean_text = tool._html_to_clean_text(html_email)

    print(f"Original HTML length: {len(html_email)} characters")
    print(f"Clean text length: {len(clean_text)} characters")
    print(f"Reduction: {((len(html_email) - len(clean_text)) / len(html_email) * 100):.1f}%")

    print("\n--- Clean Text Output ---")
    print(clean_text)
    print("--- End Clean Text ---\n")

    # Verify cleaning worked
    assert len(clean_text) > 0, "Clean text should not be empty"
    assert "<html>" not in clean_text, "HTML tags should be removed"
    assert "<style>" not in clean_text, "Style tags should be removed"
    assert "Dear Valued Customer" in clean_text, "Main content should be preserved"
    assert "New product features" in clean_text, "List items should be preserved"
    assert "Widget A" in clean_text, "Table content should be preserved"
    assert "https://example.com" in clean_text, "Links should be preserved"

    print("✅ PASSED: Rich HTML email cleaning")
    return True


def test_simple_html_email():
    """Test simple HTML email with basic formatting"""
    print("\n🧪 Testing simple HTML email...")

    tool = EmailRetrieverTool()

    simple_html = """
    <p>Hello <strong>John</strong>,</p>
    <p>Your order #12345 has been <em>shipped</em>!</p>
    <p>Track your package: <a href="https://tracking.com/12345">Track here</a></p>
    <p>Thank you for your business.</p>
    """

    clean_text = tool._html_to_clean_text(simple_html)

    print("--- Simple HTML Clean Text ---")
    print(clean_text)
    print("--- End ---\n")

    # Verify basic formatting is preserved
    assert "Hello **John**" in clean_text, "Bold formatting should be preserved"
    assert "*shipped*" in clean_text, "Italic formatting should be preserved"
    assert "Track here (https://tracking.com/12345)" in clean_text, "Links should show URL"

    print("✅ PASSED: Simple HTML email cleaning")
    return True


def test_email_with_mixed_content():
    """Test email with both plain text and HTML"""
    print("\n🧪 Testing email with mixed content...")

    tool = EmailRetrieverTool()

    # Mock email with both plain text and HTML
    mock_email = MockEmailMessage(
        subject="Mixed Content Email",
        sender="sender@example.com",
        body_text="This is the plain text version of the email.",
        body_html="<p>This is the <strong>HTML version</strong> of the email.</p>"
    )

    # Test email formatting - should prefer plain text
    formatted_results = tool._format_email_results([mock_email])

    assert len(formatted_results) == 1, "Should return one formatted email"

    result = formatted_results[0]
    body_content = result['body_content']

    # Should use plain text when available
    assert body_content == "This is the plain text version of the email.", "Should prefer plain text over HTML"

    print("✅ PASSED: Mixed content email processing")
    return True


def test_html_only_email():
    """Test email with only HTML content"""
    print("\n🧪 Testing HTML-only email...")

    tool = EmailRetrieverTool()

    mock_email = MockEmailMessage(
        subject="HTML Only Email",
        sender="html@example.com",
        body_html="<p>This email has <strong>only HTML</strong> content.</p><p>No plain text version available.</p>"
    )

    formatted_results = tool._format_email_results([mock_email])
    result = formatted_results[0]
    body_content = result['body_content']

    print(f"HTML-only clean content: {body_content}")

    # Should convert HTML to clean text
    assert "This email has **only HTML** content." in body_content, "HTML should be converted to clean text"
    assert "No plain text version available." in body_content, "All content should be preserved"
    assert "<p>" not in body_content, "HTML tags should be removed"

    print("✅ PASSED: HTML-only email conversion")
    return True


def test_malformed_html():
    """Test handling of malformed HTML"""
    print("\n🧪 Testing malformed HTML handling...")

    tool = EmailRetrieverTool()

    malformed_html = """
    <p>This has <strong>unclosed tags
    <div>Missing closing div
    <br>Some text here
    <span>More text</span>
    Random text without tags
    """

    clean_text = tool._html_to_clean_text(malformed_html)

    print(f"Malformed HTML clean text: {clean_text}")

    # Should handle gracefully without errors
    assert len(clean_text) > 0, "Should produce some clean text"
    assert "Some text here" in clean_text, "Text content should be preserved"
    assert "<" not in clean_text, "Should remove all HTML-like content"

    print("✅ PASSED: Malformed HTML handling")
    return True


def test_email_with_no_content():
    """Test email with empty or no body content"""
    print("\n🧪 Testing empty content handling...")

    tool = EmailRetrieverTool()

    # Test empty HTML
    empty_clean = tool._html_to_clean_text("")
    assert empty_clean == "", "Empty HTML should return empty string"

    # Test whitespace only
    whitespace_clean = tool._html_to_clean_text("   \n\t   ")
    assert whitespace_clean == "", "Whitespace-only HTML should return empty string"

    # Test HTML with no text content
    no_content_html = "<html><head><style>body{}</style></head><body></body></html>"
    no_content_clean = tool._html_to_clean_text(no_content_html)
    assert no_content_clean == "", "HTML with no text content should return empty string"

    print("✅ PASSED: Empty content handling")
    return True


def main():
    """Run all HTML email conversion tests"""
    print("🚀 STARTING HTML EMAIL CONVERSION TESTS")
    print("=" * 50)

    tests = [
        test_html_email_cleaning,
        test_simple_html_email,
        test_email_with_mixed_content,
        test_html_only_email,
        test_malformed_html,
        test_email_with_no_content,
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
        print("🎉 ALL HTML EMAIL CONVERSION TESTS PASSED!")
        print("🔧 HTML emails will now be converted to clean, summarizable text!")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)