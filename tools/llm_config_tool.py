#!/usr/bin/env python3
"""
LLM Configuration Tool
Interactive tool to configure llm_config.yaml with all provider and model permutations

WARNING: This tool still contains references to constants that were removed from llm_constants.py
TODO: Update this tool to work without external constants (low priority - tool not part of runtime)
"""

import os
import sys
import yaml
from pathlib import Path

# Configuration constants for tool - all values should go into llm_config.yaml
# These are for the config tool UI only
VISION_MODELS_OLLAMA = {
    'llava:7b': 'LLaVA 7B (Vision)',
    'llava:13b': 'LLaVA 13B (Vision)',
    'bakllava': 'BakLLaVA (Vision)',
    'moondream': 'Moondream (Vision)'
}

VISION_MODELS_OPENAI = {
    'gpt-4-vision-preview': 'GPT-4 Vision (Image Analysis)'
}

class LLMConfigTool:
    def __init__(self):
        self.config_file = Path("config/llm_config.yaml")
        # Combine vision models with regular models
        ollama_models = {
            'llama3.2:3b': 'Llama 3.2 3B (Fast, Light)',
            'llama3.2:1b': 'Llama 3.2 1B (Fastest)',
            'llama3.1:8b': 'Llama 3.1 8B (Balanced)',
            'qwen3:8b': 'Qwen 3 8B (Tool Calling)',
            'deepseek-r1:8b': 'DeepSeek R1 8B (Reasoning)',
            'mistral:7b': 'Mistral 7B',
            'gemma2:9b': 'Gemma 2 9B',
            'phi3:3.8b': 'Phi 3 3.8B'
        }
        ollama_models.update(VISION_MODELS_OLLAMA)
        
        openai_models = {
            'gpt-4o': 'GPT-4o (Latest)',
            'gpt-4-turbo': 'GPT-4 Turbo',
            'gpt-4': 'GPT-4',
            'gpt-3.5-turbo': 'GPT-3.5 Turbo',
            'gpt-4o-mini': 'GPT-4o Mini (Fast)'
        }
        openai_models.update(VISION_MODELS_OPENAI)
        
        self.providers = {
            'ollama': {
                'name': 'Ollama (Local)',
                'base_url': 'http://127.0.0.1:11434',
                'api_key': None,
                'models': ollama_models
            },
            'openai': {
                'name': 'OpenAI (Cloud)',
                'base_url': 'https://api.openai.com/v1',
                'api_key': ENV_VAR_OPENAI,
                'models': openai_models
            },
            'qwen': {
                'name': 'Qwen Cloud (Alibaba)',
                'base_url': 'https://dashscope.aliyuncs.com/api/v1',
                'api_key': ENV_VAR_QWEN,
                'models': {
                    'qwen-plus': 'Qwen Plus',
                    'qwen-turbo': 'Qwen Turbo',
                    'qwen-max': 'Qwen Max',
                    'qwen2.5-72b-instruct': 'Qwen 2.5 72B',
                    'qwen2.5-14b-instruct': 'Qwen 2.5 14B',
                    'qwen2.5-7b-instruct': 'Qwen 2.5 7B'
                }
            },
            'gemini': {
                'name': 'Google Gemini (Cloud)',
                'base_url': 'https://generativelanguage.googleapis.com/v1beta',
                'api_key': ENV_VAR_GOOGLE,
                'models': {
                    'gemini-1.5-pro': 'Gemini 1.5 Pro',
                    'gemini-1.5-flash': 'Gemini 1.5 Flash',
                    'gemini-1.0-pro': 'Gemini 1.0 Pro',
                    'gemini-pro': 'Gemini Pro'
                }
            }
        }
        
    def load_current_config(self):
        """Load current configuration if it exists"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        return None
    
    def display_providers(self):
        """Display available providers"""
        print("\n🔧 Available LLM Providers:")
        print("=" * 50)
        for idx, (key, provider) in enumerate(self.providers.items(), 1):
            print(f"{idx}. {provider['name']}")
            print(f"   Base URL: {provider['base_url']}")
            print(f"   API Key: {provider['api_key'] or 'Not required'}")
            print()
    
    def display_models(self, provider_key):
        """Display available models for a provider"""
        provider = self.providers[provider_key]
        print(f"\n🤖 Available models for {provider['name']}:")
        print("=" * 50)
        for idx, (model_key, model_name) in enumerate(provider['models'].items(), 1):
            print(f"{idx}. {model_key} - {model_name}")
        print()
    
    def select_provider(self):
        """Interactive provider selection"""
        self.display_providers()
        while True:
            try:
                choice = input("Select provider (1-4): ").strip()
                if choice in ['1', '2', '3', '4']:
                    provider_keys = list(self.providers.keys())
                    return provider_keys[int(choice) - 1]
                else:
                    print("Please enter 1, 2, 3, or 4")
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)
    
    def select_model(self, provider_key):
        """Interactive model selection"""
        self.display_models(provider_key)
        provider = self.providers[provider_key]
        model_keys = list(provider['models'].keys())
        
        while True:
            try:
                choice = input(f"Select model (1-{len(model_keys)}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(model_keys):
                    return model_keys[int(choice) - 1]
                else:
                    print(f"Please enter a number between 1 and {len(model_keys)}")
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)
    
    def create_config(self, primary_provider, primary_model, tool_provider, tool_model, image_provider=None, image_model=None):
        """Create complete configuration"""
        config = {
            'debug': {
                'log_requests': False,
                'log_timing': True,
                'mock_providers': False
            },
            'llm': {
                'fallback': {
                    'auto_switch': True,
                    'enabled': True,
                    'order': ['ollama', 'openai', 'qwen', 'gemini']
                },
                'primary': {
                    'type': primary_provider,
                    'config': self.get_model_config(primary_provider, primary_model, is_primary=True)
                },
                'tool_calling': {
                    'type': tool_provider,
                    'config': self.get_model_config(tool_provider, tool_model, is_primary=False)
                },
                'image_processing': {
                    'type': image_provider or 'ollama',
                    'config': self.get_model_config(image_provider or 'ollama', image_model or DEFAULT_IMAGE_PROCESSING_MODEL, is_primary=False)
                },
                'providers': {}
            },
            'performance': {
                'connection_pool_size': DEFAULT_CONNECTION_POOL_SIZE,
                'max_concurrent_requests': DEFAULT_MAX_CONCURRENT_REQUESTS,
                'request_timeout': DEFAULT_REQUEST_TIMEOUT,
                'streaming_chunk_size': DEFAULT_STREAMING_CHUNK_SIZE
            },
            'platform': {
                'config_dir': {
                    'linux': '${HOME}/.config/agentic_rag',
                    'macos': '${HOME}/.config/agentic_rag',
                    'windows': '${APPDATA}/agentic_rag'
                },
                'log_dir': {
                    'linux': '${HOME}/.local/share/agentic_rag/logs',
                    'macos': '${HOME}/.local/share/agentic_rag/logs',
                    'windows': '${LOCALAPPDATA}/agentic_rag/logs'
                },
                'temp_dir': {
                    'linux': '/tmp/agentic_rag',
                    'macos': '${TMPDIR}/agentic_rag',
                    'windows': '${TEMP}/agentic_rag'
                }
            },
            'security': {
                'api_key_encryption': False,
                'audit_logging': True,
                'rate_limiting': {
                    'enabled': True,
                    'requests_per_minute': 60,
                    'burst_limit': 10
                }
            }
        }
        
        # Add provider-specific configurations
        used_providers = set([primary_provider, tool_provider])
        if image_provider:
            used_providers.add(image_provider)
        for provider_key in used_providers:
            config['llm']['providers'][provider_key] = self.get_provider_config(provider_key)
        
        return config
    
    def get_model_config(self, provider_key, model, is_primary=True):
        """Get model-specific configuration"""
        provider = self.providers[provider_key]
        
        # Base configuration with all required fields
        base_config = {
            'model': model,
            'timeout': DEFAULT_PRIMARY_TIMEOUT if is_primary else DEFAULT_SECONDARY_TIMEOUT,
            'context_window_size': DEFAULT_CONTEXT_WINDOW_SIZE,  # CRITICAL: Required for all providers
            'temperature': 0.7
        }
        
        if provider_key == 'ollama':
            # Ollama-specific configuration
            base_config.update({
                'num_predict': OLLAMA_DEFAULT_NUM_PREDICT_PRIMARY if is_primary else OLLAMA_DEFAULT_NUM_PREDICT_SECONDARY,  # CRITICAL: Output token limit for Ollama
                'max_tokens': DEFAULT_PRIMARY_MAX_TOKENS if is_primary else DEFAULT_SECONDARY_MAX_TOKENS,    # Backward compatibility
                'base_url': 'http://127.0.0.1:11434',
                'api_key': None,
                'stream': is_primary
            })
        else:
            # Non-Ollama providers (OpenAI, Qwen, Gemini, etc.)
            base_config.update({
                'max_tokens': DEFAULT_PRIMARY_MAX_TOKENS if is_primary else DEFAULT_SECONDARY_MAX_TOKENS,    # CRITICAL: Output token limit for non-Ollama
                'stream': is_primary
            })
            
            # Provider-specific settings
            if provider_key == 'openai':
                base_config.update({
                    'api_key': ENV_VAR_OPENAI,
                    'base_url': OPENAI_BASE_URL
                })
            elif provider_key == 'qwen':
                base_config.update({
                    'api_key': ENV_VAR_QWEN,
                    'base_url': QWEN_BASE_URL
                })
            elif provider_key == 'gemini':
                base_config.update({
                    'api_key': ENV_VAR_GOOGLE,
                    'base_url': GEMINI_BASE_URL
                })
        
        return base_config
    
    def get_provider_config(self, provider_key):
        """Get provider-specific configuration"""
        configs = {
            'ollama': {
                'health_check_url': OLLAMA_HEALTH_CHECK_URL,
                'retry_attempts': DEFAULT_RETRY_ATTEMPTS,
                'retry_delay': DEFAULT_RETRY_DELAY
            },
            'openai': {
                'api_key': ENV_VAR_OPENAI,
                'base_url': 'https://api.openai.com/v1',
                'organization': None,
                'retry_attempts': DEFAULT_RETRY_ATTEMPTS,
                'retry_delay': DEFAULT_OPENAI_RETRY_DELAY,
                'models': {
                    'primary': 'gpt-4o',
                    'tool_calling': 'gpt-4o'
                }
            },
            'qwen': {
                'api_key': ENV_VAR_QWEN,
                'base_url': 'https://dashscope.aliyuncs.com/api/v1',
                'retry_attempts': DEFAULT_RETRY_ATTEMPTS,
                'retry_delay': DEFAULT_OPENAI_RETRY_DELAY,
                'models': {
                    'primary': 'qwen-plus',
                    'tool_calling': 'qwen-plus'
                }
            },
            'gemini': {
                'api_key': ENV_VAR_GOOGLE,
                'base_url': 'https://generativelanguage.googleapis.com/v1beta',
                'retry_attempts': DEFAULT_RETRY_ATTEMPTS,
                'retry_delay': DEFAULT_OPENAI_RETRY_DELAY,
                'models': {
                    'primary': 'gemini-1.5-pro',
                    'tool_calling': 'gemini-1.5-flash'
                }
            }
        }
        return configs[provider_key]
    
    def save_config(self, config):
        """Save configuration to file with proper documentation"""
        # Ensure config directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create config file with documentation header
        config_header = """# =============================================================================
