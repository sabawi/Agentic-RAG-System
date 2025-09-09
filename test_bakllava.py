#!/usr/bin/env python3
"""
Test if bakllava vision model works better than qwen2.5vl
"""
import base64
import requests
import time

def test_bakllava():
    """Test with bakllava model"""
    
    # Use the minimal PNG
    with open('/tmp/minimal.png', 'rb') as f:
        img_bytes = f.read()
    
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    print(f"🖼️ Testing bakllava with minimal PNG: {len(img_bytes)} bytes")
    
    test_data = {
        "model": "bakllava:latest",
        "prompt": "What do you see in this image?",
        "images": [base64_str],
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=test_data,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        print(f"⏱️  Response in {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ bakllava Success: {result.get('response', 'No response')}")
            return True
        else:
            print(f"❌ bakllava Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏱️  bakllava timeout")
        return False
    except Exception as e:
        print(f"❌ bakllava exception: {e}")
        return False
    
    return False

def test_with_real_image():
    """Test bakllava with the real image that was failing"""
    
    image_path = './sandbox_workspace/binomial_distribution.png'
    with open(image_path, 'rb') as f:
        img_bytes = f.read()
    
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    print(f"\n🖼️ Testing bakllava with real image: {len(img_bytes)} bytes")
    
    test_data = {
        "model": "bakllava:latest",
        "prompt": "Describe this image briefly",
        "images": [base64_str],
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=test_data,
            timeout=120
        )
        elapsed = time.time() - start_time
        
        print(f"⏱️  Real image response in {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Real image success: {result.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Real image error: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("⏱️  Real image timeout")
        return False
    except Exception as e:
        print(f"❌ Real image exception: {e}")
        return False
    
    return False

if __name__ == "__main__":
    print("🔬 Testing bakllava Vision Model")
    print("=" * 40)
    
    minimal_works = test_bakllava()
    real_works = test_with_real_image()
    
    print(f"\n📋 bakllava Results:")
    print(f"  Minimal image: {'✅ Works' if minimal_works else '❌ Failed'}")
    print(f"  Real image: {'✅ Works' if real_works else '❌ Failed'}")
    
    if minimal_works and real_works:
        print("\n💡 bakllava works! The issue is with qwen2.5vl model")
        print("   Recommendation: Switch to bakllava:latest for vision tasks")
    elif minimal_works and not real_works:
        print("\n💡 bakllava works with small images but not large ones")
    else:
        print("\n💡 bakllava also has issues - may be system-wide problem")