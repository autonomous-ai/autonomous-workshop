"""Tests for the ops module: launchd plists, shell scripts, CI workflow.

Static checks (parse, syntax, load-bearing strings) run everywhere. The
watchdog also gets behavioral tests: we copy ops/watchdog.sh into a temp
"repo" and drive it with fake heartbeats and logs, because the watchdog is
the one piece that must work precisely when everything else is broken -
text2cad's receipt: "silent-channel death must alarm" (4-night blackout,
$13 silent burn). A watchdog verified only by `bash -n` is advisory text.

Stdlib unittest only (CONTRACTS.md sec 5); no network - the watchdog runs
credential-less here, so its alert path is stderr, never curl.
"""

import os
import plistlib
import shutil
import subprocess
import tempfile
import time
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPS = os.path.join(REPO, "ops")
LAUNCHD = os.path.join(OPS, "launchd")

MAIN_PLIST = os.path.join(LAUNCHD, "ai.autonomous.bob.plist")
WATCHDOG_PLIST = os.path.join(LAUNCHD, "ai.autonomous.bob.watchdog.plist")
WATCHDOG_SH = os.path.join(OPS, "watchdog.sh")
INSTALL_SH = os.path.join(OPS, "install.sh")
UNINSTALL_SH = os.path.join(OPS, "uninstall.sh")
# ci.yml lives at the GIT ROOT (one level above bob/) so GitHub runs it
CI_YML = os.path.join(os.path.dirname(REPO), ".github", "workflows", "ci.yml")


class TestMainPlist(unittest.TestCase):
    def setUp(self):
        with open(MAIN_PLIST, "rb") as f:
            self.plist = plistlib.load(f)

    def test_label(self):
        self.assertEqual(self.plist["Label"], "ai.autonomous.bob")

    def test_interval_is_30_minutes(self):
        # 1800s: one queue step per tick; a slow cadence bounds the blast
        # radius of any single kill (text2cad lost whole days to one kill).
        self.assertEqual(self.plist["StartInterval"], 1800)

    def test_runs_bob_tick(self):
        args = self.plist["ProgramArguments"]
        self.assertEqual(args[0], "/usr/bin/python3")
        self.assertTrue(args[1].endswith("/bob.py"))
        self.assertEqual(args[2], "tick")

    def test_working_directory_is_repo(self):
        self.assertEqual(
            self.plist["WorkingDirectory"], "/Users/d/code/inventors/bob"
        )

    def test_logs_land_in_state_logs(self):
        for key in ("StandardOutPath", "StandardErrorPath"):
            self.assertIn("/state/logs/tick.log", self.plist[key])

    def test_path_includes_claude_home(self):
        # launchd gives agents a bare PATH; claude lives in ~/.local/bin.
        path = self.plist["EnvironmentVariables"]["PATH"]
        self.assertIn("/Users/d/.local/bin", path)


class TestWatchdogPlist(unittest.TestCase):
    def setUp(self):
        with open(WATCHDOG_PLIST, "rb") as f:
            self.plist = plistlib.load(f)

    def test_label(self):
        self.assertEqual(self.plist["Label"], "ai.autonomous.bob.watchdog")

    def test_hourly_calendar_interval(self):
        # StartCalendarInterval with only Minute set = every hour at :07.
        cal = self.plist["StartCalendarInterval"]
        self.assertIn("Minute", cal)
        self.assertNotIn("Hour", cal)

    def test_runs_watchdog_script(self):
        args = self.plist["ProgramArguments"]
        self.assertEqual(args[0], "/bin/bash")
        self.assertTrue(args[1].endswith("ops/watchdog.sh"))


