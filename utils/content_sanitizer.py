"""
Content Sanitizer Utility
=========================
Central utility for sanitizing content before output to files, emails,
social media, PDFs, and other destinations.

This module handles:
- JSON escape sequence normalization (\\n -> actual newlines)
- Unicode character normalization
- Whitespace cleanup
- Content safety checks

All output tools should call sanitize_content() before writing/sending content.

Version: 1.0.0
Created: 2025-12-18
"""

import re
from typing import Optional


def sanitize_content(content: str, preserve_markdown: bool = True) -> str:
    """
    Sanitize content for output - handles JSON escape sequences, Unicode, etc.

    This is the MAIN function that all output tools should call.

    Args:
        content: Raw content string (may contain escaped sequences)
        preserve_markdown: If True, preserves markdown formatting (default: True)

    Returns:
        Sanitized content string with proper newlines and formatting
    """
    if not content:
        return content

    # Step 1: Handle JSON escape sequences
    content = normalize_escape_sequences(content)

    # Step 2: Normalize Unicode characters that cause issues
    content = normalize_unicode(content)

    # Step 3: Clean up excessive whitespace (but preserve intentional formatting)
    content = cleanup_whitespace(content, preserve_markdown)

    return content


def normalize_escape_sequences(content: str) -> str:
    """
    Convert literal escape sequences to actual characters.

    Handles:
    - \\n -> newline
    - \\r -> carriage return
    - \\t -> tab
    - \\\\ -> single backslash
    - Double-escaped sequences (\\\\n -> newline)

    Args:
        content: String potentially containing literal escape sequences

    Returns:
        String with escape sequences converted to actual characters
    """
    if not content:
        return content

    # Handle double-escaped sequences first (\\\\n -> \n -> actual newline)
    # This happens when content goes through multiple JSON encoding/decoding cycles
    content = content.replace('\\\\n', '\n')
    content = content.replace('\\\\r', '\r')
    content = content.replace('\\\\t', '\t')

    # Handle single-escaped sequences (\\n -> actual newline)
    # BUT be careful not to break markdown link syntax like [text](url)
    # The pattern ](http should NOT be touched

    # Use regex to replace \n that are NOT part of markdown links
    # Negative lookbehind to avoid breaking ]( patterns
    content = re.sub(r'(?<!\])\\n', '\n', content)
    content = re.sub(r'(?<!\])\\r', '\r', content)
    content = re.sub(r'(?<!\])\\t', '\t', content)

    # Handle remaining escaped sequences that might be standalone
    # Only replace if they're clearly escape sequences (preceded by space or start of string)
    content = re.sub(r'(^|[^\\])\\n', r'\1\n', content)
    content = re.sub(r'(^|[^\\])\\r', r'\1\r', content)
    content = re.sub(r'(^|[^\\])\\t', r'\1\t', content)

    # Handle escaped backslashes (must be done after other escapes)
    content = content.replace('\\\\', '\\')

    return content


def normalize_unicode(content: str) -> str:
    """
    Normalize Unicode characters that cause issues in various outputs.

    Handles:
    - En-dash (U+2013) -> hyphen
    - Em-dash (U+2014) -> hyphen
    - Ellipsis (U+2026) -> three dots
    - Smart quotes -> regular quotes
    - Non-breaking spaces -> regular spaces

    Args:
        content: String with potential problematic Unicode characters

    Returns:
        String with normalized Unicode characters
    """
    if not content:
        return content

    # Dashes
    content = content.replace('\u2013', '-')  # en-dash
    content = content.replace('\u2014', '-')  # em-dash
    content = content.replace('\u2015', '-')  # horizontal bar

    # Ellipsis
    content = content.replace('\u2026', '...')

    # Smart quotes -> regular quotes
    content = content.replace('\u2018', "'")  # left single quote
    content = content.replace('\u2019', "'")  # right single quote (apostrophe)
    content = content.replace('\u201C', '"')  # left double quote
    content = content.replace('\u201D', '"')  # right double quote

    # Non-breaking spaces -> regular spaces
    content = content.replace('\u00A0', ' ')  # non-breaking space
    content = content.replace('\u202F', ' ')  # narrow non-breaking space

    # Zero-width characters (remove them)
    content = content.replace('\u200B', '')  # zero-width space
    content = content.replace('\u200C', '')  # zero-width non-joiner
    content = content.replace('\u200D', '')  # zero-width joiner
    content = content.replace('\uFEFF', '')  # byte order mark

    return content


def cleanup_whitespace(content: str, preserve_markdown: bool = True) -> str:
    """
    Clean up excessive whitespace while preserving intentional formatting.

    Args:
        content: String with potential whitespace issues
        preserve_markdown: If True, preserves markdown-significant whitespace

    Returns:
        String with cleaned whitespace
    """
    if not content:
        return content

    # Remove trailing whitespace from each line
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)

    # Collapse more than 3 consecutive newlines to 2
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    # Remove leading/trailing whitespace from entire content
    content = content.strip()

    return content


def sanitize_for_html(content: str) -> str:
    """
    Sanitize content specifically for HTML output.

    Applies general sanitization plus HTML-specific handling.

    Args:
        content: Raw content for HTML output

    Returns:
        Sanitized content ready for HTML processing
    """
    # Apply general sanitization first
    content = sanitize_content(content, preserve_markdown=True)

    # Additional HTML-specific sanitization can be added here
    # (Note: HTML entity escaping is handled by the HTML generator)

    return content


def sanitize_for_email(content: str) -> str:
    """
    Sanitize content specifically for email body/attachments.

    Args:
        content: Raw content for email

    Returns:
        Sanitized content ready for email
    """
    # Apply general sanitization
    content = sanitize_content(content, preserve_markdown=True)

    # Email-specific: ensure proper line endings for email protocols
    # Convert any remaining \r\n to \n, then standardize
    content = content.replace('\r\n', '\n')
    content = content.replace('\r', '\n')

    return content


def sanitize_for_social_media(content: str, platform: str = "generic") -> str:
    """
    Sanitize content for social media posting.

    Args:
        content: Raw content for social media
        platform: Target platform (twitter, wordpress, medium, substack, generic)

    Returns:
        Sanitized content ready for posting
    """
    # Apply general sanitization
    content = sanitize_content(content, preserve_markdown=True)

    # Platform-specific handling
    if platform.lower() == "twitter":
        # Twitter has character limits - don't truncate here, just sanitize
        pass
    elif platform.lower() in ["wordpress", "medium", "substack"]:
        # Long-form platforms - preserve full content
        pass

    return content


def sanitize_for_pdf(content: str) -> str:
    """
    Sanitize content for PDF generation.

    Args:
        content: Raw content for PDF

    Returns:
        Sanitized content ready for PDF generation
    """
    # Apply general sanitization
    content = sanitize_content(content, preserve_markdown=True)

    return content


# Convenience function for detecting if content needs sanitization
def needs_sanitization(content: str) -> bool:
    """
    Quick check if content likely needs sanitization.

    Args:
        content: Content to check

    Returns:
        True if content appears to need sanitization
    """
    if not content:
        return False

    # Check for literal escape sequences
    if '\\n' in content or '\\r' in content or '\\t' in content:
        return True

    # Check for problematic Unicode
    problematic_chars = ['\u2013', '\u2014', '\u2026', '\u2018', '\u2019', '\u201C', '\u201D']
    if any(char in content for char in problematic_chars):
        return True

    return False
