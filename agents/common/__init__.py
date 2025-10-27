"""
Common utilities for Agentic-RAG agents.

This module provides shared functionality across all agents including:
- Server connection management
- Retry logic with exponential backoff
- HTML report generation
- Email sending utilities
- Logging configuration
"""

from .agent_utils import (
    create_openai_client,
    test_server_connection,
    execute_with_retry,
    setup_agent_logging,
    create_output_directory
)

from .report_utils import (
    create_html_report,
    save_html_report,
    send_email_report
)

__all__ = [
    'create_openai_client',
    'test_server_connection',
    'execute_with_retry',
    'setup_agent_logging',
    'create_output_directory',
    'create_html_report',
    'save_html_report',
    'send_email_report'
]
