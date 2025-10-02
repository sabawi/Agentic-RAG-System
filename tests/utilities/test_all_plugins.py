#!/usr/bin/env python3
"""
Test All Plugins End-to-End
Comprehensive testing of the complete plugin system with all example plugins.
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
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def print_result(plugin_name, result, show_full=False):
    """Print plugin execution result"""
    print(f"\n✓ Plugin: {plugin_name}")
    print(f"  Success: {result['success']}")
    print(f"  Execution time: {result.get('execution_time', 0.0):.3f}s")

    if result['success']:
        result_text = result['result']
        if show_full:
            print(f"\n{result_text}\n")
        else:
            # Show first 200 characters
            preview = result_text[:200] + "..." if len(result_text) > 200 else result_text
            print(f"  Result preview:\n{preview}")
    else:
        print(f"  Error: {result.get('error')}")


async def test_plugin_discovery(manager):
    """Test plugin discovery"""
    print_section("1. Plugin Discovery and Registration")

    plugins = manager.get_available_plugins()

    print(f"\n✓ Discovered {len(plugins)} plugins:\n")

    for i, plugin in enumerate(plugins, 1):
        print(f"  {i}. {plugin['name']} v{plugin['version']}")
        print(f"     Category: {plugin['category']}")
        print(f"     Description: {plugin['description'][:80]}...")
        print(f"     Parameters: {list(plugin['parameters'].get('properties', {}).keys())}")
        print()

    return plugins


async def test_fortune_plugin(manager):
    """Test fortune message plugin"""
    print_section("2. Testing Fortune Message Plugin")

    print("\n2.1. Boxed format:")
    result = await manager.execute_plugin(
        'fortune_message',
        {'format_style': 'boxed'}
    )
    print_result('fortune_message', result, show_full=True)

    print("\n2.2. Quoted format:")
    result = await manager.execute_plugin(
        'fortune_message',
        {'category': 'short', 'format_style': 'quoted'}
    )
    print_result('fortune_message', result, show_full=True)


async def test_weather_plugin(manager):
    """Test weather info plugin"""
    print_section("3. Testing Weather Info Plugin")

    print("\n3.1. Weather for London (brief):")
    result = await manager.execute_plugin(
        'weather_info',
        {'city': 'London', 'units': 'metric', 'format': 'brief'}
    )
    print_result('weather_info', result, show_full=True)

    print("\n3.2. Weather for Tokyo (brief):")
    result = await manager.execute_plugin(
        'weather_info',
        {'city': 'Tokyo', 'format': 'brief'}
    )
    print_result('weather_info', result, show_full=True)


async def test_file_stats_plugin(manager):
    """Test file stats plugin"""
    print_section("4. Testing File Stats Plugin")

    print("\n4.1. Analyzing /plugins directory:")
    result = await manager.execute_plugin(
        'file_stats',
        {'path': str(project_root / 'plugins'), 'include_hidden': False, 'recursive': False}
    )
    print_result('file_stats', result, show_full=True)

    print("\n4.2. Analyzing README.md file:")
    result = await manager.execute_plugin(
        'file_stats',
        {'path': str(project_root / 'plugins' / 'README.md')}
    )
    print_result('file_stats', result)


async def test_system_monitor_plugin(manager):
    """Test system monitor plugin"""
    print_section("5. Testing System Monitor Plugin")

    print("\n5.1. CPU monitoring:")
    result = await manager.execute_plugin(
        'system_monitor',
        {'metric': 'cpu'}
    )
    print_result('system_monitor', result, show_full=True)

    print("\n5.2. Memory monitoring:")
    result = await manager.execute_plugin(
        'system_monitor',
        {'metric': 'memory'}
    )
    print_result('system_monitor', result, show_full=True)

    print("\n5.3. Top processes (top 5):")
    result = await manager.execute_plugin(
        'system_monitor',
        {'metric': 'processes', 'process_limit': 5}
    )
    print_result('system_monitor', result, show_full=True)


async def test_text_analyzer_plugin(manager):
    """Test text analyzer plugin"""
    print_section("6. Testing Text Analyzer Plugin")

    sample_text = """
    The quick brown fox jumps over the lazy dog. This is a wonderful example of text
    analysis in action. Natural language processing helps us understand content better.
    Good writing makes communication easier and more effective. Analysis reveals patterns
    and insights that improve our understanding.
    """

    print("\n6.1. Basic analysis:")
    result = await manager.execute_plugin(
        'text_analyzer',
        {'text': sample_text, 'analysis_type': 'basic'}
    )
    print_result('text_analyzer', result, show_full=True)

    print("\n6.2. Detailed analysis:")
    result = await manager.execute_plugin(
        'text_analyzer',
        {'text': sample_text, 'analysis_type': 'detailed', 'top_words_count': 5}
    )
    print_result('text_analyzer', result, show_full=True)

    print("\n6.3. Readability analysis:")
    result = await manager.execute_plugin(
        'text_analyzer',
        {'text': sample_text, 'analysis_type': 'readability'}
    )
    print_result('text_analyzer', result, show_full=True)


async def test_security_validation(manager):
    """Test security validation features"""
    print_section("7. Testing Security Validation")

    print("\n7.1. Invalid enum value (should fail):")
    result = await manager.execute_plugin(
        'fortune_message',
        {'category': 'invalid_category', 'format_style': 'boxed'}
    )
    print_result('fortune_message', result)

    print("\n7.2. SQL injection attempt (should fail):")
    result = await manager.execute_plugin(
        'weather_info',
        {'city': "London'; DROP TABLE users; --"}
    )
    print_result('weather_info', result)

    print("\n7.3. Path traversal attempt (should fail):")
    result = await manager.execute_plugin(
        'file_stats',
        {'path': '/etc/shadow'}  # Blocked path
    )
    print_result('file_stats', result)


async def test_system_metrics(manager):
    """Test system metrics and monitoring"""
    print_section("8. System Metrics and Health")

    status = manager.get_system_status()

    print(f"\n📊 Overall System Status:")
    print(f"  Plugins loaded: {status['plugins_loaded']}")
    print(f"  Plugins disabled: {status['plugins_disabled']}")
    print(f"  Total executions: {status['total_executions']}")
    print(f"  Total successes: {status['total_successes']}")
    print(f"  Total failures: {status['total_failures']}")
    print(f"  Overall success rate: {status['success_rate']}%")
    print(f"  Degraded mode enabled: {status['degraded_mode_enabled']}")
    print(f"  Retry enabled: {status['retry_enabled']}")

    print(f"\n📈 Per-Plugin Metrics:")
    all_metrics = manager.get_all_metrics()

    for name, metrics in sorted(all_metrics.items()):
        print(f"\n  Plugin: {name}")
        print(f"    Executions: {metrics['execution_count']}")
        print(f"    Success rate: {metrics['success_rate']}%")
        print(f"    Avg execution time: {metrics['average_execution_time']:.3f}s")
        if metrics['last_error']:
            print(f"    Last error: {metrics['last_error'][:60]}...")


async def test_error_handling(manager):
    """Test error handling and degraded mode"""
    print_section("9. Error Handling and Recovery")

    print("\n9.1. Non-existent plugin:")
    result = await manager.execute_plugin(
        'nonexistent_plugin',
        {}
    )
    print_result('nonexistent_plugin', result)

    print("\n9.2. Missing required parameter:")
    result = await manager.execute_plugin(
        'weather_info',
        {}  # Missing 'city' parameter
    )
    print_result('weather_info', result)

    print("\n9.3. Invalid city name:")
    result = await manager.execute_plugin(
        'weather_info',
        {'city': 'ThisCityDoesNotExist12345XYZ'}
    )
    print_result('weather_info', result)


async def main():
    """Run comprehensive plugin system tests"""
    print("\n" + "="*70)
    print("  COMPREHENSIVE PLUGIN SYSTEM TEST")
    print("  Testing all plugins from user perspective")
    print("="*70)

    # Initialize plugin manager
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
                    'max_string_length': 102400,
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

    print("\n⏳ Initializing plugin system...")
    init_result = await manager.initialize()
    print(f"✓ Initialized: {init_result['plugins_loaded']} plugins loaded in {init_result['initialization_time']:.3f}s")

    if init_result['errors']:
        print(f"⚠️  Errors during initialization: {init_result['errors']}")

    # Run all tests
    await test_plugin_discovery(manager)
    await test_fortune_plugin(manager)
    await test_weather_plugin(manager)
    await test_file_stats_plugin(manager)
    await test_system_monitor_plugin(manager)
    await test_text_analyzer_plugin(manager)
    await test_security_validation(manager)
    await test_error_handling(manager)
    await test_system_metrics(manager)

    print("\n" + "="*70)
    print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
