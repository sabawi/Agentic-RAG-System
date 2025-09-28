#!/usr/bin/env python3
"""
Configuration Compliance Checker
Verifies project follows PROJECT_CONFIGURATION_DIRECTIVE.md

USAGE: python tools/check_config_compliance.py
"""

import os
import re
import sys
from pathlib import Path

def check_hardcoded_values():
    """Check for hardcoded configuration values in Python files"""
    print("🔍 Checking for hardcoded configuration values...")

    violations = []
    project_root = Path(__file__).parent.parent

    # Patterns that indicate hardcoded config
    forbidden_patterns = [
        (r'DEFAULT_\w+\s*=', 'Hardcoded DEFAULT_ constants'),
        (r'FALLBACK_\w+\s*=', 'Hardcoded FALLBACK_ constants'),
        (r'localhost["\']?\s*[,\)]', 'Hardcoded localhost'),
        (r'127\.0\.0\.1', 'Hardcoded IP address'),
        (r'11434', 'Hardcoded port 11434'),
        (r'qwen3:8b["\']', 'Hardcoded model name'),
        (r'llama3\.\d+:\d+b["\']', 'Hardcoded model name'),
        (r'3600|8192', 'Hardcoded timeout/size values'),
    ]

    # Files to check - focus on main application code
    for py_file in project_root.rglob("*.py"):
        # Skip certain directories and test files (tests are allowed some hardcoded values)
        if any(skip in str(py_file) for skip in ['venv', '__pycache__', '.git', 'archive', 'tools/check_config_compliance.py', 'tests/', 'test_']):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern, description in forbidden_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append({
                            'file': str(py_file.relative_to(project_root)),
                            'line': line_num,
                            'content': line.strip(),
                            'violation': description
                        })
        except Exception as e:
            print(f"⚠️  Could not read {py_file}: {e}")

    return violations

def check_env_file():
    """Check .env file contains only secrets"""
    print("🔍 Checking .env file compliance...")

    violations = []
    env_file = Path(__file__).parent.parent / '.env'

    if not env_file.exists():
        return violations

    try:
        with open(env_file, 'r') as f:
            content = f.read()

        # Forbidden patterns in .env (should only contain secrets)
        forbidden_env_patterns = [
            (r'MODEL\s*=', 'Model names should be in llm_config.yaml'),
            (r'URL\s*=', 'URLs should be in llm_config.yaml'),
            (r'TIMEOUT\s*=', 'Timeouts should be in llm_config.yaml'),
            (r'PORT\s*=', 'Ports should be in llm_config.yaml'),
        ]

        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if line and not line.startswith('#'):
                for pattern, description in forbidden_env_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append({
                            'file': '.env',
                            'line': line_num,
                            'content': line,
                            'violation': description
                        })
    except Exception as e:
        print(f"⚠️  Could not read .env: {e}")

    return violations

def check_constants_files():
    """Check for eliminated constants files"""
    print("🔍 Checking for eliminated constants files...")

    violations = []
    project_root = Path(__file__).parent.parent

    # Files that should not exist
    forbidden_files = [
        'config/llm_constants.py',
        'constants.py',
        'config_constants.py'
    ]

    for forbidden_file in forbidden_files:
        file_path = project_root / forbidden_file
        if file_path.exists():
            violations.append({
                'file': forbidden_file,
                'violation': 'Constants file should be eliminated'
            })

    return violations

def main():
    """Run all compliance checks"""
    print("🚨 PROJECT CONFIGURATION COMPLIANCE CHECK")
    print("=" * 50)
    print("Enforcing PROJECT_CONFIGURATION_DIRECTIVE.md")
    print()

    all_violations = []

    # Run all checks
    all_violations.extend(check_hardcoded_values())
    all_violations.extend(check_env_file())
    all_violations.extend(check_constants_files())

    # Report results
    if all_violations:
        print("❌ CONFIGURATION VIOLATIONS DETECTED:")
        print("=" * 50)

        for violation in all_violations:
            print(f"🚫 {violation['file']}")
            if 'line' in violation:
                print(f"   Line {violation['line']}: {violation['content']}")
            print(f"   Issue: {violation['violation']}")
            print()

        print(f"Total violations: {len(all_violations)}")
        print("\n📋 ACTION REQUIRED:")
        print("1. Move configuration values to config/llm_config.yaml")
        print("2. Remove hardcoded fallbacks")
        print("3. Keep only secrets in .env file")
        print("4. Read docs/PROJECT_CONFIGURATION_DIRECTIVE.md")

        return 1
    else:
        print("✅ CONFIGURATION COMPLIANCE: PASSED")
        print("All configuration rules are being followed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())