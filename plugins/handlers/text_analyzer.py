#!/usr/bin/env python3
"""
Text Analyzer Plugin
Performs statistical and linguistic analysis on text.
"""

import sys
import json
import asyncio
import re
from typing import Dict, Any, List, Tuple
from collections import Counter


def tokenize_words(text: str) -> List[str]:
    """Tokenize text into words"""
    # Remove punctuation and convert to lowercase
    words = re.findall(r'\b[a-z]{2,}\b', text.lower())
    return words


def tokenize_sentences(text: str) -> List[str]:
    """Split text into sentences"""
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def calculate_basic_stats(text: str) -> Dict[str, Any]:
    """Calculate basic text statistics"""
    words = tokenize_words(text)
    sentences = tokenize_sentences(text)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    return {
        "character_count": len(text),
        "character_count_no_spaces": len(text.replace(' ', '')),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
        "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
        "reading_time_minutes": len(words) / 200  # Average reading speed: 200 wpm
    }


def get_word_frequency(words: List[str], top_n: int = 10) -> List[Tuple[str, int]]:
    """Get most frequent words"""
    # Common stop words to filter out
    stop_words = {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
        'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
        'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
        'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
        'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
        'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
        'into', 'year', 'your', 'some', 'could', 'them', 'see', 'other', 'than',
        'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
        'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way',
        'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'
    }

    # Filter out stop words
    filtered_words = [w for w in words if w not in stop_words]

    # Count frequencies
    word_counts = Counter(filtered_words)

    return word_counts.most_common(top_n)


