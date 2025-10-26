#!/usr/bin/env python3
"""
Social Media Publisher Tool
============================

Version: 1.0.3.11
Last Updated: October 18, 2025

This tool enables publishing content to social media platforms (Substack, Medium, Twitter, etc.)
from the Agentic-RAG system.

Tool Interface for LLM:
    {
        "name": "social_media_publisher",
        "description": "Publish content to social media platforms (Substack, Medium, Twitter/X). Supports multiple accounts per platform.",
        "parameters": {
            "platform": "Platform name (substack, medium, twitter)",
            "title": "Post title",
            "content": "Post content (HTML or Markdown depending on platform)",
            "account": "Account name (optional - uses default if not specified)",
            "subtitle": "Post subtitle (optional, Substack only)",
            "visibility": "Post visibility (optional - platform specific)",
            "tags": "Comma-separated tags (optional)",
            "send_email": "Send notification email to subscribers (optional, boolean)"
        }
    }

Usage Examples:
    1. Publish to default Substack account:
       social_media_publisher(
           platform="substack",
           title="AI News Summary",
           content="<h1>Latest AI Developments</h1><p>...</p>"
       )

    2. Publish to specific Substack account:
       social_media_publisher(
           platform="substack",
           account="agentic-developer",
           title="Technical Deep Dive",
           content="<p>...</p>",
           subtitle="Exploring advanced concepts",
           visibility="paid_subscribers"
       )

    3. Publish to Twitter:
       social_media_publisher(
           platform="twitter",
           content="Check out this amazing discovery! #AI #Tech"
       )
"""

import logging
from typing import Dict, Any, Optional
import json

# Import configuration and publishers
from user_tools.social_media.config_loader import SocialMediaConfig
from user_tools.social_media.publishers.substack_publisher import SubstackPublisher

logger = logging.getLogger(__name__)

# Global configuration instance (loaded once)
_config = None


def get_config() -> SocialMediaConfig:
    """
    Get or initialize global configuration instance.

    Returns:
        SocialMediaConfig: Configuration instance
    """
    global _config
    if _config is None:
        _config = SocialMediaConfig()
    return _config


