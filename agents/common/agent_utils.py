#!/usr/bin/env python3
"""
Core agent utilities for server communication and common operations.

All configuration values are loaded from config/agents_config.yaml.
No hardcoded configuration values allowed per PROJECT_CONFIGURATION_DIRECTIVE.

Author: Agentic-RAG Development Team
Version: 1.1.0
"""

import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Optional, Callable, TYPE_CHECKING

import openai

if TYPE_CHECKING:
    from .config_loader import AgentConfig


def create_openai_client(server_url: str, api_key: str = "not-required") -> openai.OpenAI:
    """
    Create and configure an OpenAI client for the Agentic-RAG server.

    Args:
        server_url: URL of the Agentic-RAG server (e.g., 'http://localhost:5000/v1')
        api_key: API key for authentication (default: 'not-required' for local server)

    Returns:
        Configured OpenAI client instance
    """
    return openai.OpenAI(
        base_url=server_url,
        api_key=api_key
    )


def create_client_from_config(config: 'AgentConfig') -> openai.OpenAI:
    """
    Create an OpenAI client using agent configuration.

    This is the preferred method for creating clients as it uses the
    centralized configuration system.

    Args:
        config: AgentConfig object from get_agent_config()

    Returns:
        Configured OpenAI client instance
    """
    return openai.OpenAI(
        base_url=config.get_server_url(),
        api_key=config.get_api_key()
    )


def test_server_connection(
    client: openai.OpenAI,
    logger: Optional[logging.Logger] = None,
    model: Optional[str] = None,
    config: Optional['AgentConfig'] = None
) -> bool:
    """
    Test connection to the Agentic-RAG server.

    Args:
        client: OpenAI client instance
        logger: Optional logger for output
        model: Model name to use (if not provided, uses config or defaults)
        config: Optional AgentConfig to get model from

    Returns:
        True if connection successful, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Get model from config if available
    if model is None:
        if config is not None:
            model = config.get_llm_model()
        else:
            # Fail-fast: require explicit model or config
            from .config_loader import AgentConfigLoader
            try:
                defaults = AgentConfigLoader.get_defaults()
                model = defaults.get('llm', {}).get('model')
                if not model:
                    raise ValueError("No default model configured")
            except Exception as e:
                logger.error(f"❌ No model specified and could not load default: {e}")
                return False

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=50
        )
        logger.info("✅ Server connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Server connection failed: {e}")
        return False


def execute_with_retry(
    client: openai.OpenAI,
    prompt: str,
    max_retries: Optional[int] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    logger: Optional[logging.Logger] = None,
    task_description: str = "Task",
    model: Optional[str] = None,
    config: Optional['AgentConfig'] = None,
    retry_base_delay: float = 2.0
) -> Optional[str]:
    """
    Execute a prompt with retry logic and exponential backoff.

    All parameters can be provided explicitly or loaded from config.
    Config values are used as defaults when explicit values are not provided.

    Args:
        client: OpenAI client instance
        prompt: The prompt to send to the server
        max_retries: Maximum number of retry attempts
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        logger: Optional logger for output
        task_description: Description of the task for logging
        model: Model name to use
        config: Optional AgentConfig to get defaults from
        retry_base_delay: Base delay for exponential backoff

    Returns:
        Response content as string or None if all retries failed
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Load defaults from config if provided
    if config is not None:
        if model is None:
            model = config.get_llm_model()
        if temperature is None:
            temperature = config.get_llm_setting('temperature', 0.7)
        if max_tokens is None:
            max_tokens = config.get_llm_setting('max_tokens', 4096)
        if max_retries is None:
            max_retries = config.get_execution_setting('max_retries', 3)
        retry_base_delay = config.get_execution_setting('retry_base_delay', 2.0)
    else:
        # Use provided values or sensible defaults
        if model is None:
            # Try to load from global defaults
            from .config_loader import AgentConfigLoader
            try:
                defaults = AgentConfigLoader.get_defaults()
                model = defaults.get('llm', {}).get('model')
            except Exception:
                pass
            if not model:
                logger.error("❌ No model specified and could not load default")
                return None
        if temperature is None:
            temperature = 0.7
        if max_tokens is None:
            max_tokens = 4096
        if max_retries is None:
            max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"{task_description} (attempt {attempt}/{max_retries})...")

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError("Response content is empty")

            logger.info(f"✅ {task_description} completed ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"❌ Attempt {attempt} failed: {e}")

            if attempt < max_retries:
                wait_time = retry_base_delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All retry attempts exhausted for {task_description}")
                return None


def setup_agent_logging(
    agent_name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup standardized logging for an agent.

    Args:
        agent_name: Name of the agent (used for logger name)
        log_file: Optional log file path (default: {agent_name}.log)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    if log_file is None:
        log_file = f"{agent_name}.log"

    # Create logger
    logger = logging.getLogger(agent_name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def create_output_directory(output_dir: str) -> Path:
    """
    Create output directory if it doesn't exist.

    Args:
        output_dir: Path to output directory

    Returns:
        Path object for the directory
    """
    path = Path(output_dir)
    path.mkdir(exist_ok=True, parents=True)
    return path
