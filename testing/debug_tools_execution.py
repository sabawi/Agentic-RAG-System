#!/usr/bin/env python3
"""
Debug why tools are not executing despite being enabled
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def debug_tools_execution():
    """Debug tool execution step by step"""
    print("🔧 Debugging Tool Execution")
    print("=" * 50)
    
    # Test the exact prompt that failed
    payload = {
        "prompt": "look up the latest news from the middle east as of today",
        "toolsInUse": True,
        "prompt_context": ""
    }
    
    print(f"📤 Testing prompt: {payload['prompt']}")
    print(f"🔧 toolsInUse: {payload['toolsInUse']}")
    print()
    print("🔍 This prompt should trigger:")
    print("   1. Keyword 'news' should match news tool")
    print("   2. 'middle east' should be detected as topic")
    print("   3. get_news_summaries should be called")
    print("   4. News results should be included in context")
    print()
    print("🔍 Expected server logs:")
    print("   - 'User prompt : look up the latest news...'")
    print("   - '##### toolsInUse from the client = True'")
    print("   - '---> Tools are in use'")
    print("   - 'Calling news tool for topic: middle east'")
    print("   - 'Tool: get_news_summaries'")
    print()
    
    try:
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
            full_response = ""
            tool_indicators = []
            
            # Look for evidence of tool execution
            tool_markers = [
                "tool:",
                "result:",
                "current date and time:",
                "latest news:",
                "from external sources",
                "middle east",
                "context from tools",
                "based on the provided context"
            ]
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    full_response += chunk_text
                    
                    # Check for tool execution evidence
                    chunk_lower = chunk_text.lower()
                    for marker in tool_markers:
                        if marker in chunk_lower and marker not in tool_indicators:
                            tool_indicators.append(marker)
                            print(f"   🔧 Found tool indicator: '{marker}' in chunk {chunk_count}")
                    
                    # Show some response content for analysis
                    if chunk_count <= 10:
                        try:
                            chunk_data = json.loads(chunk_text.strip())
                            if 'response' in chunk_data and chunk_data['response'].strip():
                                response_text = chunk_data['response']
                                print(f"   📝 Chunk {chunk_count}: {response_text}")
                        except:
                            pass
                    
                    # Stop after reasonable amount
                    if chunk_count >= 50:
                        print("   🛑 Stopping after 50 chunks")
                        break
            
            response.close()
            
            print()
            print("📊 Tool Execution Analysis:")
            print(f"   Chunks processed: {chunk_count}")
            print(f"   Total response length: {len(full_response)} characters")
            print(f"   Tool indicators found: {len(tool_indicators)}")
            
            if tool_indicators:
                print(f"   ✅ Tool execution detected!")
                print(f"   📋 Evidence: {', '.join(tool_indicators[:5])}...")
            else:
                print("   ❌ NO TOOL EXECUTION DETECTED!")
                print("   🔍 This means tools aren't running despite toolsInUse=True")
                
                # Check for knowledge cutoff response
                if "knowledge cutoff" in full_response.lower() or "march" in full_response.lower():
                    print("   🚨 PROBLEM: LLM responding with knowledge cutoff instead of using tools!")
                    print("   💡 This suggests the tool results aren't being added to the context")
            
            # Show sample of response for debugging
            if full_response:
                print()
                print("📝 Response Sample (first 500 chars):")
                sample = full_response[:500].replace('\n', ' ')
                print(f"   {sample}...")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")

def debug_server_health():
    """Check if server is running properly with tools"""
    print("\n🏥 Debugging Server Health")
    print("=" * 40)
    
    try:
        # Check health endpoint
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Server health check:")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Tools available: {health_data.get('tools_available', 'unknown')}")
            
            services = health_data.get('services', {})
            for service, status in services.items():
                print(f"   {service}: {status}")
                
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

def debug_simple_tool_test():
    """Test with a very simple tool-triggering prompt"""
    print("\n🧪 Simple Tool Test")
    print("=" * 30)
    
    payload = {
        "prompt": "what time is it?",  # Should trigger get_the_secret_tool
        "toolsInUse": True
    }
    
    print(f"📤 Simple prompt: {payload['prompt']}")
    print("💡 This should trigger get_the_secret_tool (always runs first)")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/llama3_1b/stream",
            json=payload,
            stream=True,
            timeout=30
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Reading simple response...")
            
            chunk_count = 0
            found_time_info = False
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    
                    # Look for current date/time (from get_the_secret_tool)
                    if any(word in chunk_text.lower() for word in ['current date', '2025', 'july', 'time:']):
                        found_time_info = True
                        print(f"   ⏰ Found time info in chunk {chunk_count}")
                    
                    if chunk_count >= 20:
                        break
            
            response.close()
            
            if found_time_info:
                print("   ✅ SUCCESS: Tools are working (found current time)")
            else:
                print("   ❌ FAILED: No current time found - tools not working")
                
        else:
            print(f"❌ Simple test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Simple test error: {e}")

if __name__ == "__main__":
    debug_server_health()
    debug_simple_tool_test()
    debug_tools_execution()
    
    print("\n" + "=" * 50)
    print("🔍 Debug Summary:")
    print("If tools are not executing, possible causes:")
    print("1. 🔧 TOOLS_AVAILABLE = False (import errors)")
    print("2. 🔧 Virtual environment not active")
    print("3. 🔧 Keyword detection not working")
    print("4. 🔧 Tool results not added to context")
    print("5. 🔧 AsyncToolManager not initialized properly")
    print()
    print("💡 Check server logs for detailed execution info!")
    print("💡 Restart server with proper virtual environment if needed!")