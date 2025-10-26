#!/usr/bin/env python3
"""
Social Media Configuration Loader
==================================

Version: 1.0.3.11
Last Updated: October 18, 2025

This module handles loading and accessing social media account configurations
from the config/social_media_accounts.yaml file.

Usage:
    from user_tools.social_media.config_loader import SocialMediaConfig

    config = SocialMediaConfig()

    # Get default Substack account
    account = config.get_account("substack")

    # Get specific account by name
    account = config.get_account("substack", "agentic-developer")

    # Get platform settings
    settings = config.get_platform_settings("substack")

    # List all accounts for a platform
    accounts = config.list_accounts("substack")
"""

import yaml
import os
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class SocialMediaConfig:
    """
    Configuration manager for social media accounts.

    Loads configuration from config/social_media_accounts.yaml and provides
    convenient methods to access account details, platform settings, and defaults.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        if config_path is None:
            # Default location relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(project_root, "config", "social_media_accounts.yaml")

        self.config_path = config_path
        self.config = self._load_config()

        logger.info(f"📋 Loaded social media configuration from: {config_path}")

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            dict: Parsed configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        if not os.path.exists(self.config_path):
            logger.error(f"❌ Configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Social media configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config:
                logger.warning("⚠️ Configuration file is empty, using defaults")
                return self._get_default_config()

            return config

        except yaml.YAMLError as e:
            logger.error(f"❌ Failed to parse configuration file: {e}")
            raise

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration if file is empty or missing.

        Returns:
            dict: Default configuration structure
        """
        return {
            "accounts": {},
            "settings": {},
            "defaults": {},
            "features": {}
        }

    def get_account(
        self,
        platform: str,
        account_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get account configuration for a specific platform and account.

        If account_name is not specified, returns the default account for the platform.

        Args:
            platform: Platform name (substack, medium, twitter)
            account_name: Optional account name. If None, uses default account.

        Returns:
            dict: Account configuration, or None if not found

        Example:
            >>> config = SocialMediaConfig()
            >>> account = config.get_account("substack", "agentic-developer")
            >>> print(account["email_env"])
            'SUBSTACK_AGENTIC_EMAIL'
        """
        accounts = self.config.get("accounts", {}).get(platform, [])

        if not accounts:
            logger.warning(f"⚠️ No accounts configured for platform: {platform}")
            return None

        # If no account name specified, get default account
        if account_name is None:
            for account in accounts:
                if account.get("default", False):
                    logger.info(f"📌 Using default account for {platform}: {account.get('name')}")
                    return account

            # If no default set, use first enabled account
            for account in accounts:
                if account.get("enabled", False):
                    logger.info(f"📌 Using first enabled account for {platform}: {account.get('name')}")
                    return account

            logger.warning(f"⚠️ No default or enabled accounts for {platform}")
            return None

        # Find specific account by name
        for account in accounts:
            if account.get("name") == account_name:
                if not account.get("enabled", False):
                    logger.warning(f"⚠️ Account {account_name} on {platform} is disabled")
                return account

        logger.warning(f"⚠️ Account '{account_name}' not found for platform: {platform}")
        return None

    def get_platform_settings(self, platform: str) -> Dict[str, Any]:
        """
        Get platform-specific settings.

        Args:
            platform: Platform name

        Returns:
            dict: Platform settings, or empty dict if not configured
        """
        return self.config.get("settings", {}).get(platform, {})

    def get_defaults(self) -> Dict[str, Any]:
        """
        Get global default settings.

        Returns:
            dict: Default settings for all platforms
        """
        return self.config.get("defaults", {})

    def get_feature_flag(self, feature: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature: Feature name (e.g., "enable_substack", "enable_scheduling")

        Returns:
            bool: True if feature is enabled, False otherwise
        """
        return self.config.get("features", {}).get(feature, False)

    def list_accounts(self, platform: str) -> List[Dict[str, Any]]:
        """
        List all accounts for a platform.

        Args:
            platform: Platform name

        Returns:
            list: List of account configurations
        """
        return self.config.get("accounts", {}).get(platform, [])

    def is_platform_enabled(self, platform: str) -> bool:
        """
        Check if a platform is enabled globally.

        Args:
            platform: Platform name

        Returns:
            bool: True if platform is enabled, False otherwise
        """
        feature_flag = f"enable_{platform}"
        return self.get_feature_flag(feature_flag)

    def get_enabled_platforms(self) -> List[str]:
        """
        Get list of all enabled platforms.

        Returns:
            list: Names of enabled platforms
        """
        features = self.config.get("features", {})
        enabled = []

        for key, value in features.items():
            if key.startswith("enable_") and value:
                platform = key.replace("enable_", "")
                enabled.append(platform)

        return enabled

    def validate_account(self, platform: str, account_name: Optional[str] = None) -> bool:
        """
        Validate that an account exists, is enabled, and has required credentials.

        Args:
            platform: Platform name
            account_name: Optional account name

        Returns:
            bool: True if account is valid and ready to use
        """
        # Check platform enabled
        if not self.is_platform_enabled(platform):
            logger.warning(f"⚠️ Platform {platform} is not enabled")
            return False

        # Get account
        account = self.get_account(platform, account_name)
        if not account:
            logger.warning(f"⚠️ Account not found: {platform}/{account_name}")
            return False

        # Check account enabled
        if not account.get("enabled", False):
            logger.warning(f"⚠️ Account {account.get('name')} is disabled")
            return False

        # Check credentials exist in environment
        env_vars_needed = [
            key for key in account.keys()
            if key.endswith("_env")
        ]

        missing_vars = []
        for var_key in env_vars_needed:
            env_var_name = account[var_key]
            if not os.getenv(env_var_name):
                missing_vars.append(env_var_name)

        if missing_vars:
            logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
            return False

        logger.info(f"✅ Account validated: {platform}/{account.get('name')}")
        return True

    def reload(self) -> None:
        """
        Reload configuration from file.

        Useful if configuration file has been modified.
        """
        self.config = self._load_config()
        logger.info("🔄 Configuration reloaded")

    def __repr__(self) -> str:
        """String representation."""
        platforms = self.get_enabled_platforms()
        return f"SocialMediaConfig(enabled_platforms={platforms})"
