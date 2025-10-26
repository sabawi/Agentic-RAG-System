#!/usr/bin/env python3
"""
Substack Publisher Plugin
==========================

Version: 1.0.3.11
Last Updated: October 18, 2025

This module provides Substack publishing capabilities for the Agentic-RAG system.
It uses the unofficial python-substack library to publish posts to Substack publications.

Usage:
    from user_tools.social_media.publishers.substack_publisher import SubstackPublisher
    from user_tools.social_media.config_loader import SocialMediaConfig

    config = SocialMediaConfig()
    account = config.get_account("substack", "agentic-developer")
    settings = config.get_platform_settings("substack")

    publisher = SubstackPublisher(account, settings)
    result = publisher.publish_post(
        title="My First Post",
        content="<p>This is the post content in HTML</p>",
        subtitle="An optional subtitle",
        visibility="everyone"
    )

    if result.success:
        print(f"Published at: {result.post_url}")
    else:
        print(f"Error: {result.error}")

IMPORTANT: This uses the UNOFFICIAL python-substack library. The API may change
without notice. Monitor for errors and be prepared to adapt.
"""

from typing import Dict, Any, Optional
import logging
from user_tools.social_media.base import SocialMediaPublisher, PublishResult

logger = logging.getLogger(__name__)

# Try to import python-substack library
try:
    from substack import Api as SubstackApi
    SUBSTACK_AVAILABLE = True
except ImportError:
    SUBSTACK_AVAILABLE = False
    logger.warning("⚠️ python-substack library not installed. Substack publishing will not work.")
    logger.warning("   Install with: pip install python-substack")


