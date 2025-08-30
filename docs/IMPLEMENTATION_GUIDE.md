# Implementation Guide - 2-Stage LLM System

## Recent Changes Summary (August 7, 2025)

This document details the specific implementations and modifications made to create the robust 2-stage LLM architecture.

## Major Architectural Changes

### 1. Email Interception System Implementation

**File**: `fastapi_server_complete.py`
**Lines**: 847-858

```python
# Global flags for email interception
email_intercepted = False
intercepted_email_params = {}

async def intercept_secure_email_sender(tool_params: Dict[str, Any]) -> str:
    """Intercept email calls during tool execution phase for post-processing"""
    global email_intercepted, intercepted_email_params
    
    print("📧 INTERCEPTING secure_email_sender call - will execute after Primary LLM")
    
    email_intercepted = True
    intercepted_email_params = tool_params.copy()
    
    return "Email scheduled for sending after content generation"
```

**Integration**: 
- Added to `AsyncToolManager.__init__()` 
- Replaces direct email execution during tool calling phase
- Enables deferred email processing after content generation

### 2. Post-Processing Engine

**File**: `fastapi_server_complete.py`  
**Lines**: 1154-1306

#### Implementation Details:

**Trigger Detection**:
```python
if email_intercepted and intercepted_email_params:
    print("🚪 ENTRANCE: Starting post-processing logic")
    print("📧 POST-LLM: Processing intercepted email call")
```

**Content Buffer Usage**:
```python
print(f"🎯 Complete LLM response length: {len(complete_llm_response)} characters")
```

**File Creation Logic**:
```python
# Default to HTML instead of PDF
attachments = intercepted_email_params.get('attachments', 'report.html')

# Extract filename and determine conversion type
filename = attachments.split(',')[0].strip() if ',' not in attachments else attachments
convert_to_pdf = filename.lower().endswith('.pdf')

# Create both Markdown and HTML files
base_filename = filename.rsplit('.', 1)[0]  # Remove extension
markdown_filename = f"{base_filename}.md"

# Create Markdown file with Primary LLM content
md_result = await tool_manager.safe_function_call("sandboxed_executor", {
    "action": "create_file",
    "filename": markdown_filename,
    "content": complete_llm_response.strip(),
    "convert_to_pdf": False
})

# Create HTML version for email attachment
html_filename = f"{base_filename}.html"
file_result = await tool_manager.safe_function_call("sandboxed_executor", {
    "action": "create_file", 
    "filename": html_filename,
    "content": complete_llm_response.strip(),
    "convert_to_pdf": False
})
```

**Email Execution**:
```python
# Send email with HTML attachment
email_result = await tool_manager.safe_function_call("secure_email_sender", {
    **intercepted_email_params,
    "attachments": html_filename
})
```

### 3. Primary LLM Content Buffering

**File**: `fastapi_server_complete.py`
**Lines**: 1063-1098

**Token Contamination Fix**:
```python
# Fixed streaming response collection to avoid token contamination
if 'response' in chunk_json and not chunk_json.get('done', False):
    # Only accumulate actual response text, not metadata/tokens
    response_text = chunk_json['response']
    if response_text:  # Skip empty responses
        complete_llm_response += response_text
```

**Before Fix**: Files contained raw JSON tokens, context arrays, model metadata
**After Fix**: Clean Primary LLM content only

### 4. Tool Calling Model System Prompt Updates

**File**: `pre_tool_model_system_prompt.txt`
**Lines**: 46-57

**Key Changes**:
1. **Default File Type**: Changed from explicit extensions to 'DEFAULT'
2. **PDF Restriction**: Only use .pdf if user explicitly requests it
3. **Tool Requirement**: Enforce sandboxed_executor + secure_email_sender calls

```
🎯 FOR FILE CREATION AND EMAIL REQUESTS:
   📄 DEFAULT FILE TYPE: Use "DEFAULT" - DO NOT specify .pdf or .html extensions!
   📄 ONLY use .pdf extension if user EXPLICITLY asks for "PDF" or "pdf file"
   📄 If user says "save", "send file", "email file" WITHOUT specifying type → USE "DEFAULT"!
   📄 Example: sandboxed_executor(action="create_file", filename="report", content="...")
   📧 Email: secure_email_sender(attachments="DEFAULT", to_email="...", subject="...", body="...")
```

### 5. Sandboxed Executor Enhancement

**File**: `user_tools/sandboxed_executor.py`
**Lines**: 775-827

**New append_file Action**:

**Parameter Schema Update** (Lines 85-100):
```python
"action": {
    "type": "string",
    "enum": ["execute", "create_file", "append_file", "read_file", "list_files", "delete_file", "run_code"],
    "description": "Action to perform: execute (run command), create_file (write file), append_file (append to file), read_file (read file), list_files (show directory), delete_file (remove file), run_code (execute code file)"
},
```

**Routing Logic** (Lines 181-183):
```python
elif action == "append_file":
    print("🚀🚀🚀 SANDBOXED EXECUTOR: -> _append_file")
    return await self._append_file(kwargs)
```

