#!/usr/bin/env python3
"""
Test if the required tools and dependencies are available
"""

def test_tool_dependencies():
    """Test all the tool dependencies"""
    print("🔧 Testing Tool Dependencies")
    print("=" * 40)
    
    # Test basic imports
    dependencies = [
        ('ollama', 'Ollama client'),
        ('bs4', 'BeautifulSoup for web scraping'),
        ('wikipediaapi', 'Wikipedia API'),
        ('gnews', 'Google News'),
        ('yfinance', 'Yahoo Finance'),
        ('aiohttp', 'Async HTTP client'),
        ('aiomysql', 'Async MySQL client'),
        ('pandas', 'Data processing'),
        ('matplotlib', 'Plotting')
    ]
    
    available = []
    missing = []
    
    for module, description in dependencies:
        try:
            __import__(module)
            available.append((module, description))
            print(f"✅ {module} - {description}")
        except ImportError as e:
            missing.append((module, description, str(e)))
            print(f"❌ {module} - {description} - Error: {e}")
    
    print()
    print(f"📊 Summary: {len(available)}/{len(dependencies)} dependencies available")
    
    if missing:
        print("⚠️ Missing dependencies:")
        for module, desc, error in missing:
            print(f"   - {module}: {desc}")
    
    # Test the specific news tool
    print()
    print("🧪 Testing News Tool Specifically")
    print("-" * 30)
    
    try:
        from gnews import GNews
        google_news = GNews(language='en', country='US', max_results=3)
        
        print("✅ GNews imported successfully")
        
        # Test a simple query
        news = google_news.get_news('financial')
        print(f"✅ News query successful - got {len(news)} articles")
        
        if news:
            print("📰 Sample article:")
            first_article = news[0]
            print(f"   Title: {first_article.get('title', 'N/A')}")
            print(f"   Date: {first_article.get('published date', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ News tool test failed: {e}")
        return False

def test_async_tool_manager():
    """Test if AsyncToolManager can be imported and initialized"""
    print()
    print("🎯 Testing AsyncToolManager")
    print("-" * 30)
    
    try:
        import sys
        import os
        
        # Add the current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from fastapi_server_complete import AsyncToolManager
        
        tool_manager = AsyncToolManager()
        print(f"✅ AsyncToolManager created with {len(tool_manager.available_functions)} tools")
        print(f"📋 Available tools: {list(tool_manager.available_functions.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ AsyncToolManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    deps_ok = test_tool_dependencies()
    manager_ok = test_async_tool_manager()
    
    print()
    print("=" * 40)
    if deps_ok and manager_ok:
        print("🎉 All tool systems appear to be working!")
        print("💡 The issue might be in the server execution flow")
    else:
        print("❌ There are issues with the tool system")
        print("🔧 Fix the above issues first")