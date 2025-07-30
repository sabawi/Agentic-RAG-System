#!/usr/bin/env python3
"""
Quick test for financial news functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_financial_news_quick():
    """Quick test with shorter timeout"""
    print("🧪 Quick Financial News Test")
    print("=" * 40)
    
    payload = {
        "prompt": "look up the latest financial news as of today then summarize it",
        "toolsInUse": True
    }
    
    print(f"📤 Request: {payload['prompt']}")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/llama3_1b/stream", 
            json=payload, 
            stream=True, 
            timeout=60
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Reading stream (first 5 chunks)...")
            
            chunk_count = 0
            financial_content_found = False
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    
                    print(f"   Chunk {chunk_count}: {len(chunk_text)} bytes")
                    
                    # Check for financial content
                    if any(word in chunk_text.lower() for word in 
                           ['financial', 'news', 'market', 'stock', 'economy', 'business']):
                        print(f"   💰 Financial content detected in chunk {chunk_count}")
                        financial_content_found = True
                    
                    # Show some content
                    if chunk_text.strip():
                        preview = chunk_text[:100].replace('\n', ' ')
                        print(f"      Preview: {preview}...")
                    
                    # Stop after 5 chunks to avoid hanging
                    if chunk_count >= 5:
                        print("   🛑 Stopping after 5 chunks")
                        break
            
            response.close()
            
            if financial_content_found:
                print("✅ SUCCESS: Financial news functionality appears to be working!")
            else:
                print("⚠️ WARNING: No clear financial content detected")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might indicate tool processing is taking long")
        print("💡 Check server logs for tool execution details")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_financial_news_quick()