# 🔍 Hardcoded Path Detection & Fix Strategy

## **🚨 CRITICAL ISSUE IDENTIFICATION**

During project reorganization, scripts may fail due to hardcoded paths that become invalid when files are moved. This strategy provides comprehensive detection and fixing procedures.

---

## **📊 DETECTION METHODOLOGY**

### **Phase 1: Automated Path Scanning**

#### **🔍 Pattern-Based Detection**
```bash
# Detect absolute hardcoded paths
rg -n "\/home\/sabawi\/Development\/flaskserver\/" --type py --type sh --type yaml --type md

# Detect relative path patterns that might break
rg -n "(\.\/|\.\.\/)?[a-zA-Z_][a-zA-Z0-9_]*\/[a-zA-Z_]" --type py --type sh

# Detect import statements with hardcoded paths
rg -n "sys\.path\.(append|insert)" --type py

# Detect file operations with potential hardcoded paths
rg -n "(open\(|with open\(|Path\(|pathlib\.|os\.path\.)" --type py -A 2 -B 2
```

#### **🔍 Critical File Types to Scan**
```bash
# Python files - most likely to have path issues
find . -name "*.py" -not -path "./venv/*" -exec echo "Scanning: {}" \;

# Shell scripts - often contain hardcoded paths
find . -name "*.sh" -exec echo "Scanning: {}" \;

# Configuration files
find . -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.cfg"

# Documentation with embedded paths
find . -name "*.md" -exec grep -l "/home/sabawi\|\./" {} \;
```

### **Phase 2: Manual Code Review**

#### **🎯 High-Risk Patterns**
```python
# RISKY: Absolute paths
"/home/sabawi/Development/flaskserver/user_tools/"
"./sandbox_workspace/"

# RISKY: Relative imports without proper base
sys.path.append("../user_tools")
from user_tools import sandboxed_executor

# RISKY: File operations with hardcoded paths
open("./config/llm_config.yaml")
Path("user_tools/sandboxed_executor.py")

# RISKY: Subprocess calls with path assumptions
subprocess.run(["python", "./scripts/test.py"])
```

#### **✅ SAFE: Patterns to Preserve**
```python
# SAFE: Dynamic path resolution
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "llm_config.yaml")

# SAFE: Relative to current working directory
os.getcwd()
pathlib.Path.cwd()

# SAFE: Environment-based paths
os.environ.get("FLASK_SERVER_ROOT", "/default/path")
```

---

## **🛠️ AUTOMATED DETECTION SCRIPT**

### **Path Scanner Tool**
```python
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
        'sys_path_modifications': r'sys\.path\.(append|insert)\(',
        'hardcoded_file_opens': r'(open\(|with open\()[\'"]/[^\'"]*[\'"]',
        'subprocess_with_paths': r'subprocess\.(run|call|Popen)\([^\)]*[\'"]\./[^\'"]*[\'"]',
        'import_from_relative': r'from \.[a-zA-Z_]+ import',
    }
    
    # File extensions to scan
    extensions = ['*.py', '*.sh', '*.yaml', '*.yml', '*.json', '*.md', '*.cfg']
    
    results = {}
    
    for ext in extensions:
        files = glob.glob(f"{root_dir}/**/{ext}", recursive=True)
        
        for file_path in files:
            # Skip virtual environments and git directories
            if 'venv' in file_path or '.git' in file_path:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                file_issues = []
                
                for line_num, line in enumerate(lines, 1):
                    for pattern_name, pattern in patterns.items():
                        if re.search(pattern, line):
                            file_issues.append((line_num, f"{pattern_name}: {line.strip()}"))
                
                if file_issues:
                    results[file_path] = file_issues
                    
            except (UnicodeDecodeError, IOError) as e:
                print(f"Error reading {file_path}: {e}")
    
    return results

def generate_fix_report(scan_results: Dict[str, List[Tuple[int, str]]]) -> str:
    """Generate a detailed fix report"""
    
    report = ["# Hardcoded Path Detection Report\n"]
    report.append(f"## Summary: {len(scan_results)} files with potential issues\n")
    
    for file_path, issues in scan_results.items():
        report.append(f"### {file_path}")
        report.append(f"**{len(issues)} issues found:**")
        
        for line_num, description in issues:
            report.append(f"- Line {line_num}: {description}")
        
        report.append("")
    
    return "\n".join(report)

if __name__ == "__main__":
    root_directory = "/home/sabawi/Development/flaskserver"
    results = scan_for_hardcoded_paths(root_directory)
    
    report = generate_fix_report(results)
    
    # Save report
    with open("hardcoded_path_detection_report.md", "w") as f:
        f.write(report)
    
    print(f"Detection complete. Found issues in {len(results)} files.")
    print("Report saved to: hardcoded_path_detection_report.md")
```

---

## **🔧 FIXING STRATEGY**

### **Critical Files Requiring Manual Updates**

#### **1. fastapi_server_complete.py**
```python
# BEFORE: Hardcoded paths
CONFIG_PATH = "./config/llm_config.yaml"
TOOL_MODULES_DIR = "./user_tools/"

# AFTER: Dynamic resolution
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "llm_config.yaml") 
TOOL_MODULES_DIR = os.path.join(BASE_DIR, "user_tools")
```

