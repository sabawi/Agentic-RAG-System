# Embedding Service Debugging Guide

## Overview

The Agentic RAG System uses a sophisticated embedding service for document indexing, semantic search, and retrieval. This guide provides comprehensive debugging, testing, and troubleshooting information for the embedding system.

**Key Components**:
- **FAISS Vector Index** - High-performance similarity search
- **Ollama Embedding Model** - `mxbai-embed-large` for text embeddings
- **Document Processor** - Handles PDF, DOCX, TXT, MD, HTML, images (OCR)
- **Automatic Directory Watcher** - Real-time document indexing

---

## Architecture Overview

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

---

## Quick Health Check

### 1. Basic System Status

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
  "last_update": "2025-08-13T11:45:23"
}
```

**Problem Indicators**:
- `total_chunks: 0` - No documents indexed
- `indexing_status: "error"` - Processing failures
- Missing `embedding_model` - Service not initialized

### 2. Embedding Service Health Test

```bash
curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test embedding functionality",
    "max_results": 1
  }'
```

**Healthy Response** (even with no results):
```json
{
  "results": [],
  "total_found": 0,
  "query_time": 0.045,
  "query_embedding_time": 0.023
}
```

**Problem Response**:
```json
{
  "error": "Embedding service unhealthy, attempting restart...",
  "status": 500
}
```

---

## Component Testing

### 1. Ollama Embedding Model

**Test Ollama Service**:
```bash
# Check if embedding model is loaded
ollama ps

# Expected output should include:
# NAME                    ID              SIZE      PROCESSOR    CONTEXT    UNTIL
# mxbai-embed-large      468836162de7    669 MB    CPU          -          4 minutes from now
```

**Test Direct Embedding Generation**:
```bash
curl http://localhost:11434/api/embeddings \
  -d '{
    "model": "mxbai-embed-large",
    "prompt": "test embedding generation"
  }'
```

**Expected Response**:
```json
{
  "embedding": [-0.123, 0.456, -0.789, ...]  // 1024-dimensional vector
}
```

**Troubleshooting Ollama Embedding**:

**Problem**: Model not loaded
```bash
# Solution: Pull the embedding model
ollama pull mxbai-embed-large
```

**Problem**: Ollama service down
```bash
# Check service status
sudo systemctl status ollama

# Restart if needed
sudo systemctl restart ollama
```

**Problem**: Model runner crashes
```bash
# Check system resources
free -h
nvidia-smi  # if using GPU

# Check Ollama logs
sudo journalctl -u ollama -f --lines=50
```

---

### 2. FAISS Index Testing

**Check Index Files**:
```bash
ls -la document_store/
# Should show:
# faiss.index          - Main vector index
# metadata.db          - SQLite metadata database
# *.backup.*           - Backup files
```

**Test Index Loading**:
```bash
curl "http://localhost:5000/documents/stats" | jq '.index_size_mb'
# Should return a positive number, not 0
```

**Manual Index Verification**:
```python
# Python script to verify FAISS index
import faiss
import numpy as np

try:
    index = faiss.read_index("document_store/faiss.index")
    print(f"✅ Index loaded successfully")
    print(f"   Vectors: {index.ntotal}")
    print(f"   Dimensions: {index.d}")
    
    # Test search with random vector
    test_vector = np.random.random((1, index.d)).astype('float32')
    distances, indices = index.search(test_vector, 1)
    print(f"✅ Search test passed")
    
except Exception as e:
    print(f"❌ Index error: {e}")
```

---

### 3. Document Processing Testing

**Test Single File Processing**:
```bash
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/single/document.pdf",
    "recursive": false
  }'
```

**Monitor Processing**:
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

---

## Advanced Debugging

### 1. Embedding Generation Performance

**Test Embedding Speed**:
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

**Slow Performance Causes**:
- CPU overload (check `htop`)
- Disk I/O issues (check `iostat`)
- Large index size (>1GB may slow searches)
- Network latency to Ollama service

### 2. Memory Usage Analysis

**Check Memory Usage**:
```bash
# Server memory usage
curl "http://localhost:5000/metrics" | jq '.memory_usage_mb'

# System memory
free -h

# Process-specific memory
ps aux | grep python | grep fastapi
```

**Memory Issues**:
- **FAISS Index**: ~1MB per 1000 document chunks
- **Embedding Model**: ~669MB when loaded
- **Document Processing**: Temporary spike during large file processing

### 3. Database Debugging

**SQLite Metadata Inspection**:
```bash
sqlite3 document_store/metadata.db "SELECT COUNT(*) FROM chunks;"
sqlite3 document_store/metadata.db "SELECT document_path, chunk_count FROM documents LIMIT 5;"
```

**Database Schema**:
```sql
-- View table structure
sqlite3 document_store/metadata.db ".schema"

