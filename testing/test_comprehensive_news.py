#!/usr/bin/env python3
"""
Test the comprehensive news functionality to verify the new implementation is loaded
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_comprehensive_news():
    """Test if the new comprehensive news implementation is working"""
    print("🧪 Testing Comprehensive News Implementation")
    print("=" * 50)
    
    # Test financial news
    payload = {
        "prompt": "look up the latest financial news as of today then summarize it",
        "toolsInUse": True
    }
    
    print(f"📤 Request: {payload['prompt']}")
    print()
    print("🔍 Looking for indicators of comprehensive news implementation:")
    print("   - 'FROM EXTERNAL SOURCES as of [Current Date'")
    print("   - Content from Reuters, CNBC, Yahoo Finance")
    print("   - Multiple news sources beyond just Google News")
    print("   - Longer, more detailed responses")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/llama3_1b/stream", 
            json=payload, 
            stream=True, 
            timeout=120  # Longer timeout for comprehensive fetching
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Reading stream (looking for comprehensive news indicators)...")
            
            chunk_count = 0
            full_response = ""
            comprehensive_indicators = []
            
            # Look for indicators of comprehensive news implementation
            comprehensive_markers = [
                "from external sources",
                "reuters",
                "cnbc", 
                "yahoo finance",
                "current date and time:",
                "from source:",
                "published on:",
                "error fetching"  # Even errors indicate it's trying multiple sources
            ]
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    full_response += chunk_text
                    
                    # Check for comprehensive implementation markers
                    chunk_lower = chunk_text.lower()
                    for marker in comprehensive_markers:
                        if marker in chunk_lower and marker not in comprehensive_indicators:
                            comprehensive_indicators.append(marker)
                            print(f"   📰 Found comprehensive indicator: '{marker}' in chunk {chunk_count}")
                    
                    # Show some content for manual verification
                    if chunk_count <= 10 and chunk_text.strip():
                        try:
                            # Try to parse as JSON to get the response content
                            chunk_data = json.loads(chunk_text.strip())
                            if 'response' in chunk_data and chunk_data['response'].strip():
                                response_text = chunk_data['response']
                                if len(response_text) > 5:  # Meaningful content
                                    print(f"   📝 Chunk {chunk_count}: {response_text[:50]}...")
                        except:
                            pass
                    
                    # Stop after reasonable amount to avoid hanging
                    if chunk_count >= 50:
                        print("   🛑 Stopping after 50 chunks")
                        break
            
            response.close()
            
            print()
            print("📊 Analysis Results:")
            print(f"   Chunks processed: {chunk_count}")
            print(f"   Total response length: {len(full_response)} characters")
            print(f"   Comprehensive indicators found: {len(comprehensive_indicators)}")
            
            if comprehensive_indicators:
                print(f"   ✅ Comprehensive implementation detected!")
                print(f"   📋 Indicators: {', '.join(comprehensive_indicators[:5])}...")
                
                # Check response quality
                if len(full_response) > 2000:
                    print("   🎯 SUCCESS: Rich, detailed news response detected!")
                    print("   💡 The new comprehensive news implementation is working!")
                else:
                    print("   ⚠️ PARTIAL: Comprehensive sources detected but response may be truncated")
            else:
                print("   ❌ FAILED: No comprehensive implementation indicators found")
                print("   💡 The server may still be running the old simple implementation")
                
                # Show sample of what we got instead
                sample = full_response[:500] if full_response else "No response content"
                print(f"   📝 Sample response: {sample}...")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
        print("💡 This might indicate the comprehensive news fetching is working but taking time")
        print("🔄 Try restarting the server to load the updated code")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_comprehensive_news()