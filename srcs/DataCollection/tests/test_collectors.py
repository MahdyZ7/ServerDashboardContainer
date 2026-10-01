"""Collector scripts and parsers, exercised locally without SSH or a database."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from parsers import (  # noqa: E402
    DISK_NOT_COLLECTED, ParseError, TOP_USERS_COLUMNS, parse_monitoring_data, parse_top_users,
)
from rates import disk_rates, network_rates  # noqa: E402


def run_script(name, *args, timeout=60):
    """Run a collector the way BashGetInfo.sh does: script on stdin to `bash -s`."""
    with open(HERE / name) as script:
        result = subprocess.run(["bash", "-s", "--", *args], stdin=script,
                                capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise AssertionError(f"{name} exited {result.returncode}: {result.stderr}")
    return result.stdout


class HostMetricsTests(unittest.TestCase):
    def test_live_output_parses_with_types(self):
        metrics = parse_monitoring_data(run_script("mini_monitering.sh", "--kv"))
        self.assertGreater(metrics["virtual_cpus"], 0)
        self.assertIsInstance(metrics["cpu_load_1min"], float)
        for key in ("cpu_usage_percent", "cpu_iowait_percent", "cpu_steal_percent"):
            self.assertIsNotNone(metrics[key], key)
            self.assertTrue(0 <= metrics[key] <= 100, (key, metrics[key]))
        self.assertTrue(0 <= metrics["ram_percentage"] <= 100)
        self.assertTrue(metrics["ram_total"].endswith("G"))

    def test_empty_values_are_unknown_not_zero(self):
        metrics = parse_monitoring_data("format_version=2\ncpu_usage_percent=\nnet_rx_bytes=\n")
        self.assertIsNone(metrics["cpu_usage_percent"])
        self.assertIsNone(metrics["net_rx_bytes"])
        self.assertIsNone(metrics["disk_percentage"])  # key absent entirely

    def test_values_may_contain_equals_and_commas(self):
        metrics = parse_monitoring_data("format_version=2\narchitecture=Linux #1 SMP, a=b\n")
        self.assertEqual(metrics["architecture"], "Linux #1 SMP, a=b")

    def test_live_output_has_mounts_devices_and_nics(self):
        metrics = parse_monitoring_data(run_script("mini_monitering.sh", "--kv"))
        mounts = {fs["mount_point"]: fs for fs in metrics["filesystems"]}
        self.assertIn("/", mounts)
        self.assertTrue(0 <= mounts["/"]["use_percent"] <= 100)
        self.assertFalse([m for m in mounts.values() if m["fstype"] in ("tmpfs", "devtmpfs")])
        self.assertTrue(metrics["block_devices"])
        self.assertFalse([d for d in metrics["block_devices"] if d["device"].startswith("loop")])
        self.assertFalse([n for n in metrics["network"] if n["interface"] == "lo"])
        self.assertIsNotNone(metrics["procs_running"])
        self.assertIsNotNone(metrics["procs_zombie"])

    def test_services_report_state_and_missing(self):
        metrics = parse_monitoring_data(run_script("mini_monitering.sh", "--kv", "--services", "sshd no-such-svc"))
        states = {s["service"]: s for s in metrics["services"]}
        self.assertEqual(states["no-such-svc"]["state"], "missing")
        self.assertEqual(states["no-such-svc"]["monitored"], 1)
        self.assertIn(states["sshd"]["state"], ("active", "inactive", "failed"))
        self.assertTrue(all(s["monitored"] == 0 for name, s in states.items()
                            if name not in ("sshd", "no-such-svc")))

    def test_records_parse_mount_with_spaces_and_unknown_inodes(self):
        metrics = parse_monitoring_data(
            "format_version=2\n"
            "fs=/mnt/my data\tvfat\t/dev/sdz1\t1000\t900\t50\t0\t0\n"
            "net=eth0\t1\t2\t3\t4\t\t\t0\t0\n"
        )
        fs = metrics["filesystems"][0]
        self.assertEqual(fs["mount_point"], "/mnt/my data")
        self.assertEqual(fs["use_percent"], 94.7)  # used / (used + avail), like df
        self.assertIsNone(fs["inode_percent"])
        self.assertIsNone(metrics["network"][0]["rx_errors"])
        with self.assertRaises(ParseError):
            parse_monitoring_data("format_version=2\nblk=sda\tsda\t1\n")

    def test_old_or_unknown_format_is_rejected(self):
        with self.assertRaises(ParseError):
            parse_monitoring_data("Linux,RHEL 9,2,8,1G/2G,50,1T/2T,50%,0.1,0.2,0.3")
        with self.assertRaises(ParseError):
            parse_monitoring_data("format_version=2\nvirtual_cpus=eight\n")


def tsv(**overrides):
    row = dict(uid="1000", user="alice", cpu="412.50", mem="3.20", rss_kb="2048", disk="",
               process_count="7", top_process="spectre x", last_login="2026-09-30 08:15:00",
               full_name="Alice Example", io_read_bytes="", io_write_bytes="",
               io_read_bps="", io_write_bps="")
    row.update(overrides)
    return "\t".join(row[c] for c in TOP_USERS_COLUMNS)


class TopUsersTests(unittest.TestCase):
    def test_live_output_parses(self):
        users = parse_top_users(run_script("TopUsers.sh", "--no-headers", "--sample-seconds", "1"))
        rows = users["top_users"]
        self.assertTrue(rows)
        me = [r for r in rows if r["uid"] == os.getuid()]
        self.assertEqual(len(me), 1, "the caller's own UID owns processes and must be listed")
        self.assertGreater(me[0]["process_count"], 0)
        # Own processes are readable, so I/O is measured rather than unknown
        self.assertIsNotNone(me[0]["io_read_bytes"])
        self.assertIs(me[0]["disk"], DISK_NOT_COLLECTED)

    def test_cpu_above_one_core_and_unknown_io(self):
        row = parse_top_users("#format=2 sample_seconds=2\n" + tsv())["top_users"][0]
        self.assertEqual(row["cpu"], 412.5)
        self.assertEqual(row["top_process"], "spectre x")
        self.assertIsNone(row["io_read_bytes"])
        self.assertEqual(row["last_login"].isoformat(), "2026-09-30T08:15:00")

    def test_disk_states(self):
        data = "#format=2\n" + "\n".join([
            tsv(user="a", disk=""), tsv(user="b", disk="none"),
            tsv(user="c", disk="0.00"), tsv(user="d", disk="1234.56"),
        ])
        disks = [r["disk"] for r in parse_top_users(data)["top_users"]]
        self.assertIs(disks[0], DISK_NOT_COLLECTED)
        self.assertEqual(disks[1:], [None, 0.0, 1234.56])

    def test_wrong_field_count_and_missing_header_are_errors(self):
        with self.assertRaises(ParseError):
            parse_top_users("#format=2\n" + tsv() + "\textra")
        with self.assertRaises(ParseError):
            parse_top_users(tsv())


class RateTests(unittest.TestCase):
    PREV = dict(reads=100, sectors_read=2000, ms_reading=50, writes=10, sectors_written=400,
                ms_writing=30, ms_doing_io=100)

    def test_disk_rates_over_interval(self):
        cur = dict(reads=200, sectors_read=4048, ms_reading=250, writes=110, sectors_written=2448,
                   ms_writing=230, ms_doing_io=500)
        r = disk_rates(self.PREV, cur, 10.0)
        self.assertEqual(r["read_bps"], round(2048 * 512 / 10))
        self.assertEqual(r["read_iops"], 10.0)
        self.assertEqual(r["util_percent"], 4.0)  # 400 ms busy in 10 s
        self.assertEqual(r["await_ms"], 2.0)      # 400 ms over 200 requests

    def test_reset_first_run_and_long_gap_are_unknown(self):
        cur = dict(self.PREV, reads=5)            # counter went backwards: reboot
        self.assertIsNone(disk_rates(self.PREV, cur, 10.0)["read_bps"])
        self.assertIsNone(disk_rates(None, self.PREV, None)["util_percent"])
        self.assertIsNone(disk_rates(self.PREV, self.PREV, 3 * 3600)["read_bps"])

    def test_network_errors_are_interval_counts(self):
        prev = dict(rx_bytes=0, tx_bytes=0, rx_packets=0, tx_packets=0, rx_errors=5,
                    tx_errors=0, rx_dropped=7, tx_dropped=0)
        cur = dict(prev, rx_bytes=9000, rx_errors=8, rx_dropped=7)
        r = network_rates(prev, cur, 900.0)
        self.assertEqual((r["rx_bps"], r["rx_errors_delta"], r["rx_dropped_delta"]), (10, 3, 0))


class SshWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        bin_dir = Path(self.temp.name)
        self.log = bin_dir / "argv"
        # Fake ssh/sshpass record their argv and whether SSHPASS reached them
        for name in ("ssh", "sshpass"):
            fake = bin_dir / name
            fake.write_text(
                "#!/bin/bash\n"
                f'printf "%s\\n" "{name}" "$@" "SSHPASS_SET=${{SSHPASS:+yes}}" >> "{self.log}"\n'
                'if [ "$1" = "-e" ]; then shift; exec ssh "$@"; fi\n'
                "cat > /dev/null\n"
            )
            fake.chmod(0o755)
        self.env = {k: v for k, v in os.environ.items() if k not in ("SSHPASS", "SSH_KEY_FILE")}
        self.env["PATH"] = f"{bin_dir}:{self.env['PATH']}"

    def run_wrapper(self, *args, **env):
        return subprocess.run(
            ["bash", str(HERE / "BashGetInfo.sh"), "10.0.0.1", "svc@example",
             str(HERE / "mini_monitering.sh"), *args],
            env={**self.env, **env}, capture_output=True, text=True, timeout=10,
        )

    def test_password_is_never_on_the_command_line(self):
        result = self.run_wrapper("--kv", SSHPASS="s3cret p@ss")
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = self.log.read_text()
        self.assertNotIn("s3cret", argv)
        self.assertIn("sshpass\n-e\n", argv)
        self.assertIn("SSHPASS_SET=yes", argv)
        self.assertIn("ConnectTimeout=10", argv)

    def test_remote_arguments_are_quoted(self):
        self.run_wrapper("--kv", "a b; rm -rf /", SSHPASS="x")
        self.assertIn("bash -s -- --kv a\\ b\\;\\ rm\\ -rf\\ /\n", self.log.read_text())

    def test_key_file_uses_batch_mode_without_sshpass(self):
        result = self.run_wrapper("--kv", SSH_KEY_FILE="/keys/k", SSHPASS="ignored")
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = self.log.read_text()
        self.assertTrue(argv.startswith("ssh\n-i\n/keys/k\n-o\nBatchMode=yes\n"), argv)
        self.assertNotIn("sshpass", argv)

    def test_missing_credentials_fail(self):
        result = self.run_wrapper("--kv")
        self.assertEqual(result.returncode, 1)
        self.assertIn("No credentials", result.stderr)


if __name__ == "__main__":
    unittest.main()
