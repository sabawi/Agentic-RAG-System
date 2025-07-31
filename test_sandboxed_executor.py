#!/usr/bin/env python3
"""
Comprehensive test suite for the Sandboxed System Executor Tool
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_tools.sandboxed_executor import SandboxedExecutorTool

async def test_sandbox_operations():
    print("🧪 Testing Sandboxed System Executor")
    print("=" * 60)
    
    # Create tool instance
    tool = SandboxedExecutorTool()
    
    # Test 1: List initial sandbox contents
    print("\n📁 TEST 1: List sandbox contents")
    result = await tool.execute(action="list_files")
    print(f"✅ Success: {result['success']}")
    if result['success']:
        files = result['result']['files']
        print(f"📊 Found {len(files)} items:")
        for file in files[:5]:  # Show first 5 items
            print(f"  - {file['name']} ({file['type']}, {file['size_bytes']} bytes)")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 2: Create a Python script
    print("\n🐍 TEST 2: Create Python script")
    python_code = """#!/usr/bin/env python3
print("Hello from sandboxed Python!")
print("Current working directory:", __import__('os').getcwd())
print("Python version:", __import__('sys').version)

# Test basic computation
numbers = [1, 2, 3, 4, 5]
result = sum(x * x for x in numbers)
print(f"Sum of squares: {result}")

# Test file operations within sandbox
with open('output.txt', 'w') as f:
    f.write(f"Generated output: {result}\\n")
    f.write("This file was created by Python script\\n")

print("✅ Python script executed successfully!")
"""
    
    result = await tool.execute(
        action="create_file",
        filename="src/hello.py",
        content=python_code
    )
    print(f"✅ Create file success: {result['success']}")
    if not result['success']:
        print(f"❌ Error: {result['error']}")
    
    # Test 3: Execute the Python script
    print("\n🚀 TEST 3: Execute Python script")
    result = await tool.execute(
        action="run_code",
        filename="src/hello.py",
        language="python"
    )
    print(f"✅ Execution success: {result['success']}")
    if result['success']:
        exec_result = result['result']
        print(f"📊 Return code: {exec_result['return_code']}")
        print(f"⏱️ Execution time: {exec_result['execution_time']}s")
        print("📤 STDOUT:")
        print(exec_result['stdout'])
        if exec_result['stderr']:
            print("📤 STDERR:")
            print(exec_result['stderr'])
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 4: Test system commands
    print("\n💻 TEST 4: Execute system commands")
    commands_to_test = [
        "pwd",
        "ls -la",
        "whoami",
        "python3 --version",
        "echo 'Testing system commands'"
    ]
    
    for cmd in commands_to_test:
        print(f"\n🔍 Testing: {cmd}")
        result = await tool.execute(action="execute", command=cmd)
        print(f"✅ Success: {result['success']}")
        if result['success']:
            print(f"📤 Output: {result['result']['stdout'].strip()}")
        else:
            print(f"❌ Error: {result['error']}")
    
    # Test 5: Create and compile C program
    print("\n🔧 TEST 5: Create and compile C program")
    c_code = """#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("Hello from sandboxed C program!\\n");
    printf("Testing basic operations...\\n");
    
    int sum = 0;
    for (int i = 1; i <= 10; i++) {
        sum += i;
    }
    
    printf("Sum of 1-10: %d\\n", sum);
    
    // Create output file
    FILE *fp = fopen("c_output.txt", "w");
    if (fp != NULL) {
        fprintf(fp, "C program output: %d\\n", sum);
        fclose(fp);
        printf("Output file created successfully\\n");
    }
    
    return 0;
}
"""
    
    result = await tool.execute(
        action="create_file",
        filename="src/hello.c",
        content=c_code
    )
    print(f"✅ Create C file: {result['success']}")
    
    if result['success']:
        # Compile and run C program
        result = await tool.execute(
            action="run_code",
            filename="src/hello.c",
            language="c"
        )
        print(f"✅ C compilation/execution: {result['success']}")
        if result['success']:
            print(f"📤 C Output: {result['result']['stdout']}")
        else:
            print(f"❌ C Error: {result['error']}")
    
    # Test 6: Test security restrictions
    print("\n🛡️ TEST 6: Test security restrictions")
    dangerous_commands = [
        "sudo ls",
        "rm -rf /",
        "cat /etc/passwd",
        "mount",
        "chmod 777 ../../../"
    ]
    
    for cmd in dangerous_commands:
        print(f"\n🚨 Testing blocked command: {cmd}")
        result = await tool.execute(action="execute", command=cmd)
        print(f"🛡️ Blocked (expected): {not result['success']}")
        if not result['success']:
            print(f"📝 Reason: {result['error']}")
    
    # Test 7: Read created files
    print("\n📖 TEST 7: Read created files")
    files_to_read = ["output.txt", "c_output.txt"]
    
    for filename in files_to_read:
        print(f"\n📄 Reading: {filename}")
        result = await tool.execute(action="read_file", filename=filename)
        if result['success']:
            print(f"✅ Content: {result['result']['content'].strip()}")
        else:
            print(f"❌ Error: {result['error']}")
    
    # Test 8: Final directory listing
    print("\n📁 TEST 8: Final sandbox state")
    result = await tool.execute(action="list_files")
    if result['success']:
        files = result['result']['files']
        print(f"📊 Final file count: {len(files)}")
        for file in files:
            print(f"  - {file['name']} ({file['type']}, {file['size_bytes']} bytes)")
    
    print("\n" + "=" * 60)
    print("🎉 Sandboxed Executor Test Suite Complete!")

if __name__ == "__main__":
    asyncio.run(test_sandbox_operations())