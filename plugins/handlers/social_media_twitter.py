#!/usr/bin/env python3
"""
Social Media Plugin - Twitter/X Handler
Handles publishing tweets to Twitter/X with OAuth 1.0a authentication.

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
    import requests
    from requests_oauthlib import OAuth1
except ImportError as e:
    print(json.dumps({
        "success": False,
        "result": None,
        "error": f"Missing required dependency: {str(e)}. Install with: pip install requests requests-oauthlib"
    }))
    sys.exit(1)


# =============================================================================
# Twitter API Configuration
# =============================================================================

TWITTER_API_BASE = "https://api.twitter.com"
TWITTER_API_VERSION = "2"


# =============================================================================
# Credential Management
# =============================================================================

def load_credentials() -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Load Twitter OAuth credentials from environment variables.

    The YAML file specifies which env vars to look for:
    - API_KEY_ENV points to actual API key var
    - API_SECRET_ENV points to actual API secret var
    - ACCESS_TOKEN_ENV points to actual access token var
    - ACCESS_SECRET_ENV points to actual access secret var

    Returns:
        (api_key, api_secret, access_token, access_secret) or (None, None, None, None) if missing
    """
    # Get the names of the env vars from the execution environment
    api_key_env = os.getenv('API_KEY_ENV')
    api_secret_env = os.getenv('API_SECRET_ENV')
    access_token_env = os.getenv('ACCESS_TOKEN_ENV')
    access_secret_env = os.getenv('ACCESS_SECRET_ENV')

    if not all([api_key_env, api_secret_env, access_token_env, access_secret_env]):
        return (None, None, None, None)

    # Now get the actual values
    api_key = os.getenv(api_key_env)
    api_secret = os.getenv(api_secret_env)
    access_token = os.getenv(access_token_env)
    access_secret = os.getenv(access_secret_env)

    return (api_key, api_secret, access_token, access_secret)


def sanitize_credentials_in_error(error_msg: str, *credentials) -> str:
    """
    Remove any credential values from error messages.

    Args:
        error_msg: Original error message
        *credentials: Variable number of credentials to redact

    Returns:
        Sanitized error message
    """
    for i, cred in enumerate(credentials):
        if cred:
            error_msg = error_msg.replace(cred, f"***CREDENTIAL_{i+1}_REDACTED***")
    return error_msg


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
    text = parameters.get('text', '')

    # Text validation
    if not text:
        return (False, "Tweet text is required")
    if len(text) > 2800:  # Allow up to 10x normal for threads/Twitter Blue
        return (False, f"Tweet text too long: {len(text)} chars (max 2800)")

    # Media URLs validation
    media_urls = parameters.get('media_urls', [])
    if len(media_urls) > 4:
        return (False, f"Too many media attachments: {len(media_urls)} (max 4)")

    for url in media_urls:
        if not url.startswith(('http://', 'https://')):
            return (False, f"Invalid media URL: {url}")

    # Poll validation
    poll_options = parameters.get('poll_options', [])
    if poll_options:
        if len(poll_options) < 2:
            return (False, "Poll must have at least 2 options")
        if len(poll_options) > 4:
            return (False, f"Too many poll options: {len(poll_options)} (max 4)")

        for option in poll_options:
            if len(option) > 25:
                return (False, f"Poll option too long: '{option}' ({len(option)} chars, max 25)")

        # Validate poll duration
        duration = parameters.get('poll_duration_minutes', 1440)
        if duration < 5 or duration > 10080:
            return (False, f"Poll duration must be between 5 and 10080 minutes (got {duration})")

    # Reply settings validation
    reply_settings = parameters.get('reply_settings', 'everyone')
    valid_reply_settings = ['everyone', 'following', 'mentioned']
    if reply_settings not in valid_reply_settings:
        return (False, f"Invalid reply_settings: {reply_settings}. Must be one of: {', '.join(valid_reply_settings)}")

    # Tweet ID validation (if provided)
    reply_to_id = parameters.get('reply_to_tweet_id')
    if reply_to_id and not reply_to_id.isdigit():
        return (False, f"Invalid reply_to_tweet_id: must be numeric")

    quote_tweet_id = parameters.get('quote_tweet_id')
    if quote_tweet_id and not quote_tweet_id.isdigit():
        return (False, f"Invalid quote_tweet_id: must be numeric")

    return (True, None)


# =============================================================================
# Twitter API Integration
# =============================================================================

def create_oauth1_session(api_key: str, api_secret: str, access_token: str, access_secret: str) -> OAuth1:
    """
    Create OAuth 1.0a session for Twitter API.

    Args:
        api_key: Twitter API key (consumer key)
        api_secret: Twitter API secret (consumer secret)
        access_token: Twitter access token
        access_secret: Twitter access token secret

    Returns:
        OAuth1 auth object for requests
    """
    return OAuth1(
        client_key=api_key,
        client_secret=api_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
        signature_method='HMAC-SHA1',
        signature_type='auth_header'
    )


