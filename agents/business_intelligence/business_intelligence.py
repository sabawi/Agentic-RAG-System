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
Version: 1.0.5
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
# Import context detection and citation formatting (v1.0.5 enhancements)
from common.context_detector import AnalysisContext
from common.citation_formatter import CitationFormatter


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

        # Initialize context detector (v1.0.5 enhancement)
        self.context = AnalysisContext(
            company=company,
            competitors=competitors,
            sectors=sectors,
            research_topics=research_topics
        )

        # Initialize citation formatter (v1.0.5 enhancement)
        self.citation_formatter = CitationFormatter()

        # Combine all targets for monitoring
        all_targets = [self.company] if self.company else []
        all_targets.extend(self.competitors)
        all_targets.extend(self.sectors)
        all_targets.extend(self.research_topics)

        self.logger.info(f"BusinessIntelligenceAgent initialized for: {', '.join(filter(None, all_targets))}")
        self.logger.info(f"Context detected: {self.context.context_type}")

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

IMPORTANT: Focus on DATA and ANALYSIS with citations. Do NOT create generic placeholder visualizations.

Provide a comprehensive market research report including:

1. Current market conditions
2. Emerging trends and opportunities
3. Key challenges and threats
4. Market size and growth projections
5. Technology adoption trends
6. Regulatory impacts
7. Consumer behavior changes
8. Competitive landscape overview

🚨 MANDATORY CITATION REQUIREMENT (v1.0.5 Enhancement) 🚨
EVERY SINGLE data point, statistic, projection, or claim MUST include an inline citation marker.
This is NOT optional - failure to include citations will result in rejection.

REQUIRED FORMAT (use HTML exactly as shown):
- News articles: <span class="citation">[Source: NEWS_SOURCE, "ARTICLE_TITLE", DATE]</span>
- Research papers: <span class="citation">[Source: AUTHORS, "PAPER_TITLE", VENUE, YEAR]</span>
- Web sources: <span class="citation">[Source: DOMAIN, "PAGE_TITLE", accessed DATE]</span>
- Market data: <span class="citation">[Source: DATA_PROVIDER, as of DATE]</span>

REQUIRED EXAMPLE (notice citation marker immediately after data):
<p>The EV market is projected to grow at 23% CAGR <span class="citation">[Source: Bloomberg, "Electric Vehicle Market Outlook", 2024-10-15]</span></p>
<p>Global smartphone sales reached 1.2B units <span class="citation">[Source: IDC, "Worldwide Quarterly Mobile Phone Tracker", Q3 2024]</span></p>

VERIFICATION CHECKLIST - Before submitting, ensure:
✓ Every numerical value has inline <span class="citation">
✓ Every market projection has inline <span class="citation">
✓ Every trend claim has inline <span class="citation">
✓ Every statistic has inline <span class="citation">
✓ Citation appears IMMEDIATELY after the data value (not end of paragraph)

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

🚨 MANDATORY CITATION REQUIREMENT (v1.0.5 Enhancement) 🚨
EVERY SINGLE numerical data point, statistic, or factual claim MUST include an inline citation marker.
This is NOT optional - failure to include citations will result in rejection.

REQUIRED FORMAT (use HTML exactly as shown):
- SEC filings: <span class="citation">[Source: {company} 10-K/10-Q filed DATE, p.XX]</span>
- Market data: <span class="citation">[Source: Yahoo Finance, as of DATE]</span>
- Calculated metrics: <span class="citation">[Calculated: FORMULA (Data from: SOURCE)]</span>

REQUIRED EXAMPLE (notice citation marker immediately after data):
<p>Revenue: $391.04B <span class="citation">[Source: {company} 10-K FY2024, filed 2024-10-31, p.24]</span></p>
<p>P/E Ratio: 28.5 <span class="citation">[Source: Yahoo Finance, as of 2024-11-01]</span></p>

