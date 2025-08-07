#!/usr/bin/env python3
"""
Story analysis tool
"""
import re
from collections import Counter

def analyze_story(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic statistics
        word_count = len(content.split())
        char_count = len(content)
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        
        # Word frequency analysis
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = Counter(words)
        
        print("📊 STORY ANALYSIS RESULTS")
        print("=" * 30)
        print(f"Characters: {char_count:,}")
        print(f"Words: {word_count:,}")
        print(f"Paragraphs: {paragraph_count}")
        print(f"Average words per paragraph: {word_count/paragraph_count:.1f}")
        
        print("\n🔤 Most common words:")
        for word, count in word_freq.most_common(10):
            if len(word) > 3:  # Skip short words
                print(f"  {word}: {count}")
        
        # Save results
        with open("story_analysis.json", "w") as f:
            import json
            results = {
                "filename": filename,
                "statistics": {
                    "characters": char_count,
                    "words": word_count,
                    "paragraphs": paragraph_count,
                    "avg_words_per_paragraph": round(word_count/paragraph_count, 1)
                },
                "top_words": dict(word_freq.most_common(10))
            }
            json.dump(results, f, indent=2)
        
        print("\n✅ Analysis saved to story_analysis.json")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")

if __name__ == "__main__":
    analyze_story("short_stories/robot_painter_story.txt")
