#!/usr/bin/env python3
"""
Fortune Message Plugin Handler
Complies with Plugin System v1.0.0

This plugin calls the Linux 'fortune' command to generate random
funny, inspirational, or philosophical messages.

Author: Agentic-RAG System
Created: 2025-10-02
Version: 1.0.0
"""

import sys
import json
import subprocess
import os
from typing import Dict, Any


def format_message_boxed(message: str) -> str:
    """Format message in a decorative box"""
    lines = message.strip().split('\n')
    max_length = max(len(line) for line in lines)

    # Create box
    top_border = "╔" + "═" * (max_length + 2) + "╗"
    bottom_border = "╚" + "═" * (max_length + 2) + "╝"

    formatted_lines = [top_border]
    for line in lines:
        padded_line = line + " " * (max_length - len(line))
        formatted_lines.append(f"║ {padded_line} ║")
    formatted_lines.append(bottom_border)

    return "\n".join(formatted_lines)


def format_message_quoted(message: str) -> str:
    """Format message with quotation marks"""
    return f'"{message.strip()}"\n\n— Fortune Cookie 🥠'


def format_message_plain(message: str) -> str:
    """Plain formatting with just a separator"""
    return f"{message.strip()}\n\n{'─' * 50}"


async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plugin entrypoint function.

    Args:
        parameters: Validated input parameters from plugin definition schema
            - category: Optional fortune category ("any", "short", "long", "offensive")
            - format_style: Output formatting ("plain", "boxed", "quoted")

    Returns:
        Dict with structure:
        {
            "success": bool,
            "result": str (formatted fortune message),
            "error": str | None,
            "metadata": {
                "category": str,
                "format_style": str,
                "message_length": int
            }
        }
    """
    try:
        # Get parameters with defaults
        category = parameters.get('category', 'any')
        format_style = parameters.get('format_style', 'boxed')

        # Get fortune command path from environment or default
        fortune_path = os.getenv('FORTUNE_PATH', '/usr/games/fortune')

        # Check if fortune command exists
        if not os.path.exists(fortune_path):
            return {
                "success": False,
                "result": None,
                "error": f"Fortune command not found at {fortune_path}. Please install fortune-mod package.",
                "metadata": {
                    "category": category,
                    "format_style": format_style
                }
            }

        # Build fortune command based on category
        cmd = [fortune_path]
        if category == "short":
            cmd.append("-s")  # Short messages only
        elif category == "long":
            cmd.append("-l")  # Long messages only
        elif category == "offensive":
            cmd.append("-o")  # Offensive fortunes (if available)
        # "any" = no flags (default behavior)

        # Execute fortune command with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5  # 5 second timeout
        )

        if result.returncode != 0:
            return {
                "success": False,
                "result": None,
                "error": f"Fortune command failed: {result.stderr.strip()}",
                "metadata": {
                    "category": category,
                    "format_style": format_style
                }
            }

        # Get the fortune message
        message = result.stdout.strip()

        if not message:
            return {
                "success": False,
                "result": None,
                "error": "Fortune command returned empty message",
                "metadata": {
                    "category": category,
                    "format_style": format_style
                }
            }

        # Format the message based on style
        if format_style == "boxed":
            formatted_message = format_message_boxed(message)
        elif format_style == "quoted":
            formatted_message = format_message_quoted(message)
        else:  # plain
            formatted_message = format_message_plain(message)

        return {
            "success": True,
            "result": formatted_message,
            "error": None,
            "metadata": {
                "category": category,
                "format_style": format_style,
                "message_length": len(message),
                "raw_message": message
            }
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "result": None,
            "error": "Fortune command timed out after 5 seconds",
            "metadata": {
                "category": parameters.get('category', 'any'),
                "format_style": parameters.get('format_style', 'boxed')
            }
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Plugin execution failed: {str(e)}",
            "metadata": {
                "category": parameters.get('category', 'any'),
                "format_style": parameters.get('format_style', 'boxed')
            }
        }


# =============================================================================
# Plugin System Communication Protocol
# =============================================================================
# This section handles stdin/stdout JSON communication with the plugin system.
# DO NOT MODIFY unless you understand the plugin communication protocol.
# =============================================================================

if __name__ == "__main__":
    try:
        # Read parameters from stdin (JSON)
        input_data = sys.stdin.read()

        if not input_data:
            result = {
                "success": False,
                "result": None,
                "error": "No input data received from plugin system"
            }
        else:
            try:
                parameters = json.loads(input_data)
            except json.JSONDecodeError as e:
                result = {
                    "success": False,
                    "result": None,
                    "error": f"Invalid JSON input: {str(e)}"
                }
                print(json.dumps(result))
                sys.exit(1)

            # Execute plugin (note: using sync wrapper since subprocess is blocking)
            import asyncio
            result = asyncio.run(execute(parameters))

        # Write result to stdout (JSON)
        print(json.dumps(result))

        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)

    except Exception as e:
        # Catastrophic error - return error JSON
        error_result = {
            "success": False,
            "result": None,
            "error": f"Plugin handler crashed: {str(e)}"
        }
        print(json.dumps(error_result))
        sys.exit(1)
