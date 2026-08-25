import json
import os
import stat
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.errors import ContractError, LeaseBusy, StateConflict
from inventor_workshop.instructions import DefaultInstructions, _write_manifest_once
from inventor_workshop.jobs import Feedback, InventContext, Need, WaitingFor
from inventor_workshop.lease_guard import LeaseGuard
from inventor_workshop.make import Wish
from inventor_workshop.runtime import Runtime
from inventor_workshop.workshop import Workshop, WorkshopTools
from tests import test_toy_workshop as toy_fixture


class WorkshopResumeTest(unittest.TestCase):
    """Crash-boundary tests for stage resume, not mid-reward-loop replay."""

    def setUp(self):
        self.fixture = toy_fixture.ToyWorkshopTest(methodName="runTest")
        self.fixture.setUp()
        self.root = self.fixture.root
        self.inventor = self.fixture.inventor

    def tearDown(self):
        self.fixture.tearDown()

    def workshop(self, runtime, **overrides):
        tools = overrides.pop(
            "tools",
            WorkshopTools(
                invent=self.fixture.invent_job,
                make=self.fixture.make_job,
                playtest=self.fixture.passing_playtest,
                instructions=DefaultInstructions(),
            ),
        )
        return Workshop(
            self.inventor,
            "moving-machines",
            tools=tools,
            runtime_root=Path(runtime).absolute(),
            **overrides,
        )

    def test_exact_registered_wish_boundary_is_idempotently_resumable(self):
        runtime_root = self.root / "registered-runtime"
        workshop = self.workshop(runtime_root)
        wish = Wish.create("registered-wish", "A spinner after a launch crash")
        state = Runtime(runtime_root / "workshop.sqlite3")
        state.register_product(
            wish.product_id,
            "wish",
            {
                "wish": wish.to_dict(),
                "inventor_id": workshop.inventor_id,
                "taste_sha256": workshop.taste.sha256,
                "blueprint_sha256": workshop.blueprint.sha256,
                "lane": workshop.lane,
                "customization_level": workshop.customization_level,
                "playtest_rounds": 2,
            },
        )

        result = workshop.resume(wish)

        self.assertEqual((result.status, result.job), ("waiting", "instructions"))
        self.assertTrue(state.verify_event_chain(wish.product_id))
        self.assertEqual(state.events(wish.product_id)[0]["to_stage"], "wish")

    def test_invent_wait_restarts_only_invent_in_a_fresh_attempt(self):
        calls = {"invent": 0, "make": 0}
        workspaces = []

        def invent(context):
            calls["invent"] += 1
            workspaces.append(context.workspace)
            if calls["invent"] == 1:
                raise WaitingFor(
                    Need("invent", "model", "Invent paused.", "Resume Invent.")
                )
            return self.fixture.invent_job(context)

        def make(context):
            calls["make"] += 1
            return self.fixture.make_job(context)

        runtime = self.root / "invent-resume-runtime"
        wish = Wish.create("invent-resume", "A top with a recoverable concept")
        tools = WorkshopTools(
            invent=invent,
            make=make,
            playtest=self.fixture.passing_playtest,
            instructions=DefaultInstructions(),
        )
        first = self.workshop(runtime, tools=tools).run(wish, playtest_rounds=1)
        resumed = self.workshop(runtime, tools=tools).resume(wish)

        self.assertEqual((first.status, first.job), ("waiting", "invent"))
        self.assertEqual((resumed.status, resumed.job), ("waiting", "instructions"))
        self.assertEqual(calls, {"invent": 2, "make": 1})
        self.assertNotEqual(workspaces[0], workspaces[1])
        self.assertTrue(all("attempts" in path.parts for path in workspaces))

    def test_custom_make_resume_keeps_invent_and_exact_later_feedback(self):
        calls = {"invent": 0, "make": 0}
        round_two_feedback = []

        def invent(context):
            calls["invent"] += 1
            return self.fixture.invent_job(context)

        def make(context):
            calls["make"] += 1
            if context.round == 2:
                round_two_feedback.append(
                    tuple(item.to_dict() for item in context.feedback)
                )
                if len(round_two_feedback) == 1:
                    raise WaitingFor(
                        Need("make", "cad", "Make paused.", "Resume Make.")
                    )
            return self.fixture.make_job(context)

        runtime = self.root / "make-resume-runtime"
        wish = Wish.create("make-resume", "A spinner improved by exact feedback")
        tools = WorkshopTools(
            invent=invent,
            instructions=DefaultInstructions(),
        )
        first_workshop = self.workshop(
            runtime,
            tools=tools,
            make=make,
            playtest=self.fixture.playtest_job,
        )
        first = first_workshop.run(wish, playtest_rounds=2)
        resumed = self.workshop(
            runtime,
            tools=tools,
            make=make,
            playtest=self.fixture.playtest_job,
        ).resume(wish)

        self.assertEqual((first.status, first.job, first.round), ("waiting", "make", 2))
        self.assertEqual((resumed.status, resumed.job), ("waiting", "instructions"))
        self.assertEqual(calls["invent"], 1)
        self.assertEqual(round_two_feedback[0], round_two_feedback[1])
        self.assertTrue(round_two_feedback[0])

    def test_custom_playtest_resume_uses_nonstandard_exact_made_root(self):
        calls = {"make": 0, "playtest": 0}
        roots = []
        playtest_workspaces = []

        def make(context):
            calls["make"] += 1
            made = self.fixture.make_job(context)
            unusual = context.workspace / "nested" / "custom-artifact"
            unusual.parent.mkdir(parents=True, exist_ok=True)
            made.artifact_root.rename(unusual)
            from inventor_workshop.jobs import Made

            return Made.from_root(unusual, made.product)

        def playtest(context):
            calls["playtest"] += 1
            roots.append(context.made.artifact_root)
            playtest_workspaces.append(context.workspace)
            if calls["playtest"] == 1:
                raise WaitingFor(
                    Need("playtest", "players", "Players paused.", "Resume Players.")
                )
            return self.fixture.passing_playtest(context)

        runtime = self.root / "playtest-resume-runtime"
        wish = Wish.create("playtest-resume", "A custom moving machine")
        tools = WorkshopTools(
            invent=self.fixture.invent_job,
            instructions=DefaultInstructions(),
        )
        first = self.workshop(
            runtime, tools=tools, make=make, playtest=playtest
        ).run(wish, playtest_rounds=1)
        resumed = self.workshop(
            runtime, tools=tools, make=make, playtest=playtest
        ).resume(wish)

        self.assertEqual((first.status, first.job), ("waiting", "playtest"))
        self.assertEqual((resumed.status, resumed.job), ("waiting", "instructions"))
        self.assertEqual(calls, {"make": 1, "playtest": 2})
        self.assertEqual(roots[0], roots[1])
        self.assertNotEqual(playtest_workspaces[0], playtest_workspaces[1])

    def test_tampered_or_symlinked_made_checkpoint_fails_before_playtest(self):
        for mode in ("tamper", "symlink"):
            with self.subTest(mode=mode):
                runtime = self.root / (mode + "-checkpoint-runtime")
                calls = {"playtest": 0}

                def waiting_playtest(context):
                    calls["playtest"] += 1
                    raise WaitingFor(
                        Need("playtest", "players", "Paused.", "Resume.")
                    )

                wish = Wish.create(mode + "-checkpoint", "A checkpoint-bound top")
                tools = WorkshopTools(
                    invent=self.fixture.invent_job,
                    make=self.fixture.make_job,
                    playtest=waiting_playtest,
                    instructions=DefaultInstructions(),
                )
                self.workshop(runtime, tools=tools).run(wish, playtest_rounds=1)
                state = Runtime(runtime / "workshop.sqlite3")
                made_event = next(
                    event
                    for event in state.events(wish.product_id)
                    if event["from_stage"] == "make"
                    and event["to_stage"] == "playtest"
                )
                checkpoint = (
                    runtime
                    / "runs"
                    / wish.product_id
                    / made_event["payload"]["made_checkpoint_path"]
                )
                if mode == "tamper":
                    checkpoint.write_text("{}\n", encoding="utf-8")
                else:
                    backup = checkpoint.with_suffix(".backup")
                    checkpoint.rename(backup)
                    checkpoint.symlink_to(backup.name)

                with self.assertRaises(ContractError):
                    self.workshop(runtime, tools=tools).resume(wish)
                self.assertEqual(calls["playtest"], 1)

    def test_legacy_playtest_without_exact_made_checkpoint_fails_actionably(self):
        runtime = self.root / "legacy-playtest-runtime"
        wish = Wish.create("legacy-playtest", "A legacy Playtest boundary")
        calls = {"playtest": 0}

        def forbidden_playtest(context):
            del context
            calls["playtest"] += 1
            raise AssertionError("legacy bytes must not enter Playtest")

        workshop = self.workshop(
            runtime,
            tools=WorkshopTools(
                invent=self.fixture.invent_job,
                make=self.fixture.make_job,
                playtest=forbidden_playtest,
            ),
        )
        state = Runtime(runtime / "workshop.sqlite3")
        metadata = {
            "wish": wish.to_dict(),
            "inventor_id": workshop.inventor_id,
            "taste_sha256": workshop.taste.sha256,
            "blueprint_sha256": workshop.blueprint.sha256,
            "lane": workshop.lane,
            "customization_level": workshop.customization_level,
            "playtest_rounds": 1,
        }
        state.register_product(wish.product_id, "wish", metadata)
        run_root = runtime / "runs" / wish.product_id
        run_root.mkdir(parents=True)
        invented = self.fixture.invent_job(
            InventContext(wish, workshop.taste, workshop.blueprint, run_root / "invent")
        )
        lease = state.acquire_lease(wish.product_id, "legacy-fixture")
        try:
            state._transition(
                wish.product_id,
                "wish",
                "invent",
                0,
                None,
                {"status": "working", "round": 1},
                lease,
            )
            state._transition(
                wish.product_id,
                "invent",
                "make",
                1,
                None,
                {
                    "status": "working",
                    "round": 1,
                    "concept_sha256": invented.concept_sha256,
                    "invent_score": invented.score,
                    "invent_target_score": invented.target_score,
                    "invented": invented.to_dict(),
                },
                lease,
            )
            state._transition(
                wish.product_id,
                "make",
                "playtest",
                2,
                "a" * 64,
                {
                    "status": "working",
                    "round": 1,
                    "artifact_sha256": "a" * 64,
                },
                lease,
            )
        finally:
            state.release_lease(wish.product_id, lease)

        with self.assertRaisesRegex(ContractError, "no exact Made checkpoint"):
            workshop.resume(wish)
        self.assertEqual(calls["playtest"], 0)

    def test_checkpoint_cannot_be_rebound_to_another_product_or_round(self):
        def waiting_playtest(context):
            raise WaitingFor(
                Need("playtest", "players", "Paused.", "Resume.")
            )

        tools = WorkshopTools(
            invent=self.fixture.invent_job,
            make=self.fixture.make_job,
            playtest=waiting_playtest,
            instructions=DefaultInstructions(),
        )

        source_runtime = self.root / "swap-source-runtime"
        source_wish = Wish.create("swap-source", "The source product")
        source_workshop = self.workshop(source_runtime, tools=tools)
        source_workshop.run(source_wish, playtest_rounds=2)
        source_state = Runtime(source_runtime / "workshop.sqlite3")
        source_event = next(
            event
            for event in source_state.events(source_wish.product_id)
            if event["from_stage"] == "make" and event["to_stage"] == "playtest"
        )

        # A valid event chain may still cite the wrong product's checkpoint;
        # original bindings must reject it before rebuilding Made or calling a hook.
        target_runtime = self.root / "swap-target-runtime"
        target_wish = Wish.create("swap-target", "The target product")
        target_workshop = self.workshop(target_runtime, tools=tools)
        target_state = Runtime(target_runtime / "workshop.sqlite3")
        target_metadata = {
            "wish": target_wish.to_dict(),
            "inventor_id": target_workshop.inventor_id,
            "taste_sha256": target_workshop.taste.sha256,
            "blueprint_sha256": target_workshop.blueprint.sha256,
            "lane": target_workshop.lane,
            "customization_level": target_workshop.customization_level,
            "playtest_rounds": 2,
        }
        target_state.register_product(target_wish.product_id, "wish", target_metadata)
        target_run = target_runtime / "runs" / target_wish.product_id
        target_checkpoint = target_run / source_event["payload"]["made_checkpoint_path"]
        target_checkpoint.parent.mkdir(parents=True)
        source_checkpoint = (
            source_runtime
            / "runs"
            / source_wish.product_id
            / source_event["payload"]["made_checkpoint_path"]
        )
        target_checkpoint.write_bytes(source_checkpoint.read_bytes())
        target_checkpoint.chmod(0o600)
        invented = self.fixture.invent_job(
            InventContext(
                target_wish,
                target_workshop.taste,
                target_workshop.blueprint,
                target_run / "invent",
            )
        )
        lease = target_state.acquire_lease(target_wish.product_id, "swap-fixture")
        try:
            target_state._transition(
                target_wish.product_id,
                "wish",
                "invent",
                0,
                None,
                {"status": "working", "round": 1},
                lease,
            )
            target_state._transition(
                target_wish.product_id,
                "invent",
                "make",
                1,
                None,
                {
                    "status": "working",
                    "round": 1,
                    "concept_sha256": invented.concept_sha256,
                    "invent_score": invented.score,
                    "invent_target_score": invented.target_score,
                    "invented": invented.to_dict(),
                },
                lease,
            )
            target_state._transition(
                target_wish.product_id,
                "make",
                "playtest",
                2,
                source_event["artifact_sha256"],
                dict(source_event["payload"]),
                lease,
            )
        finally:
            target_state.release_lease(target_wish.product_id, lease)
        with self.assertRaisesRegex(ContractError, "original Workshop bindings"):
            target_workshop.resume(target_wish)

        # The same exact checkpoint cannot be relabelled as the next round.
        round_runtime = self.root / "swap-round-runtime"
        round_wish = Wish.create("swap-round", "A round-bound product")
        round_workshop = self.workshop(round_runtime, tools=tools)
        round_workshop.run(round_wish, playtest_rounds=2)
        round_state = Runtime(round_runtime / "workshop.sqlite3")
        first_event = next(
            event
            for event in round_state.events(round_wish.product_id)
            if event["from_stage"] == "make" and event["to_stage"] == "playtest"
        )
        feedback = Feedback(
            "retry",
            "mechanism",
            "improve",
            "The first round needs work.",
            "Improve the mechanism.",
        )
        lease = round_state.acquire_lease(round_wish.product_id, "round-fixture")
        try:
            product = round_state.get_product(round_wish.product_id)
            round_state._transition(
                round_wish.product_id,
                "playtest",
                "make",
                product["revision"],
                first_event["artifact_sha256"],
                {
                    "status": "working",
                    "round": 2,
                    "feedback": [feedback.to_dict()],
                },
                lease,
            )
            product = round_state.get_product(round_wish.product_id)
            rebound = dict(first_event["payload"])
            rebound["round"] = 2
            # Preserve the honest checkpoint round so the filename lookup works;
            # payload binding must still reject round one as round two.
            rebound["made_checkpoint_round"] = 1
            round_state._transition(
                round_wish.product_id,
                "make",
                "playtest",
                product["revision"],
                first_event["artifact_sha256"],
                rebound,
                lease,
            )
        finally:
            round_state.release_lease(round_wish.product_id, lease)
        with self.assertRaisesRegex(ContractError, "different Playtest round"):
            round_workshop.resume(round_wish)

    def test_latest_playtest_wait_cannot_swap_its_made_reference(self):
        runtime = self.root / "latest-ref-runtime"
        wish = Wish.create("latest-ref", "A Playtest with one exact Made input")

        def waiting_playtest(context):
            raise WaitingFor(
                Need("playtest", "players", "Paused.", "Resume.")
            )

        tools = WorkshopTools(
            invent=self.fixture.invent_job,
            make=self.fixture.make_job,
            playtest=waiting_playtest,
        )
        workshop = self.workshop(runtime, tools=tools)
        workshop.run(wish, playtest_rounds=1)
        state = Runtime(runtime / "workshop.sqlite3")
        product = state.get_product(wish.product_id)
        latest = state.events(wish.product_id)[-1]
        payload = dict(latest["payload"])
        payload["made_checkpoint_sha256"] = "f" * 64
        lease = state.acquire_lease(wish.product_id, "mismatched-head")
        try:
            state._transition(
                wish.product_id,
                "playtest",
                "playtest",
                product["revision"],
                product["artifact_sha256"],
                payload,
                lease,
            )
        finally:
            state.release_lease(wish.product_id, lease)

        with self.assertRaisesRegex(ContractError, "different Made checkpoint"):
            workshop.resume(wish)

    def test_orphan_made_checkpoint_before_event_is_ignored(self):
        runtime = self.root / "made-orphan-runtime"
        wish = Wish.create("made-orphan", "A top after a checkpoint crash")
        tools = WorkshopTools(
            invent=self.fixture.invent_job,
            make=self.fixture.make_job,
            playtest=self.fixture.passing_playtest,
            instructions=DefaultInstructions(),
        )
        crashed = self.workshop(runtime, tools=tools)
        original_advance = crashed._advance

        def fail_before_playtest(state, product_id, to_job, **kwargs):
            if to_job == "playtest":
                raise RuntimeError("killed after Made checkpoint")
            return original_advance(state, product_id, to_job, **kwargs)

        crashed._advance = fail_before_playtest
        with self.assertRaisesRegex(RuntimeError, "Made checkpoint"):
            crashed.run(wish, playtest_rounds=1)

        resumed = self.workshop(runtime, tools=tools).resume(wish)
        checkpoints = list(
            (runtime / "runs" / wish.product_id / "checkpoints").glob("made-*.json")
        )
        self.assertEqual((resumed.status, resumed.job), ("waiting", "instructions"))
        self.assertEqual(len(checkpoints), 2)
        state = Runtime(runtime / "workshop.sqlite3")
        referenced = {
            event["payload"].get("made_checkpoint_path")
            for event in state.events(wish.product_id)
        }
        self.assertEqual(len({item for item in referenced if item}), 1)

    def test_orphan_instructions_checkpoint_before_event_is_ignored(self):
        runtime = self.root / "instructions-orphan-runtime"
        wish = Wish.create(
            "instructions-orphan", "A top after an Instructions checkpoint crash"
        )
        tools = WorkshopTools(
            invent=self.fixture.invent_job,
            make=self.fixture.make_job,
            playtest=self.fixture.passing_playtest,
            instructions=DefaultInstructions(),
        )
        crashed = self.workshop(runtime, tools=tools)
        original_advance = crashed._advance

        def fail_before_instructions(state, product_id, to_job, **kwargs):
            if to_job == "instructions":
                raise RuntimeError("killed after Instructions checkpoint")
            return original_advance(state, product_id, to_job, **kwargs)

        crashed._advance = fail_before_instructions
        with self.assertRaisesRegex(RuntimeError, "Instructions checkpoint"):
            crashed.run(wish, playtest_rounds=1)

        resumed = self.workshop(runtime, tools=tools).resume(wish)
        checkpoints = list(
            (runtime / "runs" / wish.product_id / "checkpoints").glob(
                "instructions-*.json"
            )
        )
        self.assertEqual((resumed.status, resumed.job), ("waiting", "instructions"))
        self.assertEqual(len(checkpoints), 2)

    def test_working_instructions_bound_seal_is_reconciled_without_regeneration(self):
        runtime = self.root / "working-instructions-runtime"
        wish = Wish.create("working-instructions", "A top with a killed page writer")
        standard_root = runtime / "runs" / wish.product_id / "instructions"

        def killed_site(context, root, manifest):
            del context, root, manifest
            raise RuntimeError("killed after seal")

        tools = WorkshopTools(
            invent=self.fixture.invent_job,
            make=self.fixture.make_job,
            playtest=self.fixture.passing_playtest,
            instructions=DefaultInstructions(site_writer=killed_site),
        )
        with self.assertRaisesRegex(RuntimeError, "after seal"):
            self.workshop(runtime, tools=tools).run(wish, playtest_rounds=1)
        original_bytes = {
            path.relative_to(standard_root): path.read_bytes()
            for path in standard_root.rglob("*")
            if path.is_file()
        }

        resumed = self.workshop(
            runtime,
            tools=WorkshopTools(
                invent=self.fixture.invent_job,
                make=self.fixture.make_job,
                playtest=self.fixture.passing_playtest,
                instructions=DefaultInstructions(),
            ),
        ).resume(wish)

        self.assertEqual((resumed.status, resumed.job), ("waiting", "instructions"))
        self.assertEqual(
            original_bytes,
            {
                path.relative_to(standard_root): path.read_bytes()
                for path in standard_root.rglob("*")
                if path.is_file()
            },
        )
        latest = Runtime(runtime / "workshop.sqlite3").events(wish.product_id)[-1]
        self.assertEqual(latest["payload"]["instructions_root"], "instructions")
        self.assertEqual(len(latest["payload"]["instructions_sha256"]), 64)
        self.assertTrue(
            (runtime / "runs" / wish.product_id / "instructions-manifest.json").is_file()
        )

    def test_working_instructions_unbound_sealed_tree_is_left_as_orphan(self):
        runtime = self.root / "unbound-instructions-runtime"
        wish = Wish.create("unbound-instructions", "A top with an unbound manual")

        def unbound_writer(context):
            context.workspace.mkdir(parents=True)
            (context.workspace / "UNTRUSTED.txt").write_text(
                "not event-bound\n", encoding="utf-8"
            )
            manifest = build_artifact_manifest(
                context.workspace, created_at="content-addressed"
            )
            seal = context.workspace.parent / (
                context.workspace.name + "-manifest.json"
            )
            seal.write_text(
                json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            # Deliberately violate the new bind-before-effect contract.
            raise RuntimeError("killed with an unbound seal")

        tools = WorkshopTools(
            invent=self.fixture.invent_job,
            make=self.fixture.make_job,
            playtest=self.fixture.passing_playtest,
            instructions=unbound_writer,
        )
        with self.assertRaisesRegex(RuntimeError, "unbound seal"):
            self.workshop(runtime, tools=tools).run(wish, playtest_rounds=1)
        standard = runtime / "runs" / wish.product_id / "instructions"
        original = (standard / "UNTRUSTED.txt").read_bytes()

        resumed = self.workshop(
            runtime,
            tools=WorkshopTools(
                invent=self.fixture.invent_job,
                make=self.fixture.make_job,
                playtest=self.fixture.passing_playtest,
                instructions=DefaultInstructions(),
            ),
        ).resume(wish)

        self.assertEqual((resumed.status, resumed.job), ("waiting", "instructions"))
        self.assertEqual((standard / "UNTRUSTED.txt").read_bytes(), original)
        attempts = runtime / "runs" / wish.product_id / "attempts"
        self.assertTrue(any(attempts.glob("instructions-r001-*-attempt*")))

    def test_instructions_seal_fsyncs_its_destination_directory(self):
        root = self.root / "durable-instructions"
        root.mkdir()
        (root / "INSTRUCTIONS.md").write_text("Exact manual.\n", encoding="utf-8")
        manifest = build_artifact_manifest(root, created_at="content-addressed")
        observed_directory_fsync = False
        real_fsync = os.fsync

        def observe(descriptor):
            nonlocal observed_directory_fsync
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                observed_directory_fsync = True
            return real_fsync(descriptor)

        with mock.patch(
            "inventor_workshop.instructions.os.fsync", side_effect=observe
        ):
            _write_manifest_once(root, manifest)
        self.assertTrue(observed_directory_fsync)

    def test_active_lease_blocks_resume_and_lost_guard_never_starts_hook(self):
        runtime = self.root / "lease-resume-runtime"
        wish = Wish.create("lease-resume", "A fenced Invent restart")

        def waiting_invent(context):
            raise WaitingFor(
                Need("invent", "model", "Invent paused.", "Resume Invent.")
            )

        tools = WorkshopTools(invent=waiting_invent)
        self.workshop(runtime, tools=tools).run(wish, playtest_rounds=1)
        state = Runtime(runtime / "workshop.sqlite3")
        token = state.acquire_lease(wish.product_id, "other-live-worker")
        try:
            with self.assertRaises(LeaseBusy):
                self.workshop(runtime, tools=tools).resume(wish)
        finally:
            state.release_lease(wish.product_id, token)

        hook_calls = 0
        guarded_wish = Wish.create("lost-before-hook", "A stale worker")

        def forbidden_invent(context):
            del context
            nonlocal hook_calls
            hook_calls += 1
            raise AssertionError("lost guard must not start Invent")

        guarded = self.workshop(
            self.root / "lost-before-hook-runtime",
            tools=WorkshopTools(invent=forbidden_invent),
        )
        original_assert = LeaseGuard.assert_current
        assertions = 0

        def lose_on_pre_hook(guard):
            nonlocal assertions
            assertions += 1
            if assertions == 3:
                raise StateConflict("injected lease loss")
            return original_assert(guard)

        with mock.patch.object(LeaseGuard, "assert_current", new=lose_on_pre_hook):
            with self.assertRaisesRegex(StateConflict, "injected lease loss"):
                guarded.run(guarded_wish, playtest_rounds=1)
        self.assertEqual(hook_calls, 0)

    def test_resume_fails_closed_if_stage_advances_during_lease_acquire(self):
        runtime = self.root / "stage-race-runtime"
        wish = Wish.create("stage-race", "A stage that advances during resume")

        def waiting_invent(context):
            raise WaitingFor(
                Need("invent", "model", "Paused.", "Resume.")
            )

        calls = {"invent": 0, "make": 0}

        def counted_invent(context):
            calls["invent"] += 1
            return self.fixture.invent_job(context)

        def forbidden_make(context):
            del context
            calls["make"] += 1
            raise AssertionError("raced resume must not enter Make")

        first_tools = WorkshopTools(invent=waiting_invent)
        self.workshop(runtime, tools=first_tools).run(wish, playtest_rounds=1)
        resumed = self.workshop(
            runtime,
            tools=WorkshopTools(invent=counted_invent, make=forbidden_make),
        )
        invented = self.fixture.invent_job(
            InventContext(
                wish,
                resumed.taste,
                resumed.blueprint,
                runtime / "race-invent",
            )
        )
        original_acquire = Runtime.acquire_lease
        advanced = False

        def acquire_and_advance(store, product_id, holder, ttl_seconds=2700):
            nonlocal advanced
            if holder == "toy-workshop-resume" and not advanced:
                advanced = True
                temporary = original_acquire(
                    store, product_id, "advancing-worker", ttl_seconds
                )
                product = store.get_product(product_id)
                store._transition(
                    product_id,
                    "invent",
                    "make",
                    product["revision"],
                    None,
                    {
                        "status": "working",
                        "round": 1,
                        "concept_sha256": invented.concept_sha256,
                        "invent_score": invented.score,
                        "invent_target_score": invented.target_score,
                        "invented": invented.to_dict(),
                    },
                    temporary,
                )
                store.release_lease(product_id, temporary)
            return original_acquire(store, product_id, holder, ttl_seconds)

        with mock.patch.object(Runtime, "acquire_lease", new=acquire_and_advance):
            with self.assertRaisesRegex(StateConflict, "stage advanced"):
                resumed.resume(wish)
        self.assertEqual(calls, {"invent": 0, "make": 0})

    def test_runs_symlink_cannot_escape_runtime_root(self):
        runtime = self.root / "symlink-runs-runtime"
        outside = self.root / "outside-runs"
        outside.mkdir()
        Runtime(runtime / "workshop.sqlite3")
        (runtime / "runs").symlink_to(outside, target_is_directory=True)
        wish = Wish.create("symlink-runs", "A product that must stay in runtime")

        with self.assertRaisesRegex(ContractError, "runs directory"):
            self.workshop(runtime).run(wish, playtest_rounds=1)
        self.assertFalse((outside / wish.product_id).exists())

    def test_taste_mutation_during_invent_is_never_accepted(self):
        runtime = self.root / "taste-race-runtime"
        wish = Wish.create("taste-race", "A concept bound to exact Taste")

        def mutating_invent(context):
            invented = self.fixture.invent_job(context)
            (self.inventor / "TASTE.md").write_text(
                "---\nname: Changed\ndescription: Changed during Invent.\n---\n# Changed\n",
                encoding="utf-8",
            )
            return invented

        with self.assertRaises(ContractError):
            self.workshop(
                runtime, tools=WorkshopTools(invent=mutating_invent)
            ).run(wish, playtest_rounds=1)
        state = Runtime(runtime / "workshop.sqlite3")
        self.assertEqual(state.get_product(wish.product_id)["stage"], "invent")

    def test_taste_mutation_after_make_playtest_or_instructions_is_not_accepted(self):
        taste_path = self.inventor / "TASTE.md"
        original_taste = taste_path.read_bytes()

        def mutate():
            taste_path.write_text(
                "---\nname: Changed\ndescription: Changed during a stage.\n---\n# Changed\n",
                encoding="utf-8",
            )

        for stage in ("make", "playtest", "instructions"):
            with self.subTest(stage=stage):
                taste_path.write_bytes(original_taste)
                runtime = self.root / ("taste-after-" + stage)
                wish = Wish.create(
                    "taste-after-" + stage,
                    "A product bound to Taste through " + stage,
                )

                def make(context):
                    made = self.fixture.make_job(context)
                    if stage == "make":
                        mutate()
                    return made

                def playtest(context):
                    result = self.fixture.passing_playtest(context)
                    if stage == "playtest":
                        mutate()
                    return result

                base_instructions = DefaultInstructions(
                    site_writer=self.fixture.site_writer
                )

                def instructions(context):
                    result = base_instructions(context)
                    if stage == "instructions":
                        mutate()
                    return result

                tools = WorkshopTools(
                    invent=self.fixture.invent_job,
                    make=make,
                    playtest=playtest,
                    instructions=instructions,
                )
                with self.assertRaises(ContractError):
                    self.workshop(runtime, tools=tools).run(
                        wish, playtest_rounds=1
                    )
                product = Runtime(runtime / "workshop.sqlite3").get_product(
                    wish.product_id
                )
                self.assertEqual(product["stage"], stage)
        taste_path.write_bytes(original_taste)

    def test_stopped_playtest_and_deliver_are_not_resumable(self):
        runtime = self.root / "stopped-runtime"
        wish = Wish.create("stopped-run", "A top that needs another allowance")
        stopped = self.workshop(
            runtime,
            tools=WorkshopTools(
                invent=self.fixture.invent_job,
                make=self.fixture.make_job,
                playtest=self.fixture.playtest_job,
                instructions=DefaultInstructions(),
            ),
        ).run(wish, playtest_rounds=1)
        self.assertEqual(stopped.status, "stopped")
        with self.assertRaisesRegex(ContractError, "exhausted"):
            self.workshop(runtime).resume(wish)

    def test_wish_rejects_dot_segment_product_ids(self):
        for product_id in (".", ".."):
            with self.subTest(product_id=product_id):
                with self.assertRaisesRegex(ContractError, "dot segment"):
                    Wish.create(product_id, "Unsafe path")


if __name__ == "__main__":
    unittest.main()
