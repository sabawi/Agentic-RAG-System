#!/usr/bin/env python3
"""
Debug the threshold edge cases
"""

import re

def test_base64_detection(img_data, length_threshold=20):
    """Test the exact logic from the server"""
    if isinstance(img_data, str):
        # Remove data URI prefix if present
        if img_data.startswith('data:image/'):
            _, base64_part = img_data.split(',', 1)
            img_data = base64_part

        # Check if it looks like base64 (contains only base64 characters)
        if re.match(r'^[A-Za-z0-9+/]*={0,2}$', img_data) and len(img_data) > length_threshold:
            return True, "base64"
        else:
            return False, "file_path"

    return False, "unknown"

# Test different sizes
test_cases = [
    (20, "A" * 20),
    (21, "A" * 21),
    (25, "A" * 25),
    (88, "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC")
]

print("Testing threshold logic:")
for size, test_string in test_cases:
    is_base64, type_detected = test_base64_detection(test_string, 20)
    print(f"Size {size:2d}: {len(test_string):2d} chars -> {is_base64} ({type_detected})")

print(f"\nIssue: threshold is > 20, so exactly 20 chars fails")
print(f"Solution: Use >= 20 or reduce threshold to 19")