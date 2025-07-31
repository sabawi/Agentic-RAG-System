"""
Example user-defined tool: Simple Calculator
Demonstrates how to create a custom tool for the agentic RAG system.
"""

from typing import Dict, Any
try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool


class CalculatorTool(BaseUserTool):
    """
    A simple calculator tool that can perform basic arithmetic operations.
    """
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Perform basic arithmetic calculations (addition, subtraction, multiplication, division). Useful for mathematical computations."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The arithmetic operation to perform",
                    "enum": ["add", "subtract", "multiply", "divide"]
                },
                "a": {
                    "type": "number",
                    "description": "First number"
                },
                "b": {
                    "type": "number",
                    "description": "Second number"
                }
            },
            "required": ["operation", "a", "b"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the calculator operation.
        """
        try:
            operation = kwargs.get("operation")
            a_raw = kwargs.get("a")
            b_raw = kwargs.get("b")
            
            # Convert string inputs to numbers
            try:
                a = float(a_raw) if isinstance(a_raw, str) else a_raw
                b = float(b_raw) if isinstance(b_raw, str) else b_raw
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "error": f"Invalid number format: a='{a_raw}', b='{b_raw}'",
                    "result": None
                }
            
            # Validate operation
            if operation not in ["add", "subtract", "multiply", "divide"]:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}",
                    "result": None
                }
            
            # Perform the calculation
            result = None
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return {
                        "success": False,
                        "error": "Division by zero is not allowed",
                        "result": None
                    }
                result = a / b
            
            return {
                "success": True,
                "result": {
                    "operation": operation,
                    "operands": [a, b],
                    "result": result,
                    "expression": f"{a} {self._get_operator_symbol(operation)} {b} = {result}",
                    "answer": result,
                    "calculation_verified": f"VERIFIED: {a} {self._get_operator_symbol(operation)} {b} equals exactly {result}"
                },
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Calculation error: {str(e)}",
                "result": None
            }
    
    def _get_operator_symbol(self, operation: str) -> str:
        """Get the mathematical symbol for an operation."""
        symbols = {
            "add": "+",
            "subtract": "-",
            "multiply": "*",
            "divide": "/"
        }
        return symbols.get(operation, "?")