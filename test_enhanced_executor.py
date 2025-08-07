#!/usr/bin/env python3
"""
Test script for enhanced sandboxed_executor with smart report detection
"""

import asyncio
import sys
import os
sys.path.append('/home/sabawi/Development/flaskserver')

async def test_report_creation():
    print("🧪 Testing Enhanced Sandboxed Executor with Smart Report Detection")
    print("=" * 60)
    
    from user_tools.sandboxed_executor import SandboxedExecutorTool
    executor_tool = SandboxedExecutorTool()
    
    # Test 1: Create a Python script that creates a Tesla report
    test_script = '''
import os

# Create reports directory
os.makedirs("reports", exist_ok=True)

# Create Tesla stock analysis report (should trigger smart detection)
report_path = "reports/TSLA_comprehensive_analysis.pdf" 

with open(report_path, "w") as f:
    f.write("Tesla Stock Analysis Report - Created by AI Agent\\n")
    f.write("This should be enhanced by smart report detection.\\n")

print(f"Created report file: {report_path}")

# Check file size
import os
if os.path.exists(report_path):
    size = os.path.getsize(report_path)
    print(f"Initial file size: {size} bytes")
'''
    
    print("🔧 Creating test script for report generation...")
    script_path = "/home/sabawi/Development/flaskserver/test_report_script.py"
    with open(script_path, "w") as f:
        f.write(test_script)
    
    print("📋 Executing test script via sandboxed_executor...")
    result = await executor_tool.execute(
        action="execute",
        command=f"python {script_path}",
        description="Create Tesla comprehensive stock analysis report"
    )
    
    if result["success"]:
        print("✅ Sandboxed executor completed successfully!")
        print(f"📋 Output: {result['result']}")
        
        # Check the created report file
        report_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/reports/TSLA_comprehensive_analysis.pdf"
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            print(f"\n📊 Final Report File Analysis:")
            print(f"   📁 Path: {report_path}")
            print(f"   📏 Size: {file_size} bytes")
            
            # Read and display content
            with open(report_path, "r") as f:
                content = f.read()
                print(f"   📝 Content length: {len(content)} characters")
                
            if file_size > 500:  # Should be much larger if smart detection worked
                print("🎉 SUCCESS: Smart report detection enhanced the file content!")
                print("📋 Sample content:")
                print(content[:300] + "..." if len(content) > 300 else content)
            elif file_size > 100:
                print("⚠️  PARTIAL: File was enhanced but may need more content")
                print("📋 Content:")
                print(content)
            else:
                print("❌ FAILED: File was not enhanced by smart detection")
                print("📋 Content:")
                print(content)
        else:
            print(f"❌ Report file not found at: {report_path}")
    else:
        print(f"❌ Sandboxed executor failed: {result['error']}")
    
    # Cleanup
    if os.path.exists(script_path):
        os.remove(script_path)
        print("🧹 Cleaned up test script")

if __name__ == "__main__":
    asyncio.run(test_report_creation())