#!/usr/bin/env python3
"""
Test script to verify vision model works with base64 images
Tests the fixed _process_with_ollama() implementation
"""

import sys
import os
import base64
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_tools.image_to_text import ImageToTextTool
from PIL import Image, ImageDraw, ImageFont
import io

def create_test_image_base64():
    """Create a simple test image with text and return as base64"""
    # Create a simple image with text
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)

    # Draw some text
    try:
        # Try to use a default font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    draw.text((50, 50), "TEST IMAGE", fill='black', font=font)
    draw.text((50, 100), "Vision Model Test", fill='blue', font=font)
    draw.rectangle([10, 10, 390, 190], outline='red', width=3)

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    base64_string = base64.b64encode(img_bytes).decode('utf-8')

    return base64_string

async def test_vision_with_base64():
    """Test the vision model with a base64 encoded image"""
    print("=" * 70)
    print("🧪 Testing Vision Model with Base64 Image")
    print("=" * 70)

    # Create test image
    print("\n📸 Step 1: Creating test image...")
    base64_img = create_test_image_base64()
    print(f"✅ Created test image: {len(base64_img)} chars of base64 data")
    print(f"   Preview: {base64_img[:50]}...")

    # Initialize the tool
    print("\n🔧 Step 2: Initializing ImageToTextTool...")
    tool = ImageToTextTool()
    print(f"✅ Tool initialized: {tool.name}")
    print(f"   Vision config: {tool.vision_config.get('model', 'qwen2.5vl:3b')}")

    # Test with base64 image
    print("\n🖼️  Step 3: Processing image with vision model...")
    print("   (This may take 30-60 seconds for cloud models...)")

    result = await tool.execute(
        prompt="What text do you see in this image?",
        image=base64_img
    )

    # Display results
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS")
    print("=" * 70)

    if result.get("success"):
        print("✅ SUCCESS: Vision model processed the image!")
        print("\n📝 Response:")
        description = result.get("description", "")
        # Print first 500 chars
        if len(description) > 500:
            print(description[:500] + "...")
        else:
            print(description)
        print(f"\n📏 Total response length: {len(description)} characters")
        print(f"🤖 Model used: {result.get('model', 'unknown')}")
        print(f"⏰ Timestamp: {result.get('timestamp', 'unknown')}")
    else:
        print("❌ FAILED: Vision model encountered an error")
        print(f"Error: {result.get('error', 'Unknown error')}")
        return False

    print("\n" + "=" * 70)
    return True

async def test_vision_with_data_url():
    """Test with data URL format (data:image/png;base64,...)"""
    print("\n" + "=" * 70)
    print("🧪 Testing Vision Model with Data URL Format")
    print("=" * 70)

    # Create test image
    print("\n📸 Creating test image with data URL format...")
    base64_img = create_test_image_base64()
    data_url = f"data:image/png;base64,{base64_img}"
    print(f"✅ Created data URL: {len(data_url)} chars")
    print(f"   Preview: {data_url[:60]}...")

    # Initialize the tool
    tool = ImageToTextTool()

    # Test with data URL
    print("\n🖼️  Processing image with data URL format...")
    print("   (This may take 30-60 seconds for cloud models...)")

    result = await tool.execute(
        prompt="Describe what you see",
        image=data_url
    )

    # Display results
    print("\n📊 Data URL Test Results:")
    if result.get("success"):
        print("✅ SUCCESS: Data URL format works!")
        description = result.get("description", "")
        print(f"📏 Response length: {len(description)} characters")
    else:
        print("❌ FAILED: Data URL test failed")
        print(f"Error: {result.get('error', 'Unknown error')}")
        return False

    return True

async def main():
    """Run all vision tests"""
    print("\n" + "🎯" * 35)
    print("   VISION MODEL BASE64 INTEGRATION TEST")
    print("🎯" * 35)

    try:
        # Test 1: Plain base64
        success1 = await test_vision_with_base64()

        # Test 2: Data URL format
        success2 = await test_vision_with_data_url()

        # Summary
        print("\n" + "=" * 70)
        print("🎯 TEST SUMMARY")
        print("=" * 70)
        print(f"Base64 format test:  {'✅ PASSED' if success1 else '❌ FAILED'}")
        print(f"Data URL format test: {'✅ PASSED' if success2 else '❌ FAILED'}")

        if success1 and success2:
            print("\n🎉 ALL TESTS PASSED! Vision model is working correctly!")
            print("✅ Ready for Open-WebUI testing")
        else:
            print("\n⚠️  Some tests failed. Review errors above.")

        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
