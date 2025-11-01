#!/usr/bin/env python3
"""
Citation Formatter for Business Intelligence Agent

Provides consistent citation formatting across all data source types:
- SEC filings
- News articles
- Research papers
- Web sources
- Calculated metrics

This is an ADD-ON module that enhances data presentation without breaking existing functionality.

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

from typing import Optional
from datetime import datetime


class CitationFormatter:
    """
    Format citations consistently for all data types.

    Provides static methods for formatting citations in HTML that can be
    embedded inline with data or in reference sections.
    """

    @staticmethod
    def cite_sec_filing(
        filing_type: str,
        company: str,
        date: str,
        url: str,
        page: Optional[int] = None
    ) -> str:
        """
        Format SEC filing citation.

        Args:
            filing_type: Type of filing (10-K, 10-Q, 8-K, etc.)
            company: Company name
            date: Filing date (YYYY-MM-DD format)
            url: URL to SEC filing
            page: Optional page number within filing

        Returns:
            HTML-formatted citation string

        Example:
            >>> cite_sec_filing('10-K', 'Apple Inc.', '2024-10-31', 'https://...', 24)
            '<a href="https://...">Apple Inc. 10-K</a> (Filed: 2024-10-31, p.24)'
        """
        citation = f'<a href="{url}" target="_blank">{company} {filing_type}</a>'
        citation += f' (Filed: {date}'
        if page:
            citation += f', p.{page}'
        citation += ')'
        return citation

    @staticmethod
    def cite_news_article(
        title: str,
        source: str,
        date: str,
        url: str
    ) -> str:
        """
        Format news article citation.

        Args:
            title: Article title
            source: News source name (Reuters, Bloomberg, etc.)
            date: Publication date
            url: Article URL

        Returns:
            HTML-formatted citation string

        Example:
            >>> cite_news_article('Tesla Earnings Beat', 'Reuters', '2024-10-30', 'https://...')
            '<a href="https://..." target="_blank">Tesla Earnings Beat</a> - Reuters, 2024-10-30'
        """
        return f'<a href="{url}" target="_blank">{title}</a> - {source}, {date}'

    @staticmethod
    def cite_research_paper(
        title: str,
        authors: str,
        venue: str,
        year: str,
        url: str
    ) -> str:
        """
        Format academic research paper citation.

        Args:
            title: Paper title
            authors: Author names (e.g., "Smith et al.")
            venue: Publication venue (journal/conference)
            year: Publication year
            url: Paper URL

        Returns:
            HTML-formatted citation string

        Example:
            >>> cite_research_paper('AI in Healthcare', 'Smith et al.', 'Nature Medicine', '2024', 'https://...')
            '<a href="https://..." target="_blank">AI in Healthcare</a> - Smith et al., Nature Medicine (2024)'
        """
        return f'<a href="{url}" target="_blank">{title}</a> - {authors}, {venue} ({year})'

    @staticmethod
    def cite_web_source(
        title: str,
        domain: str,
        url: str,
        accessed_date: Optional[str] = None
    ) -> str:
        """
        Format web page citation.

        Args:
            title: Page title
            domain: Website domain
            url: Page URL
            accessed_date: Date accessed (defaults to today)

        Returns:
            HTML-formatted citation string

        Example:
            >>> cite_web_source('Company Overview', 'company.com', 'https://...', '2024-10-31')
            '<a href="https://..." target="_blank">Company Overview</a> - company.com (Accessed: 2024-10-31)'
        """
        if accessed_date is None:
            accessed_date = datetime.now().strftime('%Y-%m-%d')

        return f'<a href="{url}" target="_blank">{title}</a> - {domain} (Accessed: {accessed_date})'

    @staticmethod
    def cite_calculation(
        formula: str,
        data_source: str
    ) -> str:
        """
        Format citation for calculated metrics.

        Args:
            formula: Calculation formula (e.g., "Net Income / Equity")
            data_source: Source of underlying data

        Returns:
            HTML-formatted citation string

        Example:
            >>> cite_calculation('Net Income / Equity', 'Apple 10-K FY2024')
            'Calculated: Net Income / Equity (Data from: Apple 10-K FY2024)'
        """
        return f'Calculated: {formula} (Data from: {data_source})'

    @staticmethod
    def cite_market_data(
        provider: str,
        date: Optional[str] = None
    ) -> str:
        """
        Format citation for market data providers.

        Args:
            provider: Data provider name (Yahoo Finance, Bloomberg, etc.)
            date: Data date (defaults to today)

        Returns:
            HTML-formatted citation string

        Example:
            >>> cite_market_data('Yahoo Finance', '2024-10-31')
            'Yahoo Finance (as of 2024-10-31)'
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        return f'{provider} (as of {date})'

    @staticmethod
    def format_data_with_citation(
        value: any,
        unit: str,
        citation: str,
        css_class: str = 'citation'
    ) -> str:
        """
        Format a data point with inline citation.

        Args:
            value: The data value (number, string, etc.)
            unit: Unit of measurement (B for billions, % for percent, etc.)
            citation: Pre-formatted citation string
            css_class: CSS class for citation span (default: 'citation')

        Returns:
            HTML-formatted data with inline citation

        Example:
            >>> citation = cite_sec_filing('10-K', 'Apple', '2024-10-31', 'https://...', 24)
            >>> format_data_with_citation(391.04, 'B', citation)
            '391.04B <span class="citation">[Source: <a href="...">Apple 10-K</a> (Filed: 2024-10-31, p.24)]</span>'
        """
        return f'{value}{unit} <span class="{css_class}">[Source: {citation}]</span>'

    @staticmethod
    def format_table_citation(
        citation: str,
        css_style: str = 'font-size: 11px; color: #666; font-style: italic; margin-top: 5px;'
    ) -> str:
        """
        Format citation for tables (appears below table).

        Args:
            citation: Pre-formatted citation string
            css_style: CSS styling for citation paragraph

        Returns:
            HTML paragraph with citation

        Example:
            >>> citation = cite_market_data('Yahoo Finance')
            >>> format_table_citation(citation)
            '<p style="font-size: 11px; color: #666; ...">[Source: Yahoo Finance (as of 2024-10-31)]</p>'
        """
        return f'<p style="{css_style}">[Source: {citation}]</p>'

    @staticmethod
    def format_chart_citation_text(
        citation: str
    ) -> str:
        """
        Format citation text for matplotlib charts.

        This should be used in ax.text() calls for chart citations.

        Args:
            citation: Pre-formatted citation string (without HTML tags)

        Returns:
            Plain text citation suitable for matplotlib

        Example:
            >>> format_chart_citation_text('SEC 10-Q Filings, Q1-Q4 FY2024')
            'Source: SEC 10-Q Filings, Q1-Q4 FY2024'
        """
        # Strip HTML tags for plain text use in charts
        import re
        plain_text = re.sub(r'<[^>]+>', '', citation)
        return f'Source: {plain_text}'

    @staticmethod
    def create_citation_section(
        sources: dict,
        title: str = '📚 Data Sources & Citations'
    ) -> str:
        """
        Create a complete data sources section for reports.

        Args:
            sources: Dictionary of source categories and citation lists
                     Example: {
                         'SEC Filings': ['<citation1>', '<citation2>'],
                         'News Sources': ['<citation1>', '<citation2>'],
                         ...
                     }
            title: Section title

        Returns:
            HTML-formatted data sources section

        Example:
            >>> sources = {
            ...     'SEC Filings': [cite_sec_filing(...)],
            ...     'News Sources': [cite_news_article(...)]
            ... }
            >>> create_citation_section(sources)
            '<h2>📚 Data Sources & Citations</h2><div class="data-sources">...</div>'
        """
        html = f'<h2>{title}</h2>\n'
        html += '<div class="data-sources">\n'
        html += '<p>This report is based on data from the following verified sources:</p>\n'

        for category, citation_list in sources.items():
            if citation_list:  # Only show categories with citations
                html += f'<h3>{category}</h3>\n<ul>\n'
                for citation in citation_list:
                    html += f'<li>{citation}</li>\n'
                html += '</ul>\n'

        html += f'<p style="margin-top: 20px; font-style: italic; color: #666;">'
        html += f'Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>\n'
        html += '</div>\n'

        return html

    @staticmethod
    def create_disclaimer(
        disclaimer_type: str = 'investment'
    ) -> str:
        """
        Create standard disclaimer text.

        Args:
            disclaimer_type: Type of disclaimer ('investment', 'research', 'general')

        Returns:
            HTML-formatted disclaimer text
        """
        disclaimers = {
            'investment': (
                '<p style="font-size: 11px; color: #666; font-style: italic; '
                'margin-top: 15px; padding: 10px; background-color: #fff3cd; '
                'border-left: 3px solid #ffc107;">'
                '<strong>Disclaimer:</strong> This analysis is for informational purposes only '
                'and does not constitute financial advice. Consult a qualified financial advisor '
                'before making investment decisions. Past performance does not guarantee future results.'
                '</p>'
            ),
            'research': (
                '<p style="font-size: 11px; color: #666; font-style: italic; margin-top: 15px;">'
                '<strong>Note:</strong> This research summary is based on publicly available information '
                'and academic sources. Always verify information from primary sources before use in '
                'critical applications.'
                '</p>'
            ),
            'general': (
                '<p style="font-size: 11px; color: #666; font-style: italic; margin-top: 15px;">'
                '<strong>Note:</strong> Analysis based on publicly available information as of '
                f'{datetime.now().strftime("%Y-%m-%d")}. Information may change over time.'
                '</p>'
            )
        }

        return disclaimers.get(disclaimer_type, disclaimers['general'])
