#!/usr/bin/env python3
"""
Debug script to test the two-stage tool calling in isolation
"""

import requests
import json
import asyncio
import sys
import os

# Add the current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_tool_calling():
    """Test the two-stage tool calling process"""
    
    print("🔧 Testing Two-Stage Tool Calling")
    print("=" * 50)
    
    # Get tools from the FastAPI server endpoint
    try:
        print("🔧 Getting tools array from FastAPI server...")
        health_response = requests.get("http://localhost:5000/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is responsive")
        else:
            print(f"❌ Server health check failed: {health_response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Cannot connect to FastAPI server: {e}")
        return None
    
    # Use the full tools array that the server should be using
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_the_secret_tool",
                "description": "Must call this function to get the current date and time from the system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "secret_tool": {
                            "type": "string",
                            "description": "Get the current Date and Time from the system as needed"
                        }
                    },
                    "required": ["secret_tool"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_news_summaries",
                "description": "Returns time-sensitive News! Tag all news items with Date, Time, and Source in response! This function takes a keyword string as input as a possible filter for news headlines and returns today's news headlines.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "The input filter is a string type that helps narrow down the choices of headlines. Examples: \"National\", \"Middle East\", \"World\", \"Technology\""
                        }
                    },
                    "required": ["filter"]
                }
            }
        }
    ]
    
    # Stage 1: Test tool calling model
    print("\n📡 STAGE 1: Testing Tool Calling Model")
    print("-" * 40)
    
    messages = [
        {
            "role": "system",
            "content": """BEFORE YOU MAKE FUNCTION CALLS, FOLLOW THIS GUIDELINE:
Tool Call Generation Guidelines -->:
DO NOT USE MORE THAN THREE (3) DIFFERENT FUNCTIONS.

1. Initial Context Retrieval:
- Always begin by calling get_the_secret_tool() to obtain the current date and time

4. News and Current Affairs:
- Use get_news_summaries() for:
    * Latest developments in major topics
    * Global/national events
    * Specific sectors (economy, politics, military)
"""
        },
        {
            "role": "user",
            "content": "Examine the intent of the user's prompt and apply the system directives to make the appropriate calls to the tools' functions. User Prompt: get news about middle east"
        }
    ]
    
    try:
        print(f"🔧 Calling llama3.2:3b with {len(tools)} tools...")
        
        response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": messages,
                "options": {"temperature": 0},
                "tools": tools,
                "stream": False,
                "think": False
            },
            timeout=15
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"✅ Success! Response keys: {list(response_data.keys())}")
            
            if 'message' in response_data:
                message = response_data['message']
                print(f"📋 Message keys: {list(message.keys())}")
                
                if 'content' in message:
                    print(f"📝 Content: {message['content']}")
                
                if 'tool_calls' in message:
                    tool_calls = message['tool_calls']
                    print(f"\n🎉 TOOL CALLS DETECTED! Found {len(tool_calls)} calls:")
                    
                    for i, tool_call in enumerate(tool_calls):
                        func_name = tool_call['function']['name']
                        func_args = tool_call['function']['arguments']
                        print(f"  {i+1}. {func_name}({func_args})")
                    
                    return tool_calls
                else:
                    print(f"❌ No tool_calls in message")
                    print(f"Raw message: {json.dumps(message, indent=2)}")
            else:
                print(f"❌ No message in response")
                print(f"Raw response: {json.dumps(response_data, indent=2)}")
        
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        print(f"Exception type: {type(e).__name__}")
        
    return None

def main():
    """Main test function"""
    print("🚀 Tool Calling Debug Test")
    print("Testing the two-stage algorithm in isolation...")
    
    # Test the tool calling
    result = asyncio.run(test_tool_calling())
    
    if result:
        print(f"\n✅ SUCCESS: Tool calling is working! Generated {len(result)} tool calls")
    else:
        print(f"\n❌ FAILED: Tool calling is not working properly")
    
    print("\n" + "=" * 50)
    print("Debug test complete!")

if __name__ == "__main__":
    main()