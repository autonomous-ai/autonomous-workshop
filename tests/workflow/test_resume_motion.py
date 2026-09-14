"""Resume applies motion defaults to the same private run and native session."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock
from contextlib import chdir, redirect_stdout, redirect_stderr
from io import StringIO

from tests.invent.fake_gamevault import install_fake_gamevault
from tests.workflow.test_native_host import _FakeLauncher, _FinalizedMatchThenInterruptLauncher
from dataclasses import replace
from workshop.errors import ContractError
from workshop.wish import Wish
import workshop.workflow.native_run as host


class MotionLauncher(_FakeLauncher):
    def __init__(self):
        super().__init__()
        self.rebindings = []
        self.fail_rebind = False

    def rebind_session_constitution(self, **arguments):
        if self.fail_rebind:
            raise RuntimeError("interrupted session rebind")
        self.rebindings.append(arguments)
        return {"changed": True, "previous_constitution_sha256": "a" * 64,
                "constitution_sha256": arguments["constitution_sha256"]}


class ResumeMotionTest(unittest.TestCase):
    def setUp(self):
        install_fake_gamevault(self)
        self.temp = str(Path(self.enterContext(tempfile.TemporaryDirectory())).resolve())
        self.enterContext(mock.patch.dict(os.environ, {"WORKSHOP_HOME": self.temp}, clear=True))
        self.enterContext(mock.patch.object(host, "_source_checkout_root", return_value=None))
        self.launcher = MotionLauncher()
        self.enterContext(mock.patch.object(host, "CodexNativeSessionLauncher", return_value=self.launcher))
        self.product_id = "resume-motion-fixture"

    def start(self, **options):
        host.start_native_run(Wish.create(self.product_id, "a small mechanical toy"), **options)
        self.paths = host.native_run_paths(self.product_id)

    def legacy(self):
        self.start()
        run = host._open_budgeted_agent_run(self.paths)
        payload = run._load()
        entries = [dict(item) for item in payload["inputs"] if item["path"] != "MAKE-OPTIONS.json"]
        (run.run_root / "MAKE-OPTIONS.json").unlink()
        # Model a pre-option private verifier, while retaining the exact rest
        # of the run, its budget, constitution and saved session.
        name = ".agents/skills/cad/scripts/verify_project"
        target = run.run_root / name
        source = b"#!/usr/bin/env python3\nraise SystemExit('legacy mandatory motion')\n"
        target.chmod(0o700)
        target.write_bytes(source)
        target.chmod(0o500)
        for item in entries:
            if item["path"] == name:
                item.update(sha256=hashlib.sha256(source).hexdigest(), size=len(source))
        run._write_next(payload, dict(payload, inputs=entries))
        return run

    def selected(self):
        return json.loads((self.paths.workspace / "MAKE-OPTIONS.json").read_bytes())["check_motion"]

    def test_resume_omission_disables_previously_enabled_run_and_opt_in_reenables(self):
        self.start(check_motion=True)
        for options, expected in (({}, False), ({"check_motion": True}, True), ({}, False)):
            receipt = host.resume_native_run(self.product_id, **options)
            self.assertIs(self.selected(), expected)
            self.assertEqual(receipt["status"], "waiting")
            self.assertIn("Host motion policy", self.launcher.resumes[-1]["prompt"])
            self.assertIn("reread", self.launcher.resumes[-1]["prompt"])
        self.assertEqual(len(self.launcher.starts), 1)
        self.assertEqual(len(self.launcher.resumes), 3)
        self.assertEqual(self.launcher.rebindings, [])

    def test_legacy_resume_migrates_tools_and_keeps_session_and_budget(self):
        run = self.legacy()
        before = run.snapshot()
        budget_path = self.paths.host_state / "native-budget.json"
        budget = budget_path.read_bytes()
        with mock.patch.object(host, "_resume_native_run_locked", return_value={}) as continue_run:
            host.resume_native_run(self.product_id)
        after = continue_run.call_args.kwargs["checkpoint"]
        self.assertFalse(self.selected())
        self.assertEqual(budget_path.read_bytes(), budget)
        for name in ("AGENTS.md", "WISH.json", ".agents/skills/autonomous-workshop/SKILL.md"):
            self.assertEqual(before.input_sha256s[name], after.input_sha256s[name])
        self.assertEqual(before.stage, after.stage)
        self.assertEqual(before.stage_artifacts, after.stage_artifacts)
        self.assertEqual(before.round_index, after.round_index)
        self.assertEqual(len(self.launcher.rebindings), 1)
        self.assertEqual(self.launcher.rebindings[0]["product_id"], self.product_id)
        verifier = self.paths.workspace / ".agents/skills/cad/scripts/verify_project"
        self.assertIn("--check-motion", verifier.read_text())
        policy = runpy.run_path(str(verifier.with_name("motion_policy.py")))
        self.assertFalse(policy["enabled"]())
        tool = runpy.run_path(str(verifier))
        project = tool["_sc_project"](Path(self.temp))
        (project / "README.md").write_text("## Assembly\nInsert the pin into the body.\n")
        (project / "measure/motion.json").write_text("invalid old motion manifest")
        output = StringIO()
        with chdir(Path(self.temp)), redirect_stdout(output), redirect_stderr(StringIO()):
            self.assertEqual(tool["main"]([str(project), "--dry-run"]), 0)
        self.assertIn("motion is unverified", output.getvalue())
        self.assertNotIn("scripts/check_motion", output.getvalue())
        # Once adopted, future resumes retain the materialized tools even if
        # the installed source later changes.
        with mock.patch.object(host, "product_run_agent_assets", side_effect=AssertionError("unexpected refresh")):
            host.resume_native_run(self.product_id, check_motion=True)
        self.assertTrue(self.selected())
        self.assertEqual(len(self.launcher.starts), 1)
        self.assertEqual(len(self.launcher.resumes), 1)

    def test_interrupted_legacy_migration_retries_before_setting_options(self):
        self.legacy()
        self.launcher.fail_rebind = True
        with self.assertRaisesRegex(RuntimeError, "interrupted session rebind"):
            host.resume_native_run(self.product_id)
        self.assertFalse((self.paths.workspace / "MAKE-OPTIONS.json").exists())
        self.assertEqual(self.launcher.resumes, [])
        self.launcher.fail_rebind = False
        host.resume_native_run(self.product_id)
        self.assertFalse(self.selected())
        self.assertEqual(len(self.launcher.resumes), 1)

    def test_invalid_motion_never_opens_or_mutates_run(self):
        with mock.patch.object(host, "native_run_paths") as paths:
            for invalid in (None, 0, "false"):
                with self.subTest(invalid=invalid), self.assertRaises(ContractError):
                    host.resume_native_run(self.product_id, check_motion=invalid)
            paths.assert_not_called()

    def test_policy_change_preserves_interrupted_finalized_inventor_selection(self):
        with mock.patch.object(host, "CodexNativeSessionLauncher", return_value=_FinalizedMatchThenInterruptLauncher()):
            with self.assertRaises(KeyboardInterrupt):
                self.start(check_motion=True)
        self.paths = host.native_run_paths(self.product_id)
        host.resume_native_run(self.product_id)
        self.assertFalse(self.selected())
        self.assertEqual(len(self.launcher.resumes), 1)
        self.assertIn("current invent stage", self.launcher.resumes[0]["prompt"])

    def test_pending_make_is_preserved_but_must_refinalize_after_policy_change(self):
        self.start(check_motion=False)
        run = host._open_budgeted_agent_run(self.paths)
        before = run.snapshot()
        proposal = {
            "schema_version": 1, "kind": "autonomous-workshop.agent-outcome-proposal",
            "checkpoint_sha256": before.checkpoint_sha256, "subject_sha256": "b" * 64,
            "outcome": {"schema_version": 1, "stage": "make", "status": "waiting",
                        "artifacts": [], "needs": ["motion disabled"], "proposed_transition": None},
        }
        content = json.dumps(proposal).encode()
        path = run.run_root / "agent-outcome.json"
        path.write_bytes(content)
        # Two consecutive host corrections model interrupted legacy refresh
        # followed by selection. Both must be traversed on retry.
        run.refresh_domain_skill_tools({}, reason="workshop resume --check-motion true", check_motion=True)
        run.refresh_domain_skill_tools({}, reason="workshop resume --check-motion false", check_motion=False)
        current = replace(run.snapshot(), stage="make")
        host._reconcile_motion_resume_outputs(run, current)
        self.assertFalse(path.exists())
        saved = run.host_state_root / "motion-resume-outcomes" / (hashlib.sha256(content).hexdigest() + ".json")
        self.assertEqual(saved.read_bytes(), content)
        host._reconcile_motion_resume_outputs(run, current)

    def test_publication_wait_survives_policy_checkpoint_change(self):
        self.start(check_motion=True)
        run = host._open_budgeted_agent_run(self.paths)
        before = replace(run.snapshot(), stage="release")
        waiting = {
            "schema_version": 1, "kind": "autonomous-workshop.release-effect-wait",
            "product_id": self.product_id, "stage": "release",
            "waiting_checkpoint_sha256": before.checkpoint_sha256,
            "proposal_checkpoint_sha256": "a" * 64, "proposal_subject_sha256": "b" * 64,
            "proposal_outcome_sha256": "c" * 64, "inventor_id": "soren-voss",
            "need": host._FACTORY_CREDENTIALS_NEED,
        }
        wait_path = host._release_effect_wait_path(run)
        host._atomic_private_write(wait_path, json.dumps(waiting).encode())
        run.refresh_domain_skill_tools({}, reason="workshop resume --check-motion false", check_motion=False)
        current = replace(run.snapshot(), stage="release")
        host._reconcile_motion_resume_outputs(run, current)
        actual = host._read_release_effect_wait(run, current)
        self.assertEqual(actual, {**waiting, "waiting_checkpoint_sha256": current.checkpoint_sha256})

    def test_pending_make_tool_refresh_quarantines_only_exact_ancestor(self):
        self.start(check_motion=False)
        run = host._open_budgeted_agent_run(self.paths)
        before = run.snapshot()
        proposal = {
            "schema_version": 1, "kind": "autonomous-workshop.agent-outcome-proposal",
            "checkpoint_sha256": before.checkpoint_sha256, "subject_sha256": "b" * 64,
            "outcome": {"schema_version": 1, "stage": "make", "status": "waiting",
                        "artifacts": [], "needs": ["report writer mismatch"], "proposed_transition": None},
        }
        run.refresh_domain_skill_tools({}, reason="workshop resume --refresh-tools", check_motion=True)
        current = replace(run.snapshot(), stage="make")
        path = run.run_root / "agent-outcome.json"
        for binding, stage, preserved in [
            ("f" * 64, "make", False),
            (before.checkpoint_sha256, "release", False),
            (before.checkpoint_sha256, "make", True),
        ]:
            with self.subTest(binding=binding, stage=stage):
                proposal["checkpoint_sha256"] = binding
                proposal["outcome"]["stage"] = stage
                content = json.dumps(proposal).encode()
                path.write_bytes(content)
                host._reconcile_motion_resume_outputs(run, current)
                self.assertEqual(path.exists(), not preserved)
                if preserved:
                    saved = run.host_state_root / "motion-resume-outcomes" / (hashlib.sha256(content).hexdigest() + ".json")
                    self.assertEqual(saved.read_bytes(), content)
                    host._reconcile_motion_resume_outputs(run, current)
