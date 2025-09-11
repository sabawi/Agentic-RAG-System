import re
from langchain.llms import Ollama
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain.schema import AgentAction, AgentFinish

from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
import requests
from datetime import date, datetime
from webcrawler import SeleniumCrawler
import json

# from typing import Optional, Type, Dict, Any, Union
from typing import Optional, Type, Dict, Any, Union, List, Tuple
from pydantic import BaseModel, Field
from langchain.callbacks.base import BaseCallbackHandler
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
MAX_CRAWLING_COUNT = 1
MAX_SEARCH_ENGINE_RESULTS = 3
TIMEOUT_URL_RESPONSE = 15 # in seconds
TIMEOUT_URL_CONNECT = 2 # in seconds
###################
# Utility Functions
# #################


def get_text_from_url(url : str):
    
    # Crawl on this number of pages
    max_url_count = MAX_CRAWLING_COUNT
    
    crawler = SeleniumCrawler(url, max_depth=1,max_url_count=max_url_count-1,timeout_response=TIMEOUT_URL_RESPONSE)
    # Don't check robot.txt file on the server
    crawler.setCheckRobot(False)
    
    crawler.crawl(url)
    crawler.close()

    res = ''
    # Print results
    for result in crawler.results:
        res += f"Title: {result['title']}, URL: {result['url']}\n"
        res += f"Content: {result['content']}\n"
        res += "-" * 80
        res += "\n"
        
    return res

def ducducgo(query, max_results):
    # Import the DuckDuckGo search library
    from duckduckgo_search import DDGS

    """
    Perform a search on DuckDuckGo and gather raw results for debugging purposes.
    
    Parameters:
    - query: The search query to send to DuckDuckGo.
    - max_results: The maximum number of search results to retrieve.
    
    Returns:
    - A formatted string containing details of up to the first 3 search results.
    """

    try:
        # Initialize a DuckDuckGo search session
        with DDGS() as ddgs:
            # Perform a search and store results in a list comprehension
            results = [r for r in ddgs.text(query, max_results=max_results)]
            
            urllink = None  # Initialize variable to hold a URL link
            res = ''        # String to accumulate formatted results

            # Iterate over the first three results
            for i, result in enumerate(results[:3], 1):
                # Add a header for each result (Result 1, Result 2, etc.)
                res += f"\nResult {i}:"
                
                # Loop through each key-value pair in the result dictionary
                for key, value in result.items():
                    # Append key and value to result string
                    res += f"{key}: {value}\n"
                    # Check if the current key is 'href' and assign its value to urllink if so
                    if key == 'href':
                        urllink = value

                # Attempt to retrieve 'link' or 'url' attributes directly if they exist
                if hasattr(result, 'link'):
                    res += f"Has 'link' attribute: {result.link}\n"
                    urllink = result.link
                if hasattr(result, 'url'):
                    res += f"Has 'url' attribute: {result.url}\n"
                    urllink = result.url

                # If a valid URL link was found, attempt to fetch content from the link
                if urllink:
                    content = get_text_from_url(urllink)  # Assume this function extracts content from URL
                    # Append content if it’s non-empty
                    if len(content) > 0: 
                        res += f"content: {content}\n"

            # Return the formatted result string containing details of each result
            return res
    except Exception as e:
        # Handle exceptions, print error details, and return an empty list if an error occurs
        print(f"DuckDuckGo Error: {e}", flush=True)
        return []

# #######################################################################################


class ToolInput(BaseModel):
    """Generic input class that can be extended for each specific tool."""
    pass

class GetTextFromURLInput(ToolInput):
    url: str = Field(...,description="The website URL address to read text and data from")
        
class WeatherInput(ToolInput):
    city: str = Field(..., description="The city to get weather for")

class NewsInput(ToolInput):
    topic: str = Field(..., description="The topic to get news about")

class BaseAPITool(BaseTool):
    def make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.get(url, params=params, timeout=(TIMEOUT_URL_CONNECT, TIMEOUT_URL_RESPONSE))
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Error {response.status_code}: {response.json().get('message', 'Unknown error')}"}
        except Exception as e:
            return {"error": f"Error accessing API: {str(e)}"}

