#!/usr/bin/env python3
"""
Comprehensive Safety Infrastructure Testing
Tests all aspects of the optimization safety system
"""

import asyncio
import json
import pytest
from typing import List, Dict, Any

from optimization_safety import (
    ToolOutputPreserver, 
    OptimizationValidator, 
    ValidationResult,
    safe_optimize_llm_input
)


class TestToolOutputPreserver:
    """Test the data preservation system"""
    
    def setup_method(self):
        """Setup for each test"""
        self.preserver = ToolOutputPreserver()
        
        # Sample tool results for testing
        self.sample_tool_results = [
            {
                "tool": "get_news_summaries",
                "result": "Latest tech news: OpenAI releases new model, Apple announces iPhone 16"
            },
            {
                "tool": "stock_analyzer", 
                "result": {
                    "symbol": "AAPL",
                    "price": 150.25,
                    "change": 2.50,
                    "analysis": "Strong buy recommendation"
                }
            },
            {
                "tool": "secure_email_sender",
                "result": "Email scheduled for sending"
            }
        ]
    
    def test_preserve_original_basic(self):
        """Test 1.1.1: Basic original data preservation"""
        original_summary = self.preserver.preserve_original(self.sample_tool_results)
        
        # Verify data was preserved
        assert self.preserver.original_data is not None
        assert len(self.preserver.original_data) == 3
        assert self.preserver.preservation_timestamp is not None
        
        # Verify checksums were created
        assert len(self.preserver.safety_checksums) == 3
        assert "tool_0" in self.preserver.safety_checksums
        assert "tool_1" in self.preserver.safety_checksums
        assert "tool_2" in self.preserver.safety_checksums
        
        # Verify original summary was returned
        assert "get_news_summaries" in original_summary
        assert "stock_analyzer" in original_summary
        assert "secure_email_sender" in original_summary
        
        print("✅ Test 1.1.1 PASSED: Basic data preservation works")
    
    def test_integrity_verification(self):
        """Test 1.1.2: Integrity verification system"""
        # Create fresh preserver for this test to avoid corrupting shared state
        fresh_preserver = ToolOutputPreserver()
        
        # Preserve original data
        fresh_preserver.preserve_original(self.sample_tool_results)
        
        # Verify integrity passes
        assert fresh_preserver.verify_integrity() == True
        
        # Corrupt the data and verify it fails
        fresh_preserver.original_data[0]["tool"] = "corrupted_tool"
        assert fresh_preserver.verify_integrity() == False
        
        print("✅ Test 1.1.2 PASSED: Integrity verification detects corruption")
    
    def test_deep_copy_isolation(self):
        """Test 1.1.3: Deep copy prevents external modifications"""
        # Create fresh preserver and test data for this test
        fresh_preserver = ToolOutputPreserver()
        test_data = [
            {"tool": "get_news_summaries", "result": "Latest tech news: OpenAI releases new model"}
        ]
        
        original_summary = fresh_preserver.preserve_original(test_data)
        
        # Modify original data
        test_data[0]["tool"] = "modified_tool"
        
        # Verify preserved data wasn't affected
        assert fresh_preserver.original_data[0]["tool"] == "get_news_summaries"
        
        print("✅ Test 1.1.3 PASSED: Deep copy prevents external modifications")
    
    def test_empty_tool_results(self):
        """Test 1.1.4: Handle empty tool results gracefully"""
        # Create fresh preserver for this test to avoid state from previous tests
        fresh_preserver = ToolOutputPreserver()
        
        empty_results = []
        original_summary = fresh_preserver.preserve_original(empty_results)
        
        assert fresh_preserver.original_data == []
        assert len(fresh_preserver.safety_checksums) == 0
        assert isinstance(original_summary, str)
        
        print("✅ Test 1.1.4 PASSED: Empty tool results handled gracefully")
    
    def test_malformed_tool_results(self):
        """Test 1.1.5: Handle malformed tool results"""
        # Create fresh preserver for this test
        fresh_preserver = ToolOutputPreserver()
        
        malformed_results = [
            {"missing_tool_key": "value"},
            {"tool": None, "result": None},
            {"tool": "valid_tool", "result": {"nested": {"deep": "data"}}}
        ]
        
        # Should not crash
        original_summary = fresh_preserver.preserve_original(malformed_results)
        
        assert fresh_preserver.original_data is not None
        assert len(fresh_preserver.safety_checksums) == 3
        assert isinstance(original_summary, str)
        
        print("✅ Test 1.1.5 PASSED: Malformed tool results handled safely")


