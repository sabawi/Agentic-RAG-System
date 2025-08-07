#!/usr/bin/env python3
"""
Demonstrate the CORRECT workflow for creating and emailing stock reports
"""

import asyncio
import sys
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

async def demo_correct_workflow():
    """Show the correct way to create and email stock reports"""
    print("🎯 CORRECT WORKFLOW DEMONSTRATION")
    print("=" * 50)
    
    # Method 1: Using enhanced comprehensive_stock_analyzer (RECOMMENDED)
    print("\n📊 METHOD 1: Enhanced Stock Analyzer (One-Step)")
    print("-" * 50)
    
    from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
    analyzer = ComprehensiveStockAnalyzerTool()
    
    # This single call does EVERYTHING: analysis + file creation
    result = await analyzer.execute(
        ticker="PLTR",
        format="html",           # Professional HTML format
        create_file=True,        # Automatically create file
        filename="pltr_analysis_correct.html"
    )
    
    if result["success"] and "file_created" in result:
        file_info = result["file_created"]
        print(f"✅ File created: {file_info['filename']}")
        print(f"   Path: {file_info['path']}")
        print(f"   Size: {file_info['size']} bytes")
        
        # Now email it
        from user_tools.secure_email_sender import SecureEmailSenderTool
        email_sender = SecureEmailSenderTool()
        
        email_result = await email_sender.execute(
            to_email="sabawi@gmail.com",
            subject="PLTR Stock Analysis - Correct Method",
            body="Please find attached the comprehensive PLTR stock analysis created using the enhanced workflow.",
            attachments=file_info['filename']  # Use the created filename
        )
        
        if email_result["success"]:
            print("✅ Email sent with attachment!")
        else:
            print(f"❌ Email failed: {email_result['error']}")
    
    # Method 2: Manual step-by-step (for reference)
    print("\n📊 METHOD 2: Manual Step-by-Step")
    print("-" * 50)
    
    # Step 1: Get analysis content
    analysis_result = await analyzer.execute(ticker="PLTR", format="text")
    
    if analysis_result["success"]:
        analysis_content = analysis_result["result"]
        print(f"✅ Analysis generated: {len(analysis_content)} characters")
        
        # Step 2: Create file manually
        from user_tools.sandboxed_executor import SandboxedExecutorTool
        executor = SandboxedExecutorTool()
        
        file_result = await executor.execute(
            action="create_file",
            filename="pltr_manual_report.html",
            content=f"""<!DOCTYPE html>
<html>
<head>
    <title>PLTR Stock Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        pre {{ white-space: pre-wrap; background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>PLTR Stock Analysis Report</h1>
    <pre>{analysis_content}</pre>
</body>
</html>""",
            convert_to_pdf=True  # This will create both HTML and PDF
        )
        
        if file_result["success"]:
            print(f"✅ Manual file created: {file_result['result']['filename']}")
            
            # Step 3: Email with auto-detection (no attachment specified)
            email_result2 = await email_sender.execute(
                to_email="sabawi@gmail.com",
                subject="PLTR Stock Analysis - Manual Method",
                body="This email will auto-detect and attach the recently created report."
                # No attachments parameter - will auto-detect!
            )
            
            if email_result2["success"]:
                print("✅ Email sent with auto-detected attachment!")
            else:
                print(f"❌ Email failed: {email_result2['error']}")
        else:
            print(f"❌ File creation failed: {file_result['error']}")
    
    print("\n" + "=" * 50)
    print("🎯 DEMONSTRATION COMPLETE!")
    print("\nKey Points:")
    print("• Method 1 is simpler: One tool call does analysis + file creation")
    print("• Method 2 shows manual control over each step")
    print("• Auto-attachment detection works when no attachments specified")
    print("• Both methods create properly formatted reports with real content")

if __name__ == "__main__":
    asyncio.run(demo_correct_workflow())