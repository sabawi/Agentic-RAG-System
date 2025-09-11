#!/usr/bin/env python3
"""
Test script to compare different formats for sending images to Ollama qwen2.5vl
This will help us understand the correct format that Open-WebUI uses.
"""

import base64
import json
import requests
import os

def test_image_formats():
    """Test different image formats with Ollama API directly"""
    
    # Test with a real image from the sandbox
    test_images = [
        './sandbox_workspace/binomial_distribution.png',
        './sandbox_workspace/microbial_growth_curve.png',
        './test_image.png'
    ]
    
    test_image_path = None
    for img_path in test_images:
        if os.path.exists(img_path):
            test_image_path = img_path
            break
    
    if not test_image_path:
        print("❌ No test image found")
        return
    
    print(f"🖼️ Using test image: {test_image_path}")
    
    # Read and encode the image
    with open(test_image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Test Format 1: Base64 string (what we're currently doing)
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    
    # Test Format 2: Direct API call like Open-WebUI might do
    formats_to_test = [
        {
            "name": "Format 1: Base64 string in images array",
            "data": {
                "model": "qwen2.5vl:3b",
                "prompt": "Describe this image briefly",
                "images": [base64_string],
                "stream": False
            }
        },
        {
            "name": "Format 2: Base64 with data URL prefix",
            "data": {
                "model": "qwen2.5vl:3b", 
                "prompt": "Describe this image briefly",
                "images": [f"data:image/png;base64,{base64_string}"],
                "stream": False
            }
        },
        {
            "name": "Format 3: Using /api/chat endpoint",
            "data": {
                "model": "qwen2.5vl:3b",
                "messages": [
                    {
                        "role": "user",
                        "content": "Describe this image briefly",
                        "images": [base64_string]
                    }
                ],
                "stream": False
            },
            "endpoint": "/api/chat"
        }
    ]
    
    for format_test in formats_to_test:
        print(f"\n🔍 Testing: {format_test['name']}")
        print(f"📤 Data preview: {json.dumps(format_test['data'], indent=2)[:200]}...")
        
        endpoint = format_test.get('endpoint', '/api/generate')
        url = f"http://localhost:11434{endpoint}"
        
        try:
            response = requests.post(
                url,
                json=format_test['data'],
                timeout=60
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'response' in result:
                    print(f"✅ Success! Response: {result['response'][:100]}...")
                elif 'message' in result and 'content' in result['message']:
                    print(f"✅ Success! Content: {result['message']['content'][:100]}...")
                else:
                    print(f"✅ Response received: {json.dumps(result, indent=2)[:200]}...")
            else:
                print(f"❌ Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test what happens when we send the exact same data our current implementation sends
    print(f"\n🔍 Testing our current implementation format:")
    try:
        import ollama
        response = ollama.generate(
            model="qwen2.5vl:3b",
            prompt="Describe this image briefly",
            images=[base64_string],
            stream=False,
            options={'think': False}
        )
        print(f"✅ Our format works! Response: {response.get('response', '')[:100]}...")
    except Exception as e:
        print(f"❌ Our format failed: {str(e)}")

if __name__ == "__main__":
    test_image_formats()