#!/usr/bin/env python3
"""
Test the enhanced comprehensive stock analyzer with file creation
"""

import asyncio
import sys
import os

# Add the project root to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool

async def test_file_creation():
    """Test the enhanced file creation feature"""
    print("🧪 Testing Enhanced Stock Analyzer with File Creation")
    print("=" * 60)
    
    analyzer = ComprehensiveStockAnalyzerTool()
    
    # Test 1: HTML format with file creation
    print("\n1. Testing HTML format with file creation...")
    try:
        result = await analyzer.execute(
            ticker="AAPL",
            format="html",
            create_file=True,
            filename="aapl_report.html"
        )
        
        if result["success"]:
            print("✅ Analysis completed successfully")
            print(f"   Content length: {len(result['result'])} characters")
            
            if "file_created" in result:
                file_info = result["file_created"]
                print(f"✅ File created: {file_info['filename']}")
                print(f"   Path: {file_info['path']}")
                print(f"   Size: {file_info['size']} bytes")
            else:
                print("❌ No file was created")
        else:
            print(f"❌ Analysis failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Auto-generated filename
    print("\n2. Testing auto-generated filename...")
    try:
        result = await analyzer.execute(
            ticker="TSLA",
            format="html",
            create_file=True
        )
        
        if result["success"] and "file_created" in result:
            file_info = result["file_created"]
            print(f"✅ Auto-generated file: {file_info['filename']}")
            print(f"   Size: {file_info['size']} bytes")
        else:
            print("❌ Auto-generated file creation failed")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_file_creation())