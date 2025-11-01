
import asyncio
import base64
import os
import sys
import tempfile
from io import BytesIO
from PIL import Image, ImageDraw
import pytest
from unittest.mock import patch, AsyncMock

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from user_tools.image_to_text import ImageToTextTool

@pytest.fixture
def tool():
    return ImageToTextTool()

def create_test_image(width, height, color, format):
    img = Image.new('RGB', (width, height), color=color)
    buffer = BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()

@pytest.mark.asyncio
async def test_file_input_processing(tool):
    test_image = create_test_image(100, 100, 'red', 'PNG')
    tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmp_file.write(test_image)
    tmp_path = tmp_file.name
    tmp_file.close()

    with patch.object(tool, '_process_with_ollama') as mock_process:
        mock_process.return_value = {'success': True, 'description': 'A red square'}
        result = await tool.execute(image=tmp_path)
        assert result['success']
        assert result['description'] == 'A red square'

    os.unlink(tmp_path)

@pytest.mark.asyncio
async def test_base64_input_processing(tool):
    test_image = create_test_image(100, 100, 'blue', 'JPEG')
    b64_data = base64.b64encode(test_image).decode('utf-8')
    b64_image = f"data:image/jpeg;base64,{b64_data}"

    with patch.object(tool, '_process_with_ollama') as mock_process:
        mock_process.return_value = {'success': True, 'description': 'A blue square'}
        result = await tool.execute(image=b64_image)
        assert result['success']
        assert result['description'] == 'A blue square'

@pytest.mark.asyncio
async def test_error_handling(tool):
    result = await tool.execute(image=None)
    assert not result['success']
    assert result['error'] == 'No image provided'
