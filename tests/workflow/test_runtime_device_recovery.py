"""Host recovery stays inside the run lock and before launch or budget edits."""
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workshop.errors import ContractError
from workshop.workflow import native_run as host


class RuntimeDeviceRecoveryTest(unittest.TestCase):
    def checkpoint(self, **changes):
        values = dict(
            product_id="wish-one", wish_sha256="a" * 64, manager_id="codex",
            effort="spark", stage="make", status="active", make_mode=None,
            input_sha256s={host.TOKEN_BUDGET_CAPABILITY_PATH: "b" * 64,
                          host.BUDGETS_CAPABILITY_PATH: "c" * 64},
        )
        values.update(changes)
        return SimpleNamespace(**values)

    def test_recovery_refuses_unsupported_runs_without_constructing_launcher(self):
        paths = SimpleNamespace(workspace=Path("/run"), host_state=Path("/state"))
        for changes in ({"manager_id": "claude"}, {"effort": "quest"},
                        {"stage": "release"}, {"status": "complete"},
                        {"input_sha256s": {}}):
            with self.subTest(changes=changes), mock.patch.object(host, "_native_launcher") as launcher:
                with self.assertRaises(ContractError):
                    host._recover_runtime_device(paths, self.checkpoint(**changes), 8)
                launcher.assert_not_called()

    def test_recovery_passes_exact_frozen_identity_to_runtime(self):
        paths = SimpleNamespace(workspace=Path("/run"), host_state=Path("/state"))
        checkpoint = self.checkpoint()
        launcher = mock.Mock()
        with mock.patch.object(host, "_native_launcher", return_value=launcher), mock.patch.object(
            host, "_token_budget_codex_launcher", return_value=launcher
        ) as select, mock.patch.object(host, "materialized_agent_instructions_sha256", return_value="d" * 64):
            host._recover_runtime_device(paths, checkpoint, 8)
        select.assert_called_once_with(checkpoint, launcher)
        launcher.rebind_runtime_device.assert_called_once_with(
            product_id="wish-one", wish_sha256="a" * 64, constitution_sha256="d" * 64,
            run_root=paths.workspace, host_state_root=paths.host_state, previous_device=8,
        )

    def test_resume_recovery_holds_lock_and_precedes_budget_and_launch(self):
        for fail in (False, True):
            with self.subTest(fail=fail), ExitStack() as stack:
                events = []
                checkpoint = self.checkpoint()
                paths = SimpleNamespace(workspace=Path("/run"), host_state=Path("/state"))
                run = mock.Mock(); run.snapshot.return_value = checkpoint
                @contextmanager
                def lock(_):
                    events.append("lock")
                    try: yield
                    finally: events.append("unlock")
                def recover(*args):
                    self.assertEqual(events, ["lock"])
                    events.append("recover")
                    if fail: raise ContractError("mismatch")
                patches = {
                    "native_run_paths": dict(return_value=paths),
                    "_native_run_mutation_lock": dict(side_effect=lock),
                    "_persistent_token_budget_authority": dict(return_value=None),
                    "_open_budgeted_agent_run": dict(return_value=run),
                    "_recover_runtime_device": dict(side_effect=recover),
                    "_adopt_token_budget": dict(side_effect=lambda *a: events.append("budget")),
                    "_load_lifetime_budget": dict(return_value=None),
                    "_resume_native_run_locked": dict(side_effect=lambda *a, **k: events.append("launch") or {"ok": True}),
                }
                for name, options in patches.items(): stack.enter_context(mock.patch.object(host, name, **options))
                stack.enter_context(mock.patch.object(host.AgentRun, "recover_manager_effort_change"))
                if fail:
                    with self.assertRaisesRegex(ContractError, "mismatch"):
                        host.resume_native_run("wish-one", runtime_device_from=8, max_tokens=500000000)
                    self.assertEqual(events, ["lock", "recover", "unlock"])
                else:
                    self.assertEqual(host.resume_native_run("wish-one", runtime_device_from=8, max_tokens=500000000), {"ok": True})
                    self.assertEqual(events, ["lock", "recover", "budget", "launch", "unlock"])
                run.set_manager_reasoning_effort.assert_not_called()
                run.rebind_turn_boundary.assert_not_called()

    def test_invalid_devices_refused_before_any_state_access(self):
        for value in (-1, 2**64, True, "8"):
            with self.subTest(value=value), mock.patch.object(host, "native_run_paths") as paths:
                with self.assertRaises(ContractError): host.resume_native_run("wish-one", runtime_device_from=value)
                paths.assert_not_called()
