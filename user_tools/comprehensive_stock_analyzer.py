"""
Comprehensive Stock Analyzer Tool - Combines real-time data with analysis
This tool provides both current stock data AND comprehensive analysis in one call
"""

import os
import asyncio
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import yfinance as yf
import re
import sys

# Add parent directory to path for shared utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.html_generator import create_html_report, html_generator

try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool


class ComprehensiveStockAnalyzerTool(BaseUserTool):
    """
    A comprehensive stock analysis tool that combines:
    1. Real-time stock data (price, volume, market cap)
    2. Company information and fundamentals
    3. Technical analysis and recommendations
    4. News sentiment analysis
    
    This tool solves the single-tool limitation by providing everything in one call.
    """
    
    def __init__(self):
        super().__init__()
    
    @property
    def name(self) -> str:
        return "comprehensive_stock_analyzer"
    
    @property
    def description(self) -> str:
        # 🚨 PROTECTED: Clean description without aggressive language or conflicts  
        # NEVER add emojis, "PRIMARY", "ULTIMATE" or redirections - breaks multi-tool calling
        return "INDIVIDUAL STOCK ANALYSIS ONLY - Requires exact ticker symbol (AAPL, MSFT, etc). Do NOT use for: general market news, market summaries, multiple stocks, or news searches. Only for analyzing ONE specific stock ticker."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')",
                    "pattern": "^[A-Z]{1,5}$"
                }
            },
            "required": ["ticker"]
        }
    
    def _get_company_news(self, ticker: str, company_name: str) -> List[Dict[str, Any]]:
        """Get recent news about the company using web search"""
        try:
            # Search for recent news about the company
            search_queries = [
                f"{ticker} stock news today",
                f"{company_name} earnings financial news",
                f"{ticker} analyst rating upgrade downgrade"
            ]
            
            all_news = []
            
            for query in search_queries:
                try:
                    # Use DuckDuckGo search to find recent news
                    from ddgs import DDGS
                    ddgs = DDGS()
                    results = ddgs.text(query, max_results=5)
                    
                    for result in results:
                        # Filter for financial news sources
                        financial_sources = ['yahoo', 'bloomberg', 'reuters', 'marketwatch', 'cnbc', 'benzinga', 'seeking alpha', 'fool']
                        if any(source in result['href'].lower() for source in financial_sources):
                            all_news.append({
                                'title': result['title'],
                                'url': result['href'],
                                'snippet': result['body'],
                                'source': self._extract_source(result['href'])
                            })
                    
                    if len(all_news) >= 10:  # Limit to reasonable number
                        break
                        
                except Exception as e:
                    print(f"Warning: Could not fetch news for query '{query}': {e}")
                    continue
            
            # Remove duplicates and sort by relevance
            unique_news = []
            seen_titles = set()
            for news in all_news:
                if news['title'] not in seen_titles:
                    unique_news.append(news)
                    seen_titles.add(news['title'])
            
            return unique_news[:8]  # Return top 8 news items
            
        except Exception as e:
            print(f"Warning: Could not fetch company news: {e}")
            return []
    
    def _extract_source(self, url: str) -> str:
        """Extract news source from URL"""
        try:
            if 'yahoo' in url:
                return 'Yahoo Finance'
            elif 'bloomberg' in url:
                return 'Bloomberg'
            elif 'reuters' in url:
                return 'Reuters'
            elif 'marketwatch' in url:
                return 'MarketWatch'
            elif 'cnbc' in url:
                return 'CNBC'
            elif 'benzinga' in url:
                return 'Benzinga'
            elif 'fool' in url:
                return 'The Motley Fool'
            elif 'seekingalpha' in url:
                return 'Seeking Alpha'
            else:
                # Extract domain name
                domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
                return domain.group(1).title() if domain else 'Unknown'
        except:
            return 'Unknown'
    
    def _analyze_news_sentiment(self, news_items: List[Dict[str, Any]], ticker: str) -> Dict[str, Any]:
        """Analyze sentiment from news headlines and snippets"""
        if not news_items:
            return {"sentiment": "Neutral", "score": 0, "summary": "No recent news available"}
        
        positive_words = ['buy', 'bullish', 'upgrade', 'beat', 'strong', 'growth', 'profit', 'gain', 'rise', 'surge', 'outperform', 'target', 'positive']
        negative_words = ['sell', 'bearish', 'downgrade', 'miss', 'weak', 'decline', 'loss', 'fall', 'drop', 'underperform', 'negative', 'concern']
        
        sentiment_score = 0
        total_items = 0
        
        for news in news_items:
            text = (news.get('title', '') + ' ' + news.get('snippet', '')).lower()
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > negative_count:
                sentiment_score += 1
            elif negative_count > positive_count:
                sentiment_score -= 1
            
            total_items += 1
        
        if total_items == 0:
            return {"sentiment": "Neutral", "score": 0, "summary": "No news to analyze"}
        
        avg_sentiment = sentiment_score / total_items
        
        if avg_sentiment > 0.3:
            sentiment = "🟢 Positive"
        elif avg_sentiment < -0.3:
            sentiment = "🔴 Negative"
        else:
            sentiment = "🟡 Neutral"
        
        return {
            "sentiment": sentiment,
            "score": round(avg_sentiment, 2),
            "summary": f"Based on {total_items} recent news items"
        }

    def _get_real_time_data(self, ticker: str) -> Dict[str, Any]:
        """Get real-time stock data using yfinance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1d")
            
            if hist.empty:
                return {"error": f"No data available for ticker {ticker}"}
            
            current_price = hist['Close'].iloc[-1] if len(hist) > 0 else None
            previous_close = info.get('previousClose', None)
            change = current_price - previous_close if current_price and previous_close else None
            
            return {
                "current_price": round(current_price, 2) if current_price else "N/A",
                "previous_close": round(previous_close, 2) if previous_close else "N/A", 
                "change": round(change, 2) if change else "N/A",
                "change_percent": round((change / previous_close * 100), 2) if change and previous_close else "N/A",
                "volume": info.get('volume', "N/A"),
                "market_cap": info.get('marketCap', "N/A"),
                "company_name": info.get('longName', ticker),
                "sector": info.get('sector', "N/A"),
                "industry": info.get('industry', "N/A"),
                "pe_ratio": info.get('trailingPE', "N/A"),
                "dividend_yield": info.get('dividendYield', "N/A"),
                "52_week_high": info.get('fiftyTwoWeekHigh', "N/A"),
                "52_week_low": info.get('fiftyTwoWeekLow', "N/A"),
                "beta": info.get('beta', "N/A"),
                "analyst_target": info.get('targetMeanPrice', "N/A"),
                "recommendation": info.get('recommendationMean', "N/A")
            }
        except Exception as e:
            return {"error": f"Failed to fetch data: {str(e)}"}
    
    def _format_dividend_yield(self, dividend_yield) -> str:
        """Format dividend yield safely"""
        if dividend_yield is None or dividend_yield == "N/A":
            return "N/A"
        try:
            if isinstance(dividend_yield, (int, float)) and dividend_yield > 0:
                return f"{dividend_yield:.2%}"
            else:
                return "N/A"
        except:
            return str(dividend_yield)
    
    def _format_large_number(self, number) -> str:
        """Format large numbers safely with commas"""
        if number is None or number == "N/A":
            return "N/A"
        try:
            if isinstance(number, (int, float)):
                return f"{number:,}"
            else:
                return str(number)
        except:
            return str(number)
    
    def _format_change(self, change) -> str:
        """Format change values safely"""
        if change is None or change == "N/A":
            return "N/A"
        try:
            if isinstance(change, (int, float)):
                return f"{change:+.2f}"
            else:
                return str(change)
        except:
            return str(change)
    
    def _format_percentage(self, value) -> str:
        """Format percentage values safely"""
        if value is None or value == "N/A":
            return "N/A"
        try:
            if isinstance(value, (int, float)):
                return f"{value:.2%}"
            else:
                return str(value)
        except:
            return str(value)
    
    def _convert_to_pdf(self, analysis_text: str, ticker: str) -> bytes:
        """Convert analysis to PDF format using UniversalPDFGenerator"""
        try:
            from ._universal_pdf_generator import UniversalPDFGenerator
            from io import BytesIO
            import tempfile
            import os
            
            # Determine title
            company_name = "Stock Analysis Report"
            if "**Company**:" in analysis_text:
                try:
                    company_line = analysis_text.split("**Company**:")[1].split("\n")[0].strip()
                    company_name = f"{company_line} ({ticker}) - Comprehensive Analysis"
                except:
                    company_name = f"{ticker} - Comprehensive Stock Analysis"
            
            # Create temporary file for PDF generation
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                temp_pdf_path = tmp_file.name
            
            # Use UniversalPDFGenerator for consistent formatting
            generator = UniversalPDFGenerator()
            success = generator.create_pdf(
                title=company_name,
                content=analysis_text,
                output_path=temp_pdf_path,
                subtitle="Investment Analysis & Recommendations",
                metadata=None  # No metadata per user requirements
            )
            
            if not success:
                # Fallback to HTML if PDF generation fails
                print("⚠️ PDF generation failed, falling back to HTML format")
                html_content = self._convert_to_html(analysis_text, ticker)
                # Clean up temp file
                try:
                    os.unlink(temp_pdf_path)
                except:
                    pass
                return html_content.encode('utf-8')
            
            # Read the generated PDF file
            try:
                with open(temp_pdf_path, 'rb') as f:
                    pdf_data = f.read()
                
                # Clean up temp file
                os.unlink(temp_pdf_path)
                
                return pdf_data
                
            except Exception as e:
                print(f"⚠️ Error reading PDF file: {e}")
                # Clean up temp file
                try:
                    os.unlink(temp_pdf_path)
                except:
                    pass
                # Fallback to HTML
                return self._convert_to_html(analysis_text, ticker).encode('utf-8')
                
        except ImportError:
            # If UniversalPDFGenerator is not available, fall back to HTML
            print("⚠️ UniversalPDFGenerator not available, falling back to HTML format")
            return self._convert_to_html(analysis_text, ticker).encode('utf-8')
        except Exception as e:
            print(f"⚠️ PDF conversion failed: {e}, falling back to HTML format")
            return self._convert_to_html(analysis_text, ticker).encode('utf-8')

    def _convert_to_html(self, analysis_text: str, ticker: str) -> str:
        """Convert markdown analysis to properly formatted HTML using shared template"""
        try:
            # Use shared HTML generator
            from utils.html_generator import html_generator
            
            # Extract company name from the analysis
            company_name = "Company Analysis"
            if "**Company**:" in analysis_text:
                company_line = analysis_text.split("**Company**:")[1].split("\n")[0].strip()
                company_name = f"{company_line} ({ticker})"
            
            # Convert markdown-style formatting to HTML content
            html_content = self._format_analysis_content(analysis_text)
            
            # Generate complete HTML using shared template
            return html_generator.generate_html_report(
                content=html_content,
                title=f"{company_name} - Comprehensive Stock Analysis Report",
                header_title=company_name,
                header_subtitle="Comprehensive Stock Analysis Report",
                include_disclaimer=True
            )
            
        except Exception as e:
            print(f"Warning: Shared template failed, using fallback: {e}")
            # Fallback to simple HTML if shared template fails
            return f"""<!DOCTYPE html>
