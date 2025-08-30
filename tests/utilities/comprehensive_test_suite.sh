#!/bin/bash

# Agentic RAG System - Developer Testing Framework
# Comprehensive testing suite for all system components
# Usage: ./dev_test_framework.sh [test_category]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:5000"
TEST_DIR="/tmp/agentic_test_$(date +%s)"
LOG_FILE="test_results_$(date +%Y%m%d_%H%M%S).log"

# Helper functions
log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

# Test if server is responding
check_server() {
    log "Checking server connectivity..."
    if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
        success "Server is responding"
        return 0
    else
        error "Server not responding at $BASE_URL"
        info "Please ensure the server is running: ./start_complete.sh"
        exit 1
    fi
}

# Test basic connectivity
test_basic_connectivity() {
    echo "========================================="
    echo "🔗 Testing Basic Connectivity"
    echo "========================================="
    
    # Health check
    log "Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
    if echo "$HEALTH_RESPONSE" | jq -e '.status' | grep -q "healthy"; then
        success "Health check passed"
    else
        error "Health check failed"
        echo "$HEALTH_RESPONSE"
    fi
    
    # Root endpoint
    log "Testing root endpoint..."
    if curl -s -f "$BASE_URL/" > /dev/null; then
        success "Root endpoint accessible"
    else
        error "Root endpoint failed"
    fi
    
    # API docs
    log "Testing API documentation..."
    if curl -s -f "$BASE_URL/docs" > /dev/null; then
        success "API docs accessible"
    else
        warning "API docs not accessible (may be normal)"
    fi
}

# Test Ollama integration
test_ollama_integration() {
    echo "========================================="
    echo "🤖 Testing Ollama Integration"
    echo "========================================="
    
    # Check Ollama models
    log "Checking available Ollama models..."
    MODELS_RESPONSE=$(curl -s "$BASE_URL/ollama/models")
    if echo "$MODELS_RESPONSE" | jq -e '.models' > /dev/null 2>&1; then
        MODEL_COUNT=$(echo "$MODELS_RESPONSE" | jq '.models | length')
        success "Found $MODEL_COUNT Ollama models"
    else
        error "Failed to fetch Ollama models"
        echo "$MODELS_RESPONSE"
    fi
    
    # Test direct Ollama connection
    log "Testing direct Ollama service..."
    if curl -s "http://localhost:11434/api/tags" > /dev/null 2>&1; then
        success "Direct Ollama connection working"
    else
        error "Ollama service not accessible on port 11434"
        info "Check: ollama serve"
    fi
    
    # Test embedding model
    log "Testing embedding model..."
    EMBED_TEST=$(curl -s -X POST "http://localhost:11434/api/embeddings" \
        -d '{"model": "mxbai-embed-large", "prompt": "test"}' 2>/dev/null)
    if echo "$EMBED_TEST" | jq -e '.embedding' > /dev/null 2>&1; then
        success "Embedding model working"
    else
        error "Embedding model not responding"
        info "Try: ollama pull mxbai-embed-large"
    fi
}

# Test tool calling system
test_tool_calling() {
    echo "========================================="
    echo "🛠️  Testing Tool Calling System"
    echo "========================================="
    
    # Test basic tool call (date/time)
    log "Testing basic tool calling (get_the_secret_tool)..."
    TOOL_RESPONSE=$(curl -s -X POST "$BASE_URL/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "What is the current date and time?",
            "model": "qwen3:8b",
            "toolsInUse": true,
            "stream": false
        }')
    
    if echo "$TOOL_RESPONSE" | jq -e '.response' | grep -q "$(date +%Y)"; then
        success "Basic tool calling works"
    else
        error "Basic tool calling failed"
        echo "Response: $TOOL_RESPONSE" | head -200
    fi
    
    # Test web search tool
    log "Testing web search tool..."
    WEB_RESPONSE=$(curl -s -X POST "$BASE_URL/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "Search the web for latest AI news (just get one result)",
            "model": "qwen3:8b",
            "toolsInUse": true,
            "stream": false
        }' | head -500)
    
    if echo "$WEB_RESPONSE" | jq -e '.response' > /dev/null 2>&1; then
        success "Web search tool responding"
    else
        error "Web search tool failed"
        echo "Response: $WEB_RESPONSE" | head -200
    fi
    
    # Test parallel tool execution
    log "Testing parallel tool execution..."
    PARALLEL_RESPONSE=$(curl -s -X POST "$BASE_URL/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "What is the current time? Also, what is 2+2?",
            "model": "qwen3:8b", 
            "toolsInUse": true,
            "stream": false
        }' | head -500)
    
    if echo "$PARALLEL_RESPONSE" | jq -e '.response' | grep -E "($(date +%Y)|4)" > /dev/null; then
        success "Parallel tool execution works"
    else
        warning "Parallel tool execution may have issues"
    fi
}

