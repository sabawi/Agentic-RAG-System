#!/usr/bin/env python3
"""
Very simple test to see if tools are being called
"""

import requests
import time

BASE_URL = "http://localhost:5000"

def simple_test():
    """Simple test with maximum debugging"""
    print("🧪 Simple Tool Execution Test")
    print("=" * 40)
    
    # Very simple stock query
    payload = {
        "prompt": "AAPL stock",  # Very simple to trigger stock tool
        "toolsInUse": True
    }
    
    print(f"📤 Request: {payload}")
    print("🔍 Check your server logs for:")
    print("   - 'Processing tool calls with direct keyword analysis...'")
    print("   - 'Calling stock tool for symbol: AAPL'")
    print("   - 'Executed tools: [...]'")
    print("   - 'Tools results length: X characters'")
    print("   - 'Final prompt length: X characters'")
    print()
    
    try:
        response = requests.post(f"{BASE_URL}/llama3_1b/stream", json=payload, timeout=10)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request succeeded - check server logs above")
            # Just get first chunk to trigger the tool processing
            chunk = next(response.iter_content(chunk_size=1024))
            print(f"📝 First chunk: {chunk.decode('utf-8', errors='ignore')[:100]}...")
        else:
            print(f"❌ Request failed: {response.status_code}")
            
        response.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    simple_test()