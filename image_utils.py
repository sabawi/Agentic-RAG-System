#!/usr/bin/env python3
"""
Image Utility Module
Provides image processing utilities for vision model integration including:
- Image size checking
- Image resizing to reduce token consumption
- Format conversion
"""

import base64
import io
import logging
import os
from typing import Tuple, Optional, Dict, Any
from PIL import Image

logger = logging.getLogger(__name__)


def get_image_size_mb(image_data: str) -> float:
    """
    Get the size of base64 encoded image data in megabytes.

    Args:
        image_data: Base64 encoded image string (with or without data URL prefix)

    Returns:
        Size in megabytes
    """
    try:
        # Remove data URL prefix if present
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',', 1)[1] if ',' in image_data else image_data

        # Calculate size from base64 string
        # Base64 encoding increases size by ~33%, so actual size = len * 3/4
        base64_bytes = len(image_data)
        actual_bytes = (base64_bytes * 3) / 4
        size_mb = actual_bytes / (1024 * 1024)

        return size_mb
    except Exception as e:
        logger.error(f"Error calculating image size: {e}")
        return 0.0


def decode_base64_image(image_data: str) -> Optional[Image.Image]:
    """
    Decode base64 image data to PIL Image object.

    Args:
        image_data: Base64 encoded image string (with or without data URL prefix)

    Returns:
        PIL Image object or None if decoding fails
    """
    try:
        # Remove data URL prefix if present
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',', 1)[1] if ',' in image_data else image_data

        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data)

        # Open as PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        return image
    except Exception as e:
        logger.error(f"Error decoding base64 image: {e}")
        return None


def encode_image_to_base64(image: Image.Image, format: str = 'JPEG', quality: int = 85) -> Optional[str]:
    """
    Encode PIL Image to base64 string.

    Args:
        image: PIL Image object
        format: Output format (JPEG, PNG, WEBP, etc.)
        quality: Compression quality (1-100, only for JPEG/WEBP)

    Returns:
        Base64 encoded string or None if encoding fails
    """
    try:
        # Convert RGBA to RGB if saving as JPEG
        if format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background

        # Save to bytes buffer
        buffer = io.BytesIO()
        save_kwargs = {'format': format}

        # Add quality parameter for JPEG and WEBP
        if format.upper() in ('JPEG', 'WEBP'):
            save_kwargs['quality'] = quality
            if format.upper() == 'JPEG':
                save_kwargs['optimize'] = True

        image.save(buffer, **save_kwargs)
        buffer.seek(0)

        # Encode to base64
        base64_data = base64.b64encode(buffer.read()).decode('utf-8')

        return base64_data
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}")
        return None


def resize_image(
    image: Image.Image,
    max_dimension: int = 2048,
    preserve_aspect_ratio: bool = True
) -> Image.Image:
    """
    Resize image to reduce file size while preserving quality.

    Args:
        image: PIL Image object
        max_dimension: Maximum width or height in pixels
        preserve_aspect_ratio: Whether to preserve aspect ratio

    Returns:
        Resized PIL Image object
    """
    try:
        width, height = image.size

        # Check if resizing is needed
        if width <= max_dimension and height <= max_dimension:
            logger.info(f"🖼️ Image size ({width}x{height}) already within limits, no resize needed")
            return image

        if preserve_aspect_ratio:
            # Calculate new dimensions maintaining aspect ratio
            if width > height:
                new_width = max_dimension
                new_height = int((max_dimension / width) * height)
            else:
                new_height = max_dimension
                new_width = int((max_dimension / height) * width)
        else:
            new_width = max_dimension
            new_height = max_dimension

        logger.info(f"🖼️ Resizing image from {width}x{height} to {new_width}x{new_height}")

        # Resize using high-quality Lanczos resampling
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return resized_image
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        # Return original image if resizing fails
        return image


