import json
import shlex
import tempfile
import unittest
from pathlib import Path

from workshop.release.public_example import _reproduce_markdown


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class ReproduceCommandTest(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.staging = Path(self._temporary.name) / "staging"
        _write_json(self.staging / "wish" / "wish.json", {"objective": "a moon nook"})

    def _command(self, **overrides) -> list[str]:
        values = dict(
            summary="A tiny lunar observatory.",
            manager_id="codex",
            workflow="quest",
            manager_model="gpt-6-astra",
            manager_reasoning_effort="high",
            github_requested=False,
        )
        values.update(overrides)
        markdown = _reproduce_markdown(self.staging, **values)
        self.assertIn("## Reproduce", markdown)
        command = next(
            line for line in markdown.splitlines() if line.startswith("uv run workshop wish")
        )
        return shlex.split(command)

    def test_reproduce_pins_the_selected_inventor_from_the_match_assignment(self):
        _write_json(
            self.staging / "match" / "assignment.json",
            {"selected_inventor_id": "eve", "selected_agent_path": ".codex/agents/eve.toml"},
        )
        self.assertEqual(
            self._command(),
            [
                "uv", "run", "workshop", "wish",
                "--agent", "codex",
                "--model", "gpt-6-astra",
                "--effort", "high",
                "--workflow", "quest",
                "--inventor", "eve",
                "a moon nook",
            ],
        )
        self.assertEqual(
            self._command(github_requested=True)[-4:],
            ["--github", "--inventor", "eve", "a moon nook"],
        )

    def test_reproduce_omits_the_inventor_flag_when_no_assignment_is_recorded(self):
        command = self._command()
        self.assertNotIn("--inventor", command)
        self.assertEqual(command[-3:], ["--workflow", "quest", "a moon nook"])
        _write_json(self.staging / "match" / "assignment.json", {"selected_inventor_id": 7})
        self.assertNotIn("--inventor", self._command())


if __name__ == "__main__":
    unittest.main()
