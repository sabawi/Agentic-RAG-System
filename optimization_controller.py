#!/usr/bin/env python3
"""
Optimization Controller with Feature Flags & A/B Testing
Provides safe, gradual rollout of optimization features
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OptimizationStatus(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    TESTING = "testing"
    ROLLBACK = "rollback"

@dataclass
class OptimizationMetrics:
    """Metrics tracking for optimization performance"""
    total_attempts: int = 0
    successful_optimizations: int = 0
    validation_failures: int = 0
    exception_failures: int = 0
    integrity_failures: int = 0
    fallback_count: int = 0
    average_score: float = 0.0
    average_response_time: float = 0.0
    last_updated: str = ""

class OptimizationController:
    """
    Feature flag and A/B testing controller for safe optimization rollout.
    Provides comprehensive monitoring and instant rollback capability.
    """
    
    def __init__(self):
        # Feature flags
        self.enable_optimization = False  # Master toggle
        self.rollout_percentage = 0.0     # 0-100% gradual rollout
        self.status = OptimizationStatus.DISABLED
        
        # Whitelisting
        self.tool_type_whitelist: Set[str] = set()  # Empty = all tools allowed
        self.user_whitelist: Set[str] = set()       # Empty = all users allowed
        
        # Monitoring
        self.metrics = OptimizationMetrics()
        self.performance_history: List[Dict] = []
        
        # Health thresholds for automatic rollback
        self.min_success_rate = 0.8      # 80% minimum success rate
        self.max_error_rate = 0.2        # 20% maximum error rate
        self.health_check_window = 100   # Check last 100 operations
        
        # Logging configuration
        self.detailed_logging = True
        
        logger.info("🎛️ OptimizationController initialized - Status: DISABLED")
    
    def should_optimize(self, user_id: Optional[str] = None, tool_types: Optional[List[str]] = None) -> bool:
        """
        Determine if optimization should be attempted based on feature flags.
        Returns True if optimization should proceed, False otherwise.
        """
        
        # Check master toggle
        if not self.enable_optimization:
            if self.detailed_logging:
                logger.info("🚫 Optimization DISABLED - Master toggle OFF")
            return False
            
        # Check system status
        if self.status == OptimizationStatus.ROLLBACK:
            logger.warning("🚨 Optimization DISABLED - System in ROLLBACK mode")
            return False
            
        # Check if user is whitelisted (overrides rollout percentage)
        user_is_whitelisted = self.user_whitelist and user_id and user_id in self.user_whitelist
        
        # Check user whitelist (if configured and user not whitelisted)
        if self.user_whitelist and user_id and user_id not in self.user_whitelist:
            if self.detailed_logging:
                logger.info(f"🚫 Optimization DISABLED - User {user_id} not in whitelist")
            return False
            
        # Check tool type whitelist (if configured)
        if self.tool_type_whitelist and tool_types:
            if not any(tool_type in self.tool_type_whitelist for tool_type in tool_types):
                if self.detailed_logging:
                    logger.info(f"🚫 Optimization DISABLED - Tool types {tool_types} not whitelisted")
                return False
        
        # Check percentage-based rollout (skip if user is whitelisted)
        if not user_is_whitelisted and self.rollout_percentage < 100.0:
            # Use user_id for consistent user assignment (or request hash if no user)
            hash_input = user_id if user_id else str(time.time())
            user_hash = hashlib.md5(hash_input.encode()).hexdigest()
            user_percentage = int(user_hash[:8], 16) % 100
            
            if user_percentage >= self.rollout_percentage:
                if self.detailed_logging:
                    logger.info(f"🎲 Optimization DISABLED - User hash {user_percentage}% >= rollout {self.rollout_percentage}%")
                return False
        
        # All checks passed
        if self.detailed_logging:
            logger.info(f"✅ Optimization ENABLED - Proceeding with optimization")
        return True
    
    def record_attempt(self, success: bool, validation_score: float, response_time: float, error_type: Optional[str] = None):
        """
        Record optimization attempt for monitoring and health checks.
        """
        self.metrics.total_attempts += 1
        
        if success:
            self.metrics.successful_optimizations += 1
        elif error_type == "validation":
            self.metrics.validation_failures += 1
        elif error_type == "exception":
            self.metrics.exception_failures += 1
        elif error_type == "integrity":
            self.metrics.integrity_failures += 1
        else:
            self.metrics.fallback_count += 1
            
        # Update averages
        total_scores = (self.metrics.average_score * (self.metrics.total_attempts - 1)) + validation_score
        self.metrics.average_score = total_scores / self.metrics.total_attempts
        
        total_times = (self.metrics.average_response_time * (self.metrics.total_attempts - 1)) + response_time
        self.metrics.average_response_time = total_times / self.metrics.total_attempts
        
        self.metrics.last_updated = datetime.now().isoformat()
        
        # Add to performance history (keep last 1000 entries)
        self.performance_history.append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "validation_score": validation_score,
            "response_time": response_time,
            "error_type": error_type
        })
        
        if len(self.performance_history) > 1000:
            self.performance_history.pop(0)
        
        # Check system health after each record
        self._check_system_health()
        
        if self.detailed_logging:
            logger.info(f"📊 METRICS: Attempts={self.metrics.total_attempts}, "
                       f"Success Rate={self.get_success_rate():.1%}, "
                       f"Avg Score={self.metrics.average_score:.1f}")
    
    def get_success_rate(self) -> float:
        """Calculate current success rate"""
        if self.metrics.total_attempts == 0:
            return 1.0
        return self.metrics.successful_optimizations / self.metrics.total_attempts
    
    def get_error_rate(self) -> float:
        """Calculate current error rate"""
        if self.metrics.total_attempts == 0:
            return 0.0
        total_errors = (self.metrics.validation_failures + 
                       self.metrics.exception_failures + 
                       self.metrics.integrity_failures)
        return total_errors / self.metrics.total_attempts
    
    def _check_system_health(self):
        """
        Check system health and trigger automatic rollback if necessary.
        Uses sliding window of recent operations.
        """
        if len(self.performance_history) < 10:  # Need minimum data
            return
            
        # Look at recent operations (last N or last hour, whichever is smaller)
        recent_window = min(self.health_check_window, len(self.performance_history))
        recent_operations = self.performance_history[-recent_window:]
        
        # Calculate recent success rate
        recent_successes = sum(1 for op in recent_operations if op["success"])
        recent_success_rate = recent_successes / len(recent_operations)
        
        # Calculate recent error rate
        recent_errors = sum(1 for op in recent_operations if op["error_type"] in ["exception", "integrity"])
        recent_error_rate = recent_errors / len(recent_operations)
        
        # Check health thresholds
        health_issues = []
        if recent_success_rate < self.min_success_rate:
            health_issues.append(f"Low success rate: {recent_success_rate:.1%} < {self.min_success_rate:.1%}")
            
        if recent_error_rate > self.max_error_rate:
            health_issues.append(f"High error rate: {recent_error_rate:.1%} > {self.max_error_rate:.1%}")
        
        # Trigger automatic rollback if health issues detected
        if health_issues and self.status != OptimizationStatus.ROLLBACK:
            logger.error(f"🚨 AUTOMATIC ROLLBACK TRIGGERED: {health_issues}")
            self.emergency_rollback(f"Automatic health check failure: {', '.join(health_issues)}")
    
    def enable_feature(self, rollout_percentage: float = 100.0):
        """Enable optimization with optional gradual rollout"""
        self.enable_optimization = True
        self.rollout_percentage = max(0.0, min(100.0, rollout_percentage))
        self.status = OptimizationStatus.ENABLED if rollout_percentage == 100.0 else OptimizationStatus.TESTING
        
        logger.info(f"✅ Optimization ENABLED - Rollout: {self.rollout_percentage}% - Status: {self.status.value}")
    
    def disable_feature(self):
        """Disable optimization completely"""
        self.enable_optimization = False
        self.rollout_percentage = 0.0
        self.status = OptimizationStatus.DISABLED
        
        logger.info("🚫 Optimization DISABLED")
    
    def set_rollout_percentage(self, percentage: float):
        """Update rollout percentage for gradual deployment"""
        old_percentage = self.rollout_percentage
        self.rollout_percentage = max(0.0, min(100.0, percentage))
        
        if self.rollout_percentage == 100.0:
            self.status = OptimizationStatus.ENABLED
        elif self.rollout_percentage > 0:
            self.status = OptimizationStatus.TESTING
        else:
            self.status = OptimizationStatus.DISABLED
            
        logger.info(f"🎲 Rollout percentage changed: {old_percentage}% → {self.rollout_percentage}%")
    
    def add_to_user_whitelist(self, user_ids: List[str]):
        """Add users to testing whitelist"""
        self.user_whitelist.update(user_ids)
        logger.info(f"👥 Added {len(user_ids)} users to whitelist. Total: {len(self.user_whitelist)}")
    
    def add_to_tool_whitelist(self, tool_types: List[str]):
        """Add tool types to whitelist"""
        self.tool_type_whitelist.update(tool_types)
        logger.info(f"🔧 Added {len(tool_types)} tool types to whitelist. Total: {len(self.tool_type_whitelist)}")
    
    def emergency_rollback(self, reason: str):
        """Emergency rollback - immediately disable all optimization"""
        self.enable_optimization = False
        self.rollout_percentage = 0.0
        self.status = OptimizationStatus.ROLLBACK
        
        rollback_event = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "metrics_at_rollback": self.get_status_summary()
        }
        
        logger.critical(f"🚨 EMERGENCY ROLLBACK EXECUTED: {reason}")
        logger.critical(f"📊 Metrics at rollback: {rollback_event['metrics_at_rollback']}")
        
        return rollback_event
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary"""
        return {
            "optimization_enabled": self.enable_optimization,
            "rollout_percentage": self.rollout_percentage,
            "status": self.status.value,
            "metrics": {
                "total_attempts": self.metrics.total_attempts,
                "success_rate": self.get_success_rate(),
                "error_rate": self.get_error_rate(),
                "average_score": self.metrics.average_score,
                "average_response_time": self.metrics.average_response_time,
                "last_updated": self.metrics.last_updated
            },
            "whitelists": {
                "users": len(self.user_whitelist),
                "tool_types": len(self.tool_type_whitelist)
            },
            "recent_performance": self.performance_history[-10:] if self.performance_history else []
        }


# Global instance for the FastAPI application
optimization_controller = OptimizationController()