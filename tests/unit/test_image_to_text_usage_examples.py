#!/usr/bin/env python3
"""
Image-to-Text Tool Usage Examples and Manual Testing
Demonstrates different use cases and input methods.
"""

import asyncio
import base64
import json
import os
import sys
import tempfile
from io import BytesIO
from PIL import Image, ImageDraw

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_tools.image_to_text_tool import ImageToTextUserTool


def create_test_images():
    """Create various test images for demonstration."""
    test_images = {}
    
    # 1. Simple geometric shapes
    img1 = Image.new('RGB', (400, 300), color='white')
    draw1 = ImageDraw.Draw(img1)
    draw1.rectangle([50, 50, 150, 150], fill='red', outline='black')
    draw1.ellipse([200, 100, 350, 200], fill='blue', outline='black')
    
    buffer1 = BytesIO()
    img1.save(buffer1, format='PNG')
    test_images['geometric'] = buffer1.getvalue()
    
    # 2. Text and patterns
    img2 = Image.new('RGB', (500, 200), color='yellow')
    draw2 = ImageDraw.Draw(img2)
    # Create a grid pattern
    for x in range(0, 500, 25):
        draw2.line([(x, 0), (x, 200)], fill='black', width=1)
    for y in range(0, 200, 25):
        draw2.line([(0, y), (500, y)], fill='black', width=1)
    
    buffer2 = BytesIO()
    img2.save(buffer2, format='JPEG')
    test_images['pattern'] = buffer2.getvalue()
    
    # 3. Large image that needs scaling
    img3 = Image.new('RGB', (2000, 1500), color='green')
    draw3 = ImageDraw.Draw(img3)
    draw3.ellipse([500, 375, 1500, 1125], fill='purple', outline='white', width=10)
    
    buffer3 = BytesIO()
    img3.save(buffer3, format='PNG')
    test_images['large'] = buffer3.getvalue()
    
    return test_images


async def example_file_input():
    """Example: Processing local image files."""
    print("🖼️ Example 1: File Input Processing")
    print("=" * 50)
    
    tool = ImageToTextUserTool()
    test_images = create_test_images()
    
    # Save test image to temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        tmp_file.write(test_images['geometric'])
        tmp_path = tmp_file.name
    
    try:
        # Process single file
        images = [{"type": "file", "path": tmp_path}]
        
        result = await tool.execute(
            images=images,
            processing_mode="sequential",
            include_context=True
        )
        
        print(f"Success: {result['success']}")
        print(f"Processing mode: {result.get('processing_mode')}")
        print(f"Processed images: {result.get('processed_images', 0)}")
        
        if result['results']:
            img_result = result['results'][0]
            print(f"Image source: {img_result.get('source')}")
            print(f"Original size: {img_result.get('original_size')}")
            print(f"Processed size: {img_result.get('processed_size')}")
            print(f"Description: {img_result.get('description', 'N/A')}")
        
        print()
        
    finally:
        os.unlink(tmp_path)


async def example_base64_input():
    """Example: Processing base64 encoded images."""
    print("🖼️ Example 2: Base64 Input Processing")
    print("=" * 50)
    
    tool = ImageToTextUserTool()
    test_images = create_test_images()
    
    # Convert to base64
    b64_data = base64.b64encode(test_images['pattern']).decode('utf-8')
    b64_image = f"data:image/jpeg;base64,{b64_data}"
    
    images = [{"type": "base64", "data": b64_image, "quality": "high"}]
    
    result = await tool.execute(images=images)
    
    print(f"Success: {result['success']}")
    if result['results']:
        img_result = result['results'][0]
        print(f"Image source: {img_result.get('source')}")
        print(f"Description: {img_result.get('description', 'N/A')}")
    
    print()


async def example_url_input():
    """Example: Processing image from URL (mock)."""
    print("🖼️ Example 3: URL Input Processing (Mock)")
    print("=" * 50)
    
    tool = ImageToTextUserTool()
    
    # Note: This will fail without network/actual URL, but shows the format
    images = [{
        "type": "url", 
        "url": "https://example.com/sample-image.jpg",
        "quality": "auto"
    }]
    
    try:
        result = await tool.execute(images=images)
        print(f"Success: {result['success']}")
        if not result['success']:
            print(f"Expected error for demo URL: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Expected exception for demo URL: {e}")
    
    print()


