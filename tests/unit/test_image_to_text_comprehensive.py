
import asyncio
import base64
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO
from PIL import Image, ImageDraw

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from user_tools.image_to_text import ImageToTextTool

class TestImageToTextTool(unittest.IsolatedAsyncioTestCase):
    """Comprehensive test suite for ImageToTextTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = ImageToTextTool()
        self.test_base64_image = self._create_base64_test_image()
        self.mock_description = "A test image showing geometric shapes and patterns."

    def _create_base64_test_image(self) -> str:
        """Create a base64 encoded test image."""
        img = Image.new('RGB', (800, 600), color='red')
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 300, 300], fill='blue')
        draw.ellipse([400, 200, 600, 400], fill='green')
        
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        img_bytes = buffer.getvalue()
        b64_str = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"

    def test_tool_properties(self):
        """Test tool basic properties."""
        self.assertEqual(self.tool.name, "image_to_text")
        self.assertIn("Convert images to detailed text descriptions", self.tool.description)
        
        params = self.tool.parameters
        self.assertEqual(params["type"], "object")
        self.assertIn("image", params["properties"])

    async def test_empty_images_input(self):
        """Test handling of empty images array."""
        result = await self.tool.execute(image=None)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "No image provided")

    @patch('user_tools.image_to_text.ImageToTextTool._process_with_ollama')
    async def test_full_execution_workflow(self, mock_process_with_ollama):
        """Test complete execution workflow with mixed inputs."""
        mock_process_with_ollama.return_value = {
            "success": True,
            "description": self.mock_description,
            "model": "test-model",
            "timestamp": "test-timestamp"
        }
        
        result = await self.tool.execute(
            image=self.test_base64_image,
            prompt="Describe this image"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["description"], self.mock_description)

if __name__ == '__main__':
    unittest.main(verbosity=2)
