#!/usr/bin/env python3
"""
Test script to reproduce the image processing issue reported by user.
Tests if vision LLM gets triggered when interpreting an image.
"""

import requests
import json
import base64
import sys
from pathlib import Path

def create_test_image():
    """Create a simple test image in base64 format"""
    # Create a minimal 1x1 PNG image
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG header
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # bit depth, color type, etc.
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0x00,  # compressed data
        0x00, 0x00, 0x37, 0x6E, 0xF9, 0x24, 0x00, 0x00,
        0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42,  # IEND chunk
        0x60, 0x82
    ])
    return base64.b64encode(png_data).decode('utf-8')

def test_image_processing():
    """Test image processing with the server"""

    server_url = "http://localhost:5000"

    # Check if server is running
    try:
        health_response = requests.get(f"{server_url}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Server not responding properly: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not running: {e}")
        print("   Start the server with: ./start_complete.sh")
        return False

    print("✅ Server is running")

    # Create test image
    test_image = create_test_image()
    print(f"🖼️ Created test image: {len(test_image)} chars")

    # Test 1: Correct native API format with model and messages
    print("\n🧪 TEST 1: Native API with correct format")
    payload = {
        "model": "deepseek-v3.1:671b-cloud",
        "messages": [
            {"role": "user", "content": "Please analyze this image and describe what you see."}
        ],
        "images": [test_image],
        "toolsInUse": True  # Explicitly enable tools
    }

    try:
        response = requests.post(f"{server_url}/v1/chat/completions",
                               json=payload,
                               timeout=30)

        if response.status_code == 200:
            print("✅ Request successful")
            # Stream the response to see if vision processing occurs
            response_text = response.text
            if "IMAGE PROCESSING" in response_text:
                print("✅ Vision processing detected in response!")
                return True
            else:
                print("❌ No vision processing detected in response")
                print(f"Response preview: {response_text[:500]}...")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False

    except Exception as e:
        print(f"❌ Request exception: {e}")
        return False

def test_simple_request():
    """Test simple request without images first"""
    server_url = "http://localhost:5000"

    print("\n🧪 TEST 2: Simple request without images")
    payload = {
        "model": "deepseek-v3.1:671b-cloud",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "toolsInUse": False
    }

    try:
        response = requests.post(f"{server_url}/v1/chat/completions",
                               json=payload,
                               timeout=30)

        if response.status_code == 200:
            print("✅ Simple request successful - server is working")
            return True
        else:
            print(f"❌ Simple request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False

    except Exception as e:
        print(f"❌ Simple request exception: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Image Processing Test Script")
    print("=" * 50)

    # Run tests
    test1_passed = test_image_processing()
    test2_passed = test_simple_request()

    print("\n📋 Test Results:")
    print(f"   Image Processing: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Simple Request: {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed:
        print("\n💡 Image processing is working correctly")
        sys.exit(0)
    elif test2_passed:
        print("\n💡 Server works but image processing issue confirmed")
        print("\nPossible causes:")
        print("1. Images not being detected properly")
        print("2. Vision LLM not configured correctly")
        print("3. tools_in_use not being set properly")
        print("4. image_to_text tool not available")
        sys.exit(1)
    else:
        print("\n💡 Server itself has issues - both tests failed")
        sys.exit(1)