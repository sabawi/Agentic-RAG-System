#!/usr/bin/env python3
"""
Test document search with threshold filtering directly
"""

import asyncio
import sys
sys.path.append('.')

from document_interrogator import get_document_interrogator

async def test_document_search():
    """Test document search with our new threshold filtering"""
    
    print("🔍 Testing Document Search with Threshold Filtering")
    print("=" * 60)
    
    interrogator = get_document_interrogator()
    
    query = "Alaa Sabawi"
    k = 20
    
    print(f"🎯 Testing query: '{query}' with k={k}")
    print(f"📊 FAISS index total vectors: {interrogator.store.faiss_index.ntotal}")
    print()
    
    # Test the search_similar method directly (this includes our threshold filtering)
    print("Step 1: Testing search_similar method (with threshold filtering)")
    similar_chunks = await interrogator.store.search_similar(query, k)
    
    print(f"📊 Filtered results: {len(similar_chunks)} chunks returned")
    
    for i, chunk in enumerate(similar_chunks):
        doc_name = chunk['document_path'].split('/')[-1]
        score = chunk['similarity_score']
        content_preview = chunk['content'][:50].replace('\n', ' ')
        print(f"   Result {i+1}: {doc_name} (Score: {score:.1f})")
        print(f"      Content: {content_preview}...")
        print()
    
    print()
    print("Step 2: Testing full document search pipeline")
    search_results = await interrogator.search_documents(query, k)
    
    chunks_found = search_results.get('chunks_found', 0)
    print(f"📊 Pipeline results: {chunks_found} chunks found")
    
    if chunks_found > 0:
        chunks = search_results.get('chunks', [])
        for i, chunk in enumerate(chunks):
            doc_name = chunk['document_path'].split('/')[-1]
            score = chunk['similarity_score']
            print(f"   Document {i+1}: {doc_name} (Score: {score:.1f})")

if __name__ == "__main__":
    asyncio.run(test_document_search())