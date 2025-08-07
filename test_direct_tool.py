#!/usr/bin/env python3
"""
Direct test of sandboxed executor tool to verify it works
"""
import sys
import os
sys.path.append('/home/sabawi/Development/flaskserver')

from user_tools.sandboxed_executor import SandboxedExecutorTool

def test_direct_tool():
    print("Testing sandboxed executor directly...")
    
    tool = SandboxedExecutorTool()
    
    # Test file creation
    result = tool.execute_action({
        "action": "write_file",
        "path": "hello.py",
        "content": "print('Hello World!')\nprint('This file was created by direct tool test')\n"
    })
    
    print("Direct tool result:")
    print(result)
    
    # Check if file was created
    file_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/hello.py"
    if os.path.exists(file_path):
        print(f"✅ SUCCESS: File created at {file_path}")
        with open(file_path, 'r') as f:
            print("File contents:")
            print(f.read())
    else:
        print("❌ FAILED: File not created")

if __name__ == "__main__":
    test_direct_tool()