# Universal Post-LLM Arbitrator-Based Parameter Generator

## Executive Summary

This document defines the architecture for a generalized Post-LLM parameter generation system using the Arbitrator LLM to intelligently create tool parameters when tools are auto-executed without initial parameters.

**Status:** Design Complete - Ready for Implementation
**Version:** v1.0.3.111 (proposed)
**Date:** 2025-11-18

## Problem Statement

### Current Issues (v1.0.3.110)

1. **Generic Title Generation** - Returns "Analysis Report" for all content types
2. **Content Pollution** - Posts entire LLM response including conversational disclaimers
3. **LLM Hallucinations** - Includes "I cannot post to WordPress" in published content
4. **Tool-Specific Logic** - Hardcoded fallbacks only for specific tools

### Impact

- Published WordPress posts contain unprofessional conversational text
- Titles are generic and don't reflect actual content
- Same issues affect ALL publishing tools (Medium, Substack, Email, Twitter)
- Poor user experience and manual cleanup required

## Proposed Solution

### Universal Arbitrator-Based Parameter Generator

Replace simple fallback logic with intelligent Arbitrator LLM-powered parameter generation for ANY post-LLM tool execution.

### Architecture Diagram

```
User Request: "write love poem and post to wordpress"
    ↓
Tool-Calling LLM generates tools
    ↓
[Context Overload] → Forgets WordPress tool
    ↓
Primary LLM generates essay + conversational text
    ↓
Verifier detects missing WordPress
    ↓
POST-LLM Execution Path:
    ├─ Check for deferred parameters → NOT FOUND
    ├─ ✨ NEW: Call Universal Parameter Generator
    │       ├─ Load tool schema (WordPress.yaml)
    │       ├─ Call Arbitrator LLM with:
    │       │   - user_prompt
    │       │   - complete_llm_response
    │       │   - tool_schema
    │       │   - tools_results
    │       ├─ Arbitrator analyzes context
    │       ├─ Extracts title: "A Father's Love Poem..."
    │       ├─ Filters content: [poem only, no disclaimers]
    │       ├─ Generates tags: ["poetry", "family", "parenting"]
    │       └─ Returns: {title, content, status, tags}
    └─ Execute WordPress with intelligent parameters
        ↓
    ✅ Professional post published
```

## Implementation Design

### 1. Function Signature Updates

#### Modified: `_execute_missing_tools_post_llm()`

```python
async def _execute_missing_tools_post_llm(
    missing_tools: List[str],
    tool_manager,
    tools_results: str,
    complete_llm_response: str,
    user_prompt: str,
    llm_manager  # ✨ NEW: Add LLM manager for Arbitrator access
) -> str:
```

### 2. New Function: Universal Parameter Generator

```python
async def _generate_intelligent_tool_parameters(
    tool_name: str,
    user_prompt: str,
    complete_llm_response: str,
    tools_results: str,
    tool_manager,
    llm_manager
) -> dict:
    """
    Universal Arbitrator-based parameter generator for post-LLM tool execution.

    Uses Arbitrator LLM to analyze context and generate tool-specific parameters
    based on tool schema and user intent.

    Args:
        tool_name: Name of tool being executed (e.g., "social_media_wordpress")
        user_prompt: Original user request
        complete_llm_response: Full Primary LLM output
        tools_results: Results from previously executed tools
        tool_manager: Tool manager instance for schema access
        llm_manager: LLM manager instance for Arbitrator calls

    Returns:
        dict: Intelligent parameters for tool execution

    Example Returns:
        # For WordPress:
        {
            "title": "A Father's Love Poem to His Teenage Children",
            "content": "<filtered poem content>",
            "status": "draft",
            "tags": ["poetry", "family", "parenting"]
        }

        # For Email:
        {
            "recipient": "user@example.com",
            "subject": "Love Poem for My Children",
            "body": "<filtered content>",
            "attachments": []
        }
    """
```

### 3. Arbitrator Prompt Template

