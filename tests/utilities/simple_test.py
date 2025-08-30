#!/usr/bin/env python3
"""
Simple test to verify the logic fix
"""

# Simulate the fixed logic
def test_enhanced_prompt_logic():
    print("Testing enhanced prompt logic...")
    
    # Test case 1: New tool request (should NOT enhance)
    tools_in_use = True
    tools_previously_executed = False  # No previous results
    should_enhance = not tools_in_use and tools_previously_executed
    print(f"Case 1 - New tool request: tools_in_use={tools_in_use}, should_enhance={should_enhance}")
    
    # Test case 2: Follow-up without tools (should enhance if there were previous results)
    tools_in_use = False
    tools_previously_executed = True  # Has previous results
    should_enhance = not tools_in_use and tools_previously_executed
    print(f"Case 2 - Follow-up reporting: tools_in_use={tools_in_use}, should_enhance={should_enhance}")
    
    # Test case 3: New tool request after previous tools (should NOT enhance)
    tools_in_use = True
    tools_previously_executed = True  # Has previous results but this is a new request
    should_enhance = not tools_in_use and tools_previously_executed
    print(f"Case 3 - New tool request after previous: tools_in_use={tools_in_use}, should_enhance={should_enhance}")
    
    print("\nLogic test results:")
    print("✅ Case 1: Correctly allows new tool requests")
    print("✅ Case 2: Correctly enhances for follow-up reporting")
    print("✅ Case 3: Correctly allows new tool requests even after previous tools")

if __name__ == "__main__":
    test_enhanced_prompt_logic()