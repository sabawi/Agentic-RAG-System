#!/usr/bin/env python3
"""
🔍 Document Intelligence Explorer
=================================

This example showcases advanced document search, analysis, and knowledge discovery.
Demonstrates how the Agentic-RAG server can act as your personal research assistant,
diving deep into your document collection to find connections and insights.
"""

import requests
import json
from datetime import datetime

# Configuration
SERVER_URL = "http://localhost:5000"
API_KEY = "test-key"

class DocumentIntelligenceExplorer:
    def __init__(self):
        self.server_url = SERVER_URL
        self.api_key = API_KEY
        
    def research_detective_mode(self):
        """
        🕵️ Research Detective: Find connections across documents
        """
        print("🔍 Starting Research Detective Mode...")
        
        detective_prompt = """
        I need you to be my digital research detective! 🕵️‍♂️🔍
        
        **Case File: "The Hidden Connections"**
        
        Your mission, should you choose to accept it:
        
        1. 📚 Search through ALL available documents for any mentions of:
           - Artificial Intelligence developments
           - Market trends or predictions
           - Technology company analysis
           - Investment recommendations
           
        2. 🧩 Cross-reference findings to identify:
           - Recurring themes or patterns
           - Contradictory information that needs investigation
           - Companies or topics mentioned in multiple documents
           - Time-sensitive insights that are still relevant
           
        3. 🎯 Create an intelligence dossier called "research_intelligence_brief.pdf" containing:
           - Executive summary of key discoveries
           - Document source mapping (which docs contain what info)
           - Connection matrix (how different findings relate)
           - Confidence ratings for each insight
           - Recommended follow-up research areas
           
        4. 📧 Deliver this classified report to user@example.com with subject "🕵️ Research Intelligence Brief - Classified"
        
        Be thorough but smart - I want to know not just WHAT you found, but WHY it matters!
        """
        
        return self._send_request(detective_prompt, "research_detective")
    
    def knowledge_synthesizer_mode(self):
        """
        🧠 Knowledge Synthesizer: Combine multiple sources into insights
        """
        print("🧠 Starting Knowledge Synthesizer Mode...")
        
        synthesizer_prompt = """
        Transform into my personal knowledge synthesizer! 🧠✨
        
        **Operation: Deep Knowledge Fusion**
        
        I need you to perform advanced knowledge synthesis:
        
        1. 📖 Scan our document repository for information about:
           - Business strategies or methodologies
           - Technical implementations or architectures
           - Research findings or data analysis
           - Historical patterns or case studies
           
        2. 🔗 Create knowledge connections by:
           - Identifying complementary information across different sources
           - Finding gaps where information is missing or incomplete  
           - Spotting outdated information that needs updating
           - Discovering novel insights from combining separate findings
           
        3. 📊 Generate a comprehensive knowledge map in "knowledge_synthesis_report.pdf":
           - Visual representation of information clusters
           - Source credibility and recency analysis
           - Knowledge confidence scoring
           - Synthesis insights (new conclusions from combined data)
           - Research pathway recommendations
           
        4. 🎤 Create an executive briefing and email to user@example.com with subject "🧠 Knowledge Synthesis Complete - Strategic Insights"
        
        Think like a strategic analyst - connect dots that others miss!
        """
        
        return self._send_request(synthesizer_prompt, "knowledge_synthesizer")
    
    def document_archaeology_mode(self):
        """
        🏛️ Document Archaeology: Uncover hidden gems in your documents
        """
        print("🏛️ Starting Document Archaeology Mode...")
        
        archaeology_prompt = """
        Time for some digital archaeology! 🏛️⚡
        
        **Expedition: "Lost Knowledge Recovery"**
        
        Channel your inner Indiana Jones and help me discover:
        
        1. 💎 Search for hidden gems in documents:
           - Unique insights that might be overlooked
           - Data points that could be valuable today
           - Predictions or forecasts we can verify against current reality
           - Methodologies or approaches worth revisiting
           
        2. 📜 Perform historical analysis:
           - Timeline of when different documents were created
           - Evolution of ideas or strategies over time
           - What worked vs what didn't (based on document outcomes)
           - Lessons learned that are still applicable
           
        3. 🗺️ Create an archaeological report "document_archaeology_findings.pdf":
           - Discovery catalog with significance ratings
           - Historical timeline of knowledge evolution
           - Validation status (which old insights proved correct)
           - Treasure map of most valuable findings
           - Recommendations for what to excavate deeper
           
        4. 📮 Send your expedition report to user@example.com with subject "🏛️ Archaeological Expedition Complete - Ancient Wisdom Recovered"
        
        Think like you're uncovering lost civilizations - what secrets do these documents hold?
        """
        
        return self._send_request(archaeology_prompt, "document_archaeology")
    
    def competitive_intelligence_mode(self):
        """
        🎯 Competitive Intelligence: Market and competitor analysis from documents
        """
        print("🎯 Starting Competitive Intelligence Mode...")
        
        intelligence_prompt = """
        Activate competitive intelligence protocol! 🎯🔍
        
        **Mission: "Market Intelligence Gathering"**
        
        Your strategic intelligence objectives:
        
        1. 🏢 Search documents for competitive intelligence:
           - Company analysis or competitor information
           - Market positioning strategies
           - Pricing or business model insights
           - Strengths/weaknesses assessments
           - Industry trend analysis
           
        2. 📈 Cross-reference with current market data:
           - Look up current stock prices for mentioned companies
           - Check recent news for validation of document insights
           - Identify opportunities or threats mentioned in documents
           
        3. 🎪 Create strategic intelligence report "competitive_intelligence_briefing.pdf":
           - Competitive landscape mapping
           - Market opportunity assessment
           - Threat analysis matrix
           - Strategic recommendations based on document insights
           - Intelligence confidence levels and source reliability
           
        4. 🚀 Rush this strategic briefing to user@example.com with subject "🎯 CONFIDENTIAL: Competitive Intelligence Briefing"
        
        Approach this like a professional intelligence analyst - actionable insights are key!
        """
        
        return self._send_request(intelligence_prompt, "competitive_intelligence")
    
    def _send_request(self, prompt, mode_name):
        """Send request to the agentic server"""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        
        try:
            print(f"📡 Sending {mode_name} request...")
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
                print(f"✅ {mode_name} analysis complete!")
                
                if 'choices' in result and result['choices']:
                    content = result['choices'][0]['message']['content']
                    print("📝 Analysis preview:", content[:300] + "...")
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

