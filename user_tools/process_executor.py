#!/usr/bin/env python3
"""
Process Executor Tool
Provides secure process execution and monitoring with verification capabilities
"""

import os
import sys
import json
import time
import psutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool


class ProcessExecutorTool(BaseUserTool):
    """
    A secure process executor for running commands with proper verification.
    
    Features:
    - Safe command execution with working directory control
    - Process monitoring and verification
    - Background and foreground execution modes
    - Resource limits and security controls
    - Process status tracking and cleanup
    """
    
    def __init__(self):
        super().__init__()
        
        # Security settings
        self.max_execution_time = 300  # 5 minutes for background processes
        self.max_output_size = 100000  # characters
        self.allowed_working_dirs = [
            "/home/sabawi/Development/flaskserver/sandbox_workspace",
            "/home/sabawi/Development/flaskserver/games", 
            "/home/sabawi/Development/flaskserver/projects",
            "/home/sabawi/Development/flaskserver/output",
            "/tmp"
        ]
        
        # Allowed executables for security
        self.allowed_executables = [
            "python3", "python", "node", "gcc", "g++", "rustc", "javac", "java",
            "ls", "cat", "head", "tail", "grep", "find", "pwd", "echo"
        ]
        
        # Process tracking
        self.running_processes = {}
    
    @property
    def name(self) -> str:
        return "process_executor"
    
    @property
    def description(self) -> str:
        return "Execute commands and run processes with verification, monitoring, and working directory control."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to execute. Examples: 'python3 game.py', 'ls -la', 'gcc -o program program.c'"
                },
                "working_directory": {
                    "type": "string", 
                    "description": "Working directory for command execution. Examples: '/games', 'sandbox_workspace', 'projects'"
                },
                "background": {
                    "type": "boolean",
                    "description": "Run command in background (default: false)"
                },
                "verify_execution": {
                    "type": "boolean",
                    "description": "Verify process is actually running (default: true)"
                },
                "timeout": {
                    "type": "number",
                    "description": "Execution timeout in seconds (default: 60 for foreground, 300 for background)"
                },
                "capture_output": {
                    "type": "boolean",
                    "description": "Capture stdout/stderr output (default: true for foreground, false for background)"
                }
            },
            "required": ["command"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute process with enhanced verification."""
        try:
            # Extract parameters
            command = kwargs.get("command", "").strip()
            working_directory = kwargs.get("working_directory", None)
            background = kwargs.get("background", False)
            verify_execution = kwargs.get("verify_execution", True)
            timeout = kwargs.get("timeout", 300 if background else 60)
            capture_output = kwargs.get("capture_output", not background)
            
            if not command:
                return {"success": False, "error": "Command is required", "result": None}
            
            # Validate command security
            is_valid, validation_msg = self._validate_command(command)
            if not is_valid:
                return {"success": False, "error": f"Security violation: {validation_msg}", "result": None}
            
            # Validate and resolve working directory
            is_valid, resolved_wd = self._validate_working_directory(working_directory)
            if not is_valid:
                return {"success": False, "error": resolved_wd, "result": None}
            
            print(f"🚀 PROCESS_EXECUTOR: Executing '{command}' in '{resolved_wd}' (background={background})")
            
            if background:
                return await self._execute_background(command, resolved_wd, verify_execution, timeout, capture_output)
            else:
                return await self._execute_foreground(command, resolved_wd, timeout, capture_output)
                
        except Exception as e:
            return {"success": False, "error": f"Process execution error: {str(e)}", "result": None}
    
    def _validate_command(self, command: str) -> Tuple[bool, str]:
        """Validate command for security."""
        try:
            # Extract executable name
            cmd_parts = command.split()
            if not cmd_parts:
                return False, "Empty command"
            
            executable = cmd_parts[0]
            
            # Check if executable is allowed
            if executable not in self.allowed_executables:
                return False, f"Executable not allowed: {executable}"
            
            # Check for dangerous patterns
            dangerous_patterns = [
                "rm -rf", "sudo", "su", "chmod 777", ">/etc/", "curl.*|", "wget.*|"
            ]
            
            for pattern in dangerous_patterns:
                if pattern in command:
                    return False, f"Dangerous pattern detected: {pattern}"
            
            return True, "Command validated"
            
        except Exception as e:
            return False, f"Command validation error: {e}"
    
    def _validate_working_directory(self, working_directory: str = None) -> Tuple[bool, str]:
        """Validate and resolve working directory."""
        try:
            if not working_directory:
                # Default to sandbox workspace
                default_wd = "/home/sabawi/Development/flaskserver/sandbox_workspace"
                return True, default_wd
            
            wd = working_directory.strip()
            
            # Handle relative paths
            if not wd.startswith("/"):
                base_dir = "/home/sabawi/Development/flaskserver"
                wd = f"{base_dir}/{wd}"
            
            # Normalize path
            resolved_wd = str(Path(wd).resolve())
            
            # Check if directory is allowed
            allowed = False
            for allowed_dir in self.allowed_working_dirs:
                if resolved_wd.startswith(allowed_dir):
                    allowed = True
                    break
            
            if not allowed:
                return False, f"Working directory not allowed: {resolved_wd}"
            
            # Create directory if it doesn't exist
            Path(resolved_wd).mkdir(parents=True, exist_ok=True)
            
            return True, resolved_wd
            
        except Exception as e:
            return False, f"Working directory validation error: {e}"
    
    async def _execute_foreground(self, command: str, working_dir: str, timeout: int, capture_output: bool) -> Dict[str, Any]:
        """Execute command in foreground with output capture."""
        try:
            start_time = time.time()
            
            # Execute command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                text=True,
                cwd=working_dir,
                preexec_fn=os.setsid
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                end_time = time.time()
                
                result = {
                    "command": command,
                    "working_directory": working_dir,
                    "exit_code": process.returncode,
                    "execution_time": round(end_time - start_time, 2),
                    "success": process.returncode == 0,
                    "background": False
                }
                
                if capture_output:
                    result["stdout"] = stdout[:self.max_output_size] if stdout else ""
                    result["stderr"] = stderr[:self.max_output_size] if stderr else ""
                    result["output_truncated"] = len(stdout or "") > self.max_output_size or len(stderr or "") > self.max_output_size
                
                print(f"🚀 PROCESS_EXECUTOR: Foreground execution completed (exit_code={process.returncode})")
                
                return {"success": True, "error": None, "result": result}
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return {"success": False, "error": f"Command timed out after {timeout} seconds", "result": None}
                
        except Exception as e:
            return {"success": False, "error": f"Foreground execution error: {str(e)}", "result": None}
    
    async def _execute_background(self, command: str, working_dir: str, verify_execution: bool, timeout: int, capture_output: bool) -> Dict[str, Any]:
        """Execute command in background with process tracking."""
        try:
            start_time = time.time()
            
            # Execute command in background
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                text=True,
                cwd=working_dir,
                preexec_fn=os.setsid
            )
            
            process_id = process.pid
            
            # Store process info for tracking
            self.running_processes[process_id] = {
                "command": command,
                "working_dir": working_dir,
                "start_time": start_time,
                "process": process
            }
            
            # Give process a moment to start
            time.sleep(0.1)
            
            result = {
                "command": command,
                "working_directory": working_dir,
                "process_id": process_id,
                "background": True,
                "started_at": datetime.fromtimestamp(start_time).isoformat()
            }
            
            # 🚀 PHASE 1 ENHANCEMENT: Process execution verification
            if verify_execution:
                verification = self._verify_process_running(process_id)
                result["verification"] = verification
                
                if not verification["is_running"]:
                    return {"success": False, "error": "Process failed to start or exited immediately", "result": result}
            
            print(f"🚀 PROCESS_EXECUTOR: Background process started (PID={process_id})")
            
            return {"success": True, "error": None, "result": result}
            
        except Exception as e:
            return {"success": False, "error": f"Background execution error: {str(e)}", "result": None}
    
    def _verify_process_running(self, process_id: int) -> Dict[str, Any]:
        """Verify that a process is actually running."""
        try:
            if process_id in self.running_processes:
                process = self.running_processes[process_id]["process"]
                
                # Check if process is still running
                if process.poll() is None:
                    # Process is still running, get additional info
                    try:
                        ps_process = psutil.Process(process_id)
                        verification = {
                            "is_running": True,
                            "process_id": process_id,
                            "status": ps_process.status(),
                            "cpu_percent": ps_process.cpu_percent(),
                            "memory_info": ps_process.memory_info()._asdict(),
                            "verified_at": datetime.now().isoformat()
                        }
                    except psutil.NoSuchProcess:
                        verification = {
                            "is_running": False,
                            "process_id": process_id,
                            "error": "Process not found in system",
                            "verified_at": datetime.now().isoformat()
                        }
                else:
                    # Process has exited
                    exit_code = process.poll()
                    verification = {
                        "is_running": False,
                        "process_id": process_id,
                        "exit_code": exit_code,
                        "exited": True,
                        "verified_at": datetime.now().isoformat()
                    }
            else:
                verification = {
                    "is_running": False,
                    "process_id": process_id,
                    "error": "Process not tracked by executor",
                    "verified_at": datetime.now().isoformat()
                }
            
            return verification
            
        except Exception as e:
            return {
                "is_running": False,
                "process_id": process_id,
                "error": f"Verification error: {str(e)}",
                "verified_at": datetime.now().isoformat()
            }
    
    def get_running_processes(self) -> Dict[str, Any]:
        """Get list of currently tracked processes."""
        running = {}
        for pid, info in self.running_processes.items():
            verification = self._verify_process_running(pid)
            running[str(pid)] = {
                "command": info["command"],
                "working_dir": info["working_dir"],
                "start_time": info["start_time"],
                "verification": verification
            }
        return running
    
    def cleanup_finished_processes(self):
        """Clean up tracking for finished processes."""
        finished_pids = []
        for pid in self.running_processes:
            verification = self._verify_process_running(pid)
            if not verification["is_running"]:
                finished_pids.append(pid)
        
        for pid in finished_pids:
            del self.running_processes[pid]
        
        return len(finished_pids)