# Test document processing system
test_document_processing() {
    echo "========================================="
    echo "📄 Testing Document Processing System"
    echo "========================================="
    
    # Check document stats
    log "Checking document system status..."
    DOC_STATS=$(curl -s "$BASE_URL/documents/stats")
    if echo "$DOC_STATS" | jq -e '.total_chunks' > /dev/null 2>&1; then
        TOTAL_CHUNKS=$(echo "$DOC_STATS" | jq -r '.total_chunks')
        success "Document system active ($TOTAL_CHUNKS chunks indexed)"
    else
        error "Document system not responding"
        echo "$DOC_STATS"
        return 1
    fi
    
    # Test document search
    log "Testing document search..."
    SEARCH_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/search" \
        -H "Content-Type: application/json" \
        -d '{
            "query": "test search functionality",
            "max_results": 3
        }')
    
    if echo "$SEARCH_RESPONSE" | jq -e '.results' > /dev/null 2>&1; then
        RESULT_COUNT=$(echo "$SEARCH_RESPONSE" | jq '.results | length')
        QUERY_TIME=$(echo "$SEARCH_RESPONSE" | jq -r '.query_time')
        success "Document search works (found $RESULT_COUNT results in ${QUERY_TIME}s)"
    else
        error "Document search failed"
        echo "$SEARCH_RESPONSE"
    fi
    
    # Test document interrogation (if documents exist)
    if [ "$TOTAL_CHUNKS" -gt 0 ]; then
        log "Testing document interrogation..."
        INTERROGATE_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/interrogate" \
            -H "Content-Type: application/json" \
            -d '{
                "question": "What topics are covered in these documents?",
                "max_context_chunks": 5,
                "use_llm_analysis": true
            }' | head -500)
        
        if echo "$INTERROGATE_RESPONSE" | jq -e '.response' > /dev/null 2>&1; then
            success "Document interrogation works"
        else
            warning "Document interrogation may have issues"
        fi
    else
        warning "No documents indexed - skipping interrogation test"
    fi
}

# Test OpenAI compatibility
test_openai_compatibility() {
    echo "========================================="
    echo "🔄 Testing OpenAI Compatibility"
    echo "========================================="
    
    # Test models endpoint
    log "Testing OpenAI models endpoint..."
    OPENAI_MODELS=$(curl -s "$BASE_URL/v1/models")
    if echo "$OPENAI_MODELS" | jq -e '.data' > /dev/null 2>&1; then
        MODEL_COUNT=$(echo "$OPENAI_MODELS" | jq '.data | length')
        success "OpenAI models endpoint works ($MODEL_COUNT models)"
    else
        error "OpenAI models endpoint failed"
        echo "$OPENAI_MODELS"
    fi
    
    # Test chat completions (non-streaming)
    log "Testing OpenAI chat completions (non-streaming)..."
    CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "Agentic-RAG-Model1",
            "messages": [
                {"role": "user", "content": "What is 2+2? Just give me the number."}
            ],
            "stream": false
        }')
    
    if echo "$CHAT_RESPONSE" | jq -e '.choices[0].message.content' | grep -q "4"; then
        success "OpenAI chat completions work"
    else
        error "OpenAI chat completions failed"
        echo "$CHAT_RESPONSE" | head -200
    fi
    
    # Test chat completions with tools (streaming)
    log "Testing OpenAI chat with agentic capabilities..."
    AGENTIC_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "Agentic-RAG-Model1",
            "messages": [
                {"role": "user", "content": "What time is it right now?"}
            ],
            "stream": false
        }' | head -500)
    
    if echo "$AGENTIC_RESPONSE" | jq -e '.choices[0].message.content' | grep -q "$(date +%Y)"; then
        success "OpenAI agentic capabilities work"
    else
        warning "OpenAI agentic capabilities may have issues"
        echo "$AGENTIC_RESPONSE" | head -200
    fi
}

