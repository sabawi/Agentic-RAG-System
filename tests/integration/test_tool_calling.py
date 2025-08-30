#!/usr/bin/env python3
import requests
import json

def test_tool_calling():
    # Test with explicit tool calling instruction
    payload = {
        "model": "llama3.2:3b",
        "prompt": """You have access to tools. When a user asks you to send an email, you should use the email tool.

Available tools:
- secure_email_sender: Sends emails with attachments

User request: Send an email to john@example.com with subject 'Meeting Tomorrow' telling him we need to reschedule from 3pm to 4pm.

Use the secure_email_sender tool to complete this request.""",
        "stream": False
    }
    
    try:
        response = requests.post("http://localhost:5000/llama3_1b/prompt", 
                               json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS")
            print("Response:", result['data']['response'])
        else:
            print(f"❌ FAILED - {response.text}")
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")

if __name__ == "__main__":
    test_tool_calling()