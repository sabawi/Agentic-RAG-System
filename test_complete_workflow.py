#!/usr/bin/env python3
"""
Test complete workflow: Stock analysis + Report creation + Email sending
"""

import asyncio
import sys
import os
sys.path.append('/home/sabawi/Development/flaskserver')

async def test_complete_workflow():
    print("🚀 Testing Complete Stock Analysis + Report + Email Workflow")
    print("=" * 70)
    
    # Step 1: Generate stock analysis
    print("📊 Step 1: Generating comprehensive stock analysis...")
    from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
    stock_tool = ComprehensiveStockAnalyzerTool()
    
    stock_result = await stock_tool.execute(ticker="NVDA")
    
    if stock_result["success"]:
        print("✅ Stock analysis successful!")
        analysis_content = stock_result["result"]
        print(f"📝 Analysis length: {len(analysis_content)} characters")
    else:
        print(f"❌ Stock analysis failed: {stock_result['error']}")
        return
    
    # Step 2: Create report file using smart detection
    print("\n📄 Step 2: Creating report file with smart detection...")
    from user_tools.sandboxed_executor import SandboxedExecutorTool
    executor_tool = SandboxedExecutorTool()
    
    report_result = await executor_tool.execute(
        action="create_file",
        filename="NVDA_comprehensive_investment_report.pdf",
        description="Create comprehensive NVIDIA stock investment analysis report"
    )
    
    if report_result["success"]:
        print("✅ Report file created successfully!")
        report_path = report_result["result"]["full_path"]
        file_size = report_result["result"]["size_bytes"]
        print(f"📁 Report path: {report_path}")
        print(f"📏 File size: {file_size} bytes")
    else:
        print(f"❌ Report creation failed: {report_result['error']}")
        return
    
    # Step 3: Send email with attachment
    print("\n📧 Step 3: Sending email with report attachment...")
    from user_tools.secure_email_sender import SecureEmailSenderTool
    email_tool = SecureEmailSenderTool()
    
    # Use relative path from sandbox for attachment
    attachment_path = "NVDA_comprehensive_investment_report.pdf"
    
    email_result = await email_tool.execute(
        to_email="sabawi@gmail.com",
        subject="NVIDIA (NVDA) Comprehensive Investment Analysis Report",
        body=f"""Dear Investor,

Please find attached the comprehensive investment analysis report for NVIDIA Corporation (NVDA).

Report Summary:
{analysis_content[:500]}...

This report includes:
- Real-time market data and pricing
- Fundamental analysis and key metrics
- Technical analysis and trading indicators
- Recent news and sentiment analysis
- Investment recommendations and risk assessment

The attached PDF contains the complete detailed analysis.

Best regards,
AI Investment Research Team""",
        attachments=attachment_path,
        priority="normal"
    )
    
    if email_result["success"]:
        print("✅ Email sent successfully!")
        print(f"📧 Result: {email_result['result']}")
        print("\n🎉 COMPLETE WORKFLOW SUCCESS!")
        print("   ✅ Stock analysis generated")
        print("   ✅ Report file created with smart detection")
        print("   ✅ Email sent with substantial attachment")
    else:
        print(f"❌ Email sending failed: {email_result['error']}")
        
        # Debug: Check if attachment file exists
        full_report_path = f"/home/sabawi/Development/flaskserver/sandbox_workspace/{attachment_path}"
        if os.path.exists(full_report_path):
            size = os.path.getsize(full_report_path)
            print(f"📊 Attachment file exists: {full_report_path} ({size} bytes)")
        else:
            print(f"❌ Attachment file not found: {full_report_path}")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())