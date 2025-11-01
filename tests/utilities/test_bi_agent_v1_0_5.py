#!/usr/bin/env python3
"""
Test Script for Business Intelligence Agent v1.0.5 Improvements

Tests the following enhancements:
1. Context detection (public company, private company, sector analysis)
2. Citation formatting in all sections
3. Peer comparison table (for public companies with competitors)
4. Investment recommendation (for public companies)
5. Data sources section (always included)

Author: Agentic-RAG Development Team
Date: 2025-11-01
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class BIAgentTester:
    """Test runner for Business Intelligence Agent v1.0.5 improvements."""

    def __init__(self):
        self.agent_path = project_root / "agents" / "business_intelligence" / "business_intelligence.py"
        self.test_output_dir = project_root / "tests" / "output" / "bi_agent_v1_0_5"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    def run_command(self, command: list, test_name: str) -> dict:
        """
        Run a command and capture output.

        Args:
            command: Command to execute as list
            test_name: Name of the test

        Returns:
            Dictionary with test results
        """
        print(f"\n{'=' * 80}")
        print(f"TEST: {test_name}")
        print(f"{'=' * 80}")
        print(f"Command: {' '.join(command)}")
        print()

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            success = result.returncode == 0

            test_result = {
                'test_name': test_name,
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            if success:
                print(f"✅ TEST PASSED: {test_name}")
            else:
                print(f"❌ TEST FAILED: {test_name}")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"Error output:\n{result.stderr}")

            return test_result

        except subprocess.TimeoutExpired:
            print(f"⏱️  TEST TIMEOUT: {test_name} exceeded 10 minutes")
            return {
                'test_name': test_name,
                'success': False,
                'returncode': -1,
                'error': 'Timeout after 10 minutes',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"❌ TEST ERROR: {test_name} - {str(e)}")
            return {
                'test_name': test_name,
                'success': False,
                'returncode': -1,
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def test_public_company_full_features(self):
        """
        Test 1: Public Company with Competitors (Full Features)

        Expected:
        - ✅ All existing sections (market research, financial analysis, competitor analysis, dashboard)
        - ✅ NEW: Peer comparison table (AAPL vs MSFT vs GOOGL)
        - ✅ NEW: Investment recommendation (Buy/Hold/Sell with scoring)
        - ✅ NEW: Data sources section
        - ✅ Citations throughout financial data
        """
        command = [
            str(self.agent_path),
            "--strategic",
            "--company", "AAPL",
            "--competitors", "MSFT", "GOOGL",
            "--output-dir", str(self.test_output_dir / "test1_public_company")
        ]

        result = self.run_command(command, "Test 1: Public Company (AAPL) - Full Features")
        self.results.append(result)

        # Verify expected sections in output
        if result['success']:
            stdout = result['stdout']
            expected_indicators = [
                "Step 6.5: Creating peer comparison table",
                "Step 6.75: Generating investment recommendation",
                "Step 7: Collecting data sources",
                "Peer comparison table created",
                "Investment recommendation generated",
                "Data sources section created"
            ]

            for indicator in expected_indicators:
                if indicator in stdout:
                    print(f"  ✅ Found: {indicator}")
                else:
                    print(f"  ⚠️  Missing: {indicator}")

        return result

    def test_private_company_no_financial_features(self):
        """
        Test 2: Private Company (No Financial Features)

        Expected:
        - ✅ Market research, competitor analysis (no financial tables)
        - ✅ NO peer comparison table (not public)
        - ✅ NO investment recommendation (not tradeable)
        - ✅ NEW: Data sources section (news, web sources)
        """
        command = [
            str(self.agent_path),
            "--strategic",
            "--company", "SpaceX",
            "--competitors", "Blue Origin",
            "--output-dir", str(self.test_output_dir / "test2_private_company")
        ]

        result = self.run_command(command, "Test 2: Private Company (SpaceX) - No Financial Features")
        self.results.append(result)

        # Verify context-aware behavior
        if result['success']:
            stdout = result['stdout']
            expected_skips = [
                "Peer comparison not applicable",
                "Investment recommendation not applicable"
            ]
            expected_includes = [
                "Step 7: Collecting data sources",
                "Data sources section created"
            ]

            for indicator in expected_skips:
                if indicator in stdout:
                    print(f"  ✅ Correctly skipped: {indicator}")
                else:
                    print(f"  ⚠️  Expected to skip: {indicator}")

            for indicator in expected_includes:
                if indicator in stdout:
                    print(f"  ✅ Found: {indicator}")
                else:
                    print(f"  ⚠️  Missing: {indicator}")

        return result

    def test_sector_analysis(self):
        """
        Test 3: Sector Analysis (No Company-Specific Features)

        Expected:
        - ✅ Sector overview, market trends, key players
        - ✅ NO peer comparison, NO investment rec
        - ✅ NEW: Data sources section
        """
        command = [
            str(self.agent_path),
            "--strategic",
            "--sectors", "Electric Vehicles", "Battery Technology",
            "--output-dir", str(self.test_output_dir / "test3_sector_analysis")
        ]

        result = self.run_command(command, "Test 3: Sector Analysis - Context-Aware")
        self.results.append(result)

        # Verify context-aware behavior
        if result['success']:
            stdout = result['stdout']
            expected_skips = [
                "Peer comparison not applicable",
                "Investment recommendation not applicable"
            ]
            expected_includes = [
                "Step 7: Collecting data sources",
                "Data sources section created"
            ]

            for indicator in expected_skips:
                if indicator in stdout:
                    print(f"  ✅ Correctly skipped: {indicator}")
                else:
                    print(f"  ⚠️  Expected to skip: {indicator}")

            for indicator in expected_includes:
                if indicator in stdout:
                    print(f"  ✅ Found: {indicator}")
                else:
                    print(f"  ⚠️  Missing: {indicator}")

        return result

    def generate_summary_report(self):
        """Generate summary report of all tests."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY REPORT")
        print("=" * 80)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests

        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        print("\nDetailed Results:")
        for i, result in enumerate(self.results, 1):
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{i}. [{status}] {result['test_name']}")
            if not result['success'] and 'error' in result:
                print(f"   Error: {result['error']}")

        print("\n" + "=" * 80)
        print(f"Test reports saved to: {self.test_output_dir}")
        print("=" * 80)

        # Save summary to file
        summary_file = self.test_output_dir / "TEST_SUMMARY.txt"
        with open(summary_file, 'w') as f:
            f.write("Business Intelligence Agent v1.0.5 - Test Summary\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")

            f.write("Detailed Results:\n")
            f.write("-" * 80 + "\n")
            for result in self.results:
                f.write(f"\nTest: {result['test_name']}\n")
                f.write(f"Status: {'PASS' if result['success'] else 'FAIL'}\n")
                f.write(f"Timestamp: {result['timestamp']}\n")
                if not result['success'] and 'error' in result:
                    f.write(f"Error: {result['error']}\n")

        print(f"\nSummary saved to: {summary_file}")

        return passed_tests == total_tests


def main():
    """Main entry point."""
    print("=" * 80)
    print("Business Intelligence Agent v1.0.5 - Test Suite")
    print("=" * 80)
    print(f"Testing enhancements:")
    print("  1. Context detection (public/private company, sector analysis)")
    print("  2. Citation formatting in all sections")
    print("  3. Peer comparison table (context-aware)")
    print("  4. Investment recommendation (context-aware)")
    print("  5. Data sources section (always included)")
    print()

    tester = BIAgentTester()

    # Run all tests
    tester.test_public_company_full_features()
    print("\n⏳ Waiting 5 seconds before next test...\n")
    import time
    time.sleep(5)

    tester.test_private_company_no_financial_features()
    print("\n⏳ Waiting 5 seconds before next test...\n")
    time.sleep(5)

    tester.test_sector_analysis()

    # Generate summary
    all_passed = tester.generate_summary_report()

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
