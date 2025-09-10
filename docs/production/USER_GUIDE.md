# Agentic RAG System - Complete User Guide

## 1. INTRODUCTION & OVERVIEW

The Agentic RAG System is a high-performance AI assistant that combines local language models with intelligent tool calling capabilities. This system provides you with a powerful AI agent that can:

- **Answer questions** using advanced language models
- **Search the web** and extract information from websites
- **Process documents** and provide intelligent search across your files
- **Send emails** with attachments and professional formatting
- **Execute code** safely in a sandboxed environment
- **Analyze financial data** and create visualizations
- **Manage calendar events** and schedule appointments

### Key Features

- **Local Processing**: Runs entirely on your hardware with Ollama integration
- **Tool Integration**: 11+ specialized tools for different tasks
- **Document Management**: Advanced RAG system with semantic search
- **Email Capabilities**: Professional email sending with multiple providers
- **Real-time Streaming**: Live responses as the AI processes your requests
- **OpenAI Compatible API**: Works with existing OpenAI-compatible applications

### What Makes This System Special

- **Privacy First**: Your data stays on your machine
- **Multi-Tool Intelligence**: Can use multiple tools in sequence to solve complex tasks
- **Document Understanding**: Reads and understands your documents for intelligent answers
- **Professional Communication**: Sends emails and creates reports automatically
- **Extensible**: Add your own custom tools and capabilities

## 2. GETTING STARTED

### System Requirements

**Minimum Requirements:**
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 50GB+ free space for models
- **Network**: Internet connection for initial setup

**Recommended Setup:**
- **RAM**: 16GB+ for optimal performance
- **GPU**: NVIDIA GPU with CUDA support (optional but faster)
- **Storage**: SSD storage for better model loading times

### Quick Installation

1. **Install System Dependencies:**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    git curl wget build-essential \
    tesseract-ocr tesseract-ocr-eng \
    postfix mailutils sqlite3
```

2. **Clone and Setup:**
```bash
git clone <repository-url>
cd agentic-rag-server
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Install Ollama:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
```

4. **Download AI Models:**
```bash
ollama pull qwen3:8b          # Main conversation model
ollama pull qwen2.5vl:3b      # Vision processing
ollama pull mxbai-embed-large # Document search
```

5. **Start the Server:**
```bash
./start_complete.sh
```

The server will be available at `http://localhost:5000`

### Basic Usage Test

Test that everything is working:

```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello! What can you help me with today?",
    "model": "qwen3:8b",
    "toolsInUse": false,
    "stream": false
  }'
```

You should receive a friendly response from the AI.

## 3. CORE FEATURES

### Available AI Tools

Your AI assistant has access to these specialized tools:

#### Information & Research Tools
1. **get_the_secret_tool** - Get current date and time
2. **get_news_summaries** - Get latest news with full article content
3. **search_web** - Search the web using DuckDuckGo
4. **lookup_website** - Extract content from websites and PDFs
5. **wikipedia_query** - Search and retrieve Wikipedia information

#### Communication & Productivity Tools
6. **secure_email_sender** - Send professional emails with attachments
7. **google_calendar_scheduler** - Manage calendar events and appointments

#### Analysis & Computing Tools
8. **calculator** - Advanced mathematical calculations
9. **stock_analyzer** - Financial analysis and stock evaluation
10. **sandboxed_executor** - Safe code execution and file operations
11. **get_stock_and_company_data** - Financial data retrieval

### Multi-Tool Intelligence

The system can use multiple tools in sequence to solve complex tasks:

**Example**: "Research the latest AI developments, create a summary report, and email it to my manager"

The AI will:
1. Use `search_web` to find recent AI news
2. Use `lookup_website` to get full article details
3. Use `sandboxed_executor` to create a formatted report
4. Use `secure_email_sender` to send it to your manager

### Conversation Flow

1. **You ask a question** through the API
2. **AI analyzes** your request to determine which tools are needed
3. **Tools execute** in the background (web searches, calculations, etc.)
4. **AI synthesizes** the results into a coherent response
5. **You receive** a complete answer with all the information gathered

## 4. API USAGE

### Basic API Endpoints

#### Main Conversation Endpoint
```bash
POST /llama3_1b/stream
```

**Basic Request:**
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Your question here",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

**Parameters:**
- `prompt`: Your question or request
- `model`: AI model to use (e.g., "qwen3:8b")
- `toolsInUse`: Enable tool calling (true/false)
- `stream`: Stream responses in real-time (true/false)
- `system`: Optional system prompt to customize AI behavior

