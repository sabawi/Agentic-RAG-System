#!/bin/bash

# Quick Health Check Script
# Fast verification that all core systems are working

BASE_URL="http://localhost:5000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Agentic RAG System - Quick Health Check"
echo "=========================================="

# 1. Server responding
echo -n "Server responding... "
if curl -s -f "$BASE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "Server not responding. Check: ./start_complete.sh"
    exit 1
fi

# 2. Ollama service
echo -n "Ollama service... "
if curl -s "http://localhost:11434/api/tags" > /dev/null; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "Ollama not running. Check: ollama serve"
fi

# 3. Tool calling system
echo -n "Tool calling system... "
TOOL_RESPONSE=$(curl -s -X POST "$BASE_URL/llama3_1b/stream" \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "What time is it?",
        "model": "qwen3:8b",
        "toolsInUse": true,
        "stream": false
    }' 2>/dev/null)

if echo "$TOOL_RESPONSE" | jq -r '.response' | grep -q "$(date +%Y)" 2>/dev/null; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "Tool calling not working properly"
fi

# 4. Document search
echo -n "Document search... "
DOC_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "max_results": 1}' 2>/dev/null)

if echo "$DOC_RESPONSE" | jq -e '.results' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⚠️  LIMITED${NC}"
    echo "Document search may have issues"
fi

# 5. OpenAI compatibility
echo -n "OpenAI compatibility... "
OPENAI_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Agentic-RAG-Model1",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": false
    }' 2>/dev/null)

if echo "$OPENAI_RESPONSE" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "OpenAI compatibility not working"
fi

# 6. System resources
echo -n "Memory usage... "
MEMORY=$(curl -s "$BASE_URL/metrics" | jq -r '.memory_usage_mb // 0' 2>/dev/null)
if [ "$MEMORY" -gt 0 ] && [ "$MEMORY" -lt 3000 ]; then
    echo -e "${GREEN}✅ OK (${MEMORY}MB)${NC}"
elif [ "$MEMORY" -gt 3000 ]; then
    echo -e "${YELLOW}⚠️  HIGH (${MEMORY}MB)${NC}"
else
    echo -e "${RED}❌ UNKNOWN${NC}"
fi

echo ""
echo "=========================================="
echo "Quick health check complete!"
echo ""
echo "For detailed testing, run:"
echo "  ./testing/comprehensive_test_suite.sh"
echo "  ./testing/test_embedding_service.sh"
echo "  ./testing/test_api_endpoints.sh"