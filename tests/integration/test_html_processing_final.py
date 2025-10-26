#!/usr/bin/env python3

import requests
import json
import sys

def test_html_creation():
    url = "http://localhost:5000/llama3_1b/stream"
    
    payload = {
        "prompt": "Create html_success_final.html with content SUCCESS and email it to test@example.com",
        "model": "deepseek-v3.1:671b-cloud", 
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🚀 Testing HTML file creation and email sending...")
    print(f"📤 Request: {payload}")
    print("⏳ Waiting for response (no timeout)...")
    
    try:
        # No timeout to let the Primary LLM complete and post-processing execute
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=None)
        
        print(f"📨 Response Status: {response.status_code}")
        print(f"📄 Response Length: {len(response.text)} characters")
        
        # Print last few lines of response to see completion
        lines = response.text.strip().split('\n')
        print(f"📋 Last 5 response lines:")
        for line in lines[-5:]:
            print(f"  {line}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_html_creation()
    sys.exit(0 if success else 1)