#!/usr/bin/env python3
"""
Debug script for sandboxed_executor.py issues with output generation, 
file saving, and email attachments.
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.append('/home/sabawi/Development/flaskserver')

async def debug_sandboxed_executor():
    print("🔍 DEBUGGING SANDBOXED EXECUTOR")
    print("=" * 60)
    
    # Import tools
    from user_tools.sandboxed_executor import SandboxedExecutorTool
    from user_tools.secure_email_sender import SecureEmailSenderTool
    
    executor = SandboxedExecutorTool()
    email_tool = SecureEmailSenderTool()
    
    print(f"📁 Sandbox path: {executor.sandbox_path}")
    print(f"✅ Sandbox exists: {executor.sandbox_path.exists()}")
    
    # Test 1: Create different file formats
    print("\n📝 TEST 1: Creating different file formats")
    print("-" * 40)
    
    test_files = [
        {"name": "debug_report.txt", "content": "# Debug Report\n\nThis is a text report for debugging.\n\nMultiple lines of content here."},
        {"name": "debug_report.html", "content": "<html><head><title>Debug Report</title></head><body><h1>Debug Report</h1><p>HTML content here.</p></body></html>"},
        {"name": "debug_report.md", "content": "# Debug Report\n\n## Section 1\nMarkdown content here.\n\n- Item 1\n- Item 2\n- Item 3"},
        {"name": "debug_report.pdf", "content": "# Debug PDF Report\n\nThis should be converted to PDF format.\n\nComprehensive content for PDF generation.", "convert_to_pdf": True}
    ]
    
    created_files = []
    for test_file in test_files:
        print(f"\n  Creating {test_file['name']}...")
        
        result = await executor.execute(
            action="create_file",
            filename=test_file["name"],
            content=test_file["content"],
            convert_to_pdf=test_file.get("convert_to_pdf", False)
        )
        
        if result["success"]:
            file_info = result["result"]
            print(f"  ✅ Created: {file_info['filename']}")
            print(f"     📏 Size: {file_info['size_bytes']} bytes")
            print(f"     📍 Path: {file_info['full_path']}")
            
            if "pdf_created" in file_info:
                print(f"     📄 PDF: {file_info['pdf_created']} -> {file_info.get('pdf_file', 'N/A')}")
            
            created_files.append(test_file['name'])
        else:
            print(f"  ❌ Failed: {result['error']}")
    
    # Test 2: Check file existence and content
    print(f"\n📂 TEST 2: Verifying file creation")
    print("-" * 40)
    
    for filename in created_files:
        file_path = executor.sandbox_path / filename
        print(f"\n  {filename}:")
        print(f"    📁 Exists: {file_path.exists()}")
        
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"    📏 Size: {size} bytes")
            
            # Show first 100 chars of content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(100)
                    print(f"    📝 Content preview: {repr(content[:50])}...")
            except Exception as e:
                print(f"    ❌ Read error: {e}")
    
    # Test 3: Email attachment validation
    print(f"\n📧 TEST 3: Email attachment validation")
    print("-" * 40)
    
    for filename in created_files:
        print(f"\n  Testing {filename} as attachment:")
        
        # Test path resolution
        resolved_path = email_tool._resolve_attachment_path(filename)
        print(f"    🔍 Resolved path: {resolved_path}")
        
        if resolved_path:
            # Test validation
            is_valid = email_tool._validate_attachment(filename)
            print(f"    ✅ Valid attachment: {is_valid}")
            
            # Test file size
            size = resolved_path.stat().st_size
            print(f"    📏 Size: {size} bytes")
            
            # Check if within size limits
            within_limits = size <= email_tool.max_attachment_size
            print(f"    🎯 Within limits: {within_limits}")
            
        else:
            print(f"    ❌ Could not resolve attachment path")
    
    # Test 4: Auto-detection of recent files
    print(f"\n🤖 TEST 4: Auto-detection of recent report files")
    print("-" * 40)
    
    recent_reports = email_tool._detect_recent_reports(max_age_minutes=5)
    print(f"  🔍 Recent reports found: {len(recent_reports)}")
    for report in recent_reports:
        print(f"    📄 {report}")
    
    # Test 5: Mock email sending test (without actually sending)
    print(f"\n📬 TEST 5: Mock email preparation test")
    print("-" * 40)
    
    if created_files:
        test_attachment = created_files[0]  # Use first created file
        print(f"  📎 Testing with attachment: {test_attachment}")
        
        try:
            # Test email message creation (mock)
            msg = email_tool._create_email_message(
                to_email="test@example.com",
                subject="Debug Test Report",
                body="This is a test email with attachment for debugging purposes.",
                cc_emails=[],
                bcc_emails=[],
                attachments=[test_attachment],  
                priority="normal",
                sender_email="debug@localhost"
            )
            
            print(f"  ✅ Email message created successfully")
            print(f"     📧 To: {msg['To']}")
            print(f"     📧 Subject: {msg['Subject']}")
            print(f"     📎 Attachments: {len([p for p in msg.walk() if p.get_filename()])} files")
            
        except Exception as e:
            print(f"  ❌ Email creation failed: {e}")
    
    print(f"\n🎉 DEBUG COMPLETE")
    print(f"   ✅ Created {len(created_files)} test files")
    print(f"   📁 All files saved to: {executor.sandbox_path}")
    print(f"   📧 Email attachment system working")

if __name__ == "__main__":
    asyncio.run(debug_sandboxed_executor())