#!/bin/bash

# API Endpoints Comprehensive Testing
# Tests all endpoints with proper curl commands and validation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost:5000"
TEST_LOG="api_endpoints_test_$(date +%Y%m%d_%H%M%S).log"

success() { echo -e "${GREEN}✅ $1${NC}" | tee -a "$TEST_LOG"; }
error() { echo -e "${RED}❌ $1${NC}" | tee -a "$TEST_LOG"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$TEST_LOG"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$TEST_LOG"; }

echo "🌐 API Endpoints Comprehensive Test Suite"
echo "========================================"

# Test Core LLM Endpoints
echo "=== Core LLM Endpoints ==="

# 1. Basic prompt endpoint
echo -e "\nTesting POST /llama3_1b/prompt"
BASIC_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST "$BASE_URL/llama3_1b/prompt" \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "What is 2+2? Just give me the number.",
        "model": "qwen3:8b",
        "max_tokens": 100
    }')

HTTP_CODE=$(echo "$BASIC_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
RESPONSE_BODY=$(echo "$BASIC_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | jq -e '.response' | grep -q "4"; then
    success "Basic prompt endpoint works"
else
    error "Basic prompt endpoint failed (HTTP: $HTTP_CODE)"
    echo "$RESPONSE_BODY" | head -200
fi

# 2. Streaming with tools endpoint
echo -e "\nTesting POST /llama3_1b/stream (with tools)"
STREAM_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST "$BASE_URL/llama3_1b/stream" \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "What is the current date?",
        "model": "qwen3:8b",
        "toolsInUse": true,
        "stream": false
    }')

HTTP_CODE=$(echo "$STREAM_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
RESPONSE_BODY=$(echo "$STREAM_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | jq -e '.response' | grep -q "$(date +%Y)"; then
    success "Streaming with tools endpoint works"
else
    error "Streaming with tools endpoint failed (HTTP: $HTTP_CODE)"
    echo "$RESPONSE_BODY" | head -200
fi

# 3. Streaming without tools
echo -e "\nTesting POST /llama3_1b/stream (no tools)"
NO_TOOLS_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST "$BASE_URL/llama3_1b/stream" \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "Say hello",
        "model": "qwen3:8b",
        "toolsInUse": false,
        "stream": false
    }')

HTTP_CODE=$(echo "$NO_TOOLS_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Streaming without tools endpoint works"
else
    error "Streaming without tools endpoint failed (HTTP: $HTTP_CODE)"
fi

# Test OpenAI Compatibility Endpoints
echo -e "\n=== OpenAI Compatibility Endpoints ==="

# 4. OpenAI models endpoint
echo -e "\nTesting GET /v1/models"
MODELS_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/v1/models")

HTTP_CODE=$(echo "$MODELS_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
RESPONSE_BODY=$(echo "$MODELS_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | jq -e '.data[0].id' | grep -q "Agentic-RAG"; then
    success "OpenAI models endpoint works"
else
    error "OpenAI models endpoint failed (HTTP: $HTTP_CODE)"
    echo "$RESPONSE_BODY"
fi

# 5. OpenAI chat completions (non-streaming)
echo -e "\nTesting POST /v1/chat/completions (non-streaming)"
CHAT_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Agentic-RAG-Model1",
        "messages": [
            {"role": "user", "content": "What is 3+3? Just give me the number."}
        ],
        "stream": false
    }')

HTTP_CODE=$(echo "$CHAT_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
RESPONSE_BODY=$(echo "$CHAT_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | jq -e '.choices[0].message.content' | grep -q "6"; then
    success "OpenAI chat completions (non-streaming) works"
else
    error "OpenAI chat completions failed (HTTP: $HTTP_CODE)"
    echo "$RESPONSE_BODY" | head -200
fi

# 6. OpenAI with agentic capabilities
echo -e "\nTesting POST /v1/chat/completions (with agentic tools)"
AGENTIC_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Agentic-RAG-Model1",
        "messages": [
            {"role": "user", "content": "What time is it now?"}
        ],
        "stream": false
    }')

HTTP_CODE=$(echo "$AGENTIC_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
RESPONSE_BODY=$(echo "$AGENTIC_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | jq -e '.choices[0].message.content' | grep -q "$(date +%Y)"; then
    success "OpenAI agentic capabilities work"
else
    warning "OpenAI agentic capabilities may have issues (HTTP: $HTTP_CODE)"
    echo "$RESPONSE_BODY" | head -200
fi

# Test Document Processing Endpoints
echo -e "\n=== Document Processing Endpoints ==="

# 7. Document stats
echo -e "\nTesting GET /documents/stats"
STATS_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/documents/stats")

HTTP_CODE=$(echo "$STATS_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
RESPONSE_BODY=$(echo "$STATS_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | jq -e '.total_chunks' > /dev/null; then
    success "Document stats endpoint works"
else
    error "Document stats endpoint failed (HTTP: $HTTP_CODE)"
fi

# 8. Document search
echo -e "\nTesting POST /documents/search"
SEARCH_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST "$BASE_URL/documents/search" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "test search query",
        "max_results": 3
    }')

HTTP_CODE=$(echo "$SEARCH_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Document search endpoint works"
else
    error "Document search endpoint failed (HTTP: $HTTP_CODE)"
fi

# 9. Document configuration
echo -e "\nTesting GET /documents/config"
CONFIG_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/documents/config")

HTTP_CODE=$(echo "$CONFIG_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Document config endpoint works"
else
    error "Document config endpoint failed (HTTP: $HTTP_CODE)"
fi

# Test System Management Endpoints
echo -e "\n=== System Management Endpoints ==="

# 10. Health check
echo -e "\nTesting GET /health"
HEALTH_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/health")

HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | jq -e '.status' | grep -q "healthy"; then
    success "Health endpoint works"
else
    error "Health endpoint failed (HTTP: $HTTP_CODE)"
fi

# 11. Root endpoint
echo -e "\nTesting GET /"
ROOT_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/")

HTTP_CODE=$(echo "$ROOT_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Root endpoint works"
else
    error "Root endpoint failed (HTTP: $HTTP_CODE)"
fi

# 12. Ollama models
echo -e "\nTesting GET /ollama/models"
OLLAMA_MODELS_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/ollama/models")

HTTP_CODE=$(echo "$OLLAMA_MODELS_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Ollama models endpoint works"
else
    error "Ollama models endpoint failed (HTTP: $HTTP_CODE)"
fi

# 13. System prompts
echo -e "\nTesting POST /retrieve_system_prompts"
PROMPTS_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST "$BASE_URL/retrieve_system_prompts" \
    -H "Content-Type: application/json" \
    -d '{}')

HTTP_CODE=$(echo "$PROMPTS_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "System prompts endpoint works"
else
    error "System prompts endpoint failed (HTTP: $HTTP_CODE)"
fi

# Test Monitoring Endpoints
echo -e "\n=== Monitoring Endpoints ==="

# 14. Metrics
echo -e "\nTesting GET /metrics"
METRICS_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/metrics")

HTTP_CODE=$(echo "$METRICS_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Metrics endpoint works"
else
    error "Metrics endpoint failed (HTTP: $HTTP_CODE)"
fi

# 15. Optimization status
echo -e "\nTesting GET /optimization/status"
OPT_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/optimization/status")

HTTP_CODE=$(echo "$OPT_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Optimization status endpoint works"
else
    error "Optimization status endpoint failed (HTTP: $HTTP_CODE)"
fi

# 16. Phase 2B status
echo -e "\nTesting GET /phase2b/status"
PHASE2B_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/phase2b/status")

HTTP_CODE=$(echo "$PHASE2B_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Phase 2B status endpoint works"
else
    warning "Phase 2B status endpoint failed (HTTP: $HTTP_CODE) - may be disabled"
fi

# 17. Phase 2B checkpoints
echo -e "\nTesting GET /phase2b/checkpoints"
CHECKPOINTS_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/phase2b/checkpoints")

HTTP_CODE=$(echo "$CHECKPOINTS_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Phase 2B checkpoints endpoint works"
else
    warning "Phase 2B checkpoints endpoint failed (HTTP: $HTTP_CODE) - may be disabled"
fi

# 18. Document config scan changes
echo -e "\nTesting POST /documents/config/scan-changes"
SCAN_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST "$BASE_URL/documents/config/scan-changes" \
    -H "Content-Type: application/json" \
    -d '{"force_rescan": false}')

HTTP_CODE=$(echo "$SCAN_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
    success "Document config scan changes endpoint works"
else
    error "Document config scan changes endpoint failed (HTTP: $HTTP_CODE)"
fi

# Test Error Handling
echo -e "\n=== Error Handling ==="

# 19. 404 handling
echo -e "\nTesting 404 handling"
NOT_FOUND_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BASE_URL/nonexistent-endpoint")

HTTP_CODE=$(echo "$NOT_FOUND_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "404" ]; then
    success "404 error handling works"
else
    warning "404 error handling unexpected (HTTP: $HTTP_CODE)"
fi

# 20. Malformed JSON
echo -e "\nTesting malformed JSON handling"
BAD_JSON_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST "$BASE_URL/llama3_1b/stream" \
    -H "Content-Type: application/json" \
    -d '{"invalid": json, "missing": quotes}')

HTTP_CODE=$(echo "$BAD_JSON_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
if [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "422" ]; then
    success "Malformed JSON error handling works"
else
    warning "Malformed JSON error handling unexpected (HTTP: $HTTP_CODE)"
fi

# Test Performance under Load
echo -e "\n=== Performance Testing ==="

# 21. Concurrent requests
echo -e "\nTesting concurrent request handling"
CONCURRENT_START=$(date +%s.%N)

for i in {1..5}; do
    curl -s -X POST "$BASE_URL/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "Concurrent test '${i}'",
            "model": "qwen3:8b",
            "toolsInUse": false,
            "stream": false
        }' > "/tmp/concurrent_${i}.json" &
done

wait  # Wait for all background processes

CONCURRENT_END=$(date +%s.%N)
CONCURRENT_TIME=$(echo "$CONCURRENT_END - $CONCURRENT_START" | bc -l)

# Check if all requests succeeded
CONCURRENT_SUCCESS=0
for i in {1..5}; do
    if [ -f "/tmp/concurrent_${i}.json" ] && jq -e '.response' "/tmp/concurrent_${i}.json" > /dev/null 2>&1; then
        CONCURRENT_SUCCESS=$((CONCURRENT_SUCCESS + 1))
    fi
    rm -f "/tmp/concurrent_${i}.json"
done

if [ "$CONCURRENT_SUCCESS" -eq 5 ]; then
    success "Concurrent requests handled successfully (${CONCURRENT_TIME}s total)"
else
    warning "Some concurrent requests failed ($CONCURRENT_SUCCESS/5 succeeded)"
fi

# Generate Summary
echo -e "\n========================================"
echo "📊 API Endpoints Test Results Summary"
echo "========================================"

TOTAL_TESTS=$(grep -c "✅\|❌\|⚠️" "$TEST_LOG")
PASSED=$(grep -c "✅" "$TEST_LOG")
FAILED=$(grep -c "❌" "$TEST_LOG")
WARNINGS=$(grep -c "⚠️" "$TEST_LOG")

echo "Total endpoint tests: $TOTAL_TESTS"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Warnings: $WARNINGS"

# Show failed tests
if [ "$FAILED" -gt 0 ]; then
    echo -e "\n🚨 Failed Tests:"
    grep "❌" "$TEST_LOG" | sed 's/^[[:space:]]*/  /'
fi

# Show warnings
if [ "$WARNINGS" -gt 0 ]; then
    echo -e "\n⚠️  Warnings:"
    grep "⚠️" "$TEST_LOG" | sed 's/^[[:space:]]*/  /'
fi

echo -e "\nDetailed test log saved to: $TEST_LOG"

if [ "$FAILED" -eq 0 ]; then
    echo "🎉 All critical API endpoint tests passed!"
    exit 0
else
    echo "🔧 Some API tests failed - check the detailed log"
    exit 1
fi