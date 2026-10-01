"""Exercise the CLI without contacting a license server or installing lmutil."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "LicenseUsage.sh"
REPORT = """snpslmd: UP
Users of idle_feature: (Total of 15 licenses issued; Total of 0 licenses in use)
Users of DC-Expert: (Total of 15 licenses issued; Total of 2 licenses in use)
    alice compute01 :1 (v2025.06) (license/27030 123), start Thu 9/24 10:00
    bob compute02 :2 (v2025.06) (license/27030 124), start Thu 9/24 11:00
"""


class LicenseUsageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.binary = Path(self.temp.name) / "vendor tools" / "lmutil"
        self.binary.parent.mkdir()
        self.binary.write_text(
            '#!/bin/bash\n'
            'printf "%s\\n" "$@" >> "$ARGUMENT_LOG"\n'
            'if [[ $* == *cdslmd* && ${FAIL_CADENCE:-0} == 1 ]]; then\n'
            '  echo "Error getting status: unavailable"; exit 1\n'
            'fi\n'
            'if [[ ${STALL:-0} == 1 ]]; then sleep 10; fi\n'
            'printf "%s\\n" "$REPORT"\n'
            'exit "${LMUTIL_STATUS:-0}"\n'
        )
        self.binary.chmod(0o755)
        self.log = Path(self.temp.name) / "arguments"
        self.env = dict(os.environ)
        for key in ("CDS_LIC_FILE", "SNPSLMD_LICENSE_FILE", "CADENCE_LMUTIL",
                    "SYNOPSYS_LMUTIL", "LMUTIL"):
            self.env.pop(key, None)
        self.env.update(LMUTIL=str(self.binary), ARGUMENT_LOG=str(self.log), REPORT=REPORT)

    def run_script(self, *args, **env):
        return subprocess.run(
            ["bash", str(SCRIPT), *args], env={**self.env, **env},
            capture_output=True, text=True, timeout=8,
        )

    def test_missing_configuration_is_not_zero_usage(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 2)
        self.assertIn("No servers configured", result.stderr)
        self.assertFalse(self.log.exists())

    def test_both_vendors_and_server_list_quoting(self):
        server = "5280@host1:5280@host2"
        result = self.run_script(CDS_LIC_FILE=server, SNPSLMD_LICENSE_FILE="27030@host")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("alice compute01", result.stdout)
        self.assertIn("bob compute02", result.stdout)
        self.assertEqual(self.log.read_text().splitlines(), [
            "lmstat", "-c", server, "-S", "cdslmd", "-t", "30",
            "lmstat", "-c", "27030@host", "-S", "snpslmd", "-t", "30",
        ])

    def test_explicit_options_override_environment(self):
        result = self.run_script(
            "--vendor", "synopsys", "--synopsys-server", "27030@explicit",
            "--synopsys-lmutil", str(self.binary), "--timeout", "4",
            SNPSLMD_LICENSE_FILE="27030@old", SYNOPSYS_LMUTIL="/missing",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), [
            "lmstat", "-c", "27030@explicit", "-S", "snpslmd", "-t", "4",
        ])

    def test_one_vendor_failure_does_not_hide_other_report(self):
        result = self.run_script(CDS_LIC_FILE="5280@host", SNPSLMD_LICENSE_FILE="27030@host",
                                 FAIL_CADENCE="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Synopsys license checkouts", result.stdout)
        self.assertIn("alice compute01", result.stdout)

    def test_error_output_even_with_success_exit(self):
        for report in ("", "Error getting status: unavailable", "snpslmd: DOWN",
                       "Users of feature: (Error: 15 licenses, unsupported by licensed server)"):
            with self.subTest(report=report):
                result = self.run_script(SNPSLMD_LICENSE_FILE="27030@host", REPORT=report)
                self.assertEqual(result.returncode, 1)
                self.assertIn("incomplete or unknown", result.stderr)

    def test_active_only_preserves_owners_and_errors(self):
        report = REPORT + "Users of broken: (Error: 15 licenses, unsupported by licensed server)\n"
        result = self.run_script("--active-only", SNPSLMD_LICENSE_FILE="27030@host", REPORT=report)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("idle_feature", result.stdout)
        self.assertIn("DC-Expert", result.stdout)
        self.assertIn("alice compute01", result.stdout)
        self.assertIn("Users of broken:", result.stdout)

    def test_deadline(self):
        result = self.run_script("--timeout", "1", SNPSLMD_LICENSE_FILE="27030@host", STALL="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("exit 124", result.stderr)

    def test_missing_binary(self):
        result = self.run_script(SNPSLMD_LICENSE_FILE="27030@host", SYNOPSYS_LMUTIL="/missing/lmutil")
        self.assertEqual(result.returncode, 1)
        self.assertIn("lmutil unavailable", result.stderr)

    def test_invalid_arguments(self):
        for args in (("--vendor", "unknown"), ("--timeout", "0"), ("--timeout", "1.5"),
                     ("--vendor",), ("--unknown",), ("--vendor", "cadence")):
            with self.subTest(args=args):
                self.assertEqual(self.run_script(*args).returncode, 2)


if __name__ == "__main__":
    unittest.main()
