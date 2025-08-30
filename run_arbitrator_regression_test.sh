#!/bin/bash
# 🚨 CRITICAL ARBITRATOR REGRESSION TEST RUNNER
# =============================================
# 
# This script runs the comprehensive Arbitrator word count regression test
# that ensures the critical bug fix remains working.
#
# USAGE:
#   ./run_arbitrator_regression_test.sh
#
# EXIT CODES:
#   0 = Test PASSED - Arbitrator working correctly
#   1 = Test FAILED - Arbitrator bug has returned
#   2 = Server not running
#   3 = Test setup error

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚨 ARBITRATOR REGRESSION TEST RUNNER${NC}"
echo "=" * 50

# Check if server is running
echo "🔍 Checking if server is running..."
if ! curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Server is not running on localhost:5000${NC}"
    echo "Please start the server first:"
    echo "  ./start_complete.sh"
    exit 2
fi

echo -e "${GREEN}✅ Server is running${NC}"

# Create tests directory if it doesn't exist
mkdir -p tests

# Make sure the test file exists
if [ ! -f "tests/test_arbitrator_word_count_regression.py" ]; then
    echo -e "${RED}❌ Test file not found: tests/test_arbitrator_word_count_regression.py${NC}"
    exit 3
fi

# Run the regression test
echo "🚨 Running Arbitrator regression test..."
echo "⏱️  This may take 2-5 minutes due to Arbitrator correction processing..."

if python3 tests/test_arbitrator_word_count_regression.py; then
    echo -e "${GREEN}✅ ARBITRATOR REGRESSION TEST PASSED${NC}"
    echo "🎉 The critical bug fix is still working correctly!"
    exit 0
else
    echo -e "${RED}❌ ARBITRATOR REGRESSION TEST FAILED${NC}"
    echo "🚨 The critical bug may have returned!"
    echo "📋 Action needed:"
    echo "   1. Check server logs for errors"
    echo "   2. Verify sandboxed_executor args parameter handling"
    echo "   3. Test Arbitrator correction flow manually"
    exit 1
fi