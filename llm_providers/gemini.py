"""
LLM Provider for Google Gemini models using the google-genai library
"""

import logging
import json
import google.generativeai as genai
from .base import LLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """
    LLM Provider for Google Gemini models.
    """

    def __init__(self, config: dict):
        """
        Initialize the GeminiProvider.

        Args:
            config: Configuration dictionary for the provider.
                    Requires 'api_key' and 'model'.

        Raises:
            ValueError: If required configuration is missing
        """
        super().__init__(config)

        # FAIL-FAST: No hardcoded fallback allowed per PROJECT_CONFIGURATION_DIRECTIVE.md
        if 'model' not in self.config:
            raise ValueError(
                "Gemini model must be configured in llm_config.yaml. "
                "Add 'model: gemini-flash-latest' to the gemini provider config section. "
                "No hardcoded fallbacks are allowed per project policy."
            )

        self.model_name = self.config['model']

        if not self.config.get("api_key"):
            raise ValueError(
                "API key for Gemini provider is required. "
                "Set GEMINI_API_KEY in your .env file and reference it in llm_config.yaml."
            )

        # The google-genai library uses a module-level configuration
        # for the API key.
        try:
            genai.configure(api_key=self.config["api_key"])
            logger.info("Gemini provider configured successfully.")
        except Exception as e:
            logger.error(f"Failed to configure Google Gemini client: {e}")
            raise

        self.model = genai.GenerativeModel(self.model_name)

    def _translate_messages_to_gemini(self, messages: list) -> list:
        """
        Translate a list of OpenAI-formatted messages to Gemini format.
        """
        gemini_messages = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")

            # Gemini uses 'model' for the assistant's role
            if role == "assistant":
                role = "model"

            # Skip system messages for now, as Gemini handles them differently.
            # A more robust implementation might merge the system prompt
            # into the first user message.
            if role == "system":
                logger.debug("Skipping system message for Gemini translation.")
                continue

            gemini_messages.append({
                "role": role,
                "parts": [{"text": content}]
            })
        return gemini_messages

    async def generate_stream(self, prompt: str, model: str, **kwargs):
        """
        Generate a streaming response from the Gemini model.

        Args:
            prompt: Input prompt for the model
            model: Model name (uses configured model if not specified)
            **kwargs: Additional keyword arguments (system_prompt, etc.)

        Yields:
            str: Plain text response chunks (framework handles JSON wrapping)
        """
        try:
            # Build messages array from prompt and system_prompt
            messages = []

            # Add system prompt if provided
            system_prompt = kwargs.get('system_prompt')
            if system_prompt:
                messages.append({
                    "role": "user",
                    "parts": [{"text": f"System: {system_prompt}\n\nUser: {prompt}"}]
                })
                logger.info(f"📋 Gemini: System prompt included ({len(system_prompt)} chars)")
            else:
                messages.append({
                    "role": "user",
                    "parts": [{"text": prompt}]
                })

            logger.info(f"🤖 Gemini streaming request: model={self.model_name}, prompt_len={len(prompt)}")

            # Generate content with streaming
            stream = self.model.generate_content(messages, stream=True)

            for chunk in stream:
                if chunk.text:
                    # Yield plain text content (framework handles JSON wrapping)
                    yield chunk.text

        except Exception as e:
            logger.error(f"❌ Error streaming from Gemini: {e}")
            raise Exception(f"Gemini API error: {str(e)}")

    async def generate(self, messages: list, **kwargs):
        """
        Generate a non-streaming response from the Gemini model.
        (Not typically used in this application, but implemented for completeness)
        """
        try:
            gemini_messages = self._translate_messages_to_gemini(messages)
            response = self.model.generate_content(gemini_messages)
            return response.text
        except Exception as e:
            logger.error(f"Error generating from Gemini: {e}")
            return f"Gemini API error: {str(e)}"

    async def generate_tools(self, prompt: str, model: str, tools: list, **kwargs):
        """
        Generate tool calls from the Gemini model.

        Args:
            prompt: Input prompt
            model: Model name (not used, uses configured model)
            tools: List of tool definitions
            **kwargs: Additional parameters

        Raises:
            NotImplementedError: Tool calling not yet implemented for Gemini
        """
        logger.warning("GeminiProvider.generate_tools is not yet implemented.")
        raise NotImplementedError(
            "Tool calling is not yet implemented for the Gemini provider. "
            "Please use OpenAI or Ollama for tool calling functionality."
        )

    async def health_check(self) -> bool:
        """
        Check if Gemini API is accessible.

        Returns:
            bool: True if Gemini API is accessible, False otherwise
        """
        try:
            # Try to list models to verify API access
            # The google-genai library doesn't have a dedicated health endpoint
            # so we'll try to use the model to check connectivity
            test_prompt = "test"
            response = self.model.generate_content([{"role": "user", "parts": [{"text": test_prompt}]}])
            return True
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False

    def get_available_models(self) -> list:
        """
        Get list of available Gemini models.

        Returns:
            List[str]: List of available Gemini model names
        """
        # Return common Gemini models
        # In production, you could query the API for actual available models
        models = [
            "gemini-flash-latest",
            "gemini-pro-latest",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
        ]

        # Add configured model if not in list
        configured_model = self.config.get('model')
        if configured_model and configured_model not in models:
            models.insert(0, configured_model)

        return models

    def get_provider_info(self) -> dict:
        """
        Get Gemini provider information and capabilities.

        Returns:
            Dict: Provider metadata including name, type, capabilities
        """
        return {
            'name': 'Google Gemini',
            'type': 'gemini',
            'configured_model': self.model_name,
            'supports_streaming': True,
            'supports_function_calling': False,  # Not yet implemented
            'supports_vision': True,  # Gemini supports vision
            'timeout': self.get_timeout(),
            'max_tokens': self.get_max_tokens(),
            'temperature': self.get_temperature(),
            'api_key_configured': bool(self.config.get('api_key'))
        }
