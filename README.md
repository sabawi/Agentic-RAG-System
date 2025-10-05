# Agentic-RAG Server v1.0.2.99

An advanced AI-powered server with multi-LLM orchestration, tool calling, document processing, vision capabilities, intelligent email management, and **extensible plugin system**.

[![Version](https://img.shields.io/badge/version-1.0.2.99-blue)](https://github.com/sabawi/Agentic-RAG-System/releases/tag/v1.0.2.99)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Installation](https://img.shields.io/badge/installation-automated-brightgreen)](install.sh)

## 🚀 Features

- **🔌 NEW: Plugin System**: Create custom LLM tools in 5 minutes - just 2 files (YAML + Python)
- **🚀 Intelligent Email Management**: Advanced email retrieval and optimization with 84% context reduction
- **Multi-LLM Architecture**: Primary, tool-calling, arbitration, and vision models working together
- **OpenAI-Compatible API**: Full compatibility with OpenAI client libraries
- **Vision Processing**: Image analysis and OCR capabilities with qwen2.5vl:3b
- **Document Intelligence**: FAISS-powered document store with EasyOCR integration
- **Tool Calling System**: Extensible user tools for calendar, email, web scraping, and more
- **Real-time Streaming**: Support for streaming responses
- **Auto-fallback**: Automatic failover between LLM providers
- **HTML Content Optimization**: Revolutionary HTML-to-text conversion with formatting preservation

## 📚 Documentation

### Production Documentation (V1.0)
- **[Installation Guide](docs/production/INSTALLATION_GUIDE.md)** - Automated installation system
- **[Administrator Guide](docs/production/ADMINISTRATOR_GUIDE.md)** - System administration and maintenance
- **[User Guide](docs/production/USER_GUIDE.md)** - API usage and features
- **[Developer Guide](docs/production/DEVELOPER_GUIDE.md)** - Development and architecture

### Quick Reference
- **[Main Documentation Hub](docs/README.md)** - Central navigation and overview
- **[News Sources Configuration](docs/NEWS_SOURCES_CONFIGURATION.md)** - Customize news sources without code changes

## 🚀 Quick Start

### Automated Installation (Recommended)
```bash
# Clone the repository
git clone https://github.com/sabawi/Agentic-RAG-System.git
cd Agentic-RAG-System

# Run the automated installer
./install.sh

# Start the server
./start_complete.sh
```

### Manual Installation
```bash
# See docs/production/INSTALLATION_GUIDE.md for complete setup
pip install -r requirements.txt
python fastapi_server_complete.py
```

## ⭐ What's New in V1.0.2.87

### 🚀 Major Enhancement: HTML Email Optimization System
- **84% Context Reduction**: Revolutionary email processing from 37,000 → 6,000 tokens
- **Advanced HTML-to-Text Conversion**: Preserves formatting while removing noise
- **Multi-Provider Email Support**: Gmail, Outlook, Yahoo, iCloud, Exchange, IMAP
- **Smart Content Selection**: Prioritizes plain text, converts HTML when necessary
- **Performance Breakthrough**: Sub-second email processing with maintained quality

### 🔧 System Improvements
- **Centralized Version Management**: Single source of truth for version tracking
- **Enhanced Security Hooks**: Advanced credential detection with environment variable support
- **Version Detection Fix**: Accurate upgrade progress messages (fixed "1.0.2.5 → 1.0.2.5" bug)
- **Configuration Management**: Improved config validation and error handling

## ⭐ What's New in V1.0.2.1

### 🔧 Dependency Hotfix
- **Fixed PDF Generator Tool** - Added missing reportlab dependency
- **Fixed Google Calendar Integration** - Added missing google-auth dependencies
- **Enhanced Requirements** - Updated requirements.txt for fresh installations

## ⭐ What's New in V1.0.2.0

### 🚀 Major Features
- **Automated Installation System** - One-command setup with comprehensive verification
- **Production Documentation** - Complete administrator, user, and developer guides
- **Enhanced Architecture** - Modular design with proper separation of concerns
- **Comprehensive Testing** - Full test coverage and verification systems
- **Professional Deployment** - Production-ready configuration and monitoring

### 📈 V1.0 Achievements
- ✅ Complete project reorganization (47 → 3 production guides)
- ✅ Automated installation script with system dependencies
- ✅ Cross-platform support (Linux/macOS)
- ✅ Comprehensive verification and testing
- ✅ Professional documentation structure
- ✅ Production-ready deployment

## 🧪 API Testing

Once installed, test the API:
```bash
# Test basic connectivity
curl http://localhost:5000/health

# Test chat completion
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Agentic-RAG-Model1", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## 🏗️ Architecture

### LLM Stack
- **Primary Model**: `qwen3:8b` (Local Ollama - conversation & reasoning)
- **Tool Calling**: `gpt-4o-mini` (OpenAI API - tool orchestration)*  
- **Vision Model**: `qwen2.5vl:3b` (Local Ollama - image analysis)
- **Arbitrator**: Configurable (Decision making)

*\* Tool calling requires OpenAI API key. See installation guide for setup.*

### Available Models
- **Agentic-RAG-Model1**: Primary agentic model with full tool access
- **Agentic-RAG-Model2**: Enhanced model for complex reasoning tasks

The system automatically handles multi-model orchestration internally, using local Ollama models for conversation and cloud models for specialized tool calling when needed.

### Core Components
- **FastAPI Server**: OpenAI-compatible REST API
- **Ollama Integration**: Local model serving
- **FAISS Document Store**: Vector-based document retrieval
- **Tool System**: Extensible Python tools
- **Multi-provider**: OpenAI, Gemini, Qwen fallback support

## 🛠️ Available Tools

- **📅 Calendar**: Google Calendar integration
- **📧 Email Retrieval**: 🚀 NEW: Advanced email retrieval with HTML optimization (Gmail, Outlook, Yahoo, iCloud)
- **📧 Email Sending**: Professional SMTP email sending with attachments
- **🌐 Web Scraping**: Content extraction and analysis
- **📄 Document Processing**: OCR and text extraction with FAISS indexing
- **🗂️ File Operations**: Local file management and processing
- **🖼️ Image Analysis**: Vision processing with OCR capabilities
- **🔍 Search**: Web search and academic paper retrieval
- **📊 Financial Tools**: Stock analysis and market data retrieval
- **📰 News Analysis**: Real-time news gathering and summarization

## 🏆 Competitive Advantages

| Feature | **Agentic-RAG-System v1.0** | **LangChain** | **LlamaIndex** | **Haystack** |
|---------|------------------------------|---------------|----------------|--------------|
| **Multi-Model Orchestration** | 🟢 Built-in arbitrator + multi-LLM routing | ⚪ Manual routing/dev-built | ⚪ Index-focused | ⚪ Single-LLM default |
| **Autonomous Tool Planning** | 🟢 19-tool system + GPT-4o orchestration | 🟢 ReAct/agent patterns | ⚪ Limited | ⚪ Static pipelines |
| **Production-Ready Setup** | 🟢 Automated install.sh + deployment | ⚪ Dev assembly required | ⚪ Dev assembly required | 🟢 Deployment guidance |
| **OpenAI API Compatibility** | 🟢 Full compatibility (drop-in replacement) | ⚪ SDK/API only | ⚪ SDK/API only | ⚪ API & tooling |
| **Multimodal RAG** | 🟢 Vision/OCR + multimodal built-in | ⚪ Glue code required | ⚪ Some loaders | ⚪ Limited multimodal |
| **Real-time Document Processing** | 🟢 Background scanning + auto-indexing | ⚪ Custom implementation | ⚪ Custom implementation | ⚪ Pipeline-based |
| **Built-in Monitoring** | 🟢 Arbitrator validation + integrity checks | ⚪ Needs LangSmith/3rd party | ⚪ Limited eval hooks | ⚪ Some Studio monitoring |
| **Enterprise Ready** | ⚪ Foundations (logging) - hardening recommended | ⚪ Dev responsibility | ⚪ Not core | ⚪ Limited enterprise features |

**Key Differentiators:**
- ✅ **Zero-Config Agentic Behavior**: Works out-of-the-box with autonomous tool selection
- ✅ **Revolutionary Email Optimization**: 84% context reduction with HTML-to-text conversion
- ✅ **Hybrid Local+Cloud**: Best of both worlds - privacy + power
- ✅ **True OpenAI Drop-in**: Existing OpenAI code works immediately
- ✅ **Production Focus**: From prototype to production in minutes
- ✅ **Intelligent Content Processing**: Advanced HTML optimization preserves meaning while reducing noise

## 🚀 Impressive Demo Examples

Experience the power of autonomous AI agents! These examples showcase real agentic behavior where the AI automatically selects and uses the right tools.

### 🌟 Start Simple

```bash
# Get latest news with web search
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "What is the latest news as of now?"}]
  }'
