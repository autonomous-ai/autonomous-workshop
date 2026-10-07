"""The run-local wait helper ends a Claude Code wait when the job ends (#112)."""
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
WAIT_FOR = (
    REPOSITORY
    / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/wait_for.py"
)
INTERVAL = 0.2


def wait_for(*arguments):
    started = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(WAIT_FOR), "--interval", str(INTERVAL), *arguments],
        capture_output=True, text=True, timeout=60,
    )
    return result, time.monotonic() - started


class WaitForTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_returns_within_one_interval_after_the_process_exits(self):
        job = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.6)"])
        self.addCleanup(job.wait)
        # The job stays this test's unreaped child: a zombie is an exited job.
        result, elapsed = wait_for("--pid", str(job.pid), "--timeout", "30")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(elapsed, 0.6 + INTERVAL + 1.0)
        self.assertIn("ended", result.stdout)
        self.assertIn("pid %d exited" % job.pid, result.stdout)

    def test_returns_at_the_ceiling_when_the_process_keeps_running(self):
        job = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        self.addCleanup(job.wait)
        self.addCleanup(job.kill)
        result, elapsed = wait_for("--pid", str(job.pid), "--timeout", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreaterEqual(elapsed, 1.0)
        self.assertLess(elapsed, 1.0 + INTERVAL + 1.0)
        self.assertIn("ceiling", result.stdout)
        self.assertIn("pid %d still running" % job.pid, result.stdout)

    def test_reports_the_exit_status_and_the_log_tail(self):
        log = self.directory / "verify.log"
        status = self.directory / "verify.exit"
        job = subprocess.Popen([
            "sh", "-c",
            "printf 'line one\\nverify refused: preflight\\n' > %s; sleep 0.4; echo 3 > %s"
            % (log, status),
        ])
        self.addCleanup(job.wait)
        result, elapsed = wait_for(
            "--exit-file", str(status), "--log", str(log), "--timeout", "30"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(elapsed, 0.4 + INTERVAL + 1.0)
        self.assertIn("exit status 3", result.stdout)
        self.assertIn("verify refused: preflight", result.stdout)

    def test_a_job_that_already_ended_returns_at_once(self):
        status = self.directory / "done.exit"
        status.write_text("0\n")
        result, elapsed = wait_for("--exit-file", str(status), "--timeout", "30")
        self.assertIn("exit status 0", result.stdout)
        self.assertLess(elapsed, INTERVAL + 1.0)

    def test_a_file_ends_the_wait_when_its_pattern_appears(self):
        log = self.directory / "round.log"
        log.write_text("rendering\n")
        job = subprocess.Popen(["sh", "-c", "sleep 0.4; echo 'ROUND PASS' >> %s" % log])
        self.addCleanup(job.wait)
        result, elapsed = wait_for(
            "--file", str(log), "--until-pattern", "ROUND (PASS|FAIL)", "--timeout", "30"
        )
        self.assertIn("ended", result.stdout)
        self.assertIn("ROUND PASS", result.stdout)
        self.assertLess(elapsed, 0.4 + INTERVAL + 1.0)

    def test_without_a_watch_it_waits_to_the_ceiling(self):
        # An agent wait on Claude Code: nothing to watch but the clock.
        result, elapsed = wait_for("--timeout", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreaterEqual(elapsed, 1.0)
        self.assertIn("ceiling", result.stdout)

    def test_a_ceiling_beyond_the_tool_timeout_is_refused(self):
        result, _ = wait_for("--timeout", "900")
        self.assertEqual(result.returncode, 2)
        self.assertIn("590", result.stderr)


if __name__ == "__main__":
    unittest.main()
