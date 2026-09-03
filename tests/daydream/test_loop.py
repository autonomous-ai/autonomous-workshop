import json
import os
import signal
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from workshop.daydream.contracts import DaydreamError
from workshop.daydream.loop import (
    LOOP_FILE_NAME,
    STOP_FILE_NAME,
    LoopState,
    acquire_loop,
    pid_alive,
    read_loop_state,
    request_stop,
)
from workshop.errors import ContractError


MOMENT = datetime(2026, 9, 2, 10, 15, 0, tzinfo=timezone.utc)


class LoopLeaseTest(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.home = Path(self._temporary.name).resolve() / "home"
        self.environment = mock.patch.dict(os.environ, {"WORKSHOP_HOME": str(self.home)})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def _folder(self):
        return self.home / "daydreams" / "sample"

    def test_acquire_writes_a_private_running_record_and_clears_old_stop_markers(self):
        lease = acquire_loop("sample", pid=4242, moment=MOMENT)
        path = self._folder() / LOOP_FILE_NAME
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self._folder().stat().st_mode), 0o700)
        state = read_loop_state(path)
        self.assertEqual(state.pid, 4242)
        self.assertEqual(state.status, "running")
        self.assertEqual(state.started_at, "2026-09-02T10:15:00Z")
        self.assertEqual((state.ideas, state.builds, state.published), (0, 0, 0))
        self.assertFalse(lease.stop_requested())
        (self._folder() / STOP_FILE_NAME).write_text("stop\n")
        self.assertTrue(lease.stop_requested())
        acquire_loop("sample", pid=4242, moment=MOMENT, alive=lambda pid: False)
        self.assertFalse((self._folder() / STOP_FILE_NAME).exists())

    def test_a_live_loop_elsewhere_blocks_a_second_one(self):
        acquire_loop("sample", pid=4242, moment=MOMENT)
        with self.assertRaisesRegex(DaydreamError, "already running \\(pid 4242\\)"):
            acquire_loop("sample", pid=4343, moment=MOMENT, alive=lambda pid: True)
        # The same process may re-acquire, and a dead pid is stale.
        acquire_loop("sample", pid=4242, moment=MOMENT, alive=lambda pid: True)
        lease = acquire_loop("sample", pid=4343, moment=MOMENT, alive=lambda pid: False)
        self.assertEqual(lease.state.pid, 4343)

    def test_update_and_release_persist_atomically(self):
        lease = acquire_loop("sample", pid=4242, moment=MOMENT)
        lease.update(ideas=1, last_daydream_id="daydream-20260902-101500-00000001")
        lease.update(builds=1, published=1, last_wish_id="wish-20260902-101500-0badcafe")
        (self._folder() / STOP_FILE_NAME).write_text("stop\n")
        state = lease.release(reason="stopped by workshop stop", moment=MOMENT)
        self.assertEqual(state.status, "stopped")
        self.assertEqual(state.ideas, 1)
        self.assertEqual(state.published, 1)
        self.assertEqual(state.stop_reason, "stopped by workshop stop")
        self.assertEqual(read_loop_state(self._folder() / LOOP_FILE_NAME), state)
        self.assertFalse((self._folder() / STOP_FILE_NAME).exists())
        self.assertFalse((self._folder() / (LOOP_FILE_NAME + ".tmp")).exists())
        # A stopped record never blocks the next loop.
        acquire_loop("sample", pid=4343, moment=MOMENT, alive=lambda pid: True)

    def test_request_stop_marks_and_optionally_signals(self):
        with self.assertRaisesRegex(DaydreamError, "no daydream loop is running"):
            request_stop("sample")
        acquire_loop("sample", pid=4242, moment=MOMENT)
        with self.assertRaisesRegex(DaydreamError, "no daydream loop is running"):
            request_stop("sample", alive=lambda pid: False)
        signals = []
        state = request_stop("sample", alive=lambda pid: True, signaller=lambda pid, sig: signals.append((pid, sig)))
        self.assertEqual(state.pid, 4242)
        self.assertEqual(signals, [])
        self.assertTrue((self._folder() / STOP_FILE_NAME).is_file())
        request_stop("sample", now=True, alive=lambda pid: True, signaller=lambda pid, sig: signals.append((pid, sig)))
        self.assertEqual(signals, [(4242, signal.SIGINT)])

    def test_malformed_records_read_as_absent(self):
        folder = self._folder()
        folder.mkdir(parents=True, mode=0o700)
        path = folder / LOOP_FILE_NAME
        for payload in (b"", b"{", b"[]", json.dumps({"kind": "other"}).encode()):
            path.write_bytes(payload)
            self.assertIsNone(read_loop_state(path))
        self.assertIsNone(read_loop_state(folder / "missing.json"))

    def test_state_contract_is_strict(self):
        base = dict(
            inventor_id="sample",
            pid=1,
            started_at="2026-09-02T10:15:00Z",
            updated_at="2026-09-02T10:15:00Z",
            status="running",
        )
        LoopState(**base)
        for field, value in (
            ("pid", 0),
            ("status", "paused"),
            ("ideas", -1),
            ("last_daydream_id", "nope"),
            ("stop_reason", ""),
            ("inventor_id", "Bad Id"),
        ):
            with self.subTest(field=field), self.assertRaises(ContractError):
                LoopState(**{**base, field: value})
        with self.assertRaises(ContractError):
            LoopState.parse({**LoopState(**base).to_dict(), "extra": 1})

    def test_pid_alive_reports_this_process(self):
        self.assertTrue(pid_alive(os.getpid()))
        self.assertFalse(pid_alive(2**22 - 1))


if __name__ == "__main__":
    unittest.main()
