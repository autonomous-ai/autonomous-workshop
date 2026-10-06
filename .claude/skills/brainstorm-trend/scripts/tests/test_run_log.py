"""RunLog: the append-only writer for brainstorm-trend/<trend>-<date>/run.json.

Each public method below matches one step `type` in ../../schemas/run.schema.json;
a step type added to one must be added to the other.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import run_log as RL  # noqa: E402

TODAY = date(2026, 10, 6)
GIVEN = {"trend": {"name": "Ice shelves"}, "chosen_by": "given", "shortlist": None}


def _candidate(name: str = "Comet Lumen", **changes) -> dict:
    candidate = {
        "name": name,
        "summary": "A naked-eye comet.",
        "sources": [
            {"url": "https://www.nasa.gov/comet", "title": "Comet", "published": "2026-09-30"},
            {"url": "https://apnews.com/comet", "title": "Comet", "published": "2026-09-20"},
        ],
    }
    candidate.update(changes)
    return candidate


class RunLogHeaderTests(unittest.TestCase):
    def test_start_writes_header_with_empty_steps(self) -> None:
        with _tmp_dir() as tmp:
            path = tmp / "run.json"
            log = RL.RunLog.start(
                path,
                trend={"name": "Comet Lumen"},
                chosen_by="human",
                shortlist=[_candidate(), _candidate("Ice shelves")],
                seed=42,
                image_model="openrouter/some-model",
                today=TODAY,
            )
            on_disk = json.loads(path.read_text())
            self.assertEqual(on_disk["trend"], {"name": "Comet Lumen"})
            self.assertEqual(on_disk["chosen_by"], "human")
            self.assertEqual(len(on_disk["shortlist"]), 2)
            self.assertEqual(on_disk["seed"], 42)
            self.assertEqual(on_disk["image_model"], "openrouter/some-model")
            self.assertEqual(on_disk["steps"], [])
            self.assertIsInstance(log, RL.RunLog)

    def test_start_refuses_existing_file(self) -> None:
        with _tmp_dir() as tmp:
            path = tmp / "run.json"
            RL.RunLog.start(path, **GIVEN, seed=1, image_model="m")
            with self.assertRaises(FileExistsError):
                RL.RunLog.start(path, **GIVEN, seed=1, image_model="m")


class RunLogStepTests(unittest.TestCase):
    def _log(self, tmp: Path) -> RL.RunLog:
        return RL.RunLog.start(
            tmp / "run.json", **GIVEN, seed=7, image_model="m"
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
                contract_path="brainstorm-trend/comet-lumen-2026-10-06/agent-1/CONTRACT.md",
                hero_path="brainstorm-trend/comet-lumen-2026-10-06/agent-1/hero.png",
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
                reasons=["no Trend Hook section found in the prose"],
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
                reasons=["no Trend Hook section found in the prose"],
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
                contract_path="brainstorm-trend/comet-lumen-2026-10-06/agent-3/CONTRACT.md",
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
                tmp / "run.json", **GIVEN, seed=1, image_model="m"
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
                tmp / "run.json", **GIVEN, seed=1, image_model="m"
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
            log = RL.RunLog.start(path, **GIVEN, seed=1, image_model="m")
            log.winner(agent_id="a", contract_path="p")
            loaded = RL.load(path)
            self.assertEqual(loaded["trend"]["name"], "Ice shelves")
            self.assertEqual(len(loaded["steps"]), 1)

    def test_load_refuses_a_run_missing_a_required_top_level_field(self) -> None:
        with _tmp_dir() as tmp:
            path = tmp / "run.json"
            path.write_text(json.dumps({"trend": {"name": "Ice shelves"}}))
            with self.assertRaises(ValueError):
                RL.load(path)

    def test_load_refuses_a_step_missing_a_type_specific_field(self) -> None:
        with _tmp_dir() as tmp:
            path = tmp / "run.json"
            path.write_text(
                json.dumps(
                    {
                        **GIVEN,
                        "seed": 1,
                        "image_model": "m",
                        "started_at": "2026-09-25T00:00:00Z",
                        "steps": [{"type": "winner", "at": "2026-09-25T00:00:00Z"}],
                    }
                )
            )
            with self.assertRaises(ValueError):
                RL.load(path)


class RunLogTrendHeaderTests(unittest.TestCase):
    def _start(self, tmp: Path, **changes):
        header = {**GIVEN, "seed": 1, "image_model": "m", "today": TODAY}
        header.update(changes)
        return RL.RunLog.start(tmp / "run.json", **header)

    def test_a_given_trend_has_no_shortlist(self) -> None:
        with _tmp_dir() as tmp:
            with self.assertRaisesRegex(ValueError, "no shortlist"):
                self._start(tmp, shortlist=[_candidate()])

    def test_a_picked_trend_needs_a_shortlist(self) -> None:
        with _tmp_dir() as tmp:
            with self.assertRaisesRegex(ValueError, "needs the shortlist"):
                self._start(tmp, chosen_by="human", shortlist=[])

    def test_a_picked_trend_must_be_on_the_shortlist(self) -> None:
        with _tmp_dir() as tmp:
            with self.assertRaisesRegex(ValueError, "not on the shortlist"):
                self._start(tmp, chosen_by="human", shortlist=[_candidate()])

    def test_every_shortlisted_trend_needs_evidence(self) -> None:
        with _tmp_dir() as tmp:
            stale = _candidate("Ice shelves", sources=_candidate()["sources"][:1])
            with self.assertRaisesRegex(ValueError, "'Ice shelves' lacks evidence"):
                self._start(tmp, chosen_by="human", shortlist=[stale])
            self.assertFalse((tmp / "run.json").exists())

    def test_chosen_by_is_given_or_human(self) -> None:
        with _tmp_dir() as tmp:
            with self.assertRaisesRegex(ValueError, "chosen_by"):
                self._start(tmp, chosen_by="orchestrator")

    def test_a_trend_needs_a_name(self) -> None:
        with _tmp_dir() as tmp:
            with self.assertRaisesRegex(ValueError, "needs a name"):
                self._start(tmp, trend={"name": "  "})


class TrendEvidenceTests(unittest.TestCase):
    def test_two_recent_sources_on_different_sites_pass(self) -> None:
        self.assertEqual(RL.trend_evidence_reasons(_candidate(), today=TODAY), [])

    def test_two_sources_on_one_site_count_once(self) -> None:
        sources = [
            {"url": "https://www.apnews.com/a", "published": "2026-10-01"},
            {"url": "https://apnews.com/b", "published": "2026-10-02"},
        ]
        reasons = RL.trend_evidence_reasons(_candidate(sources=sources), today=TODAY)
        self.assertEqual(reasons, ["1 site(s) dated within 30 days of 2026-10-06; needs 2"])

    def test_a_source_older_than_thirty_days_does_not_count(self) -> None:
        sources = _candidate()["sources"]
        sources[1]["published"] = "2026-09-05"
        self.assertEqual(len(RL.trend_evidence_reasons(_candidate(sources=sources), today=TODAY)), 1)
        sources[1]["published"] = "2026-09-06"
        self.assertEqual(RL.trend_evidence_reasons(_candidate(sources=sources), today=TODAY), [])

    def test_a_future_or_undated_source_does_not_count(self) -> None:
        for published in ("2026-10-07", "last week", None):
            sources = _candidate()["sources"]
            sources[1]["published"] = published
            with self.subTest(published=published):
                self.assertTrue(RL.trend_evidence_reasons(_candidate(sources=sources), today=TODAY))

    def test_a_candidate_without_sources_or_name_is_refused(self) -> None:
        self.assertEqual(
            RL.trend_evidence_reasons({"name": ""}, today=TODAY), ["no name", "no sources list"]
        )


class RunLogCliTests(unittest.TestCase):
    SCRIPT = SCRIPTS_ROOT / "run_log.py"

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.SCRIPT), *args], capture_output=True, text=True
        )

    def test_check_trends_reports_each_candidate(self) -> None:
        with _tmp_dir() as tmp:
            shortlist = tmp / "shortlist.json"
            shortlist.write_text(json.dumps([_candidate(), _candidate("Old", sources=[])]))
            result = self._run("check-trends", str(shortlist), "--today", "2026-10-06")
            self.assertEqual(result.returncode, 1)
            reasons = {row["name"]: row["reasons"] for row in json.loads(result.stdout)}
            self.assertEqual(reasons["Comet Lumen"], [])
            self.assertTrue(reasons["Old"])

    def test_start_and_append_write_the_run(self) -> None:
        with _tmp_dir() as tmp:
            run, header, fields = tmp / "r" / "run.json", tmp / "h.json", tmp / "f.json"
            header.write_text(json.dumps({**GIVEN, "seed": 3, "image_model": "m"}))
            self.assertEqual(self._run("start", str(run), str(header)).returncode, 0)
            fields.write_text(json.dumps({"standings": [{"agent_id": "a", "points": 2}]}))
            self.assertEqual(self._run("append", str(run), "standings", str(fields)).returncode, 0)
            fields.write_text(json.dumps({"pair": ["a", "b"], "ordering": "ba", "winner": None, "reason": "Split."}))
            self.assertEqual(self._run("append", str(run), "judgment", str(fields)).returncode, 0)
            self.assertEqual([step["type"] for step in RL.load(run)["steps"]], ["standings", "judgment"])

    def test_a_refused_step_exits_2_without_writing(self) -> None:
        with _tmp_dir() as tmp:
            run, header, fields = tmp / "run.json", tmp / "h.json", tmp / "f.json"
            header.write_text(json.dumps({**GIVEN, "seed": 3, "image_model": "m"}))
            self._run("start", str(run), str(header))
            fields.write_text(json.dumps({"personalities": ["a"], "seed": 3}))
            result = self._run("append", str(run), "personalities_drawn", str(fields))
            self.assertEqual(result.returncode, 2)
            self.assertIn("exactly 5", result.stderr)
            self.assertEqual(RL.load(run)["steps"], [])


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
