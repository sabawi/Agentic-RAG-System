# Agentic RAG System v0.8

A high-performance FastAPI-based agentic RAG (Retrieval-Augmented Generation) system with Ollama LLM integration and comprehensive tool calling capabilities.

## 🚀 Features

### Core Capabilities
- **Ollama LLM Integration** - Local language model processing with streaming support
- **Two-Stage Tool Calling** - Advanced tool calling algorithm with context building
- **Enhanced RAG System** - Retrieval-augmented generation with multiple data sources
- **Async Processing** - High-performance async/await architecture
- **Database Connection Pooling** - Optimized database connectivity
- **Caching Layer** - Redis-compatible caching with fallback

### Available Tools (6 Functions)
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

### Setup
```bash
# Clone the repository
git clone https://github.com/sabawi/agentic-rag-system.git
cd agentic-rag-system

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

## 🔧 Configuration

### Environment Variables
```bash
# Optional .env file
OLLAMA_BASE_URL=http://127.0.0.1:11434
DATABASE_URL=mysql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
```

### Ollama Models
Ensure these models are installed:
```bash
ollama pull llama3.2:3b      # Tool calling model
ollama pull qwen3:8b         # Primary LLM
ollama pull llama3.1:8b      # Alternative model
```

## 🧪 Testing

Comprehensive test suite available in `testing/` directory:

```bash
cd testing/
python test_fastapi.py              # Basic functionality
python test_tool_calling.py         # Tool calling system
python test_comprehensive_news.py   # Enhanced news function
./curl_test.sh                      # Shell-based tests
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

### v0.8 (Current)
- Complete FastAPI migration
- Enhanced news function with full article content
- Updated to ddgs package (from deprecated duckduckgo_search)
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

## 🔗 Links

- **Repository**: https://github.com/sabawi/agentic-rag-system
- **Issues**: https://github.com/sabawi/agentic-rag-system/issues
- **Documentation**: See testing/TestingReadme.md for detailed testing info

## 📞 Support

For questions and support, please open an issue on GitHub or contact the maintainer.

---

**Agentic RAG System v0.8** - High-performance agentic RAG with Ollama integration