#!/usr/bin/env python3
"""
Analytical Visualizer Tool
Generates plots, charts, and tables based on user prompts for enhanced analytical responses
"""

import os
import re
import json
import asyncio
import tempfile
import subprocess
import base64
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import aiohttp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticalVisualizerTool:
    """
    Intelligent visualization generator that creates relevant charts and plots
    based on user prompts to enhance analytical explanations
    """
    
    def __init__(self):
        self.name = "analytical_visualizer"
        self.description = "Generate analytical visualizations (plots, charts, tables) based on user prompts using LLM-driven code generation"
        self.working_dir = "/home/sabawi/Development/flaskserver/sandbox_workspace"
        self.visualization_llm_config = self._load_visualization_llm_config()
    
    def _load_visualization_llm_config(self) -> Dict[str, Any]:
        """
        Load visualization LLM configuration using the same pattern as arbitrator
        """
        config_path = Path("/home/sabawi/Development/flaskserver/config/llm_config.yaml")
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # Check if arbitrator config exists - use it as template for visualization
                if 'arbitrator' in config and config['arbitrator'].get('enabled', False):
                    arbitrator_config = config['arbitrator']
                    
                    # Create visualization config based on arbitrator settings
                    return {
                        'enabled': True,
                        'type': arbitrator_config['type'],
                        'config': arbitrator_config['config'].copy()
                    }
                else:
                    # Fallback to default OpenAI GPT-4o-mini config
                    return {
                        'enabled': True,
                        'type': 'openai',
                        'config': {
                            'model': 'gpt-4o-mini',
                            'timeout': 60,
                            'context_window_size': 4096,
                            'temperature': 0.1,
                            'max_tokens': 1024,
                            'stream': False,
                            'api_key': '${OPENAI_API_KEY}',
                            'base_url': 'https://api.openai.com/v1'
                        }
                    }
            else:
                logger.warning("⚠️ Configuration file not found, using default OpenAI setup")
                return {
                    'enabled': True,
                    'type': 'openai',
                    'config': {
                        'model': 'gpt-4o-mini',
                        'timeout': 60,
                        'context_window_size': 4096,
                        'temperature': 0.1,
                        'max_tokens': 1024,
                        'stream': False,
                        'api_key': '${OPENAI_API_KEY}',
                        'base_url': 'https://api.openai.com/v1'
                    }
                }
        except Exception as e:
            logger.error(f"❌ Error loading visualization LLM config: {e}")
            # Return safe fallback config
            return {
                'enabled': False,
                'type': 'ollama',
                'config': {
                    'model': 'qwen2.5:14b',
                    'base_url': 'http://127.0.0.1:11434'
                }
            }

    async def _generate_visualization_code_with_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Use LLM to generate complete Python matplotlib code for any visualization request
        """
        system_prompt = """You are an expert Python data visualization specialist with deep knowledge of matplotlib, scientific computing, and domain expertise across physics, chemistry, biology, economics, mathematics, and engineering.

Your task: Generate complete, executable Python code using matplotlib to create the most appropriate visualization for the user's request.

IMPORTANT REQUIREMENTS:
1. Generate complete, runnable Python code - no placeholders, no "..." shortcuts
2. Use realistic data that demonstrates the concept effectively
3. Include proper scientific/mathematical relationships when relevant
4. Create professional-looking plots with proper labels, titles, legends, and formatting
5. For scientific topics, use correct equations and realistic parameters
6. CRITICAL: You must save the plot to the full working directory path and output success markers
7. **MODIFICATION REQUESTS**: If the request mentions modifying existing plots (e.g., "make it go up to 6%", "superimpose", "add"), interpret the full intent and create a comprehensive new plot

SCIENTIFIC EXPERTISE:
- Physics: Use correct equations for radioactive decay, wave functions, thermodynamics, etc.
- Chemistry: Show molecular structures, reaction kinetics, phase diagrams appropriately  
- Biology: Display growth curves, population dynamics, genetic data correctly
- Economics: Model supply/demand, market equilibrium, economic indicators accurately (YIELD CURVES: use realistic maturity periods 3M, 6M, 1Y, 2Y, 5Y, 10Y, 30Y)
- Mathematics: Plot functions, derivatives, statistical distributions properly

YIELD CURVE SPECIFICATIONS:
- Normal curve: Short rates < Long rates (e.g., 3M: 2.5%, 30Y: 4.5%)
- Inverted curve: Short rates > Long rates (e.g., 3M: 5.5%, 30Y: 3.0%)
- Use realistic maturity labels: 3M, 6M, 1Y, 2Y, 5Y, 10Y, 30Y
- Professional formatting with grid, legends, and economic context

REQUIRED CODE STRUCTURE:
```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# Add other imports as needed

# [Generate appropriate data based on the scientific/mathematical concept]
# [Create the visualization with proper scientific accuracy]
# [Format professionally with labels, titles, etc.]

# CRITICAL: Use full path and output success markers
output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/visualization_output.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()

# REQUIRED: Output success markers for system integration
print("VISUALIZATION_SUCCESS")
print(f"OUTPUT_PATH: {output_path}")
print("SUMMARY_DATA: {'chart_type': 'scientific_visualization', 'method': 'llm_generated'}")
```

