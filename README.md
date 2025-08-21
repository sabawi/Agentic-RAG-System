# Agentic RAG System v0.8.1

A high-performance FastAPI-based agentic RAG (Retrieval-Augmented Generation) system with Ollama LLM integration and comprehensive tool calling capabilities.

## 🚀 Features

### Core Capabilities
- **Ollama LLM Integration** - Local language model processing with streaming support
- **Two-Stage Tool Calling** - Advanced tool calling algorithm with context building
- **Enhanced RAG System** - Retrieval-augmented generation with multiple data sources
- **Async Processing** - High-performance async/await architecture
- **Database Connection Pooling** - Optimized database connectivity
- **Caching Layer** - Redis-compatible caching with fallback

### Available Tools (11 Functions)
1. **get_the_secret_tool** - System date/time retrieval
2. **get_news_summaries** - Enhanced news with full article content extraction
3. **search_web** - DuckDuckGo web search with content extraction
4. **lookup_website** - Enhanced website & PDF content extraction (trafilatura-based)
   - **HTML Pages**: Clean content extraction from any webpage
   - **PDF Documents**: Complete text extraction from all pages
   - **arXiv Papers**: Perfect for academic papers (HTML & PDF versions)
   - **Smart Truncation**: Handles large documents intelligently
5. **wikipedia_query** - Wikipedia information retrieval
6. **get_stock_and_company_data** - Financial data and analysis

### User-Defined Tools (5 Additional Functions)
7. **calculator** - Advanced mathematical calculations and analysis
8. **stock_analyzer** - Comprehensive financial analysis and stock evaluation
9. **google_calendar_scheduler** - Calendar management and event scheduling
10. **sandboxed_executor** - Secure code execution and file operations
11. **secure_email_sender** - Professional email sending with attachments
    - **Multi-Provider Support**: Gmail, Outlook, Custom SMTP, Sendmail
    - **Security Features**: Environment-based credentials, TLS encryption
    - **Attachment Support**: File attachments with validation (25MB limit)
    - **Professional Features**: CC/BCC, priority settings, HTML/plain text

### Technical Stack
- **FastAPI** - Modern async web framework
- **Ollama** - Local LLM processing
- **aiomysql** - Async database connectivity
- **trafilatura** - Advanced web content & PDF extraction  
- **BeautifulSoup** + **Selenium** - Web scraping (fallback)
- **newspaper3k** - Article content extraction
- **ddgs** - DuckDuckGo search integration
- **PyPDF2** - PDF document processing
- **yfinance** - Financial data
- **Wikipedia-API** - Wikipedia integration

## 📁 Project Structure

```
flaskserver/
├── fastapi_server_complete.py    # Main FastAPI server
├── start_complete_server.sh      # Server startup script
├── setup_fastapi.sh              # Environment setup
├── requirements.txt              # Python dependencies
├── RAG_helper.py                 # RAG processing utilities
├── text_chunker.py               # Text processing and chunking
├── webcrawler.py                 # Web crawling utilities
├── prompts/                      # System prompts
│   └── system_prompts.json
├── user_tools/                   # User-defined tools system
│   ├── base_user_tool.py         # Base class for user tools
│   ├── secure_email_sender.py    # Email sending tool
│   ├── sandboxed_executor.py     # Code execution tool
│   ├── stock_analyzer.py         # Financial analysis tool
│   └── google_calendar_scheduler.py # Calendar management tool
├── testing/                      # Comprehensive test suite
│   ├── TestingReadme.md          # Testing documentation
│   └── test_*.py                 # Individual test files
└── venv_fastapi/                 # Virtual environment
```

## 🛠 Installation

### Prerequisites
- Python 3.12+
- Ollama service running
- MySQL/MariaDB (optional)
- System tools: `jq`, `bc` (for testing framework)

### Setup
```bash
# Clone the repository
git clone https://github.com/sabawi/agentic-rag-system.git
cd agentic-rag-system

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install jq bc

# Setup virtual environment and dependencies
./setup_fastapi.sh

# Start the server
./start_complete_server.sh
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv_fastapi
source venv_fastapi/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
python3 fastapi_server_complete.py
```

## 🚀 Usage

### Server Endpoints
- **Base URL**: `http://localhost:5000`
- **API Docs**: `http://localhost:5000/docs`
- **Health Check**: `http://localhost:5000/health`

### Key Endpoints
- `POST /llama3_1b/prompt` - Simple Ollama prompts
- `POST /llama3_1b/stream` - Streaming with tools
- `GET /retrieve_system_prompts` - Available system prompts
- `GET /ollama/models` - Available Ollama models

### Example Requests

**News Analysis:**
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Look up the latest news about AI developments",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "system": "You are a helpful assistant."
  }'
```

**Academic Paper Analysis:**
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain this paper in details: URL: https://arxiv.org/pdf/2501.00139v2.pdf",
    "model": "llama3.2:3b",
    "toolsInUse": true,
    "system": "You are a helpful assistant."
  }'
```

**Email with Attachment:**
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a summary of today'\''s tech news and email it to manager@company.com with high priority",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "system": "You are a helpful assistant."
  }'
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional .env file
OLLAMA_BASE_URL=http://127.0.0.1:11434
DATABASE_URL=mysql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379

