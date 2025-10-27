"""
Configuration for Stock Monitor Agent

Customize these settings for your environment.
"""

# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Agent Configuration
DEFAULT_PORTFOLIO = {
    "AAPL": 10,   # 10 shares
    "TSLA": 5,    # 5 shares
    "NVDA": 15    # 15 shares
}

# Alert Configuration
PRICE_CHANGE_THRESHOLD = 5.0  # Alert on 5% price change
VOLUME_THRESHOLD = 1.5        # Alert on 150% normal volume

# Output Configuration
OUTPUT_DIR = "stock_reports"
LOG_FILE = "stock_monitor.log"

# Retry Configuration
MAX_RETRIES = 3

# LLM Configuration
TEMPERATURE = 0.3  # Low temperature for factual content
MAX_TOKENS = 4096

# Schedule Configuration
MARKET_OPEN_TIME = "09:30"   # 9:30 AM (market open)
MARKET_CLOSE_TIME = "16:00"  # 4:00 PM (market close)
DAILY_RUN_TIME = "09:35"     # 9:35 AM (5 min after open)
