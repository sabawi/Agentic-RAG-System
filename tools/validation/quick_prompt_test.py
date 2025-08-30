#!/usr/bin/env python3
import requests
import json

def test_single_prompt():
    payload = {
        "model": "llama3.2:3b",
        "prompt": "Hi! Can you please send an email to john@example.com with the subject 'Meeting Tomorrow' and tell him we need to reschedule our 3pm meeting to 4pm? Thanks!",
        "stream": False
    }
    
    try:
        response = requests.post("http://localhost:5000/llama3_1b/prompt", 
                               json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ FAILED - {response.text}")
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")

if __name__ == "__main__":
    test_single_prompt()