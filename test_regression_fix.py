#!/usr/bin/env python3
"""
Test the regression fix for PDF and image functionality
"""

import requests
import json
import time

def test_pdf_conversation_request():
    """Test PDF conversation export - the main regression we fixed"""
    print("🧪 Testing PDF conversation export...")
    
    payload = {
        "prompt": "Email the above response as PDF to sabawi@gmail.com",
        "model": "qwen3:8b", 
        "toolsInUse": True,
        "stream": False,
        "prompt_context": """
        === CONVERSATION HISTORY ===
        USER: What is 2+2?
        ASSISTANT: 2+2 equals 4.
        
        === CURRENT REQUEST ===
        Email the above response as PDF to sabawi@gmail.com
        """
    }
    
    try:
        response = requests.post("http://localhost:5000/llama3_1b/stream", json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF request successful")
            print(f"Response preview: {str(result)[:200]}...")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_image_analysis():
    """Test image-to-text functionality"""  
    print("🧪 Testing image analysis...")
    
    payload = {
        "prompt": "I want to analyze an image. Use the image_to_text tool to help me.",
        "model": "qwen3:8b",
        "toolsInUse": True,
        "stream": False
    }
    
    try:
        response = requests.post("http://localhost:5000/llama3_1b/stream", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json() 
            print("✅ Image analysis request successful")
            print(f"Response preview: {str(result)[:200]}...")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔍 REGRESSION FIX TEST")
    print("=" * 30)
    
    # Test 1: PDF conversation export (the main regression)
    pdf_success = test_pdf_conversation_request()
    time.sleep(2)
    
    # Test 2: Image analysis functionality  
    image_success = test_image_analysis()
    
    print("\n📊 TEST RESULTS")
    print("=" * 20)
    print(f"PDF Export: {'✅ PASS' if pdf_success else '❌ FAIL'}")
    print(f"Image Analysis: {'✅ PASS' if image_success else '❌ FAIL'}")
    
    if pdf_success and image_success:
        print("\n🎉 ALL TESTS PASSED - Regression fix successful!")
    else:
        print("\n⚠️  Some tests failed - Check server logs")

if __name__ == "__main__":
    main()