```

### 🎓 Academic Research

```bash
# AI automatically searches academic papers and summarizes findings
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Search for the latest academic papers on Transformer enhancements in AI and summarize the key findings for me"}]
  }'
```

### 📊 Financial Analysis & Visualization

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:5000/v1", api_key="not-required")

# AI performs comprehensive stock analysis with charts and investment recommendations
response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{"role": "user", "content": "Using the provided research tool, look up available company and financial data on AMZN stock then:\n1.  Plot the stock chart for the last year and highlight percent change\n    \n2.  Perform full and thorough analysis on it's potential for growth and profit, and make reasoned recommendations whether to Buy, Hold, or Sell its stock for the next 6 months to 2 years investment horizon.\n    \n3.  In your conclusion, state clearly your final recommendation and why."}]
)
```

### 💹 Comprehensive Investment Analysis

```bash
# AI performs deep financial research and provides investment recommendations
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Using the provided research tool, look up available company and financial data on MRNA, AMGN, JNJ stocks and perform full and thorough analysis on its potential for growth and profit, and make reasoned recommendations whether to Buy, Hold, or Sell its stock for the next 6 months to 2 years investment horizon. In your conclusion, state clearly your final recommendation and why."}]
  }'
```

### 📊 Statistical & Mathematical Visualizations

