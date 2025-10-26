#!/usr/bin/env python3
"""
Test script to debug _file_needs_reindexing logic
"""
import sys
import asyncio
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

def test_file_needs_reindexing():
    """Test the file checking logic directly"""
    
    # Test file that should be in database
    # NOTE: This test requires a file to be indexed - update with actual test file path
    file_path = "/path/to/test/document.txt"  # FIXME: Update with test data file
    
    # Calculate current file stats
    file_stat = Path(file_path).stat()
    current_mtime = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
    
    # Calculate current file hash
    with open(file_path, 'rb') as f:
        current_hash = hashlib.md5(f.read()).hexdigest()
    
    print(f"File: {file_path}")
    print(f"Current mtime: {current_mtime}")
    print(f"Current hash: {current_hash}")
    
    # Check database
    db_path = "/home/sabawi/Development/flaskserver/document_store/metadata.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT file_hash, last_modified FROM documents 
        WHERE file_path = ?
    ''', (file_path,))
    
    result = cursor.fetchone()
    if not result:
        print("❌ ERROR: File not found in database!")
        return False
        
    stored_hash, stored_mtime = result
    print(f"Stored mtime: {stored_mtime}")
    print(f"Stored hash: {stored_hash}")
    
    # Compare
    if stored_hash != current_hash:
        print("❌ Hash mismatch - file NEEDS reindexing")
        return True
    elif stored_mtime != current_mtime:
        print("❌ Timestamp mismatch - file NEEDS reindexing")
        return True
    else:
        print("✅ File is UP-TO-DATE - should be skipped")
        return False

if __name__ == "__main__":
    needs_reindexing = test_file_needs_reindexing()
    print(f"\nResult: _file_needs_reindexing() should return: {needs_reindexing}")