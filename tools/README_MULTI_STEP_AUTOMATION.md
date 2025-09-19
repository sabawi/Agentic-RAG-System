# 🚀 Multi-Step Server Prompting Automation System

A comprehensive automation framework for achieving complex goals through iterative prompting with intelligent context management and goal achievement detection.

## 🎯 Overview

This system implements a sophisticated loop-based approach:
```
Prompt A → Server Response → Context Buffer → Goal Check → Prompt B + Context → Continue/Stop
```

The automation continues until either:
- ✅ The predefined goal is achieved
- ⏰ Maximum iterations reached
- ❌ Error condition encountered

## 🏗️ Architecture

### Core Components

1. **PromptTemplate**: Dynamic prompt templates with variable substitution
2. **ContextBuffer**: Intelligent context accumulation with optimization
3. **GoalAchievementDetector**: Multi-criteria goal evaluation system
4. **MultiStepAutomation**: Main orchestration engine

### Key Features

- 🧠 **Intelligent Context Management**: Automatic context optimization when size limits are exceeded
- 🎯 **Goal Achievement Detection**: Multiple criteria types (keywords, patterns, length, custom functions)
- 📊 **Comprehensive Logging**: Detailed execution tracking and analytics
- 🔄 **Adaptive Prompting**: Dynamic prompt selection based on progress
- ⚡ **Production Ready**: Error handling, timeouts, and recovery mechanisms

## 📋 Goal Achievement Criteria Types

### 1. Keyword Criteria
```json
{
  "id": "contains_solution",
  "description": "Response contains solution keywords",
  "check_type": "keyword",
  "check_value": ["solution", "answer", "result"],
  "weight": 1.5,
  "required": true
}
```

### 2. Pattern Criteria (Regex)
```json
{
  "id": "numerical_answer",
  "description": "Contains numerical result",
  "check_type": "pattern",
  "check_value": "\\b\\d+(?:\\.\\d+)?\\b",
  "weight": 2.0,
  "required": true
}
```

### 3. Length Criteria
```json
{
  "id": "sufficient_detail",
  "description": "Response has adequate length",
  "check_type": "length",
  "check_value": {"min": 500, "max": 10000},
  "weight": 1.0,
  "required": false
}
```

### 4. Custom Function Criteria
```python
def custom_check(context_buffer):
    # Custom logic here
    return {
        "passed": True,
        "details": "Custom validation passed",
        "score": 0.95
    }

criteria = {
    "id": "custom_validation",
    "description": "Custom business logic validation",
    "check_type": "custom_function",
    "check_value": custom_check,
    "weight": 1.0,
    "required": true
}
```

## 🚀 Quick Start

### 1. Basic Usage

```python
import asyncio
from multi_step_automation import MultiStepAutomation

async def simple_example():
    # Initialize automation
    automation = MultiStepAutomation(
        server_url="http://localhost:5000",
        endpoint="/llama3_1b/stream",
        max_iterations=10,
        iteration_delay=2.0
    )

    # Create configuration
    config = automation.create_example_configuration("research_analysis")

    # Save and load configuration
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    automation.load_configuration("config.json")

    # Run automation
    variables = {"topic": "artificial intelligence trends"}
    results = await automation.run_automation(variables)

    # Check results
    print(f"Goal Achieved: {results['goal_achieved']}")
    print(f"Final Score: {results['final_score']}")

    return results

# Run the example
results = asyncio.run(simple_example())
```

### 2. Command Line Usage

```bash
# Research analysis
python multi_step_automation.py --goal research_analysis --topic "quantum computing" --max-iterations 8

# Problem solving
python multi_step_automation.py --goal problem_solving --problem "improve team productivity" --max-iterations 6

# Creative writing
python multi_step_automation.py --goal creative_writing --genre "sci-fi" --theme "AI consciousness" --max-iterations 10

# Custom configuration
python multi_step_automation.py --config my_custom_config.json --output results.json
```

