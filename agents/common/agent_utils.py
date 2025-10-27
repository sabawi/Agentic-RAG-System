#!/usr/bin/env python3
"""
Core agent utilities for server communication and common operations.

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional, Callable
import openai


def create_openai_client(server_url: str) -> openai.OpenAI:
    """
    Create and configure an OpenAI client for the Agentic-RAG server.

    Args:
        server_url: URL of the Agentic-RAG server (e.g., 'http://localhost:5000/v1')

    Returns:
        Configured OpenAI client instance
    """
    return openai.OpenAI(
        base_url=server_url,
        api_key="not-required"
    )


def test_server_connection(client: openai.OpenAI, logger: Optional[logging.Logger] = None) -> bool:
    """
    Test connection to the Agentic-RAG server.

    Args:
        client: OpenAI client instance
        logger: Optional logger for output

    Returns:
        True if connection successful, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        response = client.chat.completions.create(
            model="Agentic-RAG-Model1",
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
    max_retries: int = 3,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    logger: Optional[logging.Logger] = None,
    task_description: str = "Task"
) -> Optional[str]:
    """
    Execute a prompt with retry logic and exponential backoff.

    Args:
        client: OpenAI client instance
        prompt: The prompt to send to the server
        max_retries: Maximum number of retry attempts
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        logger: Optional logger for output
        task_description: Description of the task for logging

    Returns:
        Response content as string or None if all retries failed
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"{task_description} (attempt {attempt}/{max_retries})...")

            response = client.chat.completions.create(
                model="Agentic-RAG-Model1",
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
                wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                logger.info(f"Retrying in {wait_time} seconds...")
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
