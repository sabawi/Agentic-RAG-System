#!/usr/bin/env python3
"""
Test script to verify lookup_website enhanced source block formatting
"""
import json
import sys
import os

# Add the project directory to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from fastapi_server_complete import AsyncToolManager
import asyncio

async def test_lookup_website_formatting():
    """Test lookup_website with enhanced source block formatting"""
    print("🧪 Testing Lookup Website Enhanced Source Block Formatting")
    print("=" * 60)
    
    # Initialize tool manager
    tool_manager = AsyncToolManager()
    
    # Test URL - using a simple, reliable URL
    test_url = "https://httpbin.org/html"
    
    print(f"📝 Test URL: {test_url}")
    print("-" * 40)
    
    try:
        # Call lookup_website function
        result = await tool_manager.lookup_website(test_url)
        
        print("✅ Lookup Website Result:")
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
        print(f"❌ Error testing lookup_website: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_lookup_website_formatting())
    sys.exit(0 if result else 1)