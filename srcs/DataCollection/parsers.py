"""Parsers for the collector scripts' machine output (format version 2).

Empty fields mean "not measured" and become None, never 0, so the database and
dashboard can tell a missing reading from a genuine zero.
"""
from datetime import datetime
from typing import Dict, List, Optional

FORMAT_VERSION = "2"

# Sentinel for a disk scan that did not run or did not finish: keep the stored value
DISK_NOT_COLLECTED = object()

TOP_USERS_COLUMNS = [
    "uid", "user", "cpu", "mem", "rss_kb", "disk", "process_count", "top_process",
    "last_login", "full_name", "io_read_bytes", "io_write_bytes", "io_read_bps", "io_write_bps",
]


class ParseError(ValueError):
    pass


def _int(value: str) -> Optional[int]:
    return int(value) if value != "" else None


def _float(value: str) -> Optional[float]:
    return float(value) if value != "" else None


def _str(value: str) -> Optional[str]:
    return value if value != "" else None


SERVER_METRIC_TYPES = {
    "architecture": _str,
    "operating_system": _str,
    "physical_cpus": _int,
    "virtual_cpus": _int,
    "ram_used": _str,
    "ram_total": _str,
    "ram_percentage": _int,
    "ram_available_mb": _int,
    "swap_used_mb": _int,
    "swap_total_mb": _int,
    "swap_percentage": _int,
    "disk_used": _str,
    "disk_total": _str,
    "disk_percentage": _int,
    "cpu_load_1min": _float,
    "cpu_load_5min": _float,
    "cpu_load_15min": _float,
    "cpu_usage_percent": _float,
    "cpu_iowait_percent": _float,
    "cpu_steal_percent": _float,
    "last_boot": _str,
    "tcp_connections": _int,
    "logged_users": _int,
    "active_vnc_users": _int,
    "active_ssh_users": _int,
    "net_interface": _str,
    "net_rx_bytes": _int,
    "net_tx_bytes": _int,
}


def parse_monitoring_data(data: str) -> Dict:
    """Parse `mini_monitering.sh --kv` output into a dict keyed by server_metrics column."""
    raw = {}
    for line in data.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            raw[key.strip()] = value.strip()

    if raw.get("format_version") != FORMAT_VERSION:
        raise ParseError(
            f"expected format_version={FORMAT_VERSION}, got {raw.get('format_version')!r}"
        )

    metrics = {}
    for key, convert in SERVER_METRIC_TYPES.items():
        try:
            metrics[key] = convert(raw.get(key, ""))
        except ValueError as e:
            raise ParseError(f"bad value for {key}: {raw.get(key)!r}") from e
    return metrics


def parse_top_users(data: str) -> Dict:
    """Parse `TopUsers.sh --no-headers` output (a #format line, then TSV rows)."""
    lines = data.splitlines()
    if not lines or not lines[0].startswith(f"#format={FORMAT_VERSION}"):
        raise ParseError(f"missing #format={FORMAT_VERSION} header")

    top_users: List[Dict] = []
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != len(TOP_USERS_COLUMNS):
            raise ParseError(
                f"line {number}: expected {len(TOP_USERS_COLUMNS)} fields, got {len(fields)}"
            )
        row = dict(zip(TOP_USERS_COLUMNS, fields))
        try:
            top_users.append({
                "uid": int(row["uid"]),
                "user": row["user"],
                "cpu": float(row["cpu"]),
                "mem": float(row["mem"]),
                "rss_kb": int(row["rss_kb"]),
                "disk": _parse_disk(row["disk"]),
                "process_count": int(row["process_count"]),
                "top_process": _str(row["top_process"]),
                "last_login": (datetime.strptime(row["last_login"], "%Y-%m-%d %H:%M:%S")
                               if row["last_login"] else None),
                "full_name": _str(row["full_name"]),
                "io_read_bytes": _int(row["io_read_bytes"]),
                "io_write_bytes": _int(row["io_write_bytes"]),
                "io_read_bps": _int(row["io_read_bps"]),
                "io_write_bps": _int(row["io_write_bps"]),
            })
        except ValueError as e:
            raise ParseError(f"line {number}: {e}") from e
    return {"top_users": top_users}


def _parse_disk(value: str):
    if value == "":
        return DISK_NOT_COLLECTED
    if value == "none":
        return None  # scanned: the account has no directory to measure
    return float(value)
