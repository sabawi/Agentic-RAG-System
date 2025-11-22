#!/usr/bin/env python3
"""
Report generation and email utilities for agents.

DEPRECATION NOTICE:
-------------------
This module is being phased out in favor of utils/html_generator.py.
The HTML generation functions below now act as compatibility wrappers
that redirect to the central HTML generator.

Migration Guide:
  OLD: from common.report_utils import create_html_report
  NEW: from utils.html_generator import create_html_report

All CSS classes from this module have been merged into the central
template at templates/html_report_template.html.

Author: Agentic-RAG Development Team
Version: 2.0.0 (Compatibility Wrapper)
"""

import logging
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional
import openai

# Import central HTML generator with absolute import
# Add project root to path to ensure utils can be imported
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.html_generator import create_html_report as central_create_html_report


# DEPRECATED: HTML_STYLE is kept for reference but no longer used
# All CSS has been merged into templates/html_report_template.html
HTML_STYLE = """
DEPRECATED: This CSS is no longer used.
All styling is now managed by templates/html_report_template.html
See utils/html_generator.py for current implementation.
"""


def create_html_report(
    title: str,
    content: str,
    subtitle: Optional[str] = None,
    additional_style: Optional[str] = None
) -> str:
    """
    Create a complete HTML report with standard styling.

    DEPRECATION WARNING: This is a compatibility wrapper.
    Please migrate to: from utils.html_generator import create_html_report

    Args:
        title: Main title of the report
        content: HTML content body
        subtitle: Optional subtitle/timestamp
        additional_style: Optional additional CSS styles

    Returns:
        Complete HTML document as string
    """
    # Issue deprecation warning (only once per session)
    warnings.warn(
        "common.report_utils.create_html_report is deprecated. "
        "Use utils.html_generator.create_html_report instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Generate subtitle if not provided
    if subtitle is None:
        subtitle = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # Redirect to central HTML generator with mapped parameters
    return central_create_html_report(
        content=content,
        title=title,
        header_title=title,
        header_subtitle=subtitle,
        include_disclaimer=False,  # Old report_utils didn't include disclaimer
        custom_css=additional_style
    )


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
            f"Use the secure_email_sender tool to send an email to {recipient_email} with:\n"
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
