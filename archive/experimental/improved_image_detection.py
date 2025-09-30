#!/usr/bin/env python3
"""
Improved Image Detection Logic for Production Use

This replaces the flawed length-based detection with proper validation.
"""

import base64
import re
import os
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

class ImageDetectionResult:
    """Structured result for image detection"""
    def __init__(self, is_image: bool, detection_type: str,
                 error_message: Optional[str] = None,
                 image_format: Optional[str] = None,
                 size_bytes: Optional[int] = None):
        self.is_image = is_image
        self.detection_type = detection_type
        self.error_message = error_message
        self.image_format = image_format
        self.size_bytes = size_bytes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_image": self.is_image,
            "type": self.detection_type,
            "error": self.error_message,
            "format": self.image_format,
            "size_bytes": self.size_bytes
        }

class RobustImageDetector:
    """Production-ready image detection with proper error handling"""

    # Image format signatures (magic bytes)
    IMAGE_SIGNATURES = {
        b'\x89PNG\r\n\x1a\n': 'PNG',
        b'\xff\xd8\xff': 'JPEG',
        b'GIF87a': 'GIF87a',
        b'GIF89a': 'GIF89a',
        b'RIFF': 'WEBP',  # WebP starts with RIFF, followed by size, then WEBP
        b'BM': 'BMP',
        b'\x00\x00\x01\x00': 'ICO',  # Windows Icon
        b'FORM': 'IFF',  # Some image formats use IFF
    }

    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico'}

    def detect_image(self, data: str) -> ImageDetectionResult:
        """
        Robustly detect if data represents a valid image

        Args:
            data: Input data (could be base64, data URI, or file path)

        Returns:
            ImageDetectionResult with detailed analysis
        """

        if not data or not isinstance(data, str):
            return ImageDetectionResult(
                False, "invalid_input",
                "Input is empty or not a string"
            )

        # Step 1: Handle data URI format
        original_data = data
        if data.startswith('data:'):
            try:
                # Parse data URI: data:image/png;base64,iVBORw0K...
                if not data.startswith('data:image/'):
                    return ImageDetectionResult(
                        False, "non_image_data_uri",
                        "Data URI is not for an image type"
                    )

                # Extract base64 part
                if ';base64,' not in data:
                    return ImageDetectionResult(
                        False, "malformed_data_uri",
                        "Data URI missing base64 encoding specification"
                    )

                _, base64_part = data.split(';base64,', 1)
                data = base64_part

            except ValueError:
                return ImageDetectionResult(
                    False, "malformed_data_uri",
                    "Invalid data URI format"
                )

        # Step 2: Check if it looks like a file path
        if self._looks_like_file_path(data):
            return self._handle_file_path(data)

        # Step 3: Validate as base64 image data
        return self._validate_base64_image(data)

    def _looks_like_file_path(self, data: str) -> bool:
        """Check if data looks like a file path"""
        # Contains path separators or file extensions
        path_indicators = ['/', '\\', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

        # If it contains path separators or extensions AND doesn't look like base64
        has_path_chars = any(indicator in data.lower() for indicator in path_indicators)
        looks_like_base64 = re.match(r'^[A-Za-z0-9+/]*={0,2}$', data)

        return has_path_chars and not looks_like_base64

    def _handle_file_path(self, file_path: str) -> ImageDetectionResult:
        """Handle file path inputs"""
        expanded_path = os.path.expanduser(file_path.strip())
        path_obj = Path(expanded_path)

        # Check if file exists
        if not path_obj.exists():
            return ImageDetectionResult(
                False, "file_not_found",
                f"Image file not found: {expanded_path}"
            )

        # Check if it's actually a file
        if not path_obj.is_file():
            return ImageDetectionResult(
                False, "not_a_file",
                f"Path exists but is not a file: {expanded_path}"
            )

        # Check file extension
        if path_obj.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return ImageDetectionResult(
                False, "unsupported_format",
                f"Unsupported image format: {path_obj.suffix}"
            )

        # Validate by reading file header
        try:
            with open(expanded_path, 'rb') as f:
                header = f.read(16)  # Read first 16 bytes for magic number

            image_format = self._detect_image_format(header)
            if image_format:
                file_size = path_obj.stat().st_size
                return ImageDetectionResult(
                    True, "valid_file_path", None, image_format, file_size
                )
            else:
                return ImageDetectionResult(
                    False, "invalid_image_file",
                    f"File exists but is not a valid image format"
                )

        except PermissionError:
            return ImageDetectionResult(
                False, "permission_denied",
                f"Cannot read image file: Permission denied"
            )
        except Exception as e:
            return ImageDetectionResult(
                False, "file_read_error",
                f"Error reading image file: {str(e)}"
            )

    def _validate_base64_image(self, data: str) -> ImageDetectionResult:
        """Validate base64 data as image"""

        # Check base64 pattern
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', data):
            return ImageDetectionResult(
                False, "invalid_base64_format",
                "Contains characters not valid in base64 encoding"
            )

        # Actually decode the base64
        try:
            decoded_data = base64.b64decode(data, validate=True)
        except Exception as e:
            return ImageDetectionResult(
                False, "base64_decode_error",
                f"Failed to decode base64 data: {str(e)}"
            )

        # Check if decoded data is too small to be an image
        if len(decoded_data) < 10:
            return ImageDetectionResult(
                False, "data_too_small",
                f"Decoded data is only {len(decoded_data)} bytes - too small for an image"
            )

        # Detect image format from magic bytes
        image_format = self._detect_image_format(decoded_data)
        if image_format:
            return ImageDetectionResult(
                True, "valid_base64_image", None, image_format, len(decoded_data)
            )
        else:
            return ImageDetectionResult(
                False, "valid_base64_not_image",
                "Valid base64 data but not a recognized image format"
            )

    def _detect_image_format(self, data: bytes) -> Optional[str]:
        """Detect image format from binary data"""
        for signature, format_name in self.IMAGE_SIGNATURES.items():
            if data.startswith(signature):
                # Special case for WebP - need additional validation
                if format_name == 'WEBP':
                    if len(data) >= 12 and data[8:12] == b'WEBP':
                        return 'WEBP'
                    else:
                        continue
                return format_name
        return None

    def generate_user_error_message(self, result: ImageDetectionResult,
                                    user_friendly: bool = True) -> str:
        """Generate user-friendly error messages"""

        if result.is_image:
            return f"✅ Valid {result.image_format} image detected"

        error_messages = {
            "file_not_found": "❌ Image file not found. Please check the file path and try again.",
            "permission_denied": "❌ Cannot access the image file. Please check file permissions.",
            "unsupported_format": "❌ Unsupported image format. Please use PNG, JPEG, GIF, BMP, or WebP.",
            "invalid_base64_format": "❌ Invalid image data format. Please ensure the image is properly encoded.",
            "base64_decode_error": "❌ Corrupted image data. Please re-upload your image.",
            "data_too_small": "❌ Image data appears incomplete or corrupted. Please re-upload.",
            "valid_base64_not_image": "❌ Data received but it's not a valid image format.",
            "malformed_data_uri": "❌ Image data is malformed. Please try uploading the image again.",
            "non_image_data_uri": "❌ The uploaded data is not an image. Please select an image file.",
        }

        base_message = error_messages.get(result.detection_type,
                                        f"❌ Image processing failed: {result.error_message}")

        if user_friendly:
            # Add helpful suggestions
            suggestions = {
                "file_not_found": "\n💡 Make sure the file path is correct and the file exists.",
                "unsupported_format": "\n💡 Try converting your image to PNG or JPEG format.",
                "base64_decode_error": "\n💡 The image may be corrupted. Try re-saving and re-uploading.",
                "data_too_small": "\n💡 The image file may be empty or corrupted.",
            }

            suggestion = suggestions.get(result.detection_type, "")
            return base_message + suggestion

        return base_message

def demo_improved_detection():
    """Demonstrate the improved detection system"""

    detector = RobustImageDetector()

    test_cases = [
        # Valid PNG image (our test case)
        ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC", "Valid PNG"),

        # Data URI
        ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC", "Data URI"),

        # Valid base64 but not image
        ("SGVsbG8gV29ybGQ=", "Text as base64"),

        # File path (fake)
        ("/path/to/nonexistent/image.png", "File path"),

        # Invalid base64
        ("invalid!@#$%", "Invalid data"),

        # Empty
        ("", "Empty input"),

        # Too short
        ("abc", "Too short"),
    ]

    print("🔍 Improved Image Detection Results")
    print("=" * 60)

    for test_input, description in test_cases:
        print(f"\n📝 Test: {description}")
        print(f"Input: {test_input[:40]}{'...' if len(test_input) > 40 else ''}")

        result = detector.detect_image(test_input)

        status = "✅ VALID IMAGE" if result.is_image else "❌ NOT IMAGE"
        print(f"Result: {status}")
        print(f"Type: {result.detection_type}")

        if result.image_format:
            print(f"Format: {result.image_format}")
        if result.size_bytes:
            print(f"Size: {result.size_bytes} bytes")
        if result.error_message:
            print(f"Error: {result.error_message}")

        # Show user-friendly message
        user_msg = detector.generate_user_error_message(result)
        print(f"User Message: {user_msg}")

if __name__ == "__main__":
    demo_improved_detection()