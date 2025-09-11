#!/usr/bin/env python3
import base64
import requests
import time

def test_real_minimal():
    """Test with a real minimal PNG"""
    
    # Use the proper minimal PNG we just created
    with open('/tmp/minimal.png', 'rb') as f:
        img_bytes = f.read()
    
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    print(f"🖼️ Testing with real minimal PNG: {len(img_bytes)} bytes")
    
    test_data = {
        "model": "qwen2.5vl:3b",
        "prompt": "What do you see?",
        "images": [base64_str],
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=test_data,
            timeout=30  # Give it more time but still reasonable
        )
        elapsed = time.time() - start_time
        
        print(f"⏱️  Response in {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('response', 'No response')}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏱️  Timeout - model hanging on vision")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    return False

if __name__ == "__main__":
    test_real_minimal()