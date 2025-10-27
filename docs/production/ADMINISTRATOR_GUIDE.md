# Agentic RAG System - Administrator Guide

**Version:** 1.0.3.23
**Last Updated:** October 24, 2025
**Target Audience:** System Administrators, DevOps Engineers, Production Support

**Latest Updates (v1.0.3.23):**
- ✅ Safe Embedding Model Changes with safeguards & validation
- ✅ Dimension Mismatch Detection & Prevention
- ✅ Model Metadata Tracking & Verification
- ✅ Critical Embedding OOM Fix (batch_size 25→10)
- ✅ Adaptive Batch Sizing for Resilience
- ✅ Configuration Compliance (all parameters in config file)

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
   - [Changing Embedding Models](#changing-embedding-models)
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
│ System          │    │  Document Store  │    │ • deepseek-v3.1 │
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
- Python 3.13.8 (required for optimal async I/O performance)
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
sudo apt install -y python3.13 python3.13-venv python3.13-dev \
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
ollama pull deepseek-v3.1:671b-cloud

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
deepseek-v3.1:671b-cloud          ghi789jkl012    8.0 GB    X minutes ago
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

**For comprehensive LLM configuration documentation, see:** [`docs/LLM_CONFIGURATION_GUIDE.md`](../LLM_CONFIGURATION_GUIDE.md)

The LLM configuration guide provides detailed documentation on:
- Primary, tool-calling, vision, and arbitrator LLM setup
- Context window sizing and performance tuning
- Thinking mode configuration
- Provider fallback strategies
- Troubleshooting LLM issues
- Migration guides and version history

**Quick Reference** - Edit `config/llm_config.yaml`:

```yaml
llm:
  primary:
    type: ollama
    config:
      model: deepseek-v3.1:671b-cloud  # Cloud-hosted 671B model
      context_window_size: 32768        # Large context for document searches

  tool_calling:
    type: openai
    config:
      model: gpt-4o-mini               # Reliable tool orchestration

  vision:
    type: ollama
    config:
      model: qwen2.5vl:3b              # Local vision analysis
```

**Key Admin Considerations:**
- Primary model requires cloud connection (deepseek-v3.1:671b-cloud)
- Tool calling requires `OPENAI_API_KEY` environment variable
- Context window increased to 32768 tokens (4x previous default)
- Python 3.13.8 required for 40-50% async I/O performance gains

For detailed parameter explanations and advanced tuning options, **refer to the comprehensive LLM Configuration Guide**.

### Model Management CLI Tool

**For comprehensive CLI documentation, see:** [`docs/CLI_MODEL_MANAGEMENT.md`](../CLI_MODEL_MANAGEMENT.md)

The `config_server_cli.py` CLI tool provides simplified management of LLM model configurations through named aliases. Instead of manually editing YAML files, administrators can quickly switch between different model configurations using simple commands.

#### Key Features

- **Model Aliases**: Create named aliases for full model configurations
- **Easy Switching**: Switch primary, tool_calling, or arbitrator models in seconds
- **Multi-Provider Support**: Ollama, OpenAI, OpenRouter, Qwen (Alibaba Cloud)
- **Configuration Database**: Persistent storage in `config/model_aliases.json`
- **Safety Checks**: Prevents accidental deletion of active models
- **Color-Coded Output**: Clear visual feedback for all operations

#### Quick Start Commands

```bash
# Check current active models
./config_server_cli.py status

# List all configured model aliases
./config_server_cli.py ls

# Create a new model alias
./config_server_cli.py add --alias local_qwen \
  --provider ollama \
  --model qwen3:8b \
  --description "Local Qwen model"

# Add Gemini model
./config_server_cli.py add --alias gemini_flash \
  --provider gemini \
  --model gemini-flash-latest \
  --description "Gemini Flash for vision"

# Switch primary LLM
./config_server_cli.py set --alias local_qwen --as primary

# Switch tool calling LLM
./config_server_cli.py set --alias gpt4_mini --as tool_calling

# Switch vision LLM
./config_server_cli.py set --alias gemini_flash --as vision

# Update an alias
./config_server_cli.py update --alias local_qwen --temperature 0.5

# Show detailed alias information
./config_server_cli.py show --alias local_qwen

# Delete an alias (with safety checks)
./config_server_cli.py delete --alias old_model
```

#### Integration with Server Operations

**Important**: After changing model configurations, always restart the server:

```bash
# Stop server
./stop_complete.sh

# Verify configuration
./config_server_cli.py status

# Start server
./start_complete.sh

# Monitor server logs for proper model loading
tail -f logs/server_complete.log | grep -i "model\|provider"
```

#### Supported Providers

| Provider | Description | API Key Required | Base URL |
|----------|-------------|------------------|----------|
| **ollama** | Local Ollama models | No | http://127.0.0.1:11434 |
| **openai** | OpenAI API (GPT models) | Yes | https://api.openai.com/v1 |
| **openrouter** | OpenRouter API gateway | Yes | https://openrouter.ai/api/v1 |
| **qwen** | Alibaba Cloud Qwen | Yes | https://dashscope.aliyuncs.com |
| **gemini** | Google Gemini (native API) | Yes | Native Gemini API |

#### Common Administrative Tasks

**Daily Model Switching:**
```bash
# Switch to high-performance cloud model for peak hours
./config_server_cli.py set --alias openrouter_deepseek --as primary

# Switch to local model for off-peak hours (cost savings)
./config_server_cli.py set --alias qwen_local --as primary
```

**Testing New Models:**
```bash
# Add test model alias
./config_server_cli.py add --alias test_model \
  --provider openai \
  --model gpt-4o \
  --timeout 120 \
  --temperature 0.3

# Set as primary for testing
./config_server_cli.py set --alias test_model --as primary

# Restart server and test
./stop_complete.sh && ./start_complete.sh
```

**Reasoning Models Configuration:**
```bash
# Enable think mode for reasoning models (shows internal reasoning)
./config_server_cli.py add --alias deepseek_reasoning \
  --provider ollama \
  --model deepseek-v3.1:671b-cloud \
  --think \
  --description "DeepSeek with reasoning display"

# Disable think mode for cleaner output
./config_server_cli.py update --alias deepseek_reasoning --no-think
```

#### Configuration Files

**Model Aliases Database:**
- **Location**: `config/model_aliases.json`
- **Format**: JSON with full model configurations
- **Backup**: Recommended before major changes
- **Manual Editing**: Possible but not recommended (use CLI instead)

**Active Configuration:**
- **Location**: `config/llm_config.yaml`
- **Modified By**: `./config_server_cli.py set` command
- **Preserved**: Comments and other configuration sections
- **Safety**: Automatic backup before changes

#### Troubleshooting

**Problem: "Alias not found"**
```bash
# List all available aliases
./config_server_cli.py ls

# Check exact alias name (case-sensitive)
./config_server_cli.py show --alias <name>
```

**Problem: Model switch doesn't take effect**
```bash
# Verify configuration was updated
./config_server_cli.py status
cat config/llm_config.yaml | grep -A 5 "primary:"

# Restart server (required for changes to take effect)
./stop_complete.sh && ./start_complete.sh
```

**Problem: Server fails after model switch**
```bash
# Check server logs
tail -f logs/server_complete.log | grep -i "error\|failed"

# Verify model is available (for Ollama)
ollama list

# Verify API key is set (for cloud providers)
echo $OPENAI_API_KEY
echo $OPENROUTER_API_KEY

# Revert to previous working configuration
./config_server_cli.py set --alias <previous_working_alias> --as primary
./stop_complete.sh && ./start_complete.sh
```

#### Quick Reference Card

For administrators who need quick command reference, see: `MODEL_CLI_QUICKREF.txt` in the project root directory.

**Comprehensive Documentation:** For detailed examples, workflows, and best practices, refer to [`docs/CLI_MODEL_MANAGEMENT.md`](../CLI_MODEL_MANAGEMENT.md).

### Flight Search Tool Configuration

**For complete flight search configuration, see:** `config/llm_config.yaml` (section: `flight_search`)

The flight search tool supports multiple data sources:
- **Amadeus API** (recommended for production)
- **Skyscanner API** (requires partner access)
- **SerpAPI** (Google Flights data)
- **Web scraping fallback** (always available)

**Quick Setup:**

1. **Enable flight search** in `config/llm_config.yaml`:
   ```yaml
   flight_search:
     enabled: true
   ```

2. **Configure API keys** (optional, improves reliability):
   ```bash
   # .env file
   AMADEUS_API_KEY=your_key_here
   AMADEUS_API_SECRET=your_secret_here
   ```

3. **Enable in config**:
   ```yaml
   apis:
     amadeus:
       enabled: true
   ```

**Admin Notes:**
- Web scraping works out-of-the-box (no API keys required)
- ChromeDriver auto-installs if not found
- API keys improve reliability and speed
- See `config/llm_config.yaml` for complete configuration options

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
  "version": "1.0.3.3"
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

### Changing Embedding Models

**Version Required**: v1.0.3.23 or later (includes safety safeguards)

Embedding models can be changed in the configuration file and the index can be safely rebuilt. The system includes validation to prevent dimension mismatches that could corrupt your data.

#### Available Embedding Models

| Model | Dimension | Speed | Accuracy | Memory | Best For |
|-------|-----------|-------|----------|--------|----------|
| `mxbai-embed-large` (default) | 1024 | Medium | 59.25% | 1.2GB | Highest quality, legal/medical docs |
| `nomic-embed-text` | 768 | Fast | 57.25% | 0.5GB | Speed priority, good quality |
| `nomic-bert` | 768 | Fast | ~57% | ~0.5GB | Alternative to nomic |

#### Step-by-Step: Change Embedding Model

**Step 1: Backup Current Index**
```bash
# Stop server
./stop_complete.sh

# Create backup
cp -r document_store document_store.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup
ls -la document_store.backup.*/
```

**Step 2: Update Configuration**

Edit `config/llm_config.yaml`:

```yaml
document_interrogator:
  embedding:
    # For nomic-embed-text (faster, 2% lower accuracy)
    model_name: "nomic-embed-text"
    dimension: 768

    # For mxbai-embed-large (slower, best quality)
    # model_name: "mxbai-embed-large"
    # dimension: 1024
```

**Step 3: Ensure Model is Available**

```bash
# Check if model exists
ollama list | grep "nomic-embed-text"

# If not found, pull it
ollama pull nomic-embed-text
```

**Step 4: Delete Old Index**

⚠️ **CRITICAL**: This prevents dimension mismatch corruption.

```bash
# Delete FAISS index
rm -f document_store/faiss.index

# Delete SQLite metadata
rm -f document_store/metadata.db

# Verify deletion
ls -la document_store/
# Should be mostly empty (only backups)
```

**Step 5: Restart Server**

```bash
./start_complete.sh

# Wait 15 seconds for initialization
sleep 15

# Check startup logs for success
tail -50 logs/server_complete.log | grep -E "Created new FAISS|Model metadata|error|ERROR"
```

**Expected Log Messages** (success):
```
✅ Created new FAISS index (dimension: 768, model: nomic-embed-text)
📝 Recorded model metadata: nomic-embed-text (dimension: 768)
```

**Error Messages** (indicates problem):
```
🚨 DIMENSION MISMATCH DETECTED!
❌ Storage initialization failed
```

**Step 6: Rebuild Index**

The system will automatically rebuild the index on the next scan cycle (default: 60 minutes).

To rebuild immediately:
```bash
# Trigger API scan endpoint (if available)
curl -X POST http://localhost:5000/interrogator/force-scan \
  -H "Content-Type: application/json"

# Or monitor automatic scan in logs
tail -f logs/server_complete.log | grep -E "Processing|batch|Completed batch"
```

**Expected Rebuild Time**:
- mxbai-embed-large: ~27-30 minutes for 1961 chunks
- nomic-embed-text: ~15-18 minutes for 1961 chunks

**Verify Completion**:
```bash
# Check stats
curl -s http://localhost:5000/interrogator/stats | jq '.embedding_model'

# Should show:
# {
#   "name": "nomic-embed-text",
#   "dimension": 768,
#   "model_matches": true,
#   "dimension_matches": true
# }
```

#### Safety Features (v1.0.3.23+)

✅ **Dimension Validation**: System detects mismatches and prevents startup
✅ **Model Metadata Tracking**: Stores which model created the index
✅ **Clear Error Messages**: Guides you through the fix if dimension mismatch occurs
✅ **Search Quality Warnings**: Logs when model is changed but index not rebuilt

#### Rollback Procedure

If the model change causes problems:

```bash
# 1. Stop server
./stop_complete.sh

# 2. Restore from backup
cp -r document_store.backup.20251024_120000/* document_store/

# 3. Revert config to original model
# Edit config/llm_config.yaml: change model_name and dimension back

# 4. Restart
./start_complete.sh
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

## 7A. PLUGIN SYSTEM ADMINISTRATION

The plugin system provides process-isolated, resource-controlled extensions to server functionality. Plugins are auto-discovered at server startup and require no code changes to deploy.

### Plugin Overview

**Key Features:**
- **Auto-Discovery**: Drop `.yaml` + handler files in `/plugins/` directory
- **Process Isolation**: Each plugin runs in separate process with resource limits
- **Zero-Config**: Works with sensible defaults (60s timeout, 256MB memory, 1.0 CPU)
- **Optional Configuration**: Override defaults in `config/llm_config.yaml` only if needed

### Checking Plugin Status

**Verify Plugins on Startup:**
```bash
# Check server startup logs for plugin loading
tail -100 logs/server_complete.log | grep "🔌"

# Expected output:
# 🔌 Loaded 8 plugins in 0.048s
# 🔌 Plugin: get_news_summaries (v1.0.0)
# 🔌 Plugin: social_media_twitter_test (v1.0.0)
# ...
```

**List Loaded Plugins:**
```bash
# Check server logs for complete plugin list
grep "🔌 Plugin:" logs/server_complete.log | tail -20

# Should show all loaded plugins with versions
```

### Installing New Plugins

**1. Deploy Plugin Files:**
```bash
# Copy plugin definition
cp your_plugin.yaml /path/to/server/plugins/

# Copy plugin handler
cp your_plugin.py /path/to/server/plugins/handlers/

# Set proper permissions
chmod 644 plugins/your_plugin.yaml
chmod 755 plugins/handlers/your_plugin.py
```

**2. Restart Server:**
```bash
# Stop server
./stop_complete.sh

# Start server (plugins auto-load)
./start_complete.sh

# Verify plugin loaded
tail -f logs/server_complete.log | grep "🔌 Plugin: your_plugin"
```

**3. Verify Plugin Availability:**
```bash
# Test plugin execution via API
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{
      "role": "user",
      "content": "Use your_plugin to test functionality"
    }]
  }'
