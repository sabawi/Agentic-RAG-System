# 📋 MANDATORY CHANGELOG CREATION PROCEDURE
**Status:** MANDATORY - CHECKPOINT PROTOCOL REQUIREMENT
**Location:** docs/housekeeping/status-tracking/CHANGELOG_vX.X.X.XX.md
**Updated:** 2025-10-26

---

## 🚨 REQUIREMENT

**Per CLAUDE.md CHECKPOINT PROTOCOL:**
> MANDATORY: Create version-specific changelog at docs/housekeeping/status-tracking/CHANGELOG_vX.X.X.XX.md documenting all changes, new features, fixes, dependencies, breaking changes, and migration guide.

**This is NOT optional. Every version release MUST have a changelog.**

---

## 📍 WHEN TO CREATE

Create a changelog during **EVERY checkpoint/commit** that increments the version number.

**Triggers:**
- Version number incremented in version.py
- Pre-commit audit initiated
- Checkpoint protocol activated

---

## 📂 LOCATION

**File Path:**
```
docs/housekeeping/status-tracking/CHANGELOG_v{VERSION}.md
```

**Example:**
```
docs/housekeeping/status-tracking/CHANGELOG_v1.0.3.34.md
```

**Directory Structure:**
```
docs/
└── housekeeping/
    └── status-tracking/
        ├── CHANGELOG_v1.0.3.8.md
        ├── CHANGELOG_v1.0.3.9.md
        ├── CHANGELOG_v1.0.3.10.md
        ├── CHANGELOG_v1.0.3.34.md  ← New version
        └── ...
```

---

## 📝 REQUIRED SECTIONS

### 1. Header
```markdown
# CHANGELOG v{VERSION}
**Date:** YYYY-MM-DD
**Type:** {Brief type description}
**Previous Version:** {X.X.X.XX}
```

### 2. Security Fixes (if applicable)
```markdown
## 🔒 SECURITY FIXES (CRITICAL)
- List all security-related changes
- Personal data sanitization
- Credential management
- Configuration security
```

### 3. New Features
```markdown
## 🆕 NEW FEATURES
- Major new functionality
- New modules/plugins
- New integrations
```

### 4. Improvements
```markdown
## 📦 IMPROVEMENTS
- Test infrastructure
- Installation enhancements
- Performance optimizations
```

### 5. Configuration Updates
```markdown
## 📄 CONFIGURATION UPDATES
- Environment variables added/changed
- Config file modifications
- Model configurations
```

### 6. Dependencies
```markdown
## 📊 DEPENDENCIES
### Added
- package==version - Purpose

### Removed
- package==version - Reason

### Updated
- package: old_version → new_version
```

### 7. Documentation
```markdown
## 📚 DOCUMENTATION UPDATES
- New documentation files
- Updated guides
- Housekeeping documentation
```

### 8. Project Organization
```markdown
## 🗂️ PROJECT ORGANIZATION
- Directory cleanup
- File relocations
- Deleted files
```

### 9. Breaking Changes (if applicable)
```markdown
## ⚠️ BREAKING CHANGES
**None** - All changes are backward compatible

OR

- List breaking changes
- Impact description
- Migration path
```

### 10. Migration Guide
```markdown
## 🎯 MIGRATION GUIDE
### From vX.X.X.XX to vX.X.X.XX

1. Update Environment Variables
2. Update Dependencies
3. Run Scripts
4. Test Changes
```

### 11. Statistics
```markdown
## 📈 STATISTICS
**Total Files Changed:** XXX
- Modified: XX files
- Renamed: XX files
- Deleted: XX files
- New: XX files
```

### 12. Testing Status
```markdown
## 🧪 TESTING STATUS
- Test results
- Pass rates
- Known issues
```

### 13. Related Documents
```markdown
## 📋 RELATED DOCUMENTS
- Pre-commit audit location
- Design documents
- Test documentation
```

---

## 📐 TEMPLATE

Use this template for consistency:

