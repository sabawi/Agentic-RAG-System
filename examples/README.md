# 🚀 Agentic-RAG Server Examples

This directory contains comprehensive examples showcasing the full power of the Agentic-RAG server. These examples demonstrate creative, real-world scenarios using OpenAI-compatible endpoints with sophisticated multi-tool coordination.

## 📁 Examples Overview

### 🌟 [News Analysis Workflow](news_analysis_workflow.py)
**Advanced News Intelligence & Market Analysis**

Demonstrates sophisticated news gathering, stock analysis, and automated reporting:
- 📰 Intelligent news scraping with market impact analysis
- 📊 Real-time stock price integration and trend analysis
- 📄 Automated PDF report generation
- 📧 Email delivery with executive summaries
- 🌊 Both REST and streaming API examples

**Key Features:**
- OpenAI-compatible API for seamless integration
- Creative prompts that trigger multiple tools simultaneously  
- Real-time market intelligence briefings
- Professional-grade analysis suitable for executives

**Usage:**
```bash
python examples/news_analysis_workflow.py
```

### 🔍 [Document Intelligence Explorer](document_intelligence_explorer.py)
**AI-Powered Research Assistant & Knowledge Discovery**

Showcases advanced document search, analysis, and knowledge synthesis:
- 🕵️ Research detective mode with cross-referencing
- 🧠 Knowledge synthesis from multiple document sources
- 🏛️ Document archaeology for hidden insights discovery
- 🎯 Competitive intelligence extraction and analysis

**Key Features:**
- Multi-mode document analysis (Detective, Synthesizer, Archaeology, Intelligence)
- Cross-correlation analysis across document collections
- Automated insight generation with confidence scoring
- Strategic intelligence briefing creation

**Usage:**
```bash
python examples/document_intelligence_explorer.py
```

### 🤖 [Personal Assistant Automator](personal_assistant_automator.py)
**Complete Personal Productivity Automation**

Demonstrates email automation, calendar scheduling, and productivity workflows:
- 📊 Executive daily briefings with market intelligence
- 🎯 Meeting preparation with research automation
- ✈️ Travel planning with business intelligence
- 📈 Weekly strategic review and analysis

**Key Features:**
- Executive-level briefing automation
- Multi-channel distribution (email + calendar)
- Context-aware meeting preparation
- Strategic planning automation

**Usage:**
```bash
python examples/personal_assistant_automator.py
```

### 🎭 [Mega Multi-Tool Orchestrator](mega_multitool_orchestrator.py) 
**ULTIMATE SHOWCASE - Maximum Tool Coordination**

The ultimate demonstration pushing the boundaries of agentic AI:
- 🚀 Ultimate business intelligence with 8+ tools simultaneously
- 💥 Creative disruption scenario modeling
- 🧙‍♂️ Hyper-personalized research assistance
- 🐒 Chaos monkey stress testing for system limits

**Key Features:**
- Maximum tool coordination (8+ tools per request)
- Advanced cross-correlation analysis
- Predictive intelligence generation
- Creative and chaotic testing scenarios
- System stress testing and performance validation

**Usage:**
```bash
python examples/mega_multitool_orchestrator.py
```

## 🛠️ Setup Requirements

### Server Configuration
Ensure your Agentic-RAG server is running:
```bash
./start_complete.sh
```

### Environment Variables
The examples use default configuration:
- **Server URL**: `http://localhost:5000` 
- **API Key**: `test-key` (any value works)
- **Email**: `user@example.com` (change to your email)

### Dependencies
Examples use only standard Python libraries:
- `requests` - HTTP client
- `json` - JSON processing  
- `datetime` - Time/date handling

## 📊 API Endpoint Used

### OpenAI Compatible API
```bash
POST http://localhost:5000/v1/chat/completions  
Content-Type: application/json
Authorization: Bearer test-key

{
  "model": "Agentic-RAG-Model1",
  "messages": [{"role": "user", "content": "Your prompt here"}],
  "stream": false
}
```

