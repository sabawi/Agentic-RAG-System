#!/usr/bin/env python3
"""
Test different prompting styles for robustness with the actual tool calling system
"""

import requests
import json
import time

# Email sender tool definition (matching the actual tool)
EMAIL_TOOL = {
    "type": "function",
    "function": {
        "name": "secure_email_sender",
        "description": "Sends emails securely with attachments. Requires email credentials to be configured.",
        "parameters": {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": "The recipient's email address"
                },
                "subject": {
                    "type": "string", 
                    "description": "The email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "The email body content"
                },
                "cc_email": {
                    "type": "string",
                    "description": "Optional CC email address"
                },
                "attachments": {
                    "type": "string",
                    "description": "Optional file attachment path or filename"
                }
            },
            "required": ["to_email", "subject", "body"]
        }
    }
}

def send_test_request(prompt, test_name):
    """Send a test request and return the response"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"Prompt: {prompt}")
    print(f"{'='*60}")
    
    payload = {
        "prompt": prompt,
        "toolsInUse": True,
        "model": "deepseek-v3.1:671b-cloud",
        "temperature": 0.1
    }
    
    try:
        response = requests.post("http://localhost:5000/llama3_1b/stream", 
                               json=payload, stream=True, timeout=120)
        if response.status_code == 200:
            full_response = ""
            tool_calls_found = False
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            if 'delta' in choice:
                                delta = choice['delta']
                                if 'content' in delta:
                                    full_response += delta['content']
                                if 'tool_calls' in delta:
                                    tool_calls_found = True
                                    print(f"🎯 TOOL CALLS DETECTED: {delta['tool_calls']}")
                    except json.JSONDecodeError:
                        continue
            
            if tool_calls_found:
                print(f"✅ SUCCESS: {test_name} - Tool calls triggered!")
            elif "email" in full_response.lower() or "send" in full_response.lower():
                print(f"🟡 PARTIAL: {test_name} - Understood request but no tool call")
            else:
                print(f"❌ FAILED: {test_name} - No email understanding")
                
            print(f"Response: {full_response[:200]}...")
            return full_response
        else:
            print(f"❌ FAILED: {test_name} - Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {test_name} - {str(e)}")
        return None

def main():
    print("🧪 Testing Different Prompting Styles for Email Tool Robustness")
    print("=" * 70)
    
    # Test 1: Natural conversational style
    send_test_request(
        "Hi! Can you please send an email to john@example.com with the subject 'Meeting Tomorrow' and tell him we need to reschedule our 3pm meeting to 4pm? Thanks!",
        "Natural Conversational"
    )
    
    time.sleep(2)
    
    # Test 2: Direct command style
    send_test_request(
        "Send email to jane@company.com. Subject: Project Update. Message: The quarterly report is ready for review.",
        "Direct Command"
    )
    
    time.sleep(2)
    
    # Test 3: Formal request style
    send_test_request(
        "I would like to request that you compose and send an electronic mail message to mike@business.org with the subject line 'Contract Review' and inform them that the legal documents require their signature.",
        "Formal Request"
    )
    
    time.sleep(2)
    
    # Test 4: Question format
    send_test_request(
        "Could you help me send an email to team@startup.com asking if they're available for a video call this Friday at 2pm?",
        "Question Format"
    )
    
    time.sleep(2)
    
    # Test 5: Urgent/emotional style
    send_test_request(
        "URGENT! Need to email client@important.com RIGHT NOW about the server outage. Subject should be 'Critical System Alert' and explain we're working on it!",
        "Urgent/Emotional"
    )
    
    time.sleep(2)
    
    # Test 6: Multi-step with CC
    send_test_request(
        "Send an email to boss@company.com with subject 'Weekly Report' about this week's accomplishments, and also CC accounting@company.com so they stay in the loop.",
        "Multi-step with CC"
    )

if __name__ == "__main__":
    main()