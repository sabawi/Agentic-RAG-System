#!/usr/bin/env python3
"""
Debug embedding generation to see if that's the issue
"""

import asyncio
import sys
sys.path.append('.')

from document_interrogator import get_document_interrogator

async def debug_embedding_generation():
    """Test embedding generation directly"""
    
    print("🔍 Embedding Generation Debug")
    print("=" * 40)
    
    interrogator = get_document_interrogator()
    
    test_queries = ["ALAA", "passport", "test"]
    
    for query in test_queries:
        print(f"Testing embedding for: '{query}'")
        
        try:
            # Test embedding generation directly
            embeddings = await interrogator.store._generate_embeddings([query])
            
            if embeddings:
                print(f"   ✅ Generated embedding: {len(embeddings)} vectors, dimension: {len(embeddings[0])}")
                print(f"   🔢 First 5 values: {embeddings[0][:5]}")
            else:
                print("   ❌ No embeddings generated")
                
        except Exception as e:
            print(f"   ❌ Embedding generation failed: {e}")
            import traceback
            traceback.print_exc()
        
        print()

if __name__ == "__main__":
    asyncio.run(debug_embedding_generation())