```python
PARAMETER_GENERATION_PROMPT = """
You are a specialized parameter generator for tool execution. Your task is to analyze
user requests and LLM responses to generate optimal, publication-ready parameters.

## Context

**User Request:**
{user_prompt}

**Primary LLM Response:**
{complete_llm_response}

**Tool Results (if any):**
{tools_results_summary}

**Target Tool:**
{tool_name}

**Required Parameters:**
{tool_schema}

## Your Tasks

1. **Extract/Generate Values:** Analyze the context to determine appropriate parameter values
2. **Clean Content:** Remove conversational elements:
   - Disclaimers ("I cannot post...", "Since I don't have access...")
   - Questions ("Would you like me to...")
   - Apologies ("Unfortunately...")
   - Meta-commentary
3. **Structure Content:** Ensure content is publication-ready
4. **Generate Missing Values:** Create intelligent defaults for parameters not explicitly provided

## Tool-Specific Guidelines

### Publishing Tools (WordPress, Medium, Substack):
- **title:** Generate concise, descriptive title from content theme (5-10 words)
- **content:** Extract main content ONLY, remove all conversational elements
- **status:** Default to "draft" unless user explicitly requests "publish"
- **tags:** Generate 3-5 relevant tags from content analysis

### Email Tools:
- **recipient:** Extract from user prompt or error if not found
- **subject:** Generate descriptive subject line
- **body:** Clean content, professional format
- **attachments:** List any referenced attachments

### Social Media (Twitter):
- **content:** Extract key message, limit to 280 chars, create thread if needed
- **media:** Include any referenced media

## Output Format

Return ONLY valid JSON matching the tool schema. No explanations, no markdown code blocks.

Example for WordPress:
{
    "title": "Generated Title Here",
    "content": "Cleaned content here...",
    "status": "draft",
    "tags": ["tag1", "tag2", "tag3"]
}

Generate parameters now:
"""
```

### 4. Tool Schema Registration

Each plugin YAML should define its parameter schema for intelligent generation:

```yaml
# plugins/social_media_wordpress.yaml
name: social_media_wordpress
description: Post content to WordPress blog
deferred_execution: true

parameter_schema:
  title:
    type: string
    required: true
    extraction_hint: "Generate from user intent or content summary (5-10 words)"
    examples:
      - "A Father's Love Poem to His Teenage Children"
      - "Comprehensive Analysis of Technology Stocks"

  content:
    type: string
    required: true
    extraction_hint: "Extract main content only, remove conversational elements"
    filters:
      - "Remove: 'I cannot post', 'Would you like', 'Unfortunately'"
      - "Keep: Actual content (poems, articles, reports)"

  status:
    type: string
    required: false
    default: "draft"
    allowed_values: ["draft", "publish"]
    extraction_hint: "Use 'draft' unless user explicitly says 'publish now'"

  tags:
    type: array
    required: false
    extraction_hint: "Generate 3-5 relevant tags from content analysis"
    examples:
      - ["poetry", "family", "parenting"]
      - ["stocks", "finance", "technology", "investment"]
```

### 5. Implementation Flow

```python
# In _execute_missing_tools_post_llm():

for tool_name in missing_tools:
    # Check for deferred parameters
    deferred_marker = f"DEFERRED: {tool_name}"

    if deferred_marker in tools_results:
        # Existing deferred execution path
        params = extract_deferred_params(...)
    else:
        # ✨ NEW: Universal Arbitrator-based parameter generation
        logger.info(f"🤖 ARBITRATOR PARAM GEN: Generating for {tool_name}")

        try:
            params = await _generate_intelligent_tool_parameters(
                tool_name=tool_name,
                user_prompt=user_prompt,
                complete_llm_response=complete_llm_response,
                tools_results=tools_results,
                tool_manager=tool_manager,
                llm_manager=llm_manager
            )

            logger.info(f"✅ ARBITRATOR GENERATED: {json.dumps(params, indent=2)}")

        except Exception as e:
            logger.error(f"❌ ARBITRATOR PARAM GEN FAILED: {e}")
            # Fallback to simple defaults
            params = _generate_simple_fallback(tool_name, user_prompt, complete_llm_response)

    # Execute tool with generated parameters
    result = await tool_manager.safe_function_call(tool_name, params)
```

## Benefits

### ✅ Consistency
- All tools get intelligent parameter generation
- Uniform quality across publishing platforms

### ✅ Extensibility
- New tools automatically supported via schema
- No hardcoded tool-specific logic

### ✅ Quality
- Arbitrator LLM ensures context-aware parameters
- Professional, publication-ready content

### ✅ Maintainability
- Single implementation for all tools
- Centralized parameter generation logic

### ✅ Architecture
- Follows existing Arbitrator pattern
- Reuses proven infrastructure

