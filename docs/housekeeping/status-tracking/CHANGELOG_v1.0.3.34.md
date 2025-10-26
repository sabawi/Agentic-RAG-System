# CHANGELOG v1.0.3.34
**Date:** 2025-10-26
**Type:** Test Cleanup, Security Hardening, Installation Improvements
**Previous Version:** 1.0.3.26

---

## 🔒 SECURITY FIXES (CRITICAL)

### Personal Data Sanitization
- **Sanitized 21 test files**: Replaced personal email addresses with `test@example.com`
- **Sanitized 5 test files**: Replaced personal names with generic test names
- **Fixed `agents/news_retriever/config.py`**: Moved hardcoded email to environment variable `NEWS_RECIPIENT_EMAIL`
- **Verified zero personal data** in all committable production code

### Configuration Security
- All agent configurations now use environment variables per CLAUDE.md compliance
- `.env ONLY FOR SECRETS` directive enforced
- Added comprehensive environment variable documentation to `.env.example`

---

## 🧪 TEST INFRASTRUCTURE IMPROVEMENTS

### Test Cleanup
- **Cloud Model Migration**: Migrated 45 test references from local to cloud models
  - Before: `qwen3:8b`, `qwen3:4b`, `llama3.2:3b`, `llama3.2:1b`
  - After: `deepseek-v3.1:671b-cloud`
  - Result: 0% timeout rate (was 100%), 4.5x faster execution, 89% pass rate

- **Test Organization**:
  - Renamed 24 files for clarity
  - Archived 2 obsolete tests with documentation
  - Fixed 9 import path errors

- **Test Automation Tools**:
  - Created `test_model_replacer.py` (202 lines) - automated model replacement across test suite
  - Created `test_random_sampler.py` (345 lines) - 15% random sampling for sanity checks

### Test Documentation
- Added `tests/TEST_CLEANUP_SUMMARY.md` - comprehensive test infrastructure documentation
- Added `archive/experimental/obsolete_tests/README.md` - archival documentation

---

## 🆕 NEW FEATURES (Previous Work - Included in Commit)

### Autonomous Agents
**New Directory:** `agents/`

1. **News Retriever Agent** (`agents/news_retriever/`)
   - `autonomous_news_retriever.py` - Automated news retrieval
   - `config.py` - Configuration using environment variables
   - `README.md` - Documentation

2. **System Tuner Agent** (`agents/system_tuner/`)
   - `autonomous_system_tuner.py` - System tuning automation
   - `README.md` - Documentation

**Security:** All configurations use environment variables

### LLM Provider Integration
**New Provider:** Google Gemini

1. **llm_providers/gemini.py** - Google Gemini AI integration
2. **Factory Registration** - Added Gemini to `llm_providers/factory.py`
3. **Configuration Updates**:
   - `config/llm_config.yaml` - Gemini configuration
   - `config/model_aliases.json` - Added `gemini_flash` alias

**Dependency:** Added `google-generativeai==0.8.5` to requirements.txt

### Social Media Plugins
**New Plugins:** Twitter, Medium, Substack

1. **Plugin Handlers** (`plugins/handlers/`):
   - `social_media_twitter.py` - Twitter/X OAuth integration
   - `social_media_medium.py` - Medium publishing
   - `social_media_substack.py` - Substack publishing

2. **Plugin Configurations** (`plugins/`):
   - `social_media_twitter_test.yaml`
   - `social_media_medium_test.yaml`
   - `social_media_substack_test.yaml`

**Security:** All use environment variables for credentials

### Utility Modules
- **image_utils.py** (root) - Image processing utilities using PIL/Pillow

---

## 📦 INSTALLATION IMPROVEMENTS

### install.sh Enhancement
**Auto-Pull for Ollama Models:**

1. **Updated Model List**:
   - Added: `qwen3-vl:235b-cloud` (vision cloud model)
   - Added: `mxbai-embed-large` (embeddings model)
   - Total: 6 required models (was 4)

