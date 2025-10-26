#!/usr/bin/env python3
"""
Agent Template for Agentic-RAG Server
=====================================

Copy this template to create new agents that interact with the Agentic-RAG server.

Instructions:
1. Copy this file: cp agent_template.py my_new_agent.py
2. Replace "AGENT_NAME" with your agent's name
3. Implement the agent_task() method with your logic
4. Add any additional methods you need
5. Update the argument parser for your specific needs
6. Test with --test mode before deploying

Author: Your Name
Version: 1.0.0
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
        logging.FileHandler('agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MyAgent:
    """
    [AGENT_NAME] - Brief description of what this agent does.

    Replace this with your agent's description.
    """

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        output_dir: str = "output",
        max_retries: int = 3
    ):
        """
        Initialize the agent.

        Args:
            server_url: URL of the Agentic-RAG server
            output_dir: Directory to save output files
            max_retries: Maximum number of retry attempts on failure
        """
        self.server_url = server_url
        self.output_dir = Path(output_dir)
        self.max_retries = max_retries

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)

        # Initialize OpenAI client
        self.client = openai.OpenAI(
            base_url=server_url,
            api_key="not-required"
        )

        logger.info(f"MyAgent initialized with server: {server_url}")

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

    def execute_with_retry(self, prompt: str) -> Optional[str]:
        """
        Execute a prompt with retry logic and exponential backoff.

        Args:
            prompt: The prompt to send to the server

        Returns:
            Response content as string or None if all retries failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Executing task (attempt {attempt}/{self.max_retries})...")

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=4096
                )

                content = response.choices[0].message.content

                if not content:
                    raise ValueError("Response content is empty")

                logger.info(f"✅ Task completed successfully ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return None

    def save_output(self, content: str, filename: Optional[str] = None) -> Path:
        """
        Save output content to a file.

        Args:
            content: Content to save
            filename: Optional custom filename (default: timestamped)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output_{timestamp}.txt"

        filepath = self.output_dir / filename

        try:
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"✅ Saved output to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ Failed to save file: {e}")
            raise

    def agent_task(self) -> bool:
        """
        Main agent task logic.

        REPLACE THIS METHOD with your agent's specific functionality.

        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("Starting agent task...")
        logger.info("=" * 60)

        # Example: Fetch some information from the server
        prompt = """
        [REPLACE WITH YOUR PROMPT]

        Example prompts:
        - "Get me the latest financial news about Tesla"
        - "Search for research papers on quantum computing published this year"
        - "Summarize my unread emails from the last 24 hours"
        - "Create a visualization of Bitcoin price over the last 30 days"
        """

        # Execute with retry
        result = self.execute_with_retry(prompt)

        if not result:
            logger.error("Failed to complete task")
            return False

        # Save output
        try:
            self.save_output(result)
        except Exception as e:
            logger.error(f"Failed to save output: {e}")
            return False

        logger.info("=" * 60)
        logger.info("✅ Agent task completed successfully")
        logger.info("=" * 60)
        return True

    def run_once(self) -> bool:
        """
        Run the agent task once.

        Returns:
            True if successful
        """
        return self.agent_task()

    def run_scheduled(self, interval_minutes: int = 60):
        """
        Run the agent task on a schedule.

        Args:
            interval_minutes: Minutes between each run
        """
        logger.info(f"Starting scheduled mode (every {interval_minutes} minute(s))")

        # Define the job
        def job():
            self.agent_task()

        # Schedule the job
        if interval_minutes >= 60:
            hours = interval_minutes // 60
            schedule.every(hours).hours.do(job)
        else:
            schedule.every(interval_minutes).minutes.do(job)

        # Run immediately on start
        logger.info("Running initial task...")
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
        description="[AGENT_NAME] for Agentic-RAG Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once
  %(prog)s --once

  # Run every 30 minutes (scheduled mode)
  %(prog)s --schedule --interval 30

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
        '--output-dir',
        default='output',
        help='Output directory for files (default: output)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Minutes between scheduled runs (default: 60)'
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
    agent = MyAgent(
        server_url=args.server,
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
            success = agent.run_once()
            sys.exit(0 if success else 1)

        elif args.schedule:
            # Scheduled mode
            agent.run_scheduled(interval_minutes=args.interval)

    except KeyboardInterrupt:
        logger.info("\n👋 Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
