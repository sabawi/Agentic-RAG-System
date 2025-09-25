#!/usr/bin/env python3
"""
Production-ready signature-based image detection for fastapi_server_complete.py

This module replaces the flawed length-based detection with proper
image signature validation and comprehensive error reporting.
"""

import base64
import os
import re
from typing import Tuple, Optional, List, Dict, Any

class ImageSignatureValidator:
    """
    Signature-based image validator for production use

    Replaces arbitrary length thresholds with actual image format detection
    """

    # Image format signatures (magic bytes)
    IMAGE_SIGNATURES = {
        b'\x89PNG\r\n\x1a\n': 'PNG',
        b'\xff\xd8\xff': 'JPEG',
        b'GIF87a': 'GIF',
        b'GIF89a': 'GIF',
        b'RIFF': 'WEBP',  # Requires additional validation
        b'BM': 'BMP',
        b'\x00\x00\x01\x00': 'ICO',
        b'II*\x00': 'TIFF',
        b'MM\x00*': 'TIFF',
    }

    def validate_image_data(self, img_data: str, index: int = 1) -> Dict[str, Any]:
        """
        Validate image data using signatures instead of length

        Returns:
            {
                'is_valid': bool,
                'processed_data': str,  # Base64 data or "noimage"
                'format': str,          # Image format if valid
                'size_bytes': int,      # Size in bytes
                'error': str,           # Error message if invalid
                'user_error': str       # User-friendly error message
            }
        """

        if not img_data or not isinstance(img_data, str):
            return {
                'is_valid': False,
                'processed_data': 'noimage',
                'format': None,
                'size_bytes': 0,
                'error': 'Empty or invalid input',
                'user_error': f'Image {index}: No image data provided'
            }

        # Handle data URI format
        original_data = img_data
        if img_data.startswith('data:image/'):
            try:
                if ';base64,' not in img_data:
                    return {
                        'is_valid': False,
                        'processed_data': 'noimage',
                        'format': None,
                        'size_bytes': 0,
                        'error': 'Data URI missing base64 specification',
                        'user_error': f'Image {index}: Invalid data format - missing base64 encoding'
                    }

                _, base64_part = img_data.split(';base64,', 1)
                img_data = base64_part

            except ValueError:
                return {
                    'is_valid': False,
                    'processed_data': 'noimage',
                    'format': None,
                    'size_bytes': 0,
                    'error': 'Malformed data URI',
                    'user_error': f'Image {index}: Invalid data URI format'
                }

        # Check if it looks like a file path
        if self._looks_like_file_path(img_data):
            return self._validate_image_file(img_data, index)

        # Validate as base64 image data using signatures
        return self._validate_base64_image(img_data, index)

    def _looks_like_file_path(self, data: str) -> bool:
        """Check if data appears to be a file path"""
        path_indicators = ['/', '\\']
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.ico']

        has_path_chars = any(indicator in data for indicator in path_indicators)
        has_image_ext = any(data.lower().endswith(ext) for ext in image_extensions)

        # If it has path characteristics AND doesn't look like pure base64
        return (has_path_chars or has_image_ext) and not self._looks_like_base64(data)

    def _looks_like_base64(self, data: str) -> bool:
        """Quick check if string looks like base64"""
        if len(data) < 4:
            return False
        return bool(re.match(r'^[A-Za-z0-9+/]*={0,2}$', data))

    def _validate_image_file(self, file_path: str, index: int) -> Dict[str, Any]:
        """Validate image file using signatures"""
        expanded_path = os.path.expanduser(file_path.strip())

        if not os.path.exists(expanded_path):
            return {
                'is_valid': False,
                'processed_data': 'noimage',
                'format': None,
                'size_bytes': 0,
                'error': f'File not found: {expanded_path}',
                'user_error': f'Image {index}: File not found - please check the path and try again'
            }

        if not os.path.isfile(expanded_path):
            return {
                'is_valid': False,
                'processed_data': 'noimage',
                'format': None,
                'size_bytes': 0,
                'error': f'Not a file: {expanded_path}',
                'user_error': f'Image {index}: Path exists but is not a file'
            }

        try:
            # Read file and validate using signatures
            with open(expanded_path, 'rb') as f:
                img_bytes = f.read()

            if len(img_bytes) < 8:
                return {
                    'is_valid': False,
                    'processed_data': 'noimage',
                    'format': None,
                    'size_bytes': len(img_bytes),
                    'error': f'File too small ({len(img_bytes)} bytes)',
                    'user_error': f'Image {index}: File is too small to be a valid image'
                }

            # Detect format using signatures
            image_format = self._detect_format_from_bytes(img_bytes)
            if not image_format:
                return {
                    'is_valid': False,
                    'processed_data': 'noimage',
                    'format': None,
                    'size_bytes': len(img_bytes),
                    'error': 'File is not a recognized image format',
                    'user_error': f'Image {index}: File exists but is not a valid image format'
                }

            # Convert to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            return {
                'is_valid': True,
                'processed_data': img_base64,
                'format': image_format,
                'size_bytes': len(img_bytes),
                'error': None,
                'user_error': None
            }

        except PermissionError:
            return {
                'is_valid': False,
                'processed_data': 'noimage',
                'format': None,
                'size_bytes': 0,
                'error': 'Permission denied reading file',
                'user_error': f'Image {index}: Cannot access file - permission denied'
            }
        except Exception as e:
            return {
                'is_valid': False,
                'processed_data': 'noimage',
                'format': None,
                'size_bytes': 0,
                'error': f'Error reading file: {str(e)}',
                'user_error': f'Image {index}: Error reading file - {str(e)}'
            }

    def _validate_base64_image(self, base64_data: str, index: int) -> Dict[str, Any]:
        """Validate base64 data contains image using signatures"""

        # Quick validation - must look like base64
        if not self._looks_like_base64(base64_data):
            return {
                'is_valid': False,
                'processed_data': 'noimage',
                'format': None,
                'size_bytes': 0,
                'error': 'Invalid base64 characters',
                'user_error': f'Image {index}: Contains invalid characters - please ensure image is properly encoded'
            }

        # Decode the base64 data
        try:
            decoded_bytes = base64.b64decode(base64_data, validate=True)
        except Exception as e:
            return {
                'is_valid': False,
                'processed_data': 'noimage',
                'format': None,
                'size_bytes': 0,
                'error': f'Base64 decode failed: {str(e)}',
                'user_error': f'Image {index}: Corrupted image data - please re-upload your image'
            }

        # Check minimum size
        if len(decoded_bytes) < 8:
            return {
                'is_valid': False,
                'processed_data': 'noimage',
                'format': None,
                'size_bytes': len(decoded_bytes),
                'error': f'Data too small ({len(decoded_bytes)} bytes)',
                'user_error': f'Image {index}: Image data is too small or incomplete'
            }

        # THE CRITICAL PART: Check image signatures
        image_format = self._detect_format_from_bytes(decoded_bytes)
        if not image_format:
            return {
                'is_valid': False,
                'processed_data': 'noimage',
                'format': None,
                'size_bytes': len(decoded_bytes),
                'error': 'Valid base64 but not a recognized image format',
                'user_error': f'Image {index}: Data received but it\'s not a valid image format'
            }

        return {
            'is_valid': True,
            'processed_data': base64_data,
            'format': image_format,
            'size_bytes': len(decoded_bytes),
            'error': None,
            'user_error': None
        }

    def _detect_format_from_bytes(self, data: bytes) -> Optional[str]:
        """Detect image format from binary data using magic bytes"""
        for signature, format_name in self.IMAGE_SIGNATURES.items():
            if data.startswith(signature):
                # Special case for WebP - needs additional validation
                if format_name == 'WEBP':
                    if len(data) >= 12 and data[8:12] == b'WEBP':
                        return 'WEBP'
                    else:
                        continue  # RIFF but not WebP
                return format_name
        return None

    def process_images_with_validation(self, images_raw: List[str]) -> Tuple[List[str], bool, List[str]]:
        """
        Process images with signature validation and error collection

        Returns:
            (processed_images, image_exists, user_error_messages)
        """
        if not images_raw or images_raw == ['noimage']:
            return ['noimage'], False, []

        processed_images = []
        image_exists = False
        user_errors = []

        for i, img_data in enumerate(images_raw):
            if img_data == "noimage":
                processed_images.append("noimage")
                continue

            # Validate using signatures
            validation_result = self.validate_image_data(img_data, i + 1)

            if validation_result['is_valid']:
                processed_images.append(validation_result['processed_data'])
                image_exists = True

                # Log successful validation
                format_name = validation_result['format']
                size_bytes = validation_result['size_bytes']
                print(f"🖼️ Image {i+1}: Valid {format_name} image ({size_bytes} bytes)")

            else:
                processed_images.append("noimage")
                user_errors.append(validation_result['user_error'])

                # Log error details
                print(f"🖼️ Image {i+1}: {validation_result['error']}")

        return processed_images, image_exists, user_errors

def test_integration():
    """Test the validator with various inputs"""
    validator = ImageSignatureValidator()

    test_cases = [
        # Valid PNG
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC",
        # Text as base64
        "SGVsbG8gV29ybGQ=",
        # Invalid data
        "not_base64!@#",
        # Data URI
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC",
        # File path (fake)
        "/path/to/image.png",
    ]

    print("🔍 Integration Test Results")
    print("=" * 40)

    processed, exists, errors = validator.process_images_with_validation(test_cases)

    print(f"Processed: {len(processed)} items")
    print(f"Valid images found: {exists}")

    if errors:
        print(f"User errors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")

if __name__ == "__main__":
    test_integration()