# Fundamental Analysis & DCF System Implementation Plan
## Complete Financial Analysis Using Free Data Sources

**Version:** 1.0.0
**Date:** 2025-10-31
**Status:** Ready for Implementation
**Total Cost:** $0/month (using yfinance - already installed!)
**Implementation Time:** 3-5 days

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Capabilities Analysis](#current-capabilities-analysis)
3. [Gap Analysis](#gap-analysis)
4. [Solution Design](#solution-design)
5. [Implementation Plan](#implementation-plan)
6. [Code Design](#code-design)
7. [Testing Strategy](#testing-strategy)
8. [Risk Mitigation](#risk-mitigation)

---

## Executive Summary

### What We're Building

Enhance the existing `comprehensive_stock_analyzer` tool with complete fundamental analysis and DCF valuation capabilities using data already available from yfinance (zero additional cost).

### Key Capabilities to Add

1. **Complete Financial Statements**
   - Income Statement (annual & quarterly)
   - Balance Sheet (annual & quarterly)
   - Cash Flow Statement (annual & quarterly)

2. **Advanced Financial Ratios**
   - Profitability: Gross Margin, Operating Margin, Net Margin, ROA, ROE, ROIC
   - Liquidity: Current Ratio, Quick Ratio, Cash Ratio
   - Leverage: Debt/Equity, Debt/Assets, Interest Coverage
   - Efficiency: Asset Turnover, Inventory Turnover, Receivables Turnover
   - Valuation: P/E, P/B, P/S, EV/EBITDA, P/FCF

3. **DCF Valuation Model**
   - Free Cash Flow calculation
   - WACC (Weighted Average Cost of Capital) calculation
   - Terminal value calculation
   - Intrinsic value estimation
   - Sensitivity analysis

4. **Projections & Forecasting**
   - Revenue growth projections
   - Earnings projections
   - Free cash flow projections
   - Historical trend analysis

5. **Analyst Data Integration**
   - Analyst estimates
   - EPS revisions
   - Price targets
   - Recommendation trends

### Current Status

✅ **Already Have:**
- yfinance library installed and working
- Access to ALL required financial data
- Working stock analyzer tool
- Basic financial metrics (P/E, P/B, ROE, Debt/Equity, etc.)

❌ **Missing:**
- Full financial statement extraction
- Advanced financial ratio calculations
- DCF valuation model
- Multi-year trend analysis
- Projection/forecasting capabilities

### Implementation Approach

> **CRITICAL: Follow "Do Not Break What Works" Principle**

1. **Feature Flag System** - New features start disabled
2. **Optional Enhancement** - Add optional `detailed=True` parameter
3. **Backward Compatible** - Existing functionality unchanged
4. **Graceful Degradation** - Fails safely if data unavailable
5. **No New Dependencies** - Use existing yfinance library

### Success Metrics

| Feature | Target |
|---------|--------|
| Financial Statements | 95%+ complete for most stocks |
| Ratio Calculations | 20+ ratios calculated |
| DCF Model | Intrinsic value calculated for 90%+ stocks |
| Response Time | <5s for complete analysis |
| No Regression | 100% existing functionality works |

---

## Current Capabilities Analysis

### What comprehensive_stock_analyzer Already Provides

```python
# Current output includes:
✅ Current price and daily change
✅ Volume and market cap
✅ Sector and industry
✅ P/E ratio (trailing)
✅ Forward P/E
✅ Dividend yield
✅ Beta
✅ Revenue (TTM)
✅ Revenue growth
✅ Profit margin
✅ ROE
✅ Debt/Equity
✅ Current ratio
✅ Book value
✅ Price/Book
✅ 52-week high/low
✅ Analyst target price
✅ Analyst recommendation
✅ Recent news with sentiment analysis
```

### What yfinance Provides (But We're Not Using)

```python
import yfinance as yf
ticker = yf.Ticker("AAPL")

# Financial Statements (NOT currently extracted)
❌ ticker.financials              # Annual income statement
❌ ticker.quarterly_financials    # Quarterly income statement
❌ ticker.balance_sheet           # Annual balance sheet
❌ ticker.quarterly_balance_sheet # Quarterly balance sheet
❌ ticker.cashflow                # Annual cash flow statement
❌ ticker.quarterly_cashflow      # Quarterly cash flow statement

# Analyst Data (NOT currently extracted)
❌ ticker.analyst_price_targets   # Analyst price targets
❌ ticker.earnings_estimate       # Earnings estimates
❌ ticker.revenue_estimate        # Revenue estimates
❌ ticker.eps_revisions           # EPS revisions
❌ ticker.eps_trend               # EPS trend
❌ ticker.growth_estimates        # Growth estimates

# Earnings Data (NOT currently extracted)
❌ ticker.earnings                # Historical earnings
❌ ticker.quarterly_earnings      # Quarterly earnings
❌ ticker.earnings_dates          # Earnings calendar

# Ownership Data (NOT currently extracted)
❌ ticker.institutional_holders   # Institutional ownership
❌ ticker.insider_transactions    # Insider trades
❌ ticker.insider_purchases       # Insider purchases
❌ ticker.major_holders           # Major shareholders

# Historical Data (LIMITED extraction)
❌ ticker.history(period="5y")    # 5-year historical prices
```

---

## Gap Analysis

### Gap 1: Complete Financial Statements

**Current:** Only summary metrics (revenue, profit margin, etc.)
**Needed:** Full line-by-line financial statements

**Impact:** Cannot do detailed financial analysis or DCF modeling

**Example Missing Data:**
- Income Statement: COGS, Operating Expenses, EBIT, EBITDA, Taxes, etc.
- Balance Sheet: Cash, AR, Inventory, PP&E, Total Liabilities, Equity, etc.
- Cash Flow: Operating CF, Investing CF, Financing CF, CapEx, Free Cash Flow, etc.

### Gap 2: Advanced Financial Ratios

**Current:** 10 basic ratios (P/E, ROE, Debt/Equity, etc.)
**Needed:** 20+ comprehensive ratios across all categories

**Impact:** Limited fundamental analysis capability

**Example Missing Ratios:**
- Profitability: Gross Margin, Operating Margin, ROIC
- Liquidity: Quick Ratio, Cash Ratio
- Efficiency: Asset Turnover, Inventory Turnover, DSO
- Valuation: EV/EBITDA, P/FCF, PEG Ratio

### Gap 3: DCF Valuation Model

**Current:** No intrinsic value calculation
**Needed:** Complete DCF model with sensitivity analysis

**Impact:** Cannot determine if stock is overvalued/undervalued

**Required Calculations:**
1. Free Cash Flow (FCF) = Operating CF - CapEx
2. WACC = (E/V × Re) + (D/V × Rd × (1-Tc))
3. Terminal Value = FCF × (1 + g) / (WACC - g)
4. Enterprise Value = PV(projected FCFs) + PV(terminal value)
5. Equity Value = Enterprise Value - Net Debt
6. Intrinsic Value per Share = Equity Value / Shares Outstanding

### Gap 4: Multi-Year Trend Analysis

**Current:** Single period data (TTM or most recent)
**Needed:** 3-5 year historical trends

**Impact:** Cannot identify growth patterns or trends

**Example Needed:**
- Revenue growth trend (3-5 years)
- Earnings growth trend (3-5 years)
- FCF growth trend (3-5 years)
- Margin expansion/contraction analysis
- Return on capital trends

### Gap 5: Projections & Forecasting

**Current:** Analyst estimates not extracted
**Needed:** Forward-looking projections with multiple scenarios

**Impact:** Cannot project future valuations

**Required:**
- Analyst consensus estimates (revenue, EPS)
- Growth rate calculations (historical + projected)
- Best case / Base case / Worst case scenarios
- Sensitivity analysis

---

## Solution Design

### Design Principle: Enhancement, Not Replacement

```python
# BEFORE (existing functionality - UNCHANGED):
comprehensive_stock_analyzer(ticker="AAPL")
# Returns: Current price, basic metrics, news (works as before)

# AFTER (new optional parameter - ADDITIVE):
comprehensive_stock_analyzer(ticker="AAPL", detailed=True)
# Returns: EVERYTHING above + financial statements + DCF + projections
```

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│         Comprehensive Stock Analyzer Tool (Enhanced)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          Feature Flag: ENABLE_DETAILED_ANALYSIS          │   │
│  │                  (default: False)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────┬───────────┴───────────┬──────────────────┐  │
│  │               │                        │                   │  │
│  ▼               ▼                        ▼                   ▼  │
│  Existing     Financial             DCF Valuation       Projections│
│  Analysis     Statements            Calculator          Engine    │
│  (no change)  Extractor                                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               Financial Ratio Calculator                  │  │
│  │  - Profitability  - Liquidity  - Efficiency  - Valuation │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │   yfinance      │
                   │   (free API)    │
                   └─────────────────┘
```

### Component Design

#### Component 1: Financial Statements Extractor

**Purpose:** Extract complete financial statements from yfinance

**Input:** ticker (string)
**Output:** Dictionary with income statement, balance sheet, cash flow statement

```python
class FinancialStatementsExtractor:
    """Extract and format complete financial statements."""

    def extract_financials(self, ticker_obj) -> Dict:
        """Get all financial statements."""
        return {
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
            }
        }

    def format_for_llm(self, financials: Dict) -> str:
        """Format financial statements for LLM consumption."""
        # Create readable text format
        ...
```

#### Component 2: Financial Ratio Calculator

**Purpose:** Calculate 20+ financial ratios from statements

```python
class FinancialRatioCalculator:
    """Calculate comprehensive financial ratios."""

    def calculate_profitability_ratios(self, financials: Dict) -> Dict:
        """Gross margin, operating margin, net margin, ROA, ROE, ROIC."""
        ...

    def calculate_liquidity_ratios(self, balance_sheet: Dict) -> Dict:
        """Current ratio, quick ratio, cash ratio."""
        ...

    def calculate_leverage_ratios(self, balance_sheet: Dict, income_stmt: Dict) -> Dict:
        """Debt/equity, debt/assets, interest coverage."""
        ...

    def calculate_efficiency_ratios(self, financials: Dict) -> Dict:
        """Asset turnover, inventory turnover, receivables turnover."""
        ...

    def calculate_valuation_ratios(self, market_data: Dict, financials: Dict) -> Dict:
        """P/E, P/B, P/S, EV/EBITDA, P/FCF, PEG."""
        ...
```

#### Component 3: DCF Calculator

**Purpose:** Calculate intrinsic value using DCF model

```python
class DCFCalculator:
    """Discounted Cash Flow valuation model."""

    def calculate_free_cash_flow(self, cash_flow: Dict) -> float:
        """FCF = Operating CF - CapEx"""
        ...

    def calculate_wacc(self, ticker_info: Dict, financials: Dict) -> float:
        """Weighted Average Cost of Capital"""
        # WACC = (E/V × Re) + (D/V × Rd × (1-Tc))
        ...

    def project_cash_flows(self, historical_fcf: List, growth_rate: float, years: int) -> List:
        """Project future cash flows."""
        ...

    def calculate_terminal_value(self, final_fcf: float, wacc: float, terminal_growth: float) -> float:
        """Terminal Value = FCF × (1 + g) / (WACC - g)"""
        ...

    def calculate_intrinsic_value(self, ticker: str) -> Dict:
        """Complete DCF calculation."""
        # 1. Get historical FCF
        # 2. Calculate WACC
        # 3. Project future FCFs
        # 4. Calculate terminal value
        # 5. Discount to present value
        # 6. Calculate equity value
        # 7. Divide by shares outstanding
        ...
```

#### Component 4: Projection Engine

**Purpose:** Generate revenue/earnings projections

```python
class ProjectionEngine:
    """Generate financial projections."""

    def calculate_growth_rates(self, historical_data: List) -> Dict:
        """Calculate historical growth rates (1Y, 3Y, 5Y)."""
        ...

    def project_revenue(self, historical_revenue: List, analyst_estimates: Dict) -> Dict:
        """Project future revenue (base/best/worst case)."""
        ...

    def project_earnings(self, historical_earnings: List, analyst_estimates: Dict) -> Dict:
        """Project future earnings (base/best/worst case)."""
        ...

    def project_free_cash_flow(self, historical_fcf: List, growth_rate: float) -> Dict:
        """Project future FCF."""
        ...
```

---

## Implementation Plan

### Phase 1: Foundation (Day 1)

**Goal:** Set up infrastructure for enhancements

**Tasks:**
1. Create feature flag: `ENABLE_DETAILED_ANALYSIS = False`
2. Add optional `detailed` parameter to tool
3. Create utility modules structure:
   ```
   utils/
   ├── financial_statements_extractor.py
   ├── financial_ratio_calculator.py
   ├── dcf_calculator.py
   └── projection_engine.py
   ```
4. Set up test framework

**Deliverables:**
- Feature flag system working
- Optional parameter implemented (backwards compatible)
- Utility module stubs created
- Test templates ready

---

### Phase 2: Financial Statements Extraction (Day 2)

**Goal:** Extract and format complete financial statements

**Tasks:**

**Morning (3-4 hours):**
1. Implement `FinancialStatementsExtractor.extract_financials()`
   - Extract income statement (annual + quarterly)
   - Extract balance sheet (annual + quarterly)
   - Extract cash flow statement (annual + quarterly)

2. Handle edge cases:
   - Missing data gracefully
   - Different statement formats (by industry)
   - International companies (currency handling)

**Afternoon (3-4 hours):**
3. Implement `FinancialStatementsExtractor.format_for_llm()`
   - Format income statement for readability
   - Format balance sheet for readability
   - Format cash flow statement for readability
   - Create summary views (most recent year + quarterly)

4. Testing:
   - Test with 10 different companies
   - Test with companies missing data
   - Verify formatting is LLM-friendly

**Deliverables:**
- Complete financial statements extracted
- Formatted for LLM consumption
- Handles edge cases gracefully
- Unit tests passing

---

### Phase 3: Financial Ratio Calculator (Day 3)

**Goal:** Calculate 20+ comprehensive financial ratios

**Tasks:**

**Morning (3-4 hours):**
1. Implement Profitability Ratios:
   - Gross Profit Margin = (Revenue - COGS) / Revenue
   - Operating Margin = Operating Income / Revenue
   - Net Profit Margin = Net Income / Revenue
   - ROA = Net Income / Total Assets
   - ROE = Net Income / Shareholders' Equity
   - ROIC = NOPAT / Invested Capital

2. Implement Liquidity Ratios:
   - Current Ratio = Current Assets / Current Liabilities
   - Quick Ratio = (Current Assets - Inventory) / Current Liabilities
   - Cash Ratio = Cash / Current Liabilities

**Afternoon (3-4 hours):**
3. Implement Leverage Ratios:
   - Debt-to-Equity = Total Debt / Total Equity
   - Debt-to-Assets = Total Debt / Total Assets
   - Interest Coverage = EBIT / Interest Expense

4. Implement Efficiency Ratios:
   - Asset Turnover = Revenue / Avg Total Assets
   - Inventory Turnover = COGS / Avg Inventory
   - Receivables Turnover = Revenue / Avg AR
   - Days Sales Outstanding = 365 / Receivables Turnover

5. Implement Valuation Ratios:
   - EV/EBITDA = Enterprise Value / EBITDA
   - P/FCF = Price / Free Cash Flow per Share
   - PEG Ratio = P/E / Earnings Growth Rate

**Deliverables:**
- 20+ ratios calculated
- Industry benchmarking (if available)
- Multi-year trend analysis
- Unit tests for all calculations

---

### Phase 4: DCF Valuation Model (Day 4)

**Goal:** Implement complete DCF valuation

**Tasks:**

**Morning (3-4 hours):**
1. Implement Free Cash Flow calculation:
   ```python
   FCF = Operating Cash Flow - Capital Expenditures
   ```

2. Implement WACC calculation:
   ```python
   # Cost of Equity (using CAPM)
   Re = Risk_Free_Rate + Beta × (Market_Return - Risk_Free_Rate)

   # Cost of Debt
   Rd = Interest_Expense / Total_Debt

   # WACC
   WACC = (E/V × Re) + (D/V × Rd × (1 - Tax_Rate))
   ```

3. Get required inputs:
   - Risk-free rate (10-year Treasury yield)
   - Market risk premium (historical: ~7%)
   - Beta (from yfinance)
   - Tax rate (from income statement)

**Afternoon (3-4 hours):**
4. Implement cash flow projections:
   - Calculate historical FCF growth rate
   - Project 5-year cash flows
   - Calculate terminal value
   - Discount to present value

5. Calculate intrinsic value:
   ```python
   # Present value of projected cash flows
   PV_CFs = sum(FCF_t / (1 + WACC)^t for t in 1..5)

   # Terminal value
   TV = FCF_5 × (1 + g) / (WACC - g)
   PV_TV = TV / (1 + WACC)^5

   # Enterprise value
   EV = PV_CFs + PV_TV

   # Equity value
   Equity_Value = EV - Net_Debt

   # Intrinsic value per share
   Intrinsic_Value = Equity_Value / Shares_Outstanding
   ```

6. Add sensitivity analysis:
   - Vary WACC (±1%, ±2%)
   - Vary terminal growth rate (±0.5%, ±1%)
   - Create sensitivity table

**Deliverables:**
- Complete DCF model working
- Intrinsic value calculated
- Upside/downside vs current price
- Sensitivity analysis table
- Unit tests passing

---

### Phase 5: Projections & Integration (Day 5)

**Goal:** Add projections and integrate everything

**Tasks:**

**Morning (2-3 hours):**
1. Implement Projection Engine:
   - Extract analyst estimates from yfinance
   - Calculate historical growth rates (1Y, 3Y, 5Y)
   - Project revenue (base/best/worst case)
   - Project earnings (base/best/worst case)
   - Project FCF

2. Create multi-scenario analysis:
   - Base case: Analyst consensus
   - Best case: Upper range of estimates
   - Worst case: Lower range of estimates

**Afternoon (3-4 hours):**
3. Integrate all components:
   - Modify `comprehensive_stock_analyzer.execute()`
   - Add logic for `detailed=True` parameter
   - Format complete output for LLM
   - Test end-to-end

4. Final formatting:
   - Create section headers
   - Add visual separators
   - Include interpretation guidance
   - Add caveats and assumptions

**Evening (1-2 hours):**
5. Documentation:
   - Update tool description
   - Document new parameters
   - Create usage examples
   - Document assumptions and limitations

**Deliverables:**
- Complete integration working
- Detailed analysis mode functional
- Comprehensive output formatting
- Documentation complete

---

## Code Design

### Enhanced Tool Interface

```python
class ComprehensiveStockAnalyzerTool(BaseUserTool):
    """Enhanced comprehensive stock analyzer with DCF and fundamental analysis."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol"
                },
                "detailed": {
                    "type": "boolean",
                    "description": "Include detailed financial statements, ratios, and DCF analysis",
                    "default": False
                }
            },
            "required": ["ticker"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute stock analysis (enhanced)."""
        ticker = kwargs.get('ticker')
        detailed = kwargs.get('detailed', False)

        # Feature flag check
        if detailed and not FeatureFlags.ENABLE_DETAILED_ANALYSIS:
            detailed = False  # Fall back to basic analysis

        # EXISTING ANALYSIS (unchanged)
        basic_data = self._get_real_time_data(ticker)
        news_items = self._get_company_news(ticker, basic_data.get('company_name'))
        news_sentiment = self._analyze_news_sentiment(news_items, ticker)
        basic_analysis = self._analyze_data(basic_data, ticker, news_items, news_sentiment)

        # If not detailed, return basic analysis (EXISTING FUNCTIONALITY)
        if not detailed:
            return {
                "ticker": ticker,
                "analysis": basic_analysis,
                "format": "text"
            }

        # DETAILED ANALYSIS (NEW FUNCTIONALITY)
        try:
            # Extract financial statements
            from utils.financial_statements_extractor import FinancialStatementsExtractor
            extractor = FinancialStatementsExtractor()
            financials = extractor.extract_financials(ticker)

            # Calculate financial ratios
            from utils.financial_ratio_calculator import FinancialRatioCalculator
            calculator = FinancialRatioCalculator()
            ratios = calculator.calculate_all_ratios(financials, basic_data)

            # Perform DCF analysis
            from utils.dcf_calculator import DCFCalculator
            dcf = DCFCalculator()
            valuation = dcf.calculate_intrinsic_value(ticker, financials)

            # Generate projections
            from utils.projection_engine import ProjectionEngine
            projections = ProjectionEngine()
            forecasts = projections.generate_projections(ticker, financials)

            # Format detailed analysis
            detailed_analysis = self._format_detailed_analysis(
                basic_analysis,
                financials,
                ratios,
                valuation,
                forecasts
            )

            return {
                "ticker": ticker,
                "analysis": detailed_analysis,
                "format": "text"
            }

        except Exception as e:
            # GRACEFUL DEGRADATION: If detailed analysis fails, return basic
            logger.error(f"Detailed analysis failed: {e}")
            return {
                "ticker": ticker,
                "analysis": basic_analysis + f"\n\n⚠️ Note: Detailed analysis unavailable.",
                "format": "text"
            }
```

### Financial Statements Extractor

```python
"""
Financial Statements Extractor

Extracts complete financial statements from yfinance.
"""

import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class FinancialStatementsExtractor:
    """Extract and format financial statements from yfinance."""

    def extract_financials(self, ticker: str) -> Dict[str, Any]:
        """
        Extract all financial statements.

        Returns:
            Dictionary with income statement, balance sheet, cash flow statement
        """
        try:
            import yfinance as yf
            ticker_obj = yf.Ticker(ticker)

            return {
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
        except Exception as e:
            logger.error(f"Error extracting financials for {ticker}: {e}")
            return {}

    def format_income_statement(self, income_stmt: pd.DataFrame) -> str:
        """Format income statement for LLM."""
        if income_stmt.empty:
            return "Income statement data not available"

        # Get most recent year
        latest_col = income_stmt.columns[0]

        output = ["📊 **INCOME STATEMENT** (Most Recent Annual)\n"]

        # Key line items
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
                output.append(f"{label}: ${self._format_number(value)}")

        return "\n".join(output)

    def format_balance_sheet(self, balance_sheet: pd.DataFrame) -> str:
        """Format balance sheet for LLM."""
        if balance_sheet.empty:
            return "Balance sheet data not available"

        latest_col = balance_sheet.columns[0]

        output = ["📊 **BALANCE SHEET** (Most Recent Annual)\n"]

        # Assets
        output.append("**ASSETS:**")
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
                output.append(f"  {label}: ${self._format_number(value)}")

        # Liabilities
        output.append("\n**LIABILITIES:**")
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
                output.append(f"  {label}: ${self._format_number(value)}")

        # Equity
        output.append("\n**SHAREHOLDERS' EQUITY:**")
        if 'Stockholders Equity' in balance_sheet.index:
            equity = balance_sheet.loc['Stockholders Equity', latest_col]
            output.append(f"  Total Equity: ${self._format_number(equity)}")

        return "\n".join(output)

    def format_cash_flow_statement(self, cash_flow: pd.DataFrame) -> str:
        """Format cash flow statement for LLM."""
        if cash_flow.empty:
            return "Cash flow statement data not available"

        latest_col = cash_flow.columns[0]

        output = ["📊 **CASH FLOW STATEMENT** (Most Recent Annual)\n"]

        # Operating activities
        output.append("**OPERATING ACTIVITIES:**")
        operating_items = [
            ('Operating Cash Flow', 'Operating Cash Flow'),
        ]

        for key, label in operating_items:
            if key in cash_flow.index:
                value = cash_flow.loc[key, latest_col]
                output.append(f"  {label}: ${self._format_number(value)}")

        # Investing activities
        output.append("\n**INVESTING ACTIVITIES:**")
        investing_items = [
            ('Capital Expenditure', 'Capital Expenditures'),
            ('Investing Cash Flow', 'Investing Cash Flow'),
        ]

        for key, label in investing_items:
            if key in cash_flow.index:
                value = cash_flow.loc[key, latest_col]
                output.append(f"  {label}: ${self._format_number(value)}")

        # Financing activities
        output.append("\n**FINANCING ACTIVITIES:**")
        financing_items = [
            ('Repurchase Of Capital Stock', 'Stock Repurchases'),
            ('Cash Dividends Paid', 'Dividends Paid'),
            ('Financing Cash Flow', 'Financing Cash Flow'),
        ]

        for key, label in financing_items:
            if key in cash_flow.index:
                value = cash_flow.loc[key, latest_col]
                output.append(f"  {label}: ${self._format_number(value)}")

        # Free Cash Flow
        if 'Operating Cash Flow' in cash_flow.index and 'Capital Expenditure' in cash_flow.index:
            ocf = cash_flow.loc['Operating Cash Flow', latest_col]
            capex = cash_flow.loc['Capital Expenditure', latest_col]
            fcf = ocf + capex  # CapEx is negative
            output.append(f"\n**FREE CASH FLOW:** ${self._format_number(fcf)}")

        return "\n".join(output)

    def _format_number(self, value) -> str:
        """Format large numbers with B/M/K suffix."""
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
```

### Financial Ratio Calculator

```python
"""
Financial Ratio Calculator

Calculates comprehensive financial ratios from financial statements.
"""

import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class FinancialRatioCalculator:
    """Calculate comprehensive financial ratios."""

    def calculate_all_ratios(self, financials: Dict, market_data: Dict) -> Dict[str, Any]:
        """
        Calculate all financial ratios.

        Args:
            financials: Financial statements from extractor
            market_data: Market data (price, shares, market cap)

        Returns:
            Dictionary of all calculated ratios
        """
        try:
            ratios = {}

            # Extract statements
            income_stmt = financials['income_statement']['annual']
            balance_sheet = financials['balance_sheet']['annual']
            cash_flow = financials['cash_flow']['annual']

            # Calculate ratio categories
            ratios['profitability'] = self._calculate_profitability_ratios(income_stmt, balance_sheet)
            ratios['liquidity'] = self._calculate_liquidity_ratios(balance_sheet)
            ratios['leverage'] = self._calculate_leverage_ratios(balance_sheet, income_stmt)
            ratios['efficiency'] = self._calculate_efficiency_ratios(income_stmt, balance_sheet)
            ratios['valuation'] = self._calculate_valuation_ratios(market_data, financials)

            return ratios

        except Exception as e:
            logger.error(f"Error calculating ratios: {e}")
            return {}

    def _calculate_profitability_ratios(self, income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame) -> Dict:
        """Calculate profitability ratios."""
        ratios = {}

        try:
            latest_col = income_stmt.columns[0]

            # Get values
            revenue = self._get_value(income_stmt, 'Total Revenue', latest_col)
            cogs = self._get_value(income_stmt, 'Cost Of Revenue', latest_col)
            gross_profit = self._get_value(income_stmt, 'Gross Profit', latest_col)
            operating_income = self._get_value(income_stmt, 'Operating Income', latest_col)
            net_income = self._get_value(income_stmt, 'Net Income', latest_col)

            total_assets = self._get_value(balance_sheet, 'Total Assets', balance_sheet.columns[0])
            shareholders_equity = self._get_value(balance_sheet, 'Stockholders Equity', balance_sheet.columns[0])

            # Calculate ratios
            if revenue:
                ratios['gross_margin'] = (gross_profit / revenue) if gross_profit else None
                ratios['operating_margin'] = (operating_income / revenue) if operating_income else None
                ratios['net_profit_margin'] = (net_income / revenue) if net_income else None

            if total_assets and net_income:
                ratios['roa'] = net_income / total_assets

            if shareholders_equity and net_income:
                ratios['roe'] = net_income / shareholders_equity

            # ROIC = NOPAT / Invested Capital
            # Simplified: Net Income / (Total Assets - Current Liabilities)
            current_liabilities = self._get_value(balance_sheet, 'Current Liabilities', balance_sheet.columns[0])
            if net_income and total_assets and current_liabilities:
                invested_capital = total_assets - current_liabilities
                if invested_capital > 0:
                    ratios['roic'] = net_income / invested_capital

        except Exception as e:
            logger.error(f"Error calculating profitability ratios: {e}")

        return ratios

    def _calculate_liquidity_ratios(self, balance_sheet: pd.DataFrame) -> Dict:
        """Calculate liquidity ratios."""
        ratios = {}

        try:
            latest_col = balance_sheet.columns[0]

            current_assets = self._get_value(balance_sheet, 'Current Assets', latest_col)
            current_liabilities = self._get_value(balance_sheet, 'Current Liabilities', latest_col)
            inventory = self._get_value(balance_sheet, 'Inventory', latest_col)
            cash = self._get_value(balance_sheet, 'Cash And Cash Equivalents', latest_col)

            if current_assets and current_liabilities and current_liabilities != 0:
                ratios['current_ratio'] = current_assets / current_liabilities

                # Quick ratio = (Current Assets - Inventory) / Current Liabilities
                if inventory is not None:
                    ratios['quick_ratio'] = (current_assets - inventory) / current_liabilities

                # Cash ratio
                if cash:
                    ratios['cash_ratio'] = cash / current_liabilities

        except Exception as e:
            logger.error(f"Error calculating liquidity ratios: {e}")

        return ratios

    def _calculate_leverage_ratios(self, balance_sheet: pd.DataFrame, income_stmt: pd.DataFrame) -> Dict:
        """Calculate leverage ratios."""
        ratios = {}

        try:
            bs_col = balance_sheet.columns[0]
            is_col = income_stmt.columns[0]

            total_debt = self._get_value(balance_sheet, 'Total Debt', bs_col)
            total_equity = self._get_value(balance_sheet, 'Stockholders Equity', bs_col)
            total_assets = self._get_value(balance_sheet, 'Total Assets', bs_col)
            ebit = self._get_value(income_stmt, 'Operating Income', is_col)
            interest_expense = self._get_value(income_stmt, 'Interest Expense', is_col)

            if total_debt and total_equity and total_equity != 0:
                ratios['debt_to_equity'] = total_debt / total_equity

            if total_debt and total_assets and total_assets != 0:
                ratios['debt_to_assets'] = total_debt / total_assets

            if ebit and interest_expense and interest_expense != 0:
                ratios['interest_coverage'] = ebit / abs(interest_expense)

        except Exception as e:
            logger.error(f"Error calculating leverage ratios: {e}")

        return ratios

    def _calculate_efficiency_ratios(self, income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame) -> Dict:
        """Calculate efficiency ratios."""
        ratios = {}

        try:
            is_col = income_stmt.columns[0]
            bs_col = balance_sheet.columns[0]

            revenue = self._get_value(income_stmt, 'Total Revenue', is_col)
            cogs = self._get_value(income_stmt, 'Cost Of Revenue', is_col)
            total_assets = self._get_value(balance_sheet, 'Total Assets', bs_col)
            inventory = self._get_value(balance_sheet, 'Inventory', bs_col)
            receivables = self._get_value(balance_sheet, 'Accounts Receivable', bs_col)

            # Asset turnover
            if revenue and total_assets and total_assets != 0:
                ratios['asset_turnover'] = revenue / total_assets

            # Inventory turnover
            if cogs and inventory and inventory != 0:
                ratios['inventory_turnover'] = cogs / inventory
                ratios['days_inventory_outstanding'] = 365 / ratios['inventory_turnover']

            # Receivables turnover
            if revenue and receivables and receivables != 0:
                ratios['receivables_turnover'] = revenue / receivables
                ratios['days_sales_outstanding'] = 365 / ratios['receivables_turnover']

        except Exception as e:
            logger.error(f"Error calculating efficiency ratios: {e}")

        return ratios

    def _calculate_valuation_ratios(self, market_data: Dict, financials: Dict) -> Dict:
        """Calculate valuation ratios."""
        ratios = {}

        try:
            # Get market data
            current_price = market_data.get('current_price')
            market_cap = market_data.get('market_cap')
            shares_outstanding = market_data.get('shares_outstanding')

            # Get financial data
            income_stmt = financials['income_statement']['annual']
            balance_sheet = financials['balance_sheet']['annual']
            cash_flow = financials['cash_flow']['annual']

            is_col = income_stmt.columns[0]
            bs_col = balance_sheet.columns[0]
            cf_col = cash_flow.columns[0]

            revenue = self._get_value(income_stmt, 'Total Revenue', is_col)
            net_income = self._get_value(income_stmt, 'Net Income', is_col)
            ebitda = self._get_value(income_stmt, 'EBITDA', is_col)
            book_value = self._get_value(balance_sheet, 'Stockholders Equity', bs_col)

            # Operating CF - CapEx
            ocf = self._get_value(cash_flow, 'Operating Cash Flow', cf_col)
            capex = self._get_value(cash_flow, 'Capital Expenditure', cf_col)
            fcf = (ocf + capex) if (ocf and capex) else None  # CapEx is negative

            # Enterprise Value = Market Cap + Debt - Cash
            total_debt = self._get_value(balance_sheet, 'Total Debt', bs_col)
            cash = self._get_value(balance_sheet, 'Cash And Cash Equivalents', bs_col)
            ev = market_cap
            if total_debt:
                ev += total_debt
            if cash:
                ev -= cash

            # Calculate ratios
            if current_price and net_income and shares_outstanding:
                eps = net_income / shares_outstanding
                ratios['pe_ratio'] = current_price / eps if eps != 0 else None

            if current_price and book_value and shares_outstanding:
                book_value_per_share = book_value / shares_outstanding
                ratios['price_to_book'] = current_price / book_value_per_share if book_value_per_share != 0 else None

            if market_cap and revenue and revenue != 0:
                ratios['price_to_sales'] = market_cap / revenue

            if ev and ebitda and ebitda != 0:
                ratios['ev_to_ebitda'] = ev / ebitda

            if current_price and fcf and shares_outstanding and fcf != 0:
                fcf_per_share = fcf / shares_outstanding
                ratios['price_to_fcf'] = current_price / fcf_per_share if fcf_per_share != 0 else None

            # PEG ratio = P/E / Earnings Growth Rate
            # (Would need historical earnings to calculate growth rate)

        except Exception as e:
            logger.error(f"Error calculating valuation ratios: {e}")

        return ratios

    def _get_value(self, df: pd.DataFrame, key: str, col) -> float:
        """Safely get value from DataFrame."""
        try:
            if key in df.index:
                value = df.loc[key, col]
                return float(value) if pd.notna(value) else None
            return None
        except:
            return None

    def format_ratios_for_llm(self, ratios: Dict) -> str:
        """Format calculated ratios for LLM consumption."""
        output = ["\n📊 **FINANCIAL RATIOS ANALYSIS**\n"]

        # Profitability
        if 'profitability' in ratios and ratios['profitability']:
            output.append("**PROFITABILITY RATIOS:**")
            prof = ratios['profitability']
            if 'gross_margin' in prof and prof['gross_margin']:
                output.append(f"  Gross Margin: {prof['gross_margin']:.2%}")
            if 'operating_margin' in prof and prof['operating_margin']:
                output.append(f"  Operating Margin: {prof['operating_margin']:.2%}")
            if 'net_profit_margin' in prof and prof['net_profit_margin']:
                output.append(f"  Net Profit Margin: {prof['net_profit_margin']:.2%}")
            if 'roa' in prof and prof['roa']:
                output.append(f"  Return on Assets (ROA): {prof['roa']:.2%}")
            if 'roe' in prof and prof['roe']:
                output.append(f"  Return on Equity (ROE): {prof['roe']:.2%}")
            if 'roic' in prof and prof['roic']:
                output.append(f"  Return on Invested Capital (ROIC): {prof['roic']:.2%}")

        # Liquidity
        if 'liquidity' in ratios and ratios['liquidity']:
            output.append("\n**LIQUIDITY RATIOS:**")
            liq = ratios['liquidity']
            if 'current_ratio' in liq and liq['current_ratio']:
                output.append(f"  Current Ratio: {liq['current_ratio']:.2f}")
            if 'quick_ratio' in liq and liq['quick_ratio']:
                output.append(f"  Quick Ratio: {liq['quick_ratio']:.2f}")
            if 'cash_ratio' in liq and liq['cash_ratio']:
                output.append(f"  Cash Ratio: {liq['cash_ratio']:.2f}")

        # Leverage
        if 'leverage' in ratios and ratios['leverage']:
            output.append("\n**LEVERAGE RATIOS:**")
            lev = ratios['leverage']
            if 'debt_to_equity' in lev and lev['debt_to_equity']:
                output.append(f"  Debt-to-Equity: {lev['debt_to_equity']:.2f}")
            if 'debt_to_assets' in lev and lev['debt_to_assets']:
                output.append(f"  Debt-to-Assets: {lev['debt_to_assets']:.2f}")
            if 'interest_coverage' in lev and lev['interest_coverage']:
                output.append(f"  Interest Coverage: {lev['interest_coverage']:.2f}x")

        # Efficiency
        if 'efficiency' in ratios and ratios['efficiency']:
            output.append("\n**EFFICIENCY RATIOS:**")
            eff = ratios['efficiency']
            if 'asset_turnover' in eff and eff['asset_turnover']:
                output.append(f"  Asset Turnover: {eff['asset_turnover']:.2f}")
            if 'inventory_turnover' in eff and eff['inventory_turnover']:
                output.append(f"  Inventory Turnover: {eff['inventory_turnover']:.2f}")
            if 'days_inventory_outstanding' in eff and eff['days_inventory_outstanding']:
                output.append(f"  Days Inventory Outstanding: {eff['days_inventory_outstanding']:.0f} days")
            if 'receivables_turnover' in eff and eff['receivables_turnover']:
                output.append(f"  Receivables Turnover: {eff['receivables_turnover']:.2f}")
            if 'days_sales_outstanding' in eff and eff['days_sales_outstanding']:
                output.append(f"  Days Sales Outstanding: {eff['days_sales_outstanding']:.0f} days")

        # Valuation
        if 'valuation' in ratios and ratios['valuation']:
            output.append("\n**VALUATION RATIOS:**")
            val = ratios['valuation']
            if 'pe_ratio' in val and val['pe_ratio']:
                output.append(f"  P/E Ratio: {val['pe_ratio']:.2f}")
            if 'price_to_book' in val and val['price_to_book']:
                output.append(f"  Price-to-Book: {val['price_to_book']:.2f}")
            if 'price_to_sales' in val and val['price_to_sales']:
                output.append(f"  Price-to-Sales: {val['price_to_sales']:.2f}")
            if 'ev_to_ebitda' in val and val['ev_to_ebitda']:
                output.append(f"  EV/EBITDA: {val['ev_to_ebitda']:.2f}")
            if 'price_to_fcf' in val and val['price_to_fcf']:
                output.append(f"  Price-to-FCF: {val['price_to_fcf']:.2f}")

        return "\n".join(output)
```

### DCF Calculator

```python
"""
DCF (Discounted Cash Flow) Calculator

Calculates intrinsic value using DCF valuation model.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DCFCalculator:
    """DCF valuation model calculator."""

    def __init__(self):
        # Default assumptions
        self.projection_years = 5
        self.terminal_growth_rate = 0.025  # 2.5%
        self.risk_free_rate = 0.04  # 4% (10-year Treasury yield)
        self.market_risk_premium = 0.07  # 7% (historical average)

    def calculate_intrinsic_value(self, ticker: str, financials: Dict) -> Dict[str, Any]:
        """
        Calculate intrinsic value using DCF model.

        Returns:
            Dictionary with intrinsic value, current price, upside/downside
        """
        try:
            # Extract required data
            cash_flow = financials['cash_flow']['annual']
            balance_sheet = financials['balance_sheet']['annual']
            income_stmt = financials['income_statement']['annual']
            ticker_info = financials['ticker_info']

            # Step 1: Calculate Free Cash Flow
            fcf_history = self._calculate_fcf_history(cash_flow)
            if not fcf_history or len(fcf_history) < 2:
                return {"error": "Insufficient cash flow data for DCF"}

            # Step 2: Calculate WACC
            wacc = self._calculate_wacc(ticker_info, balance_sheet, income_stmt)
            if not wacc:
                return {"error": "Unable to calculate WACC"}

            # Step 3: Project future cash flows
            growth_rate = self._calculate_fcf_growth_rate(fcf_history)
            projected_fcfs = self._project_cash_flows(fcf_history[-1], growth_rate, self.projection_years)

            # Step 4: Calculate terminal value
            terminal_fcf = projected_fcfs[-1] * (1 + self.terminal_growth_rate)
            terminal_value = terminal_fcf / (wacc - self.terminal_growth_rate)

            # Step 5: Discount to present value
            pv_projected_fcfs = sum(fcf / (1 + wacc) ** (i + 1) for i, fcf in enumerate(projected_fcfs))
            pv_terminal_value = terminal_value / (1 + wacc) ** self.projection_years

            # Step 6: Calculate enterprise value
            enterprise_value = pv_projected_fcfs + pv_terminal_value

            # Step 7: Calculate equity value
            net_debt = self._calculate_net_debt(balance_sheet)
            equity_value = enterprise_value - net_debt

            # Step 8: Calculate intrinsic value per share
            shares_outstanding = ticker_info.get('sharesOutstanding', 0)
            if shares_outstanding == 0:
                return {"error": "Shares outstanding data not available"}

            intrinsic_value_per_share = equity_value / shares_outstanding

            # Get current price for comparison
            current_price = ticker_info.get('currentPrice', 0)

            # Calculate upside/downside
            if current_price > 0:
                upside = ((intrinsic_value_per_share - current_price) / current_price) * 100
            else:
                upside = 0

            # Sensitivity analysis
            sensitivity = self._sensitivity_analysis(
                fcf_history[-1],
                growth_rate,
                wacc,
                terminal_value,
                net_debt,
                shares_outstanding
            )

            return {
                'intrinsic_value': intrinsic_value_per_share,
                'current_price': current_price,
                'upside_downside_percent': upside,
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'wacc': wacc,
                'fcf_growth_rate': growth_rate,
                'terminal_growth_rate': self.terminal_growth_rate,
                'projected_fcfs': projected_fcfs,
                'fcf_history': fcf_history,
                'sensitivity_analysis': sensitivity
            }

        except Exception as e:
            logger.error(f"Error calculating DCF: {e}", exc_info=True)
            return {"error": str(e)}

    def _calculate_fcf_history(self, cash_flow: pd.DataFrame) -> List[float]:
        """Calculate historical Free Cash Flow."""
        fcf_list = []

        try:
            for col in cash_flow.columns[:5]:  # Last 5 years
                ocf = cash_flow.loc['Operating Cash Flow', col] if 'Operating Cash Flow' in cash_flow.index else 0
                capex = cash_flow.loc['Capital Expenditure', col] if 'Capital Expenditure' in cash_flow.index else 0

                if pd.notna(ocf) and pd.notna(capex):
                    fcf = ocf + capex  # CapEx is negative
                    fcf_list.append(fcf)

            # Reverse to get chronological order (oldest to newest)
            fcf_list.reverse()

        except Exception as e:
            logger.error(f"Error calculating FCF history: {e}")

        return fcf_list

    def _calculate_fcf_growth_rate(self, fcf_history: List[float]) -> float:
        """Calculate historical FCF growth rate (CAGR)."""
        try:
            if len(fcf_history) < 2:
                return 0.05  # Default 5%

            years = len(fcf_history) - 1
            cagr = (fcf_history[-1] / fcf_history[0]) ** (1 / years) - 1

            # Cap growth rate at reasonable levels
            cagr = max(min(cagr, 0.25), -0.15)  # Between -15% and 25%

            return cagr

        except:
            return 0.05  # Default 5%

    def _calculate_wacc(self, ticker_info: Dict, balance_sheet: pd.DataFrame, income_stmt: pd.DataFrame) -> float:
        """Calculate Weighted Average Cost of Capital (WACC)."""
        try:
            # Get market value of equity (market cap)
            market_cap = ticker_info.get('marketCap', 0)
            if market_cap == 0:
                return None

            # Get total debt
            bs_col = balance_sheet.columns[0]
            total_debt = balance_sheet.loc['Total Debt', bs_col] if 'Total Debt' in balance_sheet.index else 0
            total_debt = float(total_debt) if pd.notna(total_debt) else 0

            # Total value
            total_value = market_cap + total_debt
            if total_value == 0:
                return None

            # Weight of equity and debt
            weight_equity = market_cap / total_value
            weight_debt = total_debt / total_value

            # Cost of Equity (using CAPM): Re = Rf + Beta × (Rm - Rf)
            beta = ticker_info.get('beta', 1.0)
            cost_of_equity = self.risk_free_rate + beta * self.market_risk_premium

            # Cost of Debt: Interest Expense / Total Debt
            is_col = income_stmt.columns[0]
            interest_expense = income_stmt.loc['Interest Expense', is_col] if 'Interest Expense' in income_stmt.index else 0
            interest_expense = float(interest_expense) if pd.notna(interest_expense) else 0

            if total_debt > 0 and interest_expense != 0:
                cost_of_debt = abs(interest_expense) / total_debt
            else:
                cost_of_debt = 0.04  # Default 4%

            # Tax rate
            tax_provision = income_stmt.loc['Tax Provision', is_col] if 'Tax Provision' in income_stmt.index else 0
            pretax_income = income_stmt.loc['Pretax Income', is_col] if 'Pretax Income' in income_stmt.index else 0

            tax_provision = float(tax_provision) if pd.notna(tax_provision) else 0
            pretax_income = float(pretax_income) if pd.notna(pretax_income) else 0

            if pretax_income != 0:
                tax_rate = tax_provision / pretax_income
                tax_rate = max(0, min(tax_rate, 0.35))  # Cap at 35%
            else:
                tax_rate = 0.21  # Default corporate tax rate

            # WACC = (E/V × Re) + (D/V × Rd × (1 - Tc))
            wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))

            return wacc

        except Exception as e:
            logger.error(f"Error calculating WACC: {e}")
            return None

    def _project_cash_flows(self, last_fcf: float, growth_rate: float, years: int) -> List[float]:
        """Project future cash flows."""
        projected_fcfs = []

        for year in range(1, years + 1):
            fcf = last_fcf * (1 + growth_rate) ** year
            projected_fcfs.append(fcf)

        return projected_fcfs

    def _calculate_net_debt(self, balance_sheet: pd.DataFrame) -> float:
        """Calculate net debt (Total Debt - Cash)."""
        try:
            bs_col = balance_sheet.columns[0]

            total_debt = balance_sheet.loc['Total Debt', bs_col] if 'Total Debt' in balance_sheet.index else 0
            total_debt = float(total_debt) if pd.notna(total_debt) else 0

            cash = balance_sheet.loc['Cash And Cash Equivalents', bs_col] if 'Cash And Cash Equivalents' in balance_sheet.index else 0
            cash = float(cash) if pd.notna(cash) else 0

            return total_debt - cash

        except:
            return 0

    def _sensitivity_analysis(
        self,
        base_fcf: float,
        growth_rate: float,
        wacc: float,
        terminal_value: float,
        net_debt: float,
        shares: float
    ) -> Dict:
        """Perform sensitivity analysis on WACC and terminal growth rate."""
        sensitivity_table = {}

        try:
            # Vary WACC: -2%, -1%, base, +1%, +2%
            wacc_scenarios = [wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02]

            # Vary terminal growth rate: -1%, -0.5%, base, +0.5%, +1%
            growth_scenarios = [
                self.terminal_growth_rate - 0.01,
                self.terminal_growth_rate - 0.005,
                self.terminal_growth_rate,
                self.terminal_growth_rate + 0.005,
                self.terminal_growth_rate + 0.01
            ]

            for wacc_scenario in wacc_scenarios:
                for growth_scenario in growth_scenarios:
                    # Recalculate intrinsic value
                    projected_fcfs = self._project_cash_flows(base_fcf, growth_rate, self.projection_years)
                    terminal_fcf = projected_fcfs[-1] * (1 + growth_scenario)
                    tv = terminal_fcf / (wacc_scenario - growth_scenario)

                    pv_fcfs = sum(fcf / (1 + wacc_scenario) ** (i + 1) for i, fcf in enumerate(projected_fcfs))
                    pv_tv = tv / (1 + wacc_scenario) ** self.projection_years

                    ev = pv_fcfs + pv_tv
                    equity_value = ev - net_debt
                    intrinsic_value = equity_value / shares

                    key = f"WACC {wacc_scenario:.1%}, Growth {growth_scenario:.1%}"
                    sensitivity_table[key] = intrinsic_value

        except Exception as e:
            logger.error(f"Error in sensitivity analysis: {e}")

        return sensitivity_table

    def format_dcf_for_llm(self, dcf_result: Dict) -> str:
        """Format DCF results for LLM consumption."""
        if 'error' in dcf_result:
            return f"\n⚠️ **DCF VALUATION:** {dcf_result['error']}\n"

        output = ["\n💰 **DCF VALUATION ANALYSIS**\n"]

        # Key results
        intrinsic = dcf_result['intrinsic_value']
        current = dcf_result['current_price']
        upside = dcf_result['upside_downside_percent']

        output.append(f"**Intrinsic Value per Share:** ${intrinsic:.2f}")
        output.append(f"**Current Market Price:** ${current:.2f}")

        if upside > 0:
            output.append(f"**Upside Potential:** +{upside:.1f}% (📈 Undervalued)")
        elif upside < 0:
            output.append(f"**Downside Risk:** {upside:.1f}% (📉 Overvalued)")
        else:
            output.append(f"**Valuation:** Fair Value")

        # Assumptions
        output.append(f"\n**KEY ASSUMPTIONS:**")
        output.append(f"  WACC (Discount Rate): {dcf_result['wacc']:.2%}")
        output.append(f"  FCF Growth Rate: {dcf_result['fcf_growth_rate']:.2%}")
        output.append(f"  Terminal Growth Rate: {dcf_result['terminal_growth_rate']:.2%}")
        output.append(f"  Projection Period: {self.projection_years} years")

        # Historical FCF
        output.append(f"\n**HISTORICAL FREE CASH FLOW:**")
        fcf_history = dcf_result['fcf_history']
        for i, fcf in enumerate(fcf_history[-3:]):  # Last 3 years
            output.append(f"  Year {-len(fcf_history)+i+1}: ${fcf/1e9:.2f}B")

        # Projected FCF
        output.append(f"\n**PROJECTED FREE CASH FLOW:**")
        projected = dcf_result['projected_fcfs']
        for i, fcf in enumerate(projected, 1):
            output.append(f"  Year +{i}: ${fcf/1e9:.2f}B")

        # Sensitivity analysis
        output.append(f"\n**SENSITIVITY ANALYSIS:**")
        output.append("(Intrinsic value under different WACC and growth rate scenarios)")
        sensitivity = dcf_result['sensitivity_analysis']
        for scenario, value in list(sensitivity.items())[:5]:  # Show top 5 scenarios
            output.append(f"  {scenario}: ${value:.2f}")

        output.append(f"\n**INTERPRETATION:**")
        if upside > 15:
            output.append("  🚀 Strong buy signal - significant undervaluation")
        elif upside > 5:
            output.append("  ✅ Buy signal - moderate undervaluation")
        elif upside > -5:
            output.append("  ➡️ Hold - fairly valued")
        elif upside > -15:
            output.append("  ⚠️ Sell signal - moderate overvaluation")
        else:
            output.append("  ❌ Strong sell signal - significant overvaluation")

        output.append("\n**IMPORTANT CAVEATS:**")
        output.append("  - DCF is highly sensitive to assumptions (WACC, growth rates)")
        output.append("  - Historical performance may not predict future results")
        output.append("  - Model assumes stable business conditions")
        output.append("  - Should be used alongside other valuation methods")

        return "\n".join(output)
```

---

## Testing Strategy

### Unit Tests

**Test Coverage:**
- Financial statement extraction (10 test cases)
- Ratio calculations (20 test cases per category)
- DCF calculations (15 test cases)
- Edge cases and error handling

**Example Test:**
```python
def test_fcf_calculation():
    """Test Free Cash Flow calculation."""
    calc = DCFCalculator()
    cash_flow_data = {
        'Operating Cash Flow': 100_000_000,
        'Capital Expenditure': -30_000_000
    }
    fcf = calc._calculate_fcf_history(cash_flow_data)
    assert fcf == 70_000_000  # 100M - 30M
```

### Integration Tests

**Test Complete Workflow:**
```python
def test_detailed_analysis_end_to_end():
    """Test complete detailed analysis workflow."""
    tool = ComprehensiveStockAnalyzerTool()

    # Enable feature flag
    FeatureFlags.ENABLE_DETAILED_ANALYSIS = True

    # Execute with detailed=True
    result = asyncio.run(tool.execute(ticker="AAPL", detailed=True))

    # Verify output contains all sections
    assert "INCOME STATEMENT" in result['analysis']
    assert "BALANCE SHEET" in result['analysis']
    assert "CASH FLOW STATEMENT" in result['analysis']
    assert "FINANCIAL RATIOS" in result['analysis']
    assert "DCF VALUATION" in result['analysis']
    assert "Intrinsic Value" in result['analysis']
```

### Acceptance Criteria

| Feature | Acceptance Criteria |
|---------|---------------------|
| **Financial Statements** | 95%+ complete for S&P 500 stocks |
| **Ratio Calculations** | 20+ ratios calculated with <1% error |
| **DCF Model** | Intrinsic value calculated for 90%+ stocks |
| **Response Time** | <5 seconds for complete analysis |
| **No Regression** | All existing functionality works unchanged |
| **Graceful Degradation** | Falls back to basic analysis if detailed fails |

---

## Risk Mitigation

### Risk 1: Missing Financial Data

**Probability:** Medium
**Impact:** Medium

**Mitigation:**
- Check data availability before calculations
- Use "N/A" for missing ratios
- Gracefully skip unavailable sections
- Fall back to basic analysis

### Risk 2: DCF Calculation Failures

**Probability:** Medium
**Impact:** Low

**Mitigation:**
- Extensive error handling
- Default assumptions when data missing
- Clear messaging when DCF unavailable
- DCF is optional enhancement

### Risk 3: Performance Degradation

**Probability:** Low
**Impact:** Medium

**Mitigation:**
- Cache financial statements (change infrequently)
- Parallel calculation of ratios
- Lazy loading (only when detailed=True)
- Timeout protection

### Risk 4: Incorrect Calculations

**Probability:** Low
**Impact:** High

**Mitigation:**
- Comprehensive unit tests
- Compare with known good values
- Add caveats and disclaimers
- Sensitivity analysis shows range

---

## Success Metrics

### Implementation Success

- [ ] Feature flag system working
- [ ] Backwards compatibility maintained (100%)
- [ ] Financial statements extracted (95%+ stocks)
- [ ] 20+ ratios calculated
- [ ] DCF model working (90%+ stocks)
- [ ] Response time <5 seconds
- [ ] All tests passing

### User Value Success

- [ ] Fundamental analysis capability added
- [ ] DCF valuation provides actionable insights
- [ ] Multi-year trend analysis available
- [ ] Projections help with forecasting
- [ ] Zero additional monthly costs

---

## Conclusion

This implementation plan provides a comprehensive, step-by-step guide to adding full fundamental analysis and DCF valuation capabilities to the existing stock analyzer tool.

**Key Advantages:**
1. **Zero Additional Cost** - Uses existing yfinance library
2. **Backwards Compatible** - Existing functionality unchanged
3. **Feature Flag Protected** - Safe rollout with easy rollback
4. **Comprehensive Analysis** - Complete financial statements + ratios + DCF
5. **Production Ready** - Includes testing, error handling, documentation

**Timeline:** 5 days implementation
**Risk:** LOW (with proper feature flag discipline)
**Value:** VERY HIGH (unique competitive advantage)

**Ready to start implementation!** 🚀

---

**Document Control**

**Version:** 1.0.0
**Date:** 2025-10-31
**Author:** Agentic-RAG Development Team
**Status:** Ready for Implementation

**Approval:** APPROVED for implementation

---

**End of Implementation Plan**
