import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path

from inventor_workshop.errors import LeaseBusy, StateConflict
from inventor_workshop.lease_guard import LeaseGuard
from inventor_workshop.store import InventorStore


class _OneBeatWait:
    """Let a test trigger exactly one heartbeat without sleeping."""

    def __init__(self):
        self.entered = threading.Event()
        self.proceed = threading.Event()
        self.completed = threading.Event()
        self.calls = 0
        self.timeouts = []

    def __call__(self, timeout):
        self.calls += 1
        self.timeouts.append(timeout)
        if self.calls == 1:
            self.entered.set()
            if not self.proceed.wait(2):
                raise RuntimeError("test did not release heartbeat")
            return False
        self.completed.set()
        return True


class _FakeRuntime:
    def __init__(self):
        self.token = "lease-token"
        self.renewals = []
        self.releases = []
        self.fail_renewal = None
        self.commits = []

    def acquire_lease(self, product_id, holder, ttl_seconds=2700):
        del product_id, holder, ttl_seconds
        return self.token

    def renew_lease(self, product_id, token, ttl_seconds=2700):
        self.renewals.append((product_id, token, ttl_seconds))
        if self.fail_renewal is not None:
            raise self.fail_renewal
        if token != self.token:
            raise StateConflict("stale token")
        return "2026-08-25T00:05:00+00:00"

    def release_lease(self, product_id, token):
        self.releases.append((product_id, token))
        return token == self.token

    def commit(self, token):
        self.commits.append(token)


class LeaseGuardTest(unittest.TestCase):
    def test_active_guard_rejects_another_owner_and_releases_normally(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = InventorStore(Path(temporary) / "state.sqlite3")
            store.register_product("toy", "wish")
            guard = LeaseGuard.acquire(store, "toy", "worker-a", wait=lambda _: True)
            self.assertTrue(guard._thread.daemon)
            with self.assertRaises(LeaseBusy):
                LeaseGuard.acquire(store, "toy", "worker-b", wait=lambda _: True)
            token = guard.assert_current()
            self.assertEqual(token, guard.token)
            self.assertTrue(guard.close())
            replacement = LeaseGuard.acquire(
                store, "toy", "worker-b", wait=lambda _: True
            )
            self.assertNotEqual(replacement.token, token)
            replacement.close()

    def test_daemon_renews_before_half_of_the_ttl(self):
        runtime = _FakeRuntime()
        wait = _OneBeatWait()
        guard = LeaseGuard.acquire(
            runtime,
            "toy",
            "worker",
            ttl_seconds=300,
            renew_interval_seconds=60,
            wait=wait,
        )
        self.assertTrue(wait.entered.wait(2))
        wait.proceed.set()
        self.assertTrue(wait.completed.wait(2))
        self.assertEqual(runtime.renewals, [("toy", "lease-token", 300)])
        self.assertEqual(wait.timeouts, [60.0, 60.0])
        guard.close()

    def test_holding_existing_token_verifies_it_before_starting(self):
        runtime = _FakeRuntime()
        guard = LeaseGuard.hold(
            runtime,
            "toy",
            runtime.token,
            wait=lambda _: True,
        )
        self.assertEqual(runtime.renewals, [("toy", runtime.token, 300)])
        guard.close()
        self.assertEqual(runtime.releases, [("toy", runtime.token)])

    def test_failed_initial_hold_verification_releases_its_known_token(self):
        runtime = _FakeRuntime()
        runtime.fail_renewal = StateConflict("expired")
        with self.assertRaisesRegex(StateConflict, "may not commit"):
            LeaseGuard.hold(
                runtime,
                "toy",
                runtime.token,
                wait=lambda _: True,
            )
        self.assertEqual(runtime.releases, [("toy", runtime.token)])

    def test_renewal_failure_is_latched_and_blocks_the_commit_gate(self):
        runtime = _FakeRuntime()
        wait = _OneBeatWait()
        guard = LeaseGuard.acquire(runtime, "toy", "worker", wait=wait)
        self.assertTrue(wait.entered.wait(2))
        runtime.fail_renewal = StateConflict("expired")
        wait.proceed.set()
        guard._thread.join(2)
        self.assertFalse(guard._thread.is_alive())
        renewal_count = len(runtime.renewals)
        with self.assertRaisesRegex(StateConflict, "may not commit"):
            token = guard.assert_current()
            runtime.commit(token)
        self.assertEqual(runtime.commits, [])
        self.assertEqual(len(runtime.renewals), renewal_count)
        self.assertTrue(guard.lost)
        guard.close()

    def test_synchronous_assertion_latches_a_lost_token(self):
        runtime = _FakeRuntime()
        guard = LeaseGuard.acquire(runtime, "toy", "worker", wait=lambda _: True)
        runtime.fail_renewal = StateConflict("replaced")
        with self.assertRaisesRegex(StateConflict, "may not commit"):
            guard.assert_current()
        runtime.fail_renewal = None
        with self.assertRaisesRegex(StateConflict, "may not commit"):
            guard.assert_current()
        self.assertEqual(len(runtime.renewals), 1)
        guard.close()

    def test_context_manager_releases_and_close_is_idempotent(self):
        runtime = _FakeRuntime()
        with LeaseGuard.acquire(
            runtime, "toy", "worker", wait=lambda _: True
        ) as guard:
            self.assertEqual(guard.assert_current(), runtime.token)
        self.assertEqual(runtime.releases, [("toy", runtime.token)])
        self.assertTrue(guard.close())
        self.assertEqual(runtime.releases, [("toy", runtime.token)])
        with self.assertRaisesRegex(StateConflict, "closed"):
            guard.assert_current()

    def test_expired_lease_can_be_recovered_but_stale_guard_stays_fenced(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.sqlite3"
            store = InventorStore(path)
            store.register_product("toy", "wish")
            stale = LeaseGuard.acquire(
                store, "toy", "worker-a", wait=lambda _: True
            )
            with closing(sqlite3.connect(str(path))) as connection:
                connection.execute(
                    "UPDATE leases SET expires_at='2000-01-01T00:00:00+00:00' "
                    "WHERE product_id='toy'"
                )
                connection.commit()
            current = LeaseGuard.acquire(
                store, "toy", "worker-b", wait=lambda _: True
            )
            with self.assertRaisesRegex(StateConflict, "may not commit"):
                stale.assert_current()
            self.assertNotEqual(current.token, stale.token)
            with self.assertRaises(StateConflict):
                stale.close()
            current.close()


if __name__ == "__main__":
    unittest.main()