class GetTextFromURL(BaseAPITool):
    name = "get_text_from_url"
    description = "extract text from URL text and data"
    args_schema: Type[BaseModel] = GetTextFromURLInput
    
    def _get_text_from_url(self, url : str)-> str:
        
        # Crawl on this number of pages
        max_url_count = 1
        try:
            crawler = SeleniumCrawler(url, max_depth=1,max_url_count=max_url_count-1,timeout_response=TIMEOUT_URL_RESPONSE)
            # Don't check robot.txt file on the server
            crawler.setCheckRobot(False)
            
            crawler.crawl(url)
            crawler.close()

            res = ''
            # Print results
            for result in crawler.results:
                res += f"Title: {result['title']}, URL: {result['url']}\n"
                res += f"Content: {result['content']}\n"
                res += "-" * 80
                res += "\n"
                
            return res
        except Exception as e:
            return {"error": f"Error accessing API: {str(e)}"}
        
    def _run(self, url: str) -> str:
        return self._get_text_from_url(url)

class QueryDetails(BaseModel):
    title: str = Field(default="")
    description: str = Field(default="")
    type: str = Field(default="string")

class WebSearchInput(BaseModel):
    query: Union[str, Dict, QueryDetails] = Field(..., description="The search query string or object")

class WebSearch(BaseTool):
    name = "websearch"
    description = "Queries a web search engine for current information related to the prompt."
    args_schema: Type[BaseModel] = WebSearchInput

    print(f"This is in websearch() ...",flush=True)

    def _parse_query(self, query_input: Union[str, Dict, QueryDetails]) -> str:
        """Enhanced query parsing with better error handling"""
        
        print(f"***************** In _parse_query ***********************",flush=True)
        try:
            if isinstance(query_input, str):
                return query_input
            elif isinstance(query_input, dict):
                # Handle the specific structure we're seeing in the action_input
                if 'query' in query_input:
                    query_data = query_input['query']
                    if isinstance(query_data, dict):
                        title = query_data.get('title', '')
                        description = query_data.get('description', '')
                        return f"{title} {description}".strip()
                    return str(query_data)
                return str(query_input)
            elif isinstance(query_input, QueryDetails):
                return f"{query_input.title} {query_input.description}".strip()
            return str(query_input)
        except Exception as e:
            print(f"Query parsing error: {str(e)}")
            raise

    # def _parse_query(self, query_input: Union[str, Dict, QueryDetails]) -> str:
    #     """Parse different query input formats into a search string."""
    #     if isinstance(query_input, str):
    #         return query_input
    #     elif isinstance(query_input, dict):
    #         if 'query' in query_input:
    #             nested_query = query_input['query']
    #             if isinstance(nested_query, dict):
    #                 # Handle nested dictionary structure
    #                 return f"{nested_query.get('title', '')} {nested_query.get('description', '')}".strip()
    #             return str(nested_query)
    #         return f"{query_input.get('title', '')} {query_input.get('description', '')}".strip()
    #     elif isinstance(query_input, QueryDetails):
    #         return f"{query_input.title} {query_input.description}".strip()
    #     return str(query_input)

    # def _run(self, query: Union[str, Dict, QueryDetails]) -> str:
    #     """Main entry point for the tool."""
    #     try:
    #         print(f"WebSearch _run received query: {query}", flush=True)  # Debug logging
    #         search_query = self._parse_query(query)
    #         if not search_query:
    #             return "Error: No valid query provided for web search."
    #         return self._websearch(search_query)
    #     except Exception as e:
    #         print(f"WebSearch _run error: {str(e)}", flush=True)
    #         return f"Error processing web search request: {str(e)}"


    def _run(self, query: Union[str, Dict, QueryDetails]) -> str:
        """Enhanced run method with forced execution"""
        print(f"\nWebSearch._run called with query: {query}")
        try:
            search_query = self._parse_query(query)
            if not search_query:
                return "Error: No valid query provided for web search."
                
            print(f"Executing search for: {search_query}")
            result = self._websearch(search_query)
            print(f"Search completed. Result length: {len(result)}")
            return result
            
        except Exception as e:
            print(f"WebSearch error: {str(e)}")
            raise  # Re-raise the exception to ensure proper error handling



    def _websearch(self, query: str) -> str:
        today = datetime.now().strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
        max_results = 3
        try:
            web_results = ducducgo(query, MAX_SEARCH_ENGINE_RESULTS)
            return f"As of {today}, here are the results:\n" + web_results
        except Exception as e:
            print(f"WebSearch Error: {str(e)}", flush=True)
            return f"Error accessing API: {str(e)}"

    # def _websearch(self, query: str) -> str:
    #     today = datetime.now().strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
    #     max_results = 3
    #     try:
    #         web_results = ducducgo(query, MAX_SEARCH_ENGINE_RESULTS)
    #         return f"As of {today}, here are the results:\n" + web_results
    #     except Exception as e:
    #         return f"Error accessing API: {str(e)}"
    
