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
from cli.native_run import canonical_wish_bytes
from workshop.runtime import CodexInvocationError
from workshop.wish import Wish


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


class NativeCliRunTest(unittest.TestCase):
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
                "cli.native_run.CodexNativeSessionLauncher",
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
            container = home / "runs" / product_id
            workspace = container / "workspace"
            host_state = container / "host-state"
            self.assertEqual(len(launcher.starts), 1)
            arguments = launcher.starts[0]
            self.assertEqual(arguments["run_root"], workspace)
            self.assertEqual(arguments["host_state_root"], host_state)
            self.assertEqual(stat.S_IMODE(container.stat().st_mode), 0o700)
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
            for skill_name in ("cad", "product-to-cad", "step-parts"):
                self.assertTrue(
                    (
                        workspace
                        / ".agents"
                        / "skills"
                        / skill_name
                        / "SKILL.md"
                    ).is_file()
                )
            for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
                persona = workspace / "catalog" / "inventors" / inventor_id
                self.assertTrue((persona / "inventor.json").is_file())
                self.assertTrue((persona / "TASTE.md").is_file())
                self.assertFalse((persona / "skills").exists())
                self.assertTrue(
                    (
                        workspace
                        / ".agents"
                        / "skills"
                        / (inventor_id + "-inventor")
                        / "SKILL.md"
                    ).is_file()
                )
            prompt = arguments["prompt"]
            self.assertIn("local AGENTS.md", prompt)
            self.assertIn("autonomous-workshop skill", prompt)
            self.assertIn("current match stage", prompt)
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
                "cli.native_run.CodexNativeSessionLauncher",
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
                "cli.native_run.CodexNativeSessionLauncher",
                return_value=launcher,
            ), mock.patch(
                "cli.native_run.product_run_agent_assets",
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
            with mock.patch.dict(os.environ, environment, clear=True), redirect_stdout(output):
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
                "cli.native_run.CodexNativeSessionLauncher",
                return_value=interrupted,
            ), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(main(("wish", "a tiny orbit", "--json")), 2)

            product_ids = [path.name for path in (home / "runs").iterdir()]
            self.assertEqual(len(product_ids), 1)
            product_id = product_ids[0]
            self.assertFalse(
                (home / "runs" / product_id / "host-state" / "codex-session.json").exists()
            )

            recovered = _FakeLauncher()
            output = StringIO()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                "cli.native_run.CodexNativeSessionLauncher",
                return_value=recovered,
            ), redirect_stdout(output), redirect_stderr(StringIO()):
                self.assertEqual(main(("resume", product_id, "--json")), 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["action"], "started-after-interruption")
            self.assertEqual(len(recovered.starts), 1)
            self.assertEqual(recovered.resumes, [])

    def test_native_commands_default_to_private_draft(self):
        command = parser()
        self.assertFalse(command.parse_args(("wish", "a moon")).publish)
        self.assertFalse(command.parse_args(("resume", "wish-one")).publish)
        self.assertTrue(command.parse_args(("wish", "a moon", "--publish")).publish)


if __name__ == "__main__":
    unittest.main()