# Email Configuration (for secure_email_sender tool)
GMAIL_SENDER_EMAIL=your-agent@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
OUTLOOK_SENDER_EMAIL=your-agent@outlook.com
OUTLOOK_APP_PASSWORD=your-outlook-app-password
```

### LLM Configuration (config/llm_config.yaml)

**⚠️ IMPORTANT LIMITATION v0.8**: OpenAI models can only be used for tool calling, NOT as primary LLM.

The system has an architectural limitation where:
- **Tool Calling**: Supports both Ollama and OpenAI models ✅
- **Primary LLM**: Only supports Ollama models ❌ (hardcoded execution path)

**Supported Configuration**:
```yaml
llm:
  primary:
    type: ollama          # ✅ REQUIRED: Must be 'ollama'
    config:
      model: llama3.2:3b  # Any local Ollama model
  tool_calling:
    type: openai          # ✅ SUPPORTED: Can be 'openai' or 'ollama'
    config:
      model: gpt-4o-mini  # OpenAI model for superior tool calling
```

**Why this limitation exists**: The primary LLM execution path (line 3493 in fastapi_server_complete.py) is hardcoded to use `ServerConfig.OLLAMA_URL`, while tool calling properly uses the LLM Manager abstraction that supports multiple providers.

### Ollama Models
Ensure these models are installed:
```bash
ollama pull llama3.2:3b      # Tool calling model  
ollama pull qwen3:8b         # Primary LLM
ollama pull llama3.1:8b      # Alternative model
```

## 🧪 Testing & Development

Comprehensive testing and development tools available in `testing/` directory:

### Quick Health Check
```bash
cd testing/
./quick_health_check.sh            # Fast system verification
```

### Comprehensive Testing
```bash
./comprehensive_test_suite.sh       # Full system test suite
./test_embedding_service.sh         # Document processing & search tests
./test_api_endpoints.sh             # All API endpoints with curl examples
```

### Legacy Python Tests
```bash
python test_fastapi.py              # Basic functionality
python test_tool_calling.py         # Tool calling system
python test_comprehensive_news.py   # Enhanced news function
```

See `testing/TestingReadme.md` for detailed testing documentation.

## 📊 Performance Features

- **Async Processing** - Non-blocking request handling
- **Connection Pooling** - Optimized database connections
- **Streaming Responses** - Real-time response streaming
- **Timeout Management** - Robust timeout handling
- **Race Condition Prevention** - Proper async synchronization
- **Enhanced Content Extraction** - Full article content vs. headlines only

## 🔄 Migration from Flask

This system represents a complete migration from the original Flask implementation with:
- ✅ 100% endpoint compatibility
- ✅ Enhanced performance through async processing
- ✅ Improved error handling and timeout management
- ✅ Updated dependencies and modern Python practices
- ✅ Comprehensive testing coverage

## 📈 Version History

### v0.8.1 (Current)
- **📚 Complete Developer Documentation** - Comprehensive API reference with 400+ curl examples
- **🧪 Advanced Testing Framework** - 4 specialized test suites covering all endpoints
- **🔍 Embedding Service Debug Guide** - Deep troubleshooting for document processing
- **⚡ Performance Bug Fixes** - Fixed time variable errors and parallel tool execution
- **🛠️ Troubleshooting Guide** - Complete issue diagnosis and resolution procedures
- **📋 100% Endpoint Coverage** - All 32 endpoints documented and tested
- **🎯 Quick Health Checks** - Fast system verification tools

### v0.8.0 (Previous)
- Complete FastAPI migration
- Enhanced news function with full article content  
- Updated to ddgs package (from deprecated duckduckgo_search)
- **User-Defined Tools System** - Extensible tool architecture
- **Secure Email Tool** - Professional email sending with attachments
- **Sandboxed Code Execution** - Safe code execution environment
- **Nuclear Multi-Tool Enforcement** - Prevents lazy single-tool behavior
- Comprehensive testing suite
- Proper project organization

### Previous Versions
- v0.1-0.7: Flask-based implementations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📚 Documentation

### Developer Resources
- **[Developer API Reference](DEVELOPER_API_REFERENCE.md)** - Complete API documentation with curl examples
- **[Embedding Service Debug Guide](EMBEDDING_SERVICE_DEBUG_GUIDE.md)** - Document processing troubleshooting
- **[Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions
- **[Testing Documentation](testing/TestingReadme.md)** - Comprehensive testing information

### Architecture Documentation  
- **[System Architecture](SYSTEM_ARCHITECTURE.md)** - Technical architecture overview
- **[Implementation Guide](IMPLEMENTATION_GUIDE.md)** - Development implementation details
- **[Claude Memory](CLAUDE.md)** - Project instructions and system memory

## 🔗 Links

- **Repository**: https://github.com/sabawi/agentic-rag-system
- **Issues**: https://github.com/sabawi/agentic-rag-system/issues

## 📞 Support

For questions and support, please open an issue on GitHub or contact the maintainer.

---

**Agentic RAG System v0.8.1** - High-performance agentic RAG with Ollama integration