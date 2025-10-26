#!/usr/bin/env python3
"""
Test qwen3:8b tool calling with different types of queries
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Qwen3ToolDebugger:
    def __init__(self):
        self.base_url = "http://localhost:5000"

    async def test_query(self, prompt: str, description: str):
        """Test a specific query type"""

        payload = {
            "model": "deepseek-v3.1:671b-cloud",
            "prompt": prompt,
            "stream": True,
            "toolsInUse": True,
            "searchWebInUse": True
        }

        logger.info(f"🧪 Testing: {description}")
        logger.info(f"📝 Prompt: {prompt}")
        logger.info("-" * 60)

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

                                    if chunk_count <= 3:  # Show first few chunks
                                        chunk_sample = data['response'][:50].replace('\n', '\\n')
                                        logger.info(f"📝 Chunk {chunk_count}: {chunk_sample}...")

                                if chunk_count > 100:  # Prevent runaway
                                    break

                            except json.JSONDecodeError:
                                continue

                    full_response = ''.join(content_parts)

                    logger.info(f"✅ Response received")
                    logger.info(f"📏 Length: {len(full_response)} chars")
                    logger.info(f"📊 Chunks: {chunk_count}")

                    # Check for tool usage indicators
                    has_tool_usage = any(indicator in full_response.lower() for indicator in [
                        'search', 'tool', 'function', 'api', 'data', 'result'
                    ])
                    logger.info(f"🔧 Tool usage detected: {has_tool_usage}")

                    # Show sample
                    sample = full_response[:150].replace('\n', ' ')
                    logger.info(f"📝 Sample: {sample}...")
                    logger.info("")

                    return has_tool_usage

        except Exception as e:
            logger.error(f"❌ Exception: {str(e)}")
            return False

async def main():
    """Test different query types"""
    logger.info("🚀 Starting qwen3:8b Tool Calling Debug Tests")
    logger.info("=" * 80)

    debugger = Qwen3ToolDebugger()

    # Test cases - from simple factual to complex research
    test_cases = [
        ("What is the capital of France?", "Simple factual question"),
        ("What's the current weather in Tokyo?", "Current data request"),
        ("Search for recent news about AI developments", "Explicit search request"),
        ("Find information about quantum computing breakthroughs in 2024", "Research query"),
        ("Calculate 15 * 23 + 47", "Calculation request"),
    ]

    results = {}

    for prompt, description in test_cases:
        try:
            result = await debugger.test_query(prompt, description)
            results[description] = result

            # Brief pause between tests
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ Test failed for '{description}': {e}")
            results[description] = False

    # Summary
    logger.info("=" * 80)
    logger.info("📊 TOOL CALLING TEST RESULTS")
    logger.info("=" * 80)

    success_count = 0
    for description, success in results.items():
        status = "✅ USED TOOLS" if success else "❌ NO TOOLS"
        logger.info(f"{status}: {description}")
        if success:
            success_count += 1

    logger.info(f"\n🎯 Summary: {success_count}/{len(test_cases)} tests used tools")

    if success_count == 0:
        logger.warning("💡 No tools were used in any test - system prompt may be too restrictive")
    elif success_count < len(test_cases):
        logger.info("💡 Partial tool usage - model is selective about when to use tools")
    else:
        logger.info("🎉 All tests used tools - tool calling working correctly!")

if __name__ == "__main__":
    asyncio.run(main())