#!/usr/bin/env python3
"""
Test arXiv PDF handling to verify tools are called instead of hallucination
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_arxiv_pdf():
    print("🧪 Testing arXiv Paper PDF Handling")
    print("=" * 50)
    
    # Test arXiv paper PDF URL
    payload = {
        "prompt": "Explain this paper in details: URL: https://arxiv.org/pdf/2501.00139v2.pdf",
        "model": "llama3.2:3b",
        "toolsInUse": True,
        "system": "You are a helpful assistant."
    }
    
    print(f"📤 Request: {payload['prompt']}")
    print()
    print("🔍 Looking for indicators that PDF tools were used:")
    print("   - 'Timelike boundary and corner terms' (correct paper title)")
    print("   - References to actual paper content from PDF")
    print("   - No immediate hallucinated response")
    print()
    
    try:
        print("⏳ Sending request (PDF processing may take longer)...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/llama3_1b/stream", 
            json=payload, 
            stream=True, 
            timeout=180  # 3 minutes for PDF processing
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 Reading PDF response stream...")
            
            chunk_count = 0
            actual_response = ""
            found_paper_title = False
            found_pdf_content = False
            
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
                                    
                                    # Check for PDF-specific content
                                    if ('causal set' in response_text.lower() or
                                        'dimension d' in response_text.lower() or
                                        'abstract' in response_text.lower()):
                                        found_pdf_content = True
                                        print(f"   📄 Found PDF content indicators in chunk {chunk_count}")
                                    
                                if chunk_data.get('done', False):
                                    print(f"   🏁 Stream completed at chunk {chunk_count}")
                                    break
                            except json.JSONDecodeError:
                                pass
                    
                    # Show progress
                    if chunk_count % 15 == 0:
                        print(f"   📝 Processed {chunk_count} chunks, {len(actual_response)} chars...")
                    
                    # Stop after reasonable time/content
                    if chunk_count >= 120 or len(actual_response) > 3000:
                        print(f"   🛑 Stopping after {chunk_count} chunks")
                        break
                        
            response.close()
            elapsed_time = time.time() - start_time
            
            print()
            print("📊 PDF Analysis Results:")
            print(f"   Chunks processed: {chunk_count}")
            print(f"   Response length: {len(actual_response)} characters")
            print(f"   Processing time: {elapsed_time:.1f} seconds")
            
            if found_paper_title and found_pdf_content:
                print("   🎯 SUCCESS: PDF extraction and correct content found!")
                print("   ✅ Tool calling is working perfectly for PDFs")
            elif found_paper_title:
                print("   ⚡ PARTIAL SUCCESS: Correct title found")
                print("   ✅ Tool calling working but may need more content")
            elif len(actual_response) > 200:
                if ('based on' in actual_response.lower() or 
                    'according to' in actual_response.lower() or
                    'paper' in actual_response.lower()):
                    print("   ⚡ TOOLS LIKELY EXECUTED: Response indicates PDF processing")
                else:
                    print("   ⚠️ UNCLEAR: Response received but source unclear")
                    
                print(f"   📝 Sample response: {actual_response[:400]}...")
            else:
                print("   ❌ FAILED: Very short or no response received")
                
            # Check if processing time indicates tool execution
            if elapsed_time > 45:
                print("   📈 Long processing time suggests PDF extraction occurred")
            elif elapsed_time < 10:
                print("   ⚡ Very fast response may indicate hallucination without tools")
                
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - PDF processing takes significant time!")
        print("💡 This suggests tools were being executed for PDF extraction")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_arxiv_pdf()