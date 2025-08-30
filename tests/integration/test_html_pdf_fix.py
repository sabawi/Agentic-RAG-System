#!/usr/bin/env python3

import sys
import os

# Add the user_tools directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
user_tools_dir = os.path.join(current_dir, 'user_tools')
sys.path.insert(0, user_tools_dir)

from _universal_pdf_generator import UniversalPDFGenerator

def test_html_content_processing():
    """Test the PDF generator with HTML content similar to what the LLM might produce"""
    
    # Simulate HTML content that might come from an LLM
    html_content = """<html>
<head><title>Stock Analysis Report</title></head>
<body>
<h1>Comprehensive Stock Analysis Report</h1>
<h2>Executive Summary</h2>
<p>This report provides a comprehensive analysis of stock performance and market trends.</p>

<h3>Key Findings</h3>
<ul>
<li>Market volatility has increased by 15%</li>
<li>Technology sector shows strong growth potential</li>
<li>Energy sector remains challenged</li>
</ul>

<h2>Detailed Analysis</h2>
<p>The current market conditions indicate <strong>strong performance</strong> in the following areas:</p>
<blockquote>Market analysts predict continued growth in the tech sector.</blockquote>

<h3>Recommendations</h3>
<ol>
<li>Diversify portfolio across multiple sectors</li>
<li>Monitor volatility indicators closely</li>
<li>Consider long-term investment strategies</li>
</ol>

<div class="footer">
<p><em>Generated on 2025-08-05</em></p>
</div>
</body>
</html>"""

    print("Testing HTML content processing...")
    
    generator = UniversalPDFGenerator()
    
    # Test the _clean_markdown function directly
    cleaned_content = generator._clean_markdown(html_content)
    
    print("Original HTML content (first 200 chars):")
    print(html_content[:200] + "...")
    print()
    
    print("Cleaned content (first 500 chars):")
    print(cleaned_content[:500] + "...")
    print()
    
    # Create test PDF
    output_path = "/tmp/test_html_fix.pdf"
    success = generator.create_pdf(
        title="HTML Test Report",
        content=html_content,
        output_path=output_path
    )
    
    print(f"PDF creation: {'✅ Success' if success else '❌ Failed'}")
    
    if success:
        # Check file size
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"PDF file size: {file_size} bytes")
            
            # Use file command to verify it's a real PDF
            import subprocess
            try:
                result = subprocess.run(['file', output_path], capture_output=True, text=True)
                print(f"File type: {result.stdout.strip()}")
            except:
                print("Could not verify file type")
        
    return success

if __name__ == "__main__":
    test_html_content_processing()