```python
# AI creates advanced statistical visualizations with annotations
from openai import OpenAI

client = OpenAI(base_url="http://localhost:5000/v1", api_key="not-required")

response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{"role": "user", "content": "What is the difference between normal distribution and binomial distribution. Plot both distributions side by side and add annotation and segmentation of probabilities through background colors"}]
)
```

### 📈 Mathematical Function Plotting

```python
# AI generates mathematical function plots with proper scaling and labels
from openai import OpenAI

client = OpenAI(base_url="http://localhost:5000/v1", api_key="not-required")

response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{"role": "user", "content": "Create a Plot for the equation y=3x³-2x²-10x+10"}]
)
```

### 🔍 Smart Document Search

```python
# AI searches through your local documents intelligently
response = client.chat.completions.create(
    model="Agentic-RAG-Model1", 
    messages=[{"role": "user", "content": "Find documents about server configuration and summarize the key security settings I should know about"}]
)
```

### ✈️ Travel Planning

```python
# AI searches flights, compares prices, provides booking links
response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{"role": "user", "content": "Find flights from New York to London for next month, compare prices from different airlines, and show me the best options"}]
)
```

### 📧 Smart Email Management & Communication

```python
# 🚀 NEW: Advanced Email Retrieval with HTML Optimization
response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{"role": "user", "content": "Summarize my last 5 emails from Gmail and highlight any urgent items"}]
)

# AI composes and sends professional emails
response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{"role": "user", "content": "Send a professional email to sarah@company.example about scheduling a project review meeting next week. Include availability options and meeting agenda."}]
)
```

### 📊 Email Analytics & Processing

```bash
# AI analyzes email patterns and provides insights
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Find all unread emails from work about the quarterly review and create a summary report"}]
  }'
```

