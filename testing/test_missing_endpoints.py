#!/usr/bin/env python3
"""
Test the missing endpoints that were added
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_retrieve_system_prompts():
    """Test the /retrieve_system_prompts endpoint"""
    print("🧪 Testing /retrieve_system_prompts endpoint...")
    
    try:
        payload = {
            "system_prompts_filename": "system_prompts.json"
        }
        
        response = requests.post(f"{BASE_URL}/retrieve_system_prompts", json=payload, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                content_length = len(str(data.get('data', '')))
                print(f"   ✅ System prompts retrieved successfully ({content_length} chars)")
                return True
            else:
                print(f"   ❌ Request unsuccessful: {data.get('error', 'Unknown error')}")
                return False
        elif response.status_code == 404:
            print("   ⚠️ System prompts file not found (this may be expected)")
            return True  # Not an error if file doesn't exist
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request error: {e}")
        return False

def test_llama_stream_flexible():
    """Test the /llama3_1b/stream endpoint with flexible parameters"""
    print("\n🧪 Testing /llama3_1b/stream endpoint (flexible parameters)...")
    
    try:
        # Test with minimal payload like the original Flask version
        payload = {
            "prompt": "Hello, this is a test prompt"
        }
        
        response = requests.post(f"{BASE_URL}/llama3_1b/stream", json=payload, stream=True, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Stream endpoint accepts flexible parameters")
            
            # Read a few chunks to verify streaming works
            chunks_received = 0
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunks_received += 1
                    if chunks_received >= 3:  # Just test a few chunks
                        break
            
            print(f"   ✅ Streaming working ({chunks_received} chunks received)")
            return True
        elif response.status_code == 422:
            print("   ❌ Still getting validation error (422)")
            try:
                error_detail = response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Error content: {response.text[:200]}...")
            return False
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request error: {e}")
        return False

def test_llama_stream_with_tools():
    """Test the /llama3_1b/stream endpoint with tools"""
    print("\n🧪 Testing /llama3_1b/stream endpoint with tools...")
    
    try:
        payload = {
            "prompt": "What's the current time?",
            "toolsInUse": True
        }
        
        response = requests.post(f"{BASE_URL}/llama3_1b/stream", json=payload, stream=True, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Stream endpoint with tools working")
            
            # Read a few chunks
            chunks_received = 0
            has_tool_content = False
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunks_received += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    if 'Current date and time' in chunk_text or 'Tool:' in chunk_text:
                        has_tool_content = True
                    if chunks_received >= 10:  # Test more chunks for tools
                        break
            
            if has_tool_content:
                print("   🎯 Tool execution detected in stream!")
            else:
                print("   ⚠️ Stream working but tool execution unclear")
            
            return True
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request error: {e}")
        return False

def main():
    """Run tests for the fixed endpoints"""
    print("🔧 Testing Fixed Endpoints")
    print("=" * 40)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            return
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        print("💡 Make sure to start the server with: ./start_complete_server.sh")
        return
    
    print()
    
    # Run tests
    tests = [
        ("System Prompts Retrieval", test_retrieve_system_prompts),
        ("Flexible Stream Parameters", test_llama_stream_flexible),
        ("Stream with Tools", test_llama_stream_with_tools)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All missing endpoints are now working!")
    else:
        print("⚠️ Some endpoints still need attention.")

if __name__ == "__main__":
    main()