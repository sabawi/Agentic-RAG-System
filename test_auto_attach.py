#!/usr/bin/env python3
"""
Test auto-attachment detection
"""

import asyncio
import sys
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

async def test_auto_attachment():
    """Test auto-detection of recent reports"""
    print("🧪 Testing Auto-Attachment Detection")
    print("=" * 45)
    
    # Step 1: Create a report file (simulate what the LLM does)
    from user_tools.sandboxed_executor import SandboxedExecutorTool
    executor = SandboxedExecutorTool()
    
    report_content = """NVIDIA Corporation Stock Analysis
    
Price: $173.72 (-2.33%)
Market Cap: $4.24T
P/E Ratio: 56.22
Recommendation: BUY

Recent AI chip developments show strong growth potential.
"""
    
    print("1. Creating NVIDIA report file...")
    file_result = await executor.execute(
        action="create_file",
        filename="nvidia_stock_report.pdf",
        content=report_content,
        convert_to_pdf=True
    )
    
    if file_result["success"]:
        print(f"✅ Created: {file_result['result']['filename']}")
        
        # Step 2: Send email WITHOUT specifying attachments (let it auto-detect)
        print("\n2. Sending email without specifying attachments...")
        from user_tools.secure_email_sender import SecureEmailSenderTool
        email_sender = SecureEmailSenderTool()
        
        email_result = await email_sender.execute(
            to_email="sabawi@gmail.com",
            subject="NVIDIA Stock Analysis (Auto-Attached Report)",
            body="Hi,\n\nI've completed the NVIDIA stock analysis. The system should automatically attach the recently generated report.\n\nBest regards"
            # NOTE: No 'attachments' parameter - should auto-detect!
        )
        
        if email_result["success"]:
            print("✅ Email sent with auto-detected attachment!")
            print(f"   Result: {email_result['result']}")
        else:
            print(f"❌ Email failed: {email_result['error']}")
    else:
        print(f"❌ File creation failed: {file_result['error']}")

if __name__ == "__main__":
    asyncio.run(test_auto_attachment())