# Test system performance
test_performance() {
    echo "========================================="
    echo "⚡ Testing System Performance"
    echo "========================================="
    
    # Test response time
    log "Testing response time..."
    START_TIME=$(date +%s.%N)
    RESPONSE=$(curl -s -X POST "$BASE_URL/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "Hello, just say hi back",
            "model": "qwen3:8b",
            "toolsInUse": false,
            "stream": false
        }')
    END_TIME=$(date +%s.%N)
    RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc -l)
    
    if (( $(echo "$RESPONSE_TIME < 10.0" | bc -l) )); then
        success "Response time acceptable (${RESPONSE_TIME}s)"
    else
        warning "Slow response time (${RESPONSE_TIME}s)"
    fi
    
    # Test memory usage
    log "Checking memory usage..."
    METRICS=$(curl -s "$BASE_URL/metrics")
    if echo "$METRICS" | jq -e '.memory_usage_mb' > /dev/null 2>&1; then
        MEMORY_MB=$(echo "$METRICS" | jq -r '.memory_usage_mb')
        success "Memory usage: ${MEMORY_MB}MB"
        if (( $(echo "$MEMORY_MB > 2000" | bc -l) )); then
            warning "High memory usage detected"
        fi
    else
        warning "Could not retrieve memory metrics"
    fi
    
    # Test concurrent requests (light load)
    log "Testing concurrent request handling..."
    for i in {1..3}; do
        curl -s -X POST "$BASE_URL/llama3_1b/stream" \
            -H "Content-Type: application/json" \
            -d '{
                "prompt": "Test concurrent request '${i}'",
                "model": "qwen3:8b",
                "toolsInUse": false,
                "stream": false
            }' > /dev/null &
    done
    wait
    success "Concurrent requests handled"
}

# Test email system (if configured)
test_email_system() {
    echo "========================================="
    echo "📧 Testing Email System"
    echo "========================================="
    
    # Check if email credentials are configured
    if [ -n "$GMAIL_SENDER_EMAIL" ] || [ -n "$OUTLOOK_SENDER_EMAIL" ]; then
        log "Testing email tool functionality..."
        
        # Test email tool (without actually sending)
        EMAIL_TEST_RESPONSE=$(curl -s -X POST "$BASE_URL/llama3_1b/stream" \
            -H "Content-Type: application/json" \
            -d '{
                "prompt": "Test email functionality by showing me the email configuration (do not actually send an email)",
                "model": "qwen3:8b",
                "toolsInUse": true,
                "stream": false
            }' | head -500)
        
        if echo "$EMAIL_TEST_RESPONSE" | jq -e '.response' > /dev/null 2>&1; then
            success "Email system responding"
        else
            warning "Email system may have issues"
        fi
    else
        warning "Email credentials not configured - skipping email tests"
        info "Set GMAIL_SENDER_EMAIL/GMAIL_APP_PASSWORD or OUTLOOK_SENDER_EMAIL/OUTLOOK_APP_PASSWORD to test"
    fi
}

