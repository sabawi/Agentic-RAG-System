#!/usr/bin/env python3
"""
Test to find the similarity scores for Alaa's passport documents specifically
"""

import asyncio
import sys
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from document_interrogator import get_document_interrogator

async def test_passport_scores():
    """Test what similarity scores Alaa's passport documents get"""
    
    print("🔍 Testing Passport Document Similarity Scores")
    print("=" * 60)
    
    interrogator = get_document_interrogator()
    store = interrogator.store
    
    query = "Alaa Sabawi"
    k = 100  # Get lots of results to find the passports
    
    print(f"🎯 Testing query: '{query}' with k={k}")
    print()
    
    # Generate query embedding
    query_embeddings = await store._generate_embeddings([query])
    query_vector = np.array(query_embeddings[0]).reshape(1, -1)
    
    # Search FAISS index
    scores, indices = store.faiss_index.search(query_vector, min(k, store.faiss_index.ntotal))
    
    # Get metadata from SQLite
    cursor = store.metadata_db.cursor()
    
    print("🔍 All search results (looking for passport documents):")
    
    for i, (score, faiss_idx) in enumerate(zip(scores[0], indices[0])):
        if faiss_idx == -1:  # No more results
            break
        
        cursor.execute('''
            SELECT chunk_id, document_path, chunk_index, content, metadata, created_at
            FROM chunks WHERE faiss_index = ?
        ''', (int(faiss_idx),))
        
        row = cursor.fetchone()
        if row:
            chunk_id, doc_path, chunk_idx, content, metadata_json, created_at = row
            doc_name = doc_path.split('/')[-1]
            
            # Highlight passport documents
            is_passport = 'passport' in doc_name.lower() and 'alaa' in doc_name.lower()
            marker = "🎯 PASSPORT! " if is_passport else "   "
            
            print(f"{marker}Result {i+1}: {doc_name} (Score: {score:.1f})")
            
            if is_passport:
                print(f"      Path: {doc_path}")
                print(f"      Content preview: {content[:100].replace(chr(10), ' ')}...")
                print()

if __name__ == "__main__":
    asyncio.run(test_passport_scores())