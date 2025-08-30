#!/usr/bin/env python3
"""
Hardcoded Path Detection Tool for Project Reorganization
Scans all files for potentially problematic path references
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Tuple

def scan_for_hardcoded_paths(root_dir: str) -> Dict[str, List[Tuple[int, str]]]:
    """Scan files for hardcoded path patterns"""
    
    # Critical patterns to detect
    patterns = {
        'absolute_project_paths': r'\/home\/sabawi\/Development\/flaskserver\/',
        'relative_dot_paths': r'\.\/[a-zA-Z_][a-zA-Z0-9_\/]*',
        'relative_dotdot_paths': r'\.\.\/[a-zA-Z_][a-zA-Z0-9_\/]*',
        'sys_path_modifications': r'sys\.path\.(append|insert)\(',
        'hardcoded_file_opens': r'(open\(|with open\()[\'"]/[^\'"]*[\'"]',
        'hardcoded_relative_opens': r'(open\(|with open\()[\'"]\./[^\'"]*[\'"]',
        'subprocess_with_paths': r'subprocess\.(run|call|Popen)\([^\)]*[\'"]\./[^\'"]*[\'"]',
        'import_from_relative': r'from \.[a-zA-Z_]+ import',
        'pathlib_paths': r'Path\([\'"]/[^\'"]*[\'"]',
        'pathlib_relative_paths': r'Path\([\'"]\./[^\'"]*[\'"]',
        'os_path_join_hardcoded': r'os\.path\.join\([^\)]*[\'"]/[^\'"]*[\'"]',
        'config_file_refs': r'[\'"](config|user_tools|sandbox_workspace|logs|docs|tests)/',
        'shell_cd_commands': r'cd\s+[/\.]',
        'python_execution_paths': r'python\s+[./]',
    }
    
    # File extensions to scan
    extensions = ['*.py', '*.sh', '*.yaml', '*.yml', '*.json', '*.md', '*.cfg', '*.txt']
    
    results = {}
    total_files_scanned = 0
    
    for ext in extensions:
        files = glob.glob(f"{root_dir}/**/{ext}", recursive=True)
        
        for file_path in files:
            # Skip virtual environments, git directories, and backup files
            if any(skip_dir in file_path for skip_dir in ['venv', '.git', '__pycache__', '.pytest_cache', 'node_modules']):
                continue
                
            total_files_scanned += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                file_issues = []
                
                for line_num, line in enumerate(lines, 1):
                    for pattern_name, pattern in patterns.items():
                        matches = re.findall(pattern, line)
                        if matches:
                            # Clean line for display
                            clean_line = line.strip()[:100] + ('...' if len(line.strip()) > 100 else '')
                            file_issues.append((line_num, f"{pattern_name}: {clean_line}"))
                
                if file_issues:
                    # Make path relative for cleaner display
                    rel_path = os.path.relpath(file_path, root_dir)
                    results[rel_path] = file_issues
                    
            except (UnicodeDecodeError, IOError) as e:
                print(f"Warning: Could not read {file_path}: {e}")
    
    print(f"Scanned {total_files_scanned} files total")
    return results

def categorize_issues(scan_results: Dict[str, List[Tuple[int, str]]]) -> Dict[str, List[str]]:
    """Categorize issues by severity and type"""
    
    categories = {
        'CRITICAL_ABSOLUTE_PATHS': [],
        'HIGH_RISK_RELATIVE_PATHS': [],
        'MEDIUM_RISK_IMPORTS': [],
        'LOW_RISK_DOCUMENTATION': [],
        'SHELL_SCRIPT_PATHS': [],
        'CONFIG_FILE_REFERENCES': []
    }
    
    for file_path, issues in scan_results.items():
        for line_num, description in issues:
            if 'absolute_project_paths' in description:
                categories['CRITICAL_ABSOLUTE_PATHS'].append(f"{file_path}:{line_num}")
            elif any(pattern in description for pattern in ['relative_dot_paths', 'hardcoded_file_opens']):
                categories['HIGH_RISK_RELATIVE_PATHS'].append(f"{file_path}:{line_num}")
            elif any(pattern in description for pattern in ['import_from_relative', 'sys_path_modifications']):
                categories['MEDIUM_RISK_IMPORTS'].append(f"{file_path}:{line_num}")
            elif file_path.endswith('.md') or file_path.endswith('.txt'):
                categories['LOW_RISK_DOCUMENTATION'].append(f"{file_path}:{line_num}")
            elif file_path.endswith('.sh'):
                categories['SHELL_SCRIPT_PATHS'].append(f"{file_path}:{line_num}")
            elif 'config_file_refs' in description:
                categories['CONFIG_FILE_REFERENCES'].append(f"{file_path}:{line_num}")
    
    return categories

def generate_fix_report(scan_results: Dict[str, List[Tuple[int, str]]], categories: Dict[str, List[str]]) -> str:
    """Generate a detailed fix report"""
    
    report = ["# 🔍 Hardcoded Path Detection Report\n"]
    report.append(f"## 📊 Summary: {len(scan_results)} files with potential path issues\n")
    
    # Priority summary
    report.append("## 🚨 Priority Summary")
    for category, files in categories.items():
        if files:
            severity = "🔴 CRITICAL" if "CRITICAL" in category else "🟡 HIGH" if "HIGH" in category else "🟢 MEDIUM" if "MEDIUM" in category else "🔵 LOW"
            report.append(f"- {severity} **{category.replace('_', ' ').title()}**: {len(files)} issues")
    report.append("")
    
    # Detailed file-by-file report
    report.append("## 📋 Detailed Issues by File\n")
    
    for file_path, issues in sorted(scan_results.items()):
        # Determine file severity
        file_severity = "🔴" if any("absolute_project_paths" in desc for _, desc in issues) else "🟡"
        
        report.append(f"### {file_severity} `{file_path}`")
        report.append(f"**{len(issues)} issues found:**\n")
        
        for line_num, description in issues:
            # Clean up description for readability
            pattern_type = description.split(':')[0]
            content = ':'.join(description.split(':')[1:]).strip()
            report.append(f"- **Line {line_num}** `{pattern_type}`: {content}")
        
        report.append("")
    
    # Recommended actions
    report.append("## 🔧 Recommended Fix Actions\n")
    report.append("### 1. CRITICAL - Absolute Paths (Must Fix)")
    if categories['CRITICAL_ABSOLUTE_PATHS']:
        for issue in categories['CRITICAL_ABSOLUTE_PATHS']:
            report.append(f"- [ ] Fix: {issue}")
    else:
        report.append("- ✅ No critical absolute paths found")
    
    report.append("\n### 2. HIGH RISK - Relative Paths (Should Fix)")
    if categories['HIGH_RISK_RELATIVE_PATHS']:
        for issue in categories['HIGH_RISK_RELATIVE_PATHS'][:10]:  # Show first 10
            report.append(f"- [ ] Review: {issue}")
        if len(categories['HIGH_RISK_RELATIVE_PATHS']) > 10:
            report.append(f"- ... and {len(categories['HIGH_RISK_RELATIVE_PATHS']) - 10} more")
    else:
        report.append("- ✅ No high-risk relative paths found")
    
    report.append("\n### 3. SHELL SCRIPTS (Must Fix)")
    if categories['SHELL_SCRIPT_PATHS']:
        for issue in categories['SHELL_SCRIPT_PATHS']:
            report.append(f"- [ ] Update: {issue}")
    else:
        report.append("- ✅ No shell script path issues found")
    
    return "\n".join(report)

def main():
    """Main execution function"""
    
    root_directory = os.path.dirname(os.path.abspath(__file__))
    print(f"🔍 Scanning for hardcoded paths in: {root_directory}")
    
    # Run the scan
    print("⏳ Scanning files...")
    results = scan_for_hardcoded_paths(root_directory)
    
    # Categorize results
    categories = categorize_issues(results)
    
    # Generate report
    report = generate_fix_report(results, categories)
    
    # Save report
    report_file = "hardcoded_path_detection_report.md"
    with open(report_file, "w") as f:
        f.write(report)
    
    # Print summary
    print(f"✅ Detection complete!")
    print(f"📊 Found issues in {len(results)} files")
    print(f"📄 Report saved to: {report_file}")
    
    # Print priority summary
    print(f"\n🚨 PRIORITY SUMMARY:")
    for category, files in categories.items():
        if files:
            count = len(files)
            severity = "🔴 CRITICAL" if "CRITICAL" in category else "🟡 HIGH" if "HIGH" in category else "🟢 MEDIUM"
            print(f"  {severity} {category.replace('_', ' ').title()}: {count} issues")
    
    if categories['CRITICAL_ABSOLUTE_PATHS']:
        print(f"\n⚠️  WARNING: {len(categories['CRITICAL_ABSOLUTE_PATHS'])} CRITICAL absolute paths found - MUST fix before reorganization!")
    
    return len(results) > 0

if __name__ == "__main__":
    import sys
    has_issues = main()
    sys.exit(1 if has_issues else 0)