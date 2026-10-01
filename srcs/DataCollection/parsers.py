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
    "procs_running": _int,
    "procs_blocked": _int,
    "psi_cpu_some_avg60": _float,
    "psi_memory_some_avg60": _float,
    "psi_memory_full_avg60": _float,
    "psi_io_some_avg60": _float,
    "psi_io_full_avg60": _float,
}

# Repeated records in the key=value output: key -> (result list name, TSV columns).
# The first column is text, the rest are integer counters (empty = unknown).
RECORD_TYPES = {
    "fs": ("filesystems", ["mount_point", "fstype", "source", "size_bytes", "used_bytes",
                           "avail_bytes", "inodes_total", "inodes_used"]),
    "blk": ("block_devices", ["device", "name", "reads", "sectors_read", "ms_reading", "writes",
                              "sectors_written", "ms_writing", "ms_doing_io"]),
    "net": ("network", ["interface", "rx_bytes", "tx_bytes", "rx_packets", "tx_packets",
                        "rx_errors", "tx_errors", "rx_dropped", "tx_dropped"]),
}
# Columns besides the first that hold text rather than numbers
TEXT_COLUMNS = {"fstype", "source", "name"}


def parse_monitoring_data(data: str) -> Dict:
    """Parse `mini_monitering.sh --kv` output into a dict keyed by server_metrics column."""
    raw = {}
    records = {name: [] for name, _ in RECORD_TYPES.values()}
    for line in data.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in RECORD_TYPES:
            name, columns = RECORD_TYPES[key]
            records[name].append(_parse_record(key, value, columns))
        else:
            raw[key] = value.strip()

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
    metrics.update(records)
    return metrics


def _parse_record(key: str, value: str, columns: List[str]) -> Dict:
    fields = value.split("\t")
    if len(fields) != len(columns):
        raise ParseError(f"{key}= record: expected {len(columns)} fields, got {len(fields)}")
    record = {}
    for column, field in zip(columns, fields):
        try:
            record[column] = field if column == columns[0] or column in TEXT_COLUMNS else _int(field)
        except ValueError as e:
            raise ParseError(f"{key}= record: bad {column} {field!r}") from e
    if key == "fs":
        used, avail, inodes, iused = (record[c] for c in ("used_bytes", "avail_bytes", "inodes_total", "inodes_used"))
        # Same basis as df's Use%: space reserved for root counts as unavailable
        record["use_percent"] = round(used / (used + avail) * 100, 1) if used is not None and avail and used + avail else None
        record["inode_percent"] = round(iused / inodes * 100, 1) if inodes and iused is not None else None
    return record


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
