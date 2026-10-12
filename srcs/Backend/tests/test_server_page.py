"""Per-server page rules: server lookup, session grouping, capacity and status."""
from datetime import datetime, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.server_page import (  # noqa: E402
    build_capacity, build_sessions, configured_servers, resolve_server, server_status, top_accounts,
)

NOW = datetime(2026, 10, 12, 12, 0)
THRESHOLDS = {"memory_critical": 95, "disk_critical": 95, "cpu_critical": 80}
ENV = {
    "SERVER1_NAME": "KSRC1", "SERVER1_HOST": "ksrc1.kunet.ae", "SERVER1_IP": '"10.10.19.73"',
    "SERVER3_NAME": "ku1rpaaxv007", "SERVER3_HOST": "ku1rpaaxv007.kunet.ae",
}


class ResolveServerTests(unittest.TestCase):
    def setUp(self):
        self.servers = configured_servers(ENV)

    def test_configured_in_order_with_quotes_stripped(self):
        self.assertEqual([s["name"] for s in self.servers], ["KSRC1", "ku1rpaaxv007"])
        self.assertEqual(self.servers[0]["ip"], "10.10.19.73")

    def test_name_host_short_host_and_ip_resolve(self):
        for key in ("KSRC1", "ksrc1", "ksrc1.kunet.ae", "KSRC1.KUNET.AE.", "10.10.19.73"):
            self.assertEqual(resolve_server(key, self.servers), "KSRC1", key)
        self.assertEqual(resolve_server("ku1rpaaxv007.kunet.ae", self.servers), "ku1rpaaxv007")

    def test_unknown_or_empty_is_none(self):
        for key in ("ksrc9", "", "localhost", "kunet"):
            self.assertIsNone(resolve_server(key, self.servers), key)
        self.assertIsNone(resolve_server("", [{"name": "x", "host": None, "ip": None}]))


def vnc(user, display, viewers, hosts=""):
    return {"kind": "vnc", "username": user, "session": display, "remote_host": hosts,
            "started_at": NOW, "idle_seconds": None, "viewers": viewers}


def ssh(user, tty, idle, started=NOW):
    return {"kind": "ssh", "username": user, "session": tty, "remote_host": "10.0.0.9",
            "started_at": started, "idle_seconds": idle, "viewers": None}


class SessionTests(unittest.TestCase):
    def test_vnc_states_and_multiple_desktops(self):
        s = build_sessions([vnc("eman", ":10", 0), vnc("eman", ":3", 1, "10.0.0.1,127.0.0.1"),
                            vnc("bob", ":2", None)], {"eman": "Eman Example"})
        self.assertEqual([(v["username"], v["display"]) for v in s["vnc"]],
                         [("bob", ":2"), ("eman", ":3"), ("eman", ":10")])  # display numeric order
        self.assertEqual([v["state"] for v in s["vnc"]], ["unknown", "in_use", "no_viewer"])
        self.assertEqual(s["vnc"][1]["remote_hosts"], ["10.0.0.1", "127.0.0.1"])
        self.assertEqual(s["vnc"][1]["full_name"], "Eman Example")
        self.assertEqual(s["vnc_multiple"], [{"username": "eman", "count": 2}])
        self.assertEqual((s["vnc_users"], s["vnc_in_use"]), (2, 1))

    def test_ssh_idle_threshold_and_notty_folded_per_user(self):
        s = build_sessions([ssh("amy", "pts/1", 29 * 60), ssh("amy", "pts/2", 31 * 60),
                            ssh("cy", "notty", None, NOW), ssh("cy", "notty", None, NOW - timedelta(hours=1)),
                            ssh("dee", "pts/3", None)], {}, idle_minutes=30)
        rows = [(r["username"], r["terminal"], r["state"]) for r in s["ssh"]]
        self.assertEqual(rows, [("amy", "pts/1", "in_use"), ("dee", "pts/3", "unknown"),
                                ("amy", "pts/2", "idle"), ("cy", None, "connected")])
        self.assertEqual(s["ssh"][-1]["connections"], 2)
        self.assertEqual(s["ssh"][-1]["started_at"], NOW - timedelta(hours=1))  # earliest
        self.assertEqual((s["ssh_in_use"], s["ssh_users"]), (1, 3))

    def test_no_sessions(self):
        s = build_sessions([], {})
        self.assertEqual((s["vnc"], s["ssh"], s["vnc_multiple"]), ([], [], []))


class CapacityAndStatusTests(unittest.TestCase):
    def test_free_cores_and_available_memory(self):
        c = build_capacity({"virtual_cpus": 32, "cpu_load_5min": 13.7, "ram_total": "251.4G",
                            "ram_used": "200G", "ram_available_mb": 122880, "cpu_usage_percent": 40})
        self.assertEqual((c["free_cores"], c["ram_free_gb"], c["ram_total_gb"]), (18.3, 120.0, 251.4))

    def test_overloaded_and_fallback_memory(self):
        c = build_capacity({"virtual_cpus": 8, "cpu_load_5min": 20, "ram_total": "64G", "ram_used": "60G"})
        self.assertEqual((c["free_cores"], c["ram_free_gb"], c["cpu_usage_percent"]), (0.0, 4.0, None))

    def test_status(self):
        fresh = {"timestamp": NOW - timedelta(minutes=10), "ram_percentage": 50}
        self.assertEqual(server_status(fresh, NOW, THRESHOLDS)["status"], "online")
        self.assertEqual(server_status(dict(fresh, ram_percentage=96), NOW, THRESHOLDS)["status"], "warning")
        stale = server_status(dict(fresh, timestamp=NOW - timedelta(minutes=45)), NOW, THRESHOLDS)
        self.assertEqual((stale["status"], stale["minutes_since_update"]), ("offline", 45))

    def test_top_accounts_skip_idle_accounts(self):
        users = [{"username": "a", "cpu": 0, "rss_kb": 10, "process_count": 0},
                 {"username": "b", "cpu": 5, "rss_kb": 1, "process_count": 2},
                 {"username": "c", "cpu": 5, "rss_kb": 9, "process_count": 1}]
        self.assertEqual([u["username"] for u in top_accounts(users)], ["c", "b"])

    def test_top_accounts_skip_daemons_keep_root_and_people(self):
        users = [{"username": n, "uid": uid, "cpu": 1, "rss_kb": 1, "process_count": 1}
                 for n, uid in [("root", 0), ("rpc", 32), ("rhel6user", 500), ("person", 737),
                                ("polkitd", 998), ("rhel9user", 1000), ("nobody", 65534)]]
        self.assertEqual({u["username"] for u in top_accounts(users)},
                         {"root", "rhel6user", "person", "rhel9user"})


if __name__ == "__main__":
    unittest.main()
