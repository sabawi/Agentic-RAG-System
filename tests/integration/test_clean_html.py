#!/usr/bin/env python3

import requests
import json
import sys

def test_clean_html():
    url = "http://localhost:5000/llama3_1b/stream"
    
    payload = {
        "prompt": "Research latest tech news and create a report, then email it to sabawi@gmail.com",
        "model": "qwen3:8b", 
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🚀 Testing clean HTML creation (no file type specified)...")
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
            
        # Check if post-processing completed
        if 'post_processing": "completed"' in response.text:
            print("✅ Post-processing completed successfully!")
        else:
            print("❌ Post-processing may not have completed")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_clean_html()
    sys.exit(0 if success else 1)