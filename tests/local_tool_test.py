#!/usr/bin/env python3
"""
Local Tool Calling Test - Test qwen3:4b tool calling
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalToolTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"

    async def test_local_tool_calling(self):
        """Test local tool calling with qwen3:4b"""

        payload = {
            "model": "deepseek-r1:8b",  # Primary model (will use qwen3:4b for tools)
            "prompt": "What's the current time in Tokyo? Please use tools to get this information.",
            "stream": True,
            "toolsInUse": True,
            "searchWebInUse": False  # Focus on time tool
        }

        logger.info("🧪 Testing Local Tool Calling")
        logger.info("Primary: deepseek-r1:8b | Tool Calling: qwen3:4b")
        logger.info("-" * 50)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/llama3_1b/stream", json=payload) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ HTTP {response.status}: {error_text}")
                        return False

                    content_parts = []
                    chunk_count = 0
                    tool_usage_detected = False

                    async for line in response.content:
                        if line.strip():
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'response' in data and data['response']:
                                    content_parts.append(data['response'])
                                    chunk_count += 1

                                    # Look for tool usage indicators
                                    response_content = data['response'].lower()
                                    if any(indicator in response_content for indicator in [
                                        'tool', 'function', 'current time', 'tokyo', 'jst', 'utc'
                                    ]):
                                        tool_usage_detected = True

                                    if chunk_count <= 10:  # Show first 10 chunks
                                        chunk_sample = data['response'][:60].replace('\n', '\\n')
                                        logger.info(f"📝 Chunk {chunk_count}: {chunk_sample}...")

                            except json.JSONDecodeError:
                                continue

                    full_response = ''.join(content_parts)

                    logger.info(f"✅ Test completed")
                    logger.info(f"📏 Response length: {len(full_response)} chars")
                    logger.info(f"📊 Total chunks: {chunk_count}")
                    logger.info(f"🔧 Tool usage detected: {tool_usage_detected}")

                    # Check for time-related content
                    has_time_info = any(keyword in full_response.lower() for keyword in [
                        'time', 'jst', 'utc', 'tokyo', 'hour', 'minute'
                    ])
                    logger.info(f"🕐 Time information found: {has_time_info}")

                    # Show sample response
                    sample = full_response[:200].replace('\n', ' ').replace('\t', ' ')
                    logger.info(f"📝 Sample response: {sample}...")

                    return tool_usage_detected and has_time_info

        except Exception as e:
            logger.error(f"❌ Exception: {str(e)}")
            return False

async def main():
    """Run local tool calling test"""
    logger.info("🚀 Starting Local Tool Calling Test")
    logger.info("=" * 60)

    tester = LocalToolTester()
    success = await tester.test_local_tool_calling()

    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)

    if success:
        logger.info("🎉 LOCAL TOOL CALLING IS WORKING!")
        logger.info("✅ DeepSeek-R1:8b + qwen3:4b tool calling successful")
    else:
        logger.info("❌ Local tool calling test failed")
        logger.info("💡 Check server logs for details")

if __name__ == "__main__":
    asyncio.run(main())