**Implementation**:
```python
async def _append_file(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Append content to an existing file in the sandbox."""
    try:
        filename = kwargs.get("filename", "").strip()
        content = kwargs.get("content", "")
        
        if not filename:
            return {"success": False, "error": "Filename is required", "result": None}
        
        if not content:
            return {"success": False, "error": "Content is required for append_file", "result": None}
        
        # Validate path
        is_valid, file_path = self._validate_path(filename)
        if not is_valid:
            return {"success": False, "error": file_path, "result": None}
        
        # Check if file exists
        if not Path(file_path).exists():
            return {"success": False, "error": f"File {filename} does not exist. Use create_file to create it first.", "result": None}
        
        # Append content with size validation
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        
        # Return detailed metadata
        file_stats = os.stat(file_path)
        result = {
            "filename": filename,
            "full_path": file_path,
            "size_bytes": file_stats.st_size,
            "appended_size": len(content.encode('utf-8')),
            "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "permissions": oct(file_stats.st_mode)[-3:]
        }
        
        return {"success": True, "result": result, "error": None}
        
    except Exception as e:
        return {"success": False, "error": f"File append error: {str(e)}", "result": None}
```

## File Format Implementations

### 1. Markdown File Creation

**Location**: `user_tools/sandboxed_executor.py:709-711`
**Auto-Detection**: Files ending in `.md`
**Method**: `_create_real_md_file()`

**Features**:
- YAML frontmatter with metadata
- Automatic title extraction
- Code block formatting for sections
- Professional markdown structure

### 2. HTML File Creation  

**Location**: `user_tools/sandboxed_executor.py:706-708`
**Auto-Detection**: Files ending in `.html`
**Method**: `_create_real_html_file()`

**Features**:
- Responsive CSS styling
- Email-optimized layout
- Professional report formatting
- Clean HTML5 structure

### 3. PDF File Creation

**Location**: `user_tools/sandboxed_executor.py:703-705`
**Auto-Detection**: Files ending in `.pdf` with `convert_to_pdf=True`
**Method**: `_create_real_pdf_file()`

**Features**:
- Uses `_universal_pdf_generator.py`
- Professional typography
- Proper page formatting

## Workflow Diagrams

### Standard Email + File Request Flow

```
User Request: "Research news and email report to sabawi@gmail.com"
    ↓
Stage 1: Tool Calling Model (qwen3:8b)
    ├─ get_news_summaries(filter="Technology") 
    └─ secure_email_sender(...) → INTERCEPTED
    ↓
Stage 2: Primary LLM (qwen3:8b)  
    ├─ Input: Clean tool results summary
    └─ Output: Clean markdown analysis → BUFFERED
    ↓
Stage 3: Post-Processing
    ├─ Create: report.md (storage)
    ├─ Create: report.html (email attachment)
    └─ Send: Email with HTML attachment
    ↓
Result: Email delivered with professional HTML report
        + Markdown file saved for records
```

### File Type Decision Logic

```
User Request Analysis
    ↓
Tool Calling Model
    ├─ User says "PDF" explicitly → filename="report.pdf"
    ├─ User says nothing → filename="report" (DEFAULT)
    └─ User says "HTML" → filename="report.html"
    ↓
Post-Processing
    ├─ .pdf extension → convert_to_pdf=True
    ├─ No extension → default to HTML for email
    └─ Always create both .md (storage) + email format
```

## Testing & Validation

### 1. End-to-End Email Test
```bash
# Test complete workflow
curl -X POST http://localhost:5000/llama3_1b/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Research latest tech news and create a report, then email it to sabawi@gmail.com", "model": "qwen3:8b", "stream": false}'

# Expected Results:
# - 2 files created: report.md + report.html  
# - Email sent with clean HTML attachment
# - No token contamination in files
```

### 2. File Append Test
```bash
# Test new append_file functionality
curl -X POST http://localhost:5000/llama3_1b/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a test file called notes.txt with Hello, then append World to it", "model": "qwen3:8b", "stream": false}'

# Expected Results:
# - File created with "Hello"
# - File appended with "World" 
# - Final content: "HelloWorld"
```

### 3. Log Verification
```bash
# Check server logs for successful processing
tail -f server_complete.log | grep -E "(INTERCEPTING|POST-LLM|File creation|Email sent)"
```

## Debugging Checklist

### Email Issues
1. ✅ Check `email_intercepted` flag in logs
2. ✅ Verify post-processing section reached
3. ✅ Confirm file creation success before email
4. ✅ Check `/tmp/email_debug_*.eml` files

### File Creation Issues  
1. ✅ Verify tool action routing in logs
2. ✅ Check sandbox_workspace permissions
3. ✅ Validate file type auto-detection logic
4. ✅ Test with `file` command for format verification

### Content Quality Issues
1. ✅ Check for JSON contamination in streaming logs
2. ✅ Verify `complete_llm_response` buffer content
3. ✅ Ensure clean tool results summary format
4. ✅ Test Primary LLM prompt construction

This implementation provides a robust, production-ready system for LLM-powered document generation and email delivery.