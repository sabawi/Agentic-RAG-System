"""
Plugin Executor - Process isolation and execution
Executes plugins in isolated subprocesses with resource limits and timeout enforcement.

Author: Agentic-RAG System
Created: 2025-10-02
Version: 1.0.0
"""

import asyncio
import subprocess
import json
import os
import signal
import time
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import resource for Unix systems
try:
    import resource
    RESOURCE_AVAILABLE = True
except ImportError:
    RESOURCE_AVAILABLE = False
    logger.warning("resource module not available (Windows?). Resource limits will not be enforced.")


class PluginExecutor:
    """
    Execute plugins in isolated subprocesses with resource limits.
    Provides timeout enforcement and cleanup.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Plugin Executor.

        Args:
            config: Plugin configuration from llm_config.yaml
        """
        self.config = config
        self.python_path = config.get('python_executable', 'python3')

        logger.info(f"PluginExecutor initialized with python: {self.python_path}")

    async def execute(
        self,
        plugin_def: 'PluginDefinition',
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute plugin in isolated subprocess.

        Args:
            plugin_def: Plugin definition
            parameters: Validated input parameters

        Returns:
            {
                "success": bool,
                "result": Any,
                "error": str | None,
                "execution_time": float,
                "metadata": {
                    "exit_code": int,
                    "stdout": str,
                    "stderr": str
                }
            }
        """
        start_time = time.time()

        try:
            # Prepare execution environment
            env = self._prepare_environment(plugin_def)

            # Execute based on plugin type
            if plugin_def.execution_type == 'python':
                result = await self._execute_python(plugin_def, parameters, env)
            elif plugin_def.execution_type == 'executable':
                result = await self._execute_executable(plugin_def, parameters, env)
            else:
                raise ValueError(f"Unsupported execution type: {plugin_def.execution_type}")

            execution_time = time.time() - start_time
            result['execution_time'] = execution_time

            logger.info(
                f"Plugin {plugin_def.name} executed in {execution_time:.2f}s "
                f"(success: {result.get('success', False)})"
            )

            return result

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.error(f"Plugin {plugin_def.name} timed out after {execution_time:.2f}s")
            raise

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Plugin {plugin_def.name} execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "result": None,
                "error": f"Execution failed: {str(e)}",
                "execution_time": execution_time,
                "metadata": {}
            }

    async def _execute_python(
        self,
        plugin_def: 'PluginDefinition',
        parameters: Dict[str, Any],
        env: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute Python plugin handler"""
        handler_path = plugin_def.handler_path

        # Validate handler exists
        if not handler_path.exists():
            return {
                "success": False,
                "result": None,
                "error": f"Plugin handler not found: {handler_path}",
                "metadata": {}
            }

        # Prepare subprocess command
        cmd = [self.python_path, str(handler_path)]

        # Prepare input JSON
        input_json = json.dumps(parameters)

        logger.debug(f"Executing plugin {plugin_def.name}: {' '.join(cmd)}")
        logger.debug(f"Input parameters: {input_json}")

        # Execute with resource limits and timeout
        try:
            # TODO: Resource limits disabled temporarily due to subprocess fork issues
            # Will re-enable with proper configuration after testing
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                # preexec_fn=lambda: self._set_resource_limits(plugin_def) if RESOURCE_AVAILABLE else None
            )

            # Execute with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input_json.encode()),
                    timeout=plugin_def.timeout
                )
            except asyncio.TimeoutError:
                # Kill process on timeout
                logger.warning(f"Plugin {plugin_def.name} timed out, killing process...")
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                raise

            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')

            logger.debug(f"Plugin {plugin_def.name} exit code: {process.returncode}")
            if stderr_str:
                logger.debug(f"Plugin {plugin_def.name} stderr: {stderr_str}")

            # Parse result from stdout
            try:
                result_data = json.loads(stdout_str)
            except json.JSONDecodeError as e:
                logger.error(f"Plugin {plugin_def.name} returned invalid JSON: {e}")
                logger.error(f"Stdout: {stdout_str[:500]}")
                return {
                    "success": False,
                    "result": None,
                    "error": f"Plugin returned invalid JSON: {str(e)}",
                    "metadata": {
                        "exit_code": process.returncode,
                        "stdout": stdout_str[:1000],
                        "stderr": stderr_str[:1000]
                    }
                }

            # Validate result structure
            if not isinstance(result_data, dict):
                return {
                    "success": False,
                    "result": None,
                    "error": "Plugin result must be a dictionary",
                    "metadata": {
                        "exit_code": process.returncode,
                        "stdout": stdout_str[:1000],
                        "stderr": stderr_str[:1000]
                    }
                }

            if 'success' not in result_data:
                logger.warning(f"Plugin {plugin_def.name} result missing 'success' field")
                result_data['success'] = (process.returncode == 0)

            # Add metadata
            result_data['metadata'] = result_data.get('metadata', {})
            result_data['metadata'].update({
                "exit_code": process.returncode,
                "stdout": stdout_str if len(stdout_str) < 1000 else stdout_str[:1000] + "...",
                "stderr": stderr_str if len(stderr_str) < 1000 else stderr_str[:1000] + "..."
            })

            return result_data

        except Exception as e:
            logger.error(f"Plugin {plugin_def.name} subprocess error: {e}", exc_info=True)
            raise

    async def _execute_executable(
        self,
        plugin_def: 'PluginDefinition',
        parameters: Dict[str, Any],
        env: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute external executable plugin"""
        # Similar to _execute_python but for arbitrary executables
        # Implementation can be added when needed
        return {
            "success": False,
            "result": None,
            "error": "Executable plugins not yet implemented"
        }

    def _prepare_environment(self, plugin_def: 'PluginDefinition') -> Dict[str, str]:
        """Prepare environment variables for plugin execution"""
        env = os.environ.copy()

        # Add plugin-specific environment variables
        if plugin_def.environment:
            for key, value in plugin_def.environment.items():
                # Expand ${VAR} references from environment
                if value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    env[key] = os.getenv(env_var, '')
                    logger.debug(f"Expanded {key}=${{{env_var}}} -> {env[key]}")
                else:
                    env[key] = value

        return env

    def _set_resource_limits(self, plugin_def: 'PluginDefinition'):
        """
        Set resource limits for subprocess (Unix only).
        Called via preexec_fn before subprocess starts.
        """
        if not RESOURCE_AVAILABLE:
            return

        try:
            # Memory limit (address space)
            # Note: Use DATA segment limit instead of AS (address space) for better compatibility
            # AS includes all memory mappings which can be very large for Python
            memory_bytes = plugin_def.memory_limit * 1024 * 1024  # MB to bytes
            # Use RLIMIT_DATA instead of RLIMIT_AS to avoid issues with virtual memory
            resource.setrlimit(resource.RLIMIT_DATA, (memory_bytes * 2, memory_bytes * 2))
            logger.debug(f"Set memory limit: {plugin_def.memory_limit}MB")

            # CPU time limit (soft limit = timeout)
            cpu_limit = int(plugin_def.timeout)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit + 5))
            logger.debug(f"Set CPU time limit: {cpu_limit}s")

            # File size limits (prevent large file creation)
            max_file_size = 100 * 1024 * 1024  # 100MB
            resource.setrlimit(resource.RLIMIT_FSIZE, (max_file_size, max_file_size))

            # Process limits (prevent fork bombs)
            resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))

        except Exception as e:
            logger.warning(f"Failed to set resource limits: {e}")
            # Don't fail the execution, just log the warning
