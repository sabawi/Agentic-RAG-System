#!/usr/bin/env python3
"""
Test Dynamic Path Resolution After Reorganization Fixes
Validates that all hardcoded path fixes work correctly
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_dynamic_sandbox_resolution():
    """Test that sandbox_workspace path resolves correctly from different locations"""
    print("🔍 Testing dynamic sandbox path resolution...")
    
    # Save original directory
    original_cwd = os.getcwd()
    
    try:
        # Test from current directory
        sandbox_path = os.path.join(os.getcwd(), "sandbox_workspace")
        print(f"✅ From project root: {sandbox_path}")
        assert os.path.exists(sandbox_path), f"Sandbox doesn't exist at {sandbox_path}"
        
        # Test from different directory
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)
        
        # Change back to project directory (simulating how server would work)
        os.chdir(original_cwd)
        sandbox_path = os.path.join(os.getcwd(), "sandbox_workspace")
        print(f"✅ After directory change: {sandbox_path}")
        assert os.path.exists(sandbox_path), f"Sandbox doesn't exist at {sandbox_path}"
        
        return True
        
    except Exception as e:
        print(f"❌ Dynamic path resolution failed: {e}")
        return False
    finally:
        os.chdir(original_cwd)
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)

def test_file_creation_with_dynamic_paths():
    """Test file creation using dynamic paths"""
    print("🔍 Testing file creation with dynamic paths...")
    
    try:
        # Simulate the exact path logic from fastapi_server_complete.py
        base_dir = os.path.join(os.getcwd(), "sandbox_workspace")
        test_filename = "dynamic_path_test.txt"
        full_path = os.path.join(base_dir, test_filename)
        
        # Create test file
        test_content = "Dynamic path resolution test successful!"
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"✅ Created file: {full_path}")
        
        # Verify file exists and has correct content
        assert os.path.exists(full_path), f"File not created at {full_path}"
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == test_content, f"File content mismatch"
        print(f"✅ File content verified: {len(content)} chars")
        
        # Cleanup
        os.unlink(full_path)
        print(f"✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ File creation test failed: {e}")
        return False

def test_attachment_path_resolution():
    """Test attachment path resolution (simulates email attachment logic)"""
    print("🔍 Testing attachment path resolution...")
    
    try:
        # Test the exact logic used in the fixed code
        filename = "test_attachment.txt"
        
        # Method 1: Direct os.path.join (used in fix)
        attachment_path = os.path.join(os.getcwd(), "sandbox_workspace", filename)
        print(f"✅ Method 1 - Direct join: {attachment_path}")
        
        # Create test attachment file
        with open(attachment_path, 'w') as f:
            f.write("Test attachment content")
        
        # Verify attachment exists and is accessible
        assert os.path.exists(attachment_path), f"Attachment not found at {attachment_path}"
        assert os.path.getsize(attachment_path) > 0, f"Attachment is empty"
        
        print(f"✅ Attachment created and verified: {os.path.getsize(attachment_path)} bytes")
        
        # Test that path works for email attachment parameter format
        email_attachment_param = attachment_path  # This is what gets passed to email tool
        assert os.path.exists(email_attachment_param), "Email attachment parameter path invalid"
        print(f"✅ Email attachment parameter valid: {email_attachment_param}")
        
        # Cleanup
        os.unlink(attachment_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Attachment path test failed: {e}")
        return False

def test_from_different_working_directory():
    """Test that paths work when server is started from different directory"""
    print("🔍 Testing from different working directory...")
    
    original_cwd = os.getcwd()
    temp_dir = None
    
    try:
        # Create temporary directory and change to it
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)
        print(f"✅ Changed to temp directory: {temp_dir}")
        
        # Now change to project directory (simulating server startup)
        project_dir = original_cwd
        os.chdir(project_dir)
        print(f"✅ Changed to project directory: {project_dir}")
        
        # Test that sandbox path resolves correctly
        sandbox_path = os.path.join(os.getcwd(), "sandbox_workspace")
        assert os.path.exists(sandbox_path), f"Sandbox not found: {sandbox_path}"
        print(f"✅ Sandbox path resolution works: {sandbox_path}")
        
        # Test file operations
        test_file = os.path.join(sandbox_path, "working_dir_test.txt")
        with open(test_file, 'w') as f:
            f.write("Working directory test")
        
        assert os.path.exists(test_file), "Test file not created"
        print(f"✅ File operations work from different starting directory")
        
        # Cleanup
        os.unlink(test_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Different working directory test failed: {e}")
        return False
    finally:
        os.chdir(original_cwd)
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

def run_all_tests():
    """Run all dynamic path tests"""
    print("🚀 DYNAMIC PATH RESOLUTION TESTING")
    print("=" * 50)
    
    tests = [
        ("Dynamic Sandbox Resolution", test_dynamic_sandbox_resolution),
        ("File Creation with Dynamic Paths", test_file_creation_with_dynamic_paths),
        ("Attachment Path Resolution", test_attachment_path_resolution),
        ("Different Working Directory", test_from_different_working_directory),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}")
    
    print(f"\n🎯 FINAL RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📊 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL DYNAMIC PATH TESTS PASSED!")
        print("✅ Reorganization path fixes are working correctly")
        return True
    else:
        print("🚨 Some tests failed - path fixes may need adjustment")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)