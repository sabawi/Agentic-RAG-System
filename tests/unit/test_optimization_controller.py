#!/usr/bin/env python3
"""
Comprehensive Testing for OptimizationController
Tests feature flags, A/B testing, monitoring, and rollback capabilities
"""

import time
import pytest
import sys
import os
from pathlib import Path

# 🔧 ROBUST PROJECT ROOT DISCOVERY - Works from any subdirectory
def find_project_root():
    """Find project root by looking for marker files/directories"""
    markers = ['user_tools', 'sandbox_workspace', 'config', 'fastapi_server_complete.py']
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if sum(1 for marker in markers if (parent / marker).exists()) >= 3:
            return str(parent)
    return os.getcwd()

project_root = find_project_root()
sys.path.insert(0, project_root)

from optimization_controller import OptimizationController, OptimizationStatus


class TestOptimizationController:
    """Test the feature flag and A/B testing system"""
    
    def setup_method(self):
        """Setup for each test"""
        self.controller = OptimizationController()
    
    def test_master_toggle_disabled_by_default(self):
        """Test 3.1.1: Master toggle starts disabled"""
        assert self.controller.enable_optimization == False
        assert self.controller.should_optimize() == False
        assert self.controller.status == OptimizationStatus.DISABLED
        
        print("✅ Test 3.1.1 PASSED: Master toggle disabled by default")
    
    def test_enable_disable_feature(self):
        """Test 3.1.2: Enable/disable feature toggle"""
        # Test enabling
        self.controller.enable_feature(100.0)
        assert self.controller.enable_optimization == True
        assert self.controller.rollout_percentage == 100.0
        assert self.controller.status == OptimizationStatus.ENABLED
        assert self.controller.should_optimize() == True
        
        # Test disabling
        self.controller.disable_feature()
        assert self.controller.enable_optimization == False
        assert self.controller.rollout_percentage == 0.0
        assert self.controller.status == OptimizationStatus.DISABLED
        assert self.controller.should_optimize() == False
        
        print("✅ Test 3.1.2 PASSED: Enable/disable feature toggle works")
    
    def test_percentage_based_rollout(self):
        """Test 3.1.3: Percentage-based gradual rollout"""
        # Enable with 50% rollout
        self.controller.enable_feature(50.0)
        assert self.controller.status == OptimizationStatus.TESTING
        
        # Test multiple user IDs - should have roughly 50% enabled
        test_users = [f"user_{i}" for i in range(100)]
        enabled_count = sum(1 for user in test_users if self.controller.should_optimize(user_id=user))
        
        # Should be roughly 50% (allowing for hash distribution variance)
        assert 35 <= enabled_count <= 65, f"Expected ~50, got {enabled_count}"
        
        # Test 0% rollout
        self.controller.set_rollout_percentage(0.0)
        assert self.controller.should_optimize(user_id="test_user") == False
        
        # Test 100% rollout
        self.controller.set_rollout_percentage(100.0)
        assert self.controller.should_optimize(user_id="test_user") == True
        assert self.controller.status == OptimizationStatus.ENABLED
        
        print("✅ Test 3.1.3 PASSED: Percentage-based rollout works")
    
    def test_user_whitelist(self):
        """Test 3.1.4: User whitelist functionality"""
        # Enable optimization but with 0% rollout
        self.controller.enable_feature(0.0)
        
        # Add users to whitelist
        whitelist_users = ["test_user_1", "test_user_2"]
        self.controller.add_to_user_whitelist(whitelist_users)
        
        # Whitelisted users should be enabled even with 0% rollout
        assert self.controller.should_optimize(user_id="test_user_1") == True
        assert self.controller.should_optimize(user_id="test_user_2") == True
        
        # Non-whitelisted user should be disabled
        assert self.controller.should_optimize(user_id="other_user") == False
        
        print("✅ Test 3.1.4 PASSED: User whitelist functionality works")
    
    def test_tool_type_whitelist(self):
        """Test 3.1.5: Tool type whitelist functionality"""
        # Enable optimization
        self.controller.enable_feature(100.0)
        
        # Add tool types to whitelist
        allowed_tools = ["stock_analyzer", "news_summaries"]
        self.controller.add_to_tool_whitelist(allowed_tools)
        
        # Whitelisted tools should be enabled
        assert self.controller.should_optimize(tool_types=["stock_analyzer"]) == True
        assert self.controller.should_optimize(tool_types=["news_summaries"]) == True
        assert self.controller.should_optimize(tool_types=["stock_analyzer", "news_summaries"]) == True
        
        # Non-whitelisted tools should be disabled
        assert self.controller.should_optimize(tool_types=["email_sender"]) == False
        assert self.controller.should_optimize(tool_types=["stock_analyzer", "email_sender"]) == True  # One is whitelisted
        
        print("✅ Test 3.1.5 PASSED: Tool type whitelist functionality works")
    
    def test_metrics_tracking(self):
        """Test 3.2.1: Metrics tracking system"""
        # Record successful optimization
        self.controller.record_attempt(success=True, validation_score=85.0, response_time=0.5)
        
        assert self.controller.metrics.total_attempts == 1
        assert self.controller.metrics.successful_optimizations == 1
        assert self.controller.metrics.average_score == 85.0
        assert self.controller.metrics.average_response_time == 0.5
        assert self.controller.get_success_rate() == 1.0
        assert self.controller.get_error_rate() == 0.0
        
        # Record failed optimization
        self.controller.record_attempt(success=False, validation_score=60.0, response_time=0.3, error_type="validation")
        
        assert self.controller.metrics.total_attempts == 2
        assert self.controller.metrics.successful_optimizations == 1
        assert self.controller.metrics.validation_failures == 1
        assert self.controller.get_success_rate() == 0.5
        
        # Check average calculations
        expected_avg_score = (85.0 + 60.0) / 2
        expected_avg_time = (0.5 + 0.3) / 2
        assert abs(self.controller.metrics.average_score - expected_avg_score) < 0.01
        assert abs(self.controller.metrics.average_response_time - expected_avg_time) < 0.01
        
        print("✅ Test 3.2.1 PASSED: Metrics tracking works")
    
    def test_performance_history(self):
        """Test 3.2.2: Performance history tracking"""
        # Record several attempts
        test_data = [
            (True, 90.0, 0.4, None),
            (False, 65.0, 0.6, "validation"),
            (True, 88.0, 0.3, None),
            (False, 45.0, 0.8, "exception")
        ]
        
        for success, score, time_val, error in test_data:
            self.controller.record_attempt(success, score, time_val, error)
        
        assert len(self.controller.performance_history) == 4
        
        # Check recent performance in status summary
        status = self.controller.get_status_summary()
        assert len(status["recent_performance"]) == 4
        assert status["metrics"]["total_attempts"] == 4
        assert status["metrics"]["success_rate"] == 0.5
        
        print("✅ Test 3.2.2 PASSED: Performance history tracking works")
    
    def test_automatic_health_check_rollback(self):
        """Test 3.2.3: Automatic rollback on health issues"""
        # Enable optimization
        self.controller.enable_feature(100.0)
        
        # Set very strict health thresholds for testing
        self.controller.min_success_rate = 0.9  # 90% minimum
        self.controller.max_error_rate = 0.1    # 10% maximum
        self.controller.health_check_window = 10
        
        # Record mostly failed attempts (will trigger rollback)
        for i in range(12):
            if i < 2:  # Only 2 successes out of 12
                self.controller.record_attempt(True, 85.0, 0.5)
            else:
                self.controller.record_attempt(False, 45.0, 0.5, "exception")
        
        # Should have triggered automatic rollback
        assert self.controller.status == OptimizationStatus.ROLLBACK
        assert self.controller.enable_optimization == False
        
        print("✅ Test 3.2.3 PASSED: Automatic health check rollback works")
    
    def test_manual_emergency_rollback(self):
        """Test 3.2.4: Manual emergency rollback"""
        # Enable optimization
        self.controller.enable_feature(100.0)
        
        # Trigger manual rollback
        rollback_event = self.controller.emergency_rollback("Manual testing rollback")
        
        # Check system state
        assert self.controller.status == OptimizationStatus.ROLLBACK
        assert self.controller.enable_optimization == False
        assert self.controller.rollout_percentage == 0.0
        assert self.controller.should_optimize() == False
        
        # Check rollback event
        assert "timestamp" in rollback_event
        assert rollback_event["reason"] == "Manual testing rollback"
        assert "metrics_at_rollback" in rollback_event
        
        print("✅ Test 3.2.4 PASSED: Manual emergency rollback works")
    
    def test_rollback_state_prevents_optimization(self):
        """Test 3.2.5: Rollback state prevents all optimization"""
        # Set to rollback state
        self.controller.emergency_rollback("Test rollback")
        
        # Even if we try to enable, should stay disabled
        assert self.controller.should_optimize() == False
        assert self.controller.should_optimize(user_id="any_user") == False
        assert self.controller.should_optimize(tool_types=["any_tool"]) == False
        
        print("✅ Test 3.2.5 PASSED: Rollback state prevents all optimization")
    
    def test_status_summary(self):
        """Test 3.2.6: Comprehensive status summary"""
        # Setup some state
        self.controller.enable_feature(75.0)
        self.controller.add_to_user_whitelist(["user1", "user2"])
        self.controller.add_to_tool_whitelist(["tool1"])
        self.controller.record_attempt(True, 85.0, 0.5)
        
        status = self.controller.get_status_summary()
        
        # Check all expected fields
        assert status["optimization_enabled"] == True
        assert status["rollout_percentage"] == 75.0
        assert status["status"] == "testing"
        assert "metrics" in status
        assert "whitelists" in status
        assert status["whitelists"]["users"] == 2
        assert status["whitelists"]["tool_types"] == 1
        assert "recent_performance" in status
        
        print("✅ Test 3.2.6 PASSED: Status summary comprehensive")
    
    def test_consistent_user_assignment(self):
        """Test 3.3.1: Users get consistent rollout assignment"""
        self.controller.enable_feature(50.0)
        
        # Same user should always get same result
        user_id = "test_user_123"
        first_result = self.controller.should_optimize(user_id=user_id)
        
        for _ in range(10):
            assert self.controller.should_optimize(user_id=user_id) == first_result
        
        print("✅ Test 3.3.1 PASSED: Consistent user assignment works")


