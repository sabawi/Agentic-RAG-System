# Agentic-RAG Server - Autonomous Agents

This directory contains autonomous agents that leverage the Agentic-RAG server's capabilities to perform automated tasks.

## 📁 Directory Structure

```
agents/
├── README.md                    # This file
├── AGENTS_OVERVIEW.md           # Comprehensive agents documentation
├── agent_template.py            # Template for building new agents
├── stock_monitor_agent.py       # Example: Stock portfolio monitor
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

---

## 🤖 Available Agents

### 1. **News Retriever Agent** 📰
**Location:** `news_retriever/`
**Purpose:** Automatically fetch and deliver news summaries

**Features:**
- Fetches latest news via server's LLM
- HTML formatted output with professional styling
- Email delivery or file storage
- Scheduled or on-demand execution
- 50% faster than original version

**Quick Start:**
```bash
cd news_retriever
python news_retriever_improved.py --once
```

**Documentation:** [news_retriever/README.md](news_retriever/README.md)

---

### 2. **Autonomous System Tuner** ⚙️
**Location:** `system_tuner/`
**Purpose:** Self-optimizing system performance tuner

**Features:**
- **Phase 1:** Discovers system capabilities and limitations
- **Phase 2:** Researches optimal tuning strategies via LLM
- **Phase 3:** Plans safe, reversible optimizations
- **Phase 4:** Executes changes with full backup
- **Phase 5:** Validates improvements and reports

**Quick Start:**
```bash
cd system_tuner
python autonomous_system_tuner.py --dry-run
```

**Documentation:** [system_tuner/README.md](system_tuner/README.md)

---

## 🚀 Getting Started

### Prerequisites

1. **Agentic-RAG Server Running:**
```bash
# From project root
./start_complete.sh

# Verify
curl http://localhost:5000/health
```

2. **Python Virtual Environment:**
```bash
# Each agent has its own venv (optional)
cd news_retriever
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Your First Agent

**News Retriever (Quick Test):**
```bash
cd news_retriever
python news_retriever_improved.py --test    # Test connection
python news_retriever_improved.py --once    # Fetch news once
```

**System Tuner (Safe Dry-Run):**
```bash
cd system_tuner
python autonomous_system_tuner.py --dry-run  # Plan only, no changes
```

---

## 🛠️ Building Your Own Agent

### Method 1: Use the Template

Copy and customize the template:
```bash
cp agent_template.py my_custom_agent.py
```

Edit `my_custom_agent.py`:
1. Replace `[AGENT_NAME]` with your agent's name
2. Implement the `agent_task()` method
3. Add custom methods as needed
4. Update CLI arguments

### Method 2: Study the Examples

Learn from working agents:
- **Simple:** `news_retriever_improved.py` - Single-purpose agent
- **Complex:** `autonomous_system_tuner.py` - Multi-phase autonomous agent
- **Domain-specific:** `stock_monitor_agent.py` - Financial data agent

---

## 📚 Documentation

### Main Documentation
- **[AGENTS_OVERVIEW.md](AGENTS_OVERVIEW.md)** - Comprehensive guide to all agents
  - Available server tools
  - Agent ideas and use cases
  - Best practices
  - Troubleshooting

### Agent-Specific
- **[news_retriever/README.md](news_retriever/README.md)** - News agent guide
- **[system_tuner/README.md](system_tuner/README.md)** - System tuner guide

### Server Documentation
- **[../docs/production/USER_GUIDE.md](../docs/production/USER_GUIDE.md)** - Server features and API
- **[../docs/production/ADMINISTRATOR_GUIDE.md](../docs/production/ADMINISTRATOR_GUIDE.md)** - Server admin guide

---

## 🎯 Agent Capabilities

All agents can leverage these server tools:

### Information & Research
- `get_news_summaries` - Latest news
- `search_web` - Web search
- `lookup_website` - Extract from URLs
- `wikipedia_query` - Wikipedia info
- `published_papers_search` - Academic papers
- `document_search` - Indexed documents

### Communication
- `email_retriever` - Retrieve emails
- `secure_email_sender` - Send emails with attachments
- `google_calendar_scheduler` - Calendar management
- `flight_search` - Flight information

### Analysis & Computing
- `calculator` - Math calculations
- `comprehensive_stock_analyzer` - Financial analysis
- `sandboxed_executor` - Safe code execution
- `process_executor` - System commands

### Content Creation
- `analytical_visualizer` - Charts and graphs
- `image_to_text` - OCR
- `pdf_generator` - Create PDFs

---

## 💡 Agent Ideas

Build agents for:

1. **Stock Portfolio Monitor** ✅ (Example included!)
   - Daily performance reports
   - Price alerts
   - Email notifications

2. **Document Summarizer**
   - Watch folder for new PDFs
   - Auto-summarize and email
   - Maintain searchable archive

3. **Email Digest**
   - Morning briefing from overnight emails
   - Priority categorization
   - Action item extraction

4. **Research Aggregator**
   - Track specific topics
   - Daily paper digest
   - Trend analysis

