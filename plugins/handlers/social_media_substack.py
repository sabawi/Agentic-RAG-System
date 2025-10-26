#!/usr/bin/env python3
"""
Social Media Plugin - Substack Handler
Handles publishing to Substack blogs with email/password authentication.

Complies with Plugin System v1.0.0
"""

import sys
import json
import os
import asyncio
import time
from typing import Dict, Any, Optional, Tuple
import re

# Import dependencies
try:
    import bleach
    import requests
except ImportError as e:
    print(json.dumps({
        "success": False,
        "result": None,
        "error": f"Missing required dependency: {str(e)}. Install with: pip install bleach requests"
    }))
    sys.exit(1)


# =============================================================================
# HTML Sanitization Configuration
# =============================================================================

ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'strong', 'em', 'u', 's',
    'blockquote', 'code', 'pre',
    'ul', 'ol', 'li',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'div', 'span'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
}


# =============================================================================
# Credential Management
# =============================================================================

def load_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Load account credentials from environment variables.

    The YAML file specifies which env vars to look for:
    - ACCOUNT_EMAIL_ENV points to actual email var (e.g., "SUBSTACK_TEST_EMAIL")
    - ACCOUNT_PASSWORD_ENV points to actual password var

    Returns:
        (email, password) or (None, None) if missing
    """
    # Get the names of the env vars from the execution environment
    email_env_name = os.getenv('ACCOUNT_EMAIL_ENV')
    password_env_name = os.getenv('ACCOUNT_PASSWORD_ENV')

    if not email_env_name or not password_env_name:
        return (None, None)

    # Now get the actual values
    email = os.getenv(email_env_name)
    password = os.getenv(password_env_name)

    return (email, password)


def sanitize_credentials_in_error(error_msg: str, email: Optional[str], password: Optional[str]) -> str:
    """
    Remove any credential values from error messages.

    Args:
        error_msg: Original error message
        email: Email to redact
        password: Password to redact

    Returns:
        Sanitized error message
    """
    if email:
        error_msg = error_msg.replace(email, "***EMAIL_REDACTED***")
    if password:
        error_msg = error_msg.replace(password, "***PASSWORD_REDACTED***")
    return error_msg


# =============================================================================
# Content Sanitization
# =============================================================================

def sanitize_html(content: str) -> str:
    """
    Sanitize HTML content to remove XSS vectors.

    Removes:
    - <script> tags
    - JavaScript event handlers (onclick, onerror, etc.)
    - Dangerous attributes (onerror, onload, etc.)
    - Dangerous protocols (javascript:, data:)

    Args:
        content: Raw HTML content

    Returns:
        Sanitized HTML content
    """
    # Use bleach to sanitize HTML
    clean_content = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True  # Remove disallowed tags entirely
    )

    return clean_content


def extract_slug_from_url(url: str) -> Optional[str]:
    """
    Extract publication slug from Substack URL.

    Args:
        url: Substack publication URL (e.g., "https://myblog.substack.com")

    Returns:
        Slug (e.g., "myblog") or None if invalid
    """
    # Pattern: https://SLUG.substack.com or http://SLUG.substack.com
    match = re.match(r'https?://([a-zA-Z0-9-]+)\.substack\.com', url)
    if match:
        return match.group(1)
    return None


# =============================================================================
# Content Validation
# =============================================================================

def validate_content(parameters: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate content before attempting to publish.

    Catches issues early before hitting platform API.

    Args:
        parameters: Plugin parameters

    Returns:
        (is_valid, error_message) tuple
    """
    title = parameters.get('title', '')
    content = parameters.get('content', '')

    # Title validation
    if not title:
        return (False, "Title is required for Substack")
    if len(title) > 200:
        return (False, f"Title too long: {len(title)} chars (max 200)")

    # Content validation
    if not content:
        return (False, "Content is required")
    if len(content) > 1000000:  # 1MB
        return (False, f"Content too large: {len(content)} bytes (max 1MB)")

    # Subtitle validation (if provided)
    subtitle = parameters.get('subtitle', '')
    if subtitle and len(subtitle) > 500:
        return (False, f"Subtitle too long: {len(subtitle)} chars (max 500)")

    # Visibility validation
    visibility = parameters.get('visibility', 'everyone')
    valid_visibility = ['everyone', 'paid_subscribers', 'founding_members']
    if visibility not in valid_visibility:
        return (False, f"Invalid visibility: {visibility}. Must be one of: {', '.join(valid_visibility)}")

    return (True, None)


# =============================================================================
# Substack API Integration
# =============================================================================

