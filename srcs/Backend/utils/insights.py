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

# Network filesystems are shared between servers: report each export once.
REMOTE_FSTYPES = {"nfs", "nfs4", "cifs", "smbfs", "smb3", "lustre", "gpfs", "fuse.sshfs", "ceph", "glusterfs"}
INODE_WARNING = 90
INODE_CRITICAL = 95
# Share of the last minute in which all non-idle tasks were stalled (PSI "full")
PRESSURE_WARNING = 10
# Device busy for this share of the collection interval
DISK_UTIL_WARNING = 80
# Interface errors per collection interval worth investigating
NIC_ERRORS_WARNING = 10

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
    filesystems_by_server: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    disk_io_by_server: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    network_by_server: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> List[Dict[str, Any]]:
    """
    Produce a ranked list of issues, each with a concrete next step.

    servers         latest server_metrics row per server
    disk_growth     server -> disk growth in percentage points per day (14-day trend)
    users_by_server server -> top_users rows
    thresholds      PERFORMANCE_THRESHOLDS from flask_config
    *_by_server     latest per-mount / per-device / per-interface rows (optional);
                    with mounts, fill levels are judged per mount, not on the total
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

    shared_mounts: Dict[str, Dict[str, Any]] = {}

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

        mounts = (filesystems_by_server or {}).get(name)
        if mounts:
            mount_alerts = 0
            for m in mounts:
                if (m.get("fstype") or "") in REMOTE_FSTYPES:
                    entry = shared_mounts.setdefault(m.get("source") or m["mount_point"], dict(m, servers=[]))
                    entry["servers"].append(name)
                    continue
                mount_alerts += _mount_items(add, name, m, users, thresholds)
            if days_to_full is not None and not mount_alerts:
                soon = days_to_full <= FORECAST_HORIZON_DAYS
                add("warning" if soon else "info", "disk", name,
                    f"{name} disk filling steadily",
                    f"Local disks {disk:.0f}% full in total, growing {growth:.2f} points/day "
                    f"— full in about {days_to_full:.0f} days.",
                    cleanup if soon else "No action yet; plan capacity before it crosses "
                    f"{thresholds['disk_warning']:.0f}%.",
                    disk_percentage=disk, days_to_full=days_to_full)
        else:
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

        # Resource stalls (Linux PSI; absent on older kernels)
        mem_stall = s.get("psi_memory_full_avg60")
        if mem_stall is not None and _num(mem_stall) >= PRESSURE_WARNING:
            add("warning", "memory", name, f"{name} jobs are stalling on memory",
                f"All running tasks were stalled waiting for memory {_num(mem_stall):.0f}% of the last minute.",
                "Find the job driving memory pressure and move it to a host with more free RAM.",
                psi_memory_full=_num(mem_stall))
        io_stall = s.get("psi_io_full_avg60")
        if io_stall is not None and _num(io_stall) >= PRESSURE_WARNING:
            add("warning", "io", name, f"{name} jobs are stalling on storage",
                f"All running tasks were stalled waiting for I/O {_num(io_stall):.0f}% of the last minute.",
                "Check which users have the highest I/O rates and whether a disk is saturated.",
                psi_io_full=_num(io_stall))

        for dev in (disk_io_by_server or {}).get(name, []):
            util = dev.get("util_percent")
            if util is not None and _num(util) >= DISK_UTIL_WARNING:
                label = dev.get("name") or dev["device"]
                await_ms = dev.get("await_ms")
                add("warning", "io", name, f"{name} disk {label} is saturated",
                    f"Busy {_num(util):.0f}% of the last collection interval"
                    + (f", {_num(await_ms):.0f} ms per request." if await_ms is not None else "."),
                    "Spread heavy I/O jobs across servers or move scratch data to a faster disk.",
                    device=label, util_percent=_num(util))

        for nic in (network_by_server or {}).get(name, []):
            errors = _num(nic.get("rx_errors_delta")) + _num(nic.get("tx_errors_delta"))
            if errors >= NIC_ERRORS_WARNING:
                add("warning", "network", name, f"{name} {nic['interface']} has network errors",
                    f"{errors:.0f} receive/transmit errors since the previous collection.",
                    "Check the cable, switch port and NIC (ethtool -S) for faults.",
                    interface=nic["interface"], errors=errors)

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

    # Each network export once, listing the servers that mount it
    for entry in shared_mounts.values():
        servers_list = sorted(set(entry["servers"]))
        _mount_items(add, servers_list[0], entry, [], thresholds,
                     shared_on=servers_list)

    items.sort(key=lambda i: (SEVERITY_ORDER[i["severity"]], i["server"]))
    return items


def _mount_items(add, server: str, m: Dict[str, Any], users: List[Dict[str, Any]],
                 thresholds: Dict[str, float], shared_on: Optional[List[str]] = None) -> int:
    """Add fill-level and inode items for one mount; returns how many were added."""
    mount = m["mount_point"]
    where = f"Shared {mount}" if shared_on else f"{server} {mount}"
    on = f" (mounted on {', '.join(shared_on)})" if shared_on else ""
    added = 0

    use = m.get("use_percent")
    if use is not None and _num(use) >= thresholds["disk_warning"]:
        use = _num(use)
        free = m.get("avail_bytes")
        free_text = f"{_num(free) / 1024 ** 3:.0f} GiB free" if free is not None else "little space left"
        add("critical" if use >= thresholds["disk_critical"] else "warning", "disk", server,
            f"{where} is {use:.0f}% full",
            f"{free_text} on {m.get('source') or mount}{on}.",
            _mount_action(mount, users, bool(shared_on)),
            mount_point=mount, use_percent=use)
        added += 1

    inodes = m.get("inode_percent")
    if inodes is not None and _num(inodes) >= INODE_WARNING:
        add("critical" if _num(inodes) >= INODE_CRITICAL else "warning", "disk", server,
            f"{where} is running out of inodes",
            f"{_num(inodes):.0f}% of inodes used{on}; new files will fail even with free space.",
            "Find directories with huge numbers of small files (find <dir> -xdev -type f | "
            "cut -d/ -f2-3 | sort | uniq -c | sort -n) and archive them.",
            mount_point=mount, inode_percent=_num(inodes))
        added += 1
    return added


def _mount_action(mount: str, users: List[Dict[str, Any]], shared: bool) -> str:
    if shared:
        return "Ask the storage administrator to extend the export, or archive old project data."
    if mount == "/boot":
        return "Remove old kernels (dnf remove --oldinstallonly, or package-cleanup --oldkernels on RHEL 7)."
    if mount.startswith(("/home", "/eda_work")):
        names = _names(users, "disk", " GB")
        if names:
            return f"Ask the largest users to archive or clean up: {names}."
    if mount == "/":
        return "Check /var, /tmp and /opt for large files (du -xh / --max-depth=2 | sort -h)."
    return f"Find the largest directories (du -xh {mount} --max-depth=2 | sort -h) and archive or clean up."


def rank_placement(servers: List[Dict[str, Any]], now: datetime) -> List[Dict[str, Any]]:
    """
    Rank servers by spare capacity for a new job.

    Free cores use the 5-minute load average rather than cpu_usage_percent,
    which is a short instantaneous sample and too noisy for placement. The score
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