-- Check for corruption
sqlite3 document_store/metadata.db "PRAGMA integrity_check;"
```

---

## Common Issues & Solutions

### Issue 1: "Embedding service unhealthy"

**Symptoms**:
- Document search returns errors
- Processing gets stuck
- Log shows embedding restart attempts

**Debug Steps**:
```bash
# 1. Check Ollama status
ollama ps

# 2. Test direct embedding
curl http://localhost:11434/api/embeddings -d '{"model": "mxbai-embed-large", "prompt": "test"}'

# 3. Check server logs
tail -f logs/server_complete.log | grep -i embed
```

**Solutions**:
```bash
# Solution A: Restart Ollama
sudo systemctl restart ollama
ollama pull mxbai-embed-large  # Ensure model is available

# Solution B: Check system resources
free -h  # Ensure sufficient memory
df -h    # Check disk space

# Solution C: Clear embedding cache (if corrupted)
rm -rf /tmp/embedding_cache_*
```

### Issue 2: Document processing fails

**Symptoms**:
- Files not being indexed
- Processing hangs
- Error in logs about file reading

**Debug Steps**:
```bash
# 1. Test file permissions
ls -la /path/to/documents/

# 2. Test file type support
file /path/to/documents/sample.pdf

# 3. Manual processing test
python3 -c "
from document_interrogator import DocumentInterrogator
di = DocumentInterrogator()
result = di.process_file('/path/to/test.pdf')
print(result)
"
```

**Solutions**:
```bash
# Solution A: Fix permissions
chmod 644 /path/to/documents/*

# Solution B: Install missing dependencies
pip install PyPDF2 python-docx openpyxl pytesseract

# Solution C: Check file corruption
pdfinfo /path/to/document.pdf  # For PDFs
```

### Issue 3: Search returns no results

**Symptoms**:
- All searches return empty results
- Index appears healthy
- No processing errors

**Debug Steps**:
```bash
# 1. Verify index has content
curl "http://localhost:5000/documents/stats" | jq '.total_chunks'

# 2. Test with simple query
curl -X POST "http://localhost:5000/documents/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "similarity_threshold": 0.0, "max_results": 10}'

# 3. Check embedding dimensions match
python3 -c "
import faiss
index = faiss.read_index('document_store/faiss.index')
print(f'Index dimensions: {index.d}')
print(f'Total vectors: {index.ntotal}')
"
```

**Solutions**:
```bash
# Solution A: Lower similarity threshold
# Use similarity_threshold: 0.0 in search requests

# Solution B: Rebuild index (if corrupted)
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "/your/docs", "force_rebuild": true}'

# Solution C: Check embedding model consistency
ollama list | grep embed
```

### Issue 4: Slow indexing performance

**Symptoms**:
- Document processing takes very long
- High CPU usage during indexing
- Memory usage constantly increasing

**Debug Steps**:
```bash
# 1. Monitor resource usage
htop  # Check CPU usage
iotop  # Check disk I/O

# 2. Check batch sizes
curl "http://localhost:5000/documents/stats" | jq '.'

# 3. Profile embedding generation
time curl http://localhost:11434/api/embeddings -d '{"model": "mxbai-embed-large", "prompt": "test"}'
```

**Solutions**:
```bash
# Solution A: Adjust batch size
# Modify document_interrogator.py batch_size parameter

# Solution B: Process smaller directories
# Split large document collections into smaller batches

# Solution C: Optimize system resources
# Ensure sufficient RAM, consider SSD storage
```

---

## Maintenance Procedures

### 1. Regular Health Checks

**Daily Check Script**:
```bash
#!/bin/bash
echo "🔍 Daily Embedding Service Check - $(date)"
echo "============================================"

# Check service status
echo -n "Embedding service status: "
if curl -s "http://localhost:5000/documents/stats" > /dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Failed"
fi

# Check index size
echo -n "Index size: "
curl -s "http://localhost:5000/documents/stats" | jq -r '.index_size_mb' | head -1
echo " MB"

# Check document count
echo -n "Total documents: "
curl -s "http://localhost:5000/documents/stats" | jq -r '.total_documents'

# Check recent activity
echo -n "Last update: "
curl -s "http://localhost:5000/documents/stats" | jq -r '.last_update'

echo "============================================"
```

### 2. Backup Procedures

**Manual Backup**:
```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup FAISS index
cp document_store/faiss.index backups/$(date +%Y%m%d)/
cp document_store/metadata.db backups/$(date +%Y%m%d)/

# Backup configuration
cp watched_directories.json backups/$(date +%Y%m%d)/
```

**Automated Backup Script**:
```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup core files
cp document_store/faiss.index "$BACKUP_DIR/"
cp document_store/metadata.db "$BACKUP_DIR/"
cp watched_directories.json "$BACKUP_DIR/"

# Create status report
curl -s "http://localhost:5000/documents/stats" > "$BACKUP_DIR/stats.json"

echo "✅ Backup created: $BACKUP_DIR"
```

### 3. Index Optimization

**Rebuild Index** (when performance degrades):
```bash
# Stop watching directories
curl -X POST "http://localhost:5000/documents/stop-watching" \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "all"}'

# Backup current index
mv document_store/faiss.index document_store/faiss.index.backup

# Rebuild from scratch
curl -X POST "http://localhost:5000/documents/index-directory" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/your/document/root",
    "recursive": true,
    "force_rebuild": true
  }'
```

---

## Performance Tuning

### 1. Embedding Model Optimization

**CPU Optimization**:
```bash
# Set Ollama to use specific CPU cores
export OLLAMA_NUM_PARALLEL=4  # Match CPU core count
export OLLAMA_MAX_LOADED_MODELS=2
```

**Memory Optimization**:
```bash
# Limit memory usage
export OLLAMA_MAX_LOADED_MODELS=1  # Keep only essential models loaded
```

### 2. FAISS Index Tuning

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

### 3. System-Level Optimizations

**Disk I/O**:
```bash
# Use SSD storage for index files
# Mount with proper filesystem options
mount -o noatime,data=ordered /dev/ssd /path/to/document_store/
```

**Memory**:
```bash
# Increase file cache
echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf
```

---

## Monitoring & Alerting

### 1. Key Metrics to Monitor

**Service Metrics**:
- Embedding generation time (< 100ms per request)
- Search response time (< 200ms)
- Index size growth rate
- Document processing throughput
- Error rates in logs

**System Metrics**:
- Memory usage (should be stable)
- CPU usage during indexing
- Disk space for index storage
- Network latency to Ollama

### 2. Alert Conditions

```bash
# Critical alerts
curl "http://localhost:5000/documents/stats" | jq '.indexing_status' | grep -q "error" && echo "ALERT: Indexing errors"

# Performance alerts
QUERY_TIME=$(curl -s -w "%{time_total}" -X POST "http://localhost:5000/documents/search" -H "Content-Type: application/json" -d '{"query": "test", "max_results": 1}' -o /dev/null)
if (( $(echo "$QUERY_TIME > 1.0" | bc -l) )); then
    echo "ALERT: Slow query performance: ${QUERY_TIME}s"
fi
```

---

## Development & Testing

### 1. Unit Tests for Embedding Service

```bash
# Create test file
cat > test_embedding_service.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_embedding_health():
    response = requests.get(f"{BASE_URL}/documents/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_chunks" in data
    print("✅ Embedding health check passed")

def test_search_functionality():
    payload = {
        "query": "test search functionality", 
        "max_results": 1
    }
    response = requests.post(f"{BASE_URL}/documents/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "query_time" in data
    print("✅ Search functionality test passed")

def test_performance():
    start_time = time.time()
    payload = {"query": "performance test", "max_results": 5}
    response = requests.post(f"{BASE_URL}/documents/search", json=payload)
    end_time = time.time()
    
    assert response.status_code == 200
    assert end_time - start_time < 1.0  # Should complete in under 1 second
    print(f"✅ Performance test passed: {end_time - start_time:.3f}s")

if __name__ == "__main__":
    test_embedding_health()
    test_search_functionality()
    test_performance()
    print("🎉 All embedding service tests passed!")
EOF

python3 test_embedding_service.py
```

### 2. Load Testing

```bash
# Install hey for load testing
go install github.com/rakyll/hey@latest

# Test concurrent searches
echo '{"query": "load test query", "max_results": 5}' > search_payload.json

hey -n 100 -c 10 -T "application/json" -D search_payload.json \
  "http://localhost:5000/documents/search"
```

---

This comprehensive guide covers all aspects of debugging, testing, and maintaining the embedding service. For additional support, check the main server logs and ensure all dependencies are properly installed.