def run_all_phase3_tests():
    """Run all Phase 3 tests comprehensively"""
    print("🧪 STARTING PHASE 3 COMPREHENSIVE TESTING")
    print("=" * 60)
    
    # Test OptimizationController
    print("\n🎛️ Testing OptimizationController...")
    controller_tests = TestOptimizationController()
    
    # Feature flag tests
    controller_tests.setup_method()
    controller_tests.test_master_toggle_disabled_by_default()
    
    controller_tests.setup_method()
    controller_tests.test_enable_disable_feature()
    
    controller_tests.setup_method()
    controller_tests.test_percentage_based_rollout()
    
    controller_tests.setup_method()
    controller_tests.test_user_whitelist()
    
    controller_tests.setup_method()
    controller_tests.test_tool_type_whitelist()
    
    # Monitoring tests
    controller_tests.setup_method()
    controller_tests.test_metrics_tracking()
    
    controller_tests.setup_method()
    controller_tests.test_performance_history()
    
    controller_tests.setup_method()
    controller_tests.test_automatic_health_check_rollback()
    
    controller_tests.setup_method()
    controller_tests.test_manual_emergency_rollback()
    
    controller_tests.setup_method()
    controller_tests.test_rollback_state_prevents_optimization()
    
    controller_tests.setup_method()
    controller_tests.test_status_summary()
    
    controller_tests.setup_method()
    controller_tests.test_consistent_user_assignment()
    
    print("\n" + "=" * 60)
    print("🎉 ALL PHASE 3 TESTS COMPLETED SUCCESSFULLY!")
    print("✅ Feature flags and monitoring system ready for deployment")


if __name__ == "__main__":
    run_all_phase3_tests()