#!/usr/bin/env python3
"""
Example Usage of Multi-Step Automation
======================================

Simple examples demonstrating how to use the multi-step automation system.
"""

import asyncio
import json
from multi_step_automation import MultiStepAutomation

async def example_ai_research():
    """Example: AI Research Analysis"""
    print("🔬 AI Research Analysis Example")
    print("-" * 40)

    # Initialize automation
    automation = MultiStepAutomation(
        server_url="http://localhost:5000",
        endpoint="/llama3_1b/stream",
        max_iterations=6,
        iteration_delay=2.0
    )

    # Create and load research configuration
    config = automation.create_example_configuration("research_analysis")

    # Save config for reference
    with open("ai_research_config.json", "w") as f:
        json.dump(config, f, indent=2)

    automation.load_configuration("ai_research_config.json")

    # Set research topic
    variables = {
        "topic": "large language models and their impact on software development"
    }

    print(f"📚 Research Topic: {variables['topic']}")
    print(f"🎯 Goal: Comprehensive research analysis with future insights")

    # Run automation
    results = await automation.run_automation(variables)

    # Display results
    print(f"\n✅ Completed in {results['total_iterations']} iterations")
    print(f"🎯 Goal Achieved: {results['goal_achieved']}")
    print(f"📊 Final Score: {results['final_score']:.2f}")

    # Save results
    automation.save_results(results, "ai_research_results.json")

    return results

async def example_problem_solving():
    """Example: Problem Solving"""
    print("\n🛠️ Problem Solving Example")
    print("-" * 40)

    automation = MultiStepAutomation(max_iterations=5, iteration_delay=1.5)

    # Create problem-solving configuration
    config = automation.create_example_configuration("problem_solving")

    with open("problem_solving_config.json", "w") as f:
        json.dump(config, f, indent=2)

    automation.load_configuration("problem_solving_config.json")

    # Define problem
    variables = {
        "problem_description": "Improve the user onboarding experience for a mobile app with low retention rates"
    }

    print(f"🔧 Problem: {variables['problem_description']}")
    print(f"🎯 Goal: Solution with implementation plan")

    # Run automation
    results = await automation.run_automation(variables)

    print(f"\n✅ Completed in {results['total_iterations']} iterations")
    print(f"🎯 Goal Achieved: {results['goal_achieved']}")
    print(f"📊 Final Score: {results['final_score']:.2f}")

    automation.save_results(results, "problem_solving_results.json")

    return results

async def example_creative_writing():
    """Example: Creative Writing"""
    print("\n✍️ Creative Writing Example")
    print("-" * 40)

    automation = MultiStepAutomation(max_iterations=8, iteration_delay=2.0)

    # Create creative writing configuration
    config = automation.create_example_configuration("creative_writing")

    with open("creative_writing_config.json", "w") as f:
        json.dump(config, f, indent=2)

    automation.load_configuration("creative_writing_config.json")

    # Set story parameters
    variables = {
        "genre": "cyberpunk thriller",
        "theme": "AI consciousness awakening in a corporate surveillance state"
    }

    print(f"📖 Genre: {variables['genre']}")
    print(f"🎭 Theme: {variables['theme']}")
    print(f"🎯 Goal: Complete story with characters and scenes")

    # Run automation
    results = await automation.run_automation(variables)

    print(f"\n✅ Completed in {results['total_iterations']} iterations")
    print(f"🎯 Goal Achieved: {results['goal_achieved']}")
    print(f"📊 Final Score: {results['final_score']:.2f}")

    automation.save_results(results, "creative_writing_results.json")

    return results

async def main():
    """Run all examples"""
    print("🚀 MULTI-STEP AUTOMATION EXAMPLES")
    print("=" * 50)

    examples = [
        ("AI Research", example_ai_research),
        ("Problem Solving", example_problem_solving),
        ("Creative Writing", example_creative_writing)
    ]

    results = {}

    for name, example_func in examples:
        try:
            print(f"\n▶️ Running {name} Example...")
            results[name] = await example_func()
        except Exception as e:
            print(f"❌ {name} Example failed: {e}")
            results[name] = {"error": str(e)}

    # Summary
    print(f"\n🏁 EXAMPLES SUMMARY")
    print("=" * 50)

    for name, result in results.items():
        if "error" in result:
            print(f"❌ {name}: Failed - {result['error']}")
        else:
            status = "✅ SUCCESS" if result.get('goal_achieved') else "⚠️ PARTIAL"
            score = result.get('final_score', 0)
            iterations = result.get('total_iterations', 0)
            print(f"{status} {name}: Score {score:.2f} ({iterations} iterations)")

if __name__ == "__main__":
    asyncio.run(main())