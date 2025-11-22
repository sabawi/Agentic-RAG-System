#!/usr/bin/env python3
"""
Personal Research Assistant Agent
================================

Automated academic and research paper aggregation and analysis agent.

Features:
- Monitor specific research topics for new academic papers
- Summarize papers for quick review
- Track citation trends and research developments
- Generate reading lists and literature reviews
- Send curated research digests via email

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import json

import openai
import schedule

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.html_generator import HTMLReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_assistant.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ResearchAssistantAgent:
    """Personal research assistant for academic and industry research tracking."""

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        topics: List[str] = None,
        recipient_email: Optional[str] = None,
        output_dir: str = "research_output",
        max_retries: int = 3
    ):
        """
        Initialize the research assistant agent.

        Args:
            server_url: URL of the Agentic-RAG server
            topics: List of research topics to monitor
            recipient_email: Email for research digests
            output_dir: Directory to save research reports
            max_retries: Maximum retry attempts on failure
        """
        self.server_url = server_url
        self.topics = topics or []
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

        # Initialize HTML report generator
        self.html_generator = HTMLReportGenerator()

        logger.info(f"ResearchAssistantAgent initialized for topics: {', '.join(self.topics)}")

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

    def search_research_with_retry(self, topic: str) -> Optional[str]:
        """
        Search for research papers with retry logic.

        Args:
            topic: Research topic to search for

        Returns:
            Research content as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Searching research for '{topic}' (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Please search for recent academic research papers on: {topic}

Use the published_papers_search tool to find the latest papers. Then provide:

1. Top 5-10 most relevant recent papers with:
   - Title and authors
   - Publication date and venue
   - Brief abstract or summary
   - Key findings and implications
   - Link/citation if available

2. Identify trends in the research area
3. Highlight any breakthrough findings
4. Suggest follow-up research directions

Format as a structured HTML report with:
- Professional styling
- Clear categorization
- Links to papers where available
- Summary statistics
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Low temperature for factual content
                    max_tokens=4096
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Research content is empty or too short")

                logger.info(f"✅ Research search completed ({len(content)} chars)")
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

    def analyze_research_trends_with_retry(self, topics: List[str]) -> Optional[str]:
        """
        Analyze research trends across multiple topics.

        Args:
            topics: List of research topics to analyze

        Returns:
            Trend analysis as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing research trends for {len(topics)} topics (attempt {attempt}/{self.max_retries})...")

                topics_str = ", ".join(topics)
                prompt = f"""
Analyze current research trends across these topics: {topics_str}

Use published_papers_search and other tools to provide:

1. Cross-topic analysis showing connections
2. Emerging research areas and methodologies
3. Leading researchers and institutions
4. Funding trends and priorities
5. Technology convergence areas
6. Market applications and commercial potential

Create a comprehensive trend analysis report with:
- Executive summary
- Detailed trend analysis per topic
- Cross-topic correlations
- Future predictions
- Recommendations for further investigation

Format as an HTML report with charts and visualizations where possible.
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,  # Slightly higher for analysis
                    max_tokens=4096
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Trend analysis content is empty or too short")

                logger.info(f"✅ Trend analysis completed ({len(content)} chars)")
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

    def create_reading_list(self, research_content: str) -> Optional[str]:
        """
        Create a prioritized reading list from research content.

        Args:
            research_content: Research content to analyze

        Returns:
            Reading list as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Creating reading list (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Based on the following research content, create a prioritized reading list:

{research_content}

Create a structured reading list that includes:
1. Priority ranking (1-5 scale)
2. Paper titles with brief descriptions
3. Estimated reading time
4. Prerequisites/required background knowledge
5. Relevance score to user's interests
6. Key takeaways for each paper

Format as an organized HTML document with:
- Clear priority indicators
- Estimated time requirements
- Relevance scoring
- Actionable next steps
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,  # Balanced for practical recommendations
                    max_tokens=2048
                )

                content = response.choices[0].message.content

                if not content or len(content) < 50:
                    raise ValueError("Reading list content is empty or too short")

                logger.info(f"✅ Reading list created ({len(content)} chars)")
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

    def save_research_report(self, content: str, report_type: str, topic: str = "") -> Path:
        """
        Save research report to HTML file using centralized HTML generator.

        Args:
            content: Report content to save (markdown or HTML)
            report_type: Type of report ('daily', 'weekly', 'trend', 'reading_list')
            topic: Optional topic name for file naming

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Build filename
        if topic:
            filename = f"research_{report_type}_{topic}_{timestamp}.html"
            title = f"Research {report_type.title()} Report: {topic}"
        else:
            filename = f"research_{report_type}_{timestamp}.html"
            title = f"Research {report_type.title()} Report"

        filepath = self.output_dir / filename

        try:
            # Use centralized HTML generator with automatic markdown conversion
            html_content = self.html_generator.generate_html_report(
                title=title,
                content=content,
                report_type=report_type
            )

            filepath.write_text(html_content, encoding='utf-8')
            logger.info(f"✅ Saved research report to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to save research report: {e}")
            raise

    def send_email_report(self, filepath: Path, subject: str) -> bool:
        """
        Send research report via email.

        Args:
            filepath: Path to HTML report file
            subject: Email subject

        Returns:
            True if email was sent successfully
        """
        if not self.recipient_email:
            logger.warning("No recipient email configured")
            return False

        try:
            logger.info(f"Sending research report to {self.recipient_email}...")

            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Use the secure_email_sender tool to send an email to {self.recipient_email} with:\n"
                        f"Subject: '{subject}'\n"
                        f"Body: 'Please find attached your personalized research digest with the latest papers and insights.'\n"
                        f"Attach: {filepath.absolute()}"
                    )
                }]
            )

            logger.info("✅ Research report email sent successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send research report email: {e}")
            return False

    def run_daily_research(self, send_email: bool = False) -> bool:
        """Generate daily research updates for all topics."""
        logger.info("=" * 60)
        logger.info("Starting daily research update...")
        logger.info("=" * 60)

        all_research = []
        for topic in self.topics:
            logger.info(f"Researching topic: {topic}")
            research_result = self.search_research_with_retry(topic)
            if research_result:
                all_research.append({
                    'topic': topic,
                    'content': research_result
                })
            else:
                logger.warning(f"Failed to research topic: {topic}")

        if not all_research:
            logger.error("No research results obtained")
            return False

        # Combine all research into a daily digest
        combined_content = f"""
<h2>Research Digest for {datetime.now().strftime('%Y-%m-%d')}</h2>

{datetime.now().strftime('%A, %B %d, %Y')}

<p>This is your personalized research digest with the latest papers and insights.</p>

<hr>

"""
        for research in all_research:
            combined_content += f"""
<h3>Topic: {research['topic']}</h3>
{research['content']}

<hr>
"""

        filepath = self.save_research_report(combined_content, "daily_digest")

        if send_email:
            subject = f"Daily Research Digest - {datetime.now().strftime('%Y-%m-%d')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Daily research update completed")
        return True

    def run_weekly_analysis(self, send_email: bool = False) -> bool:
        """Generate weekly research analysis and trends."""
        logger.info("=" * 60)
        logger.info("Starting weekly research analysis...")
        logger.info("=" * 60)

        # Get detailed research for each topic
        all_research = []
        for topic in self.topics:
            logger.info(f"Researching topic: {topic}")
            research_result = self.search_research_with_retry(topic)
            if research_result:
                all_research.append({
                    'topic': topic,
                    'content': research_result
                })
            else:
                logger.warning(f"Failed to research topic: {topic}")

        if not all_research:
            logger.error("No research results obtained")
            return False

        # Create trend analysis across topics
        trend_analysis = self.analyze_research_trends_with_retry(self.topics)
        if not trend_analysis:
            logger.warning("Trend analysis failed, proceeding with research only")

        # Create reading lists for each topic
        reading_lists = []
        for research in all_research:
            reading_list = self.create_reading_list(research['content'])
            if reading_list:
                reading_lists.append({
                    'topic': research['topic'],
                    'reading_list': reading_list
                })

        # Combine everything into weekly report
        weekly_content = f"""
<h2>Weekly Research Analysis - {datetime.now().strftime('%Y-%m-%d')}</h2>

<h3>Executive Summary</h3>
<p>Weekly research analysis covering {len(self.topics)} key topics with trend analysis and reading recommendations.</p>

<h3>Trending Research Areas</h3>
{trend_analysis or "Trend analysis not available"}

<hr>

<h3>Detailed Research by Topic</h3>
"""

        for research in all_research:
            weekly_content += f"""
<h4>Topic: {research['topic']}</h4>
{research['content']}
<hr>
"""

        weekly_content += "<h3>Recommended Reading Lists</h3>"
        for reading_list in reading_lists:
            weekly_content += f"""
<h4>For {reading_list['topic']}</h4>
{reading_list['reading_list']}
<hr>
"""

        filepath = self.save_research_report(weekly_content, "weekly_analysis")

        if send_email:
            subject = f"Weekly Research Analysis - {datetime.now().strftime('%Y-%m-%d')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Weekly research analysis completed")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Personal Research Assistant Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection
  %(prog)s --test

  # Daily research update for specific topics
  %(prog)s --daily --topics "machine learning" "artificial intelligence" "neural networks"

  # Daily research with email
  %(prog)s --daily --topics "quantum computing" --email researcher@example.com

  # Weekly research analysis
  %(prog)s --weekly --topics "computer vision" "nlp" --email researcher@example.com

  # Scheduled daily research at 8 AM
  %(prog)s --schedule-daily --topics "blockchain" "cryptocurrency" --email user@example.com
        """
    )

    # Mode arguments
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--test', action='store_true', help='Test server connection')
    mode_group.add_argument('--daily', action='store_true', help='Generate daily research update')
    mode_group.add_argument('--weekly', action='store_true', help='Generate weekly analysis')
    mode_group.add_argument('--schedule-daily', action='store_true', help='Schedule daily research')

    # Configuration
    parser.add_argument('--server', default='http://localhost:5000/v1', help='Server URL')
    parser.add_argument('--topics', nargs='+', required='--test' not in sys.argv, help='Research topics to monitor')
    parser.add_argument('--email', help='Recipient email for reports')
    parser.add_argument('--output-dir', default='research_output', help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create agent
    agent = ResearchAssistantAgent(
        server_url=args.server,
        topics=args.topics or [],
        recipient_email=args.email,
        output_dir=args.output_dir
    )

    try:
        if args.test:
            success = agent.test_connection()
            sys.exit(0 if success else 1)

        elif args.daily:
            success = agent.run_daily_research(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.weekly:
            success = agent.run_weekly_analysis(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.schedule_daily:
            logger.info("Scheduling daily research updates for 8:00 AM")
            schedule.every().day.at("08:00").do(
                lambda: agent.run_daily_research(send_email=bool(args.email))
            )
            logger.info("Press Ctrl+C to stop")
            while True:
                schedule.run_pending()
                time.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n👋 Research Assistant stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()