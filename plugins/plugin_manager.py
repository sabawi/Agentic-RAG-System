"""
Plugin Manager - Orchestration and lifecycle management
Coordinates PluginRegistry, PluginExecutor, and SecurityValidator.
Implements degraded mode, retry logic, and metrics tracking.

Author: Agentic-RAG System
Created: 2025-10-02
Version: 1.0.0
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta

from .plugin_registry import PluginRegistry, PluginDefinition
from .plugin_executor import PluginExecutor
from .security_validator import SecurityValidator

logger = logging.getLogger(__name__)


class PluginMetrics:
    """Track plugin execution metrics"""

    def __init__(self):
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.consecutive_failures = 0

    def record_success(self, execution_time: float):
        """Record successful execution"""
        self.execution_count += 1
        self.success_count += 1
        self.total_execution_time += execution_time
        self.last_execution_time = datetime.now()
        self.consecutive_failures = 0

    def record_failure(self, error: str):
        """Record failed execution"""
        self.execution_count += 1
        self.failure_count += 1
        self.last_execution_time = datetime.now()
        self.last_error = error
        self.consecutive_failures += 1

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100

    @property
    def average_execution_time(self) -> float:
        """Calculate average execution time"""
        if self.success_count == 0:
            return 0.0
        return self.total_execution_time / self.success_count

    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary"""
        return {
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_rate, 2),
            "average_execution_time": round(self.average_execution_time, 3),
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures
        }


