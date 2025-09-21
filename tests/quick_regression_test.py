#!/usr/bin/env python3
"""
Quick Regression Test - Post-Processing Removal Verification
==========================================================

Quick test to verify that removing think parameter post-processing
doesn't break existing functionality.

Usage: python quick_regression_test.py
"""

import asyncio
import aiohttp
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"

    async def test_current_config(self):
        """Test current configuration with basic queries"""

        test_cases = [
            {
                "name": "Simple Query (No Tools)",
                "payload": {
                    "model": "qwen3:8b",
                    "prompt": "What is 2+2? Give me a brief answer.",
                    "stream": True,
                    "toolsInUse": False,
                    "searchWebInUse": False
                }
            },
            {
                "name": "Tool Calling Query",
                "payload": {
                    "model": "qwen3:8b",
                    "prompt": "What is the current weather in Paris? Please search for information.",
                    "stream": True,
                    "toolsInUse": True,
                    "searchWebInUse": True
                }
            },
            {
                "name": "Non-Streaming Simple Query",
                "payload": {
                    "model": "qwen3:8b",
                    "prompt": "Explain what machine learning is in one sentence.",
                    "stream": False,
                    "toolsInUse": False,
                    "searchWebInUse": False
                }
            }
        ]

        logger.info("🚀 Running Quick Regression Test")
        logger.info("="*50)

        results = []

        async with aiohttp.ClientSession() as session:
            for i, test_case in enumerate(test_cases, 1):
                logger.info(f"\n🧪 Test {i}: {test_case['name']}")
                logger.info("-" * 30)

                result = await self.run_single_test(session, test_case)
                results.append(result)

                # Brief pause between tests
                await asyncio.sleep(2)

        # Summary
        self.print_summary(results)

    async def run_single_test(self, session: aiohttp.ClientSession, test_case: dict) -> dict:
        """Run a single test case"""

        start_time = time.time()

        try:
            async with session.post(f"{self.base_url}/llama3_1b/stream", json=test_case["payload"]) as response:

                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ HTTP {response.status}: {error_text}")
                    return {
                        "name": test_case["name"],
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "duration": time.time() - start_time
                    }

                content_parts = []

                if test_case["payload"].get("stream", True):
                    # Streaming response
                    async for line in response.content:
                        if line.strip():
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'response' in data and data['response']:
                                    content_parts.append(data['response'])
                            except json.JSONDecodeError:
                                continue
                else:
                    # Non-streaming response
                    text = await response.text()
                    content_parts.append(text)

                full_response = ''.join(content_parts)
                duration = time.time() - start_time

                # Analyze response
                has_content = len(full_response.strip()) > 0
                has_thinking = any(indicator in full_response.lower()
                                  for indicator in ['<think>', 'thinking', 'reason'])

                logger.info(f"✅ Success")
                logger.info(f"📏 Response length: {len(full_response)} chars")
                logger.info(f"⏱️ Duration: {duration:.2f}s")
                logger.info(f"🧠 Contains thinking: {has_thinking}")

                if full_response:
                    sample = full_response[:150].replace('\n', ' ')
                    logger.info(f"📝 Sample: {sample}...")
                else:
                    logger.warning("⚠️ Empty response")

                return {
                    "name": test_case["name"],
                    "success": True,
                    "duration": duration,
                    "response_length": len(full_response),
                    "has_content": has_content,
                    "has_thinking": has_thinking,
                    "sample": full_response[:200] if full_response else ""
                }

        except Exception as e:
            logger.error(f"❌ Exception: {str(e)}")
            return {
                "name": test_case["name"],
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

    def print_summary(self, results: list):
        """Print test summary"""

        logger.info("\n" + "="*50)
        logger.info("📊 QUICK REGRESSION TEST SUMMARY")
        logger.info("="*50)

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get("success", False))
        failed_tests = total_tests - passed_tests

        for result in results:
            name = result["name"]
            if result.get("success", False):
                status = "✅ PASS"
                details = f"({result['duration']:.2f}s, {result['response_length']} chars)"
                if result.get('has_thinking'):
                    details += " [Contains thinking content]"
            else:
                status = "❌ FAIL"
                details = f"({result.get('error', 'Unknown error')})"

            logger.info(f"{name}: {status} {details}")

        logger.info("\n" + "-"*30)
        logger.info(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")

        if failed_tests == 0:
            logger.info("🎉 All tests passed! Post-processing removal successful.")
        else:
            logger.info(f"⚠️ {failed_tests} test(s) failed. Investigation needed.")

        # Configuration check
        logger.info("\n🔧 Current Configuration Check:")
        logger.info("- Verify think parameter is properly passed to Ollama")
        logger.info("- Verify output renders AS-IS without post-processing")
        logger.info("- Verify both streaming and non-streaming work")

async def main():
    """Run quick regression test"""
    tester = QuickTester()
    await tester.test_current_config()

if __name__ == "__main__":
    asyncio.run(main())
