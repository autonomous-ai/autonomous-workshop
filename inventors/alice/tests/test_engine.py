import tempfile
import time
import unittest
import hashlib
import json
from pathlib import Path

from inventor_workshop import load_taste
from inventor_workshop.errors import ManifestError

from alice.adapters import AdapterError, AdapterReceipt, adapter_input_sha256
from alice.config import load_config
from alice.engine import AliceEngine, EngineError
from alice.fulfillment import (
    build_manufacturing_spec_from_manifest,
    canonical_sha256 as fulfillment_sha256,
    fulfillment_intent_from_payload,
    print_job_receipt_from_payload,
)
from alice.providers import AgentResponse, FixtureAgentProvider
from alice.store import DurableStore


class SlowAgentProvider:
    def run(self, request):
        time.sleep(0.12)
        return AgentResponse(
            request_id=request.request_id,
            provider_run_id="slow-provider-run",
            content={"summary": "completed after multiple lease renewals"},
            confidence=0.8,
            elapsed_seconds=0.12,
        )


class CapturingAgentProvider:
    def __init__(self):
        self.requests = []

    def run(self, request):
        self.requests.append(request)
        return AgentResponse(
            request_id=request.request_id,
            provider_run_id="captured-provider-run",
            content={"summary": "captured"},
            confidence=0.8,
        )


class TasteMutatingProvider(CapturingAgentProvider):
    def __init__(self, taste_path: Path):
        super().__init__()
        self.taste_path = taste_path

    def run(self, request):
        response = super().run(request)
        self.taste_path.write_text(
            "---\n"
            "name: Alice\n"
            "description: Invents tactile tabletop classics with strong table presence.\n"
            "---\n\n"
            "# Mutated taste\n",
            encoding="utf-8",
        )
        return response


class RecordingAdapter:
    def __init__(self):
        self.calls = []

    def invoke(self, operation, payload):
        self.calls.append((operation, payload))
        return AdapterReceipt(
            adapter="recording",
            run_id="recording-run",
            status="passed",
            evidence_class="publishing_pipeline",
            payload={"ok": True},
            input_sha256=adapter_input_sha256(operation, payload),
            elapsed_seconds=0.0,
        )


class WrongInputAdapter:
    def invoke(self, operation, payload):
        return AdapterReceipt(
            adapter="wrong-input",
            run_id="wrong-input-run",
            status="passed",
            evidence_class="deterministic",
            payload={},
            input_sha256="0" * 64,
        )


class SensitivePayloadAdapter:
    def invoke(self, operation, payload):
        return AdapterReceipt(
            adapter="library",
            run_id="sensitive-payload-run",
            status="passed",
            evidence_class="deterministic",
            payload={
                "source_id": "book-1",
                "access_basis": "licensed_ebook",
                "edition": "first",
                "citations": [],
                "claims": [{"customerName": "must-never-be-persisted"}],
                "unavailable_reason": None,
                "api_key": "must-never-be-persisted",
            },
            input_sha256=adapter_input_sha256(operation, payload),
        )


class SensitiveValueAdapter:
    def invoke(self, operation, payload):
        return AdapterReceipt(
            adapter="library",
            run_id="sensitive-value-run",
            status="passed",
            evidence_class="deterministic",
            payload={
                "source_id": "book-1",
                "access_basis": "licensed_ebook",
                "edition": "first",
                "citations": [],
                "claims": [],
                "unavailable_reason": None,
                "operator_note": (
                    "Bearer TEST0000; customer alice@example.test"
                ),
            },
            input_sha256=adapter_input_sha256(operation, payload),
        )


