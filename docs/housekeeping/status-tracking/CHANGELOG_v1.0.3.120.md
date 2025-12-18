# Changelog v1.0.3.120

**Release Date:** 2025-12-18

## Summary
This release addresses two critical issues discovered in research prompts: hallucinated URLs and literal escape sequences in HTML output. The fixes are generalized to work across all research and output scenarios.

---

## Bug Fixes

### 1. URL Hallucination Prevention
**Problem:** The local LLM was fabricating URLs based on business/organization names rather than using verified URLs from search results.

**Root Cause:** No explicit rules preventing URL fabrication when search_web() wasn't called.

**Fix Applied:**
- **`primary_model_system_prompt.txt`**: Added `SOURCE VERIFICATION RULES (CRITICAL)` section
  - ALL URLs must come from tool results
  - Never fabricate URLs based on business/organization names
  - Common hallucination patterns explicitly prohibited

- **`pre_tool_model_system_prompt.txt`**: Added `URL SOURCE VERIFICATION RULE (CRITICAL)` in Research Queries section
  - Requires search_web() for any query expecting URLs/citations
  - Explicit examples for local business queries
  - Clear rule that Primary LLM can only cite URLs from tool results

### 2. Literal Escape Sequences in HTML Output
**Problem:** JSON-encoded content contained escaped newlines (`\n`) that appeared literally in HTML files instead of being converted to actual newlines.

**Root Cause:** JSON escape sequences from conversation history were not being normalized before output.

**Fix Applied:**
- **NEW FILE: `utils/content_sanitizer.py`** - Central content sanitization utility
  - `sanitize_content()` - Main function for all output
  - `normalize_escape_sequences()` - Converts `\\n` to actual newlines
  - `normalize_unicode()` - Handles problematic Unicode characters (dashes, smart quotes, etc.)
  - Platform-specific sanitizers: `sanitize_for_html()`, `sanitize_for_email()`, `sanitize_for_pdf()`

- **`utils/html_generator.py`**: Updated to call `sanitize_for_html()` on content

- **`user_tools/sandboxed_executor.py`**: Updated `_create_file()` method to call `sanitize_content()` on all file content

### 3. Missing HTML Attachment in Email
**Problem:** Follow-up prompts like "Email the above response as HTML attachment" were not creating the HTML file before sending email.

**Root Cause:** The verifier pattern matching only detected `email_required` pattern, not that `sandboxed_executor` was also needed.

**Fix Applied:**
- **`fastapi_server_complete.py`**: Added new `html_attachment_email` pattern
  - Triggers: "html attachment", "formatted html", "neatly formatted html", "email the above", "attachment to", etc.
  - Required tools: `["sandboxed_executor", "secure_email_sender"]`
  - Ensures both file creation and email sending occur in sequence

---

## New Features

### Content Sanitizer Utility
New centralized utility (`utils/content_sanitizer.py`) that handles:
- JSON escape sequence normalization (`\\n` -> newline, `\\t` -> tab)
- Unicode character normalization (smart quotes -> regular quotes, em-dash -> hyphen)
- Whitespace cleanup (excessive newlines, trailing spaces)
- Platform-specific sanitization for HTML, email, PDF, and social media

---

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `version.py` | Modified | Version 1.0.3.119 -> 1.0.3.120 |
| `README.md` | Modified | Updated version badge |
| `primary_model_system_prompt.txt` | Modified | Added SOURCE VERIFICATION RULES |
| `pre_tool_model_system_prompt.txt` | Modified | Added URL SOURCE VERIFICATION RULE, RTICROS framework |
| `fastapi_server_complete.py` | Modified | Added html_attachment_email pattern |
| `utils/html_generator.py` | Modified | Added content sanitizer import and call |
| `user_tools/sandboxed_executor.py` | Modified | Added content sanitizer import and call in _create_file |
| `utils/content_sanitizer.py` | **NEW** | Central content sanitization utility |

---

## Testing

### Verified Scenarios
1. **Research Query with URLs**: Veterinary medicine job search in upstate NY - URLs now come from actual search_web() results (~80% valid)
2. **HTML File Creation**: No literal `\n` characters in generated HTML files
3. **HTML Email Attachment**: Pattern now correctly triggers both file creation and email sending

---

## Dependencies
No new dependencies added.

---

## Breaking Changes
None.

---

## Migration Guide
No migration required. All changes are backward compatible.
