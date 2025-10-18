#!/usr/bin/env python3
"""
Image-to-Text Tool - Simplified Implementation
Converts images to text descriptions using Ollama's qwen2.5vl:3b model.
"""

import json
import logging
import os
import base64
import yaml
import signal
from datetime import datetime
from typing import Dict, Any

try:
    import ollama
except ImportError:
    ollama = None

try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool

logger = logging.getLogger(__name__)


class ImageToTextTool(BaseUserTool):
    """Tool for converting images to text descriptions using qwen2.5vl:3b model."""

    def __init__(self):
        super().__init__()
        self.system_prompt = self._load_system_prompt()
        self.vision_config = self._load_vision_config()

    @property
    def name(self) -> str:
        return "image_to_text"

    @property
    def description(self) -> str:
        return """Convert images to detailed text descriptions using qwen2.5vl:3b vision model.
        
        Takes a prompt and image data and returns a detailed analysis including:
        - Text detection and reading
        - Object and face recognition  
        - Color analysis
        - Chart/graph analysis with trends and data insights
        - Timestamp of analysis
        """

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Instructions or query for image analysis",
                    "default": "Describe this image in detail"
                },
                "image": {
                    "type": "string",
                    "description": "Base64 encoded image data (with or without data URL prefix)"
                }
            },
            "required": ["image"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute image-to-text conversion using simple Ollama approach."""
        try:
            logger.info("🖼️ Starting vision model processing with extended timeout (30 minutes)")
            return self.get_image_processing_results(kwargs)
        except Exception as e:
            logger.error(f"🖼️ Image processing failed: {e}")
            return {
                "success": False,
                "error": f"Image processing failed: {str(e)}"
            }

    def get_image_processing_results(self, objs):
        """
        Process and analyze an image using a specified image processing model.

        Args:
            objs (dict): Dictionary containing:
                - 'prompt' (str): Instructions or query for image analysis
                - 'image' (image blob): The image to be processed

        Returns:
            str: Detailed image analysis report including:
                - Text detection
                - Object recognition
                - Color analysis
                - Trend and data insights
                - Timestamp of analysis

        Notes:
            - Uses Ollama's qwen2.5vl:3b model for image processing
            - Prepends predefined instructions to user's prompt
            - Handles image recognition and text extraction
            - Returns error message if processing fails
        """

        image_processing_model = self.vision_config.get('model', 'qwen2.5vl:3b')
        # image_processing_model = "bakllava:latest"
        imgPrompt = ''
        
        imgPrompt = str(objs.get('prompt', ''))
        img_input = objs.get('image') or objs.get('images')

        # Debug logging for Open-WebUI integration
        logger.info(f"🖼️ img_input type: {type(img_input)}")
        if isinstance(img_input, str):
            logger.info(f"🖼️ img_input length: {len(img_input)} chars")
            logger.info(f"🖼️ img_input preview: {img_input[:100]}...")
        elif isinstance(img_input, list):
            logger.info(f"🖼️ img_input is list with {len(img_input)} items")
            if img_input and len(img_input) > 0:
                logger.info(f"🖼️ First item type: {type(img_input[0])}")
                if isinstance(img_input[0], str):
                    logger.info(f"🖼️ First item preview: {img_input[0][:100]}...")
        else:
            logger.info(f"🖼️ img_input value: {img_input}")

        if not img_input:
            return {
                "success": False,
                "error": "No image provided"
            }

        # Handle different image data formats
        processed_img = self._process_image_data(img_input)

        # Log processed result
        if isinstance(processed_img, str):
            logger.info(f"🖼️ processed_img length: {len(processed_img)} chars")
            logger.info(f"🖼️ processed_img preview: {processed_img[:100]}...")
        else:
            logger.info(f"🖼️ processed_img type: {type(processed_img)}, value: {processed_img}")
        
        # Use system prompt from file (fallback to simple if loading fails)
        try:
            system_prompt_text = self.system_prompt if len(self.system_prompt) < 500 else "Analyze this image thoroughly and describe what you see in detail. Extract any visible text accurately."
        except:
            system_prompt_text = "Analyze this image thoroughly and describe what you see in detail. Extract any visible text accurately."
        
        imgPrompt = f"{system_prompt_text}\n\nUSER PROMPT: {imgPrompt}"
        
        # print(f"Prompt Parameter : {imgPrompt}",flush=True)
        # print(f"Image Blob : {img}",flush=True)
        # print("\n\n",flush=True)
        
        today = datetime.now()
        todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
        
        # Handle the case where processed_img might be None
        if processed_img is None:
            return {
                "success": False,
                "error": "No valid image data after processing"
            }
        
        # Debug processed image format (commented out in production)
        # print(f"🖼️ DEBUG: Processed image type: {type(processed_img)}", flush=True)
        # print(f"🖼️ DEBUG: Processed image preview: {str(processed_img)[:100]}...", flush=True)
        
        # Use the appropriate vision provider based on configuration
        vision_type = self.vision_config.get('type', 'ollama')

        try:
            if vision_type == 'ollama':
                return self._process_with_ollama(image_processing_model, imgPrompt, processed_img, todayStr)
            else:
                return self._process_with_openai_compatible_api(image_processing_model, imgPrompt, processed_img, todayStr)
            
        except TimeoutError as e:
            logger.error(f"🖼️ Vision model timeout: {e}")
            return {
                "success": False,
                "error": f"Vision model processing timeout: {str(e)}. The model qwen2.5vl:3b may need to be reloaded or replaced."
            }
        except Exception as e:
            logger.error(f"🖼️ Image processing exception: {e}")
            # Try fallback to basic error response
            fallback_response = f"Image processing encountered an error: {str(e)}. The vision model may need attention."
            return {
                "success": False,
                "error": fallback_response
            }

    def _process_image_data(self, img_data):
        """Process different image data formats for Ollama."""
        try:
            # Handle list of images - could be from forced processing
            if isinstance(img_data, list):
                if not img_data:
                    return None
                # It could be a list of dicts or a list of strings
                first_item = img_data[0]
                if isinstance(first_item, dict) and 'data' in first_item:
                    # It's a list of dicts, get data from the first one
                    return self._process_image_data(first_item['data'])
                else:
                    # Assume it's a list of strings (paths, urls, or base64)
                    return self._process_image_data(first_item)

            # Handle string data (could be base64, path, or URL)
            if isinstance(img_data, str):
                # If it's a file path
                if os.path.isfile(img_data):
                    return img_data
                
                # If it's base64 data with data URL prefix, extract base64 string
                if img_data.startswith('data:image/'):
                    base64_data = img_data.split(',', 1)[1] if ',' in img_data else img_data
                    try:
                        base64.b64decode(base64_data, validate=True)
                        return base64_data
                    except Exception as e:
                        logger.warning(f"🖼️ Invalid base64 data in data URL: {e}")
                        return None
                
                # If it's a URL
                if img_data.startswith(('http://', 'https://')):
                    return img_data

                # If it's raw base64 data, try to validate and return
                try:
                    base64.b64decode(img_data, validate=True)
                    return img_data
                except Exception:
                    # If it's not valid base64, it might be a file path that doesn't exist yet.
                    # Let ollama handle it.
                    return img_data

            # Handle dict from forced processing if passed directly
            if isinstance(img_data, dict) and 'data' in img_data:
                return self._process_image_data(img_data['data'])

            # Return as-is and let ollama try to handle it
            return img_data
            
        except Exception as e:
            logger.error(f"🖼️ Error processing image data: {e}")
            return img_data

    def _load_system_prompt(self) -> str:
        """Load system prompt from config file."""
        try:
            # Get the directory of this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to get to the project root
            project_root = os.path.dirname(script_dir)
            prompt_file = os.path.join(project_root, 'config', 'image_to_text_system_prompt.txt')
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"🖼️ Failed to load system prompt from file: {e}")
            # Fallback to a basic prompt
            return "You are an expert image analyst. Analyze the image very carefully and provide a detailed description including any text, objects, colors, and data trends you observe. Be thorough and accurate in your analysis."

    def _load_vision_config(self) -> Dict[str, Any]:
        """Load vision model configuration from config file."""
        try:
            # Get the directory of this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to get to the project root
            project_root = os.path.dirname(script_dir)
            config_file = os.path.join(project_root, 'config', 'llm_config.yaml')

            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                vision_section = config.get('vision', {})
                vision_type = vision_section.get('type', 'ollama')
                vision_config = vision_section.get('config', {})

                # Add the type to the config
                vision_config['type'] = vision_type

                # Resolve environment variables in the config
                if 'api_key' in vision_config:
                    vision_config['api_key'] = os.path.expandvars(vision_config['api_key'])

                logger.info(f"🖼️ Loaded vision config: type={vision_type}, model={vision_config.get('model', 'qwen2.5vl:3b')}, timeout={vision_config.get('timeout', 1800)}s")
                return vision_config
        except Exception as e:
            logger.warning(f"🖼️ Failed to load vision config from file: {e}")
            # Fallback to default configuration
            return {
                'type': 'ollama',
                'model': 'qwen2.5vl:3b',
                'timeout': 1800,
                'base_url': 'http://127.0.0.1:11434',
                'fallback_model': 'bakllava:latest'
            }

    def _process_with_ollama(self, model: str, prompt: str, image_data: str, timestamp: str) -> Dict[str, Any]:
        """Process vision request using Ollama.

        Ollama's vision models use chat() API with images in messages.
        Images can be:
        - File paths (string)
        - URLs (string)
        - Base64 encoded strings (passed directly without decoding)
        """
        if not ollama:
            return {
                "success": False,
                "error": "Ollama not available - please install ollama package"
            }

        # Add timeout protection to prevent hanging
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Vision model processing timeout")

        # Set timeout for vision model processing (configurable, default 30 minutes)
        timeout_seconds = self.vision_config.get('timeout', 1800)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        try:
            logger.info(f"🖼️ Starting vision processing with {model} using chat API...")

            # Determine the image format
            if os.path.isfile(image_data):
                logger.info(f"🖼️ Using file path: {image_data}")
            elif image_data.startswith(('http://', 'https://')):
                logger.info(f"🖼️ Using URL: {image_data[:50]}...")
            else:
                logger.info(f"🖼️ Using base64 data: {len(image_data)} chars")

            # Use chat API for vision models with images in messages
            response = ollama.chat(
                model=model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_data]  # Pass image data directly in message
                }],
                stream=False  # Turn off streaming so results return to primary LLM
            )
        finally:
            # Always clear the alarm
            signal.alarm(0)

        # Get complete response from chat API
        res = response['message']['content']
        logger.info(f"🖼️ Vision processing complete, total response: {len(res)} chars")

        res = f"\n\nHere is the image recognition and analysis report you requested as of [Current Date and Time: {timestamp}], use it to compose your response to the user's prompt:  {res}"

        return {
            "success": True,
            "description": res,
            "model": model,
            "timestamp": timestamp
        }

    def _process_with_openai_compatible_api(self, model: str, prompt: str, image_data: str, timestamp: str) -> Dict[str, Any]:
        """Process vision request using an OpenAI-compatible API."""
        import requests
        import json

        base_url = self.vision_config.get('base_url')
        api_key = self.vision_config.get('api_key')
        headers = self.vision_config.get('headers', {})
        timeout_seconds = self.vision_config.get('timeout', 1800)

        if not base_url:
            return {
                "success": False,
                "error": "API base URL not found in configuration."
            }

        logger.info(f"🖼️ Starting OpenAI-compatible API generation with {model}...")

        # Prepare the request payload in OpenAI format
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.1
        }

        # Add authorization header if API key is present
        request_headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            request_headers["Authorization"] = f"Bearer {api_key}"
        
        request_headers.update(headers)

        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=request_headers,
                json=payload,
                timeout=timeout_seconds
            )

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    res = data["choices"][0]["message"]["content"]
                    logger.info(f"🖼️ OpenAI-compatible API generation complete, total response: {len(res)} chars")

                    res = f"\n\nHere is the image recognition and analysis report you requested as of [Current Date and Time: {timestamp}], use it to compose your response to the user's prompt:  {res}"

                    return {
                        "success": True,
                        "description": res,
                        "model": model,
                        "timestamp": timestamp
                    }
                else:
                    return {
                        "success": False,
                        "error": f"No response content from API: {response.text}"
                    }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"API request timeout after {timeout_seconds} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}"
            }