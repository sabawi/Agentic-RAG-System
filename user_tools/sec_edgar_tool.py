"""
SEC EDGAR Integration Tool

Provides access to SEC regulatory filings, insider trading, and institutional holdings.

This tool retrieves official SEC filings data which is authoritative and FREE.
All output is formatted with Context Engineering standards for perfect LLM citations.
"""

from typing import Dict, Any, List
from user_tools.base_user_tool import BaseUserTool
from utils.sec_edgar_client import SECEdgarClient
from config.feature_flags import FeatureFlags
import logging

logger = logging.getLogger(__name__)


class SECEdgarTool(BaseUserTool):
    """
    Tool for accessing SEC EDGAR filings data.

    Features:
    - 10-K, 10-Q, 8-K regulatory filings
    - Form 4 insider trading data
    - 13-F institutional holdings
    - Automatic caching for performance
    - Context Engineering compliant output (SOURCE blocks)
    """

    def __init__(self):
        super().__init__()
        self.client = SECEdgarClient()

    @property
    def name(self) -> str:
        return "get_sec_filings"

    @property
    def description(self) -> str:
        return """Get SEC regulatory filings for a company ticker.

Available filing types:
- 10-K: Annual financial statements and business overview
- 10-Q: Quarterly financial statements and updates
- 8-K: Material events (mergers, executive changes, earnings, etc.)
- Form 4: Insider trading transactions by executives/directors
- 13-F: Institutional holdings by large investment firms

Use this tool when you need official regulatory filings, insider trading activity, or institutional ownership data for a publicly traded company.

Returns authoritative data from SEC EDGAR public filings with proper citations."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Company stock ticker symbol (e.g., 'TSLA', 'AAPL', 'MSFT')"
                },
                "filing_types": {
                    "type": "array",
                    "description": "Types of filings to retrieve. Defaults to ['10-K', '10-Q', '8-K']",
                    "items": {
                        "type": "string"
                    },
                    "default": ["10-K", "10-Q", "8-K"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of filings to return (1-20). Defaults to 5",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["ticker"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute SEC filings retrieval.

        Args:
            ticker: Stock ticker symbol (required)
            filing_types: List of form types (optional, default: ['10-K', '10-Q', '8-K'])
            limit: Maximum number of filings (optional, default: 5)

        Returns:
            Dict with success, result (formatted filings), or error
        """
        # Feature flag check
        if not FeatureFlags.ENABLE_SEC_EDGAR:
            return {
                "success": False,
                "error": "SEC EDGAR integration is currently disabled. Please use comprehensive_stock_analyzer for basic stock data."
            }

        try:
            # Extract parameters
            ticker = kwargs.get('ticker')
            if not ticker:
                return {
                    "success": False,
                    "error": "'ticker' parameter is required"
                }

            filing_types = kwargs.get('filing_types', ['10-K', '10-Q', '8-K'])
            limit = kwargs.get('limit', 5)

            # Validate limit
            if not isinstance(limit, int) or limit < 1 or limit > 20:
                limit = 5

            logger.info(f"Fetching SEC filings for {ticker}, types={filing_types}, limit={limit}")

            # Fetch filings with graceful degradation
            try:
                filings = self.client.get_company_filings(
                    ticker=ticker,
                    filing_types=filing_types,
                    limit=limit
                )
            except Exception as e:
                logger.error(f"SEC EDGAR fetch failed: {e}")
                return {
                    "success": False,
                    "error": f"Unable to retrieve SEC filings for {ticker}. The SEC EDGAR API may be temporarily unavailable. Please try again later."
                }

            if not filings:
                return {
                    "success": False,
                    "error": f"No SEC filings found for ticker '{ticker}'. Please verify the ticker symbol is correct."
                }

            # Format for LLM consumption (Context Engineering compliant)
            formatted_output = self._format_filings_for_llm(filings, ticker)

            logger.info(f"Successfully retrieved {len(filings)} SEC filings for {ticker}")

            return {
                "success": True,
                "result": formatted_output
            }

        except Exception as e:
            logger.error(f"SEC EDGAR tool execution error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error executing SEC filings search: {str(e)}"
            }

    def _format_filings_for_llm(self, filings: List[Dict[str, Any]], ticker: str) -> str:
        """
        Format filings using Context Engineering standards (SOURCE blocks).

        Each filing is formatted as a SOURCE block with:
        - Title: Filing type and description
        - URL: SEC EDGAR direct link
        - Date: Filing date
        - Content: Key information (truncated to 500 chars)
        """
        output_parts = [f"# SEC EDGAR Filings for {ticker.upper()}\n"]

        for i, filing in enumerate(filings, 1):
            form_type = filing.get('form', 'Unknown')
            filing_date = filing.get('filing_date', 'Unknown')
            accession_number = filing.get('accession_number', '')
            description = filing.get('description', '')
            items = filing.get('items', '')
            report_date = filing.get('report_date', '')

            # Construct SEC EDGAR URL
            # Format: https://www.sec.gov/cgi-bin/viewer?action=view&cik=XXXXX&accession_number=XXXXX&xbrl_type=v
            # For simplicity, we'll link to the filing search
            sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={form_type}&dateb=&owner=exclude&count=10"

            # Build title
            if form_type == '10-K':
                title = f"{ticker} Annual Report (10-K) - {filing_date}"
                type_desc = "Annual Report - Comprehensive financial statements and business overview"
            elif form_type == '10-Q':
                title = f"{ticker} Quarterly Report (10-Q) - {filing_date}"
                type_desc = "Quarterly Report - Financial performance and updates"
            elif form_type == '8-K':
                title = f"{ticker} Current Report (8-K) - {filing_date}"
                type_desc = "Current Report - Material events requiring immediate disclosure"
            elif form_type == '4':
                title = f"{ticker} Insider Trading (Form 4) - {filing_date}"
                type_desc = "Insider Trading - Executive/Director stock transactions"
            elif form_type == '13F':
                title = f"{ticker} Institutional Holdings (13F) - {filing_date}"
                type_desc = "Institutional Holdings - Large fund positions"
            else:
                title = f"{ticker} {form_type} Filing - {filing_date}"
                type_desc = f"{form_type} filing"

            # Build content
            content_parts = [type_desc]

            if report_date and report_date != filing_date:
                content_parts.append(f"Report Period: {report_date}")

            if description:
                content_parts.append(f"Description: {description}")

            if items:
                content_parts.append(f"Items Disclosed: {items}")

            if accession_number:
                content_parts.append(f"Accession Number: {accession_number}")

            content = "\n".join(content_parts)

            # Truncate to 500 characters (Context Engineering standard)
            if len(content) > 500:
                content = content[:497] + "..."

            # Format as SOURCE block
            source_block = f"""SOURCE {i}:
Title: {title}
URL: {sec_url}
Date: {filing_date}
{content}


"""
            output_parts.append(source_block)

        # Add summary footer
        output_parts.append(f"Total filings retrieved: {len(filings)}")
        output_parts.append("Note: This data is sourced from SEC EDGAR public filings and is authoritative.")
        output_parts.append("\n🔗 CITATION RULE: Use exact Title and URL from each SOURCE block in format [Title](URL)")

        return '\n'.join(output_parts)
