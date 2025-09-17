#!/usr/bin/env python3
"""
Test script to verify news citations with enhanced source block formatting
"""
import json
import sys
import os

# Add the project directory to path
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

from fastapi_server_complete import AsyncToolManager
import asyncio

async def test_news_citations():
    """Test news citations with enhanced source block formatting"""
    print("🧪 Testing News Citations with Enhanced Source Block Formatting")
    print("=" * 60)
    
    # Initialize tool manager
    tool_manager = AsyncToolManager()
    
    # Test query - crypto news
    test_query = "cryptocurrency"
    
    print(f"📝 Test Query: {test_query}")
    print("-" * 40)
    
    try:
        # Call get_news_summaries function
        result = await tool_manager.get_news_summaries(test_query)
        
        print("✅ News Query Result:")
        print("=" * 60)
        print(result[:2000])  # First 2000 chars
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
            ("News URLs", any(url in result for url in ["coindesk.com", "decrypt.co", "theblock.co"]))
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            status = "✅ PASS" if check_result else "❌ FAIL"
            print(f"{status}: {check_name}")
            if not check_result:
                all_passed = False
        
        print("-" * 50)
        if all_passed:
            print("🎉 ALL NEWS FORMATTING CHECKS PASSED!")
        else:
            print("⚠️  Some formatting checks failed")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing news citations: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_news_citations())
    sys.exit(0 if result else 1)