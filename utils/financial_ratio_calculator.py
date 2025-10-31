"""
Financial Ratio Calculator

Calculates comprehensive financial ratios from financial statements.

Part of: FUNDAMENTAL_ANALYSIS_DCF_IMPLEMENTATION_PLAN.md - Day 3 Implementation
"""

import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FinancialRatioCalculator:
    """
    Calculate comprehensive financial ratios.

    Categories:
    - Profitability: Gross Margin, Operating Margin, Net Margin, ROA, ROE, ROIC
    - Liquidity: Current Ratio, Quick Ratio, Cash Ratio
    - Leverage: Debt/Equity, Debt/Assets, Interest Coverage
    - Efficiency: Asset Turnover, Inventory Turnover, Receivables Turnover
    - Valuation: P/E, P/B, P/S, EV/EBITDA, P/FCF
    """

    def __init__(self):
        """Initialize the calculator."""
        pass

    def _safe_divide(self, numerator, denominator, default=None):
        """Safely divide two numbers, handling None and zero cases."""
        try:
            if numerator is None or denominator is None:
                return default
            if pd.isna(numerator) or pd.isna(denominator):
                return default
            if denominator == 0:
                return default
            return numerator / denominator
        except:
            return default

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

    def calculate_profitability_ratios(self, income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame) -> Dict[str, Any]:
        """Calculate profitability ratios."""
        ratios = {}

        # Extract values
        revenue = self._get_value(income_stmt, 'Total Revenue')
        cost_of_revenue = self._get_value(income_stmt, 'Cost Of Revenue')
        gross_profit = self._get_value(income_stmt, 'Gross Profit')
        operating_income = self._get_value(income_stmt, 'Operating Income')
        net_income = self._get_value(income_stmt, 'Net Income')
        total_assets = self._get_value(balance_sheet, 'Total Assets')
        stockholders_equity = self._get_value(balance_sheet, 'Stockholders Equity')

        # Calculate ratios
        if revenue and gross_profit:
            ratios['gross_margin'] = (gross_profit / revenue) * 100

        if revenue and operating_income:
            ratios['operating_margin'] = (operating_income / revenue) * 100

        if revenue and net_income:
            ratios['net_margin'] = (net_income / revenue) * 100

        if total_assets and net_income:
            ratios['roa'] = (net_income / total_assets) * 100

        if stockholders_equity and net_income:
            ratios['roe'] = (net_income / stockholders_equity) * 100

        # ROIC = Net Income / (Total Debt + Shareholders' Equity)
        total_debt = self._get_value(balance_sheet, 'Total Debt')
        if not total_debt:
            long_term_debt = self._get_value(balance_sheet, 'Long Term Debt') or 0
            current_debt = self._get_value(balance_sheet, 'Current Debt') or 0
            total_debt = long_term_debt + current_debt if (long_term_debt or current_debt) else None

        if total_debt is not None and stockholders_equity and net_income:
            invested_capital = total_debt + stockholders_equity
            if invested_capital > 0:
                ratios['roic'] = (net_income / invested_capital) * 100

        return ratios

    def calculate_liquidity_ratios(self, balance_sheet: pd.DataFrame) -> Dict[str, Any]:
        """Calculate liquidity ratios."""
        ratios = {}

        current_assets = self._get_value(balance_sheet, 'Current Assets')
        current_liabilities = self._get_value(balance_sheet, 'Current Liabilities')
        cash = self._get_value(balance_sheet, 'Cash And Cash Equivalents')
        inventory = self._get_value(balance_sheet, 'Inventory')
        accounts_receivable = self._get_value(balance_sheet, 'Accounts Receivable')

        # Current Ratio
        if current_assets and current_liabilities:
            ratios['current_ratio'] = current_assets / current_liabilities

        # Quick Ratio (exclude inventory)
        if current_assets and inventory is not None and current_liabilities:
            quick_assets = current_assets - inventory
            ratios['quick_ratio'] = quick_assets / current_liabilities

        # Cash Ratio
        if cash and current_liabilities:
            ratios['cash_ratio'] = cash / current_liabilities

        return ratios

    def calculate_leverage_ratios(self, income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame) -> Dict[str, Any]:
        """Calculate leverage ratios."""
        ratios = {}

        total_assets = self._get_value(balance_sheet, 'Total Assets')
        stockholders_equity = self._get_value(balance_sheet, 'Stockholders Equity')
        operating_income = self._get_value(income_stmt, 'Operating Income')
        interest_expense = self._get_value(income_stmt, 'Interest Expense')

        # Calculate total debt
        total_debt = self._get_value(balance_sheet, 'Total Debt')
        if not total_debt:
            long_term_debt = self._get_value(balance_sheet, 'Long Term Debt') or 0
            current_debt = self._get_value(balance_sheet, 'Current Debt') or 0
            total_debt = long_term_debt + current_debt if (long_term_debt or current_debt) else None

        # Debt to Equity
        if total_debt and stockholders_equity:
            ratios['debt_to_equity'] = total_debt / stockholders_equity

        # Debt to Assets
        if total_debt and total_assets:
            ratios['debt_to_assets'] = (total_debt / total_assets) * 100

        # Interest Coverage
        if operating_income and interest_expense and interest_expense != 0:
            ratios['interest_coverage'] = operating_income / abs(interest_expense)

        return ratios

    def calculate_efficiency_ratios(self, income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame) -> Dict[str, Any]:
        """Calculate efficiency ratios."""
        ratios = {}

        revenue = self._get_value(income_stmt, 'Total Revenue')
        cost_of_revenue = self._get_value(income_stmt, 'Cost Of Revenue')
        total_assets = self._get_value(balance_sheet, 'Total Assets')
        inventory = self._get_value(balance_sheet, 'Inventory')
        accounts_receivable = self._get_value(balance_sheet, 'Accounts Receivable')

        # Asset Turnover
        if revenue and total_assets:
            ratios['asset_turnover'] = revenue / total_assets

        # Inventory Turnover
        if cost_of_revenue and inventory:
            ratios['inventory_turnover'] = cost_of_revenue / inventory

        # Receivables Turnover
        if revenue and accounts_receivable:
            ratios['receivables_turnover'] = revenue / accounts_receivable
            # Days Sales Outstanding
            ratios['days_sales_outstanding'] = 365 / ratios['receivables_turnover']

        return ratios

    def calculate_valuation_ratios(self, income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame,
                                   cash_flow: pd.DataFrame, market_data: Dict) -> Dict[str, Any]:
        """Calculate valuation ratios."""
        ratios = {}

        # Extract market data
        current_price = market_data.get('current_price')
        market_cap = market_data.get('market_cap')
        shares_outstanding = market_data.get('shares_outstanding')

        # Extract financial data
        net_income = self._get_value(income_stmt, 'Net Income')
        revenue = self._get_value(income_stmt, 'Total Revenue')
        stockholders_equity = self._get_value(balance_sheet, 'Stockholders Equity')
        operating_cash_flow = self._get_value(cash_flow, 'Operating Cash Flow')
        capex = self._get_value(cash_flow, 'Capital Expenditure')

        # Calculate shares outstanding from market cap and price if not provided
        if not shares_outstanding and market_cap and current_price and current_price > 0:
            shares_outstanding = market_cap / current_price

        # Earnings per share
        eps = None
        if net_income and shares_outstanding and shares_outstanding > 0:
            eps = net_income / shares_outstanding
            ratios['eps'] = eps

        # P/E Ratio
        if current_price and eps and eps > 0:
            ratios['pe_ratio'] = current_price / eps

        # P/B Ratio
        if current_price and stockholders_equity and shares_outstanding and shares_outstanding > 0:
            book_value_per_share = stockholders_equity / shares_outstanding
            if book_value_per_share > 0:
                ratios['pb_ratio'] = current_price / book_value_per_share

        # P/S Ratio
        if market_cap and revenue and revenue > 0:
            ratios['ps_ratio'] = market_cap / revenue

        # P/FCF Ratio
        if operating_cash_flow and capex is not None:
            fcf = operating_cash_flow + capex  # capex is negative
            if fcf > 0 and market_cap:
                ratios['pfcf_ratio'] = market_cap / fcf

        # EV/EBITDA
        # Calculate EBITDA (approximate from available data)
        operating_income = self._get_value(income_stmt, 'Operating Income')
        if operating_income:
            # EBITDA ≈ Operating Income + Depreciation
            # We can approximate or use operating income as proxy
            total_debt = self._get_value(balance_sheet, 'Total Debt')
            if not total_debt:
                long_term_debt = self._get_value(balance_sheet, 'Long Term Debt') or 0
                current_debt = self._get_value(balance_sheet, 'Current Debt') or 0
                total_debt = long_term_debt + current_debt if (long_term_debt or current_debt) else 0

            cash = self._get_value(balance_sheet, 'Cash And Cash Equivalents') or 0

            if market_cap and total_debt is not None:
                enterprise_value = market_cap + total_debt - cash
                if operating_income > 0:
                    ratios['ev_ebitda'] = enterprise_value / operating_income

        return ratios

    def calculate_all_ratios(self, financials: Dict, market_data: Dict) -> Dict[str, Any]:
        """
        Calculate all financial ratios.

        Args:
            financials: Financial statements from extractor
            market_data: Market data (price, shares, market cap)

        Returns:
            Dictionary of all calculated ratios by category
        """
        logger.info("Calculating comprehensive financial ratios")

        if not financials:
            logger.warning("No financial data available for ratio calculation")
            return {
                'profitability': {},
                'liquidity': {},
                'leverage': {},
                'efficiency': {},
                'valuation': {}
            }

        # Extract financial statements
        income_stmt = financials.get('income_statement', {}).get('annual')
        balance_sheet = financials.get('balance_sheet', {}).get('annual')
        cash_flow = financials.get('cash_flow', {}).get('annual')

        return {
            'profitability': self.calculate_profitability_ratios(income_stmt, balance_sheet),
            'liquidity': self.calculate_liquidity_ratios(balance_sheet),
            'leverage': self.calculate_leverage_ratios(income_stmt, balance_sheet),
            'efficiency': self.calculate_efficiency_ratios(income_stmt, balance_sheet),
            'valuation': self.calculate_valuation_ratios(income_stmt, balance_sheet, cash_flow, market_data)
        }

    def _format_source_block(self, source_num: int, title: str, url: str, date: str, content: str) -> str:
        """
        Format content into standardized SOURCE block format for LLM context.

        This follows the Context Engineering Citation Mastery format.

        Args:
            source_num: Sequential source number
            title: Title of the analysis
            url: URL to the source
            date: Analysis date
            content: Formatted ratio data

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

    def format_ratios_for_llm(self, ratios: Dict, ticker: str = None) -> str:
        """
        Format calculated ratios for LLM consumption in SOURCE block format.

        Args:
            ratios: Dictionary of calculated ratios
            ticker: Stock ticker for URL attribution

        Returns:
            Formatted string in SOURCE block format
        """
        if not ticker:
            ticker = "UNKNOWN"

        # Check if we have any ratios
        has_ratios = any(ratios.get(category) for category in ratios.keys())
        if not has_ratios:
            return "\n⚠️ **FINANCIAL RATIOS ANALYSIS** - Data not available\n"

        output = []
        source_num = 1
        current_date = pd.Timestamp.now().strftime('%Y-%m-%d')

        # Format each category as a separate SOURCE block

        # Profitability Ratios
        if ratios.get('profitability'):
            content = self._format_profitability_ratios(ratios['profitability'])
            source_block = self._format_source_block(
                source_num=source_num,
                title=f"{ticker} Profitability Ratios Analysis",
                url=f"https://finance.yahoo.com/quote/{ticker}/key-statistics",
                date=current_date,
                content=content
            )
            output.append(source_block)
            source_num += 1

        # Liquidity Ratios
        if ratios.get('liquidity'):
            content = self._format_liquidity_ratios(ratios['liquidity'])
            source_block = self._format_source_block(
                source_num=source_num,
                title=f"{ticker} Liquidity Ratios Analysis",
                url=f"https://finance.yahoo.com/quote/{ticker}/key-statistics",
                date=current_date,
                content=content
            )
            output.append(source_block)
            source_num += 1

        # Leverage Ratios
        if ratios.get('leverage'):
            content = self._format_leverage_ratios(ratios['leverage'])
            source_block = self._format_source_block(
                source_num=source_num,
                title=f"{ticker} Leverage Ratios Analysis",
                url=f"https://finance.yahoo.com/quote/{ticker}/key-statistics",
                date=current_date,
                content=content
            )
            output.append(source_block)
            source_num += 1

        # Efficiency Ratios
        if ratios.get('efficiency'):
            content = self._format_efficiency_ratios(ratios['efficiency'])
            source_block = self._format_source_block(
                source_num=source_num,
                title=f"{ticker} Efficiency Ratios Analysis",
                url=f"https://finance.yahoo.com/quote/{ticker}/key-statistics",
                date=current_date,
                content=content
            )
            output.append(source_block)
            source_num += 1

        # Valuation Ratios
        if ratios.get('valuation'):
            content = self._format_valuation_ratios(ratios['valuation'])
            source_block = self._format_source_block(
                source_num=source_num,
                title=f"{ticker} Valuation Ratios Analysis",
                url=f"https://finance.yahoo.com/quote/{ticker}/key-statistics",
                date=current_date,
                content=content
            )
            output.append(source_block)
            source_num += 1

        return "\n".join(output)

    def _format_profitability_ratios(self, ratios: Dict) -> str:
        """Format profitability ratios."""
        lines = ["PROFITABILITY METRICS:"]

        if 'gross_margin' in ratios:
            lines.append(f"  Gross Margin: {ratios['gross_margin']:.2f}%")
        if 'operating_margin' in ratios:
            lines.append(f"  Operating Margin: {ratios['operating_margin']:.2f}%")
        if 'net_margin' in ratios:
            lines.append(f"  Net Margin: {ratios['net_margin']:.2f}%")
        if 'roa' in ratios:
            lines.append(f"  Return on Assets (ROA): {ratios['roa']:.2f}%")
        if 'roe' in ratios:
            lines.append(f"  Return on Equity (ROE): {ratios['roe']:.2f}%")
        if 'roic' in ratios:
            lines.append(f"  Return on Invested Capital (ROIC): {ratios['roic']:.2f}%")

        return "\n".join(lines)

    def _format_liquidity_ratios(self, ratios: Dict) -> str:
        """Format liquidity ratios."""
        lines = ["LIQUIDITY METRICS:"]

        if 'current_ratio' in ratios:
            lines.append(f"  Current Ratio: {ratios['current_ratio']:.2f}")
        if 'quick_ratio' in ratios:
            lines.append(f"  Quick Ratio: {ratios['quick_ratio']:.2f}")
        if 'cash_ratio' in ratios:
            lines.append(f"  Cash Ratio: {ratios['cash_ratio']:.2f}")

        return "\n".join(lines)

    def _format_leverage_ratios(self, ratios: Dict) -> str:
        """Format leverage ratios."""
        lines = ["LEVERAGE METRICS:"]

        if 'debt_to_equity' in ratios:
            lines.append(f"  Debt to Equity: {ratios['debt_to_equity']:.2f}")
        if 'debt_to_assets' in ratios:
            lines.append(f"  Debt to Assets: {ratios['debt_to_assets']:.2f}%")
        if 'interest_coverage' in ratios:
            lines.append(f"  Interest Coverage: {ratios['interest_coverage']:.2f}x")

        return "\n".join(lines)

    def _format_efficiency_ratios(self, ratios: Dict) -> str:
        """Format efficiency ratios."""
        lines = ["EFFICIENCY METRICS:"]

        if 'asset_turnover' in ratios:
            lines.append(f"  Asset Turnover: {ratios['asset_turnover']:.2f}x")
        if 'inventory_turnover' in ratios:
            lines.append(f"  Inventory Turnover: {ratios['inventory_turnover']:.2f}x")
        if 'receivables_turnover' in ratios:
            lines.append(f"  Receivables Turnover: {ratios['receivables_turnover']:.2f}x")
        if 'days_sales_outstanding' in ratios:
            lines.append(f"  Days Sales Outstanding: {ratios['days_sales_outstanding']:.1f} days")

        return "\n".join(lines)

    def _format_valuation_ratios(self, ratios: Dict) -> str:
        """Format valuation ratios."""
        lines = ["VALUATION METRICS:"]

        if 'eps' in ratios:
            lines.append(f"  Earnings Per Share (EPS): ${ratios['eps']:.2f}")
        if 'pe_ratio' in ratios:
            lines.append(f"  Price to Earnings (P/E): {ratios['pe_ratio']:.2f}")
        if 'pb_ratio' in ratios:
            lines.append(f"  Price to Book (P/B): {ratios['pb_ratio']:.2f}")
        if 'ps_ratio' in ratios:
            lines.append(f"  Price to Sales (P/S): {ratios['ps_ratio']:.2f}")
        if 'pfcf_ratio' in ratios:
            lines.append(f"  Price to Free Cash Flow (P/FCF): {ratios['pfcf_ratio']:.2f}")
        if 'ev_ebitda' in ratios:
            lines.append(f"  EV/EBITDA: {ratios['ev_ebitda']:.2f}")

        return "\n".join(lines)