async def post_tweet(
    oauth: OAuth1,
    text: str,
    media_urls: list = None,
    reply_to_tweet_id: Optional[str] = None,
    quote_tweet_id: Optional[str] = None,
    poll_options: list = None,
    poll_duration_minutes: int = 1440,
    reply_settings: str = "everyone"
) -> Dict[str, Any]:
    """
    Post tweet to Twitter/X.

    Args:
        oauth: OAuth1 authentication object
        text: Tweet text
        media_urls: List of media URLs to attach
        reply_to_tweet_id: Tweet ID to reply to
        quote_tweet_id: Tweet ID to quote
        poll_options: Poll options (creates a poll)
        poll_duration_minutes: Poll duration
        reply_settings: Who can reply

    Returns:
        Result dictionary with success status and tweet details
    """
    try:
        # Prepare tweet data
        tweet_data = {
            "text": text
        }

        # Add media if provided
        if media_urls:
            # Note: In production, you would need to upload media first
            # and get media_ids, then attach them. For simplicity, we're
            # documenting this limitation.
            pass  # Media upload requires separate API calls

        # Add reply
        if reply_to_tweet_id:
            tweet_data["reply"] = {
                "in_reply_to_tweet_id": reply_to_tweet_id
            }

        # Add quote tweet
        if quote_tweet_id:
            tweet_data["quote_tweet_id"] = quote_tweet_id

        # Add poll
        if poll_options and len(poll_options) >= 2:
            tweet_data["poll"] = {
                "options": poll_options,
                "duration_minutes": poll_duration_minutes
            }

        # Add reply settings
        if reply_settings != "everyone":
            tweet_data["reply_settings"] = reply_settings

        # Make API request
        url = f"{TWITTER_API_BASE}/{TWITTER_API_VERSION}/tweets"

        response = requests.post(
            url,
            auth=oauth,
            json=tweet_data,
            headers={
                "Content-Type": "application/json"
            },
            timeout=30
        )

        # Handle response
        if response.status_code == 401:
            return {
                "success": False,
                "result": None,
                "error": "Authentication failed: Invalid OAuth credentials",
                "error_category": "authentication"
            }

        if response.status_code == 403:
            return {
                "success": False,
                "result": None,
                "error": "Forbidden: Check API permissions and account status",
                "error_category": "authorization"
            }

        if response.status_code == 429:
            # Check rate limit headers
            reset_time = response.headers.get('x-rate-limit-reset', 'unknown')
            return {
                "success": False,
                "result": None,
                "error": f"Rate limit exceeded. Resets at: {reset_time}",
                "error_category": "rate_limit"
            }

        response.raise_for_status()
        data = response.json()

        # Extract tweet details
        tweet_info = data.get('data', {})
        tweet_id = tweet_info.get('id', '')
        tweet_text = tweet_info.get('text', text)

        # Construct tweet URL
        # Note: We'd need to get username from another API call for full URL
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}" if tweet_id else ""

        return {
            "success": True,
            "result": {
                "tweet_url": tweet_url,
                "tweet_id": tweet_id,
                "text": tweet_text,
                "platform": "twitter",
                "reply_settings": reply_settings
            },
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "result": None,
            "error": "Request timeout while posting to Twitter",
            "error_category": "timeout"
        }
    except requests.exceptions.RequestException as e:
        error_msg = str(e)

        # Categorize error
        error_category = "unknown"
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            error_category = "authentication"
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            error_category = "authorization"
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
                "character_count": int,
                ...
            }
        }
    """
    start_time = time.time()

    try:
        # 1. Load credentials
        api_key, api_secret, access_token, access_secret = load_credentials()

        if not all([api_key, api_secret, access_token, access_secret]):
            return {
                "success": False,
                "result": None,
                "error": "Missing OAuth credentials. Check .env file for TWITTER_TEST_* variables.",
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

        # 3. Extract parameters
        text = parameters['text']
        media_urls = parameters.get('media_urls', [])
        reply_to_tweet_id = parameters.get('reply_to_tweet_id')
        quote_tweet_id = parameters.get('quote_tweet_id')
        poll_options = parameters.get('poll_options')
        poll_duration_minutes = parameters.get('poll_duration_minutes', 1440)
        reply_settings = parameters.get('reply_settings', 'everyone')

        # 4. Create OAuth session
        oauth = create_oauth1_session(api_key, api_secret, access_token, access_secret)

        # 5. Post tweet
        result = await post_tweet(
            oauth=oauth,
            text=text,
            media_urls=media_urls,
            reply_to_tweet_id=reply_to_tweet_id,
            quote_tweet_id=quote_tweet_id,
            poll_options=poll_options,
            poll_duration_minutes=poll_duration_minutes,
            reply_settings=reply_settings
        )

        # 6. Add metadata
        execution_time = time.time() - start_time

        if result['success']:
            result['metadata'] = {
                "execution_time": execution_time,
                "account_type": os.getenv('ACCOUNT_TYPE', 'unknown'),
                "character_count": len(text),
                "has_media": len(media_urls) > 0,
                "has_poll": poll_options is not None,
                "is_reply": reply_to_tweet_id is not None,
                "is_quote": quote_tweet_id is not None
            }
        else:
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['execution_time'] = execution_time

        return result

    except Exception as e:
        # Catch any unexpected errors
        api_key, api_secret, access_token, access_secret = load_credentials()
        error_msg = sanitize_credentials_in_error(
            str(e), api_key, api_secret, access_token, access_secret
        )

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