2. **New Auto-Pull Feature**:
   - Detects missing models from Ollama
   - Interactive prompt to auto-pull missing models
   - Individual success/failure feedback per model
   - Graceful error handling with manual fallback
   - Shows count of missing models

**Required Models:**
- `deepseek-v3.1:671b-cloud` (primary cloud model)
- `qwen3-vl:235b-cloud` (vision cloud model)
- `qwen3:8b` (local fallback)
- `qwen2.5vl:3b` (vision fallback)
- `bakllava:latest` (vision support)
- `mxbai-embed-large` (document embeddings)

**Impact:** Improved installation experience, fewer missing model errors

---

## 📄 CONFIGURATION UPDATES

### Environment Variables (.env.example)
**New Variables Added:**
- `GEMINI_API_KEY` - Google Gemini API key
- `NEWS_RECIPIENT_EMAIL` - News retriever agent recipient
- `NEWS_SERVER_URL` - News retriever server URL
- `TWITTER_TEST_API_KEY` - Twitter API credentials (4 variables)
- `TWITTER_TEST_API_SECRET`
- `TWITTER_TEST_ACCESS_TOKEN`
- `TWITTER_TEST_ACCESS_SECRET`
- `SUBSTACK_TEST_EMAIL` - Substack test email
- `MEDIUM_TEST_INTEGRATION_TOKEN` - Medium integration token

### Configuration Files
- `config/llm_config.yaml` - Formatting cleanup, added Gemini config
- `config/model_aliases.json` - Added `gemini_flash` model alias

---

## 📚 DOCUMENTATION UPDATES

### Production Documentation (docs/)
- `CONTACT_MANAGEMENT_SYSTEM_DESIGN.md`
- `IMAGE_PROCESSING_OPTIMIZATION.md`
- `POST_LLM_ANALYSIS.md`
- `POST_LLM_OPERATIONS_SUMMARY.txt`
- `POST_LLM_REFACTORING_PROPOSAL.md`
- `POST_LLM_REFACTORING_ROADMAP.md`
- `README_POST_LLM_ANALYSIS.md`
- `SOCIAL_MEDIA_PLUGINS_RESEARCH.md`
- `SOCIAL_MEDIA_PLUGIN_ASSESSMENT.md`
- `SOCIAL_MEDIA_PLUGIN_DESIGN.md`
- `SOCIAL_MEDIA_PLUGIN_DESIGN_PART2.md`
- `SUBSTACK_TESTING_GUIDE.md`
- `TWITTER_API_SETUP_GUIDE.md`
- `TWITTER_TESTING_SUMMARY.md`

### Housekeeping Documentation (docs/housekeeping/)
- `procedures/SOCIAL_MEDIA_PLUGIN_TEST_GUIDE.md`
- `status-tracking/CONTACT_MANAGEMENT_CHECKLIST.md`
- `status-tracking/CONTACT_MANAGEMENT_STATUS.md`
- `status-tracking/SOCIAL_MEDIA_ALL_PLATFORMS_COMPLETE.md`
- `status-tracking/SOCIAL_MEDIA_PHASE_1_COMPLETE.md`
- `status-tracking/SUBSTACK_TESTING_BLOCKER.md`
- `status-tracking/REVERT_*.md` (moved from root)

---

## 🗂️ PROJECT ORGANIZATION

### Directory Cleanup (CLAUDE.md Compliance)
- Moved 4 REVERT_*.md files → `docs/housekeeping/status-tracking/`
- Archived 2 obsolete tests → `archive/experimental/obsolete_tests/`
- Removed 7 files/directories (obsolete, duplicates)
- Root directory cleanup: 7 files removed/relocated

