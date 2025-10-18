# Email Workflow Best Practices Guide

**Version**: 1.0.3.10
**Last Updated**: October 18, 2025

---

## Overview

This guide explains how to effectively use email workflows in the Agentic-RAG system. The system intelligently routes email requests through two different execution paths based on your intent:

- **PRE-LLM Execution**: When you want to email existing content (like previous responses)
- **POST-LLM Execution**: When you want the AI to generate new content and email it

---

## Quick Reference

### ✅ Patterns That Always Work

| Pattern | Example | Execution Path |
|---------|---------|----------------|
| **Research + Email** | "Search for latest AI news and email it to user@example.com" | POST-LLM |
| **Email Previous Response** | "Email the above response to user@example.com" | PRE-LLM |
| **Explicit Save + Email** | "Why is the sky blue? Save the answer and email it to user@example.com" | POST-LLM |
| **Email Existing Documents** | "Find my resume and email it to recruiter@company.com" | PRE-LLM |

---

## Detailed Workflow Patterns

### Pattern 1: Research + Email (Single Prompt)

**Use Case**: Search for information and email the results in one request

**Examples**:
```
✅ "Search the web for latest AI developments and email the results to john@example.com"
✅ "Get news about climate change and send it as HTML attachment to scientist@university.edu"
✅ "Find papers about quantum computing and email them to researcher@lab.org"
✅ "Search for stock market analysis and email it to investor@firm.com"
```

**How It Works**:
1. Tool Calling LLM detects search tools + email request
2. Search tools execute and gather data
3. File creation deferred to POST-LLM
4. Primary LLM formats the search results as HTML
5. File created with formatted content
6. Email sent with attachment

**What You'll See**:
- AI processes your search
- Generates formatted HTML report
- Confirms email sent
- You receive the email with attachment

---

### Pattern 2: Email Previous Response (2-Step)

**Use Case**: First get a response, then email that exact response

**Examples**:
```
Step 1: "What's the latest news about technology?"
Step 2: "Email the above response to user@example.com"

Step 1: "Summarize the benefits of renewable energy"
Step 2: "Send the above FULL and COMPLETE response VERBATIM to eco@domain.org"

Step 1: "Explain quantum entanglement in simple terms"
Step 2: "Email this response to student@school.edu"
```

**How It Works**:
1. First prompt: AI generates response
2. Second prompt: System detects "above", "this", or "previous"
3. File created with existing conversation content (PRE-LLM)
4. Email sent immediately
5. Primary LLM confirms: "✅ Email sent to..."

**What You'll See**:
- First: AI's full response to your question
- Second: Confirmation message that email was sent
- **Note**: You won't see HTML code, just a clean status message

**Trigger Keywords** (for PRE-LLM):
- "email the above"
- "send this"
- "email it"
- "previous response"
- "verbatim"
- "full and complete response"

---

### Pattern 3: Generate Content + Email (Explicit Save)

**Use Case**: Create new content and email it in one request

**Examples**:
```
✅ "Why is the sky blue? Save the answer and email it as HTML attachment to curious@example.com"
✅ "Write a summary of machine learning. Create a file and email it to student@university.edu"
✅ "Explain photosynthesis. Save the explanation and send it to teacher@school.org"
✅ "Create a report on stock market trends. Save as HTML and email to analyst@firm.com"
```

**How It Works**:
1. Tool Calling LLM detects "save" + email request
2. Tools deferred to POST-LLM
3. Primary LLM generates full content
4. File created with generated content
5. Email sent with attachment

**What You'll See**:
- AI generates the content you requested
- Confirmation that file was created and email sent

**Important Keywords**:
- "save"
- "create file"
- "generate file"
- "save as HTML"

---

### Pattern 4: Email Existing Documents

**Use Case**: Find documents in your system and email them

**Examples**:
```
✅ "Find my resume and email it to recruiter@company.com"
✅ "Search for Gaza story document and send it to editor@news.org"
✅ "Find quantum research documents and email them to professor@university.edu"
```

**How It Works**:
1. Document search finds matching files
2. Email sent with found documents as attachments (PRE-LLM)
3. Primary LLM confirms what was sent

---

## ❌ Patterns to Avoid (Known Limitations)

### Limitation: Implicit Email Patterns

**These patterns may not work as expected:**

