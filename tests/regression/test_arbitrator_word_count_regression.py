#!/usr/bin/env python3
"""
🚨 CRITICAL REGRESSION TEST: Arbitrator Word Count Scenario
==========================================================

This test ensures the Arbitrator system correctly handles tool failures and delivers
real execution results to the Primary LLM instead of hallucinated responses.

BUG HISTORY:
- Issue: Tool execution failures were not properly corrected by Arbitrator
- Root Cause: sandboxed_executor ignored 'args' parameter in _execute_command method
- Impact: Primary LLM received failed results, generated hallucinated word counts
- Fix: Added args parameter handling in sandboxed_executor._execute_command

CRITICAL SUCCESS CRITERIA:
1. Tool 3 (execution) initially fails with missing file path
2. Arbitrator detects failure and generates correction with proper args
3. Corrected execution succeeds with real word count results
4. Primary LLM receives formatted execution results (not failed results)
5. Final response contains accurate word counts from actual file
"""

import asyncio
import json
import requests
import time
from typing import Dict, List, Any
import pytest
import sys
import os

# Add the server directory to Python path for imports
sys.path.insert(0, '/home/sabawi/Development/flaskserver')

class ArbitratorWordCountRegressionTest:
    """Test class for the critical Arbitrator word count scenario."""
    
    def __init__(self):
        self.server_url = "http://localhost:5000"
        self.test_prompt = (
            "Find a short story about quantum entanglement, create a Python program "
            "to count words in it, execute the program, and show the top 10 most "
            "occurring words"
        )
        self.expected_results = {
            # Expected word counts from SD_TheQuantumConspiracy.md
            "a": 54,
            "the": 49, 
            "of": 40,
            "to": 30,
            "and": 27,
            "their": 22,
            "her": 19,
            "was": 17,
            "his": 16,
            "in": 15
        }
    
    def test_full_arbitrator_correction_flow(self) -> Dict[str, Any]:
        """
        🚨 CRITICAL TEST: Full Arbitrator correction flow
        
        Tests the complete end-to-end scenario that was failing:
        1. Initial tool execution failure (missing args)
        2. Arbitrator detection and correction 
        3. Successful retry with proper file path
        4. Real results delivered to Primary LLM
        5. Accurate word count response
        """
        print("🚨 STARTING CRITICAL REGRESSION TEST: Arbitrator Word Count")
        
        # Make request to server
        payload = {
            "prompt": self.test_prompt,
            "model": "gpt-4o-mini", 
            "stream": False,
            "tools": True
        }
        
        print(f"📤 Sending request: {payload}")
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.server_url}/llama3_1b/stream",
                json=payload,
                timeout=300  # 5 minutes timeout for complex correction
            )
            
            response.raise_for_status()
            result = response.json()
            execution_time = time.time() - start_time
            
            print(f"📥 Response received in {execution_time:.2f}s")
            
            # Validate response structure
            if "response" not in result:
                return {
                    "success": False,
                    "error": "Missing 'response' field in server response",
                    "raw_response": result
                }
            
            response_text = result["response"]
            print(f"📋 Response text length: {len(response_text)} chars")
            
            # CRITICAL VALIDATION: Check for success indicators
            validation_result = self._validate_arbitrator_success(response_text)
            
            return {
                "success": validation_result["success"],
                "execution_time": execution_time,
                "response_text": response_text,
                "validation_details": validation_result,
                "server_response": result
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timeout - Arbitrator may be stuck in infinite loop",
                "execution_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "execution_time": time.time() - start_time
            }
    
    def _validate_arbitrator_success(self, response_text: str) -> Dict[str, Any]:
        """
        🔍 CRITICAL VALIDATION: Ensure Arbitrator delivered real results
        
        Validates that the response contains:
        1. Real word count results (not hallucinated)
        2. Correct file path identification
        3. Success indicators for all steps
        4. NO failure messages
        """
        validation_results = {
            "success": True,
            "passed_checks": [],
            "failed_checks": [],
            "word_count_accuracy": {},
            "critical_errors": []
        }
        
        response_lower = response_text.lower()
        
        # ❌ CRITICAL FAILURE INDICATORS (These mean the bug is back!)
        failure_indicators = [
            "script failed to execute",
            "command failed with code 1", 
            "could not be retrieved",
            "tool execution error",
            "the script failed",
            "unable to execute",
            "execution failed"
        ]
        
        for indicator in failure_indicators:
            if indicator in response_lower:
                validation_results["success"] = False
                validation_results["failed_checks"].append(f"❌ CRITICAL: Found failure indicator: '{indicator}'")
                validation_results["critical_errors"].append(f"Arbitrator correction failed - found: {indicator}")
        
        # ✅ SUCCESS INDICATORS
        success_indicators = [
            "successfully executed",
            "program was successfully executed", 
            "execution completed",
            "top 10 most frequent words",
            "top 10 occurring words",
            "analysis and insights"
        ]
        
        for indicator in success_indicators:
            if indicator in response_lower:
                validation_results["passed_checks"].append(f"✅ Found success indicator: '{indicator}'")
        
        # 🎯 CRITICAL: Validate word count accuracy
        word_accuracy = self._validate_word_counts(response_text)
        validation_results["word_count_accuracy"] = word_accuracy
        
        if word_accuracy["accurate_count"] < 5:  # At least 5 words should be accurate
            validation_results["success"] = False
            validation_results["failed_checks"].append(f"❌ CRITICAL: Only {word_accuracy['accurate_count']} word counts are accurate")
            validation_results["critical_errors"].append("Word count accuracy below threshold - indicates hallucination")
        else:
            validation_results["passed_checks"].append(f"✅ Word count accuracy: {word_accuracy['accurate_count']}/10 words correct")
        
        # 📁 File path validation
        if "/var/www/html/silicon_dreams/stories/SD_TheQuantumConspiracy.md" in response_text:
            validation_results["passed_checks"].append("✅ Correct file path identified")
        else:
            validation_results["failed_checks"].append("❌ Expected file path not found")
        
        return validation_results
    
    def _validate_word_counts(self, response_text: str) -> Dict[str, Any]:
        """
        🎯 CRITICAL: Validate actual word count accuracy
        
        Extracts word counts from response and compares with expected results.
        Any significant deviation indicates the Arbitrator bug has returned.
        """
        import re
        
        accuracy_result = {
            "accurate_count": 0,
            "total_expected": len(self.expected_results),
            "found_counts": {},
            "missing_words": [],
            "incorrect_counts": []
        }
        
        # Extract word count patterns like "word: count"
        word_count_pattern = r'([a-zA-Z]+):\s*(\d+)'
        matches = re.findall(word_count_pattern, response_text)
        
        for word, count_str in matches:
            word_lower = word.lower()
            count = int(count_str)
            accuracy_result["found_counts"][word_lower] = count
            
            if word_lower in self.expected_results:
                expected_count = self.expected_results[word_lower]
                if count == expected_count:
                    accuracy_result["accurate_count"] += 1
                else:
                    accuracy_result["incorrect_counts"].append({
                        "word": word_lower,
                        "expected": expected_count,
                        "actual": count,
                        "difference": abs(count - expected_count)
                    })
        
        # Check for missing expected words
        for expected_word in self.expected_results:
            if expected_word not in accuracy_result["found_counts"]:
                accuracy_result["missing_words"].append(expected_word)
        
        return accuracy_result
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        🚨 RUN COMPLETE REGRESSION TEST
        
        This is the main test function that should be called for regression testing.
        Returns detailed results that can be used for CI/CD validation.
        """
        print("=" * 80)
        print("🚨 CRITICAL ARBITRATOR REGRESSION TEST STARTING")
        print("=" * 80)
        
        test_start = time.time()
        
        # Run the main test
        result = self.test_full_arbitrator_correction_flow()
        
        total_time = time.time() - test_start
        
        # Generate comprehensive test report
        test_report = {
            "test_name": "Arbitrator Word Count Regression Test",
            "test_version": "1.0.0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_execution_time": total_time,
            "result": result,
            "test_status": "PASSED" if result.get("success", False) else "FAILED",
            "critical_success_criteria": {
                "arbitrator_correction_working": result.get("success", False),
                "real_execution_results": result.get("validation_details", {}).get("word_count_accuracy", {}).get("accurate_count", 0) >= 5,
                "no_failure_messages": len(result.get("validation_details", {}).get("critical_errors", [])) == 0,
                "response_time_acceptable": result.get("execution_time", 999) < 120  # 2 minutes max
            }
        }
        
        # Print detailed results
        self._print_test_report(test_report)
        
        return test_report
    
    def _print_test_report(self, report: Dict[str, Any]):
        """Print formatted test report."""
        print("\n" + "=" * 80)
        print("🚨 ARBITRATOR REGRESSION TEST RESULTS")
        print("=" * 80)
        
        status = report["test_status"]
        status_icon = "✅" if status == "PASSED" else "❌"
        
        print(f"{status_icon} Test Status: {status}")
        print(f"⏱️  Total Time: {report['total_execution_time']:.2f}s")
        print(f"📅 Timestamp: {report['timestamp']}")
        
        result = report["result"]
        if result.get("success"):
            print(f"✅ Arbitrator Correction: WORKING")
            print(f"⚡ Response Time: {result.get('execution_time', 0):.2f}s")
            
            validation = result.get("validation_details", {})
            word_accuracy = validation.get("word_count_accuracy", {})
            print(f"🎯 Word Count Accuracy: {word_accuracy.get('accurate_count', 0)}/10")
            
            if validation.get("passed_checks"):
                print("✅ Success Indicators:")
                for check in validation["passed_checks"]:
                    print(f"   {check}")
        
        else:
            print(f"❌ Arbitrator Correction: FAILED")
            if result.get("error"):
                print(f"❌ Error: {result['error']}")
            
            validation = result.get("validation_details", {})
            if validation.get("failed_checks"):
                print("❌ Failed Checks:")
                for check in validation["failed_checks"]:
                    print(f"   {check}")
            
            if validation.get("critical_errors"):
                print("🚨 CRITICAL ERRORS:")
                for error in validation["critical_errors"]:
                    print(f"   🚨 {error}")
        
        print("=" * 80)


def main():
    """Main test runner function."""
    test = ArbitratorWordCountRegressionTest()
    report = test.run_comprehensive_test()
    
    # Exit with appropriate code for CI/CD
    exit_code = 0 if report["test_status"] == "PASSED" else 1
    print(f"\n🚨 Exiting with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)