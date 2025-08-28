"""
Arbitrator Logging Configuration
Centralized logging setup for arbitrator system with stability monitoring
"""

import logging
import sys
from pathlib import Path

def setup_arbitrator_logging(config: dict):
    """Configure comprehensive logging for arbitrator system"""
    
    # Get arbitrator logging config
    arbitrator_config = config.get('debug', {}).get('arbitrator_logging', {})
    
    if not arbitrator_config.get('enabled', True):
        return
    
    # Create arbitrator logger
    arbitrator_logger = logging.getLogger('arbitrator')
    arbitrator_logger.setLevel(logging.DEBUG if arbitrator_config.get('detailed_timing', True) else logging.INFO)
    
    # Prevent duplicate handlers
    if arbitrator_logger.handlers:
        return
    
    # File handler for arbitrator-specific logs
    log_file = Path("/home/sabawi/Development/flaskserver/arbitrator.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler for immediate feedback during development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Detailed formatter for file logs
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(detailed_formatter)
    
    # Concise formatter for console
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    arbitrator_logger.addHandler(file_handler)
    arbitrator_logger.addHandler(console_handler)
    
    # Configure specific loggers for different components
    if arbitrator_config.get('log_entry_exit', True):
        logging.getLogger('arbitrator.function_calls').setLevel(logging.DEBUG)
    
    if arbitrator_config.get('log_return_values', True):
        logging.getLogger('arbitrator.return_values').setLevel(logging.DEBUG)
        
    if arbitrator_config.get('log_circuit_breaker', True):
        logging.getLogger('arbitrator.circuit_breaker').setLevel(logging.DEBUG)
        
    if arbitrator_config.get('log_retry_attempts', True):
        logging.getLogger('arbitrator.retry_logic').setLevel(logging.DEBUG)
    
    arbitrator_logger.info("🔍 ARBITRATOR LOGGING: Comprehensive logging initialized")
    arbitrator_logger.debug(f"🔍 LOGGING CONFIG: {arbitrator_config}")

def log_system_state(description: str, state_data: dict):
    """Log system state for debugging stability issues"""
    
    logger = logging.getLogger('arbitrator.system_state')
    logger.info(f"📊 SYSTEM STATE: {description}")
    logger.debug(f"📊 STATE DATA: {state_data}")

def log_performance_metrics(operation: str, metrics: dict):
    """Log performance metrics for optimization tracking"""
    
    logger = logging.getLogger('arbitrator.performance')
    logger.info(f"⚡ PERFORMANCE: {operation} | {metrics.get('execution_time', 0):.3f}s")
    logger.debug(f"⚡ METRICS: {metrics}")

def log_stability_checkpoint(checkpoint_name: str, success_count: int, failure_count: int, stability_score: float):
    """Log stability checkpoints to track system maturity"""
    
    logger = logging.getLogger('arbitrator.stability')
    logger.info(f"🛡️ STABILITY: {checkpoint_name} | Success: {success_count} | Failures: {failure_count} | Score: {stability_score:.2f}")
    
    if stability_score < 0.8:
        logger.warning(f"⚠️ STABILITY CONCERN: {checkpoint_name} stability below threshold (0.8)")
    elif stability_score > 0.95:
        logger.info(f"🎯 STABILITY MILESTONE: {checkpoint_name} highly stable (>0.95)")

# Example log message formats for documentation
EXAMPLE_LOG_MESSAGES = {
    "entry": "🔵 ARBITRATOR ENTRY: evaluate_task_with_safety_1 | evaluate_task_with_safety",
    "exit": "🟢 ARBITRATOR EXIT: evaluate_task_with_safety_1 | 0.156s",
    "llm_call": "🤖 ARBITRATOR LLM CALL: gpt-4o-mini | 0.234s | 1024→256 chars",
    "circuit_breaker": "🚨 CIRCUIT BREAKER: task_3 | Decision: True",
    "retry_attempt": "🔄 RETRY ATTEMPT: task_2 | Attempt #2",
    "task_evaluation": "⚖️ TASK EVALUATION: task_1 | Status: RETRY | Confidence: 0.85",
    "session_start": "🎯 ARBITRATOR SESSION START: 4 tasks",
    "session_end": "🏁 ARBITRATOR SESSION END: 3/4 tasks | 75.0% success | 12.456s",
    "pattern_detection": "🔍 PATTERN DETECTED: INFINITE_LOOP | Task: task_2",
    "stability_checkpoint": "🛡️ STABILITY: hourly_checkpoint | Success: 45 | Failures: 3 | Score: 0.94"
}