#!/usr/bin/env python3
"""
Test SecurityValidator component
Tests input/output validation, injection detection, and security policy enforcement.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins.security_validator import SecurityValidator
from plugins.plugin_registry import PluginDefinition


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


async def test_injection_detection():
    """Test injection attack detection"""
    print_section("Testing Injection Detection")

    config = {
        'plugin_defaults': {
            'security': {
                'input_validation': {
                    'max_string_length': 10240,
                    'max_array_length': 1000
                }
            }
        }
    }

    validator = SecurityValidator(config)

    # Create a dummy plugin definition
    plugin_def = PluginDefinition(
        name="test_plugin",
        version="1.0.0",
        category="test",
        author="Test",
        description="Test plugin",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            }
        }
    )

    # Test SQL injection
    print("\n1. SQL Injection Test:")
    sql_params = {
        "query": "SELECT * FROM users WHERE id=1 UNION SELECT password FROM admin"
    }
    result = validator.validate_inputs(plugin_def, sql_params)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")

    # Test command injection
    print("\n2. Command Injection Test:")
    cmd_params = {
        "query": "test; rm -rf /"
    }
    result = validator.validate_inputs(plugin_def, cmd_params)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")

    # Test XSS
    print("\n3. XSS Test:")
    xss_params = {
        "query": "<script>alert('XSS')</script>"
    }
    result = validator.validate_inputs(plugin_def, xss_params)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")

    # Test clean input
    print("\n4. Clean Input Test:")
    clean_params = {
        "query": "Show me the weather forecast"
    }
    result = validator.validate_inputs(plugin_def, clean_params)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")


async def test_sensitive_data_detection():
    """Test sensitive data detection in outputs"""
    print_section("Testing Sensitive Data Detection")

    config = {
        'plugin_defaults': {
            'security': {
                'output_validation': {
                    'max_output_size': 10485760
                }
            }
        }
    }

    validator = SecurityValidator(config)

    plugin_def = PluginDefinition(
        name="test_plugin",
        version="1.0.0",
        category="test",
        author="Test",
        description="Test plugin",
        timeout=30
    )

    # Test SSN detection
    print("\n1. SSN Detection Test:")
    result_with_ssn = {
        "success": True,
        "result": "User SSN: 123-45-6789"
    }
    validation = validator.validate_outputs(plugin_def, result_with_ssn)
    print(f"   Valid: {validation['valid']}")
    print(f"   Warnings: {validation['warnings']}")

    # Test credit card detection
    print("\n2. Credit Card Detection Test:")
    result_with_cc = {
        "success": True,
        "result": "Card: 4532-1234-5678-9010"
    }
    validation = validator.validate_outputs(plugin_def, result_with_cc)
    print(f"   Valid: {validation['valid']}")
    print(f"   Warnings: {validation['warnings']}")

    # Test clean output
    print("\n3. Clean Output Test:")
    clean_result = {
        "success": True,
        "result": "Weather forecast: Sunny, 72°F"
    }
    validation = validator.validate_outputs(plugin_def, clean_result)
    print(f"   Valid: {validation['valid']}")
    print(f"   Warnings: {validation['warnings']}")


async def test_filesystem_access():
    """Test filesystem access control"""
    print_section("Testing Filesystem Access Control")

    config = {'plugin_defaults': {}}
    validator = SecurityValidator(config)

    # Test with allowed paths
    plugin_def = PluginDefinition(
        name="test_plugin",
        version="1.0.0",
        category="test",
        author="Test",
        description="Test plugin",
        security={
            'filesystem': {
                'enabled': True,
                'read_only': True,
                'allowed_paths': ['/usr/games', '/tmp'],
                'blocked_paths': ['/etc', '/root']
            }
        }
    )

    print("\n1. Allowed Path Test (/usr/games/fortune):")
    result = validator.check_filesystem_access(plugin_def, "/usr/games/fortune")
    print(f"   Allowed: {result['allowed']}")
    print(f"   Reason: {result['reason']}")

    print("\n2. Blocked Path Test (/etc/passwd):")
    result = validator.check_filesystem_access(plugin_def, "/etc/passwd")
    print(f"   Allowed: {result['allowed']}")
    print(f"   Reason: {result['reason']}")

    print("\n3. Unlisted Path Test (/home/user/file):")
    result = validator.check_filesystem_access(plugin_def, "/home/user/file")
    print(f"   Allowed: {result['allowed']}")
    print(f"   Reason: {result['reason']}")


async def test_network_access():
    """Test network access control"""
    print_section("Testing Network Access Control")

    config = {'plugin_defaults': {}}
    validator = SecurityValidator(config)

    # Test with network enabled
    plugin_def = PluginDefinition(
        name="test_plugin",
        version="1.0.0",
        category="test",
        author="Test",
        description="Test plugin",
        security={
            'network': {
                'enabled': True,
                'allowed_domains': ['api.example.com', 'api.github.com'],
                'allowed_ports': [443, 80]
            }
        }
    )

    print("\n1. Allowed Domain Test (api.example.com:443):")
    result = validator.check_network_access(plugin_def, "api.example.com", 443)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Reason: {result['reason']}")

    print("\n2. Blocked Domain Test (evil.com:443):")
    result = validator.check_network_access(plugin_def, "evil.com", 443)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Reason: {result['reason']}")

    print("\n3. Blocked Port Test (api.example.com:22):")
    result = validator.check_network_access(plugin_def, "api.example.com", 22)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Reason: {result['reason']}")

    # Test with network disabled
    plugin_def_no_network = PluginDefinition(
        name="test_plugin",
        version="1.0.0",
        category="test",
        author="Test",
        description="Test plugin",
        security={
            'network': {
                'enabled': False
            }
        }
    )

    print("\n4. Network Disabled Test (api.example.com:443):")
    result = validator.check_network_access(plugin_def_no_network, "api.example.com", 443)
    print(f"   Allowed: {result['allowed']}")
    print(f"   Reason: {result['reason']}")


async def test_plugin_definition_validation():
    """Test plugin definition validation"""
    print_section("Testing Plugin Definition Validation")

    config = {
        'plugin_defaults': {
            'execution': {
                'max_timeout': 300,
                'max_memory_limit': 2048
            }
        }
    }

    validator = SecurityValidator(config)

    # Test valid plugin
    print("\n1. Valid Plugin Definition:")
    valid_plugin = PluginDefinition(
        name="fortune_message",
        version="1.0.0",
        category="productivity",
        author="Test",
        description="Test plugin",
        handler="handlers/fortune_message.py",
        timeout=30,
        memory_limit=128,
        security={
            'network': {'enabled': False},
            'filesystem': {'read_only': True}
        },
        _yaml_path=Path("/home/sabawi/Development/flaskserver/plugins/fortune_message.yaml")
    )
    result = validator.validate_plugin_definition(valid_plugin)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")
    print(f"   Warnings: {result['warnings']}")

    # Test excessive timeout
    print("\n2. Excessive Timeout Test:")
    timeout_plugin = PluginDefinition(
        name="slow_plugin",
        version="1.0.0",
        category="test",
        author="Test",
        description="Test plugin",
        handler="handlers/test.py",
        timeout=999,  # Exceeds max_timeout
        memory_limit=128,
        _yaml_path=Path("/home/sabawi/Development/flaskserver/plugins/test.yaml")
    )
    result = validator.validate_plugin_definition(timeout_plugin)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")
    print(f"   Warnings: {result['warnings']}")

    # Test excessive memory
    print("\n3. Excessive Memory Test:")
    memory_plugin = PluginDefinition(
        name="memory_plugin",
        version="1.0.0",
        category="test",
        author="Test",
        description="Test plugin",
        handler="handlers/test.py",
        timeout=30,
        memory_limit=9999,  # Exceeds max_memory_limit
        _yaml_path=Path("/home/sabawi/Development/flaskserver/plugins/test.yaml")
    )
    result = validator.validate_plugin_definition(memory_plugin)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")
    print(f"   Warnings: {result['warnings']}")


async def test_fortune_plugin_validation():
    """Test validation with actual fortune plugin"""
    print_section("Testing Fortune Plugin Validation")

    config = {
        'plugin_defaults': {
            'execution': {
                'max_timeout': 300,
                'max_memory_limit': 2048
            },
            'security': {
                'input_validation': {
                    'max_string_length': 10240,
                    'max_array_length': 1000
                },
                'output_validation': {
                    'max_output_size': 10485760
                }
            }
        }
    }

    validator = SecurityValidator(config)

    # Load fortune plugin definition
    fortune_plugin = PluginDefinition(
        name="fortune_message",
        version="1.0.0",
        category="productivity",
        author="Agentic-RAG System",
        description="Generate random messages",
        handler="handlers/fortune_message.py",
        timeout=10,
        memory_limit=128,
        parameters={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["any", "short", "long", "offensive"]
                },
                "format_style": {
                    "type": "string",
                    "enum": ["plain", "boxed", "quoted"]
                }
            }
        },
        security={
            'network': {'enabled': False},
            'filesystem': {
                'read_only': True,
                'allowed_paths': ['/usr/games', '/usr/share/games/fortunes'],
                'blocked_paths': ['/etc', '/root', '/home']
            }
        },
        _yaml_path=Path("/home/sabawi/Development/flaskserver/plugins/fortune_message.yaml")
    )

    print("\n1. Fortune Plugin Definition Validation:")
    result = validator.validate_plugin_definition(fortune_plugin)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")
    print(f"   Warnings: {result['warnings']}")

    print("\n2. Valid Fortune Input Validation:")
    valid_params = {
        "category": "any",
        "format_style": "boxed"
    }
    result = validator.validate_inputs(fortune_plugin, valid_params)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")

    print("\n3. Invalid Fortune Input Validation (bad enum):")
    invalid_params = {
        "category": "invalid_category",
        "format_style": "boxed"
    }
    result = validator.validate_inputs(fortune_plugin, invalid_params)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")

    print("\n4. Fortune Output Validation:")
    sample_output = {
        "success": True,
        "result": "╔════════════════════════════════════════════════════════╗\n║ Fortune favors the bold.                              ║\n╚════════════════════════════════════════════════════════╝",
        "error": None,
        "metadata": {
            "category": "any",
            "format_style": "boxed",
            "message_length": 25
        },
        "execution_time": 0.08
    }
    result = validator.validate_outputs(fortune_plugin, sample_output)
    print(f"   Valid: {result['valid']}")
    print(f"   Errors: {result['errors']}")
    print(f"   Warnings: {result['warnings']}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  SecurityValidator Component Tests")
    print("="*60)

    await test_injection_detection()
    await test_sensitive_data_detection()
    await test_filesystem_access()
    await test_network_access()
    await test_plugin_definition_validation()
    await test_fortune_plugin_validation()

    print("\n" + "="*60)
    print("  All Tests Completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
