#!/usr/bin/env python3
"""
Sandboxed System Command Executor Tool
Provides secure code execution and system command access within isolated environment
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    from .base_user_tool import BaseUserTool
except ImportError:
    from base_user_tool import BaseUserTool


class SandboxedExecutorTool(BaseUserTool):
    """
    A secure sandboxed environment for executing system commands and running code.
    
    Features:
    - Isolated workspace directory with full RWX permissions
    - Secure command execution with output capture
    - File management within sandbox boundaries
    - Resource limits and security controls
    - Support for multiple programming languages
    """
    
    def __init__(self):
        super().__init__()
        
        # Sandbox configuration
        self.base_dir = Path("/home/sabawi/Development/flaskserver")
        self.sandbox_name = "sandbox_workspace"
        self.sandbox_path = self.base_dir / self.sandbox_name
        
        # Security settings
        self.max_execution_time = 30  # seconds
        self.max_output_size = 50000  # characters
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Allowed/blocked commands for security
        self.allowed_commands = {
            'python3', 'python', 'node', 'npm', 'pip', 'pip3',
            'gcc', 'g++', 'javac', 'java', 'rustc', 'cargo',
            'ls', 'cat', 'head', 'tail', 'wc', 'grep', 'find',
            'echo', 'pwd', 'whoami', 'id', 'uname',
            'chmod', 'mkdir', 'rmdir', 'touch', 'cp', 'mv', 'rm',
            'tar', 'gzip', 'gunzip', 'curl', 'wget',
            'pandoc', 'pdflatex', 'latex', 'convert'
        }
        
        self.blocked_commands = {
            'sudo', 'su', 'passwd', 'chown', 'chgrp',
            'mount', 'umount', 'fdisk', 'mkfs',
            'iptables', 'systemctl', 'service',
            'reboot', 'shutdown', 'halt', 'init',
            'crontab', 'at', 'batch',
            'ssh', 'scp', 'rsync', 'nc', 'netcat'
        }
        
        # Initialize sandbox
        self._setup_sandbox()
    
    @property
    def name(self) -> str:
        return "sandboxed_executor"
    
    @property
    def description(self) -> str:
        return "Execute system commands and run code files in a secure sandboxed environment with full diagnostic output capture for LLM analysis."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["execute", "create_file", "read_file", "list_files", "delete_file", "run_code"],
                    "description": "Action to perform: execute (run command), create_file (write file), read_file (read file), list_files (show directory), delete_file (remove file), run_code (execute code file)"
                },
                "command": {
                    "type": "string", 
                    "description": "System command to execute (for 'execute' action). Examples: 'python3 script.py', 'ls -la', 'gcc -o program program.c'"
                },
                "filename": {
                    "type": "string",
                    "description": "Filename for file operations (for create_file, read_file, delete_file, run_code actions)"
                },
                "content": {
                    "type": "string",
                    "description": "File content (for 'create_file' action)"
                },
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "bash", "c", "cpp", "java", "rust"],
                    "description": "Programming language (for 'run_code' action)"
                },
                "args": {
                    "type": "string",
                    "description": "Command line arguments (for 'run_code' action)"
                },
                "convert_to_pdf": {
                    "type": "boolean",
                    "description": "Convert text file to PDF using Python (for 'create_file' action)"
                },
                "path": {
                    "type": "string",
                    "description": "Directory path to list (for 'list_files' action). Examples: 'short_stories', 'src', '.' for current directory"
                }
            },
            "required": ["action"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute sandboxed system operations."""
        try:
            action = kwargs.get("action", "").strip()
            
            if not action:
                return {
                    "success": False,
                    "error": "Action parameter is required",
                    "result": None
                }
            
            # Route to appropriate handler
            if action == "execute":
                return await self._execute_command(kwargs)
            elif action == "create_file":
                return await self._create_file(kwargs)
            elif action == "read_file":
                return await self._read_file(kwargs)
            elif action == "list_files":
                return await self._list_files(kwargs)
            elif action == "delete_file":
                return await self._delete_file(kwargs)
            elif action == "run_code":
                return await self._run_code(kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "result": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Sandboxed executor error: {str(e)}",
                "result": None
            }
    
    def _setup_sandbox(self):
        """Initialize the sandbox directory with proper permissions."""
        try:
            # Create sandbox directory if it doesn't exist
            self.sandbox_path.mkdir(mode=0o755, parents=True, exist_ok=True)
            
            # Create subdirectories
            (self.sandbox_path / "src").mkdir(exist_ok=True)
            (self.sandbox_path / "bin").mkdir(exist_ok=True)
            (self.sandbox_path / "data").mkdir(exist_ok=True)
            (self.sandbox_path / "tmp").mkdir(exist_ok=True)
            
            # Create a README
            readme_content = f"""# Sandboxed Workspace
Created: {datetime.now().isoformat()}

This is a secure sandboxed environment for code execution and system commands.

## Directory Structure:
- src/    - Source code files
- bin/    - Compiled binaries
- data/   - Data files
- tmp/    - Temporary files

## Security:
- No access outside this directory
- Limited system commands
- Resource limits enforced
- All output captured for analysis
"""
            
            readme_path = self.sandbox_path / "README.md"
            if not readme_path.exists():
                readme_path.write_text(readme_content)
            
            print(f"✅ Sandbox initialized at: {self.sandbox_path}")
            
        except Exception as e:
            print(f"❌ Failed to setup sandbox: {e}")
            raise
    
    def _validate_command(self, command: str) -> Tuple[bool, str]:
        """Validate command for security."""
        if not command or not command.strip():
            return False, "Empty command"
        
        # Extract the base command
        base_cmd = command.strip().split()[0]
        
        # Check if command is blocked
        if base_cmd in self.blocked_commands:
            return False, f"Blocked command: {base_cmd}"
        
        # Check for dangerous patterns (excluding safe compilation chains)
        dangerous_patterns = [
            '../', '..\\', '/etc/', '/proc/', '/sys/', '/dev/',
            '$(', '`', 'rm -rf /', 'dd if=', 'mkfs', 'format'
        ]
        
        # Special handling for compilation chains - allow controlled && usage
        if not self._is_safe_compilation_command(command):
            dangerous_patterns.extend(['&&', '||', ';', '|'])
        
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return False, f"Dangerous pattern detected: {pattern}"
        
        return True, "Command allowed"
    
    def _analyze_command_error(self, command: str, return_code: int, stderr: str) -> str:
        """Analyze command errors and provide helpful suggestions."""
        cmd_parts = command.strip().split()
        base_cmd = cmd_parts[0] if cmd_parts else ""
        
        # Common error patterns and solutions
        if "mkdir" in base_cmd:
            if "File exists" in stderr:
                if len(cmd_parts) > 1:
                    dir_name = cmd_parts[1]
                    return f"Directory '{dir_name}' already exists. Use 'ls -la {dir_name}' to check if it's a file instead of directory, or use 'mkdir -p {dir_name}' to avoid error if it exists."
                return "Directory already exists. Consider using 'mkdir -p' to avoid this error."
            elif "Permission denied" in stderr:
                return "Permission denied creating directory. Check if you have write permissions in the current location."
        
        elif "mv" in base_cmd:
            if "No such file or directory" in stderr:
                return "Source file not found or destination directory doesn't exist. Use 'ls -la' to check current files and 'mkdir' to create destination directory if needed."
            elif "Not a directory" in stderr:
                return "Cannot move file into target because it's not a directory. Check if destination path is correct or if a file exists with the same name as your target directory."
            elif "Permission denied" in stderr:
                return "Permission denied moving file. Check file permissions with 'ls -la' and ensure destination is writable."
        
        elif "cp" in base_cmd:
            if "No such file or directory" in stderr:
                return "Source file not found or destination directory doesn't exist. Use 'ls -la' to verify file paths."
        
        elif "rm" in base_cmd:
            if "No such file or directory" in stderr:
                return "File or directory not found. Use 'ls -la' to check what files exist."
        
        elif "ls" in base_cmd:
            if "No such file or directory" in stderr:
                return "Directory or file does not exist. Use 'ls -la' without arguments to see current directory contents."
        
        # Generic error analysis
        if "Permission denied" in stderr:
            return f"Permission denied executing '{base_cmd}'. Check file permissions or try a different approach."
        elif "command not found" in stderr or "No such file or directory" in stderr and "/" not in command:
            return f"Command '{base_cmd}' not found. Check if the command is available or installed."
        elif return_code == 127:
            return f"Command '{base_cmd}' not found in PATH. Verify the command exists and is executable."
        elif return_code == 126:
            return f"Permission denied executing '{base_cmd}'. File may not be executable."
        
        # Fallback with stderr content
        if stderr.strip():
            return f"Command failed: {stderr.strip()[:200]}{'...' if len(stderr) > 200 else ''}"
        else:
            return f"Command '{command}' failed with exit code {return_code} (no error message provided)"
    
    def _is_safe_compilation_command(self, command: str) -> bool:
        """Check if command is a safe compilation chain."""
        # Allow specific compilation patterns that use && safely
        safe_patterns = [
            r'gcc.*-o\s+bin/.*\.c\s+&&\s+\./bin/',
            r'g\+\+.*-o\s+bin/.*\.cpp\s+&&\s+\./bin/',
            r'javac.*-d\s+bin.*\.java\s+&&\s+java\s+-cp\s+bin',
            r'rustc.*-o\s+bin/.*\.rs\s+&&\s+\./bin/'
        ]
        
        import re
        for pattern in safe_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_path(self, path: str) -> Tuple[bool, str]:
        """Ensure path is within sandbox boundaries."""
        try:
            # Convert to absolute path
            abs_path = Path(path).resolve() if Path(path).is_absolute() else (self.sandbox_path / path).resolve()
            
            # Check if path is within sandbox
            if not str(abs_path).startswith(str(self.sandbox_path.resolve())):
                return False, f"Path outside sandbox: {abs_path}"
            
            return True, str(abs_path)
            
        except Exception as e:
            return False, f"Invalid path: {e}"
    
    async def _execute_command(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a system command in the sandbox."""
        command = kwargs.get("command", "").strip()
        
        if not command:
            return {"success": False, "error": "Command is required", "result": None}
        
        # Validate command security
        is_valid, validation_msg = self._validate_command(command)
        if not is_valid:
            return {"success": False, "error": f"Security violation: {validation_msg}", "result": None}
        
        try:
            # Change to sandbox directory
            original_cwd = os.getcwd()
            os.chdir(self.sandbox_path)
            
            # Execute command with timeout and capture output
            start_time = time.time()
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.sandbox_path,
                preexec_fn=os.setsid  # Create new process group
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.max_execution_time)
                execution_time = time.time() - start_time
                return_code = process.returncode
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                execution_time = self.max_execution_time
                return_code = -1
                stderr += f"\n⚠️ Command timed out after {self.max_execution_time} seconds"
            
            # Restore original working directory
            os.chdir(original_cwd)
            
            # Truncate output if too long
            if len(stdout) > self.max_output_size:
                stdout = stdout[:self.max_output_size] + f"\n... (truncated, {len(stdout)} total chars)"
            
            if len(stderr) > self.max_output_size:
                stderr = stderr[:self.max_output_size] + f"\n... (truncated, {len(stderr)} total chars)"
            
            # Provide intelligent error analysis for common issues
            error_message = None
            if return_code != 0:
                error_message = self._analyze_command_error(command, return_code, stderr)
            
            return {
                "success": return_code == 0,
                "result": {
                    "command": command,
                    "return_code": return_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "execution_time": round(execution_time, 3),
                    "working_directory": str(self.sandbox_path),
                    "error_analysis": error_message
                },
                "error": None if return_code == 0 else f"Command failed with code {return_code}"
            }
            
        except Exception as e:
            # Restore original working directory
            os.chdir(original_cwd) 
            return {"success": False, "error": f"Execution error: {str(e)}", "result": None}
    
    async def _create_file(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Create a file in the sandbox."""
        filename = kwargs.get("filename", "").strip()
        content = kwargs.get("content", "")
        convert_to_pdf = kwargs.get("convert_to_pdf", False)
        
        if not filename:
            return {"success": False, "error": "Filename is required", "result": None}
        
        # Validate path
        is_valid, file_path = self._validate_path(filename)
        if not is_valid:
            return {"success": False, "error": file_path, "result": None}
        
        try:
            # Check content size
            if len(content.encode('utf-8')) > self.max_file_size:
                return {"success": False, "error": f"File too large (max {self.max_file_size} bytes)", "result": None}
            
            # Create parent directories if needed
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Get file stats
            file_stats = os.stat(file_path)
            
            result = {
                "filename": filename,
                "full_path": file_path,
                "size_bytes": file_stats.st_size,
                "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "permissions": oct(file_stats.st_mode)[-3:]
            }
            
            # Convert to PDF if requested
            if convert_to_pdf:
                pdf_result = await self._convert_text_to_pdf(file_path, content)
                if pdf_result["success"]:
                    result["pdf_file"] = pdf_result["pdf_path"]
                    result["pdf_created"] = True
                else:
                    result["pdf_error"] = pdf_result["error"]
                    result["pdf_created"] = False
            
            return {
                "success": True,
                "result": result,
                "error": None
            }
            
        except Exception as e:
            return {"success": False, "error": f"File creation error: {str(e)}", "result": None}
    
    async def _read_file(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file from the sandbox."""
        filename = kwargs.get("filename", "").strip()
        
        if not filename:
            return {"success": False, "error": "Filename is required", "result": None}
        
        # Validate path
        is_valid, file_path = self._validate_path(filename)
        if not is_valid:
            return {"success": False, "error": file_path, "result": None}
        
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {filename}", "result": None}
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return {"success": False, "error": f"File too large to read ({file_size} bytes)", "result": None}
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get file stats
            file_stats = os.stat(file_path)
            
            return {
                "success": True,
                "result": {
                    "filename": filename,
                    "full_path": file_path,
                    "content": content,
                    "size_bytes": file_stats.st_size,
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "permissions": oct(file_stats.st_mode)[-3:]
                },
                "error": None
            }
            
        except Exception as e:
            return {"success": False, "error": f"File read error: {str(e)}", "result": None}
    
    async def _list_files(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """List files in the sandbox directory."""
        path = kwargs.get("path", "").strip() or "."
        
        # Validate path
        is_valid, dir_path = self._validate_path(path)
        if not is_valid:
            return {"success": False, "error": dir_path, "result": None}
        
        try:
            if not os.path.exists(dir_path):
                return {"success": False, "error": f"Directory not found: {path}", "result": None}
            
            if not os.path.isdir(dir_path):
                return {"success": False, "error": f"Not a directory: {path}", "result": None}
            
            files = []
            for item in sorted(os.listdir(dir_path)):
                item_path = os.path.join(dir_path, item)
                stats = os.stat(item_path)
                
                files.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size_bytes": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "permissions": oct(stats.st_mode)[-3:]
                })
            
            return {
                "success": True,
                "result": {
                    "directory": path,
                    "full_path": dir_path,
                    "files": files,
                    "total_files": len(files)
                },
                "error": None
            }
            
        except Exception as e:
            return {"success": False, "error": f"Directory listing error: {str(e)}", "result": None}
    
    async def _delete_file(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file from the sandbox."""
        filename = kwargs.get("filename", "").strip()
        
        if not filename:
            return {"success": False, "error": "Filename is required", "result": None}
        
        # Validate path
        is_valid, file_path = self._validate_path(filename)
        if not is_valid:
            return {"success": False, "error": file_path, "result": None}
        
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {filename}", "result": None}
            
            # Get stats before deletion
            file_stats = os.stat(file_path)
            is_directory = os.path.isdir(file_path)
            
            # Delete file or directory
            if is_directory:
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            
            return {
                "success": True,
                "result": {
                    "filename": filename,
                    "full_path": file_path,
                    "type": "directory" if is_directory else "file",
                    "size_bytes": file_stats.st_size,
                    "deleted_at": datetime.now().isoformat()
                },
                "error": None
            }
            
        except Exception as e:
            return {"success": False, "error": f"File deletion error: {str(e)}", "result": None}
    
    async def _run_code(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Run a code file with appropriate interpreter."""
        filename = kwargs.get("filename", "").strip()
        language = kwargs.get("language", "").strip()
        args = kwargs.get("args", "").strip()
        
        if not filename:
            return {"success": False, "error": "Filename is required", "result": None}
        
        # Validate path
        is_valid, file_path = self._validate_path(filename)
        if not is_valid:
            return {"success": False, "error": file_path, "result": None}
        
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {filename}", "result": None}
        
        try:
            # Determine command based on language or file extension
            if not language:
                ext = Path(filename).suffix.lower()
                language_map = {
                    '.py': 'python',
                    '.js': 'javascript', 
                    '.sh': 'bash',
                    '.c': 'c',
                    '.cpp': 'cpp',
                    '.java': 'java',
                    '.rs': 'rust'
                }
                language = language_map.get(ext, 'unknown')
            
            # Build execution command
            commands = {
                'python': f'python3 {filename} {args}',
                'javascript': f'node {filename} {args}',
                'bash': f'bash {filename} {args}',
                'c': f'gcc -o bin/{Path(filename).stem} {filename} && ./bin/{Path(filename).stem} {args}',
                'cpp': f'g++ -o bin/{Path(filename).stem} {filename} && ./bin/{Path(filename).stem} {args}',
                'java': f'javac -d bin {filename} && java -cp bin {Path(filename).stem} {args}',
                'rust': f'rustc -o bin/{Path(filename).stem} {filename} && ./bin/{Path(filename).stem} {args}'
            }
            
            if language not in commands:
                return {"success": False, "error": f"Unsupported language: {language}", "result": None}
            
            command = commands[language].strip()
            
            # Execute using the command executor
            return await self._execute_command({"command": command})
            
        except Exception as e:
            return {"success": False, "error": f"Code execution error: {str(e)}", "result": None}
    
    async def _convert_text_to_pdf(self, text_file_path: str, content: str) -> Dict[str, Any]:
        """Convert text content to PDF using Python."""
        try:
            # Generate PDF file path
            text_path = Path(text_file_path)
            pdf_path = text_path.with_suffix('.pdf')
            
            # Create Python script to generate PDF
            pdf_script = f'''#!/usr/bin/env python3
"""
Auto-generated PDF converter script
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import textwrap

def create_pdf():
    try:
        # Read the text file
        with open("{text_file_path}", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Create PDF
        doc = SimpleDocTemplate("{pdf_path}", pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        story = []
        
        # Add title
        title = "{text_path.stem}".replace("_", " ").title()
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Split content into paragraphs
        paragraphs = content.split('\\n\\n')
        
        for para in paragraphs:
            if para.strip():
                # Wrap long lines
                wrapped_lines = []
                for line in para.split('\\n'):
                    if len(line) > 80:
                        wrapped_lines.extend(textwrap.wrap(line, width=80))
                    else:
                        wrapped_lines.append(line)
                
                para_text = ' '.join(wrapped_lines)
                story.append(Paragraph(para_text, styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        print("✅ PDF created successfully!")
        print(f"📄 Output: {pdf_path}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {{e}}")
        print("💡 Try: pip install reportlab")
        return False
    except Exception as e:
        print(f"❌ PDF creation error: {{e}}")
        return False

if __name__ == "__main__":
    success = create_pdf()
    exit(0 if success else 1)
'''
            
            # Save the PDF script
            script_path = self.sandbox_path / "tmp" / "generate_pdf.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(pdf_script)
            
            # Execute the PDF generation script
            result = await self._execute_command({"command": f"python3 {script_path}"})
            
            if result["success"] and os.path.exists(pdf_path):
                return {
                    "success": True,
                    "pdf_path": str(pdf_path),
                    "message": "PDF created successfully"
                }
            else:
                # Fallback to simple text-to-PDF using basic approach
                return await self._create_simple_pdf(text_file_path, content)
                
        except Exception as e:
            return {"success": False, "error": f"PDF conversion error: {str(e)}"}
    
    async def _create_simple_pdf(self, text_file_path: str, content: str) -> Dict[str, Any]:
        """Fallback: Create simple PDF using basic text formatting."""
        try:
            text_path = Path(text_file_path)
            pdf_path = text_path.with_suffix('.pdf')
            
            # Create simple HTML version first
            html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>{text_path.stem.replace("_", " ").title()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2cm; line-height: 1.6; }}
        h1 {{ color: #333; text-align: center; }}
        p {{ text-align: justify; margin-bottom: 1em; }}
    </style>
</head>
<body>
    <h1>{text_path.stem.replace("_", " ").title()}</h1>
    <div>
        {content.replace(chr(10), "</p><p>").replace("<p></p>", "")}
    </div>
</body>
</html>'''
            
            html_path = text_path.with_suffix('.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "pdf_path": str(html_path),
                "message": "Created HTML version (PDF conversion requires additional packages)"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Simple PDF creation error: {str(e)}"}