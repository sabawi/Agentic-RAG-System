# Business Intelligence Automation Agent

Automated business intelligence and strategic decision support agent that leverages the Agentic-RAG server's comprehensive capabilities.

## 🚀 Features

- **Comprehensive Market Research**: Across multiple sources using news, web search, and academic papers
- **Financial Analysis**: Company financials, ratios, performance trends, and valuations
- **Competitor Analysis**: Market positioning, performance comparison, and strategic initiatives
- **Document Analysis**: Company reports, whitepapers, and strategic documents
- **Data Visualization**: Charts and visualizations of market trends and financial data
- **Strategic Recommendations**: Actionable insights based on all gathered intelligence
- **Executive Dashboard**: Comprehensive business intelligence dashboard
- **Automated Reporting**: HTML/PDF reports with email delivery

## 🎯 Purpose

This agent automates the complete business intelligence workflow that typically requires hours of manual research by analysts. It combines market research, financial analysis, competitor intelligence, document analysis, and visualization into a single automated workflow.

## 🛠️ Capabilities

The agent leverages these Agentic-RAG server tools:
- `get_news_summaries` - Latest news and market updates
- `search_web` - Comprehensive web research
- `published_papers_search` - Academic research
- `comprehensive_stock_analyzer` - Financial analysis
- `get_stock_and_company_data` - Company financials
- `document_search` - Document analysis and insight extraction
- `analytical_visualizer` - Data visualization and charts
- `secure_email_sender` - Report delivery

## 📋 Usage

### Prerequisites
- Agentic-RAG server running on `http://localhost:5000`
- Required environment variables configured (API keys, email settings)

### Quick Start

**Test the connection:**
```bash
./business_intelligence.py --test
```

**Run strategic analysis for a company:**
```bash
./business_intelligence.py --strategic --company "Tesla" --competitors "Ford" "GM" "Nio" --sectors "electric vehicles" "renewable energy"
```

**Comprehensive analysis with documents and email:**
```bash
./business_intelligence.py --strategic --company "Apple" --topics "iPhone" "AI" --docs /path/to/quarterly_report.pdf --email analyst@example.com
```

**Schedule weekly analysis:**
```bash
./business_intelligence.py --schedule-weekly --company "Microsoft" --competitors "Google" "Amazon" --email executive@example.com
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--test` | Test server connection |
| `--strategic` | Run comprehensive strategic analysis |
| `--schedule-weekly` | Schedule weekly analysis |
| `--company COMPANY` | Target company to analyze |
| `--competitors COMP [COMP ...]` | Competitor companies |
| `--sectors SECTOR [SECTOR ...]` | Industry sectors to monitor |
| `--topics TOPIC [TOPIC ...]` | Research topics |
| `--docs DOC [DOC ...]` | Company document paths to analyze |
| `--email EMAIL` | Recipient email for reports |
| `--output-dir DIR` | Output directory for reports |
| `--server SERVER` | Server URL (default: http://localhost:5000/v1) |
| `--verbose` | Verbose logging |

## 📊 Output

The agent generates comprehensive business intelligence reports including:
- Market research and trend analysis
- Financial performance and valuation
- Competitor positioning and analysis
- Document insights and strategic implications
- Strategic recommendations with implementation roadmaps
- Executive dashboard with KPIs

All reports are generated in HTML format with professional styling and can be delivered via email.

## ⏰ Scheduling

The agent can be scheduled to run weekly analysis every Monday at 9:00 AM, providing regular business intelligence updates for ongoing strategic decision making.

## 🔒 Security

- Uses the server's secure email sender for report delivery
- Handles sensitive document analysis with proper access controls
- All API calls go through the Agentic-RAG server
- No local storage of sensitive data beyond the configured output directory

## 📁 Directory Structure

```
business_intelligence/
├── business_intelligence.py    # Main agent script
├── config.py                   # Configuration settings
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── business_reports/          # Default output directory
```

## 📈 Business Value

This agent transforms a complex, time-intensive business intelligence process into an automated workflow, providing:
- **Time Savings**: Reduces hours of manual research to minutes of automated processing
- **Comprehensive Coverage**: Analyzes multiple data sources that manual research might miss
- **Consistency**: Standardized analysis methodology across reports
- **Strategic Insights**: Data-driven recommendations for decision making
- **Regular Monitoring**: Scheduled analysis for ongoing market awareness
- **Executive Ready**: Professional reports suitable for leadership presentation

## 🔍 Troubleshooting

### Common Issues

**Issue: ModuleNotFoundError: No module named 'openai'**
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Or install from project root
cd /path/to/flaskserver
pip install -r requirements.txt
```

**Issue: Server connection failed**
```bash
# Solution: Check if server is running
curl http://localhost:5000/health

# Restart server if needed
cd /path/to/flaskserver
./stop_complete.sh && ./start_complete.sh
```

**Issue: Document not found errors**
```bash
# Solution: Use absolute paths for documents
./business_intelligence.py --strategic --company "Apple" \
  --docs /absolute/path/to/quarterly_report.pdf
```

**Issue: No email received**
```bash
# Solution: Verify email configuration in server's .env file
# Check SMTP settings, email addresses, and credentials
# Review business_intelligence.log for email sending errors
```

**Issue: Permission denied when running script**
```bash
# Solution: Make script executable
chmod +x business_intelligence.py
```

### Verbose Logging

For detailed troubleshooting, enable verbose logging:
```bash
./business_intelligence.py --strategic --company "Tesla" --verbose
```

### Log Files

Check the log file for detailed execution information:
```bash
tail -f business_intelligence.log
```

## ✨ Version History

### v1.0.3 (2025-10-27) - Complete HTML Formatting Fix
- 🐛 **CRITICAL FIX:** Complete solution for HTML formatting issues
  - Added `clean_html_response()` post-processing function
  - Strips markdown code blocks (` ```html`) from all responses
  - Extracts content fragments from standalone HTML documents
  - Removes `<!DOCTYPE>`, `<html>`, `<head>`, `<body>` wrapper tags
  - Applied to all 6 analysis components (market, financial, documents, competitors, dashboard, strategy)
  - Handles server-generated visualizations that may include code blocks