## 📊 Built-in Goal Types

### 1. Research Analysis
**Purpose**: Comprehensive topic investigation and analysis
**Prompts**: Initial research → Technical deep dive → Future implications → Synthesis report
**Criteria**: Content length, technical depth, future insights, structured format

```bash
python multi_step_automation.py --goal research_analysis --topic "blockchain applications in healthcare"
```

### 2. Problem Solving
**Purpose**: Systematic issue resolution with implementation plans
**Prompts**: Problem analysis → Solution generation → Evaluation → Implementation plan
**Criteria**: Solution provided, implementation details included

```bash
python multi_step_automation.py --goal problem_solving --problem "reduce customer churn in SaaS business"
```

### 3. Creative Writing
**Purpose**: Story development and refinement
**Prompts**: Story outline → Character development → Scene writing → Refinement
**Criteria**: Story length, essential story elements present

```bash
python multi_step_automation.py --goal creative_writing --genre "mystery" --theme "corporate espionage"
```

## 📝 Configuration Format

### Complete Configuration Example

```json
{
  "description": "Custom goal description",
  "max_iterations": 10,
  "iteration_delay": 2.0,
  "prompts": [
    {
      "id": "initial_prompt",
      "template": "Work on {objective}. Provide detailed analysis of {aspect}.",
      "variables": ["objective", "aspect"],
      "priority": 10,
      "context_weight": 0.5,
      "expected_response_type": "analysis"
    },
    {
      "id": "follow_up",
      "template": "Continue working on {objective}. Build upon previous progress.",
      "variables": ["objective"],
      "priority": 8,
      "context_weight": 1.0,
      "expected_response_type": "continuation"
    }
  ],
  "goal_criteria": [
    {
      "id": "completion_keywords",
      "description": "Contains completion indicators",
      "check_type": "keyword",
      "check_value": ["completed", "finished", "achieved", "done"],
      "weight": 1.5,
      "required": true
    },
    {
      "id": "sufficient_depth",
      "description": "Response has sufficient depth",
      "check_type": "length",
      "check_value": {"min": 1000, "max": 20000},
      "weight": 1.0,
      "required": true
    }
  ],
  "initial_goal_progress": {
    "phase": "starting",
    "completion_level": 0
  }
}
```

## 🔧 Advanced Features

### Context Buffer Optimization

The system automatically optimizes context when it exceeds size limits:

- **Importance Scoring**: Calculates importance based on recency, length, and key phrases
- **Smart Truncation**: Preserves recent iterations and high-importance content
- **Summary Generation**: Creates concise summaries for prompting

### Goal Progress Tracking

```python
# Access goal progress during execution
context_buffer.goal_progress = {
    "analysis_completed": True,
    "solutions_generated": 3,
    "implementation_started": False
}
```

### Custom Prompt Selection

Override the default sequential prompt selection:

```python
class CustomAutomation(MultiStepAutomation):
    def get_next_prompt(self, variables):
        # Custom logic for prompt selection
        # Based on goal progress, iteration count, etc.
        return selected_prompt_template
```

## 📊 Results and Analytics

### Results Structure

```json
{
  "session_id": "unique-session-id",
  "start_time": "2025-09-18T17:00:00",
  "end_time": "2025-09-18T17:15:30",
  "total_iterations": 6,
  "goal_achieved": true,
  "final_score": 0.92,
  "execution_time": 930.5,
  "iterations": [
    {
      "iteration": 1,
      "prompt_template": "initial_research",
      "response_length": 1250,
      "goal_status": {
        "achieved": false,
        "progress_score": 0.3,
        "criteria_results": {...}
      }
    }
  ],
  "achievement_details": {
    "timestamp": "2025-09-18T17:15:30",
    "total_iterations": 6,
    "final_score": 0.92
  },
  "final_context": "Summarized context...",
  "error": null
}
```