async def example_mixed_input():
    """Example: Processing multiple images with mixed input types."""
    print("🖼️ Example 4: Mixed Input Processing")
    print("=" * 50)
    
    tool = ImageToTextUserTool()
    test_images = create_test_images()
    
    # Create temporary files
    temp_files = []
    images = []
    
    try:
        # File input
        tmp_file1 = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp_file1.write(test_images['geometric'])
        tmp_file1.close()
        temp_files.append(tmp_file1.name)
        images.append({"type": "file", "path": tmp_file1.name})
        
        # Base64 input
        b64_data = base64.b64encode(test_images['large']).decode('utf-8')
        images.append({
            "type": "base64", 
            "data": f"data:image/png;base64,{b64_data}",
            "quality": "high"
        })
        
        # Process in batch mode (limited to 2 images per our config)
        result = await tool.execute(
            images=images,
            processing_mode="batch",
            include_context=True
        )
        
        print(f"Success: {result['success']}")
        print(f"Total images: {result.get('total_images')}")
        print(f"Processed: {result.get('processed_images')}")
        print(f"Failed: {result.get('failed_images')}")
        print(f"Processing mode: {result.get('processing_mode')}")
        
        print("\nIndividual Results:")
        for i, img_result in enumerate(result.get('results', [])):
            print(f"  Image {i+1}:")
            print(f"    Success: {img_result.get('success')}")
            print(f"    Source: {img_result.get('source')}")
            if img_result.get('original_size'):
                print(f"    Size: {img_result['original_size']} → {img_result.get('processed_size')}")
            if img_result.get('description'):
                desc = img_result['description'][:100] + "..." if len(img_result['description']) > 100 else img_result['description']
                print(f"    Description: {desc}")
            if img_result.get('error'):
                print(f"    Error: {img_result['error']}")
    
    finally:
        # Clean up temp files
        for tmp_file in temp_files:
            try:
                os.unlink(tmp_file)
            except:
                pass
    
    print()


async def example_error_handling():
    """Example: Error handling scenarios."""
    print("🖼️ Example 5: Error Handling")
    print("=" * 50)
    
    tool = ImageToTextUserTool()
    
    # Test various error conditions
    error_cases = [
        {
            "name": "Empty images array",
            "images": [],
        },
        {
            "name": "Too many images",
            "images": [{"type": "base64", "data": "test"} for _ in range(6)],  # Max is 5
        },
        {
            "name": "Invalid image type",
            "images": [{"type": "invalid", "data": "test"}],
        },
        {
            "name": "Missing file",
            "images": [{"type": "file", "path": "/nonexistent/file.jpg"}],
        },
        {
            "name": "Invalid base64 format",
            "images": [{"type": "base64", "data": "invalid_data"}],
        }
    ]
    
    for case in error_cases:
        print(f"Testing: {case['name']}")
        result = await tool.execute(images=case['images'])
        print(f"  Success: {result['success']}")
        print(f"  Error: {result.get('error', 'No error message')}")
        print()


async def example_processing_modes():
    """Example: Different processing modes."""
    print("🖼️ Example 6: Processing Modes")
    print("=" * 50)
    
    tool = ImageToTextUserTool()
    test_images = create_test_images()
    
    # Create base64 images
    images = []
    for name, img_data in test_images.items():
        b64_data = base64.b64encode(img_data).decode('utf-8')
        images.append({
            "type": "base64",
            "data": f"data:image/png;base64,{b64_data}"
        })
    
    # Test batch mode
    print("Testing Batch Mode:")
    result_batch = await tool.execute(
        images=images[:2],  # Limit to batch size
        processing_mode="batch"
    )
    print(f"  Success: {result_batch['success']}")
    print(f"  Mode used: {result_batch.get('processing_mode')}")
    print(f"  Processed: {result_batch.get('processed_images', 0)}")
    
    print("\nTesting Sequential Mode:")
    result_seq = await tool.execute(
        images=images[:2],
        processing_mode="sequential"
    )
    print(f"  Success: {result_seq['success']}")
    print(f"  Mode used: {result_seq.get('processing_mode')}")
    print(f"  Processed: {result_seq.get('processed_images', 0)}")
    
    print()


async def example_constants_verification():
    """Example: Verify constants usage compliance."""
    print("🖼️ Example 7: Constants Compliance Verification")
    print("=" * 50)
    
    tool = ImageToTextUserTool()
    
    # Check parameters use constants
    params = tool.parameters
    max_items = params["properties"]["images"]["maxItems"]
    print(f"Max images per request: {max_items}")
    
    # Verify default processing mode
    default_mode = params["properties"]["processing_mode"]["default"]
    print(f"Default processing mode: {default_mode}")
    
    # Test image scaling with large image
    from config.llm_constants import DEFAULT_MAX_IMAGE_WIDTH, DEFAULT_MAX_IMAGE_HEIGHT
    
    print(f"Max image dimensions: {DEFAULT_MAX_IMAGE_WIDTH}x{DEFAULT_MAX_IMAGE_HEIGHT}")
    
    # Create oversized image
    large_img = Image.new('RGB', (3000, 2500), color='red')
    scaled_img = tool.processor._scale_image(large_img)
    
    print(f"Large image: {large_img.size} → {scaled_img.size}")
    print(f"Within limits: {scaled_img.width <= DEFAULT_MAX_IMAGE_WIDTH and scaled_img.height <= DEFAULT_MAX_IMAGE_HEIGHT}")
    
    print()


async def run_all_examples():
    """Run all usage examples."""
    print("🖼️ IMAGE-TO-TEXT TOOL USAGE EXAMPLES")
    print("=" * 60)
    print()
    
    examples = [
        example_file_input,
        example_base64_input,
        example_url_input,
        example_mixed_input,
        example_error_handling,
        example_processing_modes,
        example_constants_verification
    ]
    
    for example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"❌ Error in {example_func.__name__}: {e}")
            print()
    
    print("🎉 All examples completed!")


if __name__ == "__main__":
    # Run examples
    print("Note: These examples will show placeholder responses since image processing LLM")
    print("      configuration is required for actual image analysis.")
    print()
    
    asyncio.run(run_all_examples())