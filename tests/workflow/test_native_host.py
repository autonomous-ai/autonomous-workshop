import hashlib
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from cli.main import main, parser
from workshop.errors import ContractError, StateConflict
from workshop.match.native import (
    InventorRoster,
    MatchRankingEntry,
    NativeMatchAssignment,
)
from workshop.product import ToyBlueprint
from workshop.workflow.native_run import (
    NativeRunPaths,
    _native_run_mutation_lock,
    canonical_wish_bytes,
    native_run_paths,
    start_native_run,
)
from workshop.runtime import CodexInvocationError
from workshop.wish import Wish
from workshop.workflow.agent_run import AgentArtifact, AgentOutcome
from workshop.workflow.proposals import AgentOutcomeProposal


class _FakeOutcome:
    def __init__(self, arguments):
        self.arguments = dict(arguments)

    def to_dict(self):
        return {
            "status": "completed",
            "session": {
                "product_id": self.arguments["product_id"],
                "wish_sha256": self.arguments["wish_sha256"],
                "constitution_sha256": self.arguments["constitution_sha256"],
                "checkpoint_sha256": "c" * 64,
            },
            "used_web_search": False,
        }


class _FakeLauncher:
    def __init__(self, *, fail_first_start=False):
        self.starts = []
        self.resumes = []
        self.fail_first_start = fail_first_start

    @staticmethod
    def _checkpoint(arguments):
        checkpoint = Path(arguments["host_state_root"]) / "codex-session.json"
        checkpoint.write_text("{}\n", encoding="utf-8")
        os.chmod(checkpoint, 0o600)

    @staticmethod
    def _write_waiting(arguments):
        stage = json.loads(
            (Path(arguments["run_root"]) / "STAGE.json").read_text(
                encoding="utf-8"
            )
        )
        proposal = {
            "schema_version": 1,
            "kind": "autonomous-workshop.agent-outcome-proposal",
            "checkpoint_sha256": stage["checkpoint_sha256"],
            "subject_sha256": stage["subject_sha256"],
            "outcome": {
                "schema_version": 1,
                "stage": stage["stage"],
                "status": "waiting",
                "artifacts": [],
                "needs": ["fixture stops after one native turn"],
                "proposed_transition": None,
            },
        }
        (Path(arguments["run_root"]) / "agent-outcome.json").write_text(
            json.dumps(proposal, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        if self.fail_first_start:
            self.fail_first_start = False
            raise CodexInvocationError("fixture interruption before thread.started")
        self._checkpoint(arguments)
        self._write_waiting(arguments)
        return _FakeOutcome(arguments)

    def resume(self, **arguments):
        self.resumes.append(dict(arguments))
        self._write_waiting(arguments)
        return _FakeOutcome(arguments)


class _FinalizedMatchThenFailLauncher(_FakeLauncher):
    """Simulate a launcher failure after the exact Match finalizer boundary."""

    def __init__(self, *, stale_proposal=False, invalid_proposal=False):
        super().__init__()
        if stale_proposal and invalid_proposal:
            raise ValueError("fixture proposal mode is ambiguous")
        self.stale_proposal = stale_proposal
        self.invalid_proposal = invalid_proposal

    @staticmethod
    def _canonical_json(value):
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

    def _write_ready_match(self, arguments):
        run_root = Path(arguments["run_root"])
        stage = json.loads((run_root / "STAGE.json").read_text(encoding="utf-8"))
        roster = InventorRoster.from_mapping(stage["inputs"]["inventor_roster"])
        selected = roster.inventors[0]
        assignment = NativeMatchAssignment(
            wish_sha256=arguments["wish_sha256"],
            inventor_roster_sha256=roster.roster_sha256,
            selected_inventor_id=selected.inventor_id,
            selected_agent_path=selected.agent_path,
            selected_agent_sha256=selected.agent_sha256,
            selected_source_manifest_sha256=selected.source_manifest_sha256,
            selected_taste_sha256=selected.taste_sha256,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=tuple(
                MatchRankingEntry(
                    inventor_id=entry.inventor_id,
                    rationale="Stable fixture ranking for the exact materialized roster.",
                )
                for entry in roster.inventors
            ),
        )
        relative = "artifacts/match/assignment.json"
        content = self._canonical_json(assignment.to_dict())
        target = run_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        artifact = AgentArtifact(
            path=relative,
            sha256=hashlib.sha256(content).hexdigest(),
        )
        outcome = AgentOutcome(
            stage="match",
            status="ready",
            artifacts=(artifact,),
            proposed_transition="invent",
        )
        proposal = AgentOutcomeProposal(
            checkpoint_sha256=(
                "0" * 64
                if self.stale_proposal
                else stage["checkpoint_sha256"]
            ),
            subject_sha256=stage["subject_sha256"],
            outcome=outcome,
        )
        outcome_path = run_root / "agent-outcome.json"
        if self.invalid_proposal:
            outcome_path.write_bytes(b"{")
        else:
            outcome_path.write_bytes(
                self._canonical_json(proposal.to_dict()) + b"\n"
            )

    def start(self, **arguments):
        self.starts.append(dict(arguments))
        self._checkpoint(arguments)
        self._write_ready_match(arguments)
        raise CodexInvocationError("fixture failed after finalization")


class NativeHostTest(unittest.TestCase):
    def test_second_mutating_host_fails_while_run_lock_is_held(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            host_state = root / "host-state"
            host_state.mkdir(mode=0o700)
            paths = NativeRunPaths(root / "toy", host_state)

            with _native_run_mutation_lock(paths):
                with self.assertRaisesRegex(
                    StateConflict, "already mutating this Wish"
                ):
                    with _native_run_mutation_lock(paths):
                        self.fail("a second mutating host acquired the run lock")

            self.assertEqual(
                stat.S_IMODE((host_state / "mutation.lock").stat().st_mode),
                0o600,
            )

    def test_source_checkout_places_toy_project_at_repository_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            repository = root / "repository"
            repository.mkdir(mode=0o700)
            home = root / "workshop-home"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=repository,
            ):
                paths = native_run_paths("stable-toy-id", create=True)

            self.assertEqual(paths.workspace, repository / "toys/stable-toy-id")
            self.assertEqual(paths.host_state, home / "state/stable-toy-id")
            self.assertFalse(paths.workspace.exists())
            self.assertFalse(paths.host_state.exists())
            self.assertTrue((repository / "toys").is_dir())
            self.assertTrue((home / "state").is_dir())

    def test_wish_starts_native_session_before_any_effect_path(self):
        launcher = _FakeLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            stdout = StringIO()
            stderr = StringIO()
            with mock.patch.dict(
                os.environ,
                {
                    "WORKSHOP_HOME": str(home),
                    "FACTORY_PASSWORD": "must-never-be-used",
                },
                clear=True,
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), redirect_stdout(stdout), redirect_stderr(stderr):
                result = main(
                    (
                        "wish",
                        "a",
                        "wind-up",
                        "version",
                        "of",
                        "my",
                        "dog",
                        "--publish",
                        "--json",
                    )
                )

            self.assertEqual(result, 0)
            receipt = json.loads(stdout.getvalue())
            product_id = receipt["product_id"]
            workspace = home / "toys" / product_id
            host_state = home / "state" / product_id
            self.assertEqual(len(launcher.starts), 1)
            arguments = launcher.starts[0]
            self.assertEqual(arguments["run_root"], workspace)
            self.assertEqual(arguments["host_state_root"], host_state)
            self.assertEqual(stat.S_IMODE(workspace.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(host_state.stat().st_mode), 0o700)
            self.assertEqual(
                (workspace / "WISH.json").read_bytes(),
                canonical_wish_bytes(
                    Wish.create(
                        product_id,
                        "a wind-up version of my dog",
                        context={"source": "workshop-cli"},
                    )
                ),
            )
            self.assertTrue((workspace / "AGENTS.md").is_file())
            self.assertTrue(
                (
                    workspace
                    / ".agents"
                    / "skills"
                    / "autonomous-workshop"
                    / "SKILL.md"
                ).is_file()
            )
            for skill_name in (
                "cad",
                "design-reference",
                "image-to-cad",
                "step-parts",
            ):
                self.assertTrue(
                    (
                        workspace
                        / ".agents"
                        / "skills"
                        / skill_name
                        / "SKILL.md"
                    ).is_file()
                )
            for inventor_id in ("abo", "alice", "bob", "eve", "ivy", "leo"):
                self.assertTrue(
                    (workspace / ".codex" / "agents" / (inventor_id + ".toml")).is_file()
                )
                self.assertTrue(
                    (
                        workspace
                        / ".agents"
                        / "skills"
                        / (inventor_id + "-inventor")
                        / "SKILL.md"
                    ).is_file()
                )
            self.assertFalse((workspace / "catalog").exists())
            prompt = arguments["prompt"]
            self.assertIn("local AGENTS.md", prompt)
            self.assertIn("autonomous-workshop skill", prompt)
            self.assertIn("current match stage", prompt)
            self.assertIn("Create one native Codex goal", prompt)
            self.assertIn("successful finalization as its stopping condition", prompt)
            self.assertIn("inspecting, acting, evaluating, and improving", prompt)
            self.assertIn("complete the goal", prompt)
            self.assertIn("STAGE.json", prompt)
            self.assertIn("agent-outcome.json", prompt)
            self.assertNotIn("wind-up", prompt)
            self.assertNotIn(str(home), prompt)
            self.assertNotIn("FACTORY", prompt)
            self.assertEqual(receipt["publication"]["status"], "not-created")
            self.assertTrue(receipt["publication"]["requested"])
            self.assertIn("before Match", stderr.getvalue())
    def test_resume_uses_exact_materialized_binding(self):
        launcher = _FakeLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            environment = {"WORKSHOP_HOME": str(home)}
            output = StringIO()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(("wish", "a moon that waddles", "--json")),
                    0,
                )
            started_receipt = json.loads(output.getvalue())
            product_id = started_receipt["product_id"]
            started = launcher.starts[0]

            output = StringIO()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "workshop.workflow.native_run.product_run_agent_assets",
                side_effect=AssertionError("resume must use materialized bytes"),
            ) as current_assets, redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(
                    main(("resume", product_id, "--json")),
                    0,
                )
            resumed_receipt = json.loads(output.getvalue())
            self.assertEqual(len(launcher.resumes), 1)
            resumed = launcher.resumes[0]
            for field in (
                "product_id",
                "wish_sha256",
                "constitution_sha256",
                "run_root",
                "host_state_root",
            ):
                self.assertEqual(resumed[field], started[field])
            self.assertNotIn("moon that waddles", resumed["prompt"])
            self.assertNotIn(str(home), resumed["prompt"])
            self.assertEqual(resumed_receipt["action"], "resumed")
            current_assets.assert_not_called()

            output = StringIO()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), redirect_stdout(output):
                self.assertEqual(main(("status", product_id, "--json")), 0)
            status = json.loads(output.getvalue())
            self.assertEqual(status["kind"], "native-agent-run")
            self.assertEqual(status["session_status"], "checkpointed")
            self.assertEqual(
                status["agent_instructions_sha256"],
                started["constitution_sha256"],
            )

    def test_resume_safely_restarts_only_when_no_session_checkpoint_exists(self):
        interrupted = _FakeLauncher(fail_first_start=True)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            environment = {"WORKSHOP_HOME": str(home)}
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=interrupted,
            ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(main(("wish", "a tiny orbit", "--json")), 2)

            product_ids = [path.name for path in (home / "toys").iterdir()]
            self.assertEqual(len(product_ids), 1)
            product_id = product_ids[0]
            self.assertFalse(
                (home / "state" / product_id / "codex-session.json").exists()
            )

            recovered = _FakeLauncher()
            output = StringIO()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=recovered,
            ), redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(main(("resume", product_id, "--json")), 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["action"], "started-after-interruption")
            self.assertEqual(len(recovered.starts), 1)
            self.assertEqual(recovered.resumes, [])

    def test_launcher_failure_after_exact_proposal_uses_normal_gate_and_continues(self):
        launcher = _FinalizedMatchThenFailLauncher()
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "post-finalizer-launch-failure"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                receipt = start_native_run(
                    Wish.create(product_id, "a small resilient clockwork toy")
                )

            self.assertEqual(receipt["stage"], "invent")
            self.assertEqual(receipt["status"], "waiting")
            self.assertEqual(receipt["native_turns"], 2)
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(len(launcher.resumes), 1)
            workspace = home / "toys" / product_id
            host_state = home / "state" / product_id
            self.assertFalse((workspace / "agent-outcome.json").exists())
            self.assertTrue(
                any(
                    path.name.endswith("-match.json")
                    for path in (host_state / "gates").iterdir()
                )
            )

    def test_launcher_failure_with_stale_proposal_fails_closed(self):
        launcher = _FinalizedMatchThenFailLauncher(stale_proposal=True)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "stale-post-finalizer-proposal"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), self.assertRaisesRegex(StateConflict, "another checkpoint"):
                start_native_run(
                    Wish.create(product_id, "a stale proposal must never advance")
                )

            host_state = home / "state" / product_id
            self.assertFalse(
                any(
                    path.name.endswith("-match.json")
                    for path in (host_state / "gates").iterdir()
                )
            )
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(launcher.resumes, [])

    def test_launcher_failure_with_invalid_proposal_fails_closed(self):
        launcher = _FinalizedMatchThenFailLauncher(invalid_proposal=True)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve() / "workshop-home"
            product_id = "invalid-post-finalizer-proposal"
            with mock.patch.dict(
                os.environ, {"WORKSHOP_HOME": str(home)}, clear=True
            ), mock.patch(
                "workshop.workflow.native_run._source_checkout_root",
                return_value=None,
            ), mock.patch(
                "workshop.workflow.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), self.assertRaisesRegex(ContractError, "strict UTF-8 JSON"):
                start_native_run(
                    Wish.create(product_id, "an invalid proposal must never advance")
                )

            host_state = home / "state" / product_id
            self.assertFalse(
                any(
                    path.name.endswith("-match.json")
                    for path in (host_state / "gates").iterdir()
                )
            )
            self.assertEqual(len(launcher.starts), 1)
            self.assertEqual(launcher.resumes, [])

    def test_native_commands_default_to_private_draft(self):
        command = parser()
        self.assertFalse(command.parse_args(("wish", "a moon")).publish)
        self.assertFalse(command.parse_args(("resume", "wish-one")).publish)
        self.assertTrue(command.parse_args(("wish", "a moon", "--publish")).publish)


if __name__ == "__main__":
    unittest.main()