# LLM Configuration File
# =============================================================================
#
# CRITICAL: Token Parameter Usage by Provider Type
# ------------------------------------------------
# 
# For OLLAMA providers (type: ollama):
#   • context_window_size → Maps to Ollama 'num_ctx' parameter (input context limit)
#   • num_predict         → Maps to Ollama 'num_predict' parameter (output tokens limit)
#   • max_tokens          → IGNORED (kept for backward compatibility only)
#
# For NON-OLLAMA providers (type: openai, qwen, gemini, etc.):
#   • context_window_size → Used for input context size management
#   • max_tokens          → Used for output tokens limit (native API parameter)
#   • num_predict         → Available but typically unused by these providers
#
# Parameter Priority (all providers):
#   1. Request-level parameters (highest priority)
#   2. Configuration file parameters  
#   3. Provider-specific defaults (lowest priority)
#
# =============================================================================

"""
        
        with open(self.config_file, 'w') as f:
            f.write(config_header)
            yaml.dump(config, f, default_flow_style=False, indent=2, sort_keys=False)
        
        print(f"✅ Configuration saved to {self.config_file}")
    
    def display_quick_configs(self):
        """Display pre-configured quick setups"""
        print("\n🚀 Quick Configuration Presets:")
        print("=" * 50)
        print("1. ⭐ Local Favorite")
        print("   Primary: Ollama qwen3:8b")
        print("   Tool Calling: Ollama qwen3:8b")
        print()
        print("2. 🌊 Surf and Turf")
        print("   Primary: Ollama qwen3:8b")
        print("   Tool Calling: OpenAI gpt-4o-mini")
        print()
        print("3. 🏃 Fast Local Setup")
        print("   Primary: Ollama llama3.2:3b")
        print("   Tool Calling: Ollama qwen3:8b")
        print()
        print("4. 🧠 Reasoning Setup")
        print("   Primary: Ollama llama3.1:8b")
        print("   Tool Calling: Ollama deepseek-r1:8b")
        print()
        print("5. ☁️ Cloud Premium Setup")
        print("   Primary: OpenAI gpt-4o")
        print("   Tool Calling: OpenAI gpt-4o")
        print()
        print("6. 🌏 Qwen Cloud Setup")
        print("   Primary: Qwen qwen-plus")
        print("   Tool Calling: Qwen qwen-plus")
        print()
        print("7. 🤖 Google Gemini Setup")
        print("   Primary: Gemini gemini-1.5-pro")
        print("   Tool Calling: Gemini gemini-1.5-flash")
        print()
        print("8. 🔧 Custom Configuration")
        print("   Choose your own combinations")
        print()
        print("9. 🖼️ Image Processing Setup")
        print("   Configure vision models for image analysis")
        print()
        print("10. ⚡ Optimization Settings")
        print("    Configure performance optimizations")
        print()
        print("11. 🧠 Arbitrator Settings")
        print("    Configure task validation and retry logic")
        print()
    
    def apply_quick_config(self, choice):
        """Apply a quick configuration preset"""
        quick_configs = {
            '1': ('ollama', 'qwen3:8b', 'ollama', 'qwen3:8b'),          # Local Favorite
            '2': ('ollama', 'qwen3:8b', 'openai', 'gpt-4o-mini'),        # Surf and Turf
            '3': ('ollama', 'llama3.2:3b', 'ollama', 'qwen3:8b'),        # Fast Local Setup
            '4': ('ollama', 'llama3.1:8b', 'ollama', 'deepseek-r1:8b'),  # Reasoning Setup
            '5': ('openai', 'gpt-4o', 'openai', 'gpt-4o'),               # Cloud Premium Setup
            '6': ('qwen', 'qwen-plus', 'qwen', 'qwen-plus'),             # Qwen Cloud Setup
            '7': ('gemini', 'gemini-1.5-pro', 'gemini', 'gemini-1.5-flash') # Google Gemini Setup
        }
        
        if choice in quick_configs:
            primary_provider, primary_model, tool_provider, tool_model = quick_configs[choice]
            return self.create_config(primary_provider, primary_model, tool_provider, tool_model)
        return None
    
    def run(self):
        """Main interactive loop"""
        print("🤖 LLM Configuration Tool")
        print("=" * 50)
        print("Configure your Agentic-RAG server with any combination of:")
        print("• Ollama (Local): llama3.2, qwen3, deepseek-r1, etc.")
        print("• OpenAI (Cloud): GPT-4o, GPT-4-turbo, etc.")
        print("• Qwen Cloud: qwen-plus, qwen-max, etc.")
        print("• Google Gemini: gemini-1.5-pro, gemini-1.5-flash, etc.")
        print()
        
        # Show current config if exists
        current = self.load_current_config()
        if current:
            primary = current.get('llm', {}).get('primary', {})
            tool_calling = current.get('llm', {}).get('tool_calling', {})
            print(f"📋 Current Configuration:")
            print(f"   Primary: {primary.get('type', 'unknown')} - {primary.get('config', {}).get('model', 'unknown')}")
            print(f"   Tool Calling: {tool_calling.get('type', 'unknown')} - {tool_calling.get('config', {}).get('model', 'unknown')}")
            print()
        
        # Quick config selection
        self.display_quick_configs()
        
        while True:
            try:
                choice = input("Select configuration (1-11): ").strip()
                
                if choice in ['1', '2', '3', '4', '5', '6', '7']:
                    config = self.apply_quick_config(choice)
                    if config:
                        self.save_config(config)
                        self.display_environment_setup(choice)
                        return
                elif choice == '8':
                    # Custom configuration
                    print("\n🔧 Custom Configuration")
                    print("\n1️⃣ Select PRIMARY model (main conversation)")
                    primary_provider = self.select_provider()
                    primary_model = self.select_model(primary_provider)
                    
                    print("\n2️⃣ Select TOOL CALLING model (function calls)")
                    tool_provider = self.select_provider()
                    tool_model = self.select_model(tool_provider)
                    
                    config = self.create_config(primary_provider, primary_model, tool_provider, tool_model)
                    self.save_config(config)
                    self.display_environment_setup_custom(primary_provider, tool_provider)
                    return
                elif choice == '9':
                    # Image processing configuration
                    self.configure_image_processing()
                    return
                elif choice == '10':
                    # Optimization settings
                    self.configure_optimization()
                    return
                elif choice == '11':
                    # Arbitrator settings
                    self.configure_arbitrator()
                    return
                else:
                    print("Please enter 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, or 11")
                    
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)
    
    def display_environment_setup(self, choice):
        """Display environment setup instructions"""
        print("\n🔐 Environment Setup Required:")
        print("=" * 50)
        
        if choice in ['5']:  # Cloud Premium (OpenAI)
            print("Set your OpenAI API key:")
            print("export OPENAI_API_KEY='your-openai-api-key-here'")
        elif choice in ['6']:  # Qwen Cloud
            print("Set your Qwen API key:")
            print("export QWEN_API_KEY='your-qwen-api-key-here'")
        elif choice in ['7']:  # Google Gemini
            print("Set your Google API key:")
            print("export GOOGLE_API_KEY='your-google-api-key-here'")
        elif choice == '2':  # Surf and Turf (needs both)
            print("Set your OpenAI API key:")
            print("export OPENAI_API_KEY='your-openai-api-key-here'")
            print()
            print("Ensure Ollama is running locally:")
            print("ollama serve")
            print()
            print("Pull required models:")
            print("ollama pull qwen3:8b")
        else:  # Pure Ollama setups
            print("Ensure Ollama is running locally:")
            print("ollama serve")
            print()
            print("Pull required models:")
            if choice == '1':  # Local Favorite
                print("ollama pull qwen3:8b")
            elif choice == '3':  # Fast Local
                print("ollama pull llama3.2:3b")
                print("ollama pull qwen3:8b")
            elif choice == '4':  # Reasoning
                print("ollama pull llama3.1:8b")
                print("ollama pull deepseek-r1:8b")
        
        print("\n🚀 Restart your server to apply changes:")
        print("./stop_complete.sh && ./start_complete.sh")
        print("\n✅ Configuration complete!")
    
    def display_environment_setup_custom(self, primary_provider, tool_provider):
        """Display environment setup for custom configuration"""
        print("\n🔐 Environment Setup Required:")
        print("=" * 50)
        
        providers_used = set([primary_provider, tool_provider])
        
        if 'openai' in providers_used:
            print("export OPENAI_API_KEY='your-openai-api-key-here'")
        if 'qwen' in providers_used:
            print("export QWEN_API_KEY='your-qwen-api-key-here'")
        if 'gemini' in providers_used:
            print("export GOOGLE_API_KEY='your-google-api-key-here'")
        if 'ollama' in providers_used:
            print("Ensure Ollama is running: ollama serve")
        
        print("\n🚀 Restart your server to apply changes:")
        print("./stop_complete.sh && ./start_complete.sh")
        print("\n✅ Configuration complete!")

    def configure_image_processing(self):
        """Configure image processing LLM settings"""
        print("\n🖼️ IMAGE PROCESSING LLM CONFIGURATION")
        print("=" * 50)
        print("Configure vision models for image analysis, OCR, and visual Q&A")
        print("These models will be available to user tools for image processing tasks")
        print()
        
        # Load current config
        current_config = self.load_current_config()
        current_image = current_config.get('llm', {}).get('image_processing', {}) if current_config else {}
        
        current_enabled = bool(current_image)
        current_provider = current_image.get('type', 'ollama')
        current_model = current_image.get('config', {}).get('model', DEFAULT_IMAGE_PROCESSING_MODEL)
        
        print(f"📋 Current Configuration:")
        print(f"   Status: {'✅ Configured' if current_enabled else '❌ Not configured'}")
        if current_enabled:
            print(f"   Provider: {current_provider}")
            print(f"   Model: {current_model}")
        print()
        
        # Configuration options
        print("🔧 Configuration Options:")
        print("1. 🏠 Local Vision Models (Ollama)")
        print("   • llava:7b - Fast, good quality")
        print("   • llava:13b - Better quality, slower")
        print("   • bakllava - Specialized for detailed analysis")
        print("   • moondream - Lightweight vision model")
        print()
        print("2. ☁️ Cloud Vision APIs")
        print("   • OpenAI GPT-4 Vision - Premium quality")
        print("   • Google Gemini Vision - Good balance")
        print("   • Qwen Vision - Cost-effective")
        print()
        print("3. ❌ Disable Image Processing")
        print()
        print("4. 🔙 Back to Main Menu")
        print()
        
        while True:
            try:
                choice = input("Select option (1-4): ").strip()
                
                if choice == '1':
                    # Local Ollama models
                    print("\n🏠 LOCAL VISION MODELS")
                    print("Available models:")
                    vision_models = [
                        ('llava:7b', 'LLaVA 7B - Fast, good quality'),
                        ('llava:13b', 'LLaVA 13B - Better quality, slower'),
                        ('bakllava', 'BakLLaVA - Detailed analysis'),
                        ('moondream', 'Moondream - Lightweight')
                    ]
                    
                    for idx, (model, desc) in enumerate(vision_models, 1):
                        print(f"{idx}. {model} - {desc}")
                    
                    model_choice = input(f"Select model (1-{len(vision_models)}): ").strip()
                    if model_choice.isdigit() and 1 <= int(model_choice) <= len(vision_models):
                        selected_model = vision_models[int(model_choice) - 1][0]
                        self.update_image_processing_config('ollama', selected_model)
                        print(f"\n✅ Image processing configured with {selected_model}")
                        print(f"🚀 Make sure to pull the model: ollama pull {selected_model}")
                        return
                    else:
                        print("Invalid selection.")
                        continue
                        
                elif choice == '2':
                    # Cloud APIs
                    print("\n☁️ CLOUD VISION APIS")
                    print("Available providers:")
                    cloud_models = [
                        ('openai', 'gpt-4-vision-preview', 'OpenAI GPT-4 Vision'),
                        ('gemini', 'gemini-1.5-pro-vision', 'Google Gemini Vision'),
                        ('qwen', 'qwen-vl-plus', 'Qwen Vision Plus')
                    ]
                    
                    for idx, (provider, model, desc) in enumerate(cloud_models, 1):
                        print(f"{idx}. {desc}")
                    
                    provider_choice = input(f"Select provider (1-{len(cloud_models)}): ").strip()
                    if provider_choice.isdigit() and 1 <= int(provider_choice) <= len(cloud_models):
                        provider, model, desc = cloud_models[int(provider_choice) - 1]
                        self.update_image_processing_config(provider, model)
                        print(f"\n✅ Image processing configured with {desc}")
                        print(f"🔐 Make sure to set your API key for {provider}")
                        return
                    else:
                        print("Invalid selection.")
                        continue
                        
                elif choice == '3':
                    # Disable
                    self.update_image_processing_config(None, None)
                    print("\n❌ Image processing disabled")
                    return
                    
                elif choice == '4':
                    # Back to main menu
                    return
                    
                else:
                    print("Please enter 1, 2, 3, or 4")
                    
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                return
        
        print("\n🚀 Restart your server to apply changes:")
        print("./stop_complete.sh && ./start_complete.sh")
    
    def update_image_processing_config(self, provider_type, model):
        """Update image processing configuration in the config file"""
        config_path = Path("config/llm_config.yaml")
        
        # Load current config
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = self._get_default_config()
        
        # Ensure LLM section exists
        if 'llm' not in config:
            config['llm'] = {}
            
        if provider_type is None:
            # Remove image processing config
            if 'image_processing' in config['llm']:
                del config['llm']['image_processing']
        else:
            # Set image processing config
            if provider_type == 'ollama':
                config['llm']['image_processing'] = {
                    'type': 'ollama',
                    'config': {
                        'model': model,
                        'timeout': DEFAULT_SECONDARY_TIMEOUT,
                        'context_window_size': DEFAULT_CONTEXT_WINDOW_SIZE,
                        'temperature': DEFAULT_SECONDARY_TEMPERATURE,
                        'max_tokens': DEFAULT_IMAGE_PROCESSING_MAX_TOKENS,
                        'stream': False,
                        'base_url': 'http://127.0.0.1:11434',
                        'api_key': None
                    }
                }
            else:
                # Cloud provider
                base_config = {
                    'model': model,
                    'timeout': DEFAULT_SECONDARY_TIMEOUT,
                    'context_window_size': DEFAULT_CONTEXT_WINDOW_SIZE,
                    'temperature': DEFAULT_SECONDARY_TEMPERATURE,
                    'max_tokens': DEFAULT_IMAGE_PROCESSING_MAX_TOKENS,
                    'stream': False
                }
                
                if provider_type == 'openai':
                    base_config.update({
                        'api_key': ENV_VAR_OPENAI,
                        'base_url': OPENAI_BASE_URL
                    })
                elif provider_type == 'gemini':
                    base_config.update({
                        'api_key': ENV_VAR_GOOGLE,
                        'base_url': GEMINI_BASE_URL
                    })
                elif provider_type == 'qwen':
                    base_config.update({
                        'api_key': ENV_VAR_QWEN,
                        'base_url': QWEN_BASE_URL
                    })
                
                config['llm']['image_processing'] = {
                    'type': provider_type,
                    'config': base_config
                }
        
        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def configure_optimization(self):
        """Interactive optimization settings configuration"""
        print("\n⚡ OPTIMIZATION SETTINGS CONFIGURATION")
        print("=" * 50)
        print()
        print("🎯 About Optimization System:")
        print("• A/B testing and gradual rollout system for performance improvements")
        print("• Automatic rollback if error rates exceed 20% or success rates fall below 80%")
        print("• Safe for production use with comprehensive monitoring")
        print("• Currently implements context compression and smart summarization")
        print()
        
        # Load current config
        current_config = self.load_current_config()
        current_opt = current_config.get('optimization', {})
        
        current_enabled = current_opt.get('enabled', False)
        current_rollout = current_opt.get('rollout_percentage', 100.0)
        current_logging = current_opt.get('detailed_logging', True)
        
        print(f"📊 Current Settings:")
        print(f"• Enabled: {'✅ YES' if current_enabled else '❌ NO'}")
        print(f"• Rollout: {current_rollout}%")
        print(f"• Detailed Logging: {'✅ YES' if current_logging else '❌ NO'}")
        print()
        
        while True:
            try:
                print("🔧 Configuration Options:")
                print("1. ✅ Enable optimization (100% rollout)")
                print("2. 🧪 Enable with gradual rollout (A/B testing)")
                print("3. ❌ Disable optimization")
                print("4. 📊 Configure detailed logging")
                print("5. 🔙 Back to main menu")
                print()
                
                choice = input("Select option (1-5): ").strip()
                
                if choice == '1':
                    # Enable full optimization
                    self.update_optimization_config(enabled=True, rollout_percentage=100.0)
                    print("\n✅ Optimization ENABLED (100% rollout)")
                    print("🚀 Performance improvements will apply to all requests")
                    break
                    
                elif choice == '2':
                    # Gradual rollout
                    print("\n🧪 GRADUAL ROLLOUT CONFIGURATION")
                    print("Enter rollout percentage (0-100):")
                    print("• 0%: Disabled")
                    print("• 25%: Apply to 25% of users (A/B testing)")
                    print("• 50%: Apply to 50% of users")
                    print("• 100%: Apply to all users")
                    
                    while True:
                        try:
                            rollout = float(input("Rollout percentage (0-100): ").strip())
                            if 0 <= rollout <= 100:
                                self.update_optimization_config(enabled=True, rollout_percentage=rollout)
                                print(f"\n🧪 Optimization ENABLED ({rollout}% rollout)")
                                if rollout < 100:
                                    print("🎲 A/B testing mode - only some users will receive optimizations")
                                break
                            else:
                                print("❌ Please enter a number between 0 and 100")
                        except ValueError:
                            print("❌ Please enter a valid number")
                    break
                    
                elif choice == '3':
                    # Disable optimization
                    self.update_optimization_config(enabled=False, rollout_percentage=0.0)
                    print("\n❌ Optimization DISABLED")
                    print("🔧 System will use standard processing (safer, potentially slower)")
                    break
                    
                elif choice == '4':
                    # Configure logging
                    print("\n📊 DETAILED LOGGING CONFIGURATION")
                    print("Detailed logging includes:")
                    print("• Optimization attempt tracking")
                    print("• Success/failure rates")
                    print("• Performance metrics")
                    print("• A/B testing statistics")
                    print()
                    
                    log_choice = input("Enable detailed logging? (y/n): ").strip().lower()
                    detailed_logging = log_choice in ['y', 'yes', '1', 'true']
                    
                    self.update_optimization_config(detailed_logging=detailed_logging)
                    print(f"\n📊 Detailed logging {'ENABLED' if detailed_logging else 'DISABLED'}")
                    break
                    
                elif choice == '5':
                    # Back to main menu
                    return
                    
                else:
                    print("❌ Please enter 1, 2, 3, 4, or 5")
                    
            except KeyboardInterrupt:
                print("\n🔙 Returning to main menu...")
                return
        
        print("\n🚀 Restart your server to apply optimization changes:")
        print("./stop_complete.sh && ./start_complete.sh")
        print("\n✅ Optimization configuration complete!")

    def update_optimization_config(self, enabled=None, rollout_percentage=None, detailed_logging=None):
        """Update optimization settings in the config file"""
        config_path = os.path.join('config', 'llm_config.yaml')
        
        # Load current config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Ensure optimization section exists
        if 'optimization' not in config:
            config['optimization'] = {}
        
        # Update only specified values
        if enabled is not None:
            config['optimization']['enabled'] = enabled
        if rollout_percentage is not None:
            config['optimization']['rollout_percentage'] = rollout_percentage
        if detailed_logging is not None:
            config['optimization']['detailed_logging'] = detailed_logging
        
        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def configure_arbitrator(self):
        """Configure arbitrator settings for task validation and retry logic"""
        print("\n🧠 Arbitrator System Configuration")
        print("=" * 50)
        print("The Arbitrator System provides intelligent task validation and retry logic")
        print("to eliminate hallucinated results from failed tool executions.")
        print()
        
        # Load current config
        current_config = self.load_current_config()
        current_arbitrator = current_config.get('arbitrator', {}) if current_config else {}
        
        # Display current status
        current_enabled = current_arbitrator.get('enabled', False)
        current_provider = current_arbitrator.get('type', 'openai')
        current_model = current_arbitrator.get('config', {}).get('model', 'gpt-4o-mini')
        
        print(f"📋 Current Configuration:")
        print(f"   Status: {'✅ Enabled' if current_enabled else '❌ Disabled'}")
        if current_enabled:
            print(f"   Provider: {current_provider}")
            print(f"   Model: {current_model}")
        print()
        
        # Configuration options
        print("🔧 Configuration Options:")
        print("1. Enable Arbitrator System")
        print("2. Disable Arbitrator System") 
        print("3. Configure Provider and Model")
        print("4. Reset to Defaults")
        print("5. Back to Main Menu")
        print()
        
        while True:
            try:
                choice = input("Select option (1-5): ").strip()
                
                if choice == '1':
                    # Enable arbitrator
                    self.update_arbitrator_config(enabled=True)
                    print("\n✅ Arbitrator System enabled successfully!")
                    print("📝 The system will now validate and retry failed tool executions.")
                    self.display_arbitrator_info()
                    return
                    
                elif choice == '2':
                    # Disable arbitrator
                    self.update_arbitrator_config(enabled=False)
                    print("\n❌ Arbitrator System disabled.")
                    print("📝 System will operate identically to original behavior.")
                    return
                    
                elif choice == '3':
                    # Configure provider and model
                    print("\n🔧 Provider Configuration")
                    print("Available providers:")
                    print("1. OpenAI (Recommended)")
                    print("2. Qwen Cloud") 
                    print("3. Google Gemini")
                    
                    provider_choice = input("Select provider (1-3): ").strip()
                    provider_map = {
                        '1': ('openai', 'gpt-4o-mini'),
                        '2': ('qwen', 'qwen-plus'),
                        '3': ('gemini', 'gemini-1.5-flash')
                    }
                    
                    if provider_choice in provider_map:
                        provider_type, default_model = provider_map[provider_choice]
                        self.update_arbitrator_config(
                            provider_type=provider_type,
                            model=default_model
                        )
                        print(f"\n✅ Arbitrator configured to use {provider_type} with {default_model}")
                    else:
                        print("Invalid provider selection.")
                    continue
                    
                elif choice == '4':
                    # Reset to defaults
                    self.update_arbitrator_config(
                        enabled=False,
                        provider_type='openai',
                        model='gpt-4o-mini'
                    )
                    print("\n🔄 Arbitrator configuration reset to defaults (disabled).")
                    return
                    
                elif choice == '5':
                    # Back to main menu
                    return
                    
                else:
                    print("Please enter 1, 2, 3, 4, or 5")
                    
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                return
    
    def update_arbitrator_config(self, enabled=None, provider_type=None, model=None):
        """Update arbitrator configuration in the config file"""
        config_path = Path("config/llm_config.yaml")
        
        # Load current config
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # Ensure arbitrator section exists
        if 'arbitrator' not in config:
            config['arbitrator'] = {
                'enabled': False,
                'type': 'openai',
                'config': {
                    'model': 'gpt-4o-mini',
                    'timeout': 60,
                    'context_window_size': 4096,
                    'temperature': DEFAULT_SECONDARY_TEMPERATURE,
                    'max_tokens': 1024,
                    'stream': False,
                    'api_key': ENV_VAR_OPENAI,
                    'base_url': OPENAI_BASE_URL
                }
            }
        
        # Update values if specified
        if enabled is not None:
            config['arbitrator']['enabled'] = enabled
            
        if provider_type is not None:
            config['arbitrator']['type'] = provider_type
            
            # Update provider-specific config
            if provider_type == 'openai':
                config['arbitrator']['config'].update({
                    'api_key': ENV_VAR_OPENAI,
                    'base_url': OPENAI_BASE_URL
                })
            elif provider_type == 'qwen':
                config['arbitrator']['config'].update({
                    'api_key': ENV_VAR_QWEN,
                    'base_url': QWEN_BASE_URL
                })
            elif provider_type == 'gemini':
                config['arbitrator']['config'].update({
                    'api_key': ENV_VAR_GOOGLE,
                    'base_url': 'https://generativelanguage.googleapis.com/v1'
                })
        
        if model is not None:
            config['arbitrator']['config']['model'] = model
        
        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def display_arbitrator_info(self):
        """Display information about arbitrator system"""
        print("\n📚 Arbitrator System Information:")
        print("=" * 50)
        print("🎯 Purpose: Eliminate hallucinated results from failed tool executions")
        print("🔄 Function: Validates tool results and retries with intelligent feedback")
        print("🛡️ Safety: Circuit breakers prevent infinite loops and resource waste")
        print("⚡ Performance: Minimal overhead when disabled, intelligent retry when enabled")
        print()
        print("📖 Example: If a script fails with 'file not found', the arbitrator will:")
        print("   1. Detect the specific error pattern") 
        print("   2. Generate corrected parameters (fix file path)")
        print("   3. Retry the tool execution with corrections")
        print("   4. Return accurate results instead of fabricated ones")
        print()
        print("🔧 Configuration: Arbitrator uses separate LLM for validation decisions")
        print("📊 Monitoring: Comprehensive logging tracks all validation attempts")

if __name__ == "__main__":
    tool = LLMConfigTool()
    tool.run()