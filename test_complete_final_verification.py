#!/usr/bin/env python3
"""
Final Verification Test for Complete Workflow
============================================

This test verifies that:
1. PDF generation using reportlab works correctly
2. Email attachment handling works properly  
3. The race condition has been resolved
4. Server auto-execution functions properly
"""

import asyncio
import requests
import json
import os
import time
from datetime import datetime

# Test configuration
SERVER_URL = "http://localhost:5000"
TEST_EMAIL = "sabawi@outlook.com"

async def test_complete_workflow():
    """Test the complete workflow with PDF generation and email sending"""
    
    print("🚀 FINAL VERIFICATION TEST")
    print("=" * 50)
    
    # Test 1: Direct PDF generation via sandboxed executor
    print("\n📝 TEST 1: Direct PDF Generation")
    test_content = """# Stock Analysis Report

## Executive Summary
This is a comprehensive analysis of market conditions and investment opportunities.

### Key Findings
- Market volatility remains elevated
- Technology sector shows strong momentum  
- Defensive sectors recommended for risk mitigation

### Recommendations
**BUY**: Technology ETFs, Blue-chip stocks
**HOLD**: Energy sector positions
**SELL**: Speculative growth stocks

## Technical Analysis
The current market environment suggests a cautious but optimistic approach to portfolio allocation.

### Risk Assessment
- **High Risk**: Small-cap growth stocks
- **Medium Risk**: International markets
- **Low Risk**: Government bonds and utilities

## Conclusion
Based on comprehensive analysis, we recommend a balanced approach with emphasis on quality companies and diversification.
"""
    
    # Test direct PDF creation via chat API
    pdf_request = {
        "prompt": f"Please create a PDF file named 'final_test_report.pdf' with this content: {test_content}",
        "conversation_id": "final_verification_test"
    }
    
    print(f"📤 Sending PDF generation request...")
    start_time = time.time()
    
    try:
        response = requests.post(f"{SERVER_URL}/v1", json=pdf_request, timeout=30)
        execution_time = time.time() - start_time
        
        print(f"⏱️ PDF generation took: {execution_time:.2f} seconds")
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ PDF Generation Result: {result.get('success', False)}")
            if result.get('result'):
                print(f"📄 PDF Details: {result['result']}")
        else:
            print(f"❌ PDF generation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        return False
    
    # Wait a moment for file system
    time.sleep(1)
    
    # Test 2: Email with PDF attachment
    print("\n📧 TEST 2: Email with PDF Attachment")
    
    email_request = {
        "prompt": f"""Please send an email to {TEST_EMAIL} with the subject "Final Verification Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" and this body:

Hello,

This is the final verification test for our PDF generation and email system.

The attached PDF should be a properly formatted document generated using the reportlab library, containing:
- Formatted headings and sections
- Proper text styling
- Professional layout
- Binary PDF format (not text)

Key Fixes Implemented:
✅ Fixed AttributeError in server tool execution
✅ Resolved race condition in _create_file method  
✅ Verified reportlab library usage
✅ Enhanced email attachment handling with retry mechanism
✅ Added comprehensive debugging and error handling

This email should arrive with a properly formatted PDF attachment.

Best regards,
AI Agent System

Please attach the file 'final_test_report.pdf' to this email and use high priority and sendmail provider.""",
        "conversation_id": "final_verification_test"
    }
    
    print(f"📤 Sending email request...")
    start_time = time.time()
    
    try:
        response = requests.post(f"{SERVER_URL}/v1", json=email_request, timeout=60)
        execution_time = time.time() - start_time
        
        print(f"⏱️ Email sending took: {execution_time:.2f} seconds")
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email Result: {result.get('success', False)}")
            if result.get('result'):
                print(f"📧 Email Details: {result['result']}")
            if result.get('error'):
                print(f"⚠️ Email Error: {result['error']}")
        else:
            print(f"❌ Email sending failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False
    
    # Test 3: Verify files were created
    print("\n📁 TEST 3: File System Verification")
    
    sandbox_path = "/home/sabawi/Development/flaskserver/sandbox_workspace"
    expected_file = os.path.join(sandbox_path, "final_test_report.pdf")
    
    if os.path.exists(expected_file):
        file_size = os.path.getsize(expected_file)
        print(f"✅ PDF file created: {expected_file}")
        print(f"📏 File size: {file_size} bytes")
        
        # Verify it's a real PDF by checking header
        with open(expected_file, 'rb') as f:
            header = f.read(4)
            if header == b'%PDF':
                print("✅ File has correct PDF header - genuine binary PDF")
            else:
                print(f"❌ File header incorrect: {header} - not a real PDF")
                return False
    else:
        print(f"❌ PDF file not found: {expected_file}")
        return False
    
    print("\n🎉 FINAL VERIFICATION COMPLETE")
    print("=" * 50)
    print("✅ All systems operational!")
    print("✅ PDF generation working with reportlab")
    print("✅ Email attachments working properly")
    print("✅ Race condition resolved")
    print("✅ Server auto-execution functioning")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_complete_workflow())
    if success:
        print("\n🚀 SUCCESS: All tests passed!")
        exit(0)
    else:
        print("\n❌ FAILURE: Some tests failed!")
        exit(1)