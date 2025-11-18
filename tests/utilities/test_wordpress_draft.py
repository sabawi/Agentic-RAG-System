#!/usr/bin/env python3
"""
Test WordPress Draft Publishing
Simple test to verify WordPress configuration is working.
"""

import sys
import os
import json
import asyncio

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the WordPress handler
from plugins.handlers.social_media_wordpress import execute

async def test_wordpress_draft():
    """Test publishing a simple draft to WordPress."""

    # Set environment variables for the plugin
    os.environ['WORDPRESS_URL_ENV'] = 'WORDPRESS_URL'
    os.environ['WORDPRESS_USERNAME_ENV'] = 'WORDPRESS_USERNAME'
    os.environ['WORDPRESS_APP_PASSWORD_ENV'] = 'WORDPRESS_APP_PASSWORD'

    # Test parameters
    test_params = {
        "title": "Test Draft Post from Agentic RAG System",
        "content": """# Test Post

This is a **test post** created by the Agentic RAG System to verify WordPress configuration.

## Purpose
- Verify WordPress credentials are working
- Test draft publishing functionality
- Confirm plugin integration

## Test Details
- Status: Draft
- Platform: WordPress.com
- Date: 2025-11-16

This post should appear in your WordPress dashboard as a **draft** and should NOT be published publicly.

---
*Posted via Agentic RAG System v1.0.3.102*
""",
        "status": "draft",
        "categories": ["Testing"],
        "tags": ["test", "agentic-rag", "automation"]
    }

    print("🧪 Testing WordPress Configuration...")
    print(f"📝 Title: {test_params['title']}")
    print(f"📊 Status: {test_params['status']}")
    print(f"🏷️  Categories: {test_params['categories']}")
    print(f"🔖 Tags: {test_params['tags']}")
    print()

    try:
        result = await execute(test_params)

        if result['success']:
            print("✅ SUCCESS! WordPress draft created successfully!")
            print()
            print("📊 Result Details:")
            print(f"   Post ID: {result['result'].get('post_id', 'N/A')}")
            print(f"   Title: {result['result'].get('title', 'N/A')}")
            print(f"   Platform: {result['result'].get('platform', 'N/A')}")
            print(f"   Status: {result['result'].get('status', 'N/A')}")
            if 'post_url' in result['result']:
                print(f"   URL: {result['result']['post_url']}")
            print()
            print("   Execution time: {:.2f}s".format(result.get('metadata', {}).get('execution_time', 0)))
            print()
            print("🎉 WordPress configuration is working correctly!")
            print("   Check your WordPress dashboard to see the draft post.")
            return True
        else:
            print("❌ FAILED! WordPress posting failed.")
            print()
            print("Error Details:")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Category: {result.get('metadata', {}).get('error_category', 'unknown')}")
            print()
            print("Common issues:")
            print("  - Check WordPress credentials in .env file")
            print("  - Verify Application Password is correct (not regular password)")
            print("  - Ensure WordPress site is accessible")
            print("  - Check WordPress.com API status")
            return False

    except Exception as e:
        print(f"❌ EXCEPTION! Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        print()
        print("   Check the error message above for details.")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("WordPress Draft Publishing Test")
    print("=" * 70)
    print()

    success = asyncio.run(test_wordpress_draft())

    print()
    print("=" * 70)
    if success:
        print("✅ Test PASSED - WordPress is configured correctly!")
    else:
        print("❌ Test FAILED - Fix the issues above and try again")
    print("=" * 70)

    sys.exit(0 if success else 1)
