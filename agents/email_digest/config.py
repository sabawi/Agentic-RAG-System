"""
Configuration for Email Digest Agent

Customize these settings for your environment.
"""

# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Agent Configuration
DEFAULT_EMAIL_PROVIDER = "gmail_primary"
DEFAULT_HOURS_BACK = 24  # Hours to look back for emails

# Output Configuration
OUTPUT_DIR = "email_digests"
LOG_FILE = "email_digest.log"

# Retry Configuration
MAX_RETRIES = 3

# LLM Configuration
TEMPERATURE = 0.3  # Low temperature for factual content
MAX_TOKENS = 4096

# Schedule Configuration
MORNING_DIGEST_TIME = "08:00"  # 8:00 AM
DAILY_DIGEST_TIME = "17:00"    # 5:00 PM