class WeatherTool(BaseAPITool):
    name = "get_weather"
    description = "Get the current weather for a city"
    args_schema: Type[BaseModel] = WeatherInput

    def _get_weather(self, city: str) -> str:
        API_KEY = "your_weather_api_key"
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": API_KEY, "units": "metric"}
        data = self.make_request(url, params)
        if "error" in data:
            return data["error"]
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        return f"Temperature in {city} is {temp}°C with {description}"

    def _run(self, city: str) -> str:
        return self._get_weather(city)

class NewsTool(BaseAPITool):
    name = "get_news"
    description = "Get the latest news about a topic"
    args_schema: Type[BaseModel] = NewsInput

    def _get_news(self, topic: str) -> str:
        API_KEY = "your_news_api_key"
        url = "https://newsapi.org/v2/everything"
        params = {"q": topic, "apiKey": API_KEY, "pageSize": 3}
        data = self.make_request(url, params)
        if "error" in data:
            return data["error"]
        articles = data.get('articles', [])[:3]
        return "\n".join(f"- {article['title']}: {article['description']}" for article in articles)

    def _run(self, topic: str) -> str:
        return self._get_news(topic)



@dataclass
class AgentOutputParser:
    """Parser for agent outputs to ensure proper termination and response handling."""
    
    @staticmethod
    def is_final_answer(text: str) -> bool:
        """Check if the output indicates a final answer."""
        return bool(re.search(r'Final Answer:', text, re.IGNORECASE))
    
    @staticmethod
    def extract_final_answer(text: str) -> str:
        """Extract the final answer portion from the output."""
        if match := re.search(r'Final Answer:\s*(.+?)(?=\n\n|$)', text, re.DOTALL):
            return match.group(1).strip()
        return text.strip()