```
❌ "Why is the sky blue? email the answer to user@example.com"
   → AI gives you the answer but says "you can email it yourself"
   → No automatic file creation or email sending

❌ "What are the benefits of exercise? send the result to health@example.com"
   → Same issue

❌ "Explain gravity. email it to student@school.edu"
   → Same issue
```

**Why?** The Tool Calling LLM doesn't recognize these as file creation + email requests because there's no explicit "save" keyword and no "above" reference to existing content.

---

## Workarounds for Implicit Patterns

If you want to use a simple pattern like "Question? email the answer...", here are your options:

### Workaround 1: Add "Save" Keyword (Recommended)

**Before** (doesn't work):
```
❌ "Why is the sky blue? email the answer to user@example.com"
```

**After** (works):
```
✅ "Why is the sky blue? Save the answer and email it to user@example.com"
```

---

### Workaround 2: Use 2-Step Process

**Step 1**: Ask your question
```
"Why is the sky blue?"
```

**Step 2**: Email the response
```
"Email the above response to user@example.com"
```

---

### Workaround 3: Use Research Pattern

For research questions, frame it as a search:

**Before** (doesn't work):
```
❌ "What's the latest AI news? email it to tech@example.com"
```

**After** (works):
```
✅ "Search for latest AI news and email it to tech@example.com"
```

---

## Best Practices

### DO:
- ✅ Use explicit keywords: "save", "create file", "email the above"
- ✅ Be specific about format: "as HTML attachment"
- ✅ Include full email addresses in your prompts
- ✅ Use descriptive requests for better file naming
- ✅ For multi-step workflows, use "above" or "previous response"

### DON'T:
- ❌ Use vague references like "email it" without "save" or "above"
- ❌ Expect implicit email patterns to work without keywords
- ❌ Omit email addresses (system won't guess)

---

## Understanding Execution Paths

### PRE-LLM Execution (Fast)

**When**: Content already exists (previous responses, existing documents)

**Flow**:
```
Your Request
    ↓
Tool Calling LLM detects "email the above"
    ↓
File created with existing content
    ↓
Email sent immediately
    ↓
Primary LLM confirms: "✅ Email sent"
```

**User Experience**: Clean status message, no HTML code visible

---

### POST-LLM Execution (Content Generation)

**When**: New content needs to be generated

**Flow**:
```
Your Request
    ↓
Tool Calling LLM detects tools needed
    ↓
Tools deferred (file creation, email)
    ↓
Primary LLM generates content
    ↓
File created with generated content
    ↓
Email sent with attachment
    ↓
Confirmation message
```

**User Experience**: See the generated content, then confirmation

---

## Examples by Use Case

### Academic Research
```
✅ "Find papers about CRISPR gene editing and email them to researcher@university.edu"
✅ "Search for latest climate science research and email summary to professor@college.org"
```

### News & Current Events
```
✅ "Get the latest news about technology and send it as HTML to tech@example.com"
✅ "Search for Gaza news and email the report to editor@newsroom.com"
```

### Business Reports
```
✅ "Analyze AAPL stock performance. Save the analysis and email to investor@firm.com"
✅ "Search for market trends in AI. Create report and email to analyst@company.org"
```

### Personal Use
```
Step 1: "Summarize the health benefits of meditation"
Step 2: "Email the above response to wellness@example.com"
```

---

## Troubleshooting

### Problem: "AI gave me an answer but didn't email it"

**Solution**: Add "save" keyword:
```
"[Your question]? Save the answer and email it to..."
```

### Problem: "I saw HTML code instead of a status message"

**Cause**: This happens in POST-LLM workflows when AI generates content

**Solution**: This is expected behavior. The AI is showing you the generated content before emailing it. You'll still receive the email with the attachment.

### Problem: "Email wasn't sent at all"

**Check**:
1. Did you include an email address in your prompt?
2. Did you use one of the recommended patterns?
3. Try adding "save" or using 2-step process

---

## Quick Decision Tree

```
Do you want to email existing content (previous response)?
├─ YES → Use "Email the above response to..."
└─ NO → Are you asking for research/search?
    ├─ YES → Use "Search for X and email it to..."
    └─ NO → Use "Ask your question. Save the answer and email to..."
```

---

## Support

For issues or questions:
- Check this guide for recommended patterns
- Review the changelog: `docs/housekeeping/status-tracking/CHANGELOG_v1.0.3.10.md`
- Report issues: https://github.com/anthropics/claude-code/issues

---

**Version History**:
- v1.0.3.10 (Oct 18, 2025): Initial guide created with smart deferral documentation
