# 2-Stage LLM Architecture System Documentation

## Overview

This system implements a sophisticated 2-stage LLM processing architecture that separates tool orchestration from content generation, enabling robust email delivery with intelligent file attachment handling.

## Architecture Components

### Stage 1: Tool Calling Model (qwen3:8b)
**Purpose**: Orchestrate data gathering and tool execution
**Location**: `pre_tool_model_system_prompt.txt`

**Key Features**:
- Enforces strict tool calling protocols
- Uses 'DEFAULT' file type specification to avoid hardcoded PDF generation
- Implements nuclear multi-tool enforcement (minimum 2 tools required)
- Intercepts email calls for post-processing

### Stage 2: Primary LLM (qwen3:8b) 
**Purpose**: Generate high-quality analysis and content
**Input**: Cleaned tool results summary
**Output**: Clean markdown content for post-processing

### Stage 3: Post-Processing Engine
**Purpose**: Handle file creation and email delivery
**Location**: `fastapi_server_complete.py:1154-1306`

## Detailed Implementation

### 1. Email Interception System

**Location**: `fastapi_server_complete.py:847-858`
```python
# Global email interception flags
email_intercepted = False
intercepted_email_params = {}

async def intercept_secure_email_sender(tool_params: Dict[str, Any]) -> str:
    global email_intercepted, intercepted_email_params
    email_intercepted = True
    intercepted_email_params = tool_params.copy()
    return "Email scheduled for sending after content generation"
```

**Trigger**: Any `secure_email_sender` tool call during Stage 1
**Result**: Email parameters stored globally, actual sending deferred to post-processing

### 2. Primary LLM Content Buffering

**Location**: `fastapi_server_complete.py:1063-1098`
```python
# Stream processing with token contamination prevention
if 'response' in chunk_json and not chunk_json.get('done', False):
    response_text = chunk_json['response']
    if response_text:  # Skip empty responses
        complete_llm_response += response_text
```

**Purpose**: Capture clean Primary LLM output without JSON metadata contamination
**Result**: `complete_llm_response` contains pure content for file creation

### 3. Post-Processing Logic

**Trigger Condition**: `email_intercepted = True` after Primary LLM completion
**Location**: `fastapi_server_complete.py:1154-1306`

#### Step 1: File Type Detection & Default Handling
```python
attachments = intercepted_email_params.get('attachments', 'report.html')  # Default to HTML
filename = attachments.split(',')[0].strip() if ',' not in attachments else attachments
convert_to_pdf = filename.lower().endswith('.pdf')
```

#### Step 2: Dual File Creation (Markdown + HTML)
```python
# Create Markdown file for storage
base_filename = filename.rsplit('.', 1)[0]
markdown_filename = f"{base_filename}.md"

md_result = await tool_manager.safe_function_call("sandboxed_executor", {
    "action": "create_file",
    "filename": markdown_filename,
    "content": complete_llm_response.strip(),
    "convert_to_pdf": False
})

# Create HTML file for email attachment
html_filename = f"{base_filename}.html"
file_result = await tool_manager.safe_function_call("sandboxed_executor", {
    "action": "create_file", 
    "filename": html_filename,
    "content": complete_llm_response.strip(),
    "convert_to_pdf": False
})
```

#### Step 3: Email Delivery
```python
email_result = await tool_manager.safe_function_call("secure_email_sender", {
    **intercepted_email_params,
    "attachments": html_filename  # Use HTML file for email
})
```

### 4. Tool Calling Model Instructions

**Location**: `pre_tool_model_system_prompt.txt:46-57`

**Key Directives**:
```
🎯 FOR FILE CREATION AND EMAIL REQUESTS:
   📄 DEFAULT FILE TYPE: Use "DEFAULT" - DO NOT specify .pdf or .html extensions!
   📄 ONLY use .pdf extension if user EXPLICITLY asks for "PDF" or "pdf file"
   📄 If user says "save", "send file", "email file" WITHOUT specifying type → USE "DEFAULT"!
   📄 Example: sandboxed_executor(action="create_file", filename="report", content="...")
   📧 Email: secure_email_sender(attachments="DEFAULT", to_email="...", subject="...", body="...")
   
   ⚠️ CRITICAL FILE CREATION RULES:
   🚫 NEVER add .pdf extension unless user explicitly requested PDF!
   🚫 NEVER add .html extension - let post-processing handle format!
   ✅ USE simple filenames like "report", "analysis", "summary"
   ✅ Always include sandboxed_executor() call for file creation + secure_email_sender() for email!
```

