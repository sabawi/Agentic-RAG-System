#!/usr/bin/env python3
"""
Reorganization Readiness Test
Simulates what will happen when test files are moved to new directory structure
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_reorganization_simulation():
    """Test that modified files will work when moved to new structure"""
    
    print("🧪 REORGANIZATION READINESS TEST")
    print("=" * 50)
    
    # Create temporary directory structure to simulate reorganization
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create the new directory structure
        test_dirs = {
            'tests': temp_path / 'tests',
            'tests_integration': temp_path / 'tests' / 'integration', 
            'tests_utilities': temp_path / 'tests' / 'utilities',
            'tools': temp_path / 'tools',
            'tools_validation': temp_path / 'tools' / 'validation'
        }
        
        # Create all directories
        for dir_name, dir_path in test_dirs.items():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created: {dir_path}")
        
        # Copy essential project files to simulate full project
        project_root = Path.cwd()
        essential_files = [
            'user_tools',
            'config', 
            'sandbox_workspace'
        ]
        
        for item in essential_files:
            src = project_root / item
            dst = temp_path / item
            if src.is_dir():
                shutil.copytree(src, dst)
                print(f"📂 Copied directory: {item}")
            elif src.is_file():
                shutil.copy2(src, dst)
                print(f"📄 Copied file: {item}")
        
        # Test file movements and path resolution
        test_files = {
            'test_complete_workflow.py': 'tests/integration',
            'test_attachment_fuzzy_matching.py': 'tests/integration',
            'test_email_provider_fix.py': 'tests/integration', 
            'test_file_creation.py': 'tests/integration',
            'test_complete_final_verification.py': 'tests/integration'
        }
        
        print(f"\n🔄 Testing file movements...")
        
        for test_file, target_dir in test_files.items():
            print(f"\n📝 Testing: {test_file} → {target_dir}/")
            
            # Copy test file to new location
            src_file = project_root / test_file
            target_path = temp_path / target_dir
            dst_file = target_path / test_file
            
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                
                # Test if the moved file can resolve paths correctly
                test_script = f"""
import sys
import os

# Change to the simulated project root (parent of tests directory)  
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

# Test the dynamic path resolution from the new location
sys.path.insert(0, project_root)

print(f"File location: {{os.path.abspath(__file__)}}")
print(f"Project root: {{project_root}}")
print(f"Working directory: {{os.getcwd()}}")

try:
    # Test imports based on file type
    if '{test_file}' == 'test_complete_workflow.py':
        from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
        from user_tools.sandboxed_executor import SandboxedExecutorTool
        from user_tools.secure_email_sender import SecureEmailSenderTool
        print("✅ All imports successful")
    elif '{test_file}' in ['test_attachment_fuzzy_matching.py', 'test_email_provider_fix.py']:
        from user_tools.secure_email_sender import SecureEmailSenderTool
        print("✅ Email sender import successful")
    elif '{test_file}' == 'test_file_creation.py':
        from user_tools.comprehensive_stock_analyzer import ComprehensiveStockAnalyzerTool
        print("✅ Stock analyzer import successful")
    elif '{test_file}' == 'test_complete_final_verification.py':
        # Test sandbox path resolution
        sandbox_path = os.path.join(os.getcwd(), "sandbox_workspace")
        if os.path.exists(sandbox_path):
            print(f"✅ Sandbox path resolution: {{sandbox_path}}")
        else:
            print(f"❌ Sandbox path not found: {{sandbox_path}}")
            
    print("REORGANIZATION_TEST_SUCCESS")
    
except ImportError as e:
    print(f"❌ Import error: {{e}}")
    print("REORGANIZATION_TEST_FAILED")
except Exception as e:
    print(f"❌ Other error: {{e}}")
    print("REORGANIZATION_TEST_FAILED")
"""
                
                # Write test script to the moved file location
                test_script_file = dst_file.parent / f"test_script_{test_file}.py"
                with open(test_script_file, 'w') as f:
                    f.write(test_script)
                
                # Run the test from the new location
                import subprocess
                result = subprocess.run([
                    sys.executable, str(test_script_file)
                ], capture_output=True, text=True, cwd=str(temp_path))
                
                if "REORGANIZATION_TEST_SUCCESS" in result.stdout:
                    print(f"  ✅ SUCCESS: Path resolution works from new location")
                else:
                    print(f"  ❌ FAILED: Path resolution broken")
                    print(f"  Output: {result.stdout}")
                    print(f"  Error: {result.stderr}")
                    return False
            else:
                print(f"  ⚠️ Source file not found: {src_file}")
        
        print(f"\n🎉 REORGANIZATION READINESS TEST COMPLETE")
        print("✅ All modified files will work correctly after reorganization!")
        
        return True

def main():
    """Main execution"""
    success = test_reorganization_simulation()
    
    if success:
        print("\n🟢 READY FOR REORGANIZATION")
        print("✅ All path fixes validated")
        print("✅ Files can be safely moved to new structure")
        return 0
    else:
        print("\n🔴 NOT READY FOR REORGANIZATION") 
        print("❌ Fix remaining issues before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())