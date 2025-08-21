# Agentic RAG System - Developer API Reference

## Overview

This comprehensive guide provides detailed documentation, examples, and debugging information for all endpoints in the Agentic RAG System. Each endpoint includes curl examples, response formats, error handling, and debugging steps.

**Base URL**: `http://localhost:5000`

---

## Table of Contents

1. [Core LLM Endpoints](#core-llm-endpoints)
2. [OpenAI Compatibility Endpoints](#openai-compatibility-endpoints)  
3. [Document Processing System](#document-processing-system)
4. [System Management](#system-management)
5. [Monitoring & Metrics](#monitoring--metrics)
6. [Debugging & Troubleshooting](#debugging--troubleshooting)
7. [Testing Framework](#testing-framework)

---

## Core LLM Endpoints

### 1. Basic Prompt Processing

**Endpoint**: `POST /llama3_1b/prompt`

Simple text processing without tool calling.

```bash
curl -X POST "http://localhost:5000/llama3_1b/prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is artificial intelligence?",
    "model": "qwen3:8b",
    "max_tokens": 500,
    "temperature": 0.7
  }'
```

**Response Format**:
```json
{
  "response": "AI is a broad field of computer science...",
  "model": "qwen3:8b",
  "tokens_used": 245,
  "processing_time": 3.2
}
```

**Debugging**:
- Check Ollama service: `ollama ps`
- Verify model availability: `ollama list`
- View server logs: `tail -f server_complete.log`

---

### 2. Streaming with Tool Calling

**Endpoint**: `POST /llama3_1b/stream`

Advanced processing with full tool calling capabilities.

```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Get the latest news about artificial intelligence and summarize it",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": true,
    "system": "You are a helpful AI assistant with access to real-time information."
  }'
```

**Key Parameters**:
- `toolsInUse`: Enable 11-tool system (required for most functionality)
- `stream`: Enable real-time response streaming
- `system`: Custom system prompt override
- `temperature`: Control randomness (0.0-1.0)
- `max_tokens`: Limit response length
- `conversation_id`: Enable conversation memory

**Available Tools**:
1. `get_the_secret_tool` - Current date/time
2. `get_news_summaries` - News with full article content
3. `search_web` - DuckDuckGo web search
4. `lookup_website` - Website/PDF content extraction
5. `wikipedia_query` - Wikipedia information
6. `get_stock_and_company_data` - Financial data
7. `calculator` - Mathematical calculations
8. `stock_analyzer` - Financial analysis
9. `google_calendar_scheduler` - Calendar management
10. `secure_email_sender` - Email with attachments
11. `sandboxed_executor` - Code execution & file operations

**Example with Conversation Memory**:
```bash
# First message
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hi, I am working on a machine learning project about NLP",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "conversation_id": "ml_project_123"
  }'

# Follow-up message (remembers context)
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the latest research papers on this topic?",
    "model": "qwen3:8b", 
    "toolsInUse": true,
    "conversation_id": "ml_project_123"
  }'
```

**Non-Streaming Mode**:
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze AAPL stock and email the report to investor@company.com",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'
```

---

## OpenAI Compatibility Endpoints

### 1. List Available Models

**Endpoint**: `GET /v1/models`

```bash
curl "http://localhost:5000/v1/models"
```

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "Agentic-RAG-Model1",
      "object": "model",
      "created": 1755089362,
      "owned_by": "local"
    },
    {
      "id": "Agentic-RAG-Model2", 
      "object": "model",
      "created": 1755089362,
      "owned_by": "local"
    }
  ]
}
```

### 2. Chat Completions (OpenAI Compatible)

**Endpoint**: `POST /v1/chat/completions`

Full OpenAI API compatibility with agentic capabilities.

```bash
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [
      {"role": "user", "content": "Research the latest developments in quantum computing and create a summary report"}
    ],
    "stream": true
  }'
```

**Non-Streaming**:
```bash
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [
      {"role": "user", "content": "What is the current stock price of TSLA?"}
    ],
    "stream": false
  }'
```

**OpenAI Response Format**:
```json
{
  "id": "chatcmpl-1755089514",
  "object": "chat.completion",
  "created": 1755089514,
  "model": "Agentic-RAG-Model1",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Based on the latest data, Tesla (TSLA) is currently trading at..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 127,
    "total_tokens": 142
  }
}
```

**Security Note**: The OpenAI compatibility layer uses zero-trust security - all parameters except the user message are ignored, ensuring consistent agentic behavior.

**⚠️ Important Limitation v0.8**: OpenAI models can only be used for tool calling, NOT as primary LLM. The OpenAI endpoints route primary LLM requests to the configured Ollama primary model due to architectural limitations.

---

## Document Processing System

The document processing system provides advanced RAG capabilities with FAISS indexing, embedding generation, and intelligent document search.

### 1. Index Directory

**Endpoint**: `POST /documents/index-directory`

Process and index all documents in a directory for searchable retrieval.

```bash
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/documents",
    "recursive": true,
    "file_types": ["pdf", "docx", "txt", "md"],
    "chunk_size": 1000,
    "chunk_overlap": 200
  }'
```

**Response**:
```json
{
  "status": "success",
  "processed_files": 45,
  "total_chunks": 1247,
  "processing_time": 23.4,
  "indexed_types": ["pdf", "docx", "txt", "md"],
  "faiss_index_size": "2562 vectors"
}
```

**Supported File Types**:
- PDF documents (text extraction)
- Microsoft Word (.docx)
- Excel spreadsheets (.xlsx)
- Text files (.txt, .md)
- HTML files
- Images (OCR with tesseract)

---

### 2. Document Search

**Endpoint**: `POST /documents/search`

Semantic search across indexed documents using vector similarity.

```bash
curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms for natural language processing",
    "max_results": 5,
    "similarity_threshold": 0.7,
    "include_metadata": true
  }'
```

**Response**:
```json
{
  "results": [
    {
      "chunk_id": "doc1_chunk_5",
      "content": "Machine learning approaches to NLP have revolutionized...",
      "similarity_score": 0.89,
      "document_path": "/docs/ml_paper.pdf",
      "chunk_index": 5,
      "metadata": {
        "page": 12,
        "section": "Methodology",
        "created_at": "2025-08-13T10:30:00"
      }
    }
  ],
  "total_found": 12,
  "query_time": 0.045
}
```

---

### 3. Document Interrogation

**Endpoint**: `POST /documents/interrogate`

Advanced document analysis with specific questions.

```bash
curl -X POST "http://localhost:5000/documents/interrogate" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main conclusions about AI safety in these documents?",
    "document_filter": "*.pdf",
    "max_context_chunks": 10,
    "use_llm_analysis": true
  }'
```

---

### 4. Directory Watching

**Endpoint**: `POST /documents/watch-directory`

Set up automatic indexing for directory changes.

```bash
curl -X POST "http://localhost:5000/documents/watch-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/watch",
    "recursive": true,
    "auto_index": true,
    "scan_interval": 300
  }'
```

**Stop Watching**:
```bash
curl -X POST "http://localhost:5000/documents/stop-watching" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/watch"
  }'
```

---

### 5. Document Statistics

**Endpoint**: `GET /documents/stats`

Get comprehensive statistics about indexed documents.

```bash
curl "http://localhost:5000/documents/stats"
```

**Response**:
```json
{
  "total_documents": 156,
  "total_chunks": 4523,
  "index_size_mb": 23.4,
  "file_types": {
    "pdf": 89,
    "docx": 34,
    "txt": 28,
    "md": 5
  },
  "embedding_model": "mxbai-embed-large",
  "last_update": "2025-08-13T11:45:23",
  "watched_directories": 2,
  "indexing_status": "idle"
}
```

---

### 6. Configuration Management

**Endpoint**: `GET /documents/config`

```bash
curl "http://localhost:5000/documents/config"
```

**Add Directory to Watch List**:
```bash
curl -X POST "http://localhost:5000/documents/config/add-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/new/documents/path",
    "recursive": true,
    "description": "Research papers collection",
    "auto_scan": true
  }'
```

**Remove Directory**:
```bash
curl -X POST "http://localhost:5000/documents/config/remove-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/old/documents/path"
  }'
```

**Scan for Changes**:
```bash
curl -X POST "http://localhost:5000/documents/config/scan-changes" \
  -H "Content-Type: application/json" \
  -d '{
    "force_rescan": false,
    "notify_on_changes": true
  }'
```

**Response**:
```json
{
  "status": "success",
  "changes_detected": 5,
  "new_files": 3,
  "modified_files": 2,
  "deleted_files": 0,
  "scan_time": 1.23
}
```

---

## System Management

### 1. Health Check

**Endpoint**: `GET /health`

```bash
curl "http://localhost:5000/health"
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-13T11:30:00Z",
  "version": "0.8.1",
  "services": {
    "ollama": "connected",
    "database": "connected", 
    "document_system": "ready",
    "embedding_service": "healthy"
  },
  "uptime": "2h 15m 30s"
}
```

---

### 2. System Information

**Endpoint**: `GET /`

```bash
curl "http://localhost:5000/"
```

---

### 3. Available Models

**Endpoint**: `GET /ollama/models`

```bash
curl "http://localhost:5000/ollama/models"
```

---

### 4. System Prompts

**Endpoint**: `POST /retrieve_system_prompts`

```bash
curl -X POST "http://localhost:5000/retrieve_system_prompts" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Monitoring & Metrics

### 1. System Metrics

**Endpoint**: `GET /metrics`

```bash
curl "http://localhost:5000/metrics"
```

**Response**:
```json
{
  "requests_total": 1547,
  "requests_per_minute": 12.3,
  "average_response_time": 2.4,
  "tool_calls_total": 892,
  "active_conversations": 5,
  "cache_hit_rate": 0.73,
  "embedding_requests": 234,
  "document_searches": 67,
  "memory_usage_mb": 1024,
  "uptime_seconds": 8100
}
```

---

### 2. Optimization Control

**Get Status**:
```bash
curl "http://localhost:5000/optimization/status"
```

**Enable Optimization**:
```bash
curl -X POST "http://localhost:5000/optimization/enable" \
  -H "Content-Type: application/json" \
  -d '{
    "features": ["response_streaming", "buffer_optimization"],
    "rollout_percentage": 50
  }'
```

**Disable Optimization**:
```bash
curl -X POST "http://localhost:5000/optimization/disable" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Performance issues detected"
  }'
```

**Gradual Rollout**:
```bash
curl -X POST "http://localhost:5000/optimization/rollout" \
  -H "Content-Type: application/json" \
  -d '{
    "target_percentage": 100,
    "rollout_speed": "fast"
  }'
```

**Emergency Rollback**:
```bash
curl -X POST "http://localhost:5000/optimization/emergency-rollback" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Critical performance degradation"
  }'
```

---

### 3. Phase 2B Advanced Features

**Get Phase 2B Status**:
```bash
curl "http://localhost:5000/phase2b/status"
```

**Enable Specific Feature**:
```bash
curl -X POST "http://localhost:5000/phase2b/feature/response_streaming/enable" \
  -H "Content-Type: application/json" \
  -d '{
    "rollout_percentage": 25,
    "monitoring_level": "verbose"
  }'
```

**Disable Specific Feature**:
```bash
curl -X POST "http://localhost:5000/phase2b/feature/buffer_optimization/disable" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Memory usage too high"
  }'
```

**Get Available Checkpoints**:
```bash
curl "http://localhost:5000/phase2b/checkpoints"
```

**Rollback to Checkpoint**:
```bash
curl -X POST "http://localhost:5000/phase2b/rollback/phase2a_baseline" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Rollback to stable version",
    "force": false
  }'
