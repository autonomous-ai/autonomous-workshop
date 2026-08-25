"""Offline proof that Pip's seams import a text2game run truthfully.

A tiny synthetic pipeline run stands in for /root/text2game — no credentials,
network, CAD service, or paid provider. The tests prove failure before
success: every missing capability waits with a typed Need, and the lane's
mass-simulation bar is never faked.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from one_decision_games.__main__ import build_workshop, create_wish

SLUG = "fixture-duel"


def write_fixture_run(root: Path, slug: str = SLUG) -> Path:
    (root / "text2game").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    run = root / "out" / slug
    (run / "parts").mkdir(parents=True)
    (run / "fe_parts").mkdir()
    (run / "gdd.md").write_text(
        "# Fixture Duel\n\n**Box face:** Flip one tile, drop one coin.\n",
        encoding="utf-8",
    )
    (run / "components.json").write_text('{"designs": 1}', encoding="utf-8")
    (run / "rulebook.md").write_text("# Rules\nOne decision per turn.\n", encoding="utf-8")
    (run / "print_kit.md").write_text("# Print kit\n", encoding="utf-8")
    (run / "parts" / "tile.py").write_text("def build():\n    pass\n", encoding="utf-8")
    (run / "fe_parts" / "tile.stl").write_bytes(b"solid tile\nendsolid tile\n")
    (run / "assembled.step").write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
    (run / "parts_index.json").write_text(
        '{"tile": {"qty": 1, "class": "functional", "tol": 0.3}}', encoding="utf-8"
    )
    (run / "part_colors.json").write_text('{"tile.stl": "#d7ff00"}', encoding="utf-8")
    (run / "phase1.json").write_text(
        json.dumps(
            {
                "round": 2,
                "critic_high": 0,
                "referee_clean": True,
                "referee_missing": False,
                "evaluate": {"depth": 8, "teach": 9},
                "exit": "clean",
                "kept_round": 2,
            }
        ),
        encoding="utf-8",
    )
    (run / "referee.md").write_text("## Game 1\n## Verdict\nCLEAN\n", encoding="utf-8")
    (run / "evaluate.json").write_text('{"round": 2, "reps": 3}', encoding="utf-8")
    (run / "gate.json").write_text(
        json.dumps({"parts": {"tile.stl": {"watertight": True, "bodies": 1}}}),
        encoding="utf-8",
    )
    (run / "fit.json").write_text("[]", encoding="utf-8")
    (run / "slice_report.json").write_text(
        json.dumps(
            {
                "parts": [
                    {
                        "part": "tile",
                        "qty": 1,
                        "grams_each": 12.5,
                        "seconds_each": 900,
                        "grams_total": 12.5,
                        "seconds_total": 900,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return run


def write_mass_simulation(run: Path) -> None:
    (run / "game_simulation.json").write_text(
        json.dumps(
            {
                "evidence_class": "ai-simulation",
                "executable": True,
                "completed_games": 1200,
                "player_styles": ["optimizing", "social", "exploratory", "adversarial"],
                "passed": True,
            }
        ),
        encoding="utf-8",
    )


class SeamTest(unittest.TestCase):
    def run_workshop(self, temporary: Path, pipeline_root: Path):
        environment = {
            "ONE_DECISION_GAMES_RUNTIME": str(temporary / "runtime"),
            "TEXT2GAME_ROOT": str(pipeline_root),
        }
        with mock.patch.dict(os.environ, environment):
            workshop = build_workshop()
            wish = create_wish(SLUG, "I wish for a tile-flipping coin duel")
            return workshop.run(wish, playtest_rounds=2)

    def test_missing_pipeline_waits_for_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            run = self.run_workshop(temporary, temporary / "nowhere")
            self.assertEqual(run.status, "waiting")
            self.assertEqual(run.job, "make")
            self.assertEqual(run.needs[0].capability, "text2game-pipeline")

    def test_missing_run_waits_with_the_exact_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            pipeline = temporary / "pipeline"
            pipeline.mkdir()
            (pipeline / "text2game").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            run = self.run_workshop(temporary, pipeline)
            self.assertEqual(run.status, "waiting")
            self.assertEqual(run.job, "make")
            self.assertEqual(run.needs[0].capability, "text2game-run")
            self.assertIn(SLUG, run.needs[0].instructions)

    def test_complete_run_without_mass_simulation_waits_for_that_bar(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            pipeline = temporary / "pipeline"
            pipeline.mkdir()
            write_fixture_run(pipeline)
            run = self.run_workshop(temporary, pipeline)
            self.assertEqual(run.status, "waiting")
            self.assertEqual(run.job, "playtest")
            self.assertEqual(
                [need.capability for need in run.needs], ["game-simulation"]
            )

    def test_mass_simulation_clears_playtest(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            pipeline = temporary / "pipeline"
            pipeline.mkdir()
            fixture = write_fixture_run(pipeline)
            write_mass_simulation(fixture)
            run = self.run_workshop(temporary, pipeline)
            self.assertNotIn(run.job, ("make", "playtest"))

    def test_failed_gate_feeds_back_and_waits_for_a_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            pipeline = temporary / "pipeline"
            pipeline.mkdir()
            fixture = write_fixture_run(pipeline)
            (fixture / "gate.json").write_text(
                json.dumps({"parts": {"tile.stl": {"watertight": False, "bodies": 2}}}),
                encoding="utf-8",
            )
            run = self.run_workshop(temporary, pipeline)
            self.assertEqual(run.status, "waiting")
            self.assertEqual(run.job, "make")
            self.assertEqual(run.needs[0].capability, "text2game-revision")

    def test_referee_residue_is_recorded_but_does_not_fail_the_round(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            pipeline = temporary / "pipeline"
            pipeline.mkdir()
            fixture = write_fixture_run(pipeline)
            phase1 = json.loads((fixture / "phase1.json").read_text(encoding="utf-8"))
            phase1["critic_high"] = 2
            phase1["referee_clean"] = False
            (fixture / "phase1.json").write_text(json.dumps(phase1), encoding="utf-8")
            run = self.run_workshop(temporary, pipeline)
            self.assertEqual(run.status, "waiting")
            self.assertEqual(run.job, "playtest")
            self.assertEqual(
                [need.capability for need in run.needs], ["game-simulation"]
            )

    def test_make_imports_the_curated_product_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            pipeline = temporary / "pipeline"
            pipeline.mkdir()
            write_fixture_run(pipeline)
            run = self.run_workshop(temporary, pipeline)
            self.assertTrue(run.artifact_sha256)
            runtime = temporary / "runtime"
            for expected in (
                "rules/rulebook.md",
                "rules/gdd.md",
                "cad/assembled.step",
                "source/parts/tile.py",
                "mesh/tile.stl",
                "assembly/parts_index.json",
            ):
                name = Path(expected).name
                matches = [
                    path
                    for path in runtime.rglob(name)
                    if path.parts[-len(Path(expected).parts) - 1] == "artifact"
                ]
                self.assertTrue(matches, "artifact is missing %s" % expected)


class VerdictTest(unittest.TestCase):
    def test_referee_without_a_kept_round_fails(self):
        from one_decision_games.text2game_bridge import referee_verdict

        passed, evidence = referee_verdict({"referee_missing": False, "kept_round": None})
        self.assertFalse(passed)
        self.assertEqual(evidence["evidence_class"], "ai-simulation")

    def test_unsliced_part_fails_the_print_test(self):
        from one_decision_games.text2game_bridge import slice_verdict

        passed, evidence = slice_verdict(
            {"parts": [{"part": "tile", "grams_each": None, "seconds_each": None}]}
        )
        self.assertFalse(passed)
        self.assertEqual(evidence["parts_sliced"], 0)

    def test_high_fit_violation_fails_the_mechanical_test(self):
        from one_decision_games.text2game_bridge import gate_verdict

        passed, evidence, fit_high = gate_verdict(
            {"parts": {"tile.stl": {"watertight": True, "bodies": 1}}},
            [{"severity": "high", "code": "too-loose", "pair": ["a", "b"]}],
        )
        self.assertFalse(passed)
        self.assertEqual(len(fit_high), 1)
        self.assertEqual(evidence["fit_high"], 1)


if __name__ == "__main__":
    unittest.main()
