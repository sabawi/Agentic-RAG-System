#!/usr/bin/env python3
"""
Intelligent Email Digest Agent
=============================

Automated email summarization and priority management agent.

Features:
- Generate morning email summaries from multiple providers
- Extract action items and categorize by importance
- Analyze email sentiment and urgency
- Send HTML-formatted digest reports
- Track email patterns and trends

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import json

import openai
import schedule

# Import central HTML generator (NO WHEEL REINVENTING!)
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.html_generator import HTMLReportGenerator

# Import shared email utility
# Add agents directory to path to allow importing from common
agents_dir = Path(__file__).parent.parent
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from common.report_utils import send_email_report



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_digest.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EmailDigestAgent:
    """Intelligent email summarization and priority management agent."""

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        email_provider: str = "gmail_primary",
        hours_back: int = 24,
        recipient_email: Optional[str] = None,
        output_dir: str = "email_digests",
        max_retries: int = 3
    ):
        """
        Initialize the email digest agent.

        Args:
            server_url: URL of the Agentic-RAG server
            email_provider: Email provider to retrieve from (e.g., gmail_primary)
            hours_back: Number of hours to look back for emails
            recipient_email: Email for digest reports
            output_dir: Directory to save digest reports
            max_retries: Maximum retry attempts on failure
        """
        self.server_url = server_url
        self.email_provider = email_provider
        self.hours_back = hours_back
        self.recipient_email = recipient_email
        self.output_dir = Path(output_dir)
        self.max_retries = max_retries

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

        # Initialize OpenAI client
        self.client = openai.OpenAI(
            base_url=server_url,
            api_key="not-required"
        )

        # Initialize central HTML generator
        self.html_generator = HTMLReportGenerator()

        logger.info(f"EmailDigestAgent initialized for provider: {email_provider}, last {hours_back} hours")

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

    def retrieve_emails_with_retry(self) -> Optional[str]:
        """
        Retrieve emails with retry logic.

        Returns:
            Email content as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Retrieving emails from {self.email_provider} (attempt {attempt}/{self.max_retries})...")

                # Calculate the date range
                start_date = (datetime.now() - timedelta(hours=self.hours_back)).strftime("%Y-%m-%d")
                
                prompt = f"""
Please retrieve recent emails from my account for the last {self.hours_back} hours.

Use the email_retriever tool to get emails. Then provide:

1. List of all emails with:
   - Sender, subject, timestamp
   - Brief preview/content
   - Importance classification (High/Medium/Low)
   - Urgency level (Critical/High/Medium/Low)

2. Identify any action items requiring immediate attention
3. Group emails by sender or topic
4. Highlight any recurring themes or patterns
5. Flag any missed follow-ups from previous emails

Format as Markdown with:
- Clear headings (## for sections, ### for subsections)
- Priority indicators (🔴 High, 🟡 Medium, 🟢 Low)
- Bullet lists for items
- **Bold** for important information
- Links where applicable
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Low temperature for factual content
                    max_tokens=4096
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Email content is empty or too short")

                logger.info(f"✅ Retrieved emails successfully ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return None

    def analyze_email_sentiment_with_retry(self, email_content: str) -> Optional[str]:
        """
        Analyze sentiment of email content.

        Args:
            email_content: Email content to analyze

        Returns:
            Sentiment analysis as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing email sentiment (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Analyze the sentiment and tone of the following email content:

{email_content}

Provide:
1. Overall sentiment (Positive/Neutral/Negative)
2. Emotional tone (Professional/Aggressive/Friendly/Urgent/etc.)
3. Sender attitude towards recipient
4. Urgency level
5. Potential concerns or conflicts
6. Recommended response approach

Format as a structured analysis report.
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,  # Slightly higher for analysis
                    max_tokens=2048
                )

                content = response.choices[0].message.content

                if not content or len(content) < 50:
                    raise ValueError("Sentiment analysis content is empty or too short")

                logger.info(f"✅ Sentiment analysis completed ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return None

    def extract_action_items_with_retry(self, email_content: str) -> Optional[str]:
        """
        Extract action items from email content.

        Args:
            email_content: Email content to analyze

        Returns:
            Action items as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Extracting action items (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Identify and extract all action items from the following email content:

{email_content}

Extract and organize action items that require:
1. Immediate attention (within 24 hours)
2. Short-term completion (within 1 week)
3. Long-term follow-up (within 1 month)

For each action item, provide:
- Description of the task
- Responsible party (if mentioned)
- Deadline or time sensitivity
- Related email/subject
- Priority level (High/Medium/Low)
- Additional context needed

Format as a prioritized action item list with:
- Clear checkboxes for tracking
- Due date indicators
- Context links to original emails
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Low temperature for accuracy
                    max_tokens=2048
                )

                content = response.choices[0].message.content

                if not content or len(content) < 50:
                    raise ValueError("Action items content is empty or too short")

                logger.info(f"✅ Action items extracted ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return None

    def save_email_digest(self, content: str, digest_type: str) -> Path:
        """
        Save email digest to HTML file using central HTML generator.

        Args:
            content: Digest content (Markdown or plain text)
            digest_type: Type of digest ('morning', 'daily', 'weekly')

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_{digest_type}_digest_{timestamp}.html"
        filepath = self.output_dir / filename

        try:
            # Use central HTML generator to convert Markdown to HTML
            html_content = self.html_generator.generate_html_report(
                content=content,
                title=f"Email {digest_type.title()} Digest - {datetime.now().strftime('%Y-%m-%d')}",
                header_title=f"📧 Email {digest_type.title()} Digest",
                header_subtitle=f"Summary from {self.email_provider} for the last {self.hours_back} hours",
                include_disclaimer=False  # No disclaimer needed for email digest
            )

            filepath.write_text(html_content, encoding='utf-8')
            logger.info(f"✅ Saved email digest to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to save email digest: {e}")
            raise


    def run_morning_digest(self, send_email: bool = False) -> bool:
        """Generate morning email digest."""
        logger.info("=" * 60)
        logger.info("Starting morning email digest...")
        logger.info("=" * 60)

        # Retrieve emails
        email_content = self.retrieve_emails_with_retry()
        if not email_content:
            logger.error("Failed to retrieve emails")
            return False

        # Extract action items
        action_items = self.extract_action_items_with_retry(email_content)
        if not action_items:
            logger.warning("Failed to extract action items")
            action_items = "No action items could be extracted."

        # Analyze sentiment
        sentiment_analysis = self.analyze_email_sentiment_with_retry(email_content)
        if not sentiment_analysis:
            logger.warning("Failed to analyze email sentiment")
            sentiment_analysis = "No sentiment analysis available."

        # Combine into digest (Markdown format - HTML generator will convert)
        digest_content = f"""
## 🔥 Critical Action Items

These require immediate attention:

{action_items}

---

## 📧 Email Summary

{email_content}

---

## 🧠 Sentiment Analysis

{sentiment_analysis}

---

### Quick Stats

- **Email Provider:** {self.email_provider}
- **Time Range:** Last {self.hours_back} hours
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        filepath = self.save_email_digest(digest_content, "morning")

        if send_email:
            subject = f"🌅 Morning Email Digest - {datetime.now().strftime('%A, %B %d')}"
            send_email_report(
                client=self.client,
                recipient_email=self.recipient_email,
                subject=subject,
                body="Please find attached your personalized email digest with summaries and action items.",
                attachment_path=filepath,
                logger=logger
            )

        logger.info("✅ Morning email digest completed")
        return True

    def run_daily_digest(self, send_email: bool = False) -> bool:
        """Generate daily email digest with deeper analysis."""
        logger.info("=" * 60)
        logger.info("Starting daily email digest...")
        logger.info("=" * 60)

        # Retrieve emails
        email_content = self.retrieve_emails_with_retry()
        if not email_content:
            logger.error("Failed to retrieve emails")
            return False

        # Extract action items
        action_items = self.extract_action_items_with_retry(email_content)
        if not action_items:
            logger.warning("Failed to extract action items")
            action_items = "No action items could be extracted."

        # Analyze sentiment
        sentiment_analysis = self.analyze_email_sentiment_with_retry(email_content)
        if not sentiment_analysis:
            logger.warning("Failed to analyze email sentiment")
            sentiment_analysis = "No sentiment analysis available."

        # Create trend analysis (patterns over time)
        trend_prompt = f"""
Analyze the following email content for patterns and trends:

{email_content}

Identify:
1. Top senders and their frequency
2. Common topics and themes
3. Time-based patterns (when emails arrive)
4. Response requirements and follow-up needs
5. Recurring contacts and important relationships
6. Potential missed connections or responses

Format as a pattern analysis report.
"""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing email patterns (attempt {attempt}/{self.max_retries})...")

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": trend_prompt}],
                    temperature=0.4,
                    max_tokens=2048
                )

                trend_analysis = response.choices[0].message.content
                break
            except Exception as e:
                logger.error(f"❌ Trend analysis attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("All trend analysis attempts failed")
                    trend_analysis = "No pattern analysis available."

        # Combine into daily report (Markdown format - HTML generator will convert)
        daily_content = f"""
## 📊 Daily Email Report - {datetime.now().strftime('%Y-%m-%d')}

### 📋 Top Priority Action Items

{action_items}

---

### 📧 Complete Email Summary

{email_content}

---

### 📈 Communication Patterns

{trend_analysis}

---

### 🧠 Sentiment Analysis

{sentiment_analysis}

---

### Today's Communication Summary

- **Provider:** {self.email_provider}
- **Period:** Last {self.hours_back} hours
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Next Review:** Tomorrow morning
"""

        filepath = self.save_email_digest(daily_content, "daily")

        if send_email:
            subject = f"📊 Daily Email Digest - {datetime.now().strftime('%A, %B %d')}"
            send_email_report(
                client=self.client,
                recipient_email=self.recipient_email,
                subject=subject,
                body="Please find attached your personalized email digest with summaries and action items.",
                attachment_path=filepath,
                logger=logger
            )

        logger.info("✅ Daily email digest completed")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Intelligent Email Digest Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection
  %(prog)s --test

  # Morning digest for last 24 hours
  %(prog)s --morning --provider gmail_primary

  # Daily digest with email
  %(prog)s --daily --provider outlook_personal --email user@example.com

  # Custom time range (last 12 hours)
  %(prog)s --morning --provider gmail_primary --hours 12 --email user@example.com

  # Scheduled morning digest at 8 AM
  %(prog)s --schedule-morning --provider gmail_primary --email user@example.com
        """
    )

    # Mode arguments
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--test', action='store_true', help='Test server connection')
    mode_group.add_argument('--morning', action='store_true', help='Generate morning digest (last 24 hours)')
    mode_group.add_argument('--daily', action='store_true', help='Generate daily analysis')
    mode_group.add_argument('--schedule-morning', action='store_true', help='Schedule morning digest')

    # Configuration
    parser.add_argument('--server', default='http://localhost:5000/v1', help='Server URL')
    parser.add_argument('--provider', default='gmail_primary', help='Email provider (default: gmail_primary)')
    parser.add_argument('--hours', type=int, default=24, help='Hours back to retrieve emails (default: 24)')
    parser.add_argument('--email', help='Recipient email for reports')
    parser.add_argument('--output-dir', default='email_digests', help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create agent
    agent = EmailDigestAgent(
        server_url=args.server,
        email_provider=args.provider,
        hours_back=args.hours,
        recipient_email=args.email,
        output_dir=args.output_dir
    )

    try:
        if args.test:
            success = agent.test_connection()
            sys.exit(0 if success else 1)

        elif args.morning:
            success = agent.run_morning_digest(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.daily:
            success = agent.run_daily_digest(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.schedule_morning:
            logger.info("Scheduling morning email digest for 8:00 AM")
            schedule.every().day.at("08:00").do(
                lambda: agent.run_morning_digest(send_email=bool(args.email))
            )
            logger.info("Press Ctrl+C to stop")
            while True:
                schedule.run_pending()
                time.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n👋 Email Digest Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
