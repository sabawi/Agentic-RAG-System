#!/usr/bin/env python3
"""
Quick Image Test - Simple verification
"""

import requests
import json
import base64
from pathlib import Path

# Get first image from Pictures
pictures_dir = Path.home() / "Pictures" 
images = list(pictures_dir.glob("*.jpg")) + list(pictures_dir.glob("*.jpeg")) + list(pictures_dir.glob("*.png"))

if not images:
    print("❌ No images found in ~/Pictures")
    print("Available files:", list(pictures_dir.iterdir())[:5])
    exit(1)

img_path = images[0]
print(f"🖼️ Testing with: {img_path.name} ({img_path.stat().st_size // 1024} KB)")

# Encode to base64
with open(img_path, "rb") as f:
    img_data = base64.b64encode(f.read()).decode('utf-8')

# Determine MIME type
ext = img_path.suffix.lower()
mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
b64_image = f"data:{mime_type};base64,{img_data}"

print(f"📤 Base64 encoded: {len(b64_image):,} characters")

# Test 1: Simple natural language
print("\n🧪 Test 1: Natural Language Request")
payload1 = {
    "prompt": "I want to analyze an image. Can you help describe what's in it?",
    "model": "qwen3:8b",
    "tools": True,
    "stream": False
}

try:
    response = requests.post("http://localhost:5000/llama3_1b/stream", json=payload1, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Natural language request successful")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Direct tool call with file path
print("\n🧪 Test 2: Direct Tool Call (File Path)")
payload2 = {
    "prompt": "Analyze image with image_to_text tool",
    "model": "qwen3:8b",
    "tools": True,
    "stream": False,
    "tool_calls": [{
        "function": {
            "name": "image_to_text",
            "arguments": {
                "images": [{
                    "type": "file",
                    "path": str(img_path)
                }],
                "processing_mode": "sequential"
            }
        }
    }]
}

try:
    response = requests.post("http://localhost:5000/llama3_1b/stream", json=payload2, timeout=60)
    print(f"Status: {response.status_code}")
    result = response.json() if response.status_code == 200 else response.text
    print(f"Response preview: {str(result)[:300]}...")
    
    if response.status_code == 200 and isinstance(result, dict):
        # Look for tool results
        if 'tool_results' in result:
            print("🔧 Found tool_results")
        if 'response' in result:
            print("📝 Found response")
            
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Quick tests complete!")
print(f"Image used: {img_path}")
print("Check server logs with: tail -f server_complete.log")