```markdown
# CHANGELOG v{VERSION}
**Date:** {YYYY-MM-DD}
**Type:** {Type}
**Previous Version:** {X.X.X.XX}

---

## 🔒 SECURITY FIXES (CRITICAL)
{If applicable}

---

## 🆕 NEW FEATURES
{List new features}

---

## 📦 IMPROVEMENTS
{List improvements}

---

## 📄 CONFIGURATION UPDATES
{List config changes}

---

## 📊 DEPENDENCIES
### Added
### Removed
### Updated

---

## 📚 DOCUMENTATION UPDATES
{List documentation}

---

## 🗂️ PROJECT ORGANIZATION
{List organizational changes}

---

## ⚠️ BREAKING CHANGES
**None** - All changes are backward compatible

---

## 🎯 MIGRATION GUIDE
### From vX.X.X.XX to vX.X.X.XX
{Step-by-step migration}

---

## 📈 STATISTICS
**Total Files Changed:** XXX

---

## 🧪 TESTING STATUS
{Test results}

---

## 📋 RELATED DOCUMENTS
- Pre-commit audit: {location}
- Design docs: {list}
```

---

## ✅ VALIDATION CHECKLIST

Before considering changelog complete:

- [ ] Version number matches version.py
- [ ] Date is accurate
- [ ] Previous version documented
- [ ] All security changes documented (if any)
- [ ] All new features listed
- [ ] All configuration changes documented
- [ ] All dependencies documented (added/removed/updated)
- [ ] Breaking changes identified (or marked as "None")
- [ ] Migration guide provided (if needed)
- [ ] File change statistics accurate
- [ ] Testing status included
- [ ] Related documents referenced

---

## 🔗 INTEGRATION WITH CHECKPOINT PROTOCOL

### Step-by-Step Integration:

**1. Review Changes**
- List all changed files (tracked and untracked)
- Review code changes
- Document fixes, features, modifications

**2. Update Documentation**
- Update README.md
- Update docs/production guides
- Update technical documentation

**3. Security Audit**
- Ensure no personal data
- Verify no hardcoded credentials
- Check .env configuration

**4. Version Update**
- Increment version.py
- Update README.md version badge
- Update GitHub About version

**5. CREATE CHANGELOG** ← **THIS STEP**
- Use template above
- Document ALL changes comprehensively
- Include migration guide
- Reference related documents

**6. Dependency Check**
- Update requirements.txt (if needed)
- Verify all imports

**7. Stage Files**
- Add core/required files
- Include changelog file
- Verify .env NOT staged

**8. Commit & Push**
- Use comprehensive commit message
- Reference changelog in commit
- Push to GitHub

---

## 📊 QUALITY STANDARDS

**Comprehensive:**
- Cover all changes, not just highlights
- Include technical details
- Document rationale for major changes

**Accurate:**
- Verify file counts
- Test migration steps
- Validate version numbers

**Accessible:**
- Use clear language
- Include examples
- Provide context

**Actionable:**
- Migration guides work
- Commands are correct
- Links are valid

---

## 🎯 EXAMPLES

**Good Changelog Examples:**
- `docs/housekeeping/status-tracking/CHANGELOG_v1.0.3.34.md` - Comprehensive, well-structured
- `docs/housekeeping/status-tracking/CHANGELOG_v1.0.3.10.md` - Clear sections, good details

**Reference for Structure:**
Current changelog format established in v1.0.3.34

---

## ⚠️ CONSEQUENCES OF SKIPPING

**If changelog is NOT created:**
- ❌ Violates CLAUDE.md CHECKPOINT PROTOCOL
- ❌ Pre-commit checklist incomplete
- ❌ No migration guide for users
- ❌ Lost documentation of changes
- ❌ Difficult to track version history
- ❌ Harder to debug issues in the future
- ❌ Non-compliant with project standards

---

## 🤖 AUTOMATION NOTES

**For Claude Code:**
- Always create changelog during checkpoint
- Use comprehensive template
- Include all sections (even if "None")
- Link to pre-commit audit
- Validate against checklist
- Update file count in pre-commit audit

**For Developers:**
- Review generated changelog
- Verify accuracy
- Add human context if needed
- Ensure migration steps tested

---

## 📚 REFERENCES

- **CLAUDE.md** - Line 101: CHECKPOINT PROTOCOL
- **CLAUDE.md** - Line 49: HOUSEKEEPING DOCUMENTATION requirement
- **Pre-Commit Audit Template** - Changelog requirement in checklist
- **Existing Changelogs** - docs/housekeeping/status-tracking/CHANGELOG_v*.md

---

**Last Updated:** 2025-10-26
**Version:** 1.0
**Author:** Claude Code (Sonnet 4.5)
