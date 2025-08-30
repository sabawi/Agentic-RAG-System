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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

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
        self.description = "Generate analytical visualizations (plots, charts, tables) based on user prompts"
        self.working_dir = "/home/sabawi/Development/flaskserver/sandbox_workspace"
        self.visualization_patterns = self._load_visualization_patterns()
        
    def _load_visualization_patterns(self) -> Dict[str, Dict]:
        """Load patterns that trigger different types of visualizations"""
        return {
            "economic": {
                "patterns": [
                    r"supply.*demand", r"price.*discovery", r"market.*equilibrium",
                    r"elasticity", r"consumer.*surplus", r"producer.*surplus",
                    r"economic.*curve", r"marginal.*cost", r"revenue.*curve"
                ],
                "chart_types": ["line_plot", "curve_intersection", "area_chart"]
            },
            "statistical": {
                "patterns": [
                    r"distribution", r"correlation", r"regression", r"probability",
                    r"normal.*curve", r"histogram", r"scatter.*plot", r"trend.*analysis"
                ],
                "chart_types": ["histogram", "scatter_plot", "line_plot", "box_plot"]
            },
            "mathematical": {
                "patterns": [
                    r"function.*plot", r"derivative", r"integral", r"optimization",
                    r"polynomial", r"exponential", r"logarithm", r"trigonometric"
                ],
                "chart_types": ["function_plot", "parametric_plot", "contour_plot"]
            },
            "scientific": {
                "patterns": [
                    r"experiment", r"data.*trend", r"simulation", r"model.*prediction",
                    r"time.*series", r"growth.*rate", r"decay", r"oscillation",
                    r"population.*growth", r"exponential.*growth", r"growth.*curve",
                    r"bacterial.*growth", r"viral.*spread", r"compound.*growth"
                ],
                "chart_types": ["time_series", "line_plot", "multi_series", "exponential_growth"]
            },
            "business": {
                "patterns": [
                    r"performance.*metric", r"growth.*analysis", r"comparison",
                    r"roi", r"profit.*margin", r"revenue.*trend", r"market.*share"
                ],
                "chart_types": ["bar_chart", "line_plot", "pie_chart", "dashboard"]
            },
            "project_management": {
                "patterns": [
                    r"s-curve", r"s.*curve", r"project.*progress", r"project.*lifecycle",
                    r"cumulative.*progress", r"project.*timeline", r"milestone.*tracking",
                    r"project.*curve", r"completion.*curve", r"typical.*s-curve"
                ],
                "chart_types": ["s_curve", "timeline", "progress_chart", "milestone_chart"]
            }
        }
    
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze user prompt to determine if visualization would be helpful
        and what type of visualization to generate
        """
        prompt_lower = prompt.lower()
        analysis_result = {
            "needs_visualization": False,
            "categories": [],
            "suggested_charts": [],
            "confidence": 0.0,
            "key_concepts": []
        }
        
        # Check each category for pattern matches
        category_scores = {}
        for category, config in self.visualization_patterns.items():
            matches = 0
            matched_patterns = []
            
            for pattern in config["patterns"]:
                if re.search(pattern, prompt_lower):
                    matches += 1
                    matched_patterns.append(pattern)
            
            if matches > 0:
                score = matches / len(config["patterns"])
                category_scores[category] = {
                    "score": score,
                    "matches": matches,
                    "patterns": matched_patterns,
                    "chart_types": config["chart_types"]
                }
        
        # Determine if visualization is needed (threshold: at least one strong match)
        if category_scores:
            analysis_result["needs_visualization"] = True
            analysis_result["categories"] = list(category_scores.keys())
            analysis_result["confidence"] = max(cat["score"] for cat in category_scores.values())
            
            # Get suggested chart types from best matching category
            best_category = max(category_scores.items(), key=lambda x: x[1]["score"])
            analysis_result["suggested_charts"] = best_category[1]["chart_types"]
            analysis_result["key_concepts"] = best_category[1]["patterns"]
        
        logger.info(f"🎯 Prompt analysis: {analysis_result}")
        return analysis_result
    
    def generate_visualization_code(self, prompt: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Python code to create the most appropriate visualization
        based on prompt analysis
        """
        if not analysis["needs_visualization"]:
            return {"success": False, "error": "No visualization needed"}
        
        # Determine the best visualization approach
        primary_category = analysis["categories"][0] if analysis["categories"] else "general"
        suggested_chart = analysis["suggested_charts"][0] if analysis["suggested_charts"] else "line_plot"
        
        # Generate specialized code based on category and prompt
        if primary_category == "economic" and "supply" in prompt.lower() and "demand" in prompt.lower():
            return self._generate_supply_demand_code(prompt)
        elif primary_category == "statistical" and ("distribution" in prompt.lower() or "normal" in prompt.lower()):
            return self._generate_distribution_code(prompt)
        elif primary_category == "mathematical" and "function" in prompt.lower():
            return self._generate_function_plot_code(prompt)
        elif primary_category == "project_management" and ("s-curve" in prompt.lower() or "s curve" in prompt.lower()):
            return self._generate_s_curve_code(prompt)
        elif primary_category == "scientific" and any(pattern in prompt.lower() for pattern in ["population", "exponential", "growth curve", "bacterial", "viral", "compound"]):
            return self._generate_exponential_growth_code(prompt)
        else:
            return self._generate_generic_analytical_code(prompt, primary_category, suggested_chart)
    
    def _generate_supply_demand_code(self, prompt: str) -> Dict[str, Any]:
        """Generate code for supply-demand curve visualization"""
        code = '''
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Generate supply-demand curve data
quantity = np.linspace(0, 100, 100)
supply = 2 + 0.5 * quantity + 0.01 * quantity**1.5  # Upward sloping
demand = 50 - 0.3 * quantity - 0.005 * quantity**2  # Downward sloping

# Find equilibrium point (approximate)
eq_idx = np.argmin(np.abs(supply - demand))
eq_quantity = quantity[eq_idx]
eq_price = supply[eq_idx]

# Create the plot
fig, ax = plt.subplots(figsize=(10, 8))

# Plot curves
ax.plot(quantity, supply, 'b-', linewidth=2, label='Supply Curve', alpha=0.8)
ax.plot(quantity, demand, 'r-', linewidth=2, label='Demand Curve', alpha=0.8)

# Mark equilibrium
ax.plot(eq_quantity, eq_price, 'go', markersize=10, label=f'Equilibrium (Q={eq_quantity:.1f}, P=${eq_price:.2f})')
ax.axvline(eq_quantity, color='gray', linestyle='--', alpha=0.5)
ax.axhline(eq_price, color='gray', linestyle='--', alpha=0.5)

# Fill areas for consumer and producer surplus
eq_demand_price = 50 - 0.3 * eq_quantity - 0.005 * eq_quantity**2
consumer_surplus_x = quantity[quantity <= eq_quantity]
consumer_surplus_y = 50 - 0.3 * consumer_surplus_x - 0.005 * consumer_surplus_x**2
ax.fill_between(consumer_surplus_x, consumer_surplus_y, eq_price, 
                alpha=0.3, color='green', label='Consumer Surplus')

producer_surplus_x = quantity[quantity <= eq_quantity]
producer_surplus_y = 2 + 0.5 * producer_surplus_x + 0.01 * producer_surplus_x**1.5
ax.fill_between(producer_surplus_x, producer_surplus_y, eq_price,
                alpha=0.3, color='blue', label='Producer Surplus')

# Formatting
ax.set_xlabel('Quantity', fontsize=12, fontweight='bold')
ax.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
ax.set_title('Supply and Demand Analysis\\nPrice Discovery Mechanism', fontsize=14, fontweight='bold')
ax.legend(loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 100)
ax.set_ylim(0, max(max(supply), max(demand)) * 1.1)

# Add annotations
ax.annotate(f'Market equilibrium occurs at Q={eq_quantity:.1f} units\\nwhere supply meets demand at ${eq_price:.2f}',
            xy=(eq_quantity, eq_price), xytext=(eq_quantity + 20, eq_price + 5),
            arrowprops=dict(arrowstyle='->', color='black', alpha=0.7),
            bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7),
            fontsize=10)

plt.tight_layout()
output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/supply_demand_analysis.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

# Generate summary data
summary_data = {
    "equilibrium_quantity": round(eq_quantity, 2),
    "equilibrium_price": round(eq_price, 2),
    "consumer_surplus_area": "Shown in green",
    "producer_surplus_area": "Shown in blue",
    "interpretation": "Market efficiency achieved at equilibrium point"
}

print("VISUALIZATION_SUCCESS")
print(f"OUTPUT_PATH: {output_path}")
print(f"SUMMARY_DATA: {summary_data}")
'''
        
        return {
            "success": True,
            "code": code,
            "output_type": "png",
            "description": "Supply and demand curve analysis with equilibrium point and surplus areas"
        }
    
    def _generate_distribution_code(self, prompt: str) -> Dict[str, Any]:
        """Generate code for statistical distribution visualization"""
        code = '''
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Generate normal distribution data
x = np.linspace(-4, 4, 1000)
normal_dist = stats.norm(0, 1)
y = normal_dist.pdf(x)

# Create the plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Plot 1: Normal Distribution Curve
ax1.plot(x, y, 'b-', linewidth=2, label='Standard Normal Distribution')
ax1.fill_between(x, y, alpha=0.3, color='lightblue')

# Add area annotations for standard deviations
z_scores = [-2, -1, 0, 1, 2]
for z in z_scores:
    ax1.axvline(z, color='red', linestyle='--', alpha=0.7)
    ax1.text(z, 0.05, f'z={z}', ha='center', fontsize=9)

ax1.set_xlabel('Standard Deviations from Mean', fontweight='bold')
ax1.set_ylabel('Probability Density', fontweight='bold')
ax1.set_title('Normal Distribution\\n68-95-99.7 Rule', fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Sample data histogram
np.random.seed(42)
sample_data = np.random.normal(100, 15, 1000)  # Mean=100, std=15
ax2.hist(sample_data, bins=30, density=True, alpha=0.7, color='skyblue', edgecolor='black')
x_sample = np.linspace(sample_data.min(), sample_data.max(), 100)
y_sample = stats.norm(100, 15).pdf(x_sample)
ax2.plot(x_sample, y_sample, 'r-', linewidth=2, label='Theoretical Normal Curve')

ax2.set_xlabel('Value', fontweight='bold')
ax2.set_ylabel('Density', fontweight='bold')
ax2.set_title('Sample Data Distribution\\n(Mean=100, Std=15)', fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/distribution_analysis.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

# Generate summary statistics
summary_data = {
    "sample_mean": round(np.mean(sample_data), 2),
    "sample_std": round(np.std(sample_data), 2),
    "sample_size": len(sample_data),
    "within_1_std": round(np.sum(np.abs(sample_data - np.mean(sample_data)) <= np.std(sample_data)) / len(sample_data) * 100, 1),
    "interpretation": "Normal distribution shows 68% of data within 1 standard deviation"
}

print("VISUALIZATION_SUCCESS")
print(f"OUTPUT_PATH: {output_path}")
print(f"SUMMARY_DATA: {summary_data}")
'''
        
        return {
            "success": True,
            "code": code,
            "output_type": "png",
            "description": "Statistical distribution analysis with normal curve and sample data"
        }
    
    def _generate_function_plot_code(self, prompt: str) -> Dict[str, Any]:
        """Generate code for mathematical function visualization"""
        code = '''
import matplotlib.pyplot as plt
import numpy as np

# Generate function data
x = np.linspace(-5, 5, 1000)

# Multiple mathematical functions
y1 = np.exp(-x**2/2) / np.sqrt(2*np.pi)  # Gaussian
y2 = 1 / (1 + np.exp(-x))  # Sigmoid
y3 = x**3 - 3*x**2 + 2*x + 1  # Cubic polynomial

# Create subplots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

# Plot 1: Gaussian function
ax1.plot(x, y1, 'b-', linewidth=2, label='Gaussian: $e^{-x²/2}/\\sqrt{2π}$')
ax1.fill_between(x, y1, alpha=0.3)
ax1.set_title('Gaussian Function', fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Sigmoid function
ax2.plot(x, y2, 'r-', linewidth=2, label='Sigmoid: $1/(1+e^{-x})$')
ax2.axhline(y=0.5, color='gray', linestyle='--', alpha=0.7)
ax2.axvline(x=0, color='gray', linestyle='--', alpha=0.7)
ax2.set_title('Sigmoid Function', fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Polynomial function and its derivative
y3_derivative = 3*x**2 - 6*x + 2
ax3.plot(x, y3, 'g-', linewidth=2, label='$f(x) = x³ - 3x² + 2x + 1$')
ax3.plot(x, y3_derivative, 'orange', linewidth=2, linestyle='--', label="$f'(x) = 3x² - 6x + 2$")
ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax3.axvline(x=0, color='black', linestyle='-', alpha=0.3)
ax3.set_title('Polynomial Function and Derivative', fontweight='bold')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Plot 4: Trigonometric functions
x_trig = np.linspace(-2*np.pi, 2*np.pi, 1000)
ax4.plot(x_trig, np.sin(x_trig), 'purple', linewidth=2, label='sin(x)')
ax4.plot(x_trig, np.cos(x_trig), 'brown', linewidth=2, label='cos(x)')
ax4.plot(x_trig, np.tan(x_trig), 'pink', linewidth=1, alpha=0.7, label='tan(x)')
ax4.set_ylim(-3, 3)
ax4.set_title('Trigonometric Functions', fontweight='bold')
ax4.legend()
ax4.grid(True, alpha=0.3)

# Add labels
for ax in [ax1, ax2, ax3, ax4]:
    ax.set_xlabel('x', fontweight='bold')
    ax.set_ylabel('f(x)', fontweight='bold')

plt.suptitle('Mathematical Function Analysis', fontsize=16, fontweight='bold')
plt.tight_layout()

output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/function_analysis.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

summary_data = {
    "functions_plotted": ["Gaussian", "Sigmoid", "Polynomial", "Trigonometric"],
    "analysis_includes": "Function behavior, derivatives, and key characteristics",
    "interpretation": "Visual representation of mathematical function properties"
}

print("VISUALIZATION_SUCCESS")
print(f"OUTPUT_PATH: {output_path}")
print(f"SUMMARY_DATA: {summary_data}")
'''
        
        return {
            "success": True,
            "code": code,
            "output_type": "png", 
            "description": "Mathematical function analysis with multiple function types and derivatives"
        }
    
    def _generate_s_curve_code(self, prompt: str) -> Dict[str, Any]:
        """Generate code for project management S-curve visualization"""
        code = '''
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Generate realistic S-curve data for project progress
time_points = np.linspace(0, 100, 100)  # Project timeline (0-100% duration)

# Logistic function for S-curve: slow start, rapid middle, slow finish
# Parameters: L=100 (max progress), k=0.1 (steepness), x0=50 (midpoint)
progress_planned = 100 / (1 + np.exp(-0.1 * (time_points - 50)))

# Add some realistic variation for actual progress
np.random.seed(42)
variation = np.random.normal(0, 2, len(time_points))
progress_actual = np.clip(progress_planned + variation, 0, 100)

# Create cumulative cost S-curve (follows similar pattern)
cost_planned = progress_planned * 1.2  # Slightly steeper cost curve
cost_actual = progress_actual * 1.15   # Actual costs with different scaling

# Create the plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Plot 1: Progress S-Curve
ax1.plot(time_points, progress_planned, 'b-', linewidth=3, label='Planned Progress', alpha=0.8)
ax1.plot(time_points, progress_actual, 'r--', linewidth=2, label='Actual Progress', alpha=0.8)
ax1.fill_between(time_points, progress_planned, alpha=0.2, color='blue')
ax1.fill_between(time_points, progress_actual, alpha=0.2, color='red')

# Mark key project phases
phase_boundaries = [0, 25, 75, 100]
phase_labels = ['Project Start', 'Acceleration Phase', 'Completion Phase', 'Project End']
colors = ['green', 'orange', 'red', 'purple']

for i, (boundary, label, color) in enumerate(zip(phase_boundaries, phase_labels, colors)):
    if i < len(phase_boundaries) - 1:
        ax1.axvline(boundary, color=color, linestyle=':', alpha=0.7, linewidth=2)
        progress_at_point = 100 / (1 + np.exp(-0.1 * (boundary - 50)))
        ax1.annotate(label, xy=(boundary, progress_at_point), xytext=(boundary, progress_at_point + 15),
                    arrowprops=dict(arrowstyle='->', color=color, alpha=0.7),
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.3),
                    fontsize=9, ha='center')

ax1.set_xlabel('Project Duration (%)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Cumulative Progress (%)', fontsize=12, fontweight='bold')
ax1.set_title('Project Management S-Curve\\nCumulative Progress Over Time', fontsize=14, fontweight='bold')
ax1.legend(loc='lower right', framealpha=0.9)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 100)
ax1.set_ylim(0, 110)

# Plot 2: Cost S-Curve
ax2.plot(time_points, cost_planned, 'g-', linewidth=3, label='Planned Cost', alpha=0.8)
ax2.plot(time_points, cost_actual, 'm--', linewidth=2, label='Actual Cost', alpha=0.8)
ax2.fill_between(time_points, cost_planned, alpha=0.2, color='green')
ax2.fill_between(time_points, cost_actual, alpha=0.2, color='magenta')

ax2.set_xlabel('Project Duration (%)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Cumulative Cost (%)', fontsize=12, fontweight='bold')
ax2.set_title('Cost S-Curve\\nCumulative Cost Expenditure', fontsize=14, fontweight='bold')
ax2.legend(loc='lower right', framealpha=0.9)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 100)
ax2.set_ylim(0, 130)

# Add explanatory text
fig.text(0.02, 0.02, 
         'S-Curve Phases: • Early Phase: Slow start due to planning and setup\\n'
         '• Middle Phase: Rapid acceleration as resources are fully deployed\\n'
         '• Final Phase: Slowdown as project completion and closeout activities occur',
         fontsize=10, style='italic', 
         bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))

plt.tight_layout()
plt.subplots_adjust(bottom=0.15)

output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/s_curve_project_analysis.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

# Generate summary data
summary_data = {
    "curve_type": "Logistic S-Curve",
    "project_phases": ["Initiation (0-25%)", "Execution (25-75%)", "Closure (75-100%)"],
    "key_characteristics": "Slow start, rapid middle phase, gradual completion",
    "applications": ["Progress tracking", "Cost management", "Resource planning"],
    "interpretation": "Typical project lifecycle showing cumulative progress and cost over time"
}

print("VISUALIZATION_SUCCESS")
print(f"OUTPUT_PATH: {output_path}")
print(f"SUMMARY_DATA: {summary_data}")
'''
        
        return {
            "success": True,
            "code": code,
            "output_type": "png",
            "description": "Project management S-curve showing cumulative progress and cost over project timeline"
        }
    
    def _generate_exponential_growth_code(self, prompt: str) -> Dict[str, Any]:
        """Generate code for exponential/population growth curve visualization"""
        code = '''
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Generate exponential growth data for population/biological growth
time_points = np.linspace(0, 10, 100)  # Time axis (years, generations, etc.)

# Exponential growth parameters
initial_population = 100  # Starting population
growth_rate = 0.3  # Growth rate (30% per time unit)

# Generate multiple growth scenarios
populations_exponential = initial_population * np.exp(growth_rate * time_points)
populations_logistic = 10000 / (1 + ((10000/initial_population - 1) * np.exp(-0.5 * time_points)))  # With carrying capacity
populations_linear = initial_population + 200 * time_points  # Linear for comparison

# Create figure with subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Plot 1: Pure Exponential Growth
ax1.plot(time_points, populations_exponential, 'b-', linewidth=3, label='Exponential Growth', alpha=0.8)
ax1.fill_between(time_points, populations_exponential, alpha=0.3, color='blue')
ax1.set_xlabel('Time (units)', fontweight='bold')
ax1.set_ylabel('Population Size', fontweight='bold')
ax1.set_title('Population Growth Curve\\nExponential Model', fontweight='bold', fontsize=14)
ax1.grid(True, alpha=0.3)
ax1.legend()
ax1.set_yscale('log')  # Log scale to better show exponential nature

# Add growth rate annotation
mid_point = len(time_points) // 2
ax1.annotate(f'Growth Rate: {growth_rate*100}% per time unit', 
             xy=(time_points[mid_point], populations_exponential[mid_point]),
             xytext=(time_points[mid_point]-2, populations_exponential[mid_point]*2),
             arrowprops=dict(arrowstyle='->', color='red', lw=2),
             fontsize=10, fontweight='bold', color='red')

# Plot 2: Comparison of Growth Models
ax2.plot(time_points, populations_exponential, 'b-', linewidth=2, label='Exponential', alpha=0.8)
ax2.plot(time_points, populations_logistic, 'g-', linewidth=2, label='Logistic (Limited)', alpha=0.8)
ax2.plot(time_points, populations_linear, 'r--', linewidth=2, label='Linear', alpha=0.8)

ax2.set_xlabel('Time (units)', fontweight='bold')
ax2.set_ylabel('Population Size', fontweight='bold')
ax2.set_title('Growth Model Comparison\\nExponential vs Logistic vs Linear', fontweight='bold', fontsize=14)
ax2.grid(True, alpha=0.3)
ax2.legend()

# Add key insights
textstr = '\\n'.join([
    'Key Insights:',
    '• Exponential: Unlimited growth',
    '• Logistic: Growth with limits',
    '• Linear: Constant rate increase'
])
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax2.text(0.02, 0.98, textstr, transform=ax2.transAxes, fontsize=9,
         verticalalignment='top', bbox=props)

plt.tight_layout()
output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/exponential_growth_analysis.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

# Generate summary data
summary_data = {
    "growth_model": "exponential",
    "initial_population": initial_population,
    "growth_rate": f"{growth_rate*100}%",
    "time_range": f"{time_points[0]} to {time_points[-1]} units",
    "final_population_exponential": int(populations_exponential[-1]),
    "interpretation": "Exponential growth shows rapid population increase over time, characteristic of biological populations with unlimited resources"
}

print("VISUALIZATION_SUCCESS")
print(f"OUTPUT_PATH: {output_path}")
print(f"SUMMARY_DATA: {summary_data}")
print("**Figure Created**: exponential_growth_analysis.png")
'''
        
        return {
            "success": True,
            "code": code,
            "output_type": "png",
            "description": "Exponential/population growth curve showing characteristic exponential increase over time"
        }
    
    def _generate_generic_analytical_code(self, prompt: str, category: str, chart_type: str) -> Dict[str, Any]:
        """Generate generic analytical visualization code"""
        code = f'''
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Generate sample analytical data
np.random.seed(42)
x_data = np.linspace(0, 10, 50)
y_data = 2 * x_data + 1 + np.random.normal(0, 1, 50)  # Linear trend with noise

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

if "{chart_type}" == "line_plot":
    ax.plot(x_data, y_data, 'bo-', linewidth=2, markersize=4, alpha=0.7)
    
    # Add trend line
    z = np.polyfit(x_data, y_data, 1)
    p = np.poly1d(z)
    ax.plot(x_data, p(x_data), 'r--', linewidth=2, alpha=0.8, label='Trend Line')
    
elif "{chart_type}" == "scatter_plot":
    ax.scatter(x_data, y_data, alpha=0.6, s=50)
    
elif "{chart_type}" == "bar_chart":
    categories = ['A', 'B', 'C', 'D', 'E']
    values = np.random.uniform(10, 50, 5)
    ax.bar(categories, values, alpha=0.7, color='steelblue')
    
else:  # Default line plot
    ax.plot(x_data, y_data, 'o-', linewidth=2, markersize=4)

# Formatting
ax.set_xlabel('X Variable', fontweight='bold')
ax.set_ylabel('Y Variable', fontweight='bold') 
ax.set_title('Analytical Visualization\\n{category.title()} Analysis', fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend()

plt.tight_layout()
output_path = "/home/sabawi/Development/flaskserver/sandbox_workspace/analytical_plot.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

summary_data = {{
    "category": "{category}",
    "chart_type": "{chart_type}",
    "data_points": len(x_data) if isinstance(x_data, np.ndarray) else "Variable",
    "interpretation": "Generated analytical visualization based on prompt analysis"
}}

print("VISUALIZATION_SUCCESS")
print(f"OUTPUT_PATH: {{output_path}}")
print(f"SUMMARY_DATA: {{summary_data}}")
'''
        
        return {
            "success": True,
            "code": code,
            "output_type": "png",
            "description": f"Generic {category} visualization using {chart_type}"
        }
    
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
        Main method: Generate visualization based on user prompt
        """
        logger.info(f"🎨 Generating visualization for prompt: {prompt}")
        
        # Step 1: Analyze prompt
        analysis = self.analyze_prompt(prompt)
        
        if not analysis["needs_visualization"]:
            return {
                "success": False,
                "error": "Prompt does not require visualization",
                "analysis": analysis
            }
        
        # Step 2: Generate appropriate code
        code_result = self.generate_visualization_code(prompt, analysis)
        
        if not code_result["success"]:
            return code_result
        
        # Step 3: Execute code safely
        execution_result = await self.execute_visualization_code(code_result)
        
        # Step 4: Return complete result
        execution_result["prompt_analysis"] = analysis
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
        return f"""✅ **Analytical Visualization Generated**

**Figure Created**: {os.path.basename(result['output_path'])}
**Full Path**: {result['output_path']}
**Type**: {result['description']}
**Categories**: {', '.join(result['prompt_analysis']['categories'])}

**Summary Data**: {json.dumps(result['summary_data'], indent=2)}

**Integration Note**: This visualization can be referenced in your response as "See Figure 1" or similar, and the image file is available for inclusion in reports or presentations.

**Confidence**: {result['prompt_analysis']['confidence']:.2%} match for visualization needs"""
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