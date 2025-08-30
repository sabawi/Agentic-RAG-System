#!/usr/bin/env python3

import subprocess
import tempfile
import os

def test_mailx_multiple_attachments():
    """Test if mailx properly handles multiple attachments"""
    
    # Create 4 test files
    test_files = []
    try:
        for i, ext in enumerate(['pdf', 'html', 'md', 'txt']):
            temp_file = f"/tmp/test_attach_{i+1}.{ext}"
            with open(temp_file, 'w') as f:
                f.write(f"Test content for file {i+1} ({ext})")
            test_files.append(temp_file)
            print(f"Created test file: {temp_file}")
        
        # Test mailx command with multiple -A flags (same as our email system)
        cmd = [
            "/usr/bin/mailx", 
            "-s", "Test Multiple Attachments",
            "-A", test_files[0],  # PDF
            "-A", test_files[1],  # HTML  
            "-A", test_files[2],  # MD
            "-A", test_files[3],  # TXT
            "sabawi@gmail.com"
        ]
        
        print(f"Testing mailx command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            input="This is a test of multiple attachments with mailx.",
            text=True,
            capture_output=True,
            timeout=30
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ mailx command succeeded")
        else:
            print("❌ mailx command failed")
            
    finally:
        # Clean up test files
        for test_file in test_files:
            try:
                os.unlink(test_file)
                print(f"Cleaned up: {test_file}")
            except:
                pass

if __name__ == "__main__":
    test_mailx_multiple_attachments()