class PluginManager:
    """
    Orchestrate plugin system components.
    Manages plugin lifecycle, security validation, execution, and degraded mode.
    """

    def __init__(self, plugins_dir: Path, config: Dict[str, Any]):
        """
        Initialize Plugin Manager.

        Args:
            plugins_dir: Path to /plugins/ directory
            config: Plugin configuration from llm_config.yaml
        """
        self.plugins_dir = Path(plugins_dir)
        self.config = config

        # Initialize components
        self.registry = PluginRegistry(plugins_dir, config)
        self.executor = PluginExecutor(config)
        self.validator = SecurityValidator(config)

        # Plugin state
        self.plugins: Dict[str, PluginDefinition] = {}
        self.disabled_plugins: Dict[str, str] = {}  # name -> reason
        self.metrics: Dict[str, PluginMetrics] = {}

        # Configuration
        self.degraded_mode_enabled = config.get('plugin_defaults', {}).get(
            'error_handling', {}
        ).get('degraded_mode', {}).get('enabled', True)

        self.disable_after_failures = config.get('plugin_defaults', {}).get(
            'error_handling', {}
        ).get('degraded_mode', {}).get('disable_after_failures', 5)

        self.retry_enabled = config.get('plugin_defaults', {}).get(
            'error_handling', {}
        ).get('retry', {}).get('enabled', True)

        self.max_retry_attempts = config.get('plugin_defaults', {}).get(
            'error_handling', {}
        ).get('retry', {}).get('max_attempts', 3)

        logger.info(f"PluginManager initialized (degraded_mode: {self.degraded_mode_enabled})")

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize plugin system: discover and validate plugins.

        Returns:
            {
                "success": bool,
                "plugins_loaded": int,
                "plugins_disabled": int,
                "errors": List[str]
            }
        """
        logger.info("Initializing plugin system...")
        start_time = time.time()
        errors = []

        try:
            # Discover plugins
            discovered_plugins = await self.registry.discover_plugins()
            logger.info(f"Discovered {len(discovered_plugins)} plugin definitions")

            # Validate and load plugins
            for plugin_def in discovered_plugins:
                try:
                    # Validate plugin definition
                    validation_result = self.validator.validate_plugin_definition(plugin_def)

                    if not validation_result['valid']:
                        error_msg = f"Plugin {plugin_def.name} validation failed: {validation_result['errors']}"
                        errors.append(error_msg)
                        self.disabled_plugins[plugin_def.name] = error_msg
                        logger.error(error_msg)
                        continue

                    if validation_result['warnings']:
                        logger.warning(f"Plugin {plugin_def.name} warnings: {validation_result['warnings']}")

                    # Load plugin
                    self.plugins[plugin_def.name] = plugin_def
                    self.metrics[plugin_def.name] = PluginMetrics()
                    logger.info(f"✅ Loaded plugin: {plugin_def.name} v{plugin_def.version}")

                except Exception as e:
                    error_msg = f"Failed to load plugin {plugin_def.name}: {str(e)}"
                    errors.append(error_msg)
                    self.disabled_plugins[plugin_def.name] = error_msg
                    logger.error(error_msg, exc_info=True)

            initialization_time = time.time() - start_time

            result = {
                "success": len(self.plugins) > 0,
                "plugins_loaded": len(self.plugins),
                "plugins_disabled": len(self.disabled_plugins),
                "errors": errors,
                "initialization_time": initialization_time
            }

            logger.info(
                f"Plugin system initialized in {initialization_time:.2f}s: "
                f"{len(self.plugins)} loaded, {len(self.disabled_plugins)} disabled"
            )

            return result

        except Exception as e:
            logger.error(f"Plugin system initialization failed: {e}", exc_info=True)
            return {
                "success": False,
                "plugins_loaded": 0,
                "plugins_disabled": 0,
                "errors": [str(e)],
                "initialization_time": time.time() - start_time
            }

    async def execute_plugin(
        self,
        plugin_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a plugin with full security validation and error handling.

        Args:
            plugin_name: Name of the plugin to execute
            parameters: Input parameters

        Returns:
            {
                "success": bool,
                "result": Any,
                "error": str | None,
                "execution_time": float,
                "metadata": Dict[str, Any]
            }
        """
        logger.info(f"Executing plugin: {plugin_name}")

        # Check if plugin exists
        if plugin_name not in self.plugins:
            if plugin_name in self.disabled_plugins:
                error_msg = f"Plugin '{plugin_name}' is disabled: {self.disabled_plugins[plugin_name]}"
                logger.warning(error_msg)
                return {
                    "success": False,
                    "result": None,
                    "error": error_msg,
                    "execution_time": 0.0,
                    "metadata": {"disabled": True}
                }
            else:
                error_msg = f"Plugin '{plugin_name}' not found"
                logger.error(error_msg)
                return {
                    "success": False,
                    "result": None,
                    "error": error_msg,
                    "execution_time": 0.0,
                    "metadata": {"not_found": True}
                }

        plugin_def = self.plugins[plugin_name]

        # Execute with retry logic
        attempt = 0
        max_attempts = self.max_retry_attempts if self.retry_enabled else 1
        last_error = None

        while attempt < max_attempts:
            attempt += 1

            try:
                logger.debug(f"Plugin {plugin_name} execution attempt {attempt}/{max_attempts}")

                # Validate inputs
                input_validation = self.validator.validate_inputs(plugin_def, parameters)
                if not input_validation['valid']:
                    error_msg = f"Input validation failed: {input_validation['errors']}"
                    logger.error(f"Plugin {plugin_name}: {error_msg}")
                    self.metrics[plugin_name].record_failure(error_msg)
                    return {
                        "success": False,
                        "result": None,
                        "error": error_msg,
                        "execution_time": 0.0,
                        "metadata": {"validation_errors": input_validation['errors']}
                    }

                # Execute plugin
                result = await self.executor.execute(
                    plugin_def,
                    input_validation['sanitized_params']
                )

                # Validate outputs
                output_validation = self.validator.validate_outputs(plugin_def, result)
                if not output_validation['valid']:
                    error_msg = f"Output validation failed: {output_validation['errors']}"
                    logger.error(f"Plugin {plugin_name}: {error_msg}")
                    result['error'] = error_msg
                    result['success'] = False

                # Add validation warnings to metadata
                if output_validation['warnings']:
                    if 'metadata' not in result:
                        result['metadata'] = {}
                    result['metadata']['validation_warnings'] = output_validation['warnings']

                # Record metrics
                if result.get('success', False):
                    self.metrics[plugin_name].record_success(result.get('execution_time', 0.0))
                    logger.info(
                        f"Plugin {plugin_name} executed successfully in "
                        f"{result.get('execution_time', 0.0):.2f}s"
                    )
                    return result
                else:
                    # Execution returned success=False
                    last_error = result.get('error', 'Unknown error')
                    self.metrics[plugin_name].record_failure(last_error)

                    # Check degraded mode
                    if self.degraded_mode_enabled:
                        if self.metrics[plugin_name].consecutive_failures >= self.disable_after_failures:
                            reason = (
                                f"Auto-disabled after {self.disable_after_failures} "
                                f"consecutive failures. Last error: {last_error}"
                            )
                            self._disable_plugin(plugin_name, reason)
                            logger.error(f"Plugin {plugin_name} disabled: {reason}")
                            result['metadata'] = result.get('metadata', {})
                            result['metadata']['auto_disabled'] = True

                    # Don't retry if plugin explicitly returned success=False
                    logger.warning(f"Plugin {plugin_name} execution failed: {last_error}")
                    return result

            except asyncio.TimeoutError:
                last_error = f"Plugin execution timed out after {plugin_def.timeout}s"
                logger.error(f"Plugin {plugin_name}: {last_error}")
                self.metrics[plugin_name].record_failure(last_error)

                if attempt < max_attempts:
                    logger.info(f"Retrying plugin {plugin_name} (attempt {attempt + 1}/{max_attempts})")
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Plugin {plugin_name}: {last_error}", exc_info=True)
                self.metrics[plugin_name].record_failure(last_error)

                if attempt < max_attempts:
                    logger.info(f"Retrying plugin {plugin_name} (attempt {attempt + 1}/{max_attempts})")
                    await asyncio.sleep(1)
                    continue

        # All retries exhausted
        logger.error(f"Plugin {plugin_name} failed after {max_attempts} attempts")

        # Check degraded mode
        if self.degraded_mode_enabled:
            if self.metrics[plugin_name].consecutive_failures >= self.disable_after_failures:
                reason = (
                    f"Auto-disabled after {self.disable_after_failures} "
                    f"consecutive failures. Last error: {last_error}"
                )
                self._disable_plugin(plugin_name, reason)

        return {
            "success": False,
            "result": None,
            "error": f"Failed after {max_attempts} attempts: {last_error}",
            "execution_time": 0.0,
            "metadata": {
                "attempts": max_attempts,
                "last_error": last_error
            }
        }

    def _disable_plugin(self, plugin_name: str, reason: str):
        """Disable a plugin (move to disabled state)"""
        if plugin_name in self.plugins:
            self.disabled_plugins[plugin_name] = reason
            del self.plugins[plugin_name]
            logger.warning(f"Plugin {plugin_name} disabled: {reason}")

    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """
        Get list of available (enabled) plugins.

        Returns:
            List of plugin metadata dictionaries
        """
        plugins_list = []

        for name, plugin_def in self.plugins.items():
            plugins_list.append({
                "name": plugin_def.name,
                "version": plugin_def.version,
                "category": plugin_def.category,
                "description": plugin_def.description,
                "author": plugin_def.author,
                "parameters": plugin_def.parameters,
                "tags": plugin_def.tags,
                "metrics": self.metrics[name].to_dict() if name in self.metrics else {}
            })

        return plugins_list

    def get_plugin_metrics(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a specific plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Metrics dictionary or None if plugin not found
        """
        if plugin_name in self.metrics:
            return self.metrics[plugin_name].to_dict()
        return None

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all plugins.

        Returns:
            Dict mapping plugin names to metrics
        """
        return {
            name: metrics.to_dict()
            for name, metrics in self.metrics.items()
        }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall plugin system status.

        Returns:
            System status dictionary
        """
        total_executions = sum(m.execution_count for m in self.metrics.values())
        total_successes = sum(m.success_count for m in self.metrics.values())
        total_failures = sum(m.failure_count for m in self.metrics.values())

        return {
            "plugins_loaded": len(self.plugins),
            "plugins_disabled": len(self.disabled_plugins),
            "total_executions": total_executions,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "success_rate": round((total_successes / total_executions * 100) if total_executions > 0 else 0.0, 2),
            "degraded_mode_enabled": self.degraded_mode_enabled,
            "retry_enabled": self.retry_enabled,
            "disabled_plugins": self.disabled_plugins
        }

    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Re-enable a disabled plugin.

        Args:
            plugin_name: Name of the plugin to enable

        Returns:
            True if plugin was re-enabled, False otherwise
        """
        if plugin_name in self.disabled_plugins:
            # Find plugin definition from original discovery
            # For now, we would need to re-run discovery
            # This is a placeholder for future enhancement
            logger.warning(f"Plugin {plugin_name} re-enable requested, but requires re-initialization")
            return False
        return False

    def get_plugin_definition(self, plugin_name: str) -> Optional[PluginDefinition]:
        """
        Get plugin definition by name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            PluginDefinition or None if not found
        """
        return self.plugins.get(plugin_name)

    async def reload_plugins(self) -> Dict[str, Any]:
        """
        Reload all plugins (re-run discovery and validation).

        Returns:
            Initialization result
        """
        logger.info("Reloading plugin system...")

        # Clear current state
        self.plugins.clear()
        self.disabled_plugins.clear()
        # Keep metrics for historical tracking

        # Re-initialize
        return await self.initialize()
