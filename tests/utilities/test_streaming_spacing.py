#!/usr/bin/env python3
"""
Spacing Test - Test whitespace preservation in streaming
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpacingTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"

    async def test_spacing(self):
        """Test spacing preservation"""

        payload = {
            "model": "deepseek-v3.1:671b-cloud",
            "prompt": "What is the capital of Egypt? Give me a detailed answer with proper spacing.",
            "stream": True,
            "toolsInUse": False,
            "searchWebInUse": False
        }

        logger.info("🧪 Testing Spacing Preservation")
        logger.info("-" * 40)

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

                                    # Show chunk content with special chars visible
                                    chunk_repr = repr(data['response'])
                                    if chunk_count <= 10:  # Show first 10 chunks
                                        logger.info(f"📝 Chunk {chunk_count}: {chunk_repr}")
                            except json.JSONDecodeError:
                                continue

                    full_response = ''.join(content_parts)

                    # Analyze spacing issues
                    issues = []
                    if '.Cairo' in full_response or '.Alexandria' in full_response:
                        issues.append("Missing space after period")
                    if 'CE.' in full_response and 'CE.It' in full_response:
                        issues.append("Missing space after sentence")
                    if '972CE' in full_response or '1050years' in full_response:
                        issues.append("Missing space between number and text")

                    logger.info(f"✅ Test completed")
                    logger.info(f"📏 Response length: {len(full_response)} chars")
                    logger.info(f"📊 Total chunks: {chunk_count}")
                    logger.info(f"⚠️ Spacing issues found: {len(issues)}")

                    if issues:
                        for issue in issues:
                            logger.warning(f"   - {issue}")
                    else:
                        logger.info("🎉 No spacing issues detected!")

                    # Show sample
                    sample = full_response[:200].replace('\n', '\\n').replace('\t', '\\t')
                    logger.info(f"📝 Sample (200 chars): {sample}")

                    return len(issues) == 0

        except Exception as e:
            logger.error(f"❌ Exception: {str(e)}")
            return False

async def main():
    """Run spacing test"""
    tester = SpacingTester()
    success = await tester.test_spacing()

    if success:
        logger.info("🎉 Spacing test PASSED!")
    else:
        logger.info("❌ Spacing test FAILED!")

if __name__ == "__main__":
    asyncio.run(main())