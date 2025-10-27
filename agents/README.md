# Agentic-RAG Server - Autonomous Agents

This directory contains autonomous agents that leverage the Agentic-RAG server's capabilities to perform automated tasks.

## 📁 Directory Structure

```
agents/
├── README.md                    # This file
├── AGENTS_OVERVIEW.md           # Comprehensive agents documentation
├── QUICKSTART.md                # Quick start guide
├── TESTING_RESULTS.md           # Testing documentation
├── agent_template.py            # Template for building new agents
│
├── common/                      # Shared utilities for all agents
│   ├── agent_utils.py          # Core agent utilities
│   ├── report_utils.py         # HTML report generation
│   ├── __init__.py
│   └── README.md
│
├── research_assistant/          # Academic paper aggregation
│   ├── research_assistant.py
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md
│   └── research_output/
│
├── email_digest/                # Email summarization
│   ├── email_digest.py
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md
│   └── email_digests/
│
├── market_sentiment/            # Market sentiment analysis
│   ├── market_sentiment.py
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md
│   └── sentiment_reports/
│
├── document_intelligence/       # Document processing
│   ├── document_intelligence.py
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md
│   └── document_reports/
│
├── social_media_tracker/        # Social media monitoring
│   ├── social_media_tracker.py
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md
│   └── social_reports/
│
├── stock_monitor/               # Stock portfolio monitoring
│   ├── stock_monitor.py
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md
│   └── stock_reports/
│
├── news_retriever/              # News retrieval
│   ├── news_retriever_improved.py
│   ├── config.py
│   ├── requirements.txt
│   ├── README.md
│   └── news_output/
│
└── system_tuner/                # Autonomous system tuner
    ├── autonomous_system_tuner.py
    ├── README.md
    └── system_tuning_backups/
```

---

## 🤖 Available Agents

### 1. **Research Assistant Agent** 📚
**Location:** `research_assistant/`
**Purpose:** Automated academic and research paper aggregation

**Features:**
- Monitor specific topics for new academic papers
- Summarize papers for quick review
- Track citation trends and research developments
- Generate reading lists and literature reviews
- Send curated research digests via email

**Quick Start:**
```bash
cd research_assistant
./research_assistant.py --daily --topics "machine learning" "AI"
```

**Documentation:** [research_assistant/README.md](research_assistant/README.md)

---

### 2. **Email Digest Agent** 📧
**Location:** `email_digest/`
**Purpose:** Automated email summarization and priority management

**Features:**
- Generate morning email summaries from multiple providers
- Extract action items and categorize by importance
- Analyze email sentiment and urgency
- Send HTML-formatted digest reports
- Track email patterns and trends

**Quick Start:**
```bash
cd email_digest
./email_digest.py --morning --provider gmail_primary
```

**Documentation:** [email_digest/README.md](email_digest/README.md)

---

### 3. **Market Sentiment Analyzer** 📈
**Location:** `market_sentiment/`
**Purpose:** Monitor market sentiment from news and analyze trends

**Features:**
- Aggregate financial news and social media sentiment
- Analyze market trends and sentiment
- Generate charts and visualizations
- Create sentiment trend reports
- Send investment recommendations

**Quick Start:**
```bash
cd market_sentiment
./market_sentiment.py --daily --symbols AAPL TSLA NVDA
```

**Documentation:** [market_sentiment/README.md](market_sentiment/README.md)

---

### 4. **Document Intelligence Agent** 📄
**Location:** `document_intelligence/`
**Purpose:** Automated document processing and insight extraction

**Features:**
- Monitor document folders for new files
- Extract key information using document interrogation
- Create executive summaries
- Track document changes and versions
- Generate searchable archives

**Quick Start:**
```bash
cd document_intelligence
./document_intelligence.py --daily --dirs ~/documents ~/reports
```

**Documentation:** [document_intelligence/README.md](document_intelligence/README.md)

---

### 5. **Social Media Trend Tracker** 📱
**Location:** `social_media_tracker/`
**Purpose:** Monitor and analyze social media trends and brand mentions

**Features:**
- Track brand mentions and social media activity
- Analyze sentiment and trending topics
- Monitor competitor activity
- Generate visual reports and trend analysis
- Create weekly social media reports

**Quick Start:**
```bash
cd social_media_tracker
./social_media_tracker.py --daily --brands "Nike" "Adidas"
```

**Documentation:** [social_media_tracker/README.md](social_media_tracker/README.md)

---

### 6. **Stock Monitor Agent** 💹
**Location:** `stock_monitor/`
**Purpose:** Real-time stock portfolio monitoring with alerts

**Features:**
- Monitor stock portfolio performance
- Alert on significant price changes
- Generate performance reports
- Integrate related news
- Assess portfolio risk

**Quick Start:**
```bash
cd stock_monitor
./stock_monitor.py --daily --symbols AAPL TSLA NVDA
```

**Documentation:** [stock_monitor/README.md](stock_monitor/README.md)

---

### 7. **News Retriever Agent** 📰
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