#### OpenAI Compatible API

For applications expecting OpenAI API format:

```bash
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "What is the weather like today?"}
    ]
  }'
```

#### Available Models

Get list of available models:
```bash
curl "http://localhost:5000/v1/models"
curl "http://localhost:5000/ollama/models"
```

### Example Use Cases

#### 1. Web Research
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Find the latest news about electric vehicles and summarize the key developments",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

#### 2. Document Analysis
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze this research paper and explain the methodology: https://arxiv.org/pdf/2501.00139v2.pdf",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

#### 3. Email Communication
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Send a professional email to john@company.com about our project meeting tomorrow at 2 PM, include agenda items",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

#### 4. Financial Analysis
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze Apple stock performance over the last 30 days and provide investment insights",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

#### 5. Code Execution
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python script that calculates compound interest and run it with principal=1000, rate=5%, time=10 years",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

#### 6. Real-time Streaming
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing concepts",
    "model": "qwen3:8b",
    "toolsInUse": false,
    "stream": true
  }'
```

## 5. CONFIGURATION

### Environment Setup

Create a `.env` file in your server directory:

```bash
# AI Model Configuration
OLLAMA_BASE_URL=http://127.0.0.1:11434

# Email Configuration (for email tools)
GMAIL_SENDER_EMAIL=your-agent@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
OUTLOOK_SENDER_EMAIL=your-agent@outlook.com
OUTLOOK_APP_PASSWORD=your-outlook-app-password

# Optional: Custom SMTP
CUSTOM_SMTP_SERVER=smtp.yourcompany.com
CUSTOM_SMTP_PORT=587
CUSTOM_SENDER_EMAIL=agent@yourcompany.com
CUSTOM_SMTP_PASSWORD=your-smtp-password

# Optional: Cloud API Keys
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### LLM Configuration

Edit `config/llm_config.yaml` to customize AI models:

```yaml
llm:
  primary:
    type: ollama
    config:
      model: qwen3:8b        # Main conversation model
      base_url: http://127.0.0.1:11434
      
  tool_calling:
    type: openai           # Can be 'openai' or 'ollama'
    config:
      model: gpt-4o-mini   # Tool orchestration model
      api_key: ${OPENAI_API_KEY}
      
  image_processing:
    type: ollama
    config:
      model: qwen2.5vl:3b  # Vision analysis model
      base_url: http://127.0.0.1:11434
```

### Email Provider Setup

#### Gmail Setup
1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account Settings → Security → App Passwords
3. Generate app password for "Mail" application
4. Use the 16-character password in your environment variables

#### Outlook Setup
1. Enable 2-Factor Authentication on Microsoft account
2. Go to Security Settings → App Passwords
3. Generate app password for email application
4. Add to your environment variables

#### Custom SMTP
Configure any SMTP server by setting the custom SMTP environment variables.

### System Customization

#### Custom System Prompts
Customize AI behavior by editing these files:
- `primary_model_system_prompt.txt` - Main conversation behavior
- `pre_tool_model_system_prompt.txt` - Tool calling behavior
- `config/image_to_text_system_prompt.txt` - Vision processing behavior

#### Model Selection
Choose models based on your hardware:

**For 16GB+ RAM:**
- Primary: `qwen3:8b` or `llama3.1:8b`
- Vision: `qwen2.5vl:3b`
- Embedding: `mxbai-embed-large`

**For 8-12GB RAM:**
- Primary: `qwen3:3b` or `llama3.2:3b`
- Vision: `qwen2.5vl:1.5b`
- Embedding: `mxbai-embed-large`

## 6. DOCUMENT MANAGEMENT

### Document Processing System

The system includes a powerful document processing engine that can:
- Index your documents for intelligent search
- Extract text from PDFs, Word docs, images (OCR)
- Provide semantic search across all your files
- Remember document content for future questions

### Setting Up Document Management

#### 1. Index Your Documents

Index a directory of documents:
```bash
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/your/documents",
    "recursive": true
  }'
```

#### 2. Search Your Documents

Search for information across all indexed documents:
```bash
curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "project timeline and milestones",
    "max_results": 5
  }'
```

#### 3. Interrogate Specific Documents

Get detailed analysis of a specific document:
```bash
curl -X POST "http://localhost:5000/documents/interrogate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main conclusions in this research?",
    "document_path": "/path/to/research_paper.pdf"
  }'
```

