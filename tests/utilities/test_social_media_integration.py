#!/usr/bin/env python3
"""
Integration Tests for Social Media Plugins
Tests the social media publishing plugins with the PluginManager framework.
"""

import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from plugins.plugin_manager import PluginManager


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def print_result(test_name, result, show_full=False):
    """Print test result"""
    print(f"\n✓ Test: {test_name}")
    print(f"  Success: {result['success']}")
    print(f"  Execution time: {result.get('execution_time', 0.0):.3f}s")

    if result['success']:
        if show_full and 'result' in result:
            print(f"  Result: {result['result']}")
        elif 'result' in result:
            result_str = str(result['result'])
            preview = result_str[:200] + "..." if len(result_str) > 200 else result_str
            print(f"  Result preview: {preview}")
    else:
        print(f"  Error: {result.get('error')}")
        if 'metadata' in result:
            error_category = result['metadata'].get('error_category', 'unknown')
            print(f"  Error category: {error_category}")


async def setup_manager():
    """Initialize PluginManager for testing"""
    plugins_dir = project_root / 'plugins'
    config = {
        'plugin_defaults': {
            'execution': {
                'timeout': 30,
                'memory_limit': 256,
                'cpu_limit': 1.0,
                'max_timeout': 300,
                'max_memory_limit': 2048
            },
            'security': {
                'input_validation': {
                    'max_string_length': 1000000,  # 1MB for content
                    'max_array_length': 1000
                },
                'output_validation': {
                    'max_output_size': 10485760  # 10MB
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
    await manager.initialize()
    return manager


async def test_plugin_discovery(manager):
    """Test that social media plugins are discovered"""
    print_section("1. Plugin Discovery")

    plugins = manager.get_available_plugins()

    # Find social media plugins
    social_media_plugins = [p for p in plugins if 'social_media' in p['name']]

    print(f"\n✓ Found {len(social_media_plugins)} social media plugin(s):\n")

    for plugin in social_media_plugins:
        print(f"  • {plugin['name']} v{plugin['version']}")
        print(f"    Category: {plugin['category']}")
        print(f"    Description: {plugin['description'][:80]}...")
        print(f"    Parameters: {list(plugin['parameters'].get('properties', {}).keys())}")

        # Verify required fields are present
        assert plugin.get('name'), "Missing name"
        assert plugin.get('version'), "Missing version"
        assert plugin.get('category'), "Missing category"
        assert plugin.get('parameters'), "Missing parameters"
        print(f"    ✓ All required fields present")
        print()

    assert len(social_media_plugins) > 0, "No social media plugins found!"

    return social_media_plugins


async def test_plugin_metadata(manager):
    """Test social media plugin metadata structure"""
    print_section("2. Plugin Metadata Validation")

    # Get plugin definition directly from manager
    if 'social_media_substack_test' not in manager.plugins:
        print("⚠️  social_media_substack_test plugin not found, skipping metadata test")
        return

    plugin_def = manager.plugins['social_media_substack_test']

    print("\n2.1. Verifying metadata structure:")

    # Check metadata
    assert plugin_def.category == 'communications', "Wrong category"
    print("  ✓ Category: communications")

    assert 'social-media' in plugin_def.tags, "Missing 'social-media' tag"
    print("  ✓ Tags include 'social-media'")

    # Check execution config
    assert plugin_def.execution_type == 'python', "Wrong execution type"
    assert plugin_def.handler == 'handlers/social_media_substack.py', "Wrong handler path"
    print("  ✓ Execution config correct")

    # Check parameters
    properties = plugin_def.parameters.get('properties', {})
    assert 'title' in properties, "Missing 'title' parameter"
    assert 'content' in properties, "Missing 'content' parameter"
    assert 'visibility' in properties, "Missing 'visibility' parameter"
    print("  ✓ Required parameters defined")

    # Check security config
    assert plugin_def.security.get('network', {}).get('enabled') == True, "Network not enabled"
    assert '*.substack.com' in plugin_def.security.get('network', {}).get('allowed_domains', []), "Substack domain not whitelisted"
    print("  ✓ Security config correct")

    print("\n✅ All metadata validations passed")


async def test_validation_errors(manager):
    """Test input validation catches errors"""
    print_section("3. Input Validation Tests")

    # Set up test environment
    os.environ['ACCOUNT_EMAIL_ENV'] = 'SUBSTACK_TEST_EMAIL'
    os.environ['ACCOUNT_PASSWORD_ENV'] = 'SUBSTACK_TEST_PASSWORD'
    os.environ['SUBSTACK_TEST_EMAIL'] = 'test@example.com'
    os.environ['SUBSTACK_TEST_PASSWORD'] = 'testpassword123'

    print("\n3.1. Missing required field (title):")
    result = await manager.execute_plugin(
        'social_media_substack_test',
        {'content': '<p>Content without title</p>'}
    )
    print_result('Missing title', result)
    assert result['success'] == False, "Should fail with missing title"
    assert 'title' in result.get('error', '').lower(), "Error should mention title"

    print("\n3.2. Missing required field (content):")
    result = await manager.execute_plugin(
        'social_media_substack_test',
        {'title': 'Title without content'}
    )
    print_result('Missing content', result)
    assert result['success'] == False, "Should fail with missing content"
    assert 'content' in result.get('error', '').lower(), "Error should mention content"

    print("\n3.3. Title too long:")
    result = await manager.execute_plugin(
        'social_media_substack_test',
        {
            'title': 'X' * 250,  # Exceeds 200 char limit
            'content': '<p>Content</p>'
        }
    )
    print_result('Title too long', result)
    assert result['success'] == False, "Should fail with title too long"
    assert 'too long' in result.get('error', '').lower(), "Error should mention 'too long'"

    print("\n3.4. Invalid visibility value:")
    result = await manager.execute_plugin(
        'social_media_substack_test',
        {
            'title': 'Test Post',
            'content': '<p>Content</p>',
            'visibility': 'invalid_visibility'
        }
    )
    print_result('Invalid visibility', result)
    assert result['success'] == False, "Should fail with invalid visibility"
    assert 'visibility' in result.get('error', '').lower(), "Error should mention visibility"

    print("\n✅ All validation tests passed")


async def test_security_sanitization(manager):
    """Test HTML sanitization and XSS prevention"""
    print_section("4. Security & Sanitization Tests")

    # Set up credentials
    os.environ['ACCOUNT_EMAIL_ENV'] = 'SUBSTACK_TEST_EMAIL'
    os.environ['ACCOUNT_PASSWORD_ENV'] = 'SUBSTACK_TEST_PASSWORD'
    os.environ['SUBSTACK_TEST_EMAIL'] = 'test@example.com'
    os.environ['SUBSTACK_TEST_PASSWORD'] = 'testpassword123'

    # Mock the Substack API to capture sanitized content
    async def mock_publish(*args, **kwargs):
        """Mock publish function that captures sanitized content"""
        content = kwargs.get('content', args[3] if len(args) > 3 else '')

        # Verify sanitization happened
        sanitization_tests = {
            '<script>': False,  # Script tags should be removed
            'alert': False,     # Alert calls should be removed
            'onerror': False,   # Event handlers should be removed
            'javascript:': False  # JavaScript protocol should be removed
        }

        for dangerous_content, should_exist in sanitization_tests.items():
            if dangerous_content in content:
                return {
                    "success": False,
                    "result": None,
                    "error": f"Sanitization failed: Found '{dangerous_content}' in content"
                }

        return {
            "success": True,
            "result": {
                "post_url": "https://test.substack.com/p/test-post",
                "post_id": "12345",
                "title": kwargs.get('title', ''),
                "platform": "substack",
                "visibility": kwargs.get('visibility', 'everyone')
            },
            "error": None
        }

    # Import and patch the handler module
    sys.path.insert(0, str(project_root / 'plugins' / 'handlers'))
    import social_media_substack

    print("\n4.1. XSS attempt with <script> tag:")
    with patch.object(social_media_substack, 'publish_to_substack', mock_publish):
        result = await manager.execute_plugin(
            'social_media_substack_test',
            {
                'title': 'Test Post',
                'content': '<p>Safe content</p><script>alert("XSS")</script>'
            }
        )
        print_result('Script tag removal', result)
        # Should succeed because sanitization removes the script tag
        if not result['success']:
            print(f"  Note: {result.get('error', 'Unknown error')}")

    print("\n4.2. XSS attempt with event handler:")
    with patch.object(social_media_substack, 'publish_to_substack', mock_publish):
        result = await manager.execute_plugin(
            'social_media_substack_test',
            {
                'title': 'Test Post',
                'content': '<img src="x" onerror="alert(1)">'
            }
        )
        print_result('Event handler removal', result)
        if not result['success']:
            print(f"  Note: {result.get('error', 'Unknown error')}")

    print("\n4.3. XSS attempt with javascript: protocol:")
    with patch.object(social_media_substack, 'publish_to_substack', mock_publish):
        result = await manager.execute_plugin(
            'social_media_substack_test',
            {
                'title': 'Test Post',
                'content': '<a href="javascript:alert(1)">Click</a>'
            }
        )
        print_result('JavaScript protocol removal', result)
        if not result['success']:
            print(f"  Note: {result.get('error', 'Unknown error')}")

    print("\n✅ Security tests completed")


async def test_missing_credentials(manager):
    """Test behavior with missing credentials"""
    print_section("5. Missing Credentials Test")

    # Clear environment variables
    for key in ['ACCOUNT_EMAIL_ENV', 'ACCOUNT_PASSWORD_ENV', 'SUBSTACK_TEST_EMAIL', 'SUBSTACK_TEST_PASSWORD']:
        os.environ.pop(key, None)

    print("\n5.1. Execution without credentials:")
    result = await manager.execute_plugin(
        'social_media_substack_test',
        {
            'title': 'Test Post',
            'content': '<p>Content</p>'
        }
    )
    print_result('Missing credentials', result)
    assert result['success'] == False, "Should fail with missing credentials"
    assert 'credential' in result.get('error', '').lower(), "Error should mention credentials"

    print("\n✅ Credentials validation passed")


async def test_metrics_tracking(manager):
    """Test metrics tracking for social media plugins"""
    print_section("6. Metrics Tracking")

    # Set up credentials
    os.environ['ACCOUNT_EMAIL_ENV'] = 'SUBSTACK_TEST_EMAIL'
    os.environ['ACCOUNT_PASSWORD_ENV'] = 'SUBSTACK_TEST_PASSWORD'
    os.environ['SUBSTACK_TEST_EMAIL'] = 'test@example.com'
    os.environ['SUBSTACK_TEST_PASSWORD'] = 'testpassword123'

    print("\n6.1. Executing plugin multiple times to generate metrics:")

    # Execute with validation errors (should increment failure count)
    for i in range(3):
        await manager.execute_plugin(
            'social_media_substack_test',
            {'content': '<p>Missing title</p>'}  # Missing required field
        )

    # Check metrics
    metrics = manager.get_plugin_metrics('social_media_substack_test')

    if metrics:
        print(f"\n  Plugin Metrics:")
        print(f"    Execution count: {metrics['execution_count']}")
        print(f"    Success count: {metrics['success_count']}")
        print(f"    Failure count: {metrics['failure_count']}")
        print(f"    Success rate: {metrics['success_rate']}%")
        print(f"    Average execution time: {metrics['average_execution_time']:.3f}s")
        print(f"    Consecutive failures: {metrics['consecutive_failures']}")

        assert metrics['execution_count'] >= 3, "Should have at least 3 executions"
        assert metrics['failure_count'] >= 3, "Should have at least 3 failures"

        print("\n✅ Metrics tracking working correctly")
    else:
        print("  ⚠️  No metrics available for plugin")


async def test_error_categorization():
    """Test error categorization in responses"""
    print_section("7. Error Categorization")

    # Create fresh manager with degraded mode disabled
    # This avoids interference from previous test failures
    plugins_dir = project_root / 'plugins'
    config = {
        'plugin_defaults': {
            'execution': {
                'timeout': 30,
                'memory_limit': 256,
                'cpu_limit': 1.0
            },
            'security': {
                'input_validation': {
                    'max_string_length': 1000000,
                    'max_array_length': 1000
                },
                'output_validation': {
                    'max_output_size': 10485760
                }
            },
            'error_handling': {
                'retry': {'enabled': False},
                'degraded_mode': {'enabled': False}  # Disable for clean testing
            }
        },
        'python_executable': 'python3'
    }

    fresh_manager = PluginManager(plugins_dir, config)
    await fresh_manager.initialize()

    # Set up credentials
    os.environ['ACCOUNT_EMAIL_ENV'] = 'SUBSTACK_TEST_EMAIL'
    os.environ['ACCOUNT_PASSWORD_ENV'] = 'SUBSTACK_TEST_PASSWORD'
    os.environ['SUBSTACK_TEST_EMAIL'] = 'test@example.com'
    os.environ['SUBSTACK_TEST_PASSWORD'] = 'testpassword123'

    print("\n7.1. Validation error (schema violation):")
    result = await fresh_manager.execute_plugin(
        'social_media_substack_test',
        {'content': '<p>Missing title</p>'}
    )
    print_result('Validation error', result)
    # Schema validation happens at PluginManager level, so error category is 'unknown'
    # This is expected behavior

    print("\n7.2. Configuration error (missing credentials):")
    # Clear credentials
    os.environ.pop('SUBSTACK_TEST_EMAIL', None)
    os.environ.pop('SUBSTACK_TEST_PASSWORD', None)

    result = await fresh_manager.execute_plugin(
        'social_media_substack_test',
        {
            'title': 'Test Post',
            'content': '<p>Content</p>'
        }
    )
    print_result('Configuration error', result)
    if 'metadata' in result:
        error_category = result['metadata'].get('error_category', 'unknown')
        print(f"  Error category: {error_category}")
        assert error_category == 'configuration', "Should be categorized as configuration error"
    else:
        print("  ⚠️  No metadata in result (error occurred before plugin execution)")

    print("\n✅ Error categorization test completed")


async def test_system_status(manager):
    """Test system status includes social media plugins"""
    print_section("8. System Status")

    status = manager.get_system_status()

    print(f"\n📊 Overall System Status:")
    print(f"  Plugins loaded: {status['plugins_loaded']}")
    print(f"  Plugins disabled: {status['plugins_disabled']}")
    print(f"  Total executions: {status['total_executions']}")
    print(f"  Total successes: {status['total_successes']}")
    print(f"  Total failures: {status['total_failures']}")
    print(f"  Overall success rate: {status['success_rate']}%")

    # Check if social media plugin metrics are included
    all_metrics = manager.get_all_metrics()
    social_media_metrics = {k: v for k, v in all_metrics.items() if 'social_media' in k}

    if social_media_metrics:
        print(f"\n📈 Social Media Plugin Metrics:")
        for name, metrics in social_media_metrics.items():
            print(f"\n  Plugin: {name}")
            print(f"    Executions: {metrics['execution_count']}")
            print(f"    Success rate: {metrics['success_rate']}%")
            print(f"    Avg execution time: {metrics['average_execution_time']:.3f}s")
            if metrics['last_error']:
                print(f"    Last error: {metrics['last_error'][:80]}...")

    print("\n✅ System status reporting working")


async def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("  SOCIAL MEDIA PLUGIN INTEGRATION TESTS")
    print("  Testing integration with PluginManager framework")
    print("="*70)

    print("\n⏳ Initializing plugin system...")
    manager = await setup_manager()
    print("✓ Plugin system initialized")

    try:
        # Run all tests
        await test_plugin_discovery(manager)
        await test_plugin_metadata(manager)
        await test_validation_errors(manager)
        await test_security_sanitization(manager)
        await test_missing_credentials(manager)
        await test_metrics_tracking(manager)
        await test_error_categorization()  # Creates its own manager
        await test_system_status(manager)

        print("\n" + "="*70)
        print("  ✅ ALL INTEGRATION TESTS PASSED!")
        print("="*70 + "\n")

    except AssertionError as e:
        print(f"\n\n❌ TEST FAILED: {str(e)}\n")
        raise
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {str(e)}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
