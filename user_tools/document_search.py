"""
Document Search Tool
Integrates FAISS document interrogation with the existing 2-stage LLM tool system
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool

logger = logging.getLogger(__name__)

class DocumentSearchTool(BaseUserTool):
    """
    Document search tool that integrates FAISS document interrogation
    with the existing 2-stage LLM tool system.
    """
    
    def __init__(self):
        super().__init__()
    
    @property
    def name(self) -> str:
        return "document_search"
    
    @property 
    def description(self) -> str:
        return """Search through indexed documents to find relevant information. This tool can search through PDF, Word, Excel, text, and other document types that have been previously indexed. Use this when you need to find information from local documents or when the user asks about content that might be in their document collection."""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query or question to find relevant documents"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of document chunks to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Execute document search using the FAISS document interrogator
        Enhanced with filename-based lookup and improved search strategies
        
        Args:
            query: Search query or question
            max_results: Maximum number of chunks to return
            
        Returns:
            Dict with success, result, and error fields as expected by BaseUserTool
        """
        # 🎯 ENFORCE REASONABLE LIMITS: Prevent massive output
        max_results = min(max_results, 10)
        logger.info(f"🔍 Document search with max_results limited to: {max_results}")
        try:
            # Import here to avoid import errors if document interrogation isn't available
            try:
                from document_interrogator import get_document_interrogator
                import sqlite3
            except ImportError:
                return {
                    "success": False,
                    "error": "Document search not available. Install dependencies: pip install faiss-cpu numpy PyPDF2 python-docx openpyxl beautifulsoup4",
                    "result": ""
                }
            
            # Get document interrogator instance
            interrogator = get_document_interrogator()
            
            if not interrogator.is_ready():
                return {
                    "success": False,
                    "error": "Document search system not ready. Please index documents first using /documents/index-directory endpoint.",
                    "result": ""
                }
            
            logger.info(f"🔍 Document search tool executing: {query}")
            
            # Strategy 1: Check if query contains a filename and do direct lookup
            filename_result = await self._try_filename_lookup(query, max_results)
            if filename_result:
                return filename_result
            
            # Strategy 2: Perform semantic search
            search_results = await interrogator.search_documents(query, max_results)
            
            logger.info(f"🔍 Search results: {search_results}")
            
            if search_results.get('error'):
                return {
                    "success": False,
                    "error": f"Search error: {search_results['error']}",
                    "result": ""
                }
            
            chunks_found = search_results.get('chunks_found', 0)
            
            if chunks_found == 0:
                # Strategy 3: Try alternative search with extracted keywords
                fallback_result = await self._try_fallback_search(query, max_results, interrogator)
                if fallback_result:
                    return fallback_result
                
                return {
                    "success": True,
                    "result": f"🔍 No relevant documents found for query: '{query}'\n\nTip: Try searching with specific content terms, names, or dates from the document rather than filenames.",
                    "error": None
                }
            
            # Format results
            result_parts = [
                f"📚 Found {chunks_found} relevant document chunks for: '{query}'",
                "",
                "📄 Document Excerpts:"
            ]
            
            chunks = search_results.get('chunks', [])
            
            for i, chunk in enumerate(chunks):
                doc_path = chunk.get('document_path', 'Unknown')
                doc_name = Path(doc_path).name if doc_path != 'Unknown' else 'Unknown Document'
                content = chunk.get('content', '')
                similarity_score = chunk.get('similarity', 0)
                
                result_parts.extend([
                    f"\n--- Document {i+1}: {doc_name} (Score: {similarity_score:.3f}) ---",
                    content[:500] + ("..." if len(content) > 500 else "")
                ])
            
            # Add sources summary
            unique_docs = set()
            for chunk in chunks:
                doc_path = chunk.get('document_path', 'Unknown')
                if doc_path != 'Unknown':
                    unique_docs.add(Path(doc_path).name)
            
            if unique_docs:
                result_parts.extend([
                    "",
                    "📋 Sources:",
                    *[f"• {doc}" for doc in sorted(unique_docs)]
                ])
            
            return {
                "success": True,
                "result": "\n".join(result_parts),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"❌ Document search tool error: {e}")
            return {
                "success": False,
                "error": f"Document search failed: {str(e)}",
                "result": ""
            }
    
    async def _try_filename_lookup(self, query: str, max_results: int) -> Optional[Dict[str, Any]]:
        """
        Check if query contains a filename and do direct database lookup
        """
        try:
            import sqlite3
            import re
            from pathlib import Path
            
            # Extract potential filenames from query (look for common patterns)
            filename_patterns = [
                r'([A-Za-z0-9_\-\s]+\.(jpg|jpeg|png|pdf|docx?|xlsx?|txt))',
                r'([A-Za-z0-9_\-\s]+_[A-Za-z0-9_\-\s]*\.(jpg|jpeg|png|pdf))',
                r'([A-Za-z0-9]+[_\-][A-Za-z0-9_\-\s]*\.(jpg|jpeg|png|pdf))'
            ]
            
            potential_filenames = []
            for pattern in filename_patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        potential_filenames.append(match[0])
                    else:
                        potential_filenames.append(match)
            
            if not potential_filenames:
                return None
            
            logger.info(f"🔍 Trying filename lookup for: {potential_filenames}")
            
            # Query database directly for filename matches
            db_path = Path(__file__).parent.parent / "document_store" / "metadata.db"
            
            with sqlite3.connect(str(db_path)) as conn:
                for filename in potential_filenames:
                    # Try exact match and fuzzy matches
                    queries = [
                        f"SELECT document_path, content FROM chunks WHERE document_path LIKE '%{filename}%' LIMIT {max_results}",
                        f"SELECT document_path, content FROM chunks WHERE document_path LIKE '%{filename.replace('_', ' ')}%' LIMIT {max_results}",
                        f"SELECT document_path, content FROM chunks WHERE document_path LIKE '%{filename.replace(' ', '_')}%' LIMIT {max_results}",
                        f"SELECT document_path, content FROM chunks WHERE document_path LIKE '%{filename.replace('-', '_')}%' LIMIT {max_results}"
                    ]
                    
                    for sql_query in queries:
                        cursor = conn.execute(sql_query)
                        rows = cursor.fetchall()
                        
                        if rows:
                            # Format results similar to semantic search
                            result_parts = [
                                f"📚 Found {len(rows)} document chunks by filename match: '{filename}'",
                                "",
                                "📄 Document Content:"
                            ]
                            
                            for i, (doc_path, content) in enumerate(rows):
                                doc_name = Path(doc_path).name
                                result_parts.extend([
                                    f"\\n--- Document {i+1}: {doc_name} (Filename Match) ---",
                                    content[:500] + ("..." if len(content) > 500 else "")
                                ])
                            
                            logger.info(f"✅ Filename lookup successful for: {filename}")
                            return {
                                "success": True,
                                "result": "\\n".join(result_parts),
                                "error": None
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Filename lookup error: {e}")
            return None
    
    async def _try_fallback_search(self, query: str, max_results: int, interrogator) -> Optional[Dict[str, Any]]:
        """
        Try alternative search strategies with extracted keywords
        """
        try:
            import re
            
            # Extract potential search terms from the query
            # Look for patterns like dates, names, addresses
            fallback_terms = []
            
            # Extract dates (MM/DD/YYYY, DD/MM/YYYY, etc.)
            date_patterns = [
                r'\\b(\\d{1,2}[/-]\\d{1,2}[/-]\\d{4})\\b',
                r'\\b(\\d{4}[/-]\\d{1,2}[/-]\\d{1,2})\\b'
            ]
            
            # Extract names (capitalized words)
            name_patterns = [
                r'\\b([A-Z][a-z]+ [A-Z][a-z]+)\\b',  # First Last
                r'\\b([A-Z]{2,})\\b'  # ALL CAPS (like SABAWI)
            ]
            
            # Extract location terms
            location_patterns = [
                r'\\b([A-Z][a-z]+ [A-Z][a-z]+,? [A-Z]{2})\\b',  # City State
                r'\\b(\\d+ [A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)\\b'  # Street address
            ]
            
            all_patterns = date_patterns + name_patterns + location_patterns
            
            for pattern in all_patterns:
                matches = re.findall(pattern, query)
                fallback_terms.extend(matches)
            
            # Try searches with individual terms
            for term in fallback_terms[:3]:  # Limit to first 3 terms
                logger.info(f"🔍 Trying fallback search with term: {term}")
                
                search_results = await interrogator.search_documents(term, max_results)
                
                if search_results.get('chunks_found', 0) > 0:
                    # Found results with this term
                    chunks = search_results.get('chunks', [])
                    result_parts = [
                        f"📚 Found {len(chunks)} documents using search term: '{term}' (extracted from your query)",
                        "",
                        "📄 Document Excerpts:"
                    ]
                    
                    for i, chunk in enumerate(chunks):
                        doc_path = chunk.get('document_path', 'Unknown')
                        doc_name = Path(doc_path).name if doc_path != 'Unknown' else 'Unknown Document'
                        content = chunk.get('content', '')
                        
                        result_parts.extend([
                            f"\\n--- Document {i+1}: {doc_name} (Term Match: '{term}') ---",
                            content[:500] + ("..." if len(content) > 500 else "")
                        ])
                    
                    logger.info(f"✅ Fallback search successful with term: {term}")
                    return {
                        "success": True,
                        "result": "\\n".join(result_parts),
                        "error": None
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fallback search error: {e}")
            return None