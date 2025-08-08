#!/usr/bin/env python3
"""
Direct test of tool calling logic to debug why read_file is still being called
"""

import asyncio
import sys
import os
import json

# Add the server directory to Python path
sys.path.append('/home/sabawi/Development/flaskserver')

from fastapi_server_complete import load_tool_model_system_prompt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tool_calling_direct():
    """Test tool calling logic directly"""
    
    print("🔍 DIRECT TOOL CALLING TEST")
    print("=" * 60)
    
    # Test the system prompt loading
    print("1. Testing system prompt loading...")
    user_system_prompt = ""  # Empty like after user removed it
    system_content = load_tool_model_system_prompt(user_system_prompt)
    
    print(f"System prompt length: {len(system_content)} chars")
    
    # Check if DATA-ALREADY-PROVIDED section is in the prompt
    if "DATA-ALREADY-PROVIDED SCENARIOS" in system_content:
        print("✅ Found DATA-ALREADY-PROVIDED section in system prompt")
    else:
        print("❌ DATA-ALREADY-PROVIDED section NOT found in system prompt!")
    
    # Check nuclear rule at the top
    if "RESUME/COVER LETTER NUCLEAR RULE" in system_content:
        print("✅ Found NUCLEAR RULE at top of system prompt")
    else:
        print("❌ Nuclear rule NOT found!")
    
    # Check specific instructions
    if "DO NOT try to read non-existent files with read_file" in system_content:
        print("✅ Found read_file prohibition instructions")
    else:
        print("❌ read_file prohibition instructions NOT found!")
    
    # Check resume detection patterns
    if "RESUME DATA DETECTION PATTERNS" in system_content:
        print("✅ Found resume detection patterns")
    else:
        print("❌ Resume detection patterns NOT found!")
    
    # Print relevant section for debugging
    print("\n2. Nuclear Rule section (TOP of prompt):")
    print("-" * 50)
    lines = system_content.split('\n')
    for i, line in enumerate(lines):
        if "NUCLEAR RULE" in line:
            # Print this line and next 15 lines
            for j in range(i, min(i+16, len(lines))):
                print(f"{j+1:3d}: {lines[j]}")
            break
    
    print("\n3. Resume Detection Patterns section:")
    print("-" * 50)
    for i, line in enumerate(lines):
        if "DETECTION PATTERNS" in line:
            # Print this line and next 10 lines
            for j in range(i, min(i+11, len(lines))):
                print(f"{j+1:3d}: {lines[j]}")
            break
    
    print("\n4. System Prompt Analysis Complete")
    print("=" * 60)
    
    # Check if the issue is with the tool calling model's interpretation
    if "DATA-ALREADY-PROVIDED SCENARIOS" in system_content and "DO NOT try to read non-existent files" in system_content:
        print("✅ System prompt contains correct instructions")
        print("🤔 Issue may be with tool calling model's interpretation or caching")
        print("\nRecommendation: The system prompt is correct. The issue may be:")
        print("   1. Tool calling model ignoring the instructions")
        print("   2. Model caching/context issues")
        print("   3. Model not properly understanding the scenario")
        print("   4. Need to make instructions even more explicit")
    else:
        print("❌ System prompt is missing critical instructions")
        print("🔧 Need to fix the system prompt file")

if __name__ == "__main__":
    test_tool_calling_direct()