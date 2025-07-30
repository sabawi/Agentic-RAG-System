#!/usr/bin/env python3
"""
Test the /retrieve_system_prompts endpoint to verify it matches the original behavior
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_retrieve_system_prompts():
    """Test the retrieve_system_prompts endpoint like the original"""
    print("🧪 Testing /retrieve_system_prompts Endpoint")
    print("=" * 50)
    
    # Test cases based on original Flask implementation
    test_cases = [
        {
            "name": "Valid request",
            "payload": {"system_prompts_filename": "system_prompts.json"},
            "expected_status": 200,
            "description": "Should return file content as JSON"
        },
        {
            "name": "Missing parameter",
            "payload": {},
            "expected_status": 400,
            "description": "Should return error for missing system_prompts_filename"
        },
        {
            "name": "Empty filename",
            "payload": {"system_prompts_filename": ""},
            "expected_status": 400,
            "description": "Should return error for empty filename"
        },
        {
            "name": "Non-existent file",
            "payload": {"system_prompts_filename": "nonexistent.json"},
            "expected_status": 404,
            "description": "Should return file not found error"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}️⃣ Testing: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   Payload: {test_case['payload']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/retrieve_system_prompts",
                json=test_case['payload'],
                timeout=10
            )
            
            print(f"   Status: {response.status_code} (expected: {test_case['expected_status']})")
            
            # Check status code
            if response.status_code == test_case['expected_status']:
                print("   ✅ Status code matches")
            else:
                print("   ❌ Status code mismatch")
                continue
            
            # Parse response
            try:
                response_data = response.json()
                print(f"   Response type: {type(response_data)}")
                
                if response.status_code == 200:
                    # For successful responses, check if it's direct content
                    if isinstance(response_data, (str, dict, list)):
                        print("   ✅ Response format matches original (direct JSON content)")
                        
                        # If it's a string, show preview
                        if isinstance(response_data, str):
                            preview = response_data[:100].replace('\n', ' ')
                            print(f"   📝 Content preview: {preview}...")
                        else:
                            print(f"   📝 Content type: {type(response_data)}")
                    else:
                        print("   ⚠️ Unexpected response format")
                        
                else:
                    # For error responses, check if it has 'message' field like original
                    if isinstance(response_data, dict) and 'message' in response_data:
                        print(f"   ✅ Error format matches original")
                        print(f"   📝 Error message: {response_data['message']}")
                    else:
                        print("   ⚠️ Error format doesn't match original")
                        print(f"   📝 Response: {response_data}")
                        
            except json.JSONDecodeError:
                print("   ❌ Response is not valid JSON")
                print(f"   📝 Raw response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        print()
    
    print("=" * 50)
    print("📊 Test Summary:")
    print("✅ If all tests passed, the endpoint matches the original Flask behavior")
    print("💡 The endpoint should:")
    print("   - Accept JSON with 'system_prompts_filename' parameter")
    print("   - Return direct file content as JSON (not wrapped in ApiResponse)")
    print("   - Return proper error messages in {'message': '...'} format")
    print("   - Use the same status codes as the original")

if __name__ == "__main__":
    test_retrieve_system_prompts()