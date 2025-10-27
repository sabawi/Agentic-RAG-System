# Common Agent Utilities

This directory contains shared utilities used by all Agentic-RAG agents.

## Modules

### `agent_utils.py`
Core utilities for agent operations:
- **`create_openai_client(server_url)`** - Create configured OpenAI client
- **`test_server_connection(client, logger)`** - Test server connectivity
- **`execute_with_retry(client, prompt, ...)`** - Execute prompts with retry logic
- **`setup_agent_logging(agent_name, ...)`** - Configure standardized logging
- **`create_output_directory(output_dir)`** - Create output directories

### `report_utils.py`
HTML report generation and email utilities:
- **`create_html_report(title, content, ...)`** - Generate styled HTML reports
- **`save_html_report(content, output_dir, ...)`** - Save reports to files
- **`send_email_report(client, recipient, ...)`** - Send reports via email

## Usage Example

```python
from common import (
    create_openai_client,
    test_server_connection,
    execute_with_retry,
    setup_agent_logging,
    create_html_report,
    save_html_report
)

# Setup logging
logger = setup_agent_logging("my_agent")

# Create client
client = create_openai_client("http://localhost:5000/v1")

# Test connection
if not test_server_connection(client, logger):
    sys.exit(1)

# Execute task with retry
result = execute_with_retry(
    client,
    prompt="Get latest news",
    task_description="Fetching news",
    logger=logger
)

# Create and save report
html = create_html_report("My Report", result)
save_html_report(html, Path("output"), logger=logger)
```

## Dependencies

- `openai>=1.0.0`
- Python 3.7+

## Benefits

- **DRY Principle**: Eliminates code duplication across agents
- **Consistency**: All agents use same patterns
- **Maintainability**: Updates apply to all agents
- **Reliability**: Well-tested shared code
