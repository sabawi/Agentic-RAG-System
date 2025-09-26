# Version Management System

## Single Source of Truth

The project now uses a **centralized version management system** to ensure consistency across all files and components.

## Key Files

- **`version.py`** - The ONLY place where version numbers are defined
- **`utils/version_sync.py`** - Utilities to sync version to config files
- **`scripts/version_update.py`** - Automated version update tool

## How to Update Versions

### Option 1: Automated Script (Recommended)

```bash
# Increment build number (1.0.2.76 → 1.0.2.77)
python scripts/version_update.py --increment build

# Increment patch number (1.0.2.76 → 1.0.3.0)
python scripts/version_update.py --increment patch

# Set specific version
python scripts/version_update.py --version 1.0.3.0

# Check current status
python scripts/version_update.py --status
```

### Option 2: Manual Update

1. Edit `version.py` and change the `VERSION` constant
2. Run sync script: `python utils/version_sync.py --update`
3. Verify consistency: `python utils/version_sync.py --verify`

## What Gets Updated Automatically

When you update the version, these files are automatically synchronized:

- ✅ `fastapi_server_complete.py` - Server version and docstring
- ✅ `config/logging_config.json` - Logging configuration version
- ✅ `/health` API endpoint - Returns current version
- ✅ All Python imports that use `from version import __version__`

## Version Format

The project uses a 4-part version scheme: `MAJOR.MINOR.PATCH.BUILD`

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible
- **BUILD**: Incremental builds, patches, hotfixes

## API Access

The current version is accessible via:

```bash
# Health endpoint
curl http://localhost:5000/health | jq '.version'

# Python code
from version import VERSION, __version__, get_version_info
```

## Benefits

1. **Consistency**: No more version mismatches between files
2. **Automation**: One command updates everything
3. **Verification**: Built-in consistency checking
4. **Maintainability**: Single point of change for version updates
5. **API Access**: Version available programmatically

## Migration from Old System

The old system had hardcoded versions in multiple places:
- `fastapi_server_complete.py` docstring
- `config/logging_config.json`
- Various documentation files

All these have been centralized to use `version.py` as the single source of truth.

## Best Practices

1. **Always use the automated script** for version updates
2. **Never hardcode version numbers** in new code
3. **Import from version.py** for any version references
4. **Run verification** before commits: `python scripts/version_update.py --verify`
5. **Update version in every commit** per project guidelines

## Troubleshooting

If version inconsistencies are detected:

```bash
# Fix all inconsistencies
python utils/version_sync.py --update

# Check what's wrong
python utils/version_sync.py --verify

# View current status
python scripts/version_update.py --status
```