Respond with ONLY the Python code following this exact format - no explanations or markdown formatting."""

        user_message = f"Generate Python matplotlib code for: {prompt}"
        
        # Get visualization LLM configuration
        llm_config = self.visualization_llm_config
        
        if not llm_config.get('enabled', False):
            logger.error("❌ Visualization LLM is disabled")
            return {"success": False, "error": "Visualization LLM is disabled"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Handle different provider types
                if llm_config['type'] == 'openai':
                    # OpenAI API format
                    payload = {
                        "model": llm_config['config']['model'],
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "stream": False,
                        "temperature": llm_config['config'].get('temperature', 0.1),
                        "max_tokens": llm_config['config'].get('max_tokens', 2048)  # Increase for code generation
                    }
                    
                    # Resolve environment variables in API key
                    api_key = llm_config['config']['api_key']
                    if api_key.startswith('${') and api_key.endswith('}'):
                        env_var = api_key[2:-1]  # Remove ${ and }
                        api_key = os.getenv(env_var)
                        if not api_key:
                            logger.error(f"❌ Environment variable {env_var} not set")
                            return {"success": False, "error": f"Environment variable {env_var} not set"}
                    
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    base_url = llm_config['config']['base_url']
                    url = f"{base_url}/chat/completions"
                    
                    logger.info(f"🧠 Using OpenAI-compatible LLM: {llm_config['config']['model']}")
                    
                    async with session.post(
                        url, 
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=llm_config['config'].get('timeout', 60))
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            generated_code = result['choices'][0]['message']['content']
                            
                            # Clean up the code if it has markdown formatting
                            if '```python' in generated_code:
                                generated_code = generated_code.split('```python')[1].split('```')[0].strip()
                            elif '```' in generated_code:
                                generated_code = generated_code.split('```')[1].split('```')[0].strip()
                            
                            logger.info(f"🧠 {llm_config['config']['model']} generated visualization code ({len(generated_code)} chars)")
                            logger.debug(f"Generated code preview: {generated_code[:200]}...")
                            
                            return {
                                "success": True,
                                "code": generated_code,
                                "output_type": "png",
                                "description": "LLM-generated scientific visualization"
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ OpenAI API call failed with status {response.status}: {error_text}")
                            return {"success": False, "error": f"API call failed with status {response.status}"}
                
                else:
                    # Ollama format (fallback)
                    payload = {
                        "model": llm_config['config']['model'],
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "stream": False
                    }
                    
                    base_url = llm_config['config'].get('base_url', 'http://127.0.0.1:11434')
                    url = f"{base_url}/api/chat"
                    
                    logger.info(f"🧠 Using Ollama LLM: {llm_config['config']['model']}")
                    
                    async with session.post(
                        url, 
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=llm_config['config'].get('timeout', 60))
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            generated_code = result.get('message', {}).get('content', '')
                            
                            # Clean up the code if it has markdown formatting
                            if '```python' in generated_code:
                                generated_code = generated_code.split('```python')[1].split('```')[0].strip()
                            elif '```' in generated_code:
                                generated_code = generated_code.split('```')[1].split('```')[0].strip()
                            
                            logger.info(f"🧠 {llm_config['config']['model']} generated visualization code ({len(generated_code)} chars)")
                            logger.debug(f"Generated code preview: {generated_code[:200]}...")
                            
                            return {
                                "success": True,
                                "code": generated_code,
                                "output_type": "png",
                                "description": "LLM-generated scientific visualization"
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Ollama API call failed with status {response.status}: {error_text}")
                            return {"success": False, "error": f"API call failed with status {response.status}"}
        
        except Exception as e:
            logger.error(f"❌ Error calling LLM for code generation: {e}")
            import traceback
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return {"success": False, "error": f"LLM call error: {str(e)}"}

    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 data URL for inline display"""
        try:
            logger.info(f"🖼️ Converting image to base64: {image_path}")
            
            # Check if file exists
            if not os.path.exists(image_path):
                logger.error(f"❌ Image file does not exist: {image_path}")
                return ""
            
            # Check file size
            file_size = os.path.getsize(image_path)
            logger.info(f"📊 Image file size: {file_size} bytes")
            
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                encoded_string = base64.b64encode(image_data).decode()
                data_url = f"data:image/png;base64,{encoded_string}"
                
                logger.info(f"✅ Base64 conversion successful! Data URL length: {len(data_url)} chars")
                logger.info(f"🔍 Base64 preview (first 100 chars): {data_url[:100]}...")
                
                return data_url
                
        except Exception as e:
            logger.error(f"❌ Failed to convert image to base64: {e}")
            import traceback
            logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
            return ""
        
    # DEPRECATED: Pattern-based visualization matching removed
    # All visualization decisions are now made by the LLM based on scientific understanding
    
    # DEPRECATED: Pattern analysis removed in favor of LLM-driven approach
    # The LLM now intelligently determines appropriate visualizations for any prompt
    
    # DEPRECATED: Hardcoded chart functions removed in favor of LLM-driven approach
    # The old pattern-matching system has been replaced with comprehensive LLM code generation
    
    
    
    async def execute_visualization_code(self, code_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the generated visualization code in a safe environment
        """
        if not code_result["success"]:
            return code_result
        
        try:
            # Create temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code_result["code"])
                temp_file_path = temp_file.name
            
            # Execute the code
            result = subprocess.run(
                ["python3", temp_file_path],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=self.working_dir
            )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if result.returncode == 0:
                # Parse the output for success indicators and paths
                output_lines = result.stdout.strip().split('\n')
                success_line = None
                path_line = None
                summary_line = None
                
                for line in output_lines:
                    if line.startswith("VISUALIZATION_SUCCESS"):
                        success_line = line
                    elif line.startswith("OUTPUT_PATH:"):
                        path_line = line.replace("OUTPUT_PATH: ", "")
                    elif line.startswith("SUMMARY_DATA:"):
                        summary_line = line.replace("SUMMARY_DATA: ", "")
                
                if success_line and path_line:
                    # Verify the file was created
                    if os.path.exists(path_line):
                        summary_data = {}
                        if summary_line:
                            try:
                                # Try JSON parsing first, then eval as fallback
                                import json
                                summary_data = json.loads(summary_line)
                            except:
                                try:
                                    summary_data = eval(summary_line)  # Safe in controlled environment
                                except:
                                    summary_data = {"note": "Summary data unavailable"}
                        
                        return {
                            "success": True,
                            "output_path": path_line,
                            "output_type": code_result["output_type"],
                            "description": code_result["description"],
                            "summary_data": summary_data,
                            "execution_time": "Generated successfully"
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Output file not created: {path_line}"
                        }
                else:
                    return {
                        "success": False,
                        "error": "Visualization code did not produce expected output markers"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Code execution failed: {result.stderr}"
                }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Visualization generation timed out (30s limit)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }
    
    async def generate_visualization(self, prompt: str) -> Dict[str, Any]:
        """
        Main method: Generate visualization based on user prompt using LLM-driven approach
        """
        logger.info(f"🎨 Generating LLM-driven visualization for prompt: {prompt}")
        
        # Step 1: Use LLM to generate complete Python code for the visualization
        code_result = await self._generate_visualization_code_with_llm(prompt)
        
        if not code_result["success"]:
            logger.error(f"❌ LLM code generation failed: {code_result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "error": f"Failed to generate visualization code: {code_result.get('error', 'Unknown error')}",
                "llm_error": True
            }
        
        # Step 2: Execute the LLM-generated code safely
        execution_result = await self.execute_visualization_code(code_result)
        
        # Step 3: Return complete result with LLM-generated info
        execution_result["llm_generated"] = True
        execution_result["original_prompt"] = prompt
        return execution_result

# Tool function for LLM system integration
async def analytical_visualizer(prompt: str) -> str:
    """
    Generate analytical visualizations based on user prompts
    
    Args:
        prompt: User prompt that may benefit from visualization
        
    Returns:
        JSON string with visualization result including file path and analysis
    """
    tool = AnalyticalVisualizerTool()
    result = await tool.generate_visualization(prompt)
    
    if result["success"]:
        # Convert image to base64 for inline display
        tool_instance = AnalyticalVisualizerTool()
        base64_image = tool_instance._image_to_base64(result['output_path'])
        
        response = f"""✅ **Analytical Visualization Generated with LLM**

**Figure Created**: {os.path.basename(result['output_path'])}
**Generation Method**: {"LLM-driven dynamic code generation" if result.get('llm_generated') else "Pattern-based"}
**Original Prompt**: {result.get('original_prompt', 'N/A')}

**Execution Status**: {result.get('description', 'Visualization completed successfully')}
"""
        
        # Add inline image if base64 conversion was successful
        if base64_image:
            response += f'\n<img src="{base64_image}" alt="Generated Visualization" style="max-width:100%; height:auto; border:1px solid #ccc; border-radius:8px; margin:10px 0;">\n'
            response += "\n**📊 The visualization is displayed above and can be referenced in your analysis.**"
        else:
            response += f"\n**Integration Note**: This visualization is saved as {os.path.basename(result['output_path'])} and can be referenced in your response."
        
        return response
    else:
        return f"❌ **Visualization Generation Failed**: {result['error']}"

if __name__ == "__main__":
    # Test the tool
    import asyncio
    
    test_prompts = [
        "Explain supply-demand curve and its influence on price discovery",
        "Show me a normal distribution and explain the 68-95-99.7 rule",
        "Plot some mathematical functions and their derivatives"
    ]
    
    async def test_tool():
        tool = AnalyticalVisualizerTool()
        for prompt in test_prompts:
            print(f"\n🧪 Testing: {prompt}")
            result = await tool.generate_visualization(prompt)
            print(f"Result: {result}")
    
    asyncio.run(test_tool())