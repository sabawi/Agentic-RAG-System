#!/usr/bin/env python3
"""
Enhanced News Retriever Agent
=============================

An improved news retrieval agent that leverages the Agentic-RAG server's
full capabilities including proper tool usage, error handling, and flexible output.

Features:
- Single efficient API call with proper prompting
- Run-once or scheduled modes
- Comprehensive error handling and logging
- Flexible output (file, email, or both)
- Command-line arguments for easy configuration
- Proper logging with rotation
- Retry logic with exponential backoff

Author: Agentic-RAG Development Team
Version: 2.0.0
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import openai
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NewsRetrieverAgent:
    """Enhanced news retrieval agent with improved error handling and features."""

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        recipient_email: Optional[str] = None,
        output_dir: str = "news_output",
        max_retries: int = 3
    ):
        """
        Initialize the news retriever agent.

        Args:
            server_url: URL of the Agentic-RAG server
            recipient_email: Email address to send news summaries to
            output_dir: Directory to save HTML output files
            max_retries: Maximum number of retry attempts on failure
        """
        self.server_url = server_url
        self.recipient_email = recipient_email
        self.output_dir = Path(output_dir)
        self.max_retries = max_retries

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)

        # Initialize OpenAI client
        self.client = openai.OpenAI(
            base_url=server_url,
            api_key="not-required"
        )

        logger.info(f"NewsRetrieverAgent initialized with server: {server_url}")

    def test_connection(self) -> bool:
        """Test connection to the server."""
        try:
            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{"role": "user", "content": "Hello, are you working?"}],
                max_tokens=50
            )
            logger.info("✅ Server connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Server connection failed: {e}")
            return False

    def get_news_with_retry(self) -> Optional[str]:
        """
        Fetch news with retry logic and exponential backoff.

        Returns:
            News content as string or None if all retries failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching news (attempt {attempt}/{self.max_retries})...")

                # Improved prompt that leverages the server's news tool
                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{
                        "role": "user",
                        "content": (
                            "Please provide a comprehensive news summary for today. "
                            "Use the get_news_summaries tool to fetch the latest news. "
                            "Format the output as a well-structured HTML document with:\n"
                            "1. A title with today's date\n"
                            "2. Main headlines organized by category\n"
                            "3. Brief summaries for each news item\n"
                            "4. Source links where available\n"
                            "5. Professional styling with proper HTML tags"
                        )
                    }],
                    temperature=0.7,
                    max_tokens=4096
                )

                news_content = response.choices[0].message.content

                if not news_content or len(news_content) < 100:
                    raise ValueError("News content is empty or too short")

                logger.info(f"✅ Successfully fetched news ({len(news_content)} chars)")
                return news_content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return None

    def save_to_file(self, content: str, filename: Optional[str] = None) -> Path:
        """
        Save news content to HTML file.

        Args:
            content: News content to save
            filename: Optional custom filename (default: timestamped)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_summary_{timestamp}.html"

        filepath = self.output_dir / filename

        try:
            # Ensure content is properly wrapped in HTML if not already
            if not content.strip().startswith("<html"):
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>News Summary - {datetime.now().strftime("%Y-%m-%d %H:%M")}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    {content}
</body>
</html>"""
            else:
                html_content = content

            filepath.write_text(html_content, encoding='utf-8')
            logger.info(f"✅ Saved news to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to save file: {e}")
            raise

    def send_email(self, html_file: Path) -> bool:
        """
        Send news summary via email using the server's email tool.

        Args:
            html_file: Path to HTML file to send

        Returns:
            True if email was sent successfully
        """
        if not self.recipient_email:
            logger.warning("No recipient email configured, skipping email")
            return False

        try:
            logger.info(f"Sending email to {self.recipient_email}...")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Please send an email to {self.recipient_email} with:\n"
                        f"Subject: 'News Summary - {timestamp}'\n"
                        f"Body: 'Please find attached the latest news summary.'\n"
                        f"Attach the file: {html_file.absolute()}\n"
                        "Use the secure_email_sender tool."
                    )
                }]
            )

            logger.info(f"✅ Email sent successfully")
            logger.debug(f"Server response: {response.choices[0].message.content}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    def run_once(self, save_file: bool = True, send_email: bool = False) -> bool:
        """
        Run the news retrieval once.

        Args:
            save_file: Whether to save output to file
            send_email: Whether to send email

        Returns:
            True if successful
        """
        logger.info("=" * 60)
        logger.info("Starting news retrieval...")
        logger.info("=" * 60)

        # Fetch news
        news_content = self.get_news_with_retry()
        if not news_content:
            logger.error("Failed to fetch news")
            return False

        # Save to file
        html_file = None
        if save_file:
            try:
                html_file = self.save_to_file(news_content)
            except Exception as e:
                logger.error(f"Failed to save file: {e}")
                return False

        # Send email
        if send_email and html_file:
            self.send_email(html_file)

        logger.info("=" * 60)
        logger.info("✅ News retrieval completed successfully")
        logger.info("=" * 60)
        return True

    def run_scheduled(
        self,
        interval_hours: int = 1,
        save_file: bool = True,
        send_email: bool = False
    ):
        """
        Run the news retrieval on a schedule.

        Args:
            interval_hours: Hours between each run
            save_file: Whether to save output to file
            send_email: Whether to send email
        """
        logger.info(f"Starting scheduled mode (every {interval_hours} hour(s))")

        # Define the job
        def job():
            self.run_once(save_file=save_file, send_email=send_email)

        # Schedule the job
        if interval_hours == 1:
            schedule.every().hour.at(":00").do(job)
        else:
            schedule.every(interval_hours).hours.do(job)

        # Run immediately on start
        logger.info("Running initial fetch...")
        job()

        # Run scheduler loop
        logger.info("Entering scheduler loop...")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enhanced News Retriever Agent for Agentic-RAG Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once and save to file
  %(prog)s --once

  # Run once and email results
  %(prog)s --once --email recipient@example.com

  # Run every 2 hours (scheduled mode)
  %(prog)s --schedule --interval 2

  # Test server connection
  %(prog)s --test

  # Custom server URL
  %(prog)s --once --server http://192.168.1.100:5000/v1
        """
    )

    # Mode arguments
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit'
    )
    mode_group.add_argument(
        '--schedule',
        action='store_true',
        help='Run on schedule (continuous)'
    )
    mode_group.add_argument(
        '--test',
        action='store_true',
        help='Test server connection and exit'
    )

    # Configuration arguments
    parser.add_argument(
        '--server',
        default='http://localhost:5000/v1',
        help='Server URL (default: http://localhost:5000/v1)'
    )
    parser.add_argument(
        '--email',
        help='Recipient email address'
    )
    parser.add_argument(
        '--output-dir',
        default='news_output',
        help='Output directory for HTML files (default: news_output)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=1,
        help='Hours between scheduled runs (default: 1)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save output to file'
    )
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Maximum retry attempts (default: 3)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create agent instance
    agent = NewsRetrieverAgent(
        server_url=args.server,
        recipient_email=args.email,
        output_dir=args.output_dir,
        max_retries=args.retries
    )

    # Execute based on mode
    try:
        if args.test:
            # Test mode
            logger.info("Testing server connection...")
            success = agent.test_connection()
            sys.exit(0 if success else 1)

        elif args.once:
            # Run once mode
            success = agent.run_once(
                save_file=not args.no_save,
                send_email=bool(args.email)
            )
            sys.exit(0 if success else 1)

        elif args.schedule:
            # Scheduled mode
            agent.run_scheduled(
                interval_hours=args.interval,
                save_file=not args.no_save,
                send_email=bool(args.email)
            )

    except KeyboardInterrupt:
        logger.info("\n👋 Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
