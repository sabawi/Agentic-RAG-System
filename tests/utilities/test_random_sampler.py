#!/usr/bin/env python3
"""
Random Test Sampler - 15% Sanity Check
======================================

Randomly samples 15% of all test files and runs them to ensure
they pass 100% of the time. This provides a quick sanity check
that core functionality is working.

Features:
- Random sampling (15% of total tests)
- Reproducible with --seed option
- Detailed success/failure reporting
- Timeout handling for hung tests
- Parallel execution option

Usage:
    python test_random_sampler.py                    # Run 15% random sample
    python test_random_sampler.py --percent 25       # Run 25% random sample
    python test_random_sampler.py --seed 42          # Reproducible sampling
    python test_random_sampler.py --list             # List what would be sampled
"""

import os
import sys
import random
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import time
import json

class RandomTestSampler:
    """Randomly sample and run tests."""

    def __init__(
        self,
        tests_dir: str = '/home/sabawi/Development/flaskserver/tests',
        sample_percent: float = 15.0,
        seed: int = None,
        timeout: int = 300
    ):
        self.tests_dir = Path(tests_dir)
        self.sample_percent = sample_percent
        self.seed = seed
        self.timeout = timeout

        if seed:
            random.seed(seed)

    def find_all_executable_tests(self) -> List[Path]:
        """Find all executable Python test files."""
        test_files = []

        # Find all Python files in tests directory
        for py_file in self.tests_dir.rglob("*.py"):
            # Skip __pycache__ and non-test files
            if '__pycache__' in str(py_file):
                continue

            # Skip utility files that aren't tests
            if py_file.name in ['test_model_replacer.py', 'test_random_sampler.py',
                                'check_imports.py', 'tool_example.py']:
                continue

            # Must start with 'test_' or contain test patterns
            if py_file.name.startswith('test_') or '_test.py' in py_file.name:
                # Check if it has a main or is executable
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        if 'if __name__' in content or 'def test_' in content:
                            test_files.append(py_file)
                except:
                    continue

        return sorted(test_files)

    def sample_tests(self, test_files: List[Path]) -> List[Path]:
        """Randomly sample tests based on percentage."""
        sample_size = max(1, int(len(test_files) * (self.sample_percent / 100.0)))
        return random.sample(test_files, sample_size)

    def run_single_test(self, test_file: Path) -> Dict:
        """Run a single test file and return results."""
        rel_path = test_file.relative_to(self.tests_dir)

        print(f"  🧪 Running: {rel_path}")
        start_time = time.time()

        try:
            # Run test with timeout
            result = subprocess.run(
                ['python3', str(test_file)],
                cwd=str(test_file.parent),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            duration = time.time() - start_time

            return {
                'file': str(rel_path),
                'success': result.returncode == 0,
                'duration': duration,
                'stdout': result.stdout[-1000:] if result.stdout else '',  # Last 1000 chars
                'stderr': result.stderr[-1000:] if result.stderr else '',
                'returncode': result.returncode
            }

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                'file': str(rel_path),
                'success': False,
                'duration': duration,
                'stdout': '',
                'stderr': f'Test timed out after {self.timeout}s',
                'returncode': -1
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                'file': str(rel_path),
                'success': False,
                'duration': duration,
                'stdout': '',
                'stderr': str(e),
                'returncode': -2
            }

    def run_sampled_tests(self, sampled_tests: List[Path]) -> Tuple[List[Dict], Dict]:
        """Run all sampled tests and return results."""
        print(f"\n🚀 Running {len(sampled_tests)} Randomly Sampled Tests")
        print("=" * 70)

        results = []
        passed = 0
        failed = 0
        total_duration = 0

        for i, test_file in enumerate(sampled_tests, 1):
            print(f"\n[{i}/{len(sampled_tests)}]", end=" ")

            result = self.run_single_test(test_file)
            results.append(result)
            total_duration += result['duration']

            if result['success']:
                passed += 1
                print(f"    ✅ PASS ({result['duration']:.1f}s)")
            else:
                failed += 1
                print(f"    ❌ FAIL ({result['duration']:.1f}s)")
                if result['stderr']:
                    print(f"       Error: {result['stderr'][:100]}")

        summary = {
            'total': len(sampled_tests),
            'passed': passed,
            'failed': failed,
            'success_rate': (passed / len(sampled_tests) * 100) if sampled_tests else 0,
            'total_duration': total_duration,
            'avg_duration': total_duration / len(sampled_tests) if sampled_tests else 0
        }

        return results, summary

    def print_summary(self, results: List[Dict], summary: Dict):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("📊 RANDOM SAMPLING TEST RESULTS")
        print("=" * 70)
        print(f"Total Tests Run:    {summary['total']}")
        print(f"Passed:             {summary['passed']} ✅")
        print(f"Failed:             {summary['failed']} ❌")
        print(f"Success Rate:       {summary['success_rate']:.1f}%")
        print(f"Total Duration:     {summary['total_duration']:.1f}s")
        print(f"Average Duration:   {summary['avg_duration']:.1f}s")
        print()

        if summary['failed'] > 0:
            print("❌ Failed Tests:")
            for result in results:
                if not result['success']:
                    print(f"   - {result['file']}")
                    if result['stderr']:
                        print(f"     Error: {result['stderr'][:100]}")
            print()

        # Sanity check goal: 100% pass rate
        if summary['success_rate'] == 100:
            print("🎉 SUCCESS: 100% pass rate achieved!")
            print("✅ Sanity check: All sampled tests passed!")
        else:
            print(f"⚠️  WARNING: {summary['failed']} test(s) failed")
            print("❌ Sanity check: Not all tests passed")

        print("=" * 70)

    def save_results(self, results: List[Dict], summary: Dict, output_file: str):
        """Save results to JSON file."""
        data = {
            'summary': summary,
            'results': results,
            'seed': self.seed,
            'sample_percent': self.sample_percent
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"💾 Results saved to: {output_file}")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Randomly sample and run tests for sanity checking'
    )
    parser.add_argument(
        '--percent',
        type=float,
        default=15.0,
        help='Percentage of tests to sample (default: 15%%)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducible sampling'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Timeout per test in seconds (default: 300)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List sampled tests without running them'
    )
    parser.add_argument(
        '--output',
        default='test_sample_results.json',
        help='Output file for results (default: test_sample_results.json)'
    )

    args = parser.parse_args()

    sampler = RandomTestSampler(
        sample_percent=args.percent,
        seed=args.seed,
        timeout=args.timeout
    )

    # Find all tests
    print("🔍 Finding all executable tests...")
    all_tests = sampler.find_all_executable_tests()
    print(f"📁 Found {len(all_tests)} total test files")

    # Sample tests
    sampled_tests = sampler.sample_tests(all_tests)
    print(f"🎲 Sampled {len(sampled_tests)} tests ({args.percent}%)")

    if args.seed:
        print(f"🌱 Using seed: {args.seed} (reproducible)")

    if args.list:
        print("\nSampled Tests:")
        for test in sampled_tests:
            print(f"  - {test.relative_to(sampler.tests_dir)}")
        return

    # Run tests
    results, summary = sampler.run_sampled_tests(sampled_tests)

    # Print summary
    sampler.print_summary(results, summary)

    # Save results
    sampler.save_results(results, summary, args.output)

    # Exit with appropriate code
    sys.exit(0 if summary['success_rate'] == 100 else 1)

if __name__ == '__main__':
    main()
