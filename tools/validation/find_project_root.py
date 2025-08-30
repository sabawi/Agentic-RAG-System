#!/usr/bin/env python3
"""
Project Root Discovery Utility
Finds the project root directory from any file location within the project
"""

import os
from pathlib import Path

def find_project_root(start_path=None):
    """
    Find the project root directory by looking for marker files/directories.
    
    Args:
        start_path: Starting directory (defaults to current file's directory)
        
    Returns:
        Path to project root directory
    """
    if start_path is None:
        start_path = os.path.dirname(os.path.abspath(__file__))
    
    # Marker files/directories that indicate project root
    markers = [
        'user_tools',           # Our main tools directory
        'sandbox_workspace',    # Our sandbox directory  
        'config',              # Config directory
        'fastapi_server_complete.py'  # Main server file
    ]
    
    current = Path(start_path).resolve()
    
    # Walk up the directory tree
    for parent in [current] + list(current.parents):
        # Check if this directory has our project markers
        marker_count = sum(1 for marker in markers if (parent / marker).exists())
        
        # If we find at least 3 of our 4 markers, this is likely the project root
        if marker_count >= 3:
            return str(parent)
    
    # If we can't find markers, fall back to current working directory
    # This handles the case where we're running from project root
    return os.getcwd()

def add_project_to_path(start_path=None):
    """
    Add project root to sys.path for imports.
    
    Args:
        start_path: Starting directory (defaults to current file's directory)
    """
    import sys
    
    project_root = find_project_root(start_path)
    
    # Add to beginning of sys.path if not already there
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    return project_root

# Test the function when run directly
if __name__ == "__main__":
    print("🔍 Testing project root discovery...")
    
    # Test from current location
    root = find_project_root()
    print(f"Project root: {root}")
    
    # Verify markers exist
    markers = ['user_tools', 'sandbox_workspace', 'config', 'fastapi_server_complete.py']
    for marker in markers:
        marker_path = os.path.join(root, marker)
        exists = os.path.exists(marker_path)
        print(f"  {'✅' if exists else '❌'} {marker}: {marker_path}")
    
    # Test adding to path
    project_root = add_project_to_path()
    print(f"Added to sys.path: {project_root}")
    
    # Test imports
    try:
        from user_tools.secure_email_sender import SecureEmailSenderTool
        print("✅ Import test successful")
    except ImportError as e:
        print(f"❌ Import test failed: {e}")