#!/usr/bin/env python3
"""
Test each tool function individually
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append('/home/sabawi/Development/flaskserver')

async def test_tools():
    """Test each tool function individually"""
    from fastapi_server_complete import AsyncToolManager, TOOLS_AVAILABLE
    
    print("🔧 Testing Individual Tool Functions")
    print("=" * 50)
    print(f"TOOLS_AVAILABLE: {TOOLS_AVAILABLE}")
    
    if not TOOLS_AVAILABLE:
        print("❌ Tools marked as unavailable!")
        return
    
    tool_manager = AsyncToolManager()
    print(f"Tools loaded: {len(tool_manager.available_functions)}")
    print()
    
    # Test each tool
    test_cases = [
        ("get_the_secret_tool", ""),
        ("wikipedia_query", "Paris"),
        ("get_stock_and_company_data", "AAPL"),
        ("get_news_summaries", "technology"),
        ("search_web", "latest news"),
        ("lookup_website", "https://example.com")
    ]
    
    results = []
    
    for tool_name, test_args in test_cases:
        print(f"🧪 Testing {tool_name}...")
        try:
            if tool_name in tool_manager.available_functions:
                result = await tool_manager.safe_function_call(tool_name, test_args)
                
                # Check if result indicates success
                success = not result.startswith("Error") and len(result) > 10
                status = "✅ PASS" if success else "⚠️ PARTIAL"
                
                print(f"   {status}")
                print(f"   Result: {result[:100]}...")
                results.append((tool_name, success, result[:200]))
            else:
                print(f"   ❌ FAIL - Tool not found")
                results.append((tool_name, False, "Tool not found"))
                
        except Exception as e:
            print(f"   ❌ FAIL - Exception: {e}")
            results.append((tool_name, False, f"Exception: {e}"))
        
        print()
    
    # Summary
    print("=" * 50)
    print("📊 Tool Test Summary:")
    
    working_count = 0
    for tool_name, success, result in results:
        status = "✅" if success else "❌"
        print(f"   {status} {tool_name}")
        if success:
            working_count += 1
    
    print(f"\n🎯 {working_count}/{len(results)} tools working properly")
    
    # Test imports specifically
    print("\n🔍 Testing Specific Imports:")
    import_tests = [
        ("yfinance", "import yfinance as yf; print('yfinance OK')"),
        ("wikipedia-api", "import wikipediaapi as wiki; print('wikipedia-api OK')"),
        ("gnews", "from gnews import GNews; print('gnews OK')"),
        ("bs4", "from bs4 import BeautifulSoup; print('bs4 OK')")
    ]
    
    for import_name, test_code in import_tests:
        try:
            exec(test_code)
            print(f"   ✅ {import_name}")
        except Exception as e:
            print(f"   ❌ {import_name}: {e}")

if __name__ == "__main__":
    asyncio.run(test_tools())