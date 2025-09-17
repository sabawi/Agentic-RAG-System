# Testing Framework Overview

## Quick Start

**For immediate system verification:**
```bash
./quick_health_check.sh
```

**For comprehensive testing:**
```bash
./comprehensive_test_suite.sh all
```

**For specific component testing:**
```bash
./test_embedding_service.sh        # Document processing & search
./test_api_endpoints.sh             # All API endpoints
```

---

## Available Test Scripts

### 1. `quick_health_check.sh`
**Purpose**: Fast 30-second system verification  
**Use Case**: Daily health monitoring, post-deployment checks  
**What it tests**:
- Server responding
- Ollama service
- Basic tool calling
- Document search
- OpenAI compatibility
- Memory usage

**Example Output:**
```
🚀 Agentic RAG System - Quick Health Check
==========================================
Server responding... ✅ OK
Ollama service... ✅ OK
Tool calling system... ✅ OK
Document search... ✅ OK
OpenAI compatibility... ✅ OK
Memory usage... ✅ OK (1024MB)
```

### 2. `comprehensive_test_suite.sh`
**Purpose**: Full system testing with detailed reporting  
**Use Case**: Pre-production validation, debugging complex issues  
**Test Categories**:
- Basic connectivity
- Ollama integration  
- Tool calling system
- Document processing
- OpenAI compatibility
- Performance testing
- Email system
- Error handling
- Conversation memory

**Usage:**
```bash
./comprehensive_test_suite.sh [category]

# Test specific category
./comprehensive_test_suite.sh tools
./comprehensive_test_suite.sh documents
./comprehensive_test_suite.sh performance

# Test everything (default)
./comprehensive_test_suite.sh all
```

### 3. `test_embedding_service.sh`
**Purpose**: Deep testing of document processing and search  
**Use Case**: Debugging search issues, validating document indexing  
**What it tests**:
- Embedding service health
- Ollama embedding model
- Document search functionality
- Search performance (5 iterations)
- Document interrogation
- FAISS index integrity
- Metadata database
- Memory usage during search
- Error handling
- Directory watching

### 4. `test_api_endpoints.sh`
**Purpose**: Comprehensive API endpoint validation  
**Use Case**: API compatibility testing, endpoint regression testing  
**Endpoints Tested**:
- Core LLM endpoints (`/llama3_1b/prompt`, `/llama3_1b/stream`)
- OpenAI compatibility (`/v1/models`, `/v1/chat/completions`)
- Document processing (`/documents/*`)
- System management (`/health`, `/metrics`)
- Error handling (404s, malformed JSON)
- Performance (concurrent requests)

---

## Test Reports

All test scripts generate detailed logs:
- `tests/results/test_results_YYYYMMDD_HHMMSS.log` (comprehensive suite)
- `tests/results/embedding_test_YYYYMMDD_HHMMSS.log` (embedding service)
- `tests/results/api_endpoints_test_YYYYMMDD_HHMMSS.log` (API endpoints)

**Example Report:**
```
📊 Test Results Summary
======================
Tests completed: 45
Passed: 42
Failed: 1
Warnings: 2

🚨 Failed Tests:
  ❌ OpenAI agentic capabilities failed

⚠️ Warnings:
  ⚠️ High memory usage detected
  ⚠️ Document interrogation may have issues
```

---

## Integration with Documentation

**For API issues** → See [Developer API Reference](../DEVELOPER_API_REFERENCE.md)  
**For embedding problems** → See [Embedding Service Debug Guide](../EMBEDDING_SERVICE_DEBUG_GUIDE.md)  
**For general issues** → See [Troubleshooting Guide](../TROUBLESHOOTING_GUIDE.md)

---

## CI/CD Integration

**GitHub Actions Example:**
```yaml
name: Agentic RAG Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          # Setup Ollama, etc.
      - name: Run health check
        run: ./testing/quick_health_check.sh
      - name: Run comprehensive tests
        run: ./testing/comprehensive_test_suite.sh
```

**Pre-commit Hook:**
```bash
#!/bin/bash
# .git/hooks/pre-commit
cd testing/
if ! ./quick_health_check.sh; then
    echo "❌ Health check failed - commit aborted"
    exit 1
fi
```

---

## Legacy Python Tests

**Still available for compatibility:**
```bash
python test_fastapi.py              # Basic functionality tests
python test_tool_calling.py         # Tool calling system tests  
python test_comprehensive_news.py   # News function tests
python test_6_tools.py              # Individual tool tests
```

**Migration Note**: New shell-based tests are more comprehensive and provide better curl examples for developers.

---

## Test Development Guidelines

**When adding new tests:**

1. **For new endpoints**: Add to `test_api_endpoints.sh`
2. **For embedding features**: Add to `test_embedding_service.sh`  
3. **For quick checks**: Add to `quick_health_check.sh`
4. **For complex scenarios**: Add to `comprehensive_test_suite.sh`

**Test format:**
```bash
# Test description
echo -e "\nTest N: Feature Description"
TEST_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/endpoint")
HTTP_CODE=$(echo "$TEST_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)

if [ "$HTTP_CODE" = "200" ]; then
    success "Test passed"
else
    error "Test failed (HTTP: $HTTP_CODE)"
fi
```

---

This testing framework provides comprehensive coverage with easy-to-use tools for developers at all levels. The combination of quick health checks and detailed component testing ensures both rapid feedback and thorough validation.