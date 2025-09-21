#!/usr/bin/env python3
"""
Test Tool Calling Support for Local Models
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelToolSupportTester:
    def __init__(self):
        # Models to test - focus on smaller, newer models that likely support tools
        self.models_to_test = [
            "mistral:7b",         # Mistral models often support tools
            "qwen3:4b",           # Qwen3 series should support tools
            "qwen3:8b",           # Qwen3 series should support tools
            "llama3.2:3b",        # Llama 3.2 might support tools
            "gemma3:4b",          # Gemma3 might support tools
            "qwen2.5-coder:7b",   # Qwen 2.5 coder might support tools
        ]

    async def test_model_tool_support(self, model_name: str) -> bool:
        """Test if a model supports tool calling"""

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
            "model": model_name,
            "messages": [{"role": "user", "content": "What's the weather in Paris?"}],
            "tools": tools,
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("http://127.0.0.1:11434/api/chat", json=payload) as response:

                    if response.status == 200:
                        response_data = await response.json()

                        if 'message' in response_data and 'tool_calls' in response_data['message']:
                            tool_calls = response_data['message']['tool_calls']
                            if tool_calls:
                                logger.info(f"✅ {model_name}: SUPPORTS TOOLS ({len(tool_calls)} tool calls)")
                                return True
                            else:
                                logger.info(f"⚠️  {model_name}: Tool calls field exists but empty")
                                return False
                        else:
                            logger.info(f"❌ {model_name}: No tool_calls in response")
                            return False
                    else:
                        error_text = await response.text()
                        if "does not support tools" in error_text:
                            logger.info(f"❌ {model_name}: Explicitly does not support tools")
                        else:
                            logger.info(f"❌ {model_name}: Error {response.status}: {error_text[:100]}")
                        return False

        except Exception as e:
            logger.error(f"❌ {model_name}: Exception - {str(e)}")
            return False

    async def run_all_tests(self):
        """Test all models for tool support"""
        logger.info("🔧 Testing Local Model Tool Calling Support")
        logger.info("=" * 60)

        supported_models = []

        for model in self.models_to_test:
            logger.info(f"\n🧪 Testing {model}...")

            try:
                if await self.test_model_tool_support(model):
                    supported_models.append(model)

            except Exception as e:
                logger.error(f"❌ {model}: Test failed - {str(e)}")

            # Brief pause between tests
            await asyncio.sleep(1)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TOOL CALLING SUPPORT SUMMARY")
        logger.info("=" * 60)

        if supported_models:
            logger.info(f"✅ Models with tool calling support ({len(supported_models)}):")
            for model in supported_models:
                logger.info(f"   • {model}")

            # Recommend the smallest one
            smallest = min(supported_models, key=lambda x: self.get_model_size_estimate(x))
            logger.info(f"\n🎯 RECOMMENDED: {smallest} (smallest with tool support)")

        else:
            logger.warning("❌ No models found with native tool calling support")
            logger.info("💡 Consider downloading a model that supports tools:")
            logger.info("   • ollama pull qwen2.5:7b")
            logger.info("   • ollama pull mistral:7b-instruct")
            logger.info("   • ollama pull llama3.3:70b-instruct")

        return supported_models

    def get_model_size_estimate(self, model_name: str) -> int:
        """Estimate model size for sorting (smaller is better)"""
        if "1b" in model_name:
            return 1
        elif "3b" in model_name:
            return 3
        elif "4b" in model_name:
            return 4
        elif "7b" in model_name:
            return 7
        elif "8b" in model_name:
            return 8
        else:
            return 10  # Default for unknown sizes

async def main():
    """Run model tool support tests"""
    tester = ModelToolSupportTester()
    supported = await tester.run_all_tests()

    if supported:
        logger.info(f"\n🚀 Ready to configure tool calling with: {supported[0]}")
    else:
        logger.info(f"\n💡 Consider pulling a tool-capable model for testing")

if __name__ == "__main__":
    asyncio.run(main())