### 8. **Autonomous System Tuner** ⚙️
**Location:** `system_tuner/`
**Purpose:** Self-optimizing system performance tuner

**Features:**
- Discovers system capabilities and limitations
- Researches optimal tuning strategies via LLM
- Plans safe, reversible optimizations
- Executes changes with full backup
- Validates improvements and reports

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

2. **Dependencies Installed:**
```bash
# Install project dependencies (from project root)
pip install -r requirements.txt
```

### Running Your First Agent

**Research Assistant (Quick Test):**
```bash
cd research_assistant
./research_assistant.py --test    # Test connection
./research_assistant.py --daily --topics "AI" "machine learning"    # Run once
```

**Email Digest (Morning Briefing):**
```bash
cd email_digest
./email_digest.py --morning --provider gmail_primary
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

### Method 2: Create Agent Directory

For a properly organized agent:
```bash
mkdir my_custom_agent
cd my_custom_agent

# Copy template
cp ../agent_template.py my_custom_agent.py

# Create support files
touch requirements.txt config.py README.md .gitignore

# Create output directory
mkdir output
```

### Method 3: Use Common Utilities

Leverage shared utilities for cleaner code:
```python
from common import (
    create_openai_client,
    test_server_connection,
    execute_with_retry,
    setup_agent_logging,
    create_html_report,
    save_html_report
)

# Setup
logger = setup_agent_logging("my_agent")
client = create_openai_client("http://localhost:5000/v1")

# Test connection
if not test_server_connection(client, logger):
    sys.exit(1)

# Execute with retry
result = execute_with_retry(
    client,
    prompt="Your prompt here",
    task_description="Fetching data",
    logger=logger
)

# Save report
html = create_html_report("My Report", result)
save_html_report(html, Path("output"), logger=logger)
```

**Benefits of Using Common Utilities:**
- Eliminates code duplication
- Consistent error handling and retry logic
- Standardized HTML reports
- Centralized logging configuration

---

## 📚 Documentation

### Main Documentation
- **[README.md](README.md)** - This file
- **[AGENTS_OVERVIEW.md](AGENTS_OVERVIEW.md)** - Comprehensive agent guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[common/README.md](common/README.md)** - Shared utilities documentation

### Agent-Specific
Each agent directory contains its own `README.md` with detailed usage instructions.

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

## 💡 Common Patterns

### Pattern 1: Scheduled Task
```python
import schedule

# Run every N hours
schedule.every(N).hours.do(task_function)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Pattern 2: Using Common Utilities
```python
from common import execute_with_retry, setup_agent_logging

logger = setup_agent_logging("my_agent")

result = execute_with_retry(
    client,
    prompt="Your prompt",
    task_description="Task description",
    logger=logger
)
```

### Pattern 3: HTML Report Generation
```python
from common import create_html_report, save_html_report

html = create_html_report("Title", content)
filepath = save_html_report(html, output_dir, logger=logger)
```

---

## 📊 Performance Tips

- **Efficient API Calls**: Use single, well-crafted prompts
- **Error Handling**: Implement retry logic with exponential backoff (use `execute_with_retry`)
- **Resource Management**: Clean up temporary files and close connections
- **Testing**: Always test with `--test` mode before scheduling

---

## 🛡️ Best Practices

1. **Logging**: Use `setup_agent_logging` for consistent logging
2. **Configuration**: Use `config.py` files for settings, `.env` for secrets
3. **Safety**: Validate inputs and handle errors gracefully
4. **Documentation**: Include README.md with usage examples in each agent directory

---

## 🐛 Troubleshooting

### Agent Can't Connect to Server
```bash
# Check if server is running
curl http://localhost:5000/health

# Test connection
cd agent_directory
./agent_script.py --test
```

### Module Import Errors
```bash
# Install dependencies
pip install -r requirements.txt

# Or install from project root
cd /path/to/flaskserver
pip install -r requirements.txt
```

### Permission Errors
```bash
# Make agent executable
chmod +x agent_script.py
```

### Logging Issues
```bash
# Check log file
tail -f agent_name.log
```

---

## 📝 Version History

- **v2.0.0** (2025-10-27)
  - Added 5 new agents: Research Assistant, Email Digest, Market Sentiment, Document Intelligence, Social Media Tracker
  - Reorganized all agents into subdirectories
  - Added common utilities module
  - Created comprehensive documentation for each agent
  - Added config.py files for all agents

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
./agent_script.py --test
```

**Run once:**
```bash
./agent_script.py --once  # or --daily, --weekly depending on agent
```

**Schedule:**
```bash
./agent_script.py --schedule  # or --schedule-daily, --schedule-morning, etc.
```

**Get help:**
```bash
./agent_script.py --help
```

---

**Happy Agent Building!** 🤖

For detailed documentation, see:
- [AGENTS_OVERVIEW.md](AGENTS_OVERVIEW.md) - Comprehensive guide
- Individual agent README.md files in each subdirectory
- [common/README.md](common/README.md) - Shared utilities guide
