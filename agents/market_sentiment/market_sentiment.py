#!/usr/bin/env python3
"""
Market Sentiment Analyzer Agent
==============================

Monitor market sentiment from news and analyze trends for investment insights.

Features:
- Aggregate financial news and social media sentiment
- Analyze market trends and sentiment
- Generate charts and visualizations
- Create sentiment trend reports
- Send investment recommendations

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
import re

import openai
import schedule

# Add project root to sys.path to allow importing utils
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import centralized HTML generator
from utils.html_generator import HTMLReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_sentiment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def clean_html_response(content: str) -> str:
    """
    Clean up HTML responses by removing markdown code blocks and extracting content fragments.

    Handles responses that may contain:
    - Markdown code blocks (```html ... ```)
    - Standalone HTML documents with <!DOCTYPE>, <html>, <head>, <body> tags

    Returns clean HTML content fragments suitable for insertion into the report template.

    Args:
        content: Raw HTML content from LLM response

    Returns:
        Cleaned HTML content fragment
    """
    if not content:
        return content

    # Remove markdown code blocks
    # Pattern: ```html ... ``` or ```... ```
    content = re.sub(r'```html\s*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'```\s*', '', content)

    # Extract content from standalone HTML documents
    # If we find <!DOCTYPE> or <html>, extract just the body content
    if '<!DOCTYPE' in content or '<html' in content:
        # Try to extract body content
        body_match = re.search(r'<body[^>]*>(.*)</body>', content, re.DOTALL | re.IGNORECASE)
        if body_match:
            content = body_match.group(1)
        else:
            # If no body tag, try to find where actual content starts (after </head>)
            head_end = re.search(r'</head>', content, re.IGNORECASE)
            if head_end:
                # Skip past </head> and remove trailing </html>
                content = content[head_end.end():]
                content = re.sub(r'</html>\s*$', '', content, flags=re.IGNORECASE)

    # Clean up any remaining HTML document tags at the start
    content = re.sub(r'^.*?<body[^>]*>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Clean up closing tags at the end
    content = re.sub(r'</body>\s*</html>\s*$', '', content, flags=re.IGNORECASE)

    return content.strip()


class MarketSentimentAgent:
    """Market sentiment analysis for investment and trading insights."""

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        symbols: List[str] = None,
        sectors: List[str] = None,
        recipient_email: Optional[str] = None,
        output_dir: str = "sentiment_reports",
        max_retries: int = 3
    ):
        """
        Initialize the market sentiment agent.

        Args:
            server_url: URL of the Agentic-RAG server
            symbols: List of stock symbols to monitor (e.g., ['AAPL', 'TSLA'])
            sectors: List of sectors to monitor (e.g., ['technology', 'finance'])
            recipient_email: Email for sentiment reports
            output_dir: Directory to save sentiment reports
            max_retries: Maximum retry attempts on failure
        """
        self.server_url = server_url
        self.symbols = symbols or []
        self.sectors = sectors or []
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

        logger.info(f"MarketSentimentAgent initialized for symbols: {', '.join(self.symbols)}, sectors: {', '.join(self.sectors)}")

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

    def analyze_market_sentiment_with_retry(self, symbols: List[str], sectors: List[str]) -> Optional[str]:
        """
        Analyze market sentiment with retry logic.

        Args:
            symbols: List of stock symbols to analyze
            sectors: List of sectors to analyze

        Returns:
            Sentiment analysis as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing market sentiment (attempt {attempt}/{self.max_retries})...")

                # Build comprehensive prompt
                symbols_str = ", ".join(symbols) if symbols else "general market"
                sectors_str = ", ".join(sectors) if sectors else "broad market"
                
                prompt = f"""
Please analyze current market sentiment for:
- Symbols: {symbols_str}
- Sectors: {sectors_str}

Use multiple tools to gather comprehensive market intelligence:
1. Use get_news_summaries to find the latest financial news
2. Use comprehensive_stock_analyzer for stock-specific data
3. Use search_web to find additional market sentiment sources
4. Use analytical_visualizer to create relevant charts if possible

Provide a comprehensive market sentiment analysis including:

1. Overall market sentiment (bullish/bearish/neutral)
2. Sector-specific sentiment analysis
3. Individual symbol sentiment (if symbols provided)
4. Key news items affecting sentiment
5. Social media sentiment trends
6. Economic indicators impact
7. Risk factors and opportunities
8. Confidence levels for each assessment

Format as an HTML report fragment with:
- Professional styling
- Color-coded sentiment indicators
- Clear charts and visualizations
- Executive summary at top
- Risk assessment section

CRITICAL FORMATTING REQUIREMENTS:
1. OUTPUT MUST BE HTML CONTENT ONLY - NO markdown syntax anywhere
2. DO NOT wrap output in code blocks (NO ```html or ``` markers)
3. DO NOT include <!DOCTYPE>, <html>, <head>, or <body> tags
4. Generate HTML CONTENT FRAGMENTS that will be inserted into an existing HTML document
5. Use semantic HTML tags:
   - <h2>, <h3>, <h4> for headings (NOT # ## ###)
   - <p> for paragraphs
   - <ul><li> and <ol><li> for lists (NOT - or *)
   - <table><tr><th><td> for tables (NOT | pipes |)
   - <strong> and <em> for emphasis (NOT ** or *)
   - <div class="info">, <div class="high">, <div class="medium"> for styled sections
6. Start directly with content (e.g., <h2>Market Overview</h2><p>Content here...</p>)
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,  # Balanced for analysis
                    max_tokens=4096
                )

                content = clean_html_response(response.choices[0].message.content)

                if not content or len(content) < 100:
                    raise ValueError("Sentiment analysis content is empty or too short")

                logger.info(f"✅ Market sentiment analysis completed ({len(content)} chars)")
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

    def generate_trading_signals_with_retry(self, market_data: str) -> Optional[str]:
        """
        Generate trading signals based on market data.

        Args:
            market_data: Market analysis data to process

        Returns:
            Trading signals as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Generating trading signals (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Based on the following market analysis data, generate trading signals and recommendations:

{market_data}

For each stock/symbol mentioned, provide:
1. Trading signal (Buy/Hold/Sell)
2. Confidence level (High/Medium/Low)
3. Price target and time frame
4. Risk assessment
5. Supporting rationale
6. Key factors influencing decision

Also provide:
- Overall market outlook
- Sector rotation recommendations
- Momentum indicators
- Volatility expectations
- Position sizing suggestions

Format as a structured trading recommendations report.

CRITICAL FORMATTING REQUIREMENTS:
1. OUTPUT MUST BE HTML CONTENT ONLY - NO markdown syntax anywhere
2. DO NOT wrap output in code blocks (NO ```html or ``` markers)
3. DO NOT include <!DOCTYPE>, <html>, <head>, or <body> tags
4. Generate HTML CONTENT FRAGMENTS that will be inserted into an existing HTML document
5. Use semantic HTML tags:
   - <h2>, <h3>, <h4> for headings (NOT # ## ###)
   - <p> for paragraphs
   - <ul><li> and <ol><li> for lists (NOT - or *)
   - <table><tr><th><td> for tables (NOT | pipes |)
   - <strong> and <em> for emphasis (NOT ** or *)
6. Start directly with content (e.g., <h2>Trading Signals</h2><p>Content here...</p>)
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,  # Balanced for practical recommendations
                    max_tokens=2048
                )

                content = clean_html_response(response.choices[0].message.content)

                if not content or len(content) < 100:
                    raise ValueError("Trading signals content is empty or too short")

                logger.info(f"✅ Trading signals generated ({len(content)} chars)")
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

    def create_market_summary_with_retry(self, sentiment_data: str) -> Optional[str]:
        """
        Create market summary dashboard.

        Args:
            sentiment_data: Complete sentiment analysis data

        Returns:
            Market summary as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Creating market summary (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Based on the following market sentiment data, create an executive market summary dashboard:

{sentiment_data}

Include:
1. Market sentiment score (0-100 scale)
2. Volatility index and trends
3. Sector performance overview
4. Top gainers and losers sentiment
5. Economic indicator impact
6. Geopolitical risk assessment
7. Technical analysis summary
8. Key support/resistance levels

Present in a dashboard format with:
- Key metrics at the top
- Color-coded risk levels
- Quick insights section

CRITICAL FORMATTING REQUIREMENTS:
1. OUTPUT MUST BE HTML CONTENT ONLY - NO markdown syntax anywhere
2. DO NOT wrap output in code blocks (NO ```html or ``` markers)
3. DO NOT include <!DOCTYPE>, <html>, <head>, or <body> tags
4. Generate HTML CONTENT FRAGMENTS that will be inserted into an existing HTML document
5. Use semantic HTML tags:
   - <h2>, <h3>, <h4> for headings (NOT # ## ###)
   - <p> for paragraphs
   - <ul><li> and <ol><li> for lists (NOT - or *)
   - <table><tr><th><td> for tables (NOT | pipes |)
   - <strong> and <em> for emphasis (NOT ** or *)
6. Start directly with content (e.g., <h2>Market Summary</h2><p>Content here...</p>)
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,  # Balanced for dashboard
                    max_tokens=2048
                )

                content = clean_html_response(response.choices[0].message.content)

                if not content or len(content) < 100:
                    raise ValueError("Market summary content is empty or too short")

                logger.info(f"✅ Market summary created ({len(content)} chars)")
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

    def save_sentiment_report(self, content: str, report_type: str) -> Path:
        """
        Save sentiment report to HTML file using centralized HTML generator.

        Args:
            content: Report content to save (markdown or HTML)
            report_type: Type of report ('daily', 'weekly', 'summary')

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sentiment_{report_type}_report_{timestamp}.html"
        title = f"Market Sentiment {report_type.title()} Report"
        filepath = self.output_dir / filename

        try:
            # Use centralized HTML generator with automatic markdown conversion
            html_content = self.html_generator.generate_html_report(
                title=title,
                content=content
            )

            filepath.write_text(html_content, encoding='utf-8')
            logger.info(f"✅ Saved sentiment report to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to save sentiment report: {e}")
            raise

    def send_email_report(self, filepath: Path, subject: str) -> bool:
        """
        Send sentiment report via email.

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
            logger.info(f"Sending sentiment report to {self.recipient_email}...")

            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Use the secure_email_sender tool to send an email to {self.recipient_email} with:\n"
                        f"Subject: '{subject}'\n"
                        f"Body: 'Please find attached your market sentiment analysis with trading insights and recommendations.'\n"
                        f"Attach: {filepath.absolute()}"
                    )
                }]
            )

            logger.info("✅ Sentiment report email sent successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send sentiment report email: {e}")
            return False

    def run_daily_sentiment(self, send_email: bool = False) -> bool:
        """Generate daily market sentiment report."""
        logger.info("=" * 60)
        logger.info("Starting daily market sentiment analysis...")
        logger.info("=" * 60)

        # Get market sentiment
        sentiment_data = self.analyze_market_sentiment_with_retry(self.symbols, self.sectors)
        if not sentiment_data:
            logger.error("Failed to get market sentiment")
            return False

        # Generate trading signals
        trading_signals = self.generate_trading_signals_with_retry(sentiment_data)
        if not trading_signals:
            logger.warning("Failed to generate trading signals")
            trading_signals = "No trading signals could be generated."

        # Create market summary
        market_summary = self.create_market_summary_with_retry(sentiment_data)
        if not market_summary:
            logger.warning("Failed to create market summary")
            market_summary = "No market summary available."

        # Combine into daily report
        daily_content = f"""
<div class="dashboard">
    <h2>📈 Daily Market Summary</h2>
    {market_summary}
</div>

<h2>📊 Market Sentiment Analysis</h2>
{sentiment_data}

<h2>🎯 Trading Signals & Recommendations</h2>
{trading_signals}

<div style="margin-top: 30px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
    <h3>Market Overview</h3>
    <ul>
        <li><strong>Symbols Monitored:</strong> {', '.join(self.symbols) if self.symbols else 'General Market'}</li>
        <li><strong>Sectors Monitored:</strong> {', '.join(self.sectors) if self.sectors else 'Broad Market'}</li>
        <li><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</li>
        <li><strong>Generated:</strong> {datetime.now().strftime('%H:%M:%S')}</li>
    </ul>
</div>
"""

        filepath = self.save_sentiment_report(daily_content, "daily")

        if send_email:
            subject = f"📈 Daily Market Sentiment Report - {datetime.now().strftime('%A, %B %d')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Daily market sentiment analysis completed")
        return True

    def run_weekly_analysis(self, send_email: bool = False) -> bool:
        """Generate weekly comprehensive market analysis."""
        logger.info("=" * 60)
        logger.info("Starting weekly comprehensive market analysis...")
        logger.info("=" * 60)

        # Get market sentiment
        sentiment_data = self.analyze_market_sentiment_with_retry(self.symbols, self.sectors)
        if not sentiment_data:
            logger.error("Failed to get market sentiment")
            return False

        # Generate trading signals
        trading_signals = self.generate_trading_signals_with_retry(sentiment_data)
        if not trading_signals:
            logger.warning("Failed to generate trading signals")
            trading_signals = "No trading signals could be generated."

        # Create market summary
        market_summary = self.create_market_summary_with_retry(sentiment_data)
        if not market_summary:
            logger.warning("Failed to create market summary")
            market_summary = "No market summary available."

        # Generate week trend analysis
        trend_prompt = f"""
Based on the following market data, analyze weekly trends and patterns:

{sentiment_data}

Provide:
1. Weekly sentiment trend analysis
2. Volatility patterns over the week
3. Sector rotation trends
4. Momentum shifts
5. Key turning points
6. Correlation analysis between sectors
7. Week-over-week comparison
8. Next week outlook

Format as a comprehensive trend analysis.

CRITICAL FORMATTING REQUIREMENTS:
1. OUTPUT MUST BE HTML CONTENT ONLY - NO markdown syntax anywhere
2. DO NOT wrap output in code blocks (NO ```html or ``` markers)
3. DO NOT include <!DOCTYPE>, <html>, <head>, or <body> tags
4. Generate HTML CONTENT FRAGMENTS that will be inserted into an existing HTML document
5. Use semantic HTML tags:
   - <h2>, <h3>, <h4> for headings (NOT # ## ###)
   - <p> for paragraphs
   - <ul><li> and <ol><li> for lists (NOT - or *)
   - <table><tr><th><td> for tables (NOT | pipes |)
   - <strong> and <em> for emphasis (NOT ** or *)
6. Start directly with content (e.g., <h2>Trend Analysis</h2><p>Content here...</p>)
"""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing weekly trends (attempt {attempt}/{self.max_retries})...")

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": trend_prompt}],
                    temperature=0.4,
                    max_tokens=2048
                )

                trend_analysis = clean_html_response(response.choices[0].message.content)
                break
            except Exception as e:
                logger.error(f"❌ Trend analysis attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("All trend analysis attempts failed")
                    trend_analysis = "No trend analysis available."

        # Combine into weekly report
        weekly_content = f"""
<h2>📊 Weekly Market Analysis - {datetime.now().strftime('%Y-%m-%d')}</h2>

<div class="dashboard">
    <h3>Weekly Market Dashboard</h3>
    {market_summary}
</div>

<h3>📈 Sentiment Analysis</h3>
{sentiment_data}

<h3>📊 Weekly Trend Analysis</h3>
{trend_analysis}

<h3>🎯 Trading Signals & Recommendations</h3>
{trading_signals}

<div style="margin-top: 30px; padding: 15px; background-color: #e8f5e8; border-radius: 5px;">
    <h3>Week's Key Insights</h3>
    <ul>
        <li><strong>Symbols Monitored:</strong> {', '.join(self.symbols) if self.symbols else 'General Market'}</li>
        <li><strong>Sectors Monitored:</strong> {', '.join(self.sectors) if self.sectors else 'Broad Market'}</li>
        <li><strong>Analysis Period:</strong> This week (Mon-Sun)</li>
        <li><strong>Next Analysis:</strong> Next Monday morning</li>
    </ul>
</div>
"""

        filepath = self.save_sentiment_report(weekly_content, "weekly")

        if send_email:
            subject = f"📊 Weekly Market Analysis Report - {datetime.now().strftime('%B %d, %Y')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Weekly market analysis completed")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Market Sentiment Analyzer Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection
  %(prog)s --test

  # Daily sentiment analysis for specific stocks
  %(prog)s --daily --symbols AAPL TSLA NVDA

  # Weekly analysis for sectors
  %(prog)s --weekly --sectors technology healthcare --email trader@example.com

  # Analysis with both stocks and sectors
  %(prog)s --daily --symbols AAPL MSFT --sectors finance --email analyst@example.com

  # Scheduled daily reports at 9 AM
  %(prog)s --schedule-daily --symbols NVDA TSLA --email investor@example.com
        """
    )

    # Mode arguments
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--test', action='store_true', help='Test server connection')
    mode_group.add_argument('--daily', action='store_true', help='Generate daily sentiment report')
    mode_group.add_argument('--weekly', action='store_true', help='Generate weekly analysis')
    mode_group.add_argument('--schedule-daily', action='store_true', help='Schedule daily reports')

    # Configuration
    parser.add_argument('--server', default='http://localhost:5000/v1', help='Server URL')
    parser.add_argument('--symbols', nargs='+', default=[], help='Stock symbols to monitor')
    parser.add_argument('--sectors', nargs='+', default=[], help='Sectors to monitor')
    parser.add_argument('--email', help='Recipient email for reports')
    parser.add_argument('--output-dir', default='sentiment_reports', help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create agent
    agent = MarketSentimentAgent(
        server_url=args.server,
        symbols=args.symbols,
        sectors=args.sectors,
        recipient_email=args.email,
        output_dir=args.output_dir
    )

    try:
        if args.test:
            success = agent.test_connection()
            sys.exit(0 if success else 1)

        elif args.daily:
            success = agent.run_daily_sentiment(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.weekly:
            success = agent.run_weekly_analysis(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.schedule_daily:
            logger.info("Scheduling daily market sentiment reports for 9:00 AM")
            schedule.every().day.at("09:00").do(
                lambda: agent.run_daily_sentiment(send_email=bool(args.email))
            )
            logger.info("Press Ctrl+C to stop")
            while True:
                schedule.run_pending()
                time.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n👋 Market Sentiment Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()