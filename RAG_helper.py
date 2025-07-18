import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

class LightweightRAG:
    def __init__(self, max_features=1000):
        """
        Initialize lightweight RAG system using TF-IDF
        
        Args:
            max_features (int): Maximum number of features for TF-IDF
        """
        # TF-IDF Vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english'
        )
        
        # Context storage
        self.context_store: List[Dict[str, Any]] = []
        
        # Embedding matrix
        self.embedding_matrix = None

    def add_context(self, text: str, metadata: Dict[str, Any] = None):
        """
        Add new context to the system
        
        Args:
            text (str): Context text to add
            metadata (dict): Additional metadata about the context
        """
        # Store context
        context_entry = {
            'text': text,
            'metadata': metadata or {}
        }
        self.context_store.append(context_entry)
        
        # Recompute embeddings
        self._update_embeddings()

    def _update_embeddings(self):
        """
        Update TF-IDF embeddings for all contexts
        """
        try:
            # Extract texts
            texts = [ctx['text'] for ctx in self.context_store]
            # Fit and transform
            self.embedding_matrix = self.vectorizer.fit_transform(texts)
        except Exception as e:
            print(f"Error:_update_embeddings() returned error. exception message: {e}",flush=True)
        

    def retrieve_relevant_context(
        self, 
        query: str, 
        top_k: int = 3, 
        similarity_threshold: float = 0.1
    ) -> List[Dict]:
        """
        Retrieve most relevant context
        
        Args:
            query (str): Query to find relevant context
            top_k (int): Number of top relevant contexts to return
            similarity_threshold (float): Minimum similarity score
        
        Returns:
            List[Dict]: Most relevant context entries
        """
        # Ensure embeddings exist
        if self.embedding_matrix is None:
            self._update_embeddings()
        
        # Transform query
        query_embedding = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embedding_matrix)[0]
        
        # Create result list with similarities
        relevant_contexts = [
            {
                'text': self.context_store[i]['text'], 
                'similarity': similarities[i],
                'metadata': self.context_store[i]['metadata']
            }
            for i in range(len(self.context_store))
            if similarities[i] >= similarity_threshold
        ]
        
        # Sort and return top k
        return sorted(
            relevant_contexts, 
            key=lambda x: x['similarity'], 
            reverse=True
        )[:top_k]

    def generate_summary(self, query: str, max_length: int = 300) -> str:
        """
        Generate a summary based on retrieved contexts
        
        Args:
            query (str): Query to base summary on
            max_length (int): Maximum summary length
        
        Returns:
            str: Generated summary
        """
        # Retrieve relevant contexts
        relevant_contexts = self.retrieve_relevant_context(query)
        
        # Combine contexts
        combined_text = " ".join([ctx['text'] for ctx in relevant_contexts])
        
        # Truncate to max length
        return combined_text[:max_length] + "..."

# Example usage
def main():
    # Initialize RAG
    rag_context = LightweightRAG()
    
    # Add sample contexts
    contexts = [
        "Machine learning uses algorithms to learn from data",
        "Deep learning is a subset of machine learning with neural networks",
        "Data science involves extracting insights from complex datasets",
        "Artificial intelligence aims to create intelligent machines"
    ]
    
    for context in contexts:
        rag_context.add_context(context)
    
    # Test retrieval
    query = "Tell me about machine learning"
    print("Relevant Contexts:")
    results = rag_context.retrieve_relevant_context(query)
    
    for result in results:
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Context: {result['text']}")
    
    # Generate summary
    print("\nSummary:")
    summary = rag_context.generate_summary(query)
    print(summary)

if __name__ == "__main__":
    main()