```

**Emergency Rollback**:
```bash
curl -X POST "http://localhost:5000/phase2b/rollback/emergency" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "System instability detected"
  }'
```

**Clear Emergency State**:
```bash
curl -X POST "http://localhost:5000/phase2b/rollback/clear-emergency" \
  -H "Content-Type: application/json" \
  -d '{
    "confirmed": true,
    "operator": "admin"
  }'
```

---

## Debugging & Troubleshooting

### Common Issues & Solutions

#### 1. Embedding Service Issues

**Problem**: Document search failing or slow embedding generation

**Debug Steps**:
```bash
# Check embedding service health
curl "http://localhost:5000/documents/stats"

# Test embedding generation
curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test query",
    "max_results": 1
  }'

# Check server logs for embedding errors
tail -f server_complete.log | grep -i embed
```

**Common Solutions**:
- Restart Ollama: `sudo systemctl restart ollama`
- Check embedding model: `ollama list | grep embed`
- Verify disk space for FAISS index files

#### 2. Tool Calling Failures

**Problem**: Tools not being called or returning errors

**Debug Steps**:
```bash
# Test individual tool availability
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the current date and time?",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }'

# Check tool model health
ollama ps

# Verify tool model system prompt
curl -X POST "http://localhost:5000/retrieve_system_prompts"
```

#### 3. Memory Issues

**Problem**: Server running out of memory

**Debug Steps**:
```bash
# Check system memory
free -h

