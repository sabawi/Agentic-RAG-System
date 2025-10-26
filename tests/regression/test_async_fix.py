#!/usr/bin/env python3
"""
Direct test of async event loop fix for PDF generation
"""

import requests
import json
import time
import os

def test_pdf_async_fix():
    """Test that async event loop fix works for PDF generation"""
    print("🔧 Testing async event loop fix for PDF generation...")
    
    # Clean up any existing test files
    test_file = "sandbox_workspace/async_test.pdf"
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"🧹 Cleaned up existing {test_file}")
    
    payload = {
        "prompt": "Create a PDF document called async_test.pdf with some test content about async event loops",
        "model": "deepseek-v3.1:671b-cloud", 
        "toolsInUse": True,
        "stream": False
    }
    
    try:
        print("📡 Sending PDF creation request...")
        response = requests.post("http://localhost:5000/llama3_1b/stream", json=payload, timeout=60)
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Request successful - parsing response...")
                print(f"📄 Response length: {len(str(result))} characters")
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"📄 Raw response (first 500 chars): {response.text[:500]}...")
                return False
                
            # Check if PDF file was created
            if os.path.exists(test_file):
                # Check if it's a proper PDF
                with open(test_file, 'rb') as f:
                    first_bytes = f.read(10)
                    if first_bytes.startswith(b'%PDF'):
                        file_size = os.path.getsize(test_file)
                        print(f"✅ SUCCESS: Proper PDF created ({file_size} bytes)")
                        return True
                    else:
                        print(f"❌ FAILED: File created but not a proper PDF (starts with: {first_bytes})")
                        return False
            else:
                print(f"❌ FAILED: PDF file not created at {test_file}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_async_fix()
    print(f"\n🎯 ASYNC FIX TEST: {'✅ SUCCESS' if success else '❌ FAILED'}")