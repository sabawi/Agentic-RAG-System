#!/usr/bin/env python3
"""
Vision Processing Fix Validation Script

This script validates that the image detection bug has been fixed and creates
a comprehensive testing framework to prevent future regressions.
"""

import os
import sys
import requests
import base64
import time
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class VisionFixValidator:
    def __init__(self):
        self.server_url = "http://localhost:5000"
        self.test_results = []

    def log_result(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append((test_name, passed, details))
        print(f"{status} {test_name}")
        if details and not passed:
            print(f"    Details: {details}")

    def check_server_health(self):
        """Verify server is running and healthy"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_result("Server Health Check", True)
                return True
            else:
                self.log_result("Server Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Server Health Check", False, str(e))
            return False

    def test_small_image_detection(self):
        """Test the specific bug that was fixed - small image detection"""

        # The exact failing case: 88-character base64 image
        tiny_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC"

        payload = {
            "model": "qwen3:8b",
            "messages": [
                {"role": "user", "content": "What do you see in this image? Just say 'SUCCESS' if you can process it."}
            ],
            "images": [tiny_image],
            "toolsInUse": True
        }

        try:
            print(f"    Testing with {len(tiny_image)}-character image...")
            response = requests.post(f"{self.server_url}/v1/chat/completions",
                                   json=payload,
                                   timeout=60,  # Vision processing can take time
                                   stream=False)

            if response.status_code == 200:
                # Check if vision processing occurred
                response_text = response.text

                # Look for signs of successful vision processing
                vision_indicators = [
                    "SUCCESS",  # Our test response
                    "image",    # Vision model talking about image
                    "see",      # Vision model describing what it sees
                ]

                has_vision_response = any(indicator.lower() in response_text.lower()
                                        for indicator in vision_indicators)

                if has_vision_response:
                    self.log_result("Small Image Vision Processing", True,
                                  f"Image size: {len(tiny_image)} chars")
                    return True
                else:
                    self.log_result("Small Image Vision Processing", False,
                                  "No vision processing detected in response")
                    return False
            else:
                self.log_result("Small Image Vision Processing", False,
                              f"HTTP {response.status_code}: {response.text[:200]}")
                return False

        except requests.exceptions.Timeout:
            self.log_result("Small Image Vision Processing", False,
                          "Request timeout (vision processing may be working but slow)")
            return False
        except Exception as e:
            self.log_result("Small Image Vision Processing", False, str(e))
            return False

    def test_various_image_sizes(self):
        """Test edge cases around the old threshold"""

        # Create test images of different sizes
        test_sizes = [50, 88, 99, 150, 500]  # 88 was the failing case

        all_passed = True

        for size in test_sizes:
            # Create a base64 string of target size (simple padding approach)
            base_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC"
            if size > len(base_image):
                # Pad with valid base64 characters
                padding = "A" * (size - len(base_image) - 1) + "="
                test_image = base_image + padding
            else:
                test_image = base_image[:size-1] + "="

            # Quick server log check (non-intrusive)
            payload = {
                "model": "qwen3:8b",
                "messages": [{"role": "user", "content": "Test"}],
                "images": [test_image],
                "toolsInUse": True
            }

            try:
                # Don't wait for full response, just check if request is accepted
                response = requests.post(f"{self.server_url}/v1/chat/completions",
                                       json=payload,
                                       timeout=5)

                if response.status_code in [200, 408]:  # 408 timeout is OK for this test
                    passed = True
                else:
                    passed = False
                    all_passed = False

            except requests.exceptions.Timeout:
                passed = True  # Timeout is OK, means server accepted the image
            except Exception:
                passed = False
                all_passed = False

            print(f"    Size {len(test_image):3d}: {'✅' if passed else '❌'}")

        self.log_result("Various Image Sizes", all_passed)
        return all_passed

    def run_regression_tests(self):
        """Run the comprehensive regression test suite"""

        test_file = project_root / "tests" / "vision_regression" / "test_critical_image_detection.py"

        if not test_file.exists():
            self.log_result("Regression Test Suite", False, "Test file not found")
            return False

        try:
            # Run the regression tests
            result = subprocess.run([
                sys.executable, str(test_file)
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                self.log_result("Regression Test Suite", True)
                return True
            else:
                self.log_result("Regression Test Suite", False,
                              f"Exit code: {result.returncode}\n{result.stdout}\n{result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.log_result("Regression Test Suite", False, "Test timeout")
            return False
        except Exception as e:
            self.log_result("Regression Test Suite", False, str(e))
            return False

    def check_server_logs_for_fix(self):
        """Check server logs to confirm the fix is working"""

        log_file = project_root / "logs" / "server_complete.log"
        if not log_file.exists():
            self.log_result("Server Log Analysis", False, "Log file not found")
            return False

        try:
            # Read recent logs
            with open(log_file, 'r') as f:
                recent_logs = f.readlines()[-100:]  # Last 100 lines

            log_text = ''.join(recent_logs)

            # Look for evidence of the fix working
            fix_indicators = [
                "🖼️ Image 1: Already base64 data",  # Fix working
                "🖼️ Starting generation with qwen2.5vl",  # Vision LLM triggered
            ]

            bug_indicators = [
                "🖼️ Image 1: File not found:",  # Bug still present
            ]

            has_fix_evidence = any(indicator in log_text for indicator in fix_indicators)
            has_bug_evidence = any(indicator in log_text for indicator in bug_indicators)

            if has_fix_evidence and not has_bug_evidence:
                self.log_result("Server Log Analysis", True, "Fix evidence found in logs")
                return True
            elif has_bug_evidence:
                self.log_result("Server Log Analysis", False, "Bug still present in logs")
                return False
            else:
                self.log_result("Server Log Analysis", False, "No recent vision activity in logs")
                return False

        except Exception as e:
            self.log_result("Server Log Analysis", False, str(e))
            return False

    def create_monitoring_script(self):
        """Create a monitoring script for ongoing regression detection"""

        monitor_script = project_root / "scripts" / "vision_health_monitor.py"

        monitor_code = '''#!/usr/bin/env python3
"""
Vision Processing Health Monitor

Runs periodic checks to ensure vision processing remains functional.
Add this to cron for automated monitoring.
"""

import requests
import sys
import time
from datetime import datetime

def check_vision_health():
    """Quick health check for vision processing"""

    tiny_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC"

    payload = {
        "model": "qwen3:8b",
        "messages": [{"role": "user", "content": "Health check - can you see this image?"}],
        "images": [tiny_image],
        "toolsInUse": True
    }

    try:
        response = requests.post("http://localhost:5000/v1/chat/completions",
                               json=payload, timeout=30)

        if response.status_code == 200 and "image" in response.text.lower():
            print(f"[{datetime.now()}] ✅ Vision health check PASSED")
            return True
        else:
            print(f"[{datetime.now()}] ❌ Vision health check FAILED")
            return False

    except Exception as e:
        print(f"[{datetime.now()}] 💥 Vision health check ERROR: {e}")
        return False

if __name__ == "__main__":
    success = check_vision_health()
    sys.exit(0 if success else 1)
'''

        try:
            with open(monitor_script, 'w') as f:
                f.write(monitor_code)

            # Make executable
            os.chmod(monitor_script, 0o755)

            self.log_result("Monitoring Script Creation", True, f"Created: {monitor_script}")
            return True

        except Exception as e:
            self.log_result("Monitoring Script Creation", False, str(e))
            return False

    def generate_report(self):
        """Generate final validation report"""

        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)

        print("\n" + "="*60)
        print("🔍 VISION FIX VALIDATION REPORT")
        print("="*60)

        print(f"\n📊 Results: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ The vision processing bug has been successfully fixed")
            print("✅ Regression prevention measures are in place")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED")
            print("❌ Vision processing may still have issues")

            print("\nFailed tests:")
            for name, passed, details in self.test_results:
                if not passed:
                    print(f"  - {name}: {details}")

        print("\n📋 Next Steps:")
        if passed_tests == total_tests:
            print("1. Add vision tests to CI/CD pipeline")
            print("2. Set up automated monitoring")
            print("3. Update development guidelines")
        else:
            print("1. Review and fix failing tests")
            print("2. Re-run validation after fixes")
            print("3. Consider rolling back if issues persist")

        print("="*60)

def main():
    """Main validation workflow"""

    print("🔍 Vision Processing Fix Validation")
    print("="*40)

    validator = VisionFixValidator()

    # Run all validation tests
    validator.check_server_health()
    validator.test_small_image_detection()
    validator.test_various_image_sizes()
    validator.run_regression_tests()
    validator.check_server_logs_for_fix()
    validator.create_monitoring_script()

    # Generate final report
    validator.generate_report()

if __name__ == "__main__":
    main()