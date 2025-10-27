# Document Intelligence Agent 📄

Automated document processing and insight extraction agent.

## Features

- 📁 **Directory Monitoring** - Watch multiple document folders for new files
- 🔍 **Smart Extraction** - Extract key information using document interrogation
- 📝 **Executive Summaries** - Create concise summaries of documents
- 🔗 **Relationship Analysis** - Find related documents and connections
- 📊 **Insight Generation** - Extract actionable insights from documents
- 📧 **Report Delivery** - Send document intelligence reports via email
- 🔄 **Scheduled Scanning** - Daily and weekly scan modes

## Installation

### 1. Navigate to Agent Directory
```bash
cd agents/document_intelligence
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure (Optional)
Edit `config.py` to set monitored directories and file types.

## Usage

### Test Connection
```bash
./document_intelligence.py --test
```

### Daily Document Scan
```bash
# Scan specific directories
./document_intelligence.py --daily --dirs ~/documents ~/downloads

# With email notification
./document_intelligence.py --daily --dirs ~/contracts ~/reports --email manager@example.com
```

### Weekly Analysis
```bash
# Comprehensive weekly analysis with relationship mapping
./document_intelligence.py --weekly --dirs ~/documents --email team@example.com
```

### Scheduled Daily Scans
```bash
# Scan daily at 10:00 AM
./document_intelligence.py --schedule-daily --dirs ~/documents ~/dropbox/contracts --email user@example.com
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--test` | Test server connection |
| `--daily` | Generate daily document scan |
| `--weekly` | Generate weekly analysis |
| `--schedule-daily` | Schedule daily scans at 10:00 AM |
| `--dirs` | Directories to monitor (required) |
| `--email` | Recipient email for reports |
| `--server` | Server URL (default: from config.py) |
| `--output-dir` | Output directory (default: document_reports) |
| `--verbose` | Enable verbose logging |

## Output

Reports are saved in `document_reports/` directory:
- `document_daily_scan_YYYYMMDD_HHMMSS.html` - Daily scans
- `document_weekly_analysis_YYYYMMDD_HHMMSS.html` - Weekly analysis

## Supported File Types

- PDF (.pdf)
- Word Documents (.doc, .docx)
- Text Files (.txt, .md)
- HTML Files (.html)
- Rich Text (.rtf)

Configure additional types in `config.py`.

## Configuration

Edit `config.py`:

```python
# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Monitored Directories
DEFAULT_DOCUMENT_DIRS = [
    "~/documents",
    "~/downloads"
]

# Supported file types
SUPPORTED_EXTENSIONS = [
    ".pdf", ".doc", ".docx", ".txt",
    ".md", ".html", ".rtf"
]

# Schedule
DAILY_SCAN_TIME = "10:00"   # 10:00 AM
WEEKLY_SCAN_TIME = "09:00"  # 9:00 AM on Mondays
```

## Server Tools Used

- `document_search` - Analyze documents in monitored directories
- LLM for content analysis and summarization
- `secure_email_sender` - Send reports

## Troubleshooting

### Directory Not Found
Ensure directories exist and use absolute paths:
```bash
./document_intelligence.py --daily --dirs /home/user/documents /home/user/reports
```

### No Documents Found
Check:
- Directory contains supported file types
- Subdirectory scanning is enabled (default)
- File permissions allow reading

### Document Processing Errors
Some files may be corrupted or protected. Check logs for specific errors.

## Examples

### Monitor Contract Folder
```bash
./document_intelligence.py --daily --dirs ~/contracts ~/legal --email legal@company.com
```

### Weekly Research Paper Analysis
```bash
./document_intelligence.py --weekly --dirs ~/research/papers --email professor@university.edu
```

### Automated Document Processing
```bash
nohup ./document_intelligence.py --schedule-daily --dirs ~/dropbox/incoming ~/documents --email archive@example.com &
```

## Logs

View processing logs:
```bash
tail -f document_intelligence.log
```

## Version

Version: 1.0.0
