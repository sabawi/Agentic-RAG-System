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
        img = None
        
        imgPrompt = str(objs.get('prompt', ''))
        img = objs.get('image', None)
        
        if img == None or img == "None":
            return {
                "success": False,
                "error": "No image provided"
            }
        
        # Debug: Log image data format (commented out in production)
        # print(f"🖼️ DEBUG: Original image data type: {type(img)}", flush=True)
        # print(f"🖼️ DEBUG: Original image data preview: {str(img)[:100]}...", flush=True)
        
        # Handle different image data formats
        processed_img = self._process_image_data(img)
        
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
        
        # Skip messages structure and use direct ollama.generate call with timeout protection

        try:
            if not ollama:
                return {
                    "success": False,
                    "error": "Ollama not available - please install ollama package"
                }

            # print(f"\n\nCalling Model ==>{image_processing_model}",flush=True)
            # Use generate method for image processing with timeout
            logger.info(f"🖼️ Starting generation with {image_processing_model} (think=False, no streaming)...")
            
            # Add timeout protection to prevent hanging
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Vision model processing timeout")
            
            # Set timeout for vision model processing (configurable, default 30 minutes)
            timeout_seconds = self.vision_config.get('timeout', 1800)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                response = ollama.generate(
                    model=image_processing_model,
                    prompt=imgPrompt,
                    images=[processed_img],  # Use images parameter in generate
                    stream=False,  # Turn off streaming so results return to primary LLM
                    options={'think': False}  # Disable thinking phase for faster processing
                )
            finally:
                # Always clear the alarm
                signal.alarm(0)
            
            # Get complete response
            res = response.get('response', '')
            logger.info(f"🖼️ Generation complete, total response: {len(res)} chars")
            
            res = f"\n\nHere is the image recognition and analysis report you requested as of [Current Date and Time: {todayStr}], use it to compose your response to the user\'s prompt:  {res}" 
            
            
            return {
                "success": True,
                "description": res,
                "model": image_processing_model,
                "timestamp": todayStr
            }
            
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
            # Handle string data (could be base64, path, or URL)
            if isinstance(img_data, str):
                # If it's a file path
                if os.path.isfile(img_data):
                    return img_data  # Return single item, not list for Ollama
                
                # If it's base64 data with data URL prefix, extract base64 string
                if img_data.startswith('data:image/'):
                    # Extract base64 data after the comma
                    base64_data = img_data.split(',', 1)[1] if ',' in img_data else img_data
                    try:
                        # Validate base64 but return the string (ollama needs base64 string, not bytes)
                        base64.b64decode(base64_data, validate=True)
                        return base64_data  # Return base64 string, not bytes
                    except Exception as e:
                        logger.warning(f"🖼️ Invalid base64 data in data URL: {e}")
                        return None
                
                # If it's raw base64 data (check if it looks like base64)
                if len(img_data) > 50 and not img_data.startswith('http'):  # Assume it's base64 if long enough
                    # Check if it's valid base64
                    try:
                        # Try to decode - if successful, it's valid base64
                        base64.b64decode(img_data, validate=True)
                        # Successfully validated base64 - return the string (not bytes)
                        return img_data  # Return base64 string for ollama
                    except Exception as e:
                        logger.warning(f"🖼️ Invalid base64 data: {e}")
                        return None
                
                # If it's a URL
                if img_data.startswith(('http://', 'https://')):
                    return img_data  # Return single item, not list
            
            # Handle list of images - return first one for now (Ollama chat typically handles single image)
            elif isinstance(img_data, list):
                if img_data:
                    return self._process_image_data(img_data[0])
                else:
                    return None
            
            # Return as-is if already in expected format
            return img_data
            
        except Exception as e:
            logger.error(f"🖼️ Error processing image data: {e}")
            # Return original data and let Ollama handle it
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
                vision_config = config.get('vision', {}).get('config', {})
                logger.info(f"🖼️ Loaded vision config: model={vision_config.get('model', 'qwen2.5vl:3b')}, timeout={vision_config.get('timeout', 1800)}s")
                return vision_config
        except Exception as e:
            logger.warning(f"🖼️ Failed to load vision config from file: {e}")
            # Fallback to default configuration
            return {
                'model': 'qwen2.5vl:3b',
                'timeout': 1800,
                'base_url': 'http://127.0.0.1:11434',
                'fallback_model': 'bakllava:latest'
            }