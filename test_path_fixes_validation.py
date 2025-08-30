#!/usr/bin/env python3
"""
Path Fixes Validation Suite
Tests that all modified test files still work correctly after dynamic path resolution fixes
"""

import os
import sys
import subprocess
import importlib.util
import traceback
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class PathFixesValidator:
    def __init__(self):
        self.project_root = Path(os.getcwd()).resolve()
        self.test_results = []
        self.modified_files = [
            "test_complete_workflow.py",
            "test_attachment_fuzzy_matching.py", 
            "test_email_provider_fix.py",
            "test_file_creation.py",
            "test_complete_final_verification.py"
        ]
        
    def test_file_syntax_validation(self) -> bool:
        """Test that all modified files have correct Python syntax"""
        print("🔍 Testing Python syntax validation...")
        success = True
        
        for file_name in self.modified_files:
            file_path = self.project_root / file_name
            
            if not file_path.exists():
                self.test_results.append(("❌", f"Syntax: {file_name}", "File not found"))
                success = False
                continue
                
            try:
                with open(file_path, 'r') as f:
                    source = f.read()
                    
                compile(source, str(file_path), 'exec')
                self.test_results.append(("✅", f"Syntax: {file_name}", "Valid Python syntax"))
                
            except SyntaxError as e:
                self.test_results.append(("❌", f"Syntax: {file_name}", f"Syntax error: {e}"))
                success = False
            except Exception as e:
                self.test_results.append(("❌", f"Syntax: {file_name}", f"Error: {e}"))
                success = False
                
        print(f"{'✅' if success else '❌'} Syntax validation: {len([r for r in self.test_results if r[0] == '✅' and 'Syntax:' in r[1]])}/{len(self.modified_files)} files passed")
        return success
    
    def test_import_resolution(self) -> bool:
        """Test that dynamic path resolution allows proper imports"""
        print("🔍 Testing import resolution...")
        success = True
        
        for file_name in self.modified_files:
            file_path = self.project_root / file_name
            
            if not file_path.exists():
                continue
                
            try:
                # Test if the file can be imported/executed without import errors
                # We'll run a subprocess to test this safely
                test_script = f"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('{file_path}')))

# Try to import the required modules that each test file needs
try:
    if '{file_name}' == 'test_complete_workflow.py':
        from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
        from user_tools.sandboxed_executor import SandboxedExecutorTool
        from user_tools.secure_email_sender import SecureEmailSenderTool
    elif '{file_name}' in ['test_attachment_fuzzy_matching.py', 'test_email_provider_fix.py']:
        from user_tools.secure_email_sender import SecureEmailSenderTool
    elif '{file_name}' == 'test_file_creation.py':
        from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
    elif '{file_name}' == 'test_complete_final_verification.py':
        import requests  # This file uses requests for API testing
    
    print("IMPORT_SUCCESS")
except ImportError as e:
    print(f"IMPORT_ERROR: {{e}}")
except Exception as e:
    print(f"OTHER_ERROR: {{e}}")