async def publish_to_substack(
    email: str,
    password: str,
    title: str,
    content: str,
    subtitle: Optional[str] = None,
    visibility: str = "everyone",
    send_email: bool = True
) -> Dict[str, Any]:
    """
    Publish post to Substack.

    Note: This is a simplified implementation. The actual python-substack library
    may have different methods. This demonstrates the pattern.

    Args:
        email: Substack account email
        password: Substack account password
        title: Post title
        content: Post content (sanitized HTML)
        subtitle: Optional subtitle
        visibility: Visibility level
        send_email: Send email notification

    Returns:
        Result dictionary with success status and post details
    """
    try:
        # Import Substack library
        try:
            from substack import SubstackApi
        except ImportError:
            return {
                "success": False,
                "result": None,
                "error": "python-substack library not installed. Install with: pip install python-substack"
            }

        # Authenticate
        try:
            client = SubstackApi(email=email, password=password)
        except Exception as auth_error:
            error_msg = sanitize_credentials_in_error(str(auth_error), email, password)
            return {
                "success": False,
                "result": None,
                "error": f"Authentication failed: {error_msg}",
                "error_category": "authentication"
            }

        # Publish post
        try:
            # Note: Actual API methods may differ - this is the expected pattern
            post_data = {
                "title": title,
                "body_html": content,
                "audience": visibility,
                "send_email": send_email
            }

            if subtitle:
                post_data["subtitle"] = subtitle

            # Make API call
            post_result = client.post.create(**post_data)

            # Extract post details
            post_url = post_result.get('canonical_url', '')
            post_id = post_result.get('id', '')

            return {
                "success": True,
                "result": {
                    "post_url": post_url,
                    "post_id": str(post_id),
                    "title": title,
                    "platform": "substack",
                    "visibility": visibility
                },
                "error": None
            }

        except Exception as publish_error:
            error_msg = sanitize_credentials_in_error(str(publish_error), email, password)

            # Categorize error
            error_category = "unknown"
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                error_category = "authentication"
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                error_category = "rate_limit"
            elif "404" in error_msg or "not found" in error_msg.lower():
                error_category = "not_found"
            elif "500" in error_msg or "503" in error_msg or "server error" in error_msg.lower():
                error_category = "server_error"

            return {
                "success": False,
                "result": None,
                "error": f"Publishing failed: {error_msg}",
                "error_category": error_category
            }

    except Exception as e:
        error_msg = sanitize_credentials_in_error(str(e), email, password)
        return {
            "success": False,
            "result": None,
            "error": f"Unexpected error: {error_msg}",
            "error_category": "unknown"
        }


# =============================================================================
# Main Plugin Entrypoint
# =============================================================================

async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plugin entrypoint function.

    Args:
        parameters: Validated input parameters from plugin definition schema

    Returns:
        Dict with structure:
        {
            "success": bool,      # REQUIRED: Execution success status
            "result": Any,        # REQUIRED if success=True: Result data
            "error": str | None,  # REQUIRED if success=False: Error message
            "metadata": {         # OPTIONAL: Execution metadata
                "execution_time": float,
                "visibility": str,
                ...
            }
        }
    """
    start_time = time.time()

    try:
        # 1. Load credentials
        email, password = load_credentials()

        if not email or not password:
            return {
                "success": False,
                "result": None,
                "error": "Missing credentials. Check .env file for SUBSTACK_TEST_EMAIL and SUBSTACK_TEST_PASSWORD.",
                "metadata": {
                    "execution_time": time.time() - start_time,
                    "error_category": "configuration"
                }
            }

        # 2. Validate content
        is_valid, validation_error = validate_content(parameters)
        if not is_valid:
            return {
                "success": False,
                "result": None,
                "error": validation_error,
                "metadata": {
                    "execution_time": time.time() - start_time,
                    "error_category": "validation"
                }
            }

        # 3. Extract and sanitize parameters
        title = parameters['title']
        content = sanitize_html(parameters['content'])
        subtitle = parameters.get('subtitle')
        visibility = parameters.get('visibility', 'everyone')
        send_email = parameters.get('send_email', True)

        # 4. Publish to Substack
        result = await publish_to_substack(
            email=email,
            password=password,
            title=title,
            content=content,
            subtitle=subtitle,
            visibility=visibility,
            send_email=send_email
        )

        # 5. Add metadata
        execution_time = time.time() - start_time

        if result['success']:
            result['metadata'] = {
                "execution_time": execution_time,
                "account_type": os.getenv('ACCOUNT_TYPE', 'unknown'),
                "visibility": visibility,
                "send_email": send_email,
                "word_count": len(content.split())
            }
        else:
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['execution_time'] = execution_time

        return result

    except Exception as e:
        # Catch any unexpected errors
        email, password = load_credentials()
        error_msg = sanitize_credentials_in_error(str(e), email, password)

        return {
            "success": False,
            "result": None,
            "error": f"Plugin execution failed: {error_msg}",
            "metadata": {
                "execution_time": time.time() - start_time,
                "error_category": "plugin_error"
            }
        }


# =============================================================================
# Plugin System Communication Protocol
# =============================================================================

if __name__ == "__main__":
    try:
        # Read parameters from stdin (JSON)
        input_data = sys.stdin.read()

        if not input_data:
            print(json.dumps({
                "success": False,
                "result": None,
                "error": "No input data received"
            }))
            sys.exit(1)

        # Parse JSON parameters
        try:
            parameters = json.loads(input_data)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "success": False,
                "result": None,
                "error": f"Invalid JSON input: {str(e)}"
            }))
            sys.exit(1)

        # Execute plugin
        result = asyncio.run(execute(parameters))

        # Write result to stdout (JSON)
        print(json.dumps(result))

        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)

    except Exception as e:
        # Catch any unhandled exceptions
        print(json.dumps({
            "success": False,
            "result": None,
            "error": f"Fatal error: {str(e)}"
        }))
        sys.exit(1)
