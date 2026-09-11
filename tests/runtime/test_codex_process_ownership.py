"""Native exec ownership follows observed creation identities across sessions."""
import signal
import threading
import time
import unittest
from unittest import mock

from workshop.runtime import codex


class ProcessError(Exception):
    pass


class NoSuchProcess(ProcessError):
    pass


class Process:
    def __init__(self, api, pid, created, parent=1):
        self.api, self.pid, self.created, self.parent = api, pid, created, parent
        self.alive = True
        self.signals = []
        self.children_error = None
        self.on_signal = None
        self.ignore_term = False
        self.state = "running"
        api.current[pid] = self

    def create_time(self):
        return self.created

    def is_running(self):
        return self.alive and self.api.current.get(self.pid) is self

    def ppid(self):
        return self.parent

    def status(self):
        return self.state

    def children(self):
        if not self.is_running():
            raise NoSuchProcess()
        if self.children_error:
            raise self.children_error
        return [p for p in self.api.current.values() if p.is_running() and p.parent == self.pid]

    def send_signal(self, number):
        if not self.is_running():
            raise NoSuchProcess()
        self.signals.append(number)
        if self.on_signal:
            self.on_signal(number)
        elif number == signal.SIGKILL or (number == signal.SIGTERM and not self.ignore_term):
            self.alive = False


class ProcessAPI:
    Error = ProcessError
    NoSuchProcess = NoSuchProcess
    STATUS_ZOMBIE = "zombie"

    def __init__(self):
        self.current = {}

    def Process(self, pid):
        process = self.current.get(pid)
        if process is None or not process.is_running():
            raise NoSuchProcess()
        return process


class NativeProcessOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.api = ProcessAPI()
        self.root = Process(self.api, 100, 10.0)
        self.identity = codex._ProcessSessionIdentity(100, 10.0)
        self.patch = mock.patch.object(codex, "_psutil_api", return_value=self.api)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def ownership(self):
        owner = codex._NativeProcessOwnership(self.identity)
        owner.observe()
        self.addCleanup(owner.stop)
        return owner

    def test_retains_reparented_child_and_discovers_its_new_descendants(self):
        child = Process(self.api, 101, 11.0, 100)
        owner = self.ownership()
        self.root.alive = False
        child.parent = 1
        grandchild = Process(self.api, 102, 12.0, child.pid)
        unrelated = Process(self.api, 103, 13.0)
        owner.signal(signal.SIGTERM)
        self.assertEqual(child.signals, [signal.SIGTERM])
        self.assertEqual(grandchild.signals, [signal.SIGTERM])
        self.assertEqual(unrelated.signals, [])
        self.assertTrue(unrelated.is_running())
        self.assertTrue(owner.healthy)
        self.assertEqual(owner.alive_members(), ())

    def test_pid_reuse_never_follows_or_signals_replacement_or_its_children(self):
        child = Process(self.api, 101, 11.0, 100)
        owner = self.ownership()
        replacement_root = Process(self.api, 100, 20.0)
        replacement_child = Process(self.api, 101, 21.0, 100)
        outsider = Process(self.api, 102, 22.0, 101)
        owner.signal(signal.SIGKILL)
        self.assertEqual(owner.alive_members(), ())
        for process in (child, replacement_root, replacement_child, outsider):
            self.assertEqual(process.signals, [])

    def test_reused_root_before_first_observation_is_unsafe_and_never_signaled(self):
        replacement = Process(self.api, 100, 20.0)
        owner = self.ownership()
        owner.signal(signal.SIGKILL)
        self.assertFalse(owner.healthy)
        self.assertEqual(replacement.signals, [])

    def test_denied_enumeration_is_sticky_but_known_members_can_be_stopped(self):
        child = Process(self.api, 101, 11.0, 100)
        owner = self.ownership()
        self.root.children_error = ProcessError("denied")
        owner.observe()
        self.root.children_error = None
        owner.signal(signal.SIGTERM)
        self.assertFalse(owner.healthy)
        self.assertEqual(child.signals, [signal.SIGTERM])
        self.assertEqual(owner.alive_members(), ())

    def test_disappearing_child_is_not_an_enumeration_failure(self):
        child = Process(self.api, 101, 11.0, 100)
        with mock.patch.object(child, "create_time", side_effect=NoSuchProcess()):
            owner = self.ownership()
        child.alive = False
        self.assertTrue(owner.healthy)
        self.assertEqual(owner.alive_members(), (self.root,))

    def test_unknown_enumeration_error_is_sticky(self):
        self.root.children_error = RuntimeError("process table changed unexpectedly")
        owner = self.ownership()
        self.root.children_error = None
        owner.observe()
        self.assertFalse(owner.healthy)

    def test_exited_zombie_is_not_signaled_but_its_retained_child_is(self):
        child = Process(self.api, 101, 11.0, 100)
        grandchild = Process(self.api, 102, 12.0, 101)
        owner = self.ownership()
        child.state = "zombie"
        grandchild.parent = 1
        owner.signal(signal.SIGTERM)
        self.assertEqual(child.signals, [])
        self.assertEqual(grandchild.signals, [signal.SIGTERM])
        self.assertEqual(owner.alive_members(), ())
        self.assertTrue(owner.healthy)

    def test_stalled_observer_cannot_hold_reap_or_its_state_lock(self):
        owner = self.ownership()
        entered, release = threading.Event(), threading.Event()
        results = []

        def blocked_children():
            entered.set()
            release.wait(5)
            return []

        guard = codex._NativeProcessGuard(mock.Mock(), 100, self.identity)
        guard._ownership = owner
        with mock.patch.object(self.root, "children", side_effect=blocked_children), \
             mock.patch.object(codex, "_wait_for_process", return_value=True), \
             mock.patch.object(codex, "_signal_process_session", return_value=0), \
             mock.patch.object(codex, "_process_session_members", return_value=()), \
             mock.patch.object(codex.os, "getsid", return_value=900):
            observer = threading.Thread(target=owner.observe)
            observer.start()
            self.assertTrue(entered.wait(1))
            cleanup = threading.Thread(target=lambda: results.append(guard.reap()), daemon=True)
            cleanup.start()
            try:
                cleanup.join(timeout=3)
                self.assertFalse(cleanup.is_alive(), "cleanup blocked on its observer")
                self.assertEqual(results, [False])
                self.assertFalse(owner.healthy)
                self.assertEqual(self.root.signals, [])
            finally:
                release.set()
                observer.join(timeout=2)
                cleanup.join(timeout=2)
                self.assertTrue(owner.stop())

    def test_stop_never_joins_its_own_watcher(self):
        owner = self.ownership()
        with mock.patch.object(threading, "current_thread", return_value=owner._thread):
            self.assertFalse(owner.stop())
        self.assertTrue(owner.stop())

    def test_unconfirmed_parent_edge_is_unsafe_and_not_signal_authority(self):
        outsider = Process(self.api, 101, 11.0)
        with mock.patch.object(self.root, "children", return_value=[outsider]):
            owner = self.ownership()
        owner.signal(signal.SIGTERM)
        self.assertFalse(owner.healthy)
        self.assertEqual(outsider.signals, [])

    def test_watcher_keeps_sampling_independently_of_event_stream(self):
        owner = self.ownership()
        owner.start()
        child = Process(self.api, 101, 11.0, 100)
        deadline = time.monotonic() + 2
        while (101, 11.0) not in owner._members and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertIn((101, 11.0), owner._members)
        self.assertTrue(owner.stop())
        self.assertFalse(owner._thread.is_alive())

    def test_sigint_grace_precedes_escalation_and_still_observes_new_children(self):
        child = Process(self.api, 101, 11.0, 100)
        child.ignore_term = True
        owner = self.ownership()
        spawned = []

        def native_sigint(number):
            if number == signal.SIGINT:
                self.root.alive = False
                child.parent = 1
                grandchild = Process(self.api, 102, 12.0, 101)
                grandchild.ignore_term = True
                spawned.append(grandchild)

        self.root.on_signal = native_sigint
        with mock.patch.object(codex, "_wait_for_process", return_value=True), \
             mock.patch.object(codex, "_signal_process_session", return_value=0), \
             mock.patch.object(codex, "_process_session_members", return_value=()), \
             mock.patch.object(codex.os, "getsid", return_value=900):
            self.assertTrue(codex._terminate_safely(
                mock.Mock(), process_group_id=100, process_session_identity=self.identity,
                process_ownership=owner,
            ))
        self.assertEqual(self.root.signals, [signal.SIGINT])
        for process in (child, *spawned):
            self.assertEqual(process.signals, [signal.SIGTERM, signal.SIGKILL])

    def test_failed_discovery_cannot_become_success_when_session_is_empty(self):
        owner = self.ownership()
        self.root.children_error = ProcessError("denied")
        owner.observe()
        self.root.children_error = None
        with mock.patch.object(codex, "_wait_for_process", return_value=True), \
             mock.patch.object(codex, "_signal_process_session", return_value=0), \
             mock.patch.object(codex, "_process_session_members", return_value=()), \
             mock.patch.object(codex.os, "getsid", return_value=900):
            self.assertFalse(codex._terminate_safely(
                mock.Mock(), process_group_id=100, process_session_identity=self.identity,
                process_ownership=owner,
            ))

    def test_concurrent_reap_is_idempotent_without_real_discovery_for_fakes(self):
        guard = codex._NativeProcessGuard(mock.Mock(), None, None)
        calls = []
        results = []

        def cleanup(*args, **kwargs):
            calls.append(True)
            time.sleep(.02)
            return True

        with mock.patch.object(codex, "_terminate_safely", side_effect=cleanup), \
             mock.patch.object(codex, "_psutil_api", side_effect=AssertionError("fake process discovery")):
            threads = [threading.Thread(target=lambda: results.append(guard.reap())) for _ in range(4)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=1)
                self.assertFalse(thread.is_alive())
        self.assertEqual(calls, [True])
        self.assertEqual(results, [True] * 4)


if __name__ == "__main__":
    unittest.main()