#### 4. Auto-Watch Directories

Set up automatic monitoring of directories for new documents:
```bash
curl -X POST "http://localhost:5000/documents/watch-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/monitor",
    "recursive": true
  }'
```

### Document Format Support

The system supports these document formats:
- **PDF files** (.pdf) - Full text extraction
- **Word documents** (.docx, .doc) - Complete content processing
- **Text files** (.txt, .md, .csv) - Direct text processing
- **Images** (.png, .jpg, .jpeg, .gif) - OCR text extraction
- **Web pages** - When provided as URLs

### Document Search Features

#### Intelligent Format Selection

When multiple versions of the same document exist (PDF, HTML, Markdown), you can specify your preferred format:

**Request PDF format:**
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Email the quarterly report in PDF format to manager@company.com",
    "model": "qwen3:8b",
    "toolsInUse": true
  }'
```

**Request HTML format:**
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Send me the HTML version of the documentation",
    "model": "qwen3:8b",
    "toolsInUse": true
  }'
```

#### Smart Document Discovery

The system automatically:
- Detects document relationships (different formats of same content)
- Prioritizes user-requested formats
- Falls back gracefully when preferred format isn't available
- Logs format selection decisions for transparency

### Document System Status

Check your document system status:
```bash
curl "http://localhost:5000/documents/stats"
```

This shows:
- Number of indexed documents
- Storage usage
- Processing statistics
- Watch directory status

## 7. ADVANCED USAGE

### Custom System Prompts

You can customize the AI's behavior for specific tasks by providing system prompts:

```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze this financial data",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "system": "You are a senior financial analyst. Provide detailed technical analysis with specific recommendations. Always include risk assessment and market context."
  }'
```

### Complex Multi-Step Workflows

The AI can handle complex workflows involving multiple tools:

**Research → Analysis → Communication:**
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Research the latest developments in renewable energy, create a comprehensive market analysis report with charts, and email it to the board of directors with high priority",
    "model": "qwen3:8b",
    "toolsInUse": true
  }'
```

This will:
1. Search for renewable energy news
2. Analyze market data and trends
3. Create visualizations and charts
4. Generate a professional report
5. Send it via email with high priority

### Image Analysis

Process and analyze images:

```bash
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Analyze this chart and provide insights"},
        {"type": "image_url", {"image_url": {"url": "file:///path/to/chart.png"}}}
      ]
    }]
  }'
```

### Calendar Management

Schedule meetings and manage your calendar:

```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Schedule a team meeting for next Tuesday at 2 PM, invite john@company.com and sarah@company.com, set agenda for project review",
    "model": "qwen3:8b",
    "toolsInUse": true
  }'
```

### Code Generation and Execution

Generate, execute, and test code:

```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python web scraper that extracts product prices from an e-commerce site, include error handling and save results to CSV",
    "model": "qwen3:8b",
    "toolsInUse": true
  }'
```

### Email with Attachments

Send professional emails with file attachments:

```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate a quarterly sales report based on our latest data and email it to stakeholders@company.com with the raw data file attached",
    "model": "qwen3:8b",
    "toolsInUse": true
  }'
```

### Performance Optimization

For better performance:

1. **Use Streaming**: Set `"stream": true` for real-time responses
2. **Disable Tools When Not Needed**: Set `"toolsInUse": false` for simple questions
3. **Choose Appropriate Models**: Use smaller models for simple tasks
4. **Enable GPU**: If available, configure Ollama to use GPU acceleration

## 8. TROUBLESHOOTING

### Quick Diagnostics

If something isn't working, start with these commands:

```bash
# Check if server is running
curl "http://localhost:5000/health"

# Test basic functionality
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, are you working correctly?",
    "model": "qwen3:8b",
    "toolsInUse": false,
    "stream": false
  }'

# Check available models
curl "http://localhost:5000/ollama/models"
```

### Common Issues

#### 1. Server Won't Start

**Problem**: Server fails to start or connection is refused

**Solutions**:
```bash
# Check if already running
ps aux | grep fastapi_server_complete.py

# Stop any existing instances
./stop_complete.sh

# Check port availability
netstat -tlnp | grep :5000

# Start fresh
./start_complete.sh

# Monitor startup logs
tail -f server_complete.log
```

#### 2. Tools Not Working

**Problem**: AI doesn't use tools or tool calls fail

**Solutions**:
```bash
# Check Ollama status
systemctl status ollama

# Restart Ollama if needed
sudo systemctl restart ollama

