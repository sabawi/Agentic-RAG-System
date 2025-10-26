#!/usr/bin/env python3
"""
Test Configuration Fail-Fast Behavior
=====================================

Verifies that the system correctly implements fail-fast behavior when
required configuration is missing, per PROJECT_CONFIGURATION_DIRECTIVE.md

Tests:
1. Ollama provider requires base_url
2. Ollama provider works with proper config
3. Gemini provider requires model
4. Gemini provider requires API key
5. Gemini provider returns available models
6. Gemini provider returns provider info
7. No hardcoded fallbacks in config_loader.py

Author: Claude Code
Date: 2025-10-17
"""

import sys
import os
import tempfile
import yaml
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm_providers.ollama import OllamaProvider
from llm_providers.gemini import GeminiProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestConfigFailFast:
    """Test suite for configuration fail-fast behavior"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0

    def test_ollama_missing_base_url(self):
        """Test that Ollama provider fails fast when base_url is missing"""
        self.total += 1
        test_name = "Ollama provider fails without base_url"

        try:
            # Create config WITHOUT base_url
            config = {
                'model': 'gpt-4o-mini',
                'timeout': 600
                # Deliberately missing 'base_url'
            }

            # This should raise ValueError
            provider = OllamaProvider(config)

            # If we get here, test FAILED
            logger.error(f"❌ {test_name}: FAILED - No exception raised!")
            self.failed += 1
            return False

        except ValueError as e:
            # Check that error message is helpful
            error_msg = str(e)
            if 'base_url' in error_msg and 'llm_config.yaml' in error_msg:
                logger.info(f"✅ {test_name}: PASSED")
                logger.info(f"   Error message: {error_msg}")
                self.passed += 1
                return True
            else:
                logger.error(f"❌ {test_name}: FAILED - Unclear error message")
                logger.error(f"   Got: {error_msg}")
                self.failed += 1
                return False
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED - Wrong exception type: {type(e).__name__}")
            logger.error(f"   {e}")
            self.failed += 1
            return False

    def test_ollama_with_base_url(self):
        """Test that Ollama provider works with proper configuration"""
        self.total += 1
        test_name = "Ollama provider succeeds with base_url"

        try:
            # Create complete config
            config = {
                'model': 'gpt-4o-mini',
                'base_url': 'http://127.0.0.1:11434',
                'timeout': 600
            }

            # This should succeed
            provider = OllamaProvider(config)

            if provider.base_url == 'http://127.0.0.1:11434':
                logger.info(f"✅ {test_name}: PASSED")
                self.passed += 1
                return True
            else:
                logger.error(f"❌ {test_name}: FAILED - Wrong base_url: {provider.base_url}")
                self.failed += 1
                return False

        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED - Unexpected exception: {e}")
            self.failed += 1
            return False

    def test_gemini_missing_model(self):
        """Test that Gemini provider fails fast when model is missing"""
        self.total += 1
        test_name = "Gemini provider fails without model"

        try:
            # Create config WITHOUT model
            config = {
                'api_key': 'test_key_12345',
                'timeout': 600
                # Deliberately missing 'model'
            }

            # This should raise ValueError
            provider = GeminiProvider(config)

            # If we get here, test FAILED
            logger.error(f"❌ {test_name}: FAILED - No exception raised!")
            self.failed += 1
            return False

        except ValueError as e:
            # Check that error message is helpful
            error_msg = str(e)
            if 'model' in error_msg and 'llm_config.yaml' in error_msg:
                logger.info(f"✅ {test_name}: PASSED")
                logger.info(f"   Error message: {error_msg}")
                self.passed += 1
                return True
            else:
                logger.error(f"❌ {test_name}: FAILED - Unclear error message")
                logger.error(f"   Got: {error_msg}")
                self.failed += 1
                return False
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED - Wrong exception type: {type(e).__name__}")
            logger.error(f"   {e}")
            self.failed += 1
            return False

    def test_gemini_missing_api_key(self):
        """Test that Gemini provider fails fast when API key is missing"""
        self.total += 1
        test_name = "Gemini provider fails without API key"

        try:
            # Create config WITHOUT api_key
            config = {
                'model': 'gemini-1.5-flash-latest',
                'timeout': 600
                # Deliberately missing 'api_key'
            }

            # This should raise ValueError
            provider = GeminiProvider(config)

            # If we get here, test FAILED
            logger.error(f"❌ {test_name}: FAILED - No exception raised!")
            self.failed += 1
            return False

        except ValueError as e:
            # Check that error message is helpful
            error_msg = str(e)
            if 'api_key' in error_msg.lower() or 'API key' in error_msg:
                logger.info(f"✅ {test_name}: PASSED")
                logger.info(f"   Error message: {error_msg}")
                self.passed += 1
                return True
            else:
                logger.error(f"❌ {test_name}: FAILED - Unclear error message")
                logger.error(f"   Got: {error_msg}")
                self.failed += 1
                return False
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED - Wrong exception type: {type(e).__name__}")
            logger.error(f"   {e}")
            self.failed += 1
            return False

    def test_gemini_get_available_models(self):
        """Test that Gemini provider returns list of available models"""
        self.total += 1
        test_name = "Gemini provider returns available models"

        try:
            # Create complete config
            config = {
                'model': 'gemini-flash-latest',
                'api_key': 'test_key_12345',
                'timeout': 600
            }

            # This should succeed (won't actually connect to API)
            provider = GeminiProvider(config)
            models = provider.get_available_models()

            # Check that it returns a list with expected models
            if isinstance(models, list) and len(models) > 0:
                if 'gemini-flash-latest' in models:
                    logger.info(f"✅ {test_name}: PASSED")
                    logger.info(f"   Found {len(models)} models: {models}")
                    self.passed += 1
                    return True
                else:
                    logger.error(f"❌ {test_name}: FAILED - Missing expected model")
                    logger.error(f"   Got: {models}")
                    self.failed += 1
                    return False
            else:
                logger.error(f"❌ {test_name}: FAILED - Invalid return type or empty list")
                logger.error(f"   Got: {models}")
                self.failed += 1
                return False

        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED - Unexpected exception: {e}")
            self.failed += 1
            return False

    def test_gemini_get_provider_info(self):
        """Test that Gemini provider returns provider information"""
        self.total += 1
        test_name = "Gemini provider returns provider info"

        try:
            # Create complete config
            config = {
                'model': 'gemini-flash-latest',
                'api_key': 'test_key_12345',
                'timeout': 600,
                'max_tokens': 2048,
                'temperature': 0.7
            }

            # This should succeed (won't actually connect to API)
            provider = GeminiProvider(config)
            info = provider.get_provider_info()

            # Check that it returns a dict with expected keys
            expected_keys = ['name', 'type', 'configured_model', 'supports_streaming',
                           'supports_function_calling', 'supports_vision', 'timeout',
                           'max_tokens', 'temperature', 'api_key_configured']

            if isinstance(info, dict):
                missing_keys = [key for key in expected_keys if key not in info]
                if not missing_keys:
                    logger.info(f"✅ {test_name}: PASSED")
                    logger.info(f"   Provider: {info['name']} ({info['type']})")
                    logger.info(f"   Model: {info['configured_model']}")
                    logger.info(f"   Streaming: {info['supports_streaming']}, Vision: {info['supports_vision']}")
                    self.passed += 1
                    return True
                else:
                    logger.error(f"❌ {test_name}: FAILED - Missing keys: {missing_keys}")
                    self.failed += 1
                    return False
            else:
                logger.error(f"❌ {test_name}: FAILED - Invalid return type: {type(info)}")
                self.failed += 1
                return False

        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED - Unexpected exception: {e}")
            self.failed += 1
            return False

    def test_no_hardcoded_fallbacks(self):
        """Test that config_loader.py has no hardcoded fallback constants"""
        self.total += 1
        test_name = "No hardcoded fallback constants in config_loader.py"

        try:
            config_loader_path = Path(__file__).parent.parent.parent / "utils" / "config_loader.py"
            with open(config_loader_path, 'r') as f:
                content = f.read()

            # Check for forbidden patterns
            forbidden_patterns = [
                'EMERGENCY_FALLBACK_BASE_URL',
                'EMERGENCY_FALLBACK_TIMEOUT',
                "= 'http://",
                '= "http://'
            ]

            found_violations = []
            for pattern in forbidden_patterns:
                if pattern in content:
                    # Check if it's in a comment (allowed)
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if pattern in line and not line.strip().startswith('#'):
                            found_violations.append(f"Line {i}: {line.strip()}")

            if not found_violations:
                logger.info(f"✅ {test_name}: PASSED")
                self.passed += 1
                return True
            else:
                logger.error(f"❌ {test_name}: FAILED - Found hardcoded values:")
                for violation in found_violations:
                    logger.error(f"   {violation}")
                self.failed += 1
                return False

        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED - Error reading file: {e}")
            self.failed += 1
            return False

    def run_all_tests(self):
        """Run all fail-fast configuration tests"""
        logger.info("=" * 80)
        logger.info("🧪 CONFIGURATION FAIL-FAST TEST SUITE")
        logger.info("=" * 80)
        logger.info("")

        # Run tests
        self.test_ollama_missing_base_url()
        logger.info("")

        self.test_ollama_with_base_url()
        logger.info("")

        self.test_gemini_missing_model()
        logger.info("")

        self.test_gemini_missing_api_key()
        logger.info("")

        self.test_gemini_get_available_models()
        logger.info("")

        self.test_gemini_get_provider_info()
        logger.info("")

        self.test_no_hardcoded_fallbacks()
        logger.info("")

        # Summary
        logger.info("=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests:  {self.total}")
        logger.info(f"Passed: ✅    {self.passed}")
        logger.info(f"Failed: ❌    {self.failed}")
        logger.info(f"Success Rate: {(self.passed/self.total*100):.1f}%")
        logger.info("=" * 80)

        if self.failed == 0:
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("✅ Configuration fail-fast behavior is correctly implemented")
            logger.info("✅ PROJECT_CONFIGURATION_DIRECTIVE.md compliance verified")
            return 0
        else:
            logger.error("❌ SOME TESTS FAILED!")
            logger.error("⚠️  Configuration fail-fast behavior needs fixes")
            return 1


if __name__ == "__main__":
    tester = TestConfigFailFast()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
