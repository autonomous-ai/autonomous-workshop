import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from inventor_workshop.batch import (
    BatchPlan,
    BatchPlanStore,
    BatchRequest,
    load_or_create_batch_manager_identity,
)
from inventor_workshop.errors import WorkshopError
from inventor_workshop.handoff import PublicationPolicy
from inventor_workshop.jobs import Need, WaitingFor
from inventor_workshop.cli import (
    _BatchProcessSupervisor,
    _batch_status_payload,
    _execute_batch,
    _print_batch_receipt,
    _run_batch_resume_child,
    _save_manager_assignment,
    main,
    parser,
)
from inventor_workshop.manager import discover_inventor_catalog
from inventor_workshop.pending_wish import PendingWishStore
from tests import test_cli as cli_fixtures


class BatchCliTest(unittest.TestCase):
    @staticmethod
    def catalog(root: Path):
        cli_fixtures.CliTest.inventor_identity(root / "inventors" / "mira", "mira")
        return discover_inventor_catalog(root)

    def test_submit_stages_every_exact_wish_before_any_worker_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = self.catalog(root)
            source = root / "wishes.txt"
            source.write_text(
                "A patient clockwork moon\nA lighthouse game for two rivals\n",
                encoding="utf-8",
            )
            receipts = []
            for _ in range(2):
                output = StringIO()
                with mock.patch(
                    "inventor_workshop.cli._run_batch_resume_child"
                ) as worker, redirect_stdout(output):
                    code = main(
                        (
                            "batch",
                            "submit",
                            str(source),
                            "--draft",
                            "--root",
                            str(root),
                            "--json",
                        )
                    )
                self.assertEqual(code, 0)
                worker.assert_not_called()
                receipts.append(json.loads(output.getvalue()))
            self.assertEqual(receipts[0], receipts[1])
            self.assertEqual(receipts[0]["count"], 2)
            self.assertEqual(receipts[0]["status"], "ready")
            plan = BatchPlanStore(catalog.collection).load(
                receipts[0]["batch_id"]
            )
            pending = PendingWishStore(catalog.collection)
            self.assertEqual(
                tuple(
                    pending.load(item.wish.product_id).record_sha256
                    for item in plan.items
                ),
                tuple(item.pending_wish_sha256 for item in plan.items),
            )

    def test_match_wait_need_is_durable_in_batch_status_and_plain_guidance(self):
        class UnavailableSemanticManager:
            judge_identity = "fixture-batch-semantic-manager"
            judge_version = "1.0.0"
            judge_config_sha256 = "a" * 64

            def retrieve(self, context):
                del context
                raise WaitingFor(
                    Need(
                        "wish",
                        "semantic-manager",
                        "The exact semantic Manager is unavailable.",
                        "Reconnect it, then resume this exact Wish.",
                    )
                )

            def judge(self, context):  # pragma: no cover - retrieve waits
                del context
                raise AssertionError("judge must not run")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.catalog(root)
            source = root / "wishes.txt"
            source.write_text("A patient mechanical moon\n", encoding="utf-8")
            submitted = StringIO()
            with redirect_stdout(submitted):
                self.assertEqual(
                    main(
                        (
                            "batch",
                            "submit",
                            str(source),
                            "--draft",
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            staged = json.loads(submitted.getvalue())
            product_id = staged["items"][0]["product_id"]

            with mock.patch(
                "inventor_workshop.cli.CodexSemanticManager",
                return_value=UnavailableSemanticManager(),
            ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(
                        (
                            "resume",
                            product_id,
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )

            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    main(
                        (
                            "batch",
                            "status",
                            staged["batch_id"],
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            receipt = json.loads(output.getvalue())
            item = receipt["items"][0]["status"]
            self.assertEqual(receipt["status"], "needs-attention")
            self.assertEqual(item["status"], "waiting")
            self.assertEqual(item["needs"][0]["capability"], "semantic-manager")
            self.assertEqual(item["match_attempt"]["status"], "waiting")

            plain = StringIO()
            with redirect_stdout(plain):
                _print_batch_receipt(receipt)
            self.assertIn("The exact semantic Manager is unavailable.", plain.getvalue())
            self.assertIn("Reconnect it, then resume this exact Wish.", plain.getvalue())

    def test_exact_submission_reuses_retained_manager_plan_instead_of_duplicating(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            base = home / "bundled-catalogs"
            old_root = base / ("a" * 64)
            current_root = base / ("b" * 64)
            old_catalog = self.catalog(old_root)
            current_catalog = self.catalog(current_root)
            identity = load_or_create_batch_manager_identity(home)
            requests = (
                BatchRequest("line-0001", "A retained patient moon", "draft"),
            )
            old_plan = BatchPlan.from_requests(
                old_catalog,
                requests,
                playtest_rounds=4,
                manager_identity=identity,
            )
            BatchPlanStore(old_catalog.collection).stage(old_plan)
            source = current_root / "wishes.txt"
            source.write_text("A retained patient moon\n", encoding="utf-8")

            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli._catalog_roots",
                return_value=(current_root.resolve(), old_root.resolve()),
            ), redirect_stdout(output):
                code = main(
                    (
                        "batch",
                        "submit",
                        str(source),
                        "--draft",
                        "--json",
                    )
                )

            receipt = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(receipt["batch_id"], old_plan.batch_id)
            self.assertEqual(receipt["catalog_root"], str(old_root.resolve()))
            self.assertIsNone(
                BatchPlanStore(current_catalog.collection).load(
                    old_plan.batch_id, allow_missing=True
                )
            )

    def test_exact_resubmission_rejects_a_retained_publication_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            catalog = self.catalog(root)
            identity = load_or_create_batch_manager_identity(root)
            requests = (
                BatchRequest("line-0001", "A private patient moon", "draft"),
            )
            proposed = BatchPlan.from_requests(
                catalog,
                requests,
                playtest_rounds=4,
                manager_identity=identity,
            )
            conflicting = BatchPlan.create(
                proposed.batch_id,
                catalog,
                (
                    (
                        proposed.items[0].wish,
                        PublicationPolicy.for_wish(publish=True),
                    ),
                ),
                playtest_rounds=proposed.playtest_rounds,
                manager_scope_id=proposed.manager_scope_id,
                submission_sha256=proposed.submission_sha256,
            )
            BatchPlanStore(catalog.collection).stage(conflicting)
            source = root / "wishes.txt"
            source.write_text("A private patient moon\n", encoding="utf-8")

            stderr = StringIO()
            with redirect_stderr(stderr):
                code = main(
                    (
                        "batch",
                        "submit",
                        str(source),
                        "--draft",
                        "--root",
                        str(root),
                    )
                )

            self.assertEqual(code, 2)
            self.assertIn("publication policies", stderr.getvalue())

    def test_resume_uses_bounded_parallel_workers_once_and_keeps_output_ordered(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.catalog(root)
            source = root / "wishes.txt"
            source.write_text("first exact Wish\nsecond exact Wish\nthird exact Wish\n", encoding="utf-8")
            staged = StringIO()
            with redirect_stdout(staged):
                self.assertEqual(
                    main(
                        (
                            "batch",
                            "submit",
                            str(source),
                            "--draft",
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            batch_id = json.loads(staged.getvalue())["batch_id"]
            active = 0
            maximum = 0
            lock = threading.Lock()
            calls = []

            def worker(product_id, selected_root):
                nonlocal active, maximum
                self.assertEqual(selected_root, root.resolve())
                with lock:
                    calls.append(product_id)
                    active += 1
                    maximum = max(maximum, active)
                time.sleep(0.03)
                with lock:
                    active -= 1
                return subprocess.CompletedProcess(
                    ["fixture"], 0, stdout="{}", stderr=""
                )

            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli._BatchProcessSupervisor.run",
                side_effect=worker,
            ), redirect_stdout(output):
                code = main(
                    (
                        "batch",
                        "resume",
                        batch_id,
                        "--root",
                        str(root),
                        "--concurrency",
                        "2",
                        "--strict",
                        "--json",
                    )
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(len(calls), 3)
            self.assertLessEqual(maximum, 2)
            self.assertGreaterEqual(maximum, 2)
            self.assertEqual(
                [item["position"] for item in receipt["items"]], [1, 2, 3]
            )
            self.assertTrue(
                all(item["launch"]["status"] == "succeeded" for item in receipt["items"])
            )

    def test_mass_visibility_is_required_and_resume_has_no_policy_switch(self):
        command = parser()
        with self.assertRaises(SystemExit):
            command.parse_args(("batch", "submit", "wishes.txt"))
        with self.assertRaises(SystemExit):
            command.parse_args(
                ("batch", "resume", "batch-one", "--publish")
            )

    def test_worker_invokes_the_installed_module_with_the_exact_wish_and_root(self):
        root = Path("/tmp/workshop-batch-root")
        completed = subprocess.CompletedProcess(["fixture"], 0, "{}", "")
        with mock.patch(
            "inventor_workshop.cli._managed_child_run", return_value=completed
        ) as run:
            self.assertIs(
                _run_batch_resume_child("wish-exact", root), completed
            )
        command = run.call_args.args[0]
        self.assertEqual(
            command,
            (
                mock.ANY,
                "-m",
                "inventor_workshop",
                "resume",
                "wish-exact",
                "--root",
                str(root),
                "--json",
            ),
        )

    def test_concurrent_supervisor_fails_fast_and_never_queues_a_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = self.catalog(root)
            source = root / "wishes.txt"
            source.write_text("A patient mechanical moon\n", encoding="utf-8")
            staged = StringIO()
            with redirect_stdout(staged):
                self.assertEqual(
                    main(
                        (
                            "batch",
                            "submit",
                            str(source),
                            "--draft",
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            plan = BatchPlanStore(catalog.collection).load(
                json.loads(staged.getvalue())["batch_id"]
            )
            store = BatchPlanStore(catalog.collection)
            entered = threading.Event()
            release = threading.Event()
            calls = []

            def worker(product_id, unused_root):
                del unused_root
                calls.append(product_id)
                entered.set()
                release.wait(5)
                return subprocess.CompletedProcess(["fixture"], 0, "", "")

            first = threading.Thread(
                target=lambda: _execute_batch(
                    plan, root.resolve(), store, concurrency=1, runner=worker
                )
            )
            first.start()
            self.assertTrue(entered.wait(3))
            started = time.monotonic()
            with self.assertRaisesRegex(WorkshopError, "already supervising"):
                _execute_batch(
                    plan, root.resolve(), store, concurrency=1, runner=worker
                )
            self.assertLess(time.monotonic() - started, 1)
            release.set()
            first.join(5)
            self.assertFalse(first.is_alive())
            self.assertEqual(len(calls), 1)

    def test_catalog_drift_blocks_only_unmatched_items(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = self.catalog(root)
            source = root / "wishes.txt"
            source.write_text(
                "First patient moon\nSecond patient moon\n", encoding="utf-8"
            )
            staged = StringIO()
            with redirect_stdout(staged):
                self.assertEqual(
                    main(
                        (
                            "batch",
                            "submit",
                            str(source),
                            "--draft",
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            plan = BatchPlanStore(catalog.collection).load(
                json.loads(staged.getvalue())["batch_id"]
            )
            assignment = cli_fixtures.CliTest.resume_assignment(
                root / "inventors" / "mira",
                "mira",
                plan.items[0].wish,
            )
            assignment.publication_policy = plan.items[0].publication_policy
            _save_manager_assignment(assignment)
            cli_fixtures.CliTest.inventor_identity(
                root / "inventors" / "taro", "taro"
            )
            calls = []

            def worker(product_id, unused_root):
                del unused_root
                calls.append(product_id)
                return subprocess.CompletedProcess(["fixture"], 0, "", "")

            receipt = _execute_batch(
                plan,
                root.resolve(),
                BatchPlanStore(catalog.collection),
                concurrency=2,
                runner=worker,
            )

            self.assertEqual(calls, [plan.items[0].wish.product_id])
            self.assertEqual(receipt["status"], "needs-attention")
            self.assertEqual(
                receipt["items"][1]["status"]["resume"]["kind"],
                "catalog-drift",
            )

    def test_nonzero_launch_is_actionable_and_public_requires_a_live_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = self.catalog(root)
            source = root / "wishes.txt"
            source.write_text("A public patient moon\n", encoding="utf-8")
            staged = StringIO()
            with redirect_stdout(staged):
                self.assertEqual(
                    main(
                        (
                            "batch",
                            "submit",
                            str(source),
                            "--publish",
                            "--root",
                            str(root),
                            "--json",
                        )
                    ),
                    0,
                )
            plan = BatchPlanStore(catalog.collection).load(
                json.loads(staged.getvalue())["batch_id"]
            )
            store = BatchPlanStore(catalog.collection)
            failed = _execute_batch(
                plan,
                root.resolve(),
                store,
                concurrency=1,
                runner=lambda *unused: subprocess.CompletedProcess(
                    ["fixture"], 2, "", "provider detail must stay private"
                ),
            )
            launch = failed["items"][0]["launch"]
            self.assertEqual(failed["status"], "needs-attention")
            self.assertEqual(launch["status"], "failed")
            self.assertIn("workshop resume", launch["next"])
            self.assertNotIn("provider detail", json.dumps(failed))
            output = StringIO()
            with redirect_stdout(output):
                _print_batch_receipt(failed)
            self.assertIn("Launch: failed", output.getvalue())
            self.assertIn("Next: workshop resume", output.getvalue())

            base_status = {
                "product_id": plan.items[0].wish.product_id,
                "wish": plan.items[0].wish.to_dict(),
                "status": "delivered",
                "job": "deliver",
                "needs": [],
                "publication_policy": plan.items[0].publication_policy.to_dict(),
                "resume": {
                    "status": "available",
                    "kind": "factory-page",
                    "command": "workshop resume exact",
                },
            }
            with mock.patch(
                "inventor_workshop.cli._batch_item_status",
                return_value={**base_status, "page": {"status": "draft"}},
            ):
                self.assertEqual(
                    _batch_status_payload(plan, root.resolve())["status"], "ready"
                )
            with mock.patch(
                "inventor_workshop.cli._batch_item_status",
                return_value={**base_status, "page": {"status": "public"}},
            ):
                self.assertEqual(
                    _batch_status_payload(plan, root.resolve())["status"],
                    "complete",
                )

    def test_process_supervisor_cancels_its_owned_process_group(self):
        supervisor = _BatchProcessSupervisor()
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            start_new_session=True,
        )
        with supervisor._lock:
            supervisor._processes[process.pid] = process
        try:
            supervisor.cancel()
            process.wait(timeout=5)
            self.assertNotEqual(process.returncode, 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)

    def test_cancelled_supervisor_never_spawns_a_queued_worker(self):
        supervisor = _BatchProcessSupervisor()
        supervisor.cancel()
        with mock.patch("inventor_workshop.cli.subprocess.Popen") as popen:
            with self.assertRaisesRegex(WorkshopError, "already cancelled"):
                supervisor.run("wish-queued", Path("/tmp"))
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
