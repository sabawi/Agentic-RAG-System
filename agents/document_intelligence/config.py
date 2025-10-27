"""
Configuration for Document Intelligence Agent

Customize these settings for your environment.
"""

# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Agent Configuration
DEFAULT_DOCUMENT_DIRS = [
    "~/documents",
    "~/downloads"
]
WATCH_SUBDIRS = True

# Supported file types
SUPPORTED_EXTENSIONS = [
    ".pdf", ".doc", ".docx", ".txt",
    ".md", ".html", ".rtf"
]

# Output Configuration
OUTPUT_DIR = "document_reports"
LOG_FILE = "document_intelligence.log"

# Retry Configuration
MAX_RETRIES = 3

# LLM Configuration
TEMPERATURE = 0.3  # Low temperature for factual content
MAX_TOKENS = 4096

# Schedule Configuration
DAILY_SCAN_TIME = "10:00"   # 10:00 AM
WEEKLY_SCAN_TIME = "09:00"  # 9:00 AM on Mondays
