#!/usr/bin/env python3
"""
Test UPDATING Existing Image Processing LLM Configuration
Tests scenarios where image processing config already exists and needs to be updated
"""

import sys
import os
import copy
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from llm_config_tool import LLMConfigTool
from utils.config_loader import config_loader

def test_update_existing_ollama_to_openai():
    """Test updating from Ollama llava to OpenAI vision"""
    print("🔄 TESTING UPDATE: Ollama → OpenAI")
    print("=" * 50)
    
    try:
        tool = LLMConfigTool()
        
        # Step 1: Start with existing Ollama config
        print("1️⃣ Setting initial Ollama configuration...")
        tool.update_image_processing_config('ollama', 'llava:7b')
        
        initial_config = tool.load_current_config()
        initial_img = initial_config['llm']['image_processing']
        print(f"   ✅ Initial: {initial_img['type']} - {initial_img['config']['model']}")
        
        # Store other LLM configs to verify they're preserved
        initial_primary = initial_config['llm']['primary'].copy()
        initial_tool_calling = initial_config['llm']['tool_calling'].copy()
        
        # Step 2: Update to OpenAI
        print("2️⃣ Updating to OpenAI configuration...")
        tool.update_image_processing_config('openai', 'gpt-4-vision-preview')
        
        updated_config = tool.load_current_config()
        updated_img = updated_config['llm']['image_processing']
        print(f"   ✅ Updated: {updated_img['type']} - {updated_img['config']['model']}")
        
        # Step 3: Verify update was successful
        if (updated_img['type'] == 'openai' and 
            updated_img['config']['model'] == 'gpt-4-vision-preview' and
            updated_img['config']['api_key'] == '${OPENAI_API_KEY}' and
            updated_img['config']['base_url'] == 'https://api.openai.com/v1'):
            print("   ✅ OpenAI configuration update successful")
        else:
            print(f"   ❌ OpenAI configuration update failed: {updated_img}")
            return False
            
        # Step 4: Verify other configs were preserved
        updated_primary = updated_config['llm']['primary']
        updated_tool_calling = updated_config['llm']['tool_calling']
        
        if (updated_primary == initial_primary and 
            updated_tool_calling == initial_tool_calling):
            print("   ✅ Other LLM configurations preserved")
        else:
            print("   ❌ Other LLM configurations were modified unexpectedly")
            print(f"      Primary changed: {updated_primary != initial_primary}")
            print(f"      Tool calling changed: {updated_tool_calling != initial_tool_calling}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing Ollama→OpenAI update: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_update_existing_openai_to_ollama():
    """Test updating from OpenAI vision back to Ollama"""
    print("\n🔄 TESTING UPDATE: OpenAI → Ollama")
    print("=" * 50)
    
    try:
        tool = LLMConfigTool()
        
        # Step 1: Start with OpenAI config (should already exist from previous test)
        print("1️⃣ Verifying current OpenAI configuration...")
        current_config = tool.load_current_config()
        current_img = current_config['llm']['image_processing']
        
        if current_img['type'] != 'openai':
            # Set it up first
            tool.update_image_processing_config('openai', 'gpt-4-vision-preview')
            current_config = tool.load_current_config()
            current_img = current_config['llm']['image_processing']
            
        print(f"   ✅ Current: {current_img['type']} - {current_img['config']['model']}")
        
        # Step 2: Update to different Ollama model
        print("2️⃣ Updating to Ollama bakllava...")
        tool.update_image_processing_config('ollama', 'bakllava')
        
        updated_config = tool.load_current_config()
        updated_img = updated_config['llm']['image_processing']
        print(f"   ✅ Updated: {updated_img['type']} - {updated_img['config']['model']}")
        
        # Step 3: Verify update was successful
        if (updated_img['type'] == 'ollama' and 
            updated_img['config']['model'] == 'bakllava' and
            updated_img['config']['api_key'] is None and
            updated_img['config']['base_url'] == 'http://127.0.0.1:11434'):
            print("   ✅ Ollama configuration update successful")
        else:
            print(f"   ❌ Ollama configuration update failed: {updated_img}")
            return False
            
        # Step 4: Verify OpenAI-specific settings were properly removed/changed
        if 'api_key' not in updated_img['config'] or updated_img['config']['api_key'] is None:
            print("   ✅ API key properly handled for local provider")
        else:
            print(f"   ❌ API key not properly handled: {updated_img['config'].get('api_key')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing OpenAI→Ollama update: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_update_model_within_provider():
    """Test updating model within the same provider"""
    print("\n🔄 TESTING UPDATE: Same Provider, Different Model")
    print("=" * 60)
    
    try:
        tool = LLMConfigTool()
        
        # Step 1: Set initial model
        print("1️⃣ Setting initial llava:7b configuration...")
        tool.update_image_processing_config('ollama', 'llava:7b')
        
        initial_config = tool.load_current_config()
        initial_img = initial_config['llm']['image_processing']
        print(f"   ✅ Initial: {initial_img['type']} - {initial_img['config']['model']}")
        
        # Store initial settings
        initial_timeout = initial_img['config']['timeout']
        initial_temperature = initial_img['config']['temperature']
        initial_base_url = initial_img['config']['base_url']
        
        # Step 2: Update to different model same provider
        print("2️⃣ Updating to llava:13b (same provider)...")
        tool.update_image_processing_config('ollama', 'llava:13b')
        
        updated_config = tool.load_current_config()
        updated_img = updated_config['llm']['image_processing']
        print(f"   ✅ Updated: {updated_img['type']} - {updated_img['config']['model']}")
        
        # Step 3: Verify model changed but other settings preserved
        if updated_img['config']['model'] == 'llava:13b':
            print("   ✅ Model successfully updated")
        else:
            print(f"   ❌ Model update failed: {updated_img['config']['model']}")
            return False
            
        # Step 4: Verify provider-specific settings were preserved
        if (updated_img['config']['timeout'] == initial_timeout and
            updated_img['config']['temperature'] == initial_temperature and
            updated_img['config']['base_url'] == initial_base_url):
            print("   ✅ Provider settings preserved during model update")
        else:
            print("   ❌ Provider settings changed unexpectedly")
            print(f"      Timeout: {initial_timeout} → {updated_img['config']['timeout']}")
            print(f"      Temperature: {initial_temperature} → {updated_img['config']['temperature']}")
            print(f"      Base URL: {initial_base_url} → {updated_img['config']['base_url']}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing same-provider model update: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loader_after_updates():
    """Test that config_loader correctly loads updated configurations"""
    print("\n📋 TESTING CONFIG LOADER AFTER UPDATES")
    print("=" * 50)
    
    try:
        # Clear cache to force reload
        config_loader._config_cache = None
        
        print("1️⃣ Testing config_loader after all updates...")
        image_config = config_loader.get_llm_config('image_processing')
        
        print(f"   ✅ Provider: {image_config['type']}")
        print(f"   ✅ Model: {image_config['config']['model']}")
        print(f"   ✅ Base URL: {image_config['config']['base_url']}")
        print(f"   ✅ API Key: {image_config['config'].get('api_key', 'None')}")
        
        # Step 2: Test that all LLM types still work
        print("2️⃣ Testing all LLM types after updates...")
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
        print(f"❌ Config loader test after updates failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compliance_after_updates():
    """Test that all configurations remain compliant after updates"""
    print("\n🔒 TESTING COMPLIANCE AFTER UPDATES")
    print("=" * 50)
    
    try:
        tool = LLMConfigTool()
        current_config = tool.load_current_config()
        
        print("1️⃣ Checking configuration structure integrity...")
        
        # Verify required sections exist
        required_sections = ['llm', 'performance', 'platform', 'security']
        for section in required_sections:
            if section in current_config:
                print(f"   ✅ {section}: Present")
            else:
                print(f"   ❌ {section}: Missing")
                return False
                
        # Verify LLM section structure
        llm_config = current_config['llm']
        required_llm_types = ['primary', 'tool_calling', 'image_processing']
        
        for llm_type in required_llm_types:
            if llm_type in llm_config:
                config_section = llm_config[llm_type]
                if 'type' in config_section and 'config' in config_section:
                    print(f"   ✅ {llm_type}: Properly structured")
                else:
                    print(f"   ❌ {llm_type}: Missing type or config")
                    return False
            else:
                print(f"   ❌ {llm_type}: Missing from configuration")
                return False
                
        print("2️⃣ Checking for security compliance...")
        
        # Check image processing config specifically
        img_config = llm_config['image_processing']
        api_key = img_config.get('config', {}).get('api_key')
        
        if api_key is None:
            print("   ✅ Local provider - no API key")
        elif isinstance(api_key, str) and api_key.startswith('${') and api_key.endswith('}'):
            print(f"   ✅ Proper environment variable: {api_key}")
        else:
            print(f"   ❌ Improper API key format: {api_key}")
            return False
            
        # Check for hardcoded secrets in entire config
        config_str = json.dumps(current_config, indent=2)
        forbidden_patterns = ['sk-', 'gsk_', 'AIza', '@gmail.com', 'password=']
        
        for pattern in forbidden_patterns:
            if pattern in config_str:
                print(f"   ❌ Security violation found: {pattern}")
                return False
                
        print("   ✅ No security violations found")
        
        return True
        
    except Exception as e:
        print(f"❌ Compliance check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all update tests"""
    print("🧪 COMPREHENSIVE IMAGE PROCESSING CONFIG UPDATE TESTS")
    print("=" * 70)
    
    tests = [
        ("Update Ollama→OpenAI", test_update_existing_ollama_to_openai),
        ("Update OpenAI→Ollama", test_update_existing_openai_to_ollama), 
        ("Update Model Within Provider", test_update_model_within_provider),
        ("Config Loader After Updates", test_config_loader_after_updates),
        ("Compliance After Updates", test_compliance_after_updates)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print(f"\n{'='*70}")
    print("📊 UPDATE TEST SUMMARY:")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        
    print(f"\n🎯 OVERALL: {passed}/{total} update tests passed")
    
    if passed == total:
        print("🎉 ALL UPDATE TESTS PASSED - Configuration updates work correctly!")
        return True
    else:
        print("⚠️  SOME UPDATE TESTS FAILED - Issues need to be addressed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)