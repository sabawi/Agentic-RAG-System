#!/usr/bin/env python3
"""
Automated Hardcoded Path Fixing Tool
Fixes critical hardcoded paths before project reorganization
"""

import os
import re
import glob
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

class PathFixer:
    def __init__(self, root_dir: str, dry_run: bool = True):
        self.root_dir = root_dir
        self.dry_run = dry_run
        self.fixes_applied = []
        self.backup_dir = f"{root_dir}_backup_{self._get_timestamp()}"
        
    def _get_timestamp(self) -> str:
        """Get timestamp for backup naming"""
        import datetime
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_backup(self) -> bool:
        """Create complete backup before making changes"""
        if self.dry_run:
            print(f"🔍 DRY RUN: Would create backup at {self.backup_dir}")
            return True
            
        try:
            print(f"📦 Creating backup at {self.backup_dir}")
            shutil.copytree(self.root_dir, self.backup_dir, 
                          ignore=shutil.ignore_patterns('.git', '__pycache__', 'venv', '*.pyc'))
            print(f"✅ Backup created successfully")
            return True
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def fix_absolute_paths(self) -> List[Tuple[str, str, str]]:
        """Fix critical absolute path references"""
        
        fixes = []
        absolute_path_pattern = r'/home/sabawi/Development/flaskserver/'
        
        # Files to scan and fix
        extensions = ['*.py', '*.sh', '*.yaml', '*.yml', '*.md', '*.json']
        
        for ext in extensions:
            files = glob.glob(f"{self.root_dir}/**/{ext}", recursive=True)
            
            for file_path in files:
                if any(skip_dir in file_path for skip_dir in ['.git', '__pycache__', 'venv']):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Fix absolute paths based on file type
                    if file_path.endswith('.py'):
                        content = self._fix_python_absolute_paths(content, file_path)
                    elif file_path.endswith('.sh'):
                        content = self._fix_shell_absolute_paths(content, file_path)
                    elif file_path.endswith('.md'):
                        content = self._fix_markdown_absolute_paths(content)
                    elif file_path.endswith(('.yaml', '.yml', '.json')):
                        content = self._fix_config_absolute_paths(content)
                    
                    if content != original_content:
                        rel_path = os.path.relpath(file_path, self.root_dir)
                        fixes.append((rel_path, "absolute_paths", "Updated absolute path references"))
                        
                        if not self.dry_run:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                        else:
                            print(f"🔍 Would fix absolute paths in: {rel_path}")
                
                except Exception as e:
                    print(f"⚠️  Warning: Could not process {file_path}: {e}")
        
        return fixes
    
    def _fix_python_absolute_paths(self, content: str, file_path: str) -> str:
        """Fix absolute paths in Python files"""
        
        # Replace absolute paths with dynamic resolution
        if 'fastapi_server_complete.py' in file_path:
            # For main server file, add BASE_DIR resolution
            if 'BASE_DIR = os.path.dirname' not in content:
                # Add BASE_DIR definition after imports
                import_section = content.find('\nfrom')
                if import_section == -1:
                    import_section = content.find('\nimport')
                
                if import_section != -1:
                    base_dir_code = '''
# 🔧 DYNAMIC PATH RESOLUTION - Added for project reorganization
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
'''
                    insert_pos = content.find('\n\n', import_section)
                    if insert_pos != -1:
                        content = content[:insert_pos] + base_dir_code + content[insert_pos:]
        
        # Replace absolute paths with relative/dynamic paths
        patterns = [
            (r'/home/sabawi/Development/flaskserver/', ''),  # Remove absolute prefix
            (r'"/home/sabawi/Development/flaskserver/([^"]+)"', r'os.path.join(BASE_DIR, "\1")'),
            (r"'/home/sabawi/Development/flaskserver/([^']+)'", r"os.path.join(BASE_DIR, '\1')"),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def _fix_shell_absolute_paths(self, content: str, file_path: str) -> str:
        """Fix absolute paths in shell scripts"""
        
        # Add script directory resolution for shell scripts
        script_dir_code = '''# 🔧 DYNAMIC PATH RESOLUTION - Added for project reorganization
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"
'''
        
        # Check if already has dynamic path resolution
        if 'SCRIPT_DIR=' not in content and 'cd /home/sabawi' in content:
            # Add after shebang
            lines = content.split('\n')
            if lines[0].startswith('#!'):
                lines.insert(1, script_dir_code)
                content = '\n'.join(lines)
        
        # Replace absolute paths
        patterns = [
            (r'cd /home/sabawi/Development/flaskserver', 'cd "$SCRIPT_DIR"'),
            (r'/home/sabawi/Development/flaskserver/', '$SCRIPT_DIR/'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def _fix_markdown_absolute_paths(self, content: str) -> str:
        """Fix absolute paths in markdown documentation"""
        
        # Replace absolute paths with relative references
        patterns = [
            (r'/home/sabawi/Development/flaskserver/([^`\s]+)', r'\1'),
            (r'`/home/sabawi/Development/flaskserver/([^`]+)`', r'`\1`'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def _fix_config_absolute_paths(self, content: str) -> str:
        """Fix absolute paths in configuration files"""
        
        # Replace with environment variable references
        patterns = [
            (r'/home/sabawi/Development/flaskserver/', '${PROJECT_ROOT}/'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def fix_relative_paths(self) -> List[Tuple[str, str, str]]:
        """Fix high-risk relative path references"""
        
        fixes = []
        
        # Common problematic patterns and their fixes
        relative_fixes = {
            # Python files
            '*.py': [
                (r'open\("(\./[^"]+)"\)', r'open(os.path.join(BASE_DIR, "\1"))'),
                (r"open\('(\./[^']+)'\)", r"open(os.path.join(BASE_DIR, '\1'))"),
                (r'Path\("(\./[^"]+)"\)', r'Path(BASE_DIR) / "\1"'),
                (r"Path\('(\./[^']+)'\)", r"Path(BASE_DIR) / '\1'"),
            ],
            # Shell scripts  
            '*.sh': [
                (r'\./([a-zA-Z_][a-zA-Z0-9_]*\.sh)', r'"$SCRIPT_DIR/\1"'),
                (r'python\s+(\./[^\s]+)', r'python "$SCRIPT_DIR/\1"'),
            ]
        }
        
        for file_pattern, pattern_fixes in relative_fixes.items():
            files = glob.glob(f"{self.root_dir}/**/{file_pattern}", recursive=True)
            
            for file_path in files:
                if any(skip_dir in file_path for skip_dir in ['.git', '__pycache__', 'venv']):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    for pattern, replacement in pattern_fixes:
                        content = re.sub(pattern, replacement, content)
                    
                    if content != original_content:
                        rel_path = os.path.relpath(file_path, self.root_dir)
                        fixes.append((rel_path, "relative_paths", "Updated relative path references"))
                        
                        if not self.dry_run:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                        else:
                            print(f"🔍 Would fix relative paths in: {rel_path}")
                
                except Exception as e:
                    print(f"⚠️  Warning: Could not process {file_path}: {e}")
        
        return fixes
    
    def generate_migration_report(self, fixes: List[Tuple[str, str, str]]) -> str:
        """Generate report of all fixes applied"""
        
        report = ["# 🔧 Hardcoded Path Fix Report\n"]
        report.append(f"## 📊 Summary: {len(fixes)} files modified\n")
        
        # Group by fix type
        fix_types = {}
        for file_path, fix_type, description in fixes:
            if fix_type not in fix_types:
                fix_types[fix_type] = []
            fix_types[fix_type].append((file_path, description))
        
        for fix_type, file_fixes in fix_types.items():
            report.append(f"### {fix_type.replace('_', ' ').title()} ({len(file_fixes)} files)")
            for file_path, description in file_fixes:
                report.append(f"- ✅ `{file_path}`: {description}")
            report.append("")
        
        if not self.dry_run:
            report.append(f"## 🛡️ Backup Created: {self.backup_dir}\n")
            report.append("To rollback changes if needed:\n")
            report.append(f"```bash\n")
            report.append(f"rm -rf {self.root_dir}/*\n")
            report.append(f"cp -r {self.backup_dir}/* {self.root_dir}/\n")
            report.append(f"```\n")
        
        return "\n".join(report)
    
    def run_fixes(self) -> bool:
        """Run all path fixes"""
        
        print(f"🔧 Running hardcoded path fixes {'(DRY RUN)' if self.dry_run else '(LIVE)'}")
        
        # Create backup if not dry run
        if not self.dry_run and not self.create_backup():
            return False
        
        all_fixes = []
        
        # Fix absolute paths (critical)
        print("🎯 Fixing absolute paths...")
        absolute_fixes = self.fix_absolute_paths()
        all_fixes.extend(absolute_fixes)
        
        # Fix relative paths (high risk)
        print("🎯 Fixing relative paths...")  
        relative_fixes = self.fix_relative_paths()
        all_fixes.extend(relative_fixes)
        
        # Generate report
        report = self.generate_migration_report(all_fixes)
        report_file = f"path_fix_report_{'dry_run' if self.dry_run else 'applied'}_{self._get_timestamp()}.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"📄 Fix report saved to: {report_file}")
        print(f"✅ Fixed {len(all_fixes)} files total")
        
        if self.dry_run:
            print("🔍 This was a DRY RUN - no files were actually modified")
            print("💡 Run with --apply to apply fixes")
        
        return True

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix hardcoded paths for project reorganization')
    parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry run)')
    parser.add_argument('--root', default='.', help='Root directory to process')
    
    args = parser.parse_args()
    
    root_dir = os.path.abspath(args.root)
    dry_run = not args.apply
    
    print(f"🎯 Processing directory: {root_dir}")
    
    fixer = PathFixer(root_dir, dry_run=dry_run)
    success = fixer.run_fixes()
    
    if not success:
        print("❌ Path fixing failed!")
        return 1
    
    if dry_run:
        print("\n💡 To apply these fixes, run:")
        print("python fix_hardcoded_paths.py --apply")
    else:
        print("\n✅ Path fixes applied successfully!")
        print("🔍 Review the changes and test functionality before proceeding with reorganization")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())