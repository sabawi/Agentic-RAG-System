#!/usr/bin/env python3
"""
Test script to understand FAISS Inner Product similarity scoring
This will help us determine appropriate relevance thresholds
"""

import asyncio
import sys
from pathlib import Path
sys.path.append('.')

from document_interrogator import get_document_interrogator

async def analyze_faiss_scoring():
    """Analyze actual FAISS similarity scores for different query types"""
    
    print("🔍 FAISS Similarity Score Analysis")
    print("=" * 50)
    
    interrogator = get_document_interrogator()
    
    if not interrogator.is_ready():
        print("❌ Document interrogator not ready")
        return
    
    test_queries = [
        ("Alaa Sabawi", "Exact name match"),
        ("ALAA", "First name only"),
        ("SABAWI", "Last name only"),
        ("driver license", "Document type"),
        ("completely unrelated random text", "Unrelated query"),
        ("passport", "Generic document term"),
        ("birth certificate", "Another document type")
    ]
    
    print(f"📊 Testing with {len(test_queries)} different query types...")
    print(f"🏗️ FAISS Index Type: IndexFlatIP (Inner Product Similarity)")
    print(f"📈 Higher scores = MORE similar (for Inner Product)")
    print()
    
    for query, description in test_queries:
        print(f"Query: '{query}' ({description})")
        print("-" * 40)
        
        try:
            # Get search results
            result = await interrogator.search_documents(query, 5)
            chunks = result.get('chunks', [])
            
            if not chunks:
                print("   No results found")
                print()
                continue
            
            # Analyze score distribution
            scores = [chunk['similarity_score'] for chunk in chunks]
            max_score = max(scores)
            min_score = min(scores)
            avg_score = sum(scores) / len(scores)
            
            print(f"   📊 Score Range: {min_score:.1f} to {max_score:.1f} (avg: {avg_score:.1f})")
            print(f"   📋 Results ({len(chunks)}):")
            
            for i, chunk in enumerate(chunks):
                doc_name = Path(chunk['document_path']).name[:30]
                score = chunk['similarity_score']
                content_preview = chunk['content'][:60].replace('\n', ' ')
                
                # Check if this document actually contains the query terms
                contains_terms = any(term.lower() in chunk['content'].lower() 
                                   for term in query.split())
                relevance_marker = "✅" if contains_terms else "❌"
                
                print(f"     {i+1}. {relevance_marker} {doc_name:<30} | Score: {score:7.1f} | {content_preview}...")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    print("🎯 ANALYSIS SUMMARY:")
    print("- Look for clear score separation between relevant/irrelevant results")
    print("- Identify minimum score threshold for meaningful results")
    print("- Determine if current search is too permissive")

if __name__ == "__main__":
    asyncio.run(analyze_faiss_scoring())