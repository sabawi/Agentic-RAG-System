# Social Media Plugin Manual Testing Guide

**Document Type**: Test Procedure
**Created**: 2025-10-18
**Last Updated**: 2025-10-18
**Status**: Phase 1 Complete - Ready for Manual Testing

---

## Overview

This guide provides step-by-step instructions for manually testing the social media publishing plugins with real Substack accounts. Use this guide after automated unit and integration tests pass.

**Prerequisites**:
- ✅ Unit tests passing (`pytest tests/utilities/test_social_media_handlers.py`)
- ✅ Integration tests passing (`python3 tests/utilities/test_social_media_integration.py`)
- ✅ Dependencies installed (`pip install -r requirements.txt`)
- ✅ Real Substack account for testing

---

## 1. Environment Setup

### 1.1. Create Test Substack Account (if needed)

1. Go to [substack.com](https://substack.com)
2. Sign up for a free account
3. Create a test publication (e.g., "Test Blog for Development")
4. Note your login credentials

### 1.2. Configure Environment Variables

Edit your `.env` file (NOT `.env.example`):

```bash
# Add these lines to your .env file
SUBSTACK_TEST_EMAIL=your_actual_test_email@example.com
SUBSTACK_TEST_PASSWORD=your_actual_test_password_here
```

**IMPORTANT**:
- Never commit `.env` to git
- Use a dedicated test account, not your production account
- Verify credentials work by logging into Substack web interface first

### 1.3. Verify Plugin Registration

```bash
# Ensure plugin is discovered
cd /home/sabawi/Development/flaskserver
python3 -c "
from plugins.plugin_manager import PluginManager
from pathlib import Path
import asyncio

async def check():
    manager = PluginManager(Path('plugins'), {'plugin_defaults': {}})
    await manager.initialize()
    plugins = manager.get_available_plugins()
    social = [p for p in plugins if 'social_media' in p['name']]
    print(f'Found {len(social)} social media plugin(s):')
    for p in social:
        print(f'  - {p[\"name\"]} v{p[\"version\"]}')

asyncio.run(check())
"
```

Expected output:
```
Found 1 social media plugin(s):
  - social_media_substack_test v1.0.0
```

---

## 2. Manual Test Cases

### Test Case 1: Basic Post Publication

**Objective**: Verify plugin can publish a simple post to Substack

**Steps**:

1. Create test script `test_manual_publish.py`:

```python
#!/usr/bin/env python3
"""Manual test: Publish basic post to Substack"""
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from plugins.plugin_manager import PluginManager

async def test_basic_publish():
    # Initialize plugin manager
    plugins_dir = project_root / 'plugins'
    config = {
        'plugin_defaults': {
            'execution': {'timeout': 30},
            'security': {
                'input_validation': {'max_string_length': 1000000},
                'output_validation': {'max_output_size': 10485760}
            },
            'error_handling': {
                'retry': {'enabled': True, 'max_attempts': 3},
                'degraded_mode': {'enabled': False}
            }
        },
        'python_executable': 'python3'
    }

    manager = PluginManager(plugins_dir, config)
    await manager.initialize()

    # Publish test post
    print("\n🚀 Publishing test post to Substack...")
    result = await manager.execute_plugin(
        'social_media_substack_test',
        {
            'title': 'Test Post from Plugin System',
            'content': '''
                <h1>Welcome to the Test</h1>
                <p>This is a test post published via the social media plugin system.</p>
                <p>It demonstrates:</p>
                <ul>
                    <li>HTML content rendering</li>
                    <li>Plugin integration</li>
                    <li>Automated publishing workflow</li>
                </ul>
                <p><strong>If you see this, the plugin is working!</strong></p>
            ''',
            'visibility': 'everyone',
            'send_email': False  # Don't spam subscribers
        }
    )

    # Display results
    print("\n" + "="*70)
    if result['success']:
        print("✅ POST PUBLISHED SUCCESSFULLY!\n")
        print(f"Post URL: {result['result']['post_url']}")
        print(f"Post ID: {result['result']['post_id']}")
        print(f"Title: {result['result']['title']}")
        print(f"Platform: {result['result']['platform']}")
        print(f"Visibility: {result['result']['visibility']}")

        if 'metadata' in result:
            print(f"\nExecution time: {result['metadata'].get('execution_time', 0):.3f}s")
            print(f"Word count: {result['metadata'].get('word_count', 0)}")
    else:
        print("❌ POST PUBLICATION FAILED!\n")
        print(f"Error: {result.get('error')}")
        if 'metadata' in result:
            print(f"Error category: {result['metadata'].get('error_category', 'unknown')}")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_basic_publish())
```

2. Run the test:

```bash
python3 test_manual_publish.py
```

3. **Verify**:
   - [ ] Script completes without errors
   - [ ] Returns `success: True`
   - [ ] Provides post URL
   - [ ] Post appears in Substack dashboard
   - [ ] HTML rendering is correct
   - [ ] No email was sent to subscribers

---

### Test Case 2: Content Sanitization (XSS Prevention)

**Objective**: Verify HTML sanitization removes dangerous content

**Test Parameters**:

```python
{
    'title': 'XSS Protection Test',
    'content': '''
        <h1>Safe Content</h1>
        <p>This paragraph is safe</p>
        <script>alert("This should be removed");</script>
        <img src="x" onerror="alert('XSS')">
        <a href="javascript:alert('XSS')">Click</a>
        <strong>Bold text (safe)</strong>
    '''
}
```

**Expected Result**:
- ✅ Post fails at security validation (framework blocks XSS)
- OR
- ✅ Script tags and event handlers are removed
- ✅ Safe HTML tags (`<h1>`, `<p>`, `<strong>`) preserved
- ✅ Published content has no executable JavaScript

---

### Test Case 3: Validation Errors

**Objective**: Verify validation catches errors before publishing

**Test 3a**: Missing required field (title)

```python
result = await manager.execute_plugin(
    'social_media_substack_test',
    {'content': '<p>Content without title</p>'}
)
```

**Expected**: `success: False`, error mentions "title"

**Test 3b**: Title too long (>200 characters)

```python
result = await manager.execute_plugin(
    'social_media_substack_test',
    {
        'title': 'X' * 250,
        'content': '<p>Content</p>'
    }
)
```

**Expected**: `success: False`, error mentions "too long"

**Test 3c**: Invalid visibility value

```python
result = await manager.execute_plugin(
    'social_media_substack_test',
    {
        'title': 'Test',
        'content': '<p>Content</p>',
        'visibility': 'invalid_value'
    }
)
```

**Expected**: `success: False`, error mentions "visibility"

---

### Test Case 4: Different Visibility Levels

**Objective**: Verify visibility settings work correctly

**Test 4a**: Public post

```python
{
    'title': 'Public Test Post',
    'content': '<p>Everyone can read this</p>',
    'visibility': 'everyone'
}
```

**Verify**: Post visible to all visitors

**Test 4b**: Paid subscribers only

```python
{
    'title': 'Paid Subscriber Test',
    'content': '<p>Only paid subscribers can read this</p>',
    'visibility': 'paid_subscribers'
}
```

**Verify**: Post marked as paid-only in Substack dashboard

---

### Test Case 5: Subtitle and Optional Parameters

**Objective**: Verify optional parameters work

```python
{
    'title': 'Post with Subtitle',
    'subtitle': 'This is a test of subtitle functionality',
    'content': '<p>Main content here</p>',
    'visibility': 'everyone',
    'send_email': False
}
```

**Verify**:
- [ ] Subtitle appears in post
- [ ] No email sent to subscribers

---

### Test Case 6: Error Recovery and Retry

**Objective**: Verify retry logic works

**Steps**:

1. Temporarily break credentials (wrong password)
2. Execute plugin
3. Verify retry attempts logged
4. Fix credentials
5. Execute again
6. Verify success

---

### Test Case 7: Concurrent Executions

**Objective**: Verify multiple posts can be published in sequence

```python
for i in range(3):
    result = await manager.execute_plugin(
        'social_media_substack_test',
        {
            'title': f'Test Post #{i+1}',
            'content': f'<p>This is test post number {i+1}</p>',
            'send_email': False
        }
    )
    print(f"Post {i+1}: {result['success']}")
```

**Verify**:
- [ ] All 3 posts publish successfully
- [ ] No rate limit errors
- [ ] Execution times reasonable (<5s each)

---

## 3. Verification Checklist

After running all test cases, verify:

### Plugin Functionality
- [ ] Posts publish successfully to Substack
- [ ] HTML content renders correctly
- [ ] Titles and subtitles display properly
- [ ] Visibility settings work as expected

### Security
- [ ] XSS attempts blocked or sanitized
- [ ] Credentials never appear in error messages
- [ ] No malicious content reaches Substack

### Error Handling
- [ ] Validation errors caught before API calls
- [ ] Missing credentials detected
- [ ] Helpful error messages provided
- [ ] Retry logic works correctly

### Performance
- [ ] Execution time <5 seconds per post
- [ ] No memory leaks
- [ ] Concurrent executions work

### Integration
- [ ] Plugin discovered by PluginManager
- [ ] Metrics tracked correctly
- [ ] System status reflects plugin usage

---

## 4. Troubleshooting

### Error: "Missing credentials"

**Cause**: Environment variables not set correctly

**Solution**:
1. Verify `.env` file contains `SUBSTACK_TEST_EMAIL` and `SUBSTACK_TEST_PASSWORD`
2. Ensure no typos in variable names
3. Restart Python interpreter to reload environment

### Error: "Authentication failed"

**Cause**: Invalid credentials or account locked

**Solution**:
1. Verify credentials work in Substack web interface
2. Check for password reset requirements
3. Ensure account is not suspended

### Error: "Module 'bleach' not found"

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
# or
pip install bleach python-substack requests
```

### Error: "Input validation failed: XSS detected"

**Cause**: Content contains potential XSS

**Solution**: This is expected behavior! The framework's security layer blocks XSS attempts. Remove `<script>` tags, event handlers, and `javascript:` URLs from content.

### Error: "Plugin disabled"

**Cause**: Too many consecutive failures triggered degraded mode

**Solution**:
1. Fix underlying issue (credentials, validation, etc.)
2. Restart PluginManager to re-enable plugin
3. Or temporarily disable degraded mode in config

---

## 5. Cleanup

After testing:

1. **Delete test posts** from Substack dashboard
2. **Clear credentials** from environment (if using temporary test account)
3. **Document results** in test log
4. **Report issues** if any tests failed

---

## 6. Next Steps

Once manual testing passes:

1. ✅ Mark Phase 1 as complete
2. ✅ Create production Substack plugin (copy from test, update credentials)
3. ✅ Implement additional accounts (personal, corporate, marketing)
4. ✅ Move to Phase 2: Medium integration
5. ✅ Move to Phase 3: Twitter integration

---

## Appendix: Test Log Template

```
==============================================================================
SOCIAL MEDIA PLUGIN MANUAL TEST LOG
==============================================================================
Date: ___________________
Tester: _________________
Environment: Production / Staging / Local
Plugin Version: _________

TEST RESULTS:
-------------
[ ] Test Case 1: Basic Post Publication - PASS / FAIL
    Notes: ___________________________________________________________

[ ] Test Case 2: Content Sanitization - PASS / FAIL
    Notes: ___________________________________________________________

[ ] Test Case 3: Validation Errors - PASS / FAIL
    Notes: ___________________________________________________________

[ ] Test Case 4: Visibility Levels - PASS / FAIL
    Notes: ___________________________________________________________

[ ] Test Case 5: Optional Parameters - PASS / FAIL
    Notes: ___________________________________________________________

[ ] Test Case 6: Error Recovery - PASS / FAIL
    Notes: ___________________________________________________________

[ ] Test Case 7: Concurrent Executions - PASS / FAIL
    Notes: ___________________________________________________________

OVERALL RESULT: PASS / FAIL

ISSUES FOUND:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

RECOMMENDATIONS:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

Tester Signature: _____________________ Date: _________________
==============================================================================
```

---

**End of Manual Testing Guide**
