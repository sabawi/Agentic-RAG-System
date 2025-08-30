#!/usr/bin/env python3
"""
Test script to specifically test title and header HTML escaping
"""
import sys
import os
sys.path.append('/home/sabawi/Development/flaskserver/user_tools')

from sandboxed_executor import SandboxedExecutorTool

# Test content with HTML in title
test_content = """# <script>alert('title hack')</script> Dangerous Title

This is content with a dangerous title that should be escaped properly.

The title contains script tags that could be dangerous if not escaped.
"""

async def test_title_escaping():
    """Test HTML entity escaping in titles and headers"""
    print("🧪 Testing title HTML entity escaping...")
    
    tool = SandboxedExecutorTool()
    
    # Test HTML file creation with dangerous title
    result = await tool._create_real_html_file("test_title_escaping.html", test_content)
    
    if result["success"]:
        file_path = result["result"]["full_path"]
        print(f"✅ Created HTML file: {file_path}")
        
        # Read the generated HTML to check for proper title escaping
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print("\n🔍 Checking for title/header escaping:")
        
        # Check if script tags in title are escaped
        if '<script>' in html_content:
            print("❌ SECURITY ISSUE: Unescaped <script> tags found in HTML!")
            # Find where script tags appear
            lines = html_content.split('\n')
            for i, line in enumerate(lines):
                if '<script>' in line:
                    print(f"   Line {i+1}: {line.strip()}")
        else:
            print("✅ No unescaped script tags found")
            
        # Check if title is properly escaped
        if '&lt;script&gt;' in html_content:
            print("✅ Script tags properly escaped in title")
        else:
            print("❌ Script tags may not be properly escaped")
            
        print(f"\n📄 HTML head section:")
        lines = html_content.split('\n')
        for i, line in enumerate(lines[:15]):  # First 15 lines
            if 'title' in line.lower() or 'script' in line.lower():
                print(f"   Line {i+1}: {line.strip()}")
                
    else:
        print(f"❌ Failed to create HTML file: {result['error']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_title_escaping())