class TestShellSyntax(unittest.TestCase):
    def _bash_n(self, path):
        proc = subprocess.run(
            ["/bin/bash", "-n", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(
            proc.returncode, 0,
            "bash -n failed for %s:\n%s" % (path, proc.stderr.decode()),
        )

    def test_watchdog_syntax(self):
        self._bash_n(WATCHDOG_SH)

    def test_install_syntax(self):
        self._bash_n(INSTALL_SH)

    def test_uninstall_syntax(self):
        self._bash_n(UNINSTALL_SH)

    def test_scripts_executable(self):
        for path in (WATCHDOG_SH, INSTALL_SH, UNINSTALL_SH):
            self.assertTrue(os.access(path, os.X_OK), "%s not +x" % path)


class TestInstallScriptContent(unittest.TestCase):
    """install.sh must bootstrap into launchd AND refuse broken deploys."""

    def setUp(self):
        with open(INSTALL_SH) as f:
            self.text = f.read()

    def test_uses_launchctl_bootstrap(self):
        self.assertIn("launchctl bootstrap", self.text)
        self.assertIn('gui/$(id -u)', self.text)

    def test_refuses_when_bob_py_missing(self):
        # The guard catches a launchd agent pointed at nothing - which would
        # otherwise fail silently every 30 minutes until the 6h stale alarm.
        self.assertIn("REFUSING", self.text)
        self.assertIn("bob.py", self.text)

    def test_refuses_when_harness_broken(self):
        self.assertIn("import harness", self.text)

    def test_creates_log_dir(self):
        self.assertIn("state/logs", self.text)

    def test_idempotent_bootout_before_bootstrap(self):
        # Re-running install must redeploy, not error on "already loaded".
        self.assertIn("launchctl bootout", self.text)


class TestUninstallScriptContent(unittest.TestCase):
    def setUp(self):
        with open(UNINSTALL_SH) as f:
            self.text = f.read()

    def test_boots_out_both_labels(self):
        self.assertIn("launchctl bootout", self.text)
        self.assertIn("ai.autonomous.bob", self.text)
        self.assertIn("ai.autonomous.bob.watchdog", self.text)


class TestCIWorkflow(unittest.TestCase):
    """YAML parsing is not stdlib, so assert existence + load-bearing strings."""

    def setUp(self):
        with open(CI_YML) as f:
            self.text = f.read()

    def test_exists_and_runs_unittest_discover(self):
        self.assertIn("unittest discover", self.text)

    def test_python_matrix_covers_runtime_and_future(self):
        self.assertIn("3.9", self.text)   # the Mac's system python (runtime)
        self.assertIn("3.12", self.text)

    def test_mock_agents_forced(self):
        self.assertIn("BOB_MOCK_AGENTS", self.text)

    def test_working_directory_is_bob(self):
        # Repo root is one level above bob/; discovery runs from inside bob/.
        self.assertIn("working-directory: bob", self.text)


class TestWatchdogBehavior(unittest.TestCase):
    """Run watchdog.sh against a fake repo tree in a temp dir.

    watchdog.sh derives REPO from its own location, so copying it to
    <tmp>/ops/watchdog.sh makes <tmp> the repo - no real state touched.
    No Telegram creds are set, so alarms go to stderr ("ALARM"), which is
    exactly the fallback path the contract requires.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="bob-ops-test-")
        os.makedirs(os.path.join(self.tmp, "ops"))
        os.makedirs(os.path.join(self.tmp, "state", "logs"))
        shutil.copy(WATCHDOG_SH, os.path.join(self.tmp, "ops", "watchdog.sh"))
        self.daybook = os.path.join(self.tmp, "state", "DAYBOOK.json")
        self.tick_log = os.path.join(self.tmp, "state", "logs", "tick.log")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self):
        env = dict(os.environ)
        # Belt and braces: make sure no ambient creds turn a test into a DM.
        env.pop("BOB_TELEGRAM_TOKEN", None)
        env.pop("BOB_TELEGRAM_CHAT", None)
        proc = subprocess.run(
            ["/bin/bash", os.path.join(self.tmp, "ops", "watchdog.sh")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        return proc.returncode, proc.stderr.decode()

    def _write(self, path, text, age_seconds=0):
        with open(path, "w") as f:
            f.write(text)
        if age_seconds:
            past = time.time() - age_seconds
            os.utime(path, (past, past))

    def test_missing_heartbeat_alarms(self):
        # A deploy that never ticked once must alarm, same as one that died.
        code, err = self._run()
        self.assertEqual(code, 0)
        self.assertIn("ALARM", err)
        self.assertIn("HEARTBEAT STALE", err)

    def test_stale_heartbeat_alarms(self):
        self._write(self.daybook, "{}", age_seconds=7 * 3600)  # 7h > 6h
        code, err = self._run()
        self.assertIn("HEARTBEAT STALE", err)

    def test_fresh_heartbeat_is_quiet(self):
        self._write(self.daybook, "{}")
        code, err = self._run()
        self.assertEqual(code, 0)
        self.assertNotIn("ALARM", err)

    def test_heartbeat_alarm_rate_limited(self):
        # One dead night must be one DM, not twelve (watchdog runs hourly;
        # a muted channel is no alarm at all).
        self._write(self.daybook, "{}", age_seconds=7 * 3600)
        _, err1 = self._run()
        self.assertIn("HEARTBEAT STALE", err1)
        _, err2 = self._run()
        self.assertNotIn("HEARTBEAT STALE", err2)

    def test_traceback_in_log_tail_alarms(self):
        self._write(self.daybook, "{}")  # heartbeat healthy: isolate alarm 2
        self._write(
            self.tick_log,
            "tick ok\nTraceback (most recent call last):\n  boom\n",
        )
        code, err = self._run()
        self.assertIn("TRACEBACK", err)

    def test_traceback_alarm_only_fires_for_new_writes(self):
        self._write(self.daybook, "{}")
        self._write(
            self.tick_log,
            "Traceback (most recent call last):\n  boom\n",
        )
        _, err1 = self._run()
        self.assertIn("TRACEBACK", err1)
        # No new log writes since the alarm marker -> same crash, no re-DM.
        past = time.time() - 3600
        os.utime(self.tick_log, (past, past))
        _, err2 = self._run()
        self.assertNotIn("TRACEBACK", err2)
        # A NEW traceback (log written after the marker) alarms again.
        time.sleep(1.1)  # marker granularity is 1s on some filesystems
        self._write(self.tick_log, "Traceback (most recent call last):\n  boom2\n")
        _, err3 = self._run()
        self.assertIn("TRACEBACK", err3)

    def test_traceback_outside_last_50_lines_ignored(self):
        # Old crashes scrolled out of the tail are history, not an emergency.
        self._write(self.daybook, "{}")
        lines = ["Traceback (most recent call last):"] + ["ok"] * 60
        self._write(self.tick_log, "\n".join(lines) + "\n")
        _, err = self._run()
        self.assertNotIn("TRACEBACK", err)


if __name__ == "__main__":
    unittest.main()
