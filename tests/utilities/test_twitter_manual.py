#!/usr/bin/env python3
"""
Manual Interactive Twitter Testing Script
=========================================

This script helps you test Twitter API functionality interactively.

Prerequisites:
1. Twitter Developer account created
2. App created with Read+Write permissions
3. API keys and access tokens generated
4. Credentials added to .env file

Usage:
    python3 tests/utilities/test_twitter_manual.py

Functions Available:
- Test authentication
- Post a test tweet
- Verify tweet appears on Twitter
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

import requests
from requests_oauthlib import OAuth1


def check_credentials():
    """Check if Twitter credentials are configured."""
    print("=" * 70)
    print("STEP 1: Check Twitter Credentials")
    print("=" * 70)
    print()

    required_vars = [
        'TWITTER_TEST_API_KEY',
        'TWITTER_TEST_API_SECRET',
        'TWITTER_TEST_ACCESS_TOKEN',
        'TWITTER_TEST_ACCESS_SECRET'
    ]

    missing = []
    found = {}

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"❌ {var}: NOT FOUND")
        else:
            # Show masked value
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            found[var] = value
            print(f"✅ {var}: {masked}")

    print()

    if missing:
        print("❌ MISSING CREDENTIALS")
        print()
        print("The following environment variables are missing from .env:")
        for var in missing:
            print(f"  - {var}")
        print()
        print("Please follow the setup guide:")
        print("  /docs/TWITTER_API_SETUP_GUIDE.md")
        print()
        return None

    print("✅ All credentials found!")
    print()
    return found


def test_authentication(creds):
    """Test Twitter API authentication."""
    print("=" * 70)
    print("STEP 2: Test Authentication")
    print("=" * 70)
    print()

    try:
        # Create OAuth1 session
        oauth = OAuth1(
            client_key=creds['TWITTER_TEST_API_KEY'],
            client_secret=creds['TWITTER_TEST_API_SECRET'],
            resource_owner_key=creds['TWITTER_TEST_ACCESS_TOKEN'],
            resource_owner_secret=creds['TWITTER_TEST_ACCESS_SECRET'],
            signature_method='HMAC-SHA1',
            signature_type='auth_header'
        )

        # Test with account verification endpoint (v1.1 API)
        print("Testing authentication with Twitter API...")
        response = requests.get(
            'https://api.twitter.com/1.1/account/verify_credentials.json',
            auth=oauth,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            username = data.get('screen_name', 'unknown')
            name = data.get('name', 'unknown')
            user_id = data.get('id_str', 'unknown')

            print("✅ Authentication successful!")
            print()
            print(f"Account Details:")
            print(f"  - Username: @{username}")
            print(f"  - Display Name: {name}")
            print(f"  - User ID: {user_id}")
            print()

            return oauth, username

        elif response.status_code == 401:
            print("❌ Authentication failed: Invalid credentials")
            print()
            print("Possible issues:")
            print("  - API keys are incorrect")
            print("  - Access tokens are incorrect")
            print("  - App permissions not set to 'Read and Write'")
            print("  - Tokens generated before permission change")
            print()
            print("Fix:")
            print("  1. Check credentials in .env")
            print("  2. Verify app permissions in Twitter Developer Portal")
            print("  3. Regenerate access tokens if needed")
            print()
            return None, None

        elif response.status_code == 403:
            print("❌ Authentication failed: Forbidden")
            print()
            print("Possible issues:")
            print("  - Account suspended")
            print("  - App suspended")
            print("  - API access revoked")
            print()
            return None, None

        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            print()
            return None, None

    except requests.exceptions.Timeout:
        print("❌ Request timeout - network issue or Twitter API down")
        print()
        return None, None

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()
        return None, None


def test_post_tweet(oauth, username):
    """Test posting a tweet."""
    print("=" * 70)
    print("STEP 3: Post Test Tweet")
    print("=" * 70)
    print()

    # Confirm with user
    response = input("Post a test tweet? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Skipped.")
        return None

    # Get tweet text
    print()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    default_text = f"Test tweet from API - {timestamp}"

    tweet_text = input(f"Enter tweet text (default: '{default_text}'): ").strip()
    if not tweet_text:
        tweet_text = default_text

    # Validate length
    if len(tweet_text) > 280:
        print(f"❌ Tweet too long: {len(tweet_text)}/280 characters")
        print("Please shorten and try again.")
        return None

    print()
    print(f"Tweet text ({len(tweet_text)}/280 chars): {tweet_text}")
    print()

    confirm = input("Post this tweet? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return None

    try:
        print()
        print("Posting tweet...")

        # Use Twitter API v2
        url = "https://api.twitter.com/2/tweets"

        response = requests.post(
            url,
            auth=oauth,
            json={"text": tweet_text},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 201:
            data = response.json()
            tweet_id = data['data']['id']
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"

            print("✅ Tweet posted successfully!")
            print()
            print(f"Tweet ID: {tweet_id}")
            print(f"Tweet URL: {tweet_url}")
            print()
            print("Open this URL in your browser to verify:")
            print(f"  {tweet_url}")
            print()

            return {'id': tweet_id, 'url': tweet_url, 'text': tweet_text}

        elif response.status_code == 400:
            error_data = response.json()
            print(f"❌ Bad request: {error_data}")
            print()
            return None

        elif response.status_code == 403:
            print("❌ Forbidden - possible duplicate tweet or account restriction")
            print()
            print("Twitter blocks duplicate tweets within ~24 hours.")
            print("Try adding a timestamp or changing the text.")
            print()
            return None

        elif response.status_code == 429:
            print("❌ Rate limit exceeded")
            print()
            print("You've hit Twitter's rate limits.")
            reset_time = response.headers.get('x-rate-limit-reset', 'unknown')
            print(f"Rate limit resets at: {reset_time}")
            print()
            return None

        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            print()
            return None

    except Exception as e:
        print(f"❌ Error posting tweet: {e}")
        import traceback
        traceback.print_exc()
        print()
        return None


def test_delete_tweet(oauth):
    """Test deleting a tweet."""
    print("=" * 70)
    print("STEP 4: Delete Test Tweet (Cleanup)")
    print("=" * 70)
    print()

    tweet_id = input("Enter tweet ID to delete (or 'skip'): ").strip()

    if tweet_id.lower() == 'skip':
        print("Skipped.")
        return

    if not tweet_id.isdigit():
        print("Invalid tweet ID (must be numeric).")
        return

    confirm = input(f"Delete tweet {tweet_id}? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return

    try:
        print()
        print("Deleting tweet...")

        # Use Twitter API v2
        url = f"https://api.twitter.com/2/tweets/{tweet_id}"

        response = requests.delete(
            url,
            auth=oauth,
            timeout=30
        )

        if response.status_code == 200:
            print("✅ Tweet deleted successfully!")
            print()
        elif response.status_code == 404:
            print("❌ Tweet not found - already deleted or invalid ID")
            print()
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            print()

    except Exception as e:
        print(f"❌ Error deleting tweet: {e}")
        print()


def show_rate_limits(oauth):
    """Show current rate limit status."""
    print("=" * 70)
    print("BONUS: Check Rate Limits")
    print("=" * 70)
    print()

    try:
        response = requests.get(
            'https://api.twitter.com/1.1/application/rate_limit_status.json',
            auth=oauth,
            params={'resources': 'statuses'},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            tweet_limits = data.get('resources', {}).get('statuses', {})

            print("Current Rate Limits:")
            print()

            for endpoint, limits in tweet_limits.items():
                remaining = limits.get('remaining', 0)
                limit = limits.get('limit', 0)
                reset = limits.get('reset', 0)
                reset_time = datetime.fromtimestamp(reset).strftime("%H:%M:%S") if reset else 'unknown'

                print(f"  {endpoint}:")
                print(f"    - Remaining: {remaining}/{limit}")
                print(f"    - Resets at: {reset_time}")
                print()
        else:
            print(f"Could not fetch rate limits: {response.status_code}")
            print()

    except Exception as e:
        print(f"Error checking rate limits: {e}")
        print()


def main():
    """Main test flow."""
    print()
    print("=" * 70)
    print("Twitter API Manual Testing Script")
    print("=" * 70)
    print()
    print("This script will test your Twitter API integration.")
    print()

    # Step 1: Check credentials
    creds = check_credentials()
    if not creds:
        sys.exit(1)

    # Step 2: Test authentication
    oauth, username = test_authentication(creds)
    if not oauth:
        print()
        print("❌ Authentication failed. Cannot proceed with tests.")
        print("   Please check your credentials and try again.")
        sys.exit(1)

    # Step 3: Post test tweet
    tweet_result = test_post_tweet(oauth, username)

    # Step 4: Delete test tweet (cleanup)
    if tweet_result:
        print()
        cleanup = input("Delete the test tweet now? (yes/no): ").strip().lower()
        if cleanup == 'yes':
            test_delete_tweet(oauth)

    # Bonus: Show rate limits
    print()
    show_limits = input("Check current rate limits? (yes/no): ").strip().lower()
    if show_limits == 'yes':
        show_rate_limits(oauth)

    print()
    print("=" * 70)
    print("✅ Testing Complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - Authentication: ✅ Working")
    print("  - Post Tweet: " + ("✅ Working" if tweet_result else "⏭️ Skipped"))
    print("  - Delete Tweet: ✅ Available")
    print()
    print("Next Steps:")
    print("  1. Test via LLM prompt:")
    print("     'Tweet from test account: Testing automated posting'")
    print("  2. Verify tweet appears on Twitter")
    print("  3. Test other features (reply, quote, poll)")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("Testing interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
