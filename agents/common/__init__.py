"""
Common utilities for Agentic-RAG agents.

This module provides shared functionality across all agents including:
- Centralized configuration loading from config/agents_config.yaml
- Server connection management
- Retry logic with exponential backoff
- HTML report generation
- Email sending utilities
- Logging configuration

Configuration Loading:
    All agents should use the centralized configuration system:

    from common.config_loader import get_agent_config

    config = get_agent_config("my_agent")
    server_url = config.get_server_url()
    model = config.get_llm_model()
"""

from .config_loader import (
    AgentConfigLoader,
    AgentConfig,
    AgentConfigError,
    get_agent_config
)

from .agent_utils import (
    create_openai_client,
    create_client_from_config,
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
    # Configuration
    'AgentConfigLoader',
    'AgentConfig',
    'AgentConfigError',
    'get_agent_config',
    # Agent utilities
    'create_openai_client',
    'create_client_from_config',
    'test_server_connection',
    'execute_with_retry',
    'setup_agent_logging',
    'create_output_directory',
    # Report utilities
    'create_html_report',
    'save_html_report',
    'send_email_report'
]
