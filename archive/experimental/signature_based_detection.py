#!/usr/bin/env python3
"""
Signature-based Image Detection - The Right Way

Uses actual image file signatures (magic bytes) to detect valid images.
No more arbitrary length thresholds or guessing!
"""

import base64
import os
from typing import Tuple, Optional, Dict, Any

class ImageSignatureDetector:
    """Production-ready image detection using file signatures"""

    # Image format signatures (magic bytes) - THE definitive way
    IMAGE_SIGNATURES = {
        # PNG: 89 50 4E 47 0D 0A 1A 0A
        b'\x89PNG\r\n\x1a\n': 'PNG',

        # JPEG: FF D8 FF
        b'\xff\xd8\xff': 'JPEG',

        # GIF87a: 47 49 46 38 37 61
        b'GIF87a': 'GIF',

        # GIF89a: 47 49 46 38 39 61
        b'GIF89a': 'GIF',

        # WebP: 52 49 46 46 [4 bytes size] 57 45 42 50
        b'RIFF': 'WEBP',  # Need additional validation

        # BMP: 42 4D
        b'BM': 'BMP',

        # ICO: 00 00 01 00
        b'\x00\x00\x01\x00': 'ICO',

        # TIFF (Intel): 49 49 2A 00
        b'II*\x00': 'TIFF',

        # TIFF (Motorola): 4D 4D 00 2A
        b'MM\x00*': 'TIFF',
    }

    def detect_image_from_data(self, data: str) -> Tuple[bool, str, Optional[str]]:
        """
        Detect if data contains a valid image using ONLY file signatures

        Args:
            data: Input string (base64, data URI, or file path)

        Returns:
            (is_image, format_or_error, details)
        """

        if not data or not isinstance(data, str):
            return False, "invalid_input", "Empty or non-string input"

        # Handle data URI format
        original_data = data
        if data.startswith('data:image/'):
            try:
                if ';base64,' not in data:
                    return False, "malformed_data_uri", "Data URI missing base64 specification"

                _, base64_part = data.split(';base64,', 1)
                data = base64_part
            except ValueError:
                return False, "malformed_data_uri", "Invalid data URI format"

        # Check if it looks like a file path
        if self._is_file_path(data):
            return self._validate_image_file(data)

        # Must be base64 data - validate using signatures
        return self._validate_base64_image(data)

    def _is_file_path(self, data: str) -> bool:
        """Check if data appears to be a file path"""
        # File paths contain slashes or have image extensions
        path_indicators = ['/', '\\']
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.ico']

        has_path_chars = any(indicator in data for indicator in path_indicators)
        has_image_ext = any(data.lower().endswith(ext) for ext in image_extensions)

        # If it has obvious path characteristics AND doesn't look like pure base64
        return (has_path_chars or has_image_ext) and not self._looks_like_base64(data)

    def _looks_like_base64(self, data: str) -> bool:
        """Quick check if string looks like base64"""
        if len(data) < 4:
            return False

        # Base64 uses only these characters
        import re
        return bool(re.match(r'^[A-Za-z0-9+/]*={0,2}$', data))

    def _validate_image_file(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate image file using file signatures"""
        expanded_path = os.path.expanduser(file_path.strip())

        if not os.path.exists(expanded_path):
            return False, "file_not_found", f"File not found: {expanded_path}"

        if not os.path.isfile(expanded_path):
            return False, "not_a_file", f"Path is not a file: {expanded_path}"

        try:
            with open(expanded_path, 'rb') as f:
                header = f.read(16)  # Read first 16 bytes

            image_format = self._detect_format_from_bytes(header)
            if image_format:
                file_size = os.path.getsize(expanded_path)
                return True, image_format, f"Valid {image_format} file ({file_size} bytes)"
            else:
                return False, "not_image_file", "File exists but is not a recognized image format"

        except PermissionError:
            return False, "permission_denied", "Cannot read file - permission denied"
        except Exception as e:
            return False, "file_read_error", f"Error reading file: {str(e)}"

    def _validate_base64_image(self, base64_data: str) -> Tuple[bool, str, Optional[str]]:
        """Validate base64 data contains image using signatures"""

        # Quick validation - must look like base64
        if not self._looks_like_base64(base64_data):
            return False, "invalid_base64_chars", "Contains invalid base64 characters"

        # Decode the base64 data
        try:
            decoded_bytes = base64.b64decode(base64_data, validate=True)
        except Exception as e:
            return False, "base64_decode_error", f"Base64 decode failed: {str(e)}"

        # Check minimum size - images need at least some bytes
        if len(decoded_bytes) < 8:
            return False, "data_too_small", f"Only {len(decoded_bytes)} bytes - too small for image"

        # THE CRITICAL PART: Check image signatures
        image_format = self._detect_format_from_bytes(decoded_bytes)
        if image_format:
            return True, image_format, f"Valid {image_format} image ({len(decoded_bytes)} bytes)"
        else:
            return False, "not_image_data", "Valid base64 but not a recognized image format"

    def _detect_format_from_bytes(self, data: bytes) -> Optional[str]:
        """Detect image format from binary data using magic bytes"""

        for signature, format_name in self.IMAGE_SIGNATURES.items():
            if data.startswith(signature):
                # Special case for WebP - needs additional validation
                if format_name == 'WEBP':
                    # WebP format: RIFF[size]WEBP
                    if len(data) >= 12 and data[8:12] == b'WEBP':
                        return 'WEBP'
                    else:
                        continue  # RIFF but not WebP
                return format_name

        return None

def demonstrate_signature_detection():
    """Show how signature detection works vs the old broken method"""

    detector = ImageSignatureDetector()

    print("🖼️  Image Signature Detection - The Right Way")
    print("=" * 60)

    test_cases = [
        # Real PNG (starts with PNG signature)
        ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC", "Real PNG image"),

        # Text encoded as base64 (no image signature)
        ("SGVsbG8gV29ybGQh", "Text 'Hello World!' as base64"),

        # Data URI
        ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC", "PNG Data URI"),

        # File path
        ("/path/to/image.png", "File path"),

        # Invalid base64
        ("not_base64!@#", "Invalid data"),

        # Valid base64 but random data
        ("dGhpcyBpcyBub3QgYW4gaW1hZ2U=", "Random data as base64"),

        # Empty
        ("", "Empty input"),

        # Very short base64 (the old problem with length thresholds)
        ("iVBOR", "Short base64 fragment"),
    ]

    for test_input, description in test_cases:
        print(f"\n📝 Test: {description}")
        print(f"Input: {test_input[:40]}{'...' if len(test_input) > 40 else ''}")

        is_image, format_or_error, details = detector.detect_image_from_data(test_input)

        if is_image:
            print(f"✅ Result: VALID {format_or_error} IMAGE")
            print(f"   Details: {details}")
        else:
            print(f"❌ Result: NOT IMAGE ({format_or_error})")
            print(f"   Reason: {details}")

def compare_old_vs_new_detection():
    """Compare the old broken method with signature detection"""

    print("\n" + "=" * 60)
    print("📊 OLD vs NEW Detection Method Comparison")
    print("=" * 60)

    # The old broken detection
    def old_broken_detection(data: str) -> bool:
        import re
        if data.startswith('data:image/'):
            _, base64_part = data.split(',', 1)
            data = base64_part
        return bool(re.match(r'^[A-Za-z0-9+/]*={0,2}$', data) and len(data) >= 20)

    detector = ImageSignatureDetector()

    test_cases = [
        ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC", "PNG image", True),
        ("SGVsbG8gV29ybGQh", "Text as base64", False),
        ("dGhpcyBpcyBub3QgYW4gaW1hZ2U=", "Random data", False),
        ("iVBOR", "Short fragment", False),
        ("", "Empty", False),
    ]

    print(f"{'Test Case':<20} {'Old Method':<12} {'New Method':<12} {'Correct?'}")
    print("-" * 60)

    for test_input, description, should_be_image in test_cases:
        old_result = old_broken_detection(test_input)
        new_result, _, _ = detector.detect_image_from_data(test_input)

        old_correct = (old_result == should_be_image)
        new_correct = (new_result == should_be_image)

        old_symbol = "✅" if old_correct else "❌"
        new_symbol = "✅" if new_correct else "❌"

        print(f"{description:<20} {str(old_result):<12} {str(new_result):<12} Old:{old_symbol} New:{new_symbol}")

if __name__ == "__main__":
    demonstrate_signature_detection()
    compare_old_vs_new_detection()

    print(f"\n💡 Key Insight:")
    print(f"   Image detection should use SIGNATURES, not arbitrary length limits!")
    print(f"   Every image format has unique magic bytes at the start.")
    print(f"   This is how file systems and browsers actually detect image types.")