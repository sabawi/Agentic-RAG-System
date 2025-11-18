#!/usr/bin/env python3
"""
Social Media Plugin - WordPress Handler
Handles publishing to WordPress sites with Application Passwords.
Complies with Plugin System v1.0.0
"""

import sys
import json
import os
import asyncio
import time
import re
from typing import Dict, Any, Optional, Tuple

import bleach
import requests
import xmlrpc.client
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup

# =============================================================================
# Credential Management
# =============================================================================

def load_credentials() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Load WordPress credentials from environment variables.
    Returns:
        (wordpress_url, username, app_password) or (None, None, None) if missing
    """
    wordpress_url_env_name = os.getenv('WORDPRESS_URL_ENV')
    username_env_name = os.getenv('WORDPRESS_USERNAME_ENV')
    app_password_env_name = os.getenv('WORDPRESS_APP_PASSWORD_ENV')

    wordpress_url = os.getenv(wordpress_url_env_name) if wordpress_url_env_name else None
    username = os.getenv(username_env_name) if username_env_name else None
    app_password = os.getenv(app_password_env_name) if app_password_env_name else None

    return (wordpress_url, username, app_password)

def sanitize_credentials_in_error(error_msg: str, username: Optional[str], app_password: Optional[str]) -> str:
    """
    Remove any credential values from error messages.
    """
    if username:
        error_msg = error_msg.replace(username, "***USERNAME_REDACTED***")
    if app_password:
        error_msg = error_msg.replace(app_password, "***PASSWORD_REDACTED***")
    return error_msg

# =============================================================================
# Content Conversion and Sanitization
# =============================================================================

def markdown_to_gutenberg(markdown_text: str) -> str:
    """
    Converts Markdown text to WordPress Gutenberg block format using markdown-it-py and BeautifulSoup.
    Sanitizes the HTML content within the blocks.
    Supports:
    - Headings (h1-h6)
    - Paragraphs (with multi-line support)
    - Bold (**text**)
    - Links ([text](url))
    - Lists (ul, ol)
    - Blockquotes
    """
    ALLOWED_INLINE_TAGS = ['strong', 'em', 'u', 's', 'a', 'br']
    ALLOWED_INLINE_ATTRIBUTES = {'a': ['href', 'title']}

    md = MarkdownIt()
    html_content = md.render(markdown_text)

    soup = BeautifulSoup(html_content, 'html.parser')
    blocks = []

    for tag in soup.find_all(recursive=False): # Only process top-level tags
        # Determine tags allowed for sanitization based on the current block type
        current_allowed_tags = list(ALLOWED_INLINE_TAGS)
        current_allowed_tags.append(tag.name) # Allow the block's own tag
        if tag.name in ['ul', 'ol']:
            current_allowed_tags.append('li') # Allow list items within lists
        
        clean_html = bleach.clean(str(tag), tags=current_allowed_tags, attributes=ALLOWED_INLINE_ATTRIBUTES, strip=True)
        
        if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            blocks.append(f'<!-- wp:heading -->\n{clean_html}\n<!-- /wp:heading -->')
        elif tag.name == 'p':
            blocks.append(f'<!-- wp:paragraph -->\n{clean_html}\n<!-- /wp:paragraph -->')
        elif tag.name in ['ul', 'ol']:
            blocks.append(f'<!-- wp:list -->\n{clean_html}\n<!-- /wp:list -->')
        elif tag.name == 'blockquote':
            blocks.append(f'<!-- wp:quote -->\n{clean_html}\n<!-- /wp:quote -->')
        else:
            # Fallback for other block-level elements, wrap in a paragraph block
            blocks.append(f'<!-- wp:html -->\n{clean_html}\n<!-- /wp:html -->') # Use wp:html for generic blocks

    return '\n\n'.join(blocks)

# =============================================================================
# Content Validation
# =============================================================================

def validate_content(parameters: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate content before attempting to publish.
    """
    title = parameters.get('title', '')
    content = parameters.get('content', '')

    if not title:
        return (False, "Title is required for WordPress posts")
    if not content:
        return (False, "Content is required for WordPress posts")

    return (True, None)

# =============================================================================
# WordPress API Integration
# =============================================================================

