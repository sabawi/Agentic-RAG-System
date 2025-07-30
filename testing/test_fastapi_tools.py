#!/usr/bin/env python3
"""
Test what the FastAPI server is actually receiving for tools
"""

import requests
import json

def test_fastapi_tools():
    """Test what tools data the FastAPI server receives"""
    
    print("🔧 Testing FastAPI Tools Data")
    print("=" * 40)
    
    # Test request similar to what the client would send
    payload = {
        "prompt": "get news about middle east", 
        "model": "qwen3:8b",
        "toolsInUse": True,
        "system": "You are a helpful assistant."
    }
    
    print("📤 Sending request to FastAPI server...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Send request and capture response
        response = requests.post(
            "http://localhost:5000/llama3_1b/stream",
            json=payload,
            stream=True,
            timeout=5
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request accepted, reading first chunk...")
            
            chunk_count = 0
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    print(f"Chunk {chunk_count}: {chunk_text[:100]}...")
                    
                    if chunk_count >= 3:  # Just read a few chunks
                        break
            
            response.close()
            
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_fastapi_tools()