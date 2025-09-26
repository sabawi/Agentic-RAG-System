#!/usr/bin/env python3
"""
Automated Version Update Script
==============================

This script provides a seamless way to update the version across the entire project.
It ensures that when you increment the version in version.py, ALL references
are automatically updated consistently.

Usage:
    # Update to specific version
    python scripts/version_update.py --version 1.0.2.77

    # Auto-increment build number
    python scripts/version_update.py --increment build

    # Auto-increment patch number
    python scripts/version_update.py --increment patch

    # Verify current version consistency
    python scripts/version_update.py --verify

    # Show version summary
    python scripts/version_update.py --status
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def update_version_in_file(new_version):
    """Update the VERSION constant in version.py"""
    version_file = Path(__file__).parent.parent / "version.py"

    with open(version_file, 'r') as f:
        content = f.read()

    # Replace the VERSION line
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('VERSION = '):
            lines[i] = f'VERSION = "{new_version}"'
            break

    with open(version_file, 'w') as f:
        f.write('\n'.join(lines))

    print(f"✅ Updated version.py to {new_version}")

def increment_version(increment_type):
    """Increment version based on type"""
    # Import current version
    from version import VERSION

    parts = VERSION.split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    build = int(parts[3]) if len(parts) > 3 else 0

    if increment_type == "major":
        major += 1
        minor = 0
        patch = 0
        build = 0
    elif increment_type == "minor":
        minor += 1
        patch = 0
        build = 0
    elif increment_type == "patch":
        patch += 1
        build = 0
    elif increment_type == "build":
        build += 1
    else:
        raise ValueError(f"Invalid increment type: {increment_type}")

    new_version = f"{major}.{minor}.{patch}.{build}"
    return new_version

def sync_all_files():
    """Synchronize version across all configuration files"""
    # Import the sync utility
    sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
    from version_sync import update_all_configs, verify_version_consistency

    print("🔄 Synchronizing version across all files...")
    results = update_all_configs()

    for file_type, success in results.items():
        if success:
            print(f"✅ Updated {file_type}")
        else:
            print(f"❌ Failed to update {file_type}")

    # Verify consistency
    verification = verify_version_consistency()
    if verification["consistent"]:
        print("✅ All version references are consistent")
    else:
        print("❌ Version inconsistencies found:")
        for issue in verification["issues"]:
            print(f"  - {issue}")

    return verification["consistent"]

def show_status():
    """Show current version status"""
    from version import VERSION, get_version_info

    print(f"📋 Current Version Status")
    print(f"{'='*50}")
    print(f"Version: {VERSION}")

    info = get_version_info()
    print(f"Components: Major={info['major']}, Minor={info['minor']}, Patch={info['patch']}, Build={info['build']}")
    print(f"Release: {info['release']}")
    print(f"Version Tuple: {info['version_tuple']}")

    # Check consistency
    sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
    from version_sync import verify_version_consistency

    verification = verify_version_consistency()
    print(f"\n🔍 Consistency Check:")
    if verification["consistent"]:
        print("✅ All version references are synchronized")
    else:
        print("❌ Issues found:")
        for issue in verification["issues"]:
            print(f"  - {issue}")

def main():
    parser = argparse.ArgumentParser(description="Automated version management")
    parser.add_argument("--version", help="Set specific version (e.g., 1.0.2.77)")
    parser.add_argument("--increment", choices=["major", "minor", "patch", "build"],
                       help="Auto-increment version component")
    parser.add_argument("--verify", action="store_true", help="Verify version consistency")
    parser.add_argument("--status", action="store_true", help="Show version status")
    parser.add_argument("--sync-only", action="store_true", help="Only sync files, don't change version")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.verify:
        print("🔍 Verifying version consistency...")
        consistent = sync_all_files()
        sys.exit(0 if consistent else 1)

    if args.sync_only:
        sync_all_files()
        return

    if args.version:
        # Set specific version
        print(f"🎯 Setting version to {args.version}")
        update_version_in_file(args.version)

    elif args.increment:
        # Auto-increment version
        print(f"📈 Incrementing {args.increment} version")
        new_version = increment_version(args.increment)
        print(f"🎯 New version: {new_version}")
        update_version_in_file(new_version)

    else:
        parser.print_help()
        return

    # Always sync files after version change
    print("\n🔄 Synchronizing all files...")
    sync_all_files()

    print(f"\n✅ Version update complete!")
    print(f"📝 Next steps:")
    print(f"  1. Review changes: git diff")
    print(f"  2. Test the application")
    print(f"  3. Commit changes: git add . && git commit -m 'version bump'")

if __name__ == "__main__":
    main()