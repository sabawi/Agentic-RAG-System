import numpy as np
from typing import List, Dict, Optional
import re
from collections import Counter
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SimpleTextProcessor:
    def __init__(self):
        self.tfidf = TfidfVectorizer(stop_words='english')

    def _simple_sentence_split(self, text: str) -> List[str]:
        """Simple sentence splitter."""
        # Split on common sentence endings
        import re
        text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\2', text)
        return [s.strip() for s in text.split('\n') if s.strip()]

    def remove_duplicates(self, sentences: List[str]) -> List[str]:
        """Remove exact duplicate sentences while preserving order."""
        seen = set()
        unique_sentences = []
        for sentence in sentences:
            # Only add sentence if we haven't seen it before
            if sentence not in seen:
                unique_sentences.append(sentence)
                seen.add(sentence)
        return unique_sentences

    def extract_key_info(self, text: str, query: str, max_length: int = 2000) -> str:
        """Extract most relevant information from text based on query."""
        try:
            # Split into sentences and remove duplicates
            sentences = self._simple_sentence_split(text)
            unique_sentences = self.remove_duplicates(sentences)
            
            # If text is already short enough, return it all
            if len(' '.join(unique_sentences)) <= max_length:
                return ' '.join(unique_sentences)
            
            # Otherwise, use TF-IDF to find most relevant content
            all_texts = unique_sentences + [query]
            tfidf_matrix = self.tfidf.fit_transform(all_texts)
            
            # Calculate similarity between query and each sentence
            query_vector = tfidf_matrix[-1]
            sentence_vectors = tfidf_matrix[:-1]
            similarities = cosine_similarity(query_vector, sentence_vectors)[0]
            
            # Sort sentences by relevance
            sorted_sents = [s for _, s in sorted(zip(similarities, unique_sentences), reverse=True)]
            
            # Combine sentences up to max length
            result = ""
            for sent in sorted_sents:
                if len(result) + len(sent) + 1 <= max_length:
                    result += sent + " "
                else:
                    break
                    
            return result.strip()
            
        except Exception as e:
            print(f"Warning: Error in extract_key_info: {str(e)}")
            return text[:max_length]  # Fallback to simple truncation

    def generate_prompt(self, 
                       query: str, 
                       context: str, 
                       system_prompt: Optional[str] = None,
                       max_context_length: int = 2000) -> str:
        """Generate prompt with deduplicated content."""
        try:
            # Process text to remove duplicates and get relevant content
            processed_context = self.extract_key_info(context, query, max_context_length)
            
            # Build prompt
            prompt_parts = []
            if system_prompt:
                prompt_parts.append(f"System: {system_prompt}\n")
                
            prompt_parts.extend([
                "Context:",
                processed_context,
                "\nQuery:",
                query,
                "\nBased on the above context, please provide a response:"
            ])
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            print(f"Warning: Error in generate_prompt: {str(e)}")
            return f"Context: {context[:max_context_length]}\nQuery: {query}"