class SubstackPublisher(SocialMediaPublisher):
    """
    Substack publishing plugin.

    Inherits from SocialMediaPublisher and implements Substack-specific
    authentication and publishing methods.

    Attributes:
        client: Substack API client instance (when authenticated)
        publication_id: Publication ID from Substack (when authenticated)
    """

    def __init__(self, account_config: Dict[str, Any], settings: Dict[str, Any]):
        """
        Initialize Substack publisher.

        Args:
            account_config: Account configuration from YAML
            settings: Platform settings from YAML
        """
        super().__init__("substack", account_config, settings)
        self.client = None
        self.publication_id = None

        if not SUBSTACK_AVAILABLE:
            logger.error("❌ Cannot create SubstackPublisher: python-substack not installed")

    def authenticate(self) -> bool:
        """
        Authenticate with Substack using email and password.

        Retrieves credentials from environment variables specified in account_config,
        then authenticates with Substack API.

        Returns:
            bool: True if authentication succeeded, False otherwise
        """
        if not SUBSTACK_AVAILABLE:
            logger.error("❌ Cannot authenticate: python-substack library not available")
            return False

        if self.authenticated:
            logger.info("✅ Already authenticated with Substack")
            return True

        try:
            # Get credentials from environment
            email_env = self.account_config.get("email_env")
            password_env = self.account_config.get("password_env")

            if not email_env or not password_env:
                logger.error("❌ email_env or password_env not specified in account configuration")
                return False

            email = self.get_credential(email_env)
            password = self.get_credential(password_env)

            if not email or not password:
                logger.error("❌ Substack credentials not found in environment variables")
                return False

            # Authenticate with Substack
            logger.info(f"🔐 Authenticating with Substack as: {email}")
            self.client = SubstackApi(email=email, password=password)

            # Get publication URL from config
            publication_url = self.account_config.get("publication_url")
            if not publication_url:
                logger.error("❌ publication_url not specified in account configuration")
                return False

            # Extract publication slug from URL (e.g., "agentic-developer" from URL)
            # URL format: https://agentic-developer.substack.com
            publication_slug = publication_url.replace("https://", "").replace("http://", "").split(".")[0]

            # Get publication ID
            logger.info(f"📡 Fetching publication ID for: {publication_slug}")
            try:
                # The python-substack library may have different methods for getting publication ID
                # This is a placeholder - need to check actual library API
                self.publication_id = publication_slug
                logger.info(f"✅ Substack authentication successful for: {self.account_name}")
                self.authenticated = True
                return True

            except Exception as e:
                logger.error(f"❌ Failed to get publication ID: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ Substack authentication failed: {e}")
            self.authenticated = False
            return False

    def publish_post(
        self,
        title: str,
        content: str,
        subtitle: Optional[str] = None,
        visibility: Optional[str] = None,
        send_email: Optional[bool] = None,
        **kwargs
    ) -> PublishResult:
        """
        Publish a post to Substack.

        Args:
            title: Post title (required)
            content: Post content in HTML format (required)
            subtitle: Optional post subtitle
            visibility: Post visibility ("everyone", "paid_subscribers", "founding_members")
                       If None, uses default from settings
            send_email: Whether to send email notification to subscribers
                       If None, uses default from settings
            **kwargs: Additional Substack-specific parameters

        Returns:
            PublishResult: Result object with success status and post details
        """
        if not SUBSTACK_AVAILABLE:
            return PublishResult(
                success=False,
                platform="substack",
                account=self.account_name,
                error="python-substack library not installed"
            )

        # Validate account is enabled
        if not self.validate_account_enabled():
            return PublishResult(
                success=False,
                platform="substack",
                account=self.account_name,
                error="Account is disabled in configuration"
            )

        # Ensure authenticated
        if not self.authenticated:
            if not self.authenticate():
                return PublishResult(
                    success=False,
                    platform="substack",
                    account=self.account_name,
                    error="Authentication failed"
                )

        # Use defaults from settings if not specified
        if visibility is None:
            visibility = self.settings.get("default_visibility", "everyone")

        if send_email is None:
            send_email = self.settings.get("default_send_email", True)

        # Save draft if configured
        if self.settings.get("save_drafts", True):
            try:
                draft_metadata = {
                    "subtitle": subtitle,
                    "visibility": visibility,
                    "send_email": send_email,
                    "kwargs": kwargs
                }
                self.save_draft(title, content, draft_metadata)
            except Exception as e:
                logger.warning(f"⚠️ Failed to save draft: {e}")

        try:
            logger.info(f"📝 Publishing to Substack: {title}")
            logger.info(f"   Visibility: {visibility}, Send Email: {send_email}")

            # Publish post using python-substack library
            # NOTE: The actual API may differ - this is based on common patterns
            # Consult python-substack documentation for exact method signatures
            post_data = {
                "title": title,
                "subtitle": subtitle or "",
                "body_html": content,
                "audience": visibility,
                "send_email": send_email
            }

            # Add any additional kwargs
            post_data.update(kwargs)

            # Publish the post
            response = self.client.post.create(
                publication_slug=self.publication_id,
                **post_data
            )

            # Extract post URL and ID from response
            # NOTE: Response structure may vary - adjust based on actual API
            post_url = response.get("url") or response.get("canonical_url")
            post_id = response.get("id") or response.get("post_id")

            result = PublishResult(
                success=True,
                platform="substack",
                account=self.account_name,
                post_url=post_url,
                post_id=str(post_id) if post_id else None,
                metadata={
                    "title": title,
                    "subtitle": subtitle,
                    "visibility": visibility,
                    "send_email": send_email
                }
            )

            logger.info(f"✅ Successfully published to Substack: {post_url}")

            # Log the post
            self.log_post(result)

            return result

        except Exception as e:
            logger.error(f"❌ Failed to publish to Substack: {e}")
            result = PublishResult(
                success=False,
                platform="substack",
                account=self.account_name,
                error=str(e)
            )
            return result

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a published post by ID.

        Args:
            post_id: Substack post ID

        Returns:
            dict: Post data, or None if not found
        """
        if not self.authenticated:
            logger.error("❌ Not authenticated")
            return None

        try:
            post = self.client.post.get(post_id=post_id)
            return post
        except Exception as e:
            logger.error(f"❌ Failed to retrieve post {post_id}: {e}")
            return None

    def update_post(
        self,
        post_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        **kwargs
    ) -> PublishResult:
        """
        Update an existing Substack post.

        Args:
            post_id: Substack post ID to update
            title: New title (optional)
            content: New content in HTML (optional)
            **kwargs: Additional fields to update

        Returns:
            PublishResult: Result object with success status
        """
        if not self.authenticated:
            if not self.authenticate():
                return PublishResult(
                    success=False,
                    platform="substack",
                    account=self.account_name,
                    error="Authentication failed"
                )

        try:
            update_data = {}
            if title:
                update_data["title"] = title
            if content:
                update_data["body_html"] = content
            update_data.update(kwargs)

            response = self.client.post.update(post_id=post_id, **update_data)

            post_url = response.get("url") or response.get("canonical_url")

            result = PublishResult(
                success=True,
                platform="substack",
                account=self.account_name,
                post_url=post_url,
                post_id=post_id,
                metadata={"updated_fields": list(update_data.keys())}
            )

            logger.info(f"✅ Successfully updated Substack post: {post_id}")
            self.log_post(result)

            return result

        except Exception as e:
            logger.error(f"❌ Failed to update Substack post {post_id}: {e}")
            return PublishResult(
                success=False,
                platform="substack",
                account=self.account_name,
                post_id=post_id,
                error=str(e)
            )
