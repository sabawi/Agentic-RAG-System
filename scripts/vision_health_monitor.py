#!/usr/bin/env python3
"""
Vision Processing Health Monitor

Runs periodic checks to ensure vision processing remains functional.
Add this to cron for automated monitoring.
"""

import requests
import sys
import time
from datetime import datetime

def check_vision_health():
    """Quick health check for vision processing"""

    tiny_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQImQEBAAAAAAA3bvkkAAAAAElFTkSuQmCC"

    payload = {
        "model": "qwen3:8b",
        "messages": [{"role": "user", "content": "Health check - can you see this image?"}],
        "images": [tiny_image],
        "toolsInUse": True
    }

    try:
        response = requests.post("http://localhost:5000/v1/chat/completions",
                               json=payload, timeout=30)

        if response.status_code == 200 and "image" in response.text.lower():
            print(f"[{datetime.now()}] ✅ Vision health check PASSED")
            return True
        else:
            print(f"[{datetime.now()}] ❌ Vision health check FAILED")
            return False

    except Exception as e:
        print(f"[{datetime.now()}] 💥 Vision health check ERROR: {e}")
        return False

if __name__ == "__main__":
    success = check_vision_health()
    sys.exit(0 if success else 1)
