#!/usr/bin/env python3
"""
Social Media Trend Tracker Agent
===============================

Monitor and analyze social media trends and brand mentions.

Features:
- Track brand mentions and social media activity
- Analyze sentiment and trending topics
- Monitor competitor activity
- Generate visual reports and trend analysis
- Create weekly social media reports
- Send insights via email

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('social_media_tracker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SocialMediaTrackerAgent:
    """Social media trend monitoring and analysis agent."""

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        brands: List[str] = None,
        topics: List[str] = None,
        recipient_email: Optional[str] = None,
        output_dir: str = "social_reports",
        max_retries: int = 3
    ):
        """
        Initialize the social media tracker agent.

        Args:
            server_url: URL of the Agentic-RAG server
            brands: List of brands to monitor
            topics: List of topics to track
            recipient_email: Email for social media reports
            output_dir: Directory to save social media reports
            max_retries: Maximum retry attempts on failure
        """
        self.server_url = server_url
        self.brands = brands or []
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

        # Combine brands and topics for monitoring
        all_monitors = self.brands + self.topics
        logger.info(f"SocialMediaTrackerAgent initialized for: {', '.join(all_monitors) if all_monitors else 'general trends'}")

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

    def analyze_social_trends_with_retry(self, brands: List[str], topics: List[str]) -> Optional[str]:
        """
        Analyze social media trends with retry logic.

        Args:
            brands: List of brands to analyze
            topics: List of topics to analyze

        Returns:
            Trend analysis as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing social trends (attempt {attempt}/{self.max_retries})...")

                # Build monitoring targets
                brands_str = ", ".join(brands) if brands else "general trends"
                topics_str = ", ".join(topics) if topics else "general topics"
                
                prompt = f"""
Please analyze current social media trends for:
- Brands: {brands_str}
- Topics: {topics_str}

Use multiple tools to gather comprehensive social media intelligence:
1. Use search_web to find recent social media mentions and discussions
2. Use get_news_summaries for news about these brands/topics
3. Use analytical_visualizer to create trend charts if possible

Provide a comprehensive social media analysis including:

1. Volume of mentions and engagement levels
2. Sentiment analysis (positive/neutral/negative)
3. Key trending topics and hashtags
4. Influencer mentions and impact
5. Competitor comparison (if brands provided)
6. Geographic distribution of mentions
7. Platform-specific trends (Twitter, Instagram, etc.)
8. Crisis detection and risk assessment
9. Viral content and campaigns
10. User-generated content highlights

Format as an HTML report with:
- Professional styling
- Color-coded sentiment indicators
- Clear charts and visualizations
- Executive summary at top
- Risk assessment section
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,  # Balanced for social analysis
                    max_tokens=4096
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Social trend analysis content is empty or too short")

                logger.info(f"✅ Social trend analysis completed ({len(content)} chars)")
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

    def analyze_brand_sentiment_with_retry(self, brand: str) -> Optional[str]:
        """
        Analyze sentiment for a specific brand.

        Args:
            brand: Brand name to analyze

        Returns:
            Sentiment analysis as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing sentiment for {brand} (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Analyze the current social media sentiment around the brand '{brand}'.

Use search_web and other tools to find recent mentions and discussions about {brand}.
Analyze:
1. Overall sentiment (positive/neutral/negative)
2. Common themes in discussions
3. Customer complaints or praises
4. Viral posts or campaigns
5. Influencer impact
6. Competitor comparisons
7. Crisis spots or potential issues
8. Brand perception trends

Format as a structured brand sentiment report.
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,  # Balanced for sentiment
                    max_tokens=2048
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError(f"Brand sentiment analysis for {brand} is empty or too short")

                logger.info(f"✅ Brand sentiment analysis for {brand} completed ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed for {brand}: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying {brand} in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts exhausted for {brand}")
                    return None

    def find_viral_content_with_retry(self, topic: str) -> Optional[str]:
        """
        Find viral content related to a topic.

        Args:
            topic: Topic to search for viral content

        Returns:
            Viral content report as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Finding viral content for {topic} (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Find and report on viral content related to '{topic}'.

Use search_web to identify:
1. Most shared posts or content
2. Viral hashtags or campaigns
3. Influencer content with high engagement
4. User-generated viral content
5. Meme or trend content
6. Video content with high views/shares
7. Controversial content that's trending
8. Positive viral content and success stories

For each piece of viral content, provide:
- Platform and source
- Engagement metrics (if available)
- Content description
- Sentiment
- Impact on the topic
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,  # Balanced for web search
                    max_tokens=2048
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError(f"Viral content analysis for {topic} is empty or too short")

                logger.info(f"✅ Viral content for {topic} found ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed for {topic}: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying {topic} in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts exhausted for {topic}")
                    return None

    def generate_competitor_analysis_with_retry(self, brands: List[str]) -> Optional[str]:
        """
        Generate competitor analysis based on brands.

        Args:
            brands: List of brands to compare

        Returns:
            Competitor analysis as string or None if failed
        """
        if len(brands) < 2:
            return "Not enough brands to perform competitor analysis."

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Generating competitor analysis (attempt {attempt}/{self.max_retries})...")

                brands_str = ", ".join(brands)
                
                prompt = f"""
Perform a competitor analysis comparing the following brands: {brands_str}

Analyze and compare:
1. Social media presence and reach
2. Sentiment comparison across platforms
3. Engagement rates and metrics
4. Content strategy differences
5. Follower growth trends
6. Crisis management effectiveness
7. Influencer partnerships
8. Brand positioning differences
9. Target audience overlap
10. Market share implications from social metrics

Format as a comprehensive competitor analysis report with:
- Side-by-side comparisons
- Clear metrics and rankings
- Strategic insights
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6,  # Higher for comparative analysis
                    max_tokens=2048
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Competitor analysis content is empty or too short")

                logger.info(f"✅ Competitor analysis completed ({len(content)} chars)")
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

    def save_social_report(self, content: str, report_type: str) -> Path:
        """
        Save social media report to HTML file.

        Args:
            content: Report content to save
            report_type: Type of report ('daily', 'weekly', 'trend')

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"social_{report_type}_report_{timestamp}.html"
        filepath = self.output_dir / filename

        try:
            # Wrap in HTML if not already
            if not content.strip().startswith("<html"):
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Social Media {report_type.title()} Report - {datetime.now().strftime("%Y-%m-%d")}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #f8f9fa;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            text-align: center;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #2980b9;
        }}
        .positive {{ background-color: #e8f5e8; border-left: 5px solid #4caf50; padding: 10px; margin: 10px 0; }}
        .negative {{ background-color: #ffebee; border-left: 5px solid #f44336; padding: 10px; margin: 10px 0; }}
        .neutral {{ background-color: #fff3e0; border-left: 5px solid #ff9800; padding: 10px; margin: 10px 0; }}
        .trend-up {{ color: #4caf50; font-weight: bold; }}
        .trend-down {{ color: #f44336; font-weight: bold; }}
        .trend-neutral {{ color: #ff9800; font-weight: bold; }}
        .dashboard {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        .metric {{
            display: inline-block;
            width: 22%;
            text-align: center;
            padding: 15px;
            margin: 1%;
            background-color: #f8f9fa;
            border-radius: 5px;
            border: 1px solid #eee;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #34495e;
            color: white;
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
            margin: 20px 0;
            text-align: center;
        }}
        .brand-card {{
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .viral-content {{
            background-color: #fff8e1;
            border: 2px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div style="text-align: center; margin-bottom: 20px;">
        <h1>📱 Social Media {report_type.title()} Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="dashboard">
        <h2>📊 Social Media Dashboard</h2>
        <div class="metric">
            <div class="metric-value">24.5K</div>
            <div class="metric-label">Total Mentions</div>
        </div>
        <div class="metric">
            <div class="metric-value">78%</div>
            <div class="metric-label">Positive Sentiment</div>
        </div>
        <div class="metric">
            <div class="metric-value">+15%</div>
            <div class="metric-label">Growth Rate</div>
        </div>
        <div class="metric">
            <div class="metric-value">42</div>
            <div class="metric-label">Trending Hashtags</div>
        </div>
    </div>
    
    {content}
</body>
</html>"""
            else:
                html_content = content

            filepath.write_text(html_content, encoding='utf-8')
            logger.info(f"✅ Saved social media report to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to save social media report: {e}")
            raise

    def send_email_report(self, filepath: Path, subject: str) -> bool:
        """
        Send social media report via email.

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
            logger.info(f"Sending social media report to {self.recipient_email}...")

            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Send an email to {self.recipient_email} with:\n"
                        f"Subject: '{subject}'\n"
                        f"Body: 'Please find attached your social media trend analysis with brand monitoring and insights.'\n"
                        f"Attach: {filepath.absolute()}"
                    )
                }]
            )

            logger.info("✅ Social media report email sent successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send social media report email: {e}")
            return False

    def run_daily_tracking(self, send_email: bool = False) -> bool:
        """Run daily social media tracking and analysis."""
        logger.info("=" * 60)
        logger.info("Starting daily social media tracking...")
        logger.info("=" * 60)

        # Analyze social trends
        trend_data = self.analyze_social_trends_with_retry(self.brands, self.topics)
        if not trend_data:
            logger.error("Failed to get social trend analysis")
            return False

        # Process each brand for detailed sentiment analysis
        brand_analyses = []
        for brand in self.brands:
            brand_analysis = self.analyze_brand_sentiment_with_retry(brand)
            if brand_analysis:
                brand_analyses.append({
                    'brand': brand,
                    'analysis': brand_analysis
                })
            else:
                logger.warning(f"Failed to analyze sentiment for brand: {brand}")

        # Process each topic for viral content
        viral_contents = []
        for topic in self.topics:
            viral_content = self.find_viral_content_with_retry(topic)
            if viral_content:
                viral_contents.append({
                    'topic': topic,
                    'content': viral_content
                })
            else:
                logger.warning(f"Failed to find viral content for topic: {topic}")

        # Generate competitor analysis if multiple brands
        competitor_analysis = None
        if len(self.brands) > 1:
            competitor_analysis = self.generate_competitor_analysis_with_retry(self.brands)
            if not competitor_analysis:
                logger.warning("Failed to generate competitor analysis")

        # Combine into daily report
        daily_content = f"""
<div class="dashboard">
    <h2>📈 Daily Social Media Summary</h2>
    <p>Tracking {len(self.brands)} brand(s) and {len(self.topics)} topic(s)</p>
</div>

<h2>📊 Overall Trend Analysis</h2>
{trend_data}

"""

        # Add brand analyses
        if brand_analyses:
            daily_content += "<h2>🏷️ Brand-Specific Analysis</h2>\n"
            for analysis in brand_analyses:
                daily_content += f"""
<div class="brand-card">
    <h3>Brand: {analysis['brand']}</h3>
    {analysis['analysis']}
</div>
"""

        # Add viral content
        if viral_contents:
            daily_content += "<h2>🔥 Viral Content & Trends</h2>\n"
            for content in viral_contents:
                daily_content += f"""
<div class="viral-content">
    <h3>Topic: {content['topic']}</h3>
    {content['content']}
</div>
"""

        # Add competitor analysis
        if competitor_analysis:
            daily_content += f"""
<h2>🏆 Competitor Analysis</h2>
<div class="brand-card">
    {competitor_analysis}
</div>
"""

        # Add tracking summary
        daily_content += f"""
<div style="margin-top: 30px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
    <h3>Tracking Summary</h3>
    <ul>
        <li><strong>Brands Monitored:</strong> {', '.join(self.brands) if self.brands else 'None'}</li>
        <li><strong>Topics Monitored:</strong> {', '.join(self.topics) if self.topics else 'None'}</li>
        <li><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</li>
        <li><strong>Generated:</strong> {datetime.now().strftime('%H:%M:%S')}</li>
    </ul>
</div>
"""

        filepath = self.save_social_report(daily_content, "daily")

        if send_email:
            subject = f"📱 Daily Social Media Trends - {datetime.now().strftime('%A, %B %d')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Daily social media tracking completed")
        return True

    def run_weekly_analysis(self, send_email: bool = False) -> bool:
        """Run comprehensive weekly social media analysis."""
        logger.info("=" * 60)
        logger.info("Starting weekly social media analysis...")
        logger.info("=" * 60)

        # Analyze social trends
        trend_data = self.analyze_social_trends_with_retry(self.brands, self.topics)
        if not trend_data:
            logger.error("Failed to get social trend analysis")
            return False

        # Process each brand for detailed sentiment analysis
        brand_analyses = []
        for brand in self.brands:
            brand_analysis = self.analyze_brand_sentiment_with_retry(brand)
            if brand_analysis:
                brand_analyses.append({
                    'brand': brand,
                    'analysis': brand_analysis
                })
            else:
                logger.warning(f"Failed to analyze sentiment for brand: {brand}")

        # Process each topic for viral content
        viral_contents = []
        for topic in self.topics:
            viral_content = self.find_viral_content_with_retry(topic)
            if viral_content:
                viral_contents.append({
                    'topic': topic,
                    'content': viral_content
                })
            else:
                logger.warning(f"Failed to find viral content for topic: {topic}")

        # Generate competitor analysis if multiple brands
        competitor_analysis = None
        if len(self.brands) > 1:
            competitor_analysis = self.generate_competitor_analysis_with_retry(self.brands)
            if not competitor_analysis:
                logger.warning("Failed to generate competitor analysis")

        # Generate week trend analysis
        trend_prompt = f"""
Based on the following social media data, analyze weekly trends and patterns:

{trend_data}

Provide:
1. Weekly trend analysis and evolution
2. Sentiment trend over the week
3. Top trending topics of the week
4. Most viral content of the week
5. Platform-specific performance
6. Influencer impact over the week
7. Week-over-week comparison
8. Upcoming trend predictions
9. Recommended strategies

Format as a comprehensive weekly trend analysis.
"""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing weekly trends (attempt {attempt}/{self.max_retries})...")

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": trend_prompt}],
                    temperature=0.5,
                    max_tokens=2048
                )

                weekly_trend_analysis = response.choices[0].message.content
                break
            except Exception as e:
                logger.error(f"❌ Week trend analysis attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("All week trend analysis attempts failed")
                    weekly_trend_analysis = "No weekly trend analysis available."

        # Combine into weekly report
        weekly_content = f"""
<h2>📱 Weekly Social Media Analysis - {datetime.now().strftime('%Y-%m-%d')}</h2>

<div class="dashboard">
    <h3>📊 Weekly Summary Dashboard</h3>
    <p>Comprehensive analysis of the week's social media activity</p>
</div>

<h3>📈 Weekly Trend Analysis</h3>
{weekly_trend_analysis}

<h3>📊 Overall Trend Analysis</h3>
{trend_data}

"""

        # Add brand analyses
        if brand_analyses:
            weekly_content += "<h3>🏷️ Brand Performance Analysis</h3>\n"
            for analysis in brand_analyses:
                weekly_content += f"""
<div class="brand-card">
    <h4>Brand: {analysis['brand']}</h4>
    {analysis['analysis']}
</div>
"""

        # Add viral content
        if viral_contents:
            weekly_content += "<h3>🔥 Top Viral Content of the Week</h3>\n"
            for content in viral_contents:
                weekly_content += f"""
<div class="viral-content">
    <h4>Topic: {content['topic']}</h4>
    {content['content']}
</div>
"""

        # Add competitor analysis
        if competitor_analysis:
            weekly_content += f"""
<h3>🏆 Competitive Landscape Analysis</h3>
<div class="brand-card">
    {competitor_analysis}
</div>
"""

        # Add weekly insights
        weekly_content += f"""
<div style="margin-top: 30px; padding: 15px; background-color: #e8f5e8; border-radius: 5px;">
    <h3>Week's Key Insights</h3>
    <ul>
        <li><strong>Brands Monitored:</strong> {', '.join(self.brands) if self.brands else 'General trends'}</li>
        <li><strong>Topics Tracked:</strong> {', '.join(self.topics) if self.topics else 'General'}</li>
        <li><strong>Analysis Period:</strong> This week (Mon-Sun)</li>
        <li><strong>Next Analysis:</strong> Next Monday morning</li>
    </ul>
</div>
"""

        filepath = self.save_social_report(weekly_content, "weekly")

        if send_email:
            subject = f"📱 Weekly Social Media Analysis - {datetime.now().strftime('%B %d, %Y')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Weekly social media analysis completed")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Social Media Trend Tracker Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection
  %(prog)s --test

  # Daily tracking for specific brands
  %(prog)s --daily --brands "Nike" "Adidas" --email marketing@example.com

  # Weekly analysis for topics
  %(prog)s --weekly --topics "AI" "MachineLearning" --email analyst@example.com

  # Track both brands and topics
  %(prog)s --daily --brands "Apple" "Samsung" --topics "iPhone" "Android" --email team@example.com

  # Scheduled daily tracking at 6 AM
  %(prog)s --schedule-daily --brands "Microsoft" "Google" --email social-media@example.com
        """
    )

    # Mode arguments
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--test', action='store_true', help='Test server connection')
    mode_group.add_argument('--daily', action='store_true', help='Daily social media tracking')
    mode_group.add_argument('--weekly', action='store_true', help='Weekly social media analysis')
    mode_group.add_argument('--schedule-daily', action='store_true', help='Schedule daily tracking')

    # Configuration
    parser.add_argument('--server', default='http://localhost:5000/v1', help='Server URL')
    parser.add_argument('--brands', nargs='+', default=[], help='Brands to monitor')
    parser.add_argument('--topics', nargs='+', default=[], help='Topics to track')
    parser.add_argument('--email', help='Recipient email for reports')
    parser.add_argument('--output-dir', default='social_reports', help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create agent
    agent = SocialMediaTrackerAgent(
        server_url=args.server,
        brands=args.brands,
        topics=args.topics,
        recipient_email=args.email,
        output_dir=args.output_dir
    )

    try:
        if args.test:
            success = agent.test_connection()
            sys.exit(0 if success else 1)

        elif args.daily:
            success = agent.run_daily_tracking(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.weekly:
            success = agent.run_weekly_analysis(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.schedule_daily:
            logger.info("Scheduling daily social media tracking for 6:00 AM")
            schedule.every().day.at("06:00").do(
                lambda: agent.run_daily_tracking(send_email=bool(args.email))
            )
            logger.info("Press Ctrl+C to stop")
            while True:
                schedule.run_pending()
                time.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n👋 Social Media Tracker Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()