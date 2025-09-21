#!/usr/bin/env python3
"""
Debug qwen3:8b tool calling response format
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_qwen3_direct():
    """Test qwen3:8b tool calling directly via Ollama API"""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_news_summaries",
                "description": "Get recent news summaries about specific topics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for news"
                        },
                        "time_range": {
                            "type": "string",
                            "description": "Time range: recent, today, week, month"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    payload = {
        "model": "qwen3:8b",
        "messages": [{"role": "user", "content": "Search for recent news about AI developments"}],
        "tools": tools,
        "stream": False
    }

    logger.info("🧪 Testing qwen3:8b Direct Tool Calling")
    logger.info("=" * 60)
    logger.info(f"📡 Payload: {json.dumps(payload, indent=2)}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("http://127.0.0.1:11434/api/chat", json=payload) as response:

                logger.info(f"📡 Response status: {response.status}")

                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Error {response.status}: {error_text}")
                    return

                response_data = await response.json()

                logger.info("📝 Raw Response Structure:")
                logger.info(f"   Keys: {list(response_data.keys())}")

                if 'message' in response_data:
                    message = response_data['message']
                    logger.info(f"   Message keys: {list(message.keys())}")

                    if 'tool_calls' in message:
                        tool_calls = message['tool_calls']
                        logger.info(f"   Tool calls count: {len(tool_calls)}")

                        for i, tool_call in enumerate(tool_calls):
                            logger.info(f"   Tool Call {i+1}:")
                            logger.info(f"      Raw: {json.dumps(tool_call, indent=6)}")

                            if 'function' in tool_call:
                                func = tool_call['function']
                                logger.info(f"      Function name: {func.get('name', 'MISSING')}")
                                logger.info(f"      Arguments: {func.get('arguments', 'MISSING')}")

                    else:
                        logger.warning("❌ No tool_calls in message")

                    if 'content' in message:
                        content = message['content']
                        logger.info(f"   Content: {content[:100]}..." if len(content) > 100 else f"   Content: {content}")

                # Show full response for debugging
                logger.info(f"\n📋 Full Response JSON:")
                logger.info(json.dumps(response_data, indent=2))

    except Exception as e:
        logger.error(f"❌ Exception: {str(e)}")

async def main():
    """Run qwen3:8b format debug"""
    await test_qwen3_direct()

if __name__ == "__main__":
    asyncio.run(main())