"""Rates from cumulative kernel counters stored on consecutive collection runs.

Rates are averages over the interval between two runs (normally 15 minutes).
They are None when there is no usable previous sample: first run, a gap longer
than MAX_GAP_SECONDS, or any counter going backwards (reboot, wrap, driver reset).
"""
from typing import Dict, Optional

MAX_GAP_SECONDS = 2 * 3600
SECTOR_BYTES = 512  # /proc/diskstats always counts 512-byte sectors

DISK_COUNTERS = ["reads", "sectors_read", "ms_reading", "writes", "sectors_written",
                 "ms_writing", "ms_doing_io"]
NETWORK_COUNTERS = ["rx_bytes", "tx_bytes", "rx_packets", "tx_packets",
                    "rx_errors", "tx_errors", "rx_dropped", "tx_dropped"]

DISK_RATE_FIELDS = ["read_bps", "write_bps", "read_iops", "write_iops", "util_percent", "await_ms"]
NETWORK_RATE_FIELDS = ["rx_bps", "tx_bps", "rx_errors_delta", "tx_errors_delta",
                       "rx_dropped_delta", "tx_dropped_delta"]


def counter_deltas(prev: Optional[Dict], cur: Dict, elapsed: Optional[float], counters) -> Optional[Dict]:
    """Per-counter increase since `prev`, or None if the pair cannot be compared."""
    if prev is None or elapsed is None or not 0 < elapsed <= MAX_GAP_SECONDS:
        return None
    deltas = {}
    for c in counters:
        if prev.get(c) is None or cur.get(c) is None or cur[c] < prev[c]:
            return None
        deltas[c] = cur[c] - prev[c]
    return deltas


def disk_rates(prev: Optional[Dict], cur: Dict, elapsed: Optional[float]) -> Dict:
    d = counter_deltas(prev, cur, elapsed, DISK_COUNTERS)
    if d is None:
        return dict.fromkeys(DISK_RATE_FIELDS)
    ios = d["reads"] + d["writes"]
    return {
        "read_bps": round(d["sectors_read"] * SECTOR_BYTES / elapsed),
        "write_bps": round(d["sectors_written"] * SECTOR_BYTES / elapsed),
        "read_iops": round(d["reads"] / elapsed, 2),
        "write_iops": round(d["writes"] / elapsed, 2),
        # Share of wall time with at least one request in flight
        "util_percent": round(min(100.0, d["ms_doing_io"] / (elapsed * 1000) * 100), 1),
        # Average time per request, queueing included
        "await_ms": round((d["ms_reading"] + d["ms_writing"]) / ios, 2) if ios else None,
    }


def network_rates(prev: Optional[Dict], cur: Dict, elapsed: Optional[float]) -> Dict:
    d = counter_deltas(prev, cur, elapsed, NETWORK_COUNTERS)
    if d is None:
        return dict.fromkeys(NETWORK_RATE_FIELDS)
    return {
        "rx_bps": round(d["rx_bytes"] / elapsed),
        "tx_bps": round(d["tx_bytes"] / elapsed),
        "rx_errors_delta": d["rx_errors"],
        "tx_errors_delta": d["tx_errors"],
        "rx_dropped_delta": d["rx_dropped"],
        "tx_dropped_delta": d["tx_dropped"],
    }