## Supported Tools

### Phase 1 (Immediate)
- ✅ social_media_wordpress
- ✅ social_media_medium
- ✅ social_media_substack

### Phase 2 (Next)
- ✅ secure_email_sender
- ✅ social_media_twitter

### Phase 3 (Future)
- ✅ Any tool with deferred execution
- ✅ Auto-discovery from plugin YAML

## Error Handling

```python
try:
    # Arbitrator parameter generation
    params = await _generate_intelligent_tool_parameters(...)

except ArbitratorTimeoutError:
    logger.error("⏱️ Arbitrator timeout - using simple fallback")
    params = _generate_simple_fallback(...)

except ArbitratorInvalidJSONError:
    logger.error("❌ Arbitrator returned invalid JSON - retrying with stricter prompt")
    # Retry once with stricter JSON formatting instructions

except Exception as e:
    logger.error(f"❌ Arbitrator failed: {e} - using simple fallback")
    params = _generate_simple_fallback(...)
```

## Testing Strategy

### Unit Tests
- Test parameter generation for each tool type
- Test content filtering (removal of conversational elements)
- Test title generation from various content types
- Test error handling and fallbacks

### Integration Tests
1. **Love Poem Test** (reported bug)
   - Prompt: "write love poem and post to wordpress"
   - Expected: Title "Love Poem", content [poem only], no disclaimers

2. **Stock Analysis Test**
   - Prompt: "analyze META stock and post to wordpress"
   - Expected: Title includes "META Stock Analysis", professional content

3. **Email Test**
   - Prompt: "email research summary to john@example.com"
   - Expected: Correct recipient, professional subject, clean body

### Regression Tests
- Ensure existing deferred execution still works
- Verify meta-task blocking (v1.0.3.110) still active
- Confirm pattern aggregation verifier still functions

## Performance Considerations

### Arbitrator Call Overhead
- Additional LLM call per auto-executed tool
- Expected latency: 1-3 seconds
- Acceptable for quality improvement

### Caching Strategy (Future)
- Cache parameter templates for common patterns
- Reduce Arbitrator calls for similar requests

### Fallback Strategy
- Simple defaults if Arbitrator fails
- Ensure system never blocks on Arbitrator failure

## Migration Path

### v1.0.3.110 → v1.0.3.111

1. Add `llm_manager` parameter to `_execute_missing_tools_post_llm()`
2. Create `_generate_intelligent_tool_parameters()` function
3. Update tool YAML files with parameter schemas
4. Update function call sites to pass `llm_manager`
5. Add comprehensive logging
6. Test with reported bug cases
7. Deploy and monitor

### Backward Compatibility

- ✅ Existing deferred execution unchanged
- ✅ Meta-task blocking preserved
- ✅ Pattern aggregation verifier preserved
- ✅ Fallback to simple defaults on failure

## Metrics and Monitoring

### Success Metrics
- Parameter generation success rate > 95%
- Content quality (no conversational elements) > 99%
- Title relevance (manual review) > 90%

### Monitoring
- Log Arbitrator call latency
- Track parameter generation failures
- Monitor fallback usage rate
- Alert on high failure rates (> 10%)

## Future Enhancements

### Phase 4 (Future)
1. **Content Structure Detection**
   - Detect poems, articles, reports, code
   - Apply tool-specific formatting

2. **Multi-Language Support**
   - Detect content language
   - Generate parameters in appropriate language

3. **User Preferences**
   - Learn user's title style preferences
   - Remember preferred tags/categories

4. **Smart Defaults Learning**
   - Machine learning on successful generations
   - Improve fallback quality over time

## Conclusion

The Universal Post-LLM Arbitrator-Based Parameter Generator represents a significant architectural improvement that:

- Solves all reported bugs (title, content filtering, hallucinations)
- Generalizes solution for ALL tools (not just WordPress)
- Follows existing architectural patterns (Arbitrator)
- Provides extensible foundation for future enhancements

**Recommendation:** Proceed with implementation of v1.0.3.111

---

## References

- Current implementation: v1.0.3.110 (Meta-task blocking)
- Related: Pattern Aggregation Verifier (v1.0.3.108)
- Related: WordPress Auto-Execution Fallback (v1.0.3.109)

## Change Log

- 2025-11-18: Initial design document created
- Version: v1.0.3.111 (proposed)
