#!/usr/bin/env python3
"""
Test script for improved HTML report generation
"""

import asyncio
import sys
import os

# Add the project root to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
from user_tools.sandboxed_executor import SandboxedExecutorTool

async def test_improved_reports():
    """Test the improved HTML report generation"""
    print("🧪 Testing Improved HTML Report Generation")
    print("=" * 50)
    
    # Test 1: Generate HTML analysis directly
    print("\n1. Testing direct HTML analysis generation...")
    analyzer = ComprehensiveStockAnalyzerTool()
    
    try:
        # Get HTML analysis for NVDA
        result = await analyzer.execute(ticker="NVDA", format="html")
        
        if result["success"]:
            print("✅ HTML analysis generated successfully")
            print(f"   Result length: {len(result['result'])} characters")
            
            # Save the HTML to a test file
            sandbox = SandboxedExecutorTool()
            file_result = await sandbox.execute(
                action="create_file",
                filename="test_nvda_improved.html",
                content=result["result"]
            )
            
            if file_result["success"]:
                print(f"✅ HTML report saved as: {file_result['result']['filename']}")
                print(f"   File size: {file_result['result']['size_bytes']} bytes")
            else:
                print(f"❌ Failed to save HTML file: {file_result['error']}")
                
        else:
            print(f"❌ Failed to generate HTML analysis: {result['error']}")
            
    except Exception as e:
        print(f"❌ Exception during HTML generation: {e}")
    
    # Test 2: Compare text vs HTML formats
    print("\n2. Testing format comparison...")
    try:
        # Get text format
        text_result = await analyzer.execute(ticker="AAPL", format="text")
        html_result = await analyzer.execute(ticker="AAPL", format="html")
        
        if text_result["success"] and html_result["success"]:
            print("✅ Both formats generated successfully")
            print(f"   Text format length: {len(text_result['result'])} characters")
            print(f"   HTML format length: {len(html_result['result'])} characters")
            
            # Save both for comparison
            await sandbox.execute(
                action="create_file",
                filename="test_aapl_text.txt",
                content=text_result["result"]
            )
            
            await sandbox.execute(
                action="create_file", 
                filename="test_aapl_html.html",
                content=html_result["result"]
            )
            
            print("✅ Both formats saved for comparison")
            
        else:
            print("❌ Failed to generate one or both formats")
            
    except Exception as e:
        print(f"❌ Exception during format comparison: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Complete! Check the sandbox_workspace directory for generated files.")

if __name__ == "__main__":
    asyncio.run(test_improved_reports())