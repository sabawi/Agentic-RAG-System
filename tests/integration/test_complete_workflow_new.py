#!/usr/bin/env python3
"""
Test the complete workflow: Analysis -> File Creation -> Email with Attachment
"""

import asyncio
import sys
import os

# Add the project root to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
from user_tools.secure_email_sender import SecureEmailSenderTool

async def test_complete_workflow():
    """Test the complete workflow from analysis to email"""
    print("🧪 Testing Complete Workflow: Analysis -> File -> Email")
    print("=" * 60)
    
    # Step 1: Generate analysis with file creation
    print("\n1. Creating stock analysis report with file...")
    analyzer = ComprehensiveStockAnalyzerTool()
    
    try:
        result = await analyzer.execute(
            ticker="NVDA",
            format="html", 
            create_file=True,
            filename="nvda_comprehensive_report.html"
        )
        
        if result["success"] and "file_created" in result:
            file_info = result["file_created"]
            print(f"✅ Report created: {file_info['filename']}")
            print(f"   Path: {file_info['path']}")
            print(f"   Size: {file_info['size']} bytes")
            
            # Step 2: Send email with attachment
            print("\n2. Sending email with report attachment...")
            
            email_sender = SecureEmailSenderTool()
            email_result = await email_sender.execute(
                to_email="test@example.com",
                subject="NVIDIA (NVDA) Comprehensive Stock Analysis Report",
                body="Please find attached the comprehensive stock analysis report for NVIDIA Corporation (NVDA). This report includes real-time market data, fundamental analysis, technical indicators, recent news sentiment, and investment recommendations.\n\nBest regards,\nStock Analysis System",
                attachments=file_info['filename']  # Just the filename since it's in sandbox
            )
            
            if email_result["success"]:
                print("✅ Email sent successfully with attachment!")
                print(f"   Result: {email_result['result']}")
            else:
                print(f"❌ Email sending failed: {email_result['error']}")
                
        else:
            print(f"❌ File creation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception in workflow: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 Complete Workflow Test Finished!")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())