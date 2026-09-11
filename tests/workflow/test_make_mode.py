"""Frozen fabrication scope without a new host engineering gate."""

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace
import unittest
from unittest import mock

import pytest

from tests.workflow import test_agent_run as run_fixture
from tests.workflow import test_resume_effort as native_fixture
from tests.workflow import test_native_host as host_fixture
from tests.make import test_native_made as made_fixture
from tests.workflow.test_inventor_selection_host import SelectionRuntime, host
from workshop.errors import ContractError, StateConflict
from workshop.artifacts import build_artifact_manifest
from workshop.wish import Wish
from workshop.workflow.agent_run import AgentArtifact, AgentOutcome, AgentRun
from workshop.workflow.proposals import AgentOutcomeProposal
from workshop.workflow.effort import EFFORT_ROUTE_CAPABILITY_PATH
from workshop.workflow.make_mode import (
    MAKE_PROJECT_PATH, make_project_bytes, parse_make_project_bytes,
    validate_make_mode, validate_make_product,
)
from workshop.workflow.native_run import (
    _open_budgeted_agent_run, materialized_agent_instructions_sha256,
    _evaluate_make_stage, _MakeProposalRejected,
    native_run_paths, refresh_native_run_tools, resume_native_run,
    start_native_run, native_run_status,
)


