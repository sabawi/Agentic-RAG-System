#!/usr/bin/env python3
"""
Test Interactive Updates via Menu Option 9
Test the actual interactive configure_image_processing method with different scenarios
"""

import sys
import os
import io
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_config_tool import LLMConfigTool
from utils.config_loader import config_loader

def test_interactive_local_model_selection():
    """Test the interactive local model selection (option 1)"""
    print("🖼️ TESTING INTERACTIVE LOCAL MODEL SELECTION")
    print("=" * 60)
    
    try:
        tool = LLMConfigTool()
        
        # Mock the interactive inputs for local model selection
        # Simulate: Option 1 (Local models), then model choice 2 (llava:13b)
        mock_inputs = ['1', '2']  # 1 = Local models, 2 = llava:13b
        
        print("1️⃣ Testing local model selection interaction...")
        
        with patch('builtins.input', side_effect=mock_inputs):
            try:
                tool.configure_image_processing()
            except (SystemExit, KeyboardInterrupt, EOFError):
                pass  # Expected when method completes
                
        # Verify the configuration was set
        current_config = tool.load_current_config()
        if 'image_processing' in current_config.get('llm', {}):
            img_config = current_config['llm']['image_processing']
            if img_config['type'] == 'ollama' and img_config['config']['model'] == 'llava:13b':
                print("   ✅ Interactive local model selection successful")
                print(f"   ✅ Set to: {img_config['type']} - {img_config['config']['model']}")
                return True
            else:
                print(f"   ❌ Wrong configuration: {img_config}")
                return False
        else:
            print("   ❌ Image processing configuration not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing interactive local selection: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_interactive_cloud_provider_selection():
    """Test the interactive cloud provider selection (option 2)"""
    print("\n☁️ TESTING INTERACTIVE CLOUD PROVIDER SELECTION") 
    print("=" * 60)
    
    try:
        tool = LLMConfigTool()
        
        # Mock the interactive inputs for cloud provider selection
        # Simulate: Option 2 (Cloud APIs), then provider choice 1 (OpenAI)
        mock_inputs = ['2', '1']  # 2 = Cloud APIs, 1 = OpenAI
        
        print("1️⃣ Testing cloud provider selection interaction...")
        
        with patch('builtins.input', side_effect=mock_inputs):
            try:
                tool.configure_image_processing()
            except (SystemExit, KeyboardInterrupt, EOFError):
                pass  # Expected when method completes
                
        # Verify the configuration was set
        current_config = tool.load_current_config()
        if 'image_processing' in current_config.get('llm', {}):
            img_config = current_config['llm']['image_processing']
            if (img_config['type'] == 'openai' and 
                img_config['config']['model'] == 'gpt-4-vision-preview' and
                img_config['config']['api_key'] == '${OPENAI_API_KEY}'):
                print("   ✅ Interactive cloud provider selection successful")
                print(f"   ✅ Set to: {img_config['type']} - {img_config['config']['model']}")
                print(f"   ✅ API key: {img_config['config']['api_key']}")
                return True
            else:
                print(f"   ❌ Wrong configuration: {img_config}")
                return False
        else:
            print("   ❌ Image processing configuration not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing interactive cloud selection: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_interactive_disable_functionality():
    """Test the interactive disable functionality (option 3)"""
    print("\n❌ TESTING INTERACTIVE DISABLE FUNCTIONALITY")
    print("=" * 60)
    
    try:
        tool = LLMConfigTool()
        
        # Ensure there's a config to disable first
        tool.update_image_processing_config('ollama', 'llava:7b')
        
        # Mock the interactive input for disable
        # Simulate: Option 3 (Disable)
        mock_inputs = ['3']  # 3 = Disable
        
        print("1️⃣ Testing disable functionality interaction...")
        
        with patch('builtins.input', side_effect=mock_inputs):
            try:
                tool.configure_image_processing()
            except (SystemExit, KeyboardInterrupt, EOFError):
                pass  # Expected when method completes
                
        # Verify the configuration was removed
        current_config = tool.load_current_config()
        if 'image_processing' not in current_config.get('llm', {}):
            print("   ✅ Interactive disable functionality successful")
            print("   ✅ Image processing configuration removed")
            return True
        else:
            print("   ❌ Image processing configuration still exists")
            return False
            
    except Exception as e:
        print(f"❌ Error testing interactive disable: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_updates_preserve_other_settings():
    """Test that interactive updates preserve other configuration settings"""
    print("\n🔒 TESTING PRESERVATION OF OTHER SETTINGS")
    print("=" * 60)
    
    try:
        tool = LLMConfigTool()
        
        # Get initial state of other configurations
        print("1️⃣ Capturing initial configuration state...")
        initial_config = tool.load_current_config()
        initial_primary = initial_config['llm']['primary'].copy()
        initial_tool_calling = initial_config['llm']['tool_calling'].copy()
        initial_performance = initial_config.get('performance', {}).copy()
        initial_platform = initial_config.get('platform', {}).copy()
        
        # Perform an interactive update
        print("2️⃣ Performing interactive configuration update...")
        mock_inputs = ['1', '1']  # Local models, llava:7b
        
        with patch('builtins.input', side_effect=mock_inputs):
            try:
                tool.configure_image_processing()
            except (SystemExit, KeyboardInterrupt, EOFError):
                pass
                
        # Verify other settings were preserved
        print("3️⃣ Verifying other settings were preserved...")
        updated_config = tool.load_current_config()
        updated_primary = updated_config['llm']['primary']
        updated_tool_calling = updated_config['llm']['tool_calling'] 
        updated_performance = updated_config.get('performance', {})
        updated_platform = updated_config.get('platform', {})
        
        checks = [
            ("Primary LLM config", initial_primary == updated_primary),
            ("Tool calling config", initial_tool_calling == updated_tool_calling),
            ("Performance config", initial_performance == updated_performance),
            ("Platform config", initial_platform == updated_platform)
        ]
        
        all_preserved = True
        for check_name, preserved in checks:
            if preserved:
                print(f"   ✅ {check_name}: Preserved")
            else:
                print(f"   ❌ {check_name}: Modified unexpectedly")
                all_preserved = False
                
        return all_preserved
        
    except Exception as e:
        print(f"❌ Error testing settings preservation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_final_state_compliance():
    """Test that the final configuration state is compliant"""
    print("\n🔒 TESTING FINAL STATE COMPLIANCE")
    print("=" * 60)
    
    try:
        # Ensure we have a working config
        tool = LLMConfigTool()
        tool.update_image_processing_config('ollama', 'llava:7b')
        
        # Clear config cache and test loading
        config_loader._config_cache = None
        
        print("1️⃣ Testing final config loading...")
        image_config = config_loader.get_llm_config('image_processing')
        
        required_fields = {
            'type': str,
            'config': dict
        }
        
        for field, expected_type in required_fields.items():
            if field in image_config and isinstance(image_config[field], expected_type):
                print(f"   ✅ {field}: Present and correct type")
            else:
                print(f"   ❌ {field}: Missing or wrong type")
                return False
                
        print("2️⃣ Testing config structure compliance...")
        config_section = image_config['config']
        required_config_fields = ['model', 'base_url', 'timeout', 'temperature']
        
        for field in required_config_fields:
            if field in config_section:
                print(f"   ✅ config.{field}: {config_section[field]}")
            else:
                print(f"   ❌ config.{field}: Missing")
                return False
                
        print("3️⃣ Testing integration with other LLM types...")
        all_types = ['primary', 'tool_calling', 'image_processing']
        
        for llm_type in all_types:
            try:
                config = config_loader.get_llm_config(llm_type)
                provider = config['type']
                model = config['config']['model']
                print(f"   ✅ {llm_type}: {provider} - {model}")
            except Exception as e:
                print(f"   ❌ {llm_type}: Failed - {e}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Final state compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all interactive update tests"""
    print("🧪 COMPREHENSIVE INTERACTIVE UPDATE TESTS")
    print("=" * 70)
    
    tests = [
        ("Interactive Local Model Selection", test_interactive_local_model_selection),
        ("Interactive Cloud Provider Selection", test_interactive_cloud_provider_selection),
        ("Interactive Disable Functionality", test_interactive_disable_functionality),
        ("Settings Preservation", test_config_updates_preserve_other_settings),
        ("Final State Compliance", test_final_state_compliance)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print(f"\n{'='*70}")
    print("📊 INTERACTIVE UPDATE TEST SUMMARY:")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        
    print(f"\n🎯 OVERALL: {passed}/{total} interactive tests passed")
    
    if passed == total:
        print("🎉 ALL INTERACTIVE UPDATE TESTS PASSED!")
        return True
    else:
        print("⚠️  SOME INTERACTIVE TESTS FAILED - Issues need to be addressed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)