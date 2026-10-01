"""
Actionable insights
Single Responsibility: turn raw metric rows into decisions for people —
what needs an admin's attention, and where a user should run a job.

Pure functions only (no database access) so the rules are easy to test.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# A server that has not reported for two collection cycles (2 x 15 min) is offline.
STALE_AFTER_MINUTES = 30

# Disks growing faster than this (percentage points per day) get a fill forecast.
MIN_GROWTH_PER_DAY = 0.05
FORECAST_HORIZON_DAYS = 30

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}

_SIZE_UNITS = {"K": 1 / (1024 * 1024), "M": 1 / 1024, "G": 1, "T": 1024, "P": 1024 * 1024}


def parse_size_gb(value: Any) -> Optional[float]:
    """Parse sizes reported by `free -h`/`df -h` ("62.88G", "801G", "1.8T") into GiB."""
    if value is None:
        return None
    match = re.match(r"^\s*([\d.]+)\s*([KMGTP])?i?B?\s*$", str(value), re.IGNORECASE)
    if not match:
        return None
    number = float(match.group(1))
    unit = (match.group(2) or "G").upper()
    return number * _SIZE_UNITS[unit]


def minutes_since(timestamp: Optional[datetime], now: datetime) -> Optional[float]:
    if timestamp is None:
        return None
    return (now - timestamp).total_seconds() / 60


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _names(users: List[Dict[str, Any]], field: str, unit: str, limit: int = 3) -> str:
    """Render 'alice (226 GB), bob (120 GB)' for the heaviest users by `field`."""
    ranked = sorted(users, key=lambda u: _num(u.get(field)), reverse=True)
    picked = [u for u in ranked if _num(u.get(field)) > 0][:limit]
    return ", ".join(f"{u['username']} ({_num(u.get(field)):.0f}{unit})" for u in picked)


def build_attention_items(
    servers: List[Dict[str, Any]],
    disk_growth: Dict[str, float],
    users_by_server: Dict[str, List[Dict[str, Any]]],
    thresholds: Dict[str, float],
    now: datetime,
) -> List[Dict[str, Any]]:
    """
    Produce a ranked list of issues, each with a concrete next step.

    servers         latest server_metrics row per server
    disk_growth     server -> disk growth in percentage points per day (14-day trend)
    users_by_server server -> top_users rows
    thresholds      PERFORMANCE_THRESHOLDS from flask_config
    """
    items: List[Dict[str, Any]] = []

    def add(severity, category, server, title, detail, action, **metric):
        items.append({
            "severity": severity,
            "category": category,
            "server": server,
            "title": title,
            "detail": detail,
            "action": action,
            "metric": metric,
        })

    for s in servers:
        name = s["server_name"]
        users = users_by_server.get(name, [])
        age = minutes_since(s.get("timestamp"), now)

        # Offline / stale data takes precedence: the other numbers are not current.
        if age is not None and age > STALE_AFTER_MINUTES:
            add("critical", "offline", name,
                f"{name} has stopped reporting",
                f"Last data received {age / 60:.1f} h ago; figures shown for it are out of date.",
                "Check SSH reachability from the DataCollection container "
                "(make logs-DataCollection) and whether the host is up.",
                minutes_since_report=round(age))
            continue

        # Disk: current fill level, and a fill-date forecast from the 14-day trend.
        disk = _num(s.get("disk_percentage"))
        growth = disk_growth.get(name, 0.0) or 0.0
        days_to_full = (100 - disk) / growth if growth >= MIN_GROWTH_PER_DAY and disk < 100 else None
        disk_users = _names(users, "disk", " GB")
        cleanup = (f"Ask the largest users to archive or clean up: {disk_users}."
                   if disk_users else "Identify large directories and archive or clean up.")

        if disk >= thresholds["disk_critical"]:
            add("critical", "disk", name, f"{name} disk is {disk:.0f}% full",
                f"{s.get('disk_used', '?')} of {s.get('disk_total', '?')} used"
                + (f"; full in about {days_to_full:.0f} days at the current rate." if days_to_full else "."),
                cleanup, disk_percentage=disk, days_to_full=days_to_full)
        elif disk >= thresholds["disk_warning"] or (days_to_full is not None and days_to_full <= FORECAST_HORIZON_DAYS):
            add("warning", "disk", name, f"{name} disk is {disk:.0f}% full",
                (f"Growing {growth:.2f} points/day — full in about {days_to_full:.0f} days."
                 if days_to_full else f"{s.get('disk_used', '?')} of {s.get('disk_total', '?')} used; no growth trend."),
                cleanup, disk_percentage=disk, days_to_full=days_to_full)
        elif days_to_full is not None:
            add("info", "disk", name, f"{name} disk filling steadily",
                f"{disk:.0f}% full, growing {growth:.2f} points/day — full in about {days_to_full:.0f} days.",
                "No action yet; plan capacity before it crosses "
                f"{thresholds['disk_warning']:.0f}%.",
                disk_percentage=disk, days_to_full=days_to_full)

        # Memory pressure
        ram = _num(s.get("ram_percentage"))
        if ram >= thresholds["memory_warning"]:
            mem_users = _names(users, "mem", "%")
            add("critical" if ram >= thresholds["memory_critical"] else "warning", "memory", name,
                f"{name} memory is {ram:.0f}% used",
                f"{s.get('ram_used', '?')} of {s.get('ram_total', '?')} in use; new jobs may swap or be killed.",
                f"Check the largest memory users: {mem_users}." if mem_users
                else "Check which processes hold the most memory (ps --sort=-rss).",
                ram_percentage=ram)

        # Swap in active use usually means memory is oversubscribed
        swap = _num(s.get("swap_percentage"))
        if swap >= 50:
            add("warning", "swap", name, f"{name} swap is {swap:.0f}% used",
                "Heavy swapping slows every job on the machine.",
                "Find the process driving memory pressure and move it to a larger host.",
                swap_percentage=swap)

        # CPU oversubscription: 5-minute load per logical CPU
        vcpus = _num(s.get("virtual_cpus"))
        load = _num(s.get("cpu_load_5min"))
        if vcpus > 0 and load / vcpus >= 1.0:
            ratio = load / vcpus
            add("critical" if ratio >= 1.5 else "warning", "cpu", name,
                f"{name} CPU is oversubscribed",
                f"Load {load:.1f} on {vcpus:.0f} logical CPUs ({ratio:.1f}× capacity); jobs are queueing.",
                "Steer new jobs to a less busy server (see Where to run).",
                load_per_cpu=round(ratio, 2))

    items.sort(key=lambda i: (SEVERITY_ORDER[i["severity"]], i["server"]))
    return items


def rank_placement(servers: List[Dict[str, Any]], now: datetime) -> List[Dict[str, Any]]:
    """
    Rank servers by spare capacity for a new job.

    Free cores use the 5-minute load average rather than cpu_usage_percent,
    which the collector currently reports as a since-boot average. The score
    (0-100) weighs free cores and free RAM equally, relative to the server
    with the most of each.
    """
    ranked = []
    for s in servers:
        age = minutes_since(s.get("timestamp"), now)
        vcpus = _num(s.get("virtual_cpus"))
        load = _num(s.get("cpu_load_5min"))
        ram_total = parse_size_gb(s.get("ram_total"))
        ram_used = parse_size_gb(s.get("ram_used"))
        free_cores = max(0.0, vcpus - load)
        free_ram = max(0.0, ram_total - ram_used) if ram_total is not None and ram_used is not None else None
        available = age is not None and age <= STALE_AFTER_MINUTES and _num(s.get("disk_percentage")) < 98

        ranked.append({
            "server_name": s["server_name"],
            "available": available,
            "score": 0,
            "free_cores": round(free_cores, 1),
            "virtual_cpus": int(vcpus),
            "load_5min": round(load, 2),
            "free_ram_gb": round(free_ram, 1) if free_ram is not None else None,
            "ram_total_gb": round(ram_total, 1) if ram_total is not None else None,
            "sessions": int(_num(s.get("logged_users"))),
            "disk_percentage": int(_num(s.get("disk_percentage"))),
        })

    # Score absolute headroom against the roomiest available server, so a large
    # host with lots of spare capacity outranks a small idle one.
    candidates = [r for r in ranked if r["available"]]
    max_cores = max((r["free_cores"] for r in candidates), default=0) or 1
    max_ram = max((r["free_ram_gb"] or 0 for r in candidates), default=0) or 1
    for r in candidates:
        r["score"] = round(100 * (0.5 * r["free_cores"] / max_cores + 0.5 * (r["free_ram_gb"] or 0) / max_ram))

    ranked.sort(key=lambda r: (not r["available"], -r["score"]))

    if candidates:
        max(candidates, key=lambda r: r["free_cores"])["best_for"] = "cpu"
        best_ram = max(candidates, key=lambda r: r["free_ram_gb"] or 0)
        best_ram["best_for"] = "both" if best_ram.get("best_for") == "cpu" else "memory"
    return ranked
