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


def mount(point, use, fstype="xfs", source=None, inodes=1.0):
    return {"mount_point": point, "fstype": fstype, "source": source or f"/dev/{point.strip('/') or 'root'}",
            "use_percent": use, "inode_percent": inodes, "avail_bytes": 10 * 1024 ** 3}


def test_full_mount_is_reported_even_when_total_looks_fine():
    fs = {"a": [mount("/", 96), mount("/data", 20)]}
    items = build_attention_items([server("a", disk_percentage=40)], {}, {}, THRESHOLDS, NOW,
                                  filesystems_by_server=fs)
    assert [(i["severity"], i["title"]) for i in items] == [("critical", "a / is 96% full")]
    assert "du -xh /" in items[0]["action"]


def test_boot_and_home_mounts_get_specific_actions():
    fs = {"a": [mount("/boot", 93), mount("/home", 90)]}
    users = {"a": [{"username": "alice", "disk": 300}]}
    items = build_attention_items([server("a")], {}, users, THRESHOLDS, NOW, filesystems_by_server=fs)
    actions = {i["metric"]["mount_point"]: i["action"] for i in items}
    assert "oldinstallonly" in actions["/boot"]
    assert "alice" in actions["/home"]


def test_shared_nfs_export_reported_once():
    share = lambda: mount("/share", 91, fstype="nfs4", source="nas:/share")
    fs = {"a": [share()], "b": [share()]}
    items = build_attention_items([server("a"), server("b")], {}, {}, THRESHOLDS, NOW,
                                  filesystems_by_server=fs)
    assert len(items) == 1
    assert items[0]["title"] == "Shared /share is 91% full"
    assert "mounted on a, b" in items[0]["detail"]


def test_inode_exhaustion():
    fs = {"a": [mount("/scratch", 30, inodes=96)]}
    items = build_attention_items([server("a")], {}, {}, THRESHOLDS, NOW, filesystems_by_server=fs)
    assert [(i["severity"], i["title"]) for i in items] == [("critical", "a /scratch is running out of inodes")]


def test_forecast_still_applies_with_mount_data():
    fs = {"a": [mount("/", 60)]}
    items = build_attention_items([server("a", disk_percentage=60)], {"a": 2.0}, {}, THRESHOLDS, NOW,
                                  filesystems_by_server=fs)
    assert [(i["severity"], i["category"]) for i in items] == [("warning", "disk")]


def test_pressure_saturated_disk_and_nic_errors():
    s = server("a", psi_io_full_avg60=25.0, psi_memory_full_avg60=None)
    io = {"a": [{"device": "dm-0", "name": "vg-root", "util_percent": 95, "await_ms": 40},
                {"device": "sdb", "name": "sdb", "util_percent": None}]}
    net = {"a": [{"interface": "eth0", "rx_errors_delta": 50, "tx_errors_delta": 0},
                 {"interface": "eth1", "rx_errors_delta": None, "tx_errors_delta": None}]}
    titles = sorted(i["title"] for i in build_attention_items(
        [s], {}, {}, THRESHOLDS, NOW, disk_io_by_server=io, network_by_server=net))
    assert titles == ["a disk vg-root is saturated", "a eth0 has network errors",
                      "a jobs are stalling on storage"]


from utils.insights import build_license_items  # noqa: E402


def snap(vendor, status="ok", minutes_ago=3, error=None):
    return {"vendor": vendor, "status": status, "error": error,
            "timestamp": NOW - timedelta(minutes=minutes_ago)}


def test_license_pool_exhausted_names_longest_holder():
    features = [{"vendor": "synopsys", "feature": "DC-Expert", "issued": 2, "in_use": 2}]
    checkouts = [
        {"vendor": "synopsys", "feature": "DC-Expert", "username": "bob", "server_name": "KSRC2",
         "client_host": "ksrc2.x", "start_at": NOW - timedelta(hours=3)},
        {"vendor": "synopsys", "feature": "DC-Expert", "username": "alice", "server_name": None,
         "client_host": "laptop7", "start_at": NOW - timedelta(days=3)},
    ]
    items = build_license_items([snap("synopsys")], features, checkouts, NOW)
    assert [(i["severity"], i["title"]) for i in items] == [("warning", "All 2 DC-Expert licenses are in use")]
    assert items[0]["detail"] == "Held by alice on laptop7 (3 d), bob on KSRC2 (3 h)."
    assert "longest held: alice" in items[0]["action"]


def test_license_query_states():
    items = build_license_items(
        [snap("all", "failed", error="SSH connection failed"), snap("cadence", "partial", error="239 features report errors"),
         snap("synopsys", minutes_ago=45)], [], [], NOW)
    assert sorted((i["severity"], i["title"]) for i in items) == [
        ("info", "Cadence license usage is incomplete"),
        ("warning", "License usage cannot be read"),
        ("warning", "Synopsys license usage is out of date"),
    ]


def test_busy_but_not_full_is_info_and_unissued_ignored():
    features = [{"vendor": "synopsys", "feature": "VCS", "issued": 10, "in_use": 8},
                {"vendor": "synopsys", "feature": "Odd", "issued": 0, "in_use": 1}]
    items = build_license_items([snap("synopsys")], features, [], NOW)
    assert [(i["severity"], i["title"]) for i in items] == [("info", "VCS: 8 of 10 licenses in use")]
