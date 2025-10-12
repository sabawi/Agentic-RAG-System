#!/usr/bin/env python3
"""
Agent Model Configuration CLI Tool
===================================

Easy-to-use CLI for managing LLM model aliases and configurations.

Usage:
    ./agent_model.py ls                                    # List all model aliases
    ./agent_model.py add --alias NAME --provider TYPE --model MODEL [options]
    ./agent_model.py update --alias NAME [options]
    ./agent_model.py delete --alias NAME
    ./agent_model.py set --alias NAME --as primary|tool_calling|arbitrator
    ./agent_model.py show --alias NAME                     # Show alias details
    ./agent_model.py status                                # Show current active models

Examples:
    # Add a new model alias
    ./agent_model.py add --alias qwen_local --provider ollama --model qwen3:8b

    # Add OpenRouter model with custom settings
    ./agent_model.py add --alias openrouter_deepseek --provider openrouter \\
        --model deepseek/deepseek-r1 --timeout 600 --temperature 0.7

    # Set an alias as primary LLM
    ./agent_model.py set --alias qwen_local --as primary

    # List all aliases
    ./agent_model.py ls

    # Show details of an alias
    ./agent_model.py show --alias qwen_local

    # Delete an alias
    ./agent_model.py delete --alias openrouter_deepseek

Author: Agentic-RAG Development Team
Version: 1.0.0
"""

import argparse
import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configuration
CONFIG_DIR = Path(__file__).parent / "config"
ALIASES_FILE = CONFIG_DIR / "model_aliases.json"
LLM_CONFIG_FILE = CONFIG_DIR / "llm_config.yaml"

# Provider defaults
PROVIDER_DEFAULTS = {
    "ollama": {
        "base_url": "http://127.0.0.1:11434",
        "timeout": 600,
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": True
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "timeout": 120,
        "temperature": 0.1,
        "max_tokens": 2048,
        "stream": True
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 600,
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": True,
        "headers": {
            "HTTP-Referer": "${OPENROUTER_SITE_URL}",
            "X-Title": "${OPENROUTER_SITE_NAME}"
        }
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "timeout": 300,
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": True
    }
}

