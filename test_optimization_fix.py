#!/usr/bin/env python3
"""
Test the enhanced validation system that should catch content mismatches
"""

import asyncio
from optimization_safety import OptimizationValidator

async def test_content_mismatch_detection():
    """Test that the enhanced validation catches the cover letter failure"""
    
    validator = OptimizationValidator()
    
    # Simulate the exact failure case
    user_prompt = "included in the context is my resume in text format. Read it and extract key fields to fill all the data you need to complete your task: Please do the following: 1) craft and nicely written cover letter to accompany it to Mr. John Wheeler (sabawi@gmail.com), director of Software Development and Research at Crontab Technologies, LLC in Cleveland, OH. ensure it gets his positive attention. 2) write a short introductory email to Mr. Wheeler and include a nicely formatted HTML version of the cover letter along with a pdf formatted resume. 3) email the introductory email and attchach a) cover letter (use html format) and b) the included resume (use html format) to Mr.Wheeler and cc sabawi@yahoo.com on it"
    
    # The failed optimization output
    failed_optimization = """# OPTIMIZED ANALYSIS
**User Request**: craft cover letter and email to Mr. Wheeler

## Secure_Email_Sender Results
I'm unable to process your request as it appears to be a prompt for a different task, not related to financial news or analysis. If you have any questions or need assistance with financial data, market trends, or economic indicators, please let me know and I'll be happy to help.
"""
    
    # Mock tool results (minimal like the failure)
    tool_results = [
        {
            "tool": "secure_email_sender",
            "result": "Email scheduled for sending after content generation"
        }
    ]
    
    print("🧪 Testing Enhanced Validation System")
    print("=" * 60)
    
    result = await validator.validate_optimization(
        original_data=tool_results,
        optimized_input=failed_optimization,
        user_prompt=user_prompt
    )
    
    print(f"Validation Score: {result.score:.1f}")
    print(f"Is Safe: {result.is_safe}")
    print(f"Issues: {result.issues}")
    print(f"Critical Issues: {result.severity_counts['critical']}")
    
    # This should FAIL validation now
    if result.score < 75.0 and result.severity_counts["critical"] > 0:
        print("✅ SUCCESS: Enhanced validation correctly REJECTED the failed optimization!")
        print(f"   Score: {result.score:.1f} < 75.0 threshold")
        print(f"   Critical Issues: {result.severity_counts['critical']}")
        return True
    else:
        print("❌ FAILURE: Validation still passed the bad optimization")
        print(f"   Score: {result.score:.1f} >= 75.0 threshold")
        print(f"   Critical Issues: {result.severity_counts['critical']}")
        return False

async def test_good_optimization():
    """Test that good optimizations still pass"""
    
    validator = OptimizationValidator()
    
    user_prompt = "Create a cover letter for Mr. John Wheeler at Crontab Technologies"
    
    good_optimization = """# Cover Letter for Software Development Position

**User Request**: Create cover letter for Mr. John Wheeler at Crontab Technologies

## Email Composition
Dear Mr. Wheeler,

I am writing to express my strong interest in the Software Development position at Crontab Technologies, LLC. With my experience in software development and research, I believe I would be a valuable addition to your team.

My background includes extensive work in software engineering, system design, and research methodologies that align well with Crontab Technologies' mission and values.

I would welcome the opportunity to discuss how my skills and experience can contribute to your team's continued success.

Sincerely,
[Your Name]

## Next Steps
This cover letter has been formatted and is ready for email delivery to Mr. Wheeler.
"""
    
    tool_results = [
        {
            "tool": "secure_email_sender",
            "result": "Email composition complete with professional formatting"
        }
    ]
    
    result = await validator.validate_optimization(
        original_data=tool_results,
        optimized_input=good_optimization,
        user_prompt=user_prompt
    )
    
    print(f"\n🧪 Testing Good Optimization")
    print("=" * 30)
    print(f"Validation Score: {result.score:.1f}")
    print(f"Is Safe: {result.is_safe}")
    print(f"Issues: {result.issues}")
    
    if result.score >= 75.0 and result.is_safe:
        print("✅ SUCCESS: Good optimization correctly PASSED validation!")
        return True
    else:
        print("❌ FAILURE: Good optimization was incorrectly rejected")
        return False

if __name__ == "__main__":
    async def run_tests():
        test1 = await test_content_mismatch_detection()
        test2 = await test_good_optimization()
        
        print("\n" + "=" * 60)
        if test1 and test2:
            print("🎉 ALL TESTS PASSED: Enhanced validation system working correctly!")
        else:
            print("❌ SOME TESTS FAILED: Need further debugging")
            
    asyncio.run(run_tests())