VERIFICATION CHECKLIST - Before submitting, ensure:
✓ Every dollar amount has inline <span class="citation">
✓ Every percentage has inline <span class="citation">
✓ Every ratio has inline <span class="citation">
✓ Every claim has inline <span class="citation">
✓ Citation appears IMMEDIATELY after the data value (not end of paragraph)

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

    def fetch_stock_data_for_companies(self, companies: List[str]) -> Optional[str]:
        """
        Fetch stock data for multiple companies.

        Args:
            companies: List of company names or ticker symbols

        Returns:
            Dictionary with company data or None if failed
        """
        companies_str = ", ".join(companies)

        prompt = f"""
Please fetch current stock and company data for the following companies: {companies_str}

Use the get_stock_and_company_data tool for EACH company to get:
- Current stock price
- Market capitalization
- 52-week high/low
- P/E ratio
- Recent price change percentage

Format the response as a structured summary with each company's data clearly listed.
Include the EXACT numerical values returned by the tool.

Example format:
Company: Tesla
Stock Price: $250.50
Market Cap: $795.2 billion
52-Week Range: $101.81 - $278.98
P/E Ratio: 79.45
Price Change: +2.5%

[Repeat for each company]
"""

        response = execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.1,  # Very low for factual data retrieval
            max_tokens=2048,
            logger=self.logger,
            task_description="Stock data fetching"
        )

        if response:
            self.logger.info(f"Fetched stock data for {len(companies)} companies")

        return response

    def analyze_competitors(self) -> Optional[str]:
        """
        Analyze competitors with structured data fetching and visualization.

        Returns:
            Competitor analysis as string or None if failed
        """
        if not self.competitors:
            return "No competitors provided for analysis."

        # Phase 1: Fetch stock data for all competitors first
        self.logger.info(f"Phase 1: Fetching stock data for competitors: {', '.join(self.competitors)}")

        # Include primary company if specified
        companies_to_analyze = []
        if self.company:
            companies_to_analyze.append(self.company)
        companies_to_analyze.extend(self.competitors)

        stock_data = self.fetch_stock_data_for_companies(companies_to_analyze)

        if not stock_data:
            self.logger.warning("Failed to fetch stock data, proceeding without structured data")
            stock_data = "Stock data unavailable"

        # Phase 2: Create visualization with the fetched data
        self.logger.info("Phase 2: Creating visualizations with real stock data")
        visualization_prompt = f"""
Using the following REAL stock data, create a stock price comparison chart:

{stock_data}

MANDATORY REQUIREMENTS:
1. Create a professional bar chart or line chart comparing current stock prices and market caps
2. Use the EXACT values from the data above - NO placeholder or estimated values
3. Include data value annotations ON EACH BAR/POINT (show the actual numbers)
4. Include proper labels, a legend, and a descriptive title
5. Add citation below chart: <p style="font-size: 11px; color: #666; font-style: italic;">[Source: Yahoo Finance, as of {datetime.now().strftime('%Y-%m-%d')}]</p>

VERIFICATION: Ensure chart includes numerical annotations and citation marker.
"""

        visualization_result = execute_with_retry(
            self.client,
            f"analytical_visualizer: {visualization_prompt}",
            max_retries=2,
            temperature=0.3,
            max_tokens=2048,
            logger=self.logger,
            task_description="Competitor visualization"
        )

        # Phase 3: Comprehensive competitor analysis
        self.logger.info("Phase 3: Generating comprehensive competitor analysis")
        competitors_str = ", ".join(self.competitors)

        analysis_prompt = f"""
Please perform a comprehensive competitor analysis for: {competitors_str}

REAL STOCK DATA ALREADY FETCHED:
{stock_data}

Use this data and gather additional intelligence:
1. Use search_web to find recent news and developments
2. Use get_news_summaries for latest updates
3. Reference the stock data provided above for financial comparisons

Provide a detailed competitor analysis including:

1. Market share and positioning
2. Financial performance comparison (using the data above)
3. Product/service offerings comparison
4. Strategic initiatives and roadmaps
5. Strengths and weaknesses
6. Recent developments and news
7. Market capitalization comparison (using data above)
8. Growth strategies
9. Competitive advantages/disadvantages

{f"VISUALIZATION CREATED:{chr(10)}{visualization_result}" if visualization_result else ""}

🚨 MANDATORY CITATION REQUIREMENT (v1.0.5 Enhancement) 🚨
EVERY SINGLE data point, statistic, claim, or competitive intelligence MUST include an inline citation marker.
This is NOT optional - failure to include citations will result in rejection.

REQUIRED FORMAT (use HTML exactly as shown):
- Stock data: <span class="citation">[Source: Yahoo Finance, as of {datetime.now().strftime('%Y-%m-%d')}]</span>
- News developments: <span class="citation">[Source: NEWS_SOURCE, "ARTICLE_TITLE", DATE]</span>
- Web research: <span class="citation">[Source: DOMAIN, "PAGE_TITLE", accessed DATE]</span>
- Calculated comparisons: <span class="citation">[Calculated from: DATA_SOURCE]</span>

REQUIRED EXAMPLE (notice citation marker immediately after data):
<p>{competitors_str.split(',')[0] if competitors_str else 'Company'} has a P/E ratio of 28.5 <span class="citation">[Source: Yahoo Finance, as of {datetime.now().strftime('%Y-%m-%d')}]</span>, compared to industry average of 24.3 <span class="citation">[Calculated from: Yahoo Finance sector data]</span></p>

For comparison tables, add citation below table:
<p style="font-size: 11px; color: #666; font-style: italic; margin-top: 5px;">[Source: Yahoo Finance, as of {datetime.now().strftime('%Y-%m-%d')}]</p>

VERIFICATION CHECKLIST - Before submitting, ensure:
✓ Every numerical value has inline <span class="citation">
✓ Every claim about competitor has inline <span class="citation">
✓ Every comparison has inline <span class="citation">
✓ Citation appears IMMEDIATELY after the data value (not end of paragraph)

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
7. Include the visualization if it was created above
"""

        return execute_with_retry(
            self.client,
            analysis_prompt,
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
2. Financial metrics at a glance
3. Competitive positioning indicators
4. Risk assessment matrix
5. Growth opportunity indicators
6. Strategic initiative progress
7. Timeline and milestone tracking

IMPORTANT: Use ONLY data from the analysis provided above. DO NOT create placeholder or generic visualizations.

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

    # ========================================================================
    # NEW METHODS - v1.0.5 Enhancements (Context-Aware Intelligence)
    # ========================================================================

    def create_peer_comparison_table(self) -> Optional[str]:
        """
        Create peer comparison table with financial metrics.

        Only called when context indicates company analysis with competitors.
        Uses existing fetch_stock_data_for_companies() but formats as HTML table.

        Returns:
            HTML table with peer comparison or None if not applicable
        """
        # Check if peer comparison is appropriate for this context
        if not self.context.should_include_peer_comparison():
            self.logger.info("Peer comparison not applicable for this analysis context")
            return None

        self.logger.info("Creating peer comparison table...")

        # Use existing data fetching method
        companies = [self.company] + self.competitors
        stock_data = self.fetch_stock_data_for_companies(companies)

        if not stock_data:
            self.logger.warning("Failed to fetch stock data for peer comparison")
            return None

        # Create formatted comparison table with citations
        prompt = f"""
Using the following stock data:
{stock_data}

Create an HTML comparison table comparing these companies: {', '.join(companies)}

Include these metrics in columns:
- P/E Ratio
- Market Cap ($ Billions)
- Revenue TTM ($ Billions)
- Net Margin (%)
- ROE (%)
- Debt/Equity Ratio

Format as:
<table>
<tr>
  <th>Metric</th>
  <th>{companies[0]}</th>
  {' '.join([f'<th>{c}</th>' for c in companies[1:]])}
</tr>
<tr>
  <td>P/E Ratio</td>
  <td>32.5</td>
  ...
</tr>
</table>

CRITICAL:
1. Use EXACT values from the stock data above
2. Add citation below table:
   <p style="font-size: 11px; color: #666; font-style: italic; margin-top: 5px;">
   [Source: Yahoo Finance, as of {datetime.now().strftime('%Y-%m-%d')}]
   </p>
3. Highlight the primary company ({companies[0]}) with bold text
4. Use HTML only, no markdown
"""

        return execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.2,  # Low temperature for factual comparison
            max_tokens=2048,
            logger=self.logger,
            task_description="Peer comparison table creation"
        )

    def generate_investment_recommendation(self, financial_data: str) -> Optional[str]:
        """
        Generate investment recommendation (Buy/Hold/Sell) with reasoning.

        Only called when context indicates public company analysis.
        Provides scoring, reasoning, and disclaimers.

        Args:
            financial_data: Financial analysis data to base recommendation on

        Returns:
            HTML-formatted investment recommendation or None if not applicable
        """
        # Check if investment recommendation is appropriate for this context
        if not self.context.should_include_investment_recommendation():
            self.logger.info("Investment recommendation not applicable (not a public company)")
            return None

        self.logger.info("Generating investment recommendation...")

        prompt = f"""
Based on the following financial analysis for {self.company}:
{financial_data}

Generate a comprehensive investment recommendation with:

1. **Rating**: BUY, HOLD, or SELL
2. **Overall Score**: 0-100 (weighted composite)
3. **Reasoning**: 2-3 sentences explaining the rating
4. **Score Breakdown**:
   - Valuation Score (0-100): Based on P/E, P/S, P/B ratios vs peers
   - Growth Score (0-100): Based on revenue growth, EPS growth
   - Profitability Score (0-100): Based on ROE, margins, returns
   - Financial Health Score (0-100): Based on debt levels, cash flow, liquidity

5. **Key Factors**: 3-5 bullet points of critical factors influencing the rating

Format as HTML:
<div class="recommendation-box" style="border-left: 5px solid #COLOR; padding: 20px; margin: 20px 0; background-color: #f8f9fa;">
    <h3>Investment Recommendation: <strong>RATING</strong></h3>
    <p><strong>Overall Score:</strong> XX/100</p>
    <p><strong>Reasoning:</strong> [2-3 sentences]</p>

    <h4>Score Breakdown:</h4>
    <ul>
        <li><strong>Valuation:</strong> XX/100 - [brief explanation]</li>
        <li><strong>Growth:</strong> XX/100 - [brief explanation]</li>
        <li><strong>Profitability:</strong> XX/100 - [brief explanation]</li>
        <li><strong>Financial Health:</strong> XX/100 - [brief explanation]</li>
    </ul>

    <h4>Key Factors:</h4>
    <ul>
        <li>[Factor 1]</li>
        <li>[Factor 2]</li>
        <li>[Factor 3]</li>
    </ul>

    <p style="font-size: 11px; color: #666; font-style: italic; margin-top: 15px; padding: 10px; background-color: #fff3cd; border-left: 3px solid #ffc107;">
    <strong>Disclaimer:</strong> This analysis is for informational purposes only and does not constitute financial advice.
    Consult a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.
    Analysis based on data as of {datetime.now().strftime('%Y-%m-%d')}.
    </p>
</div>

CRITICAL:
1. Use #28a745 (green) for BUY, #ffc107 (yellow) for HOLD, #dc3545 (red) for SELL
2. Base scores on ACTUAL data from the financial analysis above
3. Be objective and balanced in reasoning
4. HTML only, no markdown
"""

        return execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.3,  # Low-medium for balanced analysis
            max_tokens=2048,
            logger=self.logger,
            task_description="Investment recommendation generation"
        )

    def collect_data_sources(self, sections_data: Dict[str, str]) -> str:
        """
        Collect and format all data sources used in the report.

        Scans all report sections for citations and compiles them into
        a comprehensive data sources section.

        Args:
            sections_data: Dictionary of section names and content

        Returns:
            HTML-formatted data sources section
        """
        self.logger.info("Collecting data sources citations...")

        # Combine all section content for analysis
        combined_content = '\n\n'.join([
            f"SECTION: {section_name}\n{content}"
            for section_name, content in sections_data.items()
            if content  # Only include non-empty sections
        ])

        prompt = f"""
Analyze the following report sections and extract all data sources mentioned or implied:

{combined_content[:10000]}  # Limit to avoid token overflow

Create a comprehensive data sources section listing all sources used, organized by category:

1. **Official Regulatory Filings** (if SEC filings were mentioned)
   - List each filing with type, date, and link

2. **News Sources** (if news articles were mentioned)
   - List news sources with article titles and dates
   - Limit to top 10 most significant

3. **Academic Research** (if research papers were mentioned)
   - List papers with authors, title, venue, year

4. **Market Data Providers** (if stock/financial data was used)
   - List providers like Yahoo Finance, Bloomberg, etc.

5. **Web Sources** (if web research was conducted)
   - List key websites referenced

Format as HTML:
<h2>📚 Data Sources & Citations</h2>
<div class="data-sources">
    <p>This report is based on data from the following verified sources:</p>

    <h3>Official Regulatory Filings</h3>
    <ul>
        <li><a href="URL" target="_blank">Company Filing-Type</a> (Filed: DATE)</li>
    </ul>

    <h3>News Sources</h3>
    <ul>
        <li><a href="URL" target="_blank">Article Title</a> - Source Name, DATE</li>
    </ul>

    <h3>Market Data Providers</h3>
    <ul>
        <li>Yahoo Finance (as of {datetime.now().strftime('%Y-%m-%d')})</li>
    </ul>

    <p style="margin-top: 20px; font-style: italic; color: #666;">
    Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </p>
</div>

CRITICAL:
1. Only include source categories that were actually used
2. Extract URLs and dates where available
3. If no specific citations found, create generic attribution
4. HTML only, no markdown
"""

        result = execute_with_retry(
            self.client,
            prompt,
            max_retries=self.max_retries,
            temperature=0.2,  # Low temperature for factual extraction
            max_tokens=2048,
            logger=self.logger,
            task_description="Data sources collection"
        )

        return result or self._create_default_data_sources_section()

    def _create_default_data_sources_section(self) -> str:
        """
        Create default data sources section when extraction fails.

        Returns:
            HTML-formatted default data sources section
        """
        primary_sources = self.context.get_primary_data_sources()

        html = '<h2>📚 Data Sources & Citations</h2>\n'
        html += '<div class="data-sources">\n'
        html += '<p>This report is based on data from the following sources:</p>\n'
        html += '<ul>\n'

        for source in primary_sources:
            html += f'<li>{source}</li>\n'

        html += '</ul>\n'
        html += f'<p style="margin-top: 20px; font-style: italic; color: #666;">'
        html += f'Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>\n'
        html += '</div>\n'

        return html

    # ========================================================================
    # END NEW METHODS
    # ========================================================================

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

        # Step 6.5: Create peer comparison table (v1.0.5 enhancement - context-aware)
        peer_comparison = None
        if self.context.should_include_peer_comparison():
            self.logger.info("💼 Step 6.5: Creating peer comparison table...")
            peer_comparison = self.create_peer_comparison_table()
            if peer_comparison:
                peer_comparison = clean_html_response(peer_comparison)
                self.logger.info("✅ Peer comparison table created")
            else:
                self.logger.warning("Failed to create peer comparison table")
        else:
            self.logger.info("⏭️  Step 6.5: Peer comparison not applicable for this context")

        # Step 6.75: Generate investment recommendation (v1.0.5 enhancement - context-aware)
        investment_rec = None
        if self.context.should_include_investment_recommendation() and company_analysis:
            self.logger.info("🎯 Step 6.75: Generating investment recommendation...")
            investment_rec = self.generate_investment_recommendation(company_analysis)
            if investment_rec:
                investment_rec = clean_html_response(investment_rec)
                self.logger.info("✅ Investment recommendation generated")
            else:
                self.logger.warning("Failed to generate investment recommendation")
        else:
            self.logger.info("⏭️  Step 6.75: Investment recommendation not applicable for this context")

        # Step 7: Collect data sources (v1.0.5 enhancement - always included)
        self.logger.info("📚 Step 7: Collecting data sources and citations...")
        data_sources = self.collect_data_sources({
            'market': market_research,
            'company': company_analysis or '',
            'document': document_analysis,
            'competitor': competitor_analysis,
            'peer_comparison': peer_comparison or ''
        })
        if data_sources:
            data_sources = clean_html_response(data_sources)
            self.logger.info("✅ Data sources section created")
        else:
            self.logger.warning("Failed to collect data sources")
            data_sources = self._create_default_data_sources_section()

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
"""

        # Add peer comparison if available (v1.0.5 enhancement)
        if peer_comparison:
            report_content += f"""
<h2>📊 Peer Comparison</h2>
{peer_comparison}
"""

        report_content += f"""
<h2>🎯 Strategic Recommendations</h2>
<div class="recommendation">
    {strategy_recommendations}
</div>
"""

        # Add investment recommendation if available (v1.0.5 enhancement)
        if investment_rec:
            report_content += f"""
{investment_rec}
"""

        # Add data sources section (v1.0.5 enhancement - always included)
        report_content += f"""
{data_sources}
"""

        report_content += f"""
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