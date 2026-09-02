"""Tests for cross-platform system status functions."""

from __future__ import annotations

from chevereto_bot.utils.system import get_storage_status, get_system_overview, get_system_uptime


def test_system_uptime():
    uptime = get_system_uptime()
    assert "System Uptime:" in uptime


def test_storage_status():
    status = get_storage_status()
    assert "Disk Usage" in status
    assert "Total:" in status
    assert "Used:" in status
    assert "Free:" in status


def test_system_overview():
    overview = get_system_overview()
    assert "System Status Overview" in overview
    assert "CPU Usage:" in overview
    assert "Memory:" in overview
    assert "Disk Free:" in overview