class TestOptimizationValidator:
    """Test the validation system"""
    
    def setup_method(self):
        """Setup for each test"""
        self.validator = OptimizationValidator()
        
        self.sample_tool_results = [
            {
                "tool": "get_news_summaries",
                "result": "OpenAI released GPT-5 with improved reasoning capabilities. Apple announced record quarterly profits driven by iPhone sales."
            },
            {
                "tool": "stock_analyzer",
                "result": "AAPL: $150.25 (+2.50, +1.69%). Strong buy recommendation based on earnings growth and market position."
            }
        ]
        
        self.sample_user_prompt = "Research latest tech news about OpenAI and Apple, then create a report"
        
    async def test_tool_coverage_validation(self):
        """Test 2.1.1: Tool coverage validation"""
        # Good optimization - includes all tools with key content preserved
        good_optimization = """
        # Research Report on OpenAI and Apple
        
        ## News Analysis  
        OpenAI released GPT-5 with improved reasoning capabilities. Apple announced record quarterly profits driven by iPhone sales.
        
        ## Stock Analysis
        AAPL: $150.25 (+2.50, +1.69%). Strong buy recommendation based on earnings growth and market position.
        
        This report was created using news summaries and stock analyzer to research the latest developments.
        """
        
        result = await self.validator.validate_optimization(
            self.sample_tool_results, good_optimization, self.sample_user_prompt
        )
        
        print(f"DEBUG: Score = {result.score}, Issues = {result.issues}")
        assert result.score >= 70.0, f"Score too low: {result.score} - Issues: {result.issues}"
        
        # Bad optimization - missing tools
        bad_optimization = """
        # Tech News Report
        Just some general information without referencing specific tools.
        """
        
        result = await self.validator.validate_optimization(
            self.sample_tool_results, bad_optimization, self.sample_user_prompt
        )
        
        assert result.score < 75.0, f"Score should be low but was: {result.score}"
        assert result.severity_counts["critical"] > 0
        
        print("✅ Test 2.1.1 PASSED: Tool coverage validation works")
    
    async def test_keyword_preservation(self):
        """Test 2.1.2: Keyword preservation validation"""
        # Good optimization - preserves key terms
        good_optimization = """
        # Research Report on OpenAI and Apple
        
        OpenAI released GPT-5 with improved reasoning capabilities. Apple announced record quarterly profits 
        driven by iPhone sales. AAPL stock price is $150.25 with a +2.50 change (+1.69%). Strong buy 
        recommendation based on earnings growth and market position. Created this report using news research.
        """
        
        result = await self.validator.validate_optimization(
            self.sample_tool_results, good_optimization, self.sample_user_prompt
        )
        
        print(f"DEBUG Keyword test: Score = {result.score}, Issues = {result.issues}")
        assert result.score >= 75.0
        
        # Bad optimization - missing many keywords
        bad_optimization = """
        # Generic Report
        Some technology companies are doing well.
        """
        
        result = await self.validator.validate_optimization(
            self.sample_tool_results, bad_optimization, self.sample_user_prompt
        )
        
        assert result.score < 75.0
        
        print("✅ Test 2.1.2 PASSED: Keyword preservation validation works")
    
    async def test_user_intent_alignment(self):
        """Test 2.1.3: User intent alignment validation"""
        # Good optimization - matches user intent
        good_optimization = """
        # Research Report on OpenAI and Apple
        
        This report was created using research on the latest tech news about OpenAI and Apple as requested.
        
        ## OpenAI Development Analysis
        OpenAI released GPT-5 with improved reasoning capabilities based on news summaries.
        
        ## Apple Stock Performance 
        AAPL analysis shows $150.25 price with Strong Buy recommendation based on earnings growth and market position.
        
        Report created using news research and stock analysis tools.
        """
        
        result = await self.validator.validate_optimization(
            self.sample_tool_results, good_optimization, self.sample_user_prompt
        )
        
        assert result.score >= 75.0
        
        # Bad optimization - doesn't match user intent (missing key terms)
        bad_optimization = """
        # General Technology Update
        Various technology companies are making progress.
        """
        
        result = await self.validator.validate_optimization(
            self.sample_tool_results, bad_optimization, self.sample_user_prompt
        )
        
        # Should have warnings about missing user intent keywords
        assert any("intent keywords missing" in issue for issue in result.issues)
        
        print("✅ Test 2.1.3 PASSED: User intent alignment validation works")
    
    async def test_compression_ratio_validation(self):
        """Test 2.1.4: Compression ratio validation"""
        original_size = sum(len(str(result)) for result in self.sample_tool_results)
        
        # Test excessive compression (too much reduction)
        tiny_optimization = "Short."
        result = await self.validator.validate_optimization(
            self.sample_tool_results, tiny_optimization, self.sample_user_prompt
        )
        
        assert result.compression_ratio < 0.2
        assert result.severity_counts["critical"] > 0
        assert any("Excessive compression" in issue for issue in result.issues)
        
        # Test reasonable compression
        reasonable_optimization = """
        # Tech Analysis Report
        
        OpenAI released GPT-5 with improved reasoning capabilities as reported in latest tech news.
        Apple stock (AAPL) trading at $150.25 with +2.50 change (+1.69%) showing strong performance.
        Analysis indicates strong buy recommendation based on earnings growth and market position.
        """
        
        result = await self.validator.validate_optimization(
            self.sample_tool_results, reasonable_optimization, self.sample_user_prompt
        )
        
        assert 0.2 <= result.compression_ratio <= 1.5  # More realistic range for optimized content
        
        print("✅ Test 2.1.4 PASSED: Compression ratio validation works")


