# Agentic-RAG Server

An advanced AI-powered server with multi-LLM orchestration, tool calling, document processing, and vision capabilities.

## 🚀 Features

- **Multi-LLM Architecture**: Primary, tool-calling, arbitration, and vision models working together
- **OpenAI-Compatible API**: Full compatibility with OpenAI client libraries
- **Vision Processing**: Image analysis and OCR capabilities with qwen2.5vl:3b
- **Document Intelligence**: FAISS-powered document store with EasyOCR integration
- **Tool Calling System**: Extensible user tools for calendar, email, web scraping, and more
- **Real-time Streaming**: Support for streaming responses
- **Auto-fallback**: Automatic failover between LLM providers

## 📚 Documentation

- **[Installation Guide](INSTALLATION.md)** - Complete setup instructions
- **[Configuration Guide](CONFIGURATION.md)** - System configuration options
- **[API Reference](API.md)** - Endpoint documentation  
- **[User Tools Guide](TOOLS.md)** - Available tools and usage
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   # See INSTALLATION.md for complete setup
   pip install -r requirements.txt
   python test_dependencies.py
   ```

2. **Set up Ollama & Models**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull qwen3:8b
   ollama pull qwen2.5vl:3b
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Install as Service (Recommended)**
   ```bash
   ./install_service.sh
   sudo systemctl start agentic-rag-server
   ```
   
   **Or run manually:**
   ```bash
   ./start_complete.sh
   ```

5. **Test API**
   ```bash
   curl -X POST http://localhost:5000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <your-api-key>" \
     -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello!"}]}'
   ```

## 🏗️ Architecture

### LLM Stack
- **Primary Model**: `qwen3:8b` (Conversation & reasoning)
- **Tool Calling**: `gpt-4o-mini` (Tool orchestration)  
- **Vision Model**: `qwen2.5vl:3b` (Image analysis)
- **Arbitrator**: Configurable (Decision making)

### Core Components
- **FastAPI Server**: OpenAI-compatible REST API
- **Ollama Integration**: Local model serving
- **FAISS Document Store**: Vector-based document retrieval
- **Tool System**: Extensible Python tools
- **Multi-provider**: OpenAI, Gemini, Qwen fallback support

## 🛠️ Available Tools

- **📅 Calendar**: Google Calendar integration
- **📧 Email**: SMTP email sending
- **🌐 Web Scraping**: Content extraction
- **📄 Document Processing**: OCR and text extraction  
- **🗂️ File Operations**: Local file management
- **🖼️ Image Analysis**: Vision processing with OCR
- **🔍 Search**: Web search capabilities

## 🚀 Usage Examples

### Python Client

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="http://localhost:5000/v1"
)

# Text completion
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)

# Image analysis
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": "file:///path/to/image.jpg"}}
        ]
    }]
)

# Tool usage
response = client.chat.completions.create(
    model="gpt-4o", 
    messages=[{"role": "user", "content": "Send an email to john@example.com with subject 'Meeting reminder'"}]
)
```

### Curl Examples

```bash
# Basic completion
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Streaming response
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Write a story"}],
    "stream": true
  }'
```

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
tail -f server_complete.log

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
- **Logs**: Always check `server_complete.log` first

## 🙏 Acknowledgments

- [Ollama](https://ollama.com) for local model serving
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [OpenAI](https://openai.com) for API standards
- [FAISS](https://faiss.ai) for vector search
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for optical character recognition

---

**Quick Links**: [Installation](INSTALLATION.md) | [Configuration](CONFIGURATION.md) | [API Docs](API.md) | [Tools](TOOLS.md) | [Troubleshooting](TROUBLESHOOTING.md)