<html>
<head>
    <title>{ticker} Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        pre {{ white-space: pre-wrap; background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{ticker} Stock Analysis</h1>
    <pre>{analysis_text}</pre>
</body>
</html>"""
    
    def _format_analysis_content(self, analysis_text: str) -> str:
        """Format analysis text into HTML content for template"""
        try:
            # Convert markdown-style formatting to HTML
            html_content = analysis_text
            
            # Convert headers
            html_content = html_content.replace("🏢 **Company**:", "<h2>🏢 Company Information</h2><p><strong>Company:</strong>")
            html_content = html_content.replace("📊 **CURRENT MARKET DATA**", "<h2>📊 Current Market Data</h2>")
            html_content = html_content.replace("📋 **FUNDAMENTAL ANALYSIS**", "<h2>📋 Fundamental Analysis</h2>")
            html_content = html_content.replace("📈 **TECHNICAL ANALYSIS**", "<h2>📈 Technical Analysis</h2>")
            html_content = html_content.replace("📰 **RECENT FINANCIAL NEWS & ANALYSIS**", "<h2>📰 Recent Financial News & Analysis</h2>")
            html_content = html_content.replace("🎯 **INVESTMENT RECOMMENDATION**:", "<h2>🎯 Investment Recommendation</h2><p><strong>Recommendation:</strong>")
            
            # Convert bold text
            html_content = re.sub(r'\*\*(.*?)\*\*:', r'<strong>\1:</strong>', html_content)
            html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
            
            # Convert line breaks to proper HTML with better spacing control
            paragraphs = html_content.split('\n\n')
            html_paragraphs = []
            
            for para in paragraphs:
                if para.strip():
                    # Convert individual lines within paragraphs
                    lines = para.split('\n')
                    formatted_lines = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            if line.startswith(('💰', '📈', '📊', '🏦', '💵', '🎯', '📍', '⏰')):
                                formatted_lines.append(f"<div class='metric'>{line}</div>")
                            elif line.startswith('**') and line.endswith('**'):
                                formatted_lines.append(f"<h3>{line.replace('**', '')}</h3>")
                            elif '**' in line and ':' in line:
                                formatted_lines.append(f"<div class='metric'>{line}</div>")
                            elif line.startswith('<h2>'):
                                # Already processed headers - add as is
                                formatted_lines.append(line)
                            else:
                                # For regular content, don't wrap every line in <p>
                                formatted_lines.append(line)
                    
                    # Wrap the entire paragraph content in a single <p> tag if it's not a header/metric
                    paragraph_content = '\n'.join(formatted_lines)
                    if not any(paragraph_content.startswith(tag) for tag in ['<h2>', '<h3>', '<div class="metric">']):
                        if paragraph_content.strip():
                            html_paragraphs.append(f"<p>{paragraph_content}</p>")
                    else:
                        html_paragraphs.append(paragraph_content)
            
            return '\n'.join(html_paragraphs)
            
        except Exception as e:
            # Return plain text if formatting fails
            return f"<pre>{analysis_text}</pre>"

    def _analyze_data(self, data: Dict[str, Any], ticker: str, news_items: List[Dict[str, Any]], news_sentiment: Dict[str, Any]) -> str:
        """Perform comprehensive analysis of the stock data"""
        if "error" in data:
            return f"❌ Error analyzing {ticker}: {data['error']}"
        
        # Technical Analysis
        current_price = data.get("current_price")
        change = data.get("change")
        change_percent = data.get("change_percent")
        high_52 = data.get("52_week_high")
        low_52 = data.get("52_week_low")
        pe_ratio = data.get("pe_ratio")
        target = data.get("analyst_target")
        
        # Performance Assessment
        performance = "📈 Positive" if isinstance(change, (int, float)) and change > 0 else "📉 Negative" if isinstance(change, (int, float)) and change < 0 else "➡️ Neutral"
        
        # Valuation Assessment
        valuation = "N/A"
        if isinstance(pe_ratio, (int, float)):
            if pe_ratio < 15:
                valuation = "📊 Undervalued"
            elif pe_ratio > 25:
                valuation = "📊 Overvalued"
            else:
                valuation = "📊 Fair Value"
        
        # Position in Range
        range_position = "N/A"
        if isinstance(current_price, (int, float)) and isinstance(high_52, (int, float)) and isinstance(low_52, (int, float)):
            range_percent = ((current_price - low_52) / (high_52 - low_52)) * 100
            if range_percent > 80:
                range_position = f"🔥 Near 52W High ({range_percent:.1f}%)"
            elif range_percent < 20:
                range_position = f"🔥 Near 52W Low ({range_percent:.1f}%)"
            else:
                range_position = f"📊 Mid-range ({range_percent:.1f}%)"
        
        # Investment Recommendation
        recommendation = "HOLD"
        if isinstance(target, (int, float)) and isinstance(current_price, (int, float)):
            upside = ((target - current_price) / current_price) * 100
            if upside > 15:
                recommendation = "🚀 STRONG BUY"
            elif upside > 5:
                recommendation = "✅ BUY"
            elif upside < -15:
                recommendation = "❌ STRONG SELL"
            elif upside < -5:
                recommendation = "⚠️ SELL"
            else:
                recommendation = "➡️ HOLD"
        
        # Format news section
        news_section = ""
        if news_items:
            news_section = "\n📰 **RECENT FINANCIAL NEWS & ANALYSIS**\n"
            news_section += f"📊 **Market Sentiment**: {news_sentiment.get('sentiment', 'N/A')} ({news_sentiment.get('summary', '')})\n\n"
            
            for i, news in enumerate(news_items[:6], 1):  # Show top 6 news items
                news_section += f"**{i}. {news['title']}**\n"
                news_section += f"   📰 *{news['source']}*\n"
                news_section += f"   📝 {news['snippet'][:150]}{'...' if len(news['snippet']) > 150 else ''}\n\n"
        else:
            news_section = "\n📰 **RECENT FINANCIAL NEWS & ANALYSIS**\n⚠️ No recent news available for analysis\n"

        return f"""
🏢 **Company**: {data.get('company_name', ticker)}
🏭 **Sector**: {data.get('sector', 'N/A')} | **Industry**: {data.get('industry', 'N/A')}

📊 **CURRENT MARKET DATA**
💰 **Price**: ${current_price} ({self._format_change(change)} / {self._format_change(change_percent)}%)
📈 **Daily Change**: {performance}
📊 **Volume**: {self._format_large_number(data.get('volume'))} shares
🏦 **Market Cap**: ${self._format_large_number(data.get('market_cap'))}

📋 **FUNDAMENTAL DATA**
📊 **P/E Ratio (Trailing)**: {pe_ratio}
📊 **Forward P/E**: {data.get('forwardPE', 'N/A')}
💵 **Dividend Yield**: {self._format_dividend_yield(data.get('dividend_yield'))}
📊 **Beta**: {data.get('beta', 'N/A')}
💰 **Revenue (TTM)**: ${self._format_large_number(data.get('totalRevenue', 'N/A'))}
📈 **Revenue Growth**: {self._format_change(data.get('revenueGrowth', 'N/A'))}%
💡 **Profit Margin**: {self._format_percentage(data.get('profitMargins', 'N/A'))}
🏆 **ROE**: {self._format_percentage(data.get('returnOnEquity', 'N/A'))}
💪 **Debt/Equity**: {data.get('debtToEquity', 'N/A')}
💰 **Current Ratio**: {data.get('currentRatio', 'N/A')}
🎯 **Book Value**: ${data.get('bookValue', 'N/A')}
📊 **Price/Book**: {data.get('priceToBook', 'N/A')}

📈 **TECHNICAL DATA**
🎯 **52W Range**: ${low_52} - ${high_52}
📍 **Range Position**: {range_position}
🎯 **Analyst Target**: ${target}
📊 **Analyst Recommendation**: {data.get('recommendationMean', 'N/A')}

{news_section}

⏰ **Data Retrieved**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Fetch raw financial data for the specified ticker"""
        try:
            ticker = kwargs.get("ticker", "").upper().strip()
            
            if not ticker:
                return {
                    "success": False,
                    "error": "❌ TOOL MISUSE: This tool requires a specific stock ticker symbol (e.g., AAPL, MSFT). For general market news, use web search tools instead.",
                    "result": None
                }
            
            # Detect if tool is being misused for general market analysis
            general_market_tickers = ["MARKET", "NEWS", "GENERAL", "STOCK", "STOCKS", "INDEX", "SP500", "DOW", "NASDAQ"]
            if ticker.upper() in general_market_tickers:
                return {
                    "success": False,
                    "error": f"❌ TOOL MISUSE: '{ticker}' is not a valid individual stock ticker. This tool analyzes specific companies only (AAPL, MSFT, etc). For general market news, use web search instead.",
                    "result": None
                }
            
            # Validate ticker format
            if not ticker.isalpha() or len(ticker) > 5:
                return {
                    "success": False,
                    "error": f"❌ INVALID TICKER: '{ticker}' is not a valid stock symbol format. Use standard symbols like AAPL, MSFT, GOOGL, etc.",
                    "result": None
                }
            
            # Get real-time data
            real_time_data = self._get_real_time_data(ticker)
            
            if "error" in real_time_data:
                return {
                    "success": False,
                    "error": real_time_data["error"],
                    "result": None
                }
            
            # Get company news and sentiment analysis
            company_name = real_time_data.get('company_name', ticker)
            news_items = self._get_company_news(ticker, company_name)
            news_sentiment = self._analyze_news_sentiment(news_items, ticker)
            
            # Return ONLY raw data - no analysis, no file creation
            raw_data_report = self._analyze_data(real_time_data, ticker, news_items, news_sentiment)
            
            return {
                "success": True,
                "result": raw_data_report,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Stock data retrieval failed: {str(e)}",
                "result": None
            }


# Register the tool
def get_user_tool():
    """Factory function to create tool instance"""
    return ComprehensiveStockAnalyzerTool()


if __name__ == "__main__":
    # Test the tool
    tool = ComprehensiveStockAnalyzerTool()
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print("Parameters:", tool.parameters)