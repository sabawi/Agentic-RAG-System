#!/usr/bin/env python3
"""
Model Switcher - Quick Configuration Tool for Testing
Allows easy switching between pre-configured LLM models for tool calling and primary LLM.
"""

import yaml
import sys
import os
from pathlib import Path

CONFIG_FILE = "config/llm_config.yaml"

# Pre-configured model combinations for testing
MODEL_PRESETS = {
    "1": {
        "name": "qwen3:8b + qwen3:8b (Original Working)",
        "tool_calling": {
            "type": "ollama",
            "model": "qwen3:8b",
            "temperature": 0.7
        },
        "primary": {
            "type": "ollama", 
            "model": "qwen3:8b",
            "temperature": 0.7
        }
    },
    "2": {
        "name": "gpt-4o-mini + qwen3:8b (Hybrid)",
        "tool_calling": {
            "type": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.5
        },
        "primary": {
            "type": "ollama",
            "model": "qwen3:8b", 
            "temperature": 0.7
        }
    },
    "3": {
        "name": "gpt-4.1-mini + qwen3:8b (Latest)",
        "tool_calling": {
            "type": "openai",
            "model": "gpt-4.1-mini",
            "temperature": 0.5
        },
        "primary": {
            "type": "ollama",
            "model": "qwen3:8b",
            "temperature": 0.7
        }
    },
    "4": {
        "name": "gpt-4-1106-preview + qwen3:8b (Original GPT-4)",
        "tool_calling": {
            "type": "openai", 
            "model": "gpt-4-1106-preview",
            "temperature": 0.1
        },
        "primary": {
            "type": "ollama",
            "model": "qwen3:8b",
            "temperature": 0.7
        }
    },
    "5": {
        "name": "llama3.2:3b + llama3.2:3b (Local Only)",
        "tool_calling": {
            "type": "ollama",
            "model": "llama3.2:3b", 
            "temperature": 0.7
        },
        "primary": {
            "type": "ollama",
            "model": "llama3.2:3b",
            "temperature": 0.7
        }
    }
}

def load_config():
    """Load current LLM configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {CONFIG_FILE}")
        sys.exit(1)

def save_config(config):
    """Save updated LLM configuration"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        print(f"✅ Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"❌ Failed to save config: {e}")
        sys.exit(1)

def show_current_config(config):
    """Display current model configuration"""
    tool_config = config['llm']['tool_calling']
    primary_config = config['llm']['primary']
    
    print("\n📋 CURRENT CONFIGURATION:")
    print("=" * 50)
    print(f"🔧 Tool Calling: {tool_config['type']} - {tool_config['config']['model']}")
    print(f"🤖 Primary LLM:  {primary_config['type']} - {primary_config['config']['model']}")
    print("=" * 50)

def show_presets():
    """Display available model presets"""
    print("\n🎯 AVAILABLE MODEL PRESETS:")
    print("=" * 60)
    for key, preset in MODEL_PRESETS.items():
        tool = preset['tool_calling']
        primary = preset['primary']
        print(f"{key}. {preset['name']}")
        print(f"   🔧 Tool: {tool['type']} - {tool['model']} (temp: {tool['temperature']})")
        print(f"   🤖 Primary: {primary['type']} - {primary['model']} (temp: {primary['temperature']})")
        print()

def apply_preset(config, preset_key):
    """Apply a model preset to the configuration"""
    if preset_key not in MODEL_PRESETS:
        print(f"❌ Invalid preset: {preset_key}")
        return False
    
    preset = MODEL_PRESETS[preset_key]
    
    # Update tool calling configuration
    tool_config = preset['tool_calling']
    config['llm']['tool_calling']['type'] = tool_config['type']
    config['llm']['tool_calling']['config']['model'] = tool_config['model']
    config['llm']['tool_calling']['config']['temperature'] = tool_config['temperature']
    
    # Update tool calling provider-specific settings
    if tool_config['type'] == 'openai':
        config['llm']['tool_calling']['config']['base_url'] = "https://api.openai.com/v1"
        config['llm']['tool_calling']['config']['api_key'] = "${OPENAI_API_KEY}"
        config['llm']['tool_calling']['config']['timeout'] = 300
        config['llm']['tool_calling']['config']['max_tokens'] = 2048
        config['llm']['tool_calling']['config']['stream'] = False
    else:  # ollama
        config['llm']['tool_calling']['config']['base_url'] = "http://127.0.0.1:11434"
        config['llm']['tool_calling']['config']['api_key'] = None
        config['llm']['tool_calling']['config']['timeout'] = 600
        config['llm']['tool_calling']['config']['max_tokens'] = 4096
        config['llm']['tool_calling']['config']['stream'] = False
    
    # Update primary configuration 
    primary_config = preset['primary']
    config['llm']['primary']['type'] = primary_config['type']
    config['llm']['primary']['config']['model'] = primary_config['model']
    config['llm']['primary']['config']['temperature'] = primary_config['temperature']
    
    # Update primary provider-specific settings
    if primary_config['type'] == 'openai':
        config['llm']['primary']['config']['base_url'] = "https://api.openai.com/v1"
        config['llm']['primary']['config']['api_key'] = "${OPENAI_API_KEY}"
        config['llm']['primary']['config']['timeout'] = 300
        config['llm']['primary']['config']['max_tokens'] = 4096
        config['llm']['primary']['config']['stream'] = True
    else:  # ollama
        config['llm']['primary']['config']['base_url'] = "http://127.0.0.1:11434"
        config['llm']['primary']['config']['api_key'] = None
        config['llm']['primary']['config']['timeout'] = 600
        config['llm']['primary']['config']['max_tokens'] = 4096
        config['llm']['primary']['config']['stream'] = True
    
    print(f"\n✅ Applied preset: {preset['name']}")
    return True

def main():
    """Main CLI interface"""
    print("🔧 LLM Model Switcher - Testing Configuration Tool")
    print("=" * 60)
    
    # Check if config file exists
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Configuration file not found: {CONFIG_FILE}")
        sys.exit(1)
    
    # Load current configuration
    config = load_config()
    
    # Show current configuration
    show_current_config(config)
    
    # Show available presets
    show_presets()
    
    # Get user selection
    while True:
        choice = input("🎯 Select preset (1-5) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            print("👋 Goodbye!")
            sys.exit(0)
        
        if choice in MODEL_PRESETS:
            if apply_preset(config, choice):
                save_config(config)
                show_current_config(config)
                
                print("\n🚀 NEXT STEPS:")
                print("1. Restart the server: ./stop_complete.sh && ./start_complete.sh")
                print("2. Test with your Gaza news prompt")
                print("3. Check tool calling behavior")
                break
            else:
                print("❌ Failed to apply preset")
        else:
            print("❌ Invalid choice. Please select 1-5 or 'q'")

if __name__ == "__main__":
    main()