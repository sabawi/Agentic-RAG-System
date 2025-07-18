import re
import textwrap
from typing import List, Optional
from RAG_helper import LightweightRAG 
import ollama


text_model = "mistral:7b-instruct-v0.2-q4_0"

class TextChunker:
    @staticmethod
    def chunk_by_sentences(text: str, max_chunk_size: int = 500) -> List[str]:
        """
        Break text into chunks based on sentences
        
        Args:
            text (str): Input text to chunk
            max_chunk_size (int): Maximum characters per chunk
        
        Returns:
            List[str]: List of text chunks
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            # If adding this sentence would exceed max chunk size, start a new chunk
            if current_length + len(sentence) > max_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sentence)
            current_length += len(sentence) + 1  # +1 for space
        
        # Add final chunk if not empty
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    @staticmethod
    def chunk_by_paragraphs(text: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Break text into chunks based on paragraphs
        
        Args:
            text (str): Input text to chunk
            max_chunk_size (int): Maximum characters per chunk
        
        Returns:
            List[str]: List of text chunks
        """
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max chunk size, start a new chunk
            if current_length + len(paragraph) > max_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(paragraph)
            current_length += len(paragraph) + 1  # +1 for space
        
        # Add final chunk if not empty
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    @staticmethod
    def chunk_by_sliding_window(
        text: str, 
        chunk_size: int = 500, 
        overlap: int = 100
    ) -> List[str]:
        """
        Break text using a sliding window approach
        
        Args:
            text (str): Input text to chunk
            chunk_size (int): Size of each chunk
            overlap (int): Number of characters to overlap between chunks
        
        Returns:
            List[str]: List of text chunks
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Extract chunk
            chunk = text[start:start + chunk_size]
            chunks.append(chunk)
            
            # Move window
            start += chunk_size - overlap
        
        return chunks

    @staticmethod
    def semantic_chunk(
        text: str, 
        max_chunk_size: int = 10000, 
        min_chunk_size: int = 1
    ) -> List[str]:
        """
        Chunk text while preserving semantic boundaries
        
        Args:
            text (str): Input text to chunk
            max_chunk_size (int): Maximum characters per chunk
            min_chunk_size (int): Minimum characters per chunk
        
        Returns:
            List[str]: List of semantic text chunks
        """
        # Split into potential semantic units (sentences or sections)
        semantic_units = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for unit in semantic_units:
            # If current unit would make chunk too large, finalize current chunk
            if current_length + len(unit) > max_chunk_size:
                # Only create chunk if it meets minimum size
                if current_length >= min_chunk_size:
                    chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(unit)
            current_length += len(unit) + 1
        
        # Add final chunk if not empty and meets minimum size
        if current_chunk and current_length >= min_chunk_size:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def summary_by_semantics(full_text,query,max_length):
        semantic_chunks = TextChunker.semantic_chunk(full_text)
        
        lwr = LightweightRAG()
            
        for i, context in enumerate(semantic_chunks, 1):
            lwr.add_context(text=context)
    
        summary = lwr.generate_summary(query,max_length=max_length)

        return summary



    def filter_text(input_text, prompt, max_output_length=8192):
        print("ENTER : filter_text()",flush=True)
        # Chunk large input if needed
        chunks = [input_text[i:i+32000] for i in range(0, len(input_text), 32000)]
        
        filtered_results = []
        for chunk in chunks:
            response = ollama.chat(
                model=text_model, 
                messages=[
                    {
                        'role': 'system', 
                        'content': f'Extract the most semantically relevant {max_output_length} characters addressing the topic of this request: {prompt}'
                    },
                    {
                        'role': 'user', 
                        'content': chunk
                    }
                ]
            )
            filtered_results.append(response['message']['content'])
        
        # Combine and re-filter if multiple chunks
        final_filtered_text = ' '.join(filtered_results)
        print("EXIT : filter_text()",flush=True)
        return final_filtered_text[:max_output_length]




# Example usage
def main():
    # Sample large text input
    large_text = """
    Machine learning is a complex field that encompasses various approaches to data analysis. 
    At its core, machine learning involves training algorithms to recognize patterns and make 
    decisions with minimal human intervention. Deep learning, a subset of machine learning, 
    uses neural networks with multiple layers to progressively extract higher-level features 
    from raw input. These networks can learn representations of data with multiple levels of 
    abstraction, making them powerful tools for tasks like image recognition, natural language 
    processing, and predictive analytics.

    Data science builds upon these machine learning techniques, using statistical and computational 
    methods to extract insights from complex and often unstructured datasets. By combining domain 
    expertise, programming skills, and mathematical knowledge, data scientists can transform raw 
    data into actionable intelligence. The rise of big data and increasing computational power 
    has made these techniques more accessible and powerful than ever before.
    """

    # # Demonstrate different chunking methods
    # print("Chunking by Sentences:")
    # sentence_chunks = TextChunker.chunk_by_sentences(large_text)
    # for i, chunk in enumerate(sentence_chunks, 1):
    #     print(f"Chunk {i}: {chunk[:100]}...")

    # print("\nChunking by Paragraphs:")
    # paragraph_chunks = TextChunker.chunk_by_paragraphs(large_text)
    # for i, chunk in enumerate(paragraph_chunks, 1):
    #     print(f"Chunk {i}: {chunk[:100]}...")

    # print("\nChunking by Sliding Window:")
    # window_chunks = TextChunker.chunk_by_sliding_window(large_text)
    # for i, chunk in enumerate(window_chunks, 1):
    #     print(f"Chunk {i}: {chunk[:100]}...")

    # print("\nSemantic Chunking:")
    semantic_chunks = TextChunker.semantic_chunk(large_text)
    # for i, chunk in enumerate(semantic_chunks, 1):
    #     print(f"Chunk {i}: {chunk[:100]}...")

    lwr = LightweightRAG()
    
    for i, context in enumerate(semantic_chunks, 1):
        lwr.add_context(text=context)
    
    # Test retrieval
    query = "Tell me about machine learning"
    print("Relevant Contexts:")
    results = lwr.retrieve_relevant_context(query)
    
    for result in results:
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Context: {result['text']}")
    
    # Generate summary
    print("\nSummary:")
    summary = lwr.generate_summary(query)
    print(summary)

if __name__ == "__main__":
    main()
