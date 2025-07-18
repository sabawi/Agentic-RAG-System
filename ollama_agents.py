from typing import Optional, Type, Dict, Any, Union, List
from datetime import datetime
from pydantic import BaseModel, Field
from langchain.agents import AgentType, Tool
from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.memory.chat_message_histories import ChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import BaseChatMemory

from langchain.chat_models import ChatOpenAI  # Example LLM
from duckduckgo_search import DDGS
from webcrawler import SeleniumCrawler

# Utility Classes and Settings
class GetTextFromURLInput(BaseModel):
    url: str = Field(description="The URL to extract text from")

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query string")

# Global Settings
class SearchSettings:
    BASIC = {
        "MAX_CRAWLING_COUNT": 1,
        "MAX_SEARCH_ENGINE_RESULTS": 5,
        "TIMEOUT_URL_RESPONSE": 30,
        "TIMEOUT_URL_CONNECT": 2
    }

    DEEP = {
        "MAX_CRAWLING_COUNT": 3,
        "MAX_SEARCH_ENGINE_RESULTS": 10,
        "TIMEOUT_URL_RESPONSE": 50,
        "TIMEOUT_URL_CONNECT": 2
    }

default_search_setting = SearchSettings.BASIC

def set_default_search(key: str):
    global default_search_setting
    default_search_setting = SearchSettings.BASIC if key == 'basic' else SearchSettings.DEEP

# Utility Functions
def get_text_from_url(url: str) -> str:
    max_url_count = default_search_setting["MAX_CRAWLING_COUNT"]
    try:
        crawler = SeleniumCrawler(
            url, max_depth=2, max_url_count=max_url_count - 1,
            timeout_response=default_search_setting["TIMEOUT_URL_RESPONSE"]
        )
        crawler.setCheckRobot(False)
        crawler.crawl(url)
        crawler.close()

        result_text = ""
        for result in crawler.results:
            result_text += f"Title: {result['title']}, URL: {result['url']}\n"
            result_text += f"Content: {result['content']}\n{'-' * 80}\n"
        return result_text
    except Exception as e:
        return f"Error fetching text from URL: {str(e)}"

def perform_ducducgo_search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]

        result_text = ""
        for i, result in enumerate(results[:3], 1):
            result_text += f"Result {i}: {result.get('title', 'No Title')}\n"
            result_text += f"URL: {result.get('href', 'No URL')}\n"
            result_text += f"Snippet: {result.get('snippet', 'No Snippet')}\n{'-' * 80}\n"
        return result_text
    except Exception as e:
        return f"Error performing search: {str(e)}"

# Tools
class GetTextFromURL(BaseTool):
    name: str = "get_text_from_url"
    description: str = "Extracts text from a given URL."
    args_schema: Type[BaseModel] = GetTextFromURLInput

    def _run(self, url: str) -> str:
        return get_text_from_url(url)

class WebSearch(BaseTool):
    name: str = "websearch"
    description: str = "Performs a web search using DuckDuckGo."
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        return perform_ducducgo_search(query)

class AgentLibrary:
    def __init__(self):
        self.memory = BaseChatMemory(
            chat_message_history=ChatMessageHistory(),
            memory_key="chat_history"
        )

        # Example LLM: Replace `ChatOpenAI` with your actual language model
        self.llm: BaseLanguageModel = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

        self.tools = [GetTextFromURL(), WebSearch()]
        self.callback_manager = CallbackManager(
            handlers=[
                StreamingStdOutCallbackHandler(),  # Stream outputs to stdout
            ]
        )

        # Initialize the agent using `initialize_agent`
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            callback_manager=self.callback_manager,
            verbose=True
        )
        
if __name__ == "__main__":
    library = AgentLibrary()
    query = input("Enter your query: ")
    print("Processing query...")
    print(library.safe_run(query))
