#!/usr/bin/env python3
"""
Quick Fix: Replace direct Ollama calls with LLM abstraction layer
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def fix_model_selection():
    """Fix the server to use LLM abstraction layer instead of direct Ollama calls"""
    
    server_file = Path("fastapi_server_complete.py")
    if not server_file.exists():
        logger.error(f"Server file not found: {server_file}")
        return False
    
    logger.info("🔧 Fixing model selection and integrating LLM abstraction...")
    
    # Read current server file
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Create backup
    backup_file = server_file.with_suffix('.py.backup.fix')
    with open(backup_file, 'w') as f:
        f.write(content)
    logger.info(f"✅ Backup created: {backup_file}")
    
    # Fix 1: Replace tool calling direct Ollama call with LLM manager
    old_tool_call = """async with session.post(ServerConfig.OLLAMA_CHAT_URL, json=tool_payload, timeout=tool_timeout) as tool_response:"""
    
    new_tool_call = """# Use LLM abstraction layer for tool calling
                    try:
                        tool_result = await llm_manager.generate_tools(
                            prompt=user_prompt,
                            tools=tools_payload,
                            model=tools_model,
                            timeout=300
                        )
                        # Convert to expected format
                        tool_response_data = {
                            "message": {
                                "role": "assistant",
                                "content": tool_result.get("content", ""),
                                "tool_calls": tool_result.get("tool_calls", [])
                            }
                        }
                        # Simulate successful response
                        class MockToolResponse:
                            status = 200
                            async def json(self): return tool_response_data
                        tool_response = MockToolResponse()
                        async with tool_response as tool_response:"""
    
    if old_tool_call in content:
        content = content.replace(old_tool_call, new_tool_call)
        logger.info("✅ Replaced tool calling with LLM abstraction")
    
    # Fix 2: Replace primary LLM streaming call with LLM manager
    old_primary_call = """async with session.post(ServerConfig.OLLAMA_URL, json=stream_payload, timeout=None) as response:"""
    
    new_primary_call = """# Use LLM abstraction layer for primary LLM streaming
                try:
                    # Stream from LLM manager
                    complete_llm_response = ""
                    async for chunk in llm_manager.generate_stream(
                        prompt=in_prompt,
                        model=model,  # This should be the primary model (llama3.2:3b)
                        temperature=0.7,
                        max_tokens=4096
                    ):
                        complete_llm_response += chunk
                        yield f"data: {json.dumps({'response': chunk})}\\n\\n"
                    
                    # Simulate the successful response handling
                    class MockPrimaryResponse:
                        status = 200
                    response = MockPrimaryResponse()
                    async with response as response:"""
    
    if old_primary_call in content:
        content = content.replace(old_primary_call, new_primary_call)
        logger.info("✅ Replaced primary LLM with LLM abstraction")
    else:
        logger.info("⚠️ Primary LLM call pattern not found - manual integration needed")
    
    # Fix 3: Ensure proper model variable usage
    # Replace any remaining direct model references
    content = content.replace(
        'model = data.get(\'model\', ServerConfig.DEFAULT_MODEL)',
        '''# Get models from LLM abstraction layer configuration
        llm_config = config_loader.get_llm_config('primary')
        primary_model = llm_config.get('config', {}).get('model', ServerConfig.DEFAULT_MODEL)
        
        # Override with request model if provided, otherwise use configured primary model
        model = data.get('model', primary_model)'''
    )
    
    # Write modified content
    with open(server_file, 'w') as f:
        f.write(content)
    
    logger.info("✅ Model selection fixes applied!")
    return True

if __name__ == "__main__":
    success = fix_model_selection()
    if success:
        print("\n🎉 Quick fix applied!")
        print("🔄 Restart the server to use LLM abstraction layer")
        print("📋 The server will now use:")
        print("   - Primary LLM: llama3.2:3b (from config)")
        print("   - Tool LLM: qwen3:8b (from config)")
    else:
        print("❌ Fix failed")