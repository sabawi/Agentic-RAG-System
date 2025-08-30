#!/usr/bin/env python3
"""
Test the fuzzy attachment matching functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# 🔧 ROBUST PROJECT ROOT DISCOVERY - Works from any subdirectory
def find_project_root():
    """Find project root by looking for marker files/directories"""
    markers = ['user_tools', 'sandbox_workspace', 'config', 'fastapi_server_complete.py']
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if sum(1 for marker in markers if (parent / marker).exists()) >= 3:
            return str(parent)
    return os.getcwd()

project_root = find_project_root()
sys.path.insert(0, project_root)

from user_tools.secure_email_sender import SecureEmailSenderTool

async def test_fuzzy_attachment_matching():
    """Test fuzzy matching for attachment resolution"""
    print("🧪 Testing Fuzzy Attachment Matching")
    print("=" * 60)
    
    email_tool = SecureEmailSenderTool()
    
    # Test cases that should find fuzzy matches
    test_cases = [
        ("Cover Letter.pdf", "should match cover_letter.pdf"),
        ("Resume.pdf", "should match resume_al_sabawi.pdf or resume.pdf"),
        ("cover_letter_to_john_wheeler.pdf", "should match exact file"),
        ("RESUME.PDF", "should match resume.pdf (case insensitive)"),
        ("Analysis Report.pdf", "should match analysis_report_2025-08-05_04-36.pdf"),
    ]
    
    print("\n📁 Available files in sandbox:")
    sandbox_path = os.path.join(os.getcwd(), "sandbox_workspace")
    available_files = [f for f in os.listdir(sandbox_path) if f.endswith('.pdf')][:10]  # Show first 10
    for f in available_files:
        print(f"   - {f}")
    
    print(f"\n🔍 Testing {len(test_cases)} fuzzy matching scenarios:")
    
    for i, (requested_file, description) in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{requested_file}'")
        print(f"   Expected: {description}")
        
        # Test the fuzzy matching directly
        fuzzy_match = email_tool._find_fuzzy_attachment_match(requested_file)
        
        if fuzzy_match:
            print(f"   ✅ FOUND: {fuzzy_match.name}")
            print(f"   📍 Full path: {fuzzy_match}")
        else:
            print(f"   ❌ NOT FOUND")
    
    print("\n" + "="*60)
    print("🧪 Testing email with fuzzy attachments...")
    
    # Test actual email sending with fuzzy attachment matching
    try:
        result = await email_tool.execute(
            to_email="test@example.com",
            subject="Fuzzy Attachment Test",
            body="Testing fuzzy attachment matching",
            attachments="Cover Letter.pdf, Resume.pdf"  # These should fuzzy match
        )
        
        if result["success"]:
            print("✅ Email with fuzzy attachments sent successfully!")
            print(f"   Result: {result['result']}")
        else:
            print("❌ Email sending failed")
            print(f"   Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_fuzzy_attachment_matching())