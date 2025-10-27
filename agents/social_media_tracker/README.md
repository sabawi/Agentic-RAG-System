# Social Media Trend Tracker Agent 📱

Monitor and analyze social media trends and brand mentions.

## Features

- 🔍 **Brand Monitoring** - Track brand mentions across social media
- 📊 **Sentiment Analysis** - Analyze public sentiment toward brands/topics
- 🔥 **Viral Content** - Identify trending and viral content
- 🏆 **Competitor Analysis** - Monitor competitor social media activity
- 📈 **Trend Identification** - Spot emerging trends early
- 📧 **Social Reports** - Comprehensive social media analysis reports
- 🔄 **Scheduled Tracking** - Daily and weekly monitoring modes

## Installation

### 1. Navigate to Agent Directory
```bash
cd agents/social_media_tracker
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure (Optional)
Edit `config.py` to set default brands and topics.

## Usage

### Test Connection
```bash
./social_media_tracker.py --test
```

### Daily Brand Tracking
```bash
# Track specific brands
./social_media_tracker.py --daily --brands "Nike" "Adidas" "Puma"

# With email notification
./social_media_tracker.py --daily --brands "Apple" "Samsung" --email marketing@example.com
```

### Topic Trend Analysis
```bash
# Track topics and hashtags
./social_media_tracker.py --daily --topics "AI" "MachineLearning" "DeepLearning" --email analyst@example.com
```

### Combined Brand and Topic Tracking
```bash
./social_media_tracker.py --weekly --brands "Tesla" --topics "ElectricVehicles" "CleanEnergy" --email social@example.com
```

### Scheduled Daily Tracking
```bash
# Run daily at noon
./social_media_tracker.py --schedule-daily --brands "Microsoft" "Google" "Amazon" --email social-media@example.com
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--test` | Test server connection |
| `--daily` | Generate daily tracking report |
| `--weekly` | Generate weekly trend analysis |
| `--schedule-daily` | Schedule daily tracking at 12:00 PM |
| `--brands` | Brands to monitor |
| `--topics` | Topics/hashtags to track |
| `--email` | Recipient email for reports |
| `--server` | Server URL (default: from config.py) |
| `--output-dir` | Output directory (default: social_reports) |
| `--verbose` | Enable verbose logging |

## Output

Reports are saved in `social_reports/` directory:
- `social_daily_report_YYYYMMDD_HHMMSS.html` - Daily tracking
- `social_weekly_report_YYYYMMDD_HHMMSS.html` - Weekly analysis

## Configuration

Edit `config.py`:

```python
# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Default Monitoring
DEFAULT_BRANDS = ["Apple", "Google", "Microsoft"]
DEFAULT_TOPICS = ["AI", "Technology", "Innovation"]

# Schedule
DAILY_RUN_TIME = "12:00"   # 12:00 PM (midday check)
WEEKLY_RUN_TIME = "14:00"  # 2:00 PM on Mondays
```

## Server Tools Used

- `search_web` - Find social media mentions and discussions
- `get_news_summaries` - News about brands/topics
- `analytical_visualizer` - Create trend charts
- `secure_email_sender` - Send reports

## Troubleshooting

### Limited Social Media Access
The agent uses web search to find social media content. Results depend on publicly available information.

### Brand Name Ambiguity
Use specific brand names to avoid confusion (e.g., "Apple Inc" instead of "Apple").

## Examples

### Monitor Tech Brands
```bash
./social_media_tracker.py --daily --brands "Apple" "Google" "Microsoft" "Amazon" --email marketing@tech.com
```

### Track AI Trends
```bash
./social_media_tracker.py --weekly --topics "ArtificialIntelligence" "ChatGPT" "LLM" --email research@ai-lab.org
```

### Competitor Analysis
```bash
./social_media_tracker.py --daily --brands "Nike" "Adidas" "UnderArmour" "Puma" --email competitor-intel@sportswear.com
```

### Automated Brand Monitoring
```bash
nohup ./social_media_tracker.py --schedule-daily --brands "YourBrand" "Competitor1" "Competitor2" --email social@yourcompany.com &
```

## Logs

Monitor tracking activity:
```bash
tail -f social_media_tracker.log
```

## Version

Version: 1.0.0
