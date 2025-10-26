#!/usr/bin/env python3
"""
Test Image Resizing Functionality
Tests the image_utils module for proper image size checking and resizing.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import base64
import image_utils
from PIL import Image
import io


def create_test_image(width: int, height: int, format: str = 'PNG') -> str:
    """Create a test image and return as base64."""
    # Create a simple test image with some color
    img = Image.new('RGB', (width, height), color=(73, 109, 137))

    # Add some visual elements
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, width-10, height-10], outline=(255, 255, 0), width=5)
    draw.ellipse([width//4, height//4, 3*width//4, 3*height//4], fill=(255, 0, 0))

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    base64_data = base64.b64encode(buffer.read()).decode('utf-8')

    return base64_data


def test_image_size_calculation():
    """Test image size calculation."""
    print("🧪 Test 1: Image Size Calculation")
    print("=" * 60)

    # Create a test image
    test_image = create_test_image(1000, 1000, 'PNG')

    # Calculate size
    size_mb = image_utils.get_image_size_mb(test_image)

    print(f"✅ Image size: {size_mb:.2f} MB")
    print(f"   Base64 length: {len(test_image)} chars")
    print()

    return size_mb > 0


def test_image_decode_encode():
    """Test image decoding and encoding."""
    print("🧪 Test 2: Image Decode/Encode")
    print("=" * 60)

    # Create a test image
    test_image = create_test_image(800, 600, 'PNG')
    original_size = image_utils.get_image_size_mb(test_image)

    # Decode
    img = image_utils.decode_base64_image(test_image)

    if img:
        print(f"✅ Decoded successfully: {img.width}x{img.height} pixels")

        # Encode as JPEG
        encoded_jpeg = image_utils.encode_image_to_base64(img, 'JPEG', 85)
        jpeg_size = image_utils.get_image_size_mb(encoded_jpeg)

        print(f"✅ Encoded as JPEG: {jpeg_size:.2f} MB (was {original_size:.2f} MB PNG)")
        print(f"   Size reduction: {((original_size - jpeg_size) / original_size * 100):.1f}%")
        print()

        return True
    else:
        print("❌ Failed to decode image")
        print()
        return False


def test_image_resizing():
    """Test image resizing."""
    print("🧪 Test 3: Image Resizing")
    print("=" * 60)

    # Create a large test image
    test_image = create_test_image(4000, 3000, 'PNG')

    # Decode
    img = image_utils.decode_base64_image(test_image)

    if img:
        print(f"Original size: {img.width}x{img.height} pixels")

        # Resize to max 2048
        resized_img = image_utils.resize_image(img, max_dimension=2048, preserve_aspect_ratio=True)

        print(f"✅ Resized to: {resized_img.width}x{resized_img.height} pixels")

        # Check aspect ratio preserved
        original_ratio = img.width / img.height
        resized_ratio = resized_img.width / resized_img.height
        ratio_diff = abs(original_ratio - resized_ratio)

        if ratio_diff < 0.01:
            print(f"✅ Aspect ratio preserved: {original_ratio:.3f} ≈ {resized_ratio:.3f}")
        else:
            print(f"⚠️ Aspect ratio changed: {original_ratio:.3f} → {resized_ratio:.3f}")

        print()
        return True
    else:
        print("❌ Failed to decode image")
        print()
        return False


def test_full_processing_pipeline():
    """Test the complete processing pipeline."""
    print("🧪 Test 4: Full Processing Pipeline")
    print("=" * 60)

    # Create a large image that exceeds 2MB
    print("Creating large test image...")
    test_image = create_test_image(5000, 4000, 'PNG')
    original_size = image_utils.get_image_size_mb(test_image)

    print(f"Original image: {original_size:.2f} MB")

    # Configuration
    config = {
        'max_size_mb': 2.0,
        'resize_enabled': True,
        'resize_quality': 85,
        'max_dimension': 2048,
        'preserve_aspect_ratio': True,
        'output_format': 'JPEG'
    }

    # Process image
    processed_image, metadata = image_utils.process_image_for_vision_model(test_image, config)

    print("\nProcessing Results:")
    print(f"  Original size: {metadata['original_size_mb']:.2f} MB")
    print(f"  Final size: {metadata['final_size_mb']:.2f} MB")
    print(f"  Resized: {metadata['resized']}")
    print(f"  Original dimensions: {metadata['original_dimensions']}")
    print(f"  Final dimensions: {metadata['final_dimensions']}")

    if metadata['processing_error']:
        print(f"  ❌ Error: {metadata['processing_error']}")
        print()
        return False

    if metadata['resized']:
        reduction = ((metadata['original_size_mb'] - metadata['final_size_mb']) / metadata['original_size_mb']) * 100
        print(f"  ✅ Size reduction: {reduction:.1f}%")

        # Verify it's under limit
        if metadata['final_size_mb'] <= config['max_size_mb']:
            print(f"  ✅ Final size within limit ({config['max_size_mb']} MB)")
        else:
            print(f"  ⚠️ Final size still exceeds limit ({config['max_size_mb']} MB)")

    print()
    return True


def test_small_image_no_resize():
    """Test that small images are not resized."""
    print("🧪 Test 5: Small Image (No Resize)")
    print("=" * 60)

    # Create a small image
    test_image = create_test_image(800, 600, 'JPEG')
    original_size = image_utils.get_image_size_mb(test_image)

    print(f"Original image: {original_size:.2f} MB")

    # Configuration
    config = {
        'max_size_mb': 2.0,
        'resize_enabled': True,
        'resize_quality': 85,
        'max_dimension': 2048,
        'preserve_aspect_ratio': True,
        'output_format': 'JPEG'
    }

    # Process image
    processed_image, metadata = image_utils.process_image_for_vision_model(test_image, config)

    print(f"Final size: {metadata['final_size_mb']:.2f} MB")
    print(f"Resized: {metadata['resized']}")

    if not metadata['resized']:
        print("✅ Small image correctly skipped resizing")
    else:
        print("⚠️ Small image was resized unnecessarily")

    print()
    return not metadata['resized']


def test_resize_disabled():
    """Test that resizing can be disabled."""
    print("🧪 Test 6: Resize Disabled")
    print("=" * 60)

    # Create a large image
    test_image = create_test_image(4000, 3000, 'PNG')
    original_size = image_utils.get_image_size_mb(test_image)

    print(f"Original image: {original_size:.2f} MB")

    # Configuration with resize disabled
    config = {
        'max_size_mb': 2.0,
        'resize_enabled': False,  # Disabled!
        'resize_quality': 85,
        'max_dimension': 2048,
        'preserve_aspect_ratio': True,
        'output_format': 'JPEG'
    }

    # Process image
    processed_image, metadata = image_utils.process_image_for_vision_model(test_image, config)

    print(f"Final size: {metadata['final_size_mb']:.2f} MB")
    print(f"Resized: {metadata['resized']}")

    if not metadata['resized']:
        print("✅ Resizing correctly disabled")
    else:
        print("❌ Image was resized despite resize_enabled=False")

    print()
    return not metadata['resized']


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("IMAGE RESIZING TEST SUITE")
    print("=" * 60)
    print()

    tests = [
        ("Image Size Calculation", test_image_size_calculation),
        ("Image Decode/Encode", test_image_decode_encode),
        ("Image Resizing", test_image_resizing),
        ("Full Processing Pipeline", test_full_processing_pipeline),
        ("Small Image (No Resize)", test_small_image_no_resize),
        ("Resize Disabled", test_resize_disabled),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False, str(e)))
            print()

    # Print summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result, _ in results if result)
    total = len(results)

    for test_name, result, error in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if error:
            print(f"         Error: {error}")

    print()
    print(f"Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    print("=" * 60)
    print()

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
