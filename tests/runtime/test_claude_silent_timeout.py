import tempfile
import threading
import time
import unittest
from pathlib import Path

from workshop.runtime.claude import (
    ClaudeNativeSessionLauncher, ClaudeRecoverableInvocationError,
)


class ClaudeSilentTimeoutTest(unittest.TestCase):
    def test_timeout_interrupts_silent_stdout_and_reaps_cli(self):
        stopped = threading.Event()

        class SilentStream:
            def __iter__(self):
                # A deadline outside this reader must fire without another line.
                stopped.wait(5)
                return iter(())

        class Process:
            stdout = SilentStream()
            stderr = ()
            killed = False
            reaped = False

            def kill(self):
                self.killed = True
                stopped.set()

            def wait(self, timeout=None):
                self.reaped = True
                return -9

        process = Process()
        launcher = ClaudeNativeSessionLauncher(
            binary="/bin/claude", cli_version="2.1.0",
            timeout_seconds=1, popen_factory=lambda *a, **kw: process,
        )
        self.addCleanup(stopped.set)
        with tempfile.TemporaryDirectory() as tmp:
            started = time.monotonic()
            with self.assertRaisesRegex(ClaudeRecoverableInvocationError, "timed out"):
                launcher._stream(command=["/bin/claude"], run_root=Path(tmp),
                                 activity_observer=None)
            self.assertLess(time.monotonic() - started, 3)
        self.assertTrue(process.killed)
        self.assertTrue(process.reaped)
