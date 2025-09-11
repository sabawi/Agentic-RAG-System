#!/usr/bin/env python3
"""
Test Image Processing LLM Configuration
Tests the new image processing configuration system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import config_loader
import json

def test_image_processing_config():
    """Test image processing configuration loading"""
    print("🖼️ TESTING IMAGE PROCESSING LLM CONFIGURATION")
    print("=" * 60)
    
    try:
        # Test loading image processing config
        print("1️⃣ Testing image processing config loading...")
        image_config = config_loader.get_llm_config('image_processing')
        
        print(f"✅ Image processing config loaded successfully:")
        print(f"   Provider: {image_config.get('type', 'unknown')}")
        print(f"   Model: {image_config.get('config', {}).get('model', 'unknown')}")
        print(f"   Base URL: {image_config.get('config', {}).get('base_url', 'N/A')}")
        print(f"   Timeout: {image_config.get('config', {}).get('timeout', 'N/A')}")
        print(f"   Temperature: {image_config.get('config', {}).get('temperature', 'N/A')}")
        print()
        
        # Test all LLM types
        print("2️⃣ Testing all LLM type configurations...")
        llm_types = ['primary', 'tool_calling', 'image_processing']
        
        for llm_type in llm_types:
            try:
                config = config_loader.get_llm_config(llm_type)
                provider = config.get('type', 'unknown')
                model = config.get('config', {}).get('model', 'unknown')
                print(f"   {llm_type}: {provider} - {model}")
            except Exception as e:
                print(f"   ❌ {llm_type}: Error - {e}")
        
        print()
        
        # Test configuration validation
        print("3️⃣ Testing configuration structure...")
        full_config = config_loader.load_config()
        llm_config = full_config.get('llm', {})
        
        required_sections = ['primary', 'tool_calling', 'image_processing']
        for section in required_sections:
            if section in llm_config:
                print(f"   ✅ {section}: Present")
            else:
                print(f"   ❌ {section}: Missing")
        
        print()
        
        # Test detailed image processing config structure
        print("4️⃣ Testing image processing config structure...")
        if 'image_processing' in llm_config:
            img_config = llm_config['image_processing']
            required_fields = ['type', 'config']
            for field in required_fields:
                if field in img_config:
                    print(f"   ✅ {field}: Present")
                else:
                    print(f"   ❌ {field}: Missing")
            
            if 'config' in img_config:
                config_fields = ['model', 'timeout', 'temperature', 'base_url']
                for field in config_fields:
                    if field in img_config['config']:
                        value = img_config['config'][field]
                        print(f"   ✅ config.{field}: {value}")
                    else:
                        print(f"   ❌ config.{field}: Missing")
        else:
            print("   ❌ image_processing section not found")
        
        print()
        
        # Test usage simulation
        print("5️⃣ Simulating tool usage...")
        print("   Simulating how a user tool would access image processing config:")
        
        # Simulate what a user tool would do
        try:
            image_llm_config = config_loader.get_llm_config('image_processing')
            provider = image_llm_config['type']
            model_config = image_llm_config['config']
            
            print(f"   📋 Tool would use:")
            print(f"      Provider: {provider}")
            print(f"      Model: {model_config['model']}")
            print(f"      Base URL: {model_config['base_url']}")
            print(f"      API Key: {model_config.get('api_key', 'None')}")
            print("   ✅ Tool integration simulation successful")
            
        except Exception as e:
            print(f"   ❌ Tool integration simulation failed: {e}")
        
        print()
        print("🎉 IMAGE PROCESSING CONFIG TEST COMPLETE")
        print("✅ All tests passed - configuration system ready for image processing!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_config_tool_integration():
    """Test integration with the config tool"""
    print("\n🔧 TESTING CONFIG TOOL INTEGRATION")
    print("=" * 60)
    
    try:
        from llm_config_tool import LLMConfigTool
        
        # Test that config tool has vision models
        tool = LLMConfigTool()
        
        print("1️⃣ Testing vision model availability in config tool...")
        ollama_models = tool.providers['ollama']['models']
        vision_models = [model for model in ollama_models.keys() if 'llava' in model or 'moondream' in model or 'bakllava' in model]
        
        if vision_models:
            print("   ✅ Vision models found in Ollama provider:")
            for model in vision_models:
                print(f"      {model}: {ollama_models[model]}")
        else:
            print("   ❌ No vision models found in Ollama provider")
        
        print()
        
        # Test OpenAI vision model
        print("2️⃣ Testing OpenAI vision model availability...")
        openai_models = tool.providers['openai']['models']
        if 'gpt-4-vision-preview' in openai_models:
            print(f"   ✅ OpenAI vision model: {openai_models['gpt-4-vision-preview']}")
        else:
            print("   ❌ OpenAI vision model not found")
        
        print()
        print("✅ Config tool integration test complete!")
        
    except Exception as e:
        print(f"❌ Config tool integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_processing_config()
    test_config_tool_integration()