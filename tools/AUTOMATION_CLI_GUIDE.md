# 🚀 Multi-Step Automation CLI Guide

## Overview

The Multi-Step Automation CLI is an interactive, user-friendly interface for experimenting with automated AI workflows. It provides real-time monitoring, pause/resume functionality, and comprehensive result tracking.

## Quick Start

### Launch the CLI
```bash
# From project root directory
./automation

# Or directly
cd tools && python automation_cli.py
```

### Prerequisites
- FastAPI server running on `http://localhost:5000`
- Python 3.8+ with required dependencies
- Virtual environment (recommended)

## Features

### 🎯 **Real-Time Monitoring**
- Live progress bars with iteration tracking
- Step-by-step status updates
- Goal achievement scoring in real-time
- Template execution feedback

### ⏸️ **Interactive Controls**
- **CTRL+C**: Pause, stop, or continue execution
- **Graceful interruption**: Complete current iteration before stopping
- **Resume capability**: Pick up where you left off
- **Manual intervention**: Adjust workflow mid-execution

### 📊 **Comprehensive Results**
- Detailed session analytics
- Goal achievement metrics
- Iteration-by-iteration progress
- Automatic result saving
- Historical session viewing

### 🔧 **Configuration Options**
- **Preset workflows**: Math, Research, Creative Writing
- **Custom configurations**: Build your own automation logic
- **Template editor**: Create and modify prompt sequences
- **Goal customization**: Define success criteria

## Main Menu Options

### 1. 🧪 Quick Test (Simple Math Problem)
Perfect for testing the framework with straightforward problems.

**Example queries:**
- "What is 127 * 89?"
- "Solve for x: 2x + 5 = 17"
- "Calculate the area of a circle with radius 8"

**Goal criteria:**
- Solution provided with numerical answer
- Explanation of methodology
- Verification of calculations

### 2. 🔬 Research Analysis (Complex Topic Research)
Comprehensive research workflow with deep analysis.

**Example queries:**
- "Artificial intelligence in healthcare"
- "Climate change mitigation strategies"
- "Blockchain technology applications"

**Goal criteria:**
- Minimum 1000 characters of content
- Technical depth with methodologies
- Future implications and trends
- Structured report format

### 3. 💡 Creative Writing (Story Generation)
Creative content generation with narrative structure.

**Example queries:**
- "A detective in a haunted library"
- "Time travel adventure in ancient Egypt"
- "Robot companion in post-apocalyptic world"

**Goal criteria:**
- Story elements (characters, plot, setting)
- Minimum 800 characters
- Narrative structure with dialogue

### 4. 📁 Load Custom Configuration
Load pre-built configuration files.

**Available configurations:**
- `example_research_config.json`: Advanced research workflow
- `demo_config.json`: Demonstration configuration
- Custom saved configurations

### 5. ⚙️ Create New Configuration
Interactive configuration builder.

**Steps:**
1. Select goal type (problem solving, research, creative)
2. Set maximum iterations
3. Add prompt templates
4. Define success criteria
5. Save for future use

### 6. 📊 View Previous Results
Browse and analyze past automation sessions.

**Features:**
- Session list with success indicators
- Detailed result viewing
- Performance metrics
- Historical comparison

### 7. ❓ Help & Documentation
Comprehensive help system with examples and tips.

## CLI Controls During Execution

### Signal Handling (CTRL+C)
When you press CTRL+C during automation:

```
⏸️  Received interrupt signal. Current options:
1. ⏸️  Pause (resume later)
2. 🛑 Stop automation
3. ↩️  Continue

Choose action (1/2/3):
```

- **Pause (1)**: Temporarily halt execution, resume with ENTER
- **Stop (2)**: Gracefully terminate after current iteration
- **Continue (3)**: Resume normal execution

### Progress Display
```
🔄 Progress: [████████████░░░░░░░░] 60.0% | Iteration 3/5 | technical_analysis | Running
```

- **Progress bar**: Visual completion indicator
- **Iteration counter**: Current/total iterations
- **Template name**: Currently executing prompt template
- **Status**: Running, Paused, or Stopped

### Iteration Feedback
```
📊 ITERATION 2 COMPLETE:
   Template: technical_deep_dive
   Response Length: 1,247 chars
   Goal Score: 0.657
   ❌ Missing: Technical depth, Future insights
```

## Configuration File Format

