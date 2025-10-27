"""
Configuration for Market Sentiment Agent

Customize these settings for your environment.
"""

# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Agent Configuration
DEFAULT_SYMBOLS = ["AAPL", "TSLA", "NVDA"]
DEFAULT_SECTORS = ["technology", "finance"]

# Output Configuration
OUTPUT_DIR = "sentiment_reports"
LOG_FILE = "market_sentiment.log"

# Retry Configuration
MAX_RETRIES = 3

# LLM Configuration
TEMPERATURE = 0.4  # Slightly higher for analysis
MAX_TOKENS = 4096

# Schedule Configuration
DAILY_RUN_TIME = "09:00"   # 9:00 AM (after market open)
WEEKLY_RUN_TIME = "18:00"  # 6:00 PM on Fridays