### 📅 Calendar Integration

```python
# AI manages your calendar intelligently  
response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{"role": "user", "content": "Check my calendar for next week and schedule a 2-hour team planning meeting when everyone is free. Send calendar invites to the team."}]
)
```

### 🖼️ Image Analysis & OCR

```python
# AI analyzes images and extracts information
response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{
        "role": "user", 
        "content": [
            {"type": "text", "text": "Analyze this document image and extract all the key information into a structured summary"},
            {"type": "image_url", {"image_url": {"url": "file:///path/to/document.jpg"}}}
        ]
    }]
)
```

### 👤 AI-Powered Age Analysis

```bash
# AI analyzes faces and estimates age with remarkable accuracy
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Analyse this image and Guess the age of this person (no description, just guess the age only)"},
        {"type": "image_url", {"image_url": {"url": "file:///path/to/selfie.jpg"}}}
      ]
    }]
  }'
```

### 🧮 Code Execution & Analysis

```python
# AI writes and executes code to solve problems
response = client.chat.completions.create(
    model="Agentic-RAG-Model2",
    messages=[{"role": "user", "content": "Calculate the optimal portfolio allocation for these 5 stocks based on historical data, run a Monte Carlo simulation, and create a risk analysis report"}]
)
```

### 📊 Mathematical Visualization

```bash
# AI creates sophisticated mathematical plots and visualizations
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "plot typical power curve and typical S-curve side by side"}]
  }'
```

### 🎯 Custom Mathematical Functions

```python
# AI plots complex mathematical functions with automatic analysis
response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{"role": "user", "content": "plot y = 500/(1+e^-0.3*(x-200))"}]
)
```

## 🎯 What Makes This Special

**🤖 Autonomous Agent Behavior**: The AI decides which tools to use and chains them together automatically
- No manual tool specification required
- Intelligent task decomposition
- Multi-step reasoning and execution

**🔗 Tool Chaining**: Watch the AI use multiple tools in sequence:
1. Search for recent papers → Analyze findings → Summarize insights
2. Get stock data → Perform analysis → Create visualizations → Generate report
3. Search documents → Extract relevant info → Compose professional response

**🧠 Context Awareness**: The AI maintains context across tool calls and provides coherent final answers

## ⚙️ System Requirements

- **OS**: Linux (Ubuntu 20.04+)
- **RAM**: 16GB+ (8GB minimum)
- **Storage**: 50GB+ for models
- **Python**: 3.11+
- **Docker**: Optional for containerized deployment

## 📊 Monitoring & Logs

### Service Mode (Recommended)
```bash
# View real-time service logs
sudo journalctl -u agentic-rag-server -f

# View recent logs
sudo journalctl -u agentic-rag-server -n 100

# Check service status
sudo systemctl status agentic-rag-server

# Health check
curl http://localhost:5000/health
```

### Manual Mode
```bash
# Server logs
tail -f logs/server_complete.log

# Ollama service
journalctl -u ollama -f
```

### Service Management
```bash
# Start/stop/restart service
sudo systemctl start agentic-rag-server
sudo systemctl stop agentic-rag-server  
sudo systemctl restart agentic-rag-server

# Install/uninstall service
./install_service.sh
./uninstall_service.sh
```

## 🔒 Security

