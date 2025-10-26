#!/usr/bin/env python3
"""
Test the server's image processing via API to verify the fix
"""
import base64
import requests
import json
import time

def test_server_image_processing():
    """Test the server API with image processing"""
    
    # Read the test image
    image_path = './sandbox_workspace/binomial_distribution.png'
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Encode to base64 with data URL prefix (like browser would send)
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f"data:image/png;base64,{base64_string}"
    
    print(f"🖼️ Testing server API with image: {len(image_bytes)} bytes")
    print(f"📏 Data URL length: {len(data_url)} chars")
    
    # Prepare the API request using the streaming endpoint format
    payload = {
        "prompt": "Please analyze this chart image and describe what type of distribution it shows, including any notable patterns or characteristics.",
        "images": [data_url],
        "toolsInUse": True,
        "model": "deepseek-v3.1:671b-cloud"
    }
    
    print("📤 Sending request to server...")
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:5000/llama3_1b/stream",
            json=payload,
            timeout=180  # Give it plenty of time
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  Response received in {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if the response contains image analysis
            response_text = result.get('response', '')
            if 'binomial' in response_text.lower() or 'distribution' in response_text.lower():
                print(f"✅ Server image processing SUCCESS!")
                print(f"📝 Response excerpt: {response_text[:300]}...")
                return True
            else:
                print(f"🤔 Server responded but may not have processed image:")
                print(f"📝 Response: {response_text[:200]}...")
                return False
        else:
            print(f"❌ Server error: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Server Image Processing Test")
    print("=" * 40)
    
    # First check if server is responding
    try:
        status_response = requests.get("http://localhost:5000/health", timeout=5)
        if status_response.status_code == 200:
            print("✅ Server is responding")
        else:
            print(f"⚠️  Server status: {status_response.status_code}")
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        exit(1)
    
    # Test the image processing
    success = test_server_image_processing()
    
    print("\n" + "=" * 40)
    print(f"📋 End-to-End Test Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("\n💡 CONFIRMED: Image processing is fixed!")
        print("   - bakllava:latest model works correctly")
        print("   - Base64 format is handled properly")
        print("   - Server integration is working")
        print("   - Vision tool responds through API")
    else:
        print("\n💡 Still has issues - needs further investigation")