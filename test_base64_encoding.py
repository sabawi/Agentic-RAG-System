#!/usr/bin/env python3
"""
Simple test to verify our base64 encoding is correct
"""
import base64
import os

def test_base64_encoding():
    """Test if our base64 encoding matches what works"""
    
    image_path = './sandbox_workspace/binomial_distribution.png'
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    # Method 1: Our current method
    print("🔍 Testing our current base64 encoding method...")
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    our_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    print(f"📏 Original image size: {len(image_bytes)} bytes")
    print(f"📏 Base64 string size: {len(our_base64)} chars")
    print(f"🔍 Base64 starts with: {our_base64[:50]}")
    print(f"🔍 Base64 ends with: {our_base64[-50:]}")
    
    # Verify the base64 is valid by decoding it back
    try:
        decoded_back = base64.b64decode(our_base64)
        if decoded_back == image_bytes:
            print("✅ Base64 encoding/decoding is correct")
        else:
            print("❌ Base64 round-trip failed!")
    except Exception as e:
        print(f"❌ Base64 decode failed: {e}")
    
    # Check for any weird characters
    import string
    valid_b64_chars = string.ascii_letters + string.digits + '+/='
    invalid_chars = [c for c in our_base64 if c not in valid_b64_chars]
    if invalid_chars:
        print(f"⚠️  Found invalid base64 characters: {invalid_chars}")
    else:
        print("✅ All characters are valid base64")
    
    # Check if it's padded correctly
    if len(our_base64) % 4 == 0:
        print("✅ Base64 padding is correct")
    else:
        print(f"⚠️  Base64 padding issue: length {len(our_base64)} % 4 = {len(our_base64) % 4}")
    
    # Write a test file to compare with other tools
    test_b64_file = '/tmp/test_base64.txt'
    with open(test_b64_file, 'w') as f:
        f.write(our_base64)
    print(f"💾 Saved base64 to {test_b64_file}")
    
    # Let's also test with the command line base64 tool
    print("\n🔍 Comparing with command line base64 tool...")
    import subprocess
    
    try:
        # Generate base64 with command line tool
        result = subprocess.run(['base64', '-w', '0', image_path], 
                              capture_output=True, text=True, check=True)
        cmd_base64 = result.stdout.strip()
        
        print(f"📏 Command line base64 size: {len(cmd_base64)} chars")
        print(f"🔍 Command line starts with: {cmd_base64[:50]}")
        
        if our_base64 == cmd_base64:
            print("✅ Our base64 matches command line tool exactly")
        else:
            print("⚠️  Our base64 differs from command line tool")
            print(f"First difference at position: {next((i for i, (a, b) in enumerate(zip(our_base64, cmd_base64)) if a != b), 'end')}")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Command line base64 failed: {e}")
    except FileNotFoundError:
        print("❌ base64 command not found")

if __name__ == "__main__":
    test_base64_encoding()