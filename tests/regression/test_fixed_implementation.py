#!/usr/bin/env python3
"""
Test the fixed image_to_text implementation with bakllava
"""
import base64
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from user_tools.image_to_text import ImageToTextTool
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_fixed_implementation():
    """Test the fixed implementation"""
    
    # Test with the real image that was failing
    image_path = './sandbox_workspace/binomial_distribution.png'
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return False
    
    print(f"🖼️ Testing fixed implementation with: {image_path}")
    
    # Read and encode the image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    print(f"📏 Image size: {len(image_bytes)} bytes, Base64: {len(base64_string)} chars")
    
    # Test the tool
    tool = ImageToTextTool()
    
    print(f"🔧 Tool model config: {tool.vision_config.get('model', 'unknown')}")
    
    try:
        print("📤 Executing image_to_text tool...")
        result = await tool.execute(
            prompt="Describe this chart in detail, including what type of distribution it shows and any notable features.",
            image=base64_string
        )
        
        print(f"📊 Result success: {result.get('success', False)}")
        
        if result.get('success'):
            description = result.get('description', '')
            print(f"✅ Success! Description: {description[:200]}...")
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Tool failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during execution: {e}")
        return False

def test_sync_version():
    """Test sync version for easier debugging"""
    
    image_path = './sandbox_workspace/binomial_distribution.png'
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return False
    
    print(f"🖼️ Testing sync version with: {image_path}")
    
    # Read and encode the image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    
    # Test the tool's sync method directly
    tool = ImageToTextTool()
    
    print(f"🔧 Tool model config: {tool.vision_config.get('model', 'unknown')}")
    
    try:
        print("📤 Calling get_image_processing_results...")
        result = tool.get_image_processing_results({
            'prompt': "Describe this chart in detail.",
            'image': base64_string
        })
        
        print(f"📊 Result success: {result.get('success', False)}")
        
        if result.get('success'):
            description = result.get('description', '')
            print(f"✅ Success! Description: {description[:200]}...")
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Tool failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during execution: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔬 Testing Fixed Image-to-Text Implementation")
    print("=" * 50)
    
    # Test sync version (easier to debug)
    sync_result = test_sync_version()
    
    print(f"\n📋 Results:")
    print(f"  Sync version: {'✅ Works' if sync_result else '❌ Failed'}")
    
    if sync_result:
        print("\n💡 Fix confirmed! The issue was the vision model, not the format.")
        print("   bakllava:latest works correctly with our base64 format.")
    else:
        print("\n💡 Still has issues - may need further investigation")