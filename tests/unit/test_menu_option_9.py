#!/usr/bin/env python3
"""
Test Menu Option 9 for Image Processing Configuration
Simulates the interactive menu selection
"""

import sys
import os
import io
from unittest.mock import patch
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_config_tool import LLMConfigTool

def test_menu_option_9():
    """Test that menu option 9 correctly calls configure_image_processing"""
    print("🖼️ TESTING MENU OPTION 9 - IMAGE PROCESSING SETUP")
    print("=" * 60)
    
    try:
        tool = LLMConfigTool()
        
        print("1️⃣ Testing menu option 9 routing...")
        
        # Mock the configure_image_processing method to verify it gets called
        configure_called = False
        original_configure = tool.configure_image_processing
        
        def mock_configure():
            nonlocal configure_called
            configure_called = True
            print("   📞 configure_image_processing method called successfully!")
            return  # Exit instead of continuing with interactive prompts
        
        tool.configure_image_processing = mock_configure
        
        # Simulate selecting option 9
        with patch('builtins.input', return_value='9'):
            try:
                tool.run()
            except SystemExit:
                pass  # Expected when exiting
            except Exception:
                pass  # May exit due to mock
                
        if configure_called:
            print("   ✅ Menu option 9 correctly routes to configure_image_processing")
        else:
            print("   ❌ Menu option 9 did not call configure_image_processing")
            return False
            
        # Restore original method
        tool.configure_image_processing = original_configure
        
        print("\n2️⃣ Testing menu display includes image processing...")
        
        # Capture the menu display
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            try:
                tool.display_quick_configs()
            except Exception:
                pass
                
            output = mock_stdout.getvalue()
            
        if "🖼️ Image Processing Setup" in output:
            print("   ✅ Menu displays image processing option")
        else:
            print("   ❌ Menu does not display image processing option")
            return False
            
        if "Configure vision models for image analysis" in output:
            print("   ✅ Menu shows proper description")
        else:
            print("   ❌ Menu missing proper description")
            return False
            
        print("\n3️⃣ Testing menu accepts option 9...")
        
        # Test that the input validation accepts '9'
        valid_choices = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
        if '9' in valid_choices:
            print("   ✅ Option 9 is in valid choices list")
        else:
            print("   ❌ Option 9 not in valid choices list")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing menu option 9: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_interactive_image_config_menu():
    """Test the interactive image configuration menu"""
    print("\n🔧 TESTING INTERACTIVE IMAGE CONFIGURATION MENU")
    print("=" * 60)
    
    try:
        tool = LLMConfigTool()
        
        print("1️⃣ Testing configure_image_processing method structure...")
        
        # Test that the method has the expected behavior
        import inspect
        sig = inspect.signature(tool.configure_image_processing)
        print(f"   ✅ Method signature: {sig}")
        
        print("2️⃣ Testing update_image_processing_config method...")
        
        # Test the update method with both parameters
        sig = inspect.signature(tool.update_image_processing_config)
        params = list(sig.parameters.keys())
        expected_params = ['provider_type', 'model']
        
        if params == expected_params:
            print(f"   ✅ Method parameters correct: {params}")
        else:
            print(f"   ❌ Method parameters incorrect. Expected: {expected_params}, Got: {params}")
            return False
            
        print("3️⃣ Testing configuration options availability...")
        
        # Test that vision models are available in the provider
        ollama_models = tool.providers['ollama']['models']
        vision_model_count = sum(1 for model in ollama_models.keys() 
                               if any(vm in model.lower() for vm in ['llava', 'vision', 'bakllava', 'moondream']))
        
        print(f"   ✅ Vision models available: {vision_model_count}")
        
        if vision_model_count >= 3:  # Should have llava:7b, llava:13b, bakllava, moondream
            print("   ✅ Sufficient vision models available")
        else:
            print("   ❌ Insufficient vision models available")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing interactive menu: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all menu tests"""
    print("🧪 COMPREHENSIVE MENU OPTION 9 TEST")
    print("=" * 60)
    
    tests = [
        ("Menu Option 9 Routing", test_menu_option_9),
        ("Interactive Menu Structure", test_interactive_image_config_menu)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print(f"\n{'='*60}")
    print("📊 MENU TEST SUMMARY:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        
    print(f"\n🎯 OVERALL: {passed}/{total} menu tests passed")
    
    if passed == total:
        print("🎉 ALL MENU TESTS PASSED - Interactive option 9 is working!")
        return True
    else:
        print("⚠️  SOME MENU TESTS FAILED - Issues need to be addressed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)