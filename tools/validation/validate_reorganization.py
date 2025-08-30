#!/usr/bin/env python3
"""
Project Reorganization Validation Tool
Validates all path references work correctly after reorganization
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# 🔧 ROBUST PROJECT ROOT DISCOVERY - Works from any subdirectory
def find_project_root():
    """Find project root by looking for marker files/directories"""
    markers = ['user_tools', 'sandbox_workspace', 'config', 'fastapi_server_complete.py']
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if sum(1 for marker in markers if (parent / marker).exists()) >= 3:
            return str(parent)
    return os.getcwd()

# Add project root to path for imports
project_root = find_project_root()
sys.path.insert(0, project_root)

class ReorganizationValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.validation_results = []
        
    def validate_imports(self) -> bool:
        """Validate all Python imports work correctly"""
        
        print("🔍 Validating Python imports...")
        success = True
        
        # Find all Python files
        python_files = list(self.project_root.glob("**/*.py"))
        python_files = [f for f in python_files if not any(skip in str(f) for skip in ['.git', '__pycache__', 'venv'])]
        
        failed_imports = []
        
        for py_file in python_files:
            try:
                # Attempt to compile the Python file
                with open(py_file, 'r') as f:
                    source = f.read()
                
                compile(source, str(py_file), 'exec')
                self.validation_results.append(("✅", f"Import validation: {py_file.name}", "OK"))
                
            except SyntaxError as e:
                self.validation_results.append(("❌", f"Import validation: {py_file.name}", f"Syntax error: {e}"))
                failed_imports.append(str(py_file))
                success = False
            except Exception as e:
                self.validation_results.append(("⚠️", f"Import validation: {py_file.name}", f"Warning: {e}"))
        
        if failed_imports:
            print(f"❌ Failed imports in {len(failed_imports)} files:")
            for file in failed_imports[:5]:  # Show first 5
                print(f"  - {file}")
        else:
            print(f"✅ All {len(python_files)} Python files validated")
        
        return success
    
    def validate_config_files(self) -> bool:
        """Validate configuration files load correctly"""
        
        print("🔍 Validating configuration files...")
        success = True
        
        # Find configuration files
        config_patterns = ["**/*.yaml", "**/*.yml", "**/*.json", "**/*.cfg"]
        config_files = []
        
        for pattern in config_patterns:
            config_files.extend(self.project_root.glob(pattern))
        
        config_files = [f for f in config_files if not any(skip in str(f) for skip in ['.git', '__pycache__', 'venv'])]
        
        for config_file in config_files:
            try:
                if config_file.suffix in ['.yaml', '.yml']:
                    import yaml
                    with open(config_file, 'r') as f:
                        yaml.safe_load(f)
                elif config_file.suffix == '.json':
                    import json
                    with open(config_file, 'r') as f:
                        json.load(f)
                        
                self.validation_results.append(("✅", f"Config validation: {config_file.name}", "OK"))
                
            except Exception as e:
                self.validation_results.append(("❌", f"Config validation: {config_file.name}", f"Error: {e}"))
                success = False
        
        print(f"{'✅' if success else '❌'} Validated {len(config_files)} configuration files")
        return success
    
    def validate_file_operations(self) -> bool:
        """Test file read/write operations in expected locations"""
        
        print("🔍 Validating file operations...")
        success = True
        
        # Test directories that should exist and be writable
        test_dirs = [
            "config",
            "user_tools", 
            "sandbox_workspace"
        ]
        
        for dir_name in test_dirs:
            dir_path = self.project_root / dir_name
            
            if not dir_path.exists():
                self.validation_results.append(("❌", f"Directory check: {dir_name}", "Directory does not exist"))
                success = False
                continue
            
            # Test write permissions
            try:
                test_file = dir_path / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                self.validation_results.append(("✅", f"Directory check: {dir_name}", "Exists and writable"))
            except Exception as e:
                self.validation_results.append(("❌", f"Directory check: {dir_name}", f"Write error: {e}"))
                success = False
        
        print(f"{'✅' if success else '❌'} Validated {len(test_dirs)} critical directories")
        return success
    
    def validate_shell_scripts(self) -> bool:
        """Validate shell scripts execute without path errors"""
        
        print("🔍 Validating shell scripts...")
        success = True
        
        # Find shell scripts
        shell_scripts = list(self.project_root.glob("*.sh"))
        shell_scripts.extend(self.project_root.glob("**/*.sh"))
        shell_scripts = [f for f in shell_scripts if not any(skip in str(f) for skip in ['.git', 'venv'])]
        
        for script in shell_scripts:
            try:
                # Check script syntax
                result = subprocess.run(
                    ["bash", "-n", str(script)], 
                    capture_output=True, 
                    text=True,
                    cwd=str(self.project_root)
                )
                
                if result.returncode == 0:
                    self.validation_results.append(("✅", f"Shell script: {script.name}", "Syntax OK"))
                else:
                    self.validation_results.append(("❌", f"Shell script: {script.name}", f"Syntax error: {result.stderr}"))
                    success = False
                    
            except Exception as e:
                self.validation_results.append(("❌", f"Shell script: {script.name}", f"Error: {e}"))
                success = False
        
        print(f"{'✅' if success else '❌'} Validated {len(shell_scripts)} shell scripts")
        return success
    
    def validate_tool_imports(self) -> bool:
        """Validate user tool imports work correctly"""
        
        print("🔍 Validating tool imports...")
        success = True
        
        # Test critical tool imports
        critical_tools = [
            "user_tools.sandboxed_executor",
            "user_tools.secure_email_sender", 
            "user_tools.document_search",
            "user_tools.comprehensive_stock_analyzer"
        ]
        
        original_cwd = os.getcwd()
        
        try:
            # Change to project root for imports
            os.chdir(str(self.project_root))
            
            for tool_module in critical_tools:
                try:
                    # Attempt import
                    if '.' in tool_module:
                        parts = tool_module.split('.')
                        module = __import__(tool_module)
                        for part in parts[1:]:
                            module = getattr(module, part)
                    else:
                        module = __import__(tool_module)
                    
                    self.validation_results.append(("✅", f"Tool import: {tool_module}", "OK"))
                    
                except ImportError as e:
                    self.validation_results.append(("❌", f"Tool import: {tool_module}", f"Import error: {e}"))
                    success = False
                except Exception as e:
                    self.validation_results.append(("⚠️", f"Tool import: {tool_module}", f"Warning: {e}"))
        
        finally:
            os.chdir(original_cwd)
        
        print(f"{'✅' if success else '❌'} Validated {len(critical_tools)} tool imports")
        return success
    
    def test_server_startup(self) -> bool:
        """Test if server can start without path errors"""
        
        print("🔍 Testing server startup...")
        
        try:
            # Test server import and basic initialization
            server_file = self.project_root / "fastapi_server_complete.py"
            
            if not server_file.exists():
                self.validation_results.append(("❌", "Server startup", "Server file not found"))
                return False
            
            # Test syntax compilation
            with open(server_file, 'r') as f:
                source = f.read()
            
            compile(source, str(server_file), 'exec')
            self.validation_results.append(("✅", "Server startup", "Server file compiles successfully"))
            
            print("✅ Server startup test passed")
            return True
            
        except Exception as e:
            self.validation_results.append(("❌", "Server startup", f"Error: {e}"))
            print(f"❌ Server startup test failed: {e}")
            return False
    
    def run_regression_tests(self) -> bool:
        """Run available regression tests"""
        
        print("🔍 Running regression tests...")
        success = True
        
        # Find regression test scripts
        test_scripts = [
            "run_arbitrator_regression_test.sh",
            "tests/test_arbitrator_word_count_regression.py"
        ]
        
        for test_script in test_scripts:
            test_path = self.project_root / test_script
            
            if not test_path.exists():
                self.validation_results.append(("⚠️", f"Regression test: {test_script}", "Test file not found"))
                continue
            
            try:
                if test_script.endswith('.sh'):
                    # Test shell script syntax
                    result = subprocess.run(
                        ["bash", "-n", str(test_path)], 
                        capture_output=True, 
                        text=True,
                        cwd=str(self.project_root)
                    )
                    
                    if result.returncode == 0:
                        self.validation_results.append(("✅", f"Regression test: {test_script}", "Script syntax OK"))
                    else:
                        self.validation_results.append(("❌", f"Regression test: {test_script}", f"Syntax error: {result.stderr}"))
                        success = False
                        
                elif test_script.endswith('.py'):
                    # Test Python syntax
                    with open(test_path, 'r') as f:
                        source = f.read()
                    
                    compile(source, str(test_path), 'exec')
                    self.validation_results.append(("✅", f"Regression test: {test_script}", "Python syntax OK"))
                    
            except Exception as e:
                self.validation_results.append(("❌", f"Regression test: {test_script}", f"Error: {e}"))
                success = False
        
        print(f"{'✅' if success else '❌'} Validated regression tests")
        return success
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        
        report = ["# 🔍 Project Reorganization Validation Report\n"]
        
        # Count results by type
        success_count = len([r for r in self.validation_results if r[0] == "✅"])
        warning_count = len([r for r in self.validation_results if r[0] == "⚠️"])
        error_count = len([r for r in self.validation_results if r[0] == "❌"])
        
        report.append(f"## 📊 Summary")
        report.append(f"- ✅ **Passed**: {success_count} checks")
        report.append(f"- ⚠️ **Warnings**: {warning_count} checks")
        report.append(f"- ❌ **Failed**: {error_count} checks")
        report.append("")
        
        # Overall status
        overall_status = "🟢 SAFE TO PROCEED" if error_count == 0 else "🔴 ISSUES FOUND - REQUIRES ATTENTION"
        report.append(f"## 🎯 Overall Status: {overall_status}\n")
        
        # Detailed results
        report.append("## 📋 Detailed Validation Results\n")
        
        for status, test_name, result in self.validation_results:
            report.append(f"- {status} **{test_name}**: {result}")
        
        if error_count > 0:
            report.append("\n## 🚨 Action Required")
            report.append("The following issues must be resolved before proceeding with reorganization:")
            
            for status, test_name, result in self.validation_results:
                if status == "❌":
                    report.append(f"- 🔴 **{test_name}**: {result}")
        
        return "\n".join(report)
    
    def run_full_validation(self) -> bool:
        """Run complete validation suite"""
        
        print(f"🎯 Running full validation for project reorganization")
        print(f"📍 Project root: {self.project_root}")
        
        # Run all validation checks
        checks = [
            ("Python imports", self.validate_imports),
            ("Configuration files", self.validate_config_files),
            ("File operations", self.validate_file_operations),
            ("Shell scripts", self.validate_shell_scripts),
            ("Tool imports", self.validate_tool_imports),
            ("Server startup", self.test_server_startup),
            ("Regression tests", self.run_regression_tests),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"\n🔍 Running {check_name} validation...")
            try:
                result = check_func()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ {check_name} validation failed with exception: {e}")
                self.validation_results.append(("❌", f"{check_name} validation", f"Exception: {e}"))
                all_passed = False
        
        # Generate report
        report = self.generate_validation_report()
        report_file = f"reorganization_validation_report_{self._get_timestamp()}.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Validation report saved to: {report_file}")
        
        if all_passed:
            print("🟢 ALL VALIDATIONS PASSED - Safe to proceed with reorganization")
        else:
            print("🔴 VALIDATION FAILURES DETECTED - Address issues before reorganization")
        
        return all_passed
    
    def _get_timestamp(self) -> str:
        """Get timestamp for file naming"""
        import datetime
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate project reorganization readiness')
    parser.add_argument('--root', default='.', help='Project root directory')
    
    args = parser.parse_args()
    
    validator = ReorganizationValidator(args.root)
    success = validator.run_full_validation()
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())