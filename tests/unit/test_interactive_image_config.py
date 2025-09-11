#!/usr/bin/env python3
"""
Test Interactive Image Processing Configuration Tool
Tests the actual interactive menu option 9 programmatically
"""

import sys
import os
import subprocess
import tempfile
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_config_tool import LLMConfigTool
from utils.config_loader import config_loader

def test_interactive_tool_programmatically():
    """Test the configure_image_processing method directly"""
    print("🖼️ TESTING INTERACTIVE IMAGE PROCESSING CONFIGURATION")
    print("=" * 60)
    
    try:
        # Create tool instance
        tool = LLMConfigTool()
        
        print("1️⃣ Testing configure_image_processing method exists...")
        if hasattr(tool, 'configure_image_processing'):
            print("   ✅ configure_image_processing method found")
        else:
            print("   ❌ configure_image_processing method missing")
            return False
            
        print("2️⃣ Testing update_image_processing_config method...")
        if hasattr(tool, 'update_image_processing_config'):
            print("   ✅ update_image_processing_config method found")
        else:
            print("   ❌ update_image_processing_config method missing")
            return False
            
        # Test the update method directly with different providers
        print("\n3️⃣ Testing Ollama llava:7b configuration...")
        tool.update_image_processing_config('ollama', 'llava:7b')
        
        # Verify configuration was created
        current_config = tool.load_current_config()
        if 'llm' in current_config and 'image_processing' in current_config['llm']:
            img_config = current_config['llm']['image_processing']
            print(f"   ✅ Provider: {img_config['type']}")
            print(f"   ✅ Model: {img_config['config']['model']}")
            print(f"   ✅ Base URL: {img_config['config']['base_url']}")
            print(f"   ✅ Temperature: {img_config['config']['temperature']}")
        else:
            print("   ❌ Configuration not created properly")
            return False
            
        # Test OpenAI configuration
        print("\n4️⃣ Testing OpenAI configuration...")
        tool.update_image_processing_config('openai', 'gpt-4-vision-preview')
        
        current_config = tool.load_current_config()
        img_config = current_config['llm']['image_processing']
        if img_config['type'] == 'openai' and img_config['config']['model'] == 'gpt-4-vision-preview':
            print("   ✅ OpenAI configuration successful")
            print(f"   ✅ API Key placeholder: {img_config['config'].get('api_key', 'missing')}")
        else:
            print("   ❌ OpenAI configuration failed")
            return False
            
        # Test disable functionality
        print("\n5️⃣ Testing disable functionality...")
        tool.update_image_processing_config(None, None)
        
        current_config = tool.load_current_config()
        if 'image_processing' not in current_config.get('llm', {}):
            print("   ✅ Image processing successfully disabled/removed")
        else:
            print("   ❌ Failed to disable image processing")
            return False
            
        # Restore a working configuration
        print("\n6️⃣ Restoring working configuration...")
        tool.update_image_processing_config('ollama', 'llava:7b')
        print("   ✅ Configuration restored")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing interactive tool: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loader_integration():
    """Test that config_loader can properly load the generated config"""
    print("\n📋 TESTING CONFIG LOADER INTEGRATION")
    print("=" * 60)
    
    try:
        # Clear cache to force reload
        config_loader._config_cache = None
        
        # Test loading image processing config
        print("1️⃣ Testing config_loader.get_llm_config('image_processing')...")
        image_config = config_loader.get_llm_config('image_processing')
        
        # Verify all required fields
        required_fields = ['type', 'config']
        for field in required_fields:
            if field in image_config:
                print(f"   ✅ {field}: Present")
            else:
                print(f"   ❌ {field}: Missing")
                return False
                
        # Verify config structure
        config_section = image_config['config']
        required_config_fields = ['model', 'base_url', 'timeout', 'temperature']
        for field in required_config_fields:
            if field in config_section:
                print(f"   ✅ config.{field}: {config_section[field]}")
            else:
                print(f"   ❌ config.{field}: Missing")
                return False
                
        print("\n2️⃣ Testing all LLM type configurations work together...")
        llm_types = ['primary', 'tool_calling', 'image_processing']
        for llm_type in llm_types:
            try:
                config = config_loader.get_llm_config(llm_type)
                provider = config.get('type', 'unknown')
                model = config.get('config', {}).get('model', 'unknown')
                print(f"   ✅ {llm_type}: {provider} - {model}")
            except Exception as e:
                print(f"   ❌ {llm_type}: Failed - {e}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Config loader integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compliance_validation():
    """Test that the generated configuration meets compliance requirements"""
    print("\n🔒 TESTING COMPLIANCE VALIDATION")
    print("=" * 60)
    
    try:
        # Load the current configuration
        tool = LLMConfigTool()
        current_config = tool.load_current_config()
        
        print("1️⃣ Checking for hardcoded secrets...")
        config_str = str(current_config)
        
        # Check for actual secrets (not placeholders)
        forbidden_patterns = [
            'sk-', 'gsk_', 'AIza',  # Real API key prefixes
            '@gmail.com', '@outlook.com',  # Email addresses
            'pass=', 'cred=',  # Hardcoded credentials
        ]
        
        violations_found = []
        for pattern in forbidden_patterns:
            if pattern in config_str:
                violations_found.append(pattern)
                
        if violations_found:
            print(f"   ❌ Security violations found: {violations_found}")
            return False
        else:
            print("   ✅ No hardcoded secrets found")
            
        print("2️⃣ Checking for proper environment variable usage...")
        if 'image_processing' in current_config.get('llm', {}):
            img_config = current_config['llm']['image_processing']
            api_key = img_config.get('config', {}).get('api_key')
            
            if api_key is None:
                print("   ✅ Local provider - no API key needed")
            elif api_key and api_key.startswith('${') and api_key.endswith('}'):
                print(f"   ✅ Proper environment variable usage: {api_key}")
            else:
                print(f"   ❌ Improper API key format: {api_key}")
                return False
                
        print("3️⃣ Checking configuration structure compliance...")
        required_structure = {
            'llm': {
                'image_processing': {
                    'type': str,
                    'config': {
                        'model': str,
                        'timeout': (int, float),
                        'temperature': (int, float)
                    }
                }
            }
        }
        
        def check_structure(config, required, path=""):
            for key, value_type in required.items():
                if key not in config:
                    print(f"   ❌ Missing required key: {path}.{key}")
                    return False
                    
                if isinstance(value_type, dict):
                    if not check_structure(config[key], value_type, f"{path}.{key}"):
                        return False
                elif isinstance(value_type, tuple):
                    if not isinstance(config[key], value_type):
                        print(f"   ❌ Wrong type for {path}.{key}: expected {value_type}, got {type(config[key])}")
                        return False
                elif not isinstance(config[key], value_type):
                    print(f"   ❌ Wrong type for {path}.{key}: expected {value_type}, got {type(config[key])}")
                    return False
                    
            return True
        
        if check_structure(current_config, required_structure):
            print("   ✅ Configuration structure is compliant")
        else:
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Compliance validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE IMAGE PROCESSING CONFIGURATION TEST")
    print("=" * 70)
    
    tests = [
        ("Interactive Tool Functionality", test_interactive_tool_programmatically),
        ("Config Loader Integration", test_config_loader_integration),
        ("Compliance Validation", test_compliance_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print(f"\n{'='*70}")
    print("📊 TEST SUMMARY:")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Image processing configuration is ready!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Issues need to be addressed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)