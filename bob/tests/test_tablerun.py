"""Tests for loops/tablerun.py — the code-not-agent LLM table loop.

All seat replies are canned (BOB_MOCK_AGENTS=1). Coverage per the build
contract: determinism under a fixed seed + fixed replies, index parsing
robustness ('I choose 3' and '3' both parse; out-of-range counts as a
confusion event and falls back to a random LEGAL move), and the pinned
transcript/report formats with idea_sha embedded.

The fixture engine is a deliberately tiny "steprace" (every legal move
advances the mover, ties go to the later seat) rather than the goodgame
anchor: a MOCK table replays ONE canned reply every turn, and goodgame's
lane-blocking makes any constant lane choice score zero forever — the test
would then measure the move cap, not the loop. Steprace terminates under
any fixed or random policy, which is exactly what a transport test needs.
"""

import hashlib
import json
import os
import shutil
import tempfile
import unittest

from loops import tablerun

_ENV_KEYS = ("BOB_HOME", "BOB_MOCK_AGENTS")

_IDEA = {
    "slug": "tablegame",
    "title": "Table Game",
    "players": "2",
    "concept": "steprace fixture wearing a table-test costume",
}

# Engine contract per loops/playtest.py docstring; IDEA_SHA filled per home.
_STEPRACE_TEMPLATE = '''"""Steprace fixture: every move advances, so the game
terminates under ANY seat policy — constant canned replies included."""

IDEA_SHA = "%s"
ASSUMPTIONS = ["fixture: ties at the line go to the later seat"]

_TARGET = 12


def new_game(n_players, seed):
    return {"n": n_players, "pos": [0] * n_players, "to": 0,
            "over": False, "winners": []}


def player_to_move(state):
    return state["to"]


def legal_moves(state):
    return [] if state["over"] else ["step1", "step2", "step3"]


def apply(state, move):
    gain = {"step1": 1, "step2": 2, "step3": 3}[move]
    pos = list(state["pos"])
    pos[state["to"]] += gain
    nxt = {"n": state["n"], "pos": pos,
           "to": (state["to"] + 1) %% state["n"],
           "over": False, "winners": []}
    if nxt["to"] == 0 and max(pos) >= _TARGET:
        top = max(pos)
        leaders = [i for i, p in enumerate(pos) if p == top]
        nxt["over"] = True
        nxt["winners"] = [leaders[-1]]
    return nxt


def is_over(state):
    return state["over"]


def winners(state):
    return list(state["winners"])


def scores(state):
    return [float(p) for p in state["pos"]]


def observation(state, seat):
    return "You are seat %%d. Positions: %%s. First to %%d wins." %% (
        seat, state["pos"], _TARGET)
'''


class _TableCase(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in _ENV_KEYS}
        self.home = tempfile.mkdtemp(prefix="bob-tablerun-test-")
        os.environ["BOB_HOME"] = self.home
        os.environ["BOB_MOCK_AGENTS"] = "1"
        self.fixtures = os.path.join(self.home, "tests", "fixtures")
        os.makedirs(self.fixtures)

        gdir = os.path.join(self.home, "games", "tablegame")
        os.makedirs(os.path.join(gdir, "playtest"))
        idea_bytes = json.dumps(_IDEA, indent=2).encode("utf-8")
        with open(os.path.join(gdir, "idea.json"), "wb") as handle:
            handle.write(idea_bytes)
        self.sha = hashlib.sha256(idea_bytes).hexdigest()
        with open(os.path.join(gdir, "playtest", "engine.py"), "w") as handle:
            handle.write(_STEPRACE_TEMPLATE % self.sha)
        self.gdir = gdir

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        for key, val in self._saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def _plant_reply(self, text):
        path = os.path.join(self.fixtures, "bob-table-player.txt")
        with open(path, "w") as handle:
            handle.write(text)


class ParseIndexTest(unittest.TestCase):
    """The parser is the seat's entire expressive power — pin it hard."""

    def test_bare_number(self):
        self.assertEqual(tablerun.parse_index("3", 5), (3, None))

    def test_i_choose_phrasing(self):
        self.assertEqual(tablerun.parse_index("I choose 3", 5), (3, None))

    def test_prose_around_the_number(self):
        self.assertEqual(
            tablerun.parse_index("Lane 2 denies the surge. My move: 2", 3),
            (2, None))

    def test_out_of_range_is_confusion(self):
        idx, why = tablerun.parse_index("I choose 99", 3)
        self.assertIsNone(idx)
        self.assertIn("out of range", why)

    def test_negative_is_confusion(self):
        idx, why = tablerun.parse_index("-1 looks safest", 3)
        self.assertIsNone(idx)
        self.assertIn("out of range", why)

    def test_no_number_is_confusion(self):
        idx, why = tablerun.parse_index("the middle lane, obviously", 3)
        self.assertIsNone(idx)
        self.assertEqual(why, "no index in reply")

    def test_empty_is_confusion(self):
        idx, why = tablerun.parse_index("", 3)
        self.assertIsNone(idx)
        self.assertEqual(why, "empty reply")


