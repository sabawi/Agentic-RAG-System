#!/usr/bin/env python3
"""
DeepSeek-R1 Tool Calling Test
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepSeekToolTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"

    async def test_tool_calling(self):
        """Test DeepSeek-R1 tool calling"""

        payload = {
            "model": "deepseek-r1:8b",
            "prompt": "What's the current weather in New York City? Please use available tools to get this information.",
            "stream": True,
            "toolsInUse": True,
            "searchWebInUse": True
        }

        logger.info("🧪 Testing DeepSeek-R1:8b Tool Calling")
        logger.info("-" * 50)
        logger.info(f"📡 Request payload: {json.dumps(payload, indent=2)}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/llama3_1b/stream", json=payload) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ HTTP {response.status}: {error_text}")
                        return False

                    content_parts = []
                    chunk_count = 0
                    tool_calls_found = False

                    async for line in response.content:
                        if line.strip():
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'response' in data and data['response']:
                                    content_parts.append(data['response'])
                                    chunk_count += 1

                                    # Look for tool calling indicators
                                    response_content = data['response'].lower()
                                    if any(indicator in response_content for indicator in [
                                        'tool_call', 'function_call', 'search', 'weather', 'api'
                                    ]):
                                        tool_calls_found = True
                                        logger.info(f"🔧 Tool call detected in chunk {chunk_count}: {data['response'][:100]}...")

                                    if chunk_count <= 5:  # Show first few chunks
                                        logger.info(f"📝 Chunk {chunk_count}: {data['response'][:80]}...")
                            except json.JSONDecodeError:
                                continue

                    full_response = ''.join(content_parts)

                    logger.info(f"✅ Test completed")
                    logger.info(f"📏 Response length: {len(full_response)} chars")
                    logger.info(f"📊 Total chunks: {chunk_count}")
                    logger.info(f"🔧 Tool calls detected: {tool_calls_found}")

                    # Show sample response
                    sample = full_response[:300].replace('\n', '\\n')
                    logger.info(f"📝 Sample response: {sample}...")

                    return tool_calls_found

        except Exception as e:
            logger.error(f"❌ Exception: {str(e)}")
            return False

    async def test_direct_ollama_tool_call(self):
        """Test direct Ollama API tool calling"""

        logger.info("\n🔧 Testing Direct Ollama Tool Calling")
        logger.info("-" * 50)

        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city name"
                        }
                    },
                    "required": ["location"]
                }
            }
        }]

        payload = {
            "model": "deepseek-r1:8b",
            "messages": [{"role": "user", "content": "What's the weather in New York?"}],
            "tools": tools,
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://127.0.0.1:11434/api/chat", json=payload) as response:

                    logger.info(f"📡 Response status: {response.status}")

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Direct Ollama error {response.status}: {error_text}")
                        return False

                    response_data = await response.json()

                    logger.info(f"📝 Response keys: {list(response_data.keys())}")

                    if 'message' in response_data:
                        message = response_data['message']
                        logger.info(f"📨 Message keys: {list(message.keys())}")

                        if 'tool_calls' in message:
                            tool_calls = message['tool_calls']
                            logger.info(f"🔧 Tool calls found: {len(tool_calls)}")
                            for i, tool_call in enumerate(tool_calls):
                                logger.info(f"   Tool {i+1}: {tool_call}")
                            return True
                        else:
                            logger.info("❌ No tool_calls in message")
                            if 'content' in message:
                                content_sample = message['content'][:200]
                                logger.info(f"📝 Content sample: {content_sample}")

                    return False

        except Exception as e:
            logger.error(f"❌ Direct Ollama test failed: {str(e)}")
            return False

async def main():
    """Run DeepSeek tool calling tests"""
    tester = DeepSeekToolTester()

    # Test 1: Through our server
    logger.info("🚀 Starting DeepSeek-R1 Tool Calling Tests")
    logger.info("=" * 60)

    server_success = await tester.test_tool_calling()

    # Brief pause
    await asyncio.sleep(2)

    # Test 2: Direct Ollama API
    direct_success = await tester.test_direct_ollama_tool_call()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Server Tool Calling: {'✅ WORKING' if server_success else '❌ NOT WORKING'}")
    logger.info(f"Direct Ollama API: {'✅ WORKING' if direct_success else '❌ NOT WORKING'}")

    if not direct_success:
        logger.warning("💡 DeepSeek-R1:8b may not support tool calling or needs specific configuration")
    elif not server_success and direct_success:
        logger.warning("💡 Server tool calling implementation may need DeepSeek-specific adjustments")

if __name__ == "__main__":
    asyncio.run(main())