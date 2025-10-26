"""
Unit tests for Social Media Handlers

Tests the Substack handler implementation including:
- Credential loading
- HTML sanitization
- Content validation
- Publishing logic
- Error handling
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Add plugins/handlers to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../plugins/handlers'))

# Import handler
import social_media_substack


class TestCredentialLoading:
    """Test credential loading from environment variables"""

    def test_load_credentials_success(self, monkeypatch):
        """Test successful credential loading"""
        # Set up environment
        monkeypatch.setenv('ACCOUNT_EMAIL_ENV', 'SUBSTACK_TEST_EMAIL')
        monkeypatch.setenv('ACCOUNT_PASSWORD_ENV', 'SUBSTACK_TEST_PASSWORD')
        monkeypatch.setenv('SUBSTACK_TEST_EMAIL', 'test@example.com')
        monkeypatch.setenv('SUBSTACK_TEST_PASSWORD', 'password123')

        # Load credentials
        email, password = social_media_substack.load_credentials()

        # Verify
        assert email == 'test@example.com'
        assert password == 'password123'

    def test_load_credentials_missing_env_vars(self, monkeypatch):
        """Test credential loading with missing environment variable references"""
        # Don't set ACCOUNT_EMAIL_ENV and ACCOUNT_PASSWORD_ENV
        email, password = social_media_substack.load_credentials()

        # Should return None for both
        assert email is None
        assert password is None

    def test_load_credentials_missing_actual_values(self, monkeypatch):
        """Test credential loading when env var names are set but actual values are missing"""
        # Set environment variable names but not actual values
        monkeypatch.setenv('ACCOUNT_EMAIL_ENV', 'SUBSTACK_TEST_EMAIL')
        monkeypatch.setenv('ACCOUNT_PASSWORD_ENV', 'SUBSTACK_TEST_PASSWORD')
        # Don't set SUBSTACK_TEST_EMAIL and SUBSTACK_TEST_PASSWORD

        email, password = social_media_substack.load_credentials()

        # Should return None for both
        assert email is None
        assert password is None

    def test_sanitize_credentials_in_error(self):
        """Test credential redaction in error messages"""
        email = 'secret@example.com'
        password = 'super_secret_password'
        error_msg = f"Authentication failed with {email} and {password}"

        sanitized = social_media_substack.sanitize_credentials_in_error(error_msg, email, password)

        # Verify credentials are redacted
        assert email not in sanitized
        assert password not in sanitized
        assert '***EMAIL_REDACTED***' in sanitized
        assert '***PASSWORD_REDACTED***' in sanitized


class TestHTMLSanitization:
    """Test HTML sanitization for XSS protection"""

    def test_sanitize_html_removes_script_tags(self):
        """Test that <script> tags are removed"""
        malicious_html = '<h1>Title</h1><script>alert("XSS")</script><p>Content</p>'

        clean_html = social_media_substack.sanitize_html(malicious_html)

        assert '<script>' not in clean_html
        assert 'alert' not in clean_html
        assert '<h1>Title</h1>' in clean_html
        assert '<p>Content</p>' in clean_html

    def test_sanitize_html_removes_event_handlers(self):
        """Test that event handlers are removed"""
        malicious_html = '<img src="x" onerror="alert(1)">'

        clean_html = social_media_substack.sanitize_html(malicious_html)

        assert 'onerror' not in clean_html
        assert 'alert' not in clean_html

    def test_sanitize_html_removes_javascript_protocol(self):
        """Test that javascript: protocol is removed"""
        malicious_html = '<a href="javascript:alert(1)">Click</a>'

        clean_html = social_media_substack.sanitize_html(malicious_html)

        assert 'javascript:' not in clean_html
        assert 'alert' not in clean_html

    def test_sanitize_html_removes_dangerous_tags(self):
        """Test that dangerous tags are removed"""
        dangerous_tags = [
            '<iframe src="evil.com"></iframe>',
            '<object data="evil.com"></object>',
            '<embed src="evil.com">',
        ]

        for tag in dangerous_tags:
            clean_html = social_media_substack.sanitize_html(tag)
            assert '<iframe' not in clean_html.lower()
            assert '<object' not in clean_html.lower()
            assert '<embed' not in clean_html.lower()

    def test_sanitize_html_keeps_allowed_tags(self):
        """Test that allowed tags are preserved"""
        safe_html = '''
        <h1>Title</h1>
        <p>Paragraph with <strong>bold</strong> and <em>italic</em></p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <a href="https://example.com">Link</a>
        <img src="https://example.com/image.jpg" alt="Image">
        '''

        clean_html = social_media_substack.sanitize_html(safe_html)

        # Verify all allowed tags are preserved
        assert '<h1>' in clean_html
        assert '<p>' in clean_html
        assert '<strong>' in clean_html
        assert '<em>' in clean_html
        assert '<ul>' in clean_html
        assert '<li>' in clean_html
        assert '<a ' in clean_html
        assert '<img ' in clean_html


class TestContentValidation:
    """Test content validation logic"""

    def test_validate_content_success(self):
        """Test successful content validation"""
        parameters = {
            'title': 'Test Post',
            'content': '<p>This is test content</p>',
            'visibility': 'everyone',
            'send_email': True
        }

        is_valid, error = social_media_substack.validate_content(parameters)

        assert is_valid is True
        assert error is None

    def test_validate_content_missing_title(self):
        """Test validation with missing title"""
        parameters = {
            'content': '<p>This is test content</p>'
        }

        is_valid, error = social_media_substack.validate_content(parameters)

        assert is_valid is False
        assert 'title' in error.lower()
        assert 'required' in error.lower()

    def test_validate_content_title_too_long(self):
        """Test validation with title exceeding max length"""
        parameters = {
            'title': 'X' * 250,  # Exceeds 200 char limit
            'content': '<p>Content</p>'
        }

        is_valid, error = social_media_substack.validate_content(parameters)

        assert is_valid is False
        assert 'too long' in error.lower()

    def test_validate_content_missing_content(self):
        """Test validation with missing content"""
        parameters = {
            'title': 'Test Post'
        }

        is_valid, error = social_media_substack.validate_content(parameters)

        assert is_valid is False
        assert 'content' in error.lower()
        assert 'required' in error.lower()

    def test_validate_content_content_too_large(self):
        """Test validation with content exceeding max size"""
        parameters = {
            'title': 'Test Post',
            'content': 'X' * 1000001  # Exceeds 1MB limit
        }

        is_valid, error = social_media_substack.validate_content(parameters)

        assert is_valid is False
        assert 'too large' in error.lower()

    def test_validate_content_invalid_visibility(self):
        """Test validation with invalid visibility value"""
        parameters = {
            'title': 'Test Post',
            'content': '<p>Content</p>',
            'visibility': 'invalid_value'
        }

        is_valid, error = social_media_substack.validate_content(parameters)

        assert is_valid is False
        assert 'visibility' in error.lower()

    def test_validate_content_subtitle_too_long(self):
        """Test validation with subtitle exceeding max length"""
        parameters = {
            'title': 'Test Post',
            'content': '<p>Content</p>',
            'subtitle': 'X' * 600  # Exceeds 500 char limit
        }

        is_valid, error = social_media_substack.validate_content(parameters)

        assert is_valid is False
        assert 'subtitle' in error.lower()
        assert 'too long' in error.lower()


class TestExecuteFunction:
    """Test main execute function"""

    @pytest.mark.asyncio
    async def test_execute_missing_credentials(self, monkeypatch):
        """Test execution with missing credentials"""
        # Don't set any environment variables
        result = await social_media_substack.execute({
            'title': 'Test',
            'content': '<p>Content</p>'
        })

        assert result['success'] is False
        assert 'credentials' in result['error'].lower()
        assert 'metadata' in result
        assert 'execution_time' in result['metadata']

    @pytest.mark.asyncio
    async def test_execute_validation_error(self, monkeypatch):
        """Test execution with validation error"""
        # Set credentials
        monkeypatch.setenv('ACCOUNT_EMAIL_ENV', 'SUBSTACK_TEST_EMAIL')
        monkeypatch.setenv('ACCOUNT_PASSWORD_ENV', 'SUBSTACK_TEST_PASSWORD')
        monkeypatch.setenv('SUBSTACK_TEST_EMAIL', 'test@example.com')
        monkeypatch.setenv('SUBSTACK_TEST_PASSWORD', 'password123')

        # Missing required field
        result = await social_media_substack.execute({
            'content': '<p>Content</p>'  # Missing title
        })

        assert result['success'] is False
        assert 'title' in result['error'].lower()
        assert result['metadata']['error_category'] == 'validation'

    @pytest.mark.asyncio
    async def test_execute_sanitizes_html(self, monkeypatch):
        """Test that execute sanitizes HTML content"""
        # Set credentials
        monkeypatch.setenv('ACCOUNT_EMAIL_ENV', 'SUBSTACK_TEST_EMAIL')
        monkeypatch.setenv('ACCOUNT_PASSWORD_ENV', 'SUBSTACK_TEST_PASSWORD')
        monkeypatch.setenv('SUBSTACK_TEST_EMAIL', 'test@example.com')
        monkeypatch.setenv('SUBSTACK_TEST_PASSWORD', 'password123')

        # Mock the publish_to_substack function to capture sanitized content
        async def mock_publish(*args, **kwargs):
            # Verify content has been sanitized
            content = kwargs.get('content', args[3] if len(args) > 3 else '')
            assert '<script>' not in content
            assert 'alert' not in content

            return {
                "success": True,
                "result": {
                    "post_url": "https://test.substack.com/p/test",
                    "post_id": "12345",
                    "title": kwargs.get('title', ''),
                    "platform": "substack",
                    "visibility": kwargs.get('visibility', 'everyone')
                },
                "error": None
            }

        with patch.object(social_media_substack, 'publish_to_substack', mock_publish):
            result = await social_media_substack.execute({
                'title': 'Test',
                'content': '<p>Content</p><script>alert("XSS")</script>'
            })

            # Should succeed with sanitized content
            assert result['success'] is True


class TestSlugExtraction:
    """Test publication slug extraction from URL"""

    def test_extract_slug_valid_url(self):
        """Test extracting slug from valid Substack URL"""
        url = "https://myblog.substack.com"
        slug = social_media_substack.extract_slug_from_url(url)
        assert slug == "myblog"

    def test_extract_slug_with_path(self):
        """Test extracting slug from URL with path"""
        url = "https://myblog.substack.com/about"
        slug = social_media_substack.extract_slug_from_url(url)
        assert slug == "myblog"

    def test_extract_slug_http(self):
        """Test extracting slug from HTTP URL"""
        url = "http://myblog.substack.com"
        slug = social_media_substack.extract_slug_from_url(url)
        assert slug == "myblog"

    def test_extract_slug_invalid_url(self):
        """Test extracting slug from invalid URL"""
        url = "https://example.com"
        slug = social_media_substack.extract_slug_from_url(url)
        assert slug is None


# =============================================================================
# Integration Test Placeholder
# =============================================================================

class TestIntegration:
    """Integration tests (require actual Substack credentials)"""

    @pytest.mark.skip(reason="Requires real Substack account - run manually")
    @pytest.mark.asyncio
    async def test_real_publish(self, monkeypatch):
        """
        Test actual publishing to Substack.

        To run this test:
        1. Set up real Substack credentials in .env
        2. Run: pytest tests/utilities/test_social_media_handlers.py::TestIntegration::test_real_publish -v
        """
        # Set credentials from environment
        monkeypatch.setenv('ACCOUNT_EMAIL_ENV', 'SUBSTACK_TEST_EMAIL')
        monkeypatch.setenv('ACCOUNT_PASSWORD_ENV', 'SUBSTACK_TEST_PASSWORD')

        result = await social_media_substack.execute({
            'title': 'Test Post from Unit Tests',
            'content': '<h1>Test Heading</h1><p>This is a test post created by automated tests.</p>',
            'visibility': 'everyone',
            'send_email': False  # Don't spam subscribers during testing
        })

        # Verify result structure
        assert 'success' in result
        assert 'result' in result or 'error' in result
        assert 'metadata' in result

        if result['success']:
            assert result['result']['post_url']
            assert result['result']['post_id']
            print(f"\n✅ Successfully published: {result['result']['post_url']}")
        else:
            print(f"\n❌ Publishing failed: {result['error']}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v'])
