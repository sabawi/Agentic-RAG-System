
import os
import base64
import pytest
from pathlib import Path
from PIL import Image, ImageDraw
import io

# Make sure the script can find the image_utils module
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

import image_utils

def create_test_image(width: int, height: int, format: str = 'PNG') -> str:
    """Create a test image and return as base64."""
    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, width-10, height-10], outline=(255, 255, 0), width=5)
    draw.ellipse([width//4, height//4, 3*width//4, 3*height//4], fill=(255, 0, 0))

    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    base64_data = base64.b64encode(buffer.read()).decode('utf-8')
    return base64_data

def test_get_image_size_mb():
    """Test that the image size calculation is correct."""
    test_image = create_test_image(100, 100, 'PNG')
    size_mb = image_utils.get_image_size_mb(test_image)
    assert size_mb > 0

def test_decode_base64_image():
    """Test that a base64 image is decoded correctly."""
    test_image = create_test_image(100, 100, 'PNG')
    img = image_utils.decode_base64_image(test_image)
    assert isinstance(img, Image.Image)
    assert img.size == (100, 100)

def test_encode_image_to_base64():
    """Test that an image is encoded to base64 correctly."""
    img = Image.new('RGB', (100, 100), color='red')
    base64_image = image_utils.encode_image_to_base64(img)
    assert isinstance(base64_image, str)
    assert len(base64_image) > 0

def test_resize_image():
    """Test that an image is resized correctly."""
    img = Image.new('RGB', (2000, 1500), color='red')
    resized_img = image_utils.resize_image(img, max_dimension=1024)
    assert resized_img.width == 1024
    assert resized_img.height == 768

def test_process_image_for_vision_model_resize():
    """Test that a large image is resized by the processing pipeline."""
    test_image = create_test_image(8000, 6000, 'PNG')
    config = {
        'max_size_mb': 0.1,
        'resize_enabled': True,
        'resize_quality': 85,
        'max_dimension': 2048,
        'preserve_aspect_ratio': True,
        'output_format': 'JPEG'
    }
    print(f"Image size: {image_utils.get_image_size_mb(test_image)}")
    processed_image, metadata = image_utils.process_image_for_vision_model(test_image, config)
    assert metadata['resized'] is True
    assert metadata['final_size_mb'] < metadata['original_size_mb']

def test_process_image_for_vision_model_no_resize():
    """Test that a small image is not resized by the processing pipeline."""
    test_image = create_test_image(800, 600, 'JPEG')
    config = {
        'max_size_mb': 2.0,
        'resize_enabled': True,
        'resize_quality': 85,
        'max_dimension': 2048,
        'preserve_aspect_ratio': True,
        'output_format': 'JPEG'
    }
    processed_image, metadata = image_utils.process_image_for_vision_model(test_image, config)
    assert metadata['resized'] is False

def test_process_image_for_vision_model_disabled():
    """Test that resizing is disabled."""
    test_image = create_test_image(4000, 3000, 'PNG')
    config = {
        'max_size_mb': 0.1,
        'resize_enabled': False,
        'resize_quality': 85,
        'max_dimension': 2048,
        'preserve_aspect_ratio': True,
        'output_format': 'JPEG'
    }
    processed_image, metadata = image_utils.process_image_for_vision_model(test_image, config)
    assert metadata['resized'] is False
