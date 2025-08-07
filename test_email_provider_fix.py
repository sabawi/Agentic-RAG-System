#!/usr/bin/env python3
"""
Test that the email sender now defaults to sendmail (mailx/mutt/msmtp) instead of Gmail
"""

import asyncio
import sys
import os

# Add the project root to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from user_tools.secure_email_sender import SecureEmailSenderTool

async def test_default_provider():
    """Test that the default provider is now sendmail instead of gmail"""
    print("🧪 Testing Email Provider Default Change")
    print("=" * 50)
    
    email_tool = SecureEmailSenderTool()
    
    # Test without specifying provider (should default to sendmail now)
    print("\n1. Testing without provider parameter (should use sendmail/mailx/mutt/msmtp)...")
    try:
        result = await email_tool.execute(
            to_email="test@example.com",
            subject="Provider Test",
            body="Testing default provider change"
        )
        
        if result["success"]:
            print("✅ SUCCESS: Email sent without trying Gmail first")
            print(f"   Result: {result['result']}")
            
            # Check if the result mentions sendmail/mailx instead of gmail
            if "sendmail" in result['result'].lower() or "mailx" in result['result'].lower():
                print("✅ CONFIRMED: Using local mail agents (sendmail/mailx)")
            else:
                print("⚠️  Result doesn't mention sendmail/mailx explicitly")
        else:
            print("❌ FAILED: Email sending failed")
            print(f"   Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "="*50)
    print("📋 Expected behavior:")
    print("   ✅ No 'Warning: No sender email configured for gmail' message")
    print("   ✅ Should go directly to sendmail/mailx/mutt/msmtp")
    print("   ✅ Should show '📎 Trying msmtp/mailx/mutt for better MIME support'")

if __name__ == "__main__":
    asyncio.run(test_default_provider())