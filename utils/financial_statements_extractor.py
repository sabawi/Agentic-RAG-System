"""
Financial Statements Extractor

Extracts complete financial statements from yfinance.

Part of: FUNDAMENTAL_ANALYSIS_DCF_IMPLEMENTATION_PLAN.md - Day 2 Implementation
"""

import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FinancialStatementsExtractor:
    """
    Extract and format financial statements from yfinance.

    Extracts:
    - Income Statement (annual + quarterly)
    - Balance Sheet (annual + quarterly)
    - Cash Flow Statement (annual + quarterly)
    """

    def __init__(self):
        """Initialize the extractor."""
        pass

    def _format_source_block(self, source_num: int, title: str, url: str, date: str, content: str) -> str:
        """
        Format content into standardized SOURCE block format for LLM context.

        This follows the Context Engineering Citation Mastery format to ensure
        100% citation accuracy and prevent URL hallucination.

        Args:
            source_num: Sequential source number
            title: Title of the financial statement
            url: URL to the source data on Yahoo Finance
            date: Fiscal period date
            content: Formatted financial data (will be truncated to 500 chars if needed)

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

    def extract_financials(self, ticker: str) -> Dict[str, Any]:
        """
        Extract all financial statements for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Dictionary containing all financial statements

        Raises:
            Exception: If unable to fetch financial data
        """
        try:
            import yfinance as yf

            logger.info(f"Extracting financial statements for {ticker}")
            ticker_obj = yf.Ticker(ticker)

            result = {
                'income_statement': {
                    'annual': ticker_obj.financials,
                    'quarterly': ticker_obj.quarterly_financials
                },
                'balance_sheet': {
                    'annual': ticker_obj.balance_sheet,
                    'quarterly': ticker_obj.quarterly_balance_sheet
                },
                'cash_flow': {
                    'annual': ticker_obj.cashflow,
                    'quarterly': ticker_obj.quarterly_cashflow
                },
                'ticker_info': ticker_obj.info
            }

            logger.info(f"Successfully extracted financial statements for {ticker}")
            return result

        except Exception as e:
            logger.error(f"Error extracting financials for {ticker}: {e}")
            return {}

    def format_for_llm(self, financials: Dict[str, Any], ticker: str = None) -> str:
        """
        Format all financial statements for LLM consumption using SOURCE block format.

        Args:
            financials: Dictionary from extract_financials()
            ticker: Stock ticker symbol for URL attribution

        Returns:
            Formatted string with all financial statements in SOURCE block format
        """
        if not financials:
            return "⚠️ Financial statements data not available"

        output = []
        source_num = 1

        # Get ticker from info if not provided
        if not ticker and 'ticker_info' in financials:
            ticker = financials['ticker_info'].get('symbol', 'UNKNOWN')

        # Format income statement
        if 'income_statement' in financials:
            income_stmt = financials['income_statement'].get('annual')
            if income_stmt is not None and not income_stmt.empty:
                fiscal_date = income_stmt.columns[0].strftime('%Y-%m-%d') if hasattr(income_stmt.columns[0], 'strftime') else str(income_stmt.columns[0])
                source_block = self._format_source_block(
                    source_num=source_num,
                    title=f"{ticker} Annual Income Statement",
                    url=f"https://finance.yahoo.com/quote/{ticker}/financials",
                    date=fiscal_date,
                    content=self.format_income_statement(income_stmt)
                )
                output.append(source_block)
                source_num += 1

        # Format balance sheet
        if 'balance_sheet' in financials:
            balance_sheet = financials['balance_sheet'].get('annual')
            if balance_sheet is not None and not balance_sheet.empty:
                fiscal_date = balance_sheet.columns[0].strftime('%Y-%m-%d') if hasattr(balance_sheet.columns[0], 'strftime') else str(balance_sheet.columns[0])
                source_block = self._format_source_block(
                    source_num=source_num,
                    title=f"{ticker} Annual Balance Sheet",
                    url=f"https://finance.yahoo.com/quote/{ticker}/balance-sheet",
                    date=fiscal_date,
                    content=self.format_balance_sheet(balance_sheet)
                )
                output.append(source_block)
                source_num += 1

        # Format cash flow statement
        if 'cash_flow' in financials:
            cash_flow = financials['cash_flow'].get('annual')
            if cash_flow is not None and not cash_flow.empty:
                fiscal_date = cash_flow.columns[0].strftime('%Y-%m-%d') if hasattr(cash_flow.columns[0], 'strftime') else str(cash_flow.columns[0])
                source_block = self._format_source_block(
                    source_num=source_num,
                    title=f"{ticker} Annual Cash Flow Statement",
                    url=f"https://finance.yahoo.com/quote/{ticker}/cash-flow",
                    date=fiscal_date,
                    content=self.format_cash_flow_statement(cash_flow)
                )
                output.append(source_block)
                source_num += 1

        if not output:
            return "⚠️ Financial statements data not available"

        return "\n".join(output)

    def format_income_statement(self, income_stmt: pd.DataFrame) -> str:
        """
        Format income statement data (content only, no headers).

        Args:
            income_stmt: DataFrame with income statement data

        Returns:
            Formatted string (data only)
        """
        if income_stmt.empty:
            return "Income statement data not available"

        # Get most recent year
        latest_col = income_stmt.columns[0]

        output = []

        # Key line items to extract
        line_items = [
            ('Total Revenue', 'Revenue'),
            ('Cost Of Revenue', 'Cost of Goods Sold'),
            ('Gross Profit', 'Gross Profit'),
            ('Operating Expense', 'Operating Expenses'),
            ('Operating Income', 'Operating Income (EBIT)'),
            ('Interest Expense', 'Interest Expense'),
            ('Tax Provision', 'Income Tax'),
            ('Net Income', 'Net Income')
        ]

        for key, label in line_items:
            if key in income_stmt.index:
                value = income_stmt.loc[key, latest_col]
                if pd.notna(value):
                    output.append(f"{label}: ${self._format_number(value)}")

        return "\n".join(output)

    def format_balance_sheet(self, balance_sheet: pd.DataFrame) -> str:
        """
        Format balance sheet data (content only, no headers).

        Args:
            balance_sheet: DataFrame with balance sheet data

        Returns:
            Formatted string (data only)
        """
        if balance_sheet.empty:
            return "Balance sheet data not available"

        latest_col = balance_sheet.columns[0]

        output = []

        # Assets
        output.append("ASSETS:")
        asset_items = [
            ('Cash And Cash Equivalents', 'Cash & Cash Equivalents'),
            ('Accounts Receivable', 'Accounts Receivable'),
            ('Inventory', 'Inventory'),
            ('Current Assets', 'Total Current Assets'),
            ('Net PPE', 'Property, Plant & Equipment (Net)'),
            ('Total Assets', 'Total Assets')
        ]

        for key, label in asset_items:
            if key in balance_sheet.index:
                value = balance_sheet.loc[key, latest_col]
                if pd.notna(value):
                    output.append(f"  {label}: ${self._format_number(value)}")

        # Liabilities
        output.append("\nLIABILITIES:")
        liability_items = [
            ('Accounts Payable', 'Accounts Payable'),
            ('Current Debt', 'Short-term Debt'),
            ('Current Liabilities', 'Total Current Liabilities'),
            ('Long Term Debt', 'Long-term Debt'),
            ('Total Liabilities Net Minority Interest', 'Total Liabilities'),
        ]

        for key, label in liability_items:
            if key in balance_sheet.index:
                value = balance_sheet.loc[key, latest_col]
                if pd.notna(value):
                    output.append(f"  {label}: ${self._format_number(value)}")

        # Equity
        output.append("\nSHAREHOLDERS' EQUITY:")
        if 'Stockholders Equity' in balance_sheet.index:
            equity = balance_sheet.loc['Stockholders Equity', latest_col]
            if pd.notna(equity):
                output.append(f"  Total Equity: ${self._format_number(equity)}")

        return "\n".join(output)

    def format_cash_flow_statement(self, cash_flow: pd.DataFrame) -> str:
        """
        Format cash flow statement data (content only, no headers).

        Args:
            cash_flow: DataFrame with cash flow data

        Returns:
            Formatted string (data only)
        """
        if cash_flow.empty:
            return "Cash flow statement data not available"

        latest_col = cash_flow.columns[0]

        output = []

        # Operating activities
        output.append("OPERATING ACTIVITIES:")
        if 'Operating Cash Flow' in cash_flow.index:
            value = cash_flow.loc['Operating Cash Flow', latest_col]
            if pd.notna(value):
                output.append(f"  Operating Cash Flow: ${self._format_number(value)}")

        # Investing activities
        output.append("\nINVESTING ACTIVITIES:")
        investing_items = [
            ('Capital Expenditure', 'Capital Expenditures'),
            ('Investing Cash Flow', 'Investing Cash Flow'),
        ]

        for key, label in investing_items:
            if key in cash_flow.index:
                value = cash_flow.loc[key, latest_col]
                if pd.notna(value):
                    output.append(f"  {label}: ${self._format_number(value)}")

        # Financing activities
        output.append("\nFINANCING ACTIVITIES:")
        financing_items = [
            ('Repurchase Of Capital Stock', 'Stock Repurchases'),
            ('Cash Dividends Paid', 'Dividends Paid'),
            ('Financing Cash Flow', 'Financing Cash Flow'),
        ]

        for key, label in financing_items:
            if key in cash_flow.index:
                value = cash_flow.loc[key, latest_col]
                if pd.notna(value):
                    output.append(f"  {label}: ${self._format_number(value)}")

        # Free Cash Flow
        if 'Operating Cash Flow' in cash_flow.index and 'Capital Expenditure' in cash_flow.index:
            ocf = cash_flow.loc['Operating Cash Flow', latest_col]
            capex = cash_flow.loc['Capital Expenditure', latest_col]
            if pd.notna(ocf) and pd.notna(capex):
                fcf = ocf + capex  # CapEx is negative
                output.append(f"\nFREE CASH FLOW: ${self._format_number(fcf)}")

        return "\n".join(output)

    def _format_number(self, value) -> str:
        """
        Format large numbers with B/M/K suffix.

        Args:
            value: Number to format

        Returns:
            Formatted string (e.g., "$123.45B")
        """
        try:
            if pd.isna(value):
                return "N/A"

            abs_value = abs(value)
            if abs_value >= 1e9:
                return f"{value/1e9:.2f}B"
            elif abs_value >= 1e6:
                return f"{value/1e6:.2f}M"
            elif abs_value >= 1e3:
                return f"{value/1e3:.2f}K"
            else:
                return f"{value:.2f}"
        except:
            return str(value)
