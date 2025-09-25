#!/usr/bin/env python3
"""
Multi-Step Server Prompting Automation Script
==============================================

A powerful automation framework for achieving complex goals through iterative prompting.
Implements a loop-based system: Prompt A → Response → Context Buffer → Prompt B + Context → Goal Check → Continue/Stop

Features:
- Dynamic prompt sequences with context accumulation
- Goal achievement detection with customizable criteria
- Comprehensive logging and monitoring
- Flexible prompt templates and goal definitions
- Context management and optimization
- Error handling and recovery mechanisms

Usage:
    python multi_step_automation.py --config goal_config.json
    python multi_step_automation.py --goal "research_analysis" --max_iterations 10
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import aiohttp
import requests
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_step_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PromptTemplate:
    """Template for prompts with dynamic variable substitution"""
    id: str
    template: str
    variables: List[str]
    priority: int = 5
    context_weight: float = 1.0
    expected_response_type: str = "text"

    def format(self, variables: Dict[str, Any], context: str = "") -> str:
        """Format the prompt template with variables and context"""
        formatted = self.template

        # Substitute variables
        for var_name, var_value in variables.items():
            formatted = formatted.replace(f"{{{var_name}}}", str(var_value))

        # Add context if available
        if context and self.context_weight > 0:
            context_section = f"\n\n## Previous Context:\n{context}\n\n## Current Task:"
            formatted = formatted + context_section

        return formatted

@dataclass
class GoalCriteria:
    """Criteria for determining if a goal has been achieved"""
    id: str
    description: str
    check_type: str  # "keyword", "pattern", "length", "custom_function"
    check_value: Any
    weight: float = 1.0
    required: bool = True

@dataclass
class ContextBuffer:
    """Buffer for accumulating context across iterations"""
    session_id: str
    iterations: List[Dict[str, Any]]
    goal_progress: Dict[str, Any]
    current_size: int = 0
    max_size: int = 50000  # Character limit

    def add_iteration(self, prompt: str, response: str, metadata: Dict[str, Any]):
        """Add a new iteration to the context buffer"""
        iteration = {
            "iteration_number": len(self.iterations) + 1,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "metadata": metadata,
            "context_size": len(prompt) + len(response)
        }

        self.iterations.append(iteration)
        self.current_size += iteration["context_size"]

        # Optimize context if too large
        if self.current_size > self.max_size:
            self._optimize_context()

    def _optimize_context(self):
        """Optimize context buffer by removing older, less important iterations"""
        logger.info(f"Optimizing context buffer (current size: {self.current_size})")

        # Keep last 5 iterations and most important ones
        important_iterations = self.iterations[-5:]

        # Calculate importance scores for older iterations
        older_iterations = self.iterations[:-5]
        scored_iterations = []

        for iteration in older_iterations:
            score = self._calculate_importance_score(iteration)
            scored_iterations.append((score, iteration))

        # Sort by importance and keep top ones until size limit
        scored_iterations.sort(key=lambda x: x[0], reverse=True)

        optimized_iterations = important_iterations.copy()
        current_size = sum(iter["context_size"] for iter in important_iterations)

        for score, iteration in scored_iterations:
            if current_size + iteration["context_size"] <= self.max_size * 0.8:
                optimized_iterations.insert(-5, iteration)
                current_size += iteration["context_size"]

        self.iterations = sorted(optimized_iterations, key=lambda x: x["iteration_number"])
        self.current_size = current_size

        logger.info(f"Context optimized: {len(self.iterations)} iterations, {self.current_size} characters")

    def _calculate_importance_score(self, iteration: Dict[str, Any]) -> float:
        """Calculate importance score for an iteration"""
        score = 0.0

        # Recent iterations get higher scores
        recency_bonus = 1.0 / (len(self.iterations) - iteration["iteration_number"] + 1)
        score += recency_bonus * 0.3

        # Longer responses might be more important
        response_length_bonus = min(len(iteration["response"]) / 1000, 1.0)
        score += response_length_bonus * 0.2

        # Check for key phrases that indicate progress
        key_phrases = ["completed", "achieved", "success", "error", "important", "critical"]
        phrase_bonus = sum(0.1 for phrase in key_phrases if phrase.lower() in iteration["response"].lower())
        score += phrase_bonus

        return score

    def get_summary_context(self, max_length: int = 2000) -> str:
        """Get a summarized version of the context for prompting"""
        if not self.iterations:
            return ""

        # Include goal progress
        progress_summary = f"Goal Progress:\n{json.dumps(self.goal_progress, indent=2)}\n\n"

        # Include recent iterations
        recent_iterations = self.iterations[-3:]  # Last 3 iterations
        iteration_summaries = []

        for iteration in recent_iterations:
            summary = f"Iteration {iteration['iteration_number']}:\n"
            summary += f"Prompt: {iteration['prompt'][:200]}...\n"
            summary += f"Response: {iteration['response'][:300]}...\n"
            iteration_summaries.append(summary)

        full_context = progress_summary + "\n".join(iteration_summaries)

        # Truncate if too long
        if len(full_context) > max_length:
            full_context = full_context[:max_length] + "\n[Context truncated...]"

        return full_context

class GoalAchievementDetector:
    """Detects when a goal has been achieved based on defined criteria"""

    def __init__(self, criteria: List[GoalCriteria]):
        self.criteria = criteria
        self.achievement_history = []

    async def check_goal_achievement(self, context_buffer: ContextBuffer) -> Dict[str, Any]:
        """Check if the goal has been achieved using parallel criterion evaluation"""
        results = {
            "achieved": False,
            "progress_score": 0.0,
            "criteria_results": {},
            "missing_requirements": [],
            "achievement_details": {}
        }

        total_weight = sum(c.weight for c in self.criteria)
        achieved_weight = 0.0

        # Parallel criterion checking for better performance
        async def check_criterion_async(criterion):
            return criterion, self._check_single_criterion(criterion, context_buffer)

        # Run all criterion checks concurrently
        criterion_tasks = [check_criterion_async(criterion) for criterion in self.criteria]
        criterion_results = await asyncio.gather(*criterion_tasks, return_exceptions=True)

        for result in criterion_results:
            if isinstance(result, Exception):
                logger.error(f"Error in parallel criterion check: {result}")
                continue

            criterion, criterion_result = result
            results["criteria_results"][criterion.id] = criterion_result

            if criterion_result["passed"]:
                achieved_weight += criterion.weight
            elif criterion.required:
                results["missing_requirements"].append(criterion.description)

        results["progress_score"] = achieved_weight / total_weight if total_weight > 0 else 0.0

        # Goal is achieved if all required criteria are met and progress score > 0.8
        results["achieved"] = (
            len(results["missing_requirements"]) == 0 and
            results["progress_score"] >= 0.8
        )

        if results["achieved"]:
            results["achievement_details"] = {
                "timestamp": datetime.now().isoformat(),
                "total_iterations": len(context_buffer.iterations),
                "final_score": results["progress_score"]
            }
            logger.info(f"🎯 GOAL ACHIEVED! Score: {results['progress_score']:.2f}")

        return results

    def _check_single_criterion(self, criterion: GoalCriteria, context_buffer: ContextBuffer) -> Dict[str, Any]:
        """Check a single criterion against the context buffer"""
        result = {
            "passed": False,
            "details": "",
            "score": 0.0
        }

        # Get the latest response content
        latest_response = context_buffer.iterations[-1]["response"] if context_buffer.iterations else ""
        all_responses = " ".join([iter["response"] for iter in context_buffer.iterations])

        try:
            if criterion.check_type == "keyword":
                # Check for specific keywords
                if isinstance(criterion.check_value, dict):
                    keywords = criterion.check_value.get('keywords', [])
                    min_matches = criterion.check_value.get('min_matches', 1)
                else:
                    keywords = criterion.check_value if isinstance(criterion.check_value, list) else [criterion.check_value]
                    min_matches = 1

                found_keywords = [kw for kw in keywords if isinstance(kw, str) and kw.lower() in all_responses.lower()]
                result["passed"] = len(found_keywords) >= min_matches
                result["details"] = f"Found keywords: {found_keywords}"
                result["score"] = len(found_keywords) / len(keywords) if keywords else 0

            elif criterion.check_type == "pattern":
                # Check for regex patterns
                pattern = criterion.check_value
                matches = re.findall(pattern, all_responses, re.IGNORECASE)
                result["passed"] = len(matches) > 0
                result["details"] = f"Pattern matches: {len(matches)}"
                result["score"] = min(len(matches) / 5, 1.0)  # Normalize to 0-1

            elif criterion.check_type == "length":
                # Check response length requirements
                min_length = criterion.check_value.get("min", 0)
                max_length = criterion.check_value.get("max", float('inf'))
                total_length = len(all_responses)
                result["passed"] = min_length <= total_length <= max_length
                result["details"] = f"Total response length: {total_length}"
                result["score"] = 1.0 if result["passed"] else 0.0

            elif criterion.check_type == "custom_function":
                # Use a custom function for checking
                check_function = criterion.check_value
                if callable(check_function):
                    custom_result = check_function(context_buffer)
                    result.update(custom_result)
                else:
                    result["details"] = "Invalid custom function"

        except Exception as e:
            logger.error(f"Error checking criterion {criterion.id}: {e}")
            result["details"] = f"Error: {str(e)}"

        return result

class MultiStepAutomation:
    """Main automation class for multi-step server prompting"""

    def __init__(self,
                 server_url: str = "http://localhost:5000",
                 endpoint: str = "/llama3_1b/stream",
                 max_iterations: int = 20,
                 iteration_delay: float = 2.0):
        self.server_url = server_url
        self.endpoint = endpoint
        self.max_iterations = max_iterations
        self.iteration_delay = iteration_delay
        self.session_id = str(uuid.uuid4())

        # Initialize components
        self.context_buffer = None
        self.goal_detector = None
        self.prompt_templates = []
        self.current_prompt_index = 0

        logger.info(f"🚀 Multi-Step Automation initialized (Session: {self.session_id})")

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'MultiStepAutomation':
        """Create MultiStepAutomation instance from configuration dictionary"""
        # Extract basic parameters
        server_url = config.get('server_url', 'http://localhost:5000')
        endpoint = config.get('endpoint', '/llama3_1b/stream')
        max_iterations = config.get('max_iterations', 20)
        iteration_delay = config.get('iteration_delay', 2.0)

        # Create instance
        automation = cls(
            server_url=server_url,
            endpoint=endpoint,
            max_iterations=max_iterations,
            iteration_delay=iteration_delay
        )

        # Load prompt templates
        template_configs = config.get('prompt_templates', [])
        automation.prompt_templates = [
            PromptTemplate(
                id=t.get('name', f'template_{i}'),
                template=t.get('template', ''),
                variables=['query'],  # Default to query variable
                priority=5,
                context_weight=t.get('weight', 1.0)
            ) for i, t in enumerate(template_configs)
        ]

        # Set up goal detector if target_goal is provided
        target_goal = config.get('target_goal')
        if target_goal:
            criteria = []
            criteria_config = target_goal.get('criteria', {})

            for criterion_name, criterion_data in criteria_config.items():
                # Determine check type and value based on criterion data
                if 'keywords' in criterion_data:
                    check_type = "keyword"
                    check_value = {
                        'keywords': criterion_data.get('keywords', []),
                        'min_matches': criterion_data.get('min_matches', 1)
                    }
                elif 'min_length' in criterion_data:
                    check_type = "length"
                    # Convert min_length to proper format expected by checking logic
                    min_length = criterion_data.get('min_length', 0)
                    max_length = criterion_data.get('max_length', float('inf'))
                    check_value = {"min": min_length, "max": max_length}
                elif 'patterns' in criterion_data:
                    check_type = "pattern"
                    # Convert patterns list to single pattern for regex
                    patterns = criterion_data.get('patterns', [])
                    if isinstance(patterns, list):
                        # Join patterns with OR operator for regex
                        check_value = '|'.join(f'({pattern})' for pattern in patterns)
                    else:
                        check_value = patterns
                else:
                    check_type = "keyword"
                    check_value = {'keywords': [], 'min_matches': 1}

                criteria.append(GoalCriteria(
                    id=criterion_name,
                    description=f"Goal criteria: {criterion_name}",
                    check_type=check_type,
                    check_value=check_value,
                    weight=criterion_data.get('weight', 1.0),
                    required=True
                ))

            if criteria:
                automation.goal_detector = GoalAchievementDetector(criteria)

        # Initialize context buffer with goal type
        goal_type = config.get('goal_type', 'general')
        automation.context_buffer = ContextBuffer(
            session_id=automation.session_id,
            iterations=[],
            goal_progress={"type": goal_type, "target_score": target_goal.get('min_score', 0.8) if target_goal else 0.8}
        )

        logger.info(f"✅ Automation created from config - Goal: {goal_type}, Templates: {len(automation.prompt_templates)}")
        return automation

    def load_configuration(self, config_path: str):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Load prompt templates
            self.prompt_templates = [
                PromptTemplate(**template) for template in config.get("prompts", [])
            ]

            # Load goal criteria
            criteria = [
                GoalCriteria(**criterion) for criterion in config.get("goal_criteria", [])
            ]
            self.goal_detector = GoalAchievementDetector(criteria)

            # Initialize context buffer
            self.context_buffer = ContextBuffer(
                session_id=self.session_id,
                iterations=[],
                goal_progress=config.get("initial_goal_progress", {})
            )

            # Update settings
            self.max_iterations = config.get("max_iterations", self.max_iterations)
            self.iteration_delay = config.get("iteration_delay", self.iteration_delay)

            logger.info(f"✅ Configuration loaded: {len(self.prompt_templates)} prompts, {len(criteria)} criteria")

        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            raise

    def create_example_configuration(self, goal_type: str = "research_analysis") -> Dict[str, Any]:
        """Create example configurations for different goal types"""

        if goal_type == "research_analysis":
            return {
                "description": "Research Analysis Goal - Comprehensive topic investigation",
                "max_iterations": 15,
                "iteration_delay": 3.0,
                "prompts": [
                    {
                        "id": "initial_research",
                        "template": "Research and analyze the topic: {topic}. Provide a comprehensive overview covering key aspects, recent developments, and important insights. Focus on factual information and cite sources.",
                        "variables": ["topic"],
                        "priority": 10,
                        "context_weight": 0.5,
                        "expected_response_type": "detailed_analysis"
                    },
                    {
                        "id": "deep_dive",
                        "template": "Based on the previous research, dive deeper into the most important aspects of {topic}. Identify specific areas that need more investigation and provide detailed analysis.",
                        "variables": ["topic"],
                        "priority": 8,
                        "context_weight": 1.0,
                        "expected_response_type": "detailed_analysis"
                    },
                    {
                        "id": "synthesis",
                        "template": "Synthesize all the research findings about {topic}. Create a comprehensive summary that includes: 1) Key findings, 2) Important trends, 3) Future implications, 4) Recommendations.",
                        "variables": ["topic"],
                        "priority": 9,
                        "context_weight": 1.0,
                        "expected_response_type": "synthesis"
                    },
                    {
                        "id": "verification",
                        "template": "Review the research analysis for completeness and accuracy. Identify any gaps or areas that need clarification about {topic}.",
                        "variables": ["topic"],
                        "priority": 6,
                        "context_weight": 1.0,
                        "expected_response_type": "review"
                    }
                ],
                "goal_criteria": [
                    {
                        "id": "comprehensive_coverage",
                        "description": "Research covers multiple aspects comprehensively",
                        "check_type": "length",
                        "check_value": {"min": 2000, "max": 20000},
                        "weight": 1.0,
                        "required": True
                    },
                    {
                        "id": "key_insights",
                        "description": "Contains key insights and analysis",
                        "check_type": "keyword",
                        "check_value": ["insight", "analysis", "trend", "implication", "finding"],
                        "weight": 1.5,
                        "required": True
                    },
                    {
                        "id": "structured_content",
                        "description": "Content is well-structured with clear sections",
                        "check_type": "pattern",
                        "check_value": r"(?:Key findings|Summary|Implications|Recommendations|Conclusion)",
                        "weight": 1.0,
                        "required": False
                    }
                ],
                "initial_goal_progress": {
                    "research_depth": 0,
                    "coverage_areas": [],
                    "insights_discovered": 0
                }
            }

        elif goal_type == "problem_solving":
            return {
                "description": "Problem Solving Goal - Systematic issue resolution",
                "max_iterations": 10,
                "iteration_delay": 2.0,
                "prompts": [
                    {
                        "id": "problem_analysis",
                        "template": "Analyze this problem in detail: {problem_description}. Break it down into components, identify root causes, and outline potential approaches.",
                        "variables": ["problem_description"],
                        "priority": 10,
                        "context_weight": 0.3,
                        "expected_response_type": "analysis"
                    },
                    {
                        "id": "solution_generation",
                        "template": "Generate multiple solutions for the problem: {problem_description}. Provide at least 3 different approaches with pros and cons for each.",
                        "variables": ["problem_description"],
                        "priority": 9,
                        "context_weight": 1.0,
                        "expected_response_type": "solutions"
                    },
                    {
                        "id": "solution_evaluation",
                        "template": "Evaluate the proposed solutions and recommend the best approach for: {problem_description}. Consider feasibility, effectiveness, and implementation requirements.",
                        "variables": ["problem_description"],
                        "priority": 8,
                        "context_weight": 1.0,
                        "expected_response_type": "evaluation"
                    },
                    {
                        "id": "implementation_plan",
                        "template": "Create a detailed implementation plan for the recommended solution to: {problem_description}. Include steps, timeline, and success metrics.",
                        "variables": ["problem_description"],
                        "priority": 7,
                        "context_weight": 1.0,
                        "expected_response_type": "plan"
                    }
                ],
                "goal_criteria": [
                    {
                        "id": "solution_provided",
                        "description": "A concrete solution is provided",
                        "check_type": "keyword",
                        "check_value": ["solution", "approach", "recommendation", "plan"],
                        "weight": 2.0,
                        "required": True
                    },
                    {
                        "id": "implementation_details",
                        "description": "Implementation details are provided",
                        "check_type": "keyword",
                        "check_value": ["implementation", "steps", "timeline", "plan"],
                        "weight": 1.5,
                        "required": True
                    }
                ],
                "initial_goal_progress": {
                    "analysis_completed": False,
                    "solutions_generated": 0,
                    "recommendation_made": False
                }
            }

        elif goal_type == "creative_writing":
            return {
                "description": "Creative Writing Goal - Story development and refinement",
                "max_iterations": 12,
                "iteration_delay": 2.5,
                "prompts": [
                    {
                        "id": "story_outline",
                        "template": "Create an outline for a {genre} story about {theme}. Include main characters, plot structure, and key scenes.",
                        "variables": ["genre", "theme"],
                        "priority": 10,
                        "context_weight": 0.2,
                        "expected_response_type": "outline"
                    },
                    {
                        "id": "character_development",
                        "template": "Develop detailed character profiles for the {genre} story about {theme}. Include backgrounds, motivations, and character arcs.",
                        "variables": ["genre", "theme"],
                        "priority": 8,
                        "context_weight": 0.8,
                        "expected_response_type": "characters"
                    },
                    {
                        "id": "scene_writing",
                        "template": "Write key scenes for the {genre} story about {theme}. Focus on compelling dialogue and vivid descriptions.",
                        "variables": ["genre", "theme"],
                        "priority": 9,
                        "context_weight": 1.0,
                        "expected_response_type": "scenes"
                    },
                    {
                        "id": "story_refinement",
                        "template": "Refine and polish the {genre} story about {theme}. Improve flow, consistency, and overall quality.",
                        "variables": ["genre", "theme"],
                        "priority": 7,
                        "context_weight": 1.0,
                        "expected_response_type": "refined_story"
                    }
                ],
                "goal_criteria": [
                    {
                        "id": "story_length",
                        "description": "Story has adequate length",
                        "check_type": "length",
                        "check_value": {"min": 1500, "max": 50000},
                        "weight": 1.0,
                        "required": True
                    },
                    {
                        "id": "story_elements",
                        "description": "Contains essential story elements",
                        "check_type": "keyword",
                        "check_value": ["character", "plot", "dialogue", "scene", "conflict"],
                        "weight": 1.5,
                        "required": True
                    }
                ],
                "initial_goal_progress": {
                    "outline_complete": False,
                    "characters_developed": 0,
                    "scenes_written": 0
                }
            }

        else:
            # Default generic configuration
            return {
                "description": "Generic Goal - Custom objective achievement",
                "max_iterations": 10,
                "iteration_delay": 2.0,
                "prompts": [
                    {
                        "id": "initial_prompt",
                        "template": "Work on achieving this goal: {goal_description}. Provide a comprehensive response.",
                        "variables": ["goal_description"],
                        "priority": 10,
                        "context_weight": 0.5,
                        "expected_response_type": "text"
                    },
                    {
                        "id": "continuation_prompt",
                        "template": "Continue working on: {goal_description}. Build upon previous progress and provide additional insights.",
                        "variables": ["goal_description"],
                        "priority": 8,
                        "context_weight": 1.0,
                        "expected_response_type": "text"
                    },
                    {
                        "id": "refinement_prompt",
                        "template": "Refine and improve the work on: {goal_description}. Address any gaps and enhance quality.",
                        "variables": ["goal_description"],
                        "priority": 6,
                        "context_weight": 1.0,
                        "expected_response_type": "text"
                    }
                ],
                "goal_criteria": [
                    {
                        "id": "sufficient_content",
                        "description": "Sufficient content has been generated",
                        "check_type": "length",
                        "check_value": {"min": 500, "max": 50000},
                        "weight": 1.0,
                        "required": True
                    }
                ],
                "initial_goal_progress": {}
            }

    async def send_prompt_to_server(self, prompt: str) -> str:
        """Send a prompt to the server and return the response using async HTTP"""
        try:
            # Choose payload format based on endpoint
            if "/v1/chat/completions" in self.endpoint:
                # OpenAI-compatible format
                payload = {
                    "model": "qwen3:8b",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            else:
                # Legacy format for /llama3_1b/stream
                payload = {
                    "prompt": prompt,
                    "stream": False,
                    "max_tokens": 4000,
                    "temperature": 0.7
                }

            logger.info(f"📤 Sending prompt ({len(prompt)} chars) to {self.server_url}{self.endpoint}")

            # Use async HTTP client with connection pooling
            timeout = aiohttp.ClientTimeout(total=2700)  # 45 minute timeout
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                keepalive_timeout=300
            )

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            ) as session:
                async with session.post(
                    f"{self.server_url}{self.endpoint}",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Extract content based on response format
                        if "choices" in result and len(result["choices"]) > 0:
                            content = result["choices"][0].get("message", {}).get("content", "")
                        elif "response" in result:
                            content = result["response"]
                        else:
                            content = str(result)

                        logger.info(f"📥 Received response ({len(content)} chars)")
                        return content
                    else:
                        error_text = await response.text()
                        error_msg = f"Server error: {response.status} - {error_text}"
                        logger.error(error_msg)
                        return f"Error: {error_msg}"

        except asyncio.TimeoutError:
            error_msg = "Request timed out - server may be processing a complex query"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except aiohttp.ClientError as e:
            error_msg = f"Connection failed - check if server is running: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

    def get_next_prompt(self, variables: Dict[str, Any]) -> Optional[PromptTemplate]:
        """Get the next prompt template in the sequence"""
        if self.current_prompt_index >= len(self.prompt_templates):
            # Cycle back to beginning or use adaptive selection
            self.current_prompt_index = 0

        if not self.prompt_templates:
            return None

        # Simple sequential selection (can be enhanced with adaptive logic)
        template = self.prompt_templates[self.current_prompt_index]
        self.current_prompt_index += 1

        return template

    async def run_parallel_exploration(self, variables: Dict[str, Any], max_parallel: int = 3) -> Dict[str, Any]:
        """Run multiple prompt templates in parallel for faster exploration"""
        logger.info(f"🚀 Starting parallel automation exploration (max {max_parallel} concurrent)")

        start_time = time.time()
        results = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "total_iterations": 0,
            "goal_achieved": False,
            "final_score": 0.0,
            "execution_time": 0.0,
            "iterations": [],
            "final_context": "",
            "achievement_details": {}
        }

        try:
            # Run multiple prompts concurrently
            active_templates = self.prompt_templates[:max_parallel]

            async def process_template(template, template_vars):
                context = self.context_buffer.get_summary_context() if self.context_buffer else ""
                formatted_prompt = template.format(template_vars, context)
                response = await self.send_prompt_to_server(formatted_prompt)

                # Immediately add to context buffer when this template completes
                metadata = {
                    "template_id": template.id,
                    "prompt_length": len(formatted_prompt),
                    "response_length": len(response)
                }

                self.context_buffer.add_iteration(formatted_prompt, response, metadata)
                results["iterations"].append(metadata)
                logger.info(f"✅ Template '{template.id}' completed - Progress: {len(results['iterations'])}/{len(active_templates)}")

                return {
                    "template": template,
                    "prompt": formatted_prompt,
                    "response": response,
                    "metadata": metadata
                }

            # Execute templates in parallel
            template_tasks = [process_template(template, variables) for template in active_templates]
            parallel_results = await asyncio.gather(*template_tasks, return_exceptions=True)

            # Handle any exceptions from parallel execution
            for result in parallel_results:
                if isinstance(result, Exception):
                    logger.error(f"Parallel template error: {result}")
                    continue

            # Check goal achievement with all parallel results
            if self.goal_detector:
                goal_status = await self.goal_detector.check_goal_achievement(self.context_buffer)
                results["goal_achieved"] = goal_status["achieved"]
                results["final_score"] = goal_status["progress_score"]

                if goal_status["achieved"]:
                    results["achievement_details"] = goal_status["achievement_details"]
                    logger.info(f"🎉 GOAL ACHIEVED through parallel exploration!")

            results["total_iterations"] = len(results["iterations"])

        except Exception as e:
            logger.error(f"❌ Parallel automation error: {e}")
            results["error"] = str(e)

        # Finalize results
        results["execution_time"] = time.time() - start_time
        results["final_context"] = self.context_buffer.get_summary_context() if self.context_buffer else ""

        logger.info(f"🏁 PARALLEL AUTOMATION COMPLETED")
        logger.info(f"📈 Parallel Executions: {results['total_iterations']}")
        logger.info(f"🎯 Goal Achieved: {results['goal_achieved']}")
        logger.info(f"📊 Final Score: {results['final_score']:.2f}")
        logger.info(f"⏱️ Execution Time: {results['execution_time']:.1f}s")

        return results

    async def run_automation(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Run the multi-step automation process"""
        logger.info(f"🎯 Starting automation with goal achievement detection")

        start_time = time.time()
        iteration_count = 0
        goal_achieved = False

        results = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "total_iterations": 0,
            "goal_achieved": False,
            "final_score": 0.0,
            "execution_time": 0.0,
            "iterations": [],
            "final_context": "",
            "achievement_details": {}
        }

        try:
            while iteration_count < self.max_iterations and not goal_achieved:
                iteration_count += 1
                logger.info(f"\n🔄 === ITERATION {iteration_count}/{self.max_iterations} ===")

                # Get next prompt template
                prompt_template = self.get_next_prompt(variables)
                if not prompt_template:
                    logger.error("❌ No prompt templates available")
                    break

                # Get context for this iteration
                context = self.context_buffer.get_summary_context() if self.context_buffer else ""

                # Format the prompt with variables and context
                formatted_prompt = prompt_template.format(variables, context)

                logger.info(f"📝 Using prompt template: {prompt_template.id}")
                logger.info(f"📏 Prompt length: {len(formatted_prompt)} chars")

                # Send prompt to server
                response = await self.send_prompt_to_server(formatted_prompt)

                # Add to context buffer
                iteration_metadata = {
                    "prompt_template_id": prompt_template.id,
                    "prompt_length": len(formatted_prompt),
                    "response_length": len(response),
                    "variables_used": variables.copy()
                }

                self.context_buffer.add_iteration(formatted_prompt, response, iteration_metadata)

                # Check goal achievement
                goal_status = await self.goal_detector.check_goal_achievement(self.context_buffer)
                goal_achieved = goal_status["achieved"]

                # Log progress
                logger.info(f"📊 Goal Progress: {goal_status['progress_score']:.2f}")
                logger.info(f"✅ Criteria Met: {len([r for r in goal_status['criteria_results'].values() if r['passed']])}/{len(goal_status['criteria_results'])}")

                if goal_status["missing_requirements"]:
                    logger.info(f"🔍 Missing: {', '.join(goal_status['missing_requirements'])}")

                # Store iteration results
                iteration_result = {
                    "iteration": iteration_count,
                    "prompt_template": prompt_template.id,
                    "response_length": len(response),
                    "goal_status": goal_status,
                    "timestamp": datetime.now().isoformat()
                }
                results["iterations"].append(iteration_result)

                # Update results
                results["final_score"] = goal_status["progress_score"]

                if goal_achieved:
                    results["achievement_details"] = goal_status["achievement_details"]
                    logger.info(f"🎉 GOAL ACHIEVED in {iteration_count} iterations!")
                    break

                # Skip unnecessary delay for better performance
                # Note: Removed iteration delay to optimize execution speed

        except Exception as e:
            logger.error(f"❌ Automation error: {e}")
            results["error"] = str(e)

        # Finalize results
        results["total_iterations"] = iteration_count
        results["goal_achieved"] = goal_achieved
        results["execution_time"] = time.time() - start_time
        results["end_time"] = datetime.now().isoformat()
        results["final_context"] = self.context_buffer.get_summary_context(max_length=5000)

        logger.info(f"\n🏁 AUTOMATION COMPLETED")
        logger.info(f"📈 Total Iterations: {iteration_count}")
        logger.info(f"🎯 Goal Achieved: {goal_achieved}")
        logger.info(f"📊 Final Score: {results['final_score']:.2f}")
        logger.info(f"⏱️ Execution Time: {results['execution_time']:.1f}s")

        return results

    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save automation results to file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Results saved to: {output_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")

async def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Multi-Step Server Prompting Automation")
    parser.add_argument("--config", help="Path to configuration JSON file")
    parser.add_argument("--goal", default="research_analysis",
                       choices=["research_analysis", "problem_solving", "creative_writing", "custom"],
                       help="Predefined goal type")
    parser.add_argument("--server", default="http://localhost:5000", help="Server URL")
    parser.add_argument("--endpoint", default="/llama3_1b/stream", help="API endpoint")
    parser.add_argument("--max-iterations", type=int, default=10, help="Maximum iterations")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between iterations")
    parser.add_argument("--output", help="Output file for results")

    # Goal-specific arguments
    parser.add_argument("--topic", help="Research topic (for research_analysis)")
    parser.add_argument("--problem", help="Problem description (for problem_solving)")
    parser.add_argument("--genre", help="Story genre (for creative_writing)")
    parser.add_argument("--theme", help="Story theme (for creative_writing)")
    parser.add_argument("--goal-description", help="Custom goal description")

    args = parser.parse_args()

    # Initialize automation
    automation = MultiStepAutomation(
        server_url=args.server,
        endpoint=args.endpoint,
        max_iterations=args.max_iterations,
        iteration_delay=args.delay
    )

    # Load or create configuration
    if args.config:
        automation.load_configuration(args.config)
    else:
        # Create configuration based on goal type
        config = automation.create_example_configuration(args.goal)

        # Save example configuration
        config_filename = f"config_{args.goal}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(config_filename, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"📝 Generated configuration: {config_filename}")

        # Load the configuration
        automation.load_configuration(config_filename)

    # Prepare variables based on goal type
    variables = {}
    if args.goal == "research_analysis":
        variables["topic"] = args.topic or "artificial intelligence and machine learning"
    elif args.goal == "problem_solving":
        variables["problem_description"] = args.problem or "How to improve team productivity in remote work environments"
    elif args.goal == "creative_writing":
        variables["genre"] = args.genre or "science fiction"
        variables["theme"] = args.theme or "first contact with alien civilization"
    else:
        variables["goal_description"] = args.goal_description or "Complete a comprehensive analysis task"

    # Run automation
    logger.info(f"🚀 Starting {args.goal} automation with variables: {variables}")
    results = await automation.run_automation(variables)

    # Save results
    output_file = args.output or f"automation_results_{args.goal}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    automation.save_results(results, output_file)

    # Print summary
    print(f"\n{'='*60}")
    print(f"🎯 AUTOMATION SUMMARY")
    print(f"{'='*60}")
    print(f"Goal Type: {args.goal}")
    print(f"Total Iterations: {results['total_iterations']}")
    print(f"Goal Achieved: {'✅ YES' if results['goal_achieved'] else '❌ NO'}")
    print(f"Final Score: {results['final_score']:.2f}")
    print(f"Execution Time: {results['execution_time']:.1f}s")
    print(f"Results File: {output_file}")

    if results.get("achievement_details"):
        print(f"\n🏆 Achievement Details:")
        for key, value in results["achievement_details"].items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())