```

### Plugin Configuration (Optional)

**Default Configuration (No Configuration Needed):**

Plugins work out-of-the-box with these defaults:
- Timeout: 60 seconds
- Memory limit: 256MB
- CPU limit: 1.0 core
- Max string length: 100KB
- Max array length: 1000 items

**Custom Configuration:**

Only add to `config/llm_config.yaml` if you need to override defaults:

```yaml
plugins:
  enabled: true  # Optional: explicitly enable/disable

  plugin_defaults:
    execution:
      timeout: 120          # Override default 60s
      memory_limit: 512     # Override default 256MB
      cpu_limit: 2.0        # Override default 1.0 CPU
      max_timeout: 600      # Maximum allowed timeout

    security:
      input_validation:
        max_string_length: 204800   # 200KB (double default)
        max_array_length: 2000      # 2000 items (double default)
      output_validation:
        max_result_size: 2097152    # 2MB max result

  # Per-plugin overrides (optional)
  social_media_twitter_test:
    execution:
      timeout: 180         # Social media operations may take longer
      memory_limit: 512    # More memory for image processing
```

**Apply Configuration Changes:**
```bash
# Edit configuration
vim config/llm_config.yaml

# Restart server to apply changes
./stop_complete.sh && ./start_complete.sh

# Verify changes in logs
tail -f logs/server_complete.log | grep -i plugin
```

### Monitoring Plugin Execution

**Real-Time Plugin Monitoring:**
```bash
# Monitor all plugin activity
tail -f logs/server_complete.log | grep -E "(🔌|Plugin)"

