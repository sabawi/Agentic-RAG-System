#!/usr/bin/env python3
"""
Test the race condition fix for file creation and email attachment
"""

import asyncio
import sys
import os
import time
from pathlib import Path

sys.path.append('/home/sabawi/Development/flaskserver')

async def test_race_condition_fix():
    print("🔧 TESTING RACE CONDITION FIX")
    print("=" * 60)
    
    from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
    from user_tools.secure_email_sender import SecureEmailSenderTool
    
    # Clean up any existing test file
    test_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_race_test.pdf")
    if test_file.exists():
        test_file.unlink()
        print("🗑️ Cleaned up existing test file")
    
    print("\nStep 1: Creating PLTR report with race condition fix...")
    
    analyzer = ComprehensiveStockAnalyzerTool()
    
    # Start timer
    start_time = time.time()
    
    # Create the report
    result = await analyzer.execute(
        ticker="PLTR",
        create_file=True,
        filename="PLTR_race_test.pdf",
        format="text"  # Use valid format
    )
    
    creation_time = time.time() - start_time
    
    print(f"📊 Report creation completed in {creation_time:.2f} seconds")
    print(f"   Result: {result['success']}")
    
    if result["success"] and "file_created" in result:
        file_info = result["file_created"]
        print(f"   📁 File: {file_info['filename']}")
        print(f"   📏 Size: {file_info['size']} bytes")
        print(f"   📍 Path: {file_info['path']}")
    
    print(f"\nStep 2: Immediately testing email attachment (race condition test)...")
    
    email_tool = SecureEmailSenderTool()
    
    # Start timer
    email_start_time = time.time()
    
    # Test email creation immediately after file creation
    try:
        msg = email_tool._create_email_message(
            to_email="test@example.com",
            subject="PLTR Race Condition Test",
            body="Testing race condition fix for file attachments.",
            cc_emails=[],
            bcc_emails=[],
            attachments=["PLTR_race_test.pdf"],
            priority="normal",
            sender_email="test@localhost"
        )
        
        email_creation_time = time.time() - email_start_time
        
        attachment_count = len([p for p in msg.walk() if p.get_filename()])
        print(f"📧 Email creation completed in {email_creation_time:.2f} seconds")
        print(f"   ✅ Email created with {attachment_count} attachments")
        
        # Check attachment details
        for part in msg.walk():
            if part.get_filename():
                print(f"   📎 {part.get_filename()}: {len(part.get_payload())} bytes")
        
        if attachment_count > 0:
            print(f"\n🎉 SUCCESS: Race condition fix works!")
            print(f"   ✅ File created and synced properly")
            print(f"   ✅ Email tool found and attached the file")
            print(f"   ⚡ Total time: {creation_time + email_creation_time:.2f} seconds")
        else:
            print(f"\n❌ FAILURE: Race condition still exists")
            
    except Exception as e:
        print(f"❌ Email creation failed: {e}")
    
    # Step 3: Test the complete workflow simulation
    print(f"\nStep 3: Simulating complete workflow with timing...")
    
    # Clean up test file
    if test_file.exists():
        test_file.unlink()
    
    async def create_and_email():
        """Simulate the exact workflow from the logs"""
        
        # Task 1: Create report (simulating comprehensive_stock_analyzer call)
        print("   🔄 Task 1: Creating report...")
        task1_result = await analyzer.execute(
            ticker="PLTR",
            create_file=True,
            filename="PLTR_workflow_test.pdf",
            format="text"
        )
        
        # Task 2: Send email (simulating secure_email_sender call)  
        print("   🔄 Task 2: Sending email...")
        if task1_result["success"]:
            email_result = await email_tool.execute(
                to_email="test@example.com",
                subject="PLTR Workflow Test",
                body="Testing complete workflow timing.",
                attachments="PLTR_workflow_test.pdf",
                priority="normal",
                provider="sendmail"
            )
            
            print(f"   📧 Email result: {email_result['success']}")
            print(f"   📧 Message: {email_result.get('result', email_result.get('error'))}")
        
        return task1_result, email_result if task1_result["success"] else None
    
    workflow_start = time.time()
    report_result, email_result = await create_and_email()
    workflow_time = time.time() - workflow_start
    
    print(f"\n📈 WORKFLOW RESULTS:")
    print(f"   📊 Report creation: {'✅ SUCCESS' if report_result['success'] else '❌ FAILED'}")
    print(f"   📧 Email sending: {'✅ SUCCESS' if email_result and email_result['success'] else '❌ FAILED'}")
    print(f"   ⏱️ Total workflow time: {workflow_time:.2f} seconds")
    
    # Final verification
    test_workflow_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_workflow_test.pdf")
    if test_workflow_file.exists():
        size = test_workflow_file.stat().st_size
        print(f"   📁 Final file check: {size} bytes ✅")
    else:
        print(f"   📁 Final file check: File not found ❌")

if __name__ == "__main__":
    asyncio.run(test_race_condition_fix())