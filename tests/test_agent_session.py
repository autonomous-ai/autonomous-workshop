"""Unit tests for the real ``ModelDoor`` implementation, ``AgentSessionDoor``.

Every launcher here is a hand-written stub, never a real subprocess and
never the network — the same "no real process, no network" posture
``tools/agent_door_fixture.py`` follows for the Concept-specific roles.
"""

import tempfile
import threading
import unittest
from pathlib import Path

from inventor_workshop.agent_session import (
    AgentRoleConfig,
    AgentSessionDoor,
    LaunchResult,
    LauncherOverBudget,
    LauncherTimedOut,
)
from inventor_workshop.errors import AgentSessionError, ContractError
from tools.agent_door_fixture import (
    FixtureAgentLauncher,
    ROLE_CONCEPT_IMAGES,
    ROLE_EXPLODED_VIEW_CHECK,
    ROLE_WISH_RESEARCH,
)


def _role_config(**overrides):
    defaults = dict(
        tools=("web_search",),
        allowed_paths=("./",),
        wall_clock_seconds=30,
    )
    defaults.update(overrides)
    return AgentRoleConfig(**defaults)


class _RecordingLauncher:
    """A stub launcher a test configures with a canned result or failure."""

    def __init__(self, *, result=None, exception=None, write_result=True):
        self.result = result
        self.exception = exception
        self.write_result = write_result
        self.calls = []

    def __call__(self, role, request, access, workspace, result_file):
        self.calls.append((role, request, access, workspace, result_file))
        if self.exception is not None:
            raise self.exception
        if self.write_result and self.result is not None:
            import json

            result_file.write_text(json.dumps(self.result), encoding="utf-8")
        return self.result_object

    result_object = LaunchResult(exit_status=0, stdout="", stderr="")


class _SteppingClock:
    """A fake clock advancing by a fixed step on every read."""

    def __init__(self, step=1.0):
        self._value = 0.0
        self._step = step

    def __call__(self):
        self._value += self._step
        return self._value


class AgentSessionDoorConstructionTest(unittest.TestCase):
    def test_construction_without_a_launch_command_is_rejected(self):
        with self.assertRaises(ContractError):
            AgentSessionDoor([], {ROLE_WISH_RESEARCH: _role_config()})

    def test_construction_without_role_configs_is_rejected(self):
        with self.assertRaises(ContractError):
            AgentSessionDoor(["agent-cli"], {})

    def test_construction_rejects_a_non_agent_role_config(self):
        with self.assertRaises(ContractError):
            AgentSessionDoor(["agent-cli"], {ROLE_WISH_RESEARCH: {"tools": []}})


