# Substack Testing Guide

**Status**: 🔧 Manual Testing Required
**Date**: 2025-10-19
**Version**: 1.0.0

---

## Issue: CAPTCHA Blocks Automated Login

Substack's API requires solving a CAPTCHA during login, which prevents automated authentication:

```
❌ APIError(code=401): Please complete the captcha to continue
```

This is a **known limitation** of the unofficial `python-substack` library and Substack's authentication system.

---

## Solution: Cookie-Based Authentication

The Substack library supports cookie-based authentication, which bypasses the CAPTCHA requirement:

### Workflow:
1. **Manual browser login** → Solve CAPTCHA once
2. **Export cookies** → Save session to file
3. **Reuse cookies** → API uses saved session (no CAPTCHA)

### Cookie Lifespan:
- Cookies typically last **7-30 days**
- When expired, repeat the process
- More reliable than password-based auth

---

## Testing Options

### Option 1: Manual Interactive Testing (Recommended)

I've created an interactive testing script for you:

**Location**: `/tests/utilities/test_substack_manual.py`

**Features**:
- Guides you through cookie export
- Tests all Substack functions interactively
- Creates/publishes/reads/deletes posts
- Clear step-by-step instructions

**Usage**:
```bash
cd /home/sabawi/Development/flaskserver
python3 tests/utilities/test_substack_manual.py
```

**Functions Tested**:
- ✅ Authentication (cookie-based)
- ✅ Create draft post
- ✅ Publish draft
- ✅ Read published posts
- ✅ Read drafts
- ✅ Delete drafts

---

### Option 2: Browser Extension for Cookie Export

**Chrome/Edge**:
1. Install extension: "EditThisCookie" or "Cookie-Editor"
2. Login to Substack
3. Click extension icon
4. Export cookies as JSON
5. Save to `substack_cookies.json`

**Firefox**:
1. Install extension: "Cookie Quick Manager"
2. Login to Substack
3. Click extension → Export
4. Save to `substack_cookies.json`

**Cookie File Location**:
```
/home/sabawi/Development/flaskserver/substack_cookies.json
```

**⚠️ SECURITY**: Add to .gitignore! Never commit cookies!

---

### Option 3: Alternative - Test via LLM (Future)

Once cookies are set up, you can update the Substack handler to use cookies instead of email/password:

**Handler Update**:
```python
# In plugins/handlers/social_media_substack.py
def load_credentials():
    # Change from email/password to cookies_path
    cookies_path = os.getenv('SUBSTACK_COOKIES_PATH')
    return cookies_path

# In publish_to_substack():
client = SubstackApi(cookies_path=cookies_path)  # Instead of email/password
```

**Then test via LLM prompt**:
```
"Post to test Substack: 'Test post from automated testing system'"
```

---

## Current Handler Status

### ✅ Implementation Complete
- Plugin YAML configured
- Handler code written
- Input validation working
- HTML sanitization working
- Error handling comprehensive
- Security checks in place

### ⏸️ Testing Blocked
- Automated email/password auth: **BLOCKED** (CAPTCHA)
- Cookie-based auth: **READY** (needs manual cookie export)
- End-to-end testing: **PENDING** (awaiting cookies)

### 🔄 Workaround Available
- Use manual test script (Option 1 above)
- Or switch to Medium/Twitter plugins (no CAPTCHA issues)

---

## Next Steps

### Immediate (Recommended):
1. **Run the interactive test script**:
   ```bash
   python3 tests/utilities/test_substack_manual.py
   ```

2. **Follow prompts** to export cookies from browser

3. **Test all functions** interactively (create, publish, read, delete)

4. **Verify everything works** before using via LLM

### Alternative:
1. **Test Medium plugin first** (uses token-based auth, no CAPTCHA)
2. **Test Twitter plugin** (uses OAuth, no CAPTCHA)
3. **Return to Substack** after validating other platforms

---

## Available Substack Functions

Based on the `python-substack` library analysis:

### Posting:
- ✅ `post_draft(body)` - Create draft post
- ✅ `publish_draft(draft_id, send=True)` - Publish draft
- ✅ `prepublish_draft(draft_id)` - Prepare for publishing
- ✅ `schedule_draft(draft_id, date)` - Schedule publication