def calculate_readability(text: str, stats: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate readability metrics"""
    words = tokenize_words(text)
    sentences = tokenize_sentences(text)

    if not sentences or not words:
        return {
            "flesch_reading_ease": 0,
            "reading_level": "Unable to calculate",
            "complexity": "Unknown"
        }

    # Count syllables (simplified)
    def count_syllables(word: str) -> int:
        vowels = 'aeiou'
        count = sum(1 for i, char in enumerate(word) if char in vowels and (i == 0 or word[i-1] not in vowels))
        return max(1, count)

    total_syllables = sum(count_syllables(w) for w in words)

    # Flesch Reading Ease Score
    # Formula: 206.835 - 1.015(total words/total sentences) - 84.6(total syllables/total words)
    avg_sentence_length = len(words) / len(sentences)
    avg_syllables_per_word = total_syllables / len(words)

    flesch_score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word

    # Interpret score
    if flesch_score >= 90:
        level = "Very Easy (5th grade)"
        complexity = "Very Simple"
    elif flesch_score >= 80:
        level = "Easy (6th grade)"
        complexity = "Simple"
    elif flesch_score >= 70:
        level = "Fairly Easy (7th grade)"
        complexity = "Fairly Simple"
    elif flesch_score >= 60:
        level = "Standard (8th-9th grade)"
        complexity = "Standard"
    elif flesch_score >= 50:
        level = "Fairly Difficult (10th-12th grade)"
        complexity = "Fairly Complex"
    elif flesch_score >= 30:
        level = "Difficult (College)"
        complexity = "Complex"
    else:
        level = "Very Difficult (College graduate)"
        complexity = "Very Complex"

    return {
        "flesch_reading_ease": round(flesch_score, 1),
        "reading_level": level,
        "complexity": complexity,
        "avg_syllables_per_word": round(avg_syllables_per_word, 2),
        "total_syllables": total_syllables
    }


def perform_sentiment_analysis(text: str) -> Dict[str, Any]:
    """Simple sentiment analysis based on keyword matching"""
    positive_words = {
        'good', 'great', 'excellent', 'wonderful', 'amazing', 'fantastic', 'love',
        'best', 'perfect', 'beautiful', 'awesome', 'brilliant', 'happy', 'joy',
        'delightful', 'superb', 'outstanding', 'magnificent', 'terrific', 'splendid'
    }

    negative_words = {
        'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst', 'hate', 'disappointing',
        'sad', 'angry', 'annoying', 'frustrating', 'difficult', 'problem', 'issue',
        'fail', 'failure', 'wrong', 'broken', 'useless'
    }

    words = tokenize_words(text)

    positive_count = sum(1 for w in words if w in positive_words)
    negative_count = sum(1 for w in words if w in negative_words)

    total_sentiment_words = positive_count + negative_count

    if total_sentiment_words == 0:
        sentiment = "Neutral"
        polarity = 0.0
    else:
        polarity = (positive_count - negative_count) / total_sentiment_words

        if polarity > 0.3:
            sentiment = "Positive"
        elif polarity < -0.3:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

    return {
        "sentiment": sentiment,
        "polarity": round(polarity, 2),
        "positive_words": positive_count,
        "negative_words": negative_count
    }


async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze text content.

    Args:
        parameters: {
            "text": str,
            "analysis_type": "basic" | "detailed" | "readability",
            "top_words_count": int
        }

    Returns:
        {
            "success": bool,
            "result": str,
            "error": str | None,
            "metadata": dict
        }
    """
    text = parameters['text']
    analysis_type = parameters.get('analysis_type', 'basic')
    top_words_count = parameters.get('top_words_count', 10)

    try:
        # Calculate basic statistics
        stats = calculate_basic_stats(text)
        words = tokenize_words(text)

        result_lines = ["📊 Text Analysis Results:\n"]

        # Basic statistics (always included)
        result_lines.extend([
            f"📝 Basic Statistics:",
            f"  Characters: {stats['character_count']:,} (without spaces: {stats['character_count_no_spaces']:,})",
            f"  Words: {stats['word_count']:,}",
            f"  Sentences: {stats['sentence_count']:,}",
            f"  Paragraphs: {stats['paragraph_count']:,}",
            f"  Average word length: {stats['avg_word_length']:.1f} characters",
            f"  Average sentence length: {stats['avg_sentence_length']:.1f} words",
            f"  Estimated reading time: {stats['reading_time_minutes']:.1f} minutes",
        ])

        metadata = {"basic_stats": stats}

        # Detailed analysis
        if analysis_type in ['detailed', 'readability']:
            # Word frequency
            word_freq = get_word_frequency(words, top_words_count)
            result_lines.append(f"\n📈 Top {len(word_freq)} Most Frequent Words:")
            for i, (word, count) in enumerate(word_freq, 1):
                result_lines.append(f"  {i}. '{word}': {count} times")

            metadata['word_frequency'] = [{"word": w, "count": c} for w, c in word_freq]

            # Sentiment analysis
            sentiment = perform_sentiment_analysis(text)
            result_lines.extend([
                f"\n😊 Sentiment Analysis:",
                f"  Overall sentiment: {sentiment['sentiment']}",
                f"  Polarity score: {sentiment['polarity']} (-1 to +1)",
                f"  Positive words: {sentiment['positive_words']}",
                f"  Negative words: {sentiment['negative_words']}"
            ])

            metadata['sentiment'] = sentiment

        # Readability analysis
        if analysis_type == 'readability':
            readability = calculate_readability(text, stats)
            result_lines.extend([
                f"\n📖 Readability Analysis:",
                f"  Flesch Reading Ease: {readability['flesch_reading_ease']}",
                f"  Reading Level: {readability['reading_level']}",
                f"  Complexity: {readability['complexity']}",
                f"  Average syllables per word: {readability['avg_syllables_per_word']}",
                f"  Total syllables: {readability['total_syllables']:,}"
            ])

            metadata['readability'] = readability

        result_text = '\n'.join(result_lines)

        return {
            "success": True,
            "result": result_text,
            "error": None,
            "metadata": metadata
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Error analyzing text: {str(e)}",
            "metadata": {
                "analysis_type": analysis_type,
                "error_type": type(e).__name__
            }
        }


# Communication protocol (boilerplate)
if __name__ == "__main__":
    try:
        input_data = sys.stdin.read()
        parameters = json.loads(input_data)
        result = asyncio.run(execute(parameters))
        print(json.dumps(result))
        sys.exit(0 if result['success'] else 1)
    except Exception as e:
        error_result = {
            "success": False,
            "result": None,
            "error": f"Plugin error: {str(e)}",
            "metadata": {}
        }
        print(json.dumps(error_result))
        sys.exit(1)
