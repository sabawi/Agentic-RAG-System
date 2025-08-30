#!/usr/bin/env python3
"""
Fix to add escaped newlines processing to sandboxed_executor.py
"""

# Read the current file
with open('user_tools/sandboxed_executor.py', 'r') as f:
    content = f.read()

# Add the new method at the end, before the last line
fix_method = '''
    def _fix_escaped_newlines_in_code(self, content: str, filename: str) -> str:
        """
        🐛 CRITICAL FIX: Convert escaped newlines to real newlines for code files
        
        This fixes the issue where LLM generates Python code with literal \\n strings
        instead of actual newlines, causing syntax errors.
        """
        try:
            # Only process code files
            code_extensions = ['.py', '.js', '.sh', '.c', '.cpp', '.java', '.rs', '.php', '.rb', '.go']
            file_ext = filename.lower()
            
            if not any(file_ext.endswith(ext) for ext in code_extensions):
                return content  # Not a code file, return as-is
            
            print(f"🐛 NEWLINE FIX: Processing {filename} for escaped newlines")
            print(f"🐛 NEWLINE FIX: Original content length: {len(content)}")
            print(f"🐛 NEWLINE FIX: Contains \\\\n literals: {'\\\\n' in content}")
            print(f"🐛 NEWLINE FIX: Contains real newlines: {chr(10) in content}")
            
            # Check if the content has escaped newlines but no real newlines
            # This indicates the content came from JSON with escaped newlines
            has_escaped_newlines = '\\\\n' in content
            has_real_newlines = '\\n' in content
            
            # Only process if we have escaped newlines and few real newlines
            # (allowing for some real newlines that might exist)
            real_newline_count = content.count('\\n')
            escaped_newline_count = content.count('\\\\n')
            
            if has_escaped_newlines and escaped_newline_count > real_newline_count:
                print(f"🐛 NEWLINE FIX: Converting {escaped_newline_count} escaped newlines to real newlines")
                
                # Convert escaped newlines and tabs to real ones
                processed = content.replace('\\\\n', '\\n').replace('\\\\t', '\\t')
                
                # Also handle other common escape sequences that might appear in code
                processed = processed.replace('\\\\r', '\\r')
                processed = processed.replace("\\\\'", "'")  # Single quotes
                processed = processed.replace('\\\\"', '"')   # Double quotes
                
                print(f"🐛 NEWLINE FIX: Processed content length: {len(processed)}")
                print(f"🐛 NEWLINE FIX: Real newlines after processing: {processed.count(chr(10))}")
                
                # Validate the result makes sense for a code file
                if processed.count('\\n') > 0:  # Should have real newlines now
                    return processed
                else:
                    print(f"🐛 NEWLINE FIX: Warning - processed content has no newlines, keeping original")
                    return content
            else:
                print(f"🐛 NEWLINE FIX: No conversion needed (escaped: {escaped_newline_count}, real: {real_newline_count})")
                return content
                
        except Exception as e:
            print(f"🐛 NEWLINE FIX: Error processing {filename}: {e}")
            return content  # Return original content on error
'''

# Find the last line and insert before it
lines = content.split('\n')
lines.insert(-1, fix_method)
new_content = '\n'.join(lines)

# Write the modified file
with open('user_tools/sandboxed_executor.py', 'w') as f:
    f.write(new_content)

print("✅ Added _fix_escaped_newlines_in_code method to sandboxed_executor.py")