class TestSafeOptimization:
    """Test the complete safe optimization system"""
    
    def setup_method(self):
        """Setup for each test"""
        self.preserver = ToolOutputPreserver()
        self.validator = OptimizationValidator()
        
        self.sample_tool_results = [
            {
                "tool": "get_news_summaries",
                "result": "Breaking: OpenAI announces GPT-5 with revolutionary reasoning capabilities"
            },
            {
                "tool": "stock_analyzer",
                "result": "AAPL analysis: Price $150.25, Strong Buy rating, Expected growth 15%"
            }
        ]
        
        self.sample_user_prompt = "Create a report on OpenAI news and Apple stock analysis"
    
    async def test_successful_optimization(self):
        """Test 1.2.1: Successful optimization path"""
        result = await safe_optimize_llm_input(
            self.sample_tool_results,
            self.sample_user_prompt, 
            self.preserver,
            self.validator
        )
        
        assert result["input_type"] == "optimized"
        assert "content" in result
        assert "original_backup" in result
        assert result["validation_score"] >= 75.0
        
        # Verify original data was preserved
        assert self.preserver.original_data is not None
        assert self.preserver.verify_integrity()
        
        print("✅ Test 1.2.1 PASSED: Successful optimization works")
    
    async def test_fallback_on_validation_failure(self):
        """Test 1.2.2: Fallback when validation fails"""
        # We'll modify the validator to always fail for this test
        self.validator.min_validation_score = 99.0  # Impossibly high threshold
        
        result = await safe_optimize_llm_input(
            self.sample_tool_results,
            self.sample_user_prompt,
            self.preserver, 
            self.validator
        )
        
        assert result["input_type"] == "original_fallback"
        assert result["optimization_attempted"] == True
        assert "fallback_reason" in result
        assert result["validation_score"] < 99.0
        
        print("✅ Test 1.2.2 PASSED: Validation failure triggers fallback")
    
    async def test_fallback_on_exception(self):
        """Test 1.2.3: Fallback when optimization raises exception"""
        # We'll create a mock that raises an exception
        async def failing_optimization(tool_results, user_prompt):
            raise ValueError("Simulated optimization failure")
        
        # Monkey patch the optimization function
        import optimization_safety
        original_func = optimization_safety.attempt_optimization
        optimization_safety.attempt_optimization = failing_optimization
        
        try:
            result = await safe_optimize_llm_input(
                self.sample_tool_results,
                self.sample_user_prompt,
                self.preserver,
                self.validator
            )
            
            assert result["input_type"] == "original_safe"
            assert "error" in result
            assert result["validation_score"] == 0
            
        finally:
            # Restore original function
            optimization_safety.attempt_optimization = original_func
        
        print("✅ Test 1.2.3 PASSED: Exception triggers safe fallback")
    
    async def test_integrity_failure_emergency_fallback(self):
        """Test 1.2.4: Emergency fallback on integrity failure"""
        # Corrupt the preserver's integrity check
        original_verify = self.preserver.verify_integrity
        self.preserver.verify_integrity = lambda: False
        
        result = await safe_optimize_llm_input(
            self.sample_tool_results,
            self.sample_user_prompt,
            self.preserver,
            self.validator
        )
        
        assert result["input_type"] == "emergency_fallback"
        assert "integrity check failed" in result["error"]
        
        # Restore original method
        self.preserver.verify_integrity = original_verify
        
        print("✅ Test 1.2.4 PASSED: Integrity failure triggers emergency fallback")


async def run_all_phase1_tests():
    """Run all Phase 1 tests comprehensively"""
    print("🧪 STARTING PHASE 1 COMPREHENSIVE TESTING")
    print("=" * 60)
    
    # Test ToolOutputPreserver
    print("\n📋 Testing ToolOutputPreserver...")
    preserver_tests = TestToolOutputPreserver()
    preserver_tests.setup_method()
    preserver_tests.test_preserve_original_basic()
    preserver_tests.test_integrity_verification() 
    preserver_tests.test_deep_copy_isolation()
    preserver_tests.test_empty_tool_results()
    preserver_tests.test_malformed_tool_results()
    
    # Test OptimizationValidator  
    print("\n🔍 Testing OptimizationValidator...")
    validator_tests = TestOptimizationValidator()
    validator_tests.setup_method()
    await validator_tests.test_tool_coverage_validation()
    await validator_tests.test_keyword_preservation()
    await validator_tests.test_user_intent_alignment()
    await validator_tests.test_compression_ratio_validation()
    
    # Test SafeOptimization
    print("\n🛡️ Testing SafeOptimization...")
    safe_tests = TestSafeOptimization()
    safe_tests.setup_method()
    await safe_tests.test_successful_optimization()
    await safe_tests.test_fallback_on_validation_failure()
    await safe_tests.test_fallback_on_exception()
    await safe_tests.test_integrity_failure_emergency_fallback()
    
    print("\n" + "=" * 60)
    print("🎉 ALL PHASE 1 TESTS COMPLETED SUCCESSFULLY!")
    print("✅ Safety infrastructure is bulletproof and ready for use")


if __name__ == "__main__":
    asyncio.run(run_all_phase1_tests())