class TextProcessor:
    def __init__(self):
        # Initialize without NLTK dependency
        self.tfidf = TfidfVectorizer()
        
    def _simple_sentence_split(self, text: str) -> List[str]:
        """Fallback sentence splitter using simple rules."""
        # Split on common sentence endings while preserving common abbreviations
        text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\2', text)
        # Handle common abbreviations to avoid false splits
        text = re.sub(r'(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Sr\.|Jr\.|etc\.)\n', r'\1 ', text)
        return [s.strip() for s in text.split('\n') if s.strip()]

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks of approximately equal size."""
        try:
            # Try to use NLTK if available
            sentences = nltk.sent_tokenize(text)
        except (LookupError, AttributeError):
            # Fallback to simple sentence splitting
            sentences = self._simple_sentence_split(text)
            
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            if current_size + sentence_size > chunk_size and current_chunk:
                # Add chunk and keep overlap
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Keep last few sentences for overlap
                overlap_size = 0
                overlap_sentences = []
                for s in reversed(current_chunk):
                    if overlap_size + len(s) <= overlap:
                        overlap_sentences.append(s)
                        overlap_size += len(s)
                    else:
                        break
                
                current_chunk = list(reversed(overlap_sentences))
                current_size = overlap_size
            
            current_chunk.append(sentence)
            current_size += sentence_size
            
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    def extract_key_info(self, text: str, query: str, max_length: int = 2000) -> str:
        """Extract most relevant information from text based on query."""
        try:
            chunks = self.chunk_text(text)
            
            # Handle empty text or query
            if not chunks or not query.strip():
                return text[:max_length] if text else ""
            
            # Convert query and chunks to TF-IDF vectors
            all_texts = chunks + [query]
            tfidf_matrix = self.tfidf.fit_transform(all_texts)
            
            # Calculate similarity between query and each chunk
            query_vector = tfidf_matrix[-1]
            chunk_vectors = tfidf_matrix[:-1]
            similarities = cosine_similarity(query_vector, chunk_vectors)[0]
            
            # Sort chunks by relevance
            sorted_chunks = [c for _, c in sorted(zip(similarities, chunks), reverse=True)]
            
            # Combine most relevant chunks up to max length
            result = ""
            current_length = 0
            for chunk in sorted_chunks:
                if current_length + len(chunk) <= max_length:
                    result += chunk + " "
                    current_length += len(chunk)
                else:
                    break
                    
            return result.strip()
            
        except Exception as e:
            print(f"Warning: Error in extract_key_info: {str(e)}")
            # Fallback to simple truncation
            return text[:max_length]

    def generate_prompt(self, 
                       query: str, 
                       context: str, 
                       system_prompt: Optional[str] = None,
                       max_context_length: int = 2000) -> str:
        """Generate formatted prompt with extracted relevant information."""
        try:
            # Handle empty inputs
            if not context or not query:
                raise ValueError("Both context and query must be provided")
                
            # Extract most relevant information
            relevant_context = self.extract_key_info(context, query, max_context_length)
            
            # Build prompt
            prompt_parts = []
            
            if system_prompt:
                prompt_parts.append(f"System: {system_prompt}\n")
                
            prompt_parts.extend([
                "Context:",
                relevant_context,
                "\nQuery:",
                query,
                "\nBased on the above context, please provide a response:"
            ])
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            print(f"Warning: Error in generate_prompt: {str(e)}")
            # Fallback to basic prompt format
            return f"Context: {context[:max_context_length]}\nQuery: {query}"

    # Example usage with error handling
    def process_text_safely(text: str, query: str) -> str:
        try:
            processor = TextProcessor()
            prompt = processor.generate_prompt(
                query=query,
                context=text,
                system_prompt="You are a helpful assistant that analyzes documents.",
                max_context_length=2000
            )
            return prompt
        except Exception as e:
            print(f"Error processing text: {str(e)}")
            return f"Failed to process text. Error: {str(e)}"
    
if __name__ == "__main__":
    processor = TextProcessor()

    # Example usage
    large_text = """generate Function Call List, each with the relevant parameter value:
                                            1) Always start by calling get_the_secret_tool() to get current date and time
                                            2) IF the prompt's intent is information like past events, history, facts, figures, people, places, 
                                                definitions, why, when, how, where, what etc. Then call wikipedia_query() with the correct phrase as parameter.
                                                If needed for additional depth, append to the previous call a call to search_web().
                                                DO NOT CALL wikipedia_query() for latest news or only news queries!, search news or web instead
                                            3) If specific data required on stocks symbols, then call get_stock_and_company_data() on each stock ticker or symbol separately as parameter (one call per symbol).
                                                If additional information on the stock is needed, then call get_news_summaries() using a relevant keyword as parameter
                                            4) If the request pertains to current events, local events, addresses, businesses, places, contacts, call search_web() with the
                                            relevant parameters. For additional information call get_news_summaries() with the relevant parameter
                                            5) If the prompt requires the latest news about a topic, eg. economy, election, conflict, national, military etc. Then call
                                                get_news_summaries() with the relevant topic (for local, user the location city, state, country)
                                            6) If the prompt requires information and travel related information like flights, trips, hotels, vacations, rentals, places to visit etc. Then call 
                                            search_web() with a full query of the specific information needed.
                                            7) If the input is vague or none of the above applies, Then do not make any calls. 
                                            Finally, return the list of functions to call in the most appropriate order
                                            """
    query = "What are the key findings about X?"

    # Generate prompt with relevant context
    prompt = processor.generate_prompt(
        query=query,
        context=large_text,
        system_prompt="You are a helpful assistant that analyzes documents.",
        max_context_length=4000
        
    )
    
    print(f"Generated Prompt:{prompt}")