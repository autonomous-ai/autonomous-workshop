import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.errors import ContractError
from workshop.runtime.progress import (
    NATIVE_PROGRESS_FILENAME,
    WISH_RUN_TIMING_OPERATIONS,
    WISH_RUN_TIMING_RECORD_FILENAME,
    NativeProgressUnavailable,
    WishRunTimingEvent,
    begin_native_progress,
    native_progress_turn_floor,
    read_native_progress,
    read_wish_run_timing_record,
    record_wish_run_timing_event,
    trusted_native_progress,
    wish_run_timing_span,
    write_native_progress,
)


class NativeProgressTest(unittest.TestCase):
    def progress(self, path, *, started_at_ms=1_000):
        progress = begin_native_progress(
            None,
            product_id="wish-progress",
            wish_sha256="a" * 64,
            checkpoint_sha256="b" * 64,
            checkpoint_stage="make",
            started_at_ms=started_at_ms,
        )
        write_native_progress(path, progress, establish_generation=True)
        return progress

    def test_private_round_trip_is_bounded_content_free_and_checkpoint_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path = root / NATIVE_PROGRESS_FILENAME
            progress = self.progress(path).observe("tool", observed_at_ms=3_500)
            write_native_progress(path, progress)

            observed = trusted_native_progress(
                path,
                product_id="wish-progress",
                wish_sha256="a" * 64,
                checkpoint_sha256="b" * 64,
                checkpoint_stage="make",
            )

            self.assertEqual(observed, progress)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            generation = root / ".native-progress.json.generation"
            self.assertEqual(stat.S_IMODE(generation.stat().st_mode), 0o600)
            self.assertEqual(generation.read_bytes(), b"1\n")
            self.assertEqual(
                observed.public_view(observed_at_ms=5_100),
                {
                    "status": "available",
                    "stage_attempt": {"stage": "make", "number": 1},
                    "activity": "tool",
                    "elapsed_seconds": 4,
                    "last_activity_at": "1970-01-01T00:00:03.500Z",
                },
            )
            fields = set(json.loads(path.read_text(encoding="utf-8")))
            self.assertEqual(
                fields,
                {
                    "schema_version",
                    "kind",
                    "product_id",
                    "wish_sha256",
                    "checkpoint_sha256",
                    "checkpoint_stage",
                    "attempt_stage",
                    "stage_attempt",
                    "native_turns",
                    "activity",
                    "attempt_started_at_ms",
                    "last_activity_at_ms",
                    "progress_sha256",
                },
            )

    def test_turn_and_stage_attempt_counts_are_durable(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / NATIVE_PROGRESS_FILENAME
            first = self.progress(path)
            second = begin_native_progress(
                read_native_progress(path),
                product_id="wish-progress",
                wish_sha256="a" * 64,
                checkpoint_sha256="b" * 64,
                checkpoint_stage="make",
                started_at_ms=2_000,
            )
            self.assertEqual((second.native_turns, second.stage_attempt), (2, 2))

            rebound = second.rebind(
                checkpoint_sha256="c" * 64,
                checkpoint_stage="playtest",
                activity="completed",
                observed_at_ms=2_500,
            )
            third = begin_native_progress(
                rebound,
                product_id="wish-progress",
                wish_sha256="a" * 64,
                checkpoint_sha256="c" * 64,
                checkpoint_stage="playtest",
                started_at_ms=3_000,
            )
            self.assertEqual((third.native_turns, third.stage_attempt), (3, 1))
            self.assertEqual(first.native_turns, 1)

    def test_late_previous_turn_update_cannot_roll_back_current_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / NATIVE_PROGRESS_FILENAME
            first = self.progress(path)
            second = begin_native_progress(
                read_native_progress(path),
                product_id="wish-progress",
                wish_sha256="a" * 64,
                checkpoint_sha256="b" * 64,
                checkpoint_stage="make",
                started_at_ms=2_000,
            )
            self.assertTrue(
                write_native_progress(
                    path,
                    second,
                    establish_generation=True,
                )
            )

            stale = first.observe("failed", observed_at_ms=3_000)
            self.assertFalse(write_native_progress(path, stale))
            self.assertEqual(read_native_progress(path), second)
            self.assertEqual(native_progress_turn_floor(path), 2)

    def test_running_heartbeat_remains_active_and_advances_safe_time(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / NATIVE_PROGRESS_FILENAME
            running = self.progress(path).observe(
                "running",
                observed_at_ms=3_500,
            )

            self.assertEqual(
                running.public_view(observed_at_ms=5_100),
                {
                    "status": "available",
                    "stage_attempt": {"stage": "make", "number": 1},
                    "activity": "running",
                    "elapsed_seconds": 4,
                    "last_activity_at": "1970-01-01T00:00:03.500Z",
                },
            )

    def test_malformed_tampered_wrong_mode_and_symlink_records_are_unavailable(self):
        cases = ("malformed", "tampered", "wrong-mode", "symlink")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                path = root / NATIVE_PROGRESS_FILENAME
                self.progress(path)
                if case == "malformed":
                    path.write_bytes(b"{")
                    os.chmod(path, 0o600)
                elif case == "tampered":
                    value = json.loads(path.read_text(encoding="utf-8"))
                    value["native_turns"] = 999
                    path.write_text(json.dumps(value), encoding="utf-8")
                    os.chmod(path, 0o600)
                elif case == "wrong-mode":
                    os.chmod(path, 0o644)
                else:
                    target = root / "outside.json"
                    path.rename(target)
                    path.symlink_to(target)

                with self.assertRaises(NativeProgressUnavailable):
                    read_native_progress(path)
                self.assertIsNone(
                    trusted_native_progress(
                        path,
                        product_id="wish-progress",
                        wish_sha256="a" * 64,
                        checkpoint_sha256="b" * 64,
                        checkpoint_stage="make",
                    )
                )

    def test_mismatched_product_or_checkpoint_is_never_displayed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / NATIVE_PROGRESS_FILENAME
            self.progress(path)
            for overrides in (
                {"product_id": "wish-other"},
                {"wish_sha256": "c" * 64},
                {"checkpoint_sha256": "d" * 64},
                {"checkpoint_stage": "invent"},
            ):
                values = {
                    "product_id": "wish-progress",
                    "wish_sha256": "a" * 64,
                    "checkpoint_sha256": "b" * 64,
                    "checkpoint_stage": "make",
                }
                values.update(overrides)
                self.assertIsNone(trusted_native_progress(path, **values))

    def test_read_io_failure_is_unavailable_never_a_status_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / NATIVE_PROGRESS_FILENAME
            self.progress(path)
            with mock.patch(
                "workshop.runtime.progress.os.read",
                side_effect=OSError("fixture read interruption"),
            ):
                with self.assertRaises(NativeProgressUnavailable):
                    read_native_progress(path)
                self.assertIsNone(
                    trusted_native_progress(
                        path,
                        product_id="wish-progress",
                        wish_sha256="a" * 64,
                        checkpoint_sha256="b" * 64,
                        checkpoint_stage="make",
                    )
                )


class WishRunTimingTest(unittest.TestCase):
    def event(self, **overrides):
        values = {
            "observed_at": "2026-08-27T03:14:15.926Z",
            "product_id": "wish-progress",
            "stage": "make",
            "operation": "session.resume",
            "state": "completed",
            "elapsed_ms": 37,
        }
        values.update(overrides)
        return WishRunTimingEvent(**values)

    def test_event_is_bounded_and_elapsed_is_terminal_only(self):
        self.assertEqual(
            self.event().to_dict(),
            {
                "observed_at": "2026-08-27T03:14:15.926Z",
                "product_id": "wish-progress",
                "stage": "make",
                "operation": "session.resume",
                "state": "completed",
                "elapsed_ms": 37,
            },
        )
        started = self.event(state="started", elapsed_ms=None)
        self.assertNotIn("elapsed_ms", started.to_dict())
        with self.assertRaisesRegex(ContractError, "cannot have elapsed_ms"):
            self.event(state="started")
        with self.assertRaisesRegex(ContractError, "requires nonnegative"):
            self.event(elapsed_ms=-1)

    def test_event_rejects_unknown_identifiers_and_arbitrary_metadata(self):
        invalid = (
            ({"observed_at": "not-a-timestamp"}, "timestamp"),
            ({"product_id": "private wish text"}, "product_id"),
            ({"stage": "concept"}, "stage"),
            ({"operation": "provider.private-response"}, "operation"),
            ({"state": "waiting"}, "state"),
        )
        for overrides, message in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaisesRegex(ContractError, message):
                    self.event(**overrides)
        with self.assertRaises(TypeError):
            WishRunTimingEvent(
                observed_at="2026-08-27T03:14:15.926Z",
                product_id="wish-progress",
                stage="make",
                operation="session.resume",
                state="started",
                private_response="secret",
            )

    def test_span_is_noop_without_observer(self):
        with mock.patch(
            "workshop.runtime.progress._now_ms",
            side_effect=AssertionError("wall clock should not be read"),
        ), mock.patch(
            "workshop.runtime.progress.time.monotonic",
            side_effect=AssertionError("monotonic clock should not be read"),
        ):
            with wish_run_timing_span(
                None,
                product_id="wish-progress",
                stage="make",
                operation="stage.prepare",
            ):
                pass

    def test_span_emits_pair_with_monotonic_nonnegative_duration(self):
        events = []
        with mock.patch(
            "workshop.runtime.progress._now_ms",
            side_effect=(1_000, 500),
        ), mock.patch(
            "workshop.runtime.progress.time.monotonic",
            side_effect=(10.0, 11.25),
        ):
            with wish_run_timing_span(
                events.append,
                product_id="wish-progress",
                stage="make",
                operation="stage.prepare",
            ):
                pass
        self.assertEqual([event.state for event in events], ["started", "completed"])
        self.assertEqual(events[1].elapsed_ms, 1_250)
        self.assertEqual(events[1].observed_at, "1970-01-01T00:00:00.500Z")

        events.clear()
        with mock.patch(
            "workshop.runtime.progress._now_ms",
            side_effect=(1_000, 1_001),
        ), mock.patch(
            "workshop.runtime.progress.time.monotonic",
            side_effect=(12.0, 11.0),
        ):
            with wish_run_timing_span(
                events.append,
                product_id="wish-progress",
                stage="make",
                operation="stage.prepare",
            ):
                pass
        self.assertEqual(events[1].elapsed_ms, 0)

    def test_span_reports_failure_without_masking_or_exposing_it(self):
        events = []
        failure = RuntimeError("private provider response")
        with mock.patch(
            "workshop.runtime.progress._now_ms",
            side_effect=(1_000, 1_125),
        ), mock.patch(
            "workshop.runtime.progress.time.monotonic",
            side_effect=(20.0, 20.125),
        ):
            try:
                with wish_run_timing_span(
                    events.append,
                    product_id="wish-progress",
                    stage="release",
                    operation="effect.factory",
                ):
                    raise failure
            except RuntimeError as observed:
                self.assertIs(observed, failure)
            else:  # pragma: no cover
                self.fail("timing span swallowed the original exception")
        self.assertEqual([event.state for event in events], ["started", "failed"])
        self.assertEqual(events[1].elapsed_ms, 125)
        self.assertNotIn("private provider response", repr(events[1].to_dict()))

    def test_failed_observer_cannot_mask_operation_failure(self):
        failure = RuntimeError("operation failed")
        calls = 0

        def observer(event):
            nonlocal calls
            calls += 1
            if event.state == "failed":
                raise OSError("progress stream failed")

        with mock.patch(
            "workshop.runtime.progress._now_ms",
            side_effect=(1_000, 1_001),
        ), mock.patch(
            "workshop.runtime.progress.time.monotonic",
            side_effect=(1.0, 1.001),
        ):
            with self.assertRaisesRegex(RuntimeError, "operation failed") as raised:
                with wish_run_timing_span(
                    observer,
                    product_id="wish-progress",
                    stage="release",
                    operation="effect.factory",
                ):
                    raise failure
        self.assertIs(raised.exception, failure)
        self.assertEqual(calls, 2)

    def test_observer_failure_cannot_prevent_successful_operation(self):
        ran = False

        def observer(unused_event):
            raise OSError("progress stream failed")

        with mock.patch(
            "workshop.runtime.progress._now_ms",
            side_effect=(1_000, 1_001),
        ), mock.patch(
            "workshop.runtime.progress.time.monotonic",
            side_effect=(1.0, 1.001),
        ):
            with wish_run_timing_span(
                observer,
                product_id="wish-progress",
                stage="make",
                operation="stage.prepare",
            ):
                ran = True
        self.assertTrue(ran)


class WishRunTimingRecordTest(unittest.TestCase):
    """The recorder that turns a bracketed timing stream into host state."""

    def event(self, **overrides):
        values = {
            "observed_at": "2026-08-27T03:14:15.000Z",
            "product_id": "wish-timing-record",
            "stage": "make",
            "operation": "session.resume",
            "state": "completed",
            "elapsed_ms": 250,
        }
        values.update(overrides)
        return WishRunTimingEvent(**values)

    def test_pins_observed_operation_vocabulary(self):
        """Adding a bracketed operation must be a deliberate, visible change."""

        self.assertEqual(
            WISH_RUN_TIMING_OPERATIONS,
            (
                "run.initialize",
                "stage.prepare",
                "session.start",
                "session.resume",
                "outcome.process",
                "gate.evaluate",
                "effect.factory",
            ),
        )

    def test_aggregates_by_stage_then_operation_with_counts_and_states(self):
        with tempfile.TemporaryDirectory() as temporary:
            host_state = Path(temporary).resolve()
            record_wish_run_timing_event(
                host_state,
                self.event(
                    observed_at="2026-08-27T03:14:15.000Z",
                    state="started",
                    elapsed_ms=None,
                ),
            )
            record_wish_run_timing_event(
                host_state,
                self.event(
                    observed_at="2026-08-27T03:14:15.250Z",
                    state="completed",
                    elapsed_ms=250,
                ),
            )
            record_wish_run_timing_event(
                host_state,
                self.event(
                    observed_at="2026-08-27T03:14:20.000Z",
                    stage="make",
                    operation="session.resume",
                    state="failed",
                    elapsed_ms=100,
                ),
            )
            record_wish_run_timing_event(
                host_state,
                self.event(
                    observed_at="2026-08-27T03:14:21.000Z",
                    stage="release",
                    operation="effect.factory",
                    state="completed",
                    elapsed_ms=50,
                ),
            )

            record = read_wish_run_timing_record(
                host_state / WISH_RUN_TIMING_RECORD_FILENAME,
                product_id="wish-timing-record",
            )
            self.assertIsNotNone(record)
            self.assertEqual(
                record["stages"]["make"]["session.resume"],
                {"count": 2, "elapsed_ms": 350, "states": {"completed": 1, "failed": 1}},
            )
            self.assertEqual(
                record["stages"]["release"]["effect.factory"],
                {"count": 1, "elapsed_ms": 50, "states": {"completed": 1}},
            )
            self.assertEqual(record["measured_ms"], 400)
            self.assertEqual(record["total_ms"], 6_000)
            self.assertEqual(record["unmeasured_ms"], 5_600)
            self.assertEqual(
                record["total_ms"], record["measured_ms"] + record["unmeasured_ms"]
            )

    def test_started_event_with_no_terminal_partner_is_not_counted(self):
        with tempfile.TemporaryDirectory() as temporary:
            host_state = Path(temporary).resolve()
            record_wish_run_timing_event(
                host_state,
                self.event(state="started", elapsed_ms=None),
            )
            record = read_wish_run_timing_record(
                host_state / WISH_RUN_TIMING_RECORD_FILENAME,
                product_id="wish-timing-record",
            )
            self.assertIsNotNone(record)
            self.assertEqual(record["stages"], {})
            self.assertEqual(record["measured_ms"], 0)
            self.assertEqual(record["total_ms"], 0)
            self.assertEqual(record["unmeasured_ms"], 0)

    def test_dropped_write_lowers_measured_and_raises_unmeasured_not_the_total(self):
        with tempfile.TemporaryDirectory() as temporary:
            host_state = Path(temporary).resolve()
            path = host_state / WISH_RUN_TIMING_RECORD_FILENAME
            record_wish_run_timing_event(
                host_state,
                self.event(observed_at="2026-08-27T03:14:15.000Z", state="started", elapsed_ms=None),
            )
            before = read_wish_run_timing_record(path, product_id="wish-timing-record")

            # A terminal event that never lands: e.g. the observer callback
            # raised before this ran, or (as simulated here) the write itself
            # failed. Nothing about this call reaches the durable record.
            with mock.patch("os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    record_wish_run_timing_event(
                        host_state,
                        self.event(
                            observed_at="2026-08-27T03:14:20.000Z",
                            state="completed",
                            elapsed_ms=5_000,
                        ),
                    )
            dropped = read_wish_run_timing_record(path, product_id="wish-timing-record")

            # A later event succeeds and its own timestamp becomes the new
            # anchor, so the missed duration surfaces as unmeasured time
            # rather than vanishing or corrupting the total.
            record_wish_run_timing_event(
                host_state,
                self.event(
                    observed_at="2026-08-27T03:14:25.000Z",
                    state="completed",
                    elapsed_ms=100,
                ),
            )
            after = read_wish_run_timing_record(path, product_id="wish-timing-record")
            self.assertEqual(dropped, before)
            self.assertEqual(after["measured_ms"], 100)
            self.assertEqual(after["total_ms"], 10_000)
            self.assertEqual(after["unmeasured_ms"], 9_900)

    def test_unwritable_host_state_raises_for_the_caller_to_swallow(self):
        with tempfile.TemporaryDirectory() as temporary:
            host_state = Path(temporary).resolve() / "missing"
            with self.assertRaises(OSError):
                record_wish_run_timing_event(host_state, self.event())

    def test_foreign_or_corrupt_record_is_ignored_and_a_fresh_one_starts(self):
        with tempfile.TemporaryDirectory() as temporary:
            host_state = Path(temporary).resolve()
            path = host_state / WISH_RUN_TIMING_RECORD_FILENAME
            path.write_text("not json", encoding="utf-8")
            os.chmod(path, 0o600)
            record_wish_run_timing_event(host_state, self.event())
            record = read_wish_run_timing_record(
                path, product_id="wish-timing-record"
            )
            self.assertIsNotNone(record)
            self.assertEqual(record["measured_ms"], 250)

            other = read_wish_run_timing_record(path, product_id="a-different-wish")
            self.assertIsNone(other)


if __name__ == "__main__":
    unittest.main()
