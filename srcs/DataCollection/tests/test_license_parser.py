"""License report parsing against an anonymised capture of this installation's lmstat output."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from license_parser import match_server, parse_license_report, resolve_start  # noqa: E402

FIXTURE = (Path(__file__).parent / "fixtures" / "license_report.txt").read_text()


class LicenseReportTests(unittest.TestCase):
    def setUp(self):
        self.snaps = {s["vendor"]: s for s in parse_license_report(FIXTURE)}

    def test_vendor_sections_and_status(self):
        self.assertEqual(set(self.snaps), {"cadence", "synopsys"})
        self.assertEqual(self.snaps["synopsys"]["status"], "ok")
        self.assertEqual(self.snaps["synopsys"]["daemon_status"], "UP")
        cadence = self.snaps["cadence"]
        self.assertEqual(cadence["status"], "partial")  # some features report errors
        self.assertIn("2 features report errors", cadence["error"])

    def test_feature_totals_and_errors(self):
        features = {f["feature"]: f for f in self.snaps["synopsys"]["features"]}
        self.assertEqual((features["DC-Expert"]["issued"], features["DC-Expert"]["in_use"]), (15, 3))
        self.assertEqual(features["DC-Expert"]["expiry"], "06-nov-2026")
        self.assertEqual(features["SSS"]["in_use"], 0)
        cadence = {f["feature"]: f for f in self.snaps["cadence"]["features"]}
        self.assertIsNone(cadence["111"]["in_use"])  # error: unknown, not zero
        self.assertIn("unsupported by licensed server", cadence["111"]["error"])
        self.assertEqual(cadence["Virtuoso_Schematic_Editor_L"]["in_use"], 0)

    def test_checkout_rows(self):
        rows = self.snaps["synopsys"]["checkouts"]
        self.assertEqual(len(rows), 3)
        first = rows[0]
        self.assertEqual((first["feature"], first["username"], first["client_host"], first["display"]),
                         ("DC-Expert", "user_a", "ksrc6.kunet.ae", ":1"))
        self.assertEqual((first["server_host"], first["server_port"], first["handle"]), ("ku1bpaawv043", 27030, 701))
        self.assertEqual(first["start_raw"], "Tue 9/29 23:31")
        self.assertEqual(first["start_at"], datetime(2026, 9, 29, 23, 31))

    def test_unreachable_server_is_failed_not_zero(self):
        report = ("=== Synopsys license checkouts | 27030@host | 2026-10-01T16:20:10Z ===\n"
                  "lmgrd is not running: License server machine is down or not responding. (-96,7)\n")
        snap = parse_license_report(report)[0]
        self.assertEqual(snap["status"], "failed")
        self.assertEqual(snap["features"], [])
        self.assertIn("License server machine is down", snap["error"])

    def test_seat_count_and_unknown_start(self):
        report = ("=== Synopsys license checkouts | p@h | 2026-10-01T16:20:10Z ===\n"
                  "Users of VCS:  (Total of 10 licenses issued;  Total of 4 licenses in use)\n"
                  "    bob host1 /dev/pts/3 (v2025.06) (lic/27030 9), start Wed 9/30 8:05, 4 licenses\n")
        c = parse_license_report(report)[0]["checkouts"][0]
        self.assertEqual((c["username"], c["licenses"]), ("bob", 4))
        self.assertEqual(c["start_at"], datetime(2026, 9, 30, 8, 5))

    def test_start_resolution_uses_weekday_and_year_rollover(self):
        jan = datetime(2027, 1, 2, 8, 0, tzinfo=timezone.utc)
        self.assertEqual(resolve_start("Thu 12/31 23:00", jan, timezone.utc), datetime(2026, 12, 31, 23, 0))
        self.assertIsNone(resolve_start("Mon 12/31 23:00", jan, timezone.utc))  # weekday mismatch

    def test_match_server_by_short_hostname(self):
        servers = [{"name": "KSRC6", "host": None, "ip": "10.0.0.6"}]
        self.assertEqual(match_server("ksrc6.kunet.ae", servers), "KSRC6")
        self.assertIsNone(match_server("laptop7", servers))


if __name__ == "__main__":
    unittest.main()
