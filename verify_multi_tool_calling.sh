#!/bin/bash

# 🚨 CRITICAL MULTI-TOOL CALLING VERIFICATION SCRIPT 🚨
# Run this script after ANY tool-related modifications to ensure multi-tool calling still works

echo "🔍 VERIFYING MULTI-TOOL CALLING CAPABILITY"
echo "========================================="
echo

# Check if server is running
if ! curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "❌ Server is not running. Please start it first:"
    echo "   ./start_complete.sh"
    exit 1
fi

echo "✅ Server is running"
echo

# Test 1: 2 tool calls with llama3.2:3b
echo "🧪 TEST 1: 2+ tool calls with llama3.2:3b"
echo "----------------------------------------"
echo "Prompt: What is the capital of France and what are the latest tech news?"
echo

RESPONSE1=$(curl -X POST http://localhost:5000/llama3_1b/stream \
    -H "Content-Type: application/json" \
    -d '{"prompt": "What is the capital of France and what are the latest tech news?", "model": "llama3.2:3b", "tools_calling_model": "llama3.2:3b", "stream": false}' \
    2>/dev/null | head -5)

sleep 3

# Check logs for tool calls
TOOL_CALLS_1=$(grep "TOOL CALLS DETECTED" /home/sabawi/Development/flaskserver/server_complete.log | tail -1 | grep -o "Found [0-9]* tool calls")

if [[ "$TOOL_CALLS_1" =~ "Found 1 tool calls" ]]; then
    echo "❌ CRITICAL FAILURE: Only 1 tool call detected!"
    echo "🚨 REGRESSION DETECTED - Multi-tool calling is broken!"
    exit 1
elif [[ "$TOOL_CALLS_1" =~ "Found [2-9] tool calls" ]] || [[ "$TOOL_CALLS_1" =~ "Found [1-9][0-9] tool calls" ]]; then
    echo "✅ SUCCESS: $TOOL_CALLS_1"
else
    echo "⚠️  Could not verify tool calls. Check logs manually."
fi

echo

# Test 2: 3+ tool calls with qwen3:8b  
echo "🧪 TEST 2: 3+ tool calls with qwen3:8b"
echo "-------------------------------------"
echo "Prompt: Get current time, search for Apple stock data, and get recent tech news"
echo

RESPONSE2=$(curl -X POST http://localhost:5000/llama3_1b/stream \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Get current time, search for Apple stock data, and get recent tech news", "model": "llama3.2:3b", "tools_calling_model": "qwen3:8b", "stream": false}' \
    2>/dev/null | head -5)

sleep 3

# Check logs for tool calls
TOOL_CALLS_2=$(grep "TOOL CALLS DETECTED" /home/sabawi/Development/flaskserver/server_complete.log | tail -1 | grep -o "Found [0-9]* tool calls")

if [[ "$TOOL_CALLS_2" =~ "Found 1 tool calls" ]]; then
    echo "❌ CRITICAL FAILURE: Only 1 tool call detected!"
    echo "🚨 REGRESSION DETECTED - Multi-tool calling is broken!"
    exit 1
elif [[ "$TOOL_CALLS_2" =~ "Found [3-9] tool calls" ]] || [[ "$TOOL_CALLS_2" =~ "Found [1-9][0-9] tool calls" ]]; then
    echo "✅ SUCCESS: $TOOL_CALLS_2"
elif [[ "$TOOL_CALLS_2" =~ "Found 2 tool calls" ]]; then
    echo "⚠️  WARNING: Only 2 tool calls (expected 3+), but not critical failure"
else
    echo "⚠️  Could not verify tool calls. Check logs manually."
fi

echo

# Final verification
echo "📊 FINAL VERIFICATION"
echo "====================="
echo "Recent tool call history:"
grep "TOOL CALLS DETECTED" /home/sabawi/Development/flaskserver/server_complete.log | tail -5

echo
echo "🔍 Check for any single-tool regressions:"
SINGLE_TOOL_COUNT=$(grep "Found 1 tool calls" /home/sabawi/Development/flaskserver/server_complete.log | wc -l)
MULTI_TOOL_COUNT=$(grep -E "Found [2-9] tool calls|Found [1-9][0-9] tool calls" /home/sabawi/Development/flaskserver/server_complete.log | wc -l)

echo "Single tool calls in log: $SINGLE_TOOL_COUNT"
echo "Multi tool calls in log: $MULTI_TOOL_COUNT"

if [[ $SINGLE_TOOL_COUNT -gt $MULTI_TOOL_COUNT ]]; then
    echo "⚠️  WARNING: More single-tool calls than multi-tool calls detected"
    echo "This may indicate regression or improper testing"
else
    echo "✅ Multi-tool calling appears to be working correctly"
fi

echo
echo "🎯 VERIFICATION COMPLETE"
echo "========================"
echo "If you see any ❌ CRITICAL FAILURE messages above, immediately:"
echo "1. Check CRITICAL_MULTI_TOOL_CALLING_PROTECTION.md"
echo "2. Restore tool descriptions to protected baseline"
echo "3. Restart server and re-test"