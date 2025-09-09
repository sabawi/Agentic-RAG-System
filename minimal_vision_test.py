#!/usr/bin/env python3
"""
Minimal test to isolate the vision model issue
"""
import base64
import json
import requests
import sys
import time

def test_minimal_vision():
    """Test with the simplest possible image and prompt"""
    
    # Create a minimal 1x1 pixel PNG image programmatically
    minimal_png = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D,  # IHDR chunk length (13 bytes)
        0x49, 0x48, 0x44, 0x52,  # "IHDR"
        0x00, 0x00, 0x00, 0x01,  # Width: 1
        0x00, 0x00, 0x00, 0x01,  # Height: 1
        0x08, 0x02,              # Bit depth: 8, Color type: 2 (RGB)
        0x00, 0x00, 0x00,        # Compression, filter, interlace
        0x90, 0x77, 0x53, 0xDE,  # CRC for IHDR
        0x00, 0x00, 0x00, 0x0C,  # IDAT chunk length (12 bytes)
        0x49, 0x44, 0x41, 0x54,  # "IDAT"
        0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x02, 0x00, 0x01,  # Compressed data
        0xE5, 0x27, 0xDE, 0xFC,  # CRC for IDAT
        0x00, 0x00, 0x00, 0x00,  # IEND chunk length (0 bytes)
        0x49, 0x45, 0x4E, 0x44,  # "IEND"
        0xAE, 0x42, 0x60, 0x82   # CRC for IEND
    ])
    
    print(f"📏 Minimal PNG size: {len(minimal_png)} bytes")
    
    # Encode to base64
    base64_minimal = base64.b64encode(minimal_png).decode('utf-8')
    print(f"📏 Base64 size: {len(base64_minimal)} chars")
    print(f"🔍 Base64: {base64_minimal}")
    
    # Test with this minimal image
    test_data = {
        "model": "qwen2.5vl:3b",
        "prompt": "What color is this?",
        "images": [base64_minimal],
        "stream": False
    }
    
    print("\n📤 Sending minimal image to Ollama...")
    print(f"🌐 URL: http://localhost:11434/api/generate")
    
    # Use a very short timeout to see if it hangs
    timeout_seconds = 10
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=test_data,
            timeout=timeout_seconds
        )
        elapsed = time.time() - start_time
        
        print(f"⏱️  Response received in {elapsed:.2f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('response', 'No response field')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"⏱️  Timed out after {timeout_seconds}s - model is hanging")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    return True

def test_without_images():
    """Control test - same model without images"""
    print("\n🔍 Control test: text-only prompt...")
    
    test_data = {
        "model": "qwen2.5vl:3b",
        "prompt": "What is 2 + 2?",
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=test_data,
            timeout=10
        )
        elapsed = time.time() - start_time
        
        print(f"⏱️  Response received in {elapsed:.2f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Text-only works: {result.get('response', 'No response field')}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        
    return False

if __name__ == "__main__":
    print("🔬 Minimal Vision Test")
    print("=" * 40)
    
    # Test 1: Text only (control)
    text_works = test_without_images()
    
    # Test 2: Minimal image
    vision_works = test_minimal_vision()
    
    print("\n" + "=" * 40)
    print("📋 Summary:")
    print(f"  Text-only: {'✅ Works' if text_works else '❌ Failed'}")
    print(f"  Vision: {'✅ Works' if vision_works else '❌ Failed/Hangs'}")
    
    if text_works and not vision_works:
        print("\n💡 Conclusion: Vision processing is hanging - not a format issue")
        print("   This suggests the model has trouble with the vision component")
        print("   even with minimal images.")
    elif not text_works:
        print("\n💡 Conclusion: Model has issues even with text-only")
    else:
        print("\n💡 Conclusion: Both work - issue may be with larger images or our code")