# Agentic RAG System - Troubleshooting Guide

## Quick Diagnosis

**First, run the quick health check:**
```bash
cd /home/sabawi/Development/flaskserver/testing
./quick_health_check.sh
```

**For detailed diagnosis:**
```bash
./comprehensive_test_suite.sh
./test_embedding_service.sh
./test_api_endpoints.sh
```

---

## Common Issues & Solutions

### 1. Server Not Starting

**Symptoms:**
- `curl: (7) Failed to connect to localhost port 5000`
- Server process exits immediately
- Port already in use errors

**Diagnosis:**
```bash
# Check if server is already running
ps aux | grep fastapi_server_complete.py

# Check port availability
netstat -tlnp | grep :5000

# Check server logs
tail -f logs/server_complete.log
```

**Solutions:**

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

---

### 2. Ollama Service Issues

**Symptoms:**
- Tool calling returns errors
- "Ollama service not available" messages
- Model runner crashes

**Diagnosis:**
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

**Solutions:**

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

**D. GPU issues:**
```bash
# Check GPU status (if using GPU)
nvidia-smi

# Force CPU mode if GPU issues
export CUDA_VISIBLE_DEVICES=""
sudo systemctl restart ollama
```

---

### 3. Tool Calling Failures

**Symptoms:**
- Tools not being called when expected
- "Tool calling exception" in logs
- Single tool behavior instead of multi-tool

**Diagnosis:**
```bash
# Test basic tool calling
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the current date and time?",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'

# Check server logs for tool errors
tail -f logs/server_complete.log | grep -i tool
```

**Solutions:**

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

**C. Test individual tools:**
```bash
# Test different tools one by one
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Search the web for latest news",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

---

### 4. Embedding Service Problems

**Symptoms:**
- Document search returns no results
- "Embedding service unhealthy" errors
- Slow indexing or search

**Diagnosis:**
```bash
# Run embedding-specific tests
cd testing/
./test_embedding_service.sh

# Check document system status
curl "http://localhost:5000/documents/stats" | jq .

# Test direct embedding generation
curl http://localhost:11434/api/embeddings \
  -d '{"model": "mxbai-embed-large", "prompt": "test"}'
```

**Solutions:**

**A. Restart embedding model:**
```bash
ollama stop mxbai-embed-large
ollama pull mxbai-embed-large
ollama run mxbai-embed-large  # Test it works
```

**B. Check FAISS index:**
```bash
# Verify index files exist
ls -la document_store/
# Should show faiss.index and metadata.db

# If corrupted, rebuild:
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/your/documents/path",
    "force_rebuild": true
  }'
```

**C. Check system resources:**
```bash
# Embedding generation is memory-intensive
free -h
df -h  # Check disk space for index storage
```

---

### 5. OpenAI Compatibility Issues

**Symptoms:**
- OpenAI endpoints return errors
- Incompatible response formats
- Missing model listings

**Diagnosis:**
```bash
# Test OpenAI models endpoint
curl "http://localhost:5000/v1/models" | jq .

# Test chat completions
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }' | jq .
```

**Solutions:**

**A. Check OpenAI layer configuration:**
```bash
# Verify USE_DIRECT_FUNCTION_CALLS setting
grep -n "USE_DIRECT_FUNCTION_CALLS" fastapi_server_complete.py
```

**B. Test different OpenAI modes:**
```bash
# Try with streaming
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

---

### 6. Memory Leaks / Performance Issues

**Symptoms:**
- Gradual memory increase
- Slow response times
- Server becomes unresponsive

**Diagnosis:**
```bash
# Monitor memory over time
while true; do
  echo "$(date): $(curl -s http://localhost:5000/metrics | jq -r '.memory_usage_mb')MB"
  sleep 60
done

# Check system resources
htop
iotop  # Check disk I/O

# Monitor response times
time curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "qwen3:8b", "toolsInUse": false, "stream": false}'
```

**Solutions:**

**A. Regular restarts:**
```bash
# Set up daily restart (crontab -e)
0 3 * * * cd /home/sabawi/Development/flaskserver && ./stop_complete.sh && ./start_complete.sh
```

**B. Optimize resource usage:**
```bash
# Limit Ollama models loaded simultaneously
export OLLAMA_MAX_LOADED_MODELS=2

# Clear old conversation memory (if memory feature enabled)
# Conversations auto-cleanup after 7 days
```

**C. Check for resource leaks:**
```bash
# Monitor file descriptors
lsof -p $(pgrep -f fastapi_server_complete.py) | wc -l

# Check database connections
curl "http://localhost:5000/metrics" | jq '.database_connections'
```

---

### 7. Document Processing Failures

