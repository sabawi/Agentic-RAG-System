#!/usr/bin/env python3
"""
🚀 Creative News Analysis Workflow Example
===========================================

This example demonstrates a complex news gathering and analysis workflow that:
1. Searches for trending tech news
2. Analyzes stock market impact
3. Creates a detailed PDF report
4. Sends email with the report attached

Both Native API and OpenAI Compatible endpoints are shown.
"""

import requests
import json
from datetime import datetime

# Server configuration
SERVER_URL = "http://localhost:5000"
API_KEY = "test-key"  # Any value works for our server

def native_api_example():
    """
    🌟 NATIVE API: Advanced News Analysis Workflow
    
    This uses the native Agentic-RAG endpoint with full control.
    """
    print("🚀 Starting Native API News Analysis Workflow...")
    
    # Creative prompt that will trigger multiple tools
    creative_prompt = """
    I'm a curious investor fascinated by the intersection of technology and markets! 🚀📈
    
    Here's my exciting research mission:
    
    1. 🔍 Hunt down the most intriguing AI and tech news from today
    2. 🧠 Analyze which companies might be impacted (both positively and negatively)
    3. 📊 Look up current stock prices for the top 3 most mentioned companies
    4. 🎯 Create a beautiful PDF report called "tech_market_pulse_today.pdf" with:
       - Executive summary with key findings
       - News highlights with impact analysis
       - Stock price data and trend insights
       - Investment recommendations based on the analysis
    5. 📧 Email this golden report to user@example.com with subject "🚀 Today's Tech Market Pulse Report"
    
    Make this analysis insightful and engaging - I want to feel like I have insider knowledge!
    """
    
    payload = {
        "prompt": creative_prompt,
        "model": "qwen3:8b",
        "stream": False,
        "tools": True,
        "conversation_id": f"news_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    try:
        print("📡 Sending request to native endpoint...")
        response = requests.post(
            f"{SERVER_URL}/llama3_1b/stream",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=600  # 10 minutes for complex analysis
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Native API Response received!")
            print("🎯 Tools used:", result.get('tools_called', []))
            print("📝 Response preview:", result.get('response', '')[:200] + "...")
            return result
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"🚫 Request failed: {e}")
        return None

def openai_api_example():
    """
    🌐 OPENAI COMPATIBLE API: News & Market Intelligence
    
    This uses OpenAI-compatible endpoint for seamless integration.
    """
    print("\n🌐 Starting OpenAI Compatible API Workflow...")
    
    # Another creative scenario with different focus
    market_intelligence_prompt = """
    Act as my personal AI market intelligence analyst! 🕵️‍♀️💼
    
    Mission briefing:
    
    🎯 **Operation Market Radar**
    1. 📰 Scan breaking news for any mentions of cryptocurrency, AI regulation, or tech IPOs
    2. 🔍 Cross-reference with local documents in our database for any related research
    3. 📈 Get current prices for Bitcoin, Ethereum, and top 3 AI stocks (NVDA, GOOGL, MSFT)
    4. 🧮 Calculate percentage changes from yesterday
    5. 📋 Create a strategic briefing document "market_intelligence_brief.pdf" including:
       - Threat/opportunity matrix
       - Key market movers today
       - Regulatory impact assessment
       - 48-hour outlook predictions
    6. 📧 Rush this to user@example.com with subject "🚨 URGENT: Market Intelligence Brief"
    
    Be thorough but concise - this needs to read like a professional intelligence briefing!
    """
    
    payload = {
        "model": "gpt-4o",  # Using OpenAI model name (maps to our agentic system)
        "messages": [
            {"role": "user", "content": market_intelligence_prompt}
        ],
        "stream": False,
        "max_tokens": 4000
    }
    
    try:
        print("📡 Sending request to OpenAI compatible endpoint...")
        response = requests.post(
            f"{SERVER_URL}/v1/chat/completions",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            },
            timeout=600
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OpenAI API Response received!")
            
            # Extract response from OpenAI format
            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message']['content']
                print("📝 Response preview:", content[:200] + "...")
                return result
            else:
                print("⚠️ Unexpected response format")
                return result
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"🚫 Request failed: {e}")
        return None

def streaming_example():
    """
    🌊 STREAMING API: Real-time News Analysis
    
    Watch the analysis happen in real-time!
    """
    print("\n🌊 Starting Streaming News Analysis...")
    
    streaming_prompt = """
    I need real-time market surveillance! 👁️‍🗨️📊
    
    **Streaming Mission:**
    1. 🔥 Find the hottest trending stocks mentioned in today's news
    2. 📱 Search our local documents for any previous analysis on these companies
    3. 💰 Get their current stock prices and volume data
    4. 📊 Create a live tracking dashboard PDF called "live_market_pulse.pdf"
    5. 📧 Send it to user@example.com with subject "⚡ Live Market Pulse Update"
    
    Stream your thoughts as you work - I want to see the analysis unfold!
    """
    
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": streaming_prompt}],
        "stream": True
    }
    
    try:
        print("🌊 Starting streaming request...")
        response = requests.post(
            f"{SERVER_URL}/v1/chat/completions",
            json=payload,
            headers={
                "Content-Type": "application/json", 
                "Authorization": f"Bearer {API_KEY}"
            },
            stream=True,
            timeout=600
        )
        
        if response.status_code == 200:
            print("📡 Streaming response:")
            print("-" * 50)
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str != '[DONE]':
                            try:
                                chunk = json.loads(data_str)
                                if 'choices' in chunk and chunk['choices']:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        print(delta['content'], end='', flush=True)
                            except json.JSONDecodeError:
                                continue
            
            print("\n" + "-" * 50)
            print("✅ Streaming complete!")
            
        else:
            print(f"❌ Streaming error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"🚫 Streaming failed: {e}")

def main():
    """
    🎬 Main example runner
    """
    print("🎉 Welcome to the Agentic-RAG News Analysis Showcase!")
    print("=" * 60)
    
    print("\n🔥 This example will demonstrate:")
    print("• 📰 Intelligent news gathering and analysis")  
    print("• 📊 Stock market data integration")
    print("• 📄 PDF report generation")
    print("• 📧 Automated email delivery")
    print("• 🔍 Document search and cross-referencing")
    print("• 🌊 Both REST and streaming APIs")
    
    print(f"\n⚙️ Server: {SERVER_URL}")
    print("🚀 Starting demonstrations...")
    
    # Run examples
    native_result = native_api_example()
    openai_result = openai_api_example() 
    streaming_example()
    
    print("\n🎊 All examples completed!")
    print("📧 Check your email for the generated reports")
    print("📁 Check for generated PDF files in the server directory")

if __name__ == "__main__":
    main()