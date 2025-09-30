#!/usr/bin/env python3
"""
Debug script to test base64 detection logic.
"""

import re

def test_base64_detection():
    """Test the base64 detection regex that's failing"""

    # The test image from our test script
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC"

    print(f"Testing base64 string: {test_image}")
    print(f"Length: {len(test_image)}")

    # The current regex from the code
    current_pattern = r'^[A-Za-z0-9+/]*={0,2}$'

    print(f"\nUsing regex pattern: {current_pattern}")

    match = re.match(current_pattern, test_image)

    if match:
        print("✅ Current regex MATCHES")
        if len(test_image) > 100:
            print("✅ Length check PASSES (> 100)")
            print("🎯 Should be detected as base64")
        else:
            print("❌ Length check FAILS (<= 100)")
            print("🎯 Will be treated as file path")
    else:
        print("❌ Current regex FAILS")
        print("🎯 Will be treated as file path")

    # Test each character to find non-matching ones
    allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
    problem_chars = []

    for i, char in enumerate(test_image):
        if char not in allowed_chars:
            problem_chars.append((i, char))

    if problem_chars:
        print(f"\n❌ Found non-base64 characters:")
        for pos, char in problem_chars:
            print(f"   Position {pos}: '{char}' (ord: {ord(char)})")
    else:
        print(f"\n✅ All characters are valid base64")

    # Try a more permissive pattern
    print(f"\n🔧 Testing with more permissive pattern...")
    permissive_pattern = r'^[A-Za-z0-9+/]+={0,2}$'  # Require at least one char

    match2 = re.match(permissive_pattern, test_image)
    if match2:
        print("✅ Permissive regex MATCHES")
    else:
        print("❌ Permissive regex FAILS")

if __name__ == "__main__":
    test_base64_detection()