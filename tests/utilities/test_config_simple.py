#!/usr/bin/env python3
"""
Simple Configuration Test - Test current LLM configuration
=========================================================

Tests the current configuration with basic queries to verify
think parameter and streaming behavior.
"""

import asyncio
import aiohttp
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleConfigTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"

    async def test_simple_query(self):
        """Test simple query without tools"""

        payload = {
            "model": "deepseek-v3.1:671b-cloud",
            "prompt": "What is 5+7? Just give me the answer.",
            "stream": True,
            "toolsInUse": False,
            "searchWebInUse": False
        }

        logger.info("🧪 Testing Simple Query (No Tools)")
        logger.info("-" * 40)

        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/llama3_1b/stream", json=payload) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ HTTP {response.status}: {error_text}")
                        return False

                    content_parts = []
                    chunk_count = 0

                    async for line in response.content:
                        if line.strip():
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'response' in data and data['response']:
                                    content_parts.append(data['response'])
                                    chunk_count += 1
                                    if chunk_count <= 5:  # Show first few chunks
                                        logger.info(f"📝 Chunk {chunk_count}: {data['response'][:50]}...")
                            except json.JSONDecodeError:
                                continue

                    full_response = ''.join(content_parts)
                    duration = time.time() - start_time

                    # Analyze response
                    has_content = len(full_response.strip()) > 0
                    has_thinking = any(indicator in full_response.lower()
                                      for indicator in ['think', 'let me', 'i need to'])

                    logger.info(f"✅ Test completed successfully")
                    logger.info(f"📏 Response length: {len(full_response)} chars")
                    logger.info(f"⏱️ Duration: {duration:.2f}s")
                    logger.info(f"🧠 Contains thinking patterns: {has_thinking}")
                    logger.info(f"📊 Total chunks received: {chunk_count}")

                    if full_response:
                        sample = full_response[:100].replace('\n', ' ')
                        logger.info(f"📝 Sample response: {sample}...")

                    return True

        except Exception as e:
            logger.error(f"❌ Exception: {str(e)}")
            return False

    async def test_tool_query(self):
        """Test query with tool calling"""

        payload = {
            "model": "deepseek-v3.1:671b-cloud",
            "prompt": "What time is it in New York right now?",
            "stream": True,
            "toolsInUse": True,
            "searchWebInUse": True
        }

        logger.info("\n🔧 Testing Tool Calling Query")
        logger.info("-" * 40)

        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/llama3_1b/stream", json=payload) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ HTTP {response.status}: {error_text}")
                        return False

                    content_parts = []
                    chunk_count = 0
                    tool_calls_detected = False

                    async for line in response.content:
                        if line.strip():
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'response' in data and data['response']:
                                    content_parts.append(data['response'])
                                    chunk_count += 1

                                    # Check for tool call indicators
                                    if any(indicator in data['response'].lower()
                                           for indicator in ['tool', 'function', 'search', 'api']):
                                        tool_calls_detected = True

                                    if chunk_count <= 3:  # Show first few chunks
                                        logger.info(f"🔧 Chunk {chunk_count}: {data['response'][:50]}...")
                            except json.JSONDecodeError:
                                continue

                    full_response = ''.join(content_parts)
                    duration = time.time() - start_time

                    logger.info(f"✅ Tool test completed")
                    logger.info(f"📏 Response length: {len(full_response)} chars")
                    logger.info(f"⏱️ Duration: {duration:.2f}s")
                    logger.info(f"🔧 Tool calls detected: {tool_calls_detected}")
                    logger.info(f"📊 Total chunks received: {chunk_count}")

                    return True

        except Exception as e:
            logger.error(f"❌ Exception: {str(e)}")
            return False

    async def run_tests(self):
        """Run all configuration tests"""
        logger.info("🚀 Starting Simple Configuration Test")
        logger.info("=" * 50)

        # Test 1: Simple query
        simple_success = await self.test_simple_query()

        # Brief pause
        await asyncio.sleep(3)

        # Test 2: Tool calling
        tool_success = await self.test_tool_query()

        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Simple Query: {'✅ PASS' if simple_success else '❌ FAIL'}")
        logger.info(f"Tool Calling: {'✅ PASS' if tool_success else '❌ FAIL'}")

        if simple_success and tool_success:
            logger.info("🎉 All tests passed! Current configuration working properly.")
        else:
            logger.info("⚠️ Some tests failed. Check configuration.")

async def main():
    """Run simple configuration test"""
    tester = SimpleConfigTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())