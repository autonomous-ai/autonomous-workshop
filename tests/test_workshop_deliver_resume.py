import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path

from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.engine_provenance import (
    EngineProvenanceManifest,
    StageComponentManifest,
    WORKSHOP_STAGES,
)
from inventor_workshop.errors import (
    AmbiguousEffectError,
    ContractError,
    LeaseBusy,
)
from inventor_workshop.instructions import DefaultInstructions
from inventor_workshop.jobs import DeliverContext
from inventor_workshop.manager import register_workshop_engine
from inventor_workshop.make import Wish
from inventor_workshop.runtime import Runtime
from inventor_workshop.workshop import Workshop, WorkshopTools
from tests import test_toy_workshop as toy_fixture


class _CrashThenReconcileProvider:
    """One stable provider object spanning its effect and GET-only readback."""

    def __init__(self):
        self.fulfill_calls = 0
        self.readback_calls = 0
        self.readback = lambda context: None

    def __call__(self, context):
        context.assert_current()
        self.fulfill_calls += 1
        raise SystemExit("simulated effect-process crash")

    def reconcile(self, context):
        context.assert_current()
        self.readback_calls += 1
        return self.readback(context)


class WorkshopDeliverResumeTest(unittest.TestCase):
    """Deliver may resume only after an exact, proven no-effect wait."""

    def setUp(self):
        self.fixture = toy_fixture.ToyWorkshopTest(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root
        self.inventor = self.fixture.inventor

    def tearDown(self):
        self.fixture.tearDown()

    def workshop(
        self,
        runtime_root,
        *,
        deliver,
        calls=None,
        trusted=False,
        trusted_deliver_provider_id=None,
        **kwargs
    ):
        calls = calls if calls is not None else {}

        def counted(name, operation):
            def invoke(context):
                calls[name] = calls.get(name, 0) + 1
                return operation(context)

            return invoke

        instructions = DefaultInstructions(site_writer=self.fixture.site_writer)
        tools = WorkshopTools(
            invent=counted("invent", self.fixture.invent_job),
            make=counted("make", self.fixture.make_job),
            playtest=counted("playtest", self.fixture.passing_playtest),
            instructions=counted("instructions", instructions),
            deliver=deliver,
        )
        if trusted:
            provider_ids = None
            if trusted_deliver_provider_id is not None:
                provider_ids = {
                    "invent": "test.shared-invent-v1",
                    "make": "test.shared-make-v1",
                    "playtest": "test.shared-playtest-v1",
                    "instructions": "test.shared-instructions-v1",
                    "deliver": trusted_deliver_provider_id,
                }
            authority = {
                "trusted_engine": register_workshop_engine(
                    tools, provider_ids=provider_ids
                )
            }
        else:
            authority = {"tools": tools}
        return Workshop(
            self.inventor,
            kwargs.pop("lane", "moving-machines"),
            inventor_id=kwargs.pop("inventor_id", None),
            runtime_root=Path(runtime_root).absolute(),
            **authority,
            **kwargs,
        )

    def waiting_run(
        self,
        name="deliver-resume",
        *,
        calls=None,
        trusted=False,
        trusted_deliver_provider_id=None
    ):
        runtime_root = self.root / (name + "-runtime")
        wish = Wish.create(name, "A toy waiting for a real production bench")
        result = self.workshop(
            runtime_root,
            deliver=DefaultDeliver(),
            calls=calls,
            trusted=trusted,
            trusted_deliver_provider_id=trusted_deliver_provider_id,
        ).run(wish, playtest_rounds=2)
        self.assertEqual((result.status, result.job), ("waiting", "deliver"))
        return runtime_root, wish, result

    def ambiguous_working_run(
        self,
        name,
        *,
        calls=None,
        provider_id=None,
    ):
        selected_provider = provider_id or (
            "manager-services.test.deliver.reconcile.1.0.0." + "d" * 64
        )
        runtime_root, wish, waiting = self.waiting_run(
            name,
            calls=calls,
            trusted=True,
            trusted_deliver_provider_id=selected_provider,
        )
        provider = _CrashThenReconcileProvider()

        with self.assertRaisesRegex(SystemExit, "effect-process crash"):
            self.workshop(
                runtime_root,
                deliver=DefaultDeliver(provider),
                calls=calls,
                trusted=True,
                trusted_deliver_provider_id=selected_provider,
            ).resume(wish)
        self.assertEqual(provider.fulfill_calls, 1)
        latest = Runtime(runtime_root / "workshop.sqlite3").events(
            wish.product_id
        )[-1]
        self.assertEqual(latest["payload"]["status"], "working")
        return runtime_root, wish, waiting, selected_provider, provider

    def test_waiting_deliver_resumes_without_rerunning_any_earlier_stage(self):
        calls = {}
        provider_id = "manager-services.test.deliver.fixture.1.0.0." + "d" * 64
        runtime_root, wish, waiting = self.waiting_run(
            calls=calls,
            trusted=True,
            trusted_deliver_provider_id=provider_id,
        )
        self.assertEqual(
            calls,
            {"invent": 1, "make": 1, "playtest": 1, "instructions": 1},
        )

        state = Runtime(runtime_root / "workshop.sqlite3")
        waiting_payload = state.events(wish.product_id)[-1]["payload"]
        expected_attempt_id = waiting_payload["deliver_attempt_id"]
        observed_contexts = []

        def available_fulfiller(context):
            observed_contexts.append(context)
            return self.fixture.fulfiller(context)

        resumed = self.workshop(
            runtime_root,
            deliver=DefaultDeliver(available_fulfiller),
            calls=calls,
            trusted=True,
            trusted_deliver_provider_id=provider_id,
        ).resume(wish)

        self.assertEqual((resumed.status, resumed.job), ("delivered", "deliver"))
        self.assertEqual(resumed.artifact_sha256, waiting.artifact_sha256)
        self.assertEqual(resumed.instructions_sha256, waiting.instructions_sha256)
        self.assertEqual(resumed.invented, waiting.invented)
        self.assertEqual(resumed.page_url, waiting.page_url)
        self.assertEqual(len(observed_contexts), 1)
        self.assertEqual(observed_contexts[0].provider_identity, provider_id)
        self.assertEqual(observed_contexts[0].attempt_id, expected_attempt_id)
        self.assertEqual(observed_contexts[0].idempotency_key, expected_attempt_id)
        self.assertEqual(
            calls,
            {"invent": 1, "make": 1, "playtest": 1, "instructions": 1},
        )

        self.assertTrue(state.verify_event_chain(wish.product_id))
        events = state.events(wish.product_id)
        waiting_payload = next(
            event["payload"]
            for event in reversed(events)
            if event["payload"].get("status") == "waiting"
            and event["to_stage"] == "deliver"
        )
        for kind in ("instructions", "deliver"):
            self.assertEqual(
                waiting_payload["%s_checkpoint_round" % kind], waiting.round
            )
            self.assertEqual(
                len(waiting_payload["%s_checkpoint_sha256" % kind]), 64
            )
            self.assertTrue(
                (
                    runtime_root
                    / "runs"
                    / wish.product_id
                    / waiting_payload["%s_checkpoint_path" % kind]
                ).is_file()
            )
        deliver_events = [
            event
            for event in events
            if event["to_stage"] == "deliver"
            and event["payload"].get("status")
            in {"working", "waiting", "delivered"}
        ]
        self.assertGreaterEqual(len(deliver_events), 4)
        self.assertEqual(
            {
                (
                    event["payload"]["deliver_provider_id"],
                    event["payload"]["deliver_attempt_id"],
                )
                for event in deliver_events
            },
            {(provider_id, expected_attempt_id)},
        )

        provider_calls = 0

        def forbidden_provider(context):
            nonlocal provider_calls
            provider_calls += 1
            return self.fixture.fulfiller(context)

        with self.assertRaisesRegex(ContractError, "terminal"):
            self.workshop(
                runtime_root,
                deliver=DefaultDeliver(forbidden_provider),
            ).resume(wish)
        self.assertEqual(provider_calls, 0)

    def test_all_stage_provenance_is_sealed_in_registration_events_and_checkpoints(self):
        runtime_root, wish, _ = self.waiting_run(
            "deliver-provenance",
            trusted=True,
            trusted_deliver_provider_id="test.shared-deliver-v1",
        )
        state = Runtime(runtime_root / "workshop.sqlite3")
        product = state.get_product(wish.product_id)
        registered = EngineProvenanceManifest.from_dict(
            product["metadata"]["engine_provenance"]
        )
        self.assertEqual(
            tuple(component.stage for component in registered.components),
            WORKSHOP_STAGES,
        )

        events = state.events(wish.product_id)
        completed = {}
        for event in events:
            payload = event["payload"]
            active = payload.get("engine_active_stage")
            if active is not None:
                parsed = StageComponentManifest.from_dict(active)
                self.assertEqual(parsed.stage, event["to_stage"])
            sealed = payload.get("engine_completed_stage")
            if sealed is not None:
                parsed = StageComponentManifest.from_dict(sealed)
                completed[parsed.stage] = parsed
        self.assertEqual(
            set(completed), {"invent", "make", "playtest", "instructions"}
        )
        for stage, component in completed.items():
            self.assertEqual(component, registered.component(stage))

        expected_checkpoint_stage = {
            "made": "make",
            "playtested": "playtest",
            # Instructions is the approved Playtest-to-Instructions input.
            "instructions": "playtest",
            # Deliver approval is provider-neutral and binds Instructions.
            "deliver": "instructions",
            # The effect attempt, not the approval, binds Deliver's provider.
            "deliver_attempt": "deliver",
        }
        run_root = runtime_root / "runs" / wish.product_id
        for kind, expected_stage in expected_checkpoint_stage.items():
            event = next(
                item
                for item in events
                if "%s_checkpoint_path" % kind in item["payload"]
            )
            payload = event["payload"]
            document = json.loads(
                (run_root / payload["%s_checkpoint_path" % kind]).read_text(
                    encoding="utf-8"
                )
            )
            component = StageComponentManifest.from_dict(
                document["payload"]["_engine_stage"]
            )
            self.assertEqual(component.stage, expected_stage)
            self.assertEqual(component, registered.component(expected_stage))
            self.assertEqual(
                document["checkpoint_sha256"],
                payload["%s_checkpoint_sha256" % kind],
            )

    def test_deliver_checkpoint_and_instructions_tampering_fail_before_effect(self):
        for target in (
            "checkpoint",
            "provider",
            "attempt",
            "engine",
            "event-attempt",
            "made",
            "playtest",
            "instructions",
        ):
            with self.subTest(target=target):
                runtime_root, wish, _ = self.waiting_run("tamper-" + target)
                state = Runtime(runtime_root / "workshop.sqlite3")
                latest = state.events(wish.product_id)[-1]["payload"]
                run_root = runtime_root / "runs" / wish.product_id
                if target in {"checkpoint", "provider", "attempt", "engine"}:
                    path = run_root / latest[
                        "deliver_checkpoint_path"
                        if target == "checkpoint"
                        else "deliver_attempt_checkpoint_path"
                    ]
                    document = json.loads(path.read_text(encoding="utf-8"))
                    if target == "engine":
                        document["payload"]["_engine_stage"][
                            "provider_id"
                        ] = "tampered-engine-provider"
                    else:
                        field = {
                            "checkpoint": "made_artifact_sha256",
                            "provider": "deliver_provider_id",
                            "attempt": "deliver_attempt_id",
                        }[target]
                        document["payload"][field] = (
                            "0" * 64
                            if target == "checkpoint"
                            else "tampered-provider"
                            if target == "provider"
                            else "deliver-" + "0" * 64
                        )
                    path.write_text(
                        json.dumps(document, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                elif target == "event-attempt":
                    changed = dict(latest)
                    changed["deliver_attempt_id"] = "deliver-" + "0" * 64
                    with closing(
                        sqlite3.connect(str(runtime_root / "workshop.sqlite3"))
                    ) as connection:
                        connection.execute(
                            "UPDATE events SET payload_json=? "
                            "WHERE sequence=(SELECT MAX(sequence) FROM events "
                            "WHERE product_id=?)",
                            (json.dumps(changed, sort_keys=True), wish.product_id),
                        )
                        connection.commit()
                elif target in {"made", "playtest"}:
                    instructions_checkpoint = json.loads(
                        (
                            run_root / latest["instructions_checkpoint_path"]
                        ).read_text(encoding="utf-8")
                    )["payload"]
                    if target == "made":
                        value = instructions_checkpoint["made"]
                        manifest = value["manifest"]
                        tree = run_root / value["root"]
                    else:
                        value = instructions_checkpoint["playtested"]
                        manifest = value["evidence_manifest"]
                        tree = run_root / value["evidence_root"]
                    artifact = tree / manifest["entries"][0]["path"]
                    artifact.write_bytes(artifact.read_bytes() + b"tampered")
                else:
                    (run_root / "instructions" / "INSTRUCTIONS.md").write_text(
                        "changed after the no-effect Deliver wait\n",
                        encoding="utf-8",
                    )

                provider_calls = 0

                def forbidden_provider(context):
                    nonlocal provider_calls
                    provider_calls += 1
                    return self.fixture.fulfiller(context)

                with self.assertRaises(ContractError):
                    self.workshop(
                        runtime_root,
                        deliver=DefaultDeliver(forbidden_provider),
                    ).resume(wish)
                self.assertEqual(provider_calls, 0)

    def test_no_effect_wait_may_bind_a_new_provider_in_a_fresh_attempt(self):
        original_provider = (
            "manager-services.test.deliver.fulfillment.1.0.0." + "a" * 64
        )
        rotated_provider = (
            "manager-services.test.deliver.fulfillment.1.0.0." + "b" * 64
        )
        runtime_root, wish, _ = self.waiting_run(
            "deliver-provider-rotation",
            trusted=True,
            trusted_deliver_provider_id=original_provider,
        )
        first_wait = Runtime(runtime_root / "workshop.sqlite3").events(
            wish.product_id
        )[-1]["payload"]
        self.assertEqual(
            StageComponentManifest.from_dict(
                first_wait["engine_active_stage"]
            ).provider_id,
            original_provider,
        )
        incompatible_calls = 0

        def incompatible_deliver_component(context):
            nonlocal incompatible_calls
            incompatible_calls += 1
            return self.fixture.fulfiller(context)

        with self.assertRaisesRegex(
            ContractError, "beyond a provider/service update"
        ):
            self.workshop(
                runtime_root,
                deliver=incompatible_deliver_component,
                trusted=True,
                trusted_deliver_provider_id=rotated_provider,
            ).resume(wish)
        self.assertEqual(incompatible_calls, 0)
        provider_calls = []

        def available_rotated_provider(context):
            provider_calls.append(context)
            return self.fixture.fulfiller(context)

        result = self.workshop(
            runtime_root,
            deliver=DefaultDeliver(available_rotated_provider),
            trusted=True,
            trusted_deliver_provider_id=rotated_provider,
        ).resume(wish)
        self.assertEqual((result.status, result.job), ("delivered", "deliver"))
        self.assertEqual(len(provider_calls), 1)
        self.assertEqual(provider_calls[0].provider_identity, rotated_provider)
        self.assertNotEqual(
            provider_calls[0].attempt_id, first_wait["deliver_attempt_id"]
        )
        latest = Runtime(runtime_root / "workshop.sqlite3").events(
            wish.product_id
        )[-1]["payload"]
        self.assertEqual(latest["status"], "delivered")
        self.assertEqual(latest["deliver_provider_id"], rotated_provider)
        self.assertEqual(
            latest["deliver_attempt_id"], provider_calls[0].attempt_id
        )
        self.assertEqual(
            StageComponentManifest.from_dict(
                latest["engine_active_stage"]
            ).provider_id,
            rotated_provider,
        )
        self.assertEqual(
            StageComponentManifest.from_dict(
                latest["engine_completed_stage"]
            ).provider_id,
            rotated_provider,
        )
        self.assertEqual(
            first_wait["deliver_checkpoint_sha256"],
            latest["deliver_checkpoint_sha256"],
        )
        self.assertNotEqual(
            first_wait["deliver_attempt_checkpoint_sha256"],
            latest["deliver_attempt_checkpoint_sha256"],
        )

    def test_taste_and_inventor_identity_remain_bound_at_deliver(self):
        for changed in ("taste", "inventor"):
            with self.subTest(changed=changed):
                runtime_root, wish, _ = self.waiting_run("binding-" + changed)
                provider_calls = 0

                def forbidden_provider(context):
                    nonlocal provider_calls
                    provider_calls += 1
                    return self.fixture.fulfiller(context)

                if changed == "taste":
                    taste_path = self.inventor / "TASTE.md"
                    original = taste_path.read_bytes()
                    taste_path.write_bytes(original + b"\nA changed preference.\n")
                    try:
                        workshop = self.workshop(
                            runtime_root,
                            deliver=DefaultDeliver(forbidden_provider),
                        )
                        with self.assertRaisesRegex(
                            ContractError, "different inventor identity|Taste"
                        ):
                            workshop.resume(wish)
                    finally:
                        taste_path.write_bytes(original)
                else:
                    workshop = self.workshop(
                        runtime_root,
                        inventor_id="another-inventor",
                        deliver=DefaultDeliver(forbidden_provider),
                    )
                    with self.assertRaisesRegex(
                        ContractError, "different inventor identity|Taste"
                    ):
                        workshop.resume(wish)
                self.assertEqual(provider_calls, 0)

    def test_active_lease_fences_deliver_resume(self):
        runtime_root, wish, _ = self.waiting_run("deliver-active-lease")
        state = Runtime(runtime_root / "workshop.sqlite3")
        token = state.acquire_lease(wish.product_id, "other-live-manager")
        try:
            with self.assertRaises(LeaseBusy):
                self.workshop(
                    runtime_root,
                    deliver=DefaultDeliver(self.fixture.fulfiller),
                ).resume(wish)
        finally:
            state.release_lease(wish.product_id, token)

    def test_killed_deliver_attempt_is_ambiguous_and_never_retried(self):
        runtime_root, wish, _ = self.waiting_run("deliver-killed")
        killed_calls = 0

        def killed_provider(context):
            nonlocal killed_calls
            del context
            killed_calls += 1
            raise SystemExit("simulated worker kill")

        with self.assertRaisesRegex(SystemExit, "simulated worker kill"):
            self.workshop(
                runtime_root,
                deliver=DefaultDeliver(killed_provider),
            ).resume(wish)
        self.assertEqual(killed_calls, 1)
        latest = Runtime(runtime_root / "workshop.sqlite3").events(
            wish.product_id
        )[-1]
        self.assertEqual(latest["payload"]["status"], "working")

        retry_calls = 0

        def forbidden_retry(context):
            nonlocal retry_calls
            retry_calls += 1
            return self.fixture.fulfiller(context)

        with self.assertRaisesRegex(AmbiguousEffectError, "unknown external outcome"):
            self.workshop(
                runtime_root,
                deliver=DefaultDeliver(forbidden_retry),
            ).resume(wish)
        self.assertEqual(retry_calls, 0)

    def test_working_deliver_reconciles_by_readback_without_any_rerun(self):
        calls = {}
        runtime_root, wish, waiting, provider_id, provider = (
            self.ambiguous_working_run(
                "deliver-reconcile-success",
                calls=calls,
            )
        )
        expected_calls = {
            "invent": 1,
            "make": 1,
            "playtest": 1,
            "instructions": 1,
        }
        self.assertEqual(calls, expected_calls)
        state = Runtime(runtime_root / "workshop.sqlite3")
        working = state.events(wish.product_id)[-1]["payload"]
        readbacks = []

        def exact_readback(context):
            readbacks.append(context)
            return self.fixture.fulfiller(context)

        provider.readback = exact_readback

        result = self.workshop(
            runtime_root,
            deliver=DefaultDeliver(provider),
            calls=calls,
            trusted=True,
            trusted_deliver_provider_id=provider_id,
        ).reconcile_deliver(wish)

        self.assertEqual((result.status, result.job), ("delivered", "deliver"))
        self.assertEqual(result.artifact_sha256, waiting.artifact_sha256)
        self.assertEqual(result.instructions_sha256, waiting.instructions_sha256)
        self.assertEqual(provider.fulfill_calls, 1)
        self.assertEqual(len(readbacks), 1)
        context = readbacks[0]
        self.assertEqual(context.product_id, wish.product_id)
        self.assertEqual(context.wish.to_dict(), wish.to_dict())
        self.assertEqual(context.made.artifact_sha256, waiting.artifact_sha256)
        self.assertEqual(
            context.instructions.instructions_sha256,
            waiting.instructions_sha256,
        )
        self.assertEqual(context.provider_identity, working["deliver_provider_id"])
        self.assertEqual(context.attempt_id, working["deliver_attempt_id"])
        self.assertEqual(context.idempotency_key, working["deliver_attempt_id"])
        self.assertEqual(calls, expected_calls)
        latest = state.events(wish.product_id)[-1]["payload"]
        self.assertEqual(latest["status"], "delivered")
        self.assertEqual(latest["delivery"], result.delivery.to_dict())
        self.assertEqual(
            latest["deliver_attempt_checkpoint_sha256"],
            working["deliver_attempt_checkpoint_sha256"],
        )
        self.assertTrue(state.verify_event_chain(wish.product_id))

    def test_still_unknown_and_failed_readbacks_leave_working_state_unchanged(self):
        runtime_root, wish, _, provider_id, provider = (
            self.ambiguous_working_run("deliver-reconcile-unknown")
        )
        state = Runtime(runtime_root / "workshop.sqlite3")
        before = state.events(wish.product_id)

        def still_unknown(context):
            context.assert_current()
            return None

        provider.readback = still_unknown

        result = self.workshop(
            runtime_root,
            deliver=DefaultDeliver(provider),
            trusted=True,
            trusted_deliver_provider_id=provider_id,
        ).reconcile_deliver(wish)
        self.assertEqual((result.status, result.job), ("working", "deliver"))
        self.assertEqual((provider.fulfill_calls, provider.readback_calls), (1, 1))
        self.assertEqual(state.events(wish.product_id), before)

        def crashed_readback(context):
            context.assert_current()
            raise RuntimeError("provider-password=must-not-escape")

        provider.readback = crashed_readback

        with self.assertRaises(AmbiguousEffectError) as raised:
            self.workshop(
                runtime_root,
                deliver=DefaultDeliver(provider),
                trusted=True,
                trusted_deliver_provider_id=provider_id,
        ).reconcile_deliver(wish)
        self.assertNotIn("provider-password", str(raised.exception))
        self.assertEqual(provider.fulfill_calls, 1)
        self.assertEqual(provider.readback_calls, 2)
        self.assertEqual(state.events(wish.product_id), before)

        def wrong_attempt_readback(context):
            other_wish = Wish.create(
                "different-reconciliation-wish",
                "A different Wish over the same approved bytes",
            )
            other_context = DeliverContext(
                other_wish,
                context.made,
                context.instructions,
                context.provider_identity,
                context.inventor_id,
            )
            return self.fixture.fulfiller(other_context)

        provider.readback = wrong_attempt_readback
        with self.assertRaises(AmbiguousEffectError) as raised:
            self.workshop(
                runtime_root,
                deliver=DefaultDeliver(provider),
                trusted=True,
                trusted_deliver_provider_id=provider_id,
            ).reconcile_deliver(wish)
        self.assertIn("working attempt", str(raised.exception))
        self.assertEqual(provider.fulfill_calls, 1)
        self.assertEqual(provider.readback_calls, 3)
        self.assertEqual(state.events(wish.product_id), before)

    def test_working_deliver_reconciliation_forbids_provider_rotation(self):
        original_provider = (
            "manager-services.test.deliver.original.1.0.0." + "a" * 64
        )
        rotated_provider = (
            "manager-services.test.deliver.rotated.1.0.0." + "b" * 64
        )
        runtime_root, wish, _, _, provider = self.ambiguous_working_run(
            "deliver-reconcile-provider-rotation",
            provider_id=original_provider,
        )
        readbacks = 0

        def forbidden_readback(context):
            nonlocal readbacks
            del context
            readbacks += 1
            return None

        provider.readback = forbidden_readback

        with self.assertRaises(AmbiguousEffectError):
            self.workshop(
                runtime_root,
                deliver=DefaultDeliver(provider),
                trusted=True,
                trusted_deliver_provider_id=rotated_provider,
            ).reconcile_deliver(wish)
        self.assertEqual(readbacks, 0)

    def test_working_deliver_tamper_fails_before_reconciliation_readback(self):
        for target in ("attempt-checkpoint", "event", "instructions"):
            with self.subTest(target=target):
                runtime_root, wish, _, provider_id, provider = (
                    self.ambiguous_working_run(
                        "deliver-reconcile-tamper-" + target
                    )
                )
                state = Runtime(runtime_root / "workshop.sqlite3")
                latest = state.events(wish.product_id)[-1]
                payload = latest["payload"]
                run_root = runtime_root / "runs" / wish.product_id
                if target == "attempt-checkpoint":
                    path = run_root / payload[
                        "deliver_attempt_checkpoint_path"
                    ]
                    document = json.loads(path.read_text(encoding="utf-8"))
                    document["payload"]["deliver_attempt_id"] = (
                        "deliver-" + "0" * 64
                    )
                    path.write_text(
                        json.dumps(document, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                elif target == "event":
                    changed = dict(payload)
                    changed["deliver_attempt_id"] = "deliver-" + "0" * 64
                    with closing(
                        sqlite3.connect(str(runtime_root / "workshop.sqlite3"))
                    ) as connection:
                        connection.execute(
                            "UPDATE events SET payload_json=? "
                            "WHERE sequence=(SELECT MAX(sequence) FROM events "
                            "WHERE product_id=?)",
                            (json.dumps(changed, sort_keys=True), wish.product_id),
                        )
                        connection.commit()
                else:
                    (run_root / "instructions" / "INSTRUCTIONS.md").write_text(
                        "tampered after effect start\n",
                        encoding="utf-8",
                    )
                readbacks = 0

                def forbidden_readback(context):
                    nonlocal readbacks
                    del context
                    readbacks += 1
                    return None

                provider.readback = forbidden_readback

                with self.assertRaises(ContractError):
                    self.workshop(
                        runtime_root,
                        deliver=DefaultDeliver(provider),
                        trusted=True,
                        trusted_deliver_provider_id=provider_id,
                    ).reconcile_deliver(wish)
                self.assertEqual(readbacks, 0)

    def test_world_release_policy_is_rechecked_before_deliver_resume(self):
        runtime_root = self.root / "world-deliver-runtime"
        wish = Wish.create(
            "world-deliver-resume",
            "A tiny world using one admitted reference feature",
        )
        inputs = self.fixture.world_inputs(wish)
        tools = WorkshopTools(
            invent=self.fixture.world_invent_job,
            instructions=DefaultInstructions(site_writer=self.fixture.site_writer),
            deliver=DefaultDeliver(),
        )
        first = Workshop(
            self.inventor,
            "little-worlds",
            tools=tools,
            make=self.fixture.make_job,
            playtest=self.fixture.passing_invented_playtest,
            runtime_root=runtime_root,
            world_inputs=inputs,
        ).run(wish, playtest_rounds=1)
        self.assertEqual((first.status, first.job), ("waiting", "playtest"))
        evidence = self.fixture.world_evidence(
            wish, first.artifact_sha256, inputs
        )
        waiting = Workshop(
            self.inventor,
            "little-worlds",
            tools=tools,
            make=self.fixture.make_job,
            playtest=self.fixture.passing_invented_playtest,
            runtime_root=runtime_root,
            world_inputs=inputs,
            world_evidence=evidence,
        ).resume(wish)
        self.assertEqual((waiting.status, waiting.job), ("waiting", "deliver"))

        provider_calls = 0

        def forbidden_provider(context):
            nonlocal provider_calls
            provider_calls += 1
            return self.fixture.fulfiller(context)

        with self.assertRaisesRegex(ContractError, "release policy"):
            Workshop(
                self.inventor,
                "little-worlds",
                tools=WorkshopTools(
                    invent=self.fixture.world_invent_job,
                    instructions=DefaultInstructions(
                        site_writer=self.fixture.site_writer
                    ),
                    deliver=DefaultDeliver(forbidden_provider),
                ),
                make=self.fixture.make_job,
                playtest=self.fixture.passing_invented_playtest,
                runtime_root=runtime_root,
                world_inputs=inputs,
            ).resume(wish)
        self.assertEqual(provider_calls, 0)

        delivered = Workshop(
            self.inventor,
            "little-worlds",
            tools=WorkshopTools(
                invent=self.fixture.world_invent_job,
                instructions=DefaultInstructions(site_writer=self.fixture.site_writer),
                deliver=DefaultDeliver(self.fixture.fulfiller),
            ),
            make=self.fixture.make_job,
            playtest=self.fixture.passing_invented_playtest,
            runtime_root=runtime_root,
            world_inputs=inputs,
            world_evidence=evidence,
        ).resume(wish)
        self.assertEqual((delivered.status, delivered.job), ("delivered", "deliver"))


if __name__ == "__main__":
    unittest.main()
