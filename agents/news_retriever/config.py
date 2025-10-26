import os

# Email recipient - MUST be configured in .env file
RECIPIENT_EMAIL = os.getenv("NEWS_RECIPIENT_EMAIL", "user@example.com")
SERVER_URL = os.getenv("NEWS_SERVER_URL", "http://localhost:5000/v1")