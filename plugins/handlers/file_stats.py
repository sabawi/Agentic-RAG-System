#!/usr/bin/env python3
"""
File Statistics Plugin
Provides detailed file and directory statistics.
"""

import sys
import json
import asyncio
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_permissions(mode: int) -> str:
    """Format file permissions as rwxrwxrwx"""
    perms = []
    for who in ['USR', 'GRP', 'OTH']:
        for what in ['R', 'W', 'X']:
            if mode & getattr(os, f'{what}_OK'):
                perms.append(what.lower())
            else:
                perms.append('-')
    return ''.join(perms)


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """Get detailed file information"""
    stat = file_path.stat()

    info = {
        "name": file_path.name,
        "path": str(file_path.absolute()),
        "type": "directory" if file_path.is_dir() else "file",
        "size": stat.st_size,
        "size_formatted": format_size(stat.st_size),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "permissions": oct(stat.st_mode)[-3:],
        "owner_uid": stat.st_uid,
        "group_gid": stat.st_gid
    }

    # Add line count for text files
    if file_path.is_file() and stat.st_size < 10_000_000:  # Only for files < 10MB
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
            info['lines'] = line_count
        except:
            info['lines'] = None

    return info


def get_directory_stats(dir_path: Path, include_hidden: bool, recursive: bool) -> Dict[str, Any]:
    """Get directory statistics"""
    total_size = 0
    file_count = 0
    dir_count = 0
    files_list = []

    try:
        items = list(dir_path.iterdir())

        for item in items:
            # Skip hidden files if requested
            if not include_hidden and item.name.startswith('.'):
                continue

            if item.is_file():
                file_count += 1
                item_stat = item.stat()
                total_size += item_stat.st_size
                files_list.append({
                    "name": item.name,
                    "size": item_stat.st_size,
                    "size_formatted": format_size(item_stat.st_size),
                    "modified": datetime.fromtimestamp(item_stat.st_mtime).isoformat()
                })
            elif item.is_dir():
                dir_count += 1
                if recursive:
                    # Recursively calculate directory size
                    for root, dirs, files in os.walk(item):
                        for f in files:
                            try:
                                fp = Path(root) / f
                                total_size += fp.stat().st_size
                                file_count += 1
                            except:
                                pass

        # Sort files by size (largest first)
        files_list.sort(key=lambda x: x['size'], reverse=True)

        return {
            "total_size": total_size,
            "total_size_formatted": format_size(total_size),
            "file_count": file_count,
            "directory_count": dir_count,
            "largest_files": files_list[:10]  # Top 10 largest files
        }

    except PermissionError:
        raise PermissionError(f"Permission denied accessing: {dir_path}")


async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get file or directory statistics.

    Args:
        parameters: {
            "path": str,
            "include_hidden": bool,
            "recursive": bool
        }

    Returns:
        {
            "success": bool,
            "result": str,
            "error": str | None,
            "metadata": dict
        }
    """
    path_str = parameters['path']
    include_hidden = parameters.get('include_hidden', False)
    recursive = parameters.get('recursive', False)

    try:
        path = Path(path_str).expanduser().resolve()

        # Check if path exists
        if not path.exists():
            return {
                "success": False,
                "result": None,
                "error": f"Path does not exist: {path_str}",
                "metadata": {
                    "path": path_str,
                    "exists": False
                }
            }

        # Get basic info
        info = get_file_info(path)

        # Build result string
        result_lines = [
            f"📁 File Statistics: {path.name}",
            f"",
            f"Path: {info['path']}",
            f"Type: {info['type'].capitalize()}",
            f"Size: {info['size_formatted']} ({info['size']:,} bytes)",
            f"Modified: {info['modified']}",
            f"Permissions: {info['permissions']}",
        ]

        if info.get('lines') is not None:
            result_lines.append(f"Lines: {info['lines']:,}")

        # Add directory statistics
        if path.is_dir():
            result_lines.append(f"\n📊 Directory Contents:")
            dir_stats = get_directory_stats(path, include_hidden, recursive)
            result_lines.append(f"  Files: {dir_stats['file_count']:,}")
            result_lines.append(f"  Subdirectories: {dir_stats['directory_count']:,}")
            result_lines.append(f"  Total size: {dir_stats['total_size_formatted']}")

            if dir_stats['largest_files']:
                result_lines.append(f"\n📋 Largest Files:")
                for i, file in enumerate(dir_stats['largest_files'][:5], 1):
                    result_lines.append(
                        f"  {i}. {file['name']} - {file['size_formatted']}"
                    )

            info['directory_stats'] = dir_stats

        result_text = '\n'.join(result_lines)

        return {
            "success": True,
            "result": result_text,
            "error": None,
            "metadata": info
        }

    except PermissionError as e:
        return {
            "success": False,
            "result": None,
            "error": f"Permission denied: {str(e)}",
            "metadata": {
                "path": path_str,
                "permission_error": True
            }
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Error analyzing path: {str(e)}",
            "metadata": {
                "path": path_str,
                "error_type": type(e).__name__
            }
        }


# Communication protocol (boilerplate)
if __name__ == "__main__":
    try:
        input_data = sys.stdin.read()
        parameters = json.loads(input_data)
        result = asyncio.run(execute(parameters))
        print(json.dumps(result))
        sys.exit(0 if result['success'] else 1)
    except Exception as e:
        error_result = {
            "success": False,
            "result": None,
            "error": f"Plugin error: {str(e)}",
            "metadata": {}
        }
        print(json.dumps(error_result))
        sys.exit(1)
