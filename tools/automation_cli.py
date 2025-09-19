#!/usr/bin/env python3
"""
Interactive CLI for Multi-Step Automation Framework
Provides user-friendly interface for experimenting with automation workflows
"""

import asyncio
import json
import sys
import os
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tools.multi_step_automation import (
        MultiStepAutomation,
        PromptTemplate,
        GoalAchievementDetector,
        ContextBuffer
    )
except ImportError:
    print("❌ Error: Could not import multi_step_automation module")
    print("   Make sure you're running from the correct directory")
    sys.exit(1)

class AutomationCLI:
    def __init__(self):
        self.automation = None
        self.running = False
        self.paused = False
        self.stop_requested = False
        self.current_iteration = 0
        self.session_id = None

    def display_banner(self):
        """Display welcome banner"""
        print("\n" + "="*60)
        print("🚀 MULTI-STEP AUTOMATION CLI")
        print("="*60)
        print("Interactive framework for automated prompt workflows")
        print("Version: 1.0.0")
        print("="*60 + "\n")

    def display_menu(self):
        """Display main menu options"""
        print("\n📋 MAIN MENU:")
        print("1. 🧪 Quick Test (Simple Math Problem)")
        print("2. 🔬 Research Analysis (Complex Topic Research)")
        print("3. 💡 Creative Writing (Story Generation)")
        print("4. 📁 Load Custom Configuration")
        print("5. ⚙️  Create New Configuration")
        print("6. 📊 View Previous Results")
        print("7. ❓ Help & Documentation")
        print("8. 🚪 Exit")
        print("\n" + "-"*40)

    def get_user_choice(self, prompt: str, valid_choices: list) -> str:
        """Get validated user input"""
        while True:
            try:
                choice = input(f"{prompt} ").strip()
                if choice in valid_choices:
                    return choice
                print(f"❌ Invalid choice. Please select from: {', '.join(valid_choices)}")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)

    def load_preset_config(self, preset_type: str) -> Dict[str, Any]:
        """Load predefined configurations"""
        configs = {
            "simple": {
                "goal_type": "problem_solving",
                "target_goal": {
                    "criteria": {
                        "solution_provided": {
                            "keywords": ["answer", "solution", "result", "equals", "="],
                            "min_matches": 2,
                            "weight": 0.6
                        },
                        "explanation_given": {
                            "keywords": ["because", "since", "therefore", "explanation", "reason"],
                            "min_matches": 1,
                            "weight": 0.4
                        }
                    },
                    "min_score": 0.8
                },
                "prompt_templates": [
                    {
                        "name": "problem_setup",
                        "template": "Solve this math problem step by step: {query}. Show your work clearly.",
                        "weight": 1.0
                    },
                    {
                        "name": "verification",
                        "template": "Verify the solution to: {query}. Check the calculations and confirm the answer is correct.",
                        "weight": 1.0
                    },
                    {
                        "name": "explanation",
                        "template": "Explain the solution method for: {query}. Describe the mathematical concepts used.",
                        "weight": 1.0
                    }
                ],
                "max_iterations": 5,
                "server_url": "http://localhost:5000",
                "endpoint": "/v1/chat/completions"
            },
            "research": {
                "goal_type": "research_analysis",
                "target_goal": {
                    "criteria": {
                        "comprehensive_length": {
                            "min_length": 1000,
                            "weight": 0.2
                        },
                        "technical_depth": {
                            "keywords": ["analysis", "methodology", "framework", "implementation", "technical", "approach"],
                            "min_matches": 3,
                            "weight": 0.3
                        },
                        "future_insights": {
                            "keywords": ["future", "potential", "implications", "trends", "prediction", "forecast"],
                            "min_matches": 2,
                            "weight": 0.3
                        },
                        "structured_report": {
                            "patterns": ["##", "###", "1.", "2.", "3."],
                            "min_matches": 3,
                            "weight": 0.2
                        }
                    },
                    "min_score": 0.7
                },
                "prompt_templates": [
                    {
                        "name": "initial_research",
                        "template": "Conduct comprehensive research on: {query}. Provide detailed analysis with current information and data.",
                        "weight": 1.0
                    },
                    {
                        "name": "technical_deep_dive",
                        "template": "Dive deeper into the technical aspects of {query}. Analyze methodologies, frameworks, and implementation approaches.",
                        "weight": 1.0
                    },
                    {
                        "name": "future_implications",
                        "template": "Analyze the future implications and potential of {query}. Consider trends, predictions, and emerging developments.",
                        "weight": 1.0
                    },
                    {
                        "name": "synthesis_report",
                        "template": "Create a comprehensive synthesis report on {query} that includes executive summary, current state, and future outlook.",
                        "weight": 1.0
                    }
                ],
                "max_iterations": 8,
                "server_url": "http://localhost:5000",
                "endpoint": "/v1/chat/completions"
            },
            "creative": {
                "goal_type": "creative_writing",
                "target_goal": {
                    "criteria": {
                        "story_elements": {
                            "keywords": ["character", "plot", "setting", "conflict", "resolution", "dialogue"],
                            "min_matches": 4,
                            "weight": 0.4
                        },
                        "creative_length": {
                            "min_length": 800,
                            "weight": 0.3
                        },
                        "narrative_structure": {
                            "patterns": ["Chapter", "Scene", "\"", "said", "thought"],
                            "min_matches": 3,
                            "weight": 0.3
                        }
                    },
                    "min_score": 0.75
                },
                "prompt_templates": [
                    {
                        "name": "story_outline",
                        "template": "Create a detailed story outline for: {query}. Include main characters, plot structure, and key scenes.",
                        "weight": 1.0
                    },
                    {
                        "name": "character_development",
                        "template": "Develop rich characters for the story: {query}. Create detailed character profiles with motivations and backgrounds.",
                        "weight": 1.0
                    },
                    {
                        "name": "scene_writing",
                        "template": "Write engaging scenes for: {query}. Focus on dialogue, action, and character development.",
                        "weight": 1.0
                    },
                    {
                        "name": "story_completion",
                        "template": "Complete the story: {query}. Ensure proper narrative flow, character arcs, and satisfying resolution.",
                        "weight": 1.0
                    }
                ],
                "max_iterations": 6,
                "server_url": "http://localhost:5000",
                "endpoint": "/v1/chat/completions"
            }
        }
        return configs.get(preset_type, {})

    def display_progress(self, iteration: int, max_iterations: int, current_template: str, status: str):
        """Display real-time progress updates"""
        progress_bar = "█" * (iteration * 20 // max_iterations) + "░" * (20 - (iteration * 20 // max_iterations))
        percentage = (iteration / max_iterations) * 100

        print(f"\r🔄 Progress: [{progress_bar}] {percentage:5.1f}% | Iteration {iteration}/{max_iterations} | {current_template} | {status}", end="", flush=True)

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful interruption"""
        def signal_handler(signum, frame):
            print(f"\n\n⏸️  Received interrupt signal. Current options:")
            print("1. ⏸️  Pause (resume later)")
            print("2. 🛑 Stop automation")
            print("3. ↩️  Continue")

            choice = self.get_user_choice("Choose action (1/2/3):", ["1", "2", "3"])

            if choice == "1":
                self.paused = True
                print("⏸️  Automation paused. Press ENTER to resume or CTRL+C to stop.")
                input()
                self.paused = False
                print("▶️  Resuming automation...")
            elif choice == "2":
                self.stop_requested = True
                print("🛑 Stop requested. Finishing current iteration...")
            else:
                print("▶️  Continuing automation...")

        signal.signal(signal.SIGINT, signal_handler)

    def display_iteration_details(self, iteration_data: Dict[str, Any]):
        """Display detailed information about completed iteration"""
        iteration_num = iteration_data.get('iteration_number', 'N/A')
        print(f"\n📊 ITERATION {iteration_num} COMPLETE:")

        # Try to get template info from metadata
        metadata = iteration_data.get('metadata', {})
        template_name = metadata.get('template_name', metadata.get('prompt_template', 'Unknown'))
        print(f"   Template: {template_name}")

        # Calculate response length
        response = iteration_data.get('response', '')
        response_length = len(response) if response else 0
        print(f"   Response Length: {response_length} chars")

        # Goal status from metadata
        goal_status = metadata.get('goal_status', {})
        progress_score = goal_status.get('progress_score', 0)
        print(f"   Goal Score: {progress_score:.3f}")

        if goal_status.get('achieved', False):
            print("   ✅ Goal ACHIEVED!")
        else:
            missing = goal_status.get('missing_requirements', [])
            if missing:
                print(f"   ❌ Missing: {', '.join(missing[:2])}{'...' if len(missing) > 2 else ''}")
            else:
                print(f"   ⚠️ Goal progress: {progress_score:.3f}")

    async def run_automation_with_monitoring(self, query: str, config: Dict[str, Any]):
        """Run automation with real-time monitoring and user interaction"""
        self.setup_signal_handlers()

        print(f"\n🚀 Starting automation for: '{query}'")
        print(f"📊 Goal Type: {config['goal_type']}")
        print(f"🎯 Max Iterations: {config['max_iterations']}")
        print(f"⚡ Server: {config['server_url']}")
        print("\n" + "="*60)
        print("💡 Use CTRL+C anytime to pause, stop, or continue")
        print("="*60 + "\n")

        # Initialize automation
        try:
            self.automation = MultiStepAutomation.from_config(config)
            self.running = True
            self.stop_requested = False
            self.session_id = self.automation.session_id

            print(f"🔗 Session ID: {self.session_id}")
            print("⏳ Starting automation process...\n")

            # Start automation in background
            automation_task = asyncio.create_task(
                self.automation.run_automation({"query": query})
            )

            # Monitor progress
            while not automation_task.done() and not self.stop_requested:
                if self.paused:
                    await asyncio.sleep(0.1)
                    continue

                # Check for new iteration data
                current_iter = len(self.automation.context_buffer.iterations)
                if current_iter > self.current_iteration:
                    latest_iteration = self.automation.context_buffer.iterations[-1]
                    self.display_iteration_details(latest_iteration)
                    self.current_iteration = current_iter

                # Update progress display
                max_iter = config.get('max_iterations', 10)
                current_template = 'Unknown'
                if hasattr(self.automation, 'prompt_templates') and self.automation.prompt_templates:
                    template_idx = getattr(self.automation, 'current_prompt_index', 0)
                    if 0 <= template_idx < len(self.automation.prompt_templates):
                        current_template = self.automation.prompt_templates[template_idx].id
                status = "Paused" if self.paused else "Running"

                self.display_progress(current_iter, max_iter, current_template, status)

                await asyncio.sleep(0.5)

            # Handle completion or interruption
            if self.stop_requested:
                automation_task.cancel()
                print(f"\n\n🛑 Automation stopped by user at iteration {self.current_iteration}")
                return None

            # Get final results
            result = await automation_task
            return result

        except Exception as e:
            print(f"\n❌ Error during automation: {str(e)}")
            return None
        finally:
            self.running = False

    def display_results(self, result: Optional[Dict[str, Any]]):
        """Display automation results"""
        if not result:
            print("\n❌ No results to display")
            return

        print("\n\n" + "="*60)
        print("📊 AUTOMATION RESULTS")
        print("="*60)

        print(f"🔗 Session ID: {result.get('session_id', 'Unknown')}")
        print(f"⏱️  Total Time: {result.get('execution_time', 0):.1f} seconds")
        print(f"🔄 Iterations: {result.get('total_iterations', 0)}")
        print(f"🎯 Goal Achieved: {'✅ YES' if result.get('goal_achieved', False) else '❌ NO'}")
        print(f"📊 Final Score: {result.get('final_score', 0):.3f}")

        if result.get('goal_achieved', False):
            print("\n🎉 SUCCESS! The automation achieved its goal.")
        else:
            print(f"\n⚠️  Goal not fully achieved. Best score: {result.get('final_score', 0):.3f}")

        # Save results
        self.save_results(result)

        print(f"\n💾 Results saved to: tools/results/results_{result.get('session_id', 'unknown')[:8]}.json")

    def save_results(self, result: Dict[str, Any]):
        """Save automation results to file"""
        try:
            # Ensure results directory exists
            os.makedirs("tools/results", exist_ok=True)

            session_id = result.get('session_id', 'unknown')[:8]
            filename = f"tools/results/results_{session_id}.json"

            with open(filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)

        except Exception as e:
            print(f"⚠️  Could not save results: {e}")

    def load_previous_results(self):
        """Load and display previous automation results"""
        results_dir = Path("tools/results")
        result_files = list(results_dir.glob("results_*.json")) if results_dir.exists() else []

        if not result_files:
            print("\n📭 No previous results found.")
            return

        print(f"\n📂 Found {len(result_files)} previous result files:")
        for i, file in enumerate(result_files, 1):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    goal_achieved = "✅" if data.get('goal_achieved', False) else "❌"
                    print(f"{i}. {file.name} - {goal_achieved} Score: {data.get('final_score', 0):.3f}")
            except:
                print(f"{i}. {file.name} - ❌ Error reading file")

        choice = input(f"\nEnter number to view details (1-{len(result_files)}) or press ENTER to return: ").strip()

        if choice and choice.isdigit() and 1 <= int(choice) <= len(result_files):
            file_to_show = result_files[int(choice) - 1]
            try:
                with open(file_to_show, 'r') as f:
                    data = json.load(f)
                    self.display_results(data)
            except Exception as e:
                print(f"❌ Error loading file: {e}")

    def create_custom_config(self) -> Dict[str, Any]:
        """Interactive configuration creator"""
        print("\n⚙️  CUSTOM CONFIGURATION CREATOR")
        print("="*40)

        config = {
            "server_url": "http://localhost:5000",
            "prompt_templates": [],
            "max_iterations": 10
        }

        # Goal type
        print("\n1. 🧮 problem_solving - Math, logic, specific questions")
        print("2. 🔬 research_analysis - Research, analysis, reports")
        print("3. 🎨 creative_writing - Stories, creative content")

        goal_choice = self.get_user_choice("Select goal type (1/2/3):", ["1", "2", "3"])
        goal_types = {"1": "problem_solving", "2": "research_analysis", "3": "creative_writing"}
        config["goal_type"] = goal_types[goal_choice]

        # Max iterations
        max_iter = input("Max iterations (default 10): ").strip()
        if max_iter.isdigit():
            config["max_iterations"] = int(max_iter)

        # Prompt templates
        print(f"\n📝 Add prompt templates (minimum 1):")
        template_count = 1

        while True:
            print(f"\nTemplate {template_count}:")
            name = input(f"  Name (e.g., 'analysis_{template_count}'): ").strip()
            if not name:
                name = f"template_{template_count}"

            template = input(f"  Template (use {{query}} for user input): ").strip()
            if not template:
                template = "Analyze the following: {query}"

            config["prompt_templates"].append({
                "name": name,
                "template": template,
                "weight": 1.0
            })

            template_count += 1

            if template_count > 1:
                add_more = input("Add another template? (y/n): ").strip().lower()
                if add_more != 'y':
                    break

        # Simple goal criteria
        config["target_goal"] = {
            "criteria": {
                "basic_completion": {
                    "keywords": ["analysis", "solution", "answer", "result", "conclusion"],
                    "min_matches": 2,
                    "weight": 1.0
                }
            },
            "min_score": 0.6
        }

        # Save option
        save_config = input("\n💾 Save this configuration? (y/n): ").strip().lower()
        if save_config == 'y':
            config_name = input("Configuration name: ").strip()
            if not config_name:
                config_name = f"custom_{int(time.time())}"

            filename = f"tools/config_{config_name}.json"
            try:
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                print(f"✅ Configuration saved to: {filename}")
            except Exception as e:
                print(f"⚠️  Could not save configuration: {e}")

        return config

    def load_config_file(self) -> Optional[Dict[str, Any]]:
        """Load configuration from file"""
        config_dir = Path("tools")
        config_files = list(config_dir.glob("*.json"))
        config_files = [f for f in config_files if f.name.startswith(('config_', 'example_', 'demo_'))]

        if not config_files:
            print("\n📭 No configuration files found.")
            return None

        print(f"\n📂 Available configuration files:")
        for i, file in enumerate(config_files, 1):
            print(f"{i}. {file.name}")

        choice = input(f"\nEnter number to load (1-{len(config_files)}) or press ENTER to cancel: ").strip()

        if choice and choice.isdigit() and 1 <= int(choice) <= len(config_files):
            file_to_load = config_files[int(choice) - 1]
            try:
                with open(file_to_load, 'r') as f:
                    config = json.load(f)
                    print(f"✅ Loaded configuration: {file_to_load.name}")
                    return config
            except Exception as e:
                print(f"❌ Error loading file: {e}")

        return None

    def display_help(self):
        """Display help and documentation"""
        help_text = """
📖 MULTI-STEP AUTOMATION HELP
================================

🎯 WHAT IS THIS?
This tool allows you to create automated workflows that repeatedly prompt an AI
system until a specific goal is achieved. Perfect for complex tasks that need
multiple iterations to complete properly.

🔧 HOW IT WORKS:
1. Define your goal (what you want to achieve)
2. Create prompt templates (different ways to approach the problem)
3. Set criteria for success (keywords, length, patterns)
4. Run automation - the system will iterate until goal is met

📋 PRESET CONFIGURATIONS:
• Simple Math: Quick test with basic problem solving
• Research Analysis: Deep research with comprehensive reporting
• Creative Writing: Story generation with narrative structure

⚙️ CUSTOM CONFIGURATIONS:
Create your own workflows by defining:
• Goal type and success criteria
• Multiple prompt templates
• Maximum iterations and scoring thresholds

🎮 CONTROLS DURING EXECUTION:
• CTRL+C: Pause, stop, or continue
• Real-time progress monitoring
• Iteration-by-iteration feedback
• Automatic result saving

📊 RESULTS:
All automation sessions are saved with detailed metrics:
• Goal achievement status
• Execution time and iterations
• Progressive scoring
• Complete conversation history

💡 TIPS:
• Start with preset configurations to understand the framework
• Use varied prompt templates for better results
• Set realistic goals and iteration limits
• Monitor progress and adjust as needed

For more details, check: tools/README_MULTI_STEP_AUTOMATION.md
"""
        print(help_text)

    async def main_loop(self):
        """Main application loop"""
        self.display_banner()

        while True:
            self.display_menu()
            choice = self.get_user_choice("Enter your choice (1-8):",
                                        ["1", "2", "3", "4", "5", "6", "7", "8"])

            if choice == "8":
                print("\n👋 Thank you for using Multi-Step Automation CLI!")
                break

            elif choice == "1":  # Quick Test
                query = input("\n🧮 Enter a math problem (e.g., 'What is 15 * 23?'): ").strip()
                if query:
                    config = self.load_preset_config("simple")
                    result = await self.run_automation_with_monitoring(query, config)
                    if result:
                        self.display_results(result)

            elif choice == "2":  # Research Analysis
                query = input("\n🔬 Enter research topic (e.g., 'artificial intelligence in healthcare'): ").strip()
                if query:
                    config = self.load_preset_config("research")
                    result = await self.run_automation_with_monitoring(query, config)
                    if result:
                        self.display_results(result)

            elif choice == "3":  # Creative Writing
                query = input("\n💡 Enter story prompt (e.g., 'a detective in a haunted library'): ").strip()
                if query:
                    config = self.load_preset_config("creative")
                    result = await self.run_automation_with_monitoring(query, config)
                    if result:
                        self.display_results(result)

            elif choice == "4":  # Load Custom Configuration
                config = self.load_config_file()
                if config:
                    query = input("\n📝 Enter your query/prompt: ").strip()
                    if query:
                        result = await self.run_automation_with_monitoring(query, config)
                        if result:
                            self.display_results(result)

            elif choice == "5":  # Create New Configuration
                config = self.create_custom_config()
                if config:
                    query = input("\n📝 Enter your query/prompt: ").strip()
                    if query:
                        result = await self.run_automation_with_monitoring(query, config)
                        if result:
                            self.display_results(result)

            elif choice == "6":  # View Previous Results
                self.load_previous_results()

            elif choice == "7":  # Help
                self.display_help()

            input("\nPress ENTER to continue...")

def main():
    """Entry point"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Multi-Step Automation CLI")
        print("Usage: python automation_cli.py")
        print("Interactive tool for experimenting with automation workflows")
        return

    try:
        cli = AutomationCLI()
        asyncio.run(cli.main_loop())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your setup and try again.")

if __name__ == "__main__":
    main()