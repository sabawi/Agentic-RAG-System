#!/usr/bin/env python3
"""
Quick Test Script for Multi-Step Automation
===========================================

A simple script to test the multi-step automation system with different scenarios.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the current directory to the path to import our automation module
sys.path.append(str(Path(__file__).parent))

from multi_step_automation import MultiStepAutomation

async def test_simple_goal():
    """Test a simple goal achievement scenario"""
    print("🧪 Testing Simple Goal Achievement")
    print("=" * 50)

    # Create a simple configuration
    simple_config = {
        "description": "Simple Math Problem Solving",
        "max_iterations": 5,
        "iteration_delay": 1.0,
        "prompts": [
            {
                "id": "problem_setup",
                "template": "Solve this math problem step by step: {problem}. Show your work clearly.",
                "variables": ["problem"],
                "priority": 10,
                "context_weight": 0.2,
                "expected_response_type": "solution"
            },
            {
                "id": "verification",
                "template": "Verify the solution to: {problem}. Check the calculations and confirm the answer is correct.",
                "variables": ["problem"],
                "priority": 8,
                "context_weight": 1.0,
                "expected_response_type": "verification"
            },
            {
                "id": "explanation",
                "template": "Explain the solution method for: {problem}. Describe the mathematical concepts used.",
                "variables": ["problem"],
                "priority": 6,
                "context_weight": 1.0,
                "expected_response_type": "explanation"
            }
        ],
        "goal_criteria": [
            {
                "id": "solution_provided",
                "description": "A numerical solution is provided",
                "check_type": "pattern",
                "check_value": r"\b\d+(?:\.\d+)?\b",
                "weight": 2.0,
                "required": True
            },
            {
                "id": "explanation_given",
                "description": "Solution process is explained",
                "check_type": "keyword",
                "check_value": ["step", "calculate", "solution", "answer", "method"],
                "weight": 1.0,
                "required": True
            }
        ],
        "initial_goal_progress": {
            "solution_attempts": 0,
            "verification_completed": False
        }
    }

    # Save configuration
    config_file = "test_simple_config.json"
    with open(config_file, 'w') as f:
        json.dump(simple_config, f, indent=2)

    # Initialize automation
    automation = MultiStepAutomation(max_iterations=5, iteration_delay=1.0)
    automation.load_configuration(config_file)

    # Run test
    variables = {"problem": "What is the area of a circle with radius 5 meters?"}

    print(f"🎯 Goal: Solve math problem with verification")
    print(f"📝 Problem: {variables['problem']}")

    results = await automation.run_automation(variables)

    # Display results
    print(f"\n📊 RESULTS:")
    print(f"✅ Goal Achieved: {results['goal_achieved']}")
    print(f"📈 Final Score: {results['final_score']:.2f}")
    print(f"🔄 Iterations: {results['total_iterations']}")
    print(f"⏱️ Time: {results['execution_time']:.1f}s")

    # Save detailed results
    results_file = f"test_results_simple_{results['session_id'][:8]}.json"
    automation.save_results(results, results_file)

    # Cleanup
    os.remove(config_file)

    return results

async def test_research_scenario():
    """Test research analysis scenario"""
    print("\n🔬 Testing Research Analysis Scenario")
    print("=" * 50)

    # Initialize automation with research configuration
    automation = MultiStepAutomation(max_iterations=6, iteration_delay=2.0)
    automation.load_configuration("example_research_config.json")

    # Run research automation
    variables = {"topic": "quantum computing applications in cryptography"}

    print(f"🎯 Goal: Comprehensive research analysis")
    print(f"📚 Topic: {variables['topic']}")

    results = await automation.run_automation(variables)

    # Display results
    print(f"\n📊 RESULTS:")
    print(f"✅ Goal Achieved: {results['goal_achieved']}")
    print(f"📈 Final Score: {results['final_score']:.2f}")
    print(f"🔄 Iterations: {results['total_iterations']}")
    print(f"⏱️ Time: {results['execution_time']:.1f}s")

    # Show criteria breakdown
    if results['iterations']:
        last_iteration = results['iterations'][-1]
        criteria_results = last_iteration['goal_status']['criteria_results']
        print(f"\n📋 Criteria Results:")
        for criterion_id, result in criteria_results.items():
            status = "✅" if result['passed'] else "❌"
            print(f"  {status} {criterion_id}: {result['details']}")

    # Save results
    results_file = f"test_results_research_{results['session_id'][:8]}.json"
    automation.save_results(results, results_file)

    return results

async def test_custom_scenario():
    """Test custom problem-solving scenario"""
    print("\n🛠️ Testing Custom Problem-Solving Scenario")
    print("=" * 50)

    # Create custom configuration
    automation = MultiStepAutomation(max_iterations=4, iteration_delay=1.5)
    config = automation.create_example_configuration("problem_solving")

    # Save and load configuration
    config_file = "test_custom_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    automation.load_configuration(config_file)

    # Run automation
    variables = {
        "problem_description": "How to reduce energy consumption in a data center while maintaining performance"
    }

    print(f"🎯 Goal: Problem-solving with implementation plan")
    print(f"🔧 Problem: {variables['problem_description']}")

    results = await automation.run_automation(variables)

    # Display results
    print(f"\n📊 RESULTS:")
    print(f"✅ Goal Achieved: {results['goal_achieved']}")
    print(f"📈 Final Score: {results['final_score']:.2f}")
    print(f"🔄 Iterations: {results['total_iterations']}")
    print(f"⏱️ Time: {results['execution_time']:.1f}s")

    # Save results
    results_file = f"test_results_custom_{results['session_id'][:8]}.json"
    automation.save_results(results, results_file)

    # Cleanup
    os.remove(config_file)

    return results

async def run_all_tests():
    """Run all test scenarios"""
    print("🚀 MULTI-STEP AUTOMATION TEST SUITE")
    print("=" * 60)

    # Check if server is running
    import requests
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
        else:
            print("⚠️ Server responded but may have issues")
    except:
        print("❌ Server not accessible - tests may fail")
        print("💡 Make sure the FastAPI server is running on localhost:5000")
        return

    test_results = {}

    try:
        # Test 1: Simple goal
        test_results['simple'] = await test_simple_goal()

        # Test 2: Research scenario
        test_results['research'] = await test_research_scenario()

        # Test 3: Custom scenario
        test_results['custom'] = await test_custom_scenario()

    except Exception as e:
        print(f"❌ Test execution error: {e}")
        return

    # Summary
    print(f"\n🏁 TEST SUITE SUMMARY")
    print("=" * 60)

    total_tests = len(test_results)
    successful_goals = sum(1 for result in test_results.values() if result['goal_achieved'])

    print(f"📊 Tests Run: {total_tests}")
    print(f"✅ Goals Achieved: {successful_goals}/{total_tests}")
    print(f"📈 Success Rate: {(successful_goals/total_tests)*100:.1f}%")

    print(f"\n📋 Individual Results:")
    for test_name, result in test_results.items():
        status = "✅" if result['goal_achieved'] else "❌"
        print(f"  {status} {test_name.title()}: Score {result['final_score']:.2f} ({result['total_iterations']} iterations)")

if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())