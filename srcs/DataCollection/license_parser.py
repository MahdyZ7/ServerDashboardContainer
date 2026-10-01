"""Parse LicenseUsage.sh reports (FlexNet `lmutil lmstat` output per vendor).

The report is one section per vendor:

    === Synopsys license checkouts | 27030@host | 2026-10-01T16:20:10Z ===
    <raw lmstat output>

Each section yields a snapshot with a query status:
  ok       feature totals parsed, no errors reported
  partial  totals parsed, but some features or the daemon reported errors
  failed   no feature totals at all (server down, unreachable, unknown format)
A failed query must never be read as zero usage.

lmstat checkout start times carry no year ("start Tue 9/29 23:31"). The raw
text is kept; `start_at` is resolved to the most recent date on or before the
query time whose weekday matches, and left None when it does not.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

SECTION_RE = re.compile(r"^=== (?P<vendor>\S+) license checkouts \| (?P<endpoint>.*) \| (?P<queried>\S+) ===$")
USERS_OF_RE = re.compile(r"^Users of (?P<feature>[^:]+):\s+\((?P<body>.*)\)\s*$")
TOTALS_RE = re.compile(
    r"Total of (?P<issued>\d+) licenses? issued;\s+Total of (?P<in_use>\d+) licenses? in use"
)
UNCOUNTED_RE = re.compile(r"Uncounted, node-locked")
DAEMON_RE = re.compile(r"^\s*(?P<daemon>\S+): (?P<state>UP|DOWN|The desired vendor daemon is down)\b(?P<rest>.*)$")
SERVER_RE = re.compile(r"^\S+: license server (?P<state>UP|DOWN)")
FEATURE_DETAIL_RE = re.compile(r'^\s*"(?P<feature>[^"]+)" (?P<version>v\S+), vendor: (?P<vendor>[^,]+), expiry: (?P<expiry>\S+)')
# user host display [extra...] (version) (server/port handle), start Day M/D H:MM[, N licenses]
CHECKOUT_RE = re.compile(
    r"^\s+(?P<pre>\S.*?) \((?P<version>v[^)]*)\) \((?P<server>[^/\s]+)/(?P<port>\d+) (?P<handle>\d+)\)"
    r"(?:, start (?P<start>\w{3} \d{1,2}/\d{1,2} \d{1,2}:\d{2}))?(?P<tail>.*)$"
)
LICENSE_COUNT_RE = re.compile(r"(\d+) licenses?")
ERROR_LINE_RE = re.compile(
    r"Error getting status|Cannot connect to license server|License server machine is down|"
    r"Vendor daemon is down|FLEX(?:net|lm) Licensing error",
    re.IGNORECASE,
)


def parse_license_report(text: str) -> List[Dict]:
    """Split a LicenseUsage.sh report into per-vendor snapshots."""
    sections: List[Dict] = []
    current: Optional[Dict] = None
    for line in text.splitlines():
        match = SECTION_RE.match(line)
        if match:
            current = {"vendor": match["vendor"].lower(), "endpoint": match["endpoint"],
                       "queried_at": _parse_iso_utc(match["queried"]), "lines": []}
            sections.append(current)
        elif current is not None:
            current["lines"].append(line)
    return [_parse_section(s) for s in sections]


def _parse_section(section: Dict) -> Dict:
    features: Dict[str, Dict] = {}
    checkouts: List[Dict] = []
    errors: List[str] = []
    daemon_status = None
    current = None  # feature whose checkout rows follow

    for line in section["lines"]:
        users = USERS_OF_RE.match(line)
        if users:
            name = users["feature"].strip()
            body = users["body"]
            totals = TOTALS_RE.search(body)
            feature = features.setdefault(name, {"feature": name, "issued": None, "in_use": None,
                                                 "error": None, "version": None, "expiry": None})
            if totals:
                feature["issued"] = int(totals["issued"])
                feature["in_use"] = int(totals["in_use"])
            elif UNCOUNTED_RE.search(body):
                feature["error"] = None  # node-locked: no totals, not an error
            else:
                feature["error"] = body.strip()
            current = name
            continue

        detail = FEATURE_DETAIL_RE.match(line)
        if detail and detail["feature"] in features:
            features[detail["feature"]]["version"] = detail["version"]
            features[detail["feature"]]["expiry"] = detail["expiry"]
            continue

        checkout = CHECKOUT_RE.match(line)
        if checkout and current is not None:
            checkouts.append(_parse_checkout(current, checkout, line, section["queried_at"]))
            continue

        daemon = DAEMON_RE.match(line)
        if daemon and daemon["daemon"] not in ("License", "lmutil"):
            daemon_status = daemon["state"]
            if daemon["state"] != "UP":
                errors.append(line.strip())
            continue
        server = SERVER_RE.match(line)
        if server and server["state"] != "UP":
            errors.append(line.strip())
            continue
        if ERROR_LINE_RE.search(line):
            errors.append(line.strip())

    counted = [f for f in features.values() if f["in_use"] is not None]
    feature_errors = [f for f in features.values() if f["error"]]
    if not counted:
        status = "failed"
    elif feature_errors or errors:
        status = "partial"
    else:
        status = "ok"

    summary = errors[:5]
    if feature_errors:
        kinds = sorted({f["error"] for f in feature_errors})
        summary.append(f"{len(feature_errors)} features report errors, e.g. {kinds[0]}")
    if not features and not errors:
        summary.append("no feature usage found in the lmstat output")

    return {
        "vendor": section["vendor"],
        "endpoint": section["endpoint"],
        "queried_at": section["queried_at"],
        "status": status,
        "daemon_status": daemon_status,
        "error": "; ".join(summary) or None,
        "features": list(features.values()),
        "checkouts": checkouts,
    }


def _parse_checkout(feature: str, m: re.Match, line: str, queried_at: Optional[datetime]) -> Dict:
    pre = m["pre"].split()
    count = LICENSE_COUNT_RE.search(m["tail"] or "")
    return {
        "feature": feature,
        "username": pre[0],
        "client_host": pre[1] if len(pre) > 1 else None,
        "display": pre[2] if len(pre) > 2 else None,
        "version": m["version"],
        "server_host": m["server"],
        "server_port": int(m["port"]),
        "handle": int(m["handle"]),
        "start_raw": m["start"],
        "start_at": resolve_start(m["start"], queried_at),
        "licenses": int(count[1]) if count else 1,
        "raw": line.strip(),
    }


def resolve_start(raw: Optional[str], queried_at: Optional[datetime], tz=None) -> Optional[datetime]:
    """'Tue 9/29 23:31' -> latest such date not after the query, checked by weekday.

    The time is in the license server's local zone; `tz` converts the query time
    into that zone (default: the collector's local zone). Returns a naive local
    datetime, matching the database's TIMESTAMP columns.
    """
    if not raw or queried_at is None:
        return None
    try:
        weekday, date, clock = raw.split()
        month, day = (int(x) for x in date.split("/"))
        hour, minute = (int(x) for x in clock.split(":"))
    except ValueError:
        return None
    reference = queried_at.astimezone(tz).replace(tzinfo=None) + timedelta(minutes=1)
    for year in (reference.year, reference.year - 1):
        try:
            candidate = datetime(year, month, day, hour, minute)
        except ValueError:
            continue
        if candidate <= reference and candidate.strftime("%a") == weekday:
            return candidate
    return None


def match_server(client_host: Optional[str], servers: List[Dict]) -> Optional[str]:
    """Map a checkout's client host to a monitored server name (first DNS label, case-insensitive)."""
    if not client_host:
        return None
    short = client_host.split(".")[0].lower()
    for s in servers:
        names = {s.get("name"), s.get("host"), s.get("ip")}
        if short in {n.split(".")[0].lower() for n in names if n} or client_host in names:
            return s["name"]
    return None


def _parse_iso_utc(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
