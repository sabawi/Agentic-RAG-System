"""
Projection Engine

Generates financial projections based on historical data and analyst estimates.

Part of: FUNDAMENTAL_ANALYSIS_DCF_IMPLEMENTATION_PLAN.md - Day 5 Implementation
"""

import pandas as pd
from typing import Dict, Any, List, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class ProjectionEngine:
    """
    Generate financial projections.

    Features:
    - Historical growth rate calculations
    - Revenue projections (base/best/worst case)
    - Earnings projections
    - Free cash flow projections
    """

    def __init__(self):
        """Initialize the projection engine."""
        self.projection_years = 3  # 3-year forward projections

    def _get_value(self, df: pd.DataFrame, key: str, col_index: int = 0):
        """Safely extract value from DataFrame."""
        try:
            if df is None or df.empty:
                return None
            if key not in df.index:
                return None
            value = df.loc[key, df.columns[col_index]]
            if pd.isna(value):
                return None
            return value
        except:
            return None

    def calculate_historical_cagr(self, values: List[float]) -> Optional[float]:
        """
        Calculate CAGR from a list of values.

        CAGR = (Ending Value / Beginning Value)^(1/years) - 1
        """
        try:
            if not values or len(values) < 2:
                return None

            # Filter out None and invalid values
            valid_values = [v for v in values if v is not None and v > 0]

            if len(valid_values) < 2:
                return None

            beginning_value = valid_values[-1]
            ending_value = valid_values[0]
            years = len(valid_values) - 1

            if beginning_value <= 0:
                return None

            cagr = (ending_value / beginning_value) ** (1 / years) - 1

            # Cap at reasonable levels
            cagr = max(min(cagr, 1.0), -0.5)

            return cagr
        except:
            return None

    def project_metric(self, current_value: float, growth_rate: float, years: int) -> List[float]:
        """Project a metric forward using a growth rate."""
        if current_value is None or growth_rate is None:
            return []

        projections = []
        value = current_value

        for year in range(1, years + 1):
            value = value * (1 + growth_rate)
            projections.append(value)

        return projections

    def generate_revenue_projections(self, income_stmt: pd.DataFrame) -> Dict[str, Any]:
        """Generate revenue projections with base/best/worst scenarios."""
        try:
            if income_stmt is None or income_stmt.empty:
                return {}

            # Get historical revenue
            revenue_values = []
            for i in range(min(4, len(income_stmt.columns))):
                rev = self._get_value(income_stmt, 'Total Revenue', i)
                if rev:
                    revenue_values.append(rev)

            if not revenue_values:
                return {}

            current_revenue = revenue_values[0]

            # Calculate historical growth rate
            historical_growth = self.calculate_historical_cagr(revenue_values)

            if historical_growth is None:
                # Use conservative 5% if no historical data
                base_growth = 0.05
            else:
                base_growth = historical_growth

            # Create scenarios
            # Best case: 1.5x historical or +5%, whichever is higher
            best_growth = max(base_growth * 1.5, base_growth + 0.05)
            best_growth = min(best_growth, 0.25)  # Cap at 25%

            # Worst case: 0.5x historical or -5%, whichever is lower
            worst_growth = min(base_growth * 0.5, base_growth - 0.05)
            worst_growth = max(worst_growth, -0.10)  # Floor at -10%

            return {
                'current': current_revenue,
                'historical_growth': historical_growth,
                'base_case': {
                    'growth_rate': base_growth,
                    'projections': self.project_metric(current_revenue, base_growth, self.projection_years)
                },
                'best_case': {
                    'growth_rate': best_growth,
                    'projections': self.project_metric(current_revenue, best_growth, self.projection_years)
                },
                'worst_case': {
                    'growth_rate': worst_growth,
                    'projections': self.project_metric(current_revenue, worst_growth, self.projection_years)
                }
            }

        except Exception as e:
            logger.error(f"Error generating revenue projections: {e}")
            return {}

    def generate_earnings_projections(self, income_stmt: pd.DataFrame) -> Dict[str, Any]:
        """Generate earnings projections."""
        try:
            if income_stmt is None or income_stmt.empty:
                return {}

            # Get historical net income
            earnings_values = []
            for i in range(min(4, len(income_stmt.columns))):
                earnings = self._get_value(income_stmt, 'Net Income', i)
                if earnings:
                    earnings_values.append(earnings)

            if not earnings_values:
                return {}

            current_earnings = earnings_values[0]

            # Calculate historical growth rate
            historical_growth = self.calculate_historical_cagr([e for e in earnings_values if e > 0])

            if historical_growth is None:
                # Use conservative 5% if no historical data
                base_growth = 0.05
            else:
                # Use slightly more conservative growth for earnings
                base_growth = historical_growth * 0.9

            # Cap earnings growth at 20%
            base_growth = min(base_growth, 0.20)

            return {
                'current': current_earnings,
                'historical_growth': historical_growth,
                'base_case': {
                    'growth_rate': base_growth,
                    'projections': self.project_metric(current_earnings, base_growth, self.projection_years)
                }
            }

        except Exception as e:
            logger.error(f"Error generating earnings projections: {e}")
            return {}

    def generate_fcf_projections(self, cash_flow: pd.DataFrame) -> Dict[str, Any]:
        """Generate free cash flow projections."""
        try:
            if cash_flow is None or cash_flow.empty:
                return {}

            # Get historical FCF
            fcf_values = []
            for i in range(min(4, len(cash_flow.columns))):
                ocf = self._get_value(cash_flow, 'Operating Cash Flow', i)
                capex = self._get_value(cash_flow, 'Capital Expenditure', i)
                if ocf is not None and capex is not None:
                    fcf = ocf + capex  # capex is negative
                    fcf_values.append(fcf)

            if not fcf_values:
                return {}

            current_fcf = fcf_values[0]

            # Calculate historical growth rate
            historical_growth = self.calculate_historical_cagr([f for f in fcf_values if f > 0])

            if historical_growth is None:
                # Use conservative 4% if no historical data
                base_growth = 0.04
            else:
                base_growth = historical_growth

            # Be more conservative with FCF growth
            base_growth = min(base_growth, 0.15)

            return {
                'current': current_fcf,
                'historical_growth': historical_growth,
                'base_case': {
                    'growth_rate': base_growth,
                    'projections': self.project_metric(current_fcf, base_growth, self.projection_years)
                }
            }

        except Exception as e:
            logger.error(f"Error generating FCF projections: {e}")
            return {}

    def generate_projections(self, ticker: str, financials: Dict) -> Dict[str, Any]:
        """
        Generate comprehensive financial projections.

        Args:
            ticker: Stock ticker symbol
            financials: Financial statements from extractor

        Returns:
            Dictionary with all projections
        """
        logger.info(f"Generating projections for {ticker}")

        # Extract financial statements
        income_stmt = financials.get('income_statement', {}).get('annual')
        cash_flow = financials.get('cash_flow', {}).get('annual')

        return {
            'revenue_projections': self.generate_revenue_projections(income_stmt),
            'earnings_projections': self.generate_earnings_projections(income_stmt),
            'fcf_projections': self.generate_fcf_projections(cash_flow)
        }

    def _format_source_block(self, source_num: int, title: str, url: str, date: str, content: str) -> str:
        """
        Format content into standardized SOURCE block format for LLM context.

        This follows the Context Engineering Citation Mastery format.

        Args:
            source_num: Sequential source number
            title: Title of the projection
            url: URL to the source
            date: Projection date
            content: Formatted projection data

        Returns:
            Formatted SOURCE block string
        """
        # Truncate content to 500 characters max (Context Engineering standard)
        if len(content) > 500:
            content = content[:497] + "..."

        return f"""SOURCE {source_num}:
Title: {title}
URL: {url}
Date: {date}
{content}

"""

    def format_projections_for_llm(self, projections: Dict, ticker: str = None) -> str:
        """
        Format projections for LLM consumption in SOURCE block format.

        Args:
            projections: Dictionary of projections
            ticker: Stock ticker for URL attribution

        Returns:
            Formatted string in SOURCE block format
        """
        if not ticker:
            ticker = "UNKNOWN"

        # Check if we have any projections
        has_projections = any(
            projections.get(key) for key in ['revenue_projections', 'earnings_projections', 'fcf_projections']
        )

        if not has_projections:
            return "\n⚠️ **FINANCIAL PROJECTIONS** - Data not available\n"

        output = []
        source_num = 1
        current_date = pd.Timestamp.now().strftime('%Y-%m-%d')

        # Format revenue projections
        if projections.get('revenue_projections'):
            rev_proj = projections['revenue_projections']
            content = self._format_revenue_projections(rev_proj)
            if content:
                source_block = self._format_source_block(
                    source_num=source_num,
                    title=f"{ticker} Revenue Projections (3-Year Forward)",
                    url=f"https://finance.yahoo.com/quote/{ticker}/analysis",
                    date=current_date,
                    content=content
                )
                output.append(source_block)
                source_num += 1

        # Format earnings projections
        if projections.get('earnings_projections'):
            earn_proj = projections['earnings_projections']
            content = self._format_earnings_projections(earn_proj)
            if content:
                source_block = self._format_source_block(
                    source_num=source_num,
                    title=f"{ticker} Earnings Projections (3-Year Forward)",
                    url=f"https://finance.yahoo.com/quote/{ticker}/analysis",
                    date=current_date,
                    content=content
                )
                output.append(source_block)
                source_num += 1

        # Format FCF projections
        if projections.get('fcf_projections'):
            fcf_proj = projections['fcf_projections']
            content = self._format_fcf_projections(fcf_proj)
            if content:
                source_block = self._format_source_block(
                    source_num=source_num,
                    title=f"{ticker} Free Cash Flow Projections (3-Year Forward)",
                    url=f"https://finance.yahoo.com/quote/{ticker}/analysis",
                    date=current_date,
                    content=content
                )
                output.append(source_block)
                source_num += 1

        return "\n".join(output)

    def _format_revenue_projections(self, rev_proj: Dict) -> str:
        """Format revenue projections."""
        if not rev_proj:
            return ""

        lines = ["REVENUE PROJECTIONS:"]

        if 'current' in rev_proj:
            lines.append(f"  Current Revenue: ${rev_proj['current']/1e9:.2f}B")

        if 'base_case' in rev_proj:
            base = rev_proj['base_case']
            lines.append(f"\nBase Case (Growth: {base['growth_rate']*100:.1f}%):")
            for i, value in enumerate(base['projections'], 1):
                lines.append(f"  Year {i}: ${value/1e9:.2f}B")

        return "\n".join(lines)

    def _format_earnings_projections(self, earn_proj: Dict) -> str:
        """Format earnings projections."""
        if not earn_proj:
            return ""

        lines = ["EARNINGS PROJECTIONS:"]

        if 'current' in earn_proj:
            lines.append(f"  Current Net Income: ${earn_proj['current']/1e9:.2f}B")

        if 'base_case' in earn_proj:
            base = earn_proj['base_case']
            lines.append(f"\nProjected Growth: {base['growth_rate']*100:.1f}%")
            for i, value in enumerate(base['projections'], 1):
                lines.append(f"  Year {i}: ${value/1e9:.2f}B")

        return "\n".join(lines)

    def _format_fcf_projections(self, fcf_proj: Dict) -> str:
        """Format FCF projections."""
        if not fcf_proj:
            return ""

        lines = ["FREE CASH FLOW PROJECTIONS:"]

        if 'current' in fcf_proj:
            lines.append(f"  Current FCF: ${fcf_proj['current']/1e9:.2f}B")

        if 'base_case' in fcf_proj:
            base = fcf_proj['base_case']
            lines.append(f"\nProjected Growth: {base['growth_rate']*100:.1f}%")
            for i, value in enumerate(base['projections'], 1):
                lines.append(f"  Year {i}: ${value/1e9:.2f}B")

        return "\n".join(lines)
