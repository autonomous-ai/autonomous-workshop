"""Explicit resume settings preserve one real host run and native binding."""

from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from tests.invent.fake_gamevault import install_fake_gamevault
from tests.runtime.test_codex_usage import ROOT
from tests.workflow.test_native_host import _FakeLauncher
from tests.workflow.test_token_budget import observation
from workshop.errors import ContractError, StateConflict
from workshop.runtime.codex import CodexNativeSessionLauncher
from workshop.wish import Wish
from workshop.workflow import agent_run as agent_run_module
from workshop.workflow.agent_run import AgentRun, MANAGER_EFFORT_CHANGE_FILE
from workshop.workflow.budgets import BUDGETS_CAPABILITY_PATH
from workshop.workflow.native_run import (
    _load_lifetime_budget,
    _native_run_mutation_lock,
    _open_budgeted_agent_run,
    native_run_paths,
    resume_native_run,
    start_native_run,
)
from workshop.workflow.token_budget import TOKEN_BUDGET_CAPABILITY_PATH


class ResumeEffortIntegrationTests(unittest.TestCase):
    def setUp(self):
        install_fake_gamevault(self)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.patches = ExitStack()
        self.addCleanup(self.patches.close)
        self.patches.enter_context(mock.patch.dict(os.environ, {
            "WORKSHOP_HOME": str(self.root / "workshop-home"),
            "HOME": str(self.root),
            "PATH": os.defpath,
        }, clear=True))
        self.patches.enter_context(mock.patch(
            "workshop.workflow.native_run._source_checkout_root", return_value=None,
        ))
        self.commands = []
        self.turn_settings = []
        self.consumption = 0
        self.popen = mock.Mock(side_effect=AssertionError("no real native process permitted"))

        def launcher(**options):
            options.setdefault("binary", sys.executable)
            options.setdefault("cli_version", "0.153.4")
            options.setdefault("popen_factory", self.popen)
            return CodexNativeSessionLauncher(**options)

        self.patches.enter_context(mock.patch(
            "workshop.workflow.native_run.CodexNativeSessionLauncher", side_effect=launcher,
        ))
        # Keep the actual launcher command, private checkpoint and resume
        # validation. Only the external stream and its usage source are fake.
        self.patches.enter_context(mock.patch.object(
            CodexNativeSessionLauncher, "_stream", autospec=True, side_effect=self.native_stream,
        ))
        self.patches.enter_context(mock.patch(
            "workshop.workflow.native_run._read_product_token_usage",
            side_effect=lambda *_: observation(self.consumption, child=True),
        ))

    def native_stream(self, launcher, **arguments):
        self.commands.append(tuple(arguments["command"]))
        self.turn_settings.append((launcher.timeout_seconds, launcher.protect_make_input))
        if arguments["bind_thread"] is not None:
            arguments["bind_thread"](ROOT)
        else:
            self.assertEqual(arguments["expected_thread_id"], ROOT)
        self.consumption += 100
        _FakeLauncher._write_waiting(arguments)
        if launcher.token_budget_observer is not None:
            launcher.token_budget_observer.reconcile_completed_turn((100, 50, 0, 10, 5))
            launcher.token_budget_observer()
        return False, ROOT, (100, 50, 0, 10, 5)

    def initialize(self, workflow="spark", **run_options):
        self.product_id = "resume-profile-fixture"
        receipt = start_native_run(
            Wish.create(self.product_id, "A small mixed-material mechanical toy",
                        context={"inventor_id": "ivy"}),
            effort=workflow, manager_id="codex", manager_model="gpt-6-astra",
            manager_reasoning_effort="ultra", max_tokens=100_000_000,
            **run_options,
        )
        self.assertEqual(receipt["status"], "waiting")
        self.paths = native_run_paths(self.product_id)
        run = _open_budgeted_agent_run(self.paths)
        checkpoint = run.snapshot()
        self.assertIn(BUDGETS_CAPABILITY_PATH, checkpoint.input_sha256s)
        self.assertIn(TOKEN_BUDGET_CAPABILITY_PATH, checkpoint.input_sha256s)
        self.assertEqual(checkpoint.manager_reasoning_effort, "ultra")
        self.assertIn('model_reasoning_effort="ultra"', self.commands[-1])
        return checkpoint

    def preserved_files(self):
        return {
            "wish": (self.paths.workspace / "WISH.json").read_bytes(),
            "session": (self.paths.host_state / "codex-session.json").read_bytes(),
            "manager": (self.paths.workspace / "MANAGER.json").read_bytes(),
            "budget": (self.paths.host_state / "native-budget.json").read_bytes(),
        }

    def test_explicit_medium_and_500m_resume_preserve_identity_tools_and_usage(self):
        before = self.initialize()
        files = self.preserved_files()
        prior_budget = _load_lifetime_budget(self.paths, before).to_dict()
        self.assertEqual(prior_budget["used_tokens"], 220)

        receipt = resume_native_run(
            self.product_id, manager_reasoning_effort="medium", max_tokens=500_000_000,
        )

        after = _open_budgeted_agent_run(self.paths).snapshot()
        for field in ("product_id", "wish_sha256", "run_root_sha256", "host_state_root_sha256",
                      "manager_id", "manager_model", "effort", "inventor_roster", "round_index", "stage"):
            self.assertEqual(getattr(after, field), getattr(before, field), field)
        self.assertEqual(after.manager_reasoning_effort, "medium")
        before_inputs = {p: sha for p, sha in before.input_sha256s.items() if p != "MANAGER.json"}
        after_inputs = {p: sha for p, sha in after.input_sha256s.items() if p != "MANAGER.json"}
        self.assertEqual(after_inputs, before_inputs)
        self.assertEqual((self.paths.workspace / "WISH.json").read_bytes(), files["wish"])
        self.assertEqual((self.paths.host_state / "codex-session.json").read_bytes(), files["session"])
        self.assertEqual(json.loads(files["session"])["thread_id"], ROOT)
        manager = json.loads((self.paths.workspace / "MANAGER.json").read_text())
        self.assertEqual(manager["reasoning_effort"], "medium")
        self.assertEqual(manager["model"], "gpt-6-astra")
        budget = _load_lifetime_budget(self.paths, after).to_dict()
        self.assertEqual(budget["limit_tokens"], 500_000_000)
        self.assertEqual(budget["used_tokens"], 440)
        self.assertGreater(budget["used_tokens"], prior_budget["used_tokens"])
        self.assertEqual(budget["observation"], observation(200, child=True))
        self.assertEqual(receipt["effort"], "medium")
        self.assertEqual(receipt["status"], "waiting")
        self.assertEqual(receipt["action"], "resumed")
        self.assertEqual(receipt["workflow"], "spark")
        self.assertEqual(receipt["budget"]["limit_tokens"], 500_000_000)
        self.assertEqual(receipt["budget"]["used_tokens"], 440)
        command = self.commands[-1]
        self.assertIn("resume", command)
        self.assertEqual(command[-2], ROOT)
        self.assertIn('model_reasoning_effort="medium"', command)
        self.assertNotIn('model_reasoning_effort="ultra"', command)
        self.assertEqual(command[command.index("--model") + 1], "gpt-6-astra")
        self.assertEqual(len(self.commands), 2)
        self.popen.assert_not_called()

    def test_mixed_token_run_preserves_explicit_turn_boundary_across_effort_changes(self):
        before = self.initialize(make_mode="mixed", turn_seconds=7_200)
        files = self.preserved_files()
        make_bytes = (self.paths.workspace / "MAKE.json").read_bytes()
        self.assertEqual(before.make_mode, "mixed")
        self.assertEqual(self.turn_settings[-1], (7_200, True))

        resume_native_run(
            self.product_id, manager_reasoning_effort="medium",
            max_tokens=500_000_000, turn_seconds=5_400,
        )
        after = _open_budgeted_agent_run(self.paths).snapshot()
        self.assertEqual(after.turn_seconds, 5_400)
        self.assertEqual(after.manager_reasoning_effort, "medium")
        self.assertEqual(self.turn_settings[-1], (5_400, True))
        resume_native_run(self.product_id)
        self.assertEqual(self.turn_settings[-1], (5_400, True))
        resume_native_run(self.product_id, turn_untimed=True)
        self.assertEqual(self.turn_settings[-1], (None, True))
        final = _open_budgeted_agent_run(self.paths).snapshot()
        self.assertTrue(final.turn_untimed)
        self.assertEqual(final.make_mode, "mixed")
        self.assertEqual((self.paths.workspace / "MAKE.json").read_bytes(), make_bytes)
        self.assertEqual((self.paths.workspace / "WISH.json").read_bytes(), files["wish"])
        self.assertEqual((self.paths.host_state / "codex-session.json").read_bytes(), files["session"])
        budget = _load_lifetime_budget(self.paths, final).to_dict()
        self.assertEqual(budget["limit_tokens"], 500_000_000)
        self.assertEqual(budget["used_tokens"], 880)
        self.popen.assert_not_called()

    def test_invalid_turn_boundary_cannot_mutate_a_mixed_token_run(self):
        before = self.initialize(make_mode="mixed", turn_seconds=7_200)
        files = self.preserved_files()
        for invalid in (True, 0, 21_601):
            with self.subTest(turn_seconds=invalid):
                with self.assertRaises(ContractError):
                    resume_native_run(self.product_id, turn_seconds=invalid)
                self.assertEqual(_open_budgeted_agent_run(self.paths).snapshot(), before)
                self.assertEqual(self.preserved_files(), files)
        self.assertEqual(len(self.commands), 1)
        self.popen.assert_not_called()

    def test_omitted_overrides_preserve_saved_profile_and_cap(self):
        before = self.initialize()
        files = self.preserved_files()
        receipt = resume_native_run(self.product_id)
        after = _open_budgeted_agent_run(self.paths).snapshot()
        self.assertEqual(after.manager_reasoning_effort, "ultra")
        self.assertEqual(self.turn_settings[-1], (None, False))
        self.assertEqual(after.input_sha256s, before.input_sha256s)
        for name, path in (("manager", self.paths.workspace / "MANAGER.json"),
                           ("session", self.paths.host_state / "codex-session.json"),
                           ("wish", self.paths.workspace / "WISH.json")):
            self.assertEqual(path.read_bytes(), files[name])
        self.assertEqual(receipt["effort"], "ultra")
        self.assertEqual(receipt["budget"]["limit_tokens"], 100_000_000)
        self.assertEqual(receipt["budget"]["used_tokens"], 440)
        self.assertIn('model_reasoning_effort="ultra"', self.commands[-1])

    def test_invalid_effort_refused_without_changing_budget_or_session(self):
        before = self.initialize()
        files = self.preserved_files()
        with self.assertRaisesRegex(ContractError, "reasoning effort must be one of"):
            resume_native_run(self.product_id, manager_reasoning_effort="invalid",
                              max_tokens=500_000_000)
        self.assertEqual(self.preserved_files(), files)
        self.assertEqual(_open_budgeted_agent_run(self.paths).snapshot(), before)
        self.assertEqual(len(self.commands), 1)

    def test_unsupported_workflow_refused_without_changing_budget_or_session(self):
        before = self.initialize(workflow="forge")
        files = self.preserved_files()
        with self.assertRaisesRegex(ContractError, "Codex Spark token-budget run"):
            resume_native_run(self.product_id, manager_reasoning_effort="medium",
                              max_tokens=500_000_000)
        self.assertEqual(self.preserved_files(), files)
        self.assertEqual(_open_budgeted_agent_run(self.paths).snapshot(), before)
        self.assertEqual(len(self.commands), 1)

    def test_exclusive_lock_prevents_effort_recovery_or_mutation(self):
        before = self.initialize()
        files = self.preserved_files()
        with _native_run_mutation_lock(self.paths):
            with mock.patch.object(AgentRun, "recover_manager_effort_change",
                                   side_effect=AssertionError("recovery must be under lock")):
                with self.assertRaisesRegex(StateConflict, "already mutating this Wish"):
                    resume_native_run(self.product_id, manager_reasoning_effort="medium",
                                      max_tokens=500_000_000)
        self.assertEqual(self.preserved_files(), files)
        self.assertEqual(_open_budgeted_agent_run(self.paths).snapshot(), before)
        self.assertEqual(len(self.commands), 1)

    def test_resume_recovers_interrupted_effort_write_before_opening_or_launching(self):
        before = self.initialize()
        files = self.preserved_files()
        write = agent_run_module._atomic_private_write

        def interrupt_after_manager(path, content, **options):
            write(path, content, **options)
            if Path(path) == self.paths.workspace / "MANAGER.json":
                raise OSError("fixture interruption after Manager replacement")

        with mock.patch.object(agent_run_module, "_atomic_private_write",
                               side_effect=interrupt_after_manager):
            with self.assertRaisesRegex(OSError, "fixture interruption"):
                resume_native_run(self.product_id, manager_reasoning_effort="medium",
                                  max_tokens=500_000_000)
        journal = self.paths.host_state / MANAGER_EFFORT_CHANGE_FILE
        self.assertTrue(journal.is_file())
        self.assertEqual((self.paths.host_state / "native-budget.json").read_bytes(), files["budget"])
        self.assertEqual((self.paths.host_state / "codex-session.json").read_bytes(), files["session"])
        with self.assertRaises(StateConflict):
            _open_budgeted_agent_run(self.paths)
        self.assertEqual(len(self.commands), 1)

        # The durable explicit request supplies medium; omitting the effort
        # here must recover that request before normal run input validation.
        receipt = resume_native_run(self.product_id, max_tokens=500_000_000)
        self.assertFalse(journal.exists())
        self.assertEqual(receipt["effort"], "medium")
        self.assertEqual(receipt["budget"]["limit_tokens"], 500_000_000)
        self.assertEqual(receipt["budget"]["used_tokens"], 440)
        self.assertIn('model_reasoning_effort="medium"', self.commands[-1])
        self.assertEqual((self.paths.host_state / "codex-session.json").read_bytes(), files["session"])
        after = _open_budgeted_agent_run(self.paths).snapshot()
        self.assertEqual(
            {p: sha for p, sha in after.input_sha256s.items() if p != "MANAGER.json"},
            {p: sha for p, sha in before.input_sha256s.items() if p != "MANAGER.json"},
        )
        ledger = self.paths.host_state / "host-corrections.jsonl"
        corrections = [json.loads(line) for line in ledger.read_text().splitlines()]
        effort_records = [row for row in corrections if row["correction"] == "manager-reasoning-effort"]
        self.assertEqual(len(effort_records), 1)
        self.assertEqual(effort_records[0]["previous_reasoning_effort"], "ultra")
        self.assertEqual(effort_records[0]["reasoning_effort"], "medium")
        unchanged_ledger = ledger.read_bytes()
        again = resume_native_run(self.product_id)
        self.assertEqual(again["budget"]["used_tokens"], 660)
        self.assertEqual(ledger.read_bytes(), unchanged_ledger)
        self.assertEqual(self.commands[-1][-2], ROOT)
        self.popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