class MakeModeInputTests(unittest.TestCase):
    def setUp(self):
        run_fixture.AgentRunTest.setUp(self)
        (self.skill / "references" / Path(EFFORT_ROUTE_CAPABILITY_PATH).name).write_text("Frozen lifecycle routes.\n")
        self.domains = {}
        for name in ("cad", "mixed-materials"):
            root = self.root / name
            root.mkdir()
            (root / "SKILL.md").write_text("# " + name + "\n")
            self.domains[name] = root

    def create(self, **kwargs):
        kwargs.setdefault("domain_skill_roots", self.domains)
        kwargs.setdefault("effort", "spark")
        return run_fixture.AgentRunTest.create(self, **kwargs)

    def test_print_freezes_exact_input_and_omits_mixed_skill(self):
        run = self.create(make_mode="print")
        checkpoint = run.snapshot()
        source = run.run_root / MAKE_PROJECT_PATH
        self.assertEqual(source.read_bytes(), b'{"mode":"print","schema_version":1}\n')
        self.assertEqual(stat.S_IMODE(source.stat().st_mode), 0o400)
        self.assertEqual(checkpoint.input_sha256s[MAKE_PROJECT_PATH], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(checkpoint.make_mode, "print")
        self.assertTrue((run.run_root / ".agents/skills/cad/SKILL.md").is_file())
        self.assertFalse((run.run_root / ".agents/skills/mixed-materials").exists())
        reopened = AgentRun.open(run.run_root, host_state_root=run.host_state_root)
        self.assertEqual(reopened.snapshot(), checkpoint)
        without_mode = replace(checkpoint, input_sha256s={p: sha for p, sha in checkpoint.input_sha256s.items() if p != MAKE_PROJECT_PATH})
        self.assertNotEqual(materialized_agent_instructions_sha256(checkpoint), materialized_agent_instructions_sha256(without_mode))

    def test_mixed_freezes_input_and_requires_materialized_skill(self):
        run = self.create(make_mode="mixed")
        self.assertEqual(run.snapshot().make_mode, "mixed")
        self.assertEqual((run.run_root / MAKE_PROJECT_PATH).read_bytes(), make_project_bytes("mixed"))
        self.assertIn(".agents/skills/mixed-materials/SKILL.md", run.snapshot().input_sha256s)

    def test_unselected_legacy_retains_all_supplied_skills_and_no_mode_input(self):
        run = self.create(make_mode=None)
        self.assertIsNone(run.snapshot().make_mode)
        self.assertNotIn(MAKE_PROJECT_PATH, run.snapshot().input_sha256s)
        self.assertFalse((run.run_root / MAKE_PROJECT_PATH).exists())
        self.assertIn(".agents/skills/mixed-materials/SKILL.md", run.snapshot().input_sha256s)

    def test_unsupported_modes_workflows_and_missing_skill_fail_before_creation(self):
        for options in (
            {"make_mode": "3d-print"}, {"make_mode": "mixed-material"},
            {"make_mode": True}, {"make_mode": []},
            {"make_mode": "mixed", "effort": "forge"},
            {"make_mode": "mixed", "effort": "quest"},
            {"make_mode": "mixed", "effort": None},
            {"make_mode": "mixed", "domain_skill_roots": {"cad": self.domains["cad"]}},
        ):
            with self.subTest(options=options), self.assertRaises(ContractError):
                self.create(**options)
            self.assertFalse(self.run_root.exists())
            self.assertFalse(self.host_state_root.exists())

    def test_print_is_available_for_all_existing_lifecycles(self):
        for index, workflow in enumerate((None, "spark", "forge", "quest")):
            with self.subTest(workflow=workflow):
                self.run_root = self.root / ("run-%d" % index)
                self.host_state_root = self.root / ("host-%d" % index)
                run = self.create(make_mode="print", effort=workflow)
                self.assertEqual(run.snapshot().make_mode, "print")
                self.assertEqual(run.snapshot().effort, workflow)

    def test_modified_or_replaced_selection_cannot_open_or_refresh(self):
        run = self.create(make_mode="print")
        source = run.run_root / MAKE_PROJECT_PATH
        source.chmod(0o600)
        source.write_bytes(make_project_bytes("mixed"))
        source.chmod(0o400)
        with self.assertRaisesRegex(StateConflict, "immutable input bytes changed"):
            AgentRun.open(run.run_root, host_state_root=run.host_state_root)
        with self.assertRaises(StateConflict):
            run.refresh_domain_skill_tools(self.domains, reason="must not alter mode")
        source.unlink()
        other = self.root / "external-mode.json"
        other.write_bytes(make_project_bytes("print"))
        source.symlink_to(other)
        with self.assertRaises((StateConflict, ContractError)):
            AgentRun.open(run.run_root, host_state_root=run.host_state_root)

    def test_refresh_preserves_make_selection_and_cannot_add_omitted_skill(self):
        run = self.create(make_mode="print")
        before = run.snapshot()
        (self.domains["cad"] / "SKILL.md").write_text("# Corrected CAD\n")
        changes = run.refresh_domain_skill_tools(self.domains, reason="deterministic CAD correction")
        after = run.snapshot()
        self.assertEqual([row["path"] for row in changes], [".agents/skills/cad/SKILL.md"])
        self.assertEqual(after.make_mode, "print")
        self.assertEqual(after.input_sha256s[MAKE_PROJECT_PATH], before.input_sha256s[MAKE_PROJECT_PATH])
        self.assertFalse((run.run_root / ".agents/skills/mixed-materials").exists())


@pytest.mark.parametrize("content", [
    b'{}', b'[]', b'{"schema_version":true,"mode":"print"}',
    b'{"schema_version":2,"mode":"print"}',
    b'{"schema_version":1,"mode":null}',
    b'{"schema_version":1,"mode":"print","mode":"mixed"}',
    b'{"schema_version":1,"mode":"print","extra":1}',
    b'{"mode":"print","schema_version":1}',  # Noncanonical missing newline.
    b'{"mode":NaN,"schema_version":1}\n',
])
def test_invalid_frozen_input_shape_and_duplicate_keys(content):
    with pytest.raises(ContractError):
        parse_make_project_bytes(content, workflow="spark")


@pytest.mark.parametrize("mode,product", [
    ("print", {"manufacturing": None}),
    ("print", {"manufacturing": {"schema_version": 1}}),
    ("mixed", {}), ("mixed", {"manufacturing": None}),
    ("mixed", {"manufacturing": {"schema_version": True, "manifest_path": "internal/manufacturing.json", "manifest_sha256": "a" * 64}}),
    ("mixed", {"manufacturing": {"schema_version": 1, "manifest_path": "public/bom.json", "manifest_sha256": "a" * 64}}),
    ("mixed", {"manufacturing": {"schema_version": 1, "manifest_path": "internal/manufacturing.json", "manifest_sha256": "bad"}}),
])
def test_product_declaration_cannot_switch_selected_mode(mode, product):
    with pytest.raises(ContractError):
        validate_make_product(mode, product)


def test_host_mode_check_leaves_manufacturing_content_to_make_and_legacy_unchanged():
    validate_make_product("print", {"title": "Printed toy"})
    validate_make_product("mixed", {"manufacturing": {
        "schema_version": 1, "manifest_path": "internal/manufacturing.json", "manifest_sha256": "a" * 64,
    }})  # No filesystem or geometry execution is needed to check declared scope.
    validate_make_product(None, {"manufacturing": None})
    assert validate_make_mode(None, workflow="forge") is None


class MakeModeHandoffTests(unittest.TestCase):
    setUp = made_fixture.NativeMadeTest.setUp

    def evaluate(self, mode, *, manufacturing=False):
        made, product_root = made_fixture.NativeMadeTest._made(self)
        if manufacturing:
            product = dict(made.product)
            product["manufacturing"] = {
                "schema_version": 1, "manifest_path": "internal/manufacturing.json",
                "manifest_sha256": "a" * 64,
            }
            content = (json.dumps(product, sort_keys=True, separators=(",", ":")) + "\n").encode()
            (product_root / "product.json").write_bytes(content)
            made = replace(made, product=product, product_json_sha256=hashlib.sha256(content).hexdigest(),
                           product_manifest=build_artifact_manifest(product_root, created_at="content-addressed"))
        contract_path = "artifacts/make/r0001/made.json"
        content = (json.dumps(made.to_dict(), sort_keys=True, separators=(",", ":")) + "\n").encode()
        (self.run_root / contract_path).write_bytes(content)
        checkpoint = replace(host_fixture.NativeHostTest._launcher_checkpoint(effort="spark", economics_capability=None),
                             wish_sha256=self.wish_sha256, make_mode=mode)
        proposal = AgentOutcomeProposal(
            checkpoint_sha256=checkpoint.checkpoint_sha256, subject_sha256="f" * 64,
            outcome=AgentOutcome(stage="make", status="ready", proposed_transition="release",
                                 artifacts=(AgentArtifact(contract_path, hashlib.sha256(content).hexdigest()),)),
        )
        with mock.patch("workshop.workflow.native_run.verify_native_made_cad", side_effect=AssertionError("no host CAD check")):
            return _evaluate_make_stage(
                proposal, run=SimpleNamespace(run_root=self.run_root), checkpoint=checkpoint,
                subject_sha256=proposal.subject_sha256,
                context={"make_transition": "release", "assignment": self.assignment, "invented": self.invented},
            )

    def test_direct_made_handoff_cannot_omit_mixed_declaration(self):
        with self.assertRaises(_MakeProposalRejected) as failure:
            self.evaluate("mixed")
        self.assertIn("mixed Make mode requires", str(failure.exception.__cause__))

    def test_direct_made_handoff_cannot_smuggle_mixed_declaration_into_print(self):
        with self.assertRaises(_MakeProposalRejected) as failure:
            self.evaluate("print", manufacturing=True)
        self.assertIn("print Make mode forbids", str(failure.exception.__cause__))

    def test_matching_mixed_handoff_checks_only_declared_scope_and_existing_bytes(self):
        decision, _ = self.evaluate("mixed", manufacturing=True)
        self.assertTrue(decision.evidence.passed)
        self.assertEqual(decision.evidence.gate_id, "make.output-handoff-v1")
        self.assertEqual(decision.evidence.checks["host_renders_status"], "not-run")

    def test_unselected_handoff_keeps_existing_print_behavior(self):
        decision, _ = self.evaluate(None)
        self.assertTrue(decision.evidence.passed)


class MakeModeNativeTests(unittest.TestCase):
    setUp = native_fixture.ResumeEffortIntegrationTests.setUp
    native_stream = native_fixture.ResumeEffortIntegrationTests.native_stream

    def initialize_mode(self, mode):
        product_id = "make-mode-fixture"
        receipt = start_native_run(
            Wish.create(product_id, "A desktop mechanical toy", context={"inventor_id": "ivy"}),
            effort="spark", make_mode=mode, manager_model="gpt-6-astra",
            manager_reasoning_effort="medium", max_tokens=500_000_000,
        )
        paths = native_run_paths(product_id)
        return receipt, paths, _open_budgeted_agent_run(paths).snapshot()

    def test_native_print_packet_receipt_resume_and_refresh_preserve_selection(self):
        receipt, paths, before = self.initialize_mode("print")
        expected = {"schema_version": 1, "mode": "print"}
        self.assertEqual(receipt["make_mode"], "print")
        self.assertEqual(json.loads((paths.workspace / "STAGE.json").read_text())["inputs"]["make_mode"], expected)
        source = (paths.workspace / MAKE_PROJECT_PATH).read_bytes()
        session = (paths.host_state / "codex-session.json").read_bytes()
        refreshed = refresh_native_run_tools(before.product_id, reason="mode-preserving fixture refresh")
        self.assertEqual(refreshed["action"], "tools-current")
        self.assertEqual(_open_budgeted_agent_run(paths).snapshot().make_mode, "print")
        resumed = resume_native_run(before.product_id)
        self.assertEqual(resumed["make_mode"], "print")
        self.assertEqual(native_run_status(before.product_id)["make_mode"], "print")
        after = _open_budgeted_agent_run(paths).snapshot()
        self.assertEqual(after.input_sha256s[MAKE_PROJECT_PATH], before.input_sha256s[MAKE_PROJECT_PATH])
        self.assertEqual((paths.workspace / MAKE_PROJECT_PATH).read_bytes(), source)
        self.assertEqual((paths.host_state / "codex-session.json").read_bytes(), session)
        self.assertFalse((paths.workspace / ".agents/skills/mixed-materials").exists())
        self.assertEqual(resumed["budget"]["used_tokens"], 440)
        self.assertEqual(len(self.commands), 2)
        for command in self.commands:
            policy = " ".join(command)
            self.assertIn('"MAKE.json"="read"', policy)
            self.assertIn('"%s"="read"' % (paths.workspace / MAKE_PROJECT_PATH), policy)
        self.popen.assert_not_called()

    def test_native_mixed_packet_and_status_are_explicit(self):
        receipt, paths, checkpoint = self.initialize_mode("mixed")
        self.assertEqual(receipt["make_mode"], "mixed")
        self.assertEqual(checkpoint.make_mode, "mixed")
        self.assertEqual(json.loads((paths.workspace / "STAGE.json").read_text())["inputs"]["make_mode"], {"schema_version": 1, "mode": "mixed"})
        self.assertIn(".agents/skills/mixed-materials/SKILL.md", checkpoint.input_sha256s)

    def test_native_legacy_mode_absent_packet_and_null_receipt(self):
        receipt, paths, checkpoint = self.initialize_mode(None)
        self.assertIsNone(receipt["make_mode"])
        self.assertNotIn("make_mode", json.loads((paths.workspace / "STAGE.json").read_text())["inputs"])
        self.assertNotIn(MAKE_PROJECT_PATH, checkpoint.input_sha256s)
        self.assertIn(".agents/skills/mixed-materials/SKILL.md", checkpoint.input_sha256s)
        resumed = resume_native_run(checkpoint.product_id)
        self.assertIsNone(resumed["make_mode"])
        self.assertEqual(_open_budgeted_agent_run(paths).snapshot().input_sha256s, checkpoint.input_sha256s)
        for command in self.commands:
            self.assertNotIn('"MAKE.json"="read"', " ".join(command))

    def test_native_invalid_mode_or_workflow_refused_before_reservation(self):
        with mock.patch("workshop.workflow.native_run.native_run_paths") as paths:
            for mode, workflow in (("bogus", "spark"), ("mixed", "forge"), ("mixed", "quest")):
                with self.subTest(mode=mode, workflow=workflow), self.assertRaises(ContractError):
                    start_native_run(Wish.create("invalid-mode", "A toy"), effort=workflow, make_mode=mode)
            paths.assert_not_called()
        self.assertFalse(self.commands)


@pytest.mark.parametrize("mode", ["print", "mixed"])
def test_inventor_setup_receives_mode_before_make(host, mode):
    runtime = SelectionRuntime()
    wish = host(runtime)
    result = start_native_run(wish, effort="spark", make_mode=mode)
    assert result["make_mode"] == mode
    assert runtime.pending[0]["inputs"]["make_mode"] == {"schema_version": 1, "mode": mode}
    assert runtime.make[0]["inputs"]["make_mode"] == {"schema_version": 1, "mode": mode}
    assert "inputs.make_mode select " + mode in runtime.starts[0]["prompt"]
