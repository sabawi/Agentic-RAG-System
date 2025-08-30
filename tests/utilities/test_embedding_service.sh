#!/bin/bash

# Embedding Service Specific Testing
# Focused tests for document processing, FAISS indexing, and search functionality

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost:5000"
TEST_LOG="embedding_test_$(date +%Y%m%d_%H%M%S).log"

success() { echo -e "${GREEN}✅ $1${NC}" | tee -a "$TEST_LOG"; }
error() { echo -e "${RED}❌ $1${NC}" | tee -a "$TEST_LOG"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$TEST_LOG"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$TEST_LOG"; }

echo "🧠 Embedding Service Test Suite"
echo "==============================="

# Test 1: Basic embedding service health
echo "Test 1: Embedding Service Health"
STATS_RESPONSE=$(curl -s "$BASE_URL/documents/stats")
if echo "$STATS_RESPONSE" | jq -e '.total_chunks' > /dev/null 2>&1; then
    CHUNKS=$(echo "$STATS_RESPONSE" | jq -r '.total_chunks')
    success "Embedding service healthy ($CHUNKS chunks indexed)"
else
    error "Embedding service not responding"
    echo "$STATS_RESPONSE"
fi

# Test 2: Ollama embedding model
echo -e "\nTest 2: Ollama Embedding Model"
EMBED_RESPONSE=$(curl -s -X POST "http://localhost:11434/api/embeddings" \
    -d '{"model": "mxbai-embed-large", "prompt": "test embedding generation"}')
if echo "$EMBED_RESPONSE" | jq -e '.embedding[0]' > /dev/null 2>&1; then
    EMBED_SIZE=$(echo "$EMBED_RESPONSE" | jq '.embedding | length')
    success "Embedding generation works (${EMBED_SIZE}D vector)"
else
    error "Embedding model not responding"
    info "Try: ollama pull mxbai-embed-large"
fi

# Test 3: Document search functionality  
echo -e "\nTest 3: Document Search"
SEARCH_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/search" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "artificial intelligence machine learning",
        "max_results": 3,
        "similarity_threshold": 0.0
    }')

if echo "$SEARCH_RESPONSE" | jq -e '.results' > /dev/null 2>&1; then
    RESULT_COUNT=$(echo "$SEARCH_RESPONSE" | jq '.results | length')
    QUERY_TIME=$(echo "$SEARCH_RESPONSE" | jq -r '.query_time // 0')
    success "Document search works ($RESULT_COUNT results in ${QUERY_TIME}s)"
else
    error "Document search failed"
    echo "$SEARCH_RESPONSE"
fi

# Test 4: Search performance
echo -e "\nTest 4: Search Performance"
START_TIME=$(date +%s.%N)
for i in {1..5}; do
    curl -s -X POST "$BASE_URL/documents/search" \
        -H "Content-Type: application/json" \
        -d '{"query": "performance test '${i}'", "max_results": 1}' > /dev/null
done
END_TIME=$(date +%s.%N)
AVG_TIME=$(echo "($END_TIME - $START_TIME) / 5" | bc -l)

if (( $(echo "$AVG_TIME < 0.5" | bc -l) )); then
    success "Search performance good (${AVG_TIME}s average)"
else
    warning "Search performance slow (${AVG_TIME}s average)"
fi

# Test 5: Document interrogation
echo -e "\nTest 5: Document Interrogation"
if [ "$CHUNKS" -gt 0 ]; then
    INTERROGATE_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/interrogate" \
        -H "Content-Type: application/json" \
        -d '{
            "question": "What are the main topics in these documents?",
            "max_context_chunks": 5
        }')
    
    if echo "$INTERROGATE_RESPONSE" | jq -e '.response' > /dev/null 2>&1; then
        success "Document interrogation works"
    else
        warning "Document interrogation issues"
    fi
else
    warning "No documents indexed - skipping interrogation test"
fi