# Monitor plugin execution times
tail -f logs/server_complete.log | grep "execution_time"

# Monitor plugin errors
tail -f logs/server_complete.log | grep -E "(Plugin.*error|Plugin.*failed)"
```

**Plugin Performance Analysis:**
```bash
# Check for slow plugins (>30s execution time)
grep "execution_time" logs/server_complete.log | awk '$NF > 30' | tail -20

# Count plugin invocations by type
grep "🔌 Plugin:" logs/server_complete.log | cut -d: -f2 | sort | uniq -c | sort -rn

# Find plugins hitting timeout limits
grep "Plugin.*timeout" logs/server_complete.log | tail -20
```

### Troubleshooting Plugins

**Plugin Not Loading:**

```bash
# 1. Check plugin YAML syntax
python3 -c "import yaml; yaml.safe_load(open('plugins/your_plugin.yaml'))"

# 2. Verify handler file exists
ls -la plugins/handlers/your_plugin.py

# 3. Check handler is executable
chmod +x plugins/handlers/your_plugin.py

# 4. Check for errors in server logs
grep "your_plugin" logs/server_complete.log | grep -i error
```

**Plugin Execution Failures:**

```bash
# Check for timeout errors
grep "your_plugin.*timeout" logs/server_complete.log

# Solution: Increase timeout in config/llm_config.yaml
# plugins:
#   your_plugin:
#     execution:
#       timeout: 180  # Increase from default 60s