- ✅ Reports now render perfectly in all sections

### v1.0.2 (2025-10-27) - Enhanced Prompt Requirements
- 🔧 **IMPROVEMENT:** Enhanced all 6 prompts with critical formatting requirements
  - Explicit instructions to generate HTML content fragments only
  - Clear prohibition of markdown syntax and code blocks
  - Prevents LLM from generating standalone HTML documents
- ✅ Improved prompt clarity and specificity

### v1.0.1 (2025-10-27) - Initial HTML Formatting Fix
- 🐛 **FIX:** First attempt at HTML report formatting issue
  - LLM was generating Markdown instead of HTML
  - Updated all 6 prompts to explicitly request HTML-formatted output
- ✅ Added document path validation to prevent errors on missing files
- ✅ Added progress indicators showing Step X/6 for better tracking
- ✅ Enhanced error messages with emoji indicators (✅ ❌ ⚠️)
- ✅ Improved logging output for easier troubleshooting

### v1.0.0 (2025-10-27) - Initial Release
- ✅ Comprehensive 6-step business intelligence pipeline
- ✅ Multi-source data gathering (news, web, papers, financials)
- ✅ Professional HTML report generation
- ✅ Graceful degradation for optional steps
- ✅ Extensive documentation and testing
- ✅ Added comprehensive REVIEW_REPORT.md with detailed analysis
- ✅ Added TEST_REPORT.md with real company test results

## 🎓 How It Works

The Business Intelligence Agent executes a 6-step analysis pipeline:

1. **Market Research** (Step 1/6) - Gathers news, web data, and academic papers
2. **Financial Analysis** (Step 2/6) - Analyzes company financials and stock performance
3. **Document Analysis** (Step 3/6) - Interrogates company documents for insights
4. **Competitor Analysis** (Step 4/6) - Compares competitors and market positioning
5. **Dashboard Creation** (Step 5/6) - Generates KPI dashboard with metrics
6. **Strategy Recommendations** (Step 6/6) - Creates actionable strategic guidance

Each step can succeed or fail independently (graceful degradation), ensuring the analysis continues even if optional components fail.

## 💡 Tips for Best Results

1. **Be Specific**: Provide specific company names and competitor lists for focused analysis
2. **Use Real Documents**: Provide actual company documents (PDFs, reports) for deeper insights
3. **Monitor Logs**: Watch the log output to understand what the agent is analyzing
4. **Review First**: Review the generated report before sharing with stakeholders
5. **Schedule Wisely**: Use weekly scheduling for ongoing monitoring, not daily (reduces API usage)