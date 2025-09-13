#!/usr/bin/env python3
"""
🤖 Personal Assistant Automator
===============================

This example showcases email automation, calendar scheduling, and personal productivity
workflows using creative prompts that combine multiple tools. Think of this as your
AI-powered personal assistant that can handle complex, multi-step tasks automatically.
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
SERVER_URL = "http://localhost:5000"
API_KEY = "test-key"

class PersonalAssistantAutomator:
    def __init__(self):
        self.server_url = SERVER_URL
        self.api_key = API_KEY
        
    def executive_briefing_workflow(self):
        """
        📊 Executive Daily Briefing: Automated morning intelligence
        """
        print("📊 Starting Executive Daily Briefing Workflow...")
        
        briefing_prompt = """
        Good morning! Time for your executive daily briefing! ☀️📈
        
        **Operation: "Executive Intelligence Brief"**
        
        As your AI executive assistant, I need to prepare your daily intelligence package:
        
        1. 📰 **Market Intelligence**:
           - Latest tech and business news (focus on AI, fintech, market movers)
           - Identify any news that might impact your investments or decisions
           - Check for any overnight market developments
        
        2. 💹 **Portfolio Watch**:
           - Check current prices for: AAPL, GOOGL, MSFT, NVDA, TSLA
           - Calculate overnight changes and identify any significant moves
           - Flag any stocks with >5% movement for attention
        
        3. 📚 **Document Review**:
           - Search your documents for any mentions of companies in today's news
           - Cross-reference with your previous research and analysis
           - Identify if any of your documented predictions are playing out
        
        4. 📋 **Executive Summary Creation**:
           - Create "executive_daily_brief.pdf" with:
             * Market snapshot and key movers
             * News impact analysis 
             * Document cross-reference insights
             * Priority actions for today
             * Risk/opportunity alerts
        
        5. 📧 **Secure Delivery**:
           - Email the briefing to user@example.com with subject "📊 Executive Daily Brief - [DATE]"
           - Include a concise executive summary in the email body
        
        Make this briefing sharp, actionable, and worthy of a CEO's time!
        """
        
        return self._send_openai_request(briefing_prompt, "executive_briefing")
    
    def meeting_preparation_engine(self):
        """
        🎯 Meeting Preparation Engine: Research and prep automation
        """
        print("🎯 Starting Meeting Preparation Engine...")
        
        meeting_prep_prompt = """
        Transform into my strategic meeting preparation assistant! 🎯📝
        
        **Mission: "Meeting Intelligence Preparation"**
        
        I have an important meeting coming up and need comprehensive preparation:
        
        1. 🔍 **Research Phase**:
           - Search current news for any relevant industry developments
           - Look through documents for any previous analysis or data points
           - Find background information on key meeting topics
        
        2. 📊 **Market Context**:
           - Get current market data for any relevant companies/sectors
           - Identify recent trends that might influence the discussion
           - Flag any financial developments that are pertinent
        
        3. 📋 **Intelligence Dossier**:
           - Create "meeting_preparation_brief.pdf" containing:
             * Executive summary of key talking points
             * Current market context and relevant data
             * Background research findings
             * Potential questions to ask
             * Strategic recommendations
             * Risk factors to consider
        
        4. 📧 **Briefing Delivery**:
           - Email the dossier to user@example.com with subject "🎯 Meeting Preparation Brief - Strategic Intelligence"
           - Include key talking points summary in email body
        
        5. 🗓️ **Calendar Integration**:
           - Add a calendar reminder for 1 hour before the meeting with key points
           - Set title: "Meeting Prep Review - Key Points Ready"
        
        Prepare this like you're briefing a diplomat before a crucial negotiation!
        """
        
        return self._send_openai_request(meeting_prep_prompt, "meeting_preparation")
    
    def travel_planning_coordinator(self):
        """
        ✈️ Travel Planning Coordinator: Complete trip planning automation
        """
        print("✈️ Starting Travel Planning Coordinator...")
        
        travel_prompt = """
        Activate travel coordination protocol! ✈️🌍
        
        **Operation: "Complete Travel Intelligence"**
        
        I need you to become my comprehensive travel planning AI:
        
        1. 🌐 **Destination Intelligence**:
           - Research current news for my destination (assume San Francisco for this demo)
           - Check for any events, conferences, or developments happening there
           - Search documents for any previous travel notes or business contacts
        
        2. 📈 **Business Context**:
           - Find any business opportunities or meetings that could be scheduled
           - Check for relevant companies or people in the destination city
           - Look up current stock prices of major companies headquartered there
        
        3. 📋 **Travel Dossier Creation**:
           - Create "travel_planning_brief.pdf" with:
             * Destination overview and current developments
             * Business opportunities and potential meetings
             * Weather and logistics information
             * Local business context and market intelligence
             * Recommended activities and networking opportunities
        
        4. 📧 **Travel Brief Delivery**:
           - Email brief to user@example.com with subject "✈️ Travel Intelligence Brief - San Francisco"
           - Include executive summary and top 3 recommendations
        
        5. 🗓️ **Calendar Planning**:
           - Add calendar event: "Travel to San Francisco - Review Brief" 
           - Set for tomorrow at 9:00 AM as planning session
        
        Plan this trip like I'm a tech executive making strategic visits!
        """
        
        return self._send_openai_request(travel_prompt, "travel_coordination")
    
    def weekly_review_automator(self):
        """
        📈 Weekly Review Automator: Comprehensive week analysis
        """
        print("📈 Starting Weekly Review Automator...")
        
        weekly_review_prompt = """
        Time for your weekly strategic review! 📈🔍
        
        **Operation: "Weekly Intelligence Synthesis"**
        
        As your AI strategic analyst, compile this week's intelligence:
        
        1. 📊 **Market Performance Review**:
           - Analyze week's performance for major tech stocks
           - Identify significant market movements and catalysts  
           - Compare against previous predictions in documents
        
        2. 📰 **News Impact Analysis**:
           - Review major tech/business news from this week
           - Assess how news impacted market movements
           - Identify emerging trends worth monitoring
        
        3. 📚 **Document Cross-Reference**:
           - Search documents for any insights that proved correct this week
           - Find missed opportunities or areas needing attention
           - Identify research that needs updating
        
        4. 📋 **Strategic Review Report**:
           - Create "weekly_strategic_review.pdf" containing:
             * Week's market summary and key events
             * Performance vs predictions analysis
             * Emerging opportunity identification
             * Strategy adjustments needed
             * Next week's focus areas
        
        5. 📧 **Executive Summary**:
           - Email report to user@example.com with subject "📈 Weekly Strategic Review - Key Insights"
           - Include top 3 insights and next week's priorities
        
        6. 🗓️ **Planning Session**:
           - Schedule calendar event: "Weekly Strategy Review Meeting"
           - Set for Monday 8:00 AM next week
        
        Deliver insights like you're briefing a hedge fund manager!
        """
        
        return self._send_openai_request(weekly_review_prompt, "weekly_review")
    
    def _send_openai_request(self, prompt, workflow_name):
        """Send request using OpenAI compatible endpoint"""
        payload = {
            "model": "Agentic-RAG-Model1",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        
        try:
            print(f"📡 Sending {workflow_name} request...")
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                timeout=600
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {workflow_name} workflow complete!")
                
                if 'choices' in result and result['choices']:
                    content = result['choices'][0]['message']['content']
                    print("📝 Workflow result preview:", content[:250] + "...")
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
    
    def _send_native_request(self, prompt, workflow_name):
        """Send request using native endpoint"""
        payload = {
            "prompt": prompt,
            "model": "qwen3:8b",
            "stream": False,
            "tools": True,
            "conversation_id": f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        try:
            print(f"📡 Sending {workflow_name} request to native API...")
            response = requests.post(
                f"{self.server_url}/llama3_1b/stream",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=600
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {workflow_name} completed!")
                print("🎯 Tools used:", result.get('tools_called', []))
                return result
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"🚫 Request failed: {e}")
            return None

def bash_automation_examples():
    """
    🔧 Bash/cURL examples for quick automation
    """
    print("\n🔧 Quick Automation Examples (Bash/cURL):")
    print("=" * 50)
    
    # Quick email automation
    email_automation = '''
# Quick Email Automation
curl -X POST http://localhost:5000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer test-key" \\
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{
      "role": "user",
      "content": "Check the latest tech news, create a summary PDF called daily_tech_update.pdf, and email it to user@example.com with subject Daily Tech Update"
    }]
  }'
'''
    
    # Calendar + Email workflow
    calendar_workflow = '''
# Calendar + Email Workflow  
curl -X POST http://localhost:5000/llama3_1b/stream \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Schedule a calendar event for tomorrow at 2 PM called Team Meeting, then send an email to user@example.com with meeting agenda and recent project updates from our documents",
    "model": "qwen3:8b",
    "tools": true,
    "stream": false
  }'
'''
    
    # Multi-tool productivity
    productivity_automation = '''
# Complete Productivity Automation
curl -X POST http://localhost:5000/v1/chat/completions \\
  -H "Content-Type: application/json" \\  
  -H "Authorization: Bearer test-key" \\
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{
      "role": "user", 
      "content": "Act as my productivity assistant: 1) Search documents for any TODO items or action items, 2) Check current stock prices for companies mentioned, 3) Create a productivity report PDF, 4) Schedule a calendar review session, 5) Email everything to user@example.com"
    }]
  }'
'''
    
    print("📧 Email Automation:")
    print(email_automation)
    print("\n🗓️ Calendar + Email Workflow:")
    print(calendar_workflow)
    print("\n🎯 Complete Productivity Automation:")
    print(productivity_automation)

def main():
    """
    🚀 Main automation demonstration
    """
    print("🤖 Welcome to the Personal Assistant Automator!")
    print("=" * 60)
    
    print("\n🎯 This showcase demonstrates:")
    print("• 📊 Executive briefing automation with market intelligence")
    print("• 🎯 Meeting preparation with research and context")
    print("• ✈️ Travel planning with business intelligence")  
    print("• 📈 Weekly review automation with strategic analysis")
    print("• 📧 Smart email automation with PDF attachments")
    print("• 🗓️ Calendar integration with automated scheduling")
    print("• 🔗 Multi-tool workflows combining search, analysis, and communication")
    
    assistant = PersonalAssistantAutomator()
    
    print(f"\n⚙️ Server: {SERVER_URL}")
    print("🤖 Starting personal assistant automation workflows...")
    
    # Run automation workflows
    print("\n" + "="*60)
    assistant.executive_briefing_workflow()
    
    print("\n" + "="*60)
    assistant.meeting_preparation_engine()
    
    print("\n" + "="*60) 
    assistant.travel_planning_coordinator()
    
    print("\n" + "="*60)
    assistant.weekly_review_automator()
    
    # Show bash examples
    bash_automation_examples()
    
    print("\n🎊 Personal Assistant Automation Complete!")
    print("📧 Check your email for automated briefings and reports")
    print("🗓️ Check your calendar for scheduled events and reminders")
    print("📁 Check server directory for generated PDF reports")
    print("🤖 Your AI assistant has everything handled!")

if __name__ == "__main__":
    main()