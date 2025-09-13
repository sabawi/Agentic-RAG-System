# Agentic-RAG Server Installation Guide

Complete step-by-step installation and setup guide for the Agentic-RAG Server.

## 📋 Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: 16GB+ recommended (8GB minimum)
- **Storage**: 50GB+ free space for models
- **GPU**: Optional but recommended (NVIDIA GPU with CUDA support)
- **Network**: Internet connection for model downloads and cloud API access

### Required System Packages

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

## 🔧 Installation Steps

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd agentic-rag-server
```

### Step 2: Set Up Python Environment

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

### Step 3: Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Enable as system service
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify installation
ollama --version
```

### Step 4: Download Required Models

```bash
# Primary conversation model (8GB)
ollama pull qwen3:8b

# Vision processing model (2.3GB) 
ollama pull qwen2.5vl:3b

# Verify models are installed
ollama list
```

**Expected output:**
```
NAME            ID              SIZE      MODIFIED
qwen2.5vl:3b    abc123def456    2.3 GB    X minutes ago
qwen3:8b        def456abc123    8.0 GB    X minutes ago
```

### Step 5: Configure API Keys

Create environment file:

```bash
cp .env.example .env  # If example exists, or create new file
nano .env
```

Add required API keys:

```bash
# OpenAI API (required for tool calling)
OPENAI_API_KEY=REPLACE_WITH_YOUR_OPENAI_API_KEY

# Optional cloud providers
GOOGLE_API_KEY=REPLACE_WITH_YOUR_GOOGLE_API_KEY
GEMINI_API_KEY=REPLACE_WITH_YOUR_GEMINI_API_KEY
QWEN_API_KEY=REPLACE_WITH_YOUR_QWEN_API_KEY

# Email configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=REPLACE_WITH_YOUR_APP_PASSWORD

# Flight Search API Keys (optional - enables real flight data)
AMADEUS_API_KEY=REPLACE_WITH_YOUR_AMADEUS_API_KEY
AMADEUS_API_SECRET=REPLACE_WITH_YOUR_AMADEUS_API_SECRET
SKYSCANNER_API_KEY=REPLACE_WITH_YOUR_SKYSCANNER_API_KEY
SERPAPI_API_KEY=REPLACE_WITH_YOUR_SERPAPI_KEY
RAPIDAPI_KEY=REPLACE_WITH_YOUR_RAPIDAPI_KEY
CHROMEDRIVER_PATH=/path/to/chromedriver  # Optional - auto-installs if not set
```

**Flight Search API Setup Notes:**
- **Without API keys**: Flight search uses web scraping and provides verification links
- **With Amadeus API**: Best option - free tier (1000 calls/month), then $1/1000 calls
- **With SerpAPI**: Good for Google Flights data - paid service ($50/month for 5000 searches)
- **ChromeDriver**: Auto-installs if not specified, requires Chrome browser

### Step 6: Set Up Google Calendar (Optional)

If using calendar tools:

1. **Enable Google Calendar API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing
   - Enable Calendar API
   - Create credentials (Service Account)

2. **Download credentials**:
   ```bash
   # Place your service account key file
   mkdir -p config/google/
   cp ~/Downloads/your-service-account-key.json config/google/calendar-credentials.json
   ```

3. **Share calendar with service account**:
   - Open Google Calendar
   - Share your calendar with service account email
   - Grant "Make changes to events" permission

### Step 7: Configure Mail System

```bash
# Configure Postfix for local delivery
sudo dpkg-reconfigure postfix

# Select "Internet Site"
# Enter your domain name or localhost

# Test mail system
echo "Test message" | mail -s "Test Subject" your-email@example.com

# Install additional mail utilities
sudo apt install -y mutt msmtp msmtp-mta
```

### Step 8: Service Installation

You can run the server in two ways:

#### Option A: As a System Service (Recommended for Production)

Install the server as a systemd service using the automated installer:

```bash
# Make scripts executable
chmod +x install_service.sh uninstall_service.sh

# Install as system service
./install_service.sh
```

The installer will:
- ✅ Validate environment and dependencies
- ✅ Create systemd service file with proper configuration  
- ✅ Install service to `/etc/systemd/system/agentic-rag-server.service`
- ✅ Configure logging to systemd journal
- ✅ Enable auto-start on boot
- ✅ Optionally start the service immediately