def social_media_publisher(
    platform: str,
    content: str,
    title: Optional[str] = None,
    account: Optional[str] = None,
    subtitle: Optional[str] = None,
    visibility: Optional[str] = None,
    tags: Optional[str] = None,
    send_email: Optional[bool] = None,
    **kwargs
) -> str:
    """
    Publish content to a social media platform.

    This is the main entry point for social media publishing. It:
    1. Loads configuration
    2. Validates platform and account
    3. Creates appropriate publisher instance
    4. Publishes the content
    5. Returns result

    Args:
        platform: Platform name (substack, medium, twitter)
        content: Post content (HTML or text depending on platform)
        title: Post title (required for Substack/Medium, optional for Twitter)
        account: Account name (optional - uses default if not specified)
        subtitle: Post subtitle (optional, Substack only)
        visibility: Post visibility (platform-specific)
        tags: Comma-separated tags (optional)
        send_email: Send notification email to subscribers (optional)
        **kwargs: Additional platform-specific parameters

    Returns:
        str: JSON string with result details

    Example:
        >>> result = social_media_publisher(
        ...     platform="substack",
        ...     title="My Post",
        ...     content="<p>Content here</p>"
        ... )
        >>> print(result)
        '{"success": true, "post_url": "https://..."}'
    """
    try:
        logger.info(f"📱 Social media publishing request: {platform}/{account or 'default'}")

        # Validate platform
        platform = platform.lower().strip()
        supported_platforms = ["substack", "medium", "twitter"]
        if platform not in supported_platforms:
            error_msg = f"Unsupported platform: {platform}. Supported: {', '.join(supported_platforms)}"
            logger.error(f"❌ {error_msg}")
            return json.dumps({
                "success": False,
                "error": error_msg,
                "supported_platforms": supported_platforms
            })

        # Load configuration
        config = get_config()

        # Check if platform is enabled
        if not config.is_platform_enabled(platform):
            error_msg = f"Platform {platform} is not enabled in configuration"
            logger.error(f"❌ {error_msg}")
            return json.dumps({
                "success": False,
                "error": error_msg,
                "hint": f"Enable {platform} in config/social_media_accounts.yaml features section"
            })

        # Validate account
        if not config.validate_account(platform, account):
            error_msg = f"Account validation failed for {platform}/{account or 'default'}"
            logger.error(f"❌ {error_msg}")
            return json.dumps({
                "success": False,
                "error": error_msg,
                "hint": "Check that account is enabled and credentials are set in .env"
            })

        # Get account configuration
        account_config = config.get_account(platform, account)
        if not account_config:
            error_msg = f"Account not found: {platform}/{account or 'default'}"
            logger.error(f"❌ {error_msg}")
            return json.dumps({
                "success": False,
                "error": error_msg
            })

        # Get platform settings
        platform_settings = config.get_platform_settings(platform)
        defaults = config.get_defaults()
        settings = {**defaults, **platform_settings}

        # Create appropriate publisher instance
        publisher = None

        if platform == "substack":
            publisher = SubstackPublisher(account_config, settings)

            # Validate title for Substack (required)
            if not title:
                error_msg = "Title is required for Substack posts"
                logger.error(f"❌ {error_msg}")
                return json.dumps({
                    "success": False,
                    "error": error_msg
                })

            # Publish to Substack
            result = publisher.publish_post(
                title=title,
                content=content,
                subtitle=subtitle,
                visibility=visibility,
                send_email=send_email,
                **kwargs
            )

        elif platform == "medium":
            # TODO: Implement Medium publisher
            error_msg = "Medium publishing not yet implemented"
            logger.error(f"❌ {error_msg}")
            return json.dumps({
                "success": False,
                "error": error_msg,
                "status": "coming_soon"
            })

        elif platform == "twitter":
            # TODO: Implement Twitter publisher
            error_msg = "Twitter publishing not yet implemented"
            logger.error(f"❌ {error_msg}")
            return json.dumps({
                "success": False,
                "error": error_msg,
                "status": "coming_soon"
            })

        else:
            error_msg = f"Publisher not implemented for: {platform}"
            logger.error(f"❌ {error_msg}")
            return json.dumps({
                "success": False,
                "error": error_msg
            })

        # Return result
        result_dict = result.to_dict()
        logger.info(f"📊 Publishing result: {result}")

        return json.dumps(result_dict, indent=2)

    except Exception as e:
        logger.error(f"❌ Social media publishing failed: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        })


def list_platforms() -> str:
    """
    List all enabled platforms and their accounts.

    Returns:
        str: JSON string with platform and account information
    """
    try:
        config = get_config()
        enabled_platforms = config.get_enabled_platforms()

        platforms_info = {}
        for platform in enabled_platforms:
            accounts = config.list_accounts(platform)
            platforms_info[platform] = {
                "enabled": True,
                "accounts": [
                    {
                        "name": acc.get("name"),
                        "description": acc.get("description"),
                        "enabled": acc.get("enabled", False),
                        "default": acc.get("default", False)
                    }
                    for acc in accounts
                ]
            }

        return json.dumps({
            "enabled_platforms": enabled_platforms,
            "platforms": platforms_info
        }, indent=2)

    except Exception as e:
        logger.error(f"❌ Failed to list platforms: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


# Tool metadata for registration
TOOL_METADATA = {
    "name": "social_media_publisher",
    "description": "Publish content to social media platforms (Substack, Medium, Twitter/X). Supports posting articles, updates, and threads to configured accounts.",
    "parameters": {
        "type": "object",
        "properties": {
            "platform": {
                "type": "string",
                "description": "Platform name (substack, medium, twitter)",
                "enum": ["substack", "medium", "twitter"]
            },
            "content": {
                "type": "string",
                "description": "Post content (HTML for Substack/Medium, plain text for Twitter)"
            },
            "title": {
                "type": "string",
                "description": "Post title (required for Substack/Medium, optional for Twitter)"
            },
            "account": {
                "type": "string",
                "description": "Account name (optional - uses default account if not specified)"
            },
            "subtitle": {
                "type": "string",
                "description": "Post subtitle (optional, Substack only)"
            },
            "visibility": {
                "type": "string",
                "description": "Post visibility: 'everyone', 'paid_subscribers', 'founding_members' (Substack); 'public', 'draft', 'unlisted' (Medium)"
            },
            "tags": {
                "type": "string",
                "description": "Comma-separated tags (optional)"
            },
            "send_email": {
                "type": "boolean",
                "description": "Send notification email to subscribers (optional, Substack only)"
            }
        },
        "required": ["platform", "content"]
    }
}


if __name__ == "__main__":
    # Test the tool
    print("Social Media Publisher Tool")
    print("=" * 50)
    print("\nEnabled platforms:")
    print(list_platforms())