- Store API keys in `.env` file (never commit)
- Run behind reverse proxy in production
- Implement proper authentication
- Restrict network access appropriately

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Test changes (`python test_dependencies.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📝 Recent Updates

### 2025-09-28 - HTML Email Optimization & Version Management v1.0.2.87
**🚀 MAJOR: Revolutionary Email Processing System**

- **HTML Email Optimization System**:
  - 84% context reduction: 37,000 → 6,000 tokens for email processing
  - Advanced HTML-to-text conversion preserving links and formatting
  - Multi-provider email support: Gmail, Outlook, Yahoo, iCloud, Exchange, IMAP
  - Smart content prioritization: plain text preferred, HTML converted when needed
  - Sub-second processing with maintained content quality

- **Version Management Enhancement**:
  - Fixed version detection bug in install.sh upgrade messages
  - Centralized version system using version.py as single source of truth
  - Accurate upgrade progress display (fixed "1.0.2.5 → 1.0.2.5" issue)
  - Enhanced security hooks with environment variable detection

- **System Improvements**:
  - Enhanced git pre-commit hooks with intelligent credential detection
  - Improved configuration management and validation
  - Comprehensive documentation updates across all guides

**Impact**: Dramatically improved email productivity, accurate version tracking, enhanced security

### 2025-09-09 - PDF Format Selection & Header/Footer Enhancement
**🎯 ENHANCED: Smart format selection and proper PDF headers/footers**

- **Format Selection Enhancement**:
  - Users can now explicitly request PDF, HTML, or Markdown formats
  - System detects format preferences: "email the PDF format", "send HTML", "markdown version"
  - Falls back gracefully when requested format unavailable
  - Maintains backward compatibility with existing behavior

- **PDF Header/Footer Fix**:
  - Fixed blank date/title display in PDF headers and footers
  - Implemented proper WeasyPrint named strings pattern: `string-set: date-content attr(data-date)`
  - Headers now show: "Generated on Sep. 9th, 2025 - 12:28 PM" 
  - Eliminated CSS warnings: `Unable to compute PageType value`
  - Research-first approach saved development time and resources

**Files Modified:**
- `fastapi_server_complete.py`: Enhanced SMART DECISION logic with format detection (lines 6276-6300)
- `config/pdf_styles.css`: Updated CSS to use WeasyPrint named strings pattern
- `services/pdf_service.py`: Improved date formatting and title capitalization
- Added comprehensive documentation: `docs/PDF_FORMAT_SELECTION.md`, `docs/PDF_HEADER_FOOTER_FIX.md`

**Benefits:**
- ✅ Users control document format selection explicitly  
- ✅ Professional PDF headers with proper date/time formatting
- ✅ Clean CSS with no WeasyPrint warnings
- ✅ Backward compatible - no format preference uses existing logic
- ✅ Clear logging shows format selection decisions

### 2025-09-06 - POST-LLM Email Timeout Fix
**🔧 CRITICAL FIX: Resolved email execution hanging issue**

- **Issue**: POST-LLM email workflows were hanging indefinitely during email execution
- **Root Cause**: Missing timeout protection in deferred auto-execution email calls
- **Solution**: Applied comprehensive 120-second timeout with error handling to ALL email execution paths:
  - POST-LLM Auto-Execution (News Analysis)
  - POST-LLM Auto-Execution (Stock Analysis)  
  - POST-LLM HTML Email workflows
  - POST-LLM Conversation PDF Email exports
  - Regular POST-LLM Email Processing

**Files Modified:**
- `fastapi_server_complete.py`: Added `asyncio.wait_for()` timeout wrappers to 5 email execution paths
- `fastapi_server_complete.py`: Fixed conversation PDF formatting to remove artificial headers
- Enhanced logging for better debugging of email workflow issues

**Benefits:**
- ✅ Prevents infinite hanging during email operations
- ✅ Graceful timeout handling with clear error messages
- ✅ Improved PDF conversation formatting without artificial timestamps
- ✅ Enhanced debugging capabilities with detailed timeout logging

## 🆘 Support

- **Documentation**: Check the guides above
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Logs**: Always check `logs/server_complete.log` first

## 🙏 Acknowledgments

- [Ollama](https://ollama.com) for local model serving
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [OpenAI](https://openai.com) for API standards
- [FAISS](https://faiss.ai) for vector search
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for optical character recognition

---

**Quick Links**: [Installation](docs/production/INSTALLATION_GUIDE.md) | [User Guide](docs/production/USER_GUIDE.md) | [Admin Guide](docs/production/ADMINISTRATOR_GUIDE.md) | [Developer Guide](docs/production/DEVELOPER_GUIDE.md) | [Docs Hub](docs/README.md)