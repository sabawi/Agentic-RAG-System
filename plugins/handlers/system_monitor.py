#!/usr/bin/env python3
"""
System Monitor Plugin
Monitors system resources and processes.
"""

import sys
import json
import asyncio
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def get_cpu_info() -> Dict[str, Any]:
    """Get CPU usage information"""
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()

    return {
        "cpu_percent_avg": sum(cpu_percent) / len(cpu_percent),
        "cpu_percent_per_core": cpu_percent,
        "cpu_count": cpu_count,
        "cpu_freq_current": cpu_freq.current if cpu_freq else None,
        "cpu_freq_max": cpu_freq.max if cpu_freq else None
    }


def get_memory_info() -> Dict[str, Any]:
    """Get memory usage information"""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "memory_total": mem.total,
        "memory_used": mem.used,
        "memory_available": mem.available,
        "memory_percent": mem.percent,
        "swap_total": swap.total,
        "swap_used": swap.used,
        "swap_percent": swap.percent
    }


def get_disk_info() -> Dict[str, Any]:
    """Get disk usage information"""
    partitions = psutil.disk_partitions()
    disk_info = []

    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            })
        except PermissionError:
            continue

    return {"partitions": disk_info}


def get_process_info(limit: int = 10) -> Dict[str, Any]:
    """Get top processes by CPU and memory usage"""
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
        try:
            pinfo = proc.info
            processes.append({
                "pid": pinfo['pid'],
                "name": pinfo['name'],
                "cpu_percent": pinfo['cpu_percent'] or 0.0,
                "memory_percent": pinfo['memory_percent'] or 0.0,
                "memory_mb": pinfo['memory_info'].rss / 1024 / 1024 if pinfo['memory_info'] else 0
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort by CPU usage
    top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:limit]

    # Sort by memory usage
    top_memory = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:limit]

    return {
        "total_processes": len(processes),
        "top_cpu": top_cpu,
        "top_memory": top_memory
    }


def format_cpu_report(cpu_info: Dict[str, Any]) -> str:
    """Format CPU information as text"""
    lines = [
        "🖥️  CPU Information:",
        f"  Average Usage: {cpu_info['cpu_percent_avg']:.1f}%",
        f"  CPU Cores: {cpu_info['cpu_count']}",
    ]

    if cpu_info['cpu_freq_current']:
        lines.append(f"  Frequency: {cpu_info['cpu_freq_current']:.0f} MHz (max: {cpu_info['cpu_freq_max']:.0f} MHz)")

    lines.append(f"\n  Per-Core Usage:")
    for i, usage in enumerate(cpu_info['cpu_percent_per_core']):
        lines.append(f"    Core {i}: {usage:.1f}%")

    return '\n'.join(lines)


def format_memory_report(mem_info: Dict[str, Any]) -> str:
    """Format memory information as text"""
    lines = [
        "💾 Memory Information:",
        f"  Total: {format_bytes(mem_info['memory_total'])}",
        f"  Used: {format_bytes(mem_info['memory_used'])} ({mem_info['memory_percent']:.1f}%)",
        f"  Available: {format_bytes(mem_info['memory_available'])}",
    ]

    if mem_info['swap_total'] > 0:
        lines.append(f"\n  Swap:")
        lines.append(f"    Total: {format_bytes(mem_info['swap_total'])}")
        lines.append(f"    Used: {format_bytes(mem_info['swap_used'])} ({mem_info['swap_percent']:.1f}%)")

    return '\n'.join(lines)


def format_disk_report(disk_info: Dict[str, Any]) -> str:
    """Format disk information as text"""
    lines = ["💿 Disk Information:"]

    for partition in disk_info['partitions']:
        lines.append(f"\n  {partition['mountpoint']} ({partition['device']}):")
        lines.append(f"    Total: {format_bytes(partition['total'])}")
        lines.append(f"    Used: {format_bytes(partition['used'])} ({partition['percent']:.1f}%)")
        lines.append(f"    Free: {format_bytes(partition['free'])}")

    return '\n'.join(lines)


def format_process_report(proc_info: Dict[str, Any]) -> str:
    """Format process information as text"""
    lines = [f"⚙️  Process Information (Total: {proc_info['total_processes']}):"]

    lines.append(f"\n  Top CPU Consumers:")
    for i, proc in enumerate(proc_info['top_cpu'], 1):
        lines.append(
            f"    {i}. {proc['name']} (PID {proc['pid']}): "
            f"{proc['cpu_percent']:.1f}% CPU"
        )

    lines.append(f"\n  Top Memory Consumers:")
    for i, proc in enumerate(proc_info['top_memory'], 1):
        lines.append(
            f"    {i}. {proc['name']} (PID {proc['pid']}): "
            f"{proc['memory_mb']:.1f} MB ({proc['memory_percent']:.1f}%)"
        )

    return '\n'.join(lines)


async def execute(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monitor system resources.

    Args:
        parameters: {
            "metric": "cpu" | "memory" | "disk" | "processes" | "all",
            "process_limit": int
        }

    Returns:
        {
            "success": bool,
            "result": str,
            "error": str | None,
            "metadata": dict
        }
    """
    if not PSUTIL_AVAILABLE:
        return {
            "success": False,
            "result": None,
            "error": "psutil library not installed. Please run: pip install psutil",
            "metadata": {"psutil_available": False}
        }

    metric = parameters.get('metric', 'all')
    process_limit = parameters.get('process_limit', 10)

    try:
        result_lines = []
        metadata = {"metric": metric}

        if metric in ['cpu', 'all']:
            cpu_info = get_cpu_info()
            result_lines.append(format_cpu_report(cpu_info))
            metadata['cpu'] = cpu_info

        if metric in ['memory', 'all']:
            mem_info = get_memory_info()
            result_lines.append('\n' + format_memory_report(mem_info))
            metadata['memory'] = mem_info

        if metric in ['disk', 'all']:
            disk_info = get_disk_info()
            result_lines.append('\n' + format_disk_report(disk_info))
            metadata['disk'] = disk_info

        if metric in ['processes', 'all']:
            proc_info = get_process_info(process_limit)
            result_lines.append('\n' + format_process_report(proc_info))
            metadata['processes'] = {
                "total": proc_info['total_processes'],
                "top_cpu_count": len(proc_info['top_cpu']),
                "top_memory_count": len(proc_info['top_memory'])
            }

        result_text = '\n'.join(result_lines)

        return {
            "success": True,
            "result": result_text,
            "error": None,
            "metadata": metadata
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Error monitoring system: {str(e)}",
            "metadata": {
                "metric": metric,
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