# Check for memory errors
grep "your_plugin.*memory" logs/server_complete.log

# Solution: Increase memory limit
# plugins:
#   your_plugin:
#     execution:
#       memory_limit: 512  # Increase from default 256MB
```

**Plugin Process Issues:**

```bash
# Check for orphaned plugin processes
ps aux | grep "plugin" | grep -v grep

# Kill orphaned processes if found
pkill -f "plugin.*your_plugin"

# Restart server for clean state
./stop_complete.sh && sleep 5 && ./start_complete.sh
```

### Plugin Security

**File Permissions:**
```bash
# Secure plugin directory
chmod 755 plugins/
chmod 755 plugins/handlers/

# Plugin YAML files should be read-only
chmod 644 plugins/*.yaml

# Handler scripts should be executable
chmod 755 plugins/handlers/*.py
```

**Resource Limits:**

Monitor resource usage to prevent plugin abuse:
```bash
# Monitor plugin memory usage
ps aux --sort=-%mem | grep plugin | head -10

# Monitor plugin CPU usage
ps aux --sort=-%cpu | grep plugin | head -10

# Set stricter limits if needed in config/llm_config.yaml
```

### Plugin Maintenance

**Updating Plugins:**
```bash
# 1. Stop server
./stop_complete.sh

# 2. Update plugin files
cp updated_plugin.yaml plugins/
cp updated_handler.py plugins/handlers/

# 3. Start server
./start_complete.sh

# 4. Verify update
tail -f logs/server_complete.log | grep "🔌 Plugin: updated_plugin"
```

**Disabling Plugins:**
```bash
# Method 1: Remove plugin files
mv plugins/your_plugin.yaml plugins/disabled/
mv plugins/handlers/your_plugin.py plugins/handlers/disabled/

# Method 2: Disable entire plugin system (config/llm_config.yaml)
# plugins:
#   enabled: false

# Restart server
./stop_complete.sh && ./start_complete.sh
```

**Backup Plugin Configuration:**
```bash
# Backup all plugins
tar -czf plugins_backup_$(date +%Y%m%d).tar.gz plugins/

# Restore from backup
tar -xzf plugins_backup_20251026.tar.gz
```

### Plugin Documentation

For detailed plugin development and architecture information:

- **📖 User Guide:** `/docs/PLUGIN_USER_GUIDE.md` - Complete usage guide
- **🏗️ Architecture:** `/docs/PLUGIN_ARCHITECTURE_DESIGN.md` - System design details
- **⚡ Quick Start:** `/docs/QUICK_PLUGIN_GUIDE.md` - Fast deployment tutorial
- **📝 Cheat Sheet:** `/docs/PLUGIN_CHEAT_SHEET.md` - Common operations reference
- **🎯 Example:** `/docs/FORTUNE_PLUGIN_EXAMPLE.md` - Reference implementation

**Configuration Directive:**

See `/docs/PROJECT_CONFIGURATION_DIRECTIVE.md` for information on:
- Plugin configuration vs LLM configuration architecture
- Auto-discovery model vs explicit configuration
- When plugin configuration is required vs optional

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
ollama pull deepseek-v3.1:671b-cloud
ollama pull mxbai-embed-large

# Check model integrity
ollama run deepseek-v3.1:671b-cloud "Hello"
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
ollama pull deepseek-v3.1:671b-cloud
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
- **Detailed Configuration**: See [`docs/LLM_CONFIGURATION_GUIDE.md`](../LLM_CONFIGURATION_GUIDE.md) for comprehensive LLM setup
- **Version History**: See `docs/housekeeping/status-tracking/PROJECT_CHANGELOG.md` for detailed changelog
- **Updates**: Follow semantic versioning for updates

**Recent Major Changes (v1.0.3.0 - v1.0.3.3):**
- Python 3.13.8 upgrade (40-50% async I/O performance improvement)
- System prompt delivery fix for Ollama models
- Citation format enforcement (clickable `[Title](URL)` format)
- API endpoint documentation corrections
- Google API dependencies for Python 3.13 compatibility
- Context window increased to 32768 tokens (4x expansion)
- Primary model updated to deepseek-v3.1:671b-cloud

**Remember**: This system processes sensitive documents and has AI capabilities. Always follow security best practices and monitor system behavior closely in production environments.

---

**Document Version:** 1.0.3.6
**System Version:** 1.0.3.6
**Last Updated:** October 12, 2025
**Next Review:** January 2026