#!/usr/bin/env python3
"""
Test script for Logging Control API endpoints
Demonstrates all available logging control functionality via API calls
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, description, data=None):
    """Test an API endpoint with proper error handling"""
    print(f"\n🧪 Testing: {description}")
    print(f"   {method} {endpoint}")

    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        elif method == "POST":
            if data:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", timeout=10)

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success: {json.dumps(result, indent=2)}")
        else:
            print(f"   ❌ Error: {response.text}")

    except requests.exceptions.ConnectRefused:
        print(f"   ❌ Connection refused - Server not running on {BASE_URL}")
    except requests.exceptions.Timeout:
        print(f"   ⏰ Request timeout")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Test all logging control endpoints"""
    print("🚀 Logging Control API Test Suite")
    print("=" * 50)

    # Test 1: Get current logging status
    test_endpoint("GET", "/admin/logging/status", "Get current logging status")

    # Test 2: Enable logging
    test_endpoint("POST", "/admin/logging/enable", "Enable logging")

    # Test 3: Check status after enable
    test_endpoint("GET", "/admin/logging/status", "Check status after enabling")

    # Test 4: Set logging level to DEBUG
    test_endpoint("POST", "/admin/logging/level/DEBUG", "Set logging level to DEBUG")

    # Test 5: Set logging level to WARNING
    test_endpoint("POST", "/admin/logging/level/WARNING", "Set logging level to WARNING")

    # Test 6: Toggle request logging
    test_endpoint("POST", "/admin/logging/requests/toggle", "Toggle request logging")

    # Test 7: Toggle timing logging
    test_endpoint("POST", "/admin/logging/timing/toggle", "Toggle timing logging")

    # Test 8: Check status after toggles
    test_endpoint("GET", "/admin/logging/status", "Check status after toggles")

    # Test 9: Disable logging
    test_endpoint("POST", "/admin/logging/disable", "Disable all logging")

    # Test 10: Final status check
    test_endpoint("GET", "/admin/logging/status", "Final status check")

    # Test 11: Test invalid log level
    test_endpoint("POST", "/admin/logging/level/INVALID", "Test invalid log level (should fail)")

    # Test 12: Check help endpoint for admin section
    test_endpoint("GET", "/help", "Check help endpoint for admin documentation")

    print("\n" + "=" * 50)
    print("🏁 Logging Control API Test Complete")
    print("\n📚 Available Endpoints:")
    print("   GET  /admin/logging/status              - Get current logging status")
    print("   POST /admin/logging/enable              - Enable logging with INFO level")
    print("   POST /admin/logging/disable             - Disable all logging")
    print("   POST /admin/logging/level/{level}       - Set specific log level")
    print("   POST /admin/logging/requests/toggle     - Toggle request logging")
    print("   POST /admin/logging/timing/toggle       - Toggle timing logging")
    print("\n🔧 Usage Examples:")
    print("   curl -X GET http://localhost:5000/admin/logging/status")
    print("   curl -X POST http://localhost:5000/admin/logging/enable")
    print("   curl -X POST http://localhost:5000/admin/logging/level/DEBUG")
    print("   curl -X POST http://localhost:5000/admin/logging/disable")

if __name__ == "__main__":
    main()