**All examples use this OpenAI-compatible format for seamless integration with existing OpenAI client libraries.**

## 🎯 Tools Showcased

The examples demonstrate sophisticated coordination of:

- 📰 **News Scraping** - Real-time news gathering and analysis
- 📚 **Document Search** - Intelligent document retrieval and cross-referencing
- 💹 **Stock Analysis** - Market data integration and trend analysis  
- 📄 **PDF Generation** - Automated report creation with professional formatting
- 📧 **Email Automation** - Smart email composition and delivery
- 🗓️ **Calendar Integration** - Event scheduling and reminder management
- 🔍 **Web Search** - Intelligent information gathering
- 🧮 **Calculations** - Mathematical analysis and data processing
- 🖼️ **Image Processing** - Vision analysis and OCR capabilities
- 📊 **Data Visualization** - Chart and graph generation

## 🌊 Streaming vs Standard Requests

### Streaming (Real-time Response)
```python
payload = {"model": "Agentic-RAG-Model1", "messages": [...], "stream": True}
```
- Watch analysis happen in real-time
- Better for long-running tasks
- Interactive feedback during processing

### Standard (Complete Response)
```python  
payload = {"model": "Agentic-RAG-Model1", "messages": [...], "stream": False}
```
- Get complete response when finished
- Better for automated processing
- Simpler integration patterns

## 🎨 Creative Prompt Patterns

### Multi-Tool Coordination Pattern
```
"I need you to: 1) Search news for X, 2) Check documents for Y, 
3) Get market data for Z, 4) Create report PDF, 5) Email results"
```

### Role-Based Prompting
```
"Act as my [executive assistant/research detective/market analyst] 
and perform [specific multi-step workflow]"
```

### Mission-Style Prompting  
```
"OPERATION: [Name] - Your mission: [detailed multi-step instructions 
with specific deliverables and coordination requirements]"
```

### Context-Rich Scenarios
```
"Imagine you're [specific role] preparing for [specific situation]. 
Use all available tools to [comprehensive workflow description]"
```

## 🧪 Testing & Validation

### Quick Test
```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{"model": "Agentic-RAG-Model1", "messages": [{"role": "user", "content": "Test multi-tool coordination: get news, search documents, create report, send email"}]}'
```

### Health Check
```bash
curl http://localhost:5000/health
```

### Server Logs
```bash
tail -f server_complete.log
```

## 🎯 Expected Outputs

When running these examples, expect:

- 📧 **Email Reports** - Professional briefings sent to your configured email
- 📁 **PDF Files** - Generated reports in the server directory
- 🗓️ **Calendar Events** - Scheduled meetings and reminders
- 📊 **Analysis Results** - Comprehensive market and document intelligence
- 🔍 **Tool Coordination Logs** - Detailed server logs showing tool execution

## ⚠️ Important Notes

### Performance Considerations
- Complex multi-tool requests can take 2-10 minutes
- Streaming provides real-time feedback for long operations
- Use appropriate timeouts (600-900 seconds for complex workflows)

### Configuration
- Update email addresses in examples to your actual email
- Ensure SMTP is configured for email delivery
- Calendar integration requires Google Calendar setup

### System Requirements
- Server running with all tools properly configured
- Sufficient system resources for concurrent tool execution
- Network access for news scraping and market data

## 🎉 Have Fun!

These examples showcase the incredible potential of agentic AI systems. They demonstrate how AI can coordinate multiple tools, synthesize information from various sources, and deliver comprehensive, actionable intelligence.

Experiment with the prompts, modify the workflows, and discover new ways to leverage the power of multi-tool AI coordination!

---

**Quick Links:**
- [Main Documentation](../README.md)
- [Installation Guide](../docs/production/INSTALLATION_GUIDE.md)  
- [User Guide](../docs/production/USER_GUIDE.md)
- [Developer Guide](../docs/production/DEVELOPER_GUIDE.md)