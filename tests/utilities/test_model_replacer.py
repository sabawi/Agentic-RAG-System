#!/usr/bin/env python3
"""
Test Model Replacer - Replace Local Ollama Models with Fast Cloud Models
=========================================================================

Replaces heavy local Ollama models with fast cloud-based models for testing:
- qwen3:8b → deepseek-v3.1:671b-cloud (Ollama cloud)
- qwen3:4b → deepseek-v3.1:671b-cloud (Ollama cloud)
- llama3.2:3b → deepseek-v3.1:671b-cloud (Ollama cloud)

Benefits:
- Faster response times (cloud-based model)
- No local GPU/memory constraints
- Consistent performance
- No model loading delays

Usage:
    python test_model_replacer.py --replace   # Replace models in tests
    python test_model_replacer.py --restore   # Restore original models
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class TestModelReplacer:
    """Replace local ollama models with fast cloud models in test files."""

    # Model replacement mapping: local → cloud
    MODEL_REPLACEMENTS = {
        'qwen3:8b': 'deepseek-v3.1:671b-cloud',
        'qwen3:4b': 'deepseek-v3.1:671b-cloud',
        'llama3.2:3b': 'deepseek-v3.1:671b-cloud',
        'llama3.2:1b': 'deepseek-v3.1:671b-cloud',
    }

    def __init__(self, tests_dir: str = '/home/sabawi/Development/flaskserver/tests'):
        self.tests_dir = Path(tests_dir)
        self.replacements_made: List[Tuple[str, int]] = []

    def find_test_files_with_models(self) -> List[Path]:
        """Find all test files that use ollama models."""
        test_files = []

        for pattern in ['qwen3:', 'llama3.2:', 'llama3.3:']:
            result = os.popen(
                f'grep -l "{pattern}" {self.tests_dir}/**/*.py 2>/dev/null'
            ).read().strip()

            if result:
                for file_path in result.split('\n'):
                    file_path = file_path.strip()
                    if file_path and file_path not in [str(f) for f in test_files]:
                        test_files.append(Path(file_path))

        return sorted(test_files)

    def replace_models_in_file(self, file_path: Path) -> int:
        """Replace ollama models with cloud models in a single file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            original_content = content
            replacements_in_file = 0

            # Replace each model
            for local_model, cloud_model in self.MODEL_REPLACEMENTS.items():
                # Match model in various formats
                patterns = [
                    (f'"model": "{local_model}"', f'"model": "{cloud_model}"'),
                    (f"'model': '{local_model}'", f"'model': '{cloud_model}'"),
                    (f'model="{local_model}"', f'model="{cloud_model}"'),
                    (f"model='{local_model}'", f"model='{cloud_model}'"),
                ]

                for old, new in patterns:
                    if old in content:
                        content = content.replace(old, new)
                        replacements_in_file += content.count(new) - original_content.count(new)

            # Only write if changes were made
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)

                return replacements_in_file

            return 0

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return 0

    def replace_all_models(self) -> Dict[str, int]:
        """Replace models in all test files."""
        print("🔄 Replacing Local Ollama Models with Fast Cloud Models")
        print("=" * 70)
        print()
        print("Model Replacements:")
        for local, cloud in self.MODEL_REPLACEMENTS.items():
            print(f"  {local} → {cloud}")
        print()

        test_files = self.find_test_files_with_models()

        if not test_files:
            print("ℹ️  No test files found with ollama models")
            return {}

        print(f"📁 Found {len(test_files)} test files with ollama models\n")

        results = {}
        total_replacements = 0

        for file_path in test_files:
            rel_path = file_path.relative_to(self.tests_dir)
            replacements = self.replace_models_in_file(file_path)

            if replacements > 0:
                results[str(rel_path)] = replacements
                total_replacements += replacements
                print(f"✅ {rel_path}: {replacements} replacement(s)")
            else:
                print(f"⏭️  {rel_path}: No changes needed")

        print()
        print("=" * 70)
        print(f"✅ Replaced {total_replacements} model references in {len(results)} files")
        print("=" * 70)

        return results

    def create_backup(self):
        """Create backup of test files before replacement."""
        print("💾 Creating backup...")
        # Simple backup using git
        os.system(f'cd {self.tests_dir} && git stash push -m "Test model replacements backup"')

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Replace test models')
    parser.add_argument('--replace', action='store_true', help='Replace ollama models with cloud models')
    parser.add_argument('--restore', action='store_true', help='Restore original models from git')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be replaced')

    args = parser.parse_args()

    replacer = TestModelReplacer()

    if args.restore:
        print("🔄 Restoring original models...")
        os.system('cd /home/sabawi/Development/flaskserver && git checkout tests/')
        print("✅ Restored!")
    elif args.dry_run:
        test_files = replacer.find_test_files_with_models()
        print(f"Would modify {len(test_files)} files:")
        for f in test_files:
            print(f"  - {f.relative_to(replacer.tests_dir)}")
    elif args.replace:
        results = replacer.replace_all_models()
        if results:
            print("\n💡 To restore original models: python test_model_replacer.py --restore")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
