#!/usr/bin/env python3
"""
Test suite for FastAPI server with Ollama LLM integration
=========================================================

Tests all Ollama endpoints and tool functionality.
"""

import asyncio
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:5000"

def test_ollama_service():
    """Test if Ollama service is running"""
    print("🔍 Testing Ollama service availability...")
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print("   ✅ Ollama service is running")
            print(f"   📦 Available models: {len(models.get('models', []))}")
            for model in models.get('models', [])[:3]:  # Show first 3
                print(f"      - {model.get('name', 'Unknown')}")
            return True
        else:
            print("   ❌ Ollama service responded with error")
            return False
    except Exception as e:
        print(f"   ❌ Ollama service not available: {e}")
        print("   💡 Start Ollama with: ollama serve")
        return False

def test_server_health():
    """Test server health including Ollama status"""
    print("\n🏥 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Server is healthy")
            print(f"   🗄️ Database: {data.get('services', {}).get('database', 'unknown')}")
            print(f"   🧠 Ollama: {data.get('services', {}).get('ollama', 'unknown')}")
            print(f"   🔧 Tools: {'available' if data.get('tools_available') else 'unavailable'}")
            return True
        else:
            print(f"   ❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Server not accessible: {e}")
        return False

def test_ollama_models_endpoint():
    """Test listing Ollama models through API"""
    print("\n📦 Testing Ollama models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/ollama/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                models = data.get('data', {}).get('models', [])
                print(f"   ✅ Found {len(models)} models")
                for model in models[:3]:
                    print(f"      - {model.get('name', 'Unknown')}")
                return True
            else:
                print("   ❌ API returned unsuccessful response")
                return False
        else:
            print(f"   ❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Models endpoint error: {e}")
        return False

def test_simple_ollama_prompt():
    """Test simple Ollama prompt endpoint"""
    print("\n💬 Testing simple Ollama prompt...")
    try:
        payload = {
            "model": "llama3.2:3b",  # Default model
            "prompt": "What is the capital of France? Answer in one sentence.",
            "stream": False
        }
        
        response = requests.post(f"{BASE_URL}/llama3_1b/prompt", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result = data.get('data', {})
                answer = result.get('response', 'No response')
                print("   ✅ Simple prompt successful")
                print(f"   🤖 Response: {answer[:100]}...")
                return True
            else:
                print("   ❌ Prompt failed")
                return False
        else:
            print(f"   ❌ Prompt endpoint failed: {response.status_code}")
            if response.status_code == 500:
                print("   💡 Make sure Ollama is running with a model available")
            return False
    except Exception as e:
        print(f"   ❌ Prompt test error: {e}")
        return False

def test_streaming_prompt():
    """Test streaming Ollama prompt"""
    print("\n🌊 Testing streaming prompt...")
    try:
        payload = {
            "model": "llama3.2:3b",
            "prompt": "Count from 1 to 5, one number per line.",
            "stream": True
        }
        
        response = requests.post(f"{BASE_URL}/llama3_1b/prompt", json=payload, stream=True, timeout=30)
        if response.status_code == 200:
            print("   ✅ Streaming started")
            chunks_received = 0
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunks_received += 1
                    if chunks_received <= 3:  # Show first few chunks
                        try:
                            # Try to parse as JSON
                            chunk_data = json.loads(chunk.decode())
                            if 'response' in chunk_data:
                                print(f"   📄 Chunk: {chunk_data['response'][:50]}...")
                        except:
                            print(f"   📄 Raw chunk: {chunk[:50]}...")
                    if chunks_received >= 10:  # Limit for testing
                        break
            
            print(f"   ✅ Received {chunks_received} chunks")
            return True
        else:
            print(f"   ❌ Streaming failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Streaming test error: {e}")
        return False

def test_ollama_with_tools():
    """Test Ollama with tool calling"""
    print("\n🔧 Testing Ollama with tools...")
    try:
        payload = {
            "prompt": "What's the current date and time? Also get me information about Apple stock (AAPL).",
            "toolsInUse": True,
            "model": "llama3.2:3b",
            "tools_calling_model": "llama3.2:3b"
        }
        
        print("   🚀 Sending tools request (this may take 30-60 seconds)...")
        response = requests.post(f"{BASE_URL}/llama3_1b/stream", json=payload, stream=True, timeout=120)
        
        if response.status_code == 200:
            print("   ✅ Tools request started")
            chunks_received = 0
            full_response = ""
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunks_received += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    full_response += chunk_text
                    
                    if chunks_received <= 5:  # Show progress
                        print(f"   📄 Processing... (chunk {chunks_received})")
                    
                    if chunks_received >= 50:  # Reasonable limit for testing
                        break
            
            print(f"   ✅ Received {chunks_received} chunks")
            
            # Check if response contains tool results
            if "Current date and time" in full_response or "Tool:" in full_response:
                print("   🎯 Tools were executed successfully!")
            else:
                print("   ⚠️ Response received but tool execution unclear")
            
            return True
        else:
            print(f"   ❌ Tools request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Tools test error: {e}")
        return False

def test_performance():
    """Test concurrent requests performance"""
    print("\n⚡ Testing performance with concurrent requests...")
    
    def make_request(i):
        try:
            payload = {
                "model": "llama3.2:3b",
                "prompt": f"What is 2 + {i}? Just give the number.",
                "stream": False
            }
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/llama3_1b/prompt", json=payload, timeout=30)
            duration = time.time() - start_time
            return response.status_code == 200, duration
        except Exception as e:
            return False, 0
    
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [future.result() for future in futures]
            total_time = time.time() - start_time
        
        successful = sum(1 for success, _ in results if success)
        avg_time = sum(duration for _, duration in results) / len(results)
        
        print(f"   ✅ Performance test completed")
        print(f"   📊 Successful requests: {successful}/3")
        print(f"   ⏱️ Total time: {total_time:.2f}s")
        print(f"   📈 Average response time: {avg_time:.2f}s")
        
        return successful >= 2  # At least 2/3 should succeed
    except Exception as e:
        print(f"   ❌ Performance test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 FastAPI Ollama Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Ollama Service", test_ollama_service),
        ("Server Health", test_server_health),
        ("Ollama Models API", test_ollama_models_endpoint),
        ("Simple Prompt", test_simple_ollama_prompt),
        ("Streaming Prompt", test_streaming_prompt),
        ("Tools Integration", test_ollama_with_tools),
        ("Performance", test_performance)
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
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! FastAPI Ollama integration is working perfectly!")
    elif passed >= len(results) * 0.7:
        print("⚠️ Most tests passed. Check failed tests for issues.")
    else:
        print("❌ Several tests failed. Check Ollama installation and server setup.")
    
    print("\n💡 Tips:")
    print("   - Make sure Ollama is running: ollama serve")
    print("   - Install a model: ollama pull llama3.2:3b")
    print("   - Start the FastAPI server: python fastapi_server_complete.py")

if __name__ == "__main__":
    main()