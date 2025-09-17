#!/usr/bin/env python3
"""
Test script to verify web search enhanced source block formatting
"""
import json
import sys
import os

# Add the project directory to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from fastapi_server_complete import AsyncToolManager
import asyncio

async def test_web_search_formatting():
    """Test web search with enhanced source block formatting"""
    print("🧪 Testing Web Search Enhanced Source Block Formatting")
    print("=" * 60)
    
    # Initialize tool manager
    tool_manager = AsyncToolManager()
    
    # Test query
    test_query = "latest AI developments"
    
    print(f"📝 Test Query: {test_query}")
    print("-" * 40)
    
    try:
        # Call search_web function
        result = await tool_manager.search_web(test_query)
        
        print("✅ Web Search Result:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        # Check for enhanced source block formatting markers
        print("\n🔍 Checking for Enhanced Source Block Formatting:")
        print("-" * 50)
        
        checks = [
            ("SOURCE BLOCK", "SOURCE BLOCK" in result),
            ("MANDATORY CITATION URL", "MANDATORY CITATION URL" in result),
            ("═══════════", "═══════════" in result),
            ("📄", "📄" in result),
            ("🔗", "🔗" in result)
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            status = "✅ PASS" if check_result else "❌ FAIL"
            print(f"{status}: {check_name}")
            if not check_result:
                all_passed = False
        
        print("-" * 50)
        if all_passed:
            print("🎉 ALL FORMATTING CHECKS PASSED!")
        else:
            print("⚠️  Some formatting checks failed")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing web search: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_web_search_formatting())
    sys.exit(0 if result else 1)