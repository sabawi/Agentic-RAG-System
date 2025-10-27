"""
Configuration for Research Assistant Agent

Customize these settings for your environment.
"""

# Server Configuration
SERVER_URL = "http://localhost:5000/v1"

# Agent Configuration
DEFAULT_TOPICS = [
    "machine learning",
    "artificial intelligence"
]

# Output Configuration
OUTPUT_DIR = "research_output"
LOG_FILE = "research_assistant.log"

# Retry Configuration
MAX_RETRIES = 3

# LLM Configuration
TEMPERATURE = 0.3  # Low temperature for factual content
MAX_TOKENS = 4096

# Schedule Configuration
DAILY_RUN_TIME = "08:00"  # 8:00 AM