def process_image_for_vision_model(
    image_data: str,
    config: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    Process image for vision model: check size and resize if needed.

    Args:
        image_data: Base64 encoded image string
        config: Image processing configuration from llm_config.yaml

    Returns:
        Tuple of (processed_base64_data, metadata_dict)
        metadata includes: original_size_mb, final_size_mb, resized, dimensions
    """
    metadata = {
        'original_size_mb': 0.0,
        'final_size_mb': 0.0,
        'resized': False,
        'original_dimensions': None,
        'final_dimensions': None,
        'processing_error': None
    }

    try:
        # Get configuration
        max_size_mb = config.get('max_size_mb', 2.0)
        resize_enabled = config.get('resize_enabled', True)
        resize_quality = config.get('resize_quality', 85)
        max_dimension = config.get('max_dimension', 2048)
        preserve_aspect_ratio = config.get('preserve_aspect_ratio', True)
        output_format = config.get('output_format', 'JPEG').upper()

        # Calculate original size
        original_size_mb = get_image_size_mb(image_data)
        metadata['original_size_mb'] = original_size_mb

        logger.info(f"🖼️ Image size: {original_size_mb:.2f} MB (limit: {max_size_mb} MB)")

        # Check if resizing is needed
        if not resize_enabled or original_size_mb <= max_size_mb:
            logger.info(f"🖼️ Image within size limit, no processing needed")
            metadata['final_size_mb'] = original_size_mb
            return image_data, metadata

        # Decode image
        logger.info(f"🖼️ Image exceeds limit, resizing...")
        image = decode_base64_image(image_data)

        if image is None:
            metadata['processing_error'] = "Failed to decode image"
            logger.error(f"🖼️ Failed to decode image for resizing")
            return image_data, metadata

        metadata['original_dimensions'] = f"{image.width}x{image.height}"

        # Resize image
        resized_image = resize_image(image, max_dimension, preserve_aspect_ratio)
        metadata['final_dimensions'] = f"{resized_image.width}x{resized_image.height}"

        # Encode back to base64
        processed_base64 = encode_image_to_base64(resized_image, output_format, resize_quality)

        if processed_base64 is None:
            metadata['processing_error'] = "Failed to encode resized image"
            logger.error(f"🖼️ Failed to encode resized image")
            return image_data, metadata

        # Calculate final size
        final_size_mb = get_image_size_mb(processed_base64)
        metadata['final_size_mb'] = final_size_mb
        metadata['resized'] = True

        reduction_percent = ((original_size_mb - final_size_mb) / original_size_mb) * 100
        logger.info(
            f"🖼️ Image resized successfully: "
            f"{original_size_mb:.2f} MB → {final_size_mb:.2f} MB "
            f"({reduction_percent:.1f}% reduction)"
        )

        return processed_base64, metadata

    except Exception as e:
        logger.error(f"🖼️ Error processing image: {e}")
        metadata['processing_error'] = str(e)
        # Return original image on error
        return image_data, metadata


def process_image_from_file(
    file_path: str,
    config: Dict[str, Any]
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Load image from file and process it for vision model.

    Args:
        file_path: Path to image file
        config: Image processing configuration

    Returns:
        Tuple of (base64_data, metadata_dict)
    """
    metadata = {
        'original_size_mb': 0.0,
        'final_size_mb': 0.0,
        'resized': False,
        'processing_error': None
    }

    try:
        # Check if file exists
        if not os.path.isfile(file_path):
            metadata['processing_error'] = f"File not found: {file_path}"
            return None, metadata

        # Get file size
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        metadata['original_size_mb'] = file_size_mb

        # Open image
        image = Image.open(file_path)
        metadata['original_dimensions'] = f"{image.width}x{image.height}"

        # Get configuration
        max_size_mb = config.get('max_size_mb', 2.0)
        resize_enabled = config.get('resize_enabled', True)
        resize_quality = config.get('resize_quality', 85)
        max_dimension = config.get('max_dimension', 2048)
        preserve_aspect_ratio = config.get('preserve_aspect_ratio', True)
        output_format = config.get('output_format', 'JPEG').upper()

        # Check if resizing needed
        if resize_enabled and file_size_mb > max_size_mb:
            logger.info(f"🖼️ File size {file_size_mb:.2f} MB exceeds limit, resizing...")
            image = resize_image(image, max_dimension, preserve_aspect_ratio)
            metadata['resized'] = True
            metadata['final_dimensions'] = f"{image.width}x{image.height}"

        # Encode to base64
        base64_data = encode_image_to_base64(image, output_format, resize_quality)

        if base64_data:
            final_size_mb = get_image_size_mb(base64_data)
            metadata['final_size_mb'] = final_size_mb

            if metadata['resized']:
                reduction_percent = ((file_size_mb - final_size_mb) / file_size_mb) * 100
                logger.info(
                    f"🖼️ Image processed: "
                    f"{file_size_mb:.2f} MB → {final_size_mb:.2f} MB "
                    f"({reduction_percent:.1f}% reduction)"
                )

        return base64_data, metadata

    except Exception as e:
        logger.error(f"🖼️ Error processing image from file: {e}")
        metadata['processing_error'] = str(e)
        return None, metadata
