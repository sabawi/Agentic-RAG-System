#!/usr/bin/env python3
"""
Compare tool calling response formats between providers
"""

import asyncio
import json
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_providers.factory import LLMProviderFactory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_provider_formats():
    """Test tool calling response formats from different providers"""

    tools = [
        {
            "name": "get_news_summaries",
            "description": "Get recent news summaries",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "time_range": {"type": "string", "description": "Time range"}
                },
                "required": ["query"]
            }
        }
    ]

    # Test providers and their configs
    providers_to_test = [
        {
            "name": "OpenAI",
            "type": "openai",
            "config": {
                "model": "gpt-4o-mini",
                "timeout": 60,
                "max_tokens": 1024,
                "temperature": 0.1,
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": "https://api.openai.com/v1"
            }
        },
        {
            "name": "Ollama (qwen3:8b)",
            "type": "ollama",
            "config": {
                "model": "deepseek-v3.1:671b-cloud",
                "timeout": 300,
                "max_tokens": 1024,
                "temperature": 0.1,
                "base_url": "http://127.0.0.1:11434",
                "api_key": None
            }
        }
    ]

    logger.info("🧪 Comparing Tool Calling Response Formats")
    logger.info("=" * 60)

    for provider_info in providers_to_test:
        name = provider_info["name"]
        provider_type = provider_info["type"]
        config = provider_info["config"]

        logger.info(f"\n🔧 Testing {name} ({provider_type})")
        logger.info("-" * 40)

        try:
            # Create provider
            factory = LLMProviderFactory()
            provider = factory.create_provider(provider_type, config)

            # Test tool calling
            prompt = "Search for recent AI news"
            model = config["model"]

            logger.info(f"📡 Calling {name} with prompt: '{prompt}'")

            result = await provider.generate_tools(prompt, model, tools)

            logger.info(f"✅ {name} Response Structure:")
            logger.info(f"   Keys: {list(result.keys())}")
            logger.info(f"   Tool calls count: {len(result.get('tool_calls', []))}")

            tool_calls = result.get('tool_calls', [])
            if tool_calls:
                for i, tool_call in enumerate(tool_calls):
                    logger.info(f"   Tool Call {i+1}:")
                    logger.info(f"      Structure: {list(tool_call.keys())}")

                    if 'function' in tool_call:
                        func = tool_call['function']
                        logger.info(f"      Function name: {func.get('name', 'MISSING')}")
                        logger.info(f"      Function args keys: {list(func.get('arguments', {}).keys())}")
                    else:
                        logger.info(f"      ❌ NO 'function' key found!")
                        logger.info(f"      Raw tool call: {json.dumps(tool_call, indent=8)}")
            else:
                logger.warning(f"   ❌ No tool calls returned by {name}")
                logger.info(f"   Content: {result.get('content', 'NO CONTENT')[:100]}...")

            # Show full response for debugging
            logger.info(f"   Full Response:")
            logger.info(f"   {json.dumps(result, indent=4)}")

        except Exception as e:
            logger.error(f"❌ {name} failed: {str(e)}")

    logger.info(f"\n🔍 Key Insight:")
    logger.info(f"Both providers should return the same format:")
    logger.info(f"{{")
    logger.info(f"  'tool_calls': [{{")
    logger.info(f"    'function': {{")
    logger.info(f"      'name': 'function_name',")
    logger.info(f"      'arguments': {{...}}")
    logger.info(f"    }}")
    logger.info(f"  }}],")
    logger.info(f"  'content': '...',")
    logger.info(f"  'model': '...'")
    logger.info(f"}}")

async def main():
    """Run provider comparison test"""
    await test_provider_formats()

if __name__ == "__main__":
    asyncio.run(main())