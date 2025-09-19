# 🚀 Automation CLI Quick Start

## What is it?
Interactive command-line tool for experimenting with multi-step AI automation workflows.

## Launch
```bash
# Easy launcher
./automation

# Or directly
python tools/automation_cli.py
```

## Key Features
- **📊 Real-time monitoring** with progress bars and live updates
- **⏸️ Interactive controls** - pause, stop, resume with CTRL+C
- **🎯 Goal-driven automation** - keeps iterating until objectives are met
- **📁 Preset workflows** - math problems, research, creative writing
- **⚙️ Custom configurations** - build your own automation logic
- **💾 Result tracking** - comprehensive session analytics

## Quick Demo

### 1. Simple Math Test
```
Enter choice: 1
Math problem: What is 127 * 89?

🔄 Progress: [████████░░░░] 60% | Iteration 3/5 | verification | Running
✅ Goal achieved in 3 iterations!
```

### 2. Research Analysis
```
Enter choice: 2
Research topic: artificial intelligence in healthcare

🔄 Progress: [██████████░░] 75% | Iteration 6/8 | synthesis_report | Running
📊 Final Score: 0.847 - SUCCESS!
```

### 3. Creative Writing
```
Enter choice: 3
Story prompt: a detective in a haunted library

🔄 Progress: [████████████] 100% | Iteration 4/6 | story_completion | Running
🎉 Creative goal achieved!
```

## Controls During Execution

**CTRL+C** opens control menu:
- **Pause** - temporarily halt, resume later
- **Stop** - gracefully terminate current session
- **Continue** - resume normal execution

## Configuration
- Load existing configs from `tools/` directory
- Create custom workflows interactively
- Save configurations for reuse
- Import/export automation templates

## Results
All sessions automatically saved with:
- Goal achievement status
- Execution metrics
- Complete conversation history
- Performance analytics

## Documentation
- **Full Guide**: `tools/AUTOMATION_CLI_GUIDE.md`
- **Framework Docs**: `tools/README_MULTI_STEP_AUTOMATION.md`
- **Examples**: `tools/example_*.json`

Start experimenting with `./automation` - perfect for testing complex AI workflows!