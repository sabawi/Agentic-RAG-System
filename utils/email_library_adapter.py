"""
Email Library Adapter for LLM Server Integration
Bridges the server's email configuration format to the email library's expected format.
Provides connection management, configuration translation, and helper functions.
"""

import os
import tempfile
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass

# Import the email library and config loader
try:
    from .email_library import EmailLibrary, EmailMessage
    from .config_loader import ConfigLoader
except ImportError:
    from email_library import EmailLibrary, EmailMessage
    from config_loader import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class EmailSearchCriteria:
    """Data class for email search criteria"""
    provider: str
    from_sender: Optional[str] = None
    subject_contains: Optional[str] = None
    content_contains: Optional[str] = None
    days_back: int = 7
    max_results: int = 20
    include_read: bool = False
    search_folder: str = "INBOX"


class EmailLibraryAdapter:
    """
    Adapter that bridges the LLM server's email configuration to the EmailLibrary.

    Features:
    - Configuration translation between server format and library format
    - Connection pooling and management
    - Helper functions for common email operations
    - Error handling and logging
    - Provider selection and validation
    """

    def __init__(self, server_config_path: Optional[str] = None):
        """
        Initialize the email library adapter.

        Args:
            server_config_path: Path to server's llm_config.yaml file
        """
        self.server_config_path = server_config_path
        self.config_loader = ConfigLoader(server_config_path)
        self.email_library = None
        self.temp_config_file = None
        self._connections = {}

        # Load and translate configuration
        self._load_server_config()
        self._create_email_library_config()

    def _load_server_config(self):
        """Load server configuration and extract email section"""
        try:
            self.server_config = self.config_loader.load_config()

            if 'email' not in self.server_config:
                raise ValueError("Email configuration section not found in server config")

            self.email_config = self.server_config['email']

            if not self.email_config.get('enabled', False):
                raise ValueError("Email functionality is disabled in server config")

            logger.info(f"Loaded email config with {len(self.email_config.get('providers', {}))} providers")

        except Exception as e:
            logger.error(f"Failed to load server config: {e}")
            raise

    def _create_email_library_config(self):
        """Translate server config format to email library format"""
        try:
            # Extract providers from server config and translate to library format
            server_providers = self.email_config.get('providers', {})

            if not server_providers:
                raise ValueError("No email providers configured")

            # Translate to email library format
            library_config = {
                'providers': {}
            }

            for provider_name, provider_config in server_providers.items():
                # Translate provider configuration
                library_provider = {
                    'email': provider_config.get('email', ''),
                    'password': provider_config.get('password', ''),
                    'description': provider_config.get('description', f'{provider_name} email account')
                }

                # Add IMAP configuration if present
                if 'imap' in provider_config:
                    library_provider['imap'] = {
                        'server': provider_config['imap'].get('server', ''),
                        'port': provider_config['imap'].get('port', 993),
                        'use_ssl': provider_config['imap'].get('use_ssl', True)
                    }

                # Add SMTP configuration if present
                if 'smtp' in provider_config:
                    library_provider['smtp'] = {
                        'server': provider_config['smtp'].get('server', ''),
                        'port': provider_config['smtp'].get('port', 587),
                        'use_tls': provider_config['smtp'].get('use_tls', True)
                    }

                # Add POP3 configuration if present
                if 'pop3' in provider_config:
                    library_provider['pop3'] = {
                        'server': provider_config['pop3'].get('server', ''),
                        'port': provider_config['pop3'].get('port', 995),
                        'use_ssl': provider_config['pop3'].get('use_ssl', True)
                    }

                library_config['providers'][provider_name] = library_provider

            # Create temporary config file for email library
            self.temp_config_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.yaml', delete=False
            )

            yaml.dump(library_config, self.temp_config_file, default_flow_style=False)
            self.temp_config_file.close()

            logger.info(f"Created email library config: {self.temp_config_file.name}")

        except Exception as e:
            logger.error(f"Failed to create email library config: {e}")
            raise

    def get_email_library(self) -> EmailLibrary:
        """Get or create EmailLibrary instance"""
        if self.email_library is None:
            try:
                self.email_library = EmailLibrary(self.temp_config_file.name)
                logger.info("EmailLibrary instance created successfully")
            except Exception as e:
                logger.error(f"Failed to create EmailLibrary instance: {e}")
                raise

        return self.email_library

    def list_providers(self) -> List[str]:
        """List all available email providers"""
        return list(self.email_config.get('providers', {}).keys())

    def get_default_provider(self) -> str:
        """Get the default email provider"""
        return self.email_config.get('default_provider', 'gmail_primary')

    def validate_provider(self, provider_name: str) -> bool:
        """Validate that a provider exists and is configured"""
        providers = self.email_config.get('providers', {})
        return provider_name in providers

    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get information about a specific provider"""
        if not self.validate_provider(provider_name):
            raise ValueError(f"Provider '{provider_name}' not found")

        provider_config = self.email_config['providers'][provider_name]
        return {
            'name': provider_name,
            'email': provider_config.get('email', ''),
            'description': provider_config.get('description', ''),
            'has_imap': 'imap' in provider_config,
            'has_smtp': 'smtp' in provider_config,
            'has_pop3': 'pop3' in provider_config
        }

    def retrieve_emails(self, criteria: EmailSearchCriteria) -> List[EmailMessage]:
        """
        Retrieve emails based on search criteria.

        Args:
            criteria: EmailSearchCriteria object with search parameters

        Returns:
            List of EmailMessage objects
        """
        try:
            # Validate provider
            if not self.validate_provider(criteria.provider):
                available = ', '.join(self.list_providers())
                raise ValueError(f"Provider '{criteria.provider}' not found. Available: {available}")

            # Get email library instance
            email_lib = self.get_email_library()

            # Calculate date range
            from_date = datetime.now() - timedelta(days=criteria.days_back)

            # Determine retrieval type - always use full for comprehensive search
            retrieval_type = "full"

            # Perform email retrieval
            emails = email_lib.retrieve_email(
                provider_alias=criteria.provider,
                retrieval_type=retrieval_type,
                from_date=from_date,
                include_read=criteria.include_read,
                timeout=self.email_config.get('retrieval', {}).get('default_timeout', 30)
            )

            # Apply additional filtering
            filtered_emails = self._filter_emails(emails, criteria)

            logger.info(f"Retrieved {len(filtered_emails)} emails from {criteria.provider}")
            return filtered_emails

        except Exception as e:
            logger.error(f"Failed to retrieve emails: {e}")
            raise

    def _filter_emails(self, emails: List[EmailMessage], criteria: EmailSearchCriteria) -> List[EmailMessage]:
        """Apply additional filtering to retrieved emails"""
        filtered = emails

        # Filter by sender
        if criteria.from_sender:
            sender_lower = criteria.from_sender.lower()
            filtered = [
                email for email in filtered
                if sender_lower in email.sender.lower()
            ]

        # Filter by subject
        if criteria.subject_contains:
            subject_lower = criteria.subject_contains.lower()
            filtered = [
                email for email in filtered
                if subject_lower in email.subject.lower()
            ]

        # Filter by content (if body text is available)
        if criteria.content_contains:
            content_lower = criteria.content_contains.lower()
            filtered = [
                email for email in filtered
                if hasattr(email, 'body_text') and email.body_text and
                content_lower in email.body_text.lower()
            ]

        # Sort by date (newest first) - CRITICAL for "last N emails" requests
        try:
            filtered.sort(key=lambda email: email.date if email.date else datetime.min, reverse=True)
            logger.debug(f"Sorted {len(filtered)} emails by date (newest first)")
        except Exception as e:
            logger.warning(f"Failed to sort emails by date: {e}")

        # Limit results after sorting
        return filtered[:criteria.max_results]

    def send_email(self, provider: str, to_email: str, subject: str, body: str,
                   attachments: Optional[List[str]] = None) -> bool:
        """
        Send email using specified provider.

        Args:
            provider: Provider name to use for sending
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            attachments: Optional list of file paths to attach

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Validate provider
            if not self.validate_provider(provider):
                raise ValueError(f"Provider '{provider}' not found")

            # Get email library instance
            email_lib = self.get_email_library()

            # Send email (implementation depends on email library's send_email method)
            # Note: This is a placeholder - actual implementation depends on your email library's API
            success = email_lib.send_email(
                provider_alias=provider,
                to_email=to_email,
                subject=subject,
                body=body,
                attachments=attachments or []
            )

            logger.info(f"Email sent via {provider} to {to_email}: {'Success' if success else 'Failed'}")
            return success

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def test_provider_connection(self, provider_name: str) -> Dict[str, Any]:
        """
        Test connection to a specific provider.

        Args:
            provider_name: Name of provider to test

        Returns:
            Dict with test results
        """
        result = {
            'provider': provider_name,
            'success': False,
            'error': None,
            'capabilities': {
                'imap': False,
                'smtp': False,
                'pop3': False
            }
        }

        try:
            if not self.validate_provider(provider_name):
                result['error'] = f"Provider '{provider_name}' not configured"
                return result

            # Get provider info
            provider_info = self.get_provider_info(provider_name)

            # Test basic configuration
            if not provider_info['email']:
                result['error'] = "Email address not configured"
                return result

            # For now, just validate configuration structure
            # In a full implementation, you'd test actual connections
            result['success'] = True
            result['capabilities']['imap'] = provider_info['has_imap']
            result['capabilities']['smtp'] = provider_info['has_smtp']
            result['capabilities']['pop3'] = provider_info['has_pop3']

            logger.info(f"Provider {provider_name} connection test: {'PASSED' if result['success'] else 'FAILED'}")

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Provider {provider_name} connection test failed: {e}")

        return result

    def get_adapter_status(self) -> Dict[str, Any]:
        """Get current adapter status and configuration summary"""
        try:
            providers = self.list_providers()
            default_provider = self.get_default_provider()

            return {
                'status': 'ready',
                'providers_configured': len(providers),
                'providers': providers,
                'default_provider': default_provider,
                'email_enabled': self.email_config.get('enabled', False),
                'temp_config_file': self.temp_config_file.name if self.temp_config_file else None,
                'email_library_ready': self.email_library is not None
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def close(self):
        """Clean up resources"""
        try:
            # Close email library connections
            if self.email_library:
                self.email_library.close_connections()
                self.email_library = None

            # Clean up temporary config file
            if self.temp_config_file and os.path.exists(self.temp_config_file.name):
                os.unlink(self.temp_config_file.name)
                self.temp_config_file = None

            logger.info("Email adapter resources cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up adapter resources: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience functions for common operations
def create_email_adapter(config_path: Optional[str] = None) -> EmailLibraryAdapter:
    """Create and return an EmailLibraryAdapter instance"""
    return EmailLibraryAdapter(config_path)


def quick_email_search(provider: str, query: str, days_back: int = 7,
                      max_results: int = 20) -> List[EmailMessage]:
    """
    Quick email search function for simple queries.

    Args:
        provider: Email provider name
        query: Search query (can contain sender, subject, or content keywords)
        days_back: Number of days to search back
        max_results: Maximum number of results

    Returns:
        List of EmailMessage objects
    """
    with create_email_adapter() as adapter:
        # Simple query parsing
        criteria = EmailSearchCriteria(
            provider=provider,
            days_back=days_back,
            max_results=max_results
        )

        # Basic query parsing
        query_lower = query.lower()
        if 'from:' in query_lower:
            # Extract sender: "from:john@example.com" or "from:John"
            import re
            sender_match = re.search(r'from:([^\s]+)', query_lower)
            if sender_match:
                criteria.from_sender = sender_match.group(1)

        if 'subject:' in query_lower:
            # Extract subject: "subject:meeting"
            subject_match = re.search(r'subject:([^\s]+)', query_lower)
            if subject_match:
                criteria.subject_contains = subject_match.group(1)

        # If no specific filters, treat as general content search
        if not criteria.from_sender and not criteria.subject_contains:
            criteria.content_contains = query

        return adapter.retrieve_emails(criteria)


# Module-level convenience instance (optional)
_default_adapter = None

def get_default_adapter() -> EmailLibraryAdapter:
    """Get default adapter instance (singleton pattern)"""
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = EmailLibraryAdapter()
    return _default_adapter