class FulfillmentLifecycleAdapter:
    def __init__(self, paid_order, *, fail_after_print_commit=False):
        self.paid_order = paid_order
        self.calls = []
        self.fail_after_print_commit = fail_after_print_commit
        self.print_commit_failure_raised = False

    def invoke(self, operation, payload):
        self.calls.append(operation)
        if operation == "orders.poll_paid":
            adapter = "delivery"
            evidence_class = "market"
            result = {"orders": [dict(self.paid_order)]}
        elif operation in {
            "orders.create_print_job",
            "orders.reconcile_print_job",
        }:
            adapter = "print_fulfillment"
            evidence_class = "manufacturing"
            intent = fulfillment_intent_from_payload(payload["fulfillment_intent"])
            result = {
                "print_jobs": [
                    {
                        "status": "created",
                        "order_id": intent.order_id,
                        "operation_key": intent.operation_key,
                        "intent_sha256": intent.intent_sha256,
                        "packet_hash": intent.publication.packet_hash,
                        "sku": intent.publication.sku,
                        "quantity": intent.quantity,
                        "job_id": f"print-{intent.order_id}",
                        "print_profile_sha256": (
                            intent.publication.print_profile_sha256
                        ),
                        "material_spec_sha256": (
                            intent.publication.material_spec_sha256
                        ),
                        "manufacturing_spec_sha256": (
                            intent.publication.manufacturing_spec_sha256
                        ),
                        "manufacturing_spec": intent.publication.manufacturing_spec,
                        "artifact_hashes": intent.publication.artifact_hash_map,
                    }
                ]
            }
            if (
                operation == "orders.create_print_job"
                and self.fail_after_print_commit
                and not self.print_commit_failure_raised
            ):
                self.print_commit_failure_raised = True
                raise AdapterError("simulated timeout after factory commit")
        elif operation in {"orders.qa_ship", "orders.reconcile_qa_ship"}:
            adapter = "print_fulfillment"
            evidence_class = "manufacturing"
            intent = fulfillment_intent_from_payload(payload["fulfillment_intent"])
            printed = print_job_receipt_from_payload(payload["print_job_receipt"])
            qa = {
                "receipt_source": "authenticated_external_qa_readback",
                "authority": "factory-qa.example",
                "run_id": f"qa-run-{intent.order_id}",
                "protocol_id": "final-inspection-v1",
                "result": "passed",
                "defect_evidence_sha256": "9" * 64,
                "order_id": intent.order_id,
                "operation_key": intent.operation_key,
                "intent_sha256": intent.intent_sha256,
                "packet_hash": intent.publication.packet_hash,
                "sku": intent.publication.sku,
                "quantity": intent.quantity,
                "job_id": printed.job_id,
                "print_receipt_sha256": printed.receipt_sha256,
                "print_profile_sha256": intent.publication.print_profile_sha256,
                "material_spec_sha256": intent.publication.material_spec_sha256,
                "manufacturing_spec_sha256": (
                    intent.publication.manufacturing_spec_sha256
                ),
                "manufacturing_spec": intent.publication.manufacturing_spec,
                "artifact_hashes": intent.publication.artifact_hash_map,
            }
            qa["receipt_sha256"] = DurableStore.sha256_json(qa)
            result = {
                "shipments": [
                    {
                        "status": "shipped",
                        "qa_passed": True,
                        "order_id": intent.order_id,
                        "operation_key": intent.operation_key,
                        "intent_sha256": intent.intent_sha256,
                        "packet_hash": intent.publication.packet_hash,
                        "sku": intent.publication.sku,
                        "quantity": intent.quantity,
                        "job_id": printed.job_id,
                        "print_receipt_sha256": printed.receipt_sha256,
                        "print_profile_sha256": (
                            intent.publication.print_profile_sha256
                        ),
                        "material_spec_sha256": (
                            intent.publication.material_spec_sha256
                        ),
                        "manufacturing_spec_sha256": (
                            intent.publication.manufacturing_spec_sha256
                        ),
                        "manufacturing_spec": intent.publication.manufacturing_spec,
                        "artifact_hashes": intent.publication.artifact_hash_map,
                        "qa": qa,
                        "tracking": {
                            "carrier": "UPS",
                            "tracking_number": f"TRACK-{intent.order_id}",
                            "tracking_url": (
                                f"https://tracking.example/{intent.order_id}"
                            ),
                        },
                    }
                ]
            }
        else:
            raise AssertionError(f"unexpected operation {operation!r}")
        return AdapterReceipt(
            adapter=adapter,
            run_id=f"run-{operation}",
            status="passed",
            evidence_class=evidence_class,
            payload=result,
            input_sha256=adapter_input_sha256(operation, payload),
        )


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.store = DurableStore(Path(self.directory.name) / "alice.sqlite3")
        self.config = load_config()
        self.engine = AliceEngine(
            self.store,
            FixtureAgentProvider(),
            self.config,
            worker_id="test-worker",
        )

    def tearDown(self) -> None:
        self.store.close()
        self.directory.cleanup()

    def test_schedule_only_enqueues_graph_roots(self) -> None:
        self.engine.schedule(now=1_000_000)
        library = self.store.list_tasks(run_id="loop:library:11", limit=100)
        self.assertEqual({task.kind for task in library}, {"library.discover"})

    def test_completion_enqueues_successor(self) -> None:
        self.engine.schedule(now=1_000_000)
        first = self.engine.work_once(now=1_000_000.1)
        self.assertIsNotNone(first)
        # Highest-priority order root may run first; run until its successor appears.
        for offset in range(1, 20):
            self.engine.work_once(now=1_000_000.1 + offset)
        tasks = self.store.list_tasks(limit=1_000)
        self.assertTrue(any(task.payload.get("depends_on") for task in tasks))

    def test_fixture_outputs_do_not_create_fake_candidate(self) -> None:
        for offset in range(80):
            self.engine.work_once(now=2_000_000 + offset)
        self.assertEqual(self.store.list_candidates(limit=100), [])
        self.assertTrue(self.store.verify_event_chain())

    def test_fixture_cannot_fake_order_or_manufacturing_effects(self) -> None:
        self.config["runtime"]["effect_mode"] = "live"
        self.store.enqueue_task(
            "orders.poll_paid",
            {
                "loop": "orders",
                "action": "orders.poll_paid",
                "role": "fulfillment_planner",
                "objective": "poll paid orders",
                "depends_on": [],
                "dependencies": {},
                "work_payload": {},
            },
            idempotency_key="forced-order-effect",
            priority=10_000,
            now=3_000_000,
        )
        result = self.engine.work_once(now=3_000_000)
        self.assertIsNotNone(result)
        self.assertEqual(result.kind, "orders.poll_paid")
        self.assertEqual(result.state, "failed")
        self.assertIn("requires configured", result.last_error_message)

    def test_order_loop_waits_for_both_commerce_adapters(self) -> None:
        self.engine.schedule(now=3_000_000)
        self.assertFalse(
            any(task.kind.startswith("orders.") for task in self.store.list_tasks(limit=1_000))
        )

    def test_fixture_cannot_impersonate_source_or_simulation_adapters(self) -> None:
        for index, (action, role, adapter) in enumerate(
            (
                ("library.read", "design_librarian", "library"),
                ("history.scan_traditional", "game_historian", "history"),
                ("simulation.optimizer", "player_optimizer", "digital_playtest"),
            )
        ):
            task = self.store.enqueue_task(
                action,
                {
                    "loop": "test",
                    "action": action,
                    "role": role,
                    "objective": "must use real adapter",
                    "depends_on": [],
                    "dependencies": {},
                    "work_payload": {},
                },
                idempotency_key=f"required-adapter-{index}",
            )
            with self.assertRaisesRegex(EngineError, adapter):
                self.engine._execute(task)

    def test_human_playtest_adapter_owns_kit_and_results(self) -> None:
        adapter = RecordingAdapter()
        engine = AliceEngine(
            self.store,
            FixtureAgentProvider(),
            self.config,
            adapters={"human_playtest": adapter},
        )

        self.assertIs(engine._adapter_for("human.prepare_blind_kit"), adapter)
        self.assertIs(engine._adapter_for("human.collect_blind_results"), adapter)

    def test_engine_rejects_adapter_receipt_bound_to_another_input(self) -> None:
        task = self.store.enqueue_task(
            "library.read",
            {
                "loop": "library",
                "action": "library.read",
                "role": "design_librarian",
                "objective": "read one source",
                "dependencies": {},
            },
            idempotency_key="wrong-adapter-input",
        )
        engine = AliceEngine(
            self.store,
            FixtureAgentProvider(),
            self.config,
            adapters={"library": WrongInputAdapter()},
        )

        with self.assertRaisesRegex(EngineError, "different input"):
            engine._execute(task)

    def test_engine_rejects_sensitive_adapter_fields_before_persistence(self) -> None:
        task = self.store.enqueue_task(
            "library.read",
            {
                "loop": "library",
                "action": "library.read",
                "role": "design_librarian",
                "objective": "read one source",
                "dependencies": {},
            },
            idempotency_key="sensitive-adapter-payload",
        )
        engine = AliceEngine(
            self.store,
            FixtureAgentProvider(),
            self.config,
            adapters={"library": SensitivePayloadAdapter()},
        )

        with self.assertRaisesRegex(EngineError, "forbidden sensitive field"):
            engine._execute(task)

    def test_engine_rejects_sensitive_text_and_undocumented_receipt_fields(self) -> None:
        task = self.store.enqueue_task(
            "library.read",
            {
                "loop": "library",
                "action": "library.read",
                "role": "design_librarian",
                "objective": "read one source",
                "dependencies": {},
            },
            idempotency_key="sensitive-adapter-value",
        )
        engine = AliceEngine(
            self.store,
            FixtureAgentProvider(),
            self.config,
            adapters={"library": SensitiveValueAdapter()},
        )

        with self.assertRaisesRegex(EngineError, "sensitive text"):
            engine._execute(task)

    def test_physical_effect_recovery_switches_to_readback_not_second_write(self) -> None:
        candidate = self.store.create_candidate(
            {"title": "Bridgeworks"},
            candidate_id="physical-effect-candidate",
            state="human_validated",
        )
        task = self.store.enqueue_task(
            "physical.cad",
            {
                "loop": "physical",
                "action": "physical.cad",
                "role": "cad_engineer",
                "objective": "build exact CAD once",
                "candidate_id": candidate.id,
                "candidate_version": candidate.version,
                "candidate_content_sha256": self.store.sha256_json(
                    candidate.content
                ),
            },
            idempotency_key="physical-cad-reconciliation",
            candidate_id=candidate.id,
        )
        leased = self.store.lease_task(self.engine.worker_id)
        self.assertEqual(leased.id, task.id)

        first_operation, first_payload, first_cached = (
            self.engine._prepare_irreversible_task_effect(leased)
        )
        retry_operation, retry_payload, retry_cached = (
            self.engine._prepare_irreversible_task_effect(leased)
        )

        self.assertEqual(first_operation, "physical.cad")
        self.assertFalse(first_payload["reconcile_only"])
        self.assertTrue(first_payload["effect_operation_key"].startswith("alice:"))
        self.assertIsNone(first_cached)
        self.assertEqual(retry_operation, "physical.reconcile_cad")
        self.assertTrue(retry_payload["reconcile_only"])
        self.assertEqual(retry_payload["task_input_sha256"], leased.input_sha256)
        self.assertIsNone(retry_cached)
        with self.assertRaisesRegex(EngineError, "ambiguous"):
            self.engine._mark_irreversible_task_effect_ambiguous(
                leased, "remote timeout"
            )
            self.engine._prepare_irreversible_task_effect(leased)

    def test_live_clock_renews_lease_during_slow_provider_call(self) -> None:
        self.config["runtime"]["lease_seconds"] = 0.06
        engine = AliceEngine(
            self.store,
            SlowAgentProvider(),
            self.config,
            worker_id="slow-worker",
        )
        task = self.store.enqueue_task(
            "heartbeat.test",
            {
                "loop": "meta",
                "action": "heartbeat.test",
                "role": "alice_director",
                "objective": "exercise the production lease clock",
                "depends_on": [],
                "dependencies": {},
                "work_payload": {},
            },
            idempotency_key="heartbeat-test",
            priority=10_000,
        )

        completed = engine.work_once()

        self.assertIsNotNone(completed)
        self.assertEqual(completed.id, task.id)
        self.assertEqual(completed.state, "succeeded")
        renewals = self.store.list_events(
            kind="task.lease_renewed",
            aggregate_id=task.id,
            limit=100,
        )
        self.assertGreaterEqual(len(renewals), 2)

    def test_finished_research_is_fed_into_later_loops(self) -> None:
        history = self.store.enqueue_task(
            "history.scan_traditional",
            {"role": "game_historian"},
            idempotency_key="history-result",
        )
        leased = self.store.lease_task("history-worker")
        self.assertEqual(leased.id, history.id)
        self.store.complete_task(
            leased.id,
            "history-worker",
            leased.lease_token,
            {
                "executor": "agent",
                "response": {
                    "content": {
                        "summary": "A cited sowing-game pattern",
                        "citations": ["source:page"],
                    }
                },
            },
        )
        task = self.store.enqueue_task(
            "opportunity.frame",
            {
                "loop": "invention",
                "action": "opportunity.frame",
                "role": "alice_director",
                "objective": "frame an opportunity",
                "depends_on": [],
                "dependencies": {},
                "work_payload": {},
            },
            idempotency_key="opportunity-after-history",
        )
        provider = CapturingAgentProvider()
        engine = AliceEngine(self.store, provider, self.config)

        engine._execute(task)

        knowledge = provider.requests[0].context["recent_knowledge"]
        taste = provider.requests[0].context["taste"]
        self.assertEqual(taste["path"], "TASTE.md")
        self.assertEqual(taste["sha256"], engine.taste.sha256)
        self.assertIn("Alice's taste", taste["content"])
        self.assertEqual(knowledge[0]["action"], "history.scan_traditional")
        self.assertEqual(
            knowledge[0]["content"]["summary"], "A cited sowing-game pattern"
        )

    def test_taste_change_during_agent_call_rejects_the_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            taste_root = Path(temporary)
            taste_path = taste_root / "TASTE.md"
            taste_path.write_text(
                "---\n"
                "name: Alice\n"
                "description: Invents tactile tabletop classics with strong table presence.\n"
                "---\n\n"
                "# Stable taste\n",
                encoding="utf-8",
            )
            taste = load_taste(taste_root)
            task = self.store.enqueue_task(
                "opportunity.frame",
                {
                    "loop": "invention",
                    "action": "opportunity.frame",
                    "role": "alice_director",
                    "objective": "frame an opportunity",
                    "depends_on": [],
                    "dependencies": {},
                    "work_payload": {},
                },
                idempotency_key="taste-mutation",
            )
            engine = AliceEngine(
                self.store,
                TasteMutatingProvider(taste_path),
                self.config,
                taste=taste,
            )

            with self.assertRaisesRegex(ManifestError, "changed during Make"):
                engine._execute(task)

    def test_send_waits_for_its_pack_dependency(self) -> None:
        self.config["runtime"]["effect_mode"] = "live"
        candidate = self.store.create_candidate(
            {"title": "River Council"},
            candidate_id="publish-candidate",
        )
        candidate = self.store.transition_candidate(
            candidate.id,
            "publish_ready",
            expected_state="proposed",
            expected_version=1,
        )
        run_id = f"candidate:{candidate.id}:v{candidate.version}"

        self.engine.schedule(now=4_000_000)
        tasks = self.store.list_tasks(run_id=run_id, limit=100)
        self.assertEqual([task.kind for task in tasks], ["pack.product"])

        packet = self.store.lease_task(
            "packet-worker",
            lease_seconds=60,
            now=4_000_000.1,
        )
        self.assertEqual(packet.kind, "pack.product")
        completed_packet = self.store.complete_task(
            packet.id,
            "packet-worker",
            packet.lease_token,
            {
                "executor": "agent",
                "response": {
                    "content": {
                        "publication_packet": {"title": "River Council"},
                        "packet_hash": "a" * 64,
                        "policy_hash": "b" * 64,
                    }
                },
            },
            now=4_000_000.2,
        )
        self.engine.schedule(now=4_000_000.3)
        tasks = self.store.list_tasks(run_id=run_id, limit=100)
        invoke = next(task for task in tasks if task.kind == "send.to_shop")
        dependency = invoke.payload["dependencies"]["pack.product"]
        self.assertEqual(dependency["output_sha256"], completed_packet.output_sha256)

    def test_dry_run_rejects_legacy_publish_task_before_adapter_invocation(self) -> None:
        content = {"title": "River Council"}
        candidate = self.store.create_candidate(content, candidate_id="dry-publish")
        candidate = self.store.transition_candidate(
            candidate.id,
            "publish_ready",
            expected_state="proposed",
            expected_version=1,
        )
        task = self.store.enqueue_task(
            "publish.invoke_pipeline",
            {
                "candidate_id": candidate.id,
                "candidate_version": candidate.version,
                "candidate": content,
                "candidate_content_sha256": hashlib.sha256(
                    json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "role": "publisher",
            },
            candidate_id=candidate.id,
            idempotency_key="dry-publish-effect",
        )
        adapter = RecordingAdapter()
        engine = AliceEngine(
            self.store,
            FixtureAgentProvider(),
            self.config,
            adapters={"publishing_pipeline": adapter},
        )

        with self.assertRaisesRegex(EngineError, "requires effect mode 'live'"):
            engine._execute(task)

        self.assertEqual(adapter.calls, [])

    def test_stale_legacy_publish_task_is_rejected_before_adapter_invocation(self) -> None:
        self.config["runtime"]["effect_mode"] = "live"
        content = {"title": "River Council"}
        candidate = self.store.create_candidate(content, candidate_id="stale-publish")
        candidate = self.store.transition_candidate(
            candidate.id,
            "publish_ready",
            expected_state="proposed",
            expected_version=1,
        )
        task = self.store.enqueue_task(
            "publish.invoke_pipeline",
            {
                "candidate_id": candidate.id,
                "candidate_version": candidate.version,
                "candidate": content,
                "candidate_content_sha256": hashlib.sha256(
                    json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "role": "publisher",
            },
            candidate_id=candidate.id,
            idempotency_key="stale-publish-effect",
        )
        self.store.transition_candidate(
            candidate.id,
            "rework",
            expected_state="publish_ready",
            expected_version=candidate.version,
        )
        adapter = RecordingAdapter()
        engine = AliceEngine(
            self.store,
            FixtureAgentProvider(),
            self.config,
            adapters={"publishing_pipeline": adapter},
        )

        with self.assertRaisesRegex(EngineError, "stale candidate task"):
            engine._execute(task)

        self.assertEqual(adapter.calls, [])

    def test_verified_shop_door_stamps_advance_automatically(self) -> None:
        candidate = self.store.create_candidate(
            {"title": "River Council"},
            candidate_id="pipeline-candidate",
        )
        self.store.transition_candidate(
            candidate.id,
            "publish_ready",
            expected_state="proposed",
            expected_version=1,
        )
        receipt = {
            "packet_hash": "a" * 64,
            "page_url": "https://www.autonomous.ai/factory/product/river-council",
            "pipeline_run_id": "history-1",
        }
        run_id = f"candidate:{candidate.id}:v2"
        packet = self.store.enqueue_task(
            "pack.product",
            {
                "candidate_id": candidate.id,
                "candidate_version": 2,
                "role": "packer",
            },
            idempotency_key="pipeline-packet-result",
            run_id=run_id,
            candidate_id=candidate.id,
            priority=101,
        )

        invoke = self.store.enqueue_task(
            "send.to_shop",
            {
                "candidate_id": candidate.id,
                "role": "sender",
                "candidate_version": 2,
            },
            idempotency_key="pipeline-invoke-result",
            run_id=run_id,
            candidate_id=candidate.id,
            priority=100,
        )
        leased = self.store.lease_task("pipeline-worker")
        self.assertEqual(leased.id, packet.id)
        completed_packet = self.store.complete_task(
            leased.id,
            "pipeline-worker",
            leased.lease_token,
            {
                "executor": "release_policy",
                "content": {
                    "publication_packet": {"candidate_id": candidate.id},
                    "packet_hash": "a" * 64,
                    "policy_hash": "b" * 64,
                    "release_decision": {"allowed": True},
                },
            },
        )
        self.engine._record_result(completed_packet)
        leased = self.store.lease_task("pipeline-worker")
        self.assertEqual(leased.id, invoke.id)
        completed = self.store.complete_task(
            leased.id,
            "pipeline-worker",
            leased.lease_token,
            {
                "executor": "adapter",
                "receipt": {
                    "status": "passed",
                    "evidence_class": "shop_door",
                    "payload": receipt,
                },
            },
        )
        self.engine._record_result(completed)
        self.assertEqual(self.store.get_candidate(candidate.id).state, "page_ready")

        verify = next(
            task
            for task in self.store.list_tasks(
                run_id=f"candidate:{candidate.id}:v3", limit=100
            )
            if task.kind == "send.verify_shop"
        )
        leased = self.store.lease_task("pipeline-worker-2")
        self.assertEqual(leased.id, verify.id)
        completed = self.store.complete_task(
            leased.id,
            "pipeline-worker-2",
            leased.lease_token,
            {
                "executor": "adapter",
                "receipt": {
                    "status": "passed",
                    "evidence_class": "shop_door",
                    "payload": receipt,
                },
            },
        )
        self.engine._record_result(completed)
        self.assertEqual(self.store.get_candidate(candidate.id).state, "published")

        returned = self.store.transition_candidate(
            candidate.id,
            "publish_ready",
            expected_state="published",
            expected_version=4,
        )
        self.engine._record_result(
            self.store.get_task(invoke.id)
        )
        self.assertEqual(returned.version, 5)
        self.assertEqual(self.store.get_candidate(candidate.id).state, "publish_ready")

    def test_external_outcome_updates_the_durable_learning_policy(self) -> None:
        outcome_result = {
            "executor": "adapter",
            "receipt": {
                "status": "passed",
                "evidence_class": "external",
                "payload": {
                    "outcomes": [
                        {
                            "event_id": "blind-outcome-1",
                            "action": "simplify_rules",
                            "outcome": 1.0,
                            "context": {"stage": "rework"},
                            "source": "blind_human",
                            "weight": 1.0,
                        }
                    ]
                },
            },
        }
        task = self.store.enqueue_task(
            "policy.shadow",
            {
                "loop": "learning",
                "action": "policy.shadow",
                "role": "meta_scientist",
                "objective": "update from verified outcomes",
                "dependencies": {
                    "outcomes.ingest": {"result": outcome_result}
                },
            },
            idempotency_key="learning-update",
        )

        result = self.engine._execute(task)

        self.assertEqual(result["executor"], "learning_policy")
        self.assertEqual(result["content"]["accepted"], 1)
        state = self.store.get_state("alice.learning-policy")
        self.assertIsNotNone(state)
        self.assertEqual(state.value["accepted_updates"], 1)

    def test_pre_alice_market_signal_cannot_train_or_unlock_release(self) -> None:
        founder_event = "founder-report-2026-08-22-two-chess-designs"
        outcome_result = {
            "executor": "adapter",
            "receipt": {
                "status": "passed",
                "evidence_class": "external",
                "payload": {
                    "outcomes": [
                        {
                            "event_id": founder_event,
                            "action": "simplify_rules",
                            "outcome": 1.0,
                            "context": {"stage": "rework"},
                            "source": "market",
                        }
                    ]
                },
            },
        }
        task = self.store.enqueue_task(
            "policy.shadow",
            {
                "loop": "learning",
                "action": "policy.shadow",
                "role": "meta_scientist",
                "objective": "reject pre-Alice evidence",
                "dependencies": {"outcomes.ingest": {"result": outcome_result}},
            },
            idempotency_key="reject-pre-alice-learning",
        )
        with self.assertRaisesRegex(EngineError, "pre-Alice.*not eligible"):
            self.engine._execute(task)
        with self.assertRaisesRegex(EngineError, "pre-Alice.*not eligible"):
            self.engine._reject_ineligible_market_signal(founder_event, "release")

    def test_rework_uses_the_bandit_then_restarts_evidence_on_mutation(self) -> None:
        original = {
            "title": "River Council",
            "mechanism_family": "route-building",
            "components": [
                {
                    "name": "river tile",
                    "manufacturing": {"process": "3d_print"},
                }
            ],
        }
        candidate = self.store.create_candidate(
            original,
            candidate_id="learning-candidate",
            state="rework",
            metadata={
                "last_gate_failure": {"codes": ["rules_ambiguity_open"]},
                "accepted_manifests": [{"stale": True}],
            },
        )
        self.engine._schedule_candidate(candidate.id, now=5_000_000)
        choose = self.store.lease_task("learning-worker", now=5_000_000)
        self.assertEqual(choose.kind, "candidate.choose_mutation")
        choose_result = self.engine._execute(choose)
        completed_choose = self.store.complete_task(
            choose.id,
            "learning-worker",
            choose.lease_token,
            choose_result,
            now=5_000_000.1,
        )
        self.engine._record_result(completed_choose)

        apply = self.store.lease_task("mutation-worker")
        self.assertEqual(apply.kind, "candidate.apply_mutation")
        action = choose_result["content"]["action"]
        revised = {
            **original,
            "title": "River Council Revised",
            "revision": action,
        }
        completed_apply = self.store.complete_task(
            apply.id,
            "mutation-worker",
            apply.lease_token,
            {
                "executor": "agent",
                "response": {
                    "content": {
                        "candidate": revised,
                        "action": action,
                        "expectation": "Blind teach disputes fall by at least 20%.",
                    }
                },
            },
        )
        self.engine._record_result(completed_apply)

        updated = self.store.get_candidate(candidate.id)
        if action == "kill_candidate":
            self.assertEqual(updated.state, "killed")
        else:
            self.assertEqual(updated.state, "proposed")
            self.assertEqual(updated.content["title"], "River Council Revised")
            self.assertNotIn("accepted_manifests", updated.metadata)

    def test_malformed_succeeded_result_is_quarantined_without_bricking_schedule(self) -> None:
        candidate = self.store.create_candidate(
            {"title": "Malformed Trial"},
            candidate_id="malformed-trial",
            state="human_ready",
        )
        run_id = f"candidate:{candidate.id}:v{candidate.version}"
        task = self.store.enqueue_task(
            "human.collect_blind_results",
            {
                "loop": "human",
                "action": "human.collect_blind_results",
                "role": "human_researcher",
                "objective": "ingest trials",
                "candidate_id": candidate.id,
                "candidate_version": candidate.version,
                "candidate": candidate.content,
                "candidate_content_sha256": self.store.sha256_json(candidate.content),
                "accepted_artifacts": [],
                "dependencies": {},
            },
            candidate_id=candidate.id,
            run_id=run_id,
            idempotency_key="malformed-human-result",
        )
        leased = self.store.lease_task("malformed-worker")
        completed = self.store.complete_task(
            leased.id,
            "malformed-worker",
            leased.lease_token,
            {
                "executor": "adapter",
                "receipt": {
                    "status": "passed",
                    "evidence_class": "blind_human",
                    "payload": {
                        "trial_ids": ["t1"],
                        "blind_groups": "3",
                        "minimum_games_per_group": 2,
                        "designer_hints_required": 0,
                        "consent_provenance": ["consent"],
                        "reward_evidence": [],
                    },
                },
            },
        )
        self.assertEqual(completed.id, task.id)

        self.engine.schedule()
        self.engine.schedule()

        self.assertEqual(self.store.get_candidate(candidate.id).state, "rework")
        self.assertIsNotNone(self.store.get_task_derived_application(task.id))
        self.assertIsNotNone(
            self.store.get_state(f"alice.task-quarantine:{task.id}")
        )

    def test_paid_order_fans_out_once_to_exact_print_qa_and_shipment(self) -> None:
        candidate = self.store.create_candidate(
            {"title": "River Council"},
            candidate_id="fulfillment-candidate",
        )
        artifacts = {"RULES.md": "a" * 64, "board.3mf": "b" * 64}
        sku = "ALICE-RIVER-001"
        manifest = {
            "candidate_id": candidate.id,
            "candidate_version": 3,
            "candidate_content_sha256": "c" * 64,
            "listing": {"sku": sku},
            "bom": [
                {
                    "part_id": "board",
                    "name": "Board",
                    "quantity": 1,
                    "material": "PLA",
                    "manufacturing_method": "3d_print",
                    "artifact_path": "board.3mf",
                }
            ],
            "manufacturing": {
                "process": "3d_print",
                "print_profile_sha256": "8" * 64,
                "materials": ["PLA"],
                "packing": {"format": "carton", "component_count": 1},
                "vibe_design": {
                    "design_id": "design-1",
                    "slug": "river-council",
                    "history_id": "history-1",
                    "project_url": "https://cdn.example/project/",
                    "artifact_hashes": artifacts,
                }
            },
            "price": {"price_cents": 9999, "currency": "USD"},
        }
        manufacturing_spec = build_manufacturing_spec_from_manifest(manifest)
        manifest["manufacturing"]["material_spec_sha256"] = manufacturing_spec[
            "material_spec_sha256"
        ]
        manifest["manufacturing"][
            "manufacturing_spec_sha256"
        ] = manufacturing_spec["manufacturing_spec_sha256"]
        packet_hash = fulfillment_sha256(manifest)
        operation_key = f"alice:vibe:{candidate.id}:v5:{packet_hash}"
        request = {
            "schema_version": 1,
            "operation_key": operation_key,
            "candidate_id": candidate.id,
            "candidate_version": 5,
            "candidate_content_sha256": "c" * 64,
            "packet_hash": packet_hash,
            "production_packet_hash": packet_hash,
            "reviewed_packet_hash": packet_hash,
            "policy_hash": "d" * 64,
            "production_candidate_version": 3,
            "production_manifest": manifest,
            "release_decision": {
                "allowed": True,
                "effect_mode": "live",
                "candidate_id": candidate.id,
                "production_packet_hash": packet_hash,
                "reviewed_packet_hash": packet_hash,
            },
            "existing_design": {
                "design_id": "design-1",
                "slug": "river-council",
                "history_id": "history-1",
                "project_url": "https://cdn.example/project/",
                "artifact_hashes": artifacts,
            },
            "publication": {"price_cents": 9999, "currency": "USD"},
        }
        prepared = self.store.prepare_publication(
            "vibe_pipeline",
            operation_key,
            fulfillment_sha256(request),
            request,
            candidate_id=candidate.id,
            slug="river-council",
        )
        publication = self.store.transition_publication(
            prepared.id,
            "confirmed",
            expected_state="prepared",
            remote_design_id="design-1",
            slug="river-council",
            history_id="history-1",
            status="published",
            project_url="https://cdn.example/project/",
            response={
                "stage": "complete",
                "operation_key": operation_key,
                "candidate_id": candidate.id,
                "packet_hash": packet_hash,
                "listing_sku": sku,
                "price_cents": 9999,
                "currency": "USD",
            },
        )
        paid_order = {
            "order_id": "order-42",
            "payment_status": "paid",
            "publication_id": publication.id,
            "packet_hash": packet_hash,
            "sku": sku,
            "quantity": 2,
            "currency": "USD",
            "unit_price_cents": 9999,
            "product_subtotal_cents": 19998,
            "amount_paid_cents": 21998,
            "shipping_reference": "address-token-order-42",
        }
        adapter = FulfillmentLifecycleAdapter(
            paid_order, fail_after_print_commit=True
        )
        self.config["runtime"]["effect_mode"] = "live"
        engine = AliceEngine(
            self.store,
            FixtureAgentProvider(),
            self.config,
            worker_id="fulfillment-worker",
            adapters={
                "delivery": adapter,
                "print_fulfillment": adapter,
            },
        )

        def execute_one(kind, key):
            self.store.enqueue_task(
                kind,
                {
                    "loop": "orders",
                    "action": kind,
                    "role": "fulfillment_planner",
                    "objective": kind,
                    "depends_on": [],
                    "dependencies": {},
                    "work_payload": {},
                },
                idempotency_key=key,
                priority=10_000,
                max_attempts=1,
            )
            leased = self.store.lease_task(engine.worker_id)
            self.assertEqual(leased.kind, kind)
            result = engine._execute(leased)
            completed = self.store.complete_task(
                leased.id,
                engine.worker_id,
                leased.lease_token,
                result,
            )
            engine._record_result(completed)
            return completed

        execute_one("orders.poll_paid", "order-poll-first")
        print_task = self.store.list_tasks(
            run_id=None, state="queued", kind="orders.create_print_job", limit=10
        )[0]
        leased_print = self.store.lease_task(engine.worker_id)
        self.assertEqual(leased_print.id, print_task.id)
        with self.assertRaisesRegex(AdapterError, "after factory commit"):
            engine._execute(leased_print)
        failed_print = self.store.fail_task(
            leased_print.id,
            engine.worker_id,
            leased_print.lease_token,
            stage=leased_print.kind,
            error_code="AdapterError",
            error_message="simulated timeout after factory commit",
            retryable=True,
        )
        self.assertEqual(failed_print.state, "queued")

        # Recovery never repeats the write. It asks the factory to read back
        # the exact operation key and accepts only the original bound receipt.
        leased_print = self.store.lease_task(engine.worker_id)
        self.assertEqual(leased_print.id, print_task.id)
        print_result = engine._execute(leased_print)
        completed_print = self.store.complete_task(
            leased_print.id,
            engine.worker_id,
            leased_print.lease_token,
            print_result,
        )
        engine._record_result(completed_print)

        leased_ship = self.store.lease_task(engine.worker_id)
        self.assertEqual(leased_ship.kind, "orders.qa_ship")
        ship_result = engine._execute(leased_ship)
        completed_ship = self.store.complete_task(
            leased_ship.id,
            engine.worker_id,
            leased_ship.lease_token,
            ship_result,
        )
        engine._record_result(completed_ship)

        # A later poll may replay the same paid order, but the per-order task
        # identity and immutable state prevent another print or shipment.
        execute_one("orders.poll_paid", "order-poll-replay")
        tasks = self.store.list_tasks(limit=1_000)
        self.assertEqual(
            sum(task.kind == "orders.create_print_job" for task in tasks), 1
        )
        self.assertEqual(sum(task.kind == "orders.qa_ship" for task in tasks), 1)
        self.assertEqual(adapter.calls.count("orders.create_print_job"), 1)
        self.assertEqual(adapter.calls.count("orders.reconcile_print_job"), 1)
        self.assertEqual(adapter.calls.count("orders.qa_ship"), 1)
        intents = [
            task.payload["fulfillment_intent"]
            for task in tasks
            if task.kind == "orders.create_print_job"
        ]
        intent = fulfillment_intent_from_payload(intents[0])
        self.assertIsNotNone(
            self.store.get_state(
                f"alice.fulfillment-shipment:{intent.operation_key}"
            )
        )
        self.assertEqual(
            len(self.store.list_experiences(kind="fulfillment.shipped")), 1
        )


if __name__ == "__main__":
    unittest.main()
