#!/usr/bin/env python3
"""
Create a minimal valid PNG for testing
"""
import base64
import sys

try:
    from PIL import Image
    
    # Create a minimal 1x1 red image
    img = Image.new('RGB', (1, 1), color='red')
    img.save('/tmp/minimal.png')
    print("✅ Created minimal PNG at /tmp/minimal.png")
    
    # Also test with the image
    with open('/tmp/minimal.png', 'rb') as f:
        img_bytes = f.read()
    
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    print(f"📏 Size: {len(img_bytes)} bytes, Base64: {len(base64_str)} chars")
    print(f"🔍 Base64: {base64_str}")
    
except ImportError:
    print("❌ PIL not available, trying alternative approach")
    # Use a known good minimal PNG (transparent 1x1)
    minimal_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    minimal_png_bytes = base64.b64decode(minimal_png_b64)
    
    with open('/tmp/minimal.png', 'wb') as f:
        f.write(minimal_png_bytes)
    
    print(f"✅ Created minimal PNG from base64")
    print(f"📏 Size: {len(minimal_png_bytes)} bytes")
    print(f"🔍 Base64: {minimal_png_b64}")