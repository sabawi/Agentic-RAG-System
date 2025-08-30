#!/usr/bin/env python3
"""
Test script to demonstrate HTML entity escaping bug
"""
import sys
import os
sys.path.append('/home/sabawi/Development/flaskserver/user_tools')

from sandboxed_executor import SandboxedExecutorTool

# Test content with problematic HTML characters
test_content = """# Test Report: HTML Characters

This content contains HTML characters that should be escaped:

- Less than: < symbol
- Greater than: > symbol  
- Ampersand: & symbol
- Double quotes: "quoted text" here
- Single quotes: 'quoted text' here
- Combined: <div class="test" id='example'>Content & More</div>

## Code Example
```javascript
if (x < 5 && y > "test's value") {
    console.log('Hello "World" & Universe');
}
```

## List with entities:
- Item with < and >
- Item with & and "quotes"
- Item with 'single quotes' and &amp; entity
"""

async def test_html_entities():
    """Test HTML entity escaping in HTML file generation"""
    print("🧪 Testing HTML entity escaping bug...")
    
    tool = SandboxedExecutorTool()
    
    # Test HTML file creation
    result = await tool._create_real_html_file("test_entities_bug.html", test_content)
    
    if result["success"]:
        file_path = result["result"]["full_path"]
        print(f"✅ Created HTML file: {file_path}")
        
        # Read the generated HTML to check for proper escaping
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print("\n🔍 Checking for HTML entity issues:")
        issues_found = []
        
        # Check for unescaped HTML characters in content
        if '< symbol' in html_content and '&lt; symbol' not in html_content:
            issues_found.append("❌ Unescaped < character found")
        if '> symbol' in html_content and '&gt; symbol' not in html_content:
            issues_found.append("❌ Unescaped > character found") 
        if '"quoted text"' in html_content and '&quot;quoted text&quot;' not in html_content:
            issues_found.append("❌ Unescaped double quotes found")
        if "'quoted text'" in html_content and '&#39;quoted text&#39;' not in html_content:
            issues_found.append("❌ Unescaped single quotes found")
        if 'Content & More' in html_content and 'Content &amp; More' not in html_content:
            issues_found.append("❌ Unescaped ampersand found")
            
        if issues_found:
            print("🚨 HTML Entity Escaping Issues Found:")
            for issue in issues_found:
                print(f"   {issue}")
            print(f"\n📄 Generated HTML preview (first 500 chars):")
            print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
        else:
            print("✅ No HTML entity issues detected")
            
    else:
        print(f"❌ Failed to create HTML file: {result['error']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_html_entities())