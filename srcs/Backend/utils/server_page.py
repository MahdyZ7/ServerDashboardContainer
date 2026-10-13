"""
Per-server status page
Single Responsibility: find a monitored server from a URL or hostname, and shape
one server's latest collection run into what its page shows (spare capacity,
required mounts, open SSH/VNC sessions, heaviest accounts).

Pure functions only (no database or Flask access) so the rules are easy to test.
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional

from utils.insights import STALE_AFTER_MINUTES, _num, minutes_since, parse_size_gb, rank_placement

# An SSH terminal with no input for this long is idle rather than in use
SESSION_IDLE_MINUTES = 30
TOP_USERS_LIMIT = 15


def configured_servers(environ: Mapping[str, str] = os.environ) -> List[Dict[str, Optional[str]]]:
    """Servers from SERVER{n}_NAME / _HOST / _IP, in configuration order."""
    servers = []
    for i in range(1, 10):
        name = environ.get(f"SERVER{i}_NAME")
        if name:
            servers.append({
                "name": name,
                "host": environ.get(f"SERVER{i}_HOST") or None,
                "ip": (environ.get(f"SERVER{i}_IP") or "").strip('"') or None,
            })
    return servers


def resolve_server(key: str, servers: List[Dict[str, Optional[str]]]) -> Optional[str]:
    """Server name for a display name, hostname, short hostname or IP (any case)."""
    key = (key or "").strip().lower().rstrip(".")
    if not key:
        return None
    for s in servers:
        host = (s.get("host") or "").lower()
        candidates = {s["name"].lower(), host, host.split(".")[0], (s.get("ip") or "").lower()}
        if key in candidates - {""}:
            return s["name"]
    return None


def _vnc_state(viewers: Optional[int]) -> str:
    if viewers is None:
        return "unknown"  # no TCP port (e.g. -inetd), so connections cannot be counted
    return "in_use" if viewers > 0 else "no_viewer"


def build_sessions(rows: List[Dict[str, Any]], full_names: Dict[str, str],
                   idle_minutes: int = SESSION_IDLE_MINUTES) -> Dict[str, Any]:
    """Split one run's session rows into VNC desktops and SSH logins.

    SSH connections without a terminal (VS Code, sftp, port forwards) have no
    idle time; they are folded into one row per account.
    """
    vnc, ssh, notty = [], [], {}
    for r in rows:
        name = r["username"]
        base = {"username": name, "full_name": full_names.get(name), "started_at": r.get("started_at")}
        if r["kind"] == "vnc":
            hosts = [h for h in (r.get("remote_host") or "").split(",") if h]
            vnc.append(dict(base, display=r.get("session"), viewers=r.get("viewers"),
                            remote_hosts=hosts, state=_vnc_state(r.get("viewers"))))
        elif r.get("session") == "notty":
            entry = notty.setdefault(name, dict(base, terminal=None, remote_host=None,
                                                idle_seconds=None, connections=0, state="connected"))
            entry["connections"] += 1
            if r.get("started_at") and (entry["started_at"] is None or r["started_at"] < entry["started_at"]):
                entry["started_at"] = r["started_at"]
        else:
            idle = r.get("idle_seconds")
            state = "unknown" if idle is None else "in_use" if idle < idle_minutes * 60 else "idle"
            ssh.append(dict(base, terminal=r.get("session"), remote_host=r.get("remote_host"),
                            idle_seconds=idle, connections=1, state=state))

    def display_number(s):
        d = (s["display"] or "").lstrip(":")
        return int(d) if d.isdigit() else 10 ** 6

    vnc.sort(key=lambda s: (s["username"].lower(), display_number(s)))
    ssh.sort(key=lambda s: (s["state"] != "in_use", s["idle_seconds"] or 0, s["username"].lower()))
    ssh += sorted(notty.values(), key=lambda s: s["username"].lower())

    per_user: Dict[str, int] = {}
    for s in vnc:
        per_user[s["username"]] = per_user.get(s["username"], 0) + 1
    return {
        "vnc": vnc,
        "ssh": ssh,
        "vnc_multiple": sorted(({"username": u, "count": n} for u, n in per_user.items() if n > 1),
                               key=lambda x: (-x["count"], x["username"].lower())),
        "vnc_users": len(per_user),
        "vnc_in_use": sum(s["state"] == "in_use" for s in vnc),
        "ssh_in_use": sum(s["state"] == "in_use" for s in ssh),
        "ssh_users": len({s["username"] for s in ssh}),
        "idle_minutes": idle_minutes,
    }


def build_capacity(m: Dict[str, Any]) -> Dict[str, Any]:
    """Spare CPU (logical CPUs minus 5-minute load, as for placement) and memory."""
    vcpus = int(_num(m.get("virtual_cpus")))
    load = _num(m.get("cpu_load_5min"))
    ram_total = parse_size_gb(m.get("ram_total"))
    if m.get("ram_available_mb") is not None:
        ram_free = _num(m["ram_available_mb"]) / 1024
    else:
        used = parse_size_gb(m.get("ram_used"))
        ram_free = ram_total - used if ram_total is not None and used is not None else None
    return {
        "virtual_cpus": vcpus,
        "load_5min": round(load, 2),
        "free_cores": round(max(0.0, vcpus - load), 1),
        "cpu_usage_percent": _num(m["cpu_usage_percent"]) if m.get("cpu_usage_percent") is not None else None,
        "ram_total_gb": round(ram_total, 1) if ram_total is not None else None,
        "ram_free_gb": round(max(0.0, ram_free), 1) if ram_free is not None else None,
        "ram_percentage": m.get("ram_percentage"),
        "swap_percentage": m.get("swap_percentage"),
    }


def server_status(m: Dict[str, Any], now: datetime, thresholds: Dict[str, float]) -> Dict[str, Any]:
    age = minutes_since(m.get("timestamp"), now)
    if age is None or age > STALE_AFTER_MINUTES:
        status = "offline"
    elif (_num(m.get("ram_percentage")) >= thresholds["memory_critical"]
          or _num(m.get("disk_percentage")) >= thresholds["disk_critical"]
          or _num(m.get("cpu_usage_percent")) >= thresholds["cpu_critical"]):
        status = "warning"
    else:
        status = "online"
    return {"status": status, "minutes_since_update": round(age) if age is not None else None}


def is_service_account(uid: Optional[int]) -> bool:
    """Daemon accounts on both RHEL 6 (people from UID 500) and RHEL 7+ (people from
    1000, daemons allocated downward from 999). root is kept: its load matters."""
    return uid is not None and (0 < uid < 500 or 900 <= uid <= 999 or uid == 65534)


def top_accounts(users: List[Dict[str, Any]], limit: int = TOP_USERS_LIMIT) -> List[Dict[str, Any]]:
    """People (and root) with running processes, heaviest CPU first, then memory."""
    running = [u for u in users if (u.get("process_count") or 0) > 0 and not is_service_account(u.get("uid"))]
    running.sort(key=lambda u: (-_num(u.get("cpu")), -_num(u.get("rss_kb"))))
    return running[:limit]


def build_fleet(servers: List[Dict[str, Any]], sessions_by_server: Dict[str, List[Dict[str, Any]]],
                mounts_by_server: Dict[str, List[Dict[str, Any]]], now: datetime,
                thresholds: Dict[str, float], configured: Optional[List[str]] = None,
                collection_errors: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """One overview row per server, most free capacity first (the placement ranking),
    with load, session counts and required-mount state from its latest run.
    Configured servers that have never reported are listed last. Rows that are not
    reporting carry `last_error`, the reason the latest collection attempt failed."""
    errors = collection_errors or {}
    by_name = {m["server_name"]: m for m in servers}
    rows = []
    for rank in rank_placement(servers, now):
        m = by_name[rank["server_name"]]
        sessions = sessions_by_server.get(rank["server_name"], [])
        mounts = mounts_by_server.get(rank["server_name"], [])
        s = build_sessions(sessions, {})
        rows.append(dict(
            rank,
            **server_status(m, now, thresholds),
            cpu_usage_percent=_num(m["cpu_usage_percent"]) if m.get("cpu_usage_percent") is not None else None,
            ram_percentage=m.get("ram_percentage"),
            # Collectors older than the session/mount checks write neither
            detail_collected=bool(sessions or mounts),
            vnc=len(s["vnc"]),
            vnc_in_use=s["vnc_in_use"],
            ssh=sum(1 for x in s["ssh"] if x["terminal"]),
            ssh_in_use=s["ssh_in_use"],
            mounts=[{"name": x["name"], "state": x["state"]} for x in mounts],
        ))
    for name in configured or []:
        if name not in by_name:
            rows.append({"server_name": name, "status": "offline", "minutes_since_update": None,
                         "available": False, "detail_collected": False, "mounts": []})
    for row in rows:
        if row["status"] == "offline":
            row["last_error"] = errors.get(row["server_name"])
    return rows
