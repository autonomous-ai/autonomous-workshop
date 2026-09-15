"""A stopped Make adopts corrected CAD tools once and resumes its exact session."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from cli.main import main
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from tests.invent.fake_gamevault import install_fake_gamevault
from tests.workflow.test_native_host import _FakeLauncher
from tests.workflow.test_token_budget import observation
from workshop.errors import ContractError, StateConflict
import workshop.runtime.codex as runtime
from workshop.wish import Wish
from workshop.workflow.agent_run import AgentRun
import workshop.workflow.native_run as host


class BoundLauncher(_FakeLauncher):
    thread_id = "12345678-1234-5678-9234-567812345678"

    def __init__(self):
        super().__init__()
        self.real = runtime.CodexNativeSessionLauncher()
        self.rebindings = []
        self.fail_rebind = None

    def _checkpoint(self, arguments):
        payload = {
            "schema_version": 1, "kind": runtime.CODEX_SESSION_CHECKPOINT_KIND,
            "product_id": arguments["product_id"], "wish_sha256": arguments["wish_sha256"],
            "constitution_sha256": arguments["constitution_sha256"],
            "run_root_sha256": runtime._path_sha256(arguments["run_root"]),
            "host_state_root_sha256": runtime._path_sha256(arguments["host_state_root"]),
            "runtime_config_sha256": "d" * 64, "cli_version": "0.153.4",
            "permission_profile": "workshop-product-run", "native_web_search": True,
            "thread_id": self.thread_id,
        }
        payload["checkpoint_sha256"] = runtime._sha256_json(payload)
        host._write_private_json(Path(arguments["host_state_root"]) / "codex-session.json", payload)

    def rebind_session_constitution(self, **arguments):
        self.rebindings.append(arguments)
        if self.fail_rebind == "before":
            raise RuntimeError("interrupted before session rebind")
        result = self.real.rebind_session_constitution(**arguments)
        if self.fail_rebind == "after":
            raise RuntimeError("interrupted after session rebind")
        return result

    def resume(self, **arguments):
        saved = json.loads((Path(arguments["host_state_root"]) / "codex-session.json").read_bytes())
        assert saved["thread_id"] == self.thread_id
        assert saved["constitution_sha256"] == arguments["constitution_sha256"]
        return super().resume(**arguments)


class ResumeInspectionTest(unittest.TestCase):
    def setUp(self):
        install_fake_gamevault(self)
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.enterContext(mock.patch.dict(os.environ, {"WORKSHOP_HOME": str(self.root / "home")}, clear=True))
        self.enterContext(mock.patch.object(host, "_source_checkout_root", return_value=None))
        self.launcher = BoundLauncher()
        self.enterContext(mock.patch.object(host, "CodexNativeSessionLauncher", return_value=self.launcher))
        self.product_id = "resume-inspection-fixture"
        self.current_roots = host.product_run_domain_skill_roots()

    def start_old(self):
        # A real materialized run with current motion options but the old
        # duplicated kernel call, so motion migration cannot hide this case.
        old_cad = self.root / "old-cad"
        shutil.copytree(self.current_roots["cad"], old_cad,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        reference = old_cad / "references/inspection-and-validation.md"
        reference.write_bytes(reference.read_bytes().replace(host._INSPECTION_CAPABILITY_MARKER, b""))
        validity = old_cad / "scripts/packages/cadgen/src/cadgen/validity.py"
        validity.write_text(validity.read_text().replace(
            "checker = BRepAlgoAPI_Check(wrapped, True, True)\n",
            "checker = BRepAlgoAPI_Check(wrapped, True, True)\n        checker.Perform()\n"))
        with mock.patch.object(host, "product_run_domain_skill_roots", return_value={**self.current_roots, "cad": old_cad}):
            host.start_native_run(
                Wish.create(self.product_id, "a complex lunar arcade", context={"inventor_id": "soren-voss"}),
                effort="spark", max_tokens=100_000_000,
            )
        self.paths = host.native_run_paths(self.product_id)
        run = host._open_budgeted_agent_run(self.paths)
        self.assertEqual(run.snapshot().stage, "make")
        budget = host._load_lifetime_budget(self.paths, run.snapshot())
        budget.observe(observation(123))
        host._save_lifetime_budget(self.paths, run.snapshot(), budget)
        product = self.paths.workspace / "product/cad"
        product.mkdir(parents=True)
        (product / "model.step.py").write_text("# existing unfinished product source\n")
        (product / "review.json").write_text('{"status":"existing evidence"}\n')
        return run

    def ledger(self):
        return [json.loads(line) for line in (self.paths.host_state / "host-corrections.jsonl").read_bytes().splitlines()]

    def assert_corrected(self, run):
        self.assertTrue(host._has_inspection_correction(self.paths, run.snapshot()))
        for relative in ("scripts/packages/cadgen/src/cadgen/validity.py", "scripts/verify_project", "scripts/inspect/inspect_refs/cli.py"):
            self.assertEqual(
                (run.run_root / ".agents/skills/cad" / relative).read_bytes(),
                (self.current_roots["cad"] / relative).read_bytes(),
            )

    def test_plain_cli_resume_updates_tools_keeps_exact_session_and_existing_work(self):
        run = self.start_old()
        before = run.snapshot()
        session_path = self.paths.host_state / "codex-session.json"
        session = json.loads(session_path.read_bytes())
        budget = (self.paths.host_state / "native-budget.json").read_bytes()
        product = {p: p.read_bytes() for p in (self.paths.workspace / "product").rglob("*") if p.is_file()}
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(main(["resume", self.product_id, "--json"]), 0)
        run = host._open_budgeted_agent_run(self.paths)
        self.assert_corrected(run)
        after = run.snapshot()
        for name, digest in before.input_sha256s.items():
            if not name.startswith(".agents/skills/cad/"):
                self.assertEqual(after.input_sha256s[name], digest, name)
        for name in ("stage", "round_index", "max_rounds", "stage_artifacts", "wish_sha256"):
            self.assertEqual(getattr(after, name), getattr(before, name), name)
        self.assertEqual((self.paths.host_state / "native-budget.json").read_bytes(), budget)
        self.assertTrue(all(p.read_bytes() == value for p, value in product.items()))
        current_session = json.loads(session_path.read_bytes())
        for name in set(session) - {"constitution_sha256", "checkpoint_sha256"}:
            self.assertEqual(current_session[name], session[name], name)
        self.assertEqual(len(self.launcher.starts), 1)
        self.assertEqual(len(self.launcher.resumes), 1)
        self.assertIn("Host geometry inspection correction", self.launcher.resumes[0]["prompt"])
        self.assertIn("interrupted inspection has no verdict", self.launcher.resumes[0]["prompt"])

    def test_migration_is_once_and_later_installed_changes_are_not_adopted(self):
        self.start_old()
        host.resume_native_run(self.product_id)
        ledger = (self.paths.host_state / "host-corrections.jsonl").read_bytes()
        session = (self.paths.host_state / "codex-session.json").read_bytes()
        with mock.patch.object(host, "product_run_domain_skill_roots", side_effect=AssertionError("unexpected refresh")):
            host.resume_native_run(self.product_id)
        self.assertEqual((self.paths.host_state / "host-corrections.jsonl").read_bytes(), ledger)
        self.assertEqual((self.paths.host_state / "codex-session.json").read_bytes(), session)
        self.assertEqual(len(self.launcher.rebindings), 1)

    def test_rebind_interruption_is_recovered_even_after_marker_was_installed(self):
        self.start_old()
        self.launcher.fail_rebind = "before"
        with self.assertRaisesRegex(RuntimeError, "before session rebind"):
            host.resume_native_run(self.product_id)
        self.assertEqual(self.launcher.resumes, [])
        run = host._open_budgeted_agent_run(self.paths)
        self.assert_corrected(run)
        self.launcher.fail_rebind = "after"
        with self.assertRaisesRegex(RuntimeError, "after session rebind"):
            host.resume_native_run(self.product_id)
        self.assertEqual(self.launcher.resumes, [])
        self.launcher.fail_rebind = None
        host.resume_native_run(self.product_id)
        self.assertEqual(len(self.launcher.starts), 1)
        self.assertEqual(len(self.launcher.resumes), 1)
        corrections = self.ledger()
        self.assertEqual(sum(r["correction"] == "geometry-inspection-refresh-complete" for r in corrections), 1)

    def test_interruption_writing_completion_is_retryable(self):
        self.start_old()
        record = AgentRun.record_host_correction

        def interrupted(run, value):
            if value["correction"] == "geometry-inspection-refresh-complete":
                raise RuntimeError("interrupted completion record")
            return record(run, value)

        with mock.patch.object(AgentRun, "record_host_correction", interrupted):
            with self.assertRaisesRegex(RuntimeError, "completion record"):
                host.resume_native_run(self.product_id)
        host.resume_native_run(self.product_id)
        self.assertEqual(len(self.launcher.resumes), 1)

    def test_interrupted_refresh_can_finish_with_a_different_motion_choice(self):
        self.start_old()
        self.launcher.fail_rebind = "before"
        with self.assertRaisesRegex(RuntimeError, "before session rebind"):
            host.resume_native_run(self.product_id)
        self.launcher.fail_rebind = None
        host.resume_native_run(self.product_id, check_motion=True)
        ledger = (self.paths.host_state / "host-corrections.jsonl").read_bytes()
        with mock.patch.object(host, "product_run_domain_skill_roots", side_effect=AssertionError("unexpected refresh")):
            host.resume_native_run(self.product_id, check_motion=True)
        self.assertEqual((self.paths.host_state / "host-corrections.jsonl").read_bytes(), ledger)
        self.assertEqual(len(self.launcher.rebindings), 2)
        self.assertEqual(len(self.launcher.resumes), 2)

    def test_pending_make_proposal_is_preserved_and_requires_new_finalization(self):
        run = self.start_old()
        checkpoint = run.snapshot()
        proposal = {
            "schema_version": 1, "kind": "autonomous-workshop.agent-outcome-proposal",
            "checkpoint_sha256": checkpoint.checkpoint_sha256, "subject_sha256": "b" * 64,
            "outcome": {"schema_version": 1, "stage": "make", "status": "waiting",
                        "artifacts": [], "needs": ["old inspection"], "proposed_transition": None},
        }
        content = json.dumps(proposal).encode()
        (run.run_root / "agent-outcome.json").write_bytes(content)
        with mock.patch.object(host, "_resume_native_run_locked", return_value={}) as resume:
            host.resume_native_run(self.product_id)
        self.assertFalse((run.run_root / "agent-outcome.json").exists())
        saved = self.paths.host_state / "motion-resume-outcomes" / (hashlib.sha256(content).hexdigest() + ".json")
        self.assertEqual(saved.read_bytes(), content)
        self.assertNotEqual(resume.call_args.kwargs["checkpoint"].checkpoint_sha256, checkpoint.checkpoint_sha256)

    def test_tampered_frozen_tool_is_refused_before_migration_or_resume(self):
        self.start_old()
        path = self.paths.workspace / ".agents/skills/cad/scripts/verify_project"
        path.chmod(0o700)
        path.write_text("# unrecorded tool edit\n")
        path.chmod(0o500)
        with self.assertRaises(StateConflict):
            host.resume_native_run(self.product_id)
        self.assertEqual(self.launcher.resumes, [])
        self.assertEqual(self.launcher.rebindings, [])

    def test_install_without_correction_is_refused_before_refresh(self):
        run = self.start_old()
        before = run.snapshot()
        roots = {**self.current_roots, "cad": self.root / "old-cad"}
        with mock.patch.object(host, "product_run_domain_skill_roots", return_value=roots):
            with self.assertRaisesRegex(ContractError, "lacks the geometry inspection correction"):
                host.resume_native_run(self.product_id)
        self.assertEqual(run.snapshot(), before)
        self.assertEqual(self.launcher.resumes, [])
        self.assertEqual(self.launcher.rebindings, [])

    def test_status_is_read_only_and_does_not_adopt_correction(self):
        run = self.start_old()
        before = run.snapshot()
        host.native_run_status(self.product_id)
        self.assertEqual(run.snapshot(), before)
        self.assertFalse(host._has_inspection_correction(self.paths, before))

    def test_terminal_resume_does_not_refresh_tools(self):
        from dataclasses import replace
        run = self.start_old()
        for status in ("complete", "failed"):
            with self.subTest(status=status), mock.patch.object(run, "snapshot", return_value=replace(run.snapshot(), status=status)), \
                    mock.patch.object(host, "_open_budgeted_agent_run", return_value=run), \
                    mock.patch.object(host, "_resume_native_run_locked", return_value={}), \
                    mock.patch.object(host, "_adopt_resume_inspection_tools", side_effect=AssertionError("terminal migration")):
                host.resume_native_run(self.product_id)
