# Testing Documentation

This directory contains comprehensive tests for the Agentic RAG System FastAPI server migration and functionality.

## Test Categories

### 1. Import and Dependencies Tests
- **check_imports.py** - Verifies all required Python packages are available
- **test_tools_available.py** - Checks tool availability and dependencies

### 2. FastAPI Server Tests
- **test_fastapi.py** - Basic FastAPI server functionality tests
- **test_fastapi_tools.py** - Tests tool integration with FastAPI endpoints
- **test_simple.py** - Simple server connectivity tests
- **test_missing_endpoints.py** - Validates all required endpoints exist

### 3. Tool Calling System Tests
- **test_tool_calling.py** - Tests the two-stage tool calling algorithm
- **test_6_tools.py** - Tests all 6 tool functions individually
- **test_direct_tools.py** - Direct tool function execution tests
- **test_tools_individually.py** - Individual tool isolation tests
- **debug_tool_calling.py** - Debug script for tool calling issues

### 4. News and Content Tests
- **test_comprehensive_news.py** - Tests enhanced news function with full article content
- **test_financial_news.py** - Financial news retrieval tests
- **test_quick_financial.py** - Quick financial data tests
- **test_web_search.py** - DuckDuckGo web search functionality tests

### 5. Request Processing Tests
- **test_request_parsing.py** - Tests request parsing equivalence with original Flask
- **test_exact_equivalence.py** - Validates exact compatibility with original server
- **test_system_prompts.py** - System prompts endpoint tests

### 6. Ollama Integration Tests
- **test_ollama.py** - Ollama LLM integration tests
- **debug_stream.py** - Debugging streaming responses
- **debug_keywords.py** - Keyword processing debug

### 7. Utility and Example Tests
- **tool_example.py** - Example tool usage patterns
- **simple_tool_test.py** - Simple tool execution examples
- **quick_test.py** - Quick functionality verification
- **curl_test.sh** - Shell script for cURL-based testing

### 8. Debug and Troubleshooting
- **debug_tools_execution.py** - Debug tool execution flow
- **debug_tool_calling.py** - Debug two-stage tool calling
- **debug_stream.py** - Debug streaming responses
- **debug_keywords.py** - Debug keyword processing

## Key Testing Areas Covered

### ✅ Migration Verification
- All original Flask endpoints replicated
- Request parsing compatibility maintained
- Response format consistency verified

### ✅ Tool System Testing
- Two-stage tool calling algorithm implementation
- All 6 tool functions (news, web search, Wikipedia, stocks, website lookup, date/time)
- Enhanced news function with full article content extraction
- Timeout and race condition fixes

### ✅ Performance Testing
- Async processing verification
- Database connection pooling
- Caching layer functionality
- Streaming response handling

### ✅ Dependency Testing
- Virtual environment setup validation
- Package compatibility verification
- Import error handling

## Running Tests

### Prerequisites
```bash
# Activate virtual environment
source venv/bin/activate

# Ensure server is running
./start_complete_server.sh
```

### Individual Test Execution
```bash
cd testing/
python test_fastapi.py
python test_tool_calling.py
python test_comprehensive_news.py
```

### Shell Tests
```bash
cd testing/
./curl_test.sh
```

## Test Results Summary

All tests verify the successful migration from Flask to FastAPI while maintaining:
- Complete functionality parity
- Enhanced performance through async processing  
- Robust error handling and timeout management
- Full article content extraction in news functions
- Updated dependencies (ddgs package, newspaper3k)

## Dependencies Tested

- FastAPI with uvicorn
- Ollama LLM integration
- DuckDuckGo search (ddgs package)
- Google News (gnews)
- newspaper3k for article extraction
- BeautifulSoup for web scraping
- Wikipedia API
- Yahoo Finance (yfinance)
- Database connectivity (aiomysql)
- All supporting utility libraries

## Version Compatibility

Tests confirm compatibility with:
- Python 3.12+
- FastAPI 0.100+
- Ollama API latest
- All tool dependencies as specified in requirements.txt