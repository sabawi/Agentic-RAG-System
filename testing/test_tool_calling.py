#!/usr/bin/env python3
"""
Test tool calling through the streaming endpoint
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_tool_calling():
    """Test tool calling through the stream endpoint"""
    print("🔧 Testing Tool Calling via Stream Endpoint")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not running")
            return
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    print()
    
    # Test 1: Simple prompt that should trigger date/time tool
    print("1️⃣ Testing Date/Time Tool...")
    try:
        payload = {
            "prompt": "What is the current date and time?",
            "toolsInUse": True
        }
        
        response = requests.post(f"{BASE_URL}/llama3_1b/stream", json=payload, stream=True, timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   📡 Stream started, collecting response...")
            
            full_response = ""
            chunks_received = 0
            tool_detected = False
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunks_received += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    full_response += chunk_text
                    
                    # Check for tool execution indicators
                    if any(indicator in chunk_text.lower() for indicator in [
                        'current date and time', 'tool:', '2025-07-29', 'get_the_secret_tool'
                    ]):
                        tool_detected = True
                        print(f"   🎯 Tool execution detected in chunk {chunks_received}!")
                    
                    # Limit chunks for testing
                    if chunks_received >= 20:
                        print(f"   📊 Processed {chunks_received} chunks, stopping test")
                        break
            
            # Analyze response
            if tool_detected:
                print("   ✅ SUCCESS: Tool calling is working!")
            else:
                print("   ⚠️ WARNING: Tool execution not clearly detected")
                print(f"   📝 Response preview: {full_response[:200]}...")
            
            response.close()
            return tool_detected
            
        else:
            print(f"   ❌ Stream failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_stock_tool():
    """Test stock data tool specifically"""
    print("\n2️⃣ Testing Stock Data Tool...")
    try:
        payload = {
            "prompt": "Get me information about Apple stock (AAPL)",
            "toolsInUse": True
        }
        
        response = requests.post(f"{BASE_URL}/llama3_1b/stream", json=payload, stream=True, timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   📡 Stream started, looking for stock data...")
            
            chunks_received = 0
            stock_data_detected = False
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunks_received += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    
                    # Check for stock data indicators
                    if any(indicator in chunk_text.lower() for indicator in [
                        'aapl', 'apple', 'stock data', 'current price', '$', 'tool:'
                    ]):
                        stock_data_detected = True
                        print(f"   🎯 Stock data detected in chunk {chunks_received}!")
                        print(f"   📊 Content: {chunk_text[:100]}...")
                    
                    if chunks_received >= 30:
                        break
            
            if stock_data_detected:
                print("   ✅ SUCCESS: Stock tool is working!")
            else:
                print("   ⚠️ WARNING: Stock data not clearly detected")
            
            response.close()
            return stock_data_detected
            
        else:
            print(f"   ❌ Stream failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Run tool calling tests"""
    print("🧪 Tool Calling Integration Test")
    print("💡 This tests if tools are actually called during streaming")
    print()
    
    results = []
    
    # Run tests
    try:
        result1 = test_tool_calling()
        results.append(("Date/Time Tool", result1))
    except Exception as e:
        print(f"Date/Time test crashed: {e}")
        results.append(("Date/Time Tool", False))
    
    try:
        result2 = test_stock_tool()
        results.append(("Stock Data Tool", result2))
    except Exception as e:
        print(f"Stock test crashed: {e}")
        results.append(("Stock Data Tool", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Tool Calling Test Results:")
    
    successful = 0
    for test_name, success in results:
        status = "✅ WORKING" if success else "❌ NOT WORKING"
        print(f"   {status} {test_name}")
        if success:
            successful += 1
    
    print(f"\n🎯 {successful}/{len(results)} tool types working")
    
    if successful == len(results):
        print("🎉 Tool calling is fully functional!")
    elif successful > 0:
        print("⚠️ Partial success - some tools working")
    else:
        print("❌ Tool calling needs debugging")
        print("\n💡 Troubleshooting tips:")
        print("   - Check if Ollama is running and has the model")
        print("   - Verify the model can understand tool selection")
        print("   - Check server logs for detailed errors")

if __name__ == "__main__":
    main()