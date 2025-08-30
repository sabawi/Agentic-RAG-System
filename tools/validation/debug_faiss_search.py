#!/usr/bin/env python3
"""
Debug FAISS search directly to understand why 'ALAA' doesn't find results
"""

import asyncio
import sys
from pathlib import Path
sys.path.append('.')

from document_interrogator import get_document_interrogator

async def debug_faiss_direct():
    """Debug FAISS search behavior directly"""
    
    print("🔍 Direct FAISS Search Debug")
    print("=" * 50)
    
    interrogator = get_document_interrogator()
    
    if not interrogator.is_ready():
        print("❌ Document interrogator not ready")
        return
    
    print(f"📊 FAISS Index: {interrogator.store.faiss_index.ntotal} vectors")
    print(f"🔧 Index type: {type(interrogator.store.faiss_index).__name__}")
    print()
    
    # Test the semantic search directly
    test_queries = ["ALAA", "Alaa", "Alaa Sabawi", "passport", "Government"]
    
    for query in test_queries:
        print(f"Testing query: '{query}'")
        print("-" * 30)
        
        try:
            # Call the search_similar method directly
            chunks = await interrogator.store.search_similar(query, 3)
            
            if not chunks:
                print("   ❌ No results from search_similar")
            else:
                print(f"   ✅ Found {len(chunks)} results:")
                for i, chunk in enumerate(chunks):
                    score = chunk['similarity_score']
                    doc_name = Path(chunk['document_path']).name
                    content_preview = chunk['content'][:60].replace('\n', ' ')
                    
                    # Check if it actually contains our query
                    contains = query.lower() in chunk['content'].lower()
                    marker = "✅" if contains else "❌"
                    
                    print(f"     {i+1}. {marker} {doc_name} | Score: {score:.1f} | {content_preview}...")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error in search_similar: {e}")
            import traceback
            traceback.print_exc()
            print()

if __name__ == "__main__":
    asyncio.run(debug_faiss_direct())