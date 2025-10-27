# Market Sentiment Analyzer Agent 📈

Monitor market sentiment from news and analyze trends for investment insights.

## Features

- 📰 **News Aggregation** - Collect financial news from multiple sources
- 📊 **Sentiment Analysis** - Analyze market sentiment and investor mood
- 📈 **Trend Identification** - Identify emerging market trends
- 💹 **Trading Signals** - Generate buy/sell recommendations
- 📉 **Risk Assessment** - Evaluate market risks and volatility
- 📧 **Investment Reports** - Send comprehensive market analysis via email
- 🔄 **Scheduled Execution** - Daily and weekly analysis modes

## Installation

### 1. Navigate to Agent Directory
```bash
cd agents/market_sentiment
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure (Optional)
Edit `config.py` to set default stocks and sectors.

## Usage

### Test Connection
```bash
./market_sentiment.py --test
```

### Daily Sentiment Analysis
```bash
# Analyze specific stocks
./market_sentiment.py --daily --symbols AAPL TSLA NVDA

# With email notification
./market_sentiment.py --daily --symbols AAPL TSLA --email trader@example.com
```

### Weekly Sector Analysis
```bash
./market_sentiment.py --weekly --sectors technology healthcare finance --email investor@example.com
```

### Combined Stocks and Sectors
```bash
./market_sentiment.py --daily --symbols AAPL MSFT --sectors technology --email analyst@example.com
```

### Scheduled Daily Reports
```bash
# Run daily at 9:00 AM (after market open)
./market_sentiment.py --schedule-daily --symbols NVDA TSLA AMD --email investor@example.com
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--test` | Test server connection |
| `--daily` | Generate daily sentiment analysis |
| `--weekly` | Generate weekly trend report |
| `--schedule-daily` | Schedule daily analysis at 9:00 AM |
| `--symbols` | Stock symbols to analyze (e.g., AAPL TSLA) |
| `--sectors` | Sectors to analyze (e.g., technology healthcare) |
| `--email` | Recipient email for reports |
| `--server` | Server URL (default: from config.py) |
| `--output-dir` | Output directory (default: sentiment_reports) |
| `--verbose` | Enable verbose logging |

## Output

Reports are saved in `sentiment_reports/` directory:
- `sentiment_daily_report_YYYYMMDD_HHMMSS.html` - Daily analysis
- `sentiment_weekly_report_YYYYMMDD_HHMMSS.html` - Weekly trends

## Configuration

Edit `config.py`:

```python
# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Default Watchlist
DEFAULT_SYMBOLS = ["AAPL", "TSLA", "NVDA"]
DEFAULT_SECTORS = ["technology", "finance"]

# Schedule
DAILY_RUN_TIME = "09:00"   # 9:00 AM (after market open)
WEEKLY_RUN_TIME = "18:00"  # 6:00 PM on Fridays
```

## Server Tools Used

- `get_news_summaries` - Get financial news
- `comprehensive_stock_analyzer` - Stock analysis
- `search_web` - Additional market sources
- `analytical_visualizer` - Create charts
- `secure_email_sender` - Send reports

## Troubleshooting

### Invalid Stock Symbol
Ensure stock symbols are valid ticker symbols (e.g., AAPL not Apple).

### No News Found
Some symbols or sectors may have limited news coverage. Try broader searches.

## Examples

### Tech Stock Daily Watch
```bash
./market_sentiment.py --daily --symbols AAPL MSFT GOOGL AMZN --email portfolio@example.com
```

### Weekly Healthcare Sector Analysis
```bash
./market_sentiment.py --weekly --sectors healthcare biotech pharma --email analyst@fund.com
```

### Automated Trading Signals
```bash
nohup ./market_sentiment.py --schedule-daily --symbols TSLA NVDA AMD --email trader@example.com &
```

## Logs

Monitor activity:
```bash
tail -f market_sentiment.log
```

## Version

Version: 1.0.0
