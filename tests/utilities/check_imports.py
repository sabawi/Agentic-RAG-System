#!/usr/bin/env python3
"""
Check which imports are failing that cause TOOLS_AVAILABLE = False
"""

def check_tool_imports():
    """Check each import individually"""
    print("🔍 Checking Tool Import Dependencies")
    print("=" * 50)
    
    imports_to_check = [
        ('ollama', 'Ollama client for LLM'),
        ('bs4', 'BeautifulSoup for HTML parsing'),
        ('wikipediaapi', 'Wikipedia API client'),
        ('gnews', 'Google News client'),
        ('yfinance', 'Yahoo Finance client'),
        ('duckduckgo_search', 'DuckDuckGo search'),
        ('webcrawler', 'Custom Selenium webcrawler'),
        ('text_chunker', 'Custom text chunking'),
        ('PyPDF2', 'PDF text extraction'),
        ('magic', 'File type detection')
    ]
    
    available = []
    missing = []
    
    for module_name, description in imports_to_check:
        try:
            if module_name == 'bs4':
                from bs4 import BeautifulSoup
            elif module_name == 'duckduckgo_search':
                from duckduckgo_search import DDGS
            elif module_name == 'webcrawler':
                from webcrawler import SeleniumCrawler
            elif module_name == 'text_chunker':
                from text_chunker import TextChunker
            else:
                __import__(module_name)
            
            available.append((module_name, description))
            print(f"✅ {module_name} - {description}")
            
        except ImportError as e:
            missing.append((module_name, description, str(e)))
            print(f"❌ {module_name} - {description}")
            print(f"   Error: {e}")
    
    print()
    print("📊 Import Summary:")
    print(f"   Available: {len(available)}/{len(imports_to_check)}")
    print(f"   Missing: {len(missing)}")
    
    if missing:
        print()
        print("🚨 Missing Dependencies (causing TOOLS_AVAILABLE = False):")
        for module, desc, error in missing:
            print(f"   - {module}: {desc}")
            print(f"     Error: {error}")
        
        print()
        print("💡 Solutions:")
        print("1. Activate virtual environment: source venv_fastapi/bin/activate")
        print("2. Install missing packages:")
        for module, _, _ in missing:
            if module == 'duckduckgo_search':
                print(f"   pip install duckduckgo-search")
            elif module == 'webcrawler':
                print(f"   # webcrawler.py should be in same directory")
            elif module == 'text_chunker':
                print(f"   # text_chunker.py should be in same directory")
            else:
                print(f"   pip install {module}")
    else:
        print()
        print("🎉 All dependencies available!")
        print("💡 If TOOLS_AVAILABLE is still False, check server startup logs")

if __name__ == "__main__":
    check_tool_imports()