#!/usr/bin/env python3
"""
Test script to verify wikipedia_query enhanced source block formatting
"""
import json
import sys
import os

# Add the project directory to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from fastapi_server_complete import AsyncToolManager
import asyncio

async def test_wikipedia_query_formatting():
    """Test wikipedia_query with enhanced source block formatting"""
    print("🧪 Testing Wikipedia Query Enhanced Source Block Formatting")
    print("=" * 60)
    
    # Initialize tool manager
    tool_manager = AsyncToolManager()
    
    # Test query - using a well-known Wikipedia topic
    test_query = "Artificial Intelligence"
    
    print(f"📝 Test Query: {test_query}")
    print("-" * 40)
    
    try:
        # Call wikipedia_query function
        result = await tool_manager.wikipedia_query(test_query)
        
        print("✅ Wikipedia Query Result:")
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
            ("🔗", "🔗" in result),
            ("Wikipedia URL", "wikipedia.org" in result)
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
        print(f"❌ Error testing wikipedia_query: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_wikipedia_query_formatting())
    sys.exit(0 if result else 1)