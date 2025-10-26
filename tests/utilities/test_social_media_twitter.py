#!/usr/bin/env python3
"""
Unit tests for Twitter/X Social Media Handler

Tests the Twitter handler implementation including:
- OAuth credential loading
- Content validation
- Tweet posting
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
import social_media_twitter


class TestCredentialLoading:
    """Test OAuth credential loading from environment variables"""

    def test_load_credentials_success(self, monkeypatch):
        """Test successful credential loading"""
        # Set up environment
        monkeypatch.setenv('API_KEY_ENV', 'TWITTER_TEST_API_KEY')
        monkeypatch.setenv('API_SECRET_ENV', 'TWITTER_TEST_API_SECRET')
        monkeypatch.setenv('ACCESS_TOKEN_ENV', 'TWITTER_TEST_ACCESS_TOKEN')
        monkeypatch.setenv('ACCESS_SECRET_ENV', 'TWITTER_TEST_ACCESS_SECRET')

        monkeypatch.setenv('TWITTER_TEST_API_KEY', 'test_api_key')
        monkeypatch.setenv('TWITTER_TEST_API_SECRET', 'test_api_secret')
        monkeypatch.setenv('TWITTER_TEST_ACCESS_TOKEN', 'test_access_token')
        monkeypatch.setenv('TWITTER_TEST_ACCESS_SECRET', 'test_access_secret')

        # Load credentials
        api_key, api_secret, access_token, access_secret = social_media_twitter.load_credentials()

        # Verify
        assert api_key == 'test_api_key'
        assert api_secret == 'test_api_secret'
        assert access_token == 'test_access_token'
        assert access_secret == 'test_access_secret'

    def test_load_credentials_missing_env_vars(self, monkeypatch):
        """Test credential loading with missing environment variable references"""
        # Don't set any environment variables
        api_key, api_secret, access_token, access_secret = social_media_twitter.load_credentials()

        # Should return None for all
        assert api_key is None
        assert api_secret is None
        assert access_token is None
        assert access_secret is None

    def test_load_credentials_missing_actual_values(self, monkeypatch):
        """Test credential loading when env var names are set but actual values are missing"""
        # Set environment variable names but not actual values
        monkeypatch.setenv('API_KEY_ENV', 'TWITTER_TEST_API_KEY')
        monkeypatch.setenv('API_SECRET_ENV', 'TWITTER_TEST_API_SECRET')
        monkeypatch.setenv('ACCESS_TOKEN_ENV', 'TWITTER_TEST_ACCESS_TOKEN')
        monkeypatch.setenv('ACCESS_SECRET_ENV', 'TWITTER_TEST_ACCESS_SECRET')
        # Don't set actual values

        api_key, api_secret, access_token, access_secret = social_media_twitter.load_credentials()

        # Should return None for all
        assert api_key is None
        assert api_secret is None
        assert access_token is None
        assert access_secret is None

    def test_sanitize_credentials_in_error(self):
        """Test credential redaction in error messages"""
        api_key = 'secret_api_key'
        api_secret = 'secret_api_secret'
        access_token = 'secret_access_token'
        access_secret = 'secret_access_secret'

        error_msg = f"Auth failed with key: {api_key}, secret: {api_secret}, token: {access_token}, secret: {access_secret}"

        sanitized = social_media_twitter.sanitize_credentials_in_error(
            error_msg, api_key, api_secret, access_token, access_secret
        )

        # Verify credentials are redacted
        assert api_key not in sanitized
        assert api_secret not in sanitized
        assert access_token not in sanitized
        assert access_secret not in sanitized
        assert 'CREDENTIAL' in sanitized
        assert 'REDACTED' in sanitized


class TestContentValidation:
    """Test content validation logic"""

    def test_validate_content_success(self):
        """Test successful content validation"""
        parameters = {
            'text': 'This is a test tweet',
            'reply_settings': 'everyone'
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is True
        assert error is None

    def test_validate_content_missing_text(self):
        """Test validation with missing text"""
        parameters = {}

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'text' in error.lower()
        assert 'required' in error.lower()

    def test_validate_content_text_too_long(self):
        """Test validation with text exceeding max length"""
        parameters = {
            'text': 'X' * 2900  # Exceeds 2800 char limit
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'too long' in error.lower()

    def test_validate_content_too_many_media(self):
        """Test validation with too many media attachments"""
        parameters = {
            'text': 'Test tweet',
            'media_urls': [
                'https://example.com/1.jpg',
                'https://example.com/2.jpg',
                'https://example.com/3.jpg',
                'https://example.com/4.jpg',
                'https://example.com/5.jpg'  # 5 is too many
            ]
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'media' in error.lower()

    def test_validate_content_invalid_media_url(self):
        """Test validation with invalid media URL"""
        parameters = {
            'text': 'Test tweet',
            'media_urls': ['not-a-url']
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'url' in error.lower()

    def test_validate_content_poll_too_few_options(self):
        """Test validation with poll having too few options"""
        parameters = {
            'text': 'Test tweet',
            'poll_options': ['Only one option']
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'poll' in error.lower()
        assert '2' in error

    def test_validate_content_poll_too_many_options(self):
        """Test validation with poll having too many options"""
        parameters = {
            'text': 'Test tweet',
            'poll_options': ['Option 1', 'Option 2', 'Option 3', 'Option 4', 'Option 5']
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'poll' in error.lower()

    def test_validate_content_poll_option_too_long(self):
        """Test validation with poll option exceeding max length"""
        parameters = {
            'text': 'Test tweet',
            'poll_options': ['Short', 'X' * 30]  # Second option exceeds 25 char limit
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'poll' in error.lower()
        assert 'too long' in error.lower()

    def test_validate_content_invalid_poll_duration(self):
        """Test validation with invalid poll duration"""
        parameters = {
            'text': 'Test tweet',
            'poll_options': ['Option 1', 'Option 2'],
            'poll_duration_minutes': 15000  # Exceeds max 10080
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'duration' in error.lower()

    def test_validate_content_invalid_reply_settings(self):
        """Test validation with invalid reply settings"""
        parameters = {
            'text': 'Test tweet',
            'reply_settings': 'invalid_value'
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'reply_settings' in error.lower()

    def test_validate_content_invalid_reply_to_id(self):
        """Test validation with invalid reply_to_tweet_id"""
        parameters = {
            'text': 'Test tweet',
            'reply_to_tweet_id': 'not-a-number'
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'reply_to_tweet_id' in error.lower()

    def test_validate_content_invalid_quote_tweet_id(self):
        """Test validation with invalid quote_tweet_id"""
        parameters = {
            'text': 'Test tweet',
            'quote_tweet_id': 'not-a-number'
        }

        is_valid, error = social_media_twitter.validate_content(parameters)

        assert is_valid is False
        assert 'quote_tweet_id' in error.lower()


class TestOAuthSession:
    """Test OAuth session creation"""

    def test_create_oauth1_session(self):
        """Test OAuth1 session creation"""
        from requests_oauthlib import OAuth1

        oauth = social_media_twitter.create_oauth1_session(
            'api_key', 'api_secret', 'access_token', 'access_secret'
        )

        # Verify OAuth1 object created
        assert oauth is not None
        assert isinstance(oauth, OAuth1)


class TestExecuteFunction:
    """Test main execute function"""

    @pytest.mark.asyncio
    async def test_execute_missing_credentials(self, monkeypatch):
        """Test execution with missing OAuth credentials"""
        # Don't set any environment variables
        result = await social_media_twitter.execute({
            'text': 'Test tweet'
        })

        assert result['success'] is False
        assert 'credential' in result['error'].lower()
        assert 'metadata' in result
        assert result['metadata']['error_category'] == 'configuration'

    @pytest.mark.asyncio
    async def test_execute_validation_error(self, monkeypatch):
        """Test execution with validation error"""
        # Set credentials
        monkeypatch.setenv('API_KEY_ENV', 'TWITTER_TEST_API_KEY')
        monkeypatch.setenv('API_SECRET_ENV', 'TWITTER_TEST_API_SECRET')
        monkeypatch.setenv('ACCESS_TOKEN_ENV', 'TWITTER_TEST_ACCESS_TOKEN')
        monkeypatch.setenv('ACCESS_SECRET_ENV', 'TWITTER_TEST_ACCESS_SECRET')

        monkeypatch.setenv('TWITTER_TEST_API_KEY', 'test_key')
        monkeypatch.setenv('TWITTER_TEST_API_SECRET', 'test_secret')
        monkeypatch.setenv('TWITTER_TEST_ACCESS_TOKEN', 'test_token')
        monkeypatch.setenv('TWITTER_TEST_ACCESS_SECRET', 'test_access')

        # Missing required field
        result = await social_media_twitter.execute({})  # Missing text

        assert result['success'] is False
        assert 'text' in result['error'].lower()
        assert result['metadata']['error_category'] == 'validation'

    @pytest.mark.asyncio
    async def test_execute_success(self, monkeypatch):
        """Test successful tweet posting"""
        # Set credentials
        monkeypatch.setenv('API_KEY_ENV', 'TWITTER_TEST_API_KEY')
        monkeypatch.setenv('API_SECRET_ENV', 'TWITTER_TEST_API_SECRET')
        monkeypatch.setenv('ACCESS_TOKEN_ENV', 'TWITTER_TEST_ACCESS_TOKEN')
        monkeypatch.setenv('ACCESS_SECRET_ENV', 'TWITTER_TEST_ACCESS_SECRET')

        monkeypatch.setenv('TWITTER_TEST_API_KEY', 'test_key')
        monkeypatch.setenv('TWITTER_TEST_API_SECRET', 'test_secret')
        monkeypatch.setenv('TWITTER_TEST_ACCESS_TOKEN', 'test_token')
        monkeypatch.setenv('TWITTER_TEST_ACCESS_SECRET', 'test_access')

        # Mock the post_tweet function
        async def mock_post_tweet(*args, **kwargs):
            return {
                "success": True,
                "result": {
                    "tweet_url": "https://twitter.com/i/web/status/123456",
                    "tweet_id": "123456",
                    "text": kwargs.get('text', ''),
                    "platform": "twitter",
                    "reply_settings": kwargs.get('reply_settings', 'everyone')
                },
                "error": None
            }

        with patch.object(social_media_twitter, 'post_tweet', mock_post_tweet):
            result = await social_media_twitter.execute({
                'text': 'This is a test tweet!'
            })

            # Should succeed
            assert result['success'] is True
            assert result['result']['tweet_id'] == '123456'
            assert result['result']['platform'] == 'twitter'
            assert 'metadata' in result
            assert result['metadata']['character_count'] == len('This is a test tweet!')


class TestPostTweet:
    """Test tweet posting function"""

    @pytest.mark.asyncio
    async def test_post_tweet_success(self):
        """Test successful tweet posting"""
        mock_oauth = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {
                'id': '123456789',
                'text': 'Test tweet'
            }
        }

        with patch('requests.post', return_value=mock_response):
            result = await social_media_twitter.post_tweet(
                oauth=mock_oauth,
                text='Test tweet'
            )

            assert result['success'] is True
            assert result['result']['tweet_id'] == '123456789'

    @pytest.mark.asyncio
    async def test_post_tweet_auth_error(self):
        """Test tweet posting with authentication error"""
        mock_oauth = Mock()
        mock_response = Mock()
        mock_response.status_code = 401

        with patch('requests.post', return_value=mock_response):
            result = await social_media_twitter.post_tweet(
                oauth=mock_oauth,
                text='Test tweet'
            )

            assert result['success'] is False
            assert 'authentication' in result['error'].lower()
            assert result['error_category'] == 'authentication'

    @pytest.mark.asyncio
    async def test_post_tweet_rate_limit(self):
        """Test tweet posting with rate limit error"""
        mock_oauth = Mock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'x-rate-limit-reset': '1234567890'}

        with patch('requests.post', return_value=mock_response):
            result = await social_media_twitter.post_tweet(
                oauth=mock_oauth,
                text='Test tweet'
            )

            assert result['success'] is False
            assert 'rate limit' in result['error'].lower()
            assert result['error_category'] == 'rate_limit'


# =============================================================================
# Integration Test Placeholder
# =============================================================================

class TestIntegration:
    """Integration tests (require actual Twitter credentials)"""

    @pytest.mark.skip(reason="Requires real Twitter account - run manually")
    @pytest.mark.asyncio
    async def test_real_tweet(self, monkeypatch):
        """
        Test actual tweet posting to Twitter.

        To run this test:
        1. Get API credentials from https://developer.twitter.com/
        2. Set TWITTER_TEST_* variables in .env
        3. Run: pytest tests/utilities/test_social_media_twitter.py::TestIntegration::test_real_tweet -v
        """
        # Set credentials from environment
        monkeypatch.setenv('API_KEY_ENV', 'TWITTER_TEST_API_KEY')
        monkeypatch.setenv('API_SECRET_ENV', 'TWITTER_TEST_API_SECRET')
        monkeypatch.setenv('ACCESS_TOKEN_ENV', 'TWITTER_TEST_ACCESS_TOKEN')
        monkeypatch.setenv('ACCESS_SECRET_ENV', 'TWITTER_TEST_ACCESS_SECRET')

        result = await social_media_twitter.execute({
            'text': 'Test tweet from automated tests - please ignore! 🤖',
            'reply_settings': 'everyone'
        })

        # Verify result structure
        assert 'success' in result
        assert 'result' in result or 'error' in result
        assert 'metadata' in result

        if result['success']:
            assert result['result']['tweet_url']
            assert result['result']['tweet_id']
            print(f"\n✅ Successfully posted: {result['result']['tweet_url']}")
        else:
            print(f"\n❌ Posting failed: {result['error']}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v'])
