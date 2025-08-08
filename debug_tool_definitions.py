#!/usr/bin/env python3
"""
Debug tool definitions to see what the tool calling model actually receives
"""

import asyncio
import sys
import os
import json

# Add the server directory to Python path  
sys.path.append('/home/sabawi/Development/flaskserver')

from fastapi_server_complete import AsyncToolManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_tool_definitions():
    """Debug what tools definitions are actually sent to the tool calling model"""
    
    print("🔍 TOOL DEFINITIONS DEBUG")
    print("=" * 60)
    
    # Create tool manager like in the server
    tool_manager = AsyncToolManager()
    
    # Get tools definitions like the server does
    tools_array = await tool_manager.get_tools_definitions(exclude_file_email_tools=False)
    
    print(f"Total tools: {len(tools_array)}")
    
    # Find wikipedia_query tool definition
    wikipedia_found = False
    
    for i, tool in enumerate(tools_array):
        tool_name = tool.get('function', {}).get('name', 'unknown')
        
        if tool_name == 'wikipedia_query':
            wikipedia_found = True
            print(f"\n📚 WIKIPEDIA_QUERY TOOL DEFINITION:")
            print(f"Name: {tool_name}")
            print(f"Description: {tool.get('function', {}).get('description', 'No description')}")
            print(f"Parameters: {json.dumps(tool.get('function', {}).get('parameters', {}), indent=2)}")
    
    print(f"\n🔍 SEARCH RESULTS:")
    print(f"wikipedia_query found: {wikipedia_found}")
    
    if not wikipedia_found:
        print(f"\n❌ wikipedia_query not found! Available tools:")
        for tool in tools_array:
            tool_name = tool.get('function', {}).get('name', 'unknown')
            print(f"  - {tool_name}")
    else:
        print(f"\n✅ wikipedia_query tool found in definitions")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(debug_tool_definitions())