# News Retriever Agent

## Overview

An enhanced news retrieval agent that automatically fetches and delivers news summaries on demand or on a schedule.

## Features

- ✅ **Single efficient API call** (vs 3 in original version)
- ✅ **Retry logic** with exponential backoff (2s, 4s, 8s)
- ✅ **Professional HTML output** with styling
- ✅ **Run-once or scheduled modes** (flexible execution)
- ✅ **Email delivery or file storage** (or both)
- ✅ **Comprehensive logging** (file + console)
- ✅ **CLI arguments** (no code editing needed)
- ✅ **Test mode** for debugging

## Quick Start

### 1. Setup Virtual Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure
Edit `config.py`:
```python
RECIPIENT_EMAIL = "your-email@example.com"
SERVER_URL = "http://localhost:5000/v1"
```

### 3. Run

**Test connection:**
```bash
python news_retriever_improved.py --test
```

**Run once and save to file:**
```bash
python news_retriever_improved.py --once
```

**Run every 2 hours and email results:**
```bash
python news_retriever_improved.py --schedule --interval 2 --email you@example.com
```

**Custom output directory:**
```bash
python news_retriever_improved.py --once --output-dir ~/my_news
```

## Command-Line Options

```
usage: news_retriever_improved.py [-h] (--once | --schedule | --test)
                                  [--server SERVER] [--email EMAIL]
                                  [--output-dir OUTPUT_DIR]
                                  [--interval INTERVAL] [--no-save]
                                  [--retries RETRIES] [--verbose]

Mode Arguments:
  --once              Run once and exit
  --schedule          Run on schedule (continuous)
  --test              Test server connection and exit

Configuration:
  --server SERVER     Server URL (default: http://localhost:5000/v1)
  --email EMAIL       Recipient email address
  --output-dir DIR    Output directory for HTML files (default: news_output)
  --interval N        Hours between scheduled runs (default: 1)
  --no-save           Do not save output to file
  --retries N         Maximum retry attempts (default: 3)
  --verbose           Enable verbose logging
```

## Example Usage

### Daily Morning News Briefing
```bash
# Schedule for 8:00 AM daily
python news_retriever_improved.py --schedule --interval 24 \
  --email you@example.com \
  --output-dir ~/daily_news
```

### Hourly News Updates
```bash
python news_retriever_improved.py --schedule --interval 1 \
  --email you@example.com
```

### One-Time News Fetch
```bash
python news_retriever_improved.py --once --verbose
```

### Test and Debug
```bash
# Test server connection
python news_retriever_improved.py --test

# Run once with verbose output
python news_retriever_improved.py --once --verbose
```

## Output

News summaries are saved as HTML files with:
- Professional styling and formatting
- Timestamp and generation metadata
- Organized by category
- Source links
- Mobile-friendly layout

**Example output location:**
```
news_output/news_summary_20251025_143857.html
```

## Logging

All activity is logged to:
- **Console:** Real-time output
- **File:** `news_agent.log`

Log levels:
- `INFO`: Normal operation
- `WARNING`: Recoverable issues
- `ERROR`: Failures
- `DEBUG`: Detailed information (with `--verbose`)

## Performance

**Compared to original version:**
- **Speed:** 50% faster (89s vs 120-180s)
- **API Calls:** 1 vs 3 (66% reduction)
- **Reliability:** Retry logic with exponential backoff
- **Flexibility:** Multiple execution modes

## Configuration File

`config.py`:
```python
# Email recipient
RECIPIENT_EMAIL = "sabawi@gmail.com"

# Server URL (must be running)
SERVER_URL = "http://localhost:5000/v1"
```

## Requirements

See `requirements.txt`:
```
openai
schedule
```

## Troubleshooting

### Server Connection Failed
```bash
# Check if server is running
curl http://localhost:5000/health

# Test connection
python news_retriever_improved.py --test
```

### Email Not Sending
- Verify email configuration in server's `.env` file
- Check server logs for email errors
- Ensure secure_email_sender tool is configured

### No News Retrieved
- Check server logs for tool execution
- Verify network connectivity
- Run with `--verbose` for detailed output

## Integration with Agentic-RAG Server

This agent leverages the server's `get_news_summaries` tool by:
1. Sending optimized prompt to server
2. Server executes `get_news_summaries` tool
3. Server formats results as HTML
4. Agent saves and/or emails results

**Server tool used:**
- `get_news_summaries` - Fetches latest news with full article content

## Related Files

- `../agent_template.py` - Template for building new agents
- `../stock_monitor_agent.py` - Example stock portfolio monitor
- `../AGENTS_OVERVIEW.md` - Comprehensive agents documentation

## Version History

- **v2.0.0** - Complete rewrite with modern architecture
  - CLI arguments
  - Retry logic
  - Professional logging
  - Flexible execution modes

- **v1.0.0** - Original basic version
  - Hardcoded configuration
  - Scheduler only
  - Basic error handling

## License

Part of the Agentic-RAG Server project.

## Support

For issues or questions, refer to:
- Main project documentation: `../../docs/`
- Server documentation: `../../docs/production/USER_GUIDE.md`
- Agents overview: `../AGENTS_OVERVIEW.md`