**Symptoms:**
- Files not being indexed
- Processing hangs on certain documents
- OCR or PDF extraction errors

**Diagnosis:**
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

**Solutions:**

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

**C. Handle corrupted files:**
```bash
# Test file integrity
file /path/to/document.pdf
pdfinfo /path/to/document.pdf  # For PDFs

# Skip problematic files during batch processing
# Add file validation in document processing
```

---

### 8. Email Tool Issues

**Symptoms:**
- Email sending fails
- Authentication errors
- Attachment problems

**Diagnosis:**
```bash
# Check email configuration
echo $GMAIL_SENDER_EMAIL
echo $GMAIL_APP_PASSWORD  # Should show app password

# Test email tool
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Send a test email to test@example.com with subject Test",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

**Solutions:**

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
# For Outlook, ensure app password is generated

# Test SMTP connectivity
telnet smtp.gmail.com 587
```

---

### 9. Database Connection Issues

**Symptoms:**
- "Database pool initialization failed"
- Connection timeout errors
- Conversation memory not working

**Diagnosis:**
```bash
# Check database configuration
echo $DATABASE_URL

# Test database connection
mysql -u username -p -h localhost database_name

# Check connection pool status
curl "http://localhost:5000/metrics" | jq '.database_connections'
```

**Solutions:**

**A. Fix database credentials:**
```bash
# Update DATABASE_URL if needed
export DATABASE_URL="mysql://user:password@localhost/database"
```

**B. Create database if missing:**
```bash
mysql -u root -p -e "CREATE DATABASE agentic_rag;"
```

**C. Use SQLite fallback:**
```bash
# If MySQL unavailable, system will use SQLite
# No configuration needed - automatic fallback
```

---

### 10. WebSearch/Web Scraping Failures

**Symptoms:**
- Web search returns no results
- Website lookup fails
- Timeout errors on web requests

**Diagnosis:**
```bash
# Test web search directly
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Search the web for python programming tutorials",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'

# Check internet connectivity
ping google.com
curl -I https://duckduckgo.com
```

**Solutions:**

**A. Check network connectivity:**
```bash
# Test if behind firewall/proxy
export HTTP_PROXY=http://your-proxy:8080
export HTTPS_PROXY=http://your-proxy:8080
```

**B. Update web scraping dependencies:**
```bash
pip install --upgrade ddgs beautifulsoup4 requests
```

**C. Handle rate limiting:**
```bash
# Web search tools have built-in delays
# If rate limited, wait and retry
```

---

## Emergency Procedures

### Complete System Reset

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

### Data Recovery

If document index is corrupted:

```bash
# 1. Backup current index
cp document_store/faiss.index document_store/faiss.index.backup
cp document_store/metadata.db document_store/metadata.db.backup

# 2. Restore from backup if available
ls document_store/*.backup*
# cp document_store/faiss.index.backup.YYYYMMDD document_store/faiss.index

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

## Getting Help

### Log Analysis

**Key log locations:**
- **Main server**: `logs/server_complete.log`
- **Ollama service**: `sudo journalctl -u ollama -f`
- **System logs**: `/var/log/syslog`

**Important log patterns to search for:**
```bash
# Errors
grep -i "error\|failed\|exception" logs/server_complete.log

# Tool calling issues
grep -i "tool.*call\|tool.*error" logs/server_complete.log

# Performance issues
grep -i "timeout\|slow\|memory" logs/server_complete.log

# Embedding issues  
grep -i "embed\|faiss\|document" logs/server_complete.log
```

### Performance Profiling

```bash
# CPU usage
top -p $(pgrep -f fastapi_server_complete.py)

# Memory detailed analysis
pmap $(pgrep -f fastapi_server_complete.py)

# Network connections
netstat -tlnp | grep python

# Disk I/O
iotop -p $(pgrep -f fastapi_server_complete.py)
```

### Creating Bug Reports

When reporting issues, include:

1. **System info:**
   ```bash
   uname -a
   python3 --version
   ollama version
   curl --version
   ```

2. **Server status:**
   ```bash
   ./testing/quick_health_check.sh > health_report.txt
   ```

3. **Recent logs:**
   ```bash
   tail -100 logs/server_complete.log > recent_logs.txt
   ```

4. **Configuration:**
   ```bash
   env | grep -E "(GMAIL|OLLAMA|DATABASE)" > config.txt
   ```

5. **Reproduction steps:**
   - Exact curl command that fails
   - Expected vs actual behavior
   - Error messages

---

This troubleshooting guide covers the most common issues. For complex problems, run the comprehensive test suite first to identify the specific component that's failing, then follow the relevant troubleshooting section.