#!/usr/bin/env python3
"""
Test Image Processing Configuration Usage
Demonstrates how user tools would access image processing LLM configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import config_loader

def demo_user_tool_usage():
    """Demonstrate how a user tool would use image processing config"""
    print("🖼️ USER TOOL IMAGE PROCESSING CONFIGURATION DEMO")
    print("=" * 60)
    
    print("🔧 How a user tool would access image processing LLM:")
    print()
    
    # This is how a user tool would access the image processing config
    try:
        # Step 1: Get image processing configuration
        image_config = config_loader.get_llm_config('image_processing')
        
        print("1️⃣ Loading image processing configuration...")
        print(f"   Provider: {image_config['type']}")
        print(f"   Model: {image_config['config']['model']}")
        print()
        
        # Step 2: Extract connection details
        provider_type = image_config['type']
        model_config = image_config['config']
        
        print("2️⃣ Extracting connection details...")
        print(f"   Base URL: {model_config['base_url']}")
        print(f"   API Key: {model_config.get('api_key', 'None (local)')}")
        print(f"   Model: {model_config['model']}")
        print(f"   Temperature: {model_config['temperature']}")
        print(f"   Max Tokens: {model_config['max_tokens']}")
        print(f"   Timeout: {model_config['timeout']}")
        print()
        
        # Step 3: Show how tool would configure API call
        print("3️⃣ Tool would configure API call like this:")
        print()
        
        if provider_type == 'ollama':
            print("   # Ollama API configuration")
            print(f"   api_url = '{model_config['base_url']}/api/generate'")
            print(f"   model_name = '{model_config['model']}'")
            print(f"   temperature = {model_config['temperature']}")
            print("   # Tool would include image in base64 format")
            print("   payload = {")
            print(f"       'model': '{model_config['model']}',")
            print("       'prompt': user_question,")
            print("       'images': [base64_image],")
            print(f"       'temperature': {model_config['temperature']},")
            print("       'stream': False")
            print("   }")
            print()
            
        elif provider_type == 'openai':
            print("   # OpenAI Vision API configuration")
            print(f"   api_url = '{model_config['base_url']}/chat/completions'")
            print(f"   api_key = os.getenv('OPENAI_API_KEY')")
            print("   payload = {")
            print(f"       'model': '{model_config['model']}',")
            print("       'messages': [")
            print("           {")
            print("               'role': 'user',")
            print("               'content': [")
            print("                   {'type': 'text', 'text': user_question},")
            print("                   {'type': 'image_url', 'image_url': {'url': image_url}}")
            print("               ]")
            print("           }")
            print("       ],")
            print(f"       'temperature': {model_config['temperature']},")
            print(f"       'max_tokens': {model_config['max_tokens']}")
            print("   }")
            print()
        
        # Step 4: Show practical usage example
        print("4️⃣ Practical usage example in a user tool:")
        print()
        print("   def analyze_image(self, image_path, question):")
        print("       # Get image processing LLM config")
        print("       config = config_loader.get_llm_config('image_processing')")
        print("       ")
        print("       # Configure based on provider")
        print("       if config['type'] == 'ollama':")
        print("           return self._call_ollama_vision(config, image_path, question)")
        print("       elif config['type'] == 'openai':")
        print("           return self._call_openai_vision(config, image_path, question)")
        print("       ")
        print("       # Tool can support multiple providers transparently!")
        print()
        
        print("✅ Configuration access demonstration complete!")
        print("🎯 User tools can now easily access image processing LLM settings!")
        
    except Exception as e:
        print(f"❌ Error accessing image processing config: {e}")
        import traceback
        traceback.print_exc()

def show_available_configurations():
    """Show all available LLM configurations"""
    print("\n📋 AVAILABLE LLM CONFIGURATIONS")
    print("=" * 60)
    
    llm_types = ['primary', 'tool_calling', 'image_processing', 'arbitrator']
    
    for llm_type in llm_types:
        try:
            config = config_loader.get_llm_config(llm_type)
            provider = config.get('type', 'unknown')
            model = config.get('config', {}).get('model', 'unknown')
            base_url = config.get('config', {}).get('base_url', 'N/A')
            
            print(f"🔧 {llm_type.upper()}:")
            print(f"   Provider: {provider}")
            print(f"   Model: {model}")
            print(f"   Base URL: {base_url}")
            print()
            
        except Exception as e:
            print(f"❌ {llm_type}: Error loading config - {e}")
            print()

if __name__ == "__main__":
    demo_user_tool_usage()
    show_available_configurations()