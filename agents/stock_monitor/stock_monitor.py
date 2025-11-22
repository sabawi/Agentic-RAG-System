#!/usr/bin/env python3
"""
Stock Portfolio Monitor Agent
==============================

Monitors stock portfolio and sends alerts/reports using the Agentic-RAG server.

Features:
- Daily portfolio performance reports
- Price alert monitoring
- Email notifications for significant changes
- Historical trend analysis
- Automatic market open/close scheduling

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List

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
        logging.FileHandler('stock_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class StockMonitorAgent:
    """Stock Portfolio Monitor with automated alerts and reports."""

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        stocks: List[str] = None,
        recipient_email: Optional[str] = None,
        output_dir: str = "stock_reports",
        alert_threshold: float = 5.0,
        max_retries: int = 3
    ):
        """
        Initialize the stock monitor agent.

        Args:
            server_url: URL of the Agentic-RAG server
            stocks: List of stock symbols to monitor (e.g., ['AAPL', 'TSLA'])
            recipient_email: Email for alerts
            output_dir: Directory to save reports
            alert_threshold: Price change % threshold for alerts (default: 5%)
            max_retries: Maximum retry attempts on failure
        """
        self.server_url = server_url
        self.stocks = stocks or []
        self.recipient_email = recipient_email
        self.output_dir = Path(output_dir)
        self.alert_threshold = alert_threshold
        self.max_retries = max_retries

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

        # Initialize OpenAI client
        self.client = openai.OpenAI(
            base_url=server_url,
            api_key="not-required"
        )

        # Initialize HTML generator
        self.html_generator = HTMLReportGenerator()

        logger.info(f"StockMonitorAgent initialized for stocks: {', '.join(self.stocks)}")

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

    def analyze_portfolio_with_retry(self, analysis_type: str = "daily") -> Optional[str]:
        """
        Analyze portfolio with retry logic.

        Args:
            analysis_type: Type of analysis ('daily', 'weekly', 'alerts')

        Returns:
            Analysis result as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing portfolio (attempt {attempt}/{self.max_retries})...")

                # Build prompt based on analysis type
                if analysis_type == "daily":
                    prompt = self._build_daily_report_prompt()
                elif analysis_type == "weekly":
                    prompt = self._build_weekly_report_prompt()
                elif analysis_type == "alerts":
                    prompt = self._build_alert_check_prompt()
                else:
                    raise ValueError(f"Unknown analysis type: {analysis_type}")

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Lower temperature for factual analysis
                    max_tokens=4096
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Analysis content is empty or too short")

                logger.info(f"✅ Portfolio analysis completed ({len(content)} chars)")
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

    def _build_daily_report_prompt(self) -> str:
        """Build prompt for daily portfolio report."""
        stocks_list = ", ".join(self.stocks)
        return f"""
Please provide a comprehensive daily portfolio report for the following stocks: {stocks_list}

Use the comprehensive_stock_analyzer and get_stock_and_company_data tools to gather:

1. Current prices and today's price changes ($ and %)
2. Trading volume compared to average
3. Key news or events affecting each stock
4. Overall portfolio performance summary
5. Market sentiment and trends

Format as a Markdown report with:
- Clear section headers (## for main sections, ### for subsections)
- Tables for price data
- Use `.gain` class for positive changes, `.loss` class for negative changes
- Summary statistics at the top
- News highlights section
- Bullet points for key information

Make it concise but informative for a daily morning briefing.
IMPORTANT: Return ONLY Markdown format, NOT HTML.
"""

    def _build_weekly_report_prompt(self) -> str:
        """Build prompt for weekly portfolio report."""
        stocks_list = ", ".join(self.stocks)
        return f"""
Please provide a comprehensive WEEKLY portfolio report for: {stocks_list}

Use comprehensive_stock_analyzer and analytical_visualizer tools to create:

1. Week-over-week performance analysis
2. Price charts showing weekly trends
3. Volume analysis and patterns
4. Major news events and their impact
5. Sector performance comparison
6. Recommendations for next week

Format as a detailed Markdown report with:
- Executive summary at top (## header)
- Performance charts and visualizations
- Detailed analysis per stock (### subheaders)
- Portfolio recommendations
- Risk assessment
- Tables and bullet points for data

This is for weekend review and planning.
IMPORTANT: Return ONLY Markdown format, NOT HTML.
"""

    def _build_alert_check_prompt(self) -> str:
        """Build prompt for alert checking."""
        stocks_list = ", ".join(self.stocks)
        return f"""
Check for significant price movements in: {stocks_list}

Use get_stock_and_company_data to identify any stocks that have moved more than {self.alert_threshold}% today.

For each stock with significant movement:
1. Current price and % change
2. Reason for the movement (news, earnings, etc.)
3. Analysis of whether it's a trend or temporary
4. Recommendation (hold, buy more, sell, etc.)

Format as a brief alert message. Only include stocks with movements > {self.alert_threshold}%.
If no stocks meet criteria, return "No significant movements today."
"""

    def save_report(self, content: str, report_type: str) -> Path:
        """Save report to HTML file using central HTML generator."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_{report_type}_{timestamp}.html"
        filepath = self.output_dir / filename

        try:
            # Use central HTML generator to convert Markdown to HTML
            html_content = self.html_generator.generate_html_report(
                content=content,
                title=f"Portfolio {report_type.title()} Report - {datetime.now().strftime('%Y-%m-%d')}",
                header_title=f"📊 Portfolio {report_type.title()} Report",
                header_subtitle=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                include_disclaimer=False
            )

            filepath.write_text(html_content, encoding='utf-8')
            logger.info(f"✅ Saved report to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")
            raise

    def send_email_report(self, filepath: Path, subject: str) -> bool:
        """Send report via email."""
        if not self.recipient_email:
            logger.warning("No recipient email configured")
            return False

        try:
            logger.info(f"Sending report to {self.recipient_email}...")

            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Use the secure_email_sender tool to send an email to {self.recipient_email} with:\n"
                        f"Subject: '{subject}'\n"
                        f"Body: 'Please see attached portfolio report.'\n"
                        f"Attach: {filepath.absolute()}"
                    )
                }]
            )

            logger.info("✅ Email sent successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    def run_daily_report(self, send_email: bool = False) -> bool:
        """Generate and optionally email daily report."""
        logger.info("=" * 60)
        logger.info("Generating daily portfolio report...")
        logger.info("=" * 60)

        result = self.analyze_portfolio_with_retry("daily")
        if not result:
            return False

        filepath = self.save_report(result, "daily")

        if send_email:
            subject = f"Daily Portfolio Report - {datetime.now().strftime('%Y-%m-%d')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Daily report completed")
        return True

    def run_weekly_report(self, send_email: bool = False) -> bool:
        """Generate and optionally email weekly report."""
        logger.info("=" * 60)
        logger.info("Generating weekly portfolio report...")
        logger.info("=" * 60)

        result = self.analyze_portfolio_with_retry("weekly")
        if not result:
            return False

        filepath = self.save_report(result, "weekly")

        if send_email:
            subject = f"Weekly Portfolio Report - {datetime.now().strftime('%Y-%m-%d')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Weekly report completed")
        return True

    def run_alert_check(self, send_email: bool = False) -> bool:
        """Check for price alerts."""
        logger.info("Checking for price alerts...")

        result = self.analyze_portfolio_with_retry("alerts")
        if not result:
            return False

        # Only send email/save if there are actual alerts
        if "No significant movements" not in result:
            logger.warning(f"⚠️ ALERT: Significant price movements detected!")
            filepath = self.save_report(result, "alert")

            if send_email:
                subject = f"🚨 Portfolio Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                self.send_email_report(filepath, subject)
        else:
            logger.info("No significant movements detected")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Stock Portfolio Monitor Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection
  %(prog)s --test

  # Daily report for specific stocks
  %(prog)s --daily --stocks AAPL TSLA NVDA

  # Daily report with email
  %(prog)s --daily --stocks AAPL TSLA --email you@gmail.com

  # Weekly report
  %(prog)s --weekly --stocks AAPL TSLA NVDA MSFT

  # Check for alerts (5%% threshold)
  %(prog)s --alerts --stocks AAPL TSLA --threshold 5.0

  # Scheduled daily reports at market open (9:30 AM)
  %(prog)s --schedule-daily --stocks AAPL TSLA --email you@gmail.com
        """
    )

    # Mode arguments
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--test', action='store_true', help='Test server connection')
    mode_group.add_argument('--daily', action='store_true', help='Generate daily report')
    mode_group.add_argument('--weekly', action='store_true', help='Generate weekly report')
    mode_group.add_argument('--alerts', action='store_true', help='Check for price alerts')
    mode_group.add_argument('--schedule-daily', action='store_true', help='Schedule daily reports')

    # Configuration
    parser.add_argument('--server', default='http://localhost:5000/v1', help='Server URL')
    parser.add_argument('--stocks', nargs='+', required='--test' not in sys.argv, help='Stock symbols to monitor')
    parser.add_argument('--email', help='Recipient email for reports')
    parser.add_argument('--output-dir', default='stock_reports', help='Output directory')
    parser.add_argument('--threshold', type=float, default=5.0, help='Alert threshold percentage')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create agent
    agent = StockMonitorAgent(
        server_url=args.server,
        stocks=args.stocks or [],
        recipient_email=args.email,
        output_dir=args.output_dir,
        alert_threshold=args.threshold
    )

    try:
        if args.test:
            success = agent.test_connection()
            sys.exit(0 if success else 1)

        elif args.daily:
            success = agent.run_daily_report(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.weekly:
            success = agent.run_weekly_report(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.alerts:
            success = agent.run_alert_check(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.schedule_daily:
            logger.info("Scheduling daily reports for 9:30 AM (market open)")
            schedule.every().day.at("09:30").do(
                lambda: agent.run_daily_report(send_email=bool(args.email))
            )
            logger.info("Press Ctrl+C to stop")
            while True:
                schedule.run_pending()
                time.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n👋 Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