### Basic Structure
```json
{
  "goal_type": "research_analysis",
  "target_goal": {
    "criteria": {
      "criterion_name": {
        "keywords": ["keyword1", "keyword2"],
        "min_matches": 2,
        "weight": 0.4
      }
    },
    "min_score": 0.8
  },
  "prompt_templates": [
    {
      "name": "template_name",
      "template": "Your prompt with {query} placeholder",
      "weight": 1.0
    }
  ],
  "max_iterations": 10,
  "server_url": "http://localhost:5000"
}
```

### Goal Types
- **`problem_solving`**: Math, logic, specific questions
- **`research_analysis`**: Research, analysis, comprehensive reports
- **`creative_writing`**: Stories, creative content generation

### Criteria Types
- **`keywords`**: Text must contain specified keywords
- **`min_length`**: Minimum character count requirement
- **`patterns`**: Must match specific text patterns
- **`min_matches`**: Minimum number of criteria hits needed

## Advanced Usage

### Custom Prompt Templates
Templates support variable substitution:
```json
{
  "name": "analysis_template",
  "template": "Analyze {query} from multiple perspectives. Consider economic, social, and technological implications.",
  "weight": 1.0
}
```

### Complex Goal Criteria
```json
{
  "comprehensive_analysis": {
    "keywords": ["methodology", "framework", "implementation"],
    "min_matches": 2,
    "weight": 0.3
  },
  "sufficient_length": {
    "min_length": 1500,
    "weight": 0.2
  },
  "structured_format": {
    "patterns": ["##", "###", "1.", "2."],
    "min_matches": 3,
    "weight": 0.5
  }
}
```

### Debugging and Troubleshooting

#### Common Issues

**1. Server Connection Error**
```
❌ Error during automation: Connection refused
```
**Solution**: Ensure FastAPI server is running on `http://localhost:5000`

**2. Import Errors**
```
❌ Error: Could not import multi_step_automation module
```
**Solution**: Run from project root directory or check Python path

**3. Configuration Errors**
```
❌ Error loading file: Invalid JSON format
```
**Solution**: Validate JSON syntax in configuration files

#### Verbose Mode
For detailed debugging, modify the automation configuration:
```json
{
  "debug_mode": true,
  "verbose_logging": true
}
```

## Best Practices

### 1. Start Simple
- Begin with preset configurations
- Test with straightforward queries
- Gradually increase complexity

### 2. Optimize Goal Criteria
- Use realistic scoring thresholds (0.6-0.8)
- Balance multiple criteria weights
- Include both positive and negative indicators

### 3. Template Diversity
- Create varied prompt approaches
- Use different question styles
- Include verification and refinement templates

### 4. Monitor Progress
- Watch real-time feedback
- Intervene when necessary
- Adjust criteria based on results

### 5. Save Configurations
- Document successful workflows
- Create reusable templates
- Build a configuration library

## Result Analysis

### Session Metrics
```json
{
  "session_id": "abc12345",
  "execution_time": 45.2,
  "total_iterations": 5,
  "goal_achieved": true,
  "final_score": 0.847,
  "iterations": [...detailed_history...]
}
```

### Performance Indicators
- **Goal Achievement**: Binary success/failure
- **Final Score**: Weighted criteria satisfaction (0.0-1.0)
- **Execution Time**: Total automation duration
- **Iteration Efficiency**: Score improvement per iteration

## Examples

### Research Query Example
```
Query: "quantum computing applications in cryptography"

Iteration 1: initial_research (Score: 0.324)
Iteration 2: technical_deep_dive (Score: 0.567)
Iteration 3: future_implications (Score: 0.789)
✅ Goal achieved in 3 iterations!
```

### Problem Solving Example
```
Query: "What is the derivative of sin(x²)?"

Iteration 1: problem_setup (Score: 0.645)
Iteration 2: verification (Score: 0.823)
✅ Goal achieved in 2 iterations!
```

## Integration with Main System

The CLI integrates seamlessly with the main Agentic RAG System:
- Uses the same FastAPI server
- Leverages existing tool infrastructure
- Maintains session consistency
- Provides automation layer over manual queries

## Contributing

To extend the CLI:
1. Add new preset configurations in `load_preset_config()`
2. Create custom goal types in the automation framework
3. Implement additional progress monitoring features
4. Add new result visualization options

For support and contributions, see the main project documentation.