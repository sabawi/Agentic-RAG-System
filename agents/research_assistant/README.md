# Personal Research Assistant Agent 📚

Automated academic and research paper aggregation and analysis agent.

## Features

- 📄 **Paper Monitoring** - Track specific research topics for new academic papers
- 📊 **Smart Summarization** - Generate quick summaries of papers for review
- 📈 **Trend Analysis** - Identify emerging research trends and citations
- 📚 **Reading Lists** - Create prioritized reading lists with relevance scoring
- 📧 **Email Digests** - Send curated research digests via email
- 🔄 **Scheduled Execution** - Run daily or weekly automatically

## Installation

### 1. Navigate to Agent Directory
```bash
cd agents/research_assistant
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure (Optional)
Edit `config.py` to customize:
- Server URL
- Default topics
- Output directory
- Schedule times

## Usage

### Test Connection
```bash
./research_assistant.py --test
```

### Daily Research Update
```bash
# Run once with specific topics
./research_assistant.py --daily --topics "machine learning" "AI" "neural networks"

# With email notification
./research_assistant.py --daily --topics "quantum computing" --email researcher@example.com
```

### Weekly Analysis
```bash
# Comprehensive weekly analysis with trend analysis and reading lists
./research_assistant.py --weekly --topics "computer vision" "NLP" --email researcher@example.com
```

### Scheduled Execution
```bash
# Schedule daily research updates at 8:00 AM
./research_assistant.py --schedule-daily --topics "blockchain" "AI" --email user@example.com
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--test` | Test server connection |
| `--daily` | Generate daily research update |
| `--weekly` | Generate weekly analysis with trends |
| `--schedule-daily` | Schedule daily research at 8:00 AM |
| `--topics` | Research topics to monitor (required) |
| `--email` | Recipient email for reports |
| `--server` | Server URL (default: from config.py) |
| `--output-dir` | Output directory (default: research_output) |
| `--verbose` | Enable verbose logging |

## Output

Reports are saved as HTML files in the `research_output/` directory:
- `research_daily_digest_YYYYMMDD_HHMMSS.html` - Daily digests
- `research_weekly_analysis_YYYYMMDD_HHMMSS.html` - Weekly analysis

## Configuration

Edit `config.py` to customize:

```python
# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Default Topics
DEFAULT_TOPICS = [
    "machine learning",
    "artificial intelligence"
]

# Schedule
DAILY_RUN_TIME = "08:00"  # 8:00 AM
```

## Server Tools Used

- `published_papers_search` - Find recent academic papers
- LLM analysis for trend identification and summarization
- `secure_email_sender` - Send research digests

## Troubleshooting

### ModuleNotFoundError
```bash
# Ensure dependencies are installed
pip install -r requirements.txt
```

### Server Connection Failed
```bash
# Check if server is running
curl http://localhost:5000/health

# Test connection
./research_assistant.py --test
```

### Permission Denied
```bash
# Make executable
chmod +x research_assistant.py
```

## Examples

### Track AI Research Daily
```bash
./research_assistant.py --daily --topics "artificial intelligence" "deep learning" "transformers"
```

### Weekly Quantum Computing Digest
```bash
./research_assistant.py --weekly --topics "quantum computing" "quantum algorithms" --email physics@university.edu
```

### Automated Daily Research
```bash
# Run in background with nohup
nohup ./research_assistant.py --schedule-daily --topics "biotechnology" "CRISPR" --email researcher@lab.org &
```

## Logs

Activity is logged to `research_assistant.log`:
```bash
tail -f research_assistant.log
```

## Version

Version: 1.0.0
