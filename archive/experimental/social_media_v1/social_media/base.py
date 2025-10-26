#!/usr/bin/env python3
"""
Social Media Publisher Base Class
==================================

Version: 1.0.3.11
Last Updated: October 18, 2025

This module provides the abstract base class for all social media publishing plugins.
Each platform-specific publisher (Substack, Medium, Twitter, etc.) inherits from this
base class and implements the required methods.

Usage:
    from user_tools.social_media.base import SocialMediaPublisher

    class SubstackPublisher(SocialMediaPublisher):
        def authenticate(self):
            # Platform-specific authentication
            pass

        def publish_post(self, content, **kwargs):
            # Platform-specific publishing
            pass
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
import json

logger = logging.getLogger(__name__)


class PublishResult:
    """
    Standardized result object for publishing operations.

    Attributes:
        success (bool): Whether the operation succeeded
        platform (str): Platform name (substack, medium, twitter)
        account (str): Account name used
        post_url (str): URL of published post (if successful)
        post_id (str): Platform-specific post ID (if available)
        error (str): Error message (if failed)
        metadata (dict): Additional platform-specific metadata
    """

    def __init__(
        self,
        success: bool,
        platform: str,
        account: str,
        post_url: Optional[str] = None,
        post_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.platform = platform
        self.account = account
        self.post_url = post_url
        self.post_id = post_id
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "success": self.success,
            "platform": self.platform,
            "account": self.account,
            "post_url": self.post_url,
            "post_id": self.post_id,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.success:
            return f"✅ Published to {self.platform} ({self.account}): {self.post_url}"
        else:
            return f"❌ Failed to publish to {self.platform} ({self.account}): {self.error}"


class SocialMediaPublisher(ABC):
    """
    Abstract base class for social media publishing plugins.

    All platform-specific publishers must inherit from this class and implement
    the abstract methods: authenticate() and publish_post().

    Attributes:
        platform_name (str): Name of the platform (e.g., "substack", "medium")
        account_config (dict): Configuration for this specific account
        settings (dict): Platform-wide settings
        authenticated (bool): Authentication status
    """

    def __init__(
        self,
        platform_name: str,
        account_config: Dict[str, Any],
        settings: Dict[str, Any]
    ):
        """
        Initialize the publisher.

        Args:
            platform_name: Name of the platform
            account_config: Account-specific configuration from YAML
            settings: Platform-wide settings from YAML
        """
        self.platform_name = platform_name
        self.account_config = account_config
        self.settings = settings
        self.authenticated = False
        self.account_name = account_config.get("name", "unknown")

        logger.info(f"🔌 Initializing {platform_name} publisher for account: {self.account_name}")

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform using credentials from account_config.

        This method should:
        1. Retrieve credentials from environment variables (referenced in account_config)
        2. Perform platform-specific authentication
        3. Set self.authenticated = True if successful
        4. Return True on success, False on failure

        Returns:
            bool: True if authentication succeeded, False otherwise
        """
        pass

    @abstractmethod
    def publish_post(
        self,
        title: str,
        content: str,
        **kwargs
    ) -> PublishResult:
        """
        Publish a post to the platform.

        This method should:
        1. Ensure authentication (call self.authenticate() if needed)
        2. Format content according to platform requirements
        3. Publish the post
        4. Return a PublishResult object with success/failure info

        Args:
            title: Post title
            content: Post content (HTML or Markdown, platform-dependent)
            **kwargs: Platform-specific arguments (tags, visibility, etc.)

        Returns:
            PublishResult: Result object with success status and details
        """
        pass

    def get_credential(self, env_var_name: str) -> Optional[str]:
        """
        Retrieve a credential from environment variables.

        Helper method for subclasses to safely retrieve credentials.

        Args:
            env_var_name: Name of environment variable (e.g., "SUBSTACK_EMAIL")

        Returns:
            str: Credential value, or None if not found
        """
        value = os.getenv(env_var_name)
        if not value:
            logger.warning(f"⚠️ Environment variable {env_var_name} not found")
        return value

    def save_draft(self, title: str, content: str, metadata: Dict[str, Any]) -> str:
        """
        Save a draft copy of the post before publishing.

        Args:
            title: Post title
            content: Post content
            metadata: Additional metadata (account, platform, kwargs, etc.)

        Returns:
            str: Path to saved draft file
        """
        drafts_dir = self.settings.get("drafts_directory", "./drafts/social_media")
        os.makedirs(drafts_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{timestamp}_{self.platform_name}_{safe_title}.json"
        filepath = os.path.join(drafts_dir, filename)

        draft_data = {
            "platform": self.platform_name,
            "account": self.account_name,
            "title": title,
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Draft saved: {filepath}")
        return filepath

    def log_post(self, result: PublishResult) -> None:
        """
        Log published post to posts log file.

        Args:
            result: PublishResult object from publish_post()
        """
        if not self.settings.get("log_posts", True):
            return

        log_file = self.settings.get("posts_log_file", "./logs/social_media_posts.json")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Load existing logs
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ Could not load existing post logs: {e}")

        # Append new log
        logs.append(result.to_dict())

        # Save updated logs
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            logger.info(f"📝 Post logged to {log_file}")
        except Exception as e:
            logger.error(f"❌ Failed to log post: {e}")

    def validate_account_enabled(self) -> bool:
        """
        Check if this account is enabled in configuration.

        Returns:
            bool: True if account is enabled, False otherwise
        """
        enabled = self.account_config.get("enabled", False)
        if not enabled:
            logger.warning(f"⚠️ Account {self.account_name} is disabled in configuration")
        return enabled

    @property
    def is_authenticated(self) -> bool:
        """Check authentication status."""
        return self.authenticated

    @property
    def description(self) -> str:
        """Get account description from config."""
        return self.account_config.get("description", "No description")
