#!/usr/bin/env python3
"""
Debug FAISS search step by step to find where it's failing
"""

import asyncio
import sys
import numpy as np
sys.path.append('.')

from document_interrogator import get_document_interrogator

async def debug_faiss_step_by_step():
    """Debug each step of the FAISS search process"""
    
    print("🔍 FAISS Step-by-Step Debug")
    print("=" * 40)
    
    interrogator = get_document_interrogator()
    store = interrogator.store
    
    query = "Alaa Sabawi"
    k = 5
    
    print(f"🎯 Testing query: '{query}'")
    print(f"📊 FAISS index total vectors: {store.faiss_index.ntotal}")
    print()
    
    # Step 1: Generate embedding
    print("Step 1: Generate embedding")
    try:
        query_embeddings = await store._generate_embeddings([query])
        if not query_embeddings:
            print("   ❌ No embeddings generated")
            return
        
        print(f"   ✅ Generated embedding with {len(query_embeddings[0])} dimensions")
        query_vector = np.array(query_embeddings[0]).reshape(1, -1)
        print(f"   🔢 Query vector shape: {query_vector.shape}")
        print(f"   🔢 First 5 values: {query_vector[0][:5]}")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 2: FAISS search
    print("Step 2: FAISS search")
    try:
        search_k = min(k, store.faiss_index.ntotal)
        print(f"   🔍 Searching for top {search_k} results")
        
        scores, indices = store.faiss_index.search(query_vector, search_k)
        
        print(f"   📊 Raw FAISS results:")
        print(f"      Scores shape: {scores.shape}")
        print(f"      Indices shape: {indices.shape}")
        print(f"      Scores: {scores[0]}")
        print(f"      Indices: {indices[0]}")
        print()
        
    except Exception as e:
        print(f"   ❌ FAISS search error: {e}")
        return
    
    # Step 3: Process results
    print("Step 3: Process results")
    try:
        results = []
        cursor = store.metadata_db.cursor()
        
        for i, (score, faiss_idx) in enumerate(zip(scores[0], indices[0])):
            print(f"   Result {i+1}: score={score:.1f}, faiss_idx={faiss_idx}")
            
            if faiss_idx == -1:
                print(f"      ⚠️ No more results (faiss_idx = -1)")
                break
            
            # Query database
            cursor.execute('''
                SELECT chunk_id, document_path, chunk_index, content, metadata, created_at
                FROM chunks WHERE faiss_index = ?
            ''', (int(faiss_idx),))
            
            row = cursor.fetchone()
            if row:
                chunk_id, doc_path, chunk_idx, content, metadata_json, created_at = row
                print(f"      ✅ Found DB record: {doc_path.split('/')[-1]}")
                print(f"      📄 Content preview: {content[:50].replace(chr(10), ' ')}...")
                
                # Check if content contains our query
                contains_query = query.lower() in content.lower()
                print(f"      🔍 Contains '{query}': {contains_query}")
                
                results.append({
                    'chunk_id': chunk_id,
                    'document_path': doc_path,
                    'chunk_index': chunk_idx,
                    'content': content,
                    'similarity_score': float(score),
                    'created_at': created_at
                })
            else:
                print(f"      ❌ No DB record found for faiss_idx={faiss_idx}")
            
            print()
        
        print(f"📋 Final results: {len(results)} documents")
        
    except Exception as e:
        print(f"   ❌ Error processing results: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_faiss_step_by_step())