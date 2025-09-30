# 📁 Project Organization Standards & Memory

**Status**: ACTIVE PROJECT STANDARD
**Version**: v1.0.2.88+
**Effective Date**: 2025-09-29

## 🎯 Purpose
This document serves as permanent project memory for directory organization standards established through comprehensive analysis and reorganization efforts.

## 📋 Established Organization Rules

### **ROOT DIRECTORY POLICY**
**Principle**: Keep root directory clean and essential only

**REQUIRED FILES (Must remain in root):**
- `README.md` - Main project documentation
- `CLAUDE.md` - Project directives and rules
- `fastapi_server_complete.py` - Main server application
- `version.py` - Centralized version management

**CRITICAL PYTHON MODULES (Verified dependencies - Must remain in root):**
- `http_helpers.py` - Imported by fastapi_server_complete.py, document_interrogator.py
- `http_pool_manager.py` - Imported by fastapi_server_complete.py, http_helpers.py
- `text_chunker.py` - Multiple dynamic imports in fastapi_server_complete.py
- `document_interrogator.py` - Imported by fastapi_server_complete.py, user_tools/document_search.py
- `signature_image_detection.py` - Imported by fastapi_server_complete.py:6954

**FORBIDDEN IN ROOT:**
- Test files (test_*.py) → Move to tests/
- Debug files (debug_*.py, analyze_*.py) → Move to archive/experimental/
- Housekeeping documentation → Move to docs/housekeeping/
- Experimental code → Move to archive/experimental/

### **DOCUMENTATION ORGANIZATION**

#### **docs/production/** - User-Facing Documentation
**Purpose**: Essential guides for end users, administrators, developers
- `ADMINISTRATOR_GUIDE.md` - System administration
- `USER_GUIDE.md` - End user guidance
- `DEVELOPER_GUIDE.md` - Developer reference
- `INSTALLATION_GUIDE.md` - Installation procedures

#### **docs/housekeeping/** - Project Management Documentation
**Purpose**: Internal project management, NOT for code development

**Subdirectories:**
- `procedures/` - Emergency procedures, test checklists, rollback instructions
- `status-tracking/` - Project reviews, changelogs, status updates, post-mortems
- `workflow-automation/` - Internal automation guides, optimization plans

**File Types to Move Here:**
- `PHASE_STATUS_*.md, *_STATUS.md` → status-tracking/
- `ROLLBACK_*.md, *_CHECKLIST.md, UNTESTED_*.md` → procedures/
- `AUTOMATION_*.md, CLI_*QUICKSTART.md` → workflow-automation/

#### **docs/ (Main level)** - Technical Documentation
**Purpose**: Technical specifications and implementation guides
- `HTML_EMAIL_CONVERSION_SYSTEM.md` - Technical system documentation
- `LLM_CONFIGURATION_GUIDE.md` - Configuration guidance
- `PROJECT_CONFIGURATION_DIRECTIVE.md` - Configuration rules
- `*_IMPLEMENTATION_PLAN.md` - Implementation specifications

#### **docs/archive/** - Historical Documentation
**Purpose**: Historical records, validation reports, outdated docs
- Keep existing structure: `historical/`, `individual_components/`, `validation_reports/`

### **TEST ORGANIZATION**

#### **tests/utilities/** - Test Utilities and API Testing
- `test_logging_api.py` - API testing scripts
- General utility test scripts
- API endpoint testing

#### **tests/vision_regression/** - Vision and Image Testing
- `test_signature_detection.py` - Image detection testing
- `test_image_processing.py` - Image processing tests
- Vision-related regression tests

#### **tests/integration/** - Integration Testing
- Cross-system integration tests
- End-to-end functionality tests

#### **tests/data/** - Test Data Files
- Sample documents, test images
- Mock data for testing

### **ARCHIVE/EXPERIMENTAL ORGANIZATION**

#### **archive/experimental/** - Development and Debug Files
**Purpose**: Non-production code, analysis scripts, experimental implementations
- `debug_*.py` - Debug utilities
- `analyze_*.py` - Analysis scripts
- `improved_*.py` - Experimental improvements
- `signature_based_detection.py` - Alternative implementations

## 🔍 Decision Framework

### **Before Moving ANY Python File:**
1. **Run comprehensive dependency analysis:**
   ```bash
   grep -r "import.*filename|from.*filename" /home/sabawi/Development/flaskserver
   ```
2. **Check dynamic imports and runtime loading**
3. **Verify tool discovery mechanisms don't reference it**
4. **Check configuration file references**
5. **Document as "UNTESTED" until validation complete**

### **For Documentation Files:**
1. **Ask**: Is this relevant to code development? → Keep in docs/
2. **Ask**: Is this project management/status? → Move to docs/housekeeping/
3. **Ask**: Is this historical/archived? → Keep in docs/archive/
4. **Ask**: Is this user-facing? → Keep in docs/production/

### **For Test Files:**
1. **ALL test_*.py files** → Move to appropriate tests/ subdirectory
2. **NEVER leave test files in root directory**
3. **Organize by testing type**: utilities/, vision_regression/, integration/

## 📚 Historical Context

### **Lessons Learned**
1. **File Reorganization Risk**: Initial analysis suggested moving 15 files, but comprehensive dependency analysis revealed 5 had critical dependencies that would break the system
2. **Import Chain Complexity**: Files like `document_interrogator.py` have complex import chains across multiple system components
3. **Dynamic Import Detection**: Some imports are dynamic (lines 100, 3174, 8179 in fastapi_server_complete.py), requiring thorough analysis

### **Successful Reorganizations Completed**
- **September 29, 2025**: Moved 8 test files and 11 housekeeping documentation files
- **Risk Assessment**: LOW for documentation (no code impact), MEDIUM for test files (verified no dependencies)
- **Validation Status**: Documentation moves tested and confirmed safe

## 🚨 Enforcement Rules

### **MANDATORY PRACTICES**
1. **Always check dependencies before moving Python files**
2. **Never leave housekeeping docs in root or docs/ main**
3. **Never leave test files in root directory**
4. **Always document moves as "UNTESTED" until validation**
5. **Preserve all core development documentation in proper locations**

### **VALIDATION REQUIREMENTS**
- Server startup test
- HTTP connection pool test
- Document processing test
- Image processing test
- Tool discovery test
- Import chain validation

## 📖 References

**Related Documentation:**
- `CLAUDE.md` - Contains the active project directives
- `docs/housekeeping/DOCUMENTATION_REORGANIZATION_LOG.md` - Detailed reorganization history
- `docs/housekeeping/procedures/FILE_REORGANIZATION_TEST_CHECKLIST.md` - Testing procedures

**Dependency Analysis Tools:**
- Use `grep -r "import.*|from.*"` for comprehensive dependency checking
- Check `user_tools/tool_discovery.py` for dynamic loading patterns
- Verify no hardcoded file paths exist in configuration files

---

**This document serves as permanent project memory to prevent regression and ensure consistent organization practices going forward.**