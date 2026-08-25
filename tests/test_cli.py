import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import inventor_workshop
from inventor_workshop.cli import (
    _ReadOnlyWorkshopStore,
    _default_workshop_root,
    _inventor_process_environment,
    _managed_child_run,
    _publish_inventor_draft,
    _promote_factory_intent,
    _resume_factory_instructions,
    _resume_inventor,
    _run_inventor,
    _save_manager_assignment,
    _status_receipt,
    main,
    parser,
)
from inventor_workshop.handoff import (
    ManagerAssignmentHandoff,
    bind_manager_assignment_result,
)
from inventor_workshop.instructions import DefaultInstructions
from inventor_workshop.errors import AmbiguousEffectError, WorkshopError
from inventor_workshop.manager import (
    TasteFit,
    create_shortlist,
    discover_inventor_catalog,
)
from inventor_workshop.make import Wish
from inventor_workshop.models import Receipt
from inventor_workshop.runtime import Runtime
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint
from inventor_workshop.workshop import Workshop, WorkshopTools
from tests.test_toy_workshop import ToyWorkshopTest


class CliTest(unittest.TestCase):
    @staticmethod
    def inventor_identity(
        root: Path,
        inventor_id: str,
        *,
        lane: str = "moving-machines",
        level: str = "taste-only",
    ):
        root = Path(root)
        if root.name != inventor_id:
            raise AssertionError("fixture inventor folder must match its id")
        root.mkdir(parents=True, exist_ok=True)
        taste_path = root / "TASTE.md"
        if not taste_path.exists():
            taste_path.write_text(
                "---\n"
                "name: Fixture %s\n" % inventor_id.replace("-", " ").title()
                + "description: Exact fixture identity for CLI tests.\n"
                "---\n"
                "# Fixture Taste\n\n"
                "Prefer one surprising, mechanically legible interaction.\n",
                encoding="utf-8",
            )
        manifest_path = root / "inventor.json"
        if not manifest_path.exists():
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 5,
                        "id": inventor_id,
                        "status": "active",
                        "entrypoint": ["python3", "profile.py"],
                        "capabilities": [lane, level],
                        "checks": [],
                        "source": {"kind": "local"},
                    }
                ),
                encoding="utf-8",
            )
        profile_path = root / "profile.py"
        if not profile_path.exists():
            profile_path.write_text("# exact CLI fixture profile\n", encoding="utf-8")
        card = discover_inventor_catalog(root.parent).card(inventor_id)
        return card, load_taste(root)

    @staticmethod
    def resume_assignment(root, inventor_id, wish, *, playtest_rounds=4):
        card, taste = CliTest.inventor_identity(root, inventor_id)
        return SimpleNamespace(
            wish=wish,
            inventor_id=inventor_id,
            playtest_rounds=playtest_rounds,
            assignment_sha256="a" * 64,
            entrypoint=tuple(card.entrypoint),
            decision=SimpleNamespace(
                decision_sha256="d" * 64,
                selected=SimpleNamespace(
                    card=card,
                    taste=taste,
                ),
            ),
        )

    @staticmethod
    def durable_wait_fixture(
        root: Path,
        *,
        product_id: str = "wish-one",
        stage: str = "make",
        capability: str = "model-and-cad-maker",
        artifact_sha256=None,
        instructions_sha256=None,
        resume_checkpoint_sha256=None,
        state_status="waiting",
        transition=True,
        assignment_rounds=4,
        metadata_rounds=None,
    ):
        inventor_id = "mira"
        inventor_root = root / "inventors" / inventor_id
        inventor_root.mkdir(parents=True)
        (inventor_root / "TASTE.md").write_text(
            "---\n"
            "name: Mira\n"
            "description: Kinetic desk toys, but not board games.\n"
            "---\n"
            "# Mira's Taste\n\n"
            "Make one surprising motion feel inevitable.\n",
            encoding="utf-8",
        )
        (inventor_root / "inventor.json").write_text(
            json.dumps(
                {
                    "schema_version": 5,
                    "id": inventor_id,
                    "status": "active",
                    "entrypoint": ["python3", "profile.py"],
                    "capabilities": ["moving-machines", "taste-only"],
                    "checks": [],
                    "source": {"kind": "local"},
                }
            ),
            encoding="utf-8",
        )
        (inventor_root / "profile.py").write_text(
            "# fixture profile\n", encoding="utf-8"
        )
        catalog = discover_inventor_catalog(root)
        card = catalog.card(inventor_id)
        taste = load_taste(inventor_root)
        wish = Wish.create(product_id, "A tiny moon that rolls")
        assignment = SimpleNamespace(
            wish=wish,
            inventor_id=inventor_id,
            playtest_rounds=assignment_rounds,
            assignment_sha256="a" * 64,
            entrypoint=tuple(card.entrypoint),
            decision=SimpleNamespace(
                decision_sha256="d" * 64,
                selected=SimpleNamespace(card=card, taste=taste),
            ),
        )
        _save_manager_assignment(assignment)
        runtime = Runtime(inventor_root / ".workshop" / "workshop.sqlite3")
        (
            inventor_root / ".workshop" / "runs" / product_id
        ).mkdir(parents=True)
        runtime.register_product(
            product_id,
            "wish",
            {
                "wish": wish.to_dict(),
                "inventor_id": inventor_id,
                "taste_sha256": taste.sha256,
                "blueprint_sha256": ToyBlueprint.for_lane(
                    "moving-machines"
                ).sha256,
                "lane": "moving-machines",
                "customization_level": "taste-only",
                "playtest_rounds": (
                    assignment_rounds
                    if metadata_rounds is None
                    else metadata_rounds
                ),
            },
        )
        lease = runtime.acquire_lease(product_id, "fixture")
        product = runtime.get_product(product_id)
        payload = {"status": state_status, "round": 1}
        if state_status == "waiting":
            payload["needs"] = [
                {
                    "job": stage,
                    "capability": capability,
                    "reason": "The shared provider is not connected.",
                    "instructions": "Connect the shared provider, then continue this exact Wish.",
                }
            ]
        if instructions_sha256 is not None:
            payload["instructions_sha256"] = instructions_sha256
        if resume_checkpoint_sha256 is not None:
            payload["resume_checkpoint_sha256"] = resume_checkpoint_sha256
        if transition:
            runtime._transition(
                product_id,
                "wish",
                stage,
                product["revision"],
                artifact_sha256,
                payload,
                lease,
            )
        runtime.release_lease(product_id, lease)
        return assignment, runtime, inventor_root

    @staticmethod
    def durable_modern_instructions_fixture(root: Path, *, working: bool):
        """Build a real content-addressed Instructions boundary for CLI tests."""

        inventor_id = "mira"
        inventor_root = root / "inventors" / inventor_id
        inventor_root.mkdir(parents=True)
        (inventor_root / "TASTE.md").write_text(
            "---\n"
            "name: Mira\n"
            "description: Kinetic desk toys, but not board games.\n"
            "---\n"
            "# Mira's Taste\n\n"
            "Make one surprising motion feel inevitable.\n",
            encoding="utf-8",
        )
        (inventor_root / "inventor.json").write_text(
            json.dumps(
                {
                    "schema_version": 5,
                    "id": inventor_id,
                    "status": "active",
                    "entrypoint": ["python3", "profile.py"],
                    "capabilities": ["moving-machines", "taste-only"],
                    "checks": [],
                    "source": {"kind": "local"},
                }
            ),
            encoding="utf-8",
        )
        (inventor_root / "profile.py").write_text(
            "# fixture profile\n", encoding="utf-8"
        )
        card = discover_inventor_catalog(root).card(inventor_id)
        taste = load_taste(inventor_root)
        wish = Wish.create("wish-one", "A tiny moon that rolls")
        assignment = SimpleNamespace(
            wish=wish,
            inventor_id=inventor_id,
            playtest_rounds=4,
            assignment_sha256="a" * 64,
            entrypoint=tuple(card.entrypoint),
            decision=SimpleNamespace(
                decision_sha256="d" * 64,
                selected=SimpleNamespace(card=card, taste=taste),
            ),
        )
        _save_manager_assignment(assignment)

        def killed_before_instructions_output(context):
            del context
            raise RuntimeError("fixture killed at Instructions")

        instructions = (
            killed_before_instructions_output if working else DefaultInstructions()
        )
        workshop = Workshop(
            inventor_root,
            "moving-machines",
            inventor_id=inventor_id,
            tools=WorkshopTools(
                invent=ToyWorkshopTest.invent_job,
                make=ToyWorkshopTest.make_job,
                playtest=ToyWorkshopTest.passing_playtest,
                instructions=instructions,
            ),
            runtime_root=inventor_root / ".workshop",
        )
        if working:
            with unittest.TestCase().assertRaisesRegex(
                RuntimeError, "fixture killed at Instructions"
            ):
                workshop.run(wish, playtest_rounds=4)
        else:
            result = workshop.run(wish, playtest_rounds=4)
            if (result.status, result.job) != ("waiting", "instructions"):
                raise AssertionError("fixture did not stop at Instructions")
        return (
            assignment,
            Runtime(inventor_root / ".workshop" / "workshop.sqlite3"),
            inventor_root,
        )

    @staticmethod
    def durable_world_instructions_fixture(root: Path):
        """Build an approved world checkpoint, then discard Manager envelopes."""

        inventor_id = "eve"
        inventor_root = root / "inventors" / inventor_id
        card, taste = CliTest.inventor_identity(
            inventor_root,
            inventor_id,
            lane="little-worlds",
            level="taste-only",
        )
        wish = Wish.create(
            "wish-world-crash",
            "A tiny world using one exact admitted feature",
        )
        assignment = SimpleNamespace(
            wish=wish,
            inventor_id=inventor_id,
            playtest_rounds=4,
            assignment_sha256="a" * 64,
            entrypoint=tuple(card.entrypoint),
            decision=SimpleNamespace(
                decision_sha256="d" * 64,
                selected=SimpleNamespace(card=card, taste=taste),
            ),
        )
        _save_manager_assignment(assignment)
        inputs = ToyWorkshopTest.world_inputs(wish)
        tools = WorkshopTools(
            invent=ToyWorkshopTest.world_invent_job,
            make=ToyWorkshopTest.make_job,
            playtest=ToyWorkshopTest.passing_invented_playtest,
            instructions=DefaultInstructions(),
        )
        runtime_root = inventor_root / ".workshop"
        first = Workshop(
            inventor_root,
            "little-worlds",
            inventor_id=inventor_id,
            tools=tools,
            runtime_root=runtime_root,
            world_inputs=inputs,
        ).run(wish, playtest_rounds=4)
        if (first.status, first.job) != ("waiting", "playtest"):
            raise AssertionError("world fixture did not stop for Manager evidence")
        evidence = ToyWorkshopTest.world_evidence(
            wish, first.artifact_sha256, inputs
        )
        approved = Workshop(
            inventor_root,
            "little-worlds",
            inventor_id=inventor_id,
            tools=tools,
            runtime_root=runtime_root,
            world_inputs=inputs,
            world_evidence=evidence,
        ).resume(wish)
        if (approved.status, approved.job) != ("waiting", "instructions"):
            raise AssertionError("world fixture did not stop at Instructions")
        return (
            assignment,
            Runtime(runtime_root / "workshop.sqlite3"),
            inventor_root,
            inputs,
            evidence,
        )

    @staticmethod
    def factory_receipt(status="draft", artifact_sha256="f" * 64):
        history = "history-one"
        receipt = Receipt.from_design(
            {
                "id": "design-one",
                "slug": "rolling-moon",
                "owner_id": "owner-mira",
                "root_id": "design-one",
                "current_history_id": history,
                "published_history_id": history if status == "public" else None,
                "status": status,
                "project_url": "https://cdn.example.test/history-one/",
                "listing": (
                    {
                        "active": True,
                        "price_cents": 2400,
                        "currency": "USD",
                        "sku": "MOON-001",
                    }
                    if status == "public"
                    else None
                ),
            },
            "a" * 64,
            artifact_sha256,
        )
        value = receipt.to_dict()
        value["details"] = {
            **value["details"],
            "instructions_sha256": "b" * 64,
            "playtest_evidence_sha256": "c" * 64,
            "page_url": "https://www.autonomous.ai/factory/product/rolling-moon",
        }
        return Receipt.from_dict(value)

    def test_selected_inventor_receives_no_factory_or_unrelated_secrets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "eve"
            wish = Wish.create(
                "wish-one",
                "A tiny world",
                constraints={"size": {"maximum_mm": 88}, "colors": ["red", "blue"]},
                context={"source": "test", "customer": {"locale": "vi-VN"}},
            )
            assignment = self.resume_assignment(root, "eve", wish)
            observed = {}

            def runner(command, **kwargs):
                observed["command"] = command
                observed.update(kwargs)
                handoff = ManagerAssignmentHandoff.from_dict(
                    json.loads(kwargs["input"]), expected_inventor_id="eve"
                )
                result = bind_manager_assignment_result(
                    {
                        "product_id": "wish-one",
                        "status": "waiting",
                        "playtest_rounds": 4,
                    },
                    handoff,
                )
                return subprocess.CompletedProcess(
                    command, 0, stdout=json.dumps(result)
                )

            with mock.patch.dict(
                "os.environ",
                {
                    "FACTORY_PASSWORD": "fixture-password",
                    "AWS_SECRET_ACCESS_KEY": "unrelated-secret",
                    "OPENAI_API_KEY": "codex-only-token",
                },
                clear=True,
            ):
                result = _run_inventor(
                    assignment,
                    runner=runner,
                    state_validator=lambda selected, payload: payload,
                )

            self.assertEqual(result["status"], "waiting")
            self.assertNotIn("FACTORY_USERNAME", observed["env"])
            self.assertNotIn("FACTORY_PASSWORD", observed["env"])
            self.assertNotIn("AWS_SECRET_ACCESS_KEY", observed["env"])
            self.assertEqual(observed["env"]["OPENAI_API_KEY"], "codex-only-token")
            self.assertEqual(observed["env"]["WORKSHOP_AGENT_WORKERS"], "codex")
            self.assertNotIn("fixture-password", observed["command"])
            self.assertEqual(observed["command"][-2:], ["run", "--assignment-stdin"])
            self.assertNotIn(wish.product_id, observed["command"])
            self.assertNotIn(wish.objective, observed["command"])
            handed_off = json.loads(observed["input"])
            self.assertEqual(handed_off["wish"], wish.to_dict())
            self.assertEqual(handed_off["decision_sha256"], "d" * 64)
            self.assertEqual(handed_off["assignment_sha256"], "a" * 64)

    def test_resume_uses_the_same_exact_sanitized_manager_handoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "ivy"
            wish = Wish.create("wish-resume", "Keep this exact resumed Wish")
            assignment = self.resume_assignment(
                root, "ivy", wish, playtest_rounds=6
            )
            observed = {}

            def runner(command, **kwargs):
                observed["command"] = command
                observed.update(kwargs)
                handoff = ManagerAssignmentHandoff.from_dict(
                    json.loads(kwargs["input"]), expected_inventor_id="ivy"
                )
                payload = bind_manager_assignment_result(
                    {
                        "product_id": wish.product_id,
                        "status": "waiting",
                        "playtest_rounds": 6,
                    },
                    handoff,
                )
                return subprocess.CompletedProcess(
                    command, 0, stdout=json.dumps(payload)
                )

            with mock.patch.dict(
                "os.environ",
                {
                    "FACTORY_PASSWORD": "parent-only",
                    "OPENAI_API_KEY": "codex-runtime",
                },
                clear=True,
            ):
                result = _resume_inventor(
                    assignment,
                    runner=runner,
                    state_validator=lambda selected, payload: payload,
                )

            self.assertEqual(result["status"], "waiting")
            self.assertEqual(observed["command"][-2:], ["resume", "--assignment-stdin"])
            self.assertNotIn(wish.product_id, observed["command"])
            self.assertNotIn(wish.objective, observed["command"])
            self.assertNotIn("FACTORY_PASSWORD", observed["env"])
            self.assertEqual(observed["env"]["OPENAI_API_KEY"], "codex-runtime")
            self.assertEqual(
                ManagerAssignmentHandoff.from_dict(
                    json.loads(observed["input"]), expected_inventor_id="ivy"
                ).wish.to_dict(),
                wish.to_dict(),
            )

    def test_managed_child_timeout_cancels_descendant_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "orphan-wrote-after-timeout"
            grandchild = (
                "import pathlib,time; time.sleep(0.5); "
                "pathlib.Path(%r).write_text('orphan')" % str(marker)
            )
            parent = (
                "import subprocess,sys,time; "
                "subprocess.Popen([sys.executable, '-c', %r]); "
                "time.sleep(30)" % grandchild
            )
            with self.assertRaises(subprocess.TimeoutExpired):
                _managed_child_run(
                    (sys.executable, "-c", parent),
                    cwd=temporary,
                    env={"PATH": os.environ.get("PATH", "")},
                    input="",
                    capture_output=True,
                    text=True,
                    timeout=0.1,
                    check=False,
                )
            time.sleep(0.7)
            self.assertFalse(marker.exists())

    def test_selected_inventor_result_must_match_the_exact_assignment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "alice"
            assignment = self.resume_assignment(
                root,
                "alice",
                Wish.create(
                    "wish-one",
                    "Keep all of this",
                    constraints={"must": ["one", "two"]},
                    context={"source": "manager"},
                ),
                playtest_rounds=3,
            )

            def drifted_runner(command, **kwargs):
                handoff = ManagerAssignmentHandoff.from_dict(
                    json.loads(kwargs["input"]), expected_inventor_id="alice"
                )
                result = bind_manager_assignment_result(
                    {
                        "product_id": "wish-one",
                        "status": "waiting",
                        "playtest_rounds": 3,
                    },
                    handoff,
                )
                result["manager_assignment"]["assignment_sha256"] = "b" * 64
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(result))

            with self.assertRaisesRegex(
                WorkshopError, "different Manager assignment"
            ):
                _run_inventor(assignment, runner=drifted_runner)

    def test_profile_stdout_cannot_upgrade_a_durable_wait_to_delivered(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "malicious-inventor"
            root.mkdir()
            (root / "TASTE.md").write_text(
                "---\n"
                "name: Malicious Fixture\n"
                "description: A fixture whose stdout cannot outrank the Workshop log.\n"
                "---\n"
                "# Taste\n",
                encoding="utf-8",
            )
            (root / "inventor.json").write_text(
                json.dumps(
                    {
                        "schema_version": 5,
                        "id": "malicious-inventor",
                        "status": "active",
                        "entrypoint": ["python3", "profile.py"],
                        "capabilities": ["little-worlds", "taste-only"],
                        "checks": [],
                        "source": {"kind": "local"},
                    }
                ),
                encoding="utf-8",
            )
            (root / "profile.py").write_text(
                "# exact malicious CLI fixture profile\n", encoding="utf-8"
            )
            wish = Wish.create("wish-one", "A tiny impossible world")
            taste = load_taste(root)
            card = SimpleNamespace(
                inventor_id="malicious-inventor", root=root
            )
            decision = SimpleNamespace(
                decision_sha256="d" * 64,
                selected=SimpleNamespace(card=card, taste=taste),
            )
            assignment = SimpleNamespace(
                entrypoint=("python3", "profile.py"),
                wish=wish,
                inventor_id="malicious-inventor",
                playtest_rounds=4,
                assignment_sha256="a" * 64,
                decision=decision,
            )
            runtime_root = root / ".workshop"
            runtime = Runtime(runtime_root / "workshop.sqlite3")
            runtime.register_product(
                wish.product_id,
                "wish",
                {
                    "wish": wish.to_dict(),
                    "inventor_id": "malicious-inventor",
                    "taste_sha256": taste.sha256,
                    "blueprint_sha256": ToyBlueprint.for_lane("little-worlds").sha256,
                    "lane": "little-worlds",
                    "customization_level": "taste-only",
                    "playtest_rounds": 4,
                },
            )
            lease = runtime.acquire_lease(wish.product_id, "fixture")
            product = runtime.get_product(wish.product_id)
            runtime._transition(
                wish.product_id,
                "wish",
                "invent",
                product["revision"],
                None,
                {
                    "status": "waiting",
                    "round": 1,
                    "needs": [
                        {
                            "job": "invent",
                            "capability": "source-backed-design-research",
                            "reason": "Research is unavailable.",
                            "instructions": "Connect the shared provider.",
                        }
                    ],
                },
                lease,
            )
            runtime.release_lease(wish.product_id, lease)
            database = runtime_root / "workshop.sqlite3"
            before_database = database.read_bytes()
            before_database_stat = database.stat()

            def runner(command, **kwargs):
                handoff = ManagerAssignmentHandoff.from_dict(
                    json.loads(kwargs["input"]),
                    expected_inventor_id="malicious-inventor",
                )
                fabricated = bind_manager_assignment_result(
                    {
                        "product_id": wish.product_id,
                        "status": "delivered",
                        "job": "deliver",
                        "round": 1,
                        "playtest_rounds": 4,
                        "artifact_sha256": "f" * 64,
                        "instructions_sha256": "e" * 64,
                        "page_url": "https://attacker.invalid/fake",
                        "invented": None,
                        "needs": [],
                        "delivery": None,
                    },
                    handoff,
                )
                return subprocess.CompletedProcess(
                    command, 0, stdout=json.dumps(fabricated)
                )

            with self.assertRaisesRegex(WorkshopError, "stdout differs"):
                _run_inventor(assignment, runner=runner)
            self.assertEqual(database.read_bytes(), before_database)
            self.assertEqual(
                database.stat().st_mtime_ns, before_database_stat.st_mtime_ns
            )
            self.assertEqual(database.stat().st_mode, before_database_stat.st_mode)

    def test_worker_environment_without_factory_secret_has_no_partial_login(self):
        with mock.patch.dict(
            "os.environ", {"FACTORY_USERNAME": "wrong-account"}, clear=True
        ):
            environment = _inventor_process_environment("alice")
        self.assertNotIn("FACTORY_USERNAME", environment)
        self.assertNotIn("FACTORY_PASSWORD", environment)
        self.assertEqual(environment["WORKSHOP_AGENT_WORKERS"], "codex")

    def test_worker_environment_preserves_only_safe_shared_engine_configuration(self):
        allowed = {
            "WORKSHOP_CODEX_BIN": "/opt/workshop/codex",
            "WORKSHOP_INVENT_MODEL": "gpt-5.6-terra",
            "WORKSHOP_REWARD_MODEL": "gpt-5.6-luna",
            "WORKSHOP_MAKE_MODEL": "gpt-5.6-terra",
            "WORKSHOP_MAKE_REWARD_MODEL": "gpt-5.6-luna",
            "WORKSHOP_PLAYTEST_MODEL": "gpt-5.6-luna",
            "WORKSHOP_INSTRUCTIONS_MODEL": "gpt-5.6-terra",
            "WORKSHOP_INSTRUCTIONS_REWARD_MODEL": "gpt-5.6-luna",
            "WORKSHOP_PRUSASLICER_BIN": "/opt/workshop/PrusaSlicer",
            "WORKSHOP_PRUSASLICER_PRINTER_PROFILE": "/opt/workshop/printer.ini",
            "WORKSHOP_PRUSASLICER_FILAMENT_PROFILE": "/opt/workshop/filament.ini",
            "WORKSHOP_PRUSASLICER_PROCESS_PROFILE": "/opt/workshop/process.ini",
        }
        forbidden = {
            "FACTORY_PASSWORD": "factory-secret",
            "WORKSHOP_SHOP_TOKEN": "shop-secret",
            "AWS_SECRET_ACCESS_KEY": "cloud-secret",
            "GITHUB_TOKEN": "git-secret",
            "NPM_TOKEN": "package-secret",
        }
        with mock.patch.dict("os.environ", {**allowed, **forbidden}, clear=True):
            environment = _inventor_process_environment("alice")
        for name, value in allowed.items():
            self.assertEqual(environment[name], value)
        for name in forbidden:
            self.assertNotIn(name, environment)

    def test_manager_resumes_factory_handoff_without_exposing_credential_to_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "factory-resume-inventor"
            root.mkdir()
            (root / "inventor.json").write_text(
                json.dumps(
                    {
                        "schema_version": 5,
                        "id": root.name,
                        "status": "active",
                        "entrypoint": ["python3", "profile.py"],
                        "capabilities": ["moving-machines", "taste-only"],
                        "checks": [],
                        "source": {"kind": "local"},
                    }
                ),
                encoding="utf-8",
            )
            # Manifest ids must match their folder; use the temporary basename.
            inventor_id = root.name
            assignment = self.resume_assignment(
                root, inventor_id, Wish.create("wish-one", "A tiny world")
            )
            handoff = ManagerAssignmentHandoff.from_assignment(assignment)
            observed = {}

            def writer_factory(store, selected_id, credentials):
                observed["store"] = store
                observed["inventor_id"] = selected_id
                observed["credentials"] = credentials
                return lambda context, sealed_root, sealed_manifest: None

            class FakeRun:
                def to_dict(self):
                    return {"status": "waiting", "job": "deliver", "page_url": "https://example.test/product"}

            class FakeWorkshop:
                def __init__(self, *args, **kwargs):
                    observed["workshop_args"] = args
                    observed["workshop_kwargs"] = kwargs

                def resume_instructions(self, wish):
                    observed["wish"] = wish
                    return FakeRun()

            result = _resume_factory_instructions(
                assignment,
                {
                    "status": "waiting",
                    "job": "instructions",
                    "needs": [
                        {"job": "instructions", "capability": "site-page"}
                    ],
                    "manager_assignment": handoff.result_binding(),
                },
                environment={"FACTORY_PASSWORD": "manager-only-secret"},
                store_factory=lambda path: path,
                writer_factory=writer_factory,
                workshop_factory=FakeWorkshop,
                state_validator=lambda selected, payload, **kwargs: payload,
            )
            self.assertEqual(result["job"], "deliver")
            self.assertEqual(
                result["manager_assignment"], handoff.result_binding()
            )
            self.assertEqual(observed["inventor_id"], inventor_id)
            self.assertNotIn(
                "manager-only-secret", repr(observed["credentials"])
            )
            self.assertIs(observed["wish"], assignment.wish)

    def test_factory_resume_reconstructs_all_three_declared_contribution_levels(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary)
            for level in ("taste-only", "custom-make", "custom-playtest"):
                with self.subTest(level=level):
                    inventor_id = "inventor-" + level
                    root = collection / inventor_id
                    root.mkdir()
                    (root / "inventor.json").write_text(
                        json.dumps(
                            {
                                "schema_version": 5,
                                "id": inventor_id,
                                "status": "active",
                                "entrypoint": ["python3", "profile.py"],
                                "capabilities": ["moving-machines", level],
                                "checks": [],
                                "source": {"kind": "local"},
                            }
                        ),
                        encoding="utf-8",
                    )
                    assignment = self.resume_assignment(
                        root,
                        inventor_id,
                        Wish.create("wish-" + level, "A moving toy"),
                    )
                    handoff = ManagerAssignmentHandoff.from_assignment(assignment)
                    waiting = {
                        "status": "waiting",
                        "job": "instructions",
                        "needs": [
                            {"job": "instructions", "capability": "site-page"}
                        ],
                        "manager_assignment": handoff.result_binding(),
                    }
                    observed = {}

                    class FakeRun:
                        def to_dict(self):
                            return {"status": "waiting", "job": "deliver"}

                    class FakeWorkshop:
                        def __init__(self, *args, **kwargs):
                            observed["kwargs"] = kwargs

                        def resume_instructions(self, wish):
                            return FakeRun()

                    result = _resume_factory_instructions(
                        assignment,
                        waiting,
                        environment={"FACTORY_PASSWORD": "manager-only-secret"},
                        store_factory=lambda path: path,
                        writer_factory=lambda *args: (
                            lambda context, sealed_root, sealed_manifest: None
                        ),
                        workshop_factory=FakeWorkshop,
                        state_validator=lambda selected, payload, **kwargs: payload,
                    )
                    self.assertEqual(result["job"], "deliver")
                    self.assertEqual(
                        "make" in observed["kwargs"], level != "taste-only"
                    )
                    self.assertEqual(
                        "playtest" in observed["kwargs"],
                        level == "custom-playtest",
                    )

    def test_direct_world_factory_resume_requires_exact_manager_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, _, inputs, evidence = (
                self.durable_world_instructions_fixture(root)
            )
            exact = SimpleNamespace(
                **vars(assignment),
                assert_current=lambda: None,
                world_inputs=inputs,
                world_evidence=evidence,
            )
            handoff = ManagerAssignmentHandoff.from_assignment(exact)
            waiting = {
                "status": "waiting",
                "job": "instructions",
                "artifact_sha256": evidence.artifact_sha256,
                "needs": [{"job": "instructions", "capability": "site-page"}],
                "manager_assignment": handoff.result_binding(),
            }
            observed = {}

            class FakeRun:
                def to_dict(self):
                    return {"status": "waiting", "job": "deliver"}

            class FakeWorkshop:
                def __init__(self, *args, **kwargs):
                    observed["kwargs"] = kwargs

                def resume_instructions(self, wish):
                    observed["wish"] = wish
                    return FakeRun()

            result = _resume_factory_instructions(
                exact,
                waiting,
                environment={"FACTORY_PASSWORD": "manager-only"},
                store_factory=lambda path: path,
                writer_factory=lambda *args: (
                    lambda context, sealed_root, sealed_manifest: None
                ),
                workshop_factory=FakeWorkshop,
                state_validator=lambda selected, payload, **kwargs: payload,
            )

            self.assertEqual(result["job"], "deliver")
            self.assertIs(observed["kwargs"]["world_inputs"], inputs)
            self.assertIs(observed["kwargs"]["world_evidence"], evidence)
            self.assertEqual(observed["wish"], assignment.wish)

    def test_factory_resume_rejects_unknown_manifest_contribution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "unknown-level-inventor"
            root.mkdir()
            inventor_id = root.name
            (root / "inventor.json").write_text(
                json.dumps(
                    {
                        "schema_version": 5,
                        "id": inventor_id,
                        "status": "active",
                        "entrypoint": ["python3", "profile.py"],
                        "capabilities": ["little-worlds", "inventor-owned-everything"],
                        "checks": [],
                        "source": {"kind": "local"},
                    }
                ),
                encoding="utf-8",
            )
            assignment = self.resume_assignment(
                root, inventor_id, Wish.create("wish-one", "A tiny world")
            )
            with self.assertRaisesRegex(WorkshopError, "known contribution level"):
                _resume_factory_instructions(
                    assignment,
                    {
                        "status": "waiting",
                        "job": "instructions",
                        "needs": [
                            {"job": "instructions", "capability": "site-page"}
                        ],
                    },
                    environment={"FACTORY_PASSWORD": "manager-only-secret"},
                )

    def test_explicit_publish_uses_the_exact_durable_draft(self):
        page_url = "https://www.autonomous.ai/factory/product/pocket-duel"
        draft = Receipt.from_design(
            {
                "id": "design-pocket-duel",
                "slug": "pocket-duel",
                "owner_id": "owner-alice",
                "root_id": "design-pocket-duel",
                "current_history_id": "history-one",
                "published_history_id": None,
                "status": "draft",
                "project_url": "https://cdn.autonomous.ai/projects/history-one/",
                "listing": None,
            },
            "f" * 64,
            "a" * 64,
        )
        draft_value = draft.to_dict()
        draft_value["details"] = {
            **draft_value["details"],
            "page_url": page_url,
            "instructions_sha256": "b" * 64,
            "playtest_evidence_sha256": "c" * 64,
        }
        draft = Receipt.from_dict(draft_value)
        public_value = draft.to_dict()
        public_value["status"] = "public"
        public_value["published_history_id"] = "history-one"
        public_value["listing_active"] = True
        public_value["listing_price_cents"] = 2400
        public_value["listing_currency"] = "USD"
        public_value["listing_sku"] = "PD-001"
        public = Receipt.from_dict(public_value)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment = SimpleNamespace(
                wish=SimpleNamespace(product_id="wish-one"),
                decision=SimpleNamespace(
                    selected=SimpleNamespace(
                        card=SimpleNamespace(inventor_id="alice", root=root)
                    )
                ),
            )
            store = mock.Mock()
            intent = {
                "id": "intent-one",
                "state": "succeeded",
                "request": {
                    "_workshop_api_origin": "https://api.example.test",
                },
                "receipt": draft.to_dict()
            }
            store.latest_publish_intent.return_value = intent
            store.get_publish_intent.return_value = intent
            store.acquire_lease.return_value = "lease-one"
            store.begin_live.return_value = {"effect_token": "effect-one"}
            session = object()
            transition = mock.Mock()
            transition.publish.return_value = public
            with mock.patch.dict(
                "os.environ", {"FACTORY_PASSWORD": "fixture-password"}, clear=True
            ):
                publication = _publish_inventor_draft(
                    assignment,
                    {"page_url": page_url, "artifact_sha256": "a" * 64},
                    store_factory=mock.Mock(return_value=store),
                    session_factory=mock.Mock(return_value=session),
                    transition_factory=mock.Mock(return_value=transition),
                )
        transition.publish.assert_called_once_with(draft)
        store.begin_live.assert_called_once()
        store.mark_publish_live.assert_called_once_with(
            "intent-one", "effect-one", public
        )
        store.release_lease.assert_called_once_with("wish-one", "lease-one")
        self.assertEqual(publication["status"], "public")
        self.assertTrue(publication["verified"])
        self.assertEqual(publication["page_url"], page_url)

    def test_stranded_publication_is_leased_and_reconciled_by_get_without_republish(self):
        draft = self.factory_receipt("draft")
        public = self.factory_receipt("public")
        publishing = {
            "id": "intent-one",
            "state": "publishing",
            "receipt": draft.to_dict(),
        }
        unknown = {**publishing, "state": "live_unknown"}
        store = mock.Mock()
        store.acquire_lease.return_value = "lease-one"
        store.get_publish_intent.side_effect = [publishing, unknown]
        identity = SimpleNamespace(owner_id="owner-mira")
        session = SimpleNamespace(
            login=mock.Mock(return_value=identity),
            authenticated_transport=object(),
        )
        transition = mock.Mock()
        transition._design.return_value = {"status": "public"}
        transition._receipt.return_value = public
        transition._is_current_public.return_value = True
        door = mock.Mock()
        door.get_design.return_value = object()
        with mock.patch("inventor_workshop.cli.ShopDoor", return_value=door):
            observed = _promote_factory_intent(
                store,
                publishing,
                draft,
                object(),
                product_id="wish-one",
                session_factory=mock.Mock(return_value=session),
                transition_factory=mock.Mock(return_value=transition),
            )
        self.assertEqual(observed.to_dict(), public.to_dict())
        store.acquire_lease.assert_called_once_with(
            "wish-one", mock.ANY, ttl_seconds=900
        )
        store.recover_stranded_intent.assert_called_once_with(
            "intent-one",
            "previous public transition ended without a durable completion",
        )
        transition.publish.assert_not_called()
        store.resolve_live_as_public.assert_called_once_with("intent-one", public)
        store.release_lease.assert_called_once_with("wish-one", "lease-one")

    def test_live_unknown_draft_readback_never_republishes(self):
        draft = self.factory_receipt("draft")
        unknown = {
            "id": "intent-one",
            "state": "live_unknown",
            "receipt": draft.to_dict(),
        }
        store = mock.Mock()
        store.acquire_lease.return_value = "lease-one"
        store.get_publish_intent.return_value = unknown
        session = SimpleNamespace(
            login=mock.Mock(return_value=SimpleNamespace(owner_id="owner-mira")),
            authenticated_transport=object(),
        )
        transition = mock.Mock()
        transition._design.return_value = {"status": "draft"}
        transition._receipt.return_value = draft
        transition._is_current_public.return_value = False
        door = mock.Mock()
        with mock.patch("inventor_workshop.cli.ShopDoor", return_value=door):
            with self.assertRaisesRegex(
                AmbiguousEffectError, "no retry was sent"
            ):
                _promote_factory_intent(
                    store,
                    unknown,
                    draft,
                    object(),
                    product_id="wish-one",
                    session_factory=mock.Mock(return_value=session),
                    transition_factory=mock.Mock(return_value=transition),
                )
        transition.publish.assert_not_called()
        store.resolve_live_as_public.assert_not_called()
        store.release_lease.assert_called_once_with("wish-one", "lease-one")

    def test_active_publication_lease_blocks_stranded_recovery(self):
        draft = self.factory_receipt("draft")
        publishing = {
            "id": "intent-one",
            "state": "publishing",
            "receipt": draft.to_dict(),
        }
        store = mock.Mock()
        store.acquire_lease.side_effect = WorkshopError(
            "another publisher still owns the product lease"
        )
        with self.assertRaisesRegex(WorkshopError, "still owns"):
            _promote_factory_intent(
                store,
                publishing,
                draft,
                object(),
                product_id="wish-one",
                session_factory=mock.Mock(),
                transition_factory=mock.Mock(),
            )
        store.recover_stranded_intent.assert_not_called()
        store.release_lease.assert_not_called()

    def test_publish_waits_truthfully_until_instructions_has_a_draft(self):
        assignment = SimpleNamespace(
            wish=SimpleNamespace(product_id="wish-one"),
            decision=SimpleNamespace(
                selected=SimpleNamespace(
                    card=SimpleNamespace(inventor_id="alice", root=Path.cwd())
                )
            ),
        )
        publication = _publish_inventor_draft(assignment, {"job": "make"})
        self.assertEqual(publication["status"], "waiting")
        self.assertIn("Instructions", publication["reason"])

    def test_publish_draft_without_factory_secret_returns_an_exact_safe_wait(self):
        assignment = SimpleNamespace(
            wish=SimpleNamespace(product_id="wish-one"),
            decision=SimpleNamespace(
                selected=SimpleNamespace(
                    card=SimpleNamespace(
                        inventor_id="alice",
                        root=Path("/workshop/inventors/alice"),
                    )
                )
            ),
        )
        store = mock.Mock()
        with mock.patch.dict("os.environ", {}, clear=True):
            publication = _publish_inventor_draft(
                assignment,
                {
                    "page_url": "https://www.autonomous.ai/factory/product/moon",
                    "artifact_sha256": "a" * 64,
                },
                store_factory=store,
            )
        self.assertEqual(publication["status"], "waiting")
        self.assertIn("FACTORY_PASSWORD", publication["reason"])
        self.assertIn("workshop resume wish-one", publication["reason"])
        self.assertNotIn("alice", publication["reason"])
        store.assert_not_called()

    def test_wish_is_the_simple_customer_command(self):
        root = Path(__file__).resolve().parents[1]

        class FakeSemanticManager:
            judge_identity = "fixture-description-matcher"
            judge_version = "1.0.0"
            judge_config_sha256 = "a" * 64

            def retrieve(self, context):
                return create_shortlist(
                    context,
                    ("bob",),
                    retriever="fixture-description-matcher",
                    retriever_version="1.0.0",
                    rationale="Bob turns a playful movement into a real mechanism.",
                )

            def judge(self, context):
                finalist = context.finalists[0]
                return (
                    TasteFit(
                        inventor_id="bob",
                        taste_sha256=finalist.taste.sha256,
                        score=94,
                        accepted=True,
                        explanation=(
                            "Bob turns a playful movement into a real mechanism."
                        ),
                    ),
                )

        output = StringIO()
        progress = StringIO()
        with mock.patch(
            "inventor_workshop.cli.CodexSemanticManager",
            return_value=FakeSemanticManager(),
        ), mock.patch(
            "inventor_workshop.cli._run_inventor",
            return_value={
                "status": "waiting",
                "job": "make",
                "needs": [
                    {
                        "job": "make",
                        "capability": "mechanical-designer",
                        "reason": "The mechanical designer is not connected yet.",
                        "instructions": "Connect it.",
                    }
                ],
            },
        ), mock.patch(
            "inventor_workshop.cli._save_manager_assignment"
        ), mock.patch(
            "inventor_workshop.cli._publish_inventor_draft",
            return_value={
                "status": "waiting",
                "reason": "Instructions has not produced a draft yet.",
            },
        ) as publish, redirect_stdout(output), redirect_stderr(progress):
            result = main(
                (
                    "wish",
                    "a",
                    "wind-up",
                    "version",
                    "of",
                    "my",
                    "dog",
                    "--root",
                    str(root),
                    "--json",
                )
            )
        self.assertEqual(result, 0)
        receipt = json.loads(output.getvalue())
        self.assertRegex(
            receipt["wish"]["product_id"],
            r"^wish-\d{8}-\d{6}-[0-9a-f]{8}$",
        )
        self.assertEqual(
            receipt["wish"]["objective"], "a wind-up version of my dog"
        )
        self.assertEqual(receipt["match"]["inventor_id"], "bob")
        self.assertEqual(receipt["match"]["score"], 94)
        self.assertEqual(receipt["result"]["status"], "waiting")
        self.assertEqual(publish.call_count, 1)
        self.assertIn("Wish:", progress.getvalue())
        self.assertIn("Track: workshop status", progress.getvalue())
        self.assertIn("will be public", progress.getvalue())
        self.assertIn("up to 60 minutes", progress.getvalue())
        self.assertNotIn("Wish:", output.getvalue().splitlines()[0])

    def test_wish_help_discloses_default_public_wait_and_json_semantics(self):
        command = parser()
        subcommands = next(
            action
            for action in command._actions
            if hasattr(action, "choices") and action.choices
        )
        help_text = subcommands.choices["wish"].format_help()
        self.assertIn("public", help_text)
        self.assertIn("--draft", help_text)
        self.assertIn("--strict", help_text)
        self.assertIn("progress goes to stderr", help_text)
        self.assertIn("four", help_text)
        self.assertTrue(command.parse_args(("wish", "a moon")).publish)
        self.assertFalse(
            command.parse_args(("wish", "a moon", "--draft")).publish
        )

    def test_empty_working_directory_auto_detects_the_source_checkout(self):
        expected = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary, mock.patch(
            "pathlib.Path.cwd", return_value=Path(temporary)
        ):
            self.assertEqual(_default_workshop_root(), expected)
            command = parser()
            args = command.parse_args(("wish", "a rolling moon"))
            creator = command.parse_args(
                (
                    "create",
                    "inventor",
                    "mira",
                    "--description",
                    "kinetic desk toys",
                    "--lane",
                    "moving-machines",
                )
            )
        # Catalog resolution is intentionally lazy so ``workshop --help`` never
        # creates an installed WORKSHOP_HOME.
        self.assertIsNone(args.root)
        self.assertEqual(creator.root, Path(temporary))

    def test_help_does_not_materialize_an_installed_catalog(self):
        with mock.patch(
            "inventor_workshop.cli._source_workshop_root", return_value=None
        ), mock.patch(
            "inventor_workshop.cli.packaged_inventors_root",
            return_value=Path("/installed/_data/inventors"),
        ), mock.patch(
            "inventor_workshop.cli.materialize_bundled_inventors"
        ) as materialize:
            command = parser()
            command.format_help()
            self.assertIsNone(command.parse_args(("status",)).root)
        materialize.assert_not_called()

    def test_installed_customer_command_materializes_the_current_catalog_lazily(self):
        expected = Path("/customer/workshop/bundled-catalogs/current")
        with mock.patch(
            "inventor_workshop.cli._source_workshop_root", return_value=None
        ), mock.patch(
            "inventor_workshop.cli.packaged_inventors_root",
            return_value=Path("/installed/_data/inventors"),
        ), mock.patch(
            "inventor_workshop.cli.materialize_bundled_inventors",
            return_value=expected,
        ) as materialize:
            self.assertEqual(_default_workshop_root(), expected)
        materialize.assert_called_once_with()

    def test_implicit_installed_status_reads_retained_catalog_without_materializing(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "workshop-home"
            digest = "a" * 64
            retained = home / "bundled-catalogs" / digest
            self.durable_wait_fixture(retained)
            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli._source_workshop_root", return_value=None
            ), mock.patch(
                "inventor_workshop.cli.packaged_inventors_root",
                return_value=Path("/installed/_data/inventors"),
            ), mock.patch(
                "inventor_workshop.cli.existing_bundled_catalog_roots",
                return_value=(retained,),
            ), mock.patch(
                "inventor_workshop.cli.materialize_bundled_inventors"
            ) as materialize, redirect_stdout(output):
                result = main(("status", "wish-one", "--json"))
            receipt = json.loads(output.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(receipt["product_id"], "wish-one")
            self.assertEqual(receipt["catalog_root"], str(retained.resolve()))
            materialize.assert_not_called()

    def test_one_taste_file_creates_an_inventor_and_prints_a_start_command(self):
        source = (
            "---\r\n"
            'name: "Orbit Muse"\r\n'
            'description: "Moonlit kinetic desk toys, but not board games."\r\n'
            "---\r\n"
            "# Orbit Muse's Taste\r\n\r\n"
            "Make one surprising motion feel inevitable.\r\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            taste = root / "TASTE.md"
            taste.write_bytes(source.encode("utf-8"))
            output = StringIO()
            with redirect_stdout(output), redirect_stderr(StringIO()):
                result = main(
                    (
                        "create",
                        "inventor",
                        "--taste",
                        str(taste),
                        "--lane",
                        "moving-machines",
                        "--root",
                        str(root),
                    )
                )
            destination = root / "inventors" / "orbit-muse"
            self.assertEqual(result, 0)
            self.assertEqual((destination / "TASTE.md").read_bytes(), taste.read_bytes())
            self.assertTrue((destination / "run.py").is_file())
            self.assertIn("Orbit Muse joined the Workshop", output.getvalue())
            self.assertIn("Start:", output.getvalue())
            self.assertIn("workshop wish", output.getvalue())
            self.assertIn("--root %s" % root.resolve(), output.getvalue())
            self.assertNotIn(str(destination / "run.py"), output.getvalue())

    def test_status_reads_and_lists_valid_durable_state_without_model_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, _, inventor_root = self.durable_wait_fixture(root)
            database = inventor_root / ".workshop" / "workshop.sqlite3"
            before = database.read_bytes()
            before_stat = database.stat()
            output = StringIO()
            with redirect_stdout(output):
                result = main(
                    ("status", "wish-one", "--root", str(root), "--json")
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["job"], "make")
            self.assertEqual(receipt["event_chain"], "valid")
            self.assertEqual(receipt["needs"][0]["capability"], "model-and-cad-maker")
            self.assertEqual(database.read_bytes(), before)
            self.assertEqual(database.stat().st_mtime_ns, before_stat.st_mtime_ns)
            self.assertEqual(database.stat().st_mode, before_stat.st_mode)

            output = StringIO()
            with redirect_stdout(output):
                result = main(("status", "--root", str(root), "--json"))
            listing = json.loads(output.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(listing["count"], 1)
            self.assertEqual(listing["wishes"][0]["product_id"], "wish-one")

    def test_status_never_follows_runtime_or_assignment_parent_symlinks(self):
        for replaced_parent in ("runtime", "assignments"):
            with self.subTest(replaced_parent=replaced_parent), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                _, _, inventor_root = self.durable_wait_fixture(root)
                runtime_root = inventor_root / ".workshop"
                target = (
                    runtime_root
                    if replaced_parent == "runtime"
                    else runtime_root / "manager-assignments"
                )
                moved = target.with_name(target.name + "-real")
                target.rename(moved)
                target.symlink_to(moved, target_is_directory=True)
                error = StringIO()
                with redirect_stderr(error):
                    result = main(
                        ("status", "wish-one", "--root", str(root), "--json")
                    )
                self.assertEqual(result, 2)
                self.assertIn("regular directory", error.getvalue())

    def test_status_lists_assignment_even_before_the_child_registers_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, inventor_root = self.durable_wait_fixture(root)
            database = inventor_root / ".workshop" / "workshop.sqlite3"
            database.unlink()
            output = StringIO()
            with redirect_stdout(output):
                result = main(("status", "--root", str(root), "--json"))
            receipt = json.loads(output.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(receipt["count"], 1)
            self.assertEqual(receipt["wishes"][0]["status"], "assigned")
            self.assertEqual(
                receipt["wishes"][0]["product_id"], assignment.wish.product_id
            )

    def test_resume_saved_assignment_retries_run_with_the_same_wish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, inventor_root = self.durable_wait_fixture(root)
            (inventor_root / ".workshop" / "workshop.sqlite3").unlink()
            output = StringIO()
            resumed = {
                "product_id": "wish-one",
                "status": "waiting",
                "job": "invent",
                "needs": [],
                "playtest_rounds": 4,
                "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                    assignment
                ).result_binding(),
            }
            with mock.patch(
                "inventor_workshop.cli._run_inventor", return_value=resumed
            ) as child, mock.patch(
                "inventor_workshop.cli._resume_inventor"
            ) as resumed_child, redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            self.assertEqual(result, 0)
            called_assignment = child.call_args.args[0]
            self.assertEqual(
                called_assignment.wish.to_dict(), assignment.wish.to_dict()
            )
            self.assertTrue(child.call_args.kwargs["continuing"])
            resumed_child.assert_not_called()

    def test_resume_registered_wish_dispatches_hidden_resume_not_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, _ = self.durable_wait_fixture(
                root, transition=False
            )
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    main(("status", "wish-one", "--root", str(root), "--json")),
                    0,
                )
            status = json.loads(output.getvalue())
            self.assertEqual(status["resume"]["kind"], "wish")

            resumed = {
                "product_id": "wish-one",
                "status": "waiting",
                "job": "invent",
                "needs": [],
                "playtest_rounds": 4,
                "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                    assignment
                ).result_binding(),
            }
            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli._resume_inventor", return_value=resumed
            ) as child, mock.patch(
                "inventor_workshop.cli._run_inventor"
            ) as run_child, redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            self.assertEqual(result, 0)
            self.assertEqual(
                child.call_args.args[0].wish.to_dict(), assignment.wish.to_dict()
            )
            run_child.assert_not_called()

    def test_working_instructions_checkpoint_resumes_in_credential_free_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, _ = self.durable_modern_instructions_fixture(
                root, working=True
            )
            resumed = {
                "product_id": "wish-one",
                "status": "waiting",
                "job": "instructions",
                "needs": [],
                "playtest_rounds": 4,
                "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                    assignment
                ).result_binding(),
            }
            output = StringIO()
            with mock.patch.dict("os.environ", {}, clear=True), mock.patch(
                "inventor_workshop.cli._resume_inventor", return_value=resumed
            ) as child, redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output.getvalue())["result"]["job"], "instructions")
            child.assert_called_once()

    def test_status_does_not_advertise_a_missing_instructions_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.durable_wait_fixture(
                root,
                stage="instructions",
                state_status="working",
                artifact_sha256="f" * 64,
                resume_checkpoint_sha256="d" * 64,
            )
            runtime = Runtime(root / "inventors/mira/.workshop/workshop.sqlite3")
            product = runtime.get_product("wish-one")
            lease = runtime.acquire_lease("wish-one", "fixture-modernize")
            runtime._transition(
                "wish-one",
                "instructions",
                "instructions",
                product["revision"],
                "f" * 64,
                {
                    "status": "working",
                    "round": 1,
                    "resume_checkpoint_sha256": "d" * 64,
                    "instructions_checkpoint_path": (
                        "checkpoints/instructions-r001-%s.json" % ("d" * 64)
                    ),
                    "instructions_checkpoint_sha256": "d" * 64,
                    "instructions_checkpoint_round": 1,
                },
                lease,
            )
            runtime.release_lease("wish-one", lease)

            receipt = _status_receipt(root, "wish-one")
            self.assertNotIn("resume", receipt)
            output = StringIO()
            with redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            self.assertEqual(result, 1)
            resumed = json.loads(output.getvalue())["result"]
            self.assertEqual(resumed["resume"], "not-available")
            self.assertIn("checkpoint", resumed["reason"])

    def test_status_and_resume_continue_an_exact_invent_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, _ = self.durable_wait_fixture(
                root,
                stage="invent",
                capability="industrial-design",
            )
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    main(("status", "wish-one", "--root", str(root), "--json")),
                    0,
                )
            status = json.loads(output.getvalue())
            self.assertEqual(status["resume"]["kind"], "invent")
            self.assertIn("workshop resume wish-one", status["resume"]["command"])

            resumed = {
                "product_id": "wish-one",
                "status": "waiting",
                "job": "make",
                "round": 1,
                "artifact_sha256": None,
                "instructions_sha256": None,
                "page_url": None,
                "invented": None,
                "needs": [],
                "delivery": None,
                "playtest_rounds": 4,
                "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                    assignment
                ).result_binding(),
            }
            output = StringIO()
            with mock.patch(
                "inventor_workshop.cli._resume_inventor", return_value=resumed
            ) as child, redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            self.assertEqual(result, 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["result"]["job"], "make")
            self.assertEqual(
                child.call_args.args[0].wish.to_dict(), assignment.wish.to_dict()
            )

    def test_legacy_assignment_never_executes_inventor_code_on_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, inventor_root = self.durable_wait_fixture(
                root,
                stage="invent",
                capability="industrial-design",
            )
            legacy = ManagerAssignmentHandoff(
                wish=assignment.wish,
                inventor_id=assignment.inventor_id,
                playtest_rounds=assignment.playtest_rounds,
                decision_sha256=assignment.decision.decision_sha256,
                assignment_sha256=assignment.assignment_sha256,
            )
            assignment_path = next(
                (inventor_root / ".workshop/manager-assignments").glob("*.json")
            )
            assignment_path.write_text(
                json.dumps(legacy.to_dict(), sort_keys=True), encoding="utf-8"
            )

            status = _status_receipt(root, assignment.wish.product_id)
            self.assertNotIn("resume", status)
            stderr = StringIO()
            with mock.patch(
                "inventor_workshop.cli._resume_inventor"
            ) as child, redirect_stderr(stderr):
                result = main(
                    (
                        "resume",
                        assignment.wish.product_id,
                        "--root",
                        str(root),
                        "--json",
                    )
                )
            self.assertEqual(result, 2)
            self.assertIn("legacy Manager assignment", stderr.getvalue())
            child.assert_not_called()

    def test_changed_inventor_implementation_blocks_resume_before_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, inventor_root = self.durable_wait_fixture(
                root,
                stage="invent",
                capability="industrial-design",
            )
            (inventor_root / "profile.py").write_text(
                "# changed after the exact Manager assignment\n", encoding="utf-8"
            )

            status = _status_receipt(root, assignment.wish.product_id)
            self.assertNotIn("resume", status)
            stderr = StringIO()
            with mock.patch(
                "inventor_workshop.cli._resume_inventor"
            ) as child, redirect_stderr(stderr):
                result = main(
                    (
                        "resume",
                        assignment.wish.product_id,
                        "--root",
                        str(root),
                        "--json",
                    )
                )
            self.assertEqual(result, 2)
            self.assertIn("implementation", stderr.getvalue())
            child.assert_not_called()

    def test_active_worker_hides_resume_and_returns_an_actionable_wait(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, runtime, _ = self.durable_wait_fixture(
                root,
                stage="invent",
                capability="industrial-design",
            )
            lease = runtime.acquire_lease("wish-one", "still-running", ttl_seconds=300)
            try:
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(
                        main(("status", "wish-one", "--root", str(root), "--json")),
                        0,
                    )
                status = json.loads(output.getvalue())
                self.assertNotIn("resume", status)
                self.assertEqual(status["worker"]["status"], "active")

                output = StringIO()
                with mock.patch("inventor_workshop.cli._resume_inventor") as child, redirect_stdout(output):
                    result = main(
                        ("resume", "wish-one", "--root", str(root), "--json")
                    )
                receipt = json.loads(output.getvalue())
                self.assertEqual(result, 1)
                self.assertEqual(receipt["result"]["resume"], "not-available")
                self.assertIn("another Workshop worker", receipt["result"]["reason"])
                child.assert_not_called()
            finally:
                runtime.release_lease("wish-one", lease)

    def test_resume_rejects_assignment_round_drift_before_child_effects(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.durable_wait_fixture(
                root,
                stage="invent",
                capability="industrial-design",
                assignment_rounds=4,
                metadata_rounds=5,
            )
            output = StringIO()
            with mock.patch("inventor_workshop.cli._resume_inventor") as child, redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(result, 1)
            self.assertEqual(receipt["result"]["resume"], "not-available")
            self.assertIn("Playtest allowance", receipt["result"]["reason"])
            child.assert_not_called()

    def test_resume_rejects_legacy_make_without_invented_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, runtime, _ = self.durable_wait_fixture(root)
            before = runtime.events("wish-one")
            output = StringIO()
            with redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(result, 1)
            self.assertEqual(receipt["result"]["resume"], "not-available")
            self.assertIn("legacy Make", receipt["result"]["reason"])
            self.assertEqual(runtime.events("wish-one"), before)

    def test_resume_instructions_without_factory_secret_is_actionable_and_safe(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.durable_modern_instructions_fixture(
                root, working=False
            )
            output = StringIO()
            with mock.patch.dict("os.environ", {}, clear=True), mock.patch(
                "inventor_workshop.cli._resume_factory_instructions"
            ) as resume_effect, redirect_stdout(output):
                result = main(
                    ("resume", "wish-one", "--root", str(root), "--json")
                )
            receipt = json.loads(output.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(receipt["result"]["status"], "waiting")
            self.assertEqual(
                receipt["result"]["needs"][0]["capability"],
                "factory-authentication",
            )
            self.assertIn("FACTORY_PASSWORD", receipt["result"]["needs"][0]["instructions"])
            self.assertIn("workshop resume", receipt["result"]["needs"][0]["instructions"])
            resume_effect.assert_not_called()

    def test_world_instructions_crash_restart_reverifies_without_repeating_stages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, runtime, _, inputs, evidence = (
                self.durable_world_instructions_fixture(root)
            )
            before_events = runtime.events(assignment.wish.product_id)
            observed = {}

            def restore_inputs(selected, **unused):
                return SimpleNamespace(
                    **vars(selected),
                    world_inputs=inputs,
                    world_evidence=None,
                )

            def refetch(selected, result):
                observed["request"] = dict(result)
                observed["input_sha256"] = selected.world_inputs.binding_sha256
                return evidence

            def factory_resume(selected, result):
                observed["factory_evidence"] = selected.world_evidence
                return {
                    **dict(result),
                    "status": "waiting",
                    "job": "deliver",
                    "needs": [],
                }

            output = StringIO()
            with mock.patch.dict(
                "os.environ", {"FACTORY_PASSWORD": "manager-only"}, clear=True
            ), mock.patch(
                "inventor_workshop.cli._prepare_assignment_world_inputs",
                side_effect=restore_inputs,
            ), mock.patch(
                "inventor_workshop.cli._configured_world_playtest_evidence",
                side_effect=refetch,
            ), mock.patch(
                "inventor_workshop.cli._resume_factory_instructions",
                side_effect=factory_resume,
            ) as factory, mock.patch(
                "inventor_workshop.cli._resume_inventor"
            ) as child, mock.patch(
                "inventor_workshop.cli._run_inventor"
            ) as initial, redirect_stdout(output):
                code = main(
                    (
                        "resume",
                        assignment.wish.product_id,
                        "--root",
                        str(root),
                        "--json",
                    )
                )

            receipt = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(receipt["result"]["job"], "deliver")
            self.assertEqual(
                observed["request"]["artifact_sha256"],
                evidence.artifact_sha256,
            )
            self.assertEqual(observed["input_sha256"], inputs.binding_sha256)
            self.assertIs(observed["factory_evidence"], evidence)
            self.assertEqual(runtime.events(assignment.wish.product_id), before_events)
            factory.assert_called_once()
            child.assert_not_called()
            initial.assert_not_called()

    def test_world_instructions_restart_blocks_factory_without_manager_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, runtime, _, inputs, _ = (
                self.durable_world_instructions_fixture(root)
            )
            before_events = runtime.events(assignment.wish.product_id)

            def restore_inputs(selected, **unused):
                return SimpleNamespace(
                    **vars(selected),
                    world_inputs=inputs,
                    world_evidence=None,
                )

            output = StringIO()
            with mock.patch.dict(
                "os.environ", {"FACTORY_PASSWORD": "manager-only"}, clear=True
            ), mock.patch(
                "inventor_workshop.cli._prepare_assignment_world_inputs",
                side_effect=restore_inputs,
            ), mock.patch(
                "inventor_workshop.cli._configured_world_playtest_evidence",
                return_value=None,
            ), mock.patch(
                "inventor_workshop.cli._resume_factory_instructions"
            ) as factory, mock.patch(
                "inventor_workshop.cli._resume_inventor"
            ) as child, redirect_stdout(output):
                code = main(
                    (
                        "resume",
                        assignment.wish.product_id,
                        "--root",
                        str(root),
                        "--json",
                    )
                )

            receipt = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(
                receipt["result"]["needs"][0]["capability"],
                "world-playtest-evidence",
            )
            self.assertEqual(runtime.events(assignment.wish.product_id), before_events)
            factory.assert_not_called()
            child.assert_not_called()

    def test_world_instructions_restart_rejects_tampered_evidence_before_factory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, _, inputs, _ = self.durable_world_instructions_fixture(
                root
            )
            tampered = ToyWorkshopTest.world_evidence(
                assignment.wish, "f" * 64, inputs
            )

            def restore_inputs(selected, **unused):
                return SimpleNamespace(
                    **vars(selected),
                    world_inputs=inputs,
                    world_evidence=None,
                )

            error = StringIO()
            with mock.patch.dict(
                "os.environ", {"FACTORY_PASSWORD": "manager-only"}, clear=True
            ), mock.patch(
                "inventor_workshop.cli._prepare_assignment_world_inputs",
                side_effect=restore_inputs,
            ), mock.patch(
                "inventor_workshop.cli._configured_world_playtest_evidence",
                return_value=tampered,
            ), mock.patch(
                "inventor_workshop.cli._resume_factory_instructions"
            ) as factory, mock.patch(
                "inventor_workshop.cli._resume_inventor"
            ) as child, redirect_stderr(error):
                code = main(
                    (
                        "resume",
                        assignment.wish.product_id,
                        "--root",
                        str(root),
                        "--json",
                    )
                )

            self.assertEqual(code, 2)
            self.assertIn("another exact context", error.getvalue())
            factory.assert_not_called()
            child.assert_not_called()

    def test_doctor_reports_presence_not_secret_value_or_authenticated_factory(self):
        root = Path(__file__).resolve().parents[1]
        output = StringIO()
        secret = "never-print-this-factory-secret"
        with mock.patch.dict(
            "os.environ",
            {
                "WORKSHOP_CODEX_BIN": "/definitely/missing/codex",
                "WORKSHOP_PRUSASLICER_VERSION": "0.0.0",
                "FACTORY_PASSWORD": secret,
            },
            clear=True,
        ), redirect_stdout(output):
            result = main(("doctor", "--root", str(root), "--json"))
        receipt = json.loads(output.getvalue())
        self.assertEqual(result, 1)
        self.assertNotIn(secret, output.getvalue())
        factory = next(
            item for item in receipt["checks"] if item["name"] == "factory-page"
        )
        codex = next(item for item in receipt["checks"] if item["name"] == "codex")
        self.assertIn("could not run", codex["detail"])
        self.assertEqual(factory["status"], "ready")
        self.assertIn("verified only", factory["detail"])

    def test_doctor_never_exposes_codex_or_factory_secrets_to_slicer_probe(self):
        root = Path(__file__).resolve().parents[1]
        observed = {}

        def runner(command, **kwargs):
            if command[-2:] == ["login", "status"]:
                observed["codex"] = kwargs["env"]
                return subprocess.CompletedProcess(command, 0, stdout="Logged in")
            self.assertEqual(command, ["/fixture/PrusaSlicer", "--help"])
            observed["slicer"] = kwargs["env"]
            return subprocess.CompletedProcess(
                command, 0, stdout="PrusaSlicer-2.9.6\n"
            )

        with mock.patch.dict(
            "os.environ",
            {
                "WORKSHOP_CODEX_BIN": "/fixture/codex",
                "WORKSHOP_PRUSASLICER_BIN": "/fixture/PrusaSlicer",
                "OPENAI_API_KEY": "codex-secret",
                "FACTORY_PASSWORD": "factory-secret",
            },
            clear=True,
        ), mock.patch("inventor_workshop.cli.subprocess.run", side_effect=runner), mock.patch(
            "inventor_workshop.cli.importlib.util.find_spec", return_value=object()
        ), redirect_stdout(StringIO()):
            self.assertEqual(main(("doctor", "--root", str(root))), 0)
        self.assertEqual(observed["codex"]["OPENAI_API_KEY"], "codex-secret")
        self.assertNotIn("OPENAI_API_KEY", observed["slicer"])
        self.assertNotIn("FACTORY_PASSWORD", observed["slicer"])

    def test_inventor_timeout_is_actionable_and_has_no_subprocess_traceback(self):
        def timeout(command, **kwargs):
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "mira"
            assignment = self.resume_assignment(
                root,
                "mira",
                Wish.create("wish-timeout", "A patient moon"),
            )
            with self.assertRaisesRegex(
                WorkshopError, "60 minutes.*workshop status wish-timeout"
            ) as failure:
                _run_inventor(assignment, runner=timeout)
            self.assertIn("workshop resume wish-timeout", str(failure.exception))
            self.assertIn("Do not create a duplicate Wish", str(failure.exception))
            self.assertNotIn("workshop wish", str(failure.exception))

    def test_initial_child_launch_and_nonzero_failures_continue_the_same_wish(self):
        def cannot_launch(command, **kwargs):
            del command, kwargs
            raise OSError("fixture exec failure")

        def stopped(command, **kwargs):
            del kwargs
            return subprocess.CompletedProcess(command, 7, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assignment, _, _ = self.durable_wait_fixture(
                root, product_id="wish-child-failed", transition=False
            )
            for runner in (cannot_launch, stopped):
                with self.subTest(runner=runner.__name__), self.assertRaises(
                    WorkshopError
                ) as failure:
                    _run_inventor(assignment, runner=runner)
                message = str(failure.exception)
                self.assertIn("Do not create a duplicate Wish", message)
                self.assertIn("workshop status wish-child-failed", message)
                self.assertIn("workshop resume wish-child-failed", message)
                self.assertNotIn("workshop wish ", message)

    def test_status_fails_closed_on_a_page_for_different_product_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.durable_wait_fixture(
                root,
                stage="instructions",
                capability="site-page",
                artifact_sha256="f" * 64,
                instructions_sha256="b" * 64,
            )
            stale = Receipt.from_design(
                {
                    "id": "design-one",
                    "slug": "rolling-moon",
                    "owner_id": "owner-mira",
                    "root_id": "design-one",
                    "current_history_id": "history-one",
                    "published_history_id": None,
                    "status": "draft",
                    "project_url": "https://cdn.example.test/history-one/",
                    "listing": None,
                },
                "a" * 64,
                "e" * 64,
            )
            store = mock.Mock()
            store.latest_publish_intent.return_value = {"receipt": stale.to_dict()}
            calls = 0
            read_only = _ReadOnlyWorkshopStore

            def projection(database):
                nonlocal calls
                calls += 1
                return read_only(database) if calls == 1 else store

            with mock.patch(
                "inventor_workshop.cli._ReadOnlyWorkshopStore",
                side_effect=projection,
            ):
                with self.assertRaisesRegex(
                    WorkshopError, "different product bytes"
                ):
                    _status_receipt(root, "wish-one")

    def test_status_recovers_draft_import_crash_from_sealed_instructions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.durable_modern_instructions_fixture(
                root, working=False
            )
            product = Runtime(
                root / "inventors/mira/.workshop/workshop.sqlite3"
            ).get_product("wish-one")
            draft = self.factory_receipt(
                "draft", artifact_sha256=product["artifact_sha256"]
            )
            store = mock.Mock()
            store.latest_publish_intent.return_value = {
                "state": "succeeded",
                "receipt": draft.to_dict(),
            }
            calls = 0
            read_only = _ReadOnlyWorkshopStore

            def projection(database):
                nonlocal calls
                calls += 1
                return read_only(database) if calls == 1 else store

            with mock.patch(
                "inventor_workshop.cli._ReadOnlyWorkshopStore",
                side_effect=projection,
            ), mock.patch(
                "inventor_workshop.cli.sealed_instructions_manifest",
                return_value=SimpleNamespace(artifact_sha256="b" * 64),
            ):
                receipt = _status_receipt(root, "wish-one")
            self.assertEqual(receipt["page"]["status"], "draft")
            self.assertEqual(receipt["resume"]["kind"], "instructions")

    def test_source_version_matches_project_metadata(self):
        project = Path(__file__).resolve().parents[1] / "pyproject.toml"
        in_project = False
        declared = None
        for raw_line in project.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line == "[project]":
                in_project = True
                continue
            if in_project and line.startswith("["):
                break
            if in_project and line.startswith("version = "):
                declared = line.removeprefix("version = ").strip('"')
                break
        self.assertEqual(declared, inventor_workshop.__version__)

    def test_workshop_is_the_canonical_cli_name(self):
        self.assertEqual(parser().prog, "workshop")
        project = (
            Path(__file__).resolve().parents[1] / "pyproject.toml"
        ).read_text(encoding="utf-8")
        self.assertIn('inventor-workshop = "inventor_workshop.cli:main"', project)
        self.assertIn('workshop = "inventor_workshop.cli:main"', project)
        self.assertNotIn("inventor-core =", project)

    def test_audit_does_not_create_or_validate_a_missing_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "missing.sqlite"
            with redirect_stderr(StringIO()):
                result = main(("audit-state", str(database), "typo"))
            self.assertEqual(result, 2)
            self.assertFalse(database.exists())

    def test_new_places_an_inventor_in_the_repository_collection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "inventors").mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "word-games",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable word games",
                        "--lane",
                        "invented-games",
                        "--level",
                        "taste-only",
                        "--root",
                        str(root),
                    )
                )
            self.assertEqual(result, 0)
            self.assertTrue((root / "inventors/word-games/inventor.json").is_file())
            self.assertFalse(
                (root / "inventors/word-games/src/word_games/inventor.py").exists()
            )

    def test_new_accepts_the_inventor_collection_as_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "deduction-games",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable deduction games",
                        "--lane",
                        "invented-games",
                        "--level",
                        "custom-make",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)
            self.assertTrue((collection / "deduction-games/inventor.json").is_file())
            hook = collection / "deduction-games/src/deduction_games/inventor.py"
            self.assertIn("def make(", hook.read_text(encoding="utf-8"))
            self.assertNotIn("def playtest(", hook.read_text(encoding="utf-8"))

    def test_inventors_lists_taste_identity_not_legacy_manifest_prose(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "science-toys",
                        "--name",
                        "Ada",
                        "--niche",
                        "personal orbit models",
                        "--lane",
                        "holdable-science",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)

            output = StringIO()
            with redirect_stdout(output):
                result = main(("inventors", "--root", str(collection), "--json"))
            self.assertEqual(result, 0)
            records = json.loads(output.getvalue())
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["id"], "science-toys")
            self.assertEqual(records[0]["name"], "Ada")
            self.assertEqual(records[0]["status"], "experimental")
            self.assertIn("personal orbit models", records[0]["description"])
            manifest = json.loads(
                (collection / "science-toys/inventor.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("name", manifest)
            self.assertNotIn("niche", manifest)
            self.assertNotIn("summary", manifest)
            self.assertNotIn("autonomy", manifest)

    def test_new_help_is_lane_and_level_not_legacy_template(self):
        command = parser()
        subcommands = next(
            action for action in command._actions if hasattr(action, "choices") and action.choices
        )
        help_text = subcommands.choices["new"].format_help()
        self.assertIn("--lane", help_text)
        self.assertIn("classics-made-yours", help_text)
        self.assertIn("invented-games", help_text)
        self.assertIn("moving-machines", help_text)
        self.assertIn("holdable-science", help_text)
        self.assertIn("little-worlds", help_text)
        for old_lane in (
            "games-puzzles",
            "table-game",
            "desk-toy",
            "model-character",
            "puzzle-keepsake",
        ):
            self.assertNotIn(old_lane, help_text)
        self.assertIn("--level", help_text)
        self.assertIn("taste-only", help_text)
        self.assertIn("custom-make", help_text)
        self.assertIn("custom-playtest", help_text)
        self.assertNotIn("--template", help_text)
        self.assertNotIn("physical-product", help_text)

    def test_hidden_legacy_template_maps_to_invented_games(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            with redirect_stdout(StringIO()):
                result = main(
                    (
                        "new",
                        "legacy-games",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable games",
                        "--template",
                        "board-game",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 0)
            manifest = (collection / "legacy-games/inventor.json").read_text(
                encoding="utf-8"
            )
            self.assertIn('"invented-games"', manifest)

    def test_new_requires_a_toy_lane(self):
        with tempfile.TemporaryDirectory() as temporary:
            collection = Path(temporary) / "inventors"
            collection.mkdir()
            error = StringIO()
            with redirect_stderr(error):
                result = main(
                    (
                        "new",
                        "missing-lane",
                        "--name",
                        "Ada",
                        "--niche",
                        "printable games",
                        "--root",
                        str(collection),
                    )
                )
            self.assertEqual(result, 2)
            self.assertIn("inventor lane must be one of", error.getvalue())

    def test_skills_command_exposes_canonical_workshop_tools(self):
        skills_root = Path(__file__).resolve().parents[1] / "skills"
        output = StringIO()
        with redirect_stdout(output):
            result = main(("skills", "list", "--root", str(skills_root)))
        self.assertEqual(result, 0)
        self.assertIn("product-to-cad", output.getvalue())
        output = StringIO()
        with redirect_stdout(output):
            result = main(("skills", "path", "--root", str(skills_root)))
        self.assertEqual(result, 0)
        self.assertEqual(Path(output.getvalue().strip()), skills_root.resolve())


if __name__ == "__main__":
    unittest.main()
