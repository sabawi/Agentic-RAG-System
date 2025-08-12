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
        
        Args:
            query: Search query or question
            max_results: Maximum number of chunks to return
            
        Returns:
            Dict with success, result, and error fields as expected by BaseUserTool
        """
        try:
            # Import here to avoid import errors if document interrogation isn't available
            try:
                from document_interrogator import get_document_interrogator
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
            
            # Perform document search
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
                return {
                    "success": True,
                    "result": f"🔍 No relevant documents found for query: '{query}'\n\nTip: Make sure documents are indexed first, or try different search terms.",
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