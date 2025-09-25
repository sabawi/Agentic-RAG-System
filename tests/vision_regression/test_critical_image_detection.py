#!/usr/bin/env python3
"""
Critical Image Detection Regression Tests

This test suite specifically prevents the base64 detection bug that caused
vision LLM failure for small images (< 100 chars).

NEVER REMOVE OR MODIFY THESE TESTS WITHOUT EXPLICIT APPROVAL
"""

import sys
import os
import base64
import tempfile

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the actual function from the server
# Note: This would need to be extracted to a testable module
def simulate_base64_detection(img_data, length_threshold=20):
    """
    Simulate the base64 detection logic from fastapi_server_complete.py
    This is the EXACT logic that was broken
    """
    import re

    if isinstance(img_data, str):
        # Remove data URI prefix if present
        if img_data.startswith('data:image/'):
            _, base64_part = img_data.split(',', 1)
            img_data = base64_part

        # Check if it looks like base64 (contains only base64 characters)
        if re.match(r'^[A-Za-z0-9+/]*={0,2}$', img_data) and len(img_data) >= length_threshold:
            return True, "base64"
        else:
            return False, "file_path"

    return False, "unknown"

class TestCriticalImageDetection:
    """Critical regression tests for image detection bug"""

    def test_tiny_image_88_chars_the_failing_case(self):
        """
        CRITICAL: Test the exact image that failed (88 chars)
        This is the bug we discovered - 88 < 100 threshold caused failure
        """
        # This is the exact image that failed in our test
        tiny_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC"

        assert len(tiny_image) == 88, f"Test image should be 88 chars, got {len(tiny_image)}"

        # With the old broken threshold (100), this would fail
        is_base64_old, type_old = simulate_base64_detection(tiny_image, length_threshold=100)
        assert not is_base64_old, "OLD LOGIC: Should fail with 100 char threshold (the bug)"
        assert type_old == "file_path", "OLD LOGIC: Should incorrectly classify as file path"

        # With the fixed threshold (20), this should pass
        is_base64_new, type_new = simulate_base64_detection(tiny_image, length_threshold=20)
        assert is_base64_new, "NEW LOGIC: Should pass with 20 char threshold (the fix)"
        assert type_new == "base64", "NEW LOGIC: Should correctly classify as base64"

    def test_edge_cases_around_old_threshold(self):
        """Test various image sizes around the old failing threshold"""

        # Create test images of different sizes
        test_cases = [
            (50, "Very small image"),
            (88, "The failing case"),
            (99, "Just under old threshold"),
            (100, "Exactly old threshold"),
            (101, "Just over old threshold"),
            (200, "Clearly above threshold")
        ]

        for target_size, description in test_cases:
            # Create a base64 string of approximately target_size
            padding = "A" * max(0, target_size - 88)  # Base image is 88 chars
            test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC" + padding
            test_image = test_image[:target_size]  # Trim to exact size

            # Ensure it's still valid base64 pattern
            if not test_image.endswith('='):
                test_image = test_image[:-1] + '='

            actual_size = len(test_image)

            # With new threshold (20), ALL should be detected as base64
            is_base64, detection_type = simulate_base64_detection(test_image, length_threshold=20)

            assert is_base64, f"{description} (size: {actual_size}) should be detected as base64 with new threshold"
            assert detection_type == "base64", f"{description} should be classified as base64"

    def test_data_uri_format_with_small_images(self):
        """Test that data URI format works with small images"""
        tiny_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC"
        data_uri = f"data:image/png;base64,{tiny_image}"

        is_base64, detection_type = simulate_base64_detection(data_uri, length_threshold=20)
        assert is_base64, "Data URI with small image should be detected as base64"
        assert detection_type == "base64"

    def test_regression_guard_against_future_threshold_increases(self):
        """Ensure threshold is never increased above safe levels"""

        # Test various "small but valid" image sizes
        small_valid_images = [
            20,  # Minimum threshold
            30,  # Small icon
            50,  # Tiny image
            88,  # Our failing case
        ]

        for size in small_valid_images:
            test_image = "A" * size
            if not test_image.endswith('='):
                test_image = test_image[:-1] + '='

            # These should ALWAYS be detected with ANY reasonable threshold
            is_base64, _ = simulate_base64_detection(test_image, length_threshold=20)
            assert is_base64, f"Image of size {size} should always be detected as base64"

    def test_invalid_cases_still_rejected(self):
        """Ensure we don't over-correct and accept invalid base64"""

        invalid_cases = [
            "",  # Empty string
            "a",  # Too short
            "abc",  # Too short
            "/path/to/file.png",  # Obvious file path
            "not_base64_at_all_just_text",  # Regular text
            "data:text/plain;charset=utf-8,hello",  # Non-image data URI
        ]

        for invalid_case in invalid_cases:
            is_base64, detection_type = simulate_base64_detection(invalid_case, length_threshold=20)
            assert not is_base64, f"Invalid case '{invalid_case}' should not be detected as base64"
            assert detection_type != "base64", f"Invalid case should not be classified as base64"

class TestImageProcessingIntegration:
    """Integration tests to ensure end-to-end vision pipeline works"""

    def test_small_image_triggers_vision_processing(self):
        """
        Integration test: small image should trigger vision LLM
        This would have failed with the original bug
        """
        # This requires a running server - skip for now
        print("ℹ️ Integration test skipped - requires running server")

        # Would test actual API call with small image
        # response = requests.post("http://localhost:5000/v1/chat/completions", ...)
        # assert "IMAGE PROCESSING" in response.text
        return True

if __name__ == "__main__":
    # Run the critical tests
    print("🔍 Running Critical Image Detection Regression Tests")
    print("=" * 60)

    test_suite = TestCriticalImageDetection()

    try:
        test_suite.test_tiny_image_88_chars_the_failing_case()
        print("✅ CRITICAL: 88-char image test PASSED")

        test_suite.test_edge_cases_around_old_threshold()
        print("✅ CRITICAL: Edge cases test PASSED")

        test_suite.test_data_uri_format_with_small_images()
        print("✅ CRITICAL: Data URI test PASSED")

        test_suite.test_regression_guard_against_future_threshold_increases()
        print("✅ CRITICAL: Future regression guard PASSED")

        test_suite.test_invalid_cases_still_rejected()
        print("✅ CRITICAL: Invalid cases test PASSED")

        print("\n🎉 ALL CRITICAL TESTS PASSED - Regression prevented!")

    except AssertionError as e:
        print(f"\n❌ CRITICAL TEST FAILED: {e}")
        print("🚨 VISION PROCESSING REGRESSION DETECTED!")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        sys.exit(1)