async def publish_to_wordpress(
    wordpress_url: str,
    username: str,
    app_password: str,
    title: str,
    content: str,
    status: str = "draft",
    categories: list = None,
    tags: list = None
) -> Dict[str, Any]:
    """
    Publish a post to a WordPress site.
    """
    is_wordpress_com = "wordpress.com" in wordpress_url

    if is_wordpress_com:
        rpc_url = f"{wordpress_url.strip('/')}/xmlrpc.php"
        try:
            client = xmlrpc.client.ServerProxy(rpc_url)
            content_struct = {
                'title': title,
                'description': content,
                'post_status': status,
            }
            if categories:
                content_struct['categories'] = categories
            if tags:
                content_struct['mt_keywords'] = ','.join(tags)
            
            publish_flag = (status == 'publish')
            post_id = client.metaWeblog.newPost(0, username, app_password, content_struct, publish_flag)
            
            return {
                "success": True,
                "result": {
                    "post_id": str(post_id),
                    "title": title,
                    "platform": "wordpress.com",
                    "status": status
                },
                "error": None
            }
        except xmlrpc.client.Fault as fault:
            return {
                "success": False,
                "result": None,
                "error": f"WordPress.com XML-RPC fault: {fault.faultString}",
                "error_category": "network"
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"Failed to publish to WordPress.com via XML-RPC: {e}",
                "error_category": "network"
            }
    else:
        api_url = f"{wordpress_url.rstrip('/')}/wp-json/wp/v2/posts"
        headers = {'Content-Type': 'application/json'}
        auth = (username, app_password)
        data = {'title': title, 'content': content, 'status': status}
        if categories:
            data['categories'] = categories
        if tags:
            data['tags'] = tags

        try:
            response = requests.post(api_url, headers=headers, auth=auth, json=data, timeout=30)
            response.raise_for_status()
            post_data = response.json()
            return {
                "success": True,
                "result": {
                    "post_url": post_data.get('link', ''),
                    "post_id": str(post_data.get('id', '')),
                    "title": title,
                    "platform": "wordpress",
                    "status": status
                },
                "error": None
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "result": None,
                "error": f"Failed to publish to WordPress: {e}",
                "error_category": "network"
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"An unexpected error occurred: {e}",
                "error_category": "unknown"
            }

# =============================================================================
# Main Plugin Entrypoint
# =============================================================================

async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plugin entrypoint function.
    """
    start_time = time.time()
    try:
        wordpress_url, username, app_password = load_credentials()
        if not all([wordpress_url, username, app_password]):
            return {
                "success": False, "result": None,
                "error": "Missing WordPress credentials. Please set WORDPRESS_URL, WORDPRESS_USERNAME, and WORDPRESS_APP_PASSWORD in your .env file.",
                "metadata": {"execution_time": time.time() - start_time, "error_category": "configuration"}
            }

        is_valid, validation_error = validate_content(parameters)
        if not is_valid:
            return {
                "success": False, "result": None, "error": validation_error,
                "metadata": {"execution_time": time.time() - start_time, "error_category": "validation"}
            }

        title = parameters['title']
        content_markdown = parameters['content']
        content = markdown_to_gutenberg(content_markdown)

        # 🔒 SAFETY: Always default to 'draft' status
        # This ensures posts are never accidentally published publicly
        status = parameters.get('status', 'draft')

        # 🔒 SAFETY: Log if attempting to publish (not draft)
        if status != 'draft':
            print(f"⚠️ WARNING: Publishing post with status '{status}' (not draft)", file=sys.stderr)
            print(f"   Title: {title}", file=sys.stderr)
            print(f"   If this was unintentional, check your tool call parameters", file=sys.stderr)

        categories = parameters.get('categories', [])
        tags = parameters.get('tags', [])
        
        result = await publish_to_wordpress(
            wordpress_url=wordpress_url, username=username, app_password=app_password,
            title=title, content=content, status=status, categories=categories, tags=tags
        )

        execution_time = time.time() - start_time
        if result['success']:
            result['metadata'] = {"execution_time": execution_time, "account": username, "status": status}
        else:
            result['metadata'] = result.get('metadata', {})
            result['metadata']['execution_time'] = execution_time

        return result
    except Exception as e:
        username, app_password = load_credentials()[1], load_credentials()[2]
        error_msg = sanitize_credentials_in_error(str(e), username, app_password)
        return {
            "success": False, "result": None, "error": f"Plugin execution failed: {error_msg}",
            "metadata": {"execution_time": time.time() - start_time, "error_category": "plugin_error"}
        }

# =============================================================================
# Plugin System Communication Protocol
# =============================================================================

def main():
    """Main execution function for the plugin."""
    try:
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({"success": False, "result": None, "error": "No input data received"}))
            sys.exit(1)

        try:
            parameters = json.loads(input_data)
        except json.JSONDecodeError as e:
            print(json.dumps({"success": False, "result": None, "error": f"Invalid JSON input: {str(e)}"}))
            sys.exit(1)

        result = asyncio.run(execute(parameters))
        print(json.dumps(result))
        sys.exit(0 if result.get('success') else 1)

    except Exception as e:
        print(json.dumps({"success": False, "result": None, "error": f"Fatal error: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
