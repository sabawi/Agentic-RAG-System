#!/usr/bin/env python3
"""
Debug script to test different image formats with Ollama Python library
"""
import ollama
import base64
import io
from PIL import Image, ImageDraw

def create_simple_image():
    """Create a simple test image and return as base64"""
    img = Image.new('RGB', (200, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 40), "HELLO", fill='black')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    base64_string = base64.b64encode(img_bytes).decode('utf-8')

    return base64_string, img_bytes

print("=" * 70)
print("Testing Ollama Image Formats")
print("=" * 70)

base64_img, img_bytes = create_simple_image()

# Test 1: Raw base64 string
print("\n📝 Test 1: Raw base64 string")
print(f"   Length: {len(base64_img)} chars")
print(f"   Preview: {base64_img[:50]}...")
try:
    response = ollama.generate(
        model='qwen2.5vl:3b',
        prompt='What text do you see?',
        images=[base64_img],
        stream=False
    )
    print(f"✅ SUCCESS: {response['response'][:200]}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 2: Bytes object
print("\n📝 Test 2: Bytes object")
print(f"   Length: {len(img_bytes)} bytes")
try:
    response = ollama.generate(
        model='qwen2.5vl:3b',
        prompt='What text do you see?',
        images=[img_bytes],
        stream=False
    )
    print(f"✅ SUCCESS: {response['response'][:200]}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 3: Data URL format
print("\n📝 Test 3: Data URL format")
data_url = f"data:image/png;base64,{base64_img}"
print(f"   Length: {len(data_url)} chars")
print(f"   Preview: {data_url[:60]}...")
try:
    response = ollama.generate(
        model='qwen2.5vl:3b',
        prompt='What text do you see?',
        images=[data_url],
        stream=False
    )
    print(f"✅ SUCCESS: {response['response'][:200]}")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n" + "=" * 70)
