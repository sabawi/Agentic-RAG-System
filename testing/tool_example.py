import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import jinja2

@dataclass
class ToolCall:
    function: Dict[str, str]

@dataclass
class Message:
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

@dataclass
class ConversationContext:
    system: Optional[str]
    tools: Optional[List[str]]
    messages: List[Message]

def format_prompt(context: ConversationContext) -> str:
    template_str = '''<|start_header_id|>system<|end_header_id|>
Cutting Knowledge Date: December 2023
{%- if system %}
{{ system }}
{%- endif %}
{%- if tools %}
When you receive a tool call response, use the output to format an answer to the original user question.
You are a helpful assistant with tool calling capabilities.
{%- endif %}<|eot_id|>

{%- for message in messages %}
{%- if message.role == "user" %}
<|start_header_id|>user<|end_header_id|>
{%- if tools and loop.last %}
Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt.
Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}. Do not use variables.

Available functions:
{% for tool in tools %}
{{ tool }}
{% endfor %}

{{ message.content }}
{%- else %}
{{ message.content }}
{%- endif %}<|eot_id|>
{%- endif %}

{%- if message.role == "assistant" %}
<|start_header_id|>assistant<|end_header_id|>
{%- if message.tool_calls %}
{%- for tool_call in message.tool_calls %}
{"name": "{{ tool_call.function.name }}", "parameters": {{ tool_call.function.arguments }}}
{%- endfor %}
{%- else %}
{{ message.content if message.content else "" }}
{%- endif %}<|eot_id|>
{%- endif %}

{%- if message.role == "tool" %}
<|start_header_id|>ipython<|end_header_id|>
{{ message.content if message.content else "" }}<|eot_id|>
{%- endif %}
{%- endfor %}'''

    template = jinja2.Template(template_str, undefined=jinja2.StrictUndefined)
    
    try:
        result = template.render(
            system=context.system,
            tools=context.tools,
            messages=context.messages
        )
        print(f"Result: {result} \n\n")
        return result
    except jinja2.exceptions.UndefinedError as e:
        print(f"Template rendering error: {e}")
        return ""

def main():
    # Define available tools
    tools = [
        """def get_weather(location: str, unit: str = "celsius") -> str:
            \"\"\"Get the current weather for a location
            Args:
                location: City name or coordinates
                unit: Temperature unit (celsius/fahrenheit)
            Returns:
                Current weather description
            \"\"\"""",
        """def set_reminder(time: str, message: str) -> str:
            \"\"\"Set a reminder for a specific time
            Args:
                time: Time in ISO format
                message: Reminder message
            Returns:
                Confirmation message
            \"\"\""""
    ]

    # Create a conversation context for the reminder scenario
    context = ConversationContext(
        system="You are a helpful weather and reminder assistant.",
        tools=tools,
        messages=[
            Message(
                role="user",
                content="Set the reminder to 9:00 AM to call Mark"
            ),
            Message(
                role="assistant",
                tool_calls=[
                    ToolCall(
                        function={
                            "name": "set_reminder",
                            "arguments": json.dumps({
                                "time": "09:00:00",
                                "message": "Call Mark"
                            })
                        }
                    )
                ]
            ),
            Message(
                role="tool",
                content="Reminder set: 'Call Mark' for 9:00 AM"
            )
        ]
    )

    # Generate the formatted prompt
    formatted_prompt = format_prompt(context)
    print("Generated Prompt:")
    print(formatted_prompt)

if __name__ == "__main__":
    main()