5. **Calendar Assistant**
   - Daily schedule briefs
   - Meeting reminders
   - Travel time calculations

6. **Web Monitor**
   - Track websites for changes
   - Keyword alerts
   - Content archiving

7. **Financial Analyst**
   - News + stock correlation
   - Portfolio recommendations
   - Market sentiment analysis

8. **System Tuner** ✅ (Implemented!)
   - Autonomous performance optimization
   - Self-learning tuner
   - Safe and reversible

---

## 🔧 Common Patterns

### Pattern 1: Scheduled Task
```python
# Run every N hours/minutes
schedule.every(N).hours.do(task_function)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Pattern 2: Retry Logic
```python
for attempt in range(1, max_retries + 1):
    try:
        result = execute_task()
        return result
    except Exception as e:
        if attempt < max_retries:
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
```

### Pattern 3: LLM Interaction
```python
client = openai.OpenAI(base_url=server_url, api_key="not-required")

response = client.chat.completions.create(
    model="Agentic-RAG-Model1",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
)

result = response.choices[0].message.content
```

### Pattern 4: CLI Arguments
```python
parser = argparse.ArgumentParser(description="My Agent")
parser.add_argument('--once', action='store_true')
parser.add_argument('--schedule', action='store_true')
parser.add_argument('--test', action='store_true')
args = parser.parse_args()
```

---

## 📊 Performance Tips

### Efficient API Calls
- Use single, well-crafted prompts
- Explicitly reference server tools
- Leverage streaming for long responses

### Error Handling
- Implement retry logic with exponential backoff
- Log all errors with context
- Graceful degradation on failures

### Resource Management
- Clean up temporary files
- Close connections properly
- Monitor memory usage

### Testing
- Always include test mode (`--test`)
- Provide run-once mode for debugging
- Test before deploying to schedule

---

## 🛡️ Best Practices

1. **Logging**
   - Use Python's logging module
   - Log to both file and console
   - Include timestamps and severity

2. **Configuration**
   - Use CLI arguments
   - Environment variables for secrets
   - Config files for static settings

3. **Safety**
   - Validate inputs
   - Handle errors gracefully
   - Provide rollback capability

4. **Documentation**
   - Clear README for each agent
   - Usage examples
   - Troubleshooting guide

---

## 🐛 Troubleshooting

### Agent Can't Connect to Server
```bash
# Check if server is running
curl http://localhost:5000/health

# Verify server URL in agent config
# Default: http://localhost:5000/v1
```

### Module Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install/reinstall dependencies
pip install -r requirements.txt
```

### Permission Errors
```bash
# Make agent executable
chmod +x agent_name.py

# Check file permissions
ls -l agent_name.py
```

### Logging Issues
```bash
# Check log file
tail -f agent_name.log

# Enable verbose logging
python agent_name.py --verbose
```

---

## 📈 Agent Performance

### News Retriever
- **Execution Time:** ~60-90 seconds
- **API Calls:** 1 (optimized)
- **Output Size:** ~15KB HTML
- **Success Rate:** 95%+ with retry logic

### System Tuner
- **Discovery Phase:** ~5 seconds
- **Research Phase:** ~60 seconds (LLM query)
- **Execution Phase:** 2-5 minutes
- **Overall:** 3-6 minutes for complete tuning

---

## 🎓 Learning Resources

### Understanding Agents
1. Study `agent_template.py` - Basic structure
2. Review `news_retriever_improved.py` - Simple agent
3. Analyze `autonomous_system_tuner.py` - Complex agent

### Server Integration
- Review server tool documentation
- Test tools via API: `http://localhost:5000/docs`
- Check server logs for tool execution

### Python Best Practices
- Logging: Python logging module
- CLI: argparse library
- Scheduling: schedule library
- API: OpenAI client library

---

## 🚀 Contributing

To add a new agent:

1. **Create subdirectory:**
```bash
mkdir agents/my_agent
```

2. **Copy template:**
```bash
cp agent_template.py agents/my_agent/my_agent.py
```

3. **Implement functionality:**
   - Customize `agent_task()` method
   - Add specific logic
   - Update CLI arguments

4. **Add documentation:**
```bash
# Create README.md in agent directory
agents/my_agent/README.md
```

5. **Test thoroughly:**
```bash
python my_agent.py --test
python my_agent.py --once
```

6. **Update this README:**
   - Add to "Available Agents" section
   - Include quick start example

---

## 📝 Version History

- **v1.0.0** (2025-10-25)
  - Initial agents directory structure
  - News Retriever Agent (improved)
  - Autonomous System Tuner
  - Agent template
  - Stock Monitor example

---

## 📄 License

Part of the Agentic-RAG Server project.

---

## 🎯 Quick Reference

**Test an agent:**
```bash
cd agent_name
python agent_script.py --test
```

**Run once:**
```bash
python agent_script.py --once
```

**Schedule:**
```bash
python agent_script.py --schedule
```

**Get help:**
```bash
python agent_script.py --help
```

---

**Happy Agent Building!** 🤖

For detailed documentation, see [AGENTS_OVERVIEW.md](AGENTS_OVERVIEW.md)
