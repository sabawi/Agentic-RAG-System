#!/usr/bin/env python3
"""
Comprehensive Test Suite for Image-to-Text Tool
Tests all input methods, processing modes, and integration scenarios.
"""

import asyncio
import base64
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO
from PIL import Image

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_tools.image_to_text import ImageToTextTool
from user_tools.image_to_text_tool import ImageToTextUserTool
from config.llm_constants import (
    DEFAULT_MAX_IMAGE_WIDTH, DEFAULT_MAX_IMAGE_HEIGHT,
    DEFAULT_MAX_IMAGES_PER_REQUEST, DEFAULT_BATCH_PROCESSING_LIMIT,
    PROCESSING_MODE_BATCH, PROCESSING_MODE_SEQUENTIAL
)


class TestImageToTextTool(unittest.IsolatedAsyncioTestCase):
    """Comprehensive test suite for ImageToTextTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = ImageToTextTool()
        self.user_tool = ImageToTextUserTool()
        
        # Create test image data
        self.test_image_data = self._create_test_image()
        self.test_base64_image = self._create_base64_test_image()
        
        # Mock responses
        self.mock_description = "A test image showing geometric shapes and patterns."

    def _create_test_image(self) -> bytes:
        """Create a test image in memory."""
        img = Image.new('RGB', (800, 600), color='red')
        # Add some simple patterns
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 300, 300], fill='blue')
        draw.ellipse([400, 200, 600, 400], fill='green')
        
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()

    def _create_base64_test_image(self) -> str:
        """Create a base64 encoded test image."""
        img_bytes = self._create_test_image()
        b64_str = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"

    def test_tool_properties(self):
        """Test tool basic properties."""
        self.assertEqual(self.tool.name, "image_to_text")
        self.assertIn("vision-enabled AI models", self.tool.description)
        
        params = self.tool.parameters
        self.assertEqual(params["type"], "object")
        self.assertIn("images", params["properties"])
        self.assertEqual(params["properties"]["images"]["maxItems"], DEFAULT_MAX_IMAGES_PER_REQUEST)

    async def test_empty_images_input(self):
        """Test handling of empty images array."""
        result = await self.tool.execute(images=[])
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "No images provided")
        self.assertEqual(result["results"], [])

    async def test_too_many_images(self):
        """Test handling of too many images."""
        images = [{"type": "file", "path": "test.jpg"} for _ in range(DEFAULT_MAX_IMAGES_PER_REQUEST + 1)]
        result = await self.tool.execute(images=images)
        
        self.assertFalse(result["success"])
        self.assertIn("Too many images", result["error"])

    async def test_invalid_image_type(self):
        """Test handling of invalid image type."""
        images = [{"type": "invalid", "data": "test"}]
        result = await self.tool.execute(images=images)
        
        self.assertFalse(result["success"])
        self.assertEqual(len(result["results"]), 0)

    def test_image_scaling(self):
        """Test image scaling functionality."""
        # Test image that needs scaling
        large_img = Image.new('RGB', (2048, 1536), color='blue')
        scaled_img = self.tool._scale_image(large_img)
        
        self.assertLessEqual(scaled_img.width, DEFAULT_MAX_IMAGE_WIDTH)
        self.assertLessEqual(scaled_img.height, DEFAULT_MAX_IMAGE_HEIGHT)
        
        # Test aspect ratio preservation
        aspect_ratio_original = large_img.width / large_img.height
        aspect_ratio_scaled = scaled_img.width / scaled_img.height
        self.assertAlmostEqual(aspect_ratio_original, aspect_ratio_scaled, places=2)

    def test_no_scaling_needed(self):
        """Test that small images are not scaled."""
        small_img = Image.new('RGB', (512, 384), color='green')
        scaled_img = self.tool._scale_image(small_img)
        
        self.assertEqual(small_img.size, scaled_img.size)

    async def test_file_input_processing(self):
        """Test file input processing."""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(self.test_image_data)
            tmp_file_path = tmp_file.name
        
        try:
            result = await self.tool._process_file_input(tmp_file_path, 0, 'high')
            
            self.assertEqual(result['index'], 0)
            self.assertTrue(result['source'].startswith('file:'))
            self.assertTrue(result['base64_data'].startswith('data:image/jpeg;base64,'))
            self.assertEqual(result['quality'], 'high')
            self.assertIn('original_size', result)
            self.assertIn('processed_size', result)
        finally:
            os.unlink(tmp_file_path)

    async def test_file_not_found(self):
        """Test handling of non-existent file."""
        with self.assertRaises(ValueError) as context:
            await self.tool._process_file_input('/non/existent/file.jpg', 0, 'high')
        
        self.assertIn("File not found", str(context.exception))

    async def test_unsupported_file_format(self):
        """Test handling of unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b"Not an image")
            tmp_file_path = tmp_file.name
        
        try:
            with self.assertRaises(ValueError) as context:
                await self.tool._process_file_input(tmp_file_path, 0, 'high')
            
            self.assertIn("Unsupported file format", str(context.exception))
        finally:
            os.unlink(tmp_file_path)

    async def test_base64_input_processing(self):
        """Test base64 input processing."""
        result = await self.tool._process_base64_input(self.test_base64_image, 1, 'high')
        
        self.assertEqual(result['index'], 1)
        self.assertEqual(result['source'], 'base64:provided')
        self.assertTrue(result['base64_data'].startswith('data:image/jpeg;base64,'))
        self.assertEqual(result['quality'], 'high')

    async def test_base64_invalid_format(self):
        """Test handling of invalid base64 format."""
        with self.assertRaises(ValueError) as context:
            await self.tool._process_base64_input("invalid_base64", 0, 'high')
        
        self.assertIn("MIME type prefix", str(context.exception))

    async def test_base64_invalid_data(self):
        """Test handling of invalid base64 data."""
        with self.assertRaises(ValueError) as context:
            await self.tool._process_base64_input("data:image/jpeg;base64,invalid_data", 0, 'high')
        
        self.assertIn("Invalid base64 image data", str(context.exception))

    @patch('requests.get')
    async def test_url_input_processing(self, mock_get):
        """Test URL input processing."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.content = self.test_image_data
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = await self.tool._process_url_input('https://example.com/test.jpg', 2, 'high')
        
        self.assertEqual(result['index'], 2)
        self.assertTrue(result['source'].startswith('url:'))
        self.assertTrue(result['base64_data'].startswith('data:image/jpeg;base64,'))
        self.assertEqual(result['quality'], 'high')

    async def test_url_invalid_format(self):
        """Test handling of invalid URL format."""
        with self.assertRaises(ValueError) as context:
            await self.tool._process_url_input('invalid_url', 0, 'high')
        
        self.assertIn("Invalid URL", str(context.exception))

    @patch('requests.get')
    async def test_url_non_image_content(self, mock_get):
        """Test handling of non-image URL content."""
        mock_response = Mock()
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            await self.tool._process_url_input('https://example.com/test.html', 0, 'high')
        
        self.assertIn("does not point to an image", str(context.exception))

    def test_parse_batch_descriptions(self):
        """Test batch description parsing."""
        images = [
            {'index': 0, 'description': None},
            {'index': 1, 'description': None}
        ]
        descriptions = "First image description.\n\nSecond image description."
        
        result = self.tool._parse_batch_descriptions(images, descriptions)
        
        self.assertEqual(result[0]['description'], "First image description.")
        self.assertEqual(result[1]['description'], "Second image description.")

    def test_format_results(self):
        """Test result formatting."""
        results = [
            {
                'index': 0,
                'source': 'file:test.jpg',
                'description': 'Test description',
                'original_size': (800, 600),
                'processed_size': (800, 600)
            },
            {
                'index': 1,
                'error': 'Processing failed'
            }
        ]
        
        formatted = self.tool._format_results(results, include_context=True)
        
        self.assertEqual(len(formatted), 2)
        self.assertTrue(formatted[0]['success'])
        self.assertEqual(formatted[0]['description'], 'Test description')
        self.assertFalse(formatted[1]['success'])
        self.assertEqual(formatted[1]['error'], 'Processing failed')

    @patch('user_tools.image_to_text.llm_manager')
    async def test_vision_api_call_success(self, mock_llm_manager):
        """Test successful vision API call."""
        mock_llm_manager.call_image_processing = AsyncMock(return_value=self.mock_description)
        
        messages = [{"role": "system", "content": "test"}]
        result = await self.tool._call_vision_api(messages)
        
        self.assertEqual(result, self.mock_description)
        mock_llm_manager.call_image_processing.assert_called_once()

    @patch('user_tools.image_to_text.llm_manager')
    async def test_vision_api_call_failure(self, mock_llm_manager):
        """Test vision API call failure handling."""
        mock_llm_manager.call_image_processing = AsyncMock(side_effect=Exception("API Error"))
        
        messages = [{"role": "system", "content": "test"}]
        
        with self.assertRaises(Exception) as context:
            await self.tool._call_vision_api(messages)
        
        self.assertIn("Vision API call failed", str(context.exception))

    @patch('user_tools.image_to_text.llm_manager')
    async def test_vision_api_fallback_response(self, mock_llm_manager):
        """Test vision API fallback response for configuration issues."""
        mock_llm_manager.call_image_processing = AsyncMock(
            side_effect=Exception("Image processing provider not available")
        )
        
        messages = [{"role": "system", "content": "test"}]
        result = await self.tool._call_vision_api(messages)
        
        self.assertIn("not configured", result)

    @patch('user_tools.image_to_text.llm_manager', None)
    async def test_no_llm_manager(self):
        """Test handling when LLM Manager is not available."""
        messages = [{"role": "system", "content": "test"}]
        
        with self.assertRaises(Exception) as context:
            await self.tool._call_vision_api(messages)
        
        self.assertIn("LLM Manager not available", str(context.exception))

    def test_system_prompt_loading(self):
        """Test system prompt loading from file."""
        # Test with existing prompt
        prompt = self.tool._load_system_prompt()
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_system_prompt_fallback(self, mock_open):
        """Test system prompt fallback when file not found."""
        tool = ImageToTextTool()
        prompt = tool._load_system_prompt()
        
        self.assertIn("expert image analyst", prompt)

    async def test_user_tool_wrapper(self):
        """Test user tool wrapper functionality."""
        self.assertEqual(self.user_tool.name, "image_to_text")
        self.assertIn("vision-enabled", self.user_tool.description)
        
        # Test parameter forwarding
        params = self.user_tool.parameters
        self.assertIn("images", params["properties"])

    @patch('user_tools.image_to_text.llm_manager')
    async def test_full_execution_workflow(self, mock_llm_manager):
        """Test complete execution workflow with mixed inputs."""
        mock_llm_manager.call_image_processing = AsyncMock(return_value=self.mock_description)
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(self.test_image_data)
            tmp_file_path = tmp_file.name
        
        try:
            # Test with mixed input types
            images = [
                {"type": "file", "path": tmp_file_path},
                {"type": "base64", "data": self.test_base64_image}
            ]
            
            result = await self.tool.execute(
                images=images,
                processing_mode=PROCESSING_MODE_SEQUENTIAL,
                include_context=True
            )
            
            self.assertTrue(result["success"])
            self.assertEqual(result["total_images"], 2)
            self.assertEqual(result["processed_images"], 2)
            self.assertEqual(result["failed_images"], 0)
            self.assertEqual(len(result["results"]), 2)
            
            # Check both images got descriptions
            for img_result in result["results"]:
                self.assertTrue(img_result["success"])
                self.assertEqual(img_result["description"], self.mock_description)
        
        finally:
            os.unlink(tmp_file_path)

    @patch('user_tools.image_to_text.llm_manager')  
    async def test_batch_processing_mode(self, mock_llm_manager):
        """Test batch processing mode."""
        mock_llm_manager.call_image_processing = AsyncMock(
            return_value="First image description.\n\nSecond image description."
        )
        
        # Create test images
        images = [
            {"type": "base64", "data": self.test_base64_image},
            {"type": "base64", "data": self.test_base64_image}
        ]
        
        result = await self.tool.execute(
            images=images,
            processing_mode=PROCESSING_MODE_BATCH
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["processing_mode"], PROCESSING_MODE_BATCH)
        self.assertEqual(len(result["results"]), 2)

    async def test_constants_compliance(self):
        """Test that tool uses constants instead of hardcoded values."""
        # Check that all numeric and string values come from constants
        tool_code = str(self.tool.__class__)
        
        # Verify key constants are used
        self.assertEqual(self.tool.parameters["properties"]["images"]["maxItems"], 
                        DEFAULT_MAX_IMAGES_PER_REQUEST)
        
        # Test scaling uses constants
        large_img = Image.new('RGB', (3000, 2000), color='red')
        scaled = self.tool._scale_image(large_img)
        
        self.assertLessEqual(scaled.width, DEFAULT_MAX_IMAGE_WIDTH)
        self.assertLessEqual(scaled.height, DEFAULT_MAX_IMAGE_HEIGHT)


class TestImageToTextIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for image-to-text tool."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.tool = ImageToTextUserTool()

    async def test_tool_discovery_integration(self):
        """Test that tool can be discovered by the system."""
        # Test that get_tool function works
        from user_tools.image_to_text_tool import get_tool
        discovered_tool = get_tool()
        
        self.assertIsInstance(discovered_tool, ImageToTextUserTool)
        self.assertEqual(discovered_tool.name, "image_to_text")

    async def test_error_handling_integration(self):
        """Test comprehensive error handling."""
        # Test with invalid inputs
        result = await self.tool.execute(images=[{"type": "invalid"}])
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)