"""
Arbitrator System with Comprehensive Logging
Complete implementation of task validation and retry logic with detailed tracking
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from arbitrator_logger import (
    log_arbitrator_function, 
    arb_logger,
    log_arbitrator_session_start,
    log_arbitrator_session_end,
    log_pattern_detection
)

class TaskStatus(Enum):
    GOOD = "GOOD"
    BAD = "BAD" 
    RETRY = "RETRY"
    UNACHIEVABLE = "UNACHIEVABLE"

class CircuitBreakerReason(Enum):
    MAX_RETRIES = "MAX_RETRIES"
    INFINITE_LOOP = "INFINITE_LOOP"
    CONTRADICTION = "CONTRADICTION"
    IMPOSSIBILITY = "IMPOSSIBILITY"

@dataclass
class TaskResult:
    success: bool
    output: str
    error_message: Optional[str] = None
    execution_time: float = 0.0

@dataclass
class ArbitratorDecision:
    status: TaskStatus
    confidence: float
    feedback: str
    retry_suggestion: Optional[Dict[str, Any]] = None
    circuit_breaker: Optional[Dict[str, Any]] = None

@dataclass
class Task:
    id: str
    description: str
    tool: str
    parameters: Dict[str, Any]
    expected_outcome: str

class CircuitBreakerManager:
    """Manages circuit breaker logic with comprehensive logging"""
    
    def __init__(self):
        self.retry_counts = {}
        self.error_patterns = {}
        self.feedback_history = {}
        self.max_retries_per_task = 3
        self.max_total_retries = 10
        self.total_retries = 0
        
    @log_arbitrator_function
    def should_break_circuit(self, task_id: str, error: str, feedback: str, attempt_number: int) -> Dict[str, Any]:
        """Determine if circuit should break with detailed logging"""
        
        # Update counters
        self.retry_counts[task_id] = self.retry_counts.get(task_id, 0) + 1
        self.total_retries += 1
        
        # Track patterns
        if task_id not in self.error_patterns:
            self.error_patterns[task_id] = []
            self.feedback_history[task_id] = []
            
        self.error_patterns[task_id].append(error)
        self.feedback_history[task_id].append(feedback)
        
        decision = {
            "should_break": False,
            "break_reason": None,
            "escalation_strategy": None,
            "retry_count": self.retry_counts[task_id],
            "total_retries": self.total_retries
        }
        
        # Check per-task retry limit
        if self.retry_counts[task_id] >= self.max_retries_per_task:
            decision.update({
                "should_break": True,
                "break_reason": CircuitBreakerReason.MAX_RETRIES.value,
                "escalation_strategy": "DECLARE_UNACHIEVABLE"
            })
            log_pattern_detection("MAX_TASK_RETRIES", task_id, {"retries": self.retry_counts[task_id]})
            
        # Check total retry limit
        elif self.total_retries >= self.max_total_retries:
            decision.update({
                "should_break": True,
                "break_reason": CircuitBreakerReason.MAX_RETRIES.value,
                "escalation_strategy": "PARTIAL_SUCCESS_ACCEPT"
            })
            log_pattern_detection("MAX_TOTAL_RETRIES", task_id, {"total_retries": self.total_retries})
            
        # Check for infinite loop patterns
        elif self._detect_infinite_loop(task_id):
            decision.update({
                "should_break": True,
                "break_reason": CircuitBreakerReason.INFINITE_LOOP.value,
                "escalation_strategy": "ALTERNATIVE_APPROACH"
            })
            log_pattern_detection("INFINITE_LOOP", task_id, {
                "error_patterns": self.error_patterns[task_id][-3:],
                "feedback_patterns": self.feedback_history[task_id][-3:]
            })
            
        # Check for contradictory feedback
        elif self._detect_contradictory_feedback(task_id):
            decision.update({
                "should_break": True,
                "break_reason": CircuitBreakerReason.CONTRADICTION.value,
                "escalation_strategy": "USER_GUIDANCE"
            })
            log_pattern_detection("CONTRADICTORY_FEEDBACK", task_id, {
                "feedback_history": self.feedback_history[task_id]
            })
        
        arb_logger.log_circuit_breaker_decision(task_id, decision)
        return decision
    
    @log_arbitrator_function
    def _detect_infinite_loop(self, task_id: str) -> bool:
        """Detect if task is stuck in infinite loop"""
        if len(self.error_patterns[task_id]) < 3:
            return False
            
        # Check if last 3 errors are similar
        recent_errors = self.error_patterns[task_id][-3:]
        return len(set(recent_errors)) <= 1  # All same or very similar
    
    @log_arbitrator_function  
    def _detect_contradictory_feedback(self, task_id: str) -> bool:
        """Detect contradictory arbitrator feedback"""
        if len(self.feedback_history[task_id]) < 2:
            return False
            
        recent_feedback = self.feedback_history[task_id][-2:]
        
        # Simple contradiction detection (opposite instructions)
        contradictory_pairs = [
            ("shorten", "lengthen"),
            ("increase", "decrease"),
            ("add", "remove"),
            ("enable", "disable")
        ]
        
        for word1, word2 in contradictory_pairs:
            if (word1 in recent_feedback[0].lower() and word2 in recent_feedback[1].lower()) or \
               (word2 in recent_feedback[0].lower() and word1 in recent_feedback[1].lower()):
                return True
                
        return False

class ArbitratorLLM:
    """Manages calls to arbitrator LLM with comprehensive logging"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        self.system_prompt = self._load_system_prompt()
        
    @log_arbitrator_function
    def _load_system_prompt(self) -> str:
        """Load arbitrator system prompt from file"""
        try:
            with open('/home/sabawi/Development/flaskserver/config/arbitrator_system_prompt.txt', 'r') as f:
                return f.read()
        except Exception as e:
            arbitrator_logger.error(f"❌ Failed to load arbitrator system prompt: {e}")
            return "You are an arbitrator that validates task execution results."
    
    @log_arbitrator_function
    async def evaluate_task(self, task: Task, result: TaskResult, context: Dict[str, Any]) -> ArbitratorDecision:
        """Evaluate task result using arbitrator LLM"""
        
        # Prepare input for arbitrator
        arbitrator_input = {
            "task": {
                "id": task.id,
                "description": task.description,
                "tool": task.tool,
                "parameters": task.parameters,
                "expected_outcome": task.expected_outcome
            },
            "result": {
                "success": result.success,
                "output": result.output,
                "error_message": result.error_message,
                "execution_time": result.execution_time
            },
            "context": context
        }
        
        prompt = json.dumps(arbitrator_input, indent=2)
        
        # Call arbitrator LLM
        start_time = time.time()
        try:
            response = await self.llm_manager.call_arbitrator(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
            execution_time = time.time() - start_time
            
            arb_logger.log_llm_call(
                model="arbitrator",
                prompt_length=len(prompt),
                response_length=len(response),
                execution_time=execution_time
            )
            
            # Parse JSON response
            arbitrator_response = json.loads(response)
            
            # Convert to ArbitratorDecision
            decision = ArbitratorDecision(
                status=TaskStatus(arbitrator_response["status"]),
                confidence=arbitrator_response["confidence"],
                feedback=arbitrator_response["feedback"],
                retry_suggestion=arbitrator_response.get("retry_suggestion"),
                circuit_breaker=arbitrator_response.get("circuit_breaker")
            )
            
            arb_logger.log_task_evaluation(task.id, arbitrator_input, arbitrator_response)
            return decision
            
        except Exception as e:
            execution_time = time.time() - start_time
            arbitrator_logger.error(f"❌ Arbitrator LLM call failed: {e}")
            
            # Fallback decision
            return ArbitratorDecision(
                status=TaskStatus.BAD,
                confidence=0.5,
                feedback=f"Arbitrator LLM failed: {str(e)}. Using fallback retry logic.",
                retry_suggestion={"reason": "arbitrator_failure_fallback"}
            )

class ArbitratorSystem:
    """Main arbitrator system with comprehensive logging and circuit breaking"""
    
    def __init__(self, llm_manager):
        self.arbitrator_llm = ArbitratorLLM(llm_manager)
        self.circuit_breaker = CircuitBreakerManager()
        self.session_start_time = None
        
    @log_arbitrator_function
    async def execute_tasks_with_arbitration(self, user_prompt: str, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks sequentially with arbitrator validation"""
        
        self.session_start_time = time.time()
        log_arbitrator_session_start(user_prompt, [{"description": task.description} for task in tasks])
        
        completed_tasks = []
        failed_tasks = []
        
        try:
            for i, task in enumerate(tasks):
                arbitrator_logger.info(f"🎯 ARBITRATOR: Starting task {i+1}/{len(tasks)} | ID: {task.id}")
                
                task_result = await self._execute_single_task_with_validation(task, {
                    "completed_tasks": completed_tasks,
                    "user_prompt": user_prompt,
                    "task_index": i
                })
                
                if task_result["success"]:
                    completed_tasks.append(task_result)
                    arbitrator_logger.info(f"✅ ARBITRATOR: Task {task.id} completed successfully")
                else:
                    failed_tasks.append(task_result)
                    arbitrator_logger.warning(f"❌ ARBITRATOR: Task {task.id} failed permanently")
                    
                    # Check if we should continue or stop
                    if task_result.get("stop_execution", False):
                        arbitrator_logger.info(f"🛑 ARBITRATOR: Stopping execution due to unrecoverable failure")
                        break
            
            # Log session summary
            total_time = time.time() - self.session_start_time
            log_arbitrator_session_end(len(completed_tasks), len(failed_tasks), total_time)
            
            return {
                "success": len(completed_tasks) > 0,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "execution_time": total_time,
                "success_rate": len(completed_tasks) / len(tasks) if tasks else 0
            }
            
        except Exception as e:
            total_time = time.time() - self.session_start_time if self.session_start_time else 0
            arbitrator_logger.error(f"❌ ARBITRATOR SYSTEM ERROR: {e}")
            log_arbitrator_session_end(len(completed_tasks), len(failed_tasks), total_time)
            raise
    
    @log_arbitrator_function
    async def _execute_single_task_with_validation(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single task with arbitrator validation and retry logic"""
        
        attempt_number = 0
        max_attempts = 3
        
        while attempt_number < max_attempts:
            attempt_number += 1
            arbitrator_logger.info(f"🔄 ARBITRATOR: Task {task.id} attempt #{attempt_number}")
            
            # Execute the task
            try:
                task_result = await self._execute_task(task)
            except Exception as e:
                task_result = TaskResult(
                    success=False,
                    output="",
                    error_message=str(e),
                    execution_time=0.0
                )
            
            # Get arbitrator evaluation
            arbitrator_decision = await self.arbitrator_llm.evaluate_task(task, task_result, context)
            
            # Handle decision
            if arbitrator_decision.status == TaskStatus.GOOD:
                arbitrator_logger.info(f"✅ ARBITRATOR: Task {task.id} validated as successful")
                return {
                    "success": True,
                    "task": task,
                    "result": task_result,
                    "attempts": attempt_number,
                    "final_status": "GOOD"
                }
            
            elif arbitrator_decision.status in [TaskStatus.BAD, TaskStatus.RETRY]:
                # Check circuit breaker
                circuit_decision = self.circuit_breaker.should_break_circuit(
                    task_id=task.id,
                    error=task_result.error_message or "Unknown error",
                    feedback=arbitrator_decision.feedback,
                    attempt_number=attempt_number
                )
                
                if circuit_decision["should_break"]:
                    arbitrator_logger.warning(f"🚨 CIRCUIT BREAKER: Breaking for task {task.id} | Reason: {circuit_decision['break_reason']}")
                    return {
                        "success": False,
                        "task": task,
                        "result": task_result,
                        "attempts": attempt_number,
                        "final_status": "CIRCUIT_BROKEN",
                        "break_reason": circuit_decision["break_reason"],
                        "escalation_strategy": circuit_decision["escalation_strategy"],
                        "stop_execution": circuit_decision["break_reason"] in ["IMPOSSIBILITY", "MAX_TOTAL_RETRIES"]
                    }
                
                # Apply arbitrator feedback and retry
                if arbitrator_decision.retry_suggestion:
                    task = self._apply_retry_suggestions(task, arbitrator_decision.retry_suggestion)
                    
                arb_logger.log_retry_attempt(
                    task_id=task.id,
                    attempt_number=attempt_number,
                    feedback=arbitrator_decision.feedback,
                    modified_params=arbitrator_decision.retry_suggestion or {}
                )
                
                arbitrator_logger.info(f"🔄 ARBITRATOR: Retrying task {task.id} with feedback: {arbitrator_decision.feedback[:100]}...")
                
            elif arbitrator_decision.status == TaskStatus.UNACHIEVABLE:
                arbitrator_logger.warning(f"🚫 ARBITRATOR: Task {task.id} declared unachievable")
                return {
                    "success": False,
                    "task": task,
                    "result": task_result,
                    "attempts": attempt_number,
                    "final_status": "UNACHIEVABLE",
                    "arbitrator_feedback": arbitrator_decision.feedback
                }
        
        # Max attempts reached
        arbitrator_logger.error(f"❌ ARBITRATOR: Task {task.id} failed after {max_attempts} attempts")
        return {
            "success": False,
            "task": task,
            "result": task_result,
            "attempts": attempt_number,
            "final_status": "MAX_ATTEMPTS_EXCEEDED"
        }
    
    @log_arbitrator_function
    def _apply_retry_suggestions(self, task: Task, retry_suggestion: Dict[str, Any]) -> Task:
        """Apply arbitrator retry suggestions to modify task parameters"""
        
        if "modified_parameters" in retry_suggestion:
            # Update task parameters with suggestions
            modified_params = retry_suggestion["modified_parameters"]
            task.parameters.update(modified_params)
            
            arbitrator_logger.debug(f"🔧 ARBITRATOR: Applied retry suggestions to task {task.id}")
        
        return task
    
    @log_arbitrator_function
    async def _execute_task(self, task: Task) -> TaskResult:
        """Execute individual task (placeholder - integrate with existing tool system)"""
        
        # This would integrate with the existing sandboxed_executor and other tools
        # For now, return a mock result for logging demonstration
        
        start_time = time.time()
        
        # Placeholder execution logic
        if task.tool == "sandboxed_executor":
            # Simulate tool execution
            await asyncio.sleep(0.1)  # Simulate execution time
            
            # Mock different result types for demonstration
            if "missing_library" in str(task.parameters):
                return TaskResult(
                    success=False,
                    output="",
                    error_message="ModuleNotFoundError: No module named 'pandas'",
                    execution_time=time.time() - start_time
                )
            else:
                return TaskResult(
                    success=True,
                    output="Task completed successfully",
                    error_message=None,
                    execution_time=time.time() - start_time
                )
        
        return TaskResult(
            success=True,
            output="Mock execution completed",
            error_message=None,
            execution_time=time.time() - start_time
        )

@log_arbitrator_function
async def initialize_arbitrator_system(llm_manager) -> ArbitratorSystem:
    """Initialize the arbitrator system with comprehensive logging"""
    
    arbitrator_logger.info("🚀 ARBITRATOR: Initializing arbitrator system")
    system = ArbitratorSystem(llm_manager)
    arbitrator_logger.info("✅ ARBITRATOR: System initialized successfully")
    
    return system