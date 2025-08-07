#!/usr/bin/env python3
"""
Test different prompting styles to ensure the system is robust
"""

import requests
import json
import time

def send_test_request(prompt, test_name):
    """Send a test request and return the response"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"Prompt: {prompt}")
    print(f"{'='*60}")
    
    payload = {
        "model": "llama3.2:3b",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post("http://localhost:5000/llama3_1b/prompt", 
                               json=payload, timeout=120)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {test_name}")
            return result
        else:
            print(f"❌ FAILED: {test_name} - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {test_name} - {str(e)}")
        return None

def main():
    # Test 1: Natural conversational style
    send_test_request(
        "Hi! Can you please send an email to john@example.com with the subject 'Meeting Tomorrow' and tell him we need to reschedule our 3pm meeting to 4pm? Thanks!",
        "Natural Conversational Style"
    )
    
    time.sleep(2)
    
    # Test 2: Direct command style
    send_test_request(
        "Send email to jane@company.com. Subject: Project Update. Message: The quarterly report is ready for review.",
        "Direct Command Style"
    )
    
    time.sleep(2)
    
    # Test 3: Formal request style
    send_test_request(
        "I would like to request that you compose and send an electronic mail message to the recipient mike@business.org with the subject line 'Contract Review' and inform them that the legal documents require their signature.",
        "Formal Request Style"
    )
    
    time.sleep(2)
    
    # Test 4: Incomplete/vague style
    send_test_request(
        "Email sarah about the meeting... something about moving it to next week",
        "Incomplete/Vague Style"
    )
    
    time.sleep(2)
    
    # Test 5: Multi-step request
    send_test_request(
        "First, create a report about today's sales figures. Then email it to boss@company.com with subject 'Daily Sales Report' and also CC accounting@company.com",
        "Multi-step Request"
    )
    
    time.sleep(2)
    
    # Test 6: Question format
    send_test_request(
        "Could you help me send an email to team@startup.com asking if they're available for a video call this Friday at 2pm?",
        "Question Format"
    )
    
    time.sleep(2)
    
    # Test 7: Urgent/emotional style
    send_test_request(
        "URGENT! Need to email client@important.com RIGHT NOW about the server outage. Subject should be 'Critical System Alert' and explain we're working on it!",
        "Urgent/Emotional Style"
    )
    
    time.sleep(2)
    
    # Test 8: Technical jargon
    send_test_request(
        "Initiate SMTP protocol to transmit data packet to dev@tech.com regarding API endpoint deprecation with subject header 'REST API v1.0 EOL Notice'",
        "Technical Jargon Style"
    )

if __name__ == "__main__":
    main()