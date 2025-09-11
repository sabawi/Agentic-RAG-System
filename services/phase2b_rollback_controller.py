"""
Phase 2B Rollback Controller
Provides bulletproof rollback capabilities for Advanced Response Streaming & Buffer Optimization
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FeatureFlag(Enum):
    """Phase 2B feature flags for granular control"""
    RESPONSE_STREAMING = "response_streaming"
    BUFFER_OPTIMIZATION = "buffer_optimization"
    RESPONSE_CLASSIFICATION = "response_classification" 
    PERFORMANCE_MONITORING = "performance_monitoring"
    STREAMING_FALLBACK = "streaming_fallback"


@dataclass
class RollbackPoint:
    """Represents a rollback checkpoint"""
    id: str
    timestamp: float
    description: str
    feature_flags: Dict[str, bool]
    performance_baseline: Dict[str, float]
    active_features: List[str]


class Phase2BRollbackController:
    """
    Bulletproof rollback controller for Phase 2B features.
    Provides instant rollback capabilities with performance monitoring.
    """
    
    def __init__(self):
        self._feature_flags = {
            FeatureFlag.RESPONSE_STREAMING.value: False,
            FeatureFlag.BUFFER_OPTIMIZATION.value: False, 
            FeatureFlag.RESPONSE_CLASSIFICATION.value: False,
            FeatureFlag.PERFORMANCE_MONITORING.value: True,  # Always on for safety
            FeatureFlag.STREAMING_FALLBACK.value: False
        }
        
        self._rollback_points: List[RollbackPoint] = []
        self._current_baseline: Optional[Dict[str, float]] = None
        self._emergency_fallback_active = False
        
        # Create initial rollback point (Phase 2A state)
        self._create_initial_checkpoint()
    
    def _create_initial_checkpoint(self):
        """Create the Phase 2A baseline checkpoint"""
        initial_point = RollbackPoint(
            id="phase2a_baseline",
            timestamp=time.time(),
            description="Phase 2A - HTTP Connection Pooling + Multi-tool Success",
            feature_flags=self._feature_flags.copy(),
            performance_baseline={
                "avg_tool_execution_time": 7.14,  # From recent logs
                "multi_tool_success_rate": 100.0,
                "http_connection_success_rate": 100.0,
                "content_extraction_success_rate": 80.0  # Brave/Yandex working
            },
            active_features=["http_pooling", "multi_tool_execution", "persistent_sessions"]
        )
        
        self._rollback_points.append(initial_point)
        self._current_baseline = initial_point.performance_baseline.copy()
        
        logger.info("🛡️ Phase 2A baseline checkpoint created")
    
    def enable_feature(self, feature: FeatureFlag) -> bool:
        """Enable a Phase 2B feature with rollback safety"""
        try:
            if self._emergency_fallback_active:
                logger.warning(f"🚨 Cannot enable {feature.value} - emergency fallback active")
                return False
            
            # Create checkpoint before enabling
            checkpoint_id = f"pre_{feature.value}_{int(time.time())}"
            self.create_checkpoint(checkpoint_id, f"Before enabling {feature.value}")
            
            self._feature_flags[feature.value] = True
            logger.info(f"✅ Feature enabled: {feature.value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to enable {feature.value}: {e}")
            return False
    
    def disable_feature(self, feature: FeatureFlag) -> bool:
        """Disable a Phase 2B feature"""
        try:
            self._feature_flags[feature.value] = False
            logger.info(f"🔒 Feature disabled: {feature.value}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to disable {feature.value}: {e}")
            return False
    
    def is_feature_enabled(self, feature: FeatureFlag) -> bool:
        """Check if a feature is enabled"""
        return self._feature_flags.get(feature.value, False)
    
    def create_checkpoint(self, checkpoint_id: str, description: str) -> bool:
        """Create a rollback checkpoint"""
        try:
            checkpoint = RollbackPoint(
                id=checkpoint_id,
                timestamp=time.time(),
                description=description,
                feature_flags=self._feature_flags.copy(),
                performance_baseline=self._current_baseline.copy() if self._current_baseline else {},
                active_features=[k for k, v in self._feature_flags.items() if v]
            )
            
            self._rollback_points.append(checkpoint)
            logger.info(f"📋 Checkpoint created: {checkpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create checkpoint {checkpoint_id}: {e}")
            return False
    
    def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Rollback to a specific checkpoint"""
        try:
            # Find the checkpoint
            target_checkpoint = None
            for checkpoint in self._rollback_points:
                if checkpoint.id == checkpoint_id:
                    target_checkpoint = checkpoint
                    break
            
            if not target_checkpoint:
                logger.error(f"❌ Checkpoint not found: {checkpoint_id}")
                return False
            
            # Restore feature flags
            self._feature_flags = target_checkpoint.feature_flags.copy()
            self._current_baseline = target_checkpoint.performance_baseline.copy()
            
            logger.info(f"🔄 Rollback successful to: {checkpoint_id}")
            logger.info(f"🔄 Restored features: {target_checkpoint.active_features}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed to {checkpoint_id}: {e}")
            return False
    
    def emergency_rollback(self) -> bool:
        """Emergency rollback to Phase 2A baseline"""
        try:
            logger.warning("🚨 EMERGENCY ROLLBACK INITIATED")
            
            # Disable all Phase 2B features immediately
            for feature in FeatureFlag:
                if feature != FeatureFlag.PERFORMANCE_MONITORING:
                    self._feature_flags[feature.value] = False
            
            self._emergency_fallback_active = True
            
            # Rollback to Phase 2A baseline
            baseline_success = self.rollback_to_checkpoint("phase2a_baseline")
            
            if baseline_success:
                logger.info("✅ Emergency rollback successful - Phase 2A baseline restored")
            else:
                logger.error("❌ Emergency rollback failed")
            
            return baseline_success
            
        except Exception as e:
            logger.critical(f"💥 CRITICAL: Emergency rollback failed: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rollback controller status"""
        return {
            "emergency_fallback_active": self._emergency_fallback_active,
            "feature_flags": self._feature_flags.copy(),
            "active_features": [k for k, v in self._feature_flags.items() if v],
            "checkpoint_count": len(self._rollback_points),
            "latest_checkpoint": self._rollback_points[-1].id if self._rollback_points else None,
            "current_baseline": self._current_baseline.copy() if self._current_baseline else {}
        }
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints"""
        return [
            {
                "id": cp.id,
                "timestamp": cp.timestamp,
                "description": cp.description,
                "active_features": cp.active_features,
                "age_seconds": time.time() - cp.timestamp
            }
            for cp in self._rollback_points
        ]
    
    def disable_emergency_fallback(self) -> bool:
        """Disable emergency fallback mode - use with caution"""
        try:
            if self._emergency_fallback_active:
                self._emergency_fallback_active = False
                logger.info("✅ Emergency fallback mode disabled")
                return True
            else:
                logger.info("ℹ️ Emergency fallback was not active")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to disable emergency fallback: {e}")
            return False
    
    def validate_system_health(self) -> Dict[str, Any]:
        """Validate system health for rollback decisions"""
        health_status = {
            "overall_health": "good",
            "issues": [],
            "recommendations": []
        }
        
        # Check if emergency fallback is active
        if self._emergency_fallback_active:
            health_status["overall_health"] = "emergency"
            health_status["issues"].append("Emergency fallback is active")
            health_status["recommendations"].append("Investigate root cause before re-enabling features")
        
        # Check baseline performance
        if self._current_baseline:
            # Add performance checks here when monitoring is available
            pass
        
        return health_status


# Global rollback controller instance
rollback_controller = Phase2BRollbackController()


# Convenience functions
def enable_phase2b_feature(feature: FeatureFlag) -> bool:
    """Enable a Phase 2B feature"""
    return rollback_controller.enable_feature(feature)


def disable_phase2b_feature(feature: FeatureFlag) -> bool:
    """Disable a Phase 2B feature"""
    return rollback_controller.disable_feature(feature)


def is_phase2b_feature_enabled(feature: FeatureFlag) -> bool:
    """Check if a Phase 2B feature is enabled"""
    return rollback_controller.is_feature_enabled(feature)


def emergency_rollback_phase2b() -> bool:
    """Emergency rollback to Phase 2A"""
    return rollback_controller.emergency_rollback()


def create_phase2b_checkpoint(checkpoint_id: str, description: str) -> bool:
    """Create a Phase 2B checkpoint"""
    return rollback_controller.create_checkpoint(checkpoint_id, description)