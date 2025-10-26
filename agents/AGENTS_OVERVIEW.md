# Agentic-RAG Client Agents

This directory contains client agents that interact with the Agentic-RAG server to perform automated tasks.

## 📋 Available Agents

### 1. **News Retriever Agent** (news_retriever_improved.py)
**Purpose:** Automatically fetches and delivers news summaries on a schedule or on-demand.

**Features:**
- ✅ Single efficient API call (vs 3 in old version)
- ✅ Retry logic with exponential backoff
- ✅ Professional HTML output with styling
- ✅ Run-once or scheduled modes
- ✅ Email delivery or file storage
- ✅ Comprehensive logging

**Quick Start:**
```bash
# Activate virtual environment
source venv/bin/activate

# Test connection
python news_retriever_improved.py --test

# Run once and save to file
python news_retriever_improved.py --once

# Run every 2 hours and email results
python news_retriever_improved.py --schedule --interval 2 --email you@example.com

# Custom output directory
python news_retriever_improved.py --once --output-dir ~/my_news
```

**Help:**
```bash
python news_retriever_improved.py --help
```

---

## 🚀 Quick Setup

### 1. Create Virtual Environment (First Time Only)
```bash
python3 -m venv venv
source venv/bin/activate
pip install openai schedule
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 3. Run an Agent
```bash
python news_retriever_improved.py --once
```

---

## 🛠️ Building Your Own Agents

Use the template provided in `agent_template.py` to build custom agents that leverage the server's capabilities.

### Available Server Tools

Your agents can use these tools by prompting the server appropriately:

#### Information & Research
- `get_news_summaries` - Latest news with full article content
- `search_web` - DuckDuckGo web search
- `lookup_website` - Extract content from URLs and PDFs
- `wikipedia_query` - Wikipedia information
- `published_papers_search` - Academic papers and research
- `document_search` - Search through indexed documents

#### Communication & Productivity
- `email_retriever` - Retrieve and summarize emails
- `secure_email_sender` - Send emails with attachments
- `google_calendar_scheduler` - Manage calendar events
- `flight_search` - Search for flights with pricing

#### Analysis & Computing
- `calculator` - Mathematical calculations
- `comprehensive_stock_analyzer` - Financial analysis
- `get_stock_and_company_data` - Financial data retrieval
- `sandboxed_executor` - Safe code execution
- `process_executor` - System process execution

#### Content Creation
- `analytical_visualizer` - Create charts and graphs
- `image_to_text` - OCR text extraction
- `pdf_generator` - Create PDF documents

---

## 💡 Agent Ideas

Here are some useful agents you can build:

### 1. **Stock Portfolio Monitor**
- Check portfolio daily at market open
- Email alerts for significant price changes
- Generate weekly performance reports

### 2. **Document Summarizer**
- Watch a directory for new PDFs
- Automatically summarize and email key points
- Maintain searchable archive

### 3. **Calendar Assistant**
- Daily morning briefing of schedule
- Automatic meeting reminders
- Travel time calculations

### 4. **Research Aggregator**
- Track specific topics (AI, biotech, etc.)
- Daily digest of new papers and articles
- Highlight connections and trends

### 5. **Email Digest Agent**
- Summarize overnight emails
- Prioritize by importance
- Morning briefing with action items

### 6. **Web Content Monitor**
- Track specific websites for changes
- Alert on new content matching keywords
- Archive important updates

### 7. **Financial News Analyst**
- Track stocks you own
- Fetch related news and analysis
- Generate buy/sell recommendations

### 8. **Smart Reminder System**
- Context-aware reminders
- Integration with calendar and email
- Proactive suggestions

---

## 📁 File Structure

```
gagent/
├── README.md                        # This file
├── agent_template.py                # Template for new agents
├── news_retriever_improved.py       # Enhanced news agent
├── news_retriever_general.py        # Original (basic) agent
├── config.py                        # Configuration file
├── requirements.txt                 # Python dependencies
├── news_agent.log                   # Agent logs
├── news_output/                     # News HTML files
└── venv/                            # Virtual environment
```

---

## 🔧 Configuration

### Environment-Based Config
Create a `.env` file (optional):
```bash
SERVER_URL=http://localhost:5000/v1
RECIPIENT_EMAIL=you@example.com
OUTPUT_DIR=news_output
```

### Command-Line Config
All agents support command-line arguments for easy configuration without code changes.

---

## 📝 Best Practices

### 1. **Efficient API Calls**
- Use single, well-crafted prompts instead of multiple calls
- Explicitly reference server tools in your prompts
- Leverage streaming for long responses

### 2. **Error Handling**
- Implement retry logic with exponential backoff
- Log all errors with context
- Graceful degradation on failures

### 3. **Logging**
- Use Python's logging module
- Log to both file and console
- Include timestamps and severity levels

### 4. **Testing**
- Always include a test mode (`--test`)
- Provide run-once mode for debugging
- Test before deploying to schedule

### 5. **Documentation**
- Clear docstrings for all functions
- Command-line help text
- Usage examples in README

---

## 🐛 Troubleshooting

### Server Connection Issues
```bash
# Test server connectivity
python news_retriever_improved.py --test

# Check if server is running
curl http://localhost:5000/health
```

### Module Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Permission Errors
```bash
# Make scripts executable
chmod +x *.py
```

### Logging Issues
```bash
# Check log file
tail -f news_agent.log

# Enable verbose logging
python news_retriever_improved.py --once --verbose
```

---

## 📊 Performance Comparison

### Old News Agent (news_retriever_general.py)
- **API Calls:** 3 (inefficient)
- **Error Handling:** Basic try/catch
- **Logging:** Print statements only
- **Configuration:** Hardcoded
- **Testing:** Must run scheduler
- **Time:** ~120-180 seconds

### Improved News Agent (news_retriever_improved.py)
- **API Calls:** 1 (optimized prompt)
- **Error Handling:** Retry with exponential backoff
- **Logging:** Professional with file rotation
- **Configuration:** Command-line arguments
- **Testing:** Dedicated test mode
- **Time:** ~60-90 seconds (50% faster)

---

## 🎯 Next Steps

1. **Try the improved news agent** - See the difference in action
2. **Study the template** - Learn the agent pattern
3. **Build your first custom agent** - Start with something simple
4. **Share and iterate** - Contribute improvements back

---

## 📚 Additional Resources

- **Server Documentation:** `/home/sabawi/Development/flaskserver/docs/`
- **API Reference:** `http://localhost:5000/docs` (when server is running)
- **User Guide:** `docs/production/USER_GUIDE.md`
- **Tool List:** See "Available Server Tools" section above

---

**Happy Agent Building!** 🤖