class DeterminismTest(_TableCase):
    def test_same_seed_same_replies_same_report(self):
        self._plant_reply("1\nPLAY_AGAIN: YES\nAGENCY: YES\nANSWER: fine.")
        first = tablerun.run_tables("tablegame", seed=7)
        # Wipe outputs so the second run proves recomputation, not reread.
        for k in range(4):
            os.remove(os.path.join(self.gdir, "playtest",
                                   "table_%d.json" % k))
        second = tablerun.run_tables("tablegame", seed=7)
        self.assertEqual(first, second)

    def test_clean_run_files_and_votes(self):
        self._plant_reply("0\nPLAY_AGAIN: YES\nAGENCY: NO\nANSWER: tight.")
        report = tablerun.run_tables("tablegame", seed=1)
        self.assertEqual(report["idea_sha"], self.sha)
        self.assertEqual(report["n_tables"], 4)
        self.assertEqual(report["n_players"], 2)  # players.max of "2"
        # Every seat parsed "0" cleanly and voted YES / agency NO.
        self.assertEqual(report["aggregate"]["would_play_again_fraction"], 1.0)
        self.assertEqual(report["aggregate"]["seats_total"], 8)  # 4 tables x 2
        self.assertEqual(report["aggregate"]["confusion_events"], 0)
        # Four distinct questions, one per table (docs/REWARD.md).
        questions = [row["question"] for row in report["tables"]]
        self.assertEqual(len(set(questions)), 4)
        for k, row in enumerate(report["tables"]):
            self.assertTrue(row["terminated"])
            self.assertEqual(row["agency"], [False, False])
            transcript_path = os.path.join(self.gdir, "playtest",
                                           "table_%d.json" % k)
            with open(transcript_path) as handle:
                transcript = json.load(handle)
            self.assertEqual(transcript["idea_sha"], self.sha)
            self.assertEqual(transcript["question"], row["question"])
            self.assertEqual(len(transcript["seats"]), 2)
            for spec in transcript["seats"]:
                self.assertIn("persona", spec)
                self.assertIn("model", spec)
            for move in transcript["moves"]:
                self.assertFalse(move["confused"])
                self.assertEqual(move["choice_index"], 0)
                self.assertEqual(move["legal_count"], 3)
        # Summary file on disk matches the returned dict.
        with open(os.path.join(self.gdir, "playtest",
                               "table_report.json")) as handle:
            self.assertEqual(json.load(handle), report)


class ConfusionFallbackTest(_TableCase):
    def test_out_of_range_reply_counts_confusion_and_plays_legal(self):
        # "99" is never a legal index in a 3-move list, and the verdict
        # reply carries no yes/no either — every turn AND every verdict
        # must land as a confusion event, and every played move must still
        # be a legal random fallback.
        self._plant_reply("I choose 99")
        report = tablerun.run_tables("tablegame", seed=3)
        self.assertGreater(report["aggregate"]["confusion_events"], 0)
        # Fail-closed votes: unclear is never a yes.
        self.assertEqual(report["aggregate"]["would_play_again_fraction"], 0.0)
        for k in range(4):
            with open(os.path.join(self.gdir, "playtest",
                                   "table_%d.json" % k)) as handle:
                transcript = json.load(handle)
            self.assertTrue(transcript["terminated"],
                            "random fallbacks must still finish the game")
            for move in transcript["moves"]:
                self.assertTrue(move["confused"])
                # The fallback move was drawn from the LEGAL list.
                self.assertGreaterEqual(move["choice_index"], 0)
                self.assertLess(move["choice_index"], move["legal_count"])
            self.assertEqual(transcript["verdicts"]["would_play_again"],
                             [None, None])
        # Deterministic even through the fallback rng.
        again = tablerun.run_tables("tablegame", seed=3)
        self.assertEqual(report, again)

    def test_stale_engine_is_refused_before_any_spend(self):
        # Rewrite idea.json after the engine was 'written': the loader must
        # refuse (stale-verdict receipt) rather than table the wrong game.
        with open(os.path.join(self.gdir, "idea.json"), "w") as handle:
            json.dump({"players": "2", "title": "edited later"}, handle)
        self._plant_reply("0")
        from loops import playtest
        with self.assertRaises(playtest.StaleEngineError):
            tablerun.run_tables("tablegame", seed=0)


if __name__ == "__main__":
    unittest.main()
