#!/usr/bin/env python3
"""
LLM Configuration Tool
Interactive tool to configure llm_config.yaml with all provider and model permutations
"""

import os
import sys
import yaml
from pathlib import Path

class LLMConfigTool:
    def __init__(self):
        self.config_file = Path("config/llm_config.yaml")
        self.providers = {
            'ollama': {
                'name': 'Ollama (Local)',
                'base_url': 'http://127.0.0.1:11434',
                'api_key': None,
                'models': {
                    'llama3.2:3b': 'Llama 3.2 3B (Fast, Light)',
                    'llama3.2:1b': 'Llama 3.2 1B (Fastest)',
                    'llama3.1:8b': 'Llama 3.1 8B (Balanced)',
                    'qwen3:8b': 'Qwen 3 8B (Tool Calling)',
                    'deepseek-r1:8b': 'DeepSeek R1 8B (Reasoning)',
                    'mistral:7b': 'Mistral 7B',
                    'gemma2:9b': 'Gemma 2 9B',
                    'phi3:3.8b': 'Phi 3 3.8B'
                }
            },
            'openai': {
                'name': 'OpenAI (Cloud)',
                'base_url': 'https://api.openai.com/v1',
                'api_key': '${OPENAI_API_KEY}',
                'models': {
                    'gpt-4o': 'GPT-4o (Latest)',
                    'gpt-4-turbo': 'GPT-4 Turbo',
                    'gpt-4': 'GPT-4',
                    'gpt-3.5-turbo': 'GPT-3.5 Turbo',
                    'gpt-4o-mini': 'GPT-4o Mini (Fast)'
                }
            },
            'qwen': {
                'name': 'Qwen Cloud (Alibaba)',
                'base_url': 'https://dashscope.aliyuncs.com/api/v1',
                'api_key': '${QWEN_API_KEY}',
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
                'api_key': '${GOOGLE_API_KEY}',
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
    
    def create_config(self, primary_provider, primary_model, tool_provider, tool_model):
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
                'providers': {}
            },
            'performance': {
                'connection_pool_size': 10,
                'max_concurrent_requests': 5,
                'request_timeout': 600,
                'streaming_chunk_size': 1024
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
        for provider_key in used_providers:
            config['llm']['providers'][provider_key] = self.get_provider_config(provider_key)
        
        return config
    
    def get_model_config(self, provider_key, model, is_primary=True):
        """Get model-specific configuration"""
        provider = self.providers[provider_key]
        
        # Base configuration with all required fields
        base_config = {
            'model': model,
            'timeout': 600 if is_primary else 300,
            'context_window_size': 8192,  # CRITICAL: Required for all providers
            'temperature': 0.7
        }
        
        if provider_key == 'ollama':
            # Ollama-specific configuration
            base_config.update({
                'num_predict': 16384 if is_primary else 4096,  # CRITICAL: Output token limit for Ollama
                'max_tokens': 8192 if is_primary else 4096,    # Backward compatibility
                'base_url': 'http://127.0.0.1:11434',
                'api_key': None,
                'stream': is_primary
            })
        else:
            # Non-Ollama providers (OpenAI, Qwen, Gemini, etc.)
            base_config.update({
                'max_tokens': 8192 if is_primary else 4096,    # CRITICAL: Output token limit for non-Ollama
                'stream': is_primary
            })
            
            # Provider-specific settings
            if provider_key == 'openai':
                base_config.update({
                    'api_key': '${OPENAI_API_KEY}',
                    'base_url': 'https://api.openai.com/v1'
                })
            elif provider_key == 'qwen':
                base_config.update({
                    'api_key': '${QWEN_API_KEY}',
                    'base_url': 'https://dashscope.aliyuncs.com/api/v1'
                })
            elif provider_key == 'gemini':
                base_config.update({
                    'api_key': '${GOOGLE_API_KEY}',
                    'base_url': 'https://generativelanguage.googleapis.com/v1beta'
                })
        
        return base_config
    
    def get_provider_config(self, provider_key):
        """Get provider-specific configuration"""
        configs = {
            'ollama': {
                'health_check_url': 'http://127.0.0.1:11434/api/tags',
                'retry_attempts': 3,
                'retry_delay': 2
            },
            'openai': {
                'api_key': '${OPENAI_API_KEY}',
                'base_url': 'https://api.openai.com/v1',
                'organization': None,
                'retry_attempts': 3,
                'retry_delay': 1,
                'models': {
                    'primary': 'gpt-4o',
                    'tool_calling': 'gpt-4o'
                }
            },
            'qwen': {
                'api_key': '${QWEN_API_KEY}',
                'base_url': 'https://dashscope.aliyuncs.com/api/v1',
                'retry_attempts': 3,
                'retry_delay': 1,
                'models': {
                    'primary': 'qwen-plus',
                    'tool_calling': 'qwen-plus'
                }
            },
            'gemini': {
                'api_key': '${GOOGLE_API_KEY}',
                'base_url': 'https://generativelanguage.googleapis.com/v1beta',
                'retry_attempts': 3,
                'retry_delay': 1,
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
                choice = input("Select configuration (1-8): ").strip()
                
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
                else:
                    print("Please enter 1, 2, 3, 4, 5, 6, 7, or 8")
                    
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

if __name__ == "__main__":
    tool = LLMConfigTool()
    tool.run()