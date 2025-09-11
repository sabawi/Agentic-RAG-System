#!/usr/bin/env python3
"""
Rebuild FAISS index from existing database content
"""

import asyncio
import sys
import json
from pathlib import Path
sys.path.append('.')

from document_interrogator import get_document_interrogator

async def rebuild_faiss_index():
    """Rebuild FAISS index from existing database content"""
    
    print("🔄 Rebuilding FAISS Index from Database")
    print("=" * 50)
    
    interrogator = get_document_interrogator()
    store = interrogator.store
    
    # Get all chunks from database
    cursor = store.metadata_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM chunks")
    total_chunks = cursor.fetchone()[0]
    
    print(f"📊 Found {total_chunks} chunks in database")
    print(f"📊 Current FAISS index size: {store.faiss_index.ntotal}")
    
    if store.faiss_index.ntotal > 0:
        print("⚠️ FAISS index already has vectors. Clearing...")
        # Clear existing index
        store.faiss_index.reset()
    
    print("\n🔄 Starting rebuild process...")
    
    # Get all chunks with their content
    cursor.execute("""
        SELECT chunk_id, content, document_path 
        FROM chunks 
        ORDER BY faiss_index
    """)
    
    chunks_to_reindex = cursor.fetchall()
    
    batch_size = 100  # Process in batches
    total_processed = 0
    
    for i in range(0, len(chunks_to_reindex), batch_size):
        batch = chunks_to_reindex[i:i + batch_size]
        
        # Extract content for embedding generation
        batch_content = [chunk[1] for chunk in batch]  # content is index 1
        
        print(f"📦 Processing batch {i//batch_size + 1}: {len(batch)} chunks")
        
        try:
            # Generate embeddings for this batch
            embeddings = await store._generate_embeddings(batch_content)
            
            if not embeddings or len(embeddings) != len(batch):
                print(f"   ❌ Failed to generate embeddings for batch")
                continue
            
            # Add to FAISS index
            import numpy as np
            embeddings_array = np.array(embeddings).astype('float32')
            
            # The FAISS index should auto-assign indices starting from current size
            start_idx = store.faiss_index.ntotal
            store.faiss_index.add(embeddings_array)
            
            # Update database with new FAISS indices
            for j, (chunk_id, content, doc_path) in enumerate(batch):
                new_faiss_idx = start_idx + j
                cursor.execute("""
                    UPDATE chunks 
                    SET faiss_index = ? 
                    WHERE chunk_id = ?
                """, (new_faiss_idx, chunk_id))
            
            store.metadata_db.commit()
            total_processed += len(batch)
            
            print(f"   ✅ Added {len(batch)} vectors to FAISS index")
            print(f"   📊 Progress: {total_processed}/{total_chunks} chunks ({100*total_processed/total_chunks:.1f}%)")
            
        except Exception as e:
            print(f"   ❌ Error processing batch: {e}")
            import traceback
            traceback.print_exc()
    
    # Save the rebuilt index
    try:
        await store._save_index()
        print(f"\n✅ Rebuild complete!")
        print(f"📊 Final FAISS index size: {store.faiss_index.ntotal}")
        print(f"📊 Total chunks processed: {total_processed}")
        
    except Exception as e:
        print(f"\n❌ Error saving index: {e}")

if __name__ == "__main__":
    asyncio.run(rebuild_faiss_index())