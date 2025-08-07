#!/usr/bin/env python3
"""
Simple test to verify email attachments work
"""

import asyncio
import sys
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

async def test_simple_attachment():
    """Test creating a file and emailing it as attachment"""
    print("🧪 Simple Attachment Test")
    print("=" * 40)
    
    # Step 1: Create a simple test file
    from user_tools.sandboxed_executor import SandboxedExecutorTool
    executor = SandboxedExecutorTool()
    
    test_content = """NVIDIA Stock Analysis Summary

Stock: NVDA
Price: $173.72
Recommendation: BUY
Date: 2025-08-03

This is a test attachment to verify email functionality works correctly.
"""
    
    print("1. Creating test file...")
    file_result = await executor.execute(
        action="create_file",
        filename="test_attachment.txt",
        content=test_content
    )
    
    if file_result["success"]:
        print(f"✅ File created: {file_result['result']['filename']}")
        
        # Step 2: Send email with attachment
        print("2. Sending email with attachment...")
        from user_tools.secure_email_sender import SecureEmailSenderTool
        email_sender = SecureEmailSenderTool()
        
        email_result = await email_sender.execute(
            to_email="sabawi@gmail.com",
            subject="Test Email with Attachment",
            body="This is a test email to verify attachment functionality works.\n\nThe attached file should contain a simple stock analysis summary.",
            attachments="test_attachment.txt"  # This should work since file is in sandbox
        )
        
        if email_result["success"]:
            print("✅ Email sent successfully!")
            print(f"   Result: {email_result['result']}")
        else:
            print(f"❌ Email failed: {email_result['error']}")
    else:
        print(f"❌ File creation failed: {file_result['error']}")

if __name__ == "__main__":
    asyncio.run(test_simple_attachment())