
import os
import yaml
import pytest
from pathlib import Path

# Make sure the script can find the utils module
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.config_loader import ConfigLoader

@pytest.fixture
def temp_config_file(tmp_path):
    config_content = {
        'llm': {
            'primary': {
                'type': 'ollama',
                'config': {'model': 'test-primary'}
            },
            'tool_calling': {
                'type': 'openai',
                'config': {'model': 'test-tool-calling'}
            },
            'image_processing': {
                'type': 'ollama',
                'config': {
                    'model': 'test-image-processing',
                    'base_url': 'http://localhost:11434',
                    'fallback_model': 'test-fallback',
                    'timeout': 1800,
                    'temperature': 0.7
                }
            }
        }
    }
    config_file = tmp_path / "llm_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_content, f)
    return str(config_file)

def test_config_loader_integration(temp_config_file):
    """Test that config_loader can properly load the generated config"""
    config_loader = ConfigLoader(config_file=temp_config_file)
    image_config = config_loader.get_llm_config('image_processing')

    assert image_config['type'] == 'ollama'
    assert image_config['config']['model'] == 'test-image-processing'
    assert image_config['config']['base_url'] == 'http://localhost:11434'
    assert image_config['config']['fallback_model'] == 'test-fallback'
    assert image_config['config']['timeout'] == 1800
    assert image_config['config']['temperature'] == 0.7
