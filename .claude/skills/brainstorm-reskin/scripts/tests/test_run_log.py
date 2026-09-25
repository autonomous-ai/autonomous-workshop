"""RunLog: the append-only writer for brainstorm-reskin/<game>-<date>/run.json.

Each public method below matches one step `type` in ../../schemas/run.schema.json;
a step type added to one must be added to the other.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import run_log as RL  # noqa: E402


class RunLogHeaderTests(unittest.TestCase):
    def test_start_writes_header_with_empty_steps(self) -> None:
        with _tmp_dir() as tmp:
            path = tmp / "run.json"
            log = RL.RunLog.start(
                path,
                game="Catan",
                theme_hint="deep sea",
                seed=42,
                image_model="openrouter/some-model",
            )
            on_disk = json.loads(path.read_text())
            self.assertEqual(on_disk["game"], "Catan")
            self.assertEqual(on_disk["theme_hint"], "deep sea")
            self.assertEqual(on_disk["seed"], 42)
            self.assertEqual(on_disk["image_model"], "openrouter/some-model")
            self.assertEqual(on_disk["steps"], [])
            self.assertIsInstance(log, RL.RunLog)

    def test_start_refuses_existing_file(self) -> None:
        with _tmp_dir() as tmp:
            path = tmp / "run.json"
            RL.RunLog.start(path, game="Catan", theme_hint=None, seed=1, image_model="m")
            with self.assertRaises(FileExistsError):
                RL.RunLog.start(path, game="Catan", theme_hint=None, seed=1, image_model="m")


class RunLogStepTests(unittest.TestCase):
    def _log(self, tmp: Path) -> RL.RunLog:
        return RL.RunLog.start(
            tmp / "run.json", game="Catan", theme_hint=None, seed=7, image_model="m"
        )

    def test_personalities_drawn_appends_step(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.personalities_drawn(
                personalities=["a", "b", "c", "d", "e"], seed=7
            )
            steps = _read_steps(log.path)
            self.assertEqual(len(steps), 1)
            self.assertEqual(steps[0]["type"], "personalities_drawn")
            self.assertEqual(steps[0]["personalities"], ["a", "b", "c", "d", "e"])
            self.assertIn("at", steps[0])

    def test_personalities_drawn_requires_exactly_five(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            with self.assertRaises(ValueError):
                log.personalities_drawn(personalities=["a", "b"], seed=7)

    def test_contract_generated_appends_step(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.contract_generated(
                agent_id="agent-1",
                personality="the-tinkerer",
                contract_path="brainstorm-reskin/catan-2026-09-25/agent-1/CONTRACT.md",
                hero_path="brainstorm-reskin/catan-2026-09-25/agent-1/hero.png",
            )
            steps = _read_steps(log.path)
            self.assertEqual(steps[0]["type"], "contract_generated")
            self.assertEqual(steps[0]["agent_id"], "agent-1")

    def test_gate_rejected_appends_step_with_replacement(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.gate_rejected(
                agent_id="agent-2",
                personality="the-tinkerer",
                reasons=["missing Theme Hook"],
                replacement_personality="the-archivist",
            )
            steps = _read_steps(log.path)
            self.assertEqual(steps[0]["type"], "gate_rejected")
            self.assertEqual(steps[0]["replacement_personality"], "the-archivist")

    def test_gate_rejected_allows_null_replacement_when_exhausted(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.gate_rejected(
                agent_id="agent-2",
                personality="the-tinkerer",
                reasons=["missing Theme Hook"],
                replacement_personality=None,
            )
            steps = _read_steps(log.path)
            self.assertIsNone(steps[0]["replacement_personality"])

    def test_judgment_appends_step(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.judgment(
                pair=("agent-1", "agent-2"),
                ordering="ab",
                winner="agent-1",
                reason="Bolder silhouette, same craft.",
            )
            steps = _read_steps(log.path)
            self.assertEqual(steps[0]["type"], "judgment")
            self.assertEqual(steps[0]["pair"], ["agent-1", "agent-2"])
            self.assertEqual(steps[0]["winner"], "agent-1")

    def test_judgment_allows_null_winner_for_a_draw(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.judgment(
                pair=("agent-1", "agent-2"),
                ordering="ba",
                winner=None,
                reason="Split verdict.",
            )
            steps = _read_steps(log.path)
            self.assertIsNone(steps[0]["winner"])

    def test_standings_appends_step(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.standings([{"agent_id": "agent-1", "points": 3.5}])
            steps = _read_steps(log.path)
            self.assertEqual(steps[0]["type"], "standings")
            self.assertEqual(steps[0]["standings"][0]["agent_id"], "agent-1")

    def test_tie_break_appends_step(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.tie_break(
                tied=["agent-1", "agent-3"],
                winner="agent-3",
                reason="Head-to-head favored agent-3.",
            )
            steps = _read_steps(log.path)
            self.assertEqual(steps[0]["type"], "tie_break")
            self.assertEqual(steps[0]["winner"], "agent-3")

    def test_winner_appends_step(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.winner(
                agent_id="agent-3",
                contract_path="brainstorm-reskin/catan-2026-09-25/agent-3/CONTRACT.md",
            )
            steps = _read_steps(log.path)
            self.assertEqual(steps[0]["type"], "winner")

    def test_human_approval_appends_step(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.human_approval(approved_at="2026-09-25T12:00:00Z")
            steps = _read_steps(log.path)
            self.assertEqual(steps[0]["type"], "human_approval")
            self.assertEqual(steps[0]["approved_at"], "2026-09-25T12:00:00Z")

    def test_steps_append_in_order(self) -> None:
        with _tmp_dir() as tmp:
            log = self._log(tmp)
            log.personalities_drawn(personalities=["a", "b", "c", "d", "e"], seed=7)
            log.winner(agent_id="a", contract_path="p")
            steps = _read_steps(log.path)
            self.assertEqual([s["type"] for s in steps], ["personalities_drawn", "winner"])


class RunLogKeyRedactionTests(unittest.TestCase):
    def test_refuses_field_named_like_a_credential(self) -> None:
        with _tmp_dir() as tmp:
            log = RL.RunLog.start(
                tmp / "run.json", game="Catan", theme_hint=None, seed=1, image_model="m"
            )
            with self.assertRaises(ValueError):
                log.contract_generated(
                    agent_id="agent-1",
                    personality="p",
                    contract_path="c",
                    hero_path="h",
                    api_key="sk-or-v1-abcdef",  # type: ignore[call-arg]
                )

    def test_refuses_value_shaped_like_an_openrouter_key(self) -> None:
        with _tmp_dir() as tmp:
            log = RL.RunLog.start(
                tmp / "run.json", game="Catan", theme_hint=None, seed=1, image_model="m"
            )
            with self.assertRaises(ValueError):
                log.gate_rejected(
                    agent_id="agent-1",
                    personality="p",
                    reasons=["sk-or-v1-0123456789abcdef0123456789abcdef"],
                    replacement_personality=None,
                )


class RunLogLoadAndValidateTests(unittest.TestCase):
    def test_load_round_trips_a_written_run(self) -> None:
        with _tmp_dir() as tmp:
            path = tmp / "run.json"
            log = RL.RunLog.start(path, game="Catan", theme_hint=None, seed=1, image_model="m")
            log.winner(agent_id="a", contract_path="p")
            loaded = RL.load(path)
            self.assertEqual(loaded["game"], "Catan")
            self.assertEqual(len(loaded["steps"]), 1)

    def test_load_refuses_a_run_missing_a_required_top_level_field(self) -> None:
        with _tmp_dir() as tmp:
            path = tmp / "run.json"
            path.write_text(json.dumps({"game": "Catan"}))
            with self.assertRaises(ValueError):
                RL.load(path)

    def test_load_refuses_a_step_missing_a_type_specific_field(self) -> None:
        with _tmp_dir() as tmp:
            path = tmp / "run.json"
            path.write_text(
                json.dumps(
                    {
                        "game": "Catan",
                        "theme_hint": None,
                        "seed": 1,
                        "image_model": "m",
                        "started_at": "2026-09-25T00:00:00Z",
                        "steps": [{"type": "winner", "at": "2026-09-25T00:00:00Z"}],
                    }
                )
            )
            with self.assertRaises(ValueError):
                RL.load(path)


def _read_steps(path: Path) -> list[dict]:
    return json.loads(path.read_text())["steps"]


class _tmp_dir:
    def __enter__(self) -> Path:
        import tempfile

        self._tmpdir = tempfile.TemporaryDirectory()
        return Path(self._tmpdir.name)

    def __exit__(self, *exc: object) -> None:
        self._tmpdir.cleanup()


if __name__ == "__main__":
    unittest.main()
