from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
import stat
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alice.store import (  # noqa: E402
    CANDIDATE_STATES,
    SCHEMA_VERSION,
    DurableStore,
    EventChainError,
    IdempotencyConflictError,
    LeaseLostError,
    NotFoundError,
    StateConflictError,
    StoreClosedError,
)


class FakeClock:
    def __init__(self, value: float = 1_700_000_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> float:
        self.value += seconds
        return self.value


class DurableStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temporary.name) / "nested" / "alice.sqlite3"
        self.clock = FakeClock()
        self.store = DurableStore(self.db_path, clock=self.clock)

    def tearDown(self) -> None:
        self.store.close()
        self.temporary.cleanup()

    def enqueue(self, key: str = "task:one", **overrides: object):
        options: dict[str, object] = {
            "idempotency_key": key,
            "run_id": "run-17",
            "candidate_id": "candidate-9",
            "priority": 3,
            "max_attempts": 3,
        }
        options.update(overrides)
        return self.store.enqueue_task("research", {"topic": "bridges"}, **options)

    def test_wal_parent_creation_reopen_and_close(self) -> None:
        self.assertTrue(self.db_path.exists())
        self.assertEqual(self.store.journal_mode, "wal")
        task = self.enqueue()
        head = self.store.event_head()
        self.assertEqual(head[0], 1)
        self.assertEqual(self.store.quick_check(), "ok")
        self.store.close()

        reopened = DurableStore(self.db_path, clock=self.clock)
        try:
            self.assertEqual(reopened.get_task(task.id).payload["topic"], "bridges")
            self.assertEqual(reopened.event_head(), head)
            self.assertTrue(reopened.verify_event_chain(expected_head=head[1]))
            self.assertEqual(reopened.stats()["counts"]["tasks"], 1)
        finally:
            reopened.close()

        with self.assertRaises(StoreClosedError):
            self.store.stats()

    def test_alice_created_runtime_and_database_files_are_private(self) -> None:
        self.enqueue("task:private-permissions")
        self.assertEqual(
            stat.S_IMODE(self.db_path.parent.stat().st_mode), 0o700
        )
        self.assertEqual(stat.S_IMODE(self.db_path.stat().st_mode), 0o600)
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(self.db_path) + suffix)
            if sidecar.exists():
                self.assertEqual(stat.S_IMODE(sidecar.stat().st_mode), 0o600)

    def test_v1_store_is_migrated_additively_to_current_schema(self) -> None:
        self.store.close()
        connection = sqlite3.connect(self.db_path)
        try:
            connection.executescript(
                """
                DROP INDEX tasks_state_created_idx;
                DROP TABLE candidate_artifacts;
                DROP TABLE task_derived_applications;
                DROP TABLE versioned_state;
                UPDATE store_meta SET value = '1' WHERE key = 'schema_version';
                PRAGMA user_version = 1;
                """
            )
        finally:
            connection.close()

        self.store = DurableStore(self.db_path, clock=self.clock)
        self.assertEqual(SCHEMA_VERSION, 2)
        migrated = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(migrated.execute("PRAGMA user_version").fetchone()[0], 2)
            table_names = {
                row[0]
                for row in migrated.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            index_names = {
                row[0]
                for row in migrated.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                )
            }
        finally:
            migrated.close()
        self.assertTrue(
            {
                "candidate_artifacts",
                "task_derived_applications",
                "versioned_state",
            }.issubset(table_names)
        )
        self.assertIn("tasks_state_created_idx", index_names)
        self.assertEqual(self.store.stats()["schema_version"], 2)

    def test_task_enqueue_is_idempotent_and_detects_conflicts(self) -> None:
        supplied_hash = hashlib.sha256(b"exact input artifact").hexdigest()
        original = self.enqueue(input_sha256=supplied_hash)
        self.clock.advance(50)
        replay = self.enqueue(input_sha256=supplied_hash)

        self.assertEqual(replay.id, original.id)
        self.assertEqual(replay.created_at, original.created_at)
        self.assertEqual(replay.input_sha256, supplied_hash)
        self.assertEqual(replay.payload["run_id"], "run-17")
        self.assertEqual(replay.payload["candidate_id"], "candidate-9")
        self.assertEqual(replay.payload["input_sha256"], supplied_hash)
        self.assertEqual(self.store.task_counts()["queued"], 1)
        self.assertEqual(self.store.stats()["counts"]["events"], 1)
        self.assertEqual(
            self.store.get_task_by_idempotency_key("task:one").id, original.id
        )

        with self.assertRaises(IdempotencyConflictError):
            self.store.enqueue_task(
                "research",
                {"topic": "tunnels"},
                idempotency_key="task:one",
                run_id="run-17",
                candidate_id="candidate-9",
                input_sha256=supplied_hash,
                priority=3,
                max_attempts=3,
            )
        with self.assertRaises(ValueError):
            self.store.enqueue_task(
                "research",
                {"run_id": "one"},
                idempotency_key="bad-envelope",
                run_id="two",
            )

    def test_atomic_lease_is_fenced_by_worker_and_token(self) -> None:
        task = self.enqueue()
        other = DurableStore(self.db_path, clock=self.clock)
        try:
            leased = other.lease_task("worker-a", lease_seconds=20)
            self.assertEqual(leased.id, task.id)
            self.assertEqual(leased.state, "leased")
            self.assertIsNotNone(leased.lease_attempt_id)
            self.assertIsNone(self.store.lease_task("worker-b", lease_seconds=20))

            with self.assertRaises(LeaseLostError):
                self.store.complete_task(
                    task.id, "worker-b", leased.lease_token, {"answer": 1}
                )
            with self.assertRaises(LeaseLostError):
                self.store.complete_task(task.id, "worker-a", "wrong-token", {})

            renewed = other.renew_task_lease(
                task.id,
                "worker-a",
                leased.lease_token,
                lease_seconds=45,
                now=self.clock.value + 5,
            )
            self.assertEqual(renewed.lease_expires_at, self.clock.value + 50)
            output_hash = hashlib.sha256(b"artifact bytes").hexdigest()
            completed = other.complete_task(
                task.id,
                "worker-a",
                leased.lease_token,
                {"answer": 42},
                output_sha256=output_hash,
                now=self.clock.value + 6,
            )
            self.assertEqual(completed.state, "succeeded")
            self.assertEqual(completed.result, {"answer": 42})
            self.assertEqual(completed.output_sha256, output_hash)
            attempt = self.store.list_attempts(task.id)[0]
            self.assertEqual(attempt.status, "succeeded")
            self.assertEqual(attempt.output_sha256, output_hash)
            success = self.store.list_events(kind="task.succeeded")[0]
            self.assertEqual(success.attempt_id, attempt.id)
            self.assertEqual(success.attempt_seq, 1)
            self.assertEqual(success.stage, "research")
            self.assertEqual(success.input_sha256, task.input_sha256)
            self.assertEqual(success.output_sha256, output_hash)
        finally:
            other.close()

    def test_expired_leases_recover_and_exhaust_attempts(self) -> None:
        task = self.enqueue(max_attempts=2)
        first = self.store.lease_task("crashed-worker", lease_seconds=10)
        self.assertIsNotNone(first)
        self.clock.advance(10)

        recovered = self.store.recover_expired_leases()
        self.assertEqual([item.id for item in recovered], [task.id])
        self.assertEqual(recovered[0].state, "queued")
        self.assertEqual(recovered[0].last_error_code, "lease_expired")
        with self.assertRaises(LeaseLostError):
            self.store.complete_task(
                task.id, "crashed-worker", first.lease_token, {"too": "late"}
            )
        self.assertEqual(self.store.list_attempts(task.id)[0].status, "expired")

        second = self.store.lease_task("worker-two", lease_seconds=5)
        self.assertEqual(second.attempt_count, 2)
        self.clock.advance(5)
        recovered = self.store.recover_expired_leases()
        self.assertEqual(recovered[0].state, "failed")
        self.assertEqual(
            [attempt.status for attempt in self.store.list_attempts(task.id)],
            ["expired", "expired"],
        )
        self.assertIsNone(self.store.lease_task("worker-three"))
        self.assertEqual(
            len(self.store.list_events(kind="task.lease_expired")), 2
        )

    def test_retryable_failure_tracks_attempt_and_delay(self) -> None:
        task = self.enqueue()
        leased = self.store.lease_task("worker-a", lease_seconds=30)
        retried = self.store.fail_task(
            task.id,
            "worker-a",
            leased.lease_token,
            stage="research.fetch",
            error_code="upstream_timeout",
            error_message="source timed out",
            retryable=True,
            retry_delay=15,
            details={"url": "https://example.test"},
        )
        self.assertEqual(retried.state, "queued")
        self.assertEqual(retried.available_at, self.clock.value + 15)
        self.assertEqual(retried.last_error_stage, "research.fetch")
        self.assertIsNone(self.store.lease_task("early", now=self.clock.value + 14))

        next_attempt = self.store.lease_task("worker-b", now=self.clock.value + 15)
        self.assertEqual(next_attempt.attempt_count, 2)
        done = self.store.complete_task(
            task.id,
            "worker-b",
            next_attempt.lease_token,
            {"ok": True},
            now=self.clock.value + 16,
        )
        self.assertEqual(done.state, "succeeded")
        attempts = self.store.list_attempts(task.id)
        self.assertEqual([attempt.status for attempt in attempts], ["failed", "succeeded"])
        self.assertEqual(attempts[0].stage, "research.fetch")
        self.assertEqual(attempts[0].error_code, "upstream_timeout")
        self.assertEqual(attempts[0].outcome, {"url": "https://example.test"})

    def test_nonretryable_failure_and_cancel(self) -> None:
        terminal = self.enqueue("terminal")
        lease = self.store.lease_task("worker")
        failed = self.store.fail_task(
            terminal.id,
            "worker",
            lease.lease_token,
            stage="research",
            error_code="invalid_output",
            error_message="schema mismatch",
            retryable=False,
        )
        self.assertEqual(failed.state, "failed")
        self.assertIsNone(self.store.lease_task("worker"))
        with self.assertRaises(StateConflictError):
            self.store.cancel_task(terminal.id)

        queued = self.enqueue("cancel-me")
        cancelled = self.store.cancel_task(queued.id, reason="superseded")
        self.assertEqual(cancelled.state, "cancelled")
        self.assertEqual(cancelled.last_error_message, "superseded")
        self.assertEqual(self.store.cancel_task(queued.id).id, queued.id)

    def test_candidate_state_is_validated_but_transition_policy_is_external(self) -> None:
        candidate = self.store.create_candidate(
            {"rules": ["place", "move"]},
            title="Bridgeworks",
            kind="board_game",
            metadata={"generation": 1},
            idempotency_key="candidate:bridgeworks",
        )
        replay = self.store.create_candidate(
            {"rules": ["place", "move"]},
            title="Bridgeworks",
            kind="board_game",
            metadata={"generation": 1},
            idempotency_key="candidate:bridgeworks",
        )
        self.assertEqual(replay.id, candidate.id)
        self.assertIn("page_ready", CANDIDATE_STATES)

        # Persistence accepts any valid named state; policy.py owns legal edges.
        page_ready = self.store.transition_candidate(
            candidate.id,
            "page_ready",
            expected_state="proposed",
            expected_version=1,
            metadata_patch={"page": "artifact/page.json"},
        )
        self.assertEqual(page_ready.state, "page_ready")
        self.assertEqual(page_ready.version, 2)
        self.assertEqual(page_ready.metadata["generation"], 1)
        self.assertEqual(page_ready.metadata["page"], "artifact/page.json")
        # Replaying the original creation request remains idempotent after the
        # mutable candidate has advanced.
        after_transition_replay = self.store.create_candidate(
            {"rules": ["place", "move"]},
            title="Bridgeworks",
            kind="board_game",
            metadata={"generation": 1},
            idempotency_key="candidate:bridgeworks",
        )
        self.assertEqual(after_transition_replay.id, candidate.id)
        self.assertEqual(after_transition_replay.state, "page_ready")
        with self.assertRaises(IdempotencyConflictError):
            self.store.create_candidate(
                {"rules": ["different"]},
                title="Bridgeworks",
                kind="board_game",
                metadata={"generation": 1},
                idempotency_key="candidate:bridgeworks",
            )
        with self.assertRaises(StateConflictError):
            self.store.transition_candidate(
                candidate.id, "published", expected_state="proposed"
            )
        with self.assertRaises(StateConflictError):
            self.store.transition_candidate(
                candidate.id, "published", expected_version=1
            )
        with self.assertRaises(ValueError):
            self.store.transition_candidate(candidate.id, "made_up")

        updated = self.store.update_candidate(
            candidate.id,
            {"rules": ["place", "move", "score"]},
            title="Bridgeworks II",
            expected_version=2,
        )
        self.assertEqual(updated.version, 3)
        self.assertEqual(updated.title, "Bridgeworks II")

    def test_candidate_artifacts_are_exact_immutable_task_bound_snapshots(self) -> None:
        candidate = self.store.create_candidate(
            {"rules": ["move"]},
            kind="board_game",
            candidate_id="artifact-candidate",
        )
        task = self.store.enqueue_task(
            "physical.cad",
            {"candidate_version": candidate.version, "role": "cad_builder"},
            idempotency_key="artifact-task",
            candidate_id=candidate.id,
        )
        leased = self.store.lease_task("cad-worker")
        completed = self.store.complete_task(
            task.id,
            "cad-worker",
            leased.lease_token,
            {"artifact": "pawn.step", "watertight": True},
        )
        content = {
            "files": [{"name": "pawn.step", "sha256": "b" * 64}],
            "watertight": True,
        }
        artifact = self.store.record_candidate_artifact(
            candidate.id,
            completed.id,
            completed.kind,
            candidate.version,
            completed.output_sha256,
            content,
            artifact_id="artifact-one",
        )
        event_count = self.store.stats()["counts"]["events"]

        self.assertEqual(artifact.content, content)
        self.assertEqual(artifact.content_sha256, DurableStore.sha256_json(content))
        self.assertEqual(
            self.store.get_candidate_artifact("artifact-one"), artifact
        )
        self.assertEqual(
            self.store.get_candidate_artifact_for_task(task.id), artifact
        )
        self.assertEqual(
            self.store.list_candidate_artifacts(
                candidate_id=candidate.id,
                task_id=task.id,
                action="physical.cad",
                candidate_version=1,
                output_sha256=completed.output_sha256,
                content_sha256=artifact.content_sha256,
            ),
            [artifact],
        )

        # A later candidate transition does not erase the task's exact v1
        # snapshot, and an exact retry does not append another row or event.
        self.store.transition_candidate(candidate.id, "physical_ready")
        replay = self.store.record_candidate_artifact(
            candidate.id,
            completed.id,
            completed.kind,
            1,
            completed.output_sha256,
            content,
            artifact_id="artifact-one",
        )
        self.assertEqual(replay, artifact)
        self.assertEqual(self.store.stats()["counts"]["candidate_artifacts"], 1)
        self.assertEqual(self.store.stats()["counts"]["events"], event_count + 1)

        with self.assertRaises(IdempotencyConflictError):
            self.store.record_candidate_artifact(
                candidate.id,
                completed.id,
                completed.kind,
                1,
                completed.output_sha256,
                {"files": []},
            )
        with self.assertRaises(StateConflictError):
            self.store.record_candidate_artifact(
                candidate.id,
                completed.id,
                "physical.dfm",
                1,
                completed.output_sha256,
                content,
            )
        with self.assertRaises(StateConflictError):
            self.store.record_candidate_artifact(
                candidate.id,
                completed.id,
                completed.kind,
                2,
                completed.output_sha256,
                content,
            )
        with self.assertRaises(StateConflictError):
            self.store.record_candidate_artifact(
                candidate.id,
                completed.id,
                completed.kind,
                1,
                "0" * 64,
                content,
            )
        with self.assertRaises(ValueError):
            self.store.record_candidate_artifact(
                candidate.id,
                completed.id,
                completed.kind,
                1,
                completed.output_sha256,
                content,
                content_sha256="0" * 64,
            )

        attacker = sqlite3.connect(self.db_path)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                attacker.execute(
                    "UPDATE candidate_artifacts SET content_json = '{}' WHERE id = ?",
                    (artifact.id,),
                )
            attacker.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                attacker.execute(
                    "DELETE FROM candidate_artifacts WHERE id = ?", (artifact.id,)
                )
            attacker.rollback()
        finally:
            attacker.close()

    def test_derived_result_backlog_has_no_oldest_thousand_row_window(self) -> None:
        now = self.clock.value
        input_sha = hashlib.sha256(b"input").hexdigest()
        rows = []
        for index in range(1_005):
            output_sha = hashlib.sha256(f"output:{index}".encode()).hexdigest()
            rows.append(
                (
                    f"derived-task-{index:04d}",
                    f"derived-key-{index:04d}",
                    '{"input_sha256":"' + input_sha + '"}',
                    input_sha,
                    output_sha,
                    now + index,
                    now + index,
                    now + index,
                    '{"ok":true}',
                )
            )
        with self.store._write() as connection:
            connection.executemany(
                """
                INSERT INTO tasks(
                    id, idempotency_key, kind, payload_json, run_id, candidate_id,
                    input_sha256, output_sha256, state, priority, available_at,
                    created_at, updated_at, attempt_count, max_attempts,
                    lease_owner, lease_token, lease_attempt_id, lease_expires_at,
                    last_error_stage, last_error_code, last_error_message, result_json
                ) VALUES (?, ?, 'derived.test', ?, NULL, NULL, ?, ?, 'succeeded', 0,
                          ?, ?, ?, 0, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, ?)
                """,
                rows,
            )

        backlog = self.store.list_unapplied_succeeded_tasks()
        self.assertEqual(len(backlog), 1_005)
        self.assertEqual(backlog[-1].id, "derived-task-1004")
        self.assertEqual(
            len(self.store.list_unapplied_succeeded_tasks(limit=7)), 7
        )

        task = backlog[-1]
        marker = self.store.mark_task_derived_applied(
            task.id, task.output_sha256, now=now + 2_000
        )
        event_count = self.store.stats()["counts"]["events"]
        replay = self.store.mark_task_derived_applied(
            task.id, task.output_sha256, now=now + 3_000
        )
        self.assertEqual(replay, marker)
        self.assertEqual(replay.applied_at, now + 2_000)
        self.assertEqual(self.store.get_task_derived_application(task.id), marker)
        self.assertEqual(len(self.store.list_unapplied_succeeded_tasks()), 1_004)
        self.assertNotIn(
            task.id,
            {pending.id for pending in self.store.list_unapplied_succeeded_tasks()},
        )
        self.assertEqual(self.store.stats()["counts"]["events"], event_count)
        self.assertEqual(self.store.stats()["counts"]["task_derived_applications"], 1)

        attacker = sqlite3.connect(self.db_path)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                attacker.execute(
                    "UPDATE task_derived_applications SET applied_at = 0 WHERE task_id = ?",
                    (task.id,),
                )
            attacker.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                attacker.execute(
                    "DELETE FROM task_derived_applications WHERE task_id = ?",
                    (task.id,),
                )
            attacker.rollback()
        finally:
            attacker.close()

        queued = self.enqueue("not-succeeded")
        with self.assertRaises(StateConflictError):
            self.store.mark_task_derived_applied(queued.id, "0" * 64)
        with self.assertRaises(StateConflictError):
            self.store.mark_task_derived_applied(task.id, "0" * 64)

    def test_versioned_json_state_uses_strict_compare_and_set(self) -> None:
        self.assertIsNone(self.store.get_state("learner.bandit"))
        created = self.store.put_state(
            "learner.bandit", {"counts": {"cad": 1}, "reward": 0.5}, None
        )
        self.assertEqual(created.version, 1)
        self.assertEqual(self.store.get_state("learner.bandit"), created)

        # Canonical object-key ordering is the same durable value and is a no-op.
        no_op = self.store.put_state(
            "learner.bandit", {"reward": 0.5, "counts": {"cad": 1}}, 1
        )
        self.assertEqual(no_op, created)

        other = DurableStore(self.db_path, clock=self.clock)
        try:
            stale = other.get_state("learner.bandit")
            updated = self.store.put_state(
                "learner.bandit", {"counts": {"cad": 2}, "reward": 0.7}, 1
            )
            self.assertEqual(updated.version, 2)
            self.assertEqual(updated.created_at, created.created_at)
            with self.assertRaises(StateConflictError):
                other.put_state(
                    "learner.bandit", {"counts": {"cad": 3}}, stale.version
                )
        finally:
            other.close()

        with self.assertRaises(StateConflictError):
            self.store.put_state("learner.bandit", {}, None)
        with self.assertRaises(StateConflictError):
            self.store.put_state("missing", {}, 1)
        with self.assertRaises(ValueError):
            self.store.put_state("learner.bandit", {}, 0)
        self.assertEqual(self.store.stats()["counts"]["versioned_state"], 1)

    def test_evaluations_and_experiences_are_durable_and_queryable(self) -> None:
        candidate = self.store.create_candidate(
            {"rules": []}, kind="board_game", candidate_id="candidate-eval"
        )
        evaluation = self.store.add_evaluation(
            candidate.id,
            "rules-engine-v2",
            score=0.82,
            verdict="pass",
            metrics={"terminates": True},
            notes="deterministic replay passed",
            idempotency_key="evaluation:one",
        )
        replay = self.store.add_evaluation(
            candidate.id,
            "rules-engine-v2",
            score=0.82,
            verdict="pass",
            metrics={"terminates": True},
            notes="deterministic replay passed",
            idempotency_key="evaluation:one",
        )
        self.assertEqual(replay.id, evaluation.id)
        self.assertEqual(
            self.store.list_evaluations(candidate_id=candidate.id)[0].metrics,
            {"terminates": True},
        )

        experience = self.store.add_experience(
            "mechanic_signal",
            {"mechanic": "shared incentives"},
            reward=0.7,
            candidate_id=candidate.id,
            idempotency_key="experience:one",
        )
        self.assertEqual(
            self.store.list_experiences(kind="mechanic_signal")[0].id,
            experience.id,
        )
        self.assertEqual(self.store.stats()["counts"]["evaluations"], 1)
        self.assertEqual(self.store.stats()["counts"]["experiences"], 1)
        with self.assertRaises(NotFoundError):
            self.store.add_experience(
                "bad", {}, candidate_id="missing", idempotency_key="missing-ref"
            )

    def test_publication_intent_is_idempotent_and_reconcilable(self) -> None:
        candidate = self.store.create_candidate(
            {"name": "Bridgeworks"}, candidate_id="publish-candidate"
        )
        request = {"candidate_id": candidate.id, "html": "<main>...</main>"}
        request_hash = DurableStore.sha256_json(request)
        prepared = self.store.prepare_publication(
            "factory",
            "factory:bridgeworks:v1",
            request_hash,
            request,
            candidate_id=candidate.id,
            slug="bridgeworks",
        )
        replay = self.store.prepare_publication(
            "factory",
            "factory:bridgeworks:v1",
            request_hash,
            request,
            candidate_id=candidate.id,
            slug="bridgeworks",
        )
        self.assertEqual(replay.id, prepared.id)
        self.assertEqual(replay.state, "prepared")
        self.assertEqual(replay.status, "draft")
        self.assertEqual(
            self.store.get_publication_intent("factory", "factory:bridgeworks:v1").id,
            prepared.id,
        )
        with self.assertRaises(IdempotencyConflictError):
            self.store.prepare_publication(
                "factory",
                "factory:bridgeworks:v1",
                hashlib.sha256(b"different request").hexdigest(),
                request,
                candidate_id=candidate.id,
            )

        in_flight = self.store.transition_publication(
            prepared.id,
            "in_flight",
            expected_state="prepared",
            status="publishing",
        )
        self.assertEqual(in_flight.status, "publishing")
        ambiguous = self.store.update_publication_intent(
            "factory",
            "factory:bridgeworks:v1",
            "ambiguous",
            expected_state="in_flight",
            last_error="connection ended before receipt",
        )
        self.assertEqual(ambiguous.state, "ambiguous")
        self.assertEqual(ambiguous.status, "publishing")
        confirmed = self.store.transition_publication(
            prepared.id,
            "confirmed",
            expected_state="ambiguous",
            remote_design_id="design-123",
            history_id="history-456",
            project_url="https://factory.example/projects/bridgeworks",
            status="published",
            response={"published": True},
        )
        self.assertEqual(confirmed.remote_design_id, "design-123")
        self.assertEqual(confirmed.history_id, "history-456")
        self.assertEqual(confirmed.status, "published")
        self.assertEqual(confirmed.response, {"published": True})
        self.assertEqual(
            self.store.list_publications(state="confirmed")[0].id, prepared.id
        )
        with self.assertRaises(ValueError):
            self.store.transition_publication(prepared.id, "confirmed", status="private")
        with self.assertRaises(StateConflictError):
            self.store.transition_publication(
                prepared.id, "failed", expected_state="prepared"
            )

    def test_public_send_claim_atomically_fences_candidate_retraction(self) -> None:
        candidate = self.store.create_candidate(
            {"name": "River Council"},
            candidate_id="atomic-publish-candidate",
            state="publish_ready",
        )
        request = {
            "candidate_id": candidate.id,
            "candidate_version": candidate.version,
            "candidate_content_sha256": self.store.sha256_json(candidate.content),
        }
        prepared = self.store.prepare_publication(
            "vibe_pipeline",
            "atomic-publish-operation",
            self.store.sha256_json(request),
            request,
            candidate_id=candidate.id,
        )
        ready = self.store.transition_publication(
            prepared.id,
            "in_flight",
            expected_state="prepared",
            response={"stage": "publish_ready"},
        )
        sending = self.store.claim_candidate_publication_send(
            ready.id,
            candidate_id=candidate.id,
            candidate_version=candidate.version,
            candidate_content_sha256=self.store.sha256_json(candidate.content),
            response={"stage": "publish_sending"},
            effect_payload={"history_id": "history-1"},
        )
        self.assertEqual(sending.response["stage"], "publish_sending")
        with self.assertRaisesRegex(StateConflictError, "public-send fence"):
            self.store.transition_candidate(
                candidate.id,
                "rework",
                expected_state="publish_ready",
                expected_version=candidate.version,
            )
        with self.assertRaisesRegex(StateConflictError, "public-send fence"):
            self.store.update_candidate(
                candidate.id,
                {"name": "Retracted"},
                expected_version=candidate.version,
            )

        self.store.finish_candidate_publication_send(
            ready.id,
            candidate_id=candidate.id,
            candidate_version=candidate.version,
            status="failed",
        )
        reworked = self.store.transition_candidate(
            candidate.id,
            "rework",
            expected_state="publish_ready",
            expected_version=candidate.version,
        )
        self.assertEqual(reworked.state, "rework")

    def test_physical_send_claim_atomically_fences_candidate_rework(self) -> None:
        candidate = self.store.create_candidate(
            {"name": "River Council"},
            candidate_id="atomic-physical-candidate",
            state="human_validated",
        )
        content_sha256 = self.store.sha256_json(candidate.content)
        effect_key = "alice.effect:task:physical.cad:" + "a" * 64
        identity = {
            "schema_version": 1,
            "task_id": "cad-task-1",
            "task_input_sha256": "a" * 64,
            "action": "physical.cad",
            "candidate_id": candidate.id,
            "candidate_state": candidate.state,
            "candidate_version": candidate.version,
            "candidate_content_sha256": content_sha256,
            "operation_key": "alice:physical-effect:v1:physical.cad:" + "a" * 64,
        }
        claimed = self.store.claim_candidate_physical_effect_send(
            effect_key,
            candidate_id=candidate.id,
            candidate_state=candidate.state,
            candidate_version=candidate.version,
            candidate_content_sha256=content_sha256,
            action="physical.cad",
            identity=identity,
            send_attempt_id="attempt-1",
        )
        self.assertEqual(claimed.value["status"], "sending")
        with self.assertRaisesRegex(StateConflictError, "physical-effect fence"):
            self.store.transition_candidate(
                candidate.id,
                "rework",
                expected_state="human_validated",
                expected_version=candidate.version,
            )
        with self.assertRaisesRegex(StateConflictError, "physical-effect fence"):
            self.store.update_candidate(
                candidate.id,
                {"name": "retracted"},
                expected_version=candidate.version,
            )

    def test_physical_claim_loses_atomically_to_prior_rework(self) -> None:
        candidate = self.store.create_candidate(
            {"name": "River Council"},
            candidate_id="reworked-before-physical",
            state="human_validated",
        )
        old_hash = self.store.sha256_json(candidate.content)
        self.store.transition_candidate(
            candidate.id,
            "rework",
            expected_state="human_validated",
            expected_version=candidate.version,
        )
        identity = {
            "schema_version": 1,
            "task_id": "cad-task-old",
            "task_input_sha256": "b" * 64,
            "action": "physical.cad",
            "candidate_id": candidate.id,
            "candidate_state": "human_validated",
            "candidate_version": candidate.version,
            "candidate_content_sha256": old_hash,
            "operation_key": "alice:physical-effect:v1:physical.cad:" + "b" * 64,
        }
        with self.assertRaisesRegex(StateConflictError, "retracted or revised"):
            self.store.claim_candidate_physical_effect_send(
                "alice.effect:task:physical.cad:" + "b" * 64,
                candidate_id=candidate.id,
                candidate_state="human_validated",
                candidate_version=candidate.version,
                candidate_content_sha256=old_hash,
                action="physical.cad",
                identity=identity,
                send_attempt_id="attempt-old",
            )

    def test_remote_manufacturing_job_has_one_global_order_binding(self) -> None:
        first = self.store.bind_manufacturing_job(
            "remote-job-42",
            order_id="order-1",
            operation_key="operation-1",
            intent_sha256="a" * 64,
            task_input_sha256="b" * 64,
            receipt_sha256="c" * 64,
        )
        replay = self.store.bind_manufacturing_job(
            "remote-job-42",
            order_id="order-1",
            operation_key="operation-1",
            intent_sha256="a" * 64,
            task_input_sha256="b" * 64,
            receipt_sha256="c" * 64,
        )
        self.assertEqual(first, replay)
        with self.assertRaisesRegex(StateConflictError, "different paid-order"):
            self.store.bind_manufacturing_job(
                "remote-job-42",
                order_id="order-2",
                operation_key="operation-2",
                intent_sha256="d" * 64,
                task_input_sha256="e" * 64,
                receipt_sha256="f" * 64,
            )

    def test_event_chain_is_append_only_and_detects_payload_tampering(self) -> None:
        first = self.store.append_event("agent.started", {"worker": "one"})
        second = self.store.append_event("agent.observed", {"value": 7})
        third = self.store.append_event("agent.stopped", {"reason": "done"})

        self.assertEqual([first.seq, second.seq, third.seq], [1, 2, 3])
        self.assertEqual(first.prev_hash, "0" * 64)
        self.assertEqual(second.prev_hash, first.event_hash)
        report = self.store.verify_event_chain(
            expected_head=third.event_hash, expected_count=3
        )
        self.assertTrue(report.valid)
        self.assertEqual(report.events_checked, 3)

        attacker = sqlite3.connect(self.db_path)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                attacker.execute(
                    "UPDATE events SET payload_json = ? WHERE seq = 2", ('{"value":8}',)
                )
            attacker.rollback()
            attacker.execute("DROP TRIGGER events_forbid_update")
            attacker.execute(
                "UPDATE events SET payload_json = ? WHERE seq = 2", ('{"value":8}',)
            )
            attacker.commit()
        finally:
            attacker.close()

        report = self.store.verify_event_chain()
        self.assertFalse(report.valid)
        self.assertEqual(report.error_seq, 2)
        self.assertIn("event hash", report.error)
        with self.assertRaises(EventChainError):
            self.store.assert_event_chain()

    def test_event_chain_detects_truncation_via_chain_head(self) -> None:
        self.store.append_event("one", {})
        self.store.append_event("two", {})
        attacker = sqlite3.connect(self.db_path)
        try:
            attacker.execute("DROP TRIGGER events_forbid_delete")
            attacker.execute("DELETE FROM events WHERE seq = 2")
            attacker.commit()
        finally:
            attacker.close()
        report = self.store.verify_event_chain()
        self.assertFalse(report.valid)
        self.assertIn("stored chain head", report.error)

    def test_query_helpers_and_validation(self) -> None:
        self.enqueue("low", priority=1)
        self.enqueue("high", priority=10)
        first = self.store.lease_task("worker", kinds=["research"])
        self.assertEqual(first.idempotency_key, "high")
        self.assertEqual(len(self.store.list_tasks(state="queued")), 1)
        self.assertEqual(self.store.task_counts()["leased"], 1)
        self.assertEqual(self.store.list_events(after_seq=1)[0].seq, 2)
        self.assertEqual(self.store.checkpoint_wal()[0], 0)
        with self.assertRaises(ValueError):
            self.store.list_tasks(limit=0)
        with self.assertRaises(ValueError):
            self.store.list_candidates(state="not-real")
        with self.assertRaises(NotFoundError):
            self.store.get_task("missing")


if __name__ == "__main__":
    unittest.main()
