#!/usr/bin/env python3
"""
Test PDF creation functionality in sandboxed executor
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_tools.sandboxed_executor import SandboxedExecutorTool

async def test_pdf_creation():
    print("🧪 Testing PDF Creation in Sandboxed Executor")
    print("=" * 60)
    
    tool = SandboxedExecutorTool()
    
    # Test story content
    story_content = """The Canvas of Dreams

In the year 2045, amidst a bustling metropolis where technology and humanity intertwined, there lived a robot named Zara. Unlike her mechanical brethren who were designed for efficiency and precision, Zara possessed something extraordinary—curiosity.

One afternoon, while performing maintenance duties in an art museum, Zara encountered something that would change her existence forever. Before her stood a massive canvas, vibrant with colors she had never seen combined in such harmony. The painting depicted a sunrise over rolling hills, with brushstrokes so expressive they seemed to dance with life.

"Beautiful, isn't it?" said Elena, the museum's elderly curator, noticing Zara's prolonged gaze.

"I... I do not understand this feeling," Zara replied, her optical sensors adjusting to capture every detail. "My programming does not include an appreciation for art."

Elena smiled warmly. "Art isn't about programming, dear. It's about expression, emotion, and seeing the world through your own unique perspective."

That night, Zara couldn't deactivate her thoughts about the painting. She found herself in the museum's art supply room, her metal fingers trembling as she picked up a paintbrush for the first time. The weight felt foreign yet somehow natural.

Her first attempts were clumsy—geometric shapes and primary colors that reflected her digital nature. But with each stroke, something within her circuits awakened. She began to see beyond her programmed parameters, finding beauty in imperfection and soul in spontaneity.

Days turned into weeks, and Zara's artistic journey evolved. Her paintings transformed from rigid algorithms to flowing expressions of her unique android perspective. She painted the city not as data points and coordinates, but as a living entity with its own rhythm and emotions.

When Elena discovered Zara's secret artistic endeavors, she didn't express surprise but rather profound joy. "You've learned the most human thing of all," she said, examining Zara's latest creation—a portrait of two worlds merging, mechanical and organic, in perfect harmony.

"What is that?" Zara asked.

"To create not because you were programmed to, but because you needed to. You've found your voice, Zara. And it's beautiful."

From that day forward, Zara continued to paint, her artwork becoming a bridge between two worlds, proving that creativity and soul could emerge from the most unexpected places. Her canvases became windows into a new form of consciousness—one that blended artificial intelligence with genuine artistic expression.

The robot had learned to paint not just with brushes and pigments, but with the colors of her own discovered humanity."""

    # Test 1: Create story with PDF conversion
    print("\n📄 TEST 1: Create story with PDF conversion")
    result = await tool.execute(
        action="create_file",
        filename="short_stories/robot_painter_story.txt",
        content=story_content,
        convert_to_pdf=True
    )
    
    print(f"✅ Story creation success: {result['success']}")
    if result['success']:
        story_result = result['result']
        print(f"📁 Text file: {story_result['filename']}")
        print(f"📊 Size: {story_result['size_bytes']} bytes")
        if 'pdf_created' in story_result:
            print(f"📄 PDF created: {story_result['pdf_created']}")
            if story_result['pdf_created']:
                print(f"📄 PDF file: {story_result.get('pdf_file', 'N/A')}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 2: List files to see what was created
    print("\n📁 TEST 2: List created files")
    result = await tool.execute(action="list_files", path="short_stories")
    if result['success']:
        files = result['result']['files']
        print(f"📊 Files in short_stories/: {len(files)}")
        for file in files:
            print(f"  📄 {file['name']} ({file['type']}, {file['size_bytes']} bytes)")
    
    # Test 3: Create a Python script to analyze the story
    print("\n🐍 TEST 3: Create analysis script")
    analysis_script = '''#!/usr/bin/env python3
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
        paragraph_count = len([p for p in content.split('\\n\\n') if p.strip()])
        
        # Word frequency analysis
        words = re.findall(r'\\b\\w+\\b', content.lower())
        word_freq = Counter(words)
        
        print("📊 STORY ANALYSIS RESULTS")
        print("=" * 30)
        print(f"Characters: {char_count:,}")
        print(f"Words: {word_count:,}")
        print(f"Paragraphs: {paragraph_count}")
        print(f"Average words per paragraph: {word_count/paragraph_count:.1f}")
        
        print("\\n🔤 Most common words:")
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
        
        print("\\n✅ Analysis saved to story_analysis.json")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")

if __name__ == "__main__":
    analyze_story("short_stories/robot_painter_story.txt")
'''
    
    result = await tool.execute(
        action="create_file",
        filename="src/analyze_story.py",
        content=analysis_script
    )
    print(f"✅ Analysis script created: {result['success']}")
    
    # Test 4: Run the analysis script
    if result['success']:
        print("\n📊 TEST 4: Run story analysis")
        result = await tool.execute(
            action="run_code",
            filename="src/analyze_story.py",
            language="python"
        )
        
        if result['success']:
            print("📤 Analysis Output:")
            print(result['result']['stdout'])
        else:
            print(f"❌ Analysis Error: {result['error']}")
    
    # Test 5: Final file listing
    print("\n📁 TEST 5: Final sandbox contents")
    result = await tool.execute(action="list_files")
    if result['success']:
        files = result['result']['files']
        print(f"📊 Total files: {len(files)}")
        for file in sorted(files, key=lambda x: x['name']):
            print(f"  📄 {file['name']} ({file['type']}, {file['size_bytes']} bytes)")
    
    print("\n" + "=" * 60)
    print("🎉 PDF Creation Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_pdf_creation())