### Reading:
- ✅ `get_published_posts(limit=25)` - Get published posts
- ✅ `get_posts()` - Get all posts
- ✅ `get_drafts(limit=None)` - Get draft posts
- ✅ `get_draft(draft_id)` - Get specific draft

### Management:
- ✅ `delete_draft(draft_id)` - Delete a draft
- ✅ `delete_all_drafts()` - Delete all drafts
- ✅ `unschedule_draft(draft_id)` - Unschedule scheduled post

### Account:
- ✅ `get_user_profile()` - Get user info
- ✅ `get_user_publications()` - Get list of publications
- ✅ `get_publication_subscriber_count()` - Get subscriber count

### Utility:
- ✅ `export_cookies(path)` - Save cookies for reuse
- ✅ `change_publication(url)` - Switch active publication

---

## API Body Structure

For `post_draft(body)`, the body parameter should include:

```python
body = {
    "title": "Post Title",           # Required
    "body_html": "<p>Content</p>",   # Required (HTML format)
    "subtitle": "Optional subtitle", # Optional
    # Note: visibility and send_email might be set during publish_draft()
}
```

Then publish with:
```python
api.publish_draft(
    draft=draft_id,
    send=True,  # Send email to subscribers
    share_automatically=False  # Auto-share to social media
)
```

---

## Comparison: Substack vs Other Platforms

| Feature | Substack | Medium | Twitter |
|---------|----------|--------|---------|
| **Auth Method** | Email/Password + CAPTCHA | Token (permanent) | OAuth 1.0a |
| **CAPTCHA** | ⚠️ **YES (blocks automation)** | ❌ No | ❌ No |
| **Workaround** | ✅ Cookies | N/A | N/A |
| **Testing** | Manual (interactive) | Automated | Automated |
| **API Status** | Unofficial (may break) | Official (deprecated) | Official |

**Recommendation**: Start with Medium or Twitter for fully automated testing, then return to Substack with cookies.

---

## Security Notes

### Cookie Storage:
```bash
# Add to .gitignore
echo "substack_cookies.json" >> .gitignore
```

### Cookie Expiration:
- Check logs for "401 Unauthorized"
- If cookies expired, re-export from browser
- Typical lifespan: 7-30 days

### Multi-Account Support:
```bash
# Separate cookie files per account
substack_cookies_test.json      # Test account
substack_cookies_personal.json  # Personal account
substack_cookies_corporate.json # Corporate account
```

---

## Troubleshooting

### Error: "Please complete the captcha"
- **Cause**: Using email/password auth
- **Fix**: Switch to cookie-based auth

### Error: "401 Unauthorized" with cookies
- **Cause**: Cookies expired
- **Fix**: Re-export cookies from browser

### Error: "Invalid JSON" in cookie file
- **Cause**: Cookie export format incorrect
- **Fix**: Use recommended browser extensions above

### Post created but not visible
- **Cause**: Created as draft but not published
- **Fix**: Call `publish_draft(draft_id)` after `post_draft()`

---

## Documentation References

- **Design Document**: `/docs/SOCIAL_MEDIA_PLUGIN_DESIGN.md`
- **Design Part 2**: `/docs/SOCIAL_MEDIA_PLUGIN_DESIGN_PART2.md`
- **Handler Code**: `/plugins/handlers/social_media_substack.py`
- **Plugin YAML**: `/plugins/social_media_substack_test.yaml`
- **Testing Script**: `/tests/utilities/test_substack_manual.py`
- **Blocker Document**: `/docs/housekeeping/status-tracking/SUBSTACK_TESTING_BLOCKER.md`

---

## Summary

✅ **Implementation**: Complete and ready
⏸️ **Testing**: Blocked by CAPTCHA, workaround available
🔧 **Action Required**: Run interactive test script with cookies
📚 **Documentation**: Complete
🛡️ **Security**: Validated

**Estimated Time to Test**: 15-20 minutes (including cookie export)

---

**Last Updated**: 2025-10-19
**Status**: Ready for manual testing with cookies