def curl_examples():
    """
    🌟 Raw cURL examples for quick testing
    """
    print("\n🌟 cURL Examples for Document Intelligence:")
    print("=" * 50)
    
    # Simple document search
    simple_search = '''
curl -X POST http://localhost:5000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer test-key" \\
  -d '{
    "model": "gpt-4o",
    "messages": [{
      "role": "user", 
      "content": "Search our documents for any mentions of machine learning or AI. Create a summary of findings and email it to user@example.com with the subject 'AI Research Summary'"
    }]
  }'
'''
    
    # Advanced document analysis
    advanced_analysis = '''
curl -X POST http://localhost:5000/llama3_1b/stream \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "I need a comprehensive analysis! Search all documents for business strategies, extract key insights, cross-reference with current market data, create a strategic report PDF called business_intelligence.pdf, and email it to user@example.com",
    "model": "qwen3:8b",
    "tools": true,
    "stream": false
  }'
'''
    
    print("📋 Simple Document Search:")
    print(simple_search)
    print("\n📊 Advanced Document Analysis:")
    print(advanced_analysis)

def main():
    """
    🚀 Main demonstration runner
    """
    print("🔍 Welcome to the Document Intelligence Explorer!")
    print("=" * 60)
    
    print("\n🎯 This demo showcases:")
    print("• 🕵️ Advanced document search and cross-referencing")
    print("• 🧠 Knowledge synthesis from multiple sources")  
    print("• 🏛️ Discovery of hidden insights in document archives")
    print("• 🎯 Competitive intelligence extraction")
    print("• 📊 Automatic report generation with email delivery")
    print("• 🔗 Multi-tool workflows combining search, analysis, and communication")
    
    explorer = DocumentIntelligenceExplorer()
    
    print(f"\n⚙️ Server: {SERVER_URL}")
    print("🔍 Starting document intelligence operations...")
    
    # Run different intelligence modes
    print("\n" + "="*60)
    explorer.research_detective_mode()
    
    print("\n" + "="*60) 
    explorer.knowledge_synthesizer_mode()
    
    print("\n" + "="*60)
    explorer.document_archaeology_mode()
    
    print("\n" + "="*60)
    explorer.competitive_intelligence_mode()
    
    # Show cURL examples
    curl_examples()
    
    print("\n🎊 Document Intelligence Exploration Complete!")
    print("📧 Check your email for intelligence briefings")
    print("📁 Check server directory for generated analysis reports")
    print("🔍 Your documents have revealed their secrets!")

if __name__ == "__main__":
    main()