# Verify models are loaded
ollama list
ollama ps

# Test tool calling with simple request
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What time is it?",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

#### 3. Email Tools Failing

**Problem**: Email sending fails with authentication errors

**Solutions**:
```bash
# Check environment variables
echo $GMAIL_SENDER_EMAIL
echo $GMAIL_APP_PASSWORD

# Set up Gmail app password
# 1. Enable 2FA on Google account
# 2. Generate app password
# 3. Set environment variables

# Test SMTP connection
telnet smtp.gmail.com 587

# Restart server with new credentials
./stop_complete.sh
export GMAIL_SENDER_EMAIL="your-email@gmail.com"
export GMAIL_APP_PASSWORD="your-app-password"
./start_complete.sh
```

#### 4. Document Search Not Working

**Problem**: Document search returns no results

**Solutions**:
```bash
# Check document system status
curl "http://localhost:5000/documents/stats"

# Check if embedding model is loaded
ollama ps | grep embed

# Rebuild document index
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/your/documents/path",
    "force_rebuild": true,
    "recursive": true
  }'
```

#### 5. Memory Issues

**Problem**: System runs out of memory or becomes slow

**Solutions**:
```bash
# Check memory usage
free -h

# Check which models are loaded
ollama ps

# Stop unused models
ollama stop <model_name>

# Limit concurrent models
export OLLAMA_MAX_LOADED_MODELS=2

# Restart services
sudo systemctl restart ollama
./stop_complete.sh
./start_complete.sh
```

#### 6. Web Search Failing

**Problem**: Web search and website lookup tools not working

**Solutions**:
```bash
# Check internet connectivity
ping google.com
curl -I https://duckduckgo.com

# Test web tools directly
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Search for today'\''s technology news",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'

# Update web scraping dependencies
pip install --upgrade ddgs beautifulsoup4 requests
```

### Performance Issues

#### Slow Response Times

1. **Check system resources**:
```bash
top
iotop
```

2. **Optimize model usage**:
```bash
# Use smaller models for simple tasks
# qwen3:3b instead of qwen3:8b for basic questions
```

3. **Enable GPU acceleration** (if available):
```bash
# Configure Ollama for GPU
export CUDA_VISIBLE_DEVICES=0
sudo systemctl restart ollama
```

#### Memory Leaks

1. **Monitor memory usage**:
```bash
while true; do
  echo "$(date): $(curl -s http://localhost:5000/metrics | jq -r '.memory_usage_mb')MB"
  sleep 60
done
```

2. **Regular restarts** (add to crontab):
```bash
# Daily restart at 3 AM
0 3 * * * cd /home/sabawi/Development/flaskserver && ./stop_complete.sh && ./start_complete.sh
```

### Emergency Recovery

If multiple issues persist:

```bash
# Complete system reset
./stop_complete.sh
sudo systemctl stop ollama
pkill -f fastapi_server_complete.py

# Clean restart
sudo systemctl start ollama
sleep 10
ollama pull qwen3:8b
ollama pull mxbai-embed-large

# Start server
./start_complete.sh

# Verify health
curl "http://localhost:5000/health"
```

### Getting Help

#### Log Analysis

Check logs for specific issues:
```bash
# General errors
grep -i "error\|failed\|exception" server_complete.log | tail -20

# Tool-specific issues  
grep -i "tool.*error\|tool.*failed" server_complete.log | tail -10

# Email issues
grep -i "email\|smtp" server_complete.log | tail -10

# Document processing issues
grep -i "document\|embed\|faiss" server_complete.log | tail -10
```

#### System Information

When reporting issues, collect this information:
```bash
# System info
uname -a
python3 --version
ollama version

# Server status
curl "http://localhost:5000/health" | jq .

# Model status
ollama list
ollama ps

# Environment variables (sanitized)
env | grep -E "(OLLAMA|GMAIL|DATABASE)" | sed 's/=.*PASSWORD.*/=<HIDDEN>/'

# Recent logs
tail -50 server_complete.log
```

### Support Resources

- **Log Files**: Check `server_complete.log` for detailed error messages
- **Health Check**: Run `curl "http://localhost:5000/health"` to verify system status
- **Model Status**: Use `ollama list` and `ollama ps` to check AI models
- **System Resources**: Monitor with `htop`, `free -h`, and `df -h`

---

**This concludes the complete User Guide for the Agentic RAG System. You now have everything you need to effectively use your AI assistant for research, analysis, communication, and automation tasks.**