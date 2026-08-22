"""Tests for loops/playtest.py — loader contract enforcement (including the
stale-idea_sha refusal), the engine-writer prompt, and the sim_report writer."""

import hashlib
import json
import os
import shutil
import tempfile
import unittest

from loops import playtest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_GOODGAME_SRC = os.path.join(_ROOT, "tests", "fixtures", "engines", "goodgame.py")

_IDEA = {
    "slug": "testrace",
    "title": "Test Race",
    "players": "2",
    "summary": "Pick-a-lane blocking race fixture for the playtest kit tests.",
}


def _make_home(idea=None, engine_sha=None):
    """Build a temp BOB_HOME with games/testrace/{idea.json, playtest/engine.py}.

    The engine is the goodgame fixture with its IDEA_SHA line rewritten to
    ``engine_sha`` (default: the real sha of the idea.json written here) —
    exactly the artifact an engine-writer agent is contracted to produce.
    """
    home = tempfile.mkdtemp(prefix="bob-playtest-test-")
    game_dir = os.path.join(home, "games", "testrace")
    playtest_dir = os.path.join(game_dir, "playtest")
    os.makedirs(playtest_dir)

    idea_bytes = json.dumps(idea or _IDEA, indent=2).encode("utf-8")
    with open(os.path.join(game_dir, "idea.json"), "wb") as handle:
        handle.write(idea_bytes)
    real_sha = hashlib.sha256(idea_bytes).hexdigest()

    with open(_GOODGAME_SRC) as handle:
        src = handle.read()
    src = src.replace('IDEA_SHA = "GOODGAME-FIXTURE"',
                      'IDEA_SHA = "%s"' % (engine_sha or real_sha))
    with open(os.path.join(playtest_dir, "engine.py"), "w") as handle:
        handle.write(src)
    return home, real_sha


