# Agents Quick Start Guide

## Directory Structure

```
agents/
├── README.md                    # Main documentation
├── AGENTS_OVERVIEW.md           # Comprehensive guide
├── QUICKSTART.md                # This file
├── agent_template.py            # Template for new agents
├── stock_monitor_agent.py       # Example agent
│
├── news_retriever/              # News Retrieval Agent
│   ├── news_retriever_improved.py
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md
│   └── news_output/
│
└── system_tuner/                # Autonomous System Tuner
    ├── autonomous_system_tuner.py
    ├── README.md
    ├── system_tuner.log
    └── system_tuning_backups/
```

## Quick Test - News Retriever

```bash
# From project root
cd agents/news_retriever

# Create virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test connection to server
python news_retriever_improved.py --test

# Fetch news once
python news_retriever_improved.py --once
```

## Quick Test - System Tuner

```bash
# From project root  
cd agents/system_tuner

# Use project's venv (has openai installed)
../../venv/bin/python autonomous_system_tuner.py --dry-run
```

## Running from Project Root

```bash
# News Retriever (needs its own venv with dependencies)
cd agents/news_retriever
source venv/bin/activate
python news_retriever_improved.py --once

# System Tuner (use project venv)
./venv/bin/python agents/system_tuner/autonomous_system_tuner.py --dry-run
```

## Building a New Agent

```bash
# Copy template
cp agents/agent_template.py agents/my_new_agent.py

# Edit and customize
# 1. Replace [AGENT_NAME]
# 2. Implement agent_task() method
# 3. Test

python agents/my_new_agent.py --test
```

## Documentation

- **Main Guide:** [agents/README.md](README.md)
- **Comprehensive:** [agents/AGENTS_OVERVIEW.md](AGENTS_OVERVIEW.md)
- **News Retriever:** [agents/news_retriever/README.md](news_retriever/README.md)
- **System Tuner:** [agents/system_tuner/README.md](system_tuner/README.md)
