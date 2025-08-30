#!/usr/bin/env python3
"""
Debug keyword detection for financial news
"""

def test_keyword_detection():
    """Test the exact keyword detection logic from the server"""
    
    prompt = "look up the latest financial news as of today then summarize it"
    print(f"Testing prompt: '{prompt}'")
    print()
    
    prompt_lower = prompt.lower()
    print(f"Lowercased: '{prompt_lower}'")
    print()
    
    # Test news detection (from server code)
    news_keywords = ['news', 'latest', 'current events', 'headlines', 'breaking', 'financial news', 'summarize']
    print("Testing news keywords:")
    news_matches = []
    for word in news_keywords:
        if word in prompt_lower:
            news_matches.append(word)
            print(f"  ✅ Found: '{word}'")
    
    if not news_matches:
        print("  ❌ No news keywords found!")
    else:
        print(f"  📊 Total news matches: {len(news_matches)}")
    
    print()
    
    # Test financial detection (from server code) 
    financial_keywords = ['financial', 'finance', 'market', 'economy', 'business']
    print("Testing financial keywords:")
    financial_matches = []
    for word in financial_keywords:
        if word in prompt_lower:
            financial_matches.append(word) 
            print(f"  ✅ Found: '{word}'")
    
    if not financial_matches:
        print("  ❌ No financial keywords found!")
    else:
        print(f"  📊 Total financial matches: {len(financial_matches)}")
    
    print()
    
    # Final determination
    should_trigger_news = len(news_matches) > 0
    should_be_financial = len(financial_matches) > 0
    
    print("Expected behavior:")
    if should_trigger_news:
        print("  ✅ Should trigger news tool")
        if should_be_financial:
            print("  ✅ Should detect as financial news")
            print("  🎯 Expected topic: 'financial news'")
        else:
            print("  📰 Should detect as general news")
            print("  🎯 Expected topic: 'latest news'")
    else:
        print("  ❌ Should NOT trigger news tool")
    
    print()
    print("Server should log:")
    print("  - 'Processing tool calls with direct keyword analysis...'")
    print("  - 'Calling news tool for topic: financial news'")
    print("  - 'Tool: get_news_summaries'")

if __name__ == "__main__":
    test_keyword_detection()