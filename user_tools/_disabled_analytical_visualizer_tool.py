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
        return """🎯 PRIORITY: Generate analytical visualizations to enhance explanations with professional charts and graphs.
        
        ⚡ WHEN TO USE: Use this tool when explanations would benefit from visual representation:
        - Economics: supply-demand curves, elasticity, price discovery, market equilibrium
        - Statistics: distributions, correlations, regression analysis, probability curves  
        - Mathematics: function plots, derivatives, optimization, polynomial analysis
        - Science: time series data, experimental results, trend analysis
        - Business: performance metrics, growth analysis, comparative charts
        
        🎨 OUTPUT: Creates high-quality PNG visualizations with professional annotations, equilibrium points, 
        surplus areas, statistical markers, and mathematical notation. Files saved to sandbox for reference.
        
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
                
                # Format success response
                response_data = {
                    "visualization_generated": True,
                    "output_file": output_file,
                    "full_path": result["output_path"],
                    "visualization_type": result["description"],
                    "categories": result["prompt_analysis"]["categories"],
                    "confidence": result["prompt_analysis"]["confidence"],
                    "summary_data": result.get("summary_data", {}),
                    "usage_note": "This visualization can be referenced as 'Figure 1' or similar in your response"
                }
                
                return {
                    "success": True,
                    "result": response_data
                }
            
            elif force_visualization:
                return {
                    "success": False,
                    "error": f"Forced visualization failed: {result.get('error', 'Unknown error')}"
                }
            
            else:
                # Not a visualization-worthy prompt - this is not an error
                return {
                    "success": True,
                    "result": {
                        "visualization_generated": False,
                        "reason": "Prompt does not require visualization enhancement",
                        "analysis": result.get("analysis", {})
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Analytical visualizer execution failed: {str(e)}"
            }