# Test Directory Cleanup Plan

**Date:** 2025-10-25
**Total Test Files:** 128

## Issues Found

### 1. Duplicates (2 pairs)
- `test_direct_tools.py` - integration/ & utilities/
- `test_tool_calling.py` - integration/ & utilities/

### 2. Misplaced Files in Root (21 files need relocation)

#### Move to utilities/
- `deepseek_tool_test.py` → `utilities/test_deepseek_tool_calling.py`
- `local_tool_test.py` → `utilities/test_local_tool_calling.py`
- `qwen3_tool_debug.py` → `utilities/test_qwen3_tool_calling.py`
- `qwen3_tool_format_debug.py` → `utilities/test_qwen3_format_debug.py`
- `simple_config_test.py` → `utilities/test_config_simple.py`
- `spacing_test.py` → `utilities/test_streaming_spacing.py`
- `test_simplified_prompt.py` → `utilities/test_prompt_simplified.py`

#### Move to integration/
- `model_tool_support_test.py` → `integration/test_model_tool_support.py`
- `provider_comparison_test.py` → `integration/test_provider_comparison.py`
- `test_email_body_fix.py` → `integration/test_email_body_retrieval.py`
- `test_email_retriever_fvt.py` → `integration/test_email_retriever_functional.py`
- `test_html_email_conversion.py` → `integration/test_html_email_conversion.py`
- `test_lookup_website_formatting.py` → `integration/test_lookup_website_formatting.py`
- `test_news_citations.py` → `integration/test_news_citations.py`
- `test_web_search_formatting.py` → `integration/test_web_search_formatting.py`
- `test_wikipedia_query_formatting.py` → `integration/test_wikipedia_query_formatting.py`

#### Move to unit/
- `test_image_resizing.py` → `unit/test_image_resizing.py`

#### Move to regression/
- `quick_regression_test.py` → `regression/test_post_processing_regression.py`
- `test_llm_configurations.py` → `regression/test_llm_configurations.py`

#### Move to vision_regression/
- `quick_image_test.py` → `vision_regression/test_image_processing_quick.py`
- `test_vision_base64.py` → `vision_regression/test_vision_base64.py`

### 3. Outdated/Redundant Tests (Need Review)

#### Potential candidates for removal or archival:
- `test_complete_fix.py` - If issue is fixed
- `test_prompt_fix.py` - If issue is fixed
- `test_race_condition_fix.py` - If issue is fixed
- `test_optimization_fix.py` - If issue is fixed
- `test_email_provider_fix.py` - If issue is fixed
- `test_html_pdf_fix.py` - If issue is fixed
- `test_formats_quick_fix.py` - If issue is fixed
- `test_post_processing_fix.py` - If issue is fixed
- `test_async_fix.py` - If issue is fixed
- `test_regression_fix.py` - If issue is fixed

### 4. Files Needing Better Names

#### In utilities/:
- `quick_test.py` → `test_api_endpoints_quick.py`
- `simple_test.py` → `test_logic_simple.py`
- `simple_tool_test.py` → `test_tool_calling_simple.py`
- `simple_attachment_test.py` → `test_email_attachments_simple.py`
- `final_fix_test.py` → `test_race_condition_verification.py`

#### In integration/:
- `test_clean_html.py` → `test_html_cleaning.py`
- `test_html_final.py` → `test_html_processing_final.py`

### 5. Missing Documentation

Many files lack proper docstrings or inline documentation. Need to add:
- Module-level docstrings explaining purpose
- Function docstrings explaining test scenarios
- Inline comments for complex test logic

## Cleanup Actions

### Phase 1: Analyze Duplicates
1. Compare duplicate files
2. Decide which to keep
3. Remove or merge duplicates

### Phase 2: Move Misplaced Files
1. Move 21 files from root to appropriate subdirectories
2. Rename files for clarity during move
3. Update any import statements if needed

### Phase 3: Review Outdated Tests
1. Check if "fix" tests are still needed
2. Run tests to verify they still work
3. Archive or remove obsolete tests

### Phase 4: Rename for Clarity
1. Rename files with unclear names
2. Ensure names reflect what they test
3. Follow naming convention: `test_<feature>_<variant>.py`

### Phase 5: Add Documentation
1. Add module docstrings to all files
2. Add function docstrings to test functions
3. Add inline comments for complex logic

### Phase 6: Validation
1. Run all remaining tests
2. Verify no broken imports
3. Update any test runners or documentation

### Phase 7: Summary Report
1. Create summary of changes
2. Document test coverage
3. Provide guidance for running tests

## Naming Conventions

### Preferred Format:
- `test_<feature>_<test_type>.py`
- Examples:
  - `test_email_retriever_functional.py`
  - `test_tool_calling_integration.py`
  - `test_image_processing_regression.py`

### Test Types:
- `_unit` - Unit tests
- `_integration` - Integration tests
- `_functional` - Functional verification tests
- `_regression` - Regression tests
- `_performance` - Performance tests
- `_manual` - Manual/interactive tests

## Next Steps

1. Get user approval for cleanup plan
2. Execute cleanup in phases
3. Create backup of tests/ directory before major changes
4. Test after each phase
5. Document all changes

