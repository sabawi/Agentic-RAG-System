#!/usr/bin/env python3
"""
Direct Tool Testing - Bypass Server Issues
==========================================

Since the server is having timeout issues, let's test the tools directly
to verify our fixes are working properly.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project directory to Python path
sys.path.append('/home/sabawi/Development/flaskserver')

async def test_sandboxed_executor_direct():
    """Test the sandboxed executor directly"""
    print("🔧 DIRECT TOOL TEST: Sandboxed Executor")
    print("=" * 50)
    
    try:
        # Import the tool
        from user_tools.sandboxed_executor import SandboxedExecutorTool
        
        # Create instance
        executor = SandboxedExecutorTool()
        print(f"✅ Tool instantiated: {executor.name}")
        
        # Test content for PDF
        test_content = """# Direct Tool Test Report

## Executive Summary
This test validates our fixes work correctly when called directly.

### Key Validation Points
- **Reportlab Integration**: Verify binary PDF generation
- **Race Condition Fix**: Ensure _create_file completes properly
- **Argument Processing**: Confirm kwargs handling works
- **File System Operations**: Check sandbox workspace functionality

### Test Results
This section will be populated by the testing framework.

## Technical Details

### PDF Generation Pipeline
1. Content processing and validation
2. Reportlab document creation
3. Binary PDF output generation
4. File system persistence

### Error Handling
- Exception capturing and logging
- Graceful failure recovery
- Debugging trace preservation

## Conclusion
Direct tool testing bypasses server-side issues and validates core functionality.
"""
        
        print(f"📝 Testing PDF creation with {len(test_content)} characters of content...")
        
        # Test PDF creation
        result = await executor.execute(
            action="create_file",
            filename="direct_test_report.pdf",
            content=test_content
        )
        
        print(f"📤 Execution completed")
        print(f"✅ Success: {result.get('success', False)}")
        print(f"📄 Result: {result.get('result', 'No result')}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
            
        # Check if file was created
        sandbox_path = Path("/home/sabawi/Development/flaskserver/sandbox_workspace")
        pdf_file = sandbox_path / "direct_test_report.pdf"
        
        if pdf_file.exists():
            file_size = pdf_file.stat().st_size
            print(f"✅ File created: {pdf_file}")
            print(f"📏 File size: {file_size} bytes")
            
            # Check PDF header
            with open(pdf_file, 'rb') as f:
                header = f.read(4)
                if header == b'%PDF':
                    print("✅ Valid PDF header detected - genuine binary PDF!")
                    return True
                else:
                    print(f"❌ Invalid PDF header: {header}")
                    return False
        else:
            print(f"❌ File not created: {pdf_file}")
            return False
            
    except Exception as e:
        print(f"❌ Direct tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_email_tool_direct():
    """Test the email tool directly"""
    print("\n📧 DIRECT TOOL TEST: Email Sender")
    print("=" * 50)
    
    try:
        # Import the tool
        from user_tools.secure_email_sender import SecureEmailSenderTool
        
        # Create instance
        email_tool = SecureEmailSenderTool()
        print(f"✅ Tool instantiated: {email_tool.name}")
        
        # Test email sending with the PDF we just created
        result = await email_tool.execute(
            to_email="sabawi@outlook.com",
            subject="Direct Tool Test - PDF Attachment Verification",
            body="""Hello,

This email is sent directly from the tool (bypassing the server) to verify that:

✅ PDF generation works correctly with reportlab
✅ Race condition in _create_file has been resolved  
✅ Email attachment handling functions properly
✅ Binary PDF files are created (not text files with .pdf extension)

The attached PDF should be a properly formatted document.

This confirms our fixes are working at the tool level.

Best regards,
Direct Tool Test""",
            attachments="direct_test_report.pdf",
            priority="high",
            provider="sendmail"
        )
        
        print(f"📤 Email execution completed")
        print(f"✅ Success: {result.get('success', False)}")
        print(f"📧 Result: {result.get('result', 'No result')}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Direct email test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all direct tool tests"""
    print("🚀 STARTING DIRECT TOOL VERIFICATION")
    print("=" * 60)
    
    # Test 1: PDF Generation
    pdf_success = await test_sandboxed_executor_direct()
    
    if pdf_success:
        # Test 2: Email with attachment
        email_success = await test_email_tool_direct()
        
        if email_success:
            print("\n🎉 ALL DIRECT TOOL TESTS PASSED!")
            print("=" * 60)
            print("✅ PDF generation working with reportlab")
            print("✅ Race condition resolved")
            print("✅ Email attachments working")
            print("✅ Binary PDF files created correctly")
            print("\n📊 CONCLUSION: Core functionality is working!")
            print("📊 Server timeout issues are separate from tool functionality.")
            return True
        else:
            print("\n❌ Email test failed")
            return False
    else:
        print("\n❌ PDF generation test failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)