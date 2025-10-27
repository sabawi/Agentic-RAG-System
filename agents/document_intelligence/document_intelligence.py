#!/usr/bin/env python3
"""
Document Intelligence Agent
==========================

Automated document processing and insight extraction agent.

Features:
- Monitor document folders for new files
- Extract key information using document interrogation
- Create executive summaries
- Track document changes and versions
- Generate searchable archives
- Send document insights via email

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import json

import openai
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_intelligence.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DocumentIntelligenceAgent:
    """Automated document processing and insight extraction agent."""

    def __init__(
        self,
        server_url: str = "http://localhost:5000/v1",
        document_dirs: List[str] = None,
        watch_subdirs: bool = True,
        recipient_email: Optional[str] = None,
        output_dir: str = "document_reports",
        max_retries: int = 3
    ):
        """
        Initialize the document intelligence agent.

        Args:
            server_url: URL of the Agentic-RAG server
            document_dirs: List of directories to monitor for documents
            watch_subdirs: Whether to monitor subdirectories recursively
            recipient_email: Email for document reports
            output_dir: Directory to save document intelligence reports
            max_retries: Maximum retry attempts on failure
        """
        self.server_url = server_url
        self.document_dirs = document_dirs or []
        self.watch_subdirs = watch_subdirs
        self.recipient_email = recipient_email
        self.output_dir = Path(output_dir)
        self.max_retries = max_retries

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

        # Initialize OpenAI client
        self.client = openai.OpenAI(
            base_url=server_url,
            api_key="not-required"
        )

        logger.info(f"DocumentIntelligenceAgent initialized for directories: {', '.join(self.document_dirs)}")

    def test_connection(self) -> bool:
        """Test connection to the server."""
        try:
            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{"role": "user", "content": "Hello, are you working?"}],
                max_tokens=50
            )
            logger.info("✅ Server connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Server connection failed: {e}")
            return False

    def process_documents_with_retry(self, document_paths: List[str]) -> Optional[str]:
        """
        Process documents with retry logic and insight extraction.

        Args:
            document_paths: List of document paths to process

        Returns:
            Processed content as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Processing {len(document_paths)} documents (attempt {attempt}/{self.max_retries})...")

                # Build document paths string for prompt
                doc_list = "\n".join([f"- {path}" for path in document_paths])
                
                prompt = f"""
Please process the following documents and provide comprehensive insights:

{doc_list}

Use the document_search tool to analyze the documents. Then provide:

1. Executive summary for each document
2. Key points and main findings
3. Action items or recommendations
4. Critical information that requires attention
5. Cross-document insights and connections
6. Important dates, deadlines, or time-sensitive items
7. Risk factors or concerns identified
8. Follow-up requirements

For each document, provide:
- Document title/name
- Type of document (contract, report, policy, etc.)
- Key findings summary
- Action items required
- Priority level (High/Medium/Low)
- Confidentiality level

Format as an HTML report with:
- Clear document sections
- Priority indicators
- Action item tracking
- Cross-reference links between related documents
- Professional styling
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,  # Balanced for analysis
                    max_tokens=4096
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Document processing content is empty or too short")

                logger.info(f"✅ Document processing completed ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return None

    def extract_insights_with_retry(self, document_content: str) -> Optional[str]:
        """
        Extract deeper insights from document content.

        Args:
            document_content: Content to analyze

        Returns:
            Insights as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Extracting insights (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Based on the following document analysis, extract key insights and intelligence:

{document_content}

Extract and analyze:
1. Strategic insights and implications
2. Competitive intelligence
3. Financial indicators or projections
4. Market trends or opportunities
5. Risk assessments
6. Compliance considerations
7. Performance metrics or KPIs
8. Benchmark comparisons
9. Future projections or forecasts
10. Recommended next steps

Provide a structured intelligence summary with:
- Executive insights at the top
- Categorized findings
- Confidence levels for each insight
- Related document cross-references
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,  # Slightly higher for strategic analysis
                    max_tokens=2048
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Insights content is empty or too short")

                logger.info(f"✅ Insights extracted ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return None

    def summarize_documents_with_retry(self, document_content: str) -> Optional[str]:
        """
        Create comprehensive summaries of documents.

        Args:
            document_content: Content to summarize

        Returns:
            Summary as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Creating document summary (attempt {attempt}/{self.max_retries})...")

                prompt = f"""
Based on the following document analysis, create comprehensive executive summaries:

{document_content}

For each document, create:
1. One-paragraph executive summary
2. Key points list (3-5 points)
3. Critical action items (if any)
4. Timeline or deadlines mentioned
5. Stakeholders involved
6. Budget or financial implications (if mentioned)

Format as clear, scannable executive summaries with:
- Document titles clearly marked
- Key points in bullet format
- Action items highlighted
- Time-sensitive items flagged
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Lower for factual summaries
                    max_tokens=2048
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Summary content is empty or too short")

                logger.info(f"✅ Document summary created ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return None

    def find_related_documents_with_retry(self, document_paths: List[str]) -> Optional[str]:
        """
        Find related documents and create connections.

        Args:
            document_paths: List of document paths to analyze

        Returns:
            Related documents analysis as string or None if failed
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Finding related documents (attempt {attempt}/{self.max_retries})...")

                paths_str = "\n".join([f"- {path}" for path in document_paths])
                
                prompt = f"""
Analyze the following documents and identify relationships, connections, and cross-references:

{paths_str}

Identify and report on:
1. Document relationships and connections
2. Common topics or themes across documents
3. Sequential or dependent documents
4. Contradictions or inconsistencies
5. Complementary information
6. Timeline relationships
7. Shared stakeholders or entities
8. Cross-referenced information

Create a relationship map showing how documents connect and relate to each other.
"""

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6,  # Higher for relationship analysis
                    max_tokens=2048
                )

                content = response.choices[0].message.content

                if not content or len(content) < 100:
                    raise ValueError("Related documents content is empty or too short")

                logger.info(f"✅ Related documents analysis completed ({len(content)} chars)")
                return content

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    return None

    def save_document_report(self, content: str, report_type: str) -> Path:
        """
        Save document intelligence report to HTML file.

        Args:
            content: Report content to save
            report_type: Type of report ('daily', 'weekly', 'summary')

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"document_{report_type}_intel_{timestamp}.html"
        filepath = self.output_dir / filename

        try:
            # Wrap in HTML if not already
            if not content.strip().startswith("<html"):
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Document Intelligence {report_type.title()} Report - {datetime.now().strftime("%Y-%m-%d")}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #f8f9fa;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            text-align: center;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        h3 {{
            color: #2980b9;
        }}
        .critical {{ background-color: #ffebee; border-left: 5px solid #f44336; padding: 10px; margin: 10px 0; }}
        .high-priority {{ background-color: #fff3e0; border-left: 5px solid #ff9800; padding: 10px; margin: 10px 0; }}
        .medium-priority {{ background-color: #f3e5f5; border-left: 5px solid #9c27b0; padding: 10px; margin: 10px 0; }}
        .low-priority {{ background-color: #e8f5e8; border-left: 5px solid #4caf50; padding: 10px; margin: 10px 0; }}
        .action-item {{
            background-color: #fffde7;
            border: 2px solid #ffeb3b;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .document-card {{
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #34495e;
            color: white;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-style: italic;
            margin: 20px 0;
            text-align: center;
        }}
        .priority-high {{ color: #e74c3c; font-weight: bold; }}
        .priority-medium {{ color: #f39c12; font-weight: bold; }}
        .priority-low {{ color: #7f8c8d; }}
        .confidential {{ background-color: #ffcdd2; padding: 5px; border-radius: 3px; display: inline-block; }}
        .relationship-map {{
            background-color: #f1f8e9;
            border: 1px solid #9ccc65;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div style="text-align: center; margin-bottom: 20px;">
        <h1>📄 Document Intelligence {report_type.title()} Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    {content}
</body>
</html>"""
            else:
                html_content = content

            filepath.write_text(html_content, encoding='utf-8')
            logger.info(f"✅ Saved document report to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to save document report: {e}")
            raise

    def send_email_report(self, filepath: Path, subject: str) -> bool:
        """
        Send document report via email.

        Args:
            filepath: Path to HTML report file
            subject: Email subject

        Returns:
            True if email was sent successfully
        """
        if not self.recipient_email:
            logger.warning("No recipient email configured")
            return False

        try:
            logger.info(f"Sending document report to {self.recipient_email}...")

            response = self.client.chat.completions.create(
                model="Agentic-RAG-Model1",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Send an email to {self.recipient_email} with:\n"
                        f"Subject: '{subject}'\n"
                        f"Body: 'Please find attached your document intelligence report with summaries and insights.'\n"
                        f"Attach: {filepath.absolute()}"
                    )
                }]
            )

            logger.info("✅ Document report email sent successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send document report email: {e}")
            return False

    def run_daily_scan(self, send_email: bool = False) -> bool:
        """Scan document directories and generate daily report."""
        logger.info("=" * 60)
        logger.info("Starting daily document scan...")
        logger.info("=" * 60)

        # Find new documents in monitored directories
        all_documents = []
        for directory in self.document_dirs:
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue
            
            # Find documents modified in the last 24 hours
            time_threshold = datetime.now() - timedelta(hours=24)
            
            if self.watch_subdirs:
                patterns = ["*.pdf", "*.docx", "*.txt", "*.md", "*.html", "*.csv", "*.json", "*.xml"]
                for pattern in patterns:
                    for file_path in dir_path.rglob(pattern):
                        if file_path.stat().st_mtime > time_threshold.timestamp():
                            all_documents.append(str(file_path))
            else:
                patterns = ["*.pdf", "*.docx", "*.txt", "*.md", "*.html", "*.csv", "*.json", "*.xml"]
                for pattern in patterns:
                    for file_path in dir_path.glob(pattern):
                        if file_path.stat().st_mtime > time_threshold.timestamp():
                            all_documents.append(str(file_path))

        if not all_documents:
            logger.info("No new documents found in the last 24 hours")
            # Still generate a report about the status
            status_content = f"""
<h2>📋 Document Scan Results</h2>

<p>No new documents were found in the monitored directories in the last 24 hours.</p>

<h3>Directory Status:</h3>
<ul>
"""
            for directory in self.document_dirs:
                status_content += f"<li>{directory}: Monitored, no new documents</li>\n"
            status_content += """
</ul>

<h3>Next Scan:</h3>
<p>The next scan will occur tomorrow morning.</p>
"""
            
            filepath = self.save_document_report(status_content, "daily")
            if send_email:
                subject = f"📋 Daily Document Scan - {datetime.now().strftime('%A, %B %d')}"
                self.send_email_report(filepath, subject)
            
            logger.info("✅ Daily document scan completed (no new documents)")
            return True

        # Process the documents
        processed_content = self.process_documents_with_retry(all_documents)
        if not processed_content:
            logger.error("Failed to process documents")
            return False

        # Extract insights
        insights = self.extract_insights_with_retry(processed_content)
        if not insights:
            logger.warning("Failed to extract insights")
            insights = "No insights could be extracted."

        # Create summaries
        summaries = self.summarize_documents_with_retry(processed_content)
        if not summaries:
            logger.warning("Failed to create summaries")
            summaries = "No summaries could be created."

        # Find related documents
        related_docs = self.find_related_documents_with_retry(all_documents)
        if not related_docs:
            logger.warning("Failed to find related documents")
            related_docs = "No document relationships could be identified."

        # Combine into daily report
        daily_content = f"""
<div class="document-card">
    <h2>📋 Daily Document Scan Summary</h2>
    <p>Found {len(all_documents)} new document(s) in monitored directories.</p>
</div>

<h3>📄 Document Processed</h3>
<ol>
"""
        for doc in all_documents:
            daily_content += f"<li>{doc}</li>\n"
        daily_content += """
</ol>

<h3>🎯 Key Summaries</h3>
<div class="document-card">
    {summaries}
</div>

<h3>🔍 Intelligence Insights</h3>
<div class="document-card">
    {insights}
</div>

<h3>🔗 Document Relationships</h3>
<div class="relationship-map">
    {related_docs}
</div>

<div style="margin-top: 30px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
    <h3>Scan Information</h3>
    <ul>
        <li><strong>Directories Monitored:</strong> {', '.join(self.document_dirs)}</li>
        <li><strong>Files Processed:</strong> {len(all_documents)}</li>
        <li><strong>Scan Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        <li><strong>Next Scan:</strong> Tomorrow morning</li>
    </ul>
</div>
""".format(summaries=summaries, insights=insights, related_docs=related_docs)

        filepath = self.save_document_report(daily_content, "daily")

        if send_email:
            subject = f"📄 Daily Document Intelligence - {datetime.now().strftime('%A, %B %d')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Daily document scan completed")
        return True

    def run_weekly_analysis(self, send_email: bool = False) -> bool:
        """Run comprehensive weekly document intelligence analysis."""
        logger.info("=" * 60)
        logger.info("Starting weekly document analysis...")
        logger.info("=" * 60)

        # Find documents modified in the last 7 days
        all_documents = []
        for directory in self.document_dirs:
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue
            
            time_threshold = datetime.now() - timedelta(days=7)
            
            if self.watch_subdirs:
                patterns = ["*.pdf", "*.docx", "*.txt", "*.md", "*.html", "*.csv", "*.json", "*.xml"]
                for pattern in patterns:
                    for file_path in dir_path.rglob(pattern):
                        if file_path.stat().st_mtime > time_threshold.timestamp():
                            all_documents.append(str(file_path))
            else:
                patterns = ["*.pdf", "*.docx", "*.txt", "*.md", "*.html", "*.csv", "*.json", "*.xml"]
                for pattern in patterns:
                    for file_path in dir_path.glob(pattern):
                        if file_path.stat().st_mtime > time_threshold.timestamp():
                            all_documents.append(str(file_path))

        if not all_documents:
            logger.info("No documents found in the last 7 days")
            status_content = f"""
<h2>📋 Weekly Document Analysis</h2>

<p>No documents were found in the monitored directories in the last 7 days.</p>

<h3>Directory Status:</h3>
<ul>
"""
            for directory in self.document_dirs:
                status_content += f"<li>{directory}: Monitored, no documents this week</li>\n"
            status_content += """
</ul>
"""
            
            filepath = self.save_document_report(status_content, "weekly")
            if send_email:
                subject = f"📋 Weekly Document Analysis - {datetime.now().strftime('%B %d, %Y')}"
                self.send_email_report(filepath, subject)
            
            logger.info("✅ Weekly document analysis completed (no documents)")
            return True

        # Process the documents
        processed_content = self.process_documents_with_retry(all_documents)
        if not processed_content:
            logger.error("Failed to process documents")
            return False

        # Extract insights
        insights = self.extract_insights_with_retry(processed_content)
        if not insights:
            logger.warning("Failed to extract insights")
            insights = "No insights could be extracted."

        # Create summaries
        summaries = self.summarize_documents_with_retry(processed_content)
        if not summaries:
            logger.warning("Failed to create summaries")
            summaries = "No summaries could be created."

        # Find related documents
        related_docs = self.find_related_documents_with_retry(all_documents)
        if not related_docs:
            logger.warning("Failed to find related documents")
            related_docs = "No document relationships could be identified."

        # Generate week trend analysis
        trend_prompt = f"""
Based on the following document processing results from the past week, analyze trends, patterns, and insights:

{processed_content}

Provide:
1. Weekly document processing trends
2. Common themes across documents
3. Recurring topics or issues
4. Key stakeholders mentioned across documents
5. Timeline analysis of document creation/updates
6. Category or type distribution
7. Priority level distribution
8. Next week's document processing outlook
9. Recommendations for document management

Format as a comprehensive weekly trend analysis.
"""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Analyzing weekly trends (attempt {attempt}/{self.max_retries})...")

                response = self.client.chat.completions.create(
                    model="Agentic-RAG-Model1",
                    messages=[{"role": "user", "content": trend_prompt}],
                    temperature=0.5,
                    max_tokens=2048
                )

                trend_analysis = response.choices[0].message.content
                break
            except Exception as e:
                logger.error(f"❌ Trend analysis attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("All trend analysis attempts failed")
                    trend_analysis = "No trend analysis available."

        # Combine into weekly report
        weekly_content = f"""
<h2>📋 Weekly Document Analysis - {datetime.now().strftime('%Y-%m-%d')}</h2>

<div class="document-card">
    <h3>Week at a Glance</h3>
    <ul>
        <li><strong>Documents Processed:</strong> {len(all_documents)}</li>
        <li><strong>Analysis Period:</strong> Last 7 days</li>
        <li><strong>Directories Monitored:</strong> {', '.join(self.document_dirs)}</li>
    </ul>
</div>

<h3>📊 Weekly Trend Analysis</h3>
<div class="document-card">
    {trend_analysis}
</div>

<h3>📄 Key Summaries</h3>
<div class="document-card">
    {summaries}
</div>

<h3>🔍 Intelligence Insights</h3>
<div class="document-card">
    {insights}
</div>

<h3>🔗 Document Relationships</h3>
<div class="relationship-map">
    {related_docs}
</div>

<div style="margin-top: 30px; padding: 15px; background-color: #e8f5e8; border-radius: 5px;">
    <h3>Weekly Insights Summary</h3>
    <p>This week's document analysis highlights key trends and important information from your monitored directories.</p>
    <p><strong>Next Analysis:</strong> Next Monday morning</p>
</div>
"""

        filepath = self.save_document_report(weekly_content, "weekly")

        if send_email:
            subject = f"📋 Weekly Document Intelligence Report - {datetime.now().strftime('%B %d, %Y')}"
            self.send_email_report(filepath, subject)

        logger.info("✅ Weekly document analysis completed")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Document Intelligence Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection
  %(prog)s --test

  # Daily scan of specific directories
  %(prog)s --daily --dirs /home/user/documents /home/user/reports

  # Weekly analysis with email
  %(prog)s --weekly --dirs /home/user/contracts --email manager@example.com

  # Monitor with subdirectories
  %(prog)s --daily --dirs /home/user/projects --recursive --email team@example.com

  # Scheduled daily scans at 7 AM
  %(prog)s --schedule-daily --dirs /home/user/documents /home/user/reports --email user@example.com
        """
    )

    # Mode arguments
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--test', action='store_true', help='Test server connection')
    mode_group.add_argument('--daily', action='store_true', help='Scan documents daily')
    mode_group.add_argument('--weekly', action='store_true', help='Weekly document analysis')
    mode_group.add_argument('--schedule-daily', action='store_true', help='Schedule daily scans')

    # Configuration
    parser.add_argument('--server', default='http://localhost:5000/v1', help='Server URL')
    parser.add_argument('--dirs', nargs='+', dest='document_dirs', help='Directories to monitor for documents')
    parser.add_argument('--recursive', action='store_true', help='Monitor subdirectories recursively (default: True)')
    parser.add_argument('--no-recursive', action='store_true', help='Don\'t monitor subdirectories')
    parser.add_argument('--email', help='Recipient email for reports')
    parser.add_argument('--output-dir', default='document_reports', help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Handle recursive flag
    if args.no_recursive:
        watch_recursive = False
    else:
        watch_recursive = True  # Default is True

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create agent
    agent = DocumentIntelligenceAgent(
        server_url=args.server,
        document_dirs=args.document_dirs or [],
        watch_subdirs=watch_recursive,
        recipient_email=args.email,
        output_dir=args.output_dir
    )

    try:
        if args.test:
            success = agent.test_connection()
            sys.exit(0 if success else 1)

        elif args.daily:
            success = agent.run_daily_scan(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.weekly:
            success = agent.run_weekly_analysis(send_email=bool(args.email))
            sys.exit(0 if success else 1)

        elif args.schedule_daily:
            logger.info("Scheduling daily document scans for 7:00 AM")
            schedule.every().day.at("07:00").do(
                lambda: agent.run_daily_scan(send_email=bool(args.email))
            )
            logger.info("Press Ctrl+C to stop")
            while True:
                schedule.run_pending()
                time.sleep(60)

    except KeyboardInterrupt:
        logger.info("\n👋 Document Intelligence Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()