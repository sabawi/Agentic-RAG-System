#!/usr/bin/env python3
"""
Centralized Version Management
=============================

SINGLE SOURCE OF TRUTH for all version information in the Agentic-RAG System.

This module provides the authoritative version number that should be used
throughout the entire codebase. When incrementing versions, ONLY change
the VERSION constant below.

Usage:
    from version import VERSION, __version__, get_version_info, get_release_string

    # Use in code
    print(f"Server version: {__version__}")

    # Use in API responses
    {"version": VERSION}

    # Use in logging
    logger.info(f"Starting {get_release_string()}")
"""

# =============================================================================
# SINGLE SOURCE OF TRUTH - ONLY MODIFY THIS LINE TO UPDATE VERSION
# =============================================================================
VERSION = "1.0.2.99"

# =============================================================================
# DERIVED VALUES - DO NOT MODIFY THESE
# =============================================================================
__version__ = VERSION  # Standard Python version attribute
RELEASE = "Production Ready"

# Version components for programmatic access
version_parts = VERSION.split('.')
MAJOR = version_parts[0]
MINOR = version_parts[1]
PATCH = version_parts[2]
BUILD = version_parts[3] if len(version_parts) > 3 else "0"
VERSION_TUPLE = tuple(int(part) for part in version_parts)

def get_version_info():
    """
    Get comprehensive version information.

    Returns:
        dict: Complete version information including components
    """
    return {
        "version": VERSION,
        "major": int(MAJOR),
        "minor": int(MINOR),
        "patch": int(PATCH),
        "build": int(BUILD),
        "release": RELEASE,
        "version_tuple": VERSION_TUPLE
    }

def get_release_string():
    """
    Get formatted release string for display.

    Returns:
        str: Formatted release string
    """
    return f"Agentic-RAG Server v{VERSION} - {RELEASE}"

def get_api_version():
    """
    Get version in API-compatible format.

    Returns:
        str: Version string for API responses
    """
    return VERSION

def get_short_version():
    """
    Get shortened version (MAJOR.MINOR only).

    Returns:
        str: Short version string
    """
    return f"{MAJOR}.{MINOR}"

# =============================================================================
# BACKWARDS COMPATIBILITY
# =============================================================================
# These ensure existing code continues to work
__release__ = RELEASE

# =============================================================================
# VERSION VALIDATION
# =============================================================================
def validate_version():
    """Validate version format and components."""
    try:
        parts = VERSION.split('.')
        if len(parts) < 3 or len(parts) > 4:
            raise ValueError(f"Version must have 3 or 4 parts, got {len(parts)}")

        for part in parts:
            int(part)  # Ensure each part is numeric

        return True
    except Exception as e:
        raise ValueError(f"Invalid version format '{VERSION}': {e}")

# Validate on import
validate_version()