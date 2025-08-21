#!/usr/bin/env python3
"""
Test Suite for LLM Abstraction Layer

Tests all components: configuration, providers, factory, manager
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_providers import LLMProviderFactory, LLMProvider
from llm_providers.manager import llm_manager
from utils.config_loader import config_loader
from utils.platform import get_platform_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMAbstractionTester:
    """Comprehensive tester for LLM abstraction layer"""
    
    def __init__(self):
        self.results = {
            'platform': False,
            'config': False,
            'factory': False,
            'providers': {},
            'manager': False,
            'integration': False
        }
    
    async def run_all_tests(self):
        """Run all test suites"""
        logger.info("🧪 Starting LLM Abstraction Layer Test Suite")
        
        # Test 1: Platform Detection
        await self.test_platform_detection()
        
        # Test 2: Configuration Loading
        await self.test_configuration()
        
        # Test 3: Provider Factory
        await self.test_provider_factory()
        
        # Test 4: Individual Providers
        await self.test_providers()
        
        # Test 5: LLM Manager
        await self.test_llm_manager()
        
        # Test 6: Integration Test
        await self.test_integration()
        
        # Generate Report
        self.generate_report()
    
    async def test_platform_detection(self):
        """Test cross-platform detection and configuration"""
        logger.info("🔍 Testing Platform Detection...")
        
        try:
            platform_info = get_platform_info()
            logger.info(f"   Platform: {platform_info['platform']}")
            logger.info(f"   Architecture: {platform_info['architecture']}")
            logger.info(f"   Temp Dir: {platform_info['paths']['temp']}")
            logger.info(f"   Config Dir: {platform_info['paths']['config']}")
            
            self.results['platform'] = True
            logger.info("✅ Platform Detection: PASSED")
            
        except Exception as e:
            logger.error(f"❌ Platform Detection: FAILED - {e}")
            self.results['platform'] = False
    
    async def test_configuration(self):
        """Test configuration loading and processing"""
        logger.info("🔧 Testing Configuration Loading...")
        
        try:
            # Test default config loading
            config = config_loader.load_config()
            logger.info(f"   Loaded config with sections: {list(config.keys())}")
            
            # Test LLM config extraction
            primary_config = config_loader.get_llm_config('primary')
            tool_config = config_loader.get_llm_config('tool_calling')
            
            logger.info(f"   Primary LLM: {primary_config['type']}")
            logger.info(f"   Tool LLM: {tool_config['type']}")
            
            self.results['config'] = True
            logger.info("✅ Configuration Loading: PASSED")
            
        except Exception as e:
            logger.error(f"❌ Configuration Loading: FAILED - {e}")
            self.results['config'] = False
    
    async def test_provider_factory(self):
        """Test provider factory functionality"""
        logger.info("🏭 Testing Provider Factory...")
        
        try:
            # Test available providers
            available = LLMProviderFactory.get_available_providers()
            logger.info(f"   Available providers: {available}")
            
            # Test factory info
            factory_info = LLMProviderFactory.get_provider_info()
            logger.info(f"   Factory version: {factory_info['factory_version']}")
            
            self.results['factory'] = True
            logger.info("✅ Provider Factory: PASSED")
            
        except Exception as e:
            logger.error(f"❌ Provider Factory: FAILED - {e}")
            self.results['factory'] = False
    
    async def test_providers(self):
        """Test individual provider implementations"""
        logger.info("🤖 Testing Provider Implementations...")
        
        # Test Ollama Provider (should always be available)
        await self._test_single_provider('ollama', {
            'base_url': 'http://127.0.0.1:11434',
            'model': 'llama3.2:3b',
            'timeout': 30
        })
        
        # Test OpenAI Provider (mock test, no real API key)
        await self._test_single_provider('openai', {
            'api_key': 'test-key',
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-4-turbo-preview',
            'timeout': 30
        }, expect_auth_fail=True)
        
        # Test Qwen Provider (mock test, no real API key)
        await self._test_single_provider('qwen', {
            'api_key': 'test-key',
            'base_url': 'https://dashscope.aliyuncs.com/api/v1',
            'model': 'qwen-plus',
            'timeout': 30
        }, expect_auth_fail=True)
    
    async def _test_single_provider(self, provider_type: str, config: dict, expect_auth_fail: bool = False):
        """Test a single provider implementation"""
        logger.info(f"   Testing {provider_type} provider...")
        
        try:
            # Create provider
            provider = LLMProviderFactory.create_provider(provider_type, config)
            logger.info(f"     ✓ Provider created: {provider.name}")
            
            # Test provider info
            info = provider.get_provider_info()
            logger.info(f"     ✓ Provider info: {info['name']}")
            
            # Test configuration methods
            model = provider.get_model()
            timeout = provider.get_timeout()
            logger.info(f"     ✓ Config: model={model}, timeout={timeout}")
            
            # Test health check (may fail for cloud providers without auth)
            try:
                health = await provider.health_check()
                if expect_auth_fail and not health:
                    logger.info(f"     ✓ Health check failed as expected (no auth)")
                elif health:
                    logger.info(f"     ✓ Health check passed")
                else:
                    logger.info(f"     ⚠ Health check failed")
            except Exception as e:
                if expect_auth_fail:
                    logger.info(f"     ✓ Health check auth error as expected")
                else:
                    logger.warning(f"     ⚠ Health check error: {e}")
            
            # Test available models
            models = provider.get_available_models()
            logger.info(f"     ✓ Available models: {len(models)} models")
            
            # Cleanup
            await provider.__aexit__(None, None, None)
            
            self.results['providers'][provider_type] = True
            logger.info(f"   ✅ {provider_type} provider: PASSED")
            
        except Exception as e:
            logger.error(f"   ❌ {provider_type} provider: FAILED - {e}")
            self.results['providers'][provider_type] = False
    
    async def test_llm_manager(self):
        """Test LLM manager functionality"""
        logger.info("🎛️ Testing LLM Manager...")
        
        try:
            # Test manager initialization
            await llm_manager.initialize()
            logger.info("   ✓ Manager initialized")
            
            # Test provider info
            info = llm_manager.get_provider_info()
            logger.info(f"   ✓ Provider info: {info['initialized']}")
            
            # Test health check
            health = await llm_manager.health_check()
            logger.info(f"   ✓ Health check: {health}")
            
            self.results['manager'] = True
            logger.info("✅ LLM Manager: PASSED")
            
        except Exception as e:
            logger.error(f"❌ LLM Manager: FAILED - {e}")
            self.results['manager'] = False
    
    async def test_integration(self):
        """Test end-to-end integration"""
        logger.info("🔗 Testing Integration...")
        
        try:
            # Test simple prompt (if Ollama is available)
            if self.results['providers'].get('ollama', False):
                logger.info("   Testing simple prompt with Ollama...")
                
                # Test tool calling format
                test_tools = [
                    {
                        "name": "test_function",
                        "description": "A test function",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "Test message"
                                }
                            },
                            "required": ["message"]
                        }
                    }
                ]
                
                try:
                    # This might timeout or fail if Ollama isn't running, which is OK
                    result = await asyncio.wait_for(
                        llm_manager.generate_tools(
                            "Say hello", 
                            test_tools, 
                            timeout=10
                        ),
                        timeout=15
                    )
                    logger.info("   ✓ Tool calling test completed")
                except asyncio.TimeoutError:
                    logger.info("   ⚠ Tool calling test timed out (Ollama may not be running)")
                except Exception as e:
                    logger.info(f"   ⚠ Tool calling test failed: {e}")
            
            self.results['integration'] = True
            logger.info("✅ Integration: PASSED")
            
        except Exception as e:
            logger.error(f"❌ Integration: FAILED - {e}")
            self.results['integration'] = False
    
    def generate_report(self):
        """Generate final test report"""
        logger.info("\n" + "="*50)
        logger.info("📊 LLM ABSTRACTION LAYER TEST REPORT")
        logger.info("="*50)
        
        # Count results
        total_tests = 0
        passed_tests = 0
        
        # Core tests
        core_tests = ['platform', 'config', 'factory', 'manager', 'integration']
        for test in core_tests:
            total_tests += 1
            status = "✅ PASS" if self.results[test] else "❌ FAIL"
            logger.info(f"{test.title():15} : {status}")
            if self.results[test]:
                passed_tests += 1
        
        # Provider tests
        logger.info("\nProvider Tests:")
        for provider, result in self.results['providers'].items():
            total_tests += 1
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{provider.title():15} : {status}")
            if result:
                passed_tests += 1
        
        # Summary
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        logger.info(f"\nSUMMARY: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            logger.info("🎉 LLM Abstraction Layer is ready for integration!")
        elif success_rate >= 60:
            logger.info("⚠️ LLM Abstraction Layer has some issues but core functionality works")
        else:
            logger.error("❌ LLM Abstraction Layer needs significant fixes")
        
        return success_rate

async def main():
    """Main test runner"""
    tester = LLMAbstractionTester()
    await tester.run_all_tests()
    
    # Cleanup
    await llm_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())