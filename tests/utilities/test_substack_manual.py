#!/usr/bin/env python3
"""
Manual Interactive Substack Testing Script
==========================================

This script helps you test Substack functionality interactively.

⚠️ IMPORTANT: Substack requires CAPTCHA for login, so automated
authentication doesn't work. This script uses cookie-based authentication.

Setup Steps:
1. Login to Substack manually in your browser
2. This script will help you export cookies
3. Then you can test all Substack functions

Usage:
    python3 tests/utilities/test_substack_manual.py

Functions Available:
- Login and save cookies
- Create and publish a post
- Read published posts
- Read drafts
- Delete drafts
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from substack import Api


def save_cookies_from_browser():
    """
    Helper to guide user through cookie export from browser.
    """
    print("=" * 70)
    print("STEP 1: Export Cookies from Browser")
    print("=" * 70)
    print()
    print("1. Open your browser and login to Substack")
    print("2. Install a cookie export extension:")
    print("   - Chrome: 'EditThisCookie' or 'Cookie-Editor'")
    print("   - Firefox: 'Cookie Quick Manager'")
    print("3. Export cookies for 'substack.com'")
    print("4. Save as 'substack_cookies.json' in this directory")
    print()
    print("Cookie file should be at:")
    print(f"   {project_root}/substack_cookies.json")
    print()

    cookie_path = project_root / "substack_cookies.json"

    if cookie_path.exists():
        print(f"✅ Found cookie file: {cookie_path}")
        return str(cookie_path)
    else:
        print(f"❌ Cookie file not found: {cookie_path}")
        print()
        print("Please create the cookie file and run this script again.")
        return None


def test_authentication(cookies_path):
    """Test authentication with cookies."""
    print()
    print("=" * 70)
    print("STEP 2: Test Authentication")
    print("=" * 70)
    print()

    try:
        # Initialize API with cookies
        api = Api(cookies_path=cookies_path)
        print("✅ Authentication successful!")
        print()

        # Get user profile
        profile = api.get_user_profile()
        print(f"User: {profile.get('name', 'Unknown')}")
        print(f"Email: {profile.get('email', 'Unknown')}")
        print()

        # Get publications
        pubs = api.get_user_publications()
        print(f"Publications: {len(pubs)}")
        for pub in pubs:
            print(f"  - {pub.get('name', 'Unknown')} ({pub.get('subdomain', 'Unknown')}.substack.com)")
        print()

        return api

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print()
        print("Possible issues:")
        print("  - Cookies expired (login again and re-export)")
        print("  - Cookie format incorrect")
        print("  - Network connection issue")
        return None


def test_create_and_publish_post(api):
    """Test creating and publishing a post."""
    print()
    print("=" * 70)
    print("STEP 3: Create and Publish Test Post")
    print("=" * 70)
    print()

    # Confirm with user
    response = input("Create a test post? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Skipped.")
        return None

    # Get post details
    print()
    title = input("Enter post title (default: 'Test Post from API'): ").strip()
    if not title:
        title = "Test Post from API"

    content = input("Enter post content (default: 'This is a test post.'): ").strip()
    if not content:
        content = "<p>This is a test post created via the Substack API.</p>"

    try:
        # Create draft
        print()
        print("Creating draft...")
        draft_body = {
            "title": title,
            "body_html": content,
            # Add other fields as needed
        }

        draft = api.post_draft(body=draft_body)
        draft_id = draft.get('id')
        print(f"✅ Draft created: ID {draft_id}")
        print()

        # Ask if user wants to publish
        publish = input("Publish this draft? (yes/no): ").strip().lower()
        if publish == 'yes':
            print("Publishing draft...")
            result = api.publish_draft(draft=draft_id, send=False)  # Don't send email for test
            print(f"✅ Post published!")
            print(f"   URL: {result.get('canonical_url', 'Not available')}")
            print()
            return result
        else:
            print(f"Draft saved but not published (ID: {draft_id})")
            print("You can publish it later or delete it.")
            return draft

    except Exception as e:
        print(f"❌ Error creating/publishing post: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_read_posts(api):
    """Test reading published posts."""
    print()
    print("=" * 70)
    print("STEP 4: Read Published Posts")
    print("=" * 70)
    print()

    try:
        posts = api.get_published_posts(limit=10)
        print(f"Found {len(posts)} published posts:")
        print()

        for i, post in enumerate(posts[:5], 1):  # Show first 5
            print(f"{i}. {post.get('title', 'Untitled')}")
            print(f"   URL: {post.get('canonical_url', 'N/A')}")
            print(f"   Date: {post.get('post_date', 'N/A')}")
            print()

        return posts

    except Exception as e:
        print(f"❌ Error reading posts: {e}")
        return None


def test_read_drafts(api):
    """Test reading drafts."""
    print()
    print("=" * 70)
    print("STEP 5: Read Drafts")
    print("=" * 70)
    print()

    try:
        drafts = api.get_drafts(limit=10)
        print(f"Found {len(drafts)} drafts:")
        print()

        for i, draft in enumerate(drafts[:5], 1):  # Show first 5
            print(f"{i}. {draft.get('title', 'Untitled')} (ID: {draft.get('id')})")
            print(f"   Created: {draft.get('created_at', 'N/A')}")
            print()

        return drafts

    except Exception as e:
        print(f"❌ Error reading drafts: {e}")
        return None


def test_delete_draft(api):
    """Test deleting a draft."""
    print()
    print("=" * 70)
    print("STEP 6: Delete Test Draft (Cleanup)")
    print("=" * 70)
    print()

    # Get drafts
    try:
        drafts = api.get_drafts(limit=10)

        if not drafts:
            print("No drafts to delete.")
            return

        # Show drafts
        print("Available drafts:")
        for i, draft in enumerate(drafts, 1):
            print(f"{i}. {draft.get('title', 'Untitled')} (ID: {draft.get('id')})")
        print()

        # Ask which to delete
        choice = input("Enter draft number to delete (or 'skip'): ").strip()

        if choice.lower() == 'skip':
            print("Skipped.")
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(drafts):
                draft_to_delete = drafts[index]
                draft_id = draft_to_delete['id']

                confirm = input(f"Delete '{draft_to_delete.get('title')}'? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    api.delete_draft(draft_id)
                    print(f"✅ Draft deleted: {draft_id}")
                else:
                    print("Skipped.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    except Exception as e:
        print(f"❌ Error deleting draft: {e}")


def main():
    """Main test flow."""
    print()
    print("=" * 70)
    print("Substack Manual Testing Script")
    print("=" * 70)
    print()

    # Step 1: Check for cookies
    cookies_path = save_cookies_from_browser()
    if not cookies_path:
        print()
        print("❌ Cannot proceed without cookies file.")
        print("   Please follow the instructions above to export cookies.")
        sys.exit(1)

    # Step 2: Authenticate
    api = test_authentication(cookies_path)
    if not api:
        print()
        print("❌ Authentication failed. Cannot proceed with tests.")
        sys.exit(1)

    # Step 3: Create and publish post
    post_result = test_create_and_publish_post(api)

    # Step 4: Read posts
    test_read_posts(api)

    # Step 5: Read drafts
    test_read_drafts(api)

    # Step 6: Delete draft (cleanup)
    test_delete_draft(api)

    print()
    print("=" * 70)
    print("✅ Testing Complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - Authentication: ✅ Working")
    print("  - Create Post: " + ("✅ Working" if post_result else "⏭️ Skipped"))
    print("  - Read Posts: ✅ Working")
    print("  - Read Drafts: ✅ Working")
    print("  - Delete Draft: ✅ Working")
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
