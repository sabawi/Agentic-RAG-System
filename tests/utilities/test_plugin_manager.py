#!/usr/bin/env python3
"""
Test PluginManager component
Tests orchestration, degraded mode, retry logic, and metrics tracking.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins.plugin_manager import PluginManager


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


async def test_initialization():
    """Test plugin system initialization"""
    print_section("Testing Plugin System Initialization")

    plugins_dir = project_root / 'plugins'
    config = {
        'plugin_defaults': {
            'execution': {
                'timeout': 60,
                'memory_limit': 256,
                'cpu_limit': 1.0,
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
            },
            'error_handling': {
                'retry': {
                    'enabled': True,
                    'max_attempts': 3
                },
                'degraded_mode': {
                    'enabled': True,
                    'disable_after_failures': 5
                }
            }
        },
        'python_executable': 'python3'
    }

    manager = PluginManager(plugins_dir, config)

    print("\n1. Initializing plugin system...")
    result = await manager.initialize()

    print(f"\n   Success: {result['success']}")
    print(f"   Plugins loaded: {result['plugins_loaded']}")
    print(f"   Plugins disabled: {result['plugins_disabled']}")
    print(f"   Initialization time: {result['initialization_time']:.3f}s")
    if result['errors']:
        print(f"   Errors: {result['errors']}")

    return manager


async def test_plugin_discovery(manager):
    """Test plugin discovery and listing"""
    print_section("Testing Plugin Discovery")

    plugins = manager.get_available_plugins()

    print(f"\n   Found {len(plugins)} available plugins:\n")

    for i, plugin in enumerate(plugins, 1):
        print(f"   {i}. {plugin['name']} v{plugin['version']}")
        print(f"      Category: {plugin['category']}")
        print(f"      Description: {plugin['description'][:60]}...")
        print(f"      Author: {plugin['author']}")
        print(f"      Parameters: {list(plugin['parameters'].get('properties', {}).keys())}")
        print()


async def test_fortune_plugin_execution(manager):
    """Test fortune plugin execution"""
    print_section("Testing Fortune Plugin Execution")

    # Test 1: Boxed format
    print("\n1. Testing boxed format:")
    result = await manager.execute_plugin(
        'fortune_message',
        {'category': 'any', 'format_style': 'boxed'}
    )
    print(f"   Success: {result['success']}")
    print(f"   Execution time: {result.get('execution_time', 0.0):.3f}s")
    if result['success']:
        print(f"   Result preview: {result['result'][:100]}...")
    else:
        print(f"   Error: {result.get('error')}")

    # Test 2: Quoted format
    print("\n2. Testing quoted format:")
    result = await manager.execute_plugin(
        'fortune_message',
        {'category': 'short', 'format_style': 'quoted'}
    )
    print(f"   Success: {result['success']}")
    print(f"   Execution time: {result.get('execution_time', 0.0):.3f}s")
    if result['success']:
        print(f"   Result preview: {result['result'][:100]}...")

    # Test 3: Plain format
    print("\n3. Testing plain format:")
    result = await manager.execute_plugin(
        'fortune_message',
        {'format_style': 'plain'}
    )
    print(f"   Success: {result['success']}")
    print(f"   Execution time: {result.get('execution_time', 0.0):.3f}s")

    # Test 4: Check metrics after executions
    print("\n4. Plugin metrics after executions:")
    metrics = manager.get_plugin_metrics('fortune_message')
    if metrics:
        print(f"   Execution count: {metrics['execution_count']}")
        print(f"   Success count: {metrics['success_count']}")
        print(f"   Failure count: {metrics['failure_count']}")
        print(f"   Success rate: {metrics['success_rate']}%")
        print(f"   Average execution time: {metrics['average_execution_time']:.3f}s")


async def test_input_validation(manager):
    """Test input validation"""
    print_section("Testing Input Validation")

    # Test 1: Invalid parameter (bad enum value)
    print("\n1. Testing invalid enum value:")
    result = await manager.execute_plugin(
        'fortune_message',
        {'category': 'invalid_category', 'format_style': 'boxed'}
    )
    print(f"   Success: {result['success']}")
    print(f"   Error: {result.get('error')}")

    # Test 2: SQL injection attempt
    print("\n2. Testing SQL injection detection:")
    result = await manager.execute_plugin(
        'fortune_message',
        {'category': "any'; DROP TABLE users; --", 'format_style': 'boxed'}
    )
    print(f"   Success: {result['success']}")
    print(f"   Error: {result.get('error')}")

    # Test 3: Valid parameters
    print("\n3. Testing valid parameters:")
    result = await manager.execute_plugin(
        'fortune_message',
        {'category': 'any', 'format_style': 'boxed'}
    )
    print(f"   Success: {result['success']}")
    print(f"   Execution time: {result.get('execution_time', 0.0):.3f}s")


async def test_nonexistent_plugin(manager):
    """Test execution of non-existent plugin"""
    print_section("Testing Non-Existent Plugin")

    result = await manager.execute_plugin(
        'nonexistent_plugin',
        {}
    )

    print(f"\n   Success: {result['success']}")
    print(f"   Error: {result.get('error')}")
    print(f"   Metadata: {result.get('metadata')}")


async def test_metrics_tracking(manager):
    """Test metrics tracking"""
    print_section("Testing Metrics Tracking")

    # Execute plugin multiple times
    print("\n1. Executing fortune plugin 5 times...")
    for i in range(5):
        await manager.execute_plugin(
            'fortune_message',
            {'format_style': 'plain'}
        )

    # Get metrics
    metrics = manager.get_plugin_metrics('fortune_message')
    print(f"\n   Total executions: {metrics['execution_count']}")
    print(f"   Successes: {metrics['success_count']}")
    print(f"   Failures: {metrics['failure_count']}")
    print(f"   Success rate: {metrics['success_rate']}%")
    print(f"   Average execution time: {metrics['average_execution_time']:.3f}s")

    # Get all metrics
    print("\n2. All plugin metrics:")
    all_metrics = manager.get_all_metrics()
    for name, metrics in all_metrics.items():
        print(f"\n   Plugin: {name}")
        print(f"   - Executions: {metrics['execution_count']}")
        print(f"   - Success rate: {metrics['success_rate']}%")


async def test_system_status(manager):
    """Test system status reporting"""
    print_section("Testing System Status")

    status = manager.get_system_status()

    print(f"\n   Plugins loaded: {status['plugins_loaded']}")
    print(f"   Plugins disabled: {status['plugins_disabled']}")
    print(f"   Total executions: {status['total_executions']}")
    print(f"   Total successes: {status['total_successes']}")
    print(f"   Total failures: {status['total_failures']}")
    print(f"   Overall success rate: {status['success_rate']}%")
    print(f"   Degraded mode enabled: {status['degraded_mode_enabled']}")
    print(f"   Retry enabled: {status['retry_enabled']}")

    if status['disabled_plugins']:
        print(f"\n   Disabled plugins:")
        for name, reason in status['disabled_plugins'].items():
            print(f"   - {name}: {reason}")


async def test_degraded_mode():
    """Test degraded mode (auto-disable failing plugins)"""
    print_section("Testing Degraded Mode")

    # Create a manager with low failure threshold for testing
    plugins_dir = project_root / 'plugins'
    config = {
        'plugin_defaults': {
            'execution': {
                'timeout': 60,
                'memory_limit': 256,
                'cpu_limit': 1.0,
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
            },
            'error_handling': {
                'retry': {
                    'enabled': False  # Disable retry for this test
                },
                'degraded_mode': {
                    'enabled': True,
                    'disable_after_failures': 3  # Low threshold for testing
                }
            }
        },
        'python_executable': 'python3'
    }

    manager = PluginManager(plugins_dir, config)
    await manager.initialize()

    print("\n   Attempting 3 invalid executions (should trigger degraded mode)...")

    for i in range(3):
        print(f"\n   Attempt {i + 1}:")
        result = await manager.execute_plugin(
            'fortune_message',
            {'category': 'invalid_value', 'format_style': 'boxed'}  # Invalid enum
        )
        print(f"   - Success: {result['success']}")
        print(f"   - Error: {result.get('error', 'N/A')[:80]}...")

        # Check metrics
        metrics = manager.get_plugin_metrics('fortune_message')
        print(f"   - Consecutive failures: {metrics['consecutive_failures']}")

    # Check if plugin was auto-disabled
    print("\n   Checking system status after failures:")
    status = manager.get_system_status()
    print(f"   - Plugins loaded: {status['plugins_loaded']}")
    print(f"   - Plugins disabled: {status['plugins_disabled']}")

    if 'fortune_message' in status['disabled_plugins']:
        print(f"   - ✅ Fortune plugin auto-disabled: {status['disabled_plugins']['fortune_message'][:80]}...")
    else:
        print(f"   - ⚠️  Fortune plugin still active (consecutive failures: {metrics['consecutive_failures']})")


async def test_retry_logic():
    """Test retry logic"""
    print_section("Testing Retry Logic")

    plugins_dir = project_root / 'plugins'
    config = {
        'plugin_defaults': {
            'execution': {
                'timeout': 60,
                'memory_limit': 256,
                'cpu_limit': 1.0,
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
            },
            'error_handling': {
                'retry': {
                    'enabled': True,
                    'max_attempts': 3
                },
                'degraded_mode': {
                    'enabled': False  # Disable for this test
                }
            }
        },
        'python_executable': 'python3'
    }

    manager = PluginManager(plugins_dir, config)
    await manager.initialize()

    print("\n   Testing with invalid input (should not retry on validation error):")
    result = await manager.execute_plugin(
        'fortune_message',
        {'category': 'invalid_category', 'format_style': 'boxed'}
    )
    print(f"   - Success: {result['success']}")
    print(f"   - Error: {result.get('error')}")
    print(f"   - Attempts: {result.get('metadata', {}).get('attempts', 1)}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  PluginManager Component Tests")
    print("="*60)

    # Initialize manager for main tests
    manager = await test_initialization()

    await test_plugin_discovery(manager)
    await test_fortune_plugin_execution(manager)
    await test_input_validation(manager)
    await test_nonexistent_plugin(manager)
    await test_metrics_tracking(manager)
    await test_system_status(manager)

    # Separate tests with new managers
    await test_degraded_mode()
    await test_retry_logic()

    print("\n" + "="*60)
    print("  All Tests Completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