# Test 6: FAISS index integrity
echo -e "\nTest 6: FAISS Index Integrity"
if [ -f "../document_store/faiss.index" ]; then
    INDEX_SIZE=$(stat -f%z "../document_store/faiss.index" 2>/dev/null || stat -c%s "../document_store/faiss.index" 2>/dev/null)
    if [ "$INDEX_SIZE" -gt 1000 ]; then
        success "FAISS index file exists and has content (${INDEX_SIZE} bytes)"
    else
        warning "FAISS index file too small"
    fi
else
    warning "FAISS index file not found"
fi

# Test 7: Metadata database
echo -e "\nTest 7: Metadata Database"
if [ -f "../document_store/metadata.db" ]; then
    DB_SIZE=$(stat -f%z "../document_store/metadata.db" 2>/dev/null || stat -c%s "../document_store/metadata.db" 2>/dev/null)
    success "Metadata database exists (${DB_SIZE} bytes)"
    
    # Test database integrity if sqlite3 is available
    if command -v sqlite3 >/dev/null 2>&1; then
        INTEGRITY_CHECK=$(sqlite3 "../document_store/metadata.db" "PRAGMA integrity_check;" 2>/dev/null || echo "error")
        if [ "$INTEGRITY_CHECK" = "ok" ]; then
            success "Database integrity check passed"
        else
            warning "Database integrity issues detected"
        fi
    fi
else
    warning "Metadata database not found"
fi

# Test 8: Memory usage during search
echo -e "\nTest 8: Memory Usage Analysis"
METRICS_BEFORE=$(curl -s "$BASE_URL/metrics" | jq -r '.memory_usage_mb // 0')

# Perform several searches
for i in {1..10}; do
    curl -s -X POST "$BASE_URL/documents/search" \
        -H "Content-Type: application/json" \
        -d '{"query": "memory test query '${i}'", "max_results": 5}' > /dev/null
done

METRICS_AFTER=$(curl -s "$BASE_URL/metrics" | jq -r '.memory_usage_mb // 0')
MEMORY_DIFF=$(echo "$METRICS_AFTER - $METRICS_BEFORE" | bc -l)

if (( $(echo "$MEMORY_DIFF < 50" | bc -l) )); then
    success "Memory usage stable (${MEMORY_DIFF}MB change)"
else
    warning "Significant memory increase detected (${MEMORY_DIFF}MB)"
fi

# Test 9: Error handling
echo -e "\nTest 9: Error Handling"

# Invalid search query
INVALID_SEARCH=$(curl -s -X POST "$BASE_URL/documents/search" \
    -H "Content-Type: application/json" \
    -d '{"invalid": "request"}')

if echo "$INVALID_SEARCH" | jq -e '.error' > /dev/null 2>&1; then
    success "Invalid request error handling works"
else
    warning "Error handling may need improvement"
fi

# Test 10: Directory watching status
echo -e "\nTest 10: Directory Watching"
WATCH_CONFIG=$(curl -s "$BASE_URL/documents/config")
if echo "$WATCH_CONFIG" | jq -e '.directories' > /dev/null 2>&1; then
    WATCH_COUNT=$(echo "$WATCH_CONFIG" | jq '.directories | length')
    success "Directory watching configured ($WATCH_COUNT directories)"
else
    warning "Directory watching not configured"
fi

echo -e "\n==============================="
echo "🎯 Embedding Service Test Results"
echo "==============================="

TOTAL_TESTS=$(grep -c "✅\|❌\|⚠️" "$TEST_LOG")
PASSED=$(grep -c "✅" "$TEST_LOG")
FAILED=$(grep -c "❌" "$TEST_LOG")
WARNINGS=$(grep -c "⚠️" "$TEST_LOG")

echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED"
echo "Failed: $FAILED"  
echo "Warnings: $WARNINGS"

echo -e "\nTest log saved to: $TEST_LOG"

if [ "$FAILED" -eq 0 ]; then
    echo "🎉 All embedding service tests passed!"
    exit 0
else
    echo "🔧 Some tests failed - check the detailed log"
    exit 1
fi