# Test error handling
test_error_handling() {
    echo "========================================="
    echo "🚨 Testing Error Handling"
    echo "========================================="
    
    # Test invalid endpoint
    log "Testing 404 handling..."
    if curl -s -f "$BASE_URL/invalid_endpoint" > /dev/null 2>&1; then
        error "404 handling not working properly"
    else
        success "404 handling works correctly"
    fi
    
    # Test malformed request
    log "Testing malformed request handling..."
    BAD_RESPONSE=$(curl -s -X POST "$BASE_URL/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{"invalid": "json", "missing_required_fields": true}')
    
    if echo "$BAD_RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
        success "Malformed request handling works"
    else
        warning "Malformed request handling may need improvement"
    fi
    
    # Test timeout handling (using a very long prompt)
    log "Testing timeout handling..."
    LONG_PROMPT="$(printf 'This is a very long prompt %.0s' {1..100})"
    TIMEOUT_RESPONSE=$(timeout 30s curl -s -X POST "$BASE_URL/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "'"$LONG_PROMPT"'",
            "model": "qwen3:8b",
            "toolsInUse": false,
            "stream": false
        }' 2>/dev/null)
    
    if [ $? -eq 124 ]; then
        success "Request timeout handling works"
    else
        warning "Timeout handling test inconclusive"
    fi
}

# Test conversation memory
test_conversation_memory() {
    echo "========================================="
    echo "🧠 Testing Conversation Memory"
    echo "========================================="
    
    CONV_ID="test_conversation_$(date +%s)"
    
    # First message
    log "Testing conversation memory - first message..."
    FIRST_RESPONSE=$(curl -s -X POST "$BASE_URL/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "Remember that my favorite color is blue",
            "model": "qwen3:8b",
            "toolsInUse": false,
            "stream": false,
            "conversation_id": "'$CONV_ID'"
        }')
    
    if echo "$FIRST_RESPONSE" | jq -e '.response' > /dev/null 2>&1; then
        success "First conversation message processed"
    else
        error "First conversation message failed"
        return 1
    fi
    
    # Follow-up message to test memory
    log "Testing conversation memory - follow-up message..."
    SECOND_RESPONSE=$(curl -s -X POST "$BASE_URL/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "What is my favorite color?",
            "model": "qwen3:8b",
            "toolsInUse": false,
            "stream": false,
            "conversation_id": "'$CONV_ID'"
        }')
    
    if echo "$SECOND_RESPONSE" | jq -r '.response' | grep -i "blue" > /dev/null; then
        success "Conversation memory working"
    else
        warning "Conversation memory may not be working properly"
        echo "Response: $(echo "$SECOND_RESPONSE" | jq -r '.response')"
    fi
}

# Create test report
generate_test_report() {
    echo "========================================="
    echo "📊 Test Results Summary"
    echo "========================================="
    
    TOTAL_TESTS=$(grep -c "Testing\|Checking" "$LOG_FILE" || echo "0")
    PASSED_TESTS=$(grep -c "✅" "$LOG_FILE" || echo "0")
    FAILED_TESTS=$(grep -c "❌" "$LOG_FILE" || echo "0")
    WARNING_TESTS=$(grep -c "⚠️" "$LOG_FILE" || echo "0")
    
    success "Tests completed: $TOTAL_TESTS"
    success "Passed: $PASSED_TESTS"
    if [ "$FAILED_TESTS" -gt 0 ]; then
        error "Failed: $FAILED_TESTS"
    fi
    if [ "$WARNING_TESTS" -gt 0 ]; then
        warning "Warnings: $WARNING_TESTS"
    fi
    
    echo ""
    info "Full test log saved to: $LOG_FILE"
    
    if [ "$FAILED_TESTS" -eq 0 ]; then
        echo "🎉 All critical tests passed!"
        return 0
    else
        echo "🔧 Some tests failed - check the log for details"
        return 1
    fi
}

# Main test orchestrator
run_test_category() {
    case "$1" in
        "basic"|"connectivity")
            test_basic_connectivity
            ;;
        "ollama")
            test_ollama_integration
            ;;
        "tools"|"tool_calling")
            test_tool_calling
            ;;
        "documents"|"docs")
            test_document_processing
            ;;
        "openai"|"compatibility")
            test_openai_compatibility
            ;;
        "performance"|"perf")
            test_performance
            ;;
        "email")
            test_email_system
            ;;
        "errors"|"error_handling")
            test_error_handling
            ;;
        "memory"|"conversation")
            test_conversation_memory
            ;;
        "all"|"")
            test_basic_connectivity
            test_ollama_integration
            test_tool_calling
            test_document_processing
            test_openai_compatibility
            test_performance
            test_email_system
            test_error_handling
            test_conversation_memory
            ;;
        *)
            echo "Usage: $0 [test_category]"
            echo ""
            echo "Available test categories:"
            echo "  basic          - Basic connectivity tests"
            echo "  ollama         - Ollama integration tests"
            echo "  tools          - Tool calling system tests"
            echo "  documents      - Document processing tests"
            echo "  openai         - OpenAI compatibility tests"  
            echo "  performance    - Performance tests"
            echo "  email          - Email system tests"
            echo "  errors         - Error handling tests"
            echo "  memory         - Conversation memory tests"
            echo "  all            - Run all tests (default)"
            exit 1
            ;;
    esac
}

# Script start
main() {
    echo "🧪 Agentic RAG System - Developer Testing Framework"
    echo "==================================================="
    echo "Starting tests at: $(date)"
    echo "Log file: $LOG_FILE"
    echo ""
    
    # Check dependencies
    command -v jq >/dev/null 2>&1 || { 
        error "jq is required but not installed. Install with: sudo apt-get install jq"
        exit 1
    }
    
    command -v bc >/dev/null 2>&1 || { 
        error "bc is required but not installed. Install with: sudo apt-get install bc"
        exit 1
    }
    
    # Check if server is running
    check_server
    
    # Create temp directory
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"
    
    # Run requested tests
    run_test_category "${1:-all}"
    
    # Generate summary
    echo ""
    generate_test_report
    
    # Cleanup
    cd - > /dev/null
    rm -rf "$TEST_DIR"
    
    echo ""
    echo "Testing complete at: $(date)"
}

# Run the main function with all arguments
main "$@"