class LoaderTest(unittest.TestCase):
    def setUp(self):
        self.home, self.sha = _make_home()
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.engine_path = os.path.join(
            self.home, "games", "testrace", "playtest", "engine.py")

    def test_loads_a_conforming_engine(self):
        engine = playtest.load_engine(self.engine_path,
                                      expected_idea_sha=self.sha)
        state = engine.new_game(2, 7)
        self.assertFalse(engine.is_over(state))
        self.assertEqual(engine.player_to_move(state), 0)
        self.assertTrue(engine.legal_moves(state))

    def test_refuses_mismatched_idea_sha(self):
        """The stale-verdict receipt: an engine written from an older
        idea.json must be refused, never scored (vibe-ideas burned twice)."""
        with self.assertRaises(playtest.StaleEngineError):
            playtest.load_engine(self.engine_path,
                                 expected_idea_sha="0" * 64)

    def test_refuses_engine_missing_api(self):
        with open(self.engine_path) as handle:
            src = handle.read()
        src = src.replace("def winners(", "def winners_gone(")
        broken = os.path.join(os.path.dirname(self.engine_path), "broken.py")
        with open(broken, "w") as handle:
            handle.write(src)
        with self.assertRaises(playtest.EngineContractError) as ctx:
            playtest.load_engine(broken, expected_idea_sha=self.sha)
        self.assertIn("winners", str(ctx.exception))

    def test_refuses_engine_without_assumptions(self):
        with open(self.engine_path) as handle:
            src = handle.read()
        src = src.replace("ASSUMPTIONS = [", "NOT_ASSUMPTIONS = [")
        broken = os.path.join(os.path.dirname(self.engine_path), "broken2.py")
        with open(broken, "w") as handle:
            handle.write(src)
        with self.assertRaises(playtest.EngineContractError):
            playtest.load_engine(broken, expected_idea_sha=self.sha)

    def test_missing_engine_says_what_to_do(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            playtest.load_engine(os.path.join(self.home, "nope.py"))
        self.assertIn("build_engine_prompt", str(ctx.exception))


class PromptTest(unittest.TestCase):
    def setUp(self):
        self.home, self.sha = _make_home()
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    def test_prompt_carries_contract_idea_and_sha(self):
        prompt = playtest.build_engine_prompt("testrace", home=self.home)
        # The full call surface an engine must expose
        for fn in playtest.ENGINE_API:
            self.assertIn(fn, prompt)
        # The exact sha to embed (stale-verdict binding)
        self.assertIn(self.sha, prompt)
        self.assertIn("IDEA_SHA", prompt)
        # The ASSUMPTIONS register-not-guess instruction
        self.assertIn("ASSUMPTIONS", prompt)
        # The idea.json content itself
        self.assertIn("Pick-a-lane blocking race fixture", prompt)

    def test_prompt_never_leaks_thresholds(self):
        """Generators must not see the scorer (METR 43x receipt): no gate
        constant names or values belong in the engine-writer prompt."""
        prompt = playtest.build_engine_prompt("testrace", home=self.home)
        for needle in ("MIN_SKILL_EDGE", "MAX_SEAT_EDGE", "MAX_RUNAWAY",
                       "MIN_MEDIAN_BRANCHING", "harmonic"):
            self.assertNotIn(needle, prompt)

    def test_missing_idea_raises(self):
        with self.assertRaises(FileNotFoundError):
            playtest.build_engine_prompt("no-such-game", home=self.home)


class RunSimTest(unittest.TestCase):
    def setUp(self):
        self.home, self.sha = _make_home()
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    def test_writes_report_with_idea_sha_and_verdicts(self):
        report = playtest.run_sim("testrace", home=self.home,
                                  n_games=150, seed=0)
        path = os.path.join(self.home, "games", "testrace", "playtest",
                            "sim_report.json")
        self.assertTrue(os.path.exists(path))
        with open(path) as handle:
            on_disk = json.load(handle)
        self.assertEqual(on_disk, report)
        self.assertEqual(report["idea_sha"], self.sha)
        self.assertEqual(sorted(report["by_players"]), ["2"])
        self.assertIn("all_pass", report["verdicts"])
        self.assertIn("2", report["verdicts"]["per_players"])
        self.assertIn("MAX_SEAT_EDGE", report["thresholds"])
        self.assertEqual(report["engine_assumptions"],
                         list(_goodgame_assumptions(self.home)))
        # No stray tmp file left behind by the atomic write
        leftovers = [f for f in os.listdir(os.path.dirname(path))
                     if f.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_refuses_stale_engine(self):
        home, _ = _make_home(engine_sha="a" * 64)
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        with self.assertRaises(playtest.StaleEngineError):
            playtest.run_sim("testrace", home=home, n_games=20, seed=0)

    def test_bob_home_env_is_read_at_call_time(self):
        old = os.environ.get("BOB_HOME")
        os.environ["BOB_HOME"] = self.home
        try:
            self.assertEqual(playtest.idea_sha("testrace"), self.sha)
        finally:
            if old is None:
                del os.environ["BOB_HOME"]
            else:
                os.environ["BOB_HOME"] = old


def _goodgame_assumptions(home):
    engine = playtest.load_engine(
        os.path.join(home, "games", "testrace", "playtest", "engine.py"))
    return engine.ASSUMPTIONS


class PlayerRangeTest(unittest.TestCase):
    def test_accepted_spellings(self):
        cases = [
            ({"players": "2-4"}, [2, 3, 4]),
            ({"players": "3"}, [3]),
            ({"players": 2}, [2]),
            ({"players": [2, 3]}, [2, 3]),
            ({"players": {"min": 2, "max": 4}}, [2, 3, 4]),
        ]
        for idea, expected in cases:
            self.assertEqual(playtest._player_range(idea), expected, idea)

    def test_rejects_missing_or_garbage(self):
        with self.assertRaises(ValueError):
            playtest._player_range({})
        with self.assertRaises(ValueError):
            playtest._player_range({"players": "many"})


class TableStubTest(unittest.TestCase):
    """llm_table delegates to loops.tablerun (wired at integration)."""

    def test_llm_table_delegates_to_tablerun(self):
        from loops import tablerun
        self.assertIs(playtest.llm_table.__module__, playtest.__name__)
        self.assertTrue(callable(tablerun.run_tables))

    def test_llm_table_missing_game_names_the_prerequisite(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            playtest.llm_table("no-such-game-xyz", seats=[{"model": "m"}])
        self.assertIn("idea.json", str(ctx.exception))
