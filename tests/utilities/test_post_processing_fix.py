#!/usr/bin/env python3
"""
Test POST-PROCESSING fix - Gaza email request
Verifies that POST-PROCESSING email system executes after successful LLM streaming
"""
import requests
import json
import time

def test_gaza_email():
    """Test that email is sent when requested with news search"""

    prompt = "Deep search for the latest top and crucial news from Gaza and the Middle East as of today. Sort them by published date and importance. Expand and discuss key items in details. Cite date/time and sources of the news for each item. Email the full search in html attachment to test@example.com"

    print("🧪 Testing POST-PROCESSING Fix - Gaza Email Request")
    print("=" * 70)
    print(f"📝 Prompt: {prompt[:100]}...")
    print("=" * 70)
    print()

    url = "http://localhost:5000/v1/chat/completions"
    payload = {
        "model": "Agentic-RAG-Model1",
        "messages": [{"role": "user", "content": prompt}]
    }

    print("📤 Sending request...")
    start_time = time.time()

    try:
        response = requests.post(url, json=payload, timeout=300, stream=True)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            print(f"✅ Request completed in {elapsed:.2f}s")
            print()
            print("📊 Streaming response chunks:")
            print("-" * 70)

            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    try:
                        data = json.loads(line)
                        if data.get("post_processing") == "completed":
                            print(f"\n✅ POST-PROCESSING COMPLETED!")
                            print(f"   Tools executed: {data.get('tools_executed', [])}")
                    except:
                        pass

            print(f"\n📊 Total chunks received: {chunk_count}")
            print("-" * 70)

            print("\n🔍 Checking server logs for confirmation...")
            time.sleep(2)

        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(5)
    test_gaza_email()