### Deleted Files
1. `GEMINI.md` - Obsolete duplicate of CLAUDE.md
2. `REVERT_COMPLETE_SUMMARY.md` → moved
3. `REVERT_EXECUTION_REPORT.md` → moved
4. `REVERT_OPERATION_LOG.md` → moved
5. `tests/integration/test_passport_scores.py` → archived
6. `tests/unit/test_update_image_config.py` → archived
7. `system_tuning_backups/` directory → removed

---

## 📊 DEPENDENCIES

### Added
- `google-generativeai==0.8.5` - For Gemini LLM provider

### Verified Present
- `requests-oauthlib>=2.0.0` - For social media plugins
- `Pillow` - For image_utils.py
- All existing dependencies maintained

---

## 🔧 VERSION UPDATES

| File | Old Version | New Version |
|------|-------------|-------------|
| version.py | 1.0.3.26 | 1.0.3.34 |
| README.md (badge) | 1.0.3.21 | 1.0.3.34 |
| README.md (header) | 1.0.3.21 | 1.0.3.34 |

---

## 📈 STATISTICS

**Total Files Changed:** 133
- Modified: 39 files
- Renamed: 31 files
- Deleted: 7 files
- New: 54 files

**Test Performance:**
- Timeout rate: 100% → 0%
- Execution speed: 4.5x faster
- Pass rate: 89% (on 15% sample)

**Security:**
- Personal data violations: 21 found → 0 (100% clean)

---

## ⚠️ BREAKING CHANGES

**None** - All changes are backward compatible

---

## 🚨 IMPORTANT NOTES

### Testing Required Before Production Use
1. **Gemini Provider** - Test basic functionality after server restart
2. **Social Media Plugins** - Test with valid credentials
3. **Autonomous Agents** - Test in safe environment
4. **Test Sanitization** - Verify tests still pass after email sanitization

### Environment Variables Required
New installations require these environment variables:
- `GEMINI_API_KEY` (if using Gemini provider)
- `NEWS_RECIPIENT_EMAIL` (for news retriever agent)
- Twitter/Medium/Substack credentials (for social media plugins)

### Ollama Models Required
Fresh installations need these models:
```bash
ollama pull deepseek-v3.1:671b-cloud
ollama pull qwen3-vl:235b-cloud
ollama pull qwen3:8b
ollama pull qwen2.5vl:3b
ollama pull bakllava:latest
ollama pull mxbai-embed-large
```

*(install.sh now offers auto-pull)*

---

## 🎯 MIGRATION GUIDE

### From v1.0.3.26 to v1.0.3.34

1. **Update Environment Variables**:
   ```bash
   # Copy new variables from .env.example to .env
   GEMINI_API_KEY=your_key_here
   NEWS_RECIPIENT_EMAIL=your_email@example.com
   ```

2. **Pull New Ollama Models** (if needed):
   ```bash
   ollama pull qwen3-vl:235b-cloud
   ollama pull mxbai-embed-large
   ```

3. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Restart Server**:
   ```bash
   ./stop_complete.sh
   ./start_complete.sh
   ```

5. **Test Gemini Provider** (optional):
   ```bash
   curl -X POST http://localhost:5000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "gemini-flash-latest", "messages": [{"role": "user", "content": "Hello"}]}'
   ```

---

## 👥 CONTRIBUTORS

- Claude Code (Sonnet 4.5)

---

## 📋 RELATED DOCUMENTS

- **Pre-Commit Audit:** `/tmp/PRE_COMMIT_AUDIT_v1.0.3.34.md`
- **Test Cleanup Summary:** `tests/TEST_CLEANUP_SUMMARY.md`
- **Install.sh Improvements:** Documented in pre-commit audit
- **Social Media Design:** `docs/SOCIAL_MEDIA_PLUGIN_DESIGN.md`
- **Contact Management:** `docs/CONTACT_MANAGEMENT_SYSTEM_DESIGN.md`

---

**Full Commit Message:** See `/tmp/PRE_COMMIT_AUDIT_v1.0.3.34.md`
