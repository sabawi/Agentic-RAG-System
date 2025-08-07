#!/usr/bin/env python3
"""
Test smart report detection with proper parameters
"""

import asyncio
import sys
import os
sys.path.append('/home/sabawi/Development/flaskserver')

async def test_smart_report_detection():
    print("🧠 Testing Smart Report Detection with Proper Parameters")
    print("=" * 60)
    
    from user_tools.sandboxed_executor import SandboxedExecutorTool
    executor_tool = SandboxedExecutorTool()
    
    # Test with create_file action and report-like filename
    print("🔧 Testing smart detection with create_file action...")
    
    result = await executor_tool.execute(
        action="create_file",
        filename="TSLA_comprehensive_stock_analysis.pdf",
        # Don't provide content - this should trigger smart detection
        description="Create comprehensive Tesla stock analysis report"
    )
    
    if result["success"]:
        print("✅ Smart detection executed successfully!")
        print(f"📋 Result: {result['result']}")
        
        # Check the created file
        report_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/TSLA_comprehensive_stock_analysis.pdf"
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            print(f"\n📊 Smart Detection Results:")
            print(f"   📁 File: {report_path}")
            print(f"   📏 Size: {file_size} bytes")
            
            if file_size > 1000:  # Should be much larger with comprehensive content
                print("🎉 SUCCESS: Smart report detection generated comprehensive content!")
                
                # Show sample content
                with open(report_path, "r") as f:
                    content = f.read()
                    print(f"   📝 Content length: {len(content)} characters")
                    print("📋 Sample content:")
                    print(content[:400] + "..." if len(content) > 400 else content)
            else:
                print("⚠️  File created but may not have comprehensive content")
                with open(report_path, "r") as f:
                    content = f.read()
                    print(f"📋 Content ({len(content)} chars): {content}")
        else:
            print(f"❌ File not found at: {report_path}")
    else:
        print(f"❌ Smart detection failed: {result['error']}")
    
    print("\n" + "=" * 60)
    
    # Test 2: Another stock report
    print("🔧 Testing with another stock report...")
    
    result2 = await executor_tool.execute(
        action="create_file",
        filename="AAPL_financial_analysis_report.md",
        description="Create Apple stock financial analysis"
    )
    
    if result2["success"]:
        print("✅ Second test successful!")
        report_path2 = "/home/sabawi/Development/flaskserver/sandbox_workspace/AAPL_financial_analysis_report.md"
        if os.path.exists(report_path2):
            file_size2 = os.path.getsize(report_path2)
            print(f"📊 AAPL report size: {file_size2} bytes")
        else:
            print("❌ AAPL report not found")
    else:
        print(f"❌ Second test failed: {result2['error']}")

if __name__ == "__main__":
    asyncio.run(test_smart_report_detection())