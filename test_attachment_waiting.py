#!/usr/bin/env python3
"""
Test the enhanced attachment waiting mechanism
"""

import asyncio
import sys
import os
import threading
import time

# Add the project root to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from user_tools.secure_email_sender import SecureEmailSenderTool
from pathlib import Path

def create_file_after_delay(file_path: str, delay_seconds: float, content: str = "Test content"):
    """Create a file after a delay (simulates file generation)"""
    def delayed_creation():
        time.sleep(delay_seconds)
        with open(file_path, 'w') as f:
            f.write(content * 100)  # Make it substantial
        print(f"📄 Delayed file created: {file_path}")
    
    thread = threading.Thread(target=delayed_creation)
    thread.daemon = True
    thread.start()
    return thread

async def test_attachment_waiting():
    """Test the attachment waiting functionality"""
    print("🧪 Testing Enhanced Attachment Waiting Mechanism")
    print("=" * 70)
    
    email_tool = SecureEmailSenderTool()
    sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")
    
    # Test files to create with delays
    test_files = [
        "delayed_report_1.pdf",
        "delayed_report_2.pdf"
    ]
    
    # Clean up any existing test files
    for test_file in test_files:
        file_path = sandbox_path / test_file
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️ Cleaned up existing: {test_file}")
    
    print(f"\n📋 Test Plan:")
    print(f"   1. Request email with attachments: {', '.join(test_files)}")
    print(f"   2. Create files with delays: 2s and 4s")
    print(f"   3. Email tool should wait for both files")
    print(f"   4. Email should send successfully with attachments")
    
    # Start delayed file creation
    print(f"\n🚀 Starting delayed file creation...")
    create_file_after_delay(str(sandbox_path / test_files[0]), 2.0, "PDF content for report 1")
    create_file_after_delay(str(sandbox_path / test_files[1]), 4.0, "PDF content for report 2")
    
    # Test 1: Email with waiting enabled (default)
    print(f"\n1️⃣ Testing with attachment waiting ENABLED...")
    start_time = time.time()
    
    try:
        result = await email_tool.execute(
            to_email="test@example.com",
            subject="Waiting Test - Enabled",
            body="Testing attachment waiting mechanism",
            attachments=f"{test_files[0]}, {test_files[1]}",
            wait_for_attachments=True,
            attachment_timeout=10
        )
        
        elapsed = time.time() - start_time
        
        if result["success"]:
            print(f"✅ SUCCESS: Email sent after {elapsed:.1f}s")
            print(f"   Result: {result['result']}")
        else:
            print(f"❌ FAILED: {result['error']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Clean up test files
    for test_file in test_files:
        file_path = sandbox_path / test_file
        if file_path.exists():
            file_path.unlink()
    
    print(f"\n🔄 Waiting 2 seconds before next test...")
    await asyncio.sleep(2)
    
    # Test 2: Email with waiting disabled
    print(f"\n2️⃣ Testing with attachment waiting DISABLED...")
    
    # Create new test files with delay
    test_files_2 = ["instant_fail_1.pdf", "instant_fail_2.pdf"]
    create_file_after_delay(str(sandbox_path / test_files_2[0]), 3.0, "Should not wait")
    create_file_after_delay(str(sandbox_path / test_files_2[1]), 3.0, "Should not wait")
    
    start_time = time.time()
    
    try:
        result = await email_tool.execute(
            to_email="test@example.com",
            subject="Waiting Test - Disabled", 
            body="Testing with waiting disabled",
            attachments=f"{test_files_2[0]}, {test_files_2[1]}",
            wait_for_attachments=False
        )
        
        elapsed = time.time() - start_time
        
        if result["success"]:
            print(f"⚡ SUCCESS: Email sent immediately after {elapsed:.1f}s")
            print(f"   Result: {result['result']}")
        else:
            print(f"❌ FAILED: {result['error']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Clean up
    for test_file in test_files_2:
        file_path = sandbox_path / test_file
        if file_path.exists():
            file_path.unlink()
    
    print(f"\n" + "="*70)
    print(f"📊 Test Summary:")
    print(f"   ✅ Test 1 should succeed after ~4 seconds (waiting for files)")
    print(f"   ⚡ Test 2 should process immediately (no waiting)")

if __name__ == "__main__":
    asyncio.run(test_attachment_waiting())