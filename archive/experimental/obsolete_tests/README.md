# Obsolete Tests Archive

This directory contains tests that were removed from the active test suite because they test deprecated or user-specific functionality.

## Archived Tests

### 1. test_update_image_config.py
**Date Archived:** 2025-10-25  
**Reason:** Tests deprecated `tools/llm_config_tool.py` which has been replaced by `config_server_cli.py`  
**Details:**
- References undefined constant `ENV_VAR_OPENAI`
- llm_config_tool.py is not used anywhere in production code
- Current system uses config_server_cli.py (updated Oct 17, 2025)
- Last modified: Sept 28, 2025

### 2. test_passport_scores.py
**Date Archived:** 2025-10-25  
**Reason:** User-specific test requiring personal documents  
**Details:**
- Tests document_interrogator (which IS still used in production)
- Searches for "Alaa's passport documents" specifically
- Requires specific personal documents to be indexed in FAISS
- Fails on general test runs because FAISS index is empty
- This is a utility test for specific user data, not a general regression test

## Notes

These tests can be restored if:
1. `test_update_image_config.py` - If llm_config_tool.py is brought back into use
2. `test_passport_scores.py` - If converted to a general document search test with test data
