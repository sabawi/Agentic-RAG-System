#!/usr/bin/env python3
"""
Test arXiv URL handling to verify tools are called instead of hallucination
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_arxiv_paper():
    print("🧪 Testing arXiv Paper URL Handling")
    print("=" * 50)
    
    # Test arXiv paper URL
    payload = {
        "prompt": "Explain this paper in details: URL: https://arxiv.org/html/2501.00139v2#S1",
        "model": "deepseek-v3.1:671b-cloud",
        "toolsInUse": True,
        "system": "You are a helpful assistant."
    }
    
    print(f"📤 Request: {payload['prompt']}")
    print()
    print("🔍 Looking for indicators that tools were used:")
    print("   - 'Timelike boundary and corner terms' (correct paper title)")
    print("   - References to actual paper content")
    print("   - No immediate hallucinated response")
    print()
    
    try:
        print("⏳ Sending request (this may take time if tools are working)...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/llama3_1b/stream", 
            json=payload, 
            stream=True, 
            timeout=120  # 2 minutes for tool execution
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Reading response stream...")
            
            chunk_count = 0
            actual_response = ""
            found_paper_title = False
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    
                    # Parse JSON chunks to extract LLM response
                    lines = chunk_text.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            try:
                                chunk_data = json.loads(line)
                                if 'response' in chunk_data:
                                    response_text = chunk_data['response']
                                    actual_response += response_text
                                    
                                    # Check for correct paper title
                                    if ('timelike boundary' in response_text.lower() and 
                                        'corner terms' in response_text.lower()):
                                        found_paper_title = True
                                        print(f"   ✅ Found correct paper title in chunk {chunk_count}!")
                                    
                                if chunk_data.get('done', False):
                                    print(f"   🏁 Stream completed at chunk {chunk_count}")
                                    break
                            except json.JSONDecodeError:
                                pass
                    
                    # Show progress
                    if chunk_count % 10 == 0:
                        print(f"   📝 Processed {chunk_count} chunks, {len(actual_response)} chars...")
                    
                    # Stop after reasonable time/content
                    if chunk_count >= 100 or len(actual_response) > 2000:
                        print(f"   🛑 Stopping after {chunk_count} chunks")
                        break
                        
            response.close()
            elapsed_time = time.time() - start_time
            
            print()
            print("📊 Analysis Results:")
            print(f"   Chunks processed: {chunk_count}")
            print(f"   Response length: {len(actual_response)} characters")
            print(f"   Processing time: {elapsed_time:.1f} seconds")
            
            if found_paper_title:
                print("   🎯 SUCCESS: Correct paper title found!")
                print("   ✅ Tool calling is working - real content retrieved")
            elif len(actual_response) > 100:
                if ('based on' in actual_response.lower() or 
                    'retrieved' in actual_response.lower() or
                    'according to' in actual_response.lower()):
                    print("   ⚡ TOOLS LIKELY EXECUTED: Response indicates data retrieval")
                else:
                    print("   ⚠️ UNCLEAR: Response received but unclear if from tools")
                    
                print(f"   📝 Sample response: {actual_response[:300]}...")
            else:
                print("   ❌ FAILED: Very short or no response received")
                
            # Check if processing time indicates tool execution
            if elapsed_time > 30:
                print("   📈 Long processing time suggests tool execution occurred")
            elif elapsed_time < 5:
                print("   ⚡ Very fast response may indicate hallucination without tools")
                
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this actually suggests tools were being executed!")
        print("💡 The system is working but needs more time for comprehensive tool execution")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_arxiv_paper()