class EnhancedBufferCallbackHandler(BaseCallbackHandler):
    """Enhanced callback handler with better control flow and state management."""
    
    def __init__(self):
        self.action_history: List[AgentAction] = []
        self.current_action: Optional[AgentAction] = None
        self.final_output: str = ""
        self.thought_process: List[str] = []
        self.errors: List[str] = []
        self.is_finished: bool = False
        self.max_iterations: int = 10  # Increased max iterations for debugging
        self.current_iteration: int = 0
        self.buffer = []
        self.stop_condition_met = False
        self.all_output = []
        # Define the list of phrases that indicate the stop condition
        self.stop_phrases = [
            "Thought: I've reached a conclusion.",
            "Thought: I've completed my response.",
            "Thought: I'm satisfied.",
            "Thought: I'm done.",
            "Thought: I'm finished."
        ]
        
    # def on_tool_start(
    #     self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    # ) -> None:
    #     """Handle tool start with iteration tracking."""
    #     self.current_iteration += 1
    #     if self.current_iteration > self.max_iterations:
    #         self.is_finished = True
    #         return
            
    #     self.current_action = AgentAction(
    #         tool=serialized.get("name", "unknown_tool"),
    #         input=input_str,
    #         timestamp=datetime.now(),
    #         status="started"
    #     )
    #     self.action_history.append(self.current_action)
    
    
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Enhanced tool start handling with logging"""
        print(f"\nTool Execution Starting: {serialized.get('name', 'unknown_tool')}")
        print(f"Input: {input_str}")
        
        self.current_iteration += 1
        if self.current_iteration > self.max_iterations:
            self.is_finished = True
            return
            
        self.current_action = AgentAction(
            tool=serialized.get("name", "unknown_tool"),
            input=input_str,
            timestamp=datetime.now(),
            status="started"
        )
        self.action_history.append(self.current_action)

    
    def on_tool_finish(
        self, serialized: Dict[str, Any], output_str: str, **kwargs: Any
    ) -> None:
        """Handle tool finish and update action status."""
        if self.current_action:
            self.current_action.output = output_str
            self.current_action.status = "completed"
    
    def on_llm_new_token(self, token: str, **kwargs):
        # Append each token to the buffer
        self.buffer.append(token)
        # Check if the stop condition is met in the accumulated buffer
        current_output = ''.join(self.buffer)        
        # print(f"\n******************Buffer: {current_output}\n",flush=True)

        self.all_output = ''.join(self.buffer)
        # if any(phrase in current_output for phrase in self.stop_phrases):
        #     self.stop_condition_met = True
        #     print(f"***************** WE SHOULD END NOW *****************",flush=True)




    def on_llm_end(self, response, **kwargs):
        # After LLM completes, clear the buffer if stop condition is met
        if self.stop_condition_met:
            print("Breaking condition met, stopping further actions.")
            self.buffer = []
            self.stop_condition_met = False
        else:
            # No stopping condition met; proceed normally
            self.buffer = []
                
    # def on_tool_error(
    #     self, serialized: Dict[str, Any], error_msg: str, **kwargs: Any
    # ) -> None:
    #     """Handle tool errors and record them in the action history."""
    #     if self.current_action:
    #         self.current_action.status = "error"
    #         self.current_action.output = error_msg
    #         self.errors.append(error_msg)
    
    
    def on_tool_error(
        self, serialized: Dict[str, Any], error_msg: str, **kwargs: Any
    ) -> None:
        """Enhanced error handling with detailed logging"""
        print(f"\nTool Execution Error: {serialized.get('name', 'unknown_tool')}")
        print(f"Error: {error_msg}")
        
        if self.current_action:
            self.current_action.status = "error"
            self.current_action.output = error_msg
            self.errors.append(f"Tool {self.current_action.tool}: {error_msg}")   
        
    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Enhanced finish handling with proper termination."""
        self.is_finished = True
        self.final_output = AgentOutputParser.extract_final_answer(finish.return_values.get("output", ""))
        self.thought_process.append("Agent finished with final answer")
                
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all captured information."""
        return {
            "actions": [
                {
                    "tool": action.tool,
                    "input": action.input,
                    "output": getattr(action, 'output', None),
                    "full_output": self.all_output,
                    "status": getattr(action, 'status', 'unknown'),
                    "timestamp": action.timestamp.isoformat()
                }
                for action in self.action_history
            ],
            "thought_process": self.thought_process,
            "final_output": self.final_output,
            "errors": self.errors,
            "iterations": self.current_iteration
        }
    
    def clear(self) -> None:
        """Clear all stored information."""
        self.action_history.clear()
        self.thought_process.clear()
        self.errors.clear()
        self.final_output = ""
        self.current_action = None
        self.is_finished = False
        self.current_iteration = 0

class AgentLibrary:
    def __init__(self):
        # Initialize tools (assumed to be defined elsewhere)
        self.tools = {
            "websearch": WebSearch(),
            "get_text_from_url": GetTextFromURL(),
            # "weather": WeatherTool(),
            # "news": NewsTool(),
        }
        
        # Create tools list with explicit name checking
        tool_list = []
        for name, tool in self.tools.items():
            if tool.name != name:
                print(f"Warning: Tool name mismatch. Expected {name}, got {tool.name}")
                tool.name = name  # Ensure tool name matches key
            tool_list.append(tool)

        
        self.buffer_handler = EnhancedBufferCallbackHandler()
        self.callback_manager = CallbackManager(
            [
                StreamingStdOutCallbackHandler(),
                self.buffer_handler
                ]
            )
        
        self.llm = Ollama(
            model="llama3-groq-tool-use:latest",
            callback_manager=self.callback_manager,
            temperature=0.7,
            num_ctx=8000,
            top_k=15,
            top_p=0.7,
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True,
            output_key="output"
        )
        

        
        # self.agent = initialize_agent(
        #     tools=list(self.tools.values()),
        #     llm=self.llm,
        #     agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        #     verbose=True,
        #     memory=self.memory,
        #     handle_parsing_errors=True,
        #     max_iterations=10,
        #     early_stopping_method="generate",
        #     return_intermediate_steps=True
        # )

        # Create a custom agent class that forces tool execution
        self.agent = initialize_agent(
            tools=list(self.tools.values()),
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True,
            max_iterations=10,
            early_stopping_method="generate",
            return_intermediate_steps=True,
            agent_kwargs={
                "force_tool_use": True  # Force the agent to actually execute tools
            }
        )
        
    def safe_run(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Enhanced safe run with forced tool execution"""
        try:
            print("\nStarting agent execution...")
            print(f"Query: {query}")
            print("Available tools:", [tool.name for tool in self.agent.tools])
            
            self.buffer_handler.clear()
            
            # Custom handling of agent execution
            def _handle_tool_error(error: Exception, tool_name: str) -> str:
                print(f"Error executing {tool_name}: {str(error)}")
                return f"Error: {str(error)}"

            # Execute the agent with custom tool handling
            result = self.agent({"input": query})
            
            # Debug output
            if "intermediate_steps" in result:
                print("\nIntermediate steps:")
                for step in result["intermediate_steps"]:
                    action = step[0]
                    print(f"\nTool: {action.tool}")
                    print(f"Input: {action.tool_input}")
                    if hasattr(action, 'log'):
                        print(f"Log: {action.log}")
                    print(f"Output: {step[1]}")
            
            final_answer = AgentOutputParser.extract_final_answer(result.get("output", ""))
            buffer_summary = self.buffer_handler.get_summary()
            
            return final_answer, buffer_summary
            
        except Exception as e:
            print(f"\nError in agent execution: {str(e)}")
            return f"Error processing query: {str(e)}", self.buffer_handler.get_summary()

    # def safe_run(self, query: str) -> Tuple[str, Dict[str, Any]]:
    #     """Enhanced safe run with better error handling and output control."""
    #     try:
    #         self.buffer_handler.clear()
            
    #         # Run the agent with iteration control
    #         result = self.agent({"input": query})
            
    #         # Extract the final answer using the parser
    #         final_answer = AgentOutputParser.extract_final_answer(result.get("output", ""))
            
    #         # Get the buffer summary with complete execution details
    #         buffer_summary = self.buffer_handler.get_summary()
            
    #         return final_answer, buffer_summary
            
    #     except Exception as e:
    #         error_msg = f"Error processing query: {str(e)}"
    #         return error_msg, self.buffer_handler.get_summary()

    def analyze_run(self, buffer_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced analysis with more detailed metrics."""
        return {
            "total_actions": len(buffer_summary["actions"]),
            "successful_actions": sum(1 for action in buffer_summary["actions"] 
                                   if action["status"] == "completed"),
            "failed_actions": sum(1 for action in buffer_summary["actions"] 
                                if action["status"] == "error"),
            "tools_used": set(action["tool"] for action in buffer_summary["actions"]),
            "error_count": len(buffer_summary["errors"]),
            "has_final_output": bool(buffer_summary["final_output"]),
            "total_iterations": buffer_summary.get("iterations", 0),
            "execution_timeline": [
                {
                    "tool": action["tool"],
                    "timestamp": action["timestamp"],
                    "status": action["status"]
                }
                for action in buffer_summary["actions"]
            ]
        }

if __name__ == "__main__":
    library = AgentLibrary()
    
    while True:
        try:
            query = input("\nEnter your prompt (or 'quit' to exit): ").strip()
            if query.lower() == 'quit':
                break
                
            print("\nProcessing query...\n")
            
            
            # print("Testing websearch ...\n",flush=True)
            # websearch = WebSearch()
            # result = websearch._run("how big in Canada land?")
            # print(result)
            
            
            result, buffer_summary = library.safe_run(query)
            
            print(f"Final Answer: {result}\n")
            
            analysis = library.analyze_run(buffer_summary)
            print("\nExecution Summary:")
            print(f"Total iterations: {analysis['total_iterations']}")
            print(f"Actions taken: {analysis['total_actions']}")
            print(f"Tools used: {', '.join(analysis['tools_used'])}")
            print(f"Success rate: {analysis['successful_actions']}/{analysis['total_actions']}")
            
            if analysis['error_count'] > 0:
                print(f"\nErrors encountered: {analysis['error_count']}")
                for error in buffer_summary["errors"]:
                    print(f"- {error}")
                    
        except KeyboardInterrupt:
            print("\nExecution interrupted by user.")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")