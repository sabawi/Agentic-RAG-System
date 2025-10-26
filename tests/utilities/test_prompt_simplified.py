#!/usr/bin/env python3

import requests
import json
import time

def test_citation_with_simplified_prompt():
    """Test if simplified system prompt produces proper citations"""
    
    url = "http://localhost:5000/v1/chat/completions"
    
    test_cases = [
        {
            "name": "AI Technology News",
            "prompt": "What are the latest developments in AI technology this week?"
        },
        {
            "name": "Financial News",
            "prompt": "What are the latest financial market developments today?"
        },
        {
            "name": "Wikipedia Query",
            "prompt": "Tell me about artificial intelligence and its recent developments"
        }
    ]
    
    print("🧪 TESTING SIMPLIFIED SYSTEM PROMPT CITATION BEHAVIOR")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 TEST {i}: {test_case['name']}")
        print(f"Prompt: {test_case['prompt']}")
        print("-" * 40)
        
        try:
            payload = {
                "model": "deepseek-v3.1:671b-cloud",
                "messages": [
                    {"role": "user", "content": test_case['prompt']}
                ],
                "temperature": 0.7,
                "stream": False
            }
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                # Handle OpenAI API response format
                if 'choices' in result and len(result['choices']) > 0:
                    final_response = result['choices'][0].get('message', {}).get('content', '')
                else:
                    final_response = result.get('response', '')
                
                # Check for citations
                citation_count = final_response.count('[') + final_response.count('](')
                has_citations = '[' in final_response and '](' in final_response
                
                print(f"✅ Response received ({len(final_response)} chars)")
                print(f"📊 Citation analysis:")
                print(f"   - Has citations: {'YES' if has_citations else 'NO'}")
                print(f"   - Citation markers: {citation_count}")
                
                if has_citations:
                    print(f"🎯 SUCCESS: Citations detected!")
                    # Show first citation as example
                    start = final_response.find('[')
                    end = final_response.find(')', start)
                    if start != -1 and end != -1:
                        citation_example = final_response[start:end+1]
                        print(f"   Example: {citation_example}")
                else:
                    print(f"❌ FAILURE: No citations found")
                    print(f"📝 Response preview (first 200 chars):")
                    print(f"   {final_response[:200]}...")
                
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request Error: {e}")
        
        if i < len(test_cases):
            print(f"\n⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    print(f"\n🏁 TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_citation_with_simplified_prompt()