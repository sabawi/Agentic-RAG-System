#!/usr/bin/env python3
"""
Test Story Writing Prompt with Dependency-Aware Arbitrator
===========================================================

Tests: fortune_message → sandboxed_executor → secure_email_sender chain
"""

import requests
import json

SERVER_URL = "http://localhost:5000"

def test_story_with_email():
    """
    Test the complete story workflow:
    1. Get fortune
    2. Write story to file
    3. Email the story
    """

    print("\n" + "="*70)
    print("TEST: Story Writing with Fortune + File + Email")
    print("="*70)

    prompt = """
    Write a short story based on my fortune and email it to test@example.com
    then write the story into a file in sandbox_workspace/mydocuments.
    Make sure you give it an interesting name
    """

    print(f"\n📝 PROMPT:\n{prompt.strip()}")
    print(f"\n🔄 Sending to {SERVER_URL}/v1...")

    try:
        response = requests.post(
            f"{SERVER_URL}/v1",
            json={
                "model": "deepseek-v3.1:671b-cloud",
                "prompt": prompt,
                "toolsInUse": True,
                "searchWebInUse": False
            },
            timeout=180,
            stream=True
        )

        if response.status_code == 200:
            print(f"\n✅ SERVER RESPONSE (status: {response.status_code})")
            print(f"\n📊 Streaming response:")

            for line in response.iter_lines():
                if line:
                    print(line.decode('utf-8'))

            print("\n" + "="*70)
            print("CHECK LOGS FOR DEPENDENCY-AWARE EXECUTION:")
            print("="*70)
            print("Expected execution order:")
            print("  Stage 1: fortune_message")
            print("  Stage 2: sandboxed_executor (with fortune content)")
            print("  Stage 3: secure_email_sender (intercepted)")
            print("  POST-PROCESSING: Email sent with story attachment")
            print("\nRun: tail -f logs/server_complete.log | grep -E 'STAGE|DEFERRED|🐛 DEBUG'")

        else:
            print(f"\n❌ SERVER ERROR (status: {response.status_code})")
            print(response.text)

    except requests.exceptions.Timeout:
        print(f"\n⏱️  REQUEST TIMEOUT (180s)")
        print("Check logs/server_complete.log for execution details")
    except Exception as e:
        print(f"\n❌ REQUEST FAILED: {e}")

if __name__ == "__main__":
    test_story_with_email()
