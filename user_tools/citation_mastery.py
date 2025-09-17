"""
Citation Mastery Utility for User Tools
Provides the Citation Mastery formatting function for user-defined tools.
"""

from datetime import datetime
from typing import Optional


def format_source_block(source_url: str, title: str, content: str, source_num: int, timestamp: str = None) -> str:
    """
    Format individual source with simplified block structure for accurate LLM citation.
    
    This creates clear source blocks that help the Primary LLM maintain
    accurate URL-content associations without overwhelming context size.
    
    Args:
        source_url: The exact URL to cite (MANDATORY CITATION URL)
        title: Source title or description
        content: The actual content from the source
        source_num: Sequential source number for organization
        timestamp: Optional timestamp (auto-generated if not provided)
    
    Returns:
        Formatted source block with clear citation requirements
    """
    if not timestamp:
        timestamp = datetime.now().strftime('%A, %B %d, %Y %I:%M:%S %p')
    
    return f"""
═══════════════════════════════════════════════════════
📄 SOURCE BLOCK #{source_num} [REQUIRED CITATION: {source_url}]
═══════════════════════════════════════════════════════
Title: {title}
🔗 MANDATORY CITATION URL: {source_url}
📅 Retrieved: {timestamp}
───────────────────────────────────────────────────────
CONTENT: {content}
═══════════════════════════════════════════════════════
"""


def extract_domain(url: str) -> str:
    """Extract domain name from URL for titles"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        # Clean up common prefixes
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.capitalize()
    except Exception:
        return "Unknown Source"


def format_multiple_sources(sources_data: list, content_key: str = "content", 
                          url_key: str = "url", title_key: str = "title") -> str:
    """
    Format multiple sources using Citation Mastery.
    
    Args:
        sources_data: List of dictionaries containing source information
        content_key: Key for content in each source dict
        url_key: Key for URL in each source dict  
        title_key: Key for title in each source dict
    
    Returns:
        Combined formatted source blocks
    """
    if not sources_data:
        return "No sources found."
    
    formatted_blocks = []
    for i, source in enumerate(sources_data, 1):
        source_url = source.get(url_key, "")
        title = source.get(title_key, f"Source {i}")
        content = source.get(content_key, "No content available")
        
        if source_url:  # Only format sources with valid URLs
            formatted_block = format_source_block(
                source_url=source_url,
                title=title,
                content=content,
                source_num=i
            )
            formatted_blocks.append(formatted_block)
    
    return "\n".join(formatted_blocks)