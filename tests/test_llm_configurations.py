#!/usr/bin/env python3
"""
LLM Configuration Regression Testing Script
==========================================

Tests all permutations of LLM configurations after post-processing changes:
1. Ollama tool_calling + Ollama primary (think=false)
2. Ollama tool_calling + Ollama primary (think=true)
3. OpenAI tool_calling + OpenAI primary
4. Mixed configurations (Ollama+OpenAI combinations)
5. Both streaming and non-streaming modes

Usage: python test_llm_configurations.py
"""

import asyncio
import aiohttp
import json
import time
import yaml
import shutil
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMConfigTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.config_file = "config/llm_config.yaml"
        self.backup_config_file = "config/llm_config.yaml.backup"
        self.test_results = []

    def backup_config(self):
        """Backup current configuration"""
        shutil.copy(self.config_file, self.backup_config_file)
        logger.info(f"✅ Backed up config to {self.backup_config_file}")

    def restore_config(self):
        """Restore original configuration"""
        if os.path.exists(self.backup_config_file):
            shutil.copy(self.backup_config_file, self.config_file)
            logger.info(f"✅ Restored config from {self.backup_config_file}")

    def create_config(self, config_name: str, config_data: Dict[str, Any]):
        """Write a specific configuration to file"""
        with open(self.config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        logger.info(f"✅ Applied config: {config_name}")

    def get_base_config(self) -> Dict[str, Any]:
        """Get base configuration template"""
        return {
            "debug": {
                "log_requests": False,
                "log_timing": True,
                "mock_providers": False
            },
            "llm": {
                "fallback": {
                    "auto_switch": True,
                    "enabled": True,
                    "order": ["ollama", "openai", "qwen", "gemini"]
                },
                "providers": {
                    "ollama": {
                        "health_check_url": "http://127.0.0.1:11434/api/tags",
                        "retry_attempts": 3,
                        "retry_delay": 2
                    },
                    "openai": {
                        "api_key": "${OPENAI_API_KEY}",
                        "base_url": "https://api.openai.com/v1",
                        "organization": None,
                        "retry_attempts": 3,
                        "retry_delay": 1,
                        "models": {
                            "primary": "gpt-4o",
                            "tool_calling": "gpt-4o"
                        }
                    }
                }
            },
            "performance": {
                "connection_pool_size": 10,
                "max_concurrent_requests": 5,
                "request_timeout": 600,
                "streaming_chunk_size": 1024
            }
        }

    def get_test_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Get all test configuration permutations"""
        base = self.get_base_config()

        configs = {
            "ollama_both_think_false": {
                **base,
                "llm": {
                    **base["llm"],
                    "primary": {
                        "type": "ollama",
                        "config": {
                            "model": "qwen3:8b",
                            "timeout": 3600,
                            "context_window_size": 8192,
                            "temperature": 0.7,
                            "num_predict": 16384,
                            "max_tokens": 8192,
                            "base_url": "http://127.0.0.1:11434",
                            "api_key": None,
                            "stream": True,
                            "think": False
                        }
                    },
                    "tool_calling": {
                        "type": "ollama",
                        "config": {
                            "model": "qwen3:8b",
                            "timeout": 300,
                            "context_window_size": 8192,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "stream": False,
                            "base_url": "http://127.0.0.1:11434",
                            "api_key": None
                        }
                    }
                }
            },

            "ollama_both_think_true": {
                **base,
                "llm": {
                    **base["llm"],
                    "primary": {
                        "type": "ollama",
                        "config": {
                            "model": "qwen3:8b",
                            "timeout": 3600,
                            "context_window_size": 8192,
                            "temperature": 0.7,
                            "num_predict": 16384,
                            "max_tokens": 8192,
                            "base_url": "http://127.0.0.1:11434",
                            "api_key": None,
                            "stream": True,
                            "think": True
                        }
                    },
                    "tool_calling": {
                        "type": "ollama",
                        "config": {
                            "model": "qwen3:8b",
                            "timeout": 300,
                            "context_window_size": 8192,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "stream": False,
                            "base_url": "http://127.0.0.1:11434",
                            "api_key": None
                        }
                    }
                }
            },

            "openai_both": {
                **base,
                "llm": {
                    **base["llm"],
                    "primary": {
                        "type": "openai",
                        "config": {
                            "model": "gpt-4o-mini",
                            "timeout": 300,
                            "context_window_size": 128000,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "stream": True,
                            "api_key": "${OPENAI_API_KEY}",
                            "base_url": "https://api.openai.com/v1"
                        }
                    },
                    "tool_calling": {
                        "type": "openai",
                        "config": {
                            "model": "gpt-4o-mini",
                            "timeout": 300,
                            "context_window_size": 8192,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "stream": False,
                            "api_key": "${OPENAI_API_KEY}",
                            "base_url": "https://api.openai.com/v1"
                        }
                    }
                }
            },

            "ollama_tool_openai_primary": {
                **base,
                "llm": {
                    **base["llm"],
                    "primary": {
                        "type": "openai",
                        "config": {
                            "model": "gpt-4o-mini",
                            "timeout": 300,
                            "context_window_size": 128000,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "stream": True,
                            "api_key": "${OPENAI_API_KEY}",
                            "base_url": "https://api.openai.com/v1"
                        }
                    },
                    "tool_calling": {
                        "type": "ollama",
                        "config": {
                            "model": "qwen3:8b",
                            "timeout": 300,
                            "context_window_size": 8192,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "stream": False,
                            "base_url": "http://127.0.0.1:11434",
                            "api_key": None
                        }
                    }
                }
            },

            "openai_tool_ollama_primary": {
                **base,
                "llm": {
                    **base["llm"],
                    "primary": {
                        "type": "ollama",
                        "config": {
                            "model": "qwen3:8b",
                            "timeout": 3600,
                            "context_window_size": 8192,
                            "temperature": 0.7,
                            "num_predict": 16384,
                            "max_tokens": 8192,
                            "base_url": "http://127.0.0.1:11434",
                            "api_key": None,
                            "stream": True,
                            "think": False
                        }
                    },
                    "tool_calling": {
                        "type": "openai",
                        "config": {
                            "model": "gpt-4o-mini",
                            "timeout": 300,
                            "context_window_size": 8192,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                            "stream": False,
                            "api_key": "${OPENAI_API_KEY}",
                            "base_url": "https://api.openai.com/v1"
                        }
                    }
                }
            }
        }

        return configs

    async def test_basic_query(self, session: aiohttp.ClientSession, streaming: bool = True) -> Dict[str, Any]:
        """Test a basic query that requires tool calling"""

        payload = {
            "prompt": "What is the current weather in New York? Please search for recent information.",
            "stream": streaming,
            "toolsInUse": True,
            "searchWebInUse": True
        }

        start_time = time.time()

        try:
            async with session.post(f"{self.base_url}/llama_stream", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "duration": time.time() - start_time
                    }

                content = []
                if streaming:
                    async for line in response.content:
                        if line.strip():
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'response' in data:
                                    content.append(data['response'])
                            except json.JSONDecodeError:
                                continue
                else:
                    text = await response.text()
                    content.append(text)

                full_response = ''.join(content)
                duration = time.time() - start_time

                return {
                    "success": True,
                    "response_length": len(full_response),
                    "has_content": len(full_response.strip()) > 0,
                    "duration": duration,
                    "contains_thinking": "<think>" in full_response or "thinking" in full_response.lower(),
                    "sample_content": full_response[:200] + "..." if len(full_response) > 200 else full_response
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

    async def wait_for_server_restart(self, timeout: int = 30):
        """Wait for server to restart and be ready"""
        logger.info("⏳ Waiting for server to restart...")

        for i in range(timeout):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/health") as response:
                        if response.status == 200:
                            logger.info("✅ Server is ready")
                            return True
            except:
                pass

            await asyncio.sleep(1)

        logger.error("❌ Server failed to restart within timeout")
        return False

    async def run_configuration_test(self, config_name: str, config_data: Dict[str, Any]):
        """Run tests for a specific configuration"""
        logger.info(f"\n🧪 Testing configuration: {config_name}")
        logger.info("="*60)

        # Apply configuration
        self.create_config(config_name, config_data)

        # Wait for server restart
        await asyncio.sleep(5)  # Give time for config reload

        # Run tests
        results = {
            "config_name": config_name,
            "streaming_test": None,
            "non_streaming_test": None
        }

        async with aiohttp.ClientSession() as session:
            # Test streaming mode
            logger.info("📡 Testing streaming mode...")
            results["streaming_test"] = await self.test_basic_query(session, streaming=True)

            await asyncio.sleep(2)  # Brief pause between tests

            # Test non-streaming mode
            logger.info("📄 Testing non-streaming mode...")
            results["non_streaming_test"] = await self.test_basic_query(session, streaming=False)

        # Log results
        self.log_test_results(config_name, results)
        self.test_results.append(results)

        return results

    def log_test_results(self, config_name: str, results: Dict[str, Any]):
        """Log test results in a readable format"""
        logger.info(f"\n📊 Results for {config_name}:")
        logger.info("-" * 40)

        for test_type, result in results.items():
            if test_type == "config_name":
                continue

            if result:
                status = "✅ PASS" if result.get("success") else "❌ FAIL"
                logger.info(f"{test_type.replace('_', ' ').title()}: {status}")

                if result.get("success"):
                    logger.info(f"  Duration: {result['duration']:.2f}s")
                    logger.info(f"  Response length: {result['response_length']} chars")
                    logger.info(f"  Has content: {result['has_content']}")
                    logger.info(f"  Contains thinking: {result['contains_thinking']}")
                    if result.get('sample_content'):
                        logger.info(f"  Sample: {result['sample_content'][:100]}...")
                else:
                    logger.info(f"  Error: {result.get('error', 'Unknown error')}")
            else:
                logger.info(f"{test_type.replace('_', ' ').title()}: ⏭️ SKIPPED")

    def generate_summary_report(self):
        """Generate a summary report of all tests"""
        logger.info("\n" + "="*80)
        logger.info("📋 COMPREHENSIVE TEST SUMMARY REPORT")
        logger.info("="*80)

        total_tests = len(self.test_results) * 2  # 2 tests per config
        passed_tests = 0
        failed_tests = 0

        for result in self.test_results:
            config_name = result["config_name"]
            logger.info(f"\n🔧 {config_name.upper()}:")

            for test_type in ["streaming_test", "non_streaming_test"]:
                test_result = result[test_type]
                if test_result:
                    if test_result.get("success"):
                        status = "✅ PASS"
                        passed_tests += 1
                    else:
                        status = "❌ FAIL"
                        failed_tests += 1

                    logger.info(f"  {test_type.replace('_', ' ').title()}: {status}")

                    if test_result.get("success"):
                        logger.info(f"    Duration: {test_result['duration']:.2f}s")
                        logger.info(f"    Content: {test_result['response_length']} chars")
                        logger.info(f"    Thinking: {'Yes' if test_result['contains_thinking'] else 'No'}")
                    else:
                        logger.info(f"    Error: {test_result.get('error', 'Unknown')}")

        logger.info(f"\n📊 OVERALL RESULTS:")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Regression testing successful.")
        else:
            logger.info(f"\n⚠️ {failed_tests} tests failed. Review configuration issues.")

    async def run_all_tests(self):
        """Run comprehensive regression testing"""
        logger.info("🚀 Starting LLM Configuration Regression Testing")
        logger.info("="*80)

        # Backup current config
        self.backup_config()

        try:
            # Get all test configurations
            configs = self.get_test_configurations()

            logger.info(f"📝 Running tests for {len(configs)} configurations:")
            for name in configs.keys():
                logger.info(f"  - {name}")

            logger.info("\n⚠️ NOTE: Server must be restarted manually between configs")
            logger.info("Press Enter to continue...")
            input()

            # Run tests for each configuration
            for config_name, config_data in configs.items():
                await self.run_configuration_test(config_name, config_data)

                if config_name != list(configs.keys())[-1]:  # Not the last config
                    logger.info(f"\n⏸️ Please restart the server and press Enter to continue...")
                    input()

            # Generate summary report
            self.generate_summary_report()

        finally:
            # Restore original config
            self.restore_config()
            logger.info("\n✅ Original configuration restored")

async def main():
    """Main test runner"""
    tester = LLMConfigTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())