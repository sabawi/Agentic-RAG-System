"""
Configuration for Social Media Tracker Agent

Customize these settings for your environment.
"""

# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Agent Configuration
DEFAULT_BRANDS = ["Apple", "Google", "Microsoft"]
DEFAULT_TOPICS = ["AI", "Technology", "Innovation"]

# Output Configuration
OUTPUT_DIR = "social_reports"
LOG_FILE = "social_media_tracker.log"

# Retry Configuration
MAX_RETRIES = 3

# LLM Configuration
TEMPERATURE = 0.4  # Balanced for analysis and creativity
MAX_TOKENS = 4096

# Schedule Configuration
DAILY_RUN_TIME = "12:00"   # 12:00 PM (midday check)
WEEKLY_RUN_TIME = "14:00"  # 2:00 PM on Mondays
