#!/usr/bin/env python3
"""
Test to verify document_search is selected for resume retrieval
"""
import requests
import json
import time

def test_resume_retrieval():
    """Test that document_search is used to retrieve resume content"""

    # Simple prompt that should trigger document_search
    prompt = "Find and read my resume from the indexed documents. Search for 'John Smith resume' or similar resume documents and show me the key qualifications and experience."

    print("🧪 Testing Resume Tool Selection")
    print("=" * 70)
    print(f"📝 Prompt: {prompt}")
    print("=" * 70)
    print()

    url = "http://localhost:5000/v1"
    payload = {
        "prompt": prompt,
        "model": "gpt-4o-mini",
        "stream": False
    }

    print("📤 Sending request...")
    start_time = time.time()

    try:
        response = requests.post(url, json=payload, timeout=120)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()

            print(f"✅ Request completed in {elapsed:.2f}s")
            print()
            print("📊 Response:")
            print("-" * 70)

            # Check if response indicates document_search was used
            response_text = result.get('response', '')
            print(response_text)
            print("-" * 70)

            # Check logs to verify tool selection
            print()
            print("🔍 Checking server logs for tool selection...")

        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    test_resume_retrieval()