class AgentSessionDoorRunTest(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.workdir.cleanup)

    def _door(self, launcher, *, role_configs=None, clock=None):
        configs = role_configs or {ROLE_WISH_RESEARCH: _role_config()}
        kwargs = {
            "launcher": launcher,
            "workspace_root": Path(self.workdir.name),
        }
        if clock is not None:
            kwargs["clock"] = clock
        return AgentSessionDoor(["agent-cli"], configs, **kwargs)

    def test_unconfigured_role_fails_closed_with_no_process_launched(self):
        launcher = _RecordingLauncher()
        door = self._door(launcher)
        with self.assertRaises(ContractError):
            door.run("some-other-role", {}, 1_000)
        self.assertEqual(launcher.calls, [])

    def test_budget_micros_must_be_a_positive_integer(self):
        launcher = _RecordingLauncher()
        door = self._door(launcher)
        for bad in (0, -1, 1.5, True):
            with self.assertRaises(ContractError):
                door.run(ROLE_WISH_RESEARCH, {}, bad)
        self.assertEqual(launcher.calls, [])

    def test_fresh_workspace_per_call(self):
        seen_on_entry = []

        def launcher(role, request, access, workspace, result_file):
            seen_on_entry.append(list(workspace.iterdir()))
            (workspace / "leftover.txt").write_text("mine", encoding="utf-8")
            result_file.write_text('{"object": "x"}', encoding="utf-8")
            return LaunchResult(exit_status=0, stdout="", stderr="")

        door = self._door(launcher)
        door.run(ROLE_WISH_RESEARCH, {"a": 1}, 1_000)
        door.run(ROLE_WISH_RESEARCH, {"a": 2}, 1_000)
        self.assertEqual(seen_on_entry, [[], []])

    def test_concurrent_calls_never_share_a_workspace(self):
        seen_workspaces = []
        lock = threading.Lock()

        def launcher(role, request, access, workspace, result_file):
            marker = workspace / "marker.txt"
            self.assertFalse(marker.exists())
            marker.write_text("mine", encoding="utf-8")
            with lock:
                seen_workspaces.append(workspace)
            result_file.write_text('{"object": "x"}', encoding="utf-8")
            return LaunchResult(exit_status=0, stdout="", stderr="")

        door = self._door(launcher)
        threads = [
            threading.Thread(target=door.run, args=(ROLE_WISH_RESEARCH, {}, 1_000))
            for _ in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(seen_workspaces), 8)
        self.assertEqual(len(set(seen_workspaces)), 8)

    def test_role_max_budget_micros_caps_the_effective_budget(self):
        launcher = _RecordingLauncher(result={"object": "x"})
        door = self._door(
            launcher,
            role_configs={
                ROLE_WISH_RESEARCH: _role_config(max_budget_micros=100)
            },
        )
        door.run(ROLE_WISH_RESEARCH, {}, 10_000)
        access = launcher.calls[0][2]
        self.assertEqual(access.budget_micros, 100)

    def test_wall_clock_bound_exceeded_terminates_and_names_the_role(self):
        clock = _SteppingClock()
        door = self._door(
            lambda role, request, access, workspace, result_file: (_ for _ in ()).throw(
                LauncherTimedOut()
            ),
            clock=clock,
        )
        with self.assertRaises(AgentSessionError) as ctx:
            door.run(ROLE_WISH_RESEARCH, {}, 1_000)
        self.assertEqual(ctx.exception.role, ROLE_WISH_RESEARCH)
        self.assertIn("wall-clock", str(ctx.exception))
        self.assertGreater(ctx.exception.elapsed_seconds, 0)

    def test_budget_exceeded_via_launcher_termination(self):
        door = self._door(
            lambda role, request, access, workspace, result_file: (_ for _ in ()).throw(
                LauncherOverBudget(5_000)
            )
        )
        with self.assertRaises(AgentSessionError) as ctx:
            door.run(ROLE_WISH_RESEARCH, {}, 1_000)
        self.assertEqual(ctx.exception.role, ROLE_WISH_RESEARCH)
        self.assertIn("budget", str(ctx.exception))
        self.assertEqual(ctx.exception.spent_micros, 5_000)

    def test_budget_exceeded_via_post_hoc_spend_report(self):
        def launcher(role, request, access, workspace, result_file):
            result_file.write_text('{"object": "x"}', encoding="utf-8")
            return LaunchResult(exit_status=0, stdout="", stderr="", spent_micros=2_000)

        door = self._door(launcher)
        with self.assertRaises(AgentSessionError) as ctx:
            door.run(ROLE_WISH_RESEARCH, {}, 1_000)
        self.assertIn("budget", str(ctx.exception))
        self.assertEqual(ctx.exception.spent_micros, 2_000)

    def test_non_zero_exit_fails_naming_the_role(self):
        def launcher(role, request, access, workspace, result_file):
            return LaunchResult(exit_status=2, stdout="", stderr="boom")

        door = self._door(launcher)
        with self.assertRaises(AgentSessionError) as ctx:
            door.run(ROLE_WISH_RESEARCH, {}, 1_000)
        self.assertEqual(ctx.exception.role, ROLE_WISH_RESEARCH)
        self.assertIn("status 2", str(ctx.exception))

    def test_missing_result_file_fails_naming_the_role(self):
        def launcher(role, request, access, workspace, result_file):
            return LaunchResult(exit_status=0, stdout="", stderr="")

        door = self._door(launcher)
        with self.assertRaises(AgentSessionError) as ctx:
            door.run(ROLE_WISH_RESEARCH, {}, 1_000)
        self.assertEqual(ctx.exception.role, ROLE_WISH_RESEARCH)
        self.assertIn("no structured result", str(ctx.exception))

    def test_malformed_result_file_fails_naming_the_role(self):
        def launcher(role, request, access, workspace, result_file):
            result_file.write_text("not json", encoding="utf-8")
            return LaunchResult(exit_status=0, stdout="", stderr="")

        door = self._door(launcher)
        with self.assertRaises(AgentSessionError) as ctx:
            door.run(ROLE_WISH_RESEARCH, {}, 1_000)
        self.assertEqual(ctx.exception.role, ROLE_WISH_RESEARCH)

    def test_result_missing_a_declared_field_fails_naming_the_role(self):
        def launcher(role, request, access, workspace, result_file):
            result_file.write_text('{"unrelated": true}', encoding="utf-8")
            return LaunchResult(exit_status=0, stdout="", stderr="")

        door = self._door(
            launcher,
            role_configs={
                ROLE_WISH_RESEARCH: _role_config(
                    required_result_fields=("object", "category")
                )
            },
        )
        with self.assertRaises(AgentSessionError) as ctx:
            door.run(ROLE_WISH_RESEARCH, {}, 1_000)
        self.assertIn("object", str(ctx.exception))
        self.assertIn("category", str(ctx.exception))

    def test_a_failed_call_still_reports_elapsed_time_and_cost(self):
        def launcher(role, request, access, workspace, result_file):
            return LaunchResult(exit_status=3, stdout="", stderr="", spent_micros=42)

        door = self._door(launcher)
        with self.assertRaises(AgentSessionError) as ctx:
            door.run(ROLE_WISH_RESEARCH, {}, 1_000)
        self.assertGreaterEqual(ctx.exception.elapsed_seconds, 0)
        self.assertEqual(ctx.exception.spent_micros, 42)

    def test_a_successful_call_reports_elapsed_time_and_cost(self):
        def launcher(role, request, access, workspace, result_file):
            result_file.write_text('{"object": "x"}', encoding="utf-8")
            return LaunchResult(exit_status=0, stdout="", stderr="", spent_micros=7)

        door = self._door(launcher)
        outcome = door.run(ROLE_WISH_RESEARCH, {}, 1_000)
        self.assertEqual(outcome["result"], {"object": "x"})
        self.assertGreaterEqual(outcome["elapsed_seconds"], 0)
        self.assertEqual(outcome["spent_micros"], 7)


