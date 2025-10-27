# Intelligent Email Digest Agent 📧

Automated email summarization and priority management agent.

## Features

- 📨 **Multi-Provider Support** - Retrieve emails from Gmail, Outlook, and other providers
- 🎯 **Smart Prioritization** - Categorize emails by importance and urgency
- 📋 **Action Items** - Extract and highlight action items requiring attention
- 🧠 **Sentiment Analysis** - Analyze email tone and urgency
- 📊 **Pattern Recognition** - Identify communication patterns and trends
- 📧 **HTML Digests** - Professional formatted digest reports
- 🔄 **Scheduled Execution** - Morning and daily digest modes

## Installation

### 1. Navigate to Agent Directory
```bash
cd agents/email_digest
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure (Optional)
Edit `config.py` to customize email provider, schedule, etc.

## Usage

### Test Connection
```bash
./email_digest.py --test
```

### Morning Digest (Last 24 Hours)
```bash
# Run once
./email_digest.py --morning --provider gmail_primary

# With email notification
./email_digest.py --morning --provider gmail_primary --email user@example.com
```

### Daily Digest with Deep Analysis
```bash
./email_digest.py --daily --provider outlook_personal --email user@example.com
```

### Custom Time Range
```bash
# Last 12 hours
./email_digest.py --morning --provider gmail_primary --hours 12 --email user@example.com
```

### Scheduled Morning Digest
```bash
# Schedule daily at 8:00 AM
./email_digest.py --schedule-morning --provider gmail_primary --email user@example.com
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--test` | Test server connection |
| `--morning` | Generate morning digest (last 24 hours) |
| `--daily` | Generate daily analysis with patterns |
| `--schedule-morning` | Schedule morning digest at 8:00 AM |
| `--provider` | Email provider (default: gmail_primary) |
| `--hours` | Hours back to retrieve (default: 24) |
| `--email` | Recipient email for digests |
| `--server` | Server URL (default: from config.py) |
| `--output-dir` | Output directory (default: email_digests) |
| `--verbose` | Enable verbose logging |

## Output

Digests are saved in `email_digests/` directory:
- `email_morning_digest_YYYYMMDD_HHMMSS.html` - Morning digests
- `email_daily_digest_YYYYMMDD_HHMMSS.html` - Daily analysis

## Configuration

Edit `config.py`:

```python
# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Email Provider
DEFAULT_EMAIL_PROVIDER = "gmail_primary"
DEFAULT_HOURS_BACK = 24

# Schedule
MORNING_DIGEST_TIME = "08:00"  # 8:00 AM
DAILY_DIGEST_TIME = "17:00"    # 5:00 PM
```

## Server Tools Used

- `email_retriever` - Retrieve emails from multiple providers
- LLM analysis for sentiment and urgency classification
- `secure_email_sender` - Send digests

## Troubleshooting

### Email Provider Not Configured
Ensure the email provider is configured in the server's `.env` file.

### No Emails Retrieved
Check that:
- Provider name matches server configuration
- Time range is appropriate
- Server has access to email account

## Examples

### Morning Briefing
```bash
./email_digest.py --morning --provider gmail_primary --email me@example.com
```

### Daily Summary at 5 PM
```bash
./email_digest.py --schedule-daily --provider outlook_work --email me@example.com
```

## Logs

View activity in `email_digest.log`:
```bash
tail -f email_digest.log
```

## Version

Version: 1.0.0
