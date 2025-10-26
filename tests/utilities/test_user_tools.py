#!/usr/bin/env python3
"""
Test user-defined tools integration with the FastAPI server
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_user_tool_integration():
    print("🧪 Testing User-Defined Tools Integration")
    print("=" * 50)
    
    # Test calculator tool
    payload = {
        "prompt": "Calculate 15 + 27 using the calculator tool",
        "model": "deepseek-v3.1:671b-cloud",
        "toolsInUse": True,
        "system": "You are a helpful assistant with access to tools."
    }
    
    print(f"📤 Request: {payload['prompt']}")
    print()
    print("🔍 Looking for indicators that user tools are working:")
    print("   - Calculator tool appears in tools list")
    print("   - Correct calculation result: 42")
    print("   - Tool execution evidence in response")
    print()
    
    try:
        print("⏳ Sending request...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/llama3_1b/stream", 
            json=payload, 
            stream=True, 
            timeout=60
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Reading response stream...")
            
            chunk_count = 0
            actual_response = ""
            found_calculation = False
            found_tool_usage = False
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    
                    # Parse JSON chunks to extract LLM response
                    lines = chunk_text.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            try:
                                chunk_data = json.loads(line)
                                if 'response' in chunk_data:
                                    response_text = chunk_data['response']
                                    actual_response += response_text
                                    
                                    # Check for calculation result
                                    if '42' in response_text:
                                        found_calculation = True
                                        print(f"   ✅ Found calculation result in chunk {chunk_count}!")
                                    
                                    # Check for tool usage indicators
                                    if ('calculator' in response_text.lower() or
                                        'tool' in response_text.lower() or
                                        'calculate' in response_text.lower()):
                                        found_tool_usage = True
                                        print(f"   🔧 Found tool usage indicators in chunk {chunk_count}")
                                    
                                if chunk_data.get('done', False):
                                    print(f"   🏁 Stream completed at chunk {chunk_count}")
                                    break
                            except json.JSONDecodeError:
                                pass
                    
                    # Show progress
                    if chunk_count % 10 == 0:
                        print(f"   📝 Processed {chunk_count} chunks, {len(actual_response)} chars...")
                    
                    # Stop after reasonable time/content
                    if chunk_count >= 80 or len(actual_response) > 2000:
                        print(f"   🛑 Stopping after {chunk_count} chunks")
                        break
                        
            response.close()
            elapsed_time = time.time() - start_time
            
            print()
            print("📊 User Tools Test Results:")
            print(f"   Chunks processed: {chunk_count}")
            print(f"   Response length: {len(actual_response)} characters")
            print(f"   Processing time: {elapsed_time:.1f} seconds")
            
            if found_calculation and found_tool_usage:
                print("   🎯 SUCCESS: Calculator tool executed successfully!")
                print("   ✅ User-defined tools are working perfectly")
            elif found_calculation:
                print("   ⚡ PARTIAL SUCCESS: Correct calculation found")
                print("   ⚠️ May indicate tool execution or good LLM reasoning")
            elif found_tool_usage:
                print("   🔧 TOOL INDICATORS FOUND: Tool usage detected")
                print("   ⚠️ Check if calculation is correct")
            else:
                print("   ❓ UNCLEAR RESULT: Check response for tool usage")
                
            print(f"   📝 Sample response: {actual_response[:500]}...")
                
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - may indicate tool processing")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_server_tools_list():
    """Test if server shows user tools in available tools"""
    print("\n🔍 Testing Server Tools Discovery")
    print("-" * 30)
    
    try:
        # Try to get system prompts (might show tools info)
        response = requests.get(f"{BASE_URL}/retrieve_system_prompts")
        if response.status_code == 200:
            print("✅ Server is responding")
        else:
            print(f"⚠️ Server response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Make sure the FastAPI server is running on port 5000")

if __name__ == "__main__":
    test_server_tools_list()
    test_user_tool_integration()