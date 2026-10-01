"""Tests for utils.insights decision rules (no database needed)."""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.insights import build_attention_items, parse_size_gb, rank_placement  # noqa: E402

NOW = datetime(2026, 10, 1, 12, 0)
THRESHOLDS = {"disk_warning": 85, "disk_critical": 95, "memory_warning": 85, "memory_critical": 95}


def server(name, **overrides):
    row = {
        "server_name": name, "timestamp": NOW - timedelta(minutes=5),
        "disk_percentage": 50, "ram_percentage": 40, "swap_percentage": 0,
        "virtual_cpus": 32, "cpu_load_5min": 1.0,
        "ram_total": "64.00G", "ram_used": "16.00G", "disk_used": "1T", "disk_total": "2T",
        "logged_users": 2,
    }
    row.update(overrides)
    return row


def test_parse_size_gb_handles_df_and_free_units():
    assert parse_size_gb("62.88G") == 62.88
    assert parse_size_gb("1.8T") == 1.8 * 1024
    assert parse_size_gb("512M") == 0.5
    assert parse_size_gb("garbage") is None
    assert parse_size_gb(None) is None


def test_healthy_fleet_has_no_items():
    assert build_attention_items([server("A")], {}, {}, THRESHOLDS, NOW) == []


def test_stale_server_is_critical_and_suppresses_other_checks():
    stale = server("A", timestamp=NOW - timedelta(hours=2), disk_percentage=99)
    items = build_attention_items([stale], {}, {}, THRESHOLDS, NOW)
    assert [(i["severity"], i["category"]) for i in items] == [("critical", "offline")]


def test_full_disk_names_largest_users():
    users = {"A": [{"username": "alice", "disk": 200, "mem": 1},
                   {"username": "bob", "disk": 50, "mem": 1},
                   {"username": "idle", "disk": 0, "mem": 0}]}
    items = build_attention_items([server("A", disk_percentage=96)], {}, users, THRESHOLDS, NOW)
    assert items[0]["severity"] == "critical"
    assert "alice (200 GB), bob (50 GB)" in items[0]["action"]
    assert "idle" not in items[0]["action"]


def test_growth_forecast_escalates_below_threshold():
    # 70% full growing 2 points/day -> full in 15 days -> warning despite < 85%
    items = build_attention_items([server("A", disk_percentage=70)], {"A": 2.0}, {}, THRESHOLDS, NOW)
    assert items[0]["severity"] == "warning"
    assert round(items[0]["metric"]["days_to_full"]) == 15


def test_slow_growth_is_informational():
    items = build_attention_items([server("A", disk_percentage=60)], {"A": 0.5}, {}, THRESHOLDS, NOW)
    assert items[0]["severity"] == "info"


def test_cpu_oversubscription():
    items = build_attention_items([server("A", cpu_load_5min=50)], {}, {}, THRESHOLDS, NOW)
    assert items[0]["category"] == "cpu" and items[0]["severity"] == "critical"


def test_items_sorted_by_severity():
    servers = [server("A", disk_percentage=60), server("B", disk_percentage=96)]
    items = build_attention_items(servers, {"A": 0.5}, {}, THRESHOLDS, NOW)
    assert [i["severity"] for i in items] == ["critical", "info"]


def test_placement_prefers_absolute_headroom_and_skips_offline():
    big = server("big", virtual_cpus=104, cpu_load_5min=1, ram_total="256G", ram_used="128G")
    small = server("small", virtual_cpus=8, cpu_load_5min=0, ram_total="32G", ram_used="4G")
    gone = server("gone", timestamp=NOW - timedelta(hours=3))
    ranked = rank_placement([small, gone, big], NOW)
    assert [r["server_name"] for r in ranked] == ["big", "small", "gone"]
    assert ranked[0]["best_for"] == "both"
    assert ranked[-1]["available"] is False and ranked[-1]["score"] == 0
