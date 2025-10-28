#!/usr/bin/env python3
"""
Business Intelligence Automation Agent
======================================

Automated business intelligence and strategic decision support agent.

Features:
- Comprehensive market research across multiple sources
- Financial analysis of companies and sectors
- Competitor analysis and positioning
- Document analysis and insight extraction
- Data visualization and chart generation
- Executive summary creation and PDF generation
- Automated email delivery of reports

Author: Agentic-RAG Development Team
Version: 1.0.3
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import json
import os
import re

# Add the parent directory to the path so we can import common utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openai
import schedule

# Import common utilities
from common.agent_utils import (
    create_openai_client,
    test_server_connection,
    execute_with_retry,
    setup_agent_logging,
    create_output_directory
)
from common.report_utils import (
    create_html_report,
    save_html_report,
    send_email_report
)


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


class BusinessIntelligenceAgent:
    """Automated business intelligence and strategic decision support agent."""

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        company: Optional[str] = None,
        competitors: List[str] = None,
        sectors: List[str] = None,
        research_topics: List[str] = None,
        document_paths: List[str] = None,
        recipient_email: Optional[str] = None,
        output_dir: str = "business_reports",
        max_retries: int = 3
    ):
        """
        Initialize the business intelligence agent.

        Args:
            server_url: URL of the Agentic-RAG server
            company: Target company to analyze
            competitors: List of competitor companies
            sectors: Industry sectors to monitor
            research_topics: Specific topics for deep research
            document_paths: Paths to company documents to analyze
            recipient_email: Email for intelligence reports
            output_dir: Directory to save business intelligence reports
            max_retries: Maximum retry attempts on failure
        """
        self.server_url = server_url
        self.company = company
        self.competitors = competitors or []
        self.sectors = sectors or []
        self.research_topics = research_topics or []
        self.document_paths = document_paths or []
        self.recipient_email = recipient_email
        self.output_dir = Path(output_dir)
        self.max_retries = max_retries

        # Create output directory
        self.output_dir = create_output_directory(output_dir)

        # Initialize OpenAI client
        self.client = create_openai_client(server_url)

        # Initialize logger
        self.logger = setup_agent_logging(
            "business_intelligence",
            log_file="business_intelligence.log"
        )

        # Combine all targets for monitoring
        all_targets = [self.company] if self.company else []
        all_targets.extend(self.competitors)
        all_targets.extend(self.sectors)
        all_targets.extend(self.research_topics)
        
        self.logger.info(f"BusinessIntelligenceAgent initialized for: {', '.join(filter(None, all_targets))}")

    def test_connection(self) -> bool:
        """Test connection to the server."""
        return test_server_connection(self.client, self.logger)

    def research_market_trends(self) -> Optional[str]:
        """
        Research market trends.

        Returns:
            Market trend analysis as string or None if failed
        """
        # Build research targets
        targets = []
        if self.company:
            targets.append(self.company)
        targets.extend(self.competitors)
        targets.extend(self.sectors)
        targets.extend(self.research_topics)
        
        targets_str = ", ".join([t for t in targets if t]) if targets else "general market trends"
        
        prompt = f"""
Please research current market trends for: {targets_str}

Use multiple tools to gather comprehensive market intelligence:
1. Use get_news_summaries to find the latest news about these companies/sectors
2. Use search_web to gather additional market insights
3. Use published_papers_search to find academic research
4. Use analytical_visualizer to create relevant charts if possible

Provide a comprehensive market research report including:

