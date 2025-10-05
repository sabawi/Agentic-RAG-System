#!/usr/bin/env python3
"""
Test Real Prompt with Dependency-Aware Arbitrator
==================================================

Send actual prompt to server and monitor dependency-aware execution
"""

import requests
import json
import time

SERVER_URL = "http://localhost:5000"

def test_web_article_save_email():
    """
    Test the web article save + email workflow with dependency-aware arbitrator.
    Expected: lookup_website → sandboxed_executor → secure_email_sender
    """

    print("\n" + "="*70)
    print("TEST: Web Article Save + Email (Real Prompt)")
    print("="*70)

    # The prompt that should trigger all 3 tools in dependency order
    prompt = """
    Save this article https://www.anthropic.com/research/measuring-model-persuasiveness
    to sandbox_workspace/mydocuments/persuasion_article.html
    then email it to sabawi@gmail.com with subject "Anthropic Research Article"
    """

    print(f"\n📝 PROMPT:\n{prompt.strip()}")
    print(f"\n🔄 Sending to {SERVER_URL}/query...")

    try:
        response = requests.post(
            f"{SERVER_URL}/v1",
            json={
                "model": "llama3.3:70b-instruct-q4_K_M",
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
            # Read streaming response
            for line in response.iter_lines():
                if line:
                    print(line.decode('utf-8'))

            print("\n" + "="*70)
            print("CHECK LOGS FOR DEPENDENCY-AWARE EXECUTION:")
            print("="*70)
            print("Expected log entries:")
            print("  🧠 DEPENDENCY-AWARE MODE: Using arbitrator-based execution planning")
            print("  ✅ ARBITRATOR PLAN CREATED: 3 execution stages")
            print("     Stage 1 (→ SEQUENTIAL): ['lookup_website']")
            print("     Stage 2 (→ SEQUENTIAL): ['sandboxed_executor']")
            print("     Stage 3 (→ SEQUENTIAL): ['secure_email_sender']")
            print("\nRun: tail -f logs/server_complete.log | grep -E 'DEPENDENCY|ARBITRATOR|STAGE'")

        else:
            print(f"\n❌ SERVER ERROR (status: {response.status_code})")
            print(response.text)

    except requests.exceptions.Timeout:
        print(f"\n⏱️  REQUEST TIMEOUT (120s)")
        print("Check logs/server_complete.log for execution details")
    except Exception as e:
        print(f"\n❌ REQUEST FAILED: {e}")

if __name__ == "__main__":
    test_web_article_save_email()