# API key environment variable mappings
API_KEY_ENV_VARS = {
    "ollama": None,  # Ollama doesn't need API key
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "qwen": "DASHSCOPE_API_KEY"
}


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ModelAliasManager:
    """Manages model aliases and configurations"""

    def __init__(self):
        self.aliases_file = ALIASES_FILE
        self.llm_config_file = LLM_CONFIG_FILE
        self.aliases = self._load_aliases()

    def _load_aliases(self) -> Dict[str, Any]:
        """Load model aliases from JSON file"""
        if not self.aliases_file.exists():
            return {}

        try:
            with open(self.aliases_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"{Colors.FAIL}Error loading aliases file: {e}{Colors.ENDC}")
            return {}

    def _save_aliases(self):
        """Save model aliases to JSON file"""
        self.aliases_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.aliases_file, 'w') as f:
            json.dump(self.aliases, f, indent=2)
        print(f"{Colors.OKGREEN}✓ Aliases saved to {self.aliases_file}{Colors.ENDC}")

    def _load_llm_config(self) -> Dict[str, Any]:
        """Load LLM configuration YAML"""
        if not self.llm_config_file.exists():
            print(f"{Colors.FAIL}Error: LLM config file not found: {self.llm_config_file}{Colors.ENDC}")
            sys.exit(1)

        with open(self.llm_config_file, 'r') as f:
            return yaml.safe_load(f)

    def _save_llm_config(self, config: Dict[str, Any]):
        """Save LLM configuration YAML"""
        with open(self.llm_config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"{Colors.OKGREEN}✓ LLM config updated: {self.llm_config_file}{Colors.ENDC}")

    def list_aliases(self):
        """List all model aliases"""
        if not self.aliases:
            print(f"{Colors.WARNING}No model aliases configured.{Colors.ENDC}")
            print(f"Use '{Colors.BOLD}./agent_model.py add{Colors.ENDC}' to create your first alias.")
            return

        # Load current config to show active models
        llm_config = self._load_llm_config()
        active_primary = llm_config.get('llm', {}).get('primary', {})
        active_tool = llm_config.get('llm', {}).get('tool_calling', {})
        active_arb = llm_config.get('arbitrator', {})

        print(f"\n{Colors.HEADER}{Colors.BOLD}Model Aliases{Colors.ENDC}")
        print("=" * 80)

        for alias, config in sorted(self.aliases.items()):
            # Check if this alias is active
            active_roles = []
            if (active_primary.get('type') == config.get('provider') and
                active_primary.get('config', {}).get('model') == config.get('model')):
                active_roles.append(f"{Colors.OKGREEN}PRIMARY{Colors.ENDC}")

            if (active_tool.get('type') == config.get('provider') and
                active_tool.get('config', {}).get('model') == config.get('model')):
                active_roles.append(f"{Colors.OKCYAN}TOOL_CALLING{Colors.ENDC}")

            if (active_arb.get('type') == config.get('provider') and
                active_arb.get('config', {}).get('model') == config.get('model')):
                active_roles.append(f"{Colors.OKBLUE}ARBITRATOR{Colors.ENDC}")

            status = f" [{', '.join(active_roles)}]" if active_roles else ""

            print(f"\n{Colors.BOLD}{alias}{Colors.ENDC}{status}")
            print(f"  Provider:    {config.get('provider')}")
            print(f"  Model:       {config.get('model')}")
            print(f"  Timeout:     {config.get('timeout')}s")
            print(f"  Temperature: {config.get('temperature')}")
            print(f"  Max Tokens:  {config.get('max_tokens')}")
            if config.get('description'):
                print(f"  Description: {config.get('description')}")
            if config.get('created_at'):
                print(f"  Created:     {config.get('created_at')}")

        print()

    def add_alias(self, alias: str, provider: str, model: str,
                  timeout: Optional[int] = None,
                  temperature: Optional[float] = None,
                  max_tokens: Optional[int] = None,
                  context_window: Optional[int] = None,
                  think: Optional[bool] = None,
                  no_think: Optional[bool] = None,
                  description: Optional[str] = None):
        """Add a new model alias"""

        # Validate provider
        provider = provider.lower()
        if provider not in PROVIDER_DEFAULTS:
            print(f"{Colors.FAIL}Error: Unknown provider '{provider}'{Colors.ENDC}")
            print(f"Supported providers: {', '.join(PROVIDER_DEFAULTS.keys())}")
            sys.exit(1)

        # Check if alias already exists
        if alias in self.aliases:
            print(f"{Colors.FAIL}Error: Alias '{alias}' already exists.{Colors.ENDC}")
            print(f"Use '{Colors.BOLD}./agent_model.py update --alias {alias}{Colors.ENDC}' to modify it.")
            sys.exit(1)

        # Get defaults for provider
        defaults = PROVIDER_DEFAULTS[provider].copy()

        # Build configuration
        config = {
            "provider": provider,
            "model": model,
            "base_url": defaults.get("base_url"),
            "timeout": timeout if timeout is not None else defaults.get("timeout"),
            "temperature": temperature if temperature is not None else defaults.get("temperature"),
            "max_tokens": max_tokens if max_tokens is not None else defaults.get("max_tokens"),
            "stream": defaults.get("stream", True),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        if context_window:
            config["context_window_size"] = context_window

        # Handle think parameter (for Ollama reasoning models)
        if think:
            config["think"] = True
        elif no_think:
            config["think"] = False

        if description:
            config["description"] = description

        # Add API key reference if needed
        api_key_var = API_KEY_ENV_VARS.get(provider)
        if api_key_var:
            config["api_key"] = f"${{{api_key_var}}}"

        # Add provider-specific settings
        if provider == "openrouter":
            config["headers"] = defaults.get("headers", {})

        # Save alias
        self.aliases[alias] = config
        self._save_aliases()

        print(f"\n{Colors.OKGREEN}✓ Created model alias '{alias}'{Colors.ENDC}")
        print(f"\nTo use this alias:")
        print(f"  {Colors.BOLD}./agent_model.py set --alias {alias} --as primary{Colors.ENDC}")

    def update_alias(self, alias: str, **kwargs):
        """Update an existing model alias"""
        if alias not in self.aliases:
            print(f"{Colors.FAIL}Error: Alias '{alias}' not found.{Colors.ENDC}")
            print(f"Use '{Colors.BOLD}./agent_model.py ls{Colors.ENDC}' to see available aliases.")
            sys.exit(1)

        # Update fields
        config = self.aliases[alias]
        updated = False

        for key, value in kwargs.items():
            if value is not None and key in ['model', 'timeout', 'temperature', 'max_tokens',
                                              'context_window', 'description']:
                if key == 'context_window':
                    config['context_window_size'] = value
                else:
                    config[key] = value
                updated = True

        # Handle think parameter separately
        if 'think' in kwargs and kwargs['think']:
            config['think'] = True
            updated = True
        elif 'no_think' in kwargs and kwargs['no_think']:
            config['think'] = False
            updated = True

        if updated:
            config['updated_at'] = datetime.now().isoformat()
            self.aliases[alias] = config
            self._save_aliases()
            print(f"{Colors.OKGREEN}✓ Updated alias '{alias}'{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}No changes made to alias '{alias}'{Colors.ENDC}")

    def delete_alias(self, alias: str, force: bool = False):
        """Delete a model alias"""
        if alias not in self.aliases:
            print(f"{Colors.FAIL}Error: Alias '{alias}' not found.{Colors.ENDC}")
            sys.exit(1)

        # Check if alias is currently in use
        llm_config = self._load_llm_config()
        config = self.aliases[alias]

        in_use = []
        if (llm_config.get('llm', {}).get('primary', {}).get('type') == config.get('provider') and
            llm_config.get('llm', {}).get('primary', {}).get('config', {}).get('model') == config.get('model')):
            in_use.append('primary')

        if (llm_config.get('llm', {}).get('tool_calling', {}).get('type') == config.get('provider') and
            llm_config.get('llm', {}).get('tool_calling', {}).get('config', {}).get('model') == config.get('model')):
            in_use.append('tool_calling')

        if (llm_config.get('arbitrator', {}).get('type') == config.get('provider') and
            llm_config.get('arbitrator', {}).get('config', {}).get('model') == config.get('model')):
            in_use.append('arbitrator')

        if in_use and not force:
            print(f"{Colors.WARNING}Warning: Alias '{alias}' is currently active for: {', '.join(in_use)}{Colors.ENDC}")
            print(f"Use --force to delete anyway.")
            sys.exit(1)

        del self.aliases[alias]
        self._save_aliases()
        print(f"{Colors.OKGREEN}✓ Deleted alias '{alias}'{Colors.ENDC}")

    def show_alias(self, alias: str):
        """Show detailed information about an alias"""
        if alias not in self.aliases:
            print(f"{Colors.FAIL}Error: Alias '{alias}' not found.{Colors.ENDC}")
            sys.exit(1)

        config = self.aliases[alias]

        print(f"\n{Colors.HEADER}{Colors.BOLD}Alias: {alias}{Colors.ENDC}")
        print("=" * 80)

        for key, value in sorted(config.items()):
            print(f"{key:20s}: {value}")

        print()

    def set_alias(self, alias: str, role: str):
        """Set an alias as primary, tool_calling, or arbitrator"""
        if alias not in self.aliases:
            print(f"{Colors.FAIL}Error: Alias '{alias}' not found.{Colors.ENDC}")
            sys.exit(1)

        role = role.lower()
        if role not in ['primary', 'tool_calling', 'arbitrator']:
            print(f"{Colors.FAIL}Error: Invalid role '{role}'{Colors.ENDC}")
            print("Valid roles: primary, tool_calling, arbitrator")
            sys.exit(1)

        # Load current config
        llm_config = self._load_llm_config()
        alias_config = self.aliases[alias]

        # Build new configuration section
        new_config = {
            "type": alias_config["provider"],
            "config": {
                "model": alias_config["model"],
                "timeout": alias_config["timeout"],
                "temperature": alias_config["temperature"],
                "max_tokens": alias_config["max_tokens"],
                "stream": alias_config.get("stream", True)
            }
        }

        # Add context_window_size if present
        if "context_window_size" in alias_config:
            new_config["config"]["context_window_size"] = alias_config["context_window_size"]

        # Add provider-specific settings
        if alias_config["provider"] in ["openai", "openrouter", "qwen"]:
            new_config["config"]["base_url"] = alias_config["base_url"]
            if "api_key" in alias_config:
                new_config["config"]["api_key"] = alias_config["api_key"]

        if alias_config["provider"] == "openrouter" and "headers" in alias_config:
            new_config["config"]["headers"] = alias_config["headers"]

        # Add think parameter if present (for Ollama reasoning models)
        if "think" in alias_config:
            new_config["config"]["think"] = alias_config["think"]

        # Update appropriate section
        if role == "arbitrator":
            llm_config["arbitrator"] = new_config
        else:
            if "llm" not in llm_config:
                llm_config["llm"] = {}
            llm_config["llm"][role] = new_config

        # Save updated config
        self._save_llm_config(llm_config)

        print(f"{Colors.OKGREEN}✓ Set '{alias}' as {role.upper()} LLM{Colors.ENDC}")
        print(f"\nCurrent {role} configuration:")
        print(f"  Provider: {alias_config['provider']}")
        print(f"  Model:    {alias_config['model']}")

    def show_status(self):
        """Show current active models"""
        llm_config = self._load_llm_config()

        print(f"\n{Colors.HEADER}{Colors.BOLD}Current Active Models{Colors.ENDC}")
        print("=" * 80)

        # Primary
        primary = llm_config.get('llm', {}).get('primary', {})
        print(f"\n{Colors.OKGREEN}PRIMARY:{Colors.ENDC}")
        print(f"  Provider: {primary.get('type', 'Not set')}")
        print(f"  Model:    {primary.get('config', {}).get('model', 'Not set')}")

        # Tool Calling
        tool = llm_config.get('llm', {}).get('tool_calling', {})
        print(f"\n{Colors.OKCYAN}TOOL_CALLING:{Colors.ENDC}")
        print(f"  Provider: {tool.get('type', 'Not set')}")
        print(f"  Model:    {tool.get('config', {}).get('model', 'Not set')}")

        # Arbitrator
        arb = llm_config.get('arbitrator', {})
        print(f"\n{Colors.OKBLUE}ARBITRATOR:{Colors.ENDC}")
        print(f"  Provider: {arb.get('type', 'Not set')}")
        print(f"  Model:    {arb.get('config', {}).get('model', 'Not set')}")

        print()


def main():
    parser = argparse.ArgumentParser(
        description="Agent Model Configuration CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ls
  %(prog)s add --alias qwen_local --provider ollama --model qwen3:8b
  %(prog)s set --alias qwen_local --as primary
  %(prog)s show --alias qwen_local
  %(prog)s delete --alias qwen_local
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    subparsers.add_parser('ls', help='List all model aliases')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new model alias')
    add_parser.add_argument('--alias', required=True, help='Alias name')
    add_parser.add_argument('--provider', required=True,
                           choices=['ollama', 'openai', 'openrouter', 'qwen'],
                           help='LLM provider')
    add_parser.add_argument('--model', required=True, help='Model name')
    add_parser.add_argument('--timeout', type=int, help='Timeout in seconds')
    add_parser.add_argument('--temperature', type=float, help='Temperature (0.0-2.0)')
    add_parser.add_argument('--max-tokens', type=int, help='Max tokens to generate')
    add_parser.add_argument('--context-window', type=int, help='Context window size')
    add_parser.add_argument('--think', action='store_true', help='Enable think mode (Ollama reasoning models)')
    add_parser.add_argument('--no-think', action='store_true', help='Disable think mode (Ollama reasoning models)')
    add_parser.add_argument('--description', help='Description of this alias')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update an existing alias')
    update_parser.add_argument('--alias', required=True, help='Alias name')
    update_parser.add_argument('--model', help='New model name')
    update_parser.add_argument('--timeout', type=int, help='New timeout')
    update_parser.add_argument('--temperature', type=float, help='New temperature')
    update_parser.add_argument('--max-tokens', type=int, help='New max tokens')
    update_parser.add_argument('--context-window', type=int, help='New context window')
    update_parser.add_argument('--think', action='store_true', help='Enable think mode')
    update_parser.add_argument('--no-think', action='store_true', help='Disable think mode')
    update_parser.add_argument('--description', help='New description')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a model alias')
    delete_parser.add_argument('--alias', required=True, help='Alias name to delete')
    delete_parser.add_argument('--force', action='store_true',
                              help='Force delete even if in use')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show alias details')
    show_parser.add_argument('--alias', required=True, help='Alias name')

    # Set command
    set_parser = subparsers.add_parser('set', help='Set an alias as primary/tool_calling/arbitrator')
    set_parser.add_argument('--alias', required=True, help='Alias name')
    set_parser.add_argument('--as', dest='role', required=True,
                           choices=['primary', 'tool_calling', 'arbitrator'],
                           help='Role to assign')

    # Status command
    subparsers.add_parser('status', help='Show current active models')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize manager
    manager = ModelAliasManager()

    # Execute command
    try:
        if args.command == 'ls':
            manager.list_aliases()

        elif args.command == 'add':
            manager.add_alias(
                alias=args.alias,
                provider=args.provider,
                model=args.model,
                timeout=args.timeout,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                context_window=args.context_window,
                think=args.think,
                no_think=args.no_think,
                description=args.description
            )

        elif args.command == 'update':
            manager.update_alias(
                alias=args.alias,
                model=args.model,
                timeout=args.timeout,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                context_window=args.context_window,
                think=args.think,
                no_think=args.no_think,
                description=args.description
            )

        elif args.command == 'delete':
            manager.delete_alias(args.alias, force=args.force)

        elif args.command == 'show':
            manager.show_alias(args.alias)

        elif args.command == 'set':
            manager.set_alias(args.alias, args.role)

        elif args.command == 'status':
            manager.show_status()

    except Exception as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