### 5. Enhanced Sandboxed Executor Tool

**New Feature**: `append_file` action
**Location**: `user_tools/sandboxed_executor.py:775-827`

```python
async def _append_file(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Append content to an existing file in the sandbox."""
    filename = kwargs.get("filename", "").strip()
    content = kwargs.get("content", "")
    
    # Validation: file exists, content provided, size limits
    # Safe append operation with detailed result metadata
```

**Supported Actions**:
- `execute` - run command
- `create_file` - write file  
- `append_file` - append to existing file (NEW)
- `read_file` - read file
- `list_files` - show directory
- `delete_file` - remove file
- `run_code` - execute code file

### 6. File Format Handling

#### Markdown Files (.md)
**Purpose**: Primary storage format for LLM-generated content
**Features**: 
- YAML frontmatter with metadata
- Clean markdown formatting
- Automatic section headers with code blocks for styling

#### HTML Files (.html)
**Purpose**: Email attachments with professional presentation
**Features**:
- Responsive CSS styling
- Professional report formatting
- Email-optimized layout
- Clean HTML structure converted from markdown

#### PDF Files (.pdf)
**Purpose**: High-quality document generation (when explicitly requested)
**Features**:
- Uses `_universal_pdf_generator.py`
- Professional typography
- Proper page formatting

### 7. Email Processing Pipeline

#### Stage 1 (Tool Calling Model)
1. User requests file creation + email
2. Model calls `secure_email_sender` 
3. Email intercepted and deferred
4. Parameters stored globally

#### Stage 2 (Primary LLM)
1. Receives clean tool results summary
2. Generates analysis content
3. Content buffered without JSON contamination

#### Stage 3 (Post-Processing)
1. Detects email interception flag
2. Creates dual files (Markdown + HTML)
3. Sends email with HTML attachment
4. Provides completion confirmation

## Benefits

### 1. Clean Content Generation
- No LLM token contamination in files
- Pure markdown content from Primary LLM
- Professional HTML formatting for emails

### 2. Robust File Type Handling
- Intelligent defaults (HTML for email, Markdown for storage)
- User intent preservation
- Flexible format conversion

### 3. Reliable Email Delivery
- Deferred execution prevents race conditions
- Complete file creation before email sending
- Proper MIME encoding for attachments

### 4. Architectural Separation
- Tool orchestration separate from content generation
- Clean interfaces between components
- Easy debugging and maintenance

## Configuration Files

### Core Server
- `fastapi_server_complete.py` - Main server with 2-stage architecture
- `start_complete.sh` / `stop_complete.sh` - Server management scripts

### Tool Calling Model
- `pre_tool_model_system_prompt.txt` - Nuclear enforcement instructions

### Tools
- `user_tools/sandboxed_executor.py` - Enhanced file operations
- `user_tools/secure_email_sender.py` - Email delivery system
- `user_tools/_universal_pdf_generator.py` - PDF generation

### Memory
- `CLAUDE.md` - System debugging procedures and critical fixes

## Testing Procedures

### End-to-End Email Test
```bash
curl -X POST http://localhost:5000/llama3_1b/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Research latest tech news and create a report, then email it to sabawi@gmail.com", "model": "qwen3:8b", "stream": false}'
```

### File Creation Test
```bash
curl -X POST http://localhost:5000/llama3_1b/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a test file and append content to it", "model": "qwen3:8b", "stream": false}'
```

## Troubleshooting

### Email Attachment Issues
1. Check `email_intercepted` flag status
2. Verify post-processing execution in logs
3. Confirm file creation success before email sending
4. Check email debug files in `/tmp/email_debug_*.eml`

### File Creation Problems
1. Verify sandboxed_executor tool availability
2. Check file permissions in sandbox_workspace
3. Validate file extension handling logic
4. Test file type auto-detection

### Primary LLM Content Issues
1. Check for JSON token contamination in streaming
2. Verify complete_llm_response buffer content
3. Ensure clean tool results summary formatting

This architecture provides a robust, scalable foundation for LLM-powered document generation and email delivery systems.