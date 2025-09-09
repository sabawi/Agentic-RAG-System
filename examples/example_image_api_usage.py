#!/usr/bin/env python3
"""
Example: Using Image-to-Text Tool with Native API
"""

import requests
import json
import base64

# Server configuration
SERVER_URL = "http://localhost:5000"

def encode_image_file(image_path):
    """Encode local image file to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Example 1: File-based image analysis
def example_file_analysis():
    """Analyze local image files."""
    
    payload = {
        "prompt": "Analyze these images using the image_to_text tool",
        "tools": True,
        "model": "qwen3:8b",
        "stream": False,
        "tool_calls": [
            {
                "function": {
                    "name": "image_to_text",
                    "arguments": {
                        "images": [
                            {
                                "type": "file",
                                "path": "/home/user/screenshot.png"
                            },
                            {
                                "type": "file", 
                                "path": "/home/user/chart.jpg"
                            }
                        ],
                        "processing_mode": "batch",
                        "include_context": True
                    }
                }
            }
        ]
    }
    
    response = requests.post(f"{SERVER_URL}/llama3_1b/stream", 
                           json=payload, 
                           headers={"Content-Type": "application/json"})
    
    print("File Analysis Response:")
    print(response.json())

# Example 2: Base64 image analysis  
def example_base64_analysis():
    """Analyze base64 encoded images."""
    
    # Encode your image
    image_b64 = encode_image_file("/path/to/your/image.jpg")
    
    payload = {
        "prompt": "Please analyze this image in detail",
        "tools": True,
        "model": "qwen3:8b", 
        "stream": False,
        "tool_calls": [
            {
                "function": {
                    "name": "image_to_text",
                    "arguments": {
                        "images": [
                            {
                                "type": "base64",
                                "data": f"data:image/jpeg;base64,{image_b64}",
                                "quality": "high"
                            }
                        ],
                        "processing_mode": "sequential"
                    }
                }
            }
        ]
    }
    
    response = requests.post(f"{SERVER_URL}/llama3_1b/stream", json=payload)
    print("Base64 Analysis Response:")
    print(response.json())

# Example 3: URL-based image analysis
def example_url_analysis():
    """Analyze images from URLs."""
    
    payload = {
        "prompt": "Analyze this online image",
        "tools": True,
        "stream": False,
        "tool_calls": [
            {
                "function": {
                    "name": "image_to_text",
                    "arguments": {
                        "images": [
                            {
                                "type": "url",
                                "url": "https://example.com/sample-chart.png",
                                "quality": "auto"
                            }
                        ]
                    }
                }
            }
        ]
    }
    
    response = requests.post(f"{SERVER_URL}/llama3_1b/stream", json=payload)
    print("URL Analysis Response:")
    print(response.json())

if __name__ == "__main__":
    print("🖼️ Image-to-Text Tool API Examples")
    print("=" * 50)
    
    # Run examples (comment out as needed)
    # example_file_analysis()
    # example_base64_analysis() 
    # example_url_analysis()
    
    print("Update the file paths and URLs to test with real images!")