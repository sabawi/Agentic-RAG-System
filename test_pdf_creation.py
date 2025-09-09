#!/usr/bin/env python3
"""
Test PDF creation directly using the PDFGeneratorTool
"""

import asyncio
import sys
import os
sys.path.append('/home/sabawi/Development/flaskserver')

from user_tools.pdf_generator_tool import PDFGeneratorTool

async def test_pdf_generation():
    """Test that PDFGeneratorTool creates proper binary PDFs"""
    print("🧪 Testing PDFGeneratorTool directly...")
    
    pdf_tool = PDFGeneratorTool()
    
    result = await pdf_tool.execute(
        content="# Test Document\n\nThis is a test with **bold** text and *italic* text.\n\n- Bullet point 1\n- Bullet point 2\n\n## Summary\nThis should create a proper PDF.",
        filename="test_direct_pdf.pdf",
        title="Direct PDF Test",
        subtitle="Testing PDFGeneratorTool functionality",
        content_type="markdown"
    )
    
    print(f"Result: {result}")
    
    if result.get('success'):
        pdf_path = result.get('pdf_path')
        print(f"PDF created at: {pdf_path}")
        
        # Check if it's a proper PDF
        import subprocess
        file_result = subprocess.run(['file', pdf_path], capture_output=True, text=True)
        print(f"File type: {file_result.stdout.strip()}")
        
        # Check file size
        if os.path.exists(pdf_path):
            size = os.path.getsize(pdf_path)
            print(f"File size: {size} bytes")
            
            # Try to read first few bytes (PDF should start with %PDF)
            with open(pdf_path, 'rb') as f:
                first_bytes = f.read(10)
                print(f"First 10 bytes: {first_bytes}")
                
                if first_bytes.startswith(b'%PDF'):
                    print("✅ PROPER PDF - starts with %PDF magic bytes")
                    return True
                else:
                    print("❌ BROKEN - not a proper PDF file")
                    return False
        else:
            print("❌ File not created")
            return False
    else:
        print("❌ PDF generation failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_pdf_generation())
    print(f"\n🎯 Result: {'✅ SUCCESS' if success else '❌ FAILURE'}")