#!/usr/bin/env python3
"""
Direct test of sandboxed executor tool to verify it works
"""
import sys
import os
from pathlib import Path

# 🔧 ROBUST PROJECT ROOT DISCOVERY - Works from any subdirectory
def find_project_root():
    """Find project root by looking for marker files/directories"""
    markers = ['user_tools', 'sandbox_workspace', 'config', 'fastapi_server_complete.py']
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if sum(1 for marker in markers if (parent / marker).exists()) >= 3:
            return str(parent)
    return os.getcwd()

project_root = find_project_root()
sys.path.insert(0, project_root)

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