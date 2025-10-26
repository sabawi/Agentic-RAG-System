#!/usr/bin/env python3
"""
Social Media Plugin - Medium Handler
Handles publishing to Medium blogs with integration token authentication.

Complies with Plugin System v1.0.0
"""

import sys
import json
import os
import asyncio
import time
from typing import Dict, Any, Optional, Tuple

# Import dependencies
try:
    import bleach
    import requests
    import markdown
except ImportError as e:
    print(json.dumps({
        "success": False,
        "result": None,
        "error": f"Missing required dependency: {str(e)}. Install with: pip install bleach requests markdown"
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
    'div', 'span', 'hr'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'code': ['class'],  # For syntax highlighting
}


# =============================================================================
# Medium API Configuration
# =============================================================================

MEDIUM_API_BASE = "https://api.medium.com/v1"


# =============================================================================
# Credential Management
# =============================================================================

def load_integration_token() -> Optional[str]:
    """
    Load Medium integration token from environment variables.

    The YAML file specifies which env var to look for:
    - INTEGRATION_TOKEN_ENV points to actual token var (e.g., "MEDIUM_TEST_TOKEN")

    Returns:
        Integration token or None if missing
    """
    # Get the name of the env var from the execution environment
    token_env_name = os.getenv('INTEGRATION_TOKEN_ENV')

    if not token_env_name:
        return None

    # Now get the actual token value
    token = os.getenv(token_env_name)

    return token


def sanitize_token_in_error(error_msg: str, token: Optional[str]) -> str:
    """
    Remove token from error messages.

    Args:
        error_msg: Original error message
        token: Integration token to redact

    Returns:
        Sanitized error message
    """
    if token:
        error_msg = error_msg.replace(token, "***TOKEN_REDACTED***")
    return error_msg


# =============================================================================
# Content Processing
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
    clean_content = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True  # Remove disallowed tags entirely
    )

    return clean_content


def convert_markdown_to_html(markdown_content: str) -> str:
    """
    Convert Markdown to HTML.

    Args:
        markdown_content: Markdown formatted content

    Returns:
        HTML content
    """
    html_content = markdown.markdown(
        markdown_content,
        extensions=['extra', 'codehilite', 'tables']
    )

    # Sanitize the generated HTML
    return sanitize_html(html_content)


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
        return (False, "Title is required for Medium")
    if len(title) > 100:
        return (False, f"Title too long: {len(title)} chars (max 100)")

    # Content validation
    if not content:
        return (False, "Content is required")
    if len(content) > 1000000:  # 1MB
        return (False, f"Content too large: {len(content)} bytes (max 1MB)")

    # Tags validation
    tags = parameters.get('tags', [])
    if len(tags) > 5:
        return (False, f"Too many tags: {len(tags)} (max 5)")

    for tag in tags:
        if len(tag) > 25:
            return (False, f"Tag too long: '{tag}' ({len(tag)} chars, max 25)")

    # Content format validation
    content_format = parameters.get('content_format', 'html')
    if content_format not in ['html', 'markdown']:
        return (False, f"Invalid content_format: {content_format}. Must be 'html' or 'markdown'")

    # Publish status validation
    publish_status = parameters.get('publish_status', 'draft')
    valid_statuses = ['public', 'draft', 'unlisted']
    if publish_status not in valid_statuses:
        return (False, f"Invalid publish_status: {publish_status}. Must be one of: {', '.join(valid_statuses)}")

    return (True, None)


# =============================================================================
# Medium API Integration
# =============================================================================

async def get_user_id(token: str) -> Dict[str, Any]:
    """
    Get authenticated user's Medium ID.

    Args:
        token: Medium integration token

    Returns:
        Result dictionary with user_id or error
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.get(
            f"{MEDIUM_API_BASE}/me",
            headers=headers,
            timeout=10
        )

        if response.status_code == 401:
            return {
                "success": False,
                "result": None,
                "error": "Authentication failed: Invalid integration token"
            }

        response.raise_for_status()
        data = response.json()

        user_id = data.get('data', {}).get('id')
        if not user_id:
            return {
                "success": False,
                "result": None,
                "error": "Failed to retrieve user ID from Medium API"
            }

        return {
            "success": True,
            "result": user_id,
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "result": None,
            "error": "Request timeout while getting user ID"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "result": None,
            "error": f"Network error while getting user ID: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Unexpected error getting user ID: {str(e)}"
        }


async def publish_to_medium(
    token: str,
    title: str,
    content: str,
    content_format: str = "html",
    publish_status: str = "draft",
    tags: list = None,
    canonical_url: Optional[str] = None,
    notify_followers: bool = False,
    license_type: str = "all-rights-reserved"
) -> Dict[str, Any]:
    """
    Publish post to Medium.

    Args:
        token: Medium integration token
        title: Post title
        content: Post content (HTML or Markdown)
        content_format: "html" or "markdown"
        publish_status: "public", "draft", or "unlisted"
        tags: List of tags (max 5)
        canonical_url: Canonical URL if cross-posting
        notify_followers: Notify followers
        license_type: Content license

    Returns:
        Result dictionary with success status and post details
    """
    try:
        # Get user ID first
        user_result = await get_user_id(token)
        if not user_result['success']:
            return user_result

        user_id = user_result['result']

        # Prepare post data
        post_data = {
            "title": title,
            "contentFormat": content_format,
            "content": content,
            "publishStatus": publish_status,
            "license": license_type,
            "notifyFollowers": notify_followers
        }

        # Add optional fields
        if tags:
            post_data["tags"] = tags

        if canonical_url:
            post_data["canonicalUrl"] = canonical_url

        # Make API request
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.post(
            f"{MEDIUM_API_BASE}/users/{user_id}/posts",
            headers=headers,
            json=post_data,
            timeout=30
        )

        # Handle response
        if response.status_code == 401:
            return {
                "success": False,
                "result": None,
                "error": "Authentication failed: Invalid integration token",
                "error_category": "authentication"
            }

        if response.status_code == 429:
            return {
                "success": False,
                "result": None,
                "error": "Rate limit exceeded. Please try again later.",
                "error_category": "rate_limit"
            }

        response.raise_for_status()
        data = response.json()

        # Extract post details
        post_info = data.get('data', {})
        post_url = post_info.get('url', '')
        post_id = post_info.get('id', '')

        return {
            "success": True,
            "result": {
                "post_url": post_url,
                "post_id": post_id,
                "title": title,
                "platform": "medium",
                "publish_status": publish_status,
                "tags": tags or []
            },
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "result": None,
            "error": "Request timeout while publishing to Medium",
            "error_category": "timeout"
        }
    except requests.exceptions.RequestException as e:
        error_msg = str(e)

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
        else:
            error_category = "network_error"

        return {
            "success": False,
            "result": None,
            "error": f"Publishing failed: {error_msg}",
            "error_category": error_category
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Unexpected error: {str(e)}",
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
                "publish_status": str,
                ...
            }
        }
    """
    start_time = time.time()

    try:
        # 1. Load integration token
        token = load_integration_token()

        if not token:
            return {
                "success": False,
                "result": None,
                "error": "Missing integration token. Check .env file for MEDIUM_TEST_TOKEN.",
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

        # 3. Extract and process parameters
        title = parameters['title']
        content = parameters['content']
        content_format = parameters.get('content_format', 'html')
        publish_status = parameters.get('publish_status', 'draft')
        tags = parameters.get('tags', [])
        canonical_url = parameters.get('canonical_url')
        notify_followers = parameters.get('notify_followers', False)
        license_type = parameters.get('license', 'all-rights-reserved')

        # 4. Process content based on format
        if content_format == 'markdown':
            # Convert markdown to HTML and sanitize
            processed_content = convert_markdown_to_html(content)
            # Medium API expects HTML, so we use html format
            api_content_format = 'html'
        else:
            # Sanitize HTML
            processed_content = sanitize_html(content)
            api_content_format = 'html'

        # 5. Publish to Medium
        result = await publish_to_medium(
            token=token,
            title=title,
            content=processed_content,
            content_format=api_content_format,
            publish_status=publish_status,
            tags=tags,
            canonical_url=canonical_url,
            notify_followers=notify_followers,
            license_type=license_type
        )

        # 6. Add metadata
        execution_time = time.time() - start_time

        if result['success']:
            result['metadata'] = {
                "execution_time": execution_time,
                "account_type": os.getenv('ACCOUNT_TYPE', 'unknown'),
                "publish_status": publish_status,
                "tags": tags,
                "word_count": len(content.split()),
                "content_format": content_format
            }
        else:
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['execution_time'] = execution_time

        return result

    except Exception as e:
        # Catch any unexpected errors
        token = load_integration_token()
        error_msg = sanitize_token_in_error(str(e), token)

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
