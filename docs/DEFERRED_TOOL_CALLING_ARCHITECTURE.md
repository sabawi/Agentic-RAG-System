# Deferred Tool Calling Architecture

**Version:** 1.0.3.102
**Date:** 2025-11-16
**Status:** Production Implementation

## Table of Contents
1. [Overview](#overview)
2. [Workflow Stages](#workflow-stages)
3. [Tool Classification](#tool-classification)
4. [Implementation Details](#implementation-details)
5. [POST-LLM Processing](#post-llm-processing)
6. [Future Platform Integrations](#future-platform-integrations)

---

## Overview

### The Problem
Traditional tool calling executes all tools immediately when the tool-calling LLM identifies them. This creates a critical issue: **content-generation tools cannot execute until the primary LLM creates the content they need.**

### The Solution
**Deferred Tool Calling** - A two-phase execution model:
1. **Immediate Phase**: Data collection tools execute BEFORE primary LLM
2. **Deferred Phase**: Content creation/distribution tools execute AFTER primary LLM

### Key Principle
> **The tool-calling LLM identifies what needs to be done, but does not have the content yet. It's punting to the primary LLM to generate content from the context built by data collection tools.**

---

## Workflow Stages

### Stage 1: Tool Calling LLM
**Input:** User prompt
**Process:** Analyze request and identify required tools
**Output:** List of tool calls with parameters

**Example User Prompt:**
```
"Research META, GOOGL stocks and email analysis to sabawi@gmail.com"
```

**Tool Calling LLM Output:**
```json
[
  {"name": "search_stocks", "params": {"symbols": ["META", "GOOGL"]}},
  {"name": "sandboxed_executor", "params": {"filename": "analysis.html", "content": "{{PRIMARY_LLM_OUTPUT}}"}},
  {"name": "secure_email", "params": {"to": "sabawi@gmail.com", "attachment": "analysis.html"}}
]
```

**Note:** `content` parameter is a placeholder - PRIMARY_LLM will generate this.

---

### Stage 2: Tool Classification (Immediate vs Deferred)

**Immediate Tools** (Execute BEFORE Primary LLM):
- ✅ Data collection: `search_*`, `read_*`, `lookup_*`, `fetch_*`
- ✅ Information gathering: `get_stock_data`, `web_search`, `file_read`
- ✅ Context building: Any tool that PROVIDES information

**Deferred Tools** (Execute AFTER Primary LLM):
- ⏸️ File creation: `sandboxed_executor(filename, content)`
- ⏸️ Communication: `secure_email(to, subject, attachment)`
- ⏸️ Publishing: `wordpress_post(title, content)`
- ⏸️ Social media: `twitter_post(text)`, `medium_publish(article)`
- ⏸️ Any tool that CONSUMES primary LLM generated content

**Classification Logic:**
```python
def classify_tool(tool_name, tool_params):
    """Classify tool as immediate or deferred."""

    # Immediate: Data collection tools
    immediate_prefixes = ['search_', 'read_', 'lookup_', 'get_', 'fetch_', 'web_']
    if any(tool_name.startswith(prefix) for prefix in immediate_prefixes):
        return 'IMMEDIATE'

    # Deferred: Tools with content/file/attachment parameters
    deferred_tools = ['sandboxed_executor', 'secure_email', 'wordpress_post',
                      'twitter_post', 'medium_publish', 'social_media_post']
    if tool_name in deferred_tools:
        return 'DEFERRED'

    # Deferred: Any tool with placeholder parameters
    if any('{{PRIMARY_LLM' in str(v) for v in tool_params.values()):
        return 'DEFERRED'

    # Default: Immediate
    return 'IMMEDIATE'
```

---

### Stage 3: Execute Immediate Tool Calls

**Purpose:** Build context for primary LLM by gathering all required data.

**Example Execution:**
```python
immediate_tools = [tool for tool in tools if classify_tool(tool) == 'IMMEDIATE']

context_results = []
for tool in immediate_tools:
    result = execute_tool(tool.name, tool.params)
    context_results.append({
        'tool': tool.name,
        'params': tool.params,
        'result': result
    })

# Example results:
# [
#   {
#     'tool': 'search_stocks',
#     'params': {'symbols': ['META', 'GOOGL']},
#     'result': {
#       'META': {'price': 609.46, 'pe': 24.65, ...},
#       'GOOGL': {'price': 276.41, 'pe': 33.61, ...}
#     }
#   }
# ]
```

---

### Stage 4: Context Building and Optimization

**Purpose:** Consolidate all immediate tool results into optimized context for primary LLM.

**Context Structure:**
```python
primary_llm_context = f"""
### User Request:
{user_prompt}

### Available Data (from tool execution):
{format_tool_results(context_results)}

### Your Task:
Generate comprehensive analysis based on the data above.
The output will be used for: {identify_deferred_tools_purpose(deferred_tools)}

### Output Requirements:
- Format: {determine_format(deferred_tools)}  # HTML if file creation, plain if email only
- Include: {extract_requirements(user_prompt)}
- Structure: {suggest_structure(deferred_tools)}
"""
```

**Optimization Strategies:**
- Remove redundant data
- Summarize large datasets
- Prioritize relevant information
- Structure for easy LLM consumption

---

### Stage 5: Primary LLM Generation

**Input:** Optimized context from immediate tool results
**Process:** Generate complete content based on gathered data
**Output:** Complete response (analysis, report, article, etc.)

**Example:**
```python
primary_llm_prompt = build_context(user_prompt, immediate_tool_results)

complete_llm_response = ""
async for chunk in llm_manager.generate_stream(primary_llm_prompt, **config):
    complete_llm_response += chunk
    yield chunk  # Stream to user

# complete_llm_response now contains:
# - Full stock analysis
# - Tables with data
# - Recommendations
# - Formatted for HTML
```

**Key Point:** Primary LLM has NO knowledge of deferred tools. It simply generates the best possible response based on available context.

---

### Stage 6: POST-LLM Processing

**Purpose:** Prepare primary LLM output for deferred tool execution.

**Critical Steps:**

#### 6.1 Content Cleaning
```python
# Remove LLM artifacts
cleaned_content = _clean_llm_response_content(complete_llm_response)

# Fill template placeholders (if any)
cleaned_content = _fill_template_placeholders(
    cleaned_content,
    user_prompt,
    immediate_tool_results
)
```

#### 6.2 Format Detection and Conversion
```python
# Detect content format
is_html = '<html>' in cleaned_content or '<table>' in cleaned_content
is_markdown = has_markdown_syntax(cleaned_content)

# Convert to required format for deferred tools
if needs_html_output(deferred_tools):
    if is_markdown:
        final_content = html_generator.generate_html_report(
            content=cleaned_content,
            title=extract_title(user_prompt)
        )
    elif not is_html:
        final_content = html_generator.generate_html_report(
            content=cleaned_content,
            title=extract_title(user_prompt)
        )
    else:
        final_content = cleaned_content
```

#### 6.3 File Creation (if needed)
```python
# Extract sandboxed_executor calls
file_creation_tools = [t for t in deferred_tools if t.name == 'sandboxed_executor']

for tool in file_creation_tools:
    # Fill in the PRIMARY_LLM_OUTPUT placeholder
    tool.params['content'] = final_content

    # Execute file creation
    created_file_path = execute_sandboxed_executor(
        filename=tool.params['filename'],
        content=tool.params['content']
    )

    # Store path for communication tools
    file_registry[tool.params['filename']] = created_file_path
```

---

### Stage 7: Execute Deferred Tool Calls

**Purpose:** Execute communication/publishing tools with generated content.

#### 7.1 Resolve File References
```python
for tool in deferred_tools:
    if tool.name in ['secure_email', 'wordpress_post', 'social_media_post']:
        # Replace filename references with actual paths
        if 'attachment' in tool.params:
            filename = tool.params['attachment']
            tool.params['attachment'] = file_registry.get(filename)

        if 'content_file' in tool.params:
            filename = tool.params['content_file']
            tool.params['content'] = read_file(file_registry.get(filename))
```

#### 7.2 Execute Communication Tools
```python
# Email example
if tool.name == 'secure_email':
    send_email(
        to=tool.params['to'],
        subject=tool.params.get('subject', extract_title(complete_llm_response)),
        body=generate_email_body(complete_llm_response),
        attachments=[tool.params['attachment']]
    )

# WordPress example
if tool.name == 'wordpress_post':
    publish_to_wordpress(
        title=tool.params['title'],
        content=tool.params['content'],
        categories=tool.params.get('categories', []),
        featured_image=tool.params.get('featured_image')
    )
```

---

## Implementation Details

### File: `fastapi_server_complete.py`

**Tool Classification Location:** Lines ~8800-8900
```python
def classify_tool_execution_phase(tool_call):
    """Classify tool as immediate or deferred."""
    # Implementation per Stage 2 above
```

**Immediate Execution Location:** Lines ~8900-9000
```python
# Execute immediate tools
immediate_results = await execute_immediate_tools(immediate_tool_calls)
```

**Primary LLM Call Location:** Lines ~9100-9200
```python
# Build context from immediate results
context = build_primary_llm_context(user_prompt, immediate_results)

# Generate with primary LLM
async for chunk in llm_manager.generate_stream(context, **config):
    complete_llm_response += chunk
```

**POST-LLM Processing Location:** Lines ~6690-6800
```python
# Clean and prepare content
report_content = _clean_llm_response_content(complete_llm_response)
report_content = _fill_template_placeholders(report_content, user_prompt, tools_results)

# Create files if needed
if 'sandboxed_executor' in deferred_tools:
    created_file = create_file_with_content(report_content)
```

**Deferred Execution Location:** Lines ~6800-6900
```python
# Execute deferred communication tools
for tool in deferred_tools:
    if tool.name == 'secure_email':
        execute_email_tool(tool, created_file)
    elif tool.name == 'wordpress_post':
        execute_wordpress_tool(tool, created_file)
```

---

## POST-LLM Processing

### Critical Functions

#### `_clean_llm_response_content(raw_content)`
**Location:** fastapi_server_complete.py:6089-6156
**Purpose:** Remove LLM artifacts, JSON markers, metadata
**Input:** Raw LLM output
**Output:** Clean content ready for formatting

**Key Operations:**
- Remove JSON response markers
- Remove model parameters
- Remove timestamps/metadata
- Preserve paragraph structure
- **Critical:** Remove blank lines (but html_generator re-inserts for tables!)

#### `_fill_template_placeholders(content, user_prompt, tools_results)`
**Location:** fastapi_server_complete.py:6158-6259
**Purpose:** Replace placeholders with actual data
**Input:** Cleaned content, context
**Output:** Content with placeholders filled

**Placeholders:**
- `{{USER_PROMPT}}` → Original user request
- `{{TOOLS_RESULTS}}` → Formatted immediate tool results
- `{{DATE}}` → Current date
- `{{TITLE}}` → Extracted/generated title

#### `html_generator.generate_html_report()`
**Location:** utils/html_generator.py:305-450
**Purpose:** Convert markdown/plain text to professional HTML
**Input:** Content (markdown/plain/HTML)
**Output:** Complete HTML document

**Key Features:**
- Markdown detection and conversion (Python-Markdown library)
- Table support with proper blank line insertion (v1.0.3.102 fix)
- Professional CSS styling
- Citation formatting
- Template integration

---

## Deferred Tool Execution Flow

### Email Tool Example

**Tool Definition:**
```python
{
    "name": "secure_email",
    "params": {
        "to": "sabawi@gmail.com",
        "subject": "Stock Analysis Report",
        "attachment": "financial_analysis.html"  # Created by sandboxed_executor
    }
}
```

**Execution Sequence:**
```python
# 1. PRIMARY LLM completes generation
complete_llm_response = "# Stock Analysis\n| Stock | Price |..."

# 2. POST-LLM creates file
file_path = sandboxed_executor(
    filename="financial_analysis.html",
    content=html_generator.generate_html_report(complete_llm_response)
)

# 3. Email tool executes with created file
secure_email(
    to="sabawi@gmail.com",
    subject="Stock Analysis Report",
    attachment=file_path  # Resolved from registry
)
```

### WordPress Tool Example (Future)

**Tool Definition:**
```python
{
    "name": "wordpress_post",
    "params": {
        "title": "{{EXTRACT_FROM_CONTENT}}",
        "content": "{{PRIMARY_LLM_OUTPUT}}",
        "categories": ["Finance", "Analysis"],
        "status": "draft"
    }
}
```

**Execution Sequence:**
```python
# 1. PRIMARY LLM generates article
complete_llm_response = "# Market Analysis...\n\nDetailed content..."

# 2. POST-LLM extracts title and prepares content
title = extract_title(complete_llm_response)  # "Market Analysis"
content = format_for_wordpress(complete_llm_response)  # Clean HTML

# 3. WordPress tool executes
wordpress_post(
    title=title,
    content=content,
    categories=["Finance", "Analysis"],
    status="draft"
)
```

---

## Future Platform Integrations

### Planned Integrations

#### WordPress (Next Implementation)
**Tool Name:** `wordpress_post`
**Classification:** Deferred
**Dependencies:** PRIMARY_LLM_OUTPUT

**Parameters:**
- `title`: Post title (extracted or specified)
- `content`: Post content (PRIMARY_LLM generated HTML/markdown)
- `categories`: Category IDs or names
- `tags`: Tag names
- `status`: 'draft' | 'publish' | 'pending'
- `featured_image`: Image file path (optional)

**Implementation Pattern:**
```python
# Similar to email - execute AFTER primary LLM
wordpress_handler.publish_post(
    wp_url=config['wordpress_url'],
    wp_user=config['wordpress_user'],
    wp_password=config['wordpress_app_password'],
    title=extract_title(complete_llm_response),
    content=format_for_wordpress(complete_llm_response),
    **tool.params
)
```

#### Twitter/X
**Tool Name:** `twitter_post`
**Classification:** Deferred
**Dependencies:** PRIMARY_LLM_OUTPUT (summarized)

**Pattern:**
```python
# Primary LLM generates long-form content
# POST-LLM summarizes to 280 chars
# Twitter tool posts summary with link to full content
```

#### Medium
**Tool Name:** `medium_publish`
**Classification:** Deferred
**Dependencies:** PRIMARY_LLM_OUTPUT

**Pattern:**
```python
# Convert markdown to Medium's format
# Upload images
# Publish article
```

#### LinkedIn
**Tool Name:** `linkedin_post`
**Classification:** Deferred
**Dependencies:** PRIMARY_LLM_OUTPUT

**Pattern:**
```python
# Format for LinkedIn (text + optional document)
# Post to profile or company page
```

---

## Best Practices

### 1. Always Classify Tools Explicitly
```python
# BAD: Assume all tools are immediate
for tool in all_tools:
    execute_tool(tool)

# GOOD: Classify first
immediate = [t for t in all_tools if classify_tool(t) == 'IMMEDIATE']
deferred = [t for t in all_tools if classify_tool(t) == 'DEFERRED']
```

### 2. Build Rich Context for Primary LLM
```python
# BAD: Just pass raw tool results
context = json.dumps(tool_results)

# GOOD: Format for LLM consumption
context = f"""
Based on the following data:

Stock Prices:
- META: $609.46 (P/E: 24.65)
- GOOGL: $276.41 (P/E: 33.61)

Recent News:
- META: AI capex concerns
- GOOGL: First $100B quarter

Analyze and provide recommendations.
"""
```

### 3. Validate Deferred Tool Parameters
```python
# Before executing deferred tools
for tool in deferred_tools:
    if 'attachment' in tool.params:
        if not file_exists(tool.params['attachment']):
            raise ValueError(f"File not found: {tool.params['attachment']}")

    if '{{PRIMARY_LLM' in str(tool.params):
        raise ValueError(f"Placeholder not filled: {tool.params}")
```

### 4. Handle Failures Gracefully
```python
# If primary LLM fails, don't execute deferred tools
try:
    complete_llm_response = await generate_primary_llm()
except Exception as e:
    logger.error(f"Primary LLM failed: {e}")
    # Notify user but don't execute deferred tools
    return error_response("Content generation failed")

# If file creation fails, don't execute email
try:
    file_path = create_file(content)
except Exception as e:
    logger.error(f"File creation failed: {e}")
    # Skip email tool or send without attachment
```

---

## Testing Checklist

### For Each New Platform Integration:

- [ ] Tool classification works correctly (returns 'DEFERRED')
- [ ] Immediate tools execute before primary LLM
- [ ] Primary LLM receives proper context
- [ ] PRIMARY_LLM_OUTPUT placeholder filled correctly
- [ ] File creation (if needed) completes successfully
- [ ] File paths resolved correctly in communication tools
- [ ] Platform-specific formatting applied
- [ ] Error handling for all failure modes
- [ ] Success/failure reported to user
- [ ] Logs capture full execution flow

### Test Scenarios:

1. **Data → Analysis → Email**
   - Search stocks → Generate analysis → Email report

2. **Data → Article → WordPress**
   - Research topic → Write article → Publish to WordPress

3. **Multiple Deferred Tools**
   - Generate content → Email + WordPress + Twitter

4. **Error Recovery**
   - Primary LLM fails → Deferred tools skipped
   - File creation fails → Email without attachment
   - Platform API fails → Retry or notify user

---

## WordPress Implementation Roadmap

### Phase 1: Basic Publishing (Week 1)
- [ ] Create `wordpress_post` tool handler
- [ ] Implement authentication (Application Passwords)
- [ ] Test content publishing (draft mode)
- [ ] Verify POST-LLM integration

### Phase 2: Enhanced Features (Week 2)
- [ ] Category/tag support
- [ ] Featured image upload
- [ ] Custom fields
- [ ] SEO metadata

### Phase 3: Advanced Workflows (Week 3)
- [ ] Schedule publishing
- [ ] Multi-site support
- [ ] Content templates
- [ ] Automated formatting

**Expectation:** "this time it should go fast and smooth" ✅

---

## Conclusion

The deferred tool calling architecture separates **data gathering** (immediate) from **content creation/distribution** (deferred), allowing the primary LLM to generate rich content based on collected context before executing platform-specific publishing actions.

**Key Insight:** The tool-calling LLM identifies the workflow, immediate tools gather data, primary LLM creates content, and deferred tools distribute it. This pattern scales to any publishing platform.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-16
**Next Review:** Before WordPress implementation