class AgentDoorFixtureLauncherTest(unittest.TestCase):
    """The fixture serves every documented role, deterministically, offline."""

    def setUp(self):
        self.workdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.workdir.cleanup)
        self.launcher = FixtureAgentLauncher()
        self.door = AgentSessionDoor(
            ["not-a-real-binary"],
            {
                ROLE_WISH_RESEARCH: _role_config(),
                ROLE_CONCEPT_IMAGES: _role_config(),
                ROLE_EXPLODED_VIEW_CHECK: _role_config(),
            },
            launcher=self.launcher,
            workspace_root=Path(self.workdir.name),
        )

    def test_wish_research_role_is_deterministic(self):
        request = {
            "wish": {"objective": "A pocket sundial.", "constraints": {}},
            "taste": {"name": "Test", "description": "spare"},
            "lane": "holdable-science",
            "round": 1,
        }
        first = self.door.run(ROLE_WISH_RESEARCH, request, 1_000)
        second = self.door.run(ROLE_WISH_RESEARCH, request, 1_000)
        self.assertEqual(first["result"], second["result"])
        self.assertIn("object", first["result"])
        self.assertIn("components", first["result"])

    def test_concept_images_role_is_deterministic(self):
        request = {"role": "front", "kind": "overall", "prompt": "a lamp", "round": 1}
        first = self.door.run(ROLE_CONCEPT_IMAGES, request, 1_000)
        second = self.door.run(ROLE_CONCEPT_IMAGES, request, 1_000)
        self.assertEqual(first["result"], second["result"])
        self.assertIn("image_base64", first["result"])

    def test_exploded_view_check_role_reports_visible_components(self):
        import base64

        from tools.agent_door_fixture import _encode_png, component_colour

        rows = [component_colour("base"), component_colour("crown")]
        image_b64 = base64.b64encode(_encode_png(rows)).decode("ascii")
        request = {
            "image": {"media_type": "image/png", "data_base64": image_b64},
            "object": "a spinner",
            "components": [{"key": "base", "name": "Base"}, {"key": "crown", "name": "Crown"}],
        }
        outcome = self.door.run(ROLE_EXPLODED_VIEW_CHECK, request, 1_000)
        self.assertEqual(sorted(outcome["result"]["components"]), ["base", "crown"])

    def test_no_process_or_network_access(self):
        # The fixture writes the result file itself, in-process; nothing here
        # ever imports subprocess or urllib, and this test's own launcher
        # call is a plain Python function call.
        request = {"role": "front", "kind": "overall", "prompt": "a lamp", "round": 1}
        self.door.run(ROLE_CONCEPT_IMAGES, request, 1_000)
        self.assertEqual(len(self.launcher.calls), 1)


if __name__ == "__main__":
    unittest.main()
