#!/bin/bash
"""
Phase 2B Rollback Validation Test Script
Comprehensive testing of rollback functionality and safety systems
"""

set -e  # Exit on any error

echo "🧪 Phase 2B Rollback Validation Tests"
echo "====================================="

# Configuration
SERVER_URL="http://localhost:5000"
TEST_LOG="rollback_test_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$TEST_LOG"
}

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -e "\n${BLUE}🧪 Test $TESTS_TOTAL: $test_name${NC}"
    log "Starting test: $test_name"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        log "PASSED: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        log "FAILED: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Check if server is running
check_server() {
    curl -s "${SERVER_URL}/health" > /dev/null 2>&1
}

# Test Phase 2B status endpoint
test_status_endpoint() {
    local response=$(curl -s "${SERVER_URL}/phase2b/status")
    echo "$response" | jq -e '.success == true' > /dev/null 2>&1
}

# Test checkpoint listing
test_checkpoint_listing() {
    local response=$(curl -s "${SERVER_URL}/phase2b/checkpoints")
    local count=$(echo "$response" | jq -r '.count')
    [ "$count" -ge 1 ]
}

# Test feature flag states (should all be disabled initially)
test_initial_feature_states() {
    local response=$(curl -s "${SERVER_URL}/phase2b/status")
    local streaming=$(echo "$response" | jq -r '.rollback_controller.feature_flags.streaming_fallback')
    local buffer=$(echo "$response" | jq -r '.rollback_controller.feature_flags.buffer_optimization')
    local classification=$(echo "$response" | jq -r '.rollback_controller.feature_flags.response_classification')
    
    [ "$streaming" = "false" ] && [ "$buffer" = "false" ] && [ "$classification" = "false" ]
}

# Test performance monitoring (should be active)
test_performance_monitoring() {
    local response=$(curl -s "${SERVER_URL}/phase2b/status")
    local monitoring=$(echo "$response" | jq -r '.rollback_controller.feature_flags.performance_monitoring')
    local health=$(echo "$response" | jq -r '.performance_health.overall_status')
    
    [ "$monitoring" = "true" ] && [ "$health" = "healthy" ]
}

# Test baseline checkpoint exists
test_baseline_checkpoint() {
    local response=$(curl -s "${SERVER_URL}/phase2b/checkpoints")
    echo "$response" | jq -e '.checkpoints[] | select(.id == "phase2a_baseline")' > /dev/null 2>&1
}

# Test feature enable/disable cycle
test_feature_toggle() {
    local feature="buffer_optimization"
    
    # Enable feature
    local enable_response=$(curl -s -X POST "${SERVER_URL}/phase2b/feature/${feature}/enable")
    local enable_success=$(echo "$enable_response" | jq -r '.success')
    
    if [ "$enable_success" != "true" ]; then
        return 1
    fi
    
    # Verify it's enabled
    local status_response=$(curl -s "${SERVER_URL}/phase2b/status")
    local enabled=$(echo "$status_response" | jq -r ".rollback_controller.feature_flags.${feature}")
    
    if [ "$enabled" != "true" ]; then
        return 1
    fi
    
    # Disable feature
    local disable_response=$(curl -s -X POST "${SERVER_URL}/phase2b/feature/${feature}/disable")
    local disable_success=$(echo "$disable_response" | jq -r '.success')
    
    if [ "$disable_success" != "true" ]; then
        return 1
    fi
    
    # Verify it's disabled
    status_response=$(curl -s "${SERVER_URL}/phase2b/status")
    local disabled=$(echo "$status_response" | jq -r ".rollback_controller.feature_flags.${feature}")
    
    [ "$disabled" = "false" ]
}

# Test emergency rollback (should work but not change state since all features are off)
test_emergency_rollback() {
    local response=$(curl -s -X POST "${SERVER_URL}/phase2b/rollback/emergency")
    local success=$(echo "$response" | jq -r '.success')
    
    [ "$success" = "true" ]
}

# Test rollback to specific checkpoint
test_specific_rollback() {
    local response=$(curl -s -X POST "${SERVER_URL}/phase2b/rollback/phase2a_baseline")
    local success=$(echo "$response" | jq -r '.success')
    
    [ "$success" = "true" ]
}

# Test invalid feature name handling
test_invalid_feature() {
    local response=$(curl -s -X POST "${SERVER_URL}/phase2b/feature/invalid_feature/enable")
    local success=$(echo "$response" | jq -r '.success')
    
    [ "$success" = "false" ]
}

# Test system health after operations
test_system_health() {
    # Run a quick tool operation to verify system still works
    local response=$(curl -s -X POST "${SERVER_URL}/llama3_1b/stream" \
        -H "Content-Type: application/json" \
        -d '{"prompt": "What is 2+2?", "model": "qwen3:8b", "stream": false}')
    
    # Check if we got a response (system is working)
    [ -n "$response" ]
}

# Main test execution
main() {
    echo -e "${BLUE}Phase 2B Rollback Validation Test Suite${NC}"
    echo "Log file: $TEST_LOG"
    echo ""
    
    log "Starting Phase 2B rollback validation tests"
    
    # Verify server is running
    if ! check_server; then
        echo -e "${RED}❌ Server not running at ${SERVER_URL}${NC}"
        log "ERROR: Server not running"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Server is running${NC}"
    log "Server connectivity verified"
    
    # Run all tests
    run_test "Phase 2B Status Endpoint" "test_status_endpoint"
    run_test "Checkpoint Listing" "test_checkpoint_listing"  
    run_test "Initial Feature States" "test_initial_feature_states"
    run_test "Performance Monitoring Active" "test_performance_monitoring"
    run_test "Baseline Checkpoint Exists" "test_baseline_checkpoint"
    run_test "Feature Toggle Cycle" "test_feature_toggle"
    run_test "Emergency Rollback" "test_emergency_rollback"
    run_test "Specific Rollback" "test_specific_rollback"
    run_test "Invalid Feature Handling" "test_invalid_feature"
    run_test "System Health After Operations" "test_system_health"
    
    # Test summary
    echo ""
    echo "====================================="
    echo -e "${BLUE}Test Summary${NC}"
    echo "====================================="
    echo "Total Tests: $TESTS_TOTAL"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Phase 2B rollback system is working perfectly!${NC}"
        log "ALL TESTS PASSED - Phase 2B rollback validation successful"
        exit 0
    else
        echo -e "\n${RED}❌ Some tests failed. Check the logs for details.${NC}"
        log "SOME TESTS FAILED - Phase 2B rollback validation has issues"
        exit 1
    fi
}

# Run main function
main "$@"