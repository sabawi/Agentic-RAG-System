#!/usr/bin/env python3
"""
Weather Information Plugin
Retrieves current weather data using wttr.in service.
"""

import sys
import json
import asyncio
import subprocess
from typing import Dict, Any


async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get weather information for a city.

    Args:
        parameters: {
            "city": str,
            "units": "metric" | "imperial",
            "format": "brief" | "detailed"
        }

    Returns:
        {
            "success": bool,
            "result": str,
            "error": str | None,
            "metadata": dict
        }
    """
    city = parameters['city']
    units = parameters.get('units', 'metric')
    output_format = parameters.get('format', 'brief')

    try:
        # Determine wttr.in format code
        # Format: 1 = current weather, 2 = today + tomorrow, 3 = 3 days
        wttr_format = '1' if output_format == 'brief' else '2'

        # Build URL
        # wttr.in accepts: ?format=... for custom output
        # Using curl to fetch data
        url = f"wttr.in/{city}?format=%l:+%C+%t+%h+%w"

        if output_format == 'detailed':
            # Get more detailed ASCII art format
            url = f"wttr.in/{city}?{wttr_format}"

        # Use curl to fetch weather data
        result = subprocess.run(
            ['curl', '-s', '-m', '10', url],
            capture_output=True,
            text=True,
            timeout=12
        )

        if result.returncode != 0:
            return {
                "success": False,
                "result": None,
                "error": f"Failed to fetch weather data: {result.stderr}",
                "metadata": {
                    "city": city,
                    "units": units
                }
            }

        weather_data = result.stdout.strip()

        if not weather_data or "Unknown location" in weather_data:
            return {
                "success": False,
                "result": None,
                "error": f"City '{city}' not found. Please check the spelling.",
                "metadata": {
                    "city": city,
                    "units": units
                }
            }

        # Parse brief format: "Location: Conditions Temperature Humidity Wind"
        if output_format == 'brief':
            # Format the output nicely
            formatted = f"🌤️  Weather for {city}:\n\n{weather_data}"
        else:
            # Detailed format includes ASCII art
            formatted = weather_data

        return {
            "success": True,
            "result": formatted,
            "error": None,
            "metadata": {
                "city": city,
                "units": units,
                "format": output_format,
                "data_length": len(weather_data)
            }
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "result": None,
            "error": "Weather service request timed out. Please try again.",
            "metadata": {
                "city": city,
                "timeout": True
            }
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Unexpected error: {str(e)}",
            "metadata": {
                "city": city,
                "error_type": type(e).__name__
            }
        }


# Communication protocol (boilerplate)
if __name__ == "__main__":
    try:
        input_data = sys.stdin.read()
        parameters = json.loads(input_data)
        result = asyncio.run(execute(parameters))
        print(json.dumps(result))
        sys.exit(0 if result['success'] else 1)
    except Exception as e:
        error_result = {
            "success": False,
            "result": None,
            "error": f"Plugin error: {str(e)}",
            "metadata": {}
        }
        print(json.dumps(error_result))
        sys.exit(1)
