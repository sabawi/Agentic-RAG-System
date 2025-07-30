#!/usr/bin/env python3
"""
Test the improved direct tool calling system
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_direct_tool_calling():
    """Test the improved direct tool calling"""
    print("🎯 Testing Direct Tool Calling (No JSON Parsing)")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not running")
            return
        print("✅ Server is running\n")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    test_cases = [
        {
            "name": "Stock Query",
            "prompt": "What is the current price of Apple stock (AAPL)?",
            "expected_tools": ["get_the_secret_tool", "get_stock_and_company_data"],
            "keywords_to_check": ["aapl", "apple", "stock data", "current price", "$"]
        },
        {
            "name": "News Query", 
            "prompt": "What are the latest news headlines today?",
            "expected_tools": ["get_the_secret_tool", "get_news_summaries"],
            "keywords_to_check": ["latest news", "news:", "headlines"]
        },
        {
            "name": "Wikipedia Query",
            "prompt": "Tell me about Paris, France",
            "expected_tools": ["get_the_secret_tool", "wikipedia_query"],
            "keywords_to_check": ["paris", "wikipedia", "france"]
        },
        {
            "name": "Multi-tool Query",
            "prompt": "What time is it and what's the price of Tesla stock (TSLA)?",
            "expected_tools": ["get_the_secret_tool", "get_stock_and_company_data"],
            "keywords_to_check": ["current date", "tsla", "tesla", "stock data"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}️⃣ Testing: {test_case['name']}")
        print(f"   Prompt: {test_case['prompt']}")
        
        try:
            payload = {
                "prompt": test_case['prompt'],
                "toolsInUse": True
            }
            
            response = requests.post(f"{BASE_URL}/llama3_1b/stream", json=payload, stream=True, timeout=45)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   📡 Processing stream...")
                
                full_response = ""
                chunks_received = 0
                tools_detected = []
                keywords_found = []
                
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        chunks_received += 1
                        chunk_text = chunk.decode('utf-8', errors='ignore')
                        full_response += chunk_text
                        
                        # Check for tool execution
                        if "Tool:" in chunk_text:
                            # Extract tool name
                            lines = chunk_text.split('\n')
                            for line in lines:
                                if line.startswith('Tool:'):
                                    tool_name = line.replace('Tool:', '').strip()
                                    if tool_name not in tools_detected:
                                        tools_detected.append(tool_name)
                                        print(f"   🔧 Tool detected: {tool_name}")
                        
                        # Check for expected keywords
                        chunk_lower = chunk_text.lower()
                        for keyword in test_case['keywords_to_check']:
                            if keyword.lower() in chunk_lower and keyword not in keywords_found:
                                keywords_found.append(keyword)
                                print(f"   🎯 Keyword found: {keyword}")
                        
                        # Limit chunks for testing
                        if chunks_received >= 25:
                            break
                
                response.close()
                
                # Evaluate results
                tools_success = len(tools_detected) >= 2  # At least date/time + one other
                keywords_success = len(keywords_found) > 0
                overall_success = tools_success and keywords_success
                
                status = "✅ SUCCESS" if overall_success else "⚠️ PARTIAL" if (tools_success or keywords_success) else "❌ FAILED"
                print(f"   {status}")
                print(f"   📊 Tools executed: {len(tools_detected)} ({', '.join(tools_detected)})")
                print(f"   🔍 Keywords found: {len(keywords_found)} ({', '.join(keywords_found)})")
                
                results.append((test_case['name'], overall_success, tools_detected, keywords_found))
                
            else:
                print(f"   ❌ Stream failed: {response.status_code}")
                results.append((test_case['name'], False, [], []))
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            results.append((test_case['name'], False, [], []))
        
        print()
    
    # Final summary
    print("=" * 60)
    print("📊 Direct Tool Calling Test Results:")
    
    successful = 0
    for test_name, success, tools, keywords in results:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
        if tools:
            print(f"      Tools: {', '.join(tools)}")
        if keywords:
            print(f"      Data: {', '.join(keywords[:3])}...")
        if success:
            successful += 1
    
    print(f"\n🎯 {successful}/{len(results)} tests passed")
    
    if successful == len(results):
        print("🎉 Direct tool calling is working perfectly!")
        print("✨ No more JSON parsing errors!")
    elif successful > 0:
        print("⚠️ Mostly working - some edge cases to handle")
    else:
        print("❌ Tool calling still needs debugging")

if __name__ == "__main__":
    test_direct_tool_calling()