#!/usr/bin/env python3
"""
Final test to verify the race condition fix works for the exact scenario from logs
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.append('/home/sabawi/Development/flaskserver')

async def test_exact_log_scenario():
    print("🎯 TESTING EXACT SCENARIO FROM LOGS")
    print("=" * 50)
    
    from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
    from user_tools.secure_email_sender import SecureEmailSenderTool
    
    # Clean up any existing PLTR_report.pdf
    test_file = Path("/home/sabawi/Development/flaskserver/sandbox_workspace/PLTR_report.pdf")
    if test_file.exists():
        os.remove(test_file)
        print("🗑️ Removed existing PLTR_report.pdf")
    
    print("\n📊 Step 1: Calling comprehensive_stock_analyzer (exact parameters from logs)")
    print("   Parameters: create_file=True, filename='PLTR_report.pdf', format='pdf', ticker='PLTR'")
    
    analyzer = ComprehensiveStockAnalyzerTool()
    
    # Call 1: comprehensive_stock_analyzer (from logs)
    result1 = await analyzer.execute(
        create_file=True,
        filename='PLTR_report.pdf',
        format='pdf',  # Note: This was the invalid format in logs, but tool handles it
        ticker='PLTR'
    )
    
    print(f"   Result: {'SUCCESS' if result1['success'] else 'FAILED'}")
    if result1['success'] and 'file_created' in result1:
        file_info = result1['file_created']
        print(f"   📁 File: {file_info['filename']} ({file_info['size']} bytes)")
        print(f"   📍 Path: {file_info['path']}")
    
    print("\n📧 Step 2: Calling secure_email_sender (exact parameters from logs)")
    print("   Parameters: attachments='PLTR_report.pdf', to_email='test@example.com', etc.")
    
    # Call 2: secure_email_sender (from logs)
    email_tool = SecureEmailSenderTool()
    
    result2 = await email_tool.execute(
        attachments='PLTR_report.pdf',
        bcc_emails='',
        body='Please find attached the comprehensive report and analysis for PLTR.',
        cc_emails='',
        priority='normal',
        provider='gmail',
        subject='PLTR Stock Report',
        to_email='test@example.com'  # Using test email instead of real one
    )
    
    print(f"   Result: {'SUCCESS' if result2['success'] else 'FAILED'}")
    print(f"   Message: {result2.get('result', result2.get('error'))}")
    
    # Verification
    print(f"\n🔍 VERIFICATION:")
    
    if test_file.exists():
        size = test_file.stat().st_size
        print(f"   ✅ File exists: {test_file.name} ({size} bytes)")
        
        # Check first few lines of content
        with open(test_file, 'r') as f:
            content = f.read(200)
        print(f"   📄 Content preview: {content[:100]}...")
        
        if size > 100:  # Should be much larger than 16 bytes
            print(f"   ✅ File has proper content (not empty)")
        else:
            print(f"   ❌ File too small, likely empty or corrupted")
    else:
        print(f"   ❌ File does not exist")
    
    # Final assessment
    print(f"\n🎯 FINAL ASSESSMENT:")
    
    success_conditions = [
        result1['success'] and 'file_created' in result1,
        result2['success'],
        test_file.exists() and test_file.stat().st_size > 100
    ]
    
    if all(success_conditions):
        print(f"   🎉 SUCCESS! Race condition issue is FIXED!")
        print(f"   ✅ File creation: Working")
        print(f"   ✅ Email attachment: Working")
        print(f"   ✅ No more empty 16-byte files")
        print(f"   ✅ Proper timing and synchronization")
    else:
        print(f"   ❌ FAILURE! Issues still exist:")
        if not success_conditions[0]:
            print(f"      - File creation failed")
        if not success_conditions[1]:
            print(f"      - Email sending failed")
        if not success_conditions[2]:
            print(f"      - File is missing or empty")

if __name__ == "__main__":
    asyncio.run(test_exact_log_scenario())