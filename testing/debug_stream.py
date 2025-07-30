#!/usr/bin/env python3
"""
Debug the streaming output to see what's actually being sent
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def debug_stream_output():
    """Debug what's actually in the stream"""
    print("🔍 Debugging Stream Output")
    print("=" * 50)
    
    payload = {
        "prompt": "What is the current time and Apple stock price?",
        "toolsInUse": True
    }
    
    print(f"📤 Sending request: {payload}")
    print()
    
    try:
        response = requests.post(f"{BASE_URL}/llama3_1b/stream", json=payload, stream=True, timeout=30)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Stream content:")
            print("-" * 30)
            
            chunk_count = 0
            total_content = ""
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    total_content += chunk_text
                    
                    print(f"Chunk {chunk_count}: {repr(chunk_text[:100])}...")
                    
                    # Look for JSON structure
                    if chunk_text.strip():
                        try:
                            chunk_json = json.loads(chunk_text.strip())
                            if 'response' in chunk_json:
                                print(f"  → Response: {chunk_json['response'][:100]}...")
                        except json.JSONDecodeError:
                            print(f"  → Raw text: {chunk_text[:100]}...")
                    
                    if chunk_count >= 10:  # Limit for debugging
                        print("... (stopping after 10 chunks)")
                        break
            
            print("-" * 30)
            print(f"📈 Total chunks: {chunk_count}")
            print(f"📝 Total content length: {len(total_content)}")
            
            # Check if tool results are in the content
            if "Tool:" in total_content:
                print("✅ Tool execution found in stream!")
            elif "current date" in total_content.lower():
                print("✅ Tool results found indirectly!")
            elif "stock" in total_content.lower() and "apple" in total_content.lower():
                print("✅ Stock data found in response!")
            else:
                print("⚠️ No clear tool execution evidence in output")
                
            response.close()
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    debug_stream_output()