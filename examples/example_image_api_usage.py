#!/usr/bin/env python3
"""
Example: Using Image-to-Text Tool with OpenAI Compatible API
"""

import requests
import json
import base64

# Server configuration  
SERVER_URL = "http://localhost:5000"
API_KEY = "test-key"  # Any value works for our server

def encode_image_file(image_path):
    """Encode local image file to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Example 1: File-based image analysis
def example_file_analysis():
    """Analyze local image files."""
    
    payload = {
        "model": "Agentic-RAG-Model1",
        "messages": [
            {
                "role": "user", 
                "content": "Please analyze these two image files: /home/user/screenshot.png and /home/user/chart.jpg. Use the image_to_text tool in batch processing mode with context included."
            }
        ],
        "stream": False
    }
    
    response = requests.post(
        f"{SERVER_URL}/v1/chat/completions", 
        json=payload, 
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer test-key"
        }
    )
    
    print("File Analysis Response:")
    if response.status_code == 200:
        result = response.json()
        if 'choices' in result and result['choices']:
            print(result['choices'][0]['message']['content'])
        else:
            print(result)
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Example 2: Base64 image analysis  
def example_base64_analysis():
    """Analyze base64 encoded images."""
    
    # Note: Update this path to point to your actual image file
    try:
        image_b64 = encode_image_file("/path/to/your/image.jpg")
    except FileNotFoundError:
        print("Please update the image path to point to an actual image file")
        return
    
    payload = {
        "model": "Agentic-RAG-Model1",
        "messages": [
            {
                "role": "user",
                "content": f"Please analyze this base64 encoded image in detail using the image_to_text tool with high quality processing: data:image/jpeg;base64,{image_b64}"
            }
        ],
        "stream": False
    }
    
    response = requests.post(
        f"{SERVER_URL}/v1/chat/completions", 
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer test-key"
        }
    )
    
    print("Base64 Analysis Response:")
    if response.status_code == 200:
        result = response.json()
        if 'choices' in result and result['choices']:
            print(result['choices'][0]['message']['content'])
        else:
            print(result)
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Example 3: URL-based image analysis
def example_url_analysis():
    """Analyze images from URLs."""
    
    payload = {
        "model": "Agentic-RAG-Model1",
        "messages": [
            {
                "role": "user",
                "content": "Please analyze this online image using the image_to_text tool: https://example.com/sample-chart.png with automatic quality detection."
            }
        ],
        "stream": False
    }
    
    response = requests.post(
        f"{SERVER_URL}/v1/chat/completions", 
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer test-key"
        }
    )
    
    print("URL Analysis Response:")
    if response.status_code == 200:
        result = response.json()
        if 'choices' in result and result['choices']:
            print(result['choices'][0]['message']['content'])
        else:
            print(result)
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🖼️ Image-to-Text Tool OpenAI Compatible API Examples")
    print("=" * 60)
    
    print("These examples use the OpenAI Compatible API endpoint:")
    print(f"POST {SERVER_URL}/v1/chat/completions")
    print("")
    
    # Run examples (comment out as needed)
    print("Uncomment the examples below to test:")
    print("# example_file_analysis()")
    print("# example_base64_analysis()")
    print("# example_url_analysis()")
    print("")
    print("Remember to:")
    print("1. Update file paths to point to real image files")
    print("2. Ensure your Agentic-RAG server is running on http://localhost:5000")
    print("3. Configure image processing models using: python llm_config_tool.py")