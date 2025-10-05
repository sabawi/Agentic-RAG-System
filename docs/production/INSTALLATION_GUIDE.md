# Installation Guide - Agentic RAG System

## Overview

The Agentic RAG System comes with a comprehensive installation script (`install.sh`) that handles:

- ✅ System requirements verification
- ✅ System dependencies installation (tesseract, wkhtmltopdf, etc.)
- ✅ Python virtual environment setup
- ✅ Python dependencies installation
- ✅ Ollama API configuration and verification
- ✅ Cloud API keys configuration (OpenAI, Gemini, Qwen)
- ✅ Installation verification and testing
- ✅ Server connectivity testing

## Quick Start

```bash
# Clone the repository
git clone https://github.com/sabawi/Agentic-RAG-System.git
cd Agentic-RAG-System

# Run the installation script
./install.sh
```

## Script Usage

### Fresh Installation
```bash
./install.sh
```
This will perform a complete fresh installation including system dependencies, virtual environment setup, and configuration.

### Upgrade Existing Installation
```bash
./install.sh upgrade
```
This will pull the latest changes from GitHub and update Python dependencies while preserving your configuration.

### Verify Installation
```bash
./install.sh verify
```
This will check that all components are properly installed and configured.

### Dry Run (Preview)
```bash
./install.sh --dry-run
./install.sh upgrade --dry-run
./install.sh verify --dry-run
```
Shows what the script would do without actually executing any changes.

### Help
```bash
./install.sh --help
```

## Installation Process Details

### 1. System Requirements Check
- ✅ Operating System: Linux/macOS
- ✅ Python 3.8+ with pip
- ✅ Git for repository management
- ✅ curl for API testing

### 2. System Dependencies Installation
**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr wkhtmltopdf build-essential python3-dev python3-venv curl git
```

**macOS (Homebrew):**
```bash
brew install tesseract wkhtmltopdf python3
```

### 3. Virtual Environment Setup
- Automatically detects existing virtual environments (`venv`, `.venv`, `env`)
- Creates `venv` if none exists
- Upgrades pip to latest version

### 4. Python Dependencies
Installs all packages from `requirements.txt` including:
- FastAPI and web framework dependencies
- AI/ML libraries (faiss-cpu, numpy, pandas)
- Document processing (pytesseract, PyPDF2, python-docx)
- Web scraping (selenium, beautifulsoup4)
- Visualization (matplotlib, seaborn)

### 5. Ollama Configuration
**Interactive Setup:**
- Prompts for Ollama API URL (default: `http://127.0.0.1:11434`)
- Tests API connectivity
- Verifies required models:
  - `deepseek-v3.1:671b-cloud` (Primary LLM - Cloud)
  - `qwen3:8b` (Local alternative LLM)
  - `qwen2.5vl:3b` (Vision model)
  - `bakllava:latest` (Fallback vision model)
- Updates `config/llm_config.yaml` with your Ollama URL

**If Ollama is not installed locally:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull required models
ollama pull deepseek-v3.1:671b-cloud
ollama pull qwen3:8b
ollama pull qwen2.5vl:3b
ollama pull bakllava:latest
```

### 6. Cloud API Keys Configuration
**Interactive Setup for:**
- **OpenAI API Key** (`OPENAI_API_KEY`)
  - Used for tool calling and arbitrator
  - Get from: https://platform.openai.com/api-keys
- **Gemini API Key** (`GEMINI_API_KEY`) 
  - Optional fallback provider
  - Get from: https://makersuite.google.com/app/apikey
- **Qwen API Key** (`QWEN_API_KEY`)
  - Optional cloud Qwen access
  - Get from: https://help.aliyun.com/zh/dashscope/

**Keys are stored in `.env` file:**
```bash
OPENAI_API_KEY="your_openai_api_key_here"
GEMINI_API_KEY="your_gemini_api_key_here"
QWEN_API_KEY="your_qwen_api_key_here"
```

### 7. Installation Verification
**Automatic checks:**
- ✅ Virtual environment exists and is activated
- ✅ Required files present (`fastapi_server_complete.py`, `config/llm_config.yaml`)
- ✅ Python package imports work (FastAPI, FAISS, Tesseract)
- ✅ System commands available (`tesseract`, `wkhtmltopdf`)

### 8. Server Connectivity Test
**Optional final test:**
- Starts the server temporarily
- Sends "Hello World!" prompt via API
- Verifies end-to-end functionality
- Automatically cleans up test server

## Post-Installation

### Start the Server
```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start the server
./start_complete.sh

# Or directly with Python
python fastapi_server_complete.py
```

### Access Points
- **API Server:** http://localhost:8000
- **Health Check:** http://localhost:8000/health
- **API Documentation:** http://localhost:8000/docs
- **Metrics:** http://localhost:8000/metrics

### Configuration Files
- **LLM Config:** `config/llm_config.yaml`
- **Environment:** `.env`
- **Server Logs:** `logs/server_complete.log`

## Troubleshooting

### Common Issues

**1. Python Version Too Old**
```bash
# Update Python on Ubuntu
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev

# Or install Python 3.10+
sudo apt install python3.10 python3.10-venv python3.10-dev
```

**2. System Dependencies Missing**
```bash
# Manually install missing dependencies
sudo apt-get install tesseract-ocr wkhtmltopdf build-essential python3-dev
```

**3. Ollama Not Accessible**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama
ollama serve

# Pull required models
ollama pull deepseek-v3.1:671b-cloud
ollama pull qwen3:8b
ollama pull qwen2.5vl:3b
ollama pull bakllava:latest
```

**4. API Key Issues**
- Verify keys are correctly formatted in `.env`
- Test API connectivity manually
- Check for typos or expired keys

**5. Permission Issues**
```bash
# Make script executable
chmod +x install.sh

# Fix virtual environment permissions
sudo chown -R $USER:$USER venv/
```

### Getting Help

**Documentation:**
- [Administrator Guide](./ADMINISTRATOR_GUIDE.md) - System administration and maintenance
- [User Guide](./USER_GUIDE.md) - API usage and features  
- [Developer Guide](./DEVELOPER_GUIDE.md) - Development and architecture

**Verification Commands:**
```bash
# Check installation
./install.sh verify

# Test individual components
python -c "import fastapi; print('FastAPI OK')"
python -c "import faiss; print('FAISS OK')"
tesseract --version
wkhtmltopdf --version

# Test Ollama
curl http://localhost:11434/api/tags

# Test server startup
timeout 30 python fastapi_server_complete.py
```

## Advanced Usage

### Custom Ollama Installation
```bash
# Remote Ollama server
OLLAMA_URL="http://192.168.1.100:11434"

# During installation, enter your custom URL when prompted
```

### Environment Variables
```bash
# Load environment automatically
source .env

# Or set manually
export OPENAI_API_KEY="your_key_here"
export OLLAMA_BASE_URL="http://your-ollama:11434"
```

### Development Setup
```bash
# Fresh installation for development
./install.sh

# Install additional dev dependencies
pip install pytest pytest-asyncio black isort mypy

# Run tests
python -m pytest tests/
```

The installation script provides a robust, user-friendly way to set up the Agentic RAG System with comprehensive verification and testing capabilities.