#!/usr/bin/env python3
"""
Test with minimal image and prompt to isolate the hanging issue
"""
import base64
import requests
import time

def test_minimal_request():
    """Test with the minimal 1x1 pixel PNG we created earlier"""
    
    # Use the minimal PNG we created earlier
    with open('/tmp/minimal.png', 'rb') as f:
        image_bytes = f.read()
    
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f"data:image/png;base64,{base64_string}"
    
    print(f"🖼️ Testing with minimal image: {len(image_bytes)} bytes")
    print(f"📏 Base64 size: {len(base64_string)} chars")
    
    # Minimal request
    payload = {
        "prompt": "What color?",  # Very short prompt
        "images": [data_url],
        "toolsInUse": True,
        "model": "deepseek-v3.1:671b-cloud"
    }
    
    print("📤 Sending minimal request...")
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:5000/llama3_1b/stream",
            json=payload,
            timeout=60  # Shorter timeout to detect hang quickly
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  Response in {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            # Just check if we get any content back
            content = response.text[:200]
            print(f"✅ Got response: {content}")
            return True
        else:
            print(f"❌ Error: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("⏱️  Timed out - confirming hang issue")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    return False

if __name__ == "__main__":
    print("🔬 Minimal Image Test (Debug Primary LLM Hang)")
    print("=" * 50)
    
    result = test_minimal_request()
    print(f"\nResult: {'✅ Works' if result else '❌ Hangs'}")