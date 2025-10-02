"""
Security Validator - Input/output validation and security policy enforcement
Validates plugin inputs/outputs, detects injection attacks, enforces security policies.

Author: Agentic-RAG System
Created: 2025-10-02
Version: 1.0.0
"""

import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class SecurityValidator:
    """
    Validate plugin inputs, outputs, and enforce security policies.
    Provides injection detection, sensitive data scanning, and resource validation.
    """

    # Injection patterns for common attacks
    INJECTION_PATTERNS = {
        'sql_injection': [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(;.*--)",
            r"('.*OR.*'.*=.*')",
        ],
        'command_injection': [
            r"(;\s*rm\s+-rf)",
            r"(&&\s*cat\s+/etc/passwd)",
            r"(\|\s*bash)",
            r"(`.*`)",
            r"(\$\(.*\))",
        ],
        'xss': [
            r"(<script[^>]*>.*</script>)",
            r"(javascript:)",
            r"(onerror\s*=)",
            r"(onload\s*=)",
        ],
        'path_traversal': [
            r"(\.\./)",
            r"(\.\.\\)",
            r"(%2e%2e)",
        ],
    }

    # Sensitive data patterns
    SENSITIVE_PATTERNS = {
        'ssn': [r'\b\d{3}-\d{2}-\d{4}\b'],
        'credit_card': [r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'],
        'api_key': [r'\b[A-Za-z0-9]{32,}\b'],
        'private_key': [r'-----BEGIN (RSA |EC |)PRIVATE KEY-----'],
        'aws_key': [r'AKIA[0-9A-Z]{16}'],
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Security Validator.

        Args:
            config: Plugin configuration from llm_config.yaml
        """
        self.config = config
        self.defaults = config.get('plugin_defaults', {})

        # Compile regex patterns for performance
        self._compiled_injection_patterns = self._compile_patterns(self.INJECTION_PATTERNS)
        self._compiled_sensitive_patterns = self._compile_patterns(self.SENSITIVE_PATTERNS)

        logger.info("SecurityValidator initialized")

    def _compile_patterns(self, pattern_dict: Dict[str, List[str]]) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficiency"""
        compiled = {}
        for category, patterns in pattern_dict.items():
            compiled[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled

    def validate_plugin_definition(self, plugin_def: 'PluginDefinition') -> Dict[str, Any]:
        """
        Validate plugin definition against security requirements.

        Args:
            plugin_def: Plugin definition to validate

        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        errors = []
        warnings = []

        # Check timeout limits
        max_timeout = self.defaults.get('execution', {}).get('max_timeout', 300)
        if plugin_def.timeout > max_timeout:
            errors.append(f"Timeout {plugin_def.timeout}s exceeds maximum {max_timeout}s")

        # Check memory limits
        max_memory = self.defaults.get('execution', {}).get('max_memory_limit', 2048)
        if plugin_def.memory_limit > max_memory:
            errors.append(f"Memory limit {plugin_def.memory_limit}MB exceeds maximum {max_memory}MB")

        # Validate handler path exists
        if not plugin_def.handler_path.exists():
            errors.append(f"Plugin handler not found: {plugin_def.handler_path}")

        # Check security configuration
        security = plugin_def.security

        # Network security
        if security.get('network', {}).get('enabled', False):
            if not security.get('network', {}).get('allowed_domains'):
                warnings.append("Network enabled but no allowed_domains specified")

        # Filesystem security
        if not security.get('filesystem', {}).get('read_only', True):
            warnings.append("Filesystem is not read-only - write access may pose security risk")

        # Validate allowed paths if specified
        allowed_paths = security.get('filesystem', {}).get('allowed_paths', [])
        for path_str in allowed_paths:
            path = Path(path_str)
            if not path.exists():
                warnings.append(f"Allowed path does not exist: {path_str}")

        logger.debug(
            f"Plugin definition validation for {plugin_def.name}: "
            f"{len(errors)} errors, {len(warnings)} warnings"
        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def validate_inputs(
        self,
        plugin_def: 'PluginDefinition',
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate plugin input parameters against JSON schema and security rules.

        Args:
            plugin_def: Plugin definition with parameter schema
            parameters: Input parameters to validate

        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "sanitized_params": Dict[str, Any]
            }
        """
        errors = []
        sanitized_params = parameters.copy()

        # JSON Schema validation
        try:
            validate(instance=parameters, schema=plugin_def.parameters)
        except ValidationError as e:
            errors.append(f"Schema validation failed: {e.message}")
            logger.warning(f"Plugin {plugin_def.name} input validation error: {e.message}")

        # Check for injection patterns in string values
        injection_results = self._check_injection_patterns(parameters)
        if injection_results:
            for attack_type, matches in injection_results.items():
                errors.append(f"Potential {attack_type} detected: {matches}")
                logger.warning(f"Plugin {plugin_def.name} - Injection attack detected: {attack_type}")

        # Validate string lengths
        max_string_length = self.defaults.get('security', {}).get('input_validation', {}).get('max_string_length', 10240)
        for key, value in parameters.items():
            if isinstance(value, str) and len(value) > max_string_length:
                errors.append(f"Parameter '{key}' exceeds max length {max_string_length}")

        # Validate array sizes
        max_array_length = self.defaults.get('security', {}).get('input_validation', {}).get('max_array_length', 1000)
        for key, value in parameters.items():
            if isinstance(value, list) and len(value) > max_array_length:
                errors.append(f"Parameter '{key}' array exceeds max length {max_array_length}")

        logger.debug(
            f"Input validation for {plugin_def.name}: "
            f"{len(errors)} errors, {len(parameters)} parameters"
        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "sanitized_params": sanitized_params
        }

    def validate_outputs(
        self,
        plugin_def: 'PluginDefinition',
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate plugin output for security issues.

        Args:
            plugin_def: Plugin definition
            result: Plugin execution result

        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "sanitized_result": Dict[str, Any]
            }
        """
        errors = []
        warnings = []
        sanitized_result = result.copy()

        # Validate result structure
        if not isinstance(result, dict):
            errors.append("Result must be a dictionary")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings,
                "sanitized_result": {}
            }

        if 'success' not in result:
            warnings.append("Result missing 'success' field")

        # Check output size limits
        max_output_size = self.defaults.get('security', {}).get('output_validation', {}).get('max_output_size', 10485760)  # 10MB

        result_str = str(result)
        if len(result_str) > max_output_size:
            errors.append(f"Output size {len(result_str)} exceeds maximum {max_output_size}")

        # Check for sensitive data in outputs
        sensitive_results = self._check_sensitive_data(result)
        if sensitive_results:
            for data_type, matches in sensitive_results.items():
                warnings.append(f"Potential {data_type} detected in output: {len(matches)} matches")
                logger.warning(
                    f"Plugin {plugin_def.name} - Sensitive data detected: "
                    f"{data_type} ({len(matches)} matches)"
                )

        # Validate execution time if present
        if 'execution_time' in result:
            exec_time = result['execution_time']
            if exec_time > plugin_def.timeout:
                warnings.append(f"Execution time {exec_time:.2f}s exceeded timeout {plugin_def.timeout}s")

        logger.debug(
            f"Output validation for {plugin_def.name}: "
            f"{len(errors)} errors, {len(warnings)} warnings"
        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized_result": sanitized_result
        }

    def _check_injection_patterns(self, data: Any, path: str = "") -> Dict[str, List[str]]:
        """
        Recursively check for injection patterns in data structure.

        Args:
            data: Data to check (can be dict, list, str, etc.)
            path: Current path in data structure (for error reporting)

        Returns:
            Dict mapping attack types to list of matched patterns
        """
        matches = {}

        if isinstance(data, str):
            # Check string against all injection patterns
            for attack_type, patterns in self._compiled_injection_patterns.items():
                for pattern in patterns:
                    if pattern.search(data):
                        if attack_type not in matches:
                            matches[attack_type] = []
                        matches[attack_type].append(f"{path}: {pattern.pattern}")

        elif isinstance(data, dict):
            # Recursively check dictionary values
            for key, value in data.items():
                sub_path = f"{path}.{key}" if path else key
                sub_matches = self._check_injection_patterns(value, sub_path)
                for attack_type, patterns in sub_matches.items():
                    if attack_type not in matches:
                        matches[attack_type] = []
                    matches[attack_type].extend(patterns)

        elif isinstance(data, list):
            # Recursively check list items
            for i, item in enumerate(data):
                sub_path = f"{path}[{i}]"
                sub_matches = self._check_injection_patterns(item, sub_path)
                for attack_type, patterns in sub_matches.items():
                    if attack_type not in matches:
                        matches[attack_type] = []
                    matches[attack_type].extend(patterns)

        return matches

    def _check_sensitive_data(self, data: Any, path: str = "") -> Dict[str, List[str]]:
        """
        Recursively check for sensitive data patterns in output.

        Args:
            data: Data to check
            path: Current path in data structure

        Returns:
            Dict mapping sensitive data types to list of matches
        """
        matches = {}

        if isinstance(data, str):
            # Check string against all sensitive data patterns
            for data_type, patterns in self._compiled_sensitive_patterns.items():
                for pattern in patterns:
                    found = pattern.findall(data)
                    if found:
                        if data_type not in matches:
                            matches[data_type] = []
                        matches[data_type].extend([f"{path}: {match}" for match in found])

        elif isinstance(data, dict):
            # Recursively check dictionary values
            for key, value in data.items():
                sub_path = f"{path}.{key}" if path else key
                sub_matches = self._check_sensitive_data(value, sub_path)
                for data_type, patterns in sub_matches.items():
                    if data_type not in matches:
                        matches[data_type] = []
                    matches[data_type].extend(patterns)

        elif isinstance(data, list):
            # Recursively check list items
            for i, item in enumerate(data):
                sub_path = f"{path}[{i}]"
                sub_matches = self._check_sensitive_data(item, sub_path)
                for data_type, patterns in sub_matches.items():
                    if data_type not in matches:
                        matches[data_type] = []
                    matches[data_type].extend(patterns)

        return matches

    def check_filesystem_access(
        self,
        plugin_def: 'PluginDefinition',
        requested_path: str
    ) -> Dict[str, Any]:
        """
        Check if plugin is allowed to access a filesystem path.

        Args:
            plugin_def: Plugin definition with filesystem security config
            requested_path: Path the plugin wants to access

        Returns:
            {
                "allowed": bool,
                "reason": str | None
            }
        """
        filesystem_config = plugin_def.security.get('filesystem', {})

        # Check if filesystem access is completely blocked
        if not filesystem_config.get('enabled', True):
            return {
                "allowed": False,
                "reason": "Filesystem access disabled for this plugin"
            }

        requested = Path(requested_path).resolve()

        # Check blocked paths first (blacklist)
        blocked_paths = filesystem_config.get('blocked_paths', [])
        for blocked_str in blocked_paths:
            blocked = Path(blocked_str).resolve()
            try:
                requested.relative_to(blocked)
                # If we get here, requested_path is under blocked path
                return {
                    "allowed": False,
                    "reason": f"Path is under blocked directory: {blocked}"
                }
            except ValueError:
                # Not under this blocked path, continue checking
                pass

        # Check allowed paths (whitelist)
        allowed_paths = filesystem_config.get('allowed_paths', [])
        if allowed_paths:
            for allowed_str in allowed_paths:
                allowed = Path(allowed_str).resolve()
                try:
                    requested.relative_to(allowed)
                    # Path is under allowed directory
                    return {"allowed": True, "reason": None}
                except ValueError:
                    # Not under this allowed path, continue checking
                    pass

            # Path not in any allowed directory
            return {
                "allowed": False,
                "reason": f"Path not in allowed directories: {allowed_paths}"
            }

        # No restrictions configured
        return {"allowed": True, "reason": None}

    def check_network_access(
        self,
        plugin_def: 'PluginDefinition',
        domain: str,
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if plugin is allowed to access a network domain/port.

        Args:
            plugin_def: Plugin definition with network security config
            domain: Domain to access
            port: Port number (optional)

        Returns:
            {
                "allowed": bool,
                "reason": str | None
            }
        """
        network_config = plugin_def.security.get('network', {})

        # Check if network access is enabled
        if not network_config.get('enabled', False):
            return {
                "allowed": False,
                "reason": "Network access disabled for this plugin"
            }

        # Check allowed domains
        allowed_domains = network_config.get('allowed_domains', [])
        if allowed_domains and domain not in allowed_domains:
            return {
                "allowed": False,
                "reason": f"Domain not in allowed list: {allowed_domains}"
            }

        # Check allowed ports
        if port is not None:
            allowed_ports = network_config.get('allowed_ports', [])
            if allowed_ports and port not in allowed_ports:
                return {
                    "allowed": False,
                    "reason": f"Port {port} not in allowed list: {allowed_ports}"
                }

        return {"allowed": True, "reason": None}
