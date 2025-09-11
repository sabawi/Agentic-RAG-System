#!/usr/bin/env python3
"""
Test Constants Compliance
Verify that hardcoded values have been replaced with constants and everything works correctly
"""

import sys
import os
import re
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.llm_constants import *
from utils.config_loader import config_loader
from llm_config_tool import LLMConfigTool

def test_constants_import():
    """Test that constants can be imported and have expected values"""
    print("📦 TESTING CONSTANTS IMPORT AND VALUES")
    print("=" * 50)
    
    try:
        # Test that all constants are defined
        constants_to_check = [
            ('DEFAULT_PRIMARY_TIMEOUT', DEFAULT_PRIMARY_TIMEOUT, 600),
            ('DEFAULT_SECONDARY_TIMEOUT', DEFAULT_SECONDARY_TIMEOUT, 300),
            ('DEFAULT_SECONDARY_TEMPERATURE', DEFAULT_SECONDARY_TEMPERATURE, 0.1),
            ('DEFAULT_CONTEXT_WINDOW_SIZE', DEFAULT_CONTEXT_WINDOW_SIZE, 8192),
            ('DEFAULT_IMAGE_PROCESSING_MAX_TOKENS', DEFAULT_IMAGE_PROCESSING_MAX_TOKENS, 2048),
            ('OLLAMA_DEFAULT_BASE_URL', OLLAMA_DEFAULT_BASE_URL, 'http://127.0.0.1:11434'),
            ('OPENAI_BASE_URL', OPENAI_BASE_URL, 'https://api.openai.com/v1'),
            ('DEFAULT_IMAGE_PROCESSING_MODEL', DEFAULT_IMAGE_PROCESSING_MODEL, 'llava:7b'),
            ('ENV_OPENAI_API_KEY', ENV_OPENAI_API_KEY, '${OPENAI_API_KEY}'),
        ]
        
        print("1️⃣ Checking constant definitions and values...")
        for const_name, const_value, expected_value in constants_to_check:
            if const_value == expected_value:
                print(f"   ✅ {const_name}: {const_value}")
            else:
                print(f"   ❌ {const_name}: Expected {expected_value}, got {const_value}")
                return False
                
        print("2️⃣ Checking vision models constants...")
        if 'llava:7b' in VISION_MODELS_OLLAMA and 'gpt-4-vision-preview' in VISION_MODELS_OPENAI:
            print("   ✅ Vision models constants defined correctly")
        else:
            print("   ❌ Vision models constants missing or incorrect")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Constants import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loader_with_constants():
    """Test that config_loader works correctly with constants"""
    print("\n📋 TESTING CONFIG LOADER WITH CONSTANTS")
    print("=" * 50)
    
    try:
        # Clear cache to force reload
        config_loader._config_cache = None
        
        print("1️⃣ Testing default configuration generation...")
        default_config = config_loader._get_default_config()
        
        # Check that constants are being used
        image_config = default_config['llm']['image_processing']
        
        expected_values = {
            'base_url': OLLAMA_DEFAULT_BASE_URL,
            'model': DEFAULT_IMAGE_PROCESSING_MODEL,
            'timeout': DEFAULT_SECONDARY_TIMEOUT,
            'temperature': DEFAULT_SECONDARY_TEMPERATURE,
            'max_tokens': DEFAULT_IMAGE_PROCESSING_MAX_TOKENS
        }
        
        for field, expected_value in expected_values.items():
            if image_config['config'][field] == expected_value:
                print(f"   ✅ {field}: {image_config['config'][field]}")
            else:
                print(f"   ❌ {field}: Expected {expected_value}, got {image_config['config'][field]}")
                return False
                
        print("2️⃣ Testing config loading...")
        image_config = config_loader.get_llm_config('image_processing')
        
        if (image_config['type'] in ['ollama', 'openai'] and
            'model' in image_config['config'] and
            'base_url' in image_config['config']):
            print("   ✅ Config loading works with constants")
        else:
            print(f"   ❌ Config loading failed: {image_config}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Config loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_config_tool_with_constants():
    """Test that LLMConfigTool works correctly with constants"""
    print("\n🔧 TESTING LLM CONFIG TOOL WITH CONSTANTS")
    print("=" * 50)
    
    try:
        tool = LLMConfigTool()
        
        print("1️⃣ Testing tool initialization with constants...")
        if (OLLAMA_DEFAULT_BASE_URL in str(tool.providers) and
            OPENAI_BASE_URL in str(tool.providers)):
            print("   ✅ Tool providers use constants for URLs")
        else:
            print("   ❌ Tool providers not using constants")
            return False
            
        print("2️⃣ Testing configuration creation with constants...")
        tool.update_image_processing_config('ollama', DEFAULT_IMAGE_PROCESSING_MODEL)
        
        current_config = tool.load_current_config()
        img_config = current_config['llm']['image_processing']
        
        if (img_config['config']['model'] == DEFAULT_IMAGE_PROCESSING_MODEL and
            img_config['config']['base_url'] == OLLAMA_DEFAULT_BASE_URL and
            img_config['config']['timeout'] == DEFAULT_SECONDARY_TIMEOUT):
            print("   ✅ Tool creates config using constants")
        else:
            print(f"   ❌ Tool not using constants: {img_config['config']}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ LLM config tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_no_hardcoded_values_remain():
    """Test that no hardcoded values remain in the code"""
    print("\n🔍 TESTING FOR REMAINING HARDCODED VALUES")
    print("=" * 50)
    
    try:
        files_to_check = [
            'utils/config_loader.py',
            'llm_config_tool.py'
        ]
        
        # Patterns that should NOT appear (hardcoded values)
        forbidden_patterns = [
            r"'timeout': 300(?![a-zA-Z_])",  # Not followed by letter/underscore (to avoid constants)
            r"'timeout': 600(?![a-zA-Z_])",
            r"'temperature': 0\.1(?![a-zA-Z_])",
            r"'max_tokens': 2048(?![a-zA-Z_])",
            r"'context_window_size': 8192(?![a-zA-Z_])",
            r"'base_url': 'http://127\.0\.0\.1:11434'",
            r"'base_url': 'https://api\.openai\.com/v1'",
            r"'model': 'llava:7b'",
        ]
        
        print("1️⃣ Scanning for hardcoded patterns...")
        violations_found = []
        
        for file_path in files_to_check:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                for pattern in forbidden_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        violations_found.append(f"{file_path}: {pattern} -> {matches}")
        
        if violations_found:
            print("   ❌ Hardcoded values found:")
            for violation in violations_found:
                print(f"      {violation}")
            return False
        else:
            print("   ✅ No hardcoded values found in scanned files")
            
        print("2️⃣ Checking for proper constant usage...")
        
        # Check that constants are actually being used
        constant_patterns = [
            'DEFAULT_SECONDARY_TIMEOUT',
            'DEFAULT_IMAGE_PROCESSING_MAX_TOKENS',
            'OLLAMA_DEFAULT_BASE_URL',
            'DEFAULT_IMAGE_PROCESSING_MODEL'
        ]
        
        constants_used = []
        for file_path in files_to_check:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                for pattern in constant_patterns:
                    if pattern in content:
                        constants_used.append(f"{file_path}: {pattern}")
        
        if len(constants_used) >= 4:  # Should have multiple constants used
            print("   ✅ Constants are being properly used")
            for usage in constants_used[:4]:  # Show first few examples
                print(f"      {usage}")
        else:
            print("   ❌ Constants not being used properly")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Hardcoded values scan failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all constants compliance tests"""
    print("🧪 COMPREHENSIVE CONSTANTS COMPLIANCE TEST")
    print("=" * 60)
    
    tests = [
        ("Constants Import and Values", test_constants_import),
        ("Config Loader with Constants", test_config_loader_with_constants),
        ("LLM Config Tool with Constants", test_llm_config_tool_with_constants),
        ("No Hardcoded Values Remain", test_no_hardcoded_values_remain)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print(f"\n{'='*60}")
    print("📊 CONSTANTS COMPLIANCE SUMMARY:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL CONSTANTS COMPLIANCE TESTS PASSED!")
        print("✅ No hardcoded values found - all constants properly used!")
        return True
    else:
        print("⚠️  SOME COMPLIANCE TESTS FAILED - Hardcoded values still exist")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)