1. Current market conditions
2. Emerging trends and opportunities
3. Key challenges and threats
4. Market size and growth projections
5. Technology adoption trends
6. Regulatory impacts
7. Consumer behavior changes
8. Competitive landscape overview

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

        return execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.4,  # Balanced for analysis
            max_tokens=4096,
            logger=self.logger,
            task_description="Market research"
        )

    def analyze_company_financials(self, company: str) -> Optional[str]:
        """
        Analyze company financials.

        Args:
            company: Company to analyze

        Returns:
            Financial analysis as string or None if failed
        """
        prompt = f"""
Please perform a comprehensive financial analysis for {company}.

Use the comprehensive_stock_analyzer and get_stock_and_company_data tools to gather:

1. Current stock price and performance
2. Financial ratios and metrics
3. Revenue and earnings trends
4. Market capitalization and valuation
5. Debt-to-equity and other key ratios
6. Competitive positioning in the market
7. Quarterly and annual performance
8. Analyst ratings and target prices
9. Risk factors and concerns

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
   - <div class="high">, <div class="medium">, <div class="info"> for styled sections
6. Start directly with content (e.g., <h2>Financial Overview</h2><p>Content here...</p>)
"""

        return execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.3,  # Low temperature for factual financial data
            max_tokens=4096,
            logger=self.logger,
            task_description=f"Financial analysis for {company}"
        )

    def validate_document_paths(self) -> List[str]:
        """
        Validate that document paths exist.

        Returns:
            List of valid document paths
        """
        valid_paths = []
        for path in self.document_paths:
            p = Path(path)
            if p.exists() and p.is_file():
                valid_paths.append(path)
                self.logger.info(f"✅ Document found: {path}")
            else:
                self.logger.warning(f"❌ Document not found or not a file: {path}")
        return valid_paths

    def analyze_documents(self) -> Optional[str]:
        """
        Analyze company documents.

        Returns:
            Document analysis as string or None if failed
        """
        if not self.document_paths:
            return "No company documents provided for analysis."

        # Validate document paths
        valid_paths = self.validate_document_paths()
        if not valid_paths:
            return f"⚠️ No valid document paths found. Checked {len(self.document_paths)} path(s)."

        doc_paths_str = "\n".join([f"- {path}" for path in valid_paths])
        
        prompt = f"""
Please analyze the following company documents:

{doc_paths_str}

Use the document_search tool to thoroughly analyze these documents. Then provide:

1. Executive summary of key information
2. Financial insights from financial reports
3. Strategic initiatives and plans
4. Risk factors and concerns
5. Competitive positioning insights
6. Future projections and goals
7. Management commentary analysis
8. Compliance and regulatory considerations

For each document, provide:
- Document type and purpose
- Key findings and insights
- Strategic implications
- Action items or recommendations

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
6. Start directly with content (e.g., <h2>Document Analysis</h2><p>Content here...</p>)
"""

        return execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.4,  # Balanced for document analysis
            max_tokens=4096,
            logger=self.logger,
            task_description="Document analysis"
        )

    def analyze_competitors(self) -> Optional[str]:
        """
        Analyze competitors.

        Returns:
            Competitor analysis as string or None if failed
        """
        if not self.competitors:
            return "No competitors provided for analysis."

        competitors_str = ", ".join(self.competitors)
        
        prompt = f"""
Please perform a comprehensive competitor analysis for: {competitors_str}

Use multiple tools to gather competitive intelligence:
1. Use search_web to find recent news and developments
2. Use get_news_summaries for latest updates
3. Use get_stock_and_company_data for financial comparisons
4. Use analytical_visualizer to create comparison charts

Provide a detailed competitor analysis including:

1. Market share and positioning
2. Financial performance comparison
3. Product/service offerings comparison
4. Strategic initiatives and roadmaps
5. Strengths and weaknesses
6. Recent developments and news
7. Market capitalization comparison
8. Growth strategies
9. Competitive advantages/disadvantages

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
6. Start directly with content (e.g., <h2>Competitor Analysis</h2><p>Content here...</p>)
"""

        return execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.5,  # Higher for comparative analysis
            max_tokens=4096,
            logger=self.logger,
            task_description="Competitor analysis"
        )

    def generate_strategy_recommendations(self, market_data: str, financial_data: str) -> Optional[str]:
        """
        Generate strategic recommendations.

        Args:
            market_data: Market research data
            financial_data: Financial analysis data

        Returns:
            Strategy recommendations as string or None if failed
        """
        prompt = f"""
Based on the following market research and financial analysis data, generate comprehensive strategic recommendations:

MARKET RESEARCH DATA:
{market_data}

FINANCIAL ANALYSIS DATA:
{financial_data}

Provide strategic recommendations including:

1. Market opportunity assessment
2. Competitive positioning strategy
3. Investment priorities
4. Risk mitigation strategies
5. Growth opportunities
6. Market entry strategies
7. Partnership opportunities
8. Technology adoption recommendations
9. Resource allocation suggestions
10. Timeline and roadmap

Focus on actionable, data-driven recommendations that consider:
- Current market conditions
- Financial constraints and opportunities
- Competitive landscape
- Regulatory environment
- Technology trends
- Consumer behavior changes

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
   - <div class="priority-1">, <div class="priority-2">, etc. for priority levels
6. Start directly with content (e.g., <h2>Strategic Recommendations</h2><p>Content here...</p>)
"""

        return execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.6,  # Higher for strategic thinking
            max_tokens=4096,
            logger=self.logger,
            task_description="Strategy recommendations"
        )

    def create_business_dashboard(self, analysis_data: str) -> Optional[str]:
        """
        Create business intelligence dashboard.

        Args:
            analysis_data: Complete analysis data

        Returns:
            Dashboard content as string or None if failed
        """
        prompt = f"""
Based on the following business analysis data, create an executive business intelligence dashboard:

{analysis_data}

Create a comprehensive dashboard with:
1. Key Performance Indicators (KPIs) summary
2. Market trends visualization
3. Financial metrics at a glance
4. Competitive positioning indicators
5. Risk assessment matrix
6. Growth opportunity indicators
7. Strategic initiative progress
8. Timeline and milestone tracking

CRITICAL FORMATTING REQUIREMENTS:
1. OUTPUT MUST BE HTML CONTENT ONLY - NO markdown syntax anywhere
2. DO NOT wrap output in code blocks (NO ```html or ``` markers)
3. DO NOT include <!DOCTYPE>, <html>, <head>, or <body> tags
4. Generate HTML CONTENT FRAGMENTS that will be inserted into an existing HTML document
5. Use semantic HTML tags:
   - <h2>, <h3>, <h4> for headings (NOT # ## ###)
   - <p> for paragraphs
   - <ul><li> and <ol><li> for lists (NOT - or *)
   - <table><tr><th><td> for KPI tables (NOT | pipes |)
   - <strong> and <em> for emphasis (NOT ** or *)
   - <div class="critical">, <div class="high">, <div class="medium"> for color-coded sections
6. Start directly with content (e.g., <h2>Executive Dashboard</h2><table>...</table>)
"""

        return execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.5,  # Balanced for dashboard creation
            max_tokens=2048,
            logger=self.logger,
            task_description="Business dashboard creation"
        )

    def run_strategic_analysis(self, send_email: bool = False) -> bool:
        """Run comprehensive business intelligence and strategic analysis."""
        self.logger.info("=" * 60)
        self.logger.info("Starting comprehensive business intelligence analysis...")
        self.logger.info("=" * 60)

        total_steps = 6

        # Step 1: Research market trends
        self.logger.info(f"🔍 Step 1/{total_steps}: Researching market trends...")
        market_research = self.research_market_trends()
        if not market_research:
            self.logger.error("Failed to get market research")
            return False
        market_research = clean_html_response(market_research)

        # Step 2: Analyze target company financials (if specified)
        company_analysis = None
        if self.company:
            self.logger.info(f"💼 Step 2/{total_steps}: Analyzing {self.company} financials...")
            company_analysis = self.analyze_company_financials(self.company)
            if not company_analysis:
                self.logger.warning(f"Failed to analyze {self.company} financials")
                company_analysis = f"No financial analysis available for {self.company}."
            else:
                company_analysis = clean_html_response(company_analysis)

        # Step 3: Analyze documents
        self.logger.info(f"📄 Step 3/{total_steps}: Analyzing company documents...")
        document_analysis = self.analyze_documents()
        if not document_analysis:
            self.logger.warning("Failed to analyze documents")
            document_analysis = "No document analysis performed."
        else:
            document_analysis = clean_html_response(document_analysis)

        # Step 4: Analyze competitors
        self.logger.info(f"🏆 Step 4/{total_steps}: Analyzing competitors...")
        competitor_analysis = self.analyze_competitors()
        if not competitor_analysis:
            self.logger.warning("Failed to analyze competitors")
            competitor_analysis = "No competitor analysis performed."
        else:
            competitor_analysis = clean_html_response(competitor_analysis)

        # Step 5: Create business dashboard
        self.logger.info(f"📊 Step 5/{total_steps}: Creating business intelligence dashboard...")
        dashboard_content = self.create_business_dashboard(
            f"MARKET RESEARCH:\n{market_research}\n\nCOMPANY ANALYSIS:\n{company_analysis or ''}\n\nDOCUMENT ANALYSIS:\n{document_analysis}\n\nCOMPETITOR ANALYSIS:\n{competitor_analysis}"
        )
        if not dashboard_content:
            self.logger.warning("Failed to create dashboard")
            dashboard_content = "No dashboard created."
        else:
            dashboard_content = clean_html_response(dashboard_content)

        # Step 6: Generate strategy recommendations
        self.logger.info(f"🎯 Step 6/{total_steps}: Generating strategy recommendations...")
        strategy_recommendations = self.generate_strategy_recommendations(
            market_research,
            company_analysis or ""
        )
        if not strategy_recommendations:
            self.logger.warning("Failed to generate strategy recommendations")
            strategy_recommendations = "No strategy recommendations generated."
        else:
            strategy_recommendations = clean_html_response(strategy_recommendations)

        # Combine all into comprehensive report
        report_content = f"""
<div class="dashboard">
    <h2>💼 Business Intelligence Dashboard</h2>
    {dashboard_content}
</div>

<h2>🔍 Market Research Analysis</h2>
{market_research}

"""
        if company_analysis:
            report_content += f"""
<h2>💼 Company Financial Analysis - {self.company or 'N/A'}</h2>
<div class="company-card">
    {company_analysis}
</div>
"""

        report_content += f"""
<h2>📄 Document Analysis</h2>
{document_analysis}

<h2>🏆 Competitor Analysis</h2>
{competitor_analysis}

<h2>🎯 Strategic Recommendations</h2>
<div class="recommendation">
    {strategy_recommendations}
</div>

<div style="margin-top: 30px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
    <h3>Intelligence Summary</h3>
    <ul>
        <li><strong>Target Company:</strong> {self.company or 'Not specified'}</li>
        <li><strong>Competitors Analyzed:</strong> {', '.join(self.competitors) if self.competitors else 'None'}</li>
        <li><strong>Sectors Monitored:</strong> {', '.join(self.sectors) if self.sectors else 'General'}</li>
        <li><strong>Research Topics:</strong> {', '.join(self.research_topics) if self.research_topics else 'General'}</li>
        <li><strong>Documents Analyzed:</strong> {len(self.document_paths)} files</li>
        <li><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</li>
        <li><strong>Generated:</strong> {datetime.now().strftime('%H:%M:%S')}</li>
    </ul>
</div>
"""

        # Create and save HTML report
        html_report = create_html_report(
            f"Business Intelligence Report - {self.company or 'Strategic Analysis'}",
            report_content,
            subtitle=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        html_filepath = save_html_report(
            html_report,
            self.output_dir,
            logger=self.logger
        )

        # Send email if requested
        if send_email and self.recipient_email:
            email_body = f"Please find attached your comprehensive business intelligence report for {self.company or 'strategic analysis'} with market analysis, financial insights, and strategic recommendations."
            send_email_report(
                self.client,
                self.recipient_email,
                f"💼 Business Intelligence Report - {self.company or 'Strategic Analysis'} - {datetime.now().strftime('%B %d, %Y')}",
                email_body,
                html_filepath,
                logger=self.logger
            )

        self.logger.info("✅ Comprehensive business intelligence analysis completed")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Business Intelligence Automation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection
  %(prog)s --test

  # Strategic analysis for a company
  %(prog)s --strategic --company "Tesla" --competitors "Ford" "GM" "Nio" --sectors "electric vehicles" "renewable energy"

  # Comprehensive analysis with documents and email
  %(prog)s --strategic --company "Apple" --topics "iPhone" "AI" --docs /path/to/quarterly_report.pdf --email analyst@example.com

  # Scheduled weekly analysis
  %(prog)s --schedule-weekly --company "Microsoft" --competitors "Google" "Amazon" --email executive@example.com
        """
    )

    # Mode arguments
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--test', action='store_true', help='Test server connection')
    mode_group.add_argument('--strategic', action='store_true', help='Run comprehensive strategic analysis')
    mode_group.add_argument('--schedule-weekly', action='store_true', help='Schedule weekly analysis')

    # Configuration
    parser.add_argument('--server', default='http://localhost:5000/v1', help='Server URL')
    parser.add_argument('--company', help='Target company to analyze')
    parser.add_argument('--competitors', nargs='+', default=[], help='Competitor companies')
    parser.add_argument('--sectors', nargs='+', default=[], help='Industry sectors to monitor')
    parser.add_argument('--topics', nargs='+', default=[], dest='research_topics', help='Research topics')
    parser.add_argument('--docs', nargs='+', default=[], dest='document_paths', help='Company document paths to analyze')
    parser.add_argument('--email', help='Recipient email for reports')
    parser.add_argument('--output-dir', default='business_reports', help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Initialize agent
    agent = BusinessIntelligenceAgent(
        server_url=args.server,
        company=args.company,
        competitors=args.competitors,
        sectors=args.sectors,
        research_topics=args.research_topics,
        document_paths=args.document_paths,
        recipient_email=args.email,
        output_dir=args.output_dir
    )

    if args.verbose:
        agent.logger.setLevel(logging.DEBUG)

    try:
        if args.test:
            success = agent.test_connection()
            sys.exit(0 if success else 1)

        elif args.strategic:
            success = agent.run_strategic_analysis(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.schedule_weekly:
            agent.logger.info("Scheduling weekly business intelligence analysis for Monday 9:00 AM")
            schedule.every().monday.at("09:00").do(
                lambda: agent.run_strategic_analysis(send_email=bool(args.email))
            )
            agent.logger.info("Press Ctrl+C to stop")
            while True:
                schedule.run_pending()
                time.sleep(60)

    except KeyboardInterrupt:
        agent.logger.info("\n👋 Business Intelligence Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        agent.logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()