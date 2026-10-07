"""The seeded personality draw: three of each lean, then replacements in order."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import draw_personalities as DP  # noqa: E402


class PoolTests(unittest.TestCase):
    def test_the_shipped_pool_is_thirty_split_evenly(self) -> None:
        pool = DP.load_pool()
        self.assertEqual(len(pool), 30)
        self.assertEqual(Counter(entry["leans"] for entry in pool), {"mechanism": 15, "form": 15})
        for entry in pool:
            with self.subTest(id=entry["id"]):
                self.assertTrue(entry["name"].strip())
                self.assertTrue(entry["method"].strip())

    def _refused(self, pool: list) -> str:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pool.json"
            path.write_text(json.dumps(pool))
            with self.assertRaises(DP.DrawError) as failure:
                DP.load_pool(path)
        return str(failure.exception)

    def test_a_pool_with_repeated_ids_is_refused(self) -> None:
        self.assertIn("unique", self._refused([{"id": "a", "leans": "form"}] * 16))

    def test_a_personality_without_a_known_lean_is_refused(self) -> None:
        self.assertIn("mechanism or form", self._refused([{"id": "a", "leans": "both"}]))

    def test_each_lean_must_cover_every_replacement(self) -> None:
        pool = [{"id": "m%d" % index, "leans": "mechanism"} for index in range(8)]
        pool += [{"id": "f%d" % index, "leans": "form"} for index in range(7)]
        self.assertIn("at least 8 form", self._refused(pool))


class DrawTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pool = DP.load_pool()

    def test_the_same_seed_draws_the_same_six(self) -> None:
        self.assertEqual(DP.draw(self.pool, 41), DP.draw(self.pool, 41))
        self.assertEqual(len(DP.draw(self.pool, 41)), 6)

    def test_a_draw_is_three_mechanism_then_three_form(self) -> None:
        for seed in range(20):
            with self.subTest(seed=seed):
                leans = [entry["leans"] for entry in DP.draw(self.pool, seed)]
                self.assertEqual(leans, ["mechanism"] * 3 + ["form"] * 3)

    def test_different_seeds_draw_different_contests(self) -> None:
        draws = {tuple(entry["id"] for entry in DP.draw(self.pool, seed)) for seed in range(20)}
        self.assertGreater(len(draws), 15)

    def test_replacements_never_repeat_a_drawn_personality(self) -> None:
        for seed in range(50):
            drawn = [entry["id"] for entry in DP.draw(self.pool, seed)]
            replacements = [
                DP.replacement(self.pool, seed, lean, number)
                for lean in DP.LEANS
                for number in range(1, 6)
            ]
            with self.subTest(seed=seed):
                self.assertEqual(len(set(drawn + [entry["id"] for entry in replacements])), 16)

    def test_a_replacement_keeps_the_rejected_lean(self) -> None:
        for lean in DP.LEANS:
            self.assertEqual(DP.replacement(self.pool, 3, lean, 2)["leans"], lean)

    def test_only_five_replacements_exist(self) -> None:
        for number in (0, 6):
            with self.assertRaises(DP.DrawError):
                DP.replacement(self.pool, 1, "form", number)


class CliTests(unittest.TestCase):
    SCRIPT = SCRIPTS_ROOT / "draw_personalities.py"

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(self.SCRIPT), *args], capture_output=True, text=True)

    def test_a_fresh_draw_records_its_seed_and_replays(self) -> None:
        first = json.loads(self._run().stdout)
        replay = json.loads(self._run("--seed", str(first["seed"])).stdout)
        self.assertEqual(first, replay)

    def test_a_replacement_comes_after_the_three_of_its_lean(self) -> None:
        result = json.loads(self._run("--seed", "7", "--lean", "form", "--replacement", "1").stdout)
        self.assertEqual(result["personality"], DP.order(DP.load_pool(), 7)["form"][3])

    def test_a_replacement_without_a_seed_or_lean_exits_2(self) -> None:
        for args in (("--lean", "form"), ("--seed", "7")):
            result = self._run(*args, "--replacement", "1")
            self.assertEqual(result.returncode, 2)
            self.assertIn("--seed and the --lean", result.stderr)


if __name__ == "__main__":
    unittest.main()
