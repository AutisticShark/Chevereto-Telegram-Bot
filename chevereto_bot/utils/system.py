"""Cross-platform system monitoring using psutil."""

from __future__ import annotations

import datetime
import os
import time

import psutil

from chevereto_bot.utils.media import format_file_size


def get_system_uptime() -> str:
    """Return formatted system uptime."""
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    delta = datetime.timedelta(seconds=int(uptime_seconds))
    return f"System Uptime: {delta}"


def get_storage_status(path: str = ".") -> str:
    """Return disk storage status for the drive containing path."""
    usage = psutil.disk_usage(os.path.abspath(path))
    total_str = format_file_size(usage.total)
    used_str = format_file_size(usage.used)
    free_str = format_file_size(usage.free)
    return (
        f"Disk Usage ({os.path.abspath(path)}):\n"
        f"Total: {total_str}\n"
        f"Used: {used_str} ({usage.percent}%)\n"
        f"Free: {free_str}"
    )


def get_system_overview() -> str:
    """Return a comprehensive system status report."""
    uptime_str = get_system_uptime()
    cpu_percent = psutil.cpu_percent(interval=0.1)

    mem = psutil.virtual_memory()
    mem_used = format_file_size(mem.used)
    mem_total = format_file_size(mem.total)

    disk = psutil.disk_usage(os.path.abspath("."))
    disk_free = format_file_size(disk.free)
    disk_total = format_file_size(disk.total)

    return (
        f"🖥️ System Status Overview:\n"
        f"⏱️ {uptime_str}\n"
        f"⚙️ CPU Usage: {cpu_percent}%\n"
        f"🧠 Memory: {mem_used} / {mem_total} ({mem.percent}%)\n"
        f"💾 Disk Free: {disk_free} / {disk_total} ({100 - disk.percent:.1f}% free)"
    )