# Monitor server memory usage
curl "http://localhost:5000/metrics" | jq '.memory_usage_mb'

# Check Ollama memory usage
ollama ps
```

#### 4. Connection Issues

**Problem**: Database or external service connection failures

**Debug Steps**:
```bash
# Test basic connectivity
curl "http://localhost:5000/health"

# Check specific service status
curl "http://localhost:5000/health" | jq '.services'
```

---

## Testing Framework

### Quick Verification Tests

**Test 1: Basic Connectivity**
```bash
curl -f "http://localhost:5000/health" && echo "✅ Server responding" || echo "❌ Server not responding"
```

**Test 2: Tool Calling System**
```bash
curl -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What time is it?",
    "model": "qwen3:8b",
    "toolsInUse": true,
    "stream": false
  }' | jq '.response' | grep -q "$(date +%Y)" && echo "✅ Tool calling works" || echo "❌ Tool calling failed"
```

**Test 3: Document Search**
```bash
curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "max_results": 1
  }' | jq '.results | length' | grep -q "1" && echo "✅ Document search works" || echo "❌ Document search failed"
```

**Test 4: Embedding Service**
```bash
curl "http://localhost:5000/documents/stats" | jq '.total_chunks' | grep -q "[0-9]" && echo "✅ Embedding service healthy" || echo "❌ Embedding service issues"
```

**Test 5: OpenAI Compatibility**
```bash
curl -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }' | jq '.choices[0].message.content' | grep -q "." && echo "✅ OpenAI compatibility works" || echo "❌ OpenAI compatibility failed"
```

### Comprehensive Test Suite

**Run All Tests**:
```bash
#!/bin/bash
echo "🧪 Running Agentic RAG System Test Suite"
echo "========================================"

