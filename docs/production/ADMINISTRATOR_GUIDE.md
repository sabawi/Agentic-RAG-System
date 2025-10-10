# Agentic RAG System - Administrator Guide

**Version:** 2.1.87
**Last Updated:** September 28, 2025
**Target Audience:** System Administrators, DevOps Engineers, Production Support
**Latest Update:** HTML Email Content Optimization System

---

## Table of Contents

1. [SYSTEM OVERVIEW](#1-system-overview)
2. [INSTALLATION & SETUP](#2-installation--setup)
3. [CONFIGURATION MANAGEMENT](#3-configuration-management)
4. [SERVICE OPERATIONS](#4-service-operations)
5. [CORE SYSTEM MONITORING](#5-core-system-monitoring)
   - [Logging Management System](#logging-management-system)
6. [EMAIL SYSTEM ADMINISTRATION (A-1)](#6-email-system-administration-a-1)
7. [EMBEDDING SERVICE ADMINISTRATION (A-2)](#7-embedding-service-administration-a-2)
8. [DIRECTORY WATCHING SYSTEM (A-3)](#8-directory-watching-system-a-3)
9. [SECURITY ADMINISTRATION (A-4)](#9-security-administration-a-4)
10. [TROUBLESHOOTING](#10-troubleshooting)
11. [MAINTENANCE PROCEDURES](#11-maintenance-procedures)
12. [PERFORMANCE OPTIMIZATION](#12-performance-optimization)
13. [APPENDICES](#13-appendices)

---

## 1. SYSTEM OVERVIEW

### Architecture Summary

The Agentic RAG System is a production-ready, AI-powered document retrieval and agent system built on:

- **FastAPI Server**: Core application server (port 5000)
- **Ollama Service**: Local LLM hosting (ports 11434/11435)
- **FAISS Vector Store**: High-performance document search
- **SQLite/MySQL**: Metadata and conversation storage
- **Automatic Document Processing**: Real-time directory monitoring

### Key Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Apps   │───▶│  FastAPI Server  │───▶│ Ollama Service  │
│                 │    │    (Port 5000)   │    │ (Port 11434)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Directory Watch │    │  FAISS Index     │    │ LLM Models      │
│ System          │    │  Document Store  │    │ • qwen3:8b      │
│                 │    │                  │    │ • mxbai-embed   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### System Requirements

**Production Environment**:
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: 16GB+ (32GB recommended for large deployments)
- **Storage**: 50GB+ SSD for models and document index
- **CPU**: 8+ cores (16+ for high-performance deployments)
- **GPU**: Optional but recommended (NVIDIA GPU with CUDA support)
- **Network**: Internet access for model downloads and cloud APIs

**Service Dependencies**:
- Python 3.11+
- Ollama service
- SQLite3 or MySQL
- Postfix (for email tools)
- Docker (optional)

---

## 2. INSTALLATION & SETUP

### Prerequisites

#### System Packages Installation

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    git curl wget build-essential \
    tesseract-ocr tesseract-ocr-eng \
    postfix mailutils \
    sqlite3 \
    docker.io docker-compose

# Enable and start services
sudo systemctl enable postfix
sudo systemctl start postfix
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -a -G docker $USER
```

### Core Installation Steps

#### Step 1: Repository Setup

```bash
git clone <repository-url>
cd agentic-rag-server
```

#### Step 2: Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
python tests/test_dependencies.py
```

#### Step 3: Ollama Installation

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Enable as system service
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify installation
ollama --version
```

#### Step 4: Required Models Download

```bash
# Primary conversation model (8GB)
ollama pull qwen3:8b

# Vision processing model (2.3GB) 
ollama pull qwen2.5vl:3b

# Embedding model for RAG (669MB)
ollama pull mxbai-embed-large

# Verify models are installed
ollama list
```

**Expected output:**
```
NAME              ID              SIZE      MODIFIED
mxbai-embed-large abc123def456    669 MB    X minutes ago
qwen2.5vl:3b      def456abc123    2.3 GB    X minutes ago
qwen3:8b          ghi789jkl012    8.0 GB    X minutes ago
```

### Production Service Installation

#### Option A: System Service (Recommended)

```bash
# Make scripts executable
chmod +x install_service.sh uninstall_service.sh

# Install as system service
./install_service.sh
```

**Service Management**:
```bash
# Start service
sudo systemctl start agentic-rag-server

# Stop service  
sudo systemctl stop agentic-rag-server

# Restart service
sudo systemctl restart agentic-rag-server

# Check status
sudo systemctl status agentic-rag-server

# View logs (real-time)
sudo journalctl -u agentic-rag-server -f

# View recent logs
sudo journalctl -u agentic-rag-server -n 50
```

#### Option B: Manual Execution (Development)

```bash
# Start server
./start_complete.sh

# Stop server
./stop_complete.sh
```

---

## 3. CONFIGURATION MANAGEMENT

### Environment Variables Configuration

Create `.env` file with required API keys:

```bash
# Core API Keys
OPENAI_API_KEY=REPLACE_WITH_YOUR_OPENAI_API_KEY

# Optional cloud providers
GOOGLE_API_KEY=REPLACE_WITH_YOUR_GOOGLE_API_KEY
GEMINI_API_KEY=REPLACE_WITH_YOUR_GEMINI_API_KEY

# Email configuration (see Section 8 for security setup)
GMAIL_SENDER_EMAIL=your-agent@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password

# Database configuration (optional - defaults to SQLite)
DATABASE_URL=mysql://user:password@localhost/agentic_rag

# Custom SMTP (optional)
CUSTOM_SMTP_SERVER=smtp.yourcompany.com
CUSTOM_SMTP_PORT=587
CUSTOM_SENDER_EMAIL=agent@yourcompany.com
CUSTOM_SMTP_PASSWORD=your-smtp-password

# Flight Search API Keys (optional - enables real flight data)
AMADEUS_API_KEY=your_amadeus_api_key_here
AMADEUS_API_SECRET=your_amadeus_api_secret_here
SKYSCANNER_API_KEY=your_skyscanner_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
CHROMEDRIVER_PATH=/path/to/chromedriver  # Optional - auto-installs if not set
```

### LLM Configuration

Edit `config/llm_config.yaml`:

```yaml
llm:
  primary:
    type: ollama
    config:
      model: qwen3:8b        # Primary conversation model
      base_url: http://127.0.0.1:11434
      
  tool_calling:
    type: openai
    config:
      model: gpt-4o-mini     # Tool orchestration
      api_key: ${OPENAI_API_KEY}
      
  image_processing:
    type: ollama
    config:
      model: qwen2.5vl:3b    # Vision analysis
      base_url: http://127.0.0.1:11434
      
  embedding:
    type: ollama
    config:
      model: mxbai-embed-large  # Document embeddings
      base_url: http://127.0.0.1:11434
```

### Flight Search Tool Configuration

The flight search tool supports multiple data sources and requires configuration for optimal performance:

```yaml
flight_search:
  enabled: true
  web_scraping:
    enabled: true
    timeout_seconds: 30
    max_results: 10
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  apis:
    # Flight search API providers - Add your API keys via environment variables
    amadeus:
      enabled: false  # Set to true when API key is configured
      api_key: ${AMADEUS_API_KEY}
      api_secret: ${AMADEUS_API_SECRET}
      base_url: "https://test.api.amadeus.com"  # Use "https://api.amadeus.com" for production
    skyscanner:
      enabled: false  # Set to true when API key is configured
      api_key: ${SKYSCANNER_API_KEY}
      base_url: "https://partners.api.skyscanner.net"
    serpapi:
      enabled: false  # Set to true when API key is configured
      api_key: ${SERPAPI_API_KEY}
      base_url: "https://serpapi.com/search.json"
    rapidapi_skyscanner:
      enabled: false  # Set to true when API key is configured
      api_key: ${RAPIDAPI_KEY}
      base_url: "https://skyscanner50.p.rapidapi.com"
      host: "skyscanner50.p.rapidapi.com"
  verification_links:
    # Booking sites always included for verification
    kayak: "https://www.kayak.com/flights"
    expedia: "https://www.expedia.com/Flights-Search"
    google_flights: "https://www.google.com/travel/flights"
    priceline: "https://www.priceline.com/relax/at/flights"
    momondo: "https://www.momondo.com/flight-search"
  chromedriver:
    # ChromeDriver configuration for web scraping fallback
    path: ${CHROMEDRIVER_PATH}  # Optional - auto-installs if not specified
    auto_install: true
    headless: true
    timeout: 30
    window_size: "1920,1080"
```

#### Flight Search API Setup

**Priority Order**: The tool tries API providers in this order:
1. Amadeus API (recommended for production)
2. Skyscanner API (partner access required)
3. SerpAPI (Google Flights data)
4. Web scraping fallback (always available)

**Amadeus API Setup** (Recommended):
1. Visit [Amadeus for Developers](https://developers.amadeus.com/)
2. Create free account and application
3. Set environment variables and enable in config:
   ```bash
   export AMADEUS_API_KEY="your_key"
   export AMADEUS_API_SECRET="your_secret"
   ```
   ```yaml
   amadeus:
     enabled: true
   ```

**SerpAPI Setup** (Google Flights):
1. Visit [SerpAPI](https://serpapi.com/) and create account
2. Set environment variable and enable:
   ```bash
   export SERPAPI_API_KEY="your_key"
   ```
   ```yaml
   serpapi:
     enabled: true
   ```

**Cost Considerations**:
- Amadeus: Free tier (1000 calls/month), then $1/1000 calls
- SerpAPI: Paid service, $50/month for 5000 searches
- Web scraping: Free but slower and less reliable

### System Prompts Customization

Key configuration files:
- `primary_model_system_prompt.txt` - Main conversation model
- `pre_tool_model_system_prompt.txt` - Tool calling orchestration  
- `config/image_to_text_system_prompt.txt` - Vision model instructions
- `config/arbitrator_system_prompt.txt` - Decision arbitration

---

## 4. SERVICE OPERATIONS

### Service Lifecycle Management

#### Starting Services

```bash
# Method 1: Using service scripts
./start_complete.sh

# Method 2: Using systemd (if installed as service)
sudo systemctl start agentic-rag-server

# Method 3: Manual startup sequence
source venv/bin/activate
python fastapi_server_complete.py
```

#### Stopping Services

```bash
# Method 1: Using service scripts
./stop_complete.sh

# Method 2: Using systemd
sudo systemctl stop agentic-rag-server

# Method 3: Emergency stop
pkill -f fastapi_server_complete.py
```

#### Health Checks

```bash
# Basic health check
curl http://localhost:5000/health

# Comprehensive health check
cd testing/
./quick_health_check.sh

# Component-specific checks
./test_embedding_service.sh
./test_api_endpoints.sh
```

### Log Management

#### Key Log Locations

- **Main Server**: `logs/server_complete.log`
- **Ollama Service**: `sudo journalctl -u ollama -f`
- **System Service**: `sudo journalctl -u agentic-rag-server -f`
- **System Logs**: `/var/log/syslog`

#### Log Monitoring Commands

```bash
# Real-time server logs
tail -f logs/server_complete.log

# Filter for errors
grep -i "error\|failed\|exception" logs/server_complete.log

# Monitor tool calling
tail -f logs/server_complete.log | grep -i "tool.*call\|tool.*error"

# Performance monitoring
tail -f logs/server_complete.log | grep -i "timeout\|slow\|memory"

# Embedding service logs
tail -f logs/server_complete.log | grep -i "embed\|faiss\|document"
```

---

## 5. CORE SYSTEM MONITORING

### System Metrics

#### Server Status Endpoints

```bash
# System statistics
curl "http://localhost:5000/documents/stats" | jq .

# Server metrics
curl "http://localhost:5000/metrics" | jq .

# Service health
curl "http://localhost:5000/health"
```

#### Resource Monitoring

```bash
# CPU usage
top -p $(pgrep -f fastapi_server_complete.py)

# Memory detailed analysis
pmap $(pgrep -f fastapi_server_complete.py)

# Disk I/O
iotop -p $(pgrep -f fastapi_server_complete.py)

# Network connections
netstat -tlnp | grep python
```

### Performance Benchmarks

#### Expected Performance Metrics

- **API Response Time**: < 200ms for simple queries
- **Document Search**: < 500ms for complex searches
- **Embedding Generation**: < 100ms per request
- **Memory Usage**: 2-8GB depending on loaded models
- **CPU Usage**: 10-30% idle, up to 100% during processing

#### Performance Testing

```bash
# Basic API test
time curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Document search test
time curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence machine learning",
    "max_results": 5
  }'
```

### Logging Management System

#### Overview

The system provides comprehensive logging management through both API endpoints and a dedicated CLI tool (`./server_logs`). This enables real-time control of logging levels, timing data, and request monitoring without server restarts.

#### Logging Components

- **API Endpoints**: Direct server control via REST calls
- **CLI Tool**: `./server_logs` - User-friendly command interface
- **Persistent Configuration**: Settings survive server restarts
- **Real-time Monitoring**: Live log streaming with color coding

#### Core Logging Commands

```bash
# Quick Status Check
./server_logs status                    # View current logging configuration

# Essential Controls
./server_logs enable                    # Enable logging (INFO level)
./server_logs disable                   # Disable all logging
./server_logs level DEBUG               # Set logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)

# Granular Controls
./server_logs requests on               # Enable HTTP request/response logging
./server_logs timing on                 # Enable performance timing measurements

# Persistence Management
./server_logs save                      # Save current settings as defaults
./server_logs restore                   # Restore persistent settings

# Live Monitoring
./server_logs monitor                   # Real-time colorized log streaming
```

#### Timing Logging Deep Dive

**What Timing Logging Captures:**
- ⏱️ **Request Processing Duration** - Total HTTP request-to-response time
- 🛠️ **Tool Execution Times** - Individual function and operation timing
- 🗄️ **Database Query Times** - SQL operations and FAISS vector searches
- 🌐 **API Call Durations** - External service response times (Ollama, OpenAI)
- 📋 **Background Task Timing** - Scheduled operations like file scanning
- 🧠 **LLM Response Times** - Model inference and generation timing

**Example Timing Log Entries:**
```bash
⏱️ Tool execution took 1.23s
⏱️ Database query completed in 450ms
⏱️ Request processed in 2.1s
⏱️ FAISS search took 89ms
⏱️ LLM generation completed in 3.4s
```

**When to Enable Timing Logging:**
- 🐛 **Performance Debugging** - Identify slow operations and bottlenecks
- 📈 **Production Monitoring** - Track response times and SLA compliance
- ⚡ **Optimization Projects** - Measure improvement impact
- 🔍 **Issue Investigation** - Understand time allocation during problems

#### Live Monitoring Features

**Color-Coded Real-Time Monitoring:**
```bash
./server_logs monitor
```

**Color Coding System:**
- 🔴 **RED** - ERROR messages (critical issues requiring attention)
- 🟡 **YELLOW** - WARNING messages (potential issues to monitor)
- 🔵 **BLUE** - INFO messages (general operational information)
- ⚫ **DEFAULT** - DEBUG messages (detailed debugging information)
- 🟢 **GREEN** - SUCCESS messages (successful operations)

**Advanced Monitoring Techniques:**
```bash
# Monitor specific patterns
tail -f logs/server_complete.log | grep -E "(⏱️|took|duration)" --line-buffered    # Timing only
tail -f logs/server_complete.log | grep -E "(ERROR|CRITICAL)" --line-buffered      # Errors only
tail -f logs/server_complete.log | grep -E "(TOOL|Citation|🔗)" --line-buffered    # Tool activity
```

#### Environment-Specific Configurations

**Production Environment:**
```bash
./server_logs level WARNING             # Appropriate production level
./server_logs requests off              # Reduce log volume
./server_logs timing on                 # Keep performance monitoring
./server_logs save                      # Make settings persistent
```

**Development Environment:**
```bash
./server_logs level DEBUG               # Detailed debugging
./server_logs requests on               # Full request tracking
./server_logs timing on                 # Performance optimization data
./server_logs save                      # Persist development settings
./server_logs monitor                   # Start live monitoring
```

**Emergency Response:**
```bash
./server_logs level CRITICAL            # Only critical errors
./server_logs requests off              # Reduce system load
./server_logs timing off                # Minimal logging overhead
./server_logs disable                   # Emergency: disable all logging
```

#### API Integration

**REST Endpoints for Programmatic Control:**
```bash
# Status Information
curl -X GET "http://localhost:5000/admin/logging/status"

# Enable/Disable Logging
curl -X POST "http://localhost:5000/admin/logging/enable"
curl -X POST "http://localhost:5000/admin/logging/disable"

# Set Logging Level
curl -X POST "http://localhost:5000/admin/logging/level/DEBUG"

# Toggle Features
curl -X POST "http://localhost:5000/admin/logging/requests/toggle"
curl -X POST "http://localhost:5000/admin/logging/timing/toggle"
```

#### Persistent Configuration

**Configuration File:** `config/logging_config.json`

**Example Configuration:**
```json
{
  "enabled": true,
  "level": "INFO",
  "log_requests": false,
  "log_timing": true,
  "saved_at": "2025-09-22T07:42:55.080704",
  "version": "1.0.2.59"
}
```

**Automatic Restoration:**
- Settings automatically restored on server startup
- Integrated with `start_complete.sh` startup script
- No manual intervention required

#### Performance Monitoring Integration

**Continuous Performance Monitoring:**
```bash
# Monitor slow operations (>5 seconds)
while true; do
    SLOW_OPS=$(tail -n 100 logs/server_complete.log | grep -E "took [5-9]\.[0-9]+s|took [0-9]{2,}\.[0-9]+s")
    if [ ! -z "$SLOW_OPS" ]; then
        echo "⚠️ ALERT: Slow operations detected!"
        echo "$SLOW_OPS"
    fi
    sleep 30
done

# Performance correlation with system resources
while true; do
    TIMING_LOGS=$(tail -n 50 logs/server_complete.log | grep "⏱️" | tail -5)
    MEMORY=$(free -m | awk 'NR==2{printf "Memory: %s/%sMB (%.2f%%)", $3,$2,$3*100/$2 }')
    echo "$(date): $MEMORY"
    echo "Recent timing: $TIMING_LOGS"
    sleep 120
done
```

#### Best Practices Summary

1. **Always check status first**: `./server_logs status`
2. **Use appropriate levels for environment** (DEBUG for dev, WARNING for prod)
3. **Enable timing logging for performance monitoring**
4. **Save configurations after changes**: `./server_logs save`
5. **Use live monitoring during investigations**: `./server_logs monitor`
6. **Disable logging only in emergencies** to maintain observability

---

## 6. EMAIL SYSTEM ADMINISTRATION (A-1)

### 🚀 HTML Email Content Optimization System
**Status**: ✅ Production Ready | **Performance**: 84% Context Reduction

#### Overview
The email system provides advanced email retrieval and processing capabilities with major performance optimization achieved through HTML content conversion.

**Key Achievement**: Context size reduced from 37,000 tokens to 6,000 tokens (84% reduction) while maintaining all meaningful content.

#### Architecture Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Email Query   │───▶│  Email Retriever │───▶│ Content Cleaner │
│   Processing    │    │     Tool         │    │   HTML→Text     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Provider Config │    │ Smart Selection  │    │ Clean Context   │
│ • Gmail         │    │ • Plain Text 1st │    │ • No HTML Bloat │
│ • Outlook       │    │ • HTML Convert   │    │ • Links Preserved│
│ • Yahoo/iCloud  │    │ • Format Retain  │    │ • 84% Reduction │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

#### Configuration Management

**1. Email Provider Configuration**
Location: `config/llm_config.yaml`

```yaml
email_integration:
  providers:
    gmail_primary:
      server: "imap.gmail.com"
      port: 993
      username: "${GMAIL_PRIMARY_EMAIL}"
      password: "${GMAIL_PRIMARY_APP_PASSWORD}"
    outlook_personal:
      server: "outlook.office365.com"
      port: 993
      username: "${OUTLOOK_PERSONAL_EMAIL}"
      password: "${OUTLOOK_PERSONAL_PASSWORD}"
    # Additional providers...
```

**2. Environment Variables**
Required for secure credential management:

```bash
# Gmail Configuration
export GMAIL_PRIMARY_EMAIL="user@example.com"
export GMAIL_PRIMARY_APP_PASSWORD="your_app_password_here"

# Outlook Configuration
export OUTLOOK_PERSONAL_EMAIL="user@example.com"
export OUTLOOK_PERSONAL_PASSWORD="your_outlook_password_here"
```

#### Performance Monitoring

**1. Context Size Tracking**
Monitor email processing efficiency:

```bash
# Monitor context sizes in logs
tail -f logs/server_complete.log | grep "CONTEXT SIZE"

# Expected: 6,000-8,000 tokens for typical email queries
# Alert if: >15,000 tokens (potential HTML conversion issue)
```

**2. HTML Conversion Metrics**
Track conversion performance:

```bash
# Check conversion logs
grep "Converted HTML email body" logs/server_complete.log

# Expected format: "1234 chars -> 456 chars" (60%+ reduction)
```

**3. Email Retrieval Performance**
Monitor query processing times:

```bash
# Track email retrieval duration
grep "EMAIL RETRIEVAL SUCCESS" logs/server_complete.log

# Expected: <5 seconds for typical queries
# Alert if: >30 seconds (connection issues)
```

#### Troubleshooting Email Issues

**Problem: High Context Size (>20k tokens)**
```bash
# Check if HTML conversion is working
grep "raw_html" logs/server_complete.log
# Should be: No results (raw_html removed in v1.0.2.87)

# Verify HTML cleaning is active
grep "_html_to_clean_text" logs/server_complete.log
# Should show conversion activity
```

**Problem: Email Content Missing**
```bash
# Check server status
curl -X GET http://localhost:5000/admin/logging/status

# Verify email credentials
python -c "
from utils.email_library_adapter import EmailLibraryAdapter
adapter = EmailLibraryAdapter('config/llm_config.yaml')
print(adapter.list_providers())
"
```

**Problem: Poor Email Summarization**
```bash
# Verify clean text conversion
tail -f logs/server_complete.log | grep "body_content"
# Should show clean, formatted text without HTML tags
```

#### Maintenance Procedures

**1. Test Email System Health**
```bash
# Run email conversion tests
python tests/test_html_email_conversion.py
# Expected: All tests passing with 60%+ size reduction

# Test email retrieval
python tests/test_email_body_fix.py
# Expected: Clean content extraction verified
```

**2. Update Email Credentials**
```bash
# Update environment variables
vi ~/.bashrc  # Add new credentials
source ~/.bashrc

# Restart server to apply changes
./stop_complete.sh && ./start_complete.sh
```

**3. Monitor Performance Metrics**
```bash
# Check daily email processing efficiency
grep "EMAIL RETRIEVAL SUCCESS" logs/server_complete.log | \
  grep "$(date +%Y-%m-%d)" | \
  awk '{print $NF}' | # Extract duration
  sort -n
```

## 7. EMBEDDING SERVICE ADMINISTRATION (A-2)

### Architecture Overview

The embedding service provides semantic search capabilities using:

- **FAISS Vector Index**: High-performance similarity search
- **Ollama Embedding Model**: `mxbai-embed-large` (1024 dimensions)
- **Document Processor**: Handles PDF, DOCX, TXT, MD, HTML, images (OCR)
- **Automatic Directory Watcher**: Real-time document indexing

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Documents     │───▶│  Text Chunker    │───▶│ Embedding Model │
│ (PDF/DOCX/etc.) │    │  (1000 chars)    │    │ (mxbai-embed)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Search Query  │───▶│   Query Vector   │───▶│  FAISS Index    │
│                 │    │   Generation     │    │  (Similarity)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Service Health Monitoring

#### Basic Health Check

```bash
curl "http://localhost:5000/documents/stats"
```

**Healthy Response**:
```json
{
  "total_documents": 156,
  "total_chunks": 2562,
  "index_size_mb": 23.4,
  "embedding_model": "mxbai-embed-large",
  "indexing_status": "idle",
  "last_update": "2025-09-10T11:45:23"
}
```

**Problem Indicators**:
- `total_chunks: 0` - No documents indexed
- `indexing_status: "error"` - Processing failures
- Missing `embedding_model` - Service not initialized

#### Embedding Service Test

```bash
curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test embedding functionality",
    "max_results": 1
  }'
```

### Component Testing

#### Ollama Embedding Model

```bash
# Check if embedding model is loaded
ollama ps

# Expected output:
# NAME                 ID              SIZE      PROCESSOR    UNTIL
# mxbai-embed-large   468836162de7    669 MB    CPU          4 minutes from now

# Test direct embedding generation
curl http://localhost:11434/api/embeddings \
  -d '{
    "model": "mxbai-embed-large",
    "prompt": "test embedding generation"
  }'
```

#### FAISS Index Testing

```bash
# Check index files
ls -la document_store/
# Should show:
# faiss.index          - Main vector index
# metadata.db          - SQLite metadata database
# *.backup.*           - Backup files

# Test index loading
curl "http://localhost:5000/documents/stats" | jq '.index_size_mb'
# Should return a positive number, not 0
```

### Document Processing

#### Test Single File Processing

```bash
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/single/document.pdf",
    "recursive": false
  }'
```

#### Monitor Processing

```bash
# Watch server logs during processing
tail -f logs/server_complete.log | grep -E "(Processing|Embedding|FAISS|document)"
```

**Expected Log Flow**:
```
📄 Processing document: /path/document.pdf
🔍 Extracted 1247 words, created 3 chunks
🧠 Generating embeddings for 3 chunks
✅ Generated 3 embeddings across 1 batches
🗃️ Added 3 vectors to FAISS index
✅ Processing complete: 1 files, 3 chunks indexed
```

### Performance Monitoring

#### Embedding Speed Test

```bash
time curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence machine learning",
    "max_results": 5
  }'
```

**Performance Benchmarks**:
- **Query embedding**: < 0.1 seconds
- **FAISS search**: < 0.05 seconds  
- **Total query time**: < 0.2 seconds

#### Memory Usage Analysis

```bash
# Server memory usage
curl "http://localhost:5000/metrics" | jq '.memory_usage_mb'

# FAISS Index memory: ~1MB per 1000 document chunks
# Embedding Model: ~669MB when loaded
```

### Database Administration

#### SQLite Metadata Inspection

```bash
# Check document counts
sqlite3 document_store/metadata.db "SELECT COUNT(*) FROM chunks;"
sqlite3 document_store/metadata.db "SELECT document_path, chunk_count FROM documents LIMIT 5;"

# Database integrity check
sqlite3 document_store/metadata.db "PRAGMA integrity_check;"

# View schema
sqlite3 document_store/metadata.db ".schema"
```

### Common Issues & Solutions

#### Issue: "Embedding service unhealthy"

**Symptoms**:
- Document search returns errors
- Processing gets stuck
- Log shows embedding restart attempts

**Solutions**:
```bash
# Solution A: Restart Ollama
sudo systemctl restart ollama
ollama pull mxbai-embed-large

# Solution B: Check system resources
free -h  # Ensure sufficient memory
df -h    # Check disk space

# Solution C: Clear embedding cache
rm -rf /tmp/embedding_cache_*
```

#### Issue: Search returns no results

**Solutions**:
```bash
# Lower similarity threshold
curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "similarity_threshold": 0.0, "max_results": 10}'

# Rebuild index if corrupted
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "/your/docs", "force_rebuild": true}'
```

---

## 7. DIRECTORY WATCHING SYSTEM (A-2)

### Overview

The Automatic Directory Watching System provides intelligent, production-ready document indexing with:

- **Startup Scanning**: Automatic directory scan on server start
- **Periodic Scanning**: Background scanning every 60 minutes
- **Smart Change Detection**: MD5 hash + modification time comparison
- **Batch Processing**: Efficient processing of 25 documents per batch
- **Error Recovery**: Graceful handling of failures

### Configuration

#### Configuration File: `watched_directories.json`

```json
{
  "version": "1.0",
  "config": {
    "scan_on_startup": true,
    "batch_size": 25,
    "scan_interval_minutes": 60,
    "auto_watch_enabled": true
  },
  "directories": [
    {
      "path": "/home/sabawi/Documents",
      "recursive": true,
      "enabled": true,
      "description": "Personal documents",
      "added_at": "2025-09-10T10:30:00"
    }
  ],
  "last_scan": "2025-09-10T14:31:06.918360",
  "stats": {
    "total_directories": 1,
    "active_directories": 1,
    "last_config_update": "2025-09-10T14:31:06.918373"
  }
}
```

#### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scan_on_startup` | boolean | `true` | Enable automatic scanning on server startup |
| `batch_size` | integer | `25` | Number of documents to process in each batch |
| `scan_interval_minutes` | integer | `60` | Minutes between periodic scans |
| `auto_watch_enabled` | boolean | `true` | Enable background periodic scanning |

### API Management

#### Directory Management Endpoints

```bash
# Add directory to watch list
curl -X POST "http://localhost:5000/documents/watch-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/documents",
    "recursive": true,
    "description": "Project documentation"
  }'

# Get current watch status
curl "http://localhost:5000/documents/watch-status" | jq .

# Remove directory from watch list
curl -X DELETE "http://localhost:5000/documents/unwatch-directory" \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "/path/to/documents"}'

# Manual directory scan trigger
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/documents",
    "recursive": true,
    "force_rebuild": false
  }'
```

### Operational Flow

#### Startup Sequence

1. **Server Initialization**: FastAPI server starts
2. **Configuration Loading**: Load `watched_directories.json`
3. **FAISS Index Loading**: Load existing vector database
4. **Startup Scan Trigger**: Scan all configured directories
5. **Background Task Start**: Begin periodic scanning loop
6. **Service Ready**: System operational and monitoring

#### Change Detection Logic

```python
# File Processing Decision Tree
if file_not_in_database:
    return True  # New file, needs processing
elif file_hash_changed:
    return True  # Content modified
elif modification_time_changed:
    return True  # File touched/updated
else:
    return False  # File unchanged, skip processing
```

### Monitoring

#### Log Patterns

```bash
# Monitor scanning activity
tail -f logs/server_complete.log | grep -E "(Safe scan|Periodic scan)"

# Startup Scanning
🔍 Safe scan: Starting scan of 2 configured directories
📊 Directory 1: scanned 38 files
✅ Directory 1 complete: 38 scanned, 0 processed
🎉 Safe scan complete: 56 files scanned, 0 files processed

# Periodic Scanning
⏰ Periodic scan starting (interval: 60min)
✅ Periodic scan completed successfully

# Change Detection
🔄 Change detected (hash): filename.txt
📋 New file detected: newfile.pdf
✅ File up-to-date: unchanged.doc
```

#### Performance Metrics

- **Startup Scan**: ~50 files/second
- **Change Detection**: ~100 files/second
- **Embedding Generation**: 25 documents/batch (2-3 seconds per batch)
- **Memory Usage**: 500MB-1GB depending on index size

### Supported File Types

- **Documents**: PDF, DOCX, DOC, RTF, ODT
- **Text Files**: TXT, MD, CSV, JSON, XML
- **Web Files**: HTML, HTM
- **Code Files**: PY, JS, CSS, SQL (configurable)

### Troubleshooting

#### Common Issues

**Issue: "No files processed" when files have changed**
- Check file permissions and accessibility
- Verify metadata database integrity
- Review embedding service health

**Issue: Background scanning not triggering**
- Verify `auto_watch_enabled: true`
- Check server logs for task initialization
- Ensure graceful shutdown/startup cycle

#### Debug Commands

```bash
# Check configuration
cat watched_directories.json

# Monitor scanning activity
tail -f logs/server_complete.log | grep -E "(Safe scan|Periodic scan)"

# Check database records
sqlite3 document_store/metadata.db "SELECT COUNT(*) FROM documents;"

# Verify service health
curl http://localhost:5000/documents/stats
```

---

## 8. SECURITY ADMINISTRATION (A-3)

### Email Security Setup

The Secure Email Sender Tool implements enterprise-grade security measures for AI agent email functionality.

#### Security Features

- **Credential Management**: Environment variables with app-specific passwords
- **Email Validation**: RFC 5322 compliant validation with domain checks
- **Attachment Security**: File type filtering, size limits (25MB), path validation
- **Connection Security**: TLS/SSL encryption with timeout protection

#### Configuration Methods

**Method 1: Environment Variables (Recommended)**

```bash
# Gmail Configuration
export GMAIL_SENDER_EMAIL="your-agent@gmail.com"
export GMAIL_APP_PASSWORD="your-16-char-app-password"

# Outlook Configuration  
export OUTLOOK_SENDER_EMAIL="your-agent@outlook.com"
export OUTLOOK_APP_PASSWORD="your-outlook-app-password"

# Custom SMTP Configuration
export CUSTOM_SMTP_SERVER="smtp.yourcompany.com"
export CUSTOM_SMTP_PORT="587"
export CUSTOM_SENDER_EMAIL="agent@yourcompany.com"
export CUSTOM_SMTP_PASSWORD="your-smtp-password"
```

**Method 2: Configuration File (Optional)**

Create `email_config.json` with restrictive permissions:

```json
{
  "gmail": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-agent@gmail.com",
    "app_password": "your-16-char-app-password"
  },
  "outlook": {
    "smtp_server": "smtp-mail.outlook.com",
    "smtp_port": 587, 
    "sender_email": "your-agent@outlook.com",
    "app_password": "your-outlook-app-password"
  }
}
```

```bash
# Set restrictive permissions
chmod 600 email_config.json
```

#### Getting App Passwords

**Gmail Setup**:
1. Enable 2-Factor Authentication on Google account
2. Go to Google Account Settings → Security → App Passwords
3. Generate app password for "Mail" application
4. Use the 16-character password (spaces removed)

**Outlook Setup**:
1. Enable 2-Factor Authentication on Microsoft account
2. Go to Security Settings → App Passwords
3. Generate app password for email application
4. Use the generated password

#### Security Best Practices

```bash
# Secure credential storage
source /secure/path/email_credentials.env

# Set proper file permissions
chmod 600 email_credentials.env
chmod 600 email_config.json
chmod 700 /secure/path/

# Monitor email sending
tail -f logs/server_complete.log | grep -i "email\|smtp"
```

#### Testing Email Configuration

```bash
# Test email tool functionality
cd user_tools/
python3 secure_email_sender.py

# Test via API
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Send a test email to test@example.com with subject Test Email"}],
    "stream": false
  }'
```

### API Security

#### Authentication

The system supports multiple authentication methods:

```bash
# Bearer token authentication
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"model": "Agentic-RAG-Model1", "messages": [{"role": "user", "content": "Hello"}]}'

# Basic API key validation
# Configure API keys in environment or configuration files
export API_KEYS="key1,key2,key3"
```

#### Network Security

```bash
# Firewall configuration (example for Ubuntu/ufw)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5000/tcp  # FastAPI server (consider restricting to internal network)
sudo ufw deny 11434/tcp  # Ollama (should not be externally accessible)
sudo ufw enable

# Run behind reverse proxy (nginx example)
upstream agentic_rag {
    server localhost:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://agentic_rag;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Data Security

#### Database Security

```bash
# SQLite security
chmod 600 document_store/metadata.db
chmod 600 document_store/faiss.index

# MySQL security (if used)
# Use dedicated database user with minimal privileges
CREATE USER 'agentic_rag'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON agentic_rag.* TO 'agentic_rag'@'localhost';
FLUSH PRIVILEGES;
```

#### Document Security

```bash
# Secure document directories
chmod 755 /path/to/documents/
chmod 644 /path/to/documents/*

# Monitor document access
tail -f logs/server_complete.log | grep -E "(Processing|document)"
```

---

## 9. TROUBLESHOOTING

### Quick Diagnosis

**Start with the quick health check:**
```bash
cd testing/
./quick_health_check.sh
```

**For detailed diagnosis:**
```bash
./comprehensive_test_suite.sh
./test_embedding_service.sh
./test_api_endpoints.sh
```

### Common Issues & Solutions

#### 1. Server Not Starting

**Symptoms**:
- `curl: (7) Failed to connect to localhost port 5000`
- Server process exits immediately
- Port already in use errors

**Diagnosis**:
```bash
# Check if server is already running
ps aux | grep fastapi_server_complete.py

# Check port availability
netstat -tlnp | grep :5000

# Check server logs
tail -f logs/server_complete.log
```

**Solutions**:

**A. Kill existing processes:**
```bash
./stop_complete.sh
# Or manually:
pkill -f fastapi_server_complete.py
```

**B. Check port conflicts:**
```bash
# If port 5000 is taken, change in fastapi_server_complete.py:
# port = int(os.environ.get("PORT", 5001))  # Change to 5001
```

**C. Check dependencies:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Ollama Service Issues

**Symptoms**:
- Tool calling returns errors
- "Ollama service not available" messages
- Model runner crashes

**Diagnosis**:
```bash
# Check Ollama service status
systemctl status ollama

# Check direct Ollama API
curl http://localhost:11434/api/tags

# Check loaded models
ollama ps

# Check available models
ollama list
```

**Solutions**:

**A. Restart Ollama service:**
```bash
sudo systemctl restart ollama
# Sometimes need daemon reload first:
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

**B. Fix model issues:**
```bash
# Pull required models
ollama pull qwen3:8b
ollama pull mxbai-embed-large

# Check model integrity
ollama run qwen3:8b "Hello"
```

**C. Memory issues:**
```bash
# Check system memory
free -h

# If low memory, stop other models
ollama stop <unused_model>
```

#### 3. Tool Calling Failures

**Symptoms**:
- Tools not being called when expected
- "Tool calling exception" in logs
- Single tool behavior instead of multi-tool

**Diagnosis**:
```bash
# Test basic tool calling
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "What is the current date and time?"}],
    "stream": false
  }'

# Check server logs for tool errors
tail -f logs/server_complete.log | grep -i tool
```

**Solutions**:

**A. Check tool model system prompt:**
```bash
# Verify pre_tool_model_system_prompt.txt exists and is readable
cat pre_tool_model_system_prompt.txt | head -10
```

**B. Restart with proper tool loading:**
```bash
./stop_complete.sh
./start_complete.sh

# Check tool initialization in logs
tail -f logs/server_complete.log | grep -i "tool.*loaded"
```

#### 4. Document Processing Failures

**Symptoms**:
- Files not being indexed
- Processing hangs on certain documents
- OCR or PDF extraction errors

**Diagnosis**:
```bash
# Test specific file processing
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/problematic/document.pdf",
    "recursive": false
  }'

# Check document processing logs
tail -f logs/server_complete.log | grep -i "processing\|document\|pdf"
```

**Solutions**:

**A. Check file permissions:**
```bash
ls -la /path/to/documents/
chmod 644 /path/to/documents/*
```

**B. Install missing dependencies:**
```bash
# For PDF processing
pip install PyPDF2

# For Word documents  
pip install python-docx

# For OCR (images)
sudo apt-get install tesseract-ocr
pip install pytesseract
```

#### 5. Email Tool Issues

**Symptoms**:
- Email sending fails
- Authentication errors
- Attachment problems

**Solutions**:

**A. Fix email credentials:**
```bash
# Set proper environment variables
export GMAIL_SENDER_EMAIL="your-agent@gmail.com"
export GMAIL_APP_PASSWORD="your-16-char-app-password"

# Restart server to pick up new env vars
./stop_complete.sh && ./start_complete.sh
```

**B. Check email provider settings:**
```bash
# For Gmail, ensure 2FA is enabled and app password is created
# Test SMTP connectivity
telnet smtp.gmail.com 587
```

### Emergency Procedures

#### Complete System Reset

If multiple issues persist:

```bash
# 1. Stop everything
./stop_complete.sh
sudo systemctl stop ollama

# 2. Clean up processes
pkill -f fastapi_server_complete.py
pkill -f ollama

# 3. Restart Ollama
sudo systemctl daemon-reload
sudo systemctl start ollama

# 4. Wait for Ollama to be ready
sleep 10

# 5. Pull required models
ollama pull qwen3:8b
ollama pull mxbai-embed-large

# 6. Restart server
./start_complete.sh

# 7. Verify health
./testing/quick_health_check.sh
```

#### Data Recovery

If document index is corrupted:

```bash
# 1. Backup current index
cp document_store/faiss.index document_store/faiss.index.backup
cp document_store/metadata.db document_store/metadata.db.backup

# 2. Restore from backup if available
ls document_store/*.backup*

# 3. Or rebuild from scratch
rm document_store/faiss.index document_store/metadata.db
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/your/documents/root",
    "recursive": true,
    "force_rebuild": true
  }'
```

---

## 10. MAINTENANCE PROCEDURES

### Regular Maintenance Tasks

#### Daily Maintenance

```bash
#!/bin/bash
echo "🔍 Daily System Check - $(date)"
echo "============================================"

# Check service status
echo -n "Server status: "
if curl -s "http://localhost:5000/health" > /dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Failed"
fi

# Check embedding service
echo -n "Embedding service status: "
if curl -s "http://localhost:5000/documents/stats" > /dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Failed"
fi

# Check disk space
echo -n "Disk usage: "
df -h / | tail -1 | awk '{print $5}'

# Check memory usage
echo -n "Memory usage: "
free | grep Mem | awk '{printf "%.1f%%\n", ($3/$2) * 100.0}'

echo "============================================"
```

#### Weekly Maintenance

```bash
#!/bin/bash
echo "📊 Weekly System Maintenance - $(date)"

# Backup document store
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp document_store/faiss.index "$BACKUP_DIR/"
cp document_store/metadata.db "$BACKUP_DIR/"
cp watched_directories.json "$BACKUP_DIR/"
echo "✅ Backup created: $BACKUP_DIR"

# Clean old logs (keep last 30 days)
find . -name "*.log" -type f -mtime +30 -delete
echo "✅ Old logs cleaned"

# Update system packages (if automated updates are desired)
# sudo apt update && sudo apt upgrade -y
echo "✅ System packages checked"

# Restart services for fresh start
./stop_complete.sh
sleep 5
./start_complete.sh
echo "✅ Services restarted"
```

#### Monthly Maintenance

```bash
#!/bin/bash
echo "🔧 Monthly System Maintenance - $(date)"

# Deep database cleanup
sqlite3 document_store/metadata.db "VACUUM;"
echo "✅ Database vacuumed"

# Rebuild FAISS index for optimization
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/your/document/root",
    "recursive": true,
    "force_rebuild": true
  }'
echo "✅ FAISS index optimized"

# Clean temporary files
rm -rf /tmp/embedding_cache_*
rm -rf /tmp/ollama_*
echo "✅ Temporary files cleaned"

# Generate system health report
./testing/comprehensive_test_suite.sh > "reports/health_$(date +%Y%m%d).txt"
echo "✅ Health report generated"
```

### Backup Procedures

#### Automated Backup Script

```bash
#!/bin/bash
BACKUP_ROOT="/var/backups/agentic-rag"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$DATE"

mkdir -p "$BACKUP_DIR"

# Core data files
cp document_store/faiss.index "$BACKUP_DIR/"
cp document_store/metadata.db "$BACKUP_DIR/"
cp watched_directories.json "$BACKUP_DIR/"

# Configuration files
cp .env "$BACKUP_DIR/" 2>/dev/null || echo "No .env file"
cp config/llm_config.yaml "$BACKUP_DIR/"
cp -r config/ "$BACKUP_DIR/"

# System state
curl -s "http://localhost:5000/documents/stats" > "$BACKUP_DIR/system_stats.json"
curl -s "http://localhost:5000/metrics" > "$BACKUP_DIR/system_metrics.json"

# Compress backup
tar -czf "$BACKUP_ROOT/agentic_rag_$DATE.tar.gz" -C "$BACKUP_ROOT" "$DATE"
rm -rf "$BACKUP_DIR"

# Clean old backups (keep 30 days)
find "$BACKUP_ROOT" -name "*.tar.gz" -type f -mtime +30 -delete

echo "✅ Backup completed: agentic_rag_$DATE.tar.gz"
```

#### Backup Restoration

```bash
#!/bin/bash
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

echo "🔄 Restoring from backup: $BACKUP_FILE"

# Stop services
./stop_complete.sh

# Extract backup
TEMP_DIR="/tmp/restore_$$"
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Restore files
RESTORE_DIR=$(ls "$TEMP_DIR")
cp "$TEMP_DIR/$RESTORE_DIR/faiss.index" document_store/
cp "$TEMP_DIR/$RESTORE_DIR/metadata.db" document_store/
cp "$TEMP_DIR/$RESTORE_DIR/watched_directories.json" .
cp "$TEMP_DIR/$RESTORE_DIR/llm_config.yaml" config/

# Clean up
rm -rf "$TEMP_DIR"

# Start services
./start_complete.sh

echo "✅ Restoration completed"
```

### Log Rotation

#### Setup Log Rotation

Create `/etc/logrotate.d/agentic-rag`:

```bash
/path/to/agentic-rag/logs/server_complete.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 user group
    postrotate
        /bin/kill -USR1 $(cat /var/run/agentic-rag.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
```

---

## 11. PERFORMANCE OPTIMIZATION

### System-Level Optimization

#### CPU Optimization

```bash
# Set CPU governor to performance mode
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Configure CPU affinity for better performance
taskset -c 0-3 python fastapi_server_complete.py  # Use specific CPU cores
```

#### Memory Optimization

```bash
# Increase shared memory for FAISS operations
echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf

# Optimize memory cache behavior
echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf
echo 'vm.swappiness=10' >> /etc/sysctl.conf

# Apply changes
sysctl -p
```

#### Disk I/O Optimization

```bash
# Use SSD storage for document store
# Mount with optimal options
mount -o noatime,data=ordered /dev/ssd /path/to/document_store/

# Configure I/O scheduler for SSD
echo 'noop' > /sys/block/sda/queue/scheduler  # For SSD
echo 'deadline' > /sys/block/sda/queue/scheduler  # For HDD
```

### Application-Level Optimization

#### Ollama Optimization

```bash
# Configure Ollama environment variables
export OLLAMA_NUM_PARALLEL=4          # Match CPU core count
export OLLAMA_MAX_LOADED_MODELS=3     # Limit concurrent models
export OLLAMA_KEEP_ALIVE="5m"         # Keep models loaded for 5 minutes

# For GPU acceleration
export CUDA_VISIBLE_DEVICES=0         # Use specific GPU
export OLLAMA_GPU_LAYERS=40           # Offload layers to GPU

# Restart Ollama to apply settings
sudo systemctl restart ollama
```

#### FAISS Index Optimization

For large document collections (>10k documents), consider advanced FAISS configurations:

```python
# In document_interrogator.py, use optimized index
import faiss

# For large datasets, use IVF index
nlist = 100  # Number of clusters
quantizer = faiss.IndexFlatL2(dimension)
index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)

# Train the index
index.train(training_vectors)
```

#### Document Processing Optimization

```json
{
  "batch_size": 25,                    // Increase for better throughput (max ~50)
  "scan_interval_minutes": 60,         // Adjust based on change frequency
  "max_files_per_scan": 1000,          // Safety limit for large directories
  "chunk_size": 1000,                  // Optimal for most documents
  "chunk_overlap": 100                 // Balance between context and performance
}
```

### Network Optimization

#### Reverse Proxy Configuration (Nginx)

```nginx
upstream agentic_rag {
    server localhost:5000;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Optimize client body size for large documents
    client_max_body_size 100M;
    
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml;
    
    # Optimize proxy settings
    location / {
        proxy_pass http://agentic_rag;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Optimize timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;  # Allow longer for complex queries
        
        # Enable keep-alive
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
    
    # Cache static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Load Balancing (High Availability)

```nginx
upstream agentic_rag_cluster {
    least_conn;
    server localhost:5000 weight=1 max_fails=3 fail_timeout=30s;
    server localhost:5001 weight=1 max_fails=3 fail_timeout=30s;
    server localhost:5002 weight=1 max_fails=3 fail_timeout=30s;
    
    keepalive 32;
}
```

### Monitoring and Alerting

#### Performance Monitoring Script

```bash
#!/bin/bash
THRESHOLD_CPU=80
THRESHOLD_MEM=85
THRESHOLD_DISK=90

# CPU usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
if (( $(echo "$CPU_USAGE > $THRESHOLD_CPU" | bc -l) )); then
    echo "ALERT: CPU usage high: ${CPU_USAGE}%"
fi

# Memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", ($3/$2) * 100.0}')
if (( $(echo "$MEM_USAGE > $THRESHOLD_MEM" | bc -l) )); then
    echo "ALERT: Memory usage high: ${MEM_USAGE}%"
fi

# Disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
if [ "$DISK_USAGE" -gt "$THRESHOLD_DISK" ]; then
    echo "ALERT: Disk usage high: ${DISK_USAGE}%"
fi

# API response time
RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null "http://localhost:5000/health")
if (( $(echo "$RESPONSE_TIME > 1.0" | bc -l) )); then
    echo "ALERT: Slow API response: ${RESPONSE_TIME}s"
fi
```

---

## 12. APPENDICES

### Appendix A: Configuration Reference

#### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for tool calling |
| `GMAIL_SENDER_EMAIL` | No | - | Gmail account for email tools |
| `GMAIL_APP_PASSWORD` | No | - | Gmail app-specific password |
| `DATABASE_URL` | No | SQLite | Database connection string |
| `PORT` | No | 5000 | Server port |
| `OLLAMA_NUM_PARALLEL` | No | 1 | Parallel Ollama requests |
| `OLLAMA_MAX_LOADED_MODELS` | No | 1 | Max loaded Ollama models |
| `EMAIL_DEBUG` | No | false | Enable email debugging |

#### File Locations

| Component | Location | Description |
|-----------|----------|-------------|
| Main Configuration | `config/llm_config.yaml` | LLM and service configuration |
| Environment Variables | `.env` | API keys and secrets |
| Document Store | `document_store/` | FAISS index and metadata |
| Logs | `logs/server_complete.log` | Main application logs |
| Watch Config | `watched_directories.json` | Directory monitoring settings |
| System Prompts | `config/*.txt` | AI model instructions |

### Appendix B: API Reference

#### Core Endpoints

```bash
# Health check
GET /health

# System metrics
GET /metrics

# Document statistics
GET /documents/stats

# Document search
POST /documents/search
{
  "query": "search terms",
  "max_results": 10,
  "similarity_threshold": 0.7
}

# OpenAI-compatible chat
POST /v1/chat/completions
{
  "model": "Agentic-RAG-Model1",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}

# Directory management
POST /documents/watch-directory
GET /documents/watch-status
DELETE /documents/unwatch-directory

# Manual indexing
POST /documents/index-directory
```

### Appendix C: Common Error Codes

| Error Code | Description | Common Causes | Solution |
|------------|-------------|---------------|----------|
| 500 | Internal Server Error | Ollama service down | Restart Ollama |
| 503 | Service Unavailable | Embedding service failed | Check model availability |
| 404 | Not Found | Missing files/endpoints | Verify paths and routes |
| 400 | Bad Request | Invalid request format | Check API documentation |
| 401 | Unauthorized | Invalid API key | Verify authentication |
| 413 | Payload Too Large | Large document/attachment | Check size limits |

### Appendix D: Performance Benchmarks

#### System Performance Targets

| Metric | Target | Acceptable | Action Required |
|--------|--------|------------|-----------------|
| API Response Time | < 200ms | < 500ms | > 1s |
| Document Search | < 300ms | < 1s | > 2s |
| Embedding Generation | < 100ms | < 300ms | > 500ms |
| Memory Usage | < 4GB | < 8GB | > 12GB |
| CPU Usage (idle) | < 20% | < 50% | > 80% |
| Disk Space | < 70% | < 85% | > 90% |

#### Load Testing Results

**Test Environment**: 8-core CPU, 16GB RAM, SSD storage

| Concurrent Users | Response Time | Success Rate | Notes |
|------------------|---------------|--------------|-------|
| 1 | 150ms | 100% | Baseline |
| 10 | 200ms | 100% | Normal load |
| 50 | 350ms | 98% | High load |
| 100 | 800ms | 95% | Peak capacity |
| 200 | 1500ms | 85% | Over capacity |

### Appendix E: Security Checklist

#### Production Security Checklist

- [ ] **API Keys**: Stored in environment variables, not code
- [ ] **File Permissions**: Restrictive permissions on config files (600)
- [ ] **Network Security**: Firewall configured, unnecessary ports closed
- [ ] **TLS/SSL**: HTTPS enabled for external access
- [ ] **Authentication**: API key validation implemented
- [ ] **Email Security**: App passwords used, 2FA enabled
- [ ] **Database Security**: Proper user privileges, secure passwords
- [ ] **Log Security**: No sensitive data in logs
- [ ] **Update Management**: Regular security updates applied
- [ ] **Access Control**: Minimal user privileges
- [ ] **Backup Security**: Encrypted backups, secure storage
- [ ] **Monitoring**: Security event logging and alerting

### Appendix F: Troubleshooting Decision Tree

```
Server Not Responding?
├─ Check if process running → No → Start server
├─ Check port availability → Conflict → Change port or kill process
├─ Check logs for errors → Errors → Address specific errors
└─ Check system resources → Low → Add resources or optimize

Ollama Issues?
├─ Service not running → Restart systemctl
├─ Models not loaded → Pull required models
├─ Memory issues → Reduce concurrent models
└─ GPU problems → Check CUDA/drivers or use CPU

Document Processing Issues?
├─ Files not indexed → Check permissions and file types
├─ Search returns nothing → Verify index integrity
├─ Slow processing → Check system resources
└─ Embedding errors → Restart Ollama service

Email Issues?
├─ Authentication failed → Check app passwords
├─ Connection timeout → Check firewall/network
├─ Large attachments → Check size limits
└─ Configuration error → Verify SMTP settings
```

---

## Final Notes

This Administrator Guide provides comprehensive coverage of the Agentic RAG System's operational aspects. For additional support:

- **System Logs**: Always check `logs/server_complete.log` first
- **Health Checks**: Use provided testing scripts regularly
- **Community**: Refer to project documentation and issues
- **Updates**: Follow semantic versioning for updates

**Remember**: This system processes sensitive documents and has AI capabilities. Always follow security best practices and monitor system behavior closely in production environments.

---

*Document Version: 2.0*  
*Last Updated: September 2025*  
*Next Review: December 2025*