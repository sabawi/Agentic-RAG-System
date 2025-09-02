#!/usr/bin/env python3
"""
Analytical Visualizer Tool - LLM Integration Wrapper
Generates analytical visualizations (plots, charts, tables) to enhance explanations
"""

import os
import json
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(__file__))

from base_user_tool import BaseUserTool
from analytical_visualizer import AnalyticalVisualizerTool


class AnalyticalVisualizerUserTool(BaseUserTool):
    """
    User tool wrapper for the Analytical Visualizer.
    Automatically generates relevant charts and plots based on prompts.
    """
    
    def __init__(self):
        super().__init__()
        self.visualizer = AnalyticalVisualizerTool()
    
    @property
    def name(self) -> str:
        return "analytical_visualizer"
    
    @property
    def description(self) -> str:
        return """🎯 PRIORITY: Generate and modify analytical visualizations to enhance explanations with professional charts and graphs.
        
        ⚡ WHEN TO USE: Use this tool for ALL visualization needs including:
        - **NEW PLOTS**: Economics, statistics, mathematics, science, business charts
        - **PLOT MODIFICATIONS**: Changing scales, adding curves, updating parameters, refinements
        - **PLOT VARIATIONS**: Superimposing curves, comparing scenarios, showing alternatives
        - **PLOT IMPROVEMENTS**: Better annotations, different styles, enhanced clarity
        
        📊 EXAMPLES OF MODIFICATION REQUESTS:
        - "Make the plot go up to 6% yield" 
        - "Superimpose an inverted yield curve"
        - "Add error bars to the data points"
        - "Change the scale to logarithmic"
        - "Show both linear and exponential trends"
        
        🎨 OUTPUT: Creates high-quality PNG visualizations with professional annotations, equilibrium points, 
        surplus areas, statistical markers, and mathematical notation. Files saved to sandbox for reference.
        
        🚨 CRITICAL: ALWAYS use this tool for plot modifications - NEVER generate code directly in responses!
        
        💡 TIP: Even when gathering information about analytical topics, consider generating supporting visuals."""
    
    @property 
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user prompt or query that may benefit from visualization"
                },
                "force_visualization": {
                    "type": "boolean",
                    "description": "Force visualization generation even if automatic detection doesn't trigger",
                    "default": False
                }
            },
            "required": ["prompt"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the analytical visualizer based on the prompt.
        
        Args:
            prompt: The user prompt to analyze for visualization opportunities
            force_visualization: Force generation even if not automatically detected
            
        Returns:
            Dict containing visualization result with file path and analysis
        """
        try:
            prompt = kwargs.get("prompt", "")
            force_visualization = kwargs.get("force_visualization", False)
            
            if not prompt:
                return {
                    "success": False,
                    "error": "No prompt provided for visualization analysis"
                }
            
            # Generate visualization
            result = await self.visualizer.generate_visualization(prompt)
            
            if result["success"]:
                # Extract filename for cleaner presentation
                output_file = os.path.basename(result["output_path"])
                
                # Convert image to base64 for inline display
                base64_image = self.visualizer._image_to_base64(result["output_path"])
                
                # Format success response with base64 image (updated for LLM-driven approach)
                response_message = f"""✅ **Analytical Visualization Generated with LLM**

**Figure Created**: {output_file}
**Generation Method**: {"LLM-driven dynamic code generation" if result.get('llm_generated') else "Pattern-based"}
**Original Prompt**: {result.get('original_prompt', prompt)}

**Execution Status**: {result.get('description', 'Visualization completed successfully')}

**Summary Data**: {json.dumps(result.get("summary_data", {}), indent=2)}
"""
                
                # Add inline image if base64 conversion was successful
                if base64_image:
                    response_message += f'\n<img src="{base64_image}" alt="Generated Visualization" style="max-width:100%; height:auto; border:1px solid #ccc; border-radius:8px; margin:10px 0;">\n'
                    response_message += "\n**📊 The visualization is displayed above and can be referenced in your analysis.**"
                else:
                    response_message += f"\n**Integration Note**: This visualization is saved as {output_file} and can be referenced in your response."
                
                return {
                    "success": True,
                    "result": response_message
                }
            
            elif force_visualization:
                return {
                    "success": False,
                    "error": f"Forced visualization failed: {result.get('error', 'Unknown error')}"
                }
            
            else:
                # LLM-driven approach always tries to generate visualizations
                # If it fails, return the error for debugging
                return {
                    "success": False,
                    "error": f"Visualization generation failed: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Analytical visualizer execution failed: {str(e)}"
            }