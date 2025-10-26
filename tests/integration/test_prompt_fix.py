#!/usr/bin/env python3
"""
Quick test to verify the prompt format fix works
"""

import requests
import json

def test_single_prompt():
    payload = {
        "prompt": "Send an email to test@example.com with subject 'Test' and body 'Hello world'",
        "toolsInUse": True,
        "model": "deepseek-v3.1:671b-cloud"
    }
    
    print("🧪 Testing Fixed Prompt Format")
    print("=" * 40)
    print(f"Prompt: {payload['prompt']}")
    print(f"Format: {list(payload.keys())}")
    
    try:
        response = requests.post("http://localhost:5000/llama3_1b/stream", 
                               json=payload, stream=True, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS - No more KeyError!")
            # Just read first few chunks to confirm it's working
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    if chunk_count > 3:  # Just test first few chunks
                        break
                    try:
                        data = json.loads(line.decode('utf-8'))
                        print(f"  Chunk {chunk_count}: {list(data.keys())}")
                    except:
                        print(f"  Chunk {chunk_count}: raw data")
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")

if __name__ == "__main__":
    test_single_prompt()