"""
Base class for user-defined tools in the agentic RAG system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json


class BaseUserTool(ABC):
    """
    Base class for all user-defined tools.
    
    User tools must inherit from this class and implement the required methods.
    """
    
    def __init__(self):
        """Initialize the user tool."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the tool.
        This will be used as the function name in the LLM prompt.
        Must be a valid Python identifier.
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Return a description of what the tool does.
        This will be included in the LLM prompt to help it understand when to use the tool.
        """
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        Return the JSON schema for tool parameters.
        
        Example:
        {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 10
                }
            },
            "required": ["query"]
        }
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.
        
        Args:
            **kwargs: Parameters as defined in the parameters schema
            
        Returns:
            Dict containing the tool's response. Should include:
            - success: bool indicating if execution was successful
            - result: The actual result data
            - error: Error message if success is False
        """
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Optional[str]:
        """
        Validate parameters against the schema.
        
        Args:
            parameters: The parameters to validate
            
        Returns:
            None if valid, error message string if invalid
        """
        schema = self.parameters
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for field in required_fields:
            if field not in parameters:
                return f"Missing required parameter: {field}"
        
        # Basic type checking
        for param_name, param_value in parameters.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                if expected_type == "string" and not isinstance(param_value, str):
                    return f"Parameter '{param_name}' must be a string"
                elif expected_type == "integer" and not isinstance(param_value, int):
                    return f"Parameter '{param_name}' must be an integer"
                elif expected_type == "boolean" and not isinstance(param_value, bool):
                    return f"Parameter '{param_name}' must be a boolean"
                elif expected_type == "array" and not isinstance(param_value, list):
                    return f"Parameter '{param_name}' must be an array"
        
        return None
    
    def get_function_definition(self) -> Dict[str, Any]:
        """
        Get the function definition for the LLM prompt.
        
        Returns:
            Dict in the format expected by the LLM function calling system
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    def __str__(self) -> str:
        """String representation of the tool."""
        return f"UserTool(name='{self.name}', description='{self.description[:50]}...')"