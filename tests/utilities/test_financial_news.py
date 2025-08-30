#!/usr/bin/env python3
"""
Test the specific financial news prompt
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_financial_news():
    """Test the financial news prompt specifically"""
    print("📰 Testing Financial News Tool")
    print("=" * 50)
    
    # Your exact prompt
    payload = {
        "prompt": "look up the latest financial news as of today then summarize it",
        "toolsInUse": True
    }
    
    print(f"📤 Request: {payload['prompt']}")
    print()
    print("🔍 Expected server logs:")
    print("   - 'Processing tool calls with direct keyword analysis...'")
    print("   - 'Calling news tool for topic: financial' (or similar)")
    print("   - 'Tool: get_news_summaries'")
    print("   - 'Latest News:' in the results")
    print()
    
    try:
        response = requests.post(f"{BASE_URL}/llama3_1b/stream", json=payload, stream=True, timeout=60)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Processing stream (looking for news content)...")
            
            chunks_received = 0
            full_response = ""
            news_indicators_found = []
            
            # Look for indicators that news tool was executed
            news_indicators = [
                "latest news",
                "financial", 
                "news:",
                "tool:",
                "market",
                "stock",
                "economy",
                "business",
                "reuters",
                "bloomberg", 
                "cnbc",
                "wall street"
            ]
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunks_received += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    full_response += chunk_text
                    
                    # Check for news-related content
                    chunk_lower = chunk_text.lower()
                    for indicator in news_indicators:
                        if indicator in chunk_lower and indicator not in news_indicators_found:
                            news_indicators_found.append(indicator)
                            print(f"   📰 Found: '{indicator}' in chunk {chunks_received}")
                    
                    # Show progress
                    if chunks_received % 10 == 0:
                        print(f"   📊 Processed {chunks_received} chunks...")
                    
                    # Stop after reasonable amount
                    if chunks_received >= 50:
                        print("   🛑 Stopping after 50 chunks")
                        break
            
            response.close()
            
            print()
            print("📊 Analysis Results:")
            print(f"   Chunks processed: {chunks_received}")
            print(f"   Total response length: {len(full_response)} characters")
            print(f"   News indicators found: {len(news_indicators_found)}")
            
            if news_indicators_found:
                print(f"   ✅ News-related content detected: {', '.join(news_indicators_found[:5])}")
                
                # Check if we got actual news vs generic response
                if any(word in news_indicators_found for word in ["latest news", "market", "business", "financial"]):
                    print("   🎯 SUCCESS: Financial news tool appears to be working!")
                else:
                    print("   ⚠️ PARTIAL: Some news content found but may not be from tool")
            else:
                print("   ❌ FAILED: No news-related content detected")
                print(f"   Sample response: {full_response[:200]}...")
            
            # Also check for generic LLM responses that indicate tool wasn't used
            generic_phrases = ["i'm sorry", "i can't", "i don't have access", "i'm not able"]
            if any(phrase in full_response.lower() for phrase in generic_phrases):
                print("   ⚠️ WARNING: Response contains generic phrases suggesting tools weren't used")
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_news_tool_directly():
    """Test the news tool function directly first"""
    print("\n🔧 Testing News Tool Function Directly")
    print("=" * 50)
    
    try:
        # Import and test the tool directly
        import sys
        sys.path.append('/home/sabawi/Development/flaskserver')
        
        from fastapi_server_complete import AsyncToolManager
        import asyncio
        
        async def direct_test():
            tool_manager = AsyncToolManager()
            
            # Test with financial filter
            result = await tool_manager.safe_function_call('get_news_summaries', 'financial')
            print(f"📰 Direct news tool result (financial):")
            print(f"   Length: {len(result)} characters")
            print(f"   Content: {result[:300]}...")
            
            return len(result) > 100 and "news" in result.lower()
        
        success = asyncio.run(direct_test())
        
        if success:
            print("   ✅ News tool working directly")
        else:
            print("   ❌ News tool not working properly")
            
        return success
        
    except Exception as e:
        print(f"   ❌ Direct test failed: {e}")
        return False

def main():
    """Run both tests"""
    print("🧪 Financial News Tool Test Suite")
    print("💡 Testing: 'look up the latest financial news as of today then summarize it'")
    print()
    
    # Test 1: Direct tool function
    direct_success = test_news_tool_directly()
    
    # Test 2: Through streaming endpoint
    test_financial_news()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    if direct_success:
        print("✅ News tool function works correctly")
        print("🔍 If streaming test failed, issue is in keyword detection or prompt processing")
    else:
        print("❌ News tool function has issues")
        print("🔧 Need to fix the tool function first")
    
    print("\n💡 Check your server logs for detailed execution info!")

if __name__ == "__main__":
    main()