#!/usr/bin/env python3
"""
Debug HTML entity escaping through the processing pipeline
"""
import html

# Test content
test_content = 'Double quotes: "quoted text" and single quotes: \'single quotes\''

print("🧪 Testing HTML entity escaping pipeline:")
print(f"Original: {test_content}")

# Step 1: HTML escape
escaped = html.escape(test_content, quote=True)
print(f"After html.escape(): {escaped}")

# Step 2: BeautifulSoup processing (simulating _clean_html_content)
from bs4 import BeautifulSoup

# Wrap in HTML to simulate what happens in the pipeline
html_wrapped = f"<p>{escaped}</p>"
print(f"HTML wrapped: {html_wrapped}")

soup = BeautifulSoup(html_wrapped, 'html.parser')
soup_result = str(soup)
print(f"After BeautifulSoup: {soup_result}")

# Check if entities are preserved
if '&quot;' in soup_result:
    print("✅ Quotes remain escaped after BeautifulSoup")
else:
    print("❌ Quotes were unescaped by BeautifulSoup!")

if '&#x27;' in soup_result or '&#39;' in soup_result or '&apos;' in soup_result:
    print("✅ Single quotes remain escaped after BeautifulSoup")
else:
    print("❌ Single quotes were unescaped by BeautifulSoup!")