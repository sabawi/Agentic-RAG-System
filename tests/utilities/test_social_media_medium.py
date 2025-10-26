#!/usr/bin/env python3
"""
Unit tests for Medium Social Media Handler

Tests the Medium handler implementation including:
- Token loading
- HTML sanitization
- Markdown conversion
- Content validation
- Publishing logic
- Error handling
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add plugins/handlers to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'plugins' / 'handlers'))

# Import handler
import social_media_medium


class TestTokenLoading:
    """Test integration token loading from environment variables"""

    def test_load_token_success(self, monkeypatch):
        """Test successful token loading"""
        # Set up environment
        monkeypatch.setenv('INTEGRATION_TOKEN_ENV', 'MEDIUM_TEST_TOKEN')
        monkeypatch.setenv('MEDIUM_TEST_TOKEN', 'test_token_12345')

        # Load token
        token = social_media_medium.load_integration_token()

        # Verify
        assert token == 'test_token_12345'

    def test_load_token_missing_env_var(self, monkeypatch):
        """Test token loading with missing environment variable reference"""
        # Don't set INTEGRATION_TOKEN_ENV
        token = social_media_medium.load_integration_token()

        # Should return None
        assert token is None

    def test_load_token_missing_actual_value(self, monkeypatch):
        """Test token loading when env var name is set but actual value is missing"""
        # Set environment variable name but not actual value
        monkeypatch.setenv('INTEGRATION_TOKEN_ENV', 'MEDIUM_TEST_TOKEN')
        # Don't set MEDIUM_TEST_TOKEN

        token = social_media_medium.load_integration_token()

        # Should return None
        assert token is None

    def test_sanitize_token_in_error(self):
        """Test token redaction in error messages"""
        token = 'secret_token_12345'
        error_msg = f"Authentication failed with token: {token}"

        sanitized = social_media_medium.sanitize_token_in_error(error_msg, token)

        # Verify token is redacted
        assert token not in sanitized
        assert '***TOKEN_REDACTED***' in sanitized


class TestHTMLSanitization:
    """Test HTML sanitization for XSS protection"""

    def test_sanitize_html_removes_script_tags(self):
        """Test that <script> tags are removed"""
        malicious_html = '<h1>Title</h1><script>alert("XSS")</script><p>Content</p>'

        clean_html = social_media_medium.sanitize_html(malicious_html)

        # Script tags should be removed (content may remain as plain text, which is safe)
        assert '<script>' not in clean_html
        assert '</script>' not in clean_html
        assert '<h1>Title</h1>' in clean_html
        assert '<p>Content</p>' in clean_html

    def test_sanitize_html_removes_event_handlers(self):
        """Test that event handlers are removed"""
        malicious_html = '<img src="x" onerror="alert(1)">'

        clean_html = social_media_medium.sanitize_html(malicious_html)

        assert 'onerror' not in clean_html
        assert 'alert' not in clean_html

    def test_sanitize_html_removes_javascript_protocol(self):
        """Test that javascript: protocol is removed"""
        malicious_html = '<a href="javascript:alert(1)">Click</a>'

        clean_html = social_media_medium.sanitize_html(malicious_html)

        assert 'javascript:' not in clean_html
        assert 'alert' not in clean_html

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

        clean_html = social_media_medium.sanitize_html(safe_html)

        # Verify all allowed tags are preserved
        assert '<h1>' in clean_html
        assert '<p>' in clean_html
        assert '<strong>' in clean_html
        assert '<em>' in clean_html
        assert '<ul>' in clean_html
        assert '<li>' in clean_html
        assert '<a ' in clean_html
        assert '<img ' in clean_html


class TestMarkdownConversion:
    """Test Markdown to HTML conversion"""

    def test_convert_markdown_to_html_basic(self):
        """Test basic markdown conversion"""
        markdown_content = '''
# Heading 1

This is a paragraph with **bold** and *italic* text.

## Heading 2

- List item 1
- List item 2
        '''

        html = social_media_medium.convert_markdown_to_html(markdown_content)

        # Verify conversion
        assert '<h1>' in html
        assert '<h2>' in html
        assert '<strong>' in html or '<b>' in html  # Bold
        assert '<em>' in html or '<i>' in html  # Italic
        assert '<ul>' in html
        assert '<li>' in html

    def test_convert_markdown_sanitizes_output(self):
        """Test that markdown conversion sanitizes HTML"""
        markdown_with_html = '''
# Safe Heading

<script>alert("XSS")</script>

Regular paragraph
        '''

        html = social_media_medium.convert_markdown_to_html(markdown_with_html)

        # Verify script tags removed (content may remain as plain text, which is safe)
        assert '<script>' not in html
        assert '</script>' not in html
        assert '<h1>' in html  # Safe content preserved

    def test_convert_markdown_with_code(self):
        """Test markdown with code blocks"""
        markdown_code = '''
Here is some code:

```python
def hello():
    print("Hello, World!")
```
        '''

        html = social_media_medium.convert_markdown_to_html(markdown_code)

        # Verify code blocks converted
        assert '<code>' in html or '<pre>' in html


class TestContentValidation:
    """Test content validation logic"""

    def test_validate_content_success(self):
        """Test successful content validation"""
        parameters = {
            'title': 'Test Post',
            'content': '<p>This is test content</p>',
            'publish_status': 'draft',
            'tags': ['test', 'demo']
        }

        is_valid, error = social_media_medium.validate_content(parameters)

        assert is_valid is True
        assert error is None

    def test_validate_content_missing_title(self):
        """Test validation with missing title"""
        parameters = {
            'content': '<p>This is test content</p>'
        }

        is_valid, error = social_media_medium.validate_content(parameters)

        assert is_valid is False
        assert 'title' in error.lower()
        assert 'required' in error.lower()

    def test_validate_content_title_too_long(self):
        """Test validation with title exceeding max length"""
        parameters = {
            'title': 'X' * 150,  # Exceeds 100 char limit
            'content': '<p>Content</p>'
        }

        is_valid, error = social_media_medium.validate_content(parameters)

        assert is_valid is False
        assert 'too long' in error.lower()

    def test_validate_content_missing_content(self):
        """Test validation with missing content"""
        parameters = {
            'title': 'Test Post'
        }

        is_valid, error = social_media_medium.validate_content(parameters)

        assert is_valid is False
        assert 'content' in error.lower()
        assert 'required' in error.lower()

    def test_validate_content_too_many_tags(self):
        """Test validation with too many tags"""
        parameters = {
            'title': 'Test Post',
            'content': '<p>Content</p>',
            'tags': ['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6']  # More than 5
        }

        is_valid, error = social_media_medium.validate_content(parameters)

        assert is_valid is False
        assert 'tag' in error.lower()

    def test_validate_content_tag_too_long(self):
        """Test validation with tag exceeding max length"""
        parameters = {
            'title': 'Test Post',
            'content': '<p>Content</p>',
            'tags': ['X' * 30]  # Exceeds 25 char limit
        }

        is_valid, error = social_media_medium.validate_content(parameters)

        assert is_valid is False
        assert 'tag' in error.lower()
        assert 'too long' in error.lower()

    def test_validate_content_invalid_format(self):
        """Test validation with invalid content format"""
        parameters = {
            'title': 'Test Post',
            'content': '<p>Content</p>',
            'content_format': 'invalid_format'
        }

        is_valid, error = social_media_medium.validate_content(parameters)

        assert is_valid is False
        assert 'content_format' in error.lower()

    def test_validate_content_invalid_publish_status(self):
        """Test validation with invalid publish status"""
        parameters = {
            'title': 'Test Post',
            'content': '<p>Content</p>',
            'publish_status': 'invalid_status'
        }

        is_valid, error = social_media_medium.validate_content(parameters)

        assert is_valid is False
        assert 'publish_status' in error.lower()


class TestExecuteFunction:
    """Test main execute function"""

    @pytest.mark.asyncio
    async def test_execute_missing_token(self, monkeypatch):
        """Test execution with missing integration token"""
        # Don't set any environment variables
        result = await social_media_medium.execute({
            'title': 'Test',
            'content': '<p>Content</p>'
        })

        assert result['success'] is False
        assert 'token' in result['error'].lower()
        assert 'metadata' in result
        assert result['metadata']['error_category'] == 'configuration'

    @pytest.mark.asyncio
    async def test_execute_validation_error(self, monkeypatch):
        """Test execution with validation error"""
        # Set token
        monkeypatch.setenv('INTEGRATION_TOKEN_ENV', 'MEDIUM_TEST_TOKEN')
        monkeypatch.setenv('MEDIUM_TEST_TOKEN', 'test_token')

        # Missing required field
        result = await social_media_medium.execute({
            'content': '<p>Content</p>'  # Missing title
        })

        assert result['success'] is False
        assert 'title' in result['error'].lower()
        assert result['metadata']['error_category'] == 'validation'

    @pytest.mark.asyncio
    async def test_execute_sanitizes_html(self, monkeypatch):
        """Test that execute sanitizes HTML content"""
        # Set token
        monkeypatch.setenv('INTEGRATION_TOKEN_ENV', 'MEDIUM_TEST_TOKEN')
        monkeypatch.setenv('MEDIUM_TEST_TOKEN', 'test_token')

        # Mock the publish_to_medium function
        async def mock_publish(*args, **kwargs):
            content = kwargs.get('content', '')

            # Verify dangerous tags have been removed
            # (text content may remain but that's safe without the tags)
            assert '<script>' not in content
            assert '</script>' not in content

            return {
                "success": True,
                "result": {
                    "post_url": "https://medium.com/@test/test-post",
                    "post_id": "12345",
                    "title": kwargs.get('title', ''),
                    "platform": "medium",
                    "publish_status": kwargs.get('publish_status', 'draft'),
                    "tags": kwargs.get('tags', [])
                },
                "error": None
            }

        with patch.object(social_media_medium, 'publish_to_medium', mock_publish):
            result = await social_media_medium.execute({
                'title': 'Test',
                'content': '<p>Content</p><script>alert("XSS")</script>'
            })

            # Should succeed with sanitized content
            assert result['success'] is True

    @pytest.mark.asyncio
    async def test_execute_markdown_conversion(self, monkeypatch):
        """Test that execute converts markdown to HTML"""
        # Set token
        monkeypatch.setenv('INTEGRATION_TOKEN_ENV', 'MEDIUM_TEST_TOKEN')
        monkeypatch.setenv('MEDIUM_TEST_TOKEN', 'test_token')

        # Mock the publish_to_medium function
        async def mock_publish(*args, **kwargs):
            content = kwargs.get('content', '')

            # Verify markdown was converted to HTML
            assert '<h1>' in content  # Markdown heading converted
            assert '<strong>' in content or '<b>' in content  # Bold converted

            return {
                "success": True,
                "result": {
                    "post_url": "https://medium.com/@test/test-post",
                    "post_id": "12345",
                    "title": kwargs.get('title', ''),
                    "platform": "medium",
                    "publish_status": kwargs.get('publish_status', 'draft'),
                    "tags": kwargs.get('tags', [])
                },
                "error": None
            }

        with patch.object(social_media_medium, 'publish_to_medium', mock_publish):
            result = await social_media_medium.execute({
                'title': 'Test',
                'content': '# Heading\n\n**Bold text**',
                'content_format': 'markdown'
            })

            # Should succeed with converted content
            assert result['success'] is True


class TestGetUserId:
    """Test Medium user ID retrieval"""

    @pytest.mark.asyncio
    async def test_get_user_id_success(self):
        """Test successful user ID retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'id': 'user123', 'username': 'testuser'}
        }

        with patch('requests.get', return_value=mock_response):
            result = await social_media_medium.get_user_id('test_token')

            assert result['success'] is True
            assert result['result'] == 'user123'

    @pytest.mark.asyncio
    async def test_get_user_id_invalid_token(self):
        """Test user ID retrieval with invalid token"""
        mock_response = Mock()
        mock_response.status_code = 401

        with patch('requests.get', return_value=mock_response):
            result = await social_media_medium.get_user_id('invalid_token')

            assert result['success'] is False
            assert 'authentication' in result['error'].lower() or 'invalid' in result['error'].lower()


# =============================================================================
# Integration Test Placeholder
# =============================================================================

class TestIntegration:
    """Integration tests (require actual Medium token)"""

    @pytest.mark.skip(reason="Requires real Medium account - run manually")
    @pytest.mark.asyncio
    async def test_real_publish(self, monkeypatch):
        """
        Test actual publishing to Medium.

        To run this test:
        1. Get integration token from https://medium.com/me/settings/security
        2. Set MEDIUM_TEST_TOKEN in .env
        3. Run: pytest tests/utilities/test_social_media_medium.py::TestIntegration::test_real_publish -v
        """
        # Set token from environment
        monkeypatch.setenv('INTEGRATION_TOKEN_ENV', 'MEDIUM_TEST_TOKEN')

        result = await social_media_medium.execute({
            'title': 'Test Post from Unit Tests',
            'content': '''
                # Test Heading

                This is a test post created by automated tests.

                - Item 1
                - Item 2

                **Bold text** and *italic text*.
            ''',
            'content_format': 'markdown',
            'publish_status': 'draft',  # Don't publish publicly
            'tags': ['test', 'automated'],
            'notify_followers': False
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
