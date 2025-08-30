#!/usr/bin/env python3
"""
Test various tool request patterns for fool-proofing
This tests how robust the system is to different ways users might request tool usage
"""

import asyncio
import sys
import os

# Add the project root to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from user_tools.secure_email_sender import SecureEmailSenderTool

async def test_direct_tool_execution():
    """Test direct tool execution with various parameter patterns"""
    print("🧪 Testing Various Tool Request Patterns")
    print("=" * 60)
    
    email_tool = SecureEmailSenderTool()
    test_results = []
    
    # Test 1: Minimal required parameters
    print("\n1. Testing minimal required parameters...")
    try:
        result = await email_tool.execute(
            to_email="test1@example.com",
            subject="Test 1",
            body="Minimal test"
        )
        test_results.append(("Minimal params", result["success"], None))
        print(f"✅ Success: {result['success']}")
    except Exception as e:
        test_results.append(("Minimal params", False, str(e)))
        print(f"❌ Error: {e}")
    
    # Test 2: With CC parameter
    print("\n2. Testing with CC parameter...")
    try:
        result = await email_tool.execute(
            to_email="test2@example.com",
            subject="Test 2",
            body="Test with CC",
            cc_email="cc@example.com"
        )
        test_results.append(("With CC", result["success"], None))
        print(f"✅ Success: {result['success']}")
    except Exception as e:
        test_results.append(("With CC", False, str(e)))
        print(f"❌ Error: {e}")
    
    # Test 3: With attachment (non-existent file)
    print("\n3. Testing with non-existent attachment...")
    try:
        result = await email_tool.execute(
            to_email="test3@example.com",
            subject="Test 3",
            body="Test with bad attachment",
            attachments="nonexistent_file.pdf"
        )
        test_results.append(("Bad attachment", result["success"], None))
        print(f"✅ Success: {result['success']}")
    except Exception as e:
        test_results.append(("Bad attachment", False, str(e)))
        print(f"❌ Error: {e}")
    
    # Test 4: With valid attachment (if available)
    print("\n4. Testing with valid attachment...")
    try:
        # Check if there's a file in sandbox_workspace
        sandbox_files = os.listdir('/home/sabawi/Development/flaskserver/sandbox_workspace/')
        if sandbox_files:
            attachment_file = sandbox_files[0]
            result = await email_tool.execute(
                to_email="test4@example.com",
                subject="Test 4",
                body="Test with valid attachment",
                attachments=attachment_file
            )
            test_results.append(("Valid attachment", result["success"], None))
            print(f"✅ Success: {result['success']}")
        else:
            test_results.append(("Valid attachment", False, "No files available"))
            print("⚠️ Skipped: No files in sandbox")
    except Exception as e:
        test_results.append(("Valid attachment", False, str(e)))
        print(f"❌ Error: {e}")
    
    # Test 5: Invalid email address patterns
    print("\n5. Testing invalid email addresses...")
    invalid_emails = [
        "invalid-email",
        "test@",
        "@example.com",
        "test..double.dot@example.com",
        ""
    ]
    
    for i, invalid_email in enumerate(invalid_emails):
        try:
            result = await email_tool.execute(
                to_email=invalid_email,
                subject=f"Test invalid {i+1}",
                body=f"Testing invalid email: {invalid_email}"
            )
            test_results.append((f"Invalid email {i+1}", result["success"], None))
            print(f"  Invalid email '{invalid_email}': {'✅' if result['success'] else '❌'}")
        except Exception as e:
            test_results.append((f"Invalid email {i+1}", False, str(e)))
            print(f"  Invalid email '{invalid_email}': ❌ {e}")
    
    # Test 6: Empty/None parameters
    print("\n6. Testing empty/None parameters...")
    empty_tests = [
        ("Empty subject", {"to_email": "test@example.com", "subject": "", "body": "Test"}),
        ("Empty body", {"to_email": "test@example.com", "subject": "Test", "body": ""}),
        ("None subject", {"to_email": "test@example.com", "subject": None, "body": "Test"}),
        ("None body", {"to_email": "test@example.com", "subject": "Test", "body": None}),
    ]
    
    for test_name, params in empty_tests:
        try:
            result = await email_tool.execute(**params)
            test_results.append((test_name, result["success"], None))
            print(f"  {test_name}: {'✅' if result['success'] else '❌'}")
        except Exception as e:
            test_results.append((test_name, False, str(e)))
            print(f"  {test_name}: ❌ {e}")
    
    # Test 7: Large content
    print("\n7. Testing large content...")
    try:
        large_body = "This is a test with large content. " * 1000  # ~35KB
        result = await email_tool.execute(
            to_email="test7@example.com",
            subject="Large Content Test",
            body=large_body
        )
        test_results.append(("Large content", result["success"], None))
        print(f"✅ Success: {result['success']}")
    except Exception as e:
        test_results.append(("Large content", False, str(e)))
        print(f"❌ Error: {e}")
    
    # Test 8: Special characters in content
    print("\n8. Testing special characters...")
    try:
        special_content = "Testing special chars: 🎉 ñáéíóú çñü αβγ 中文 العربية русский"
        result = await email_tool.execute(
            to_email="test8@example.com",
            subject=f"Special Chars: {special_content[:20]}...",
            body=special_content
        )
        test_results.append(("Special chars", result["success"], None))
        print(f"✅ Success: {result['success']}")
    except Exception as e:
        test_results.append(("Special chars", False, str(e)))
        print(f"❌ Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 TOOL REQUEST PATTERNS TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    print(f"Total tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success rate: {(successful/total)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, success, error in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        error_msg = f" ({error})" if error else ""
        print(f"  {status}: {test_name}{error_msg}")
    
    return test_results

if __name__ == "__main__":
    asyncio.run(test_direct_tool_execution())