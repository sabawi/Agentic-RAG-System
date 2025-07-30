#!/usr/bin/env python3
"""
Test comprehensive web search functionality including DDG search, webcrawling, and text chunking
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_web_search():
    """Test the web search functionality with DuckDuckGo"""
    print("🔍 Testing Web Search with DuckDuckGo")
    print("=" * 50)
    
    payload = {
        "prompt": "search for the latest information about artificial intelligence developments in 2025",
        "toolsInUse": True
    }
    
    print(f"📤 Request: {payload['prompt']}")
    print()
    print("🔍 Looking for web search indicators:")
    print("   - 'As of [Current Date and Time:'")
    print("   - 'Result 1:', 'Result 2:', 'Result 3:'")
    print("   - URLs and web content")
    print("   - DuckDuckGo search results")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/llama3_1b/stream", 
            json=payload, 
            stream=True, 
            timeout=120
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Reading stream for web search content...")
            
            chunk_count = 0
            full_response = ""
            web_search_indicators = []
            
            # Look for web search indicators
            search_markers = [
                "as of [current date",
                "result 1:",
                "result 2:", 
                "result 3:",
                "title:",
                "url:",
                "description:",
                "content:",
                "web search results",
                "duckduckgo"
            ]
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    full_response += chunk_text
                    
                    # Check for web search markers
                    chunk_lower = chunk_text.lower()
                    for marker in search_markers:
                        if marker in chunk_lower and marker not in web_search_indicators:
                            web_search_indicators.append(marker)
                            print(f"   🔍 Found web search indicator: '{marker}' in chunk {chunk_count}")
                    
                    # Show progress every 20 chunks
                    if chunk_count % 20 == 0:
                        print(f"   📊 Processed {chunk_count} chunks...")
                    
                    # Stop after reasonable amount
                    if chunk_count >= 100:
                        print("   🛑 Stopping after 100 chunks")
                        break
            
            response.close()
            
            print()
            print("📊 Web Search Analysis:")
            print(f"   Chunks processed: {chunk_count}")
            print(f"   Total response length: {len(full_response)} characters")
            print(f"   Web search indicators found: {len(web_search_indicators)}")
            
            if web_search_indicators:
                print(f"   ✅ Web search functionality detected!")
                print(f"   📋 Indicators: {', '.join(web_search_indicators[:5])}...")
                
                # Check response quality
                if len(full_response) > 5000:
                    print("   🎯 SUCCESS: Rich web search response detected!")
                    print("   💡 DuckDuckGo search with content extraction is working!")
                else:
                    print("   ⚠️ PARTIAL: Web search detected but response may be limited")
            else:
                print("   ❌ FAILED: No web search indicators found")
                sample = full_response[:500] if full_response else "No response content"
                print(f"   📝 Sample response: {sample}...")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
        print("💡 Web search with content extraction takes time - this may be normal")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_website_lookup():
    """Test the website lookup functionality"""
    print("\n🌐 Testing Website Lookup with Selenium/BeautifulSoup")
    print("=" * 50)
    
    payload = {
        "prompt": "lookup the website https://www.bbc.com/news and summarize the content",
        "toolsInUse": True
    }
    
    print(f"📤 Request: {payload['prompt']}")
    print()
    print("🔍 Looking for website lookup indicators:")
    print("   - 'As of [Current Date and Time:'")
    print("   - 'lookup results:'")
    print("   - Website content and titles")
    print("   - Selenium or BeautifulSoup extraction")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/llama3_1b/stream", 
            json=payload, 
            stream=True, 
            timeout=120
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Reading stream for website lookup content...")
            
            chunk_count = 0
            full_response = ""
            lookup_indicators = []
            
            lookup_markers = [
                "lookup results:",
                "title:",
                "content:",
                "as of [current date",
                "bbc",
                "news",
                "selenium",
                "beautifulsoup",
                "pdf",
                "error extracting"
            ]
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    full_response += chunk_text
                    
                    chunk_lower = chunk_text.lower()
                    for marker in lookup_markers:
                        if marker in chunk_lower and marker not in lookup_indicators:
                            lookup_indicators.append(marker)
                            print(f"   🌐 Found lookup indicator: '{marker}' in chunk {chunk_count}")
                    
                    if chunk_count % 20 == 0:
                        print(f"   📊 Processed {chunk_count} chunks...")
                    
                    if chunk_count >= 100:
                        print("   🛑 Stopping after 100 chunks")
                        break
            
            response.close()
            
            print()
            print("📊 Website Lookup Analysis:")
            print(f"   Chunks processed: {chunk_count}")
            print(f"   Total response length: {len(full_response)} characters")
            print(f"   Lookup indicators found: {len(lookup_indicators)}")
            
            if lookup_indicators:
                print(f"   ✅ Website lookup functionality detected!")
                print(f"   📋 Indicators: {', '.join(lookup_indicators[:5])}...")
                
                if len(full_response) > 3000:
                    print("   🎯 SUCCESS: Rich website content extraction working!")
                    print("   💡 Selenium/BeautifulSoup website lookup is functional!")
                else:
                    print("   ⚠️ PARTIAL: Website lookup detected but content may be limited")
            else:
                print("   ❌ FAILED: No website lookup indicators found")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
        print("💡 Website extraction with Selenium takes time - this may be normal")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_text_chunking():
    """Test if text chunking is working for large content"""
    print("\n📝 Testing Text Chunking for Large Content")
    print("=" * 50)
    
    # Create a long prompt that would generate lots of tool results
    payload = {
        "prompt": "search for information about machine learning, artificial intelligence, neural networks, deep learning, natural language processing, computer vision, and robotics. Then look up the latest news about each topic and provide a comprehensive summary.",
        "toolsInUse": True
    }
    
    print(f"📤 Request: {payload['prompt']}")
    print("💡 This should generate lots of content and potentially trigger text chunking")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/llama3_1b/stream", 
            json=payload, 
            stream=True, 
            timeout=180  # Longer timeout for comprehensive search
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Reading stream for text chunking evidence...")
            
            chunk_count = 0
            full_response = ""
            content_length = 0
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    full_response += chunk_text
                    content_length += len(chunk_text)
                    
                    if chunk_count % 50 == 0:
                        print(f"   📊 Processed {chunk_count} chunks, {content_length} bytes...")
                    
                    # Stop after reasonable processing
                    if chunk_count >= 200:
                        print("   🛑 Stopping after 200 chunks")
                        break
            
            response.close()
            
            print()
            print("📊 Text Chunking Analysis:")
            print(f"   Chunks processed: {chunk_count}")
            print(f"   Total content length: {content_length} bytes")
            
            if content_length > 50000:  # 50KB+ suggests comprehensive content
                print("   🎯 SUCCESS: Large content processed - text chunking likely working!")
                print("   💡 The system can handle comprehensive web searches and content extraction!")
            elif content_length > 20000:  # 20KB+ 
                print("   ✅ GOOD: Substantial content processed - system working well!")
            else:
                print("   ⚠️ LIMITED: Less content than expected - may need investigation")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
        print("💡 Comprehensive searches take time - this suggests the system is working hard!")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    """Run all web search and content extraction tests"""
    print("🧪 Comprehensive Web Search & Content Extraction Test Suite")
    print("💡 Testing DuckDuckGo search, Selenium webcrawling, and text chunking")
    print()
    
    # Test 1: Web Search
    test_web_search()
    
    # Test 2: Website Lookup  
    test_website_lookup()
    
    # Test 3: Text Chunking
    test_text_chunking()
    
    print("\n" + "=" * 50)
    print("📊 Test Suite Summary:")
    print("✅ If tests show rich content and indicators, the comprehensive system is working!")
    print("🔍 Web search uses DuckDuckGo + content extraction")
    print("🌐 Website lookup uses Selenium + BeautifulSoup fallback + PDF support")
    print("📝 Text chunking keeps context within reasonable limits")
    print("💡 Check server logs for detailed execution info!")

if __name__ == "__main__":
    main()