### Performance Metrics

- **Goal Achievement Rate**: Percentage of successful goal completions
- **Average Iterations**: Mean iterations required for goal achievement
- **Context Efficiency**: Context utilization and optimization frequency
- **Response Quality**: Length and content analysis trends

## 🧪 Testing

### Run Test Suite

```bash
# Run all tests
python quick_automation_test.py

# Run specific examples
python run_automation_example.py
```

### Test Output Example

```
🧪 Testing Simple Goal Achievement
==================================================
🎯 Goal: Solve math problem with verification
📝 Problem: What is the area of a circle with radius 5 meters?

📊 RESULTS:
✅ Goal Achieved: True
📈 Final Score: 0.95
🔄 Iterations: 3
⏱️ Time: 8.2s
```

## 🛠️ Production Deployment

### Server Requirements

- **FastAPI Server**: Running on specified URL/endpoint
- **Python 3.8+**: With required dependencies
- **Memory**: Sufficient for context buffer management
- **Network**: Stable connection for API calls

### Error Handling

The system includes comprehensive error handling:

- **Server Timeouts**: Configurable timeout with retry logic
- **Context Overflow**: Automatic optimization and recovery
- **Goal Detection Failures**: Graceful degradation and logging
- **Network Issues**: Retry mechanisms and error reporting

### Monitoring

Enable detailed logging:

```python
import logging
logging.getLogger('multi_step_automation').setLevel(logging.DEBUG)
```

Monitor key metrics:
- Iteration success rates
- Context optimization frequency
- Goal achievement statistics
- Response quality trends

## 🔗 API Integration

### Custom Server Endpoints

Adapt to different server configurations:

```python
automation = MultiStepAutomation(
    server_url="https://your-server.com",
    endpoint="/v1/chat/completions",  # OpenAI compatible
    max_iterations=15,
    iteration_delay=1.0
)
```

### Response Format Handling

The system automatically handles various response formats:
- OpenAI API format (`choices[0].message.content`)
- Custom format (`response` field)
- Raw text responses

## 📈 Use Cases

### Business Applications

1. **Market Research**: Comprehensive industry analysis
2. **Product Planning**: Feature requirement analysis
3. **Content Creation**: Documentation and marketing materials
4. **Problem Resolution**: Technical troubleshooting workflows
5. **Strategic Planning**: Business strategy development

### Technical Applications

1. **Code Analysis**: Architecture review and optimization
2. **Documentation Generation**: API and system documentation
3. **Testing Scenarios**: Test case generation and validation
4. **System Design**: Architecture planning and evaluation
5. **Debugging Workflows**: Systematic issue investigation

## 🎯 Best Practices

### Configuration Design

1. **Clear Objectives**: Define specific, measurable goals
2. **Progressive Prompts**: Build complexity gradually
3. **Balanced Criteria**: Mix required and optional criteria
4. **Realistic Limits**: Set appropriate iteration limits

### Prompt Engineering

1. **Context Integration**: Use context_weight effectively
2. **Variable Substitution**: Leverage dynamic variables
3. **Response Guidance**: Specify expected response types
4. **Progressive Depth**: Increase specificity over iterations

### Goal Achievement

1. **Multiple Criteria**: Use diverse criteria types
2. **Weighted Scoring**: Assign appropriate criterion weights
3. **Required vs Optional**: Balance mandatory and bonus criteria
4. **Custom Validation**: Implement domain-specific checks

## 🔮 Future Enhancements

- **Machine Learning Integration**: Adaptive prompt selection
- **Multi-Agent Orchestration**: Parallel goal pursuit
- **Template Learning**: Automatic prompt optimization
- **Real-time Analytics**: Live performance dashboards
- **Cloud Deployment**: Scalable infrastructure support

---

**Version**: 1.0.0
**Last Updated**: September 18, 2025
**Status**: Production Ready

For support and contributions, see the main project documentation.