import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from inventor_workshop.jobs import Invented
from inventor_workshop.make import Wish
from inventor_workshop.manager import (
    TasteFit,
    WorkshopManager,
    create_shortlist,
    register_workshop_engine,
)
from inventor_workshop.manager_execution import execute_manager_workshop
from inventor_workshop.scaffold import scaffold_inventor
from inventor_workshop.workshop import WorkshopTools


ROOT = Path(__file__).resolve().parents[1]
IDS = ("alice", "bob", "eve", "ivy", "leo")
JUDGE_CONFIG_SHA256 = hashlib.sha256(b"manager execution test judge").hexdigest()


def trusted_test_isolation(command, context):
    del context
    return tuple(command)


def passing_invent(context):
    wish_sha256 = hashlib.sha256(
        json.dumps(
            context.wish.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    return Invented(
        wish_sha256,
        context.taste.sha256,
        context.blueprint.lane,
        {
            "title": "Manager-owned industrial design",
            "summary": "A deterministic accepted concept for contribution RPC tests.",
        },
        100,
        90,
    )


def invent_engine():
    return register_workshop_engine(
        WorkshopTools(invent=passing_invent),
        provider_ids={"invent": "tests.manager-owned-invent-v1"},
    )


def assignment_for(root: Path, inventor_id: str, wish: Wish):
    def retrieve(context):
        return create_shortlist(
            context,
            (inventor_id,),
            retriever="manager-execution-test-index",
            retriever_version="manager-execution-index-1.0.0",
            rationale="The test selected one exact card without running its entrypoint.",
        )

    def judge(context):
        finalist = context.finalists[0]
        return (
            TasteFit(
                finalist.inventor_id,
                finalist.taste.sha256,
                99,
                True,
                "The exact test Wish is assigned to this selected Inventor.",
            ),
        )

    return WorkshopManager(
        root=root,
        retriever=retrieve,
        judge=judge,
        judge_identity="manager-execution-test-judge",
        judge_version="manager-execution-judge-1.0.0",
        judge_config_sha256=JUDGE_CONFIG_SHA256,
    ).assign(wish, playtest_rounds=2)


class ManagerExecutionTest(unittest.TestCase):
    def test_reconcile_action_dispatches_only_deliver_readback(self):
        with tempfile.TemporaryDirectory() as temporary:
            assignment = assignment_for(
                ROOT,
                "alice",
                Wish.create(
                    "manager-reconcile-only",
                    "A saved toy whose carrier handoff needs readback",
                ),
            )
            calls = []

            class Result:
                @staticmethod
                def to_dict():
                    return {
                        "product_id": assignment.wish.product_id,
                        "status": "working",
                        "job": "deliver",
                    }

            class FakeWorkshop:
                def run(self, *args, **kwargs):
                    del args, kwargs
                    raise AssertionError("reconciliation must not run stages")

                def resume(self, *args, **kwargs):
                    del args, kwargs
                    raise AssertionError("reconciliation must not resume stages")

                def reconcile_deliver(self, wish):
                    calls.append(wish)
                    return Result()

            result = execute_manager_workshop(
                assignment,
                action="reconcile",
                runtime_root=Path(temporary).resolve(),
                workshop_factory=lambda *args, **kwargs: FakeWorkshop(),
            )
            self.assertEqual(calls, [assignment.wish])
            self.assertEqual((result["status"], result["job"]), ("working", "deliver"))

    def test_manager_password_never_configures_factory_during_the_initial_engine_pass(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(
            os.environ,
            {"FACTORY_PASSWORD": "manager-owned-test-secret"},
            clear=True,
        ):
            assignment = assignment_for(
                ROOT,
                "alice",
                Wish.create(
                    "manager-local-instructions",
                    "A personal checkers set for a midnight studio",
                ),
            )
            captured = {}

            class Result:
                @staticmethod
                def to_dict():
                    return {
                        "status": "waiting",
                        "job": "instructions",
                        "product_id": assignment.wish.product_id,
                    }

            class FakeWorkshop:
                def run(self, wish, *, playtest_rounds):
                    self.wish = wish
                    self.playtest_rounds = playtest_rounds
                    return Result()

            def workshop_factory(root, lane, **kwargs):
                del root, lane
                captured.update(kwargs)
                return FakeWorkshop()

            execute_manager_workshop(
                assignment,
                runtime_root=Path(temporary).resolve(),
                workshop_factory=workshop_factory,
            )
            engine = captured["trusted_engine"]
            self.assertIsNone(engine.tools.instructions.site_writer)
            self.assertEqual(
                dict(engine.provider_ids)["instructions"],
                "workshop.rewarded-instructions-v1",
            )
            self.assertEqual(len(engine.provider_ids), 5)
            self.assertIsNotNone(engine.provenance)

    def test_hostile_profile_can_mint_a_registry_but_workshop_wish_never_executes_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            inventor = scaffold_inventor(
                root,
                "hostile-registry",
                "Hostile Registry",
                "tries to claim Workshop provider authority",
                lane="moving-machines",
                level="taste-only",
            )
            marker = inventor / "profile-executed"
            (inventor / "run.py").write_text(
                "from pathlib import Path\n"
                "from inventor_workshop import WorkshopTools\n"
                "from inventor_workshop.manager import register_workshop_engine\n"
                "root = Path(__file__).resolve().parent\n"
                "(root / 'profile-executed').write_text('bad', encoding='utf-8')\n"
                "register_workshop_engine(WorkshopTools(invent=lambda value: value))\n",
                encoding="utf-8",
            )
            assignment = assignment_for(
                root,
                "hostile-registry",
                Wish.create("hostile-registry-wish", "A tiny hand-cranked surprise"),
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_AGENT_WORKERS": "disabled"}, clear=True
            ), mock.patch(
                "subprocess.Popen",
                side_effect=AssertionError("Manager execution must not spawn profile.py"),
            ):
                result = execute_manager_workshop(
                    assignment,
                    runtime_root=root / "manager-runtime",
                )
            self.assertEqual((result["status"], result["job"]), ("waiting", "invent"))
            self.assertFalse(marker.exists())
            self.assertEqual(
                result["manager_assignment"]["assignment_sha256"],
                assignment.assignment_sha256,
            )

    def test_all_five_builtins_run_shared_engine_in_manager_process(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(
            os.environ, {"WORKSHOP_AGENT_WORKERS": "disabled"}, clear=True
        ), mock.patch(
            "subprocess.Popen",
            side_effect=AssertionError("taste-only execution must not spawn a profile"),
        ), mock.patch(
            "inventor_workshop.manager_execution.manager_service_forbidden_read_paths",
            side_effect=AssertionError(
                "taste-only execution must not inspect Manager service distributions"
            ),
        ):
            runtime = Path(temporary).resolve()
            for inventor_id in IDS:
                with self.subTest(inventor_id=inventor_id):
                    assignment = assignment_for(
                        ROOT,
                        inventor_id,
                        Wish.create(
                            "manager-owned-%s" % inventor_id,
                            "A Wish routed through the shared Workshop engine",
                        ),
                    )
                    result = execute_manager_workshop(
                        assignment,
                        runtime_root=runtime / inventor_id,
                    )
                    self.assertEqual(result["status"], "waiting")
                    self.assertEqual(result["job"], "invent")
                    self.assertEqual(
                        result["manager_assignment"]["assignment_sha256"],
                        assignment.assignment_sha256,
                    )

    def test_custom_make_runs_only_its_bounded_stage_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            inventor = scaffold_inventor(
                root,
                "custom-worker",
                "Custom Worker",
                "declares its own Make hook",
                lane="moving-machines",
                level="custom-make",
            )
            profile_marker = inventor / "profile-executed"
            provider_code = root / "manager-provider.py"
            provider_code.write_text(
                "raise AssertionError('Manager provider must not run in child')\n",
                encoding="utf-8",
            )
            (inventor / "run.py").write_text(
                "from pathlib import Path\n"
                "(Path(__file__).resolve().parent / 'profile-executed').write_text('bad')\n",
                encoding="utf-8",
            )
            # The assignment must bind the final implementation bytes.
            assignment = assignment_for(
                root,
                "custom-worker",
                Wish.create("custom-worker-wish-2", "A custom mechanical surprise"),
            )
            observed = {}

            def isolated(command, context):
                observed["forbidden"] = context.forbidden_read_paths
                return tuple(command)

            with mock.patch.dict(
                os.environ, {"WORKSHOP_AGENT_WORKERS": "disabled"}, clear=True
            ), mock.patch(
                "inventor_workshop.manager_execution.manager_service_forbidden_read_paths",
                return_value=(provider_code,),
            ):
                result = execute_manager_workshop(
                    assignment,
                    runtime_root=root / "manager-runtime",
                    trusted_engine=invent_engine(),
                    contribution_isolation=isolated,
                )
            self.assertEqual((result["status"], result["job"]), ("waiting", "make"))
            self.assertEqual(result["needs"][0]["capability"], "inventor-make")
            self.assertFalse(profile_marker.exists())
            self.assertEqual(observed["forbidden"], (provider_code,))

    def test_custom_playtest_still_passes_through_common_release_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            inventor = scaffold_inventor(
                root,
                "custom-player",
                "Custom Player",
                "declares custom mechanical design and AI play",
                lane="moving-machines",
                level="custom-playtest",
            )
            (inventor / "src/custom_player/inventor.py").write_text(
                '''import hashlib
import json

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.jobs import Made, Playtested
from inventor_workshop.models import PlaytestResult
from inventor_workshop.playtest import Playtest


def make(context):
    context.workspace.mkdir(mode=0o700)
    (context.workspace / "toy.txt").write_text(
        "exact custom mechanical design\\n", encoding="utf-8"
    )
    return Made.from_root(
        context.workspace,
        {
            "title": "Custom Waver",
            "summary": "A deliberately incomplete moving-machine fixture.",
            "lane": context.blueprint.lane,
        },
    )


def playtest(context):
    context.workspace.mkdir(mode=0o700)
    relative = "custom-player.json"
    evidence = {
        "evidence_class": "ai-simulation",
        "artifact_sha256": context.made.artifact_sha256,
        "finding": "One custom AI player returned a passing observation.",
    }
    payload = json.dumps(evidence, sort_keys=True) + "\\n"
    (context.workspace / relative).write_text(payload, encoding="utf-8")
    result = PlaytestResult.create(
        "custom-observation",
        True,
        context.made.artifact_sha256,
        evidence,
        "custom-ai-player",
        "1.0.0",
        "f" * 64,
        relative,
        hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )
    return Playtested(
        Playtest(
            context.made.artifact_manifest,
            (result,),
            evidence_manifest=build_artifact_manifest(
                context.workspace, created_at="content-addressed"
            ),
        )
    )
''',
                encoding="utf-8",
            )
            assignment = assignment_for(
                root,
                "custom-player",
                Wish.create("custom-player-wish", "A custom waving creature"),
            )
            with mock.patch.dict(
                os.environ, {"WORKSHOP_AGENT_WORKERS": "disabled"}, clear=True
            ):
                result = execute_manager_workshop(
                    assignment,
                    runtime_root=root / "manager-runtime",
                    trusted_engine=invent_engine(),
                    contribution_isolation=trusted_test_isolation,
                )
            self.assertEqual((result["status"], result["job"]), ("waiting", "playtest"))
            self.assertEqual(
                tuple(need["capability"] for need in result["needs"]),
                ("agent-playtest", "motion-test", "mechanical-test", "print-test"),
            )


if __name__ == "__main__":
    unittest.main()
