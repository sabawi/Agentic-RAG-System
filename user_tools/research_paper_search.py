"""
Research Paper Search Tool

Searches academic research papers across multiple FREE APIs:
- Semantic Scholar (citation-ranked, high-impact papers)
- arXiv (CS/Math/Physics preprints)
- PubMed (biomedical research)

All output is Context Engineering compliant with SOURCE blocks for perfect citations.
"""

from typing import Dict, Any, List
from user_tools.base_user_tool import BaseUserTool
from utils.academic_research_client import AcademicResearchClient
from config.feature_flags import FeatureFlags
import logging

logger = logging.getLogger(__name__)


class ResearchPaperSearchTool(BaseUserTool):
    """
    Tool for searching academic research papers.

    Features:
    - Multi-API search (Semantic Scholar, arXiv, PubMed)
    - Automatic domain detection (CS vs Medical vs General)
    - Citation-ranked results
    - Full abstracts and PDF links when available
    - Context Engineering compliant output (SOURCE blocks)
    """

    def __init__(self):
        super().__init__()
        self.client = AcademicResearchClient()

    @property
    def name(self) -> str:
        return "search_research_papers"

    @property
    def description(self) -> str:
        return """Search for academic research papers across multiple FREE databases.

Searches:
- **Semantic Scholar**: High-impact papers with citation counts and influence metrics
- **arXiv**: Latest preprints in Computer Science, Mathematics, and Physics
- **PubMed**: 35M+ biomedical and life sciences articles

Features:
- Automatic source selection based on query domain
- Citation-ranked results (most influential papers first)
- Full abstracts when available
- Direct PDF links for open-access papers
- Publication dates and author information

Use this tool when you need:
- Latest AI/ML research and breakthroughs
- Scientific evidence for medical/health questions
- Academic papers on any technical or scientific topic
- Citation data and impact metrics
- Peer-reviewed research

Returns papers with proper citations and direct links to full texts."""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Research query or topic (e.g., 'transformer models in NLP', 'COVID-19 treatments', 'quantum computing algorithms')"
                },
                "sources": {
                    "type": "array",
                    "description": "Optional: Specific sources to search. Options: 'semantic_scholar', 'arxiv', 'pubmed'. If not specified, sources are auto-selected based on query.",
                    "items": {
                        "type": "string",
                        "enum": ["semantic_scholar", "arxiv", "pubmed"]
                    }
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of papers per source (1-20). Defaults to 10",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute research paper search.

        Args:
            query: Research query (required)
            sources: List of sources to search (optional, auto-detected if not provided)
            limit: Max results per source (optional, default: 10)

        Returns:
            Dict with success, result (formatted papers), or error
        """
        # Feature flag check
        if not FeatureFlags.ENABLE_ACADEMIC_RESEARCH:
            return {
                "success": False,
                "error": "Academic research integration is currently disabled."
            }

        try:
            # Extract parameters
            query = kwargs.get('query')
            if not query:
                return {
                    "success": False,
                    "error": "'query' parameter is required"
                }

            sources = kwargs.get('sources')  # Can be None (auto-detect)
            limit = kwargs.get('limit', 10)

            # Validate limit
            if not isinstance(limit, int) or limit < 1 or limit > 20:
                limit = 10

            logger.info(f"Searching research papers: query='{query}', sources={sources}, limit={limit}")

            # Search papers
            try:
                papers = self.client.search_papers(
                    query=query,
                    sources=sources,
                    limit=limit
                )
            except Exception as e:
                logger.error(f"Research search failed: {e}")
                return {
                    "success": False,
                    "error": f"Unable to search research papers. The academic APIs may be temporarily unavailable. Error: {str(e)}"
                }

            if not papers:
                return {
                    "success": False,
                    "error": f"No research papers found for query '{query}'. Try different keywords or broader terms."
                }

            # Format for LLM consumption (Context Engineering compliant)
            formatted_output = self._format_papers_for_llm(papers, query)

            logger.info(f"Successfully retrieved {len(papers)} research papers")

            return {
                "success": True,
                "result": formatted_output
            }

        except Exception as e:
            logger.error(f"Research paper search tool error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error executing research paper search: {str(e)}"
            }

    def _format_papers_for_llm(self, papers: List[Dict[str, Any]], query: str) -> str:
        """
        Format papers using Context Engineering standards (SOURCE blocks).

        Each paper is formatted as a SOURCE block with:
        - Title: Paper title and authors
        - URL: Direct link to paper
        - Date: Publication date
        - Content: Abstract, citations, source (truncated to 500 chars)
        """
        output_parts = [f"# Research Papers for: {query}\n"]

        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'Untitled')
            authors = paper.get('authors', [])
            abstract = paper.get('abstract', 'No abstract available')
            year = paper.get('year', 'Unknown')
            url = paper.get('url', '')
            pdf_url = paper.get('pdf_url')
            source = paper.get('source', 'Unknown')
            citations = paper.get('citation_count', 0)
            influential = paper.get('influential_citations', 0)
            journal = paper.get('journal', '')
            pub_date = paper.get('publication_date', '')

            # Format authors (limit to first 3)
            author_str = ', '.join(authors[:3])
            if len(authors) > 3:
                author_str += f' et al. ({len(authors)} authors)'

            # Build title with authors and year
            full_title = f"{title} ({year})"
            if author_str:
                full_title += f" - {author_str}"

            # Build content with abstract and metadata
            content_parts = []

            if abstract and abstract != 'No abstract available':
                content_parts.append(f"Abstract: {abstract}")

            # Add citation info for Semantic Scholar
            if source == 'Semantic Scholar' and citations > 0:
                citation_info = f"Citations: {citations:,}"
                if influential > 0:
                    citation_info += f" (Influential: {influential:,})"
                content_parts.append(citation_info)

            # Add source and journal info
            source_info = f"Source: {source}"
            if journal:
                source_info += f" | Journal: {journal}"
            content_parts.append(source_info)

            # Add PDF availability
            if pdf_url:
                content_parts.append(f"PDF Available: {pdf_url}")

            # Add publication date if different from year
            if pub_date and str(year) not in pub_date:
                content_parts.append(f"Published: {pub_date}")

            content = "\n".join(content_parts)

            # Truncate to 500 characters (Context Engineering standard)
            if len(content) > 500:
                content = content[:497] + "..."

            # Format as SOURCE block
            source_block = f"""SOURCE {i}:
Title: {full_title}
URL: {url}
Date: {year}
{content}


"""
            output_parts.append(source_block)

        # Add summary footer
        output_parts.append(f"\nTotal papers found: {len(papers)}")
        output_parts.append("Note: Papers ranked by relevance, citation impact, and recency.")
        output_parts.append("\n🔗 CITATION RULE: Use exact Title and URL from each SOURCE block in format [Title](URL)")

        return '\n'.join(output_parts)
