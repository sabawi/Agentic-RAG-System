# Stock Monitor Agent 💹

Real-time stock portfolio monitoring with alerts and analysis.

## Features

- 📊 **Portfolio Tracking** - Monitor stock portfolio performance
- 🔔 **Price Alerts** - Alert on significant price changes
- 📈 **Performance Analysis** - Daily, weekly, and monthly reports
- 📰 **News Integration** - Related news for portfolio stocks
- 💹 **Risk Assessment** - Evaluate portfolio risk and diversification
- 📧 **Email Reports** - Comprehensive portfolio reports via email
- 🔄 **Scheduled Monitoring** - Automated market-hours tracking

## Installation

### 1. Navigate to Agent Directory
```bash
cd agents/stock_monitor
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Portfolio
Edit `config.py` to set your portfolio holdings.

## Usage

### Test Connection
```bash
./stock_monitor.py --test
```

### Daily Portfolio Check
```bash
# Quick daily analysis
./stock_monitor.py --daily --symbols AAPL TSLA NVDA

# With email notification
./stock_monitor.py --daily --symbols AAPL TSLA NVDA --email investor@example.com
```

### Weekly Performance Report
```bash
./stock_monitor.py --weekly --symbols AAPL MSFT GOOGL --email portfolio@example.com
```

### Scheduled Market Monitoring
```bash
# Run at market open (9:35 AM)
./stock_monitor.py --schedule --symbols AAPL TSLA NVDA AMD --email trader@example.com
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--test` | Test server connection |
| `--daily` | Generate daily portfolio analysis |
| `--weekly` | Generate weekly performance report |
| `--schedule` | Schedule monitoring at market open |
| `--symbols` | Stock symbols to monitor (required) |
| `--email` | Recipient email for reports |
| `--server` | Server URL (default: from config.py) |
| `--output-dir` | Output directory (default: stock_reports) |
| `--verbose` | Enable verbose logging |

## Output

Reports are saved in `stock_reports/` directory:
- `stock_daily_report_YYYYMMDD_HHMMSS.html` - Daily analysis
- `stock_weekly_report_YYYYMMDD_HHMMSS.html` - Weekly performance

## Configuration

Edit `config.py`:

```python
# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Portfolio
DEFAULT_PORTFOLIO = {
    "AAPL": 10,   # 10 shares
    "TSLA": 5,    # 5 shares
    "NVDA": 15    # 15 shares
}

# Alert Thresholds
PRICE_CHANGE_THRESHOLD = 5.0  # Alert on 5% price change
VOLUME_THRESHOLD = 1.5        # Alert on 150% normal volume

# Schedule
DAILY_RUN_TIME = "09:35"  # 9:35 AM (5 min after open)
```

## Server Tools Used

- `comprehensive_stock_analyzer` - Detailed stock analysis
- `get_stock_and_company_data` - Real-time stock data
- `get_news_summaries` - Related financial news
- `secure_email_sender` - Send reports

## Troubleshooting

### Invalid Stock Symbol
Verify ticker symbols are correct (e.g., AAPL not Apple).

### Market Hours
Stock data updates during market hours (9:30 AM - 4:00 PM ET).

### No Data Available
Some stocks may have delayed data or limited coverage.

## Examples

### Tech Portfolio Monitoring
```bash
./stock_monitor.py --daily --symbols AAPL MSFT GOOGL AMZN META --email tech-portfolio@example.com
```

### Weekly Growth Stock Review
```bash
./stock_monitor.py --weekly --symbols TSLA NVDA AMD PLTR --email growth-stocks@example.com
```

### Automated Morning Check
```bash
nohup ./stock_monitor.py --schedule --symbols AAPL TSLA NVDA MSFT --email alerts@example.com &
```

## Logs

View monitoring logs:
```bash
tail -f stock_monitor.log
```

## Version

Version: 1.0.0