# Test 1: Server Health
echo -n "Testing server health... "
curl -s -f "http://localhost:5000/health" > /dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: Model Availability  
echo -n "Testing Ollama models... "
curl -s "http://localhost:5000/ollama/models" | jq '.models | length' | grep -q "[1-9]" && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Basic Tool Calling
echo -n "Testing tool calling system... "
RESPONSE=$(curl -s -X POST "http://localhost:5000/llama3_1b/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the current date?",
    "model": "qwen3:8b", 
    "toolsInUse": true,
    "stream": false
  }')
echo "$RESPONSE" | jq -r '.response' | grep -q "$(date +%Y)" && echo "✅ PASS" || echo "❌ FAIL"

# Test 4: Document System
echo -n "Testing document search... "
curl -s -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "max_results": 1}' | jq '.results' > /dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Test 5: OpenAI Compatibility
echo -n "Testing OpenAI compatibility... "
curl -s -X POST "http://localhost:5000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Agentic-RAG-Model1",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }' | jq '.choices[0]' > /dev/null && echo "✅ PASS" || echo "❌ FAIL"

echo "========================================"
echo "🎉 Test suite complete!"
```

Save as `test_comprehensive.sh` and run with `chmod +x test_comprehensive.sh && ./test_comprehensive.sh`

---

## Performance Benchmarking

### Load Testing

**Test concurrent requests**:
```bash
# Install apache bench if needed: sudo apt install apache2-utils

# Test 100 requests with 10 concurrent connections
ab -n 100 -c 10 -T "application/json" -p test_payload.json "http://localhost:5000/llama3_1b/stream"
```

**Create test_payload.json**:
```json
{
  "prompt": "What is artificial intelligence?",
  "model": "qwen3:8b",
  "toolsInUse": false,
  "stream": false
}
```

---

## Environment Variables

**Required for Full Functionality**:
```bash
# Email tool configuration
export GMAIL_SENDER_EMAIL="your-agent@gmail.com"
export GMAIL_APP_PASSWORD="your-16-char-app-password"

# Ollama configuration
export OLLAMA_BASE_URL="http://127.0.0.1:11434"

# Database (optional)
export DATABASE_URL="mysql://user:pass@localhost/db"

# Document processing
export TESSDATA_PREFIX="/usr/share/tesseract-ocr/4.00/tessdata/"
```

---

## API Response Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid request format or parameters |
| 404 | Not Found | Endpoint not found |
| 500 | Internal Server Error | Server processing error |
| 502 | Bad Gateway | Ollama service unavailable |
| 503 | Service Unavailable | System temporarily unavailable |

---

## Rate Limits

**Default Limits**:
- 100 requests per minute per IP for basic endpoints
- 20 requests per minute for tool calling endpoints
- 10 requests per minute for document processing endpoints

**Custom limits** can be configured via environment variables.

---

This completes the comprehensive API reference. For additional support, check the troubleshooting section or review server logs at `server_complete.log`.