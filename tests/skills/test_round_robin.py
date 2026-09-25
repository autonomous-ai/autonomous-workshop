import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
TOOL = (
    REPOSITORY
    / ".claude"
    / "skills"
    / "brainstorm-reskin"
    / "scripts"
    / "round_robin.py"
)


def _load_tool():
    spec = importlib.util.spec_from_file_location("round_robin_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


round_robin = _load_tool()


class BuildScheduleTest(unittest.TestCase):
    def test_every_pair_appears_in_both_orderings(self):
        schedule = round_robin.build_schedule(["ada", "bly", "cai"])

        pairs = {(match.a, match.b) for match in schedule}
        self.assertEqual(len(schedule), 6)
        self.assertEqual(
            pairs,
            {
                ("ada", "bly"), ("bly", "ada"),
                ("ada", "cai"), ("cai", "ada"),
                ("bly", "cai"), ("cai", "bly"),
            },
        )

    def test_indexes_are_sequential_and_unique(self):
        schedule = round_robin.build_schedule(["ada", "bly", "cai", "dex"])
        self.assertEqual([match.index for match in schedule], list(range(len(schedule))))
        self.assertEqual(len(schedule), 4 * 3)

    def test_is_deterministic_across_calls(self):
        contestants = ["ada", "bly", "cai", "dex", "eli"]
        first = round_robin.build_schedule(contestants)
        second = round_robin.build_schedule(contestants)
        self.assertEqual(first, second)

    def test_refuses_fewer_than_two_contestants(self):
        with self.assertRaises(round_robin.RoundRobinError):
            round_robin.build_schedule(["ada"])

    def test_refuses_duplicate_contestants(self):
        with self.assertRaises(round_robin.RoundRobinError):
            round_robin.build_schedule(["ada", "bly", "ada"])

    def test_refuses_empty_contestant_name(self):
        with self.assertRaises(round_robin.RoundRobinError):
            round_robin.build_schedule(["ada", ""])


class ScoreMatchesTest(unittest.TestCase):
    def test_wins_and_split_score_correctly(self):
        schedule = round_robin.build_schedule(["ada", "bly"])
        # match 0: ada(a) vs bly(b); match 1: bly(a) vs ada(b)
        verdicts = {0: "a", 1: "split"}

        scores = round_robin.score_matches(schedule, verdicts)

        self.assertEqual(scores, {"ada": 1.5, "bly": 0.5})

    def test_refuses_missing_verdict(self):
        schedule = round_robin.build_schedule(["ada", "bly"])
        with self.assertRaises(round_robin.RoundRobinError):
            round_robin.score_matches(schedule, {0: "a"})

    def test_refuses_extra_verdict(self):
        schedule = round_robin.build_schedule(["ada", "bly"])
        with self.assertRaises(round_robin.RoundRobinError):
            round_robin.score_matches(schedule, {0: "a", 1: "b", 2: "a"})

    def test_refuses_unknown_verdict_value(self):
        schedule = round_robin.build_schedule(["ada", "bly"])
        with self.assertRaises(round_robin.RoundRobinError):
            round_robin.score_matches(schedule, {0: "a", 1: "draw"})


class RankStandingsTest(unittest.TestCase):
    def test_outright_winner_ranks_first(self):
        schedule = round_robin.build_schedule(["ada", "bly", "cai"])
        # ada beats everyone both ways; bly beats cai both ways.
        verdicts = {}
        for match in schedule:
            if "ada" in (match.a, match.b):
                verdicts[match.index] = "a" if match.a == "ada" else "b"
            else:
                verdicts[match.index] = "a" if match.a == "bly" else "b"

        result = round_robin.rank_standings(schedule, verdicts)

        ordered = [standing.contestant for standing in result.standings]
        self.assertEqual(ordered, ["ada", "bly", "cai"])
        self.assertEqual([standing.rank for standing in result.standings], [1, 2, 3])
        self.assertEqual(result.unresolved_ties, ())

    def test_tie_breaks_by_head_to_head(self):
        # Four-way round robin where ada and bly tie on points overall (4
        # each, ahead of cai and dex), but ada beat bly head-to-head both
        # times, so ada must rank above bly with no unresolved tie between
        # them.
        schedule = round_robin.build_schedule(["ada", "bly", "cai", "dex"])
        verdicts = {
            0: "a", 1: "b",    # ada beats bly both times
            2: "a", 3: "b",    # ada beats cai both times
            4: "b", 5: "a",    # dex beats ada both times
            6: "a", 7: "b",    # bly beats cai both times
            8: "a", 9: "b",    # bly beats dex both times
            10: "split", 11: "split",  # cai and dex split
        }

        scores = round_robin.score_matches(schedule, verdicts)
        self.assertEqual(scores, {"ada": 4.0, "bly": 4.0, "cai": 1.0, "dex": 3.0})

        result = round_robin.rank_standings(schedule, verdicts)

        standings_by_name = {s.contestant: s for s in result.standings}
        self.assertEqual(standings_by_name["ada"].rank, 1)
        self.assertEqual(standings_by_name["bly"].rank, 2)
        self.assertEqual(standings_by_name["dex"].rank, 3)
        self.assertEqual(standings_by_name["cai"].rank, 4)
        self.assertEqual(standings_by_name["ada"].tied_with, ())
        self.assertEqual(standings_by_name["bly"].tied_with, ())
        self.assertEqual(result.unresolved_ties, ())

    def test_reports_unresolved_tie_for_the_orchestrator(self):
        # Two contestants split both matches: equal on points and on
        # head-to-head. No further deterministic signal exists.
        schedule = round_robin.build_schedule(["ada", "bly"])
        verdicts = {0: "split", 1: "split"}

        result = round_robin.rank_standings(schedule, verdicts)

        self.assertEqual(result.unresolved_ties, (("ada", "bly"),))
        for standing in result.standings:
            self.assertEqual(standing.rank, 1)
            self.assertEqual(set(standing.tied_with) | {standing.contestant}, {"ada", "bly"})

    def test_is_deterministic_across_calls(self):
        schedule = round_robin.build_schedule(["ada", "bly", "cai", "dex"])
        verdicts = {match.index: ("a" if match.index % 2 == 0 else "split") for match in schedule}

        first = round_robin.rank_standings(schedule, verdicts)
        second = round_robin.rank_standings(schedule, verdicts)

        self.assertEqual(first, second)


class CLITest(unittest.TestCase):
    def test_schedule_then_score_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contestants_path = root / "contestants.json"
            contestants_path.write_text(json.dumps(["ada", "bly", "cai"]), encoding="utf-8")

            schedule_output = subprocess.run(
                [sys.executable, str(TOOL), "schedule", "--contestants", str(contestants_path)],
                capture_output=True, text=True, check=True,
            )
            schedule_json = json.loads(schedule_output.stdout)
            self.assertEqual(len(schedule_json["matches"]), 6)

            schedule_path = root / "schedule.json"
            schedule_path.write_text(json.dumps(schedule_json), encoding="utf-8")
            verdicts_path = root / "verdicts.json"
            verdicts = {str(match["index"]): "a" for match in schedule_json["matches"]}
            verdicts_path.write_text(json.dumps(verdicts), encoding="utf-8")

            score_output = subprocess.run(
                [
                    sys.executable, str(TOOL), "score",
                    "--schedule", str(schedule_path),
                    "--verdicts", str(verdicts_path),
                ],
                capture_output=True, text=True, check=True,
            )
            result_json = json.loads(score_output.stdout)
            self.assertIn("standings", result_json)
            self.assertIn("unresolved_ties", result_json)

    def test_score_refuses_malformed_verdicts_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            schedule_path = root / "schedule.json"
            schedule_path.write_text(
                json.dumps({"matches": [{"index": 0, "a": "ada", "b": "bly"}]}), encoding="utf-8"
            )
            verdicts_path = root / "verdicts.json"
            verdicts_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable, str(TOOL), "score",
                    "--schedule", str(schedule_path),
                    "--verdicts", str(verdicts_path),
                ],
                capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("round-robin:", completed.stderr)


if __name__ == "__main__":
    unittest.main()