#### **2. Shell Scripts (start_complete.sh, stop_complete.sh)**
```bash
# BEFORE: Relative path assumptions
cd /home/sabawi/Development/flaskserver
python fastapi_server_complete.py

# AFTER: Script-relative paths
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"
python fastapi_server_complete.py
```

#### **3. Configuration Files**
```yaml
# BEFORE: Hardcoded paths in config
sandbox_root: "/home/sabawi/Development/flaskserver/sandbox_workspace"
logs_dir: "./logs"

# AFTER: Relative or environment-based
sandbox_root: "${PROJECT_ROOT}/sandbox_workspace"
logs_dir: "${PROJECT_ROOT}/logs"
```

#### **4. Import Statements**
```python
# BEFORE: Problematic imports
sys.path.append("./user_tools")
from user_tools.sandboxed_executor import SandboxedExecutor

# AFTER: Proper package imports
from src.user_tools.sandboxed_executor import SandboxedExecutor
```

---

## **🧪 VALIDATION TESTING STRATEGY**

### **Pre-Reorganization Testing**
```bash
# 1. Create comprehensive test script
python test_all_paths.py --mode=pre_reorganization

# 2. Capture baseline functionality
./run_all_regression_tests.sh > baseline_results.txt

# 3. Test critical workflows
curl -X POST http://localhost:5000/llama3_1b/stream -d '{"prompt": "test file creation"}'
```

### **Post-Reorganization Testing**
```bash
# 1. Run automated path verification
python verify_reorganization_paths.py

# 2. Test all updated paths
python test_all_paths.py --mode=post_reorganization

# 3. Compare results with baseline
diff baseline_results.txt post_reorganization_results.txt

# 4. Run full regression suite
./run_arbitrator_regression_test.sh
```

### **Critical Test Cases**
```python
# Test file creation in new locations
test_sandbox_file_creation()
test_log_file_generation()  
test_config_file_access()
test_user_tools_import()

# Test script execution from new locations
test_start_stop_scripts()
test_llm_config_tool()
test_email_attachment_generation()

# Test tool calling with new paths
test_sandboxed_executor_paths()
test_document_search_paths()
test_file_operations()
```

---

## **🛡️ ROLLBACK & SAFETY MECHANISMS**

### **Pre-Reorganization Backup**
```bash
# Create complete backup before any changes
tar -czf flaskserver_backup_$(date +%Y%m%d_%H%M%S).tar.gz .

# Git safety net
git add -A
git commit -m "🛡️ PRE-REORGANIZATION: Complete backup before structural changes"
git tag pre-reorganization-backup
```

### **Incremental Migration Strategy**
```bash
# Phase 1: Create new directory structure (no file moves)
mkdir -p src/{core,user_tools,utils}
mkdir -p tests/{unit,integration,regression}
mkdir -p docs/{architecture,api}

# Phase 2: Update path references in files (no moves)
python update_path_references.py --dry-run
python update_path_references.py --apply

# Phase 3: Test with updated references but original locations
./test_updated_references.sh

# Phase 4: Actually move files
python move_files_to_new_structure.py

# Phase 5: Final validation
./validate_complete_reorganization.sh
```

### **Emergency Rollback Procedure**
```bash
# If ANY issues detected during reorganization:

# 1. Stop server immediately
./stop_complete.sh

# 2. Restore from backup
rm -rf ./*
tar -xzf flaskserver_backup_YYYYMMDD_HHMMSS.tar.gz

# 3. Reset git state
git reset --hard pre-reorganization-backup

# 4. Restart with original structure
./start_complete.sh

# 5. Verify system works
curl http://localhost:5000/health
```

---

## **⚡ EXECUTION CHECKLIST**

### **Before Reorganization**
- [ ] Run automated path detection script
- [ ] Manually review all flagged files  
- [ ] Create comprehensive backup
- [ ] Test baseline functionality
- [ ] Commit pre-reorganization state to git
- [ ] Prepare rollback procedure

### **During Reorganization**
- [ ] Update path references BEFORE moving files
- [ ] Test each phase incrementally
- [ ] Validate imports work with new structure
- [ ] Check configuration file paths
- [ ] Test shell scripts with new paths
- [ ] Verify all tool modules load correctly

### **After Reorganization**
- [ ] Run complete regression test suite
- [ ] Test Arbitrator system end-to-end
- [ ] Validate email attachment generation
- [ ] Check OpenAI compatibility layer
- [ ] Test all shell scripts and configuration tools
- [ ] Monitor server logs for path-related errors

---

## **🎯 CRITICAL SUCCESS CRITERIA**

**✅ MUST WORK After Reorganization:**
- Server starts without path errors
- All tool imports function correctly
- Configuration files load properly  
- Shell scripts execute from any directory
- Arbitrator regression test passes
- File generation works in new locations
- Email attachments create properly

**🚨 IMMEDIATE ROLLBACK Triggers:**
- Any import failures
- Configuration loading errors
- Tool execution path failures
- Regression test failures
- File generation in wrong locations
- Shell script execution failures

This comprehensive strategy ensures safe project reorganization while maintaining all functionality and providing robust rollback mechanisms for any issues that arise.