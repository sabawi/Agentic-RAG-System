"""
Arbitrator System Comprehensive Logging Module
Provides detailed entry/exit logging for all arbitrator functions until system stability is proven
"""

import logging
import time
import json
import functools
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass

# Configure arbitrator-specific logger
arbitrator_logger = logging.getLogger('arbitrator')
arbitrator_logger.setLevel(logging.DEBUG)

@dataclass
class LogEntry:
    timestamp: float
    function_name: str
    entry_data: Dict[str, Any]
    exit_data: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    success: bool = True
    error: Optional[str] = None

class ArbitratorLogger:
    """Centralized logging for arbitrator system with detailed tracking"""
    
    def __init__(self):
        self.active_calls = {}
        self.call_counter = 0
        
    def log_function_entry(self, func_name: str, **kwargs) -> str:
        """Log function entry with parameters"""
        call_id = f"{func_name}_{self.call_counter}"
        self.call_counter += 1
        
        entry_data = {
            "call_id": call_id,
            "function": func_name,
            "parameters": self._sanitize_log_data(kwargs),
            "timestamp": time.time()
        }
        
        self.active_calls[call_id] = LogEntry(
            timestamp=time.time(),
            function_name=func_name,
            entry_data=entry_data
        )
        
        arbitrator_logger.info(f"🔵 ARBITRATOR ENTRY: {call_id} | {func_name}")
        arbitrator_logger.debug(f"🔵 ENTRY DATA: {json.dumps(entry_data, indent=2)}")
        
        return call_id
    
    def log_function_exit(self, call_id: str, return_value: Any = None, error: Exception = None):
        """Log function exit with return value and timing"""
        if call_id not in self.active_calls:
            arbitrator_logger.warning(f"⚠️ EXIT LOG: Unknown call_id {call_id}")
            return
        
        log_entry = self.active_calls[call_id]
        log_entry.execution_time = time.time() - log_entry.timestamp
        log_entry.success = error is None
        log_entry.error = str(error) if error else None
        
        exit_data = {
            "call_id": call_id,
            "execution_time": log_entry.execution_time,
            "success": log_entry.success,
            "return_value": self._sanitize_log_data(return_value),
            "error": log_entry.error
        }
        
        log_entry.exit_data = exit_data
        
        status_emoji = "🟢" if log_entry.success else "🔴"
        arbitrator_logger.info(f"{status_emoji} ARBITRATOR EXIT: {call_id} | {log_entry.execution_time:.3f}s")
        arbitrator_logger.debug(f"{status_emoji} EXIT DATA: {json.dumps(exit_data, indent=2)}")
        
        # Clean up completed calls
        del self.active_calls[call_id]
    
    def log_circuit_breaker_decision(self, task_id: str, decision: Dict[str, Any]):
        """Log circuit breaker decisions with full context"""
        log_data = {
            "task_id": task_id,
            "decision": decision,
            "timestamp": time.time()
        }
        
        arbitrator_logger.info(f"🚨 CIRCUIT BREAKER: {task_id} | Decision: {decision.get('should_break', False)}")
        arbitrator_logger.debug(f"🚨 CIRCUIT BREAKER DATA: {json.dumps(log_data, indent=2)}")
    
    def log_retry_attempt(self, task_id: str, attempt_number: int, feedback: str, modified_params: Dict[str, Any]):
        """Log retry attempts with modifications"""
        log_data = {
            "task_id": task_id,
            "attempt_number": attempt_number,
            "feedback": feedback,
            "modified_parameters": self._sanitize_log_data(modified_params),
            "timestamp": time.time()
        }
        
        arbitrator_logger.info(f"🔄 RETRY ATTEMPT: {task_id} | Attempt #{attempt_number}")
        arbitrator_logger.debug(f"🔄 RETRY DATA: {json.dumps(log_data, indent=2)}")
    
    def log_task_evaluation(self, task_id: str, result: Dict[str, Any], arbitrator_response: Dict[str, Any]):
        """Log complete task evaluation with inputs and outputs"""
        log_data = {
            "task_id": task_id,
            "evaluation_input": self._sanitize_log_data(result),
            "arbitrator_decision": arbitrator_response,
            "timestamp": time.time()
        }
        
        status = arbitrator_response.get('status', 'UNKNOWN')
        confidence = arbitrator_response.get('confidence', 0.0)
        
        arbitrator_logger.info(f"⚖️ TASK EVALUATION: {task_id} | Status: {status} | Confidence: {confidence}")
        arbitrator_logger.debug(f"⚖️ EVALUATION DATA: {json.dumps(log_data, indent=2)}")
    
    def log_llm_call(self, model: str, prompt_length: int, response_length: int, execution_time: float):
        """Log arbitrator LLM API calls"""
        log_data = {
            "model": model,
            "prompt_length": prompt_length,
            "response_length": response_length,
            "execution_time": execution_time,
            "timestamp": time.time()
        }
        
        arbitrator_logger.info(f"🤖 ARBITRATOR LLM CALL: {model} | {execution_time:.3f}s | {prompt_length}→{response_length} chars")
        arbitrator_logger.debug(f"🤖 LLM CALL DATA: {json.dumps(log_data, indent=2)}")
    
    def _sanitize_log_data(self, data: Any) -> Any:
        """Sanitize data for logging (remove sensitive info, truncate large content)"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if key.lower() in ['api_key', 'password', 'token', 'secret']:
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, str) and len(value) > 1000:
                    sanitized[key] = value[:500] + f"...[truncated {len(value)-500} chars]"
                else:
                    sanitized[key] = self._sanitize_log_data(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_log_data(item) for item in data[:10]]  # Limit to first 10 items
        elif isinstance(data, str) and len(data) > 1000:
            return data[:500] + f"...[truncated {len(data)-500} chars]"
        else:
            return data

# Global logger instance
arb_logger = ArbitratorLogger()

def log_arbitrator_function(func: Callable) -> Callable:
    """Decorator for automatic entry/exit logging of arbitrator functions"""
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        call_id = arb_logger.log_function_entry(func.__name__, args=args, kwargs=kwargs)
        try:
            result = await func(*args, **kwargs)
            arb_logger.log_function_exit(call_id, return_value=result)
            return result
        except Exception as e:
            arb_logger.log_function_exit(call_id, error=e)
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        call_id = arb_logger.log_function_entry(func.__name__, args=args, kwargs=kwargs)
        try:
            result = func(*args, **kwargs)
            arb_logger.log_function_exit(call_id, return_value=result)
            return result
        except Exception as e:
            arb_logger.log_function_exit(call_id, error=e)
            raise
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# Logging helper functions for specific arbitrator operations
def log_arbitrator_session_start(user_prompt: str, tasks: list):
    """Log the start of a new arbitrator session"""
    log_data = {
        "user_prompt": user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt,
        "total_tasks": len(tasks),
        "task_descriptions": [task.get('description', 'Unknown') for task in tasks],
        "session_start": time.time()
    }
    
    arbitrator_logger.info(f"🎯 ARBITRATOR SESSION START: {len(tasks)} tasks")
    arbitrator_logger.debug(f"🎯 SESSION DATA: {json.dumps(log_data, indent=2)}")

def log_arbitrator_session_end(completed_tasks: int, failed_tasks: int, total_time: float):
    """Log the end of an arbitrator session with summary"""
    log_data = {
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "total_tasks": completed_tasks + failed_tasks,
        "success_rate": completed_tasks / (completed_tasks + failed_tasks) if (completed_tasks + failed_tasks) > 0 else 0,
        "total_execution_time": total_time,
        "session_end": time.time()
    }
    
    success_rate = log_data['success_rate'] * 100
    arbitrator_logger.info(f"🏁 ARBITRATOR SESSION END: {completed_tasks}/{log_data['total_tasks']} tasks | {success_rate:.1f}% success | {total_time:.3f}s")
    arbitrator_logger.debug(f"🏁 SESSION SUMMARY: {json.dumps(log_data, indent=2)}")

def log_pattern_detection(pattern_type: str, task_id: str, pattern_data: Dict[str, Any]):
    """Log pattern detection events (infinite loops, contradictions, etc.)"""
    log_data = {
        "pattern_type": pattern_type,
        "task_id": task_id,
        "pattern_data": pattern_data,
        "timestamp": time.time()
    }
    
    arbitrator_logger.warning(f"🔍 PATTERN DETECTED: {pattern_type} | Task: {task_id}")
    arbitrator_logger.debug(f"🔍 PATTERN DATA: {json.dumps(log_data, indent=2)}")