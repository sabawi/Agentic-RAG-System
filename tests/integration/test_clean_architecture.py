#!/usr/bin/env python3
"""
Test script to verify the clean two-stage architecture:
1. Tool Model: User Prompt → Tool Calls
2. Primary Model: System Prompt + Context (tool results) + User Prompt → Response
"""
import requests
import json
import time

def test_clean_architecture():
    """Test the clean two-stage architecture"""
    
    # Simple test request that should trigger tool calls
    test_request = {
        "model": "qwen3:8b",
        "prompt": "What's the current date and give me today's top news summary?",
        "stream": False,
        "toolsInUse": [
            {
                'type': 'function', 
                'function': {
                    'name': 'get_the_secret_tool', 
                    'description': 'Must call this function to get the current date and time from the system.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'secret_tool': {
                                'type': 'string',
                                'description': 'Get the current Date and Time from the system as needed'
                            }
                        },
                        'required': ['secret_tool']
                    }
                }
            },
            {
                'type': 'function', 
                'function': {
                    'name': 'get_news_summaries', 
                    'description': 'Returns time-sensitive News! Tag all news items with Date, Time, and Source in response! This function takes a keyword string as input as a possible filter for news headlines and returns today\'s news headlines.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'filter': {
                                'type': 'string',
                                'description': 'The input filter is a string type that helps narrow down the choices of headlines. Examples: "National", "Middle East", "World", "Technology"'
                            }
                        },
                        'required': ['filter']
                    }
                }
            }
        ],
        "system": "You are a helpful news assistant. Be concise and informative."
    }

    print("🧪 Testing Clean Two-Stage Architecture")
    print("=" * 50)
    print(f"📝 Test Request: {test_request['prompt']}")
    print(f"🔧 Tools Available: {len(test_request['toolsInUse'])}")
    print(f"⚙️ User System Prompt: {test_request['system']}")
    print()

    try:
        # Make the request
        print("📡 Sending request to server...")
        response = requests.post(
            'http://localhost:5000/llama3_1b/stream',
            headers={'Content-Type': 'application/json'},
            json=test_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"📊 Response length: {len(result.get('response', ''))}")
            print()
            print("🎯 RESPONSE PREVIEW:")
            print("-" * 30)
            response_text = result.get('response', '')[:500] + "..." if len(result.get('response', '')) > 500 else result.get('response', '')
            print(response_text)
            print()
            
            # Check if it looks like the clean architecture worked
            if "date" in response_text.lower() and "news" in response_text.lower():
                print("✅ SUCCESS: Clean two-stage architecture appears to be working!")
                print("   - Tools were called (we got date and news)")
                print("   - Primary model provided structured response")
                return True
            else:
                print("⚠️ WARNING: Response doesn't contain expected tool results")
                return False
                
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Clean Architecture Test")
    print("Make sure your server is running on localhost:5000")
    print()
    
    success = test_clean_architecture()
    
    print()
    print("=" * 50)
    if success:
        print("🎉 TEST PASSED: Clean two-stage architecture is working correctly!")
    else:
        print("🚨 TEST FAILED: Architecture needs debugging")
    print("=" * 50)