#!/usr/bin/env python3
"""
Add LLM Abstraction Layer Endpoints

This script adds new endpoints to test the LLM abstraction layer
without modifying existing functionality.
"""

import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def add_llm_endpoints():
    """Add LLM abstraction endpoints to the server"""
    
    server_file = Path("fastapi_server_complete.py")
    if not server_file.exists():
        logger.error(f"Server file not found: {server_file}")
        return False
    
    logger.info("🔧 Adding LLM abstraction endpoints...")
    
    # Read current server file
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Create backup
    backup_file = server_file.with_suffix('.py.backup.llm')
    with open(backup_file, 'w') as f:
        f.write(content)
    logger.info(f"✅ Backup created: {backup_file}")
    
    # Check if already added
    if "from llm_providers.manager import llm_manager" in content:
        logger.info("⚠️ LLM abstraction endpoints already added")
        return True
    
    # Add imports
    import_addition = """
# LLM Abstraction Layer
from llm_providers.manager import llm_manager
from utils.config_loader import config_loader"""
    
    # Find imports section and add our imports
    if "import aiohttp" in content:
        content = content.replace(
            "import aiohttp",
            f"import aiohttp{import_addition}"
        )
        logger.info("✅ Added LLM abstraction imports")
    
    # Add startup initialization
    startup_code = """
    # Initialize LLM abstraction layer
    try:
        await llm_manager.initialize()
        logger.info("🤖 LLM Manager initialized successfully")
    except Exception as e:
        logger.error(f"❌ LLM Manager initialization failed: {e}")"""
    
    # Find startup section and add initialization
    if "logger.info(\"🚀 Server startup complete\")" in content:
        content = content.replace(
            "logger.info(\"🚀 Server startup complete\")",
            f"{startup_code}\n        logger.info(\"🚀 Server startup complete\")"
        )
        logger.info("✅ Added LLM manager initialization")
    
    # Add shutdown
    shutdown_code = """
    # Shutdown LLM abstraction layer
    try:
        await llm_manager.shutdown()
        logger.info("🛑 LLM Manager shutdown complete")
    except Exception as e:
        logger.error(f"❌ LLM Manager shutdown failed: {e}")"""
    
    if "cleanup_http_pool()" in content:
        content = content.replace(
            "cleanup_http_pool()",
            f"cleanup_http_pool(){shutdown_code}"
        )
        logger.info("✅ Added LLM manager shutdown")
    
    # Add new endpoints
    endpoints = '''
# LLM Abstraction Layer Endpoints
@app.get("/llm/config")
async def get_llm_config():
    """Get current LLM provider configuration"""
    try:
        if not llm_manager._initialized:
            await llm_manager.initialize()
            
        provider_info = llm_manager.get_provider_info()
        health = await llm_manager.health_check()
        
        return {
            "status": "success",
            "providers": provider_info.get("providers", {}),
            "health": health,
            "initialized": provider_info.get("initialized", False),
            "factory_info": provider_info.get("factory_info", {})
        }
    except Exception as e:
        logger.error(f"Failed to get LLM config: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/llm/health")
async def get_llm_health():
    """Get LLM provider health status"""
    try:
        if not llm_manager._initialized:
            await llm_manager.initialize()
            
        health = await llm_manager.health_check()
        return {
            "status": "success",
            "health": health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get LLM health: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/llm/test/stream")
async def test_llm_stream(request: dict):
    """Test LLM abstraction layer streaming"""
    try:
        if not llm_manager._initialized:
            await llm_manager.initialize()
            
        prompt = request.get("prompt", "Hello, world!")
        
        async def generate():
            try:
                async for chunk in llm_manager.generate_stream(prompt):
                    yield f"data: {json.dumps({'response': chunk})}\\n\\n"
                yield "data: [DONE]\\n\\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\\n\\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Failed to stream with LLM abstraction: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/llm/test/tools")
async def test_llm_tools(request: dict):
    """Test LLM abstraction layer tool calling"""
    try:
        if not llm_manager._initialized:
            await llm_manager.initialize()
            
        prompt = request.get("prompt", "What's the weather like?")
        tools = request.get("tools", [
            {
                "name": "get_weather",
                "description": "Get current weather information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        }
                    },
                    "required": ["location"]
                }
            }
        ])
        
        result = await llm_manager.generate_tools(prompt, tools)
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to call tools with LLM abstraction: {e}")
        return {"status": "error", "message": str(e)}
'''
    
    # Add endpoints before the main section
    if 'if __name__ == "__main__":' in content:
        content = content.replace(
            'if __name__ == "__main__":',
            f'{endpoints}\nif __name__ == "__main__":'
        )
        logger.info("✅ Added LLM abstraction test endpoints")
    
    # Write modified content
    with open(server_file, 'w') as f:
        f.write(content)
    
    logger.info("✅ LLM abstraction endpoints added!")
    return True

if __name__ == "__main__":
    success = add_llm_endpoints()
    if success:
        print("\n🎉 LLM abstraction endpoints added!")
        print("🔄 Restart the server to use the new endpoints")
        print("\n📋 Test endpoints:")
        print("  GET  /llm/config    - View provider configuration")
        print("  GET  /llm/health    - Check provider health")
        print("  POST /llm/test/stream - Test streaming with abstraction layer")
        print("  POST /llm/test/tools  - Test tool calling with abstraction layer")
    else:
        print("❌ Failed to add endpoints")