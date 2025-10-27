#!/usr/bin/env python3
"""
Report generation and email utilities for agents.

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import openai


# Standard HTML styling for reports
HTML_STYLE = """
<style>
    body {
        font-family: Arial, sans-serif;
        max-width: 1000px;
        margin: 0 auto;
        padding: 20px;
        line-height: 1.6;
        background-color: #f8f9fa;
    }
    h1 {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
    }
    h2 {
        color: #34495e;
        margin-top: 30px;
    }
    h3 {
        color: #2980b9;
    }
    .critical {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 10px;
        margin: 10px 0;
    }
    .high {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 10px;
        margin: 10px 0;
    }
    .medium {
        background-color: #f3e5f5;
        border-left: 5px solid #9c27b0;
        padding: 10px;
        margin: 10px 0;
    }
    .low {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
        padding: 10px;
        margin: 10px 0;
    }
    .info {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
        padding: 10px;
        margin: 10px 0;
    }
    .action-item {
        background-color: #fffde7;
        border: 2px solid #ffeb3b;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .priority-1 {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 10px;
    }
    .priority-2 {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 10px;
    }
    .priority-3 {
        background-color: #f3e5f5;
        border-left: 5px solid #9c27b0;
        padding: 10px;
    }
    .priority-4 {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
        padding: 10px;
    }
    .priority-5 {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
        padding: 10px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    th {
        background-color: #34495e;
        color: white;
    }
    tr:hover {
        background-color: #f5f5f5;
    }
    a {
        color: #3498db;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    .timestamp {
        color: #7f8c8d;
        font-style: italic;
        margin: 20px 0;
    }
    .sender {
        font-weight: bold;
        color: #2c3e50;
    }
    .subject {
        font-style: italic;
        color: #7f8c8d;
    }
    .priority-high {
        color: #e74c3c;
        font-weight: bold;
    }
    .priority-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .priority-low {
        color: #7f8c8d;
    }
    .relevance-high {
        color: #e74c3c;
        font-weight: bold;
    }
    .relevance-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .relevance-low {
        color: #7f8c8d;
    }
    .stats-box {
        margin-top: 30px;
        padding: 15px;
        background-color: #e3f2fd;
        border-radius: 5px;
    }
</style>
"""


def create_html_report(
    title: str,
    content: str,
    subtitle: Optional[str] = None,
    additional_style: Optional[str] = None
) -> str:
    """
    Create a complete HTML report with standard styling.

    Args:
        title: Main title of the report
        content: HTML content body
        subtitle: Optional subtitle/timestamp
        additional_style: Optional additional CSS styles

    Returns:
        Complete HTML document as string
    """
    if subtitle is None:
        subtitle = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # Combine styles
    style = HTML_STYLE
    if additional_style:
        style += f"\n{additional_style}"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {style}
</head>
<body>
    <div style="text-align: center; margin-bottom: 20px;">
        <h1>{title}</h1>
        <p class="timestamp">{subtitle}</p>
    </div>
    {content}
</body>
</html>"""

    return html_content


def save_html_report(
    content: str,
    output_dir: Path,
    filename: Optional[str] = None,
    title: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> Path:
    """
    Save HTML report to file.

    Args:
        content: HTML content (can be full HTML or just body content)
        output_dir: Directory to save report
        filename: Optional custom filename (default: timestamped)
        title: Optional title if content is not full HTML
        logger: Optional logger for output

    Returns:
        Path to saved file

    Raises:
        Exception if save fails
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.html"

    filepath = output_dir / filename

    try:
        # Wrap in HTML if not already complete
        if not content.strip().startswith("<!DOCTYPE html") and not content.strip().startswith("<html"):
            if title is None:
                title = "Agent Report"
            html_content = create_html_report(title, content)
        else:
            html_content = content

        filepath.write_text(html_content, encoding='utf-8')
        logger.info(f"✅ Saved report to: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"❌ Failed to save report: {e}")
        raise


def send_email_report(
    client: openai.OpenAI,
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Send email report using the server's secure_email_sender tool.

    Args:
        client: OpenAI client instance
        recipient_email: Recipient email address
        subject: Email subject
        body: Email body text
        attachment_path: Optional path to file attachment
        logger: Optional logger for output

    Returns:
        True if email was sent successfully, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        logger.info(f"Sending email to {recipient_email}...")

        # Build email prompt
        email_content = (
            f"Send an email to {recipient_email} with:\n"
            f"Subject: '{subject}'\n"
            f"Body: '{body}'\n"
        )

        if attachment_path:
            email_content += f"Attach: {attachment_path.absolute()}"

        response = client.chat.completions.create(
            model="Agentic-RAG-Model1",
            messages=[{"role": "user", "content": email_content}],
            max_tokens=500
        )

        logger.info("✅ Email sent successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False