**Service Management Commands:**
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

# Disable service (prevent auto-start)
sudo systemctl disable agentic-rag-server
```

**Service Features:**
- 🔄 **Auto-restart** on failure
- 📋 **Centralized logging** to systemd journal
- 🚀 **Auto-start** on system boot
- 🔒 **Proper isolation** and security settings
- 📊 **Resource management** and limits
- ⚡ **Graceful shutdown** handling

#### Option B: Manual Execution (Development/Testing)

```bash
# Run directly for development
./start_complete.sh

# Stop with
./stop_complete.sh
```

#### Uninstalling the Service

To remove the systemd service:

```bash
# Stop and uninstall service
./uninstall_service.sh
```

This will:
- Stop the running service
- Disable auto-start 
- Remove service file
- Reload systemd daemon

## 🧪 Testing Installation

### 1. Test Dependencies

```bash
python tests/test_dependencies.py
```

**Expected output:**
```
🎉 All dependencies successfully installed and tested!
✅ Ready to run the Agentic-RAG server
```

### 2. Test Ollama Models

```bash
# Test primary model
python -c "import ollama; print(ollama.generate('qwen3:8b', 'Hello'))"

# Test vision model
python tests/test_ollama_image2text.py qwen2.5vl:3b ~/path/to/test/image.jpg
```

### 3. Test Server Startup

```bash
./start_complete.sh
```

Watch for successful startup messages:
- ✅ Ollama service healthy
- ✅ Models loaded successfully  
- ✅ Server running on http://localhost:5000

### 4. Test API Endpoint

```bash
# Test basic completion
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Test image analysis
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image"},
        {"type": "image_url", {"image_url": {"url": "file:///path/to/image.jpg"}}}
      ]
    }]
  }'
```

## ⚙️ Configuration

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
```

### System Prompts

Customize AI behavior by editing:

- `primary_model_system_prompt.txt` - Main conversation model
- `pre_tool_model_system_prompt.txt` - Tool calling orchestration  
- `config/image_to_text_system_prompt.txt` - Vision model instructions
- `config/arbitrator_system_prompt.txt` - Decision arbitration

## 🐛 Troubleshooting

### Common Issues

1. **Ollama connection failed**
   ```bash
   # Restart Ollama service
   sudo systemctl restart ollama
   
   # Check if models are loaded
   ollama list
   ```

2. **Python dependencies missing**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   
   # Test dependencies
   python tests/test_dependencies.py
   ```

3. **Out of memory errors**
   ```bash
   # Check system memory
   free -h
   
   # Reduce model concurrency in config
   # Set max_concurrent_requests: 1
   ```

4. **Vision processing fails**
   ```bash
   # Test EasyOCR installation
   python -c "import easyocr; print('EasyOCR OK')"
   
   # Test vision model directly
   ollama run qwen2.5vl:3b "Describe this image: /path/to/image.jpg"
   ```

5. **Email tools not working**
   ```bash
   # Test mail system
   echo "Test" | mail -s "Test" your-email@example.com
   
   # Check postfix status
   sudo systemctl status postfix
   
   # View mail logs
   sudo tail -f /var/log/mail.log
   ```

### Getting Help

- Check logs in `server_complete.log`
- Run `python tests/test_dependencies.py` to verify setup
- Ensure all required models are downloaded with `ollama list`
- Verify API keys are set correctly in `.env`

## 🔒 Security Notes

- **API Keys**: Store securely in `.env` file, never commit to version control
- **Network**: Run behind reverse proxy (nginx) in production
- **Authentication**: Implement proper API key management
- **Firewall**: Restrict access to port 5000 externally

## 📈 Performance Optimization

### For Production

1. **Use GPU acceleration** if available
2. **Increase memory** allocation for Ollama
3. **Use SSD storage** for models
4. **Configure load balancing** for high availability
5. **Monitor resource usage** with systemd limits

### Model Optimization

```bash
# Optimize model loading
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_MAX_LOADED_MODELS=4

# For GPU acceleration
export CUDA_VISIBLE_DEVICES=0
```

## 📚 Additional Resources

- [Ollama Documentation](https://ollama.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [FAISS Documentation](https://faiss.ai)

---

**Note**: This installation requires significant system resources. Ensure your system meets the minimum requirements before proceeding.