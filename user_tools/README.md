# User-Defined Tools for Agentic RAG System

This directory contains the user-defined tools system that allows you to extend the agentic RAG system with custom tools that the LLM can call.

## Overview

The user tools system automatically discovers and loads custom tools from Python files in this directory. These tools integrate seamlessly with the existing tool calling system and appear alongside built-in tools like `get_news_summaries`, `search_web`, etc.

## Quick Start

1. **Create a new tool** by copying `example_calculator.py` as a template
2. **Inherit from BaseUserTool** and implement the required methods
3. **Restart the server** - tools are loaded automatically at startup
4. **Test your tool** by asking the LLM to use it in a conversation

## Creating a Custom Tool

### 1. Basic Structure

```python
from typing import Dict, Any
try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool

class MyCustomTool(BaseUserTool):
    @property
    def name(self) -> str:
        return "my_custom_tool"  # Used as function name
    
    @property 
    def description(self) -> str:
        return "Description of what the tool does"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Parameter description"
                }
            },
            "required": ["param1"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        # Your tool logic here
        return {
            "success": True,
            "result": "Your result data",
            "error": None
        }
```

### 2. Parameter Schema

Use JSON Schema format to define parameters:

```python
{
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search query"},
        "limit": {"type": "integer", "description": "Max results", "default": 10},
        "enabled": {"type": "boolean", "description": "Enable feature"}
    },
    "required": ["query"]
}
```

### 3. Return Format

Always return a dict with this structure:

```python
{
    "success": bool,      # True if successful
    "result": Any,        # Your actual result data
    "error": str | None   # Error message if success=False
}
```

## Example Tools

### Calculator Tool (`example_calculator.py`)
Performs basic arithmetic operations. Shows parameter validation and error handling.

**Usage**: "Calculate 15 + 27 using the calculator"

### Ideas for Custom Tools

- **Database Query Tool**: Query your application database
- **File System Tool**: Read/write files, list directories  
- **API Integration Tool**: Call external APIs
- **Data Processing Tool**: Transform or analyze data
- **System Monitoring Tool**: Check system resources
- **Email/Notification Tool**: Send alerts or messages

## Tool Discovery

- Tools are discovered automatically at server startup
- Only `.py` files in this directory are scanned
- Files starting with `_` or named `base_user_tool.py`, `tool_discovery.py` are skipped
- Classes ending in "Tool" with required methods are loaded

## Integration with LLM

User tools appear in the LLM's function calling system alongside built-in tools:

1. **Tool Selection**: LLM decides which tool to use based on descriptions
2. **Parameter Extraction**: LLM extracts parameters from user input
3. **Tool Execution**: System calls your `execute()` method
4. **Result Integration**: Tool results are provided to LLM for response generation

## Testing

Test your tools independently:

```python
import asyncio
from user_tools import discover_user_tools

async def test():
    tools = await discover_user_tools()
    for tool in tools:
        if tool.name == "my_tool":
            result = await tool.execute(param1="test")
            print(result)

asyncio.run(test())
```

Or test through the server:

```bash
python testing/test_user_tools.py
```

## Best Practices

1. **Clear Descriptions**: Write clear, specific tool descriptions
2. **Parameter Validation**: Validate inputs in your `execute()` method
3. **Error Handling**: Return proper error messages, don't raise exceptions
4. **Async Methods**: All tool methods should be async
5. **JSON Serializable**: Return data that can be JSON serialized
6. **Documentation**: Comment your tool code for maintainability

## Troubleshooting

- **Tool not loading**: Check for syntax errors, ensure class ends with "Tool"
- **Import errors**: Use the try/except import pattern shown above
- **Validation errors**: Implement required properties: name, description, parameters, execute
- **Runtime errors**: Check server logs for detailed error messages

## Security Considerations

- User tools run with full server privileges
- Validate all inputs to prevent injection attacks
- Be careful with file system access or external API calls
- Consider implementing rate limiting for expensive operations

---

The user tools system extends the agentic RAG capabilities while maintaining the same interface and user experience as built-in tools.