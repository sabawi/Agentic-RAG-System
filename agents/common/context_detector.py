#!/usr/bin/env python3
"""
Context Detection for Business Intelligence Agent

Detects and classifies analysis context to determine:
- Which tools are relevant
- Which report sections should be included
- What type of analysis is appropriate

This is an ADD-ON module that enhances the agent without breaking existing functionality.

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

from typing import List, Optional, Dict


class AnalysisContext:
    """
    Detect and classify the type of business intelligence analysis being performed.

    This class determines:
    - Context type (PUBLIC_COMPANY, PRIVATE_COMPANY, SECTOR_ANALYSIS, TOPIC_RESEARCH)
    - Which data sources are relevant
    - Which report sections should be included
    - Which tools should be used
    """

    def __init__(
        self,
        company: Optional[str] = None,
        competitors: Optional[List[str]] = None,
        sectors: Optional[List[str]] = None,
        research_topics: Optional[List[str]] = None
    ):
        """
        Initialize context detector.

        Args:
            company: Primary company to analyze
            competitors: List of competitor companies
            sectors: List of industry sectors
            research_topics: List of research topics
        """
        self.company = company
        self.competitors = competitors or []
        self.sectors = sectors or []
        self.research_topics = research_topics or []

        # Detect context type
        self.context_type = self._detect_context_type()

    def _detect_context_type(self) -> str:
        """
        Detect the overall analysis context type.

        Returns:
            Context type string
        """
        # Priority 1: If company is specified, it's company analysis
        if self.company:
            # Assume public until proven otherwise (will check at runtime)
            return 'COMPANY_ANALYSIS'

        # Priority 2: Sector analysis (no company but sectors specified)
        elif self.sectors and not self.company:
            return 'SECTOR_ANALYSIS'

        # Priority 3: Research topic analysis
        elif self.research_topics and not self.company and not self.sectors:
            return 'TOPIC_RESEARCH'

        # Default: General intelligence
        else:
            return 'GENERAL_INTELLIGENCE'

    def is_company_analysis(self) -> bool:
        """Returns True if analyzing a specific company."""
        return self.context_type == 'COMPANY_ANALYSIS'

    def is_sector_analysis(self) -> bool:
        """Returns True if analyzing industry sectors."""
        return self.context_type == 'SECTOR_ANALYSIS'

    def is_topic_research(self) -> bool:
        """Returns True if performing research topic analysis."""
        return self.context_type == 'TOPIC_RESEARCH'

    def should_include_financial_analysis(self) -> bool:
        """
        Determine if financial analysis section should be included.

        Financial analysis is relevant when:
        - Analyzing a specific company (assumes public)
        - Has competitors (for comparison)

        Returns:
            True if financial analysis should be included
        """
        return self.is_company_analysis()

    def should_include_sec_filings(self) -> bool:
        """
        Determine if SEC filings should be fetched.

        SEC filings are only available for public companies.
        Since we assume company analysis means public company,
        this returns True for company analysis.

        Note: At runtime, if SEC filing fetch fails, it means
        the company is private and we gracefully degrade.

        Returns:
            True if SEC filings should be attempted
        """
        return self.is_company_analysis()

    def should_include_peer_comparison(self) -> bool:
        """
        Determine if peer comparison table should be included.

        Peer comparison makes sense when:
        - Analyzing a company AND
        - Have competitors specified AND
        - Should include financial analysis

        Returns:
            True if peer comparison should be included
        """
        return (
            self.is_company_analysis() and
            len(self.competitors) > 0 and
            self.should_include_financial_analysis()
        )

    def should_include_investment_recommendation(self) -> bool:
        """
        Determine if investment recommendation should be included.

        Investment recommendations (Buy/Hold/Sell) are only appropriate for:
        - Public companies (tradeable securities)
        - When financial data is available

        Returns:
            True if investment recommendation should be included
        """
        return self.is_company_analysis() and self.should_include_financial_analysis()

    def should_use_research_papers(self) -> bool:
        """
        Determine if academic research papers should be searched.

        Research papers are relevant for:
        - Sector analysis (industry research)
        - Topic research (primary source)
        - Company analysis with research topics specified

        Returns:
            True if research papers should be searched
        """
        return (
            self.is_sector_analysis() or
            self.is_topic_research() or
            (self.is_company_analysis() and len(self.research_topics) > 0)
        )

    def get_primary_data_sources(self) -> List[str]:
        """
        Get list of primary data sources for this context.

        Returns:
            List of data source names in priority order
        """
        sources = []

        if self.is_company_analysis():
            sources.extend([
                'SEC EDGAR (get_sec_filings)',
                'Financial Data (comprehensive_stock_analyzer)',
                'Market Data (get_stock_and_company_data)',
                'News (get_news_summaries)',
                'Web Research (search_web)'
            ])

        elif self.is_sector_analysis():
            sources.extend([
                'Academic Research (search_research_papers)',
                'News (get_news_summaries)',
                'Web Research (search_web)'
            ])

        elif self.is_topic_research():
            sources.extend([
                'Academic Research (search_research_papers)',
                'News (get_news_summaries)',
                'Web Research (search_web)'
            ])

        else:  # GENERAL_INTELLIGENCE
            sources.extend([
                'News (get_news_summaries)',
                'Web Research (search_web)'
            ])

        return sources

    def get_required_sections(self) -> List[str]:
        """
        Get list of required report sections for this context.

        Returns:
            List of section names that should be included
        """
        sections = ['executive_summary']  # Always include

        if self.is_company_analysis():
            sections.extend([
                'market_analysis',
                'financial_analysis',
                'competitive_analysis',
                'risk_assessment',
                'strategic_recommendations'
            ])

            if self.should_include_peer_comparison():
                sections.append('peer_comparison')

            if self.should_include_investment_recommendation():
                sections.append('investment_recommendation')

        elif self.is_sector_analysis():
            sections.extend([
                'sector_overview',
                'market_trends',
                'key_players',
                'technology_landscape',
                'growth_projections'
            ])

        elif self.is_topic_research():
            sections.extend([
                'research_overview',
                'key_findings',
                'academic_consensus',
                'future_directions'
            ])

        else:  # GENERAL_INTELLIGENCE
            sections.extend([
                'market_overview',
                'key_insights'
            ])

        sections.append('data_sources')  # Always include at end

        return sections

    def get_context_summary(self) -> Dict[str, any]:
        """
        Get summary of detected context for logging/debugging.

        Returns:
            Dictionary with context information
        """
        return {
            'context_type': self.context_type,
            'company': self.company,
            'competitors_count': len(self.competitors),
            'sectors_count': len(self.sectors),
            'research_topics_count': len(self.research_topics),
            'will_include_financials': self.should_include_financial_analysis(),
            'will_fetch_sec_filings': self.should_include_sec_filings(),
            'will_include_peer_comparison': self.should_include_peer_comparison(),
            'will_include_investment_rec': self.should_include_investment_recommendation(),
            'will_use_research_papers': self.should_use_research_papers(),
            'primary_data_sources': self.get_primary_data_sources(),
            'required_sections': self.get_required_sections()
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"AnalysisContext(type={self.context_type}, company={self.company}, competitors={len(self.competitors)})"
