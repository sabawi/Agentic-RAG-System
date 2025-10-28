"""
Configuration for Business Intelligence Agent

Customize these settings for your environment.
"""

# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Agent Configuration
DEFAULT_COMPANY = "Apple"
DEFAULT_COMPETITORS = [
    "Microsoft",
    "Google",
    "Amazon"
]
DEFAULT_SECTORS = [
    "Technology",
    "Consumer Electronics"
]

# Output Configuration
OUTPUT_DIR = "business_reports"
LOG_FILE = "business_intelligence.log"

# Retry Configuration
MAX_RETRIES = 3

# LLM Configuration
TEMPERATURE = 0.5  # Balanced for business analysis
MAX_TOKENS = 4096

# Schedule Configuration
WEEKLY_RUN_DAY = "monday"
WEEKLY_RUN_TIME = "09:00"  # 9:00 AM