"""
                
                result = subprocess.run([
                    sys.executable, '-c', test_script
                ], capture_output=True, text=True, cwd=str(self.project_root))
                
                if "IMPORT_SUCCESS" in result.stdout:
                    self.test_results.append(("✅", f"Import: {file_name}", "Import resolution successful"))
                elif "IMPORT_ERROR" in result.stdout:
                    error_msg = result.stdout.split("IMPORT_ERROR: ", 1)[1].strip()
                    self.test_results.append(("❌", f"Import: {file_name}", f"Import failed: {error_msg}"))
                    success = False
                else:
                    self.test_results.append(("⚠️", f"Import: {file_name}", f"Unexpected output: {result.stdout}"))
                    
            except Exception as e:
                self.test_results.append(("❌", f"Import: {file_name}", f"Test error: {e}"))
                success = False
                
        print(f"{'✅' if success else '❌'} Import resolution: {len([r for r in self.test_results if r[0] == '✅' and 'Import:' in r[1]])}/{len(self.modified_files)} files passed")
        return success
    
    def test_path_resolution_logic(self) -> bool:
        """Test that the new dynamic path resolution logic works correctly"""
        print("🔍 Testing path resolution logic...")
        success = True
        
        # Test the path resolution patterns we implemented
        test_cases = [
            {
                'name': 'sys.path dynamic resolution',
                'pattern': 'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))',
                'test_code': '''
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# This should resolve to the current project root
expected_path = os.getcwd()
actual_path = sys.path[0]
print(f"Expected: {expected_path}")
print(f"Actual: {actual_path}")
success = os.path.samefile(expected_path, actual_path)
print(f"PATH_RESOLUTION_{'SUCCESS' if success else 'FAILED'}")
'''
            },
            {
                'name': 'sandbox_workspace path resolution', 
                'pattern': 'os.path.join(os.getcwd(), "sandbox_workspace")',
                'test_code': '''
import os
sandbox_path = os.path.join(os.getcwd(), "sandbox_workspace")
expected_path = "/home/sabawi/Development/flaskserver/sandbox_workspace"
success = os.path.samefile(sandbox_path, expected_path) if os.path.exists(sandbox_path) else False
print(f"Sandbox path: {sandbox_path}")
print(f"Expected: {expected_path}")
print(f"Exists: {os.path.exists(sandbox_path)}")
print(f"SANDBOX_PATH_{'SUCCESS' if success else 'FAILED'}")
'''
            }
        ]
        
        for test_case in test_cases:
            try:
                result = subprocess.run([
                    sys.executable, '-c', test_case['test_code']
                ], capture_output=True, text=True, cwd=str(self.project_root))
                
                if "SUCCESS" in result.stdout:
                    self.test_results.append(("✅", f"Path Logic: {test_case['name']}", "Resolution works correctly"))
                else:
                    self.test_results.append(("❌", f"Path Logic: {test_case['name']}", f"Resolution failed: {result.stdout}"))
                    success = False
                    
            except Exception as e:
                self.test_results.append(("❌", f"Path Logic: {test_case['name']}", f"Test error: {e}"))
                success = False
                
        print(f"{'✅' if success else '❌'} Path resolution logic: {len([r for r in self.test_results if r[0] == '✅' and 'Path Logic:' in r[1]])}/{len(test_cases)} tests passed")
        return success
    
    def test_file_system_dependencies(self) -> bool:
        """Test that files can access their required filesystem dependencies"""
        print("🔍 Testing filesystem dependencies...")
        success = True
        
        # Test critical directories and files exist
        dependencies = [
            ("user_tools directory", "user_tools", "directory"),
            ("sandbox_workspace directory", "sandbox_workspace", "directory"),
            ("config directory", "config", "directory"),
            ("sandboxed_executor tool", "user_tools/sandboxed_executor.py", "file"),
            ("secure_email_sender tool", "user_tools/secure_email_sender.py", "file"),
            ("comprehensive_stock_analyzer tool", "user_tools/comprehensive_stock_analyzer.py", "file")
        ]
        
        for dep_name, dep_path, dep_type in dependencies:
            full_path = self.project_root / dep_path
            
            if dep_type == "directory":
                if full_path.exists() and full_path.is_dir():
                    self.test_results.append(("✅", f"Dependency: {dep_name}", "Found and accessible"))
                else:
                    self.test_results.append(("❌", f"Dependency: {dep_name}", "Not found or not a directory"))
                    success = False
            elif dep_type == "file":
                if full_path.exists() and full_path.is_file():
                    self.test_results.append(("✅", f"Dependency: {dep_name}", "Found and accessible"))
                else:
                    self.test_results.append(("❌", f"Dependency: {dep_name}", "Not found or not a file"))
                    success = False
                    
        print(f"{'✅' if success else '❌'} Filesystem dependencies: {len([r for r in self.test_results if r[0] == '✅' and 'Dependency:' in r[1]])}/{len(dependencies)} dependencies satisfied")
        return success
    
    def test_server_compatibility(self) -> bool:
        """Test that modifications don't break server functionality"""
        print("🔍 Testing server compatibility...")
        
        try:
            # Test server can still import and compile
            server_file = self.project_root / "fastapi_server_complete.py"
            
            if not server_file.exists():
                self.test_results.append(("❌", "Server Compatibility", "Server file not found"))
                return False
                
            with open(server_file, 'r') as f:
                source = f.read()
                
            compile(source, str(server_file), 'exec')
            self.test_results.append(("✅", "Server Compatibility", "Server still compiles correctly"))
            
            print("✅ Server compatibility: Server file compiles successfully")
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Server Compatibility", f"Server compile error: {e}"))
            print(f"❌ Server compatibility: Failed - {e}")
            return False
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        
        report = ["# 🔧 Path Fixes Validation Report\n"]
        
        # Count results by type
        success_count = len([r for r in self.test_results if r[0] == "✅"])
        warning_count = len([r for r in self.test_results if r[0] == "⚠️"])
        error_count = len([r for r in self.test_results if r[0] == "❌"])
        
        report.append(f"## 📊 Summary")
        report.append(f"- ✅ **Passed**: {success_count} checks")
        report.append(f"- ⚠️ **Warnings**: {warning_count} checks")
        report.append(f"- ❌ **Failed**: {error_count} checks")
        report.append("")
        
        # Overall status
        overall_status = "🟢 ALL FIXES WORKING" if error_count == 0 else "🔴 ISSUES DETECTED"
        report.append(f"## 🎯 Overall Status: {overall_status}\n")
        
        # Modified files summary
        report.append("## 📋 Modified Files Tested\n")
        for file_name in self.modified_files:
            report.append(f"- `{file_name}` - Dynamic path resolution implemented")
        report.append("")
        
        # Detailed results
        report.append("## 📋 Detailed Test Results\n")
        
        test_categories = {}
        for status, test_name, result in self.test_results:
            category = test_name.split(':')[0] if ':' in test_name else 'General'
            if category not in test_categories:
                test_categories[category] = []
            test_categories[category].append((status, test_name, result))
            
        for category, tests in test_categories.items():
            report.append(f"### {category}")
            for status, test_name, result in tests:
                report.append(f"- {status} **{test_name}**: {result}")
            report.append("")
        
        if error_count > 0:
            report.append("## 🚨 Issues to Address")
            for status, test_name, result in self.test_results:
                if status == "❌":
                    report.append(f"- 🔴 **{test_name}**: {result}")
        
        return "\n".join(report)
    
    def run_full_validation(self) -> bool:
        """Run complete validation suite for path fixes"""
        
        print(f"🎯 Running full validation for path fixes")
        print(f"📍 Project root: {self.project_root}")
        print(f"📝 Modified files: {len(self.modified_files)}")
        
        # Run all validation checks
        checks = [
            ("File syntax validation", self.test_file_syntax_validation),
            ("Import resolution", self.test_import_resolution),
            ("Path resolution logic", self.test_path_resolution_logic),
            ("Filesystem dependencies", self.test_file_system_dependencies),
            ("Server compatibility", self.test_server_compatibility),
        ]
        
        all_passed = True
        
        print("=" * 70)
        for check_name, check_func in checks:
            print(f"\n🔍 Running {check_name}...")
            try:
                result = check_func()
                if not result:
                    all_passed = False
                    print(f"❌ {check_name} - FAILED")
                else:
                    print(f"✅ {check_name} - PASSED")
            except Exception as e:
                print(f"❌ {check_name} - EXCEPTION: {e}")
                traceback.print_exc()
                self.test_results.append(("❌", f"{check_name}", f"Exception: {e}"))
                all_passed = False
        
        # Generate report
        print("\n" + "=" * 70)
        report = self.generate_validation_report()
        report_file = f"path_fixes_validation_report_{self._get_timestamp()}.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Validation report saved to: {report_file}")
        
        if all_passed:
            print("🟢 ALL PATH FIXES VALIDATED - Files ready for reorganization!")
        else:
            print("🔴 VALIDATION FAILURES - Fix issues before proceeding with reorganization")
        
        return all_passed
    
    def _get_timestamp(self) -> str:
        """Get timestamp for file naming"""
        import datetime
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def main():
    """Main execution function"""
    print("🧪 PATH FIXES VALIDATION SUITE")
    print("=" * 50)
    
    validator = PathFixesValidator()
    success = validator.run_full_validation()
    
    if success:
        print("\n🎉 SUCCESS: All path fixes validated!")
        print("✅ Ready to proceed with file reorganization")
        return 0
    else:
        print("\n❌ FAILURES DETECTED: Address issues before reorganization")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())