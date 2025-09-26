#!/usr/bin/env python3
"""
Version Synchronization Utilities
=================================

Utilities to ensure all configuration files and non-Python files
stay synchronized with the centralized version from version.py.

This module provides functions to update JSON config files, documentation,
and other files that can't directly import the version module.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import version
sys.path.insert(0, str(Path(__file__).parent.parent))
from version import VERSION, get_version_info

def update_logging_config():
    """
    Update the logging configuration file with current version.

    Returns:
        bool: True if updated successfully, False otherwise
    """
    config_path = Path(__file__).parent.parent / "config" / "logging_config.json"

    try:
        # Read current config
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        # Update version and timestamp
        config["version"] = VERSION
        config["last_updated"] = datetime.now().isoformat()

        # Write back to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Updated logging config version to {VERSION}")
        return True

    except Exception as e:
        print(f"❌ Failed to update logging config: {e}")
        return False

def update_all_configs():
    """
    Update all configuration files with current version.

    Returns:
        dict: Results of update operations
    """
    results = {}

    # Update logging config
    results["logging_config"] = update_logging_config()

    return results

def verify_version_consistency():
    """
    Verify that all version references are consistent.

    Returns:
        dict: Verification results
    """
    results = {
        "consistent": True,
        "issues": [],
        "version": VERSION
    }

    # Check logging config
    config_path = Path(__file__).parent.parent / "config" / "logging_config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            if config.get("version") != VERSION:
                results["consistent"] = False
                results["issues"].append(f"logging_config.json has version {config.get('version')}, expected {VERSION}")
        except Exception as e:
            results["issues"].append(f"Failed to check logging_config.json: {e}")

    return results

def get_version_summary():
    """
    Get comprehensive version information for diagnostics.

    Returns:
        dict: Complete version information
    """
    return {
        "version": VERSION,
        "version_info": get_version_info(),
        "files_checked": [
            "config/logging_config.json"
        ],
        "consistency": verify_version_consistency()
    }

if __name__ == "__main__":
    # Command line interface
    import argparse

    parser = argparse.ArgumentParser(description="Version synchronization utilities")
    parser.add_argument("--update", action="store_true", help="Update all config files")
    parser.add_argument("--verify", action="store_true", help="Verify version consistency")
    parser.add_argument("--summary", action="store_true", help="Show version summary")

    args = parser.parse_args()

    if args.update:
        results = update_all_configs()
        print("Update results:", json.dumps(results, indent=2))

    if args.verify:
        results = verify_version_consistency()
        print("Verification results:", json.dumps(results, indent=2))

    if args.summary:
        summary = get_version_summary()
        print("Version summary:", json.dumps(summary, indent=2))

    if not any([args.update, args.verify, args.summary]):
        print(f"Current version: {VERSION}")
        print("Use --help for available commands")