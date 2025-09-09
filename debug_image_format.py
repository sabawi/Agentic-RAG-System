#!/usr/bin/env python3
"""
Debug script to understand the exact format differences between working and non-working image calls
"""

import base64
import json
import requests
import sys
import os

def test_with_direct_api_calls():
    """Test different combinations directly with Ollama API"""
    
    # Use a real image
    image_path = './sandbox_workspace/binomial_distribution.png'
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return
    
    print(f"🖼️ Testing with: {image_path}")
    
    # Read the image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    print(f"📏 Image size: {len(image_bytes)} bytes")
    
    # Encode to base64
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    print(f"📏 Base64 size: {len(base64_string)} chars")
    print(f"🔍 Base64 preview: {base64_string[:50]}...")
    
    # Test formats that Open-WebUI might use
    api_tests = [
        {
            "name": "Direct /api/generate with base64 string",
            "url": "http://localhost:11434/api/generate",
            "data": {
                "model": "qwen2.5vl:3b",
                "prompt": "Describe this image in one sentence.",
                "images": [base64_string],
                "stream": False
            }
        },
        {
            "name": "Chat API with base64 in message",
            "url": "http://localhost:11434/api/chat",
            "data": {
                "model": "qwen2.5vl:3b",
                "messages": [
                    {
                        "role": "user",
                        "content": "Describe this image in one sentence.",
                        "images": [base64_string]
                    }
                ],
                "stream": False
            }
        }
    ]
    
    for test in api_tests:
        print(f"\n🔍 Testing: {test['name']}")
        print(f"🌐 URL: {test['url']}")
        
        try:
            print("📤 Sending request...")
            response = requests.post(
                test['url'],
                json=test['data'],
                timeout=30  # Shorter timeout for testing
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'response' in result:
                    print(f"✅ Success! Response: {result['response'][:100]}...")
                    return True  # Found working format
                elif 'message' in result:
                    if 'content' in result['message']:
                        print(f"✅ Success! Content: {result['message']['content'][:100]}...")
                        return True
                    else:
                        print(f"🤔 Message format: {json.dumps(result['message'], indent=2)[:200]}...")
                else:
                    print(f"🤔 Unknown success format: {json.dumps(result, indent=2)[:200]}...")
            else:
                error_text = response.text[:500]
                print(f"❌ Error: {error_text}")
                
        except requests.exceptions.Timeout:
            print("⏱️ Request timed out (30s)")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    return False

def test_with_ollama_library():
    """Test using ollama library like our current implementation"""
    
    print(f"\n🐍 Testing with ollama Python library...")
    
    try:
        import ollama
        
        # Use the same image
        image_path = './sandbox_workspace/binomial_distribution.png'
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        
        print("📤 Calling ollama.generate()...")
        response = ollama.generate(
            model="qwen2.5vl:3b",
            prompt="Describe this image in one sentence.",
            images=[base64_string],
            stream=False,
            options={'think': False}
        )
        
        if 'response' in response:
            print(f"✅ ollama.generate() works! Response: {response['response'][:100]}...")
            return True
        else:
            print(f"🤔 Unexpected response format: {json.dumps(response, indent=2)[:200]}...")
            
    except Exception as e:
        print(f"❌ ollama.generate() failed: {str(e)}")
    
    return False

def main():
    print("🔬 Image Format Debug Test")
    print("=" * 50)
    
    # Test 1: Direct API calls
    api_works = test_with_direct_api_calls()
    
    # Test 2: Ollama library 
    library_works = test_with_ollama_library()
    
    print("\n" + "=" * 50)
    print("📋 Results Summary:")
    print(f"  Direct API calls work: {api_works}")
    print(f"  Ollama library works: {library_works}")
    
    if not api_works and not library_works:
        print("❌ Neither format works - there may be a deeper issue")
    elif api_works and not library_works:
        print("🤔 API works but library doesn't - version mismatch?")
    elif library_works and not api_works:
        print("🤔 Library works but API doesn't - format issue?")
    else:
        print("✅ Both formats work - issue may be in our implementation")

if __name__ == "__main__":
    main()