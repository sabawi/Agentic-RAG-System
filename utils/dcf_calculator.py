"""
DCF (Discounted Cash Flow) Calculator

Calculates intrinsic value using DCF valuation model.

Part of: FUNDAMENTAL_ANALYSIS_DCF_IMPLEMENTATION_PLAN.md - Day 4 Implementation
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DCFCalculator:
    """
    DCF valuation model calculator.

    Calculates:
    - Free Cash Flow (FCF)
    - WACC (Weighted Average Cost of Capital)
    - Projected cash flows
    - Terminal value
    - Intrinsic value per share
    - Sensitivity analysis
    """

    def __init__(self):
        """Initialize calculator with default assumptions."""
        # Default assumptions
        self.projection_years = 5
        self.terminal_growth_rate = 0.025  # 2.5%
        self.risk_free_rate = 0.04  # 4% (10-year Treasury yield)
        self.market_risk_premium = 0.07  # 7% (historical average)

        # WACC adjustment for blue-chip companies
        # CAPM often overestimates cost of equity for mature, cash-rich companies
        self.blue_chip_wacc_adjustment = 0.02  # Reduce WACC by 2% for blue chips

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

    def calculate_free_cash_flow(self, cash_flow: pd.DataFrame) -> Optional[float]:
        """
        Calculate Free Cash Flow.

        FCF = Operating Cash Flow - Capital Expenditures
        """
        ocf = self._get_value(cash_flow, 'Operating Cash Flow')
        capex = self._get_value(cash_flow, 'Capital Expenditure')

        if ocf is not None and capex is not None:
            # CapEx is typically negative in the data
            fcf = ocf + capex
            return fcf
        return None

    def calculate_historical_growth_rate(self, cash_flow: pd.DataFrame, periods: int = 3) -> Optional[float]:
        """
        Calculate historical FCF growth rate.

        Uses CAGR (Compound Annual Growth Rate) formula:
        CAGR = (Ending Value / Beginning Value)^(1/years) - 1
        """
        try:
            if cash_flow is None or cash_flow.empty:
                return None

            if len(cash_flow.columns) < periods + 1:
                periods = len(cash_flow.columns) - 1

            if periods < 1:
                return None

            # Get FCF for each available period
            fcf_values = []
            for i in range(min(periods + 1, len(cash_flow.columns))):
                ocf = self._get_value(cash_flow, 'Operating Cash Flow', i)
                capex = self._get_value(cash_flow, 'Capital Expenditure', i)
                if ocf is not None and capex is not None:
                    fcf_values.append(ocf + capex)

            if len(fcf_values) < 2:
                return None

            # Calculate CAGR
            beginning_value = fcf_values[-1]
            ending_value = fcf_values[0]

            if beginning_value <= 0 or ending_value <= 0:
                # Use simple average growth if values are negative
                growth_rates = []
                for i in range(len(fcf_values) - 1):
                    if fcf_values[i+1] != 0:
                        growth = (fcf_values[i] - fcf_values[i+1]) / abs(fcf_values[i+1])
                        growth_rates.append(growth)
                if growth_rates:
                    return np.median(growth_rates)
                return None

            years = len(fcf_values) - 1
            cagr = (ending_value / beginning_value) ** (1 / years) - 1

            # Cap growth rate at reasonable levels (-50% to +100%)
            cagr = max(min(cagr, 1.0), -0.5)

            return cagr
        except:
            return None

    def calculate_wacc(self, financials: Dict, market_data: Dict) -> Optional[float]:
        """
        Calculate WACC (Weighted Average Cost of Capital).

        WACC = (E/V × Re) + (D/V × Rd × (1-T))

        Where:
        - E = Market value of equity
        - D = Market value of debt
        - V = E + D
        - Re = Cost of equity (using CAPM)
        - Rd = Cost of debt
        - T = Tax rate
        """
        try:
            balance_sheet = financials.get('balance_sheet', {}).get('annual')
            income_stmt = financials.get('income_statement', {}).get('annual')

            if balance_sheet is None or income_stmt is None:
                return None

            # Get market value of equity (market cap)
            market_cap = market_data.get('market_cap')
            if not market_cap:
                return None

            # Get total debt
            total_debt = self._get_value(balance_sheet, 'Total Debt')
            if not total_debt:
                long_term_debt = self._get_value(balance_sheet, 'Long Term Debt') or 0
                current_debt = self._get_value(balance_sheet, 'Current Debt') or 0
                total_debt = long_term_debt + current_debt

            if not total_debt or total_debt <= 0:
                # If no debt, WACC = Cost of Equity
                cost_of_equity = self.calculate_cost_of_equity(market_data)
                return cost_of_equity

            # Calculate cost of equity using CAPM
            cost_of_equity = self.calculate_cost_of_equity(market_data)
            if not cost_of_equity:
                return None

            # Calculate cost of debt
            interest_expense = self._get_value(income_stmt, 'Interest Expense')
            if interest_expense and total_debt > 0:
                cost_of_debt = abs(interest_expense) / total_debt
            else:
                # Use approximation: 5% for investment grade
                cost_of_debt = 0.05

            # Calculate tax rate
            pretax_income = self._get_value(income_stmt, 'Pretax Income')
            tax_provision = self._get_value(income_stmt, 'Tax Provision')
            if pretax_income and tax_provision and pretax_income > 0:
                tax_rate = tax_provision / pretax_income
            else:
                # Use corporate tax rate approximation
                tax_rate = 0.21

            # Calculate WACC
            total_value = market_cap + total_debt
            equity_weight = market_cap / total_value
            debt_weight = total_debt / total_value

            wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1 - tax_rate))

            return wacc

        except Exception as e:
            logger.warning(f"Error calculating WACC: {e}")
            return None

    def calculate_cost_of_equity(self, market_data: Dict) -> Optional[float]:
        """
        Calculate cost of equity using CAPM.

        Re = Rf + β × (Rm - Rf)

        Where:
        - Rf = Risk-free rate
        - β = Beta
        - Rm - Rf = Market risk premium
        """
        beta = market_data.get('beta')

        if not beta:
            # Use market average beta
            beta = 1.0

        cost_of_equity = self.risk_free_rate + (beta * self.market_risk_premium)
        return cost_of_equity

    def project_cash_flows(self, current_fcf: float, growth_rate: float, years: int) -> List[float]:
        """
        Project future free cash flows.

        FCF(t) = FCF(t-1) × (1 + growth_rate)
        """
        projected_fcf = []
        fcf = current_fcf

        for year in range(1, years + 1):
            fcf = fcf * (1 + growth_rate)
            projected_fcf.append(fcf)

        return projected_fcf

    def calculate_terminal_value(self, final_fcf: float, wacc: float, terminal_growth: float) -> float:
        """
        Calculate terminal value using Gordon Growth Model.

        TV = FCF(n+1) / (WACC - g)
        """
        if wacc <= terminal_growth:
            # Invalid: WACC must be greater than terminal growth rate
            # Use conservative terminal growth
            terminal_growth = wacc * 0.5

        fcf_terminal = final_fcf * (1 + terminal_growth)
        terminal_value = fcf_terminal / (wacc - terminal_growth)

        return terminal_value

    def calculate_present_value(self, cash_flows: List[float], discount_rate: float) -> float:
        """
        Calculate present value of cash flows.

        PV = CF / (1 + r)^t
        """
        pv = 0
        for t, cf in enumerate(cash_flows, start=1):
            pv += cf / ((1 + discount_rate) ** t)
        return pv

    def calculate_intrinsic_value(self, ticker: str, financials: Dict, market_data: Dict = None) -> Dict[str, Any]:
        """
        Calculate intrinsic value using DCF model.

        Args:
            ticker: Stock ticker symbol
            financials: Financial statements from extractor
            market_data: Market data (price, shares, market cap) - optional

        Returns:
            Dictionary with intrinsic value, upside/downside, and analysis
        """
        logger.info(f"Calculating DCF for {ticker}")

        result = {
            'ticker': ticker,
            'assumptions': {},
            'calculations': {},
            'intrinsic_value': None,
            'current_price': None,
            'upside_downside': None,
            'error': None
        }

        try:
            # Extract financial statements
            cash_flow = financials.get('cash_flow', {}).get('annual')
            balance_sheet = financials.get('balance_sheet', {}).get('annual')
            income_stmt = financials.get('income_statement', {}).get('annual')

            if cash_flow is None or cash_flow.empty:
                result['error'] = 'Cash flow data not available'
                return result

            # Use ticker_info as market_data if not provided separately
            if market_data is None:
                market_data = financials.get('ticker_info', {})

            # Step 1: Calculate current FCF
            current_fcf = self.calculate_free_cash_flow(cash_flow)
            if not current_fcf:
                result['error'] = 'Unable to calculate Free Cash Flow'
                return result

            result['calculations']['current_fcf'] = current_fcf

            # Step 2: Calculate historical growth rate
            historical_growth = self.calculate_historical_growth_rate(cash_flow, periods=3)
            if historical_growth is not None:
                result['calculations']['historical_growth'] = historical_growth
                # Use conservative estimate: average of historical and long-term sustainable (5%)
                projection_growth = (historical_growth + 0.05) / 2
                # Cap at 20% for safety
                projection_growth = min(projection_growth, 0.20)
            else:
                projection_growth = 0.05  # Default 5% growth

            result['assumptions']['projection_growth'] = projection_growth

            # Step 3: Calculate WACC
            wacc = self.calculate_wacc(financials, market_data)
            if not wacc:
                # Use cost of equity as fallback
                wacc = self.calculate_cost_of_equity(market_data)
            if not wacc:
                wacc = 0.10  # Default 10% discount rate

            # Apply blue-chip adjustment for large-cap companies
            # CAPM often overestimates discount rate for mature, cash-rich companies
            market_cap = market_data.get('market_cap') or market_data.get('marketCap')
            is_blue_chip = market_cap and market_cap > 1e12  # $1 trillion+

            wacc_unadjusted = wacc
            if is_blue_chip:
                wacc = max(wacc - self.blue_chip_wacc_adjustment, 0.08)  # Floor at 8%
                result['assumptions']['wacc_adjustment'] = 'Blue-chip adjustment applied (-2%)'

            result['assumptions']['wacc'] = wacc
            result['assumptions']['wacc_unadjusted'] = wacc_unadjusted
            result['assumptions']['terminal_growth'] = self.terminal_growth_rate

            # Step 4: Project future cash flows
            projected_fcf = self.project_cash_flows(
                current_fcf,
                projection_growth,
                self.projection_years
            )
            result['calculations']['projected_fcf'] = projected_fcf

            # Step 5: Calculate terminal value
            terminal_value = self.calculate_terminal_value(
                projected_fcf[-1],
                wacc,
                self.terminal_growth_rate
            )
            result['calculations']['terminal_value'] = terminal_value

            # Step 6: Calculate present values
            pv_projected_fcf = self.calculate_present_value(projected_fcf, wacc)
            pv_terminal_value = terminal_value / ((1 + wacc) ** self.projection_years)

            result['calculations']['pv_projected_fcf'] = pv_projected_fcf
            result['calculations']['pv_terminal_value'] = pv_terminal_value

            # Step 7: Calculate enterprise value
            enterprise_value = pv_projected_fcf + pv_terminal_value
            result['calculations']['enterprise_value'] = enterprise_value

            # Step 8: Calculate equity value
            # EV - Net Debt = Equity Value
            total_debt = self._get_value(balance_sheet, 'Total Debt')
            if not total_debt:
                long_term_debt = self._get_value(balance_sheet, 'Long Term Debt') or 0
                current_debt = self._get_value(balance_sheet, 'Current Debt') or 0
                total_debt = long_term_debt + current_debt

            cash = self._get_value(balance_sheet, 'Cash And Cash Equivalents') or 0
            net_debt = (total_debt or 0) - cash

            equity_value = enterprise_value - net_debt
            result['calculations']['equity_value'] = equity_value

            # Step 9: Calculate intrinsic value per share
            shares_outstanding = market_data.get('sharesOutstanding')
            if not shares_outstanding:
                # Try to calculate from market cap and price
                market_cap = market_data.get('market_cap') or market_data.get('marketCap')
                current_price = market_data.get('current_price') or market_data.get('currentPrice')
                if market_cap and current_price and current_price > 0:
                    shares_outstanding = market_cap / current_price

            if shares_outstanding and shares_outstanding > 0:
                intrinsic_value_per_share = equity_value / shares_outstanding
                result['intrinsic_value'] = intrinsic_value_per_share

                # Step 10: Calculate upside/downside
                current_price = market_data.get('current_price') or market_data.get('currentPrice')
                if current_price:
                    result['current_price'] = current_price
                    upside_downside = ((intrinsic_value_per_share - current_price) / current_price) * 100
                    result['upside_downside'] = upside_downside
            else:
                result['error'] = 'Shares outstanding data not available'

            return result

        except Exception as e:
            logger.error(f"Error calculating DCF for {ticker}: {e}")
            result['error'] = str(e)
            return result

    def _format_source_block(self, source_num: int, title: str, url: str, date: str, content: str) -> str:
        """
        Format content into standardized SOURCE block format for LLM context.

        This follows the Context Engineering Citation Mastery format.

        Args:
            source_num: Sequential source number
            title: Title of the analysis
            url: URL to the source
            date: Analysis date
            content: Formatted DCF data

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

    def format_dcf_for_llm(self, dcf_result: Dict, ticker: str = None) -> str:
        """
        Format DCF results for LLM consumption in SOURCE block format.

        Args:
            dcf_result: DCF calculation results
            ticker: Stock ticker for URL attribution

        Returns:
            Formatted string in SOURCE block format
        """
        if dcf_result.get('error'):
            return f"\n⚠️ **DCF VALUATION ANALYSIS** - {dcf_result['error']}\n"

        if not ticker:
            ticker = dcf_result.get('ticker', 'UNKNOWN')

        current_date = pd.Timestamp.now().strftime('%Y-%m-%d')

        # Format DCF summary
        content_lines = ["DCF VALUATION MODEL RESULTS:"]

        # Current metrics
        if 'current_fcf' in dcf_result.get('calculations', {}):
            fcf = dcf_result['calculations']['current_fcf']
            content_lines.append(f"  Current Free Cash Flow: ${fcf/1e9:.2f}B")

        # Assumptions
        if dcf_result.get('assumptions'):
            assumptions = dcf_result['assumptions']
            if 'projection_growth' in assumptions:
                content_lines.append(f"  Projected FCF Growth Rate: {assumptions['projection_growth']*100:.1f}%")
            if 'wacc' in assumptions:
                wacc_line = f"  Discount Rate (WACC): {assumptions['wacc']*100:.1f}%"
                if 'wacc_unadjusted' in assumptions:
                    wacc_line += f" (adjusted from {assumptions['wacc_unadjusted']*100:.1f}%)"
                content_lines.append(wacc_line)
            if 'terminal_growth' in assumptions:
                content_lines.append(f"  Terminal Growth Rate: {assumptions['terminal_growth']*100:.1f}%")

            # Add sensitivity warning
            if 'wacc_adjustment' in assumptions:
                content_lines.append(f"\nNOTE: {assumptions['wacc_adjustment']}")

        # Valuation results
        if dcf_result.get('intrinsic_value'):
            iv = dcf_result['intrinsic_value']
            content_lines.append(f"\nINTRINSIC VALUE PER SHARE: ${iv:.2f}")

            if dcf_result.get('current_price'):
                cp = dcf_result['current_price']
                content_lines.append(f"  Current Market Price: ${cp:.2f}")

            if dcf_result.get('upside_downside') is not None:
                upside = dcf_result['upside_downside']
                direction = "upside" if upside > 0 else "downside"
                content_lines.append(f"  Potential {direction.upper()}: {abs(upside):.1f}%")

        content = "\n".join(content_lines)

        # Create SOURCE block
        source_block = self._format_source_block(
            source_num=1,
            title=f"{ticker} DCF Valuation Analysis",
            url=f"https://finance.yahoo.com/quote/{ticker}/analysis",
            date=current_date,
            content=content
        )

        return source_block
