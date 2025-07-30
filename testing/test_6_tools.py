#!/usr/bin/env python3
"""
Test tool calling with the exact same 6 tools array as FastAPI server
"""

import requests
import json

def test_6_tools():
    """Test with exact same tools array as FastAPI"""
    
    print("🔧 Testing 6 Tools (Same as FastAPI Server)")
    print("=" * 50)
    
    # EXACT same tools array that FastAPI server generates
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_the_secret_tool",
                "description": "Must call this function to get the current date and time from the system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "secret_tool": {
                            "type": "string",
                            "description": "Get the current Date and Time from the system as needed"
                        }
                    },
                    "required": ["secret_tool"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_news_summaries",
                "description": "Returns time-sensitive News! Tag all news items with Date, Time, and Source in response! This function takes a keyword string as input as a possible filter for news headlines and returns today's news headlines.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "The input filter is a string type that helps narrow down the choices of headlines. Examples: \"National\", \"Middle East\", \"World\", \"Technology\""
                        }
                    },
                    "required": ["filter"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "This function takes a query string as input and searches the web for information using the query verbatim. It returns links and URLs if found with a brief description, or an error message if no information is available.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The input query is a string type that is sent to the web search engine."
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "lookup_website",
                "description": "This function takes a URL (href) web address for a website and makes an HTTP request to retrieve the text from the website for further processing to respond to the user's prompt.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL link to be used directly to request a website download."
                        }
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "wikipedia_query",
                "description": "Retrieves concise factual information from Wikipedia about a specific topic based on a user-provided query. This function processes the query to identify the main topic and searches Wikipedia using the topic as a reference.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "A natural language query, key phrase, or topic of interest. This input should focus on a single topic to ensure accurate results."
                        }
                    },
                    "required": ["question"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_stock_and_company_data",
                "description": "Calls a financial data provider to get latest stock and company data. Returns description, financial information, news, stock prices, analysts sentiments, and forward earnings estimates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The ticker symbol traded on the stock exchange. Examples: \"AAPL\", \"MSFT\", \"AMZN\", \"ORCL\""
                        }
                    },
                    "required": ["symbol"]
                }
            }
        }
    ]
    
    # Use the EXACT same system prompt as FastAPI server
    messages = [
        {
            "role": "system",
            "content": """BEFORE YOU MAKE FUNCTION CALLS, FOLLOW THIS GUIDELINE:
            Tool Call Generation Guidelines -->:
        DO NOT USE MORE THAN THREE (3) DIFFERENT FUNCTIONS. YOU CAN CALL THE SAME FUNCTION MULTIPLE TIMES WIth DIFFERENT PARAMETERS  :
        
        Execution Strategy:
        - Analyze the entire input comprehensively
        - Select only the tools needed and most relevant to the prompt in most logical sequence
        - Prioritize precision and relevance
        - Avoid redundant or unnecessary tool calls.
        - Ensure each function is called with relevant and required parameters
        - Use exact proper nouns or specific topics as parameters
        
        1. Initial Context Retrieval:
        - Always begin by calling get_the_secret_tool() to obtain the current date and time
        - This ensures all subsequent tool calls have accurate temporal context
        - Depending on the information needed, select a maximum of 2 tools out of the list and call them with more than once if needed with relevant parameters

        2. Stock and Financial Information:
        - For stock data, call get_stock_and_company_data() 
            * One distinct call per stock symbol
            * Use exact stock ticker as parameter
        - For additional market context, use get_news_summaries() 
            * Apply relevant keyword as parameter
            * Focus on financial keywords related to the stock/sector

        3. Current Events, Up-to-date Data, and Local Information
        - Use search_web() for:
            * Local events
            * Current business information
            * Addresses
            * Contact details
            * Real-time local context
        - For deeper and current news context, supplement with get_news_summaries()

        4. News and Current Affairs:
        - Use get_news_summaries() for:
            * Latest developments in major topics
            * Global/national events
            * Specific sectors (economy, politics, military)
        - When local news is needed, include location specifics 
            (city, state, country) in the parameter

        5. Travel and Lifestyle Information:
        - Employ search_web() for comprehensive queries about:
            * Flight details
            * Hotel availability
            * Vacation destinations
            * Rental information
            * Tourist attractions
        - Use full, detailed query strings
        
        6. Encyclopedia and Factual Information: 
        - Divide the question into partial questions. Use wikipedia_query() only if needed. Call wikipedia_query() once per question as parameter for the following cases:
            * Historical events
            * Academic facts
            * Biographical information
            * Geographical details
            * Definitional content
            * Example Prompt: "Compare the Roman Empire with the Persian Empire and describe their strength and weaknesses." 
                --> Respond with : tool_calls : wikipedia_query() with {'question'='roman empire'} then call wikipedia_query() again with {'question' : 'persian empire'} 
            
            
        7. Ambiguous or Undefined Requests:
        - If the input lacks clear actionable context or the need for external data, then
            * Do NOT generate unnecessary function calls
            * Return an empty list of function calls
            * Ask user for clarification
        
        8. CRITICAL: Do NOT use wikipedia_query() for:
            * Current news
            * Recent events
            * Breaking stories
        
        """
        },
        {
            "role": "user",
            "content": "Examine the intent of the user's prompt and apply the system directives to make the appropriate calls to the tools' functions. User Prompt: get news about middle east"
        }
    ]
    
    print(f"🔧 Testing with {len(tools)} tools (same as FastAPI)...")
    print("📝 Using exact same system prompt as FastAPI...")
    
    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={
                "model": "llama3.2:3b",
                "messages": messages,
                "options": {"temperature": 0},
                "tools": tools,
                "stream": False,
                "think": False
            },
            timeout=20  # Longer timeout to see if it completes
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ SUCCESS with 6 tools!")
            
            if 'message' in response_data and 'tool_calls' in response_data['message']:
                tool_calls = response_data['message']['tool_calls']
                print(f"🎉 Generated {len(tool_calls)} tool calls:")
                
                for i, tool_call in enumerate(tool_calls):
                    func_name = tool_call['function']['name']
                    func_args = tool_call['function']['arguments']
                    print(f"  {i+1}. {func_name}({func_args})")
            else:
                print("❌ No tool calls generated")
                
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception with 6 tools: {e}")
        print(f"Exception type: {type(e).__name__}")
        
        if "timeout" in str(e).lower():
            print("🔍 TIMEOUT CONFIRMED: The 6-tool array is causing Ollama to hang!")
            print("💡 Possible solutions:")
            print("   1. Reduce number of tools sent to Ollama")
            print("   2. Simplify tool descriptions")
            print("   3. Use different timeout values")
        
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_6_tools()