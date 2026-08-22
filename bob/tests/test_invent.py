"""Tests for loops/invent.py — the L1 pipeline driven end-to-end with
BOB_MOCK_AGENTS=1 canned replies (no network, no wallet, per CONTRACTS §5).

Coverage per the build contract:
- one INVENTION game sparked -> tabled: artifacts written, idea_sha embedded
  in every verdict, ledger rows appended — then on through the real table
  loop, build, review, and the dry-run auto-publish to live;
- the gate refusal: a failing sim PARKS with the reason;
- one EDITION game sparked -> briefed via the legal skip path;
- tick()'s failure routing (AgentError releases, state unchanged).
"""

import hashlib
import json
import os
import re
import shutil
import tempfile
import unittest

from harness import ledger, queue
from loops import invent

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENGINES = os.path.join(_ROOT, "tests", "fixtures", "engines")

_ENV_KEYS = ("BOB_HOME", "BOB_MOCK_AGENTS", "BOB_SIM_GAMES", "BOB_SIM_SEED",
             "BOB_PUBLISH_DRY_RUN")

# One reply per agent: the pipeline's mock session. rules_md is >200 chars
# and mentions every bill component by name (the deterministic lint checks
# exactly that), and players is "2" because the goodgame anchor is tuned
# fair at 2p only (wave-1 simmetrics note).
_RULES_MD = (
    "# Lane War — rules\n\n"
    "A two-player blocking race. Each turn the mover picks one of three "
    "lanes and advances by that lane's payout; the picked lane pays zero "
    "on the very next turn, so every move both scores and denies.\n\n"
    "## Components\nEach player takes one lane token and one score peg.\n\n"
    "## Turn loop\nOn your turn: pick a lane with your lane token, advance "
    "your score peg by the payout shown.\n\n"
    "## End\nFirst peg to 30 at the end of a full round wins; ties go to "
    "the later seat.\n"
)

_FIXTURES = {
    "bob-ideator": json.dumps([
        {"title": "Lane War", "concept": "pick-a-lane blocking race with "
         "payout surges", "mechanism": "lane denial", "players": "2",
         "weight": "light", "physical_hook": "weighted lane tokens"},
        {"title": "Dud One", "concept": "x", "players": "2"},
        {"title": "Dud Two", "concept": "x", "players": "2"},
        {"title": "Dud Three", "concept": "x", "players": "2"},
        {"title": "Dud Four", "concept": "x", "players": "2"},
    ]),
    "bob-triage-judge": json.dumps(
        {"pick": 0, "safety_pass": True,
         "reasons": "spark 0 is the only mechanism-first spark"}),
    "bob-novelty-judge": json.dumps(
        {"pass": True, "evidence_url": None,
         "nearest": ["Quoridor", "Downforce"], "margin": "far",
         "notes": "no confusable set found"}),
    "bob-rules-writer": json.dumps({
        "rules_md": _RULES_MD,
        "bill": [
            {"name": "lane token", "qty": 2, "size_mm": 30,
             "per_player": True},
            {"name": "score peg", "qty": 2, "size_mm": 15,
             "per_player": True},
        ],
        "game": {
            "action_types": ["pick_lane"],
            "rules": {"win": "first score peg to 30 after a full round"},
            "players": "2",
            "components": [
                {"name": "lane token", "qty": 2, "per_player": True},
                {"name": "score peg", "qty": 2, "per_player": True},
            ],
        },
    }),
    "bob-rules-lens": json.dumps({"verdict": "PASS", "issues": []}),
    # Move prompts read the FIRST integer ("0" = lane 0, always legal in
    # goodgame); verdict prompts read the labeled fields.
    "bob-table-player": "0\nPLAY_AGAIN: YES\nAGENCY: YES\n"
                        "ANSWER: The lane denial felt like a real decision.",
    "bob-fresh-reader": json.dumps(
        {"questions": 12, "misses": 1, "teach_minutes": 4,
         "findings": ["tiebreak sentence could be earlier"]}),
    "bob-brief-writer": json.dumps(
        {"brief_md": "# Parts brief\nPrint the weighted lane tokens only — "
                     "the denial mechanism IS the game."}),
    # Mock builder cannot use tools, so it hands the loop a parts map.
    "bob-builder": json.dumps(
        {"parts": {"lane_token.py": "# CadQuery source for the weighted "
                                    "lane token (fixture stand-in)"}}),
    "bob-build-lens": json.dumps(
        {"verdict": "PASS", "survives_as_cardboard": False, "issues": []}),
}


def _engine_source(name, sha):
    """A fixture engine with its IDEA_SHA rewritten to the real idea.json
    hash — exactly the artifact an engine-writer agent is contracted to
    produce (same trick as test_playtest)."""
    with open(os.path.join(_ENGINES, name + ".py")) as handle:
        src = handle.read()
    return re.sub(r'IDEA_SHA = "[^"]*"', 'IDEA_SHA = "%s"' % sha, src, count=1)


class _HomeCase(unittest.TestCase):
    """Temp BOB_HOME per test class; env saved/restored around each test."""

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in _ENV_KEYS}
        self.home = tempfile.mkdtemp(prefix="bob-invent-test-")
        os.environ["BOB_HOME"] = self.home
        os.environ["BOB_MOCK_AGENTS"] = "1"
        os.environ["BOB_SIM_GAMES"] = "600"  # goodgame's verified floor size
        os.environ["BOB_SIM_SEED"] = "0"
        os.environ["BOB_PUBLISH_DRY_RUN"] = "1"
        self.fixtures = os.path.join(self.home, "tests", "fixtures")
        os.makedirs(self.fixtures)

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)
        for key, val in self._saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def _plant(self, name, text):
        with open(os.path.join(self.fixtures, name + ".txt"), "w") as handle:
            handle.write(text)

    def _plant_all(self, names):
        for name in names:
            self._plant(name, _FIXTURES[name])

    def _tick_once(self, expect_state):
        step = queue.claim_next("test")
        self.assertIsNotNone(step, "queue handed out nothing")
        self.assertEqual(step.state, expect_state)
        invent.tick(step)
        return step

    def _state(self, slug):
        return queue.load()["games"][slug]["state"]

    def _read(self, slug, *rel):
        with open(os.path.join(self.home, "games", slug, *rel)) as handle:
            return json.load(handle)


class InventionPipelineTest(_HomeCase):
    """One invention game, sparked -> tabled (the contract point), then on
    through the real table loop, build, review, and the dry-run publish."""

    def test_sparked_to_tabled_then_published_dry(self):
        slug = "lanewar"
        queue.add_game(slug, "placeholder", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        self._plant_all(["bob-ideator", "bob-triage-judge"])

        self._tick_once("sparked")
        self.assertEqual(self._state(slug), "researched")
        idea = self._read(slug, "idea.json")
        self.assertEqual(idea["title"], "Lane War")
        self.assertEqual(idea["lane"], "invention")
        idea_path = os.path.join(self.home, "games", slug, "idea.json")
        with open(idea_path, "rb") as handle:
            sha = hashlib.sha256(handle.read()).hexdigest()
        safety = self._read(slug, "review", "safety.json")
        self.assertEqual(safety["idea_sha"], sha)
        self.assertTrue(safety["safety_pass"])
        # Queue picked up the chosen spark's title.
        self.assertEqual(queue.load()["games"][slug]["title"], "Lane War")

        self._plant_all(["bob-novelty-judge"])
        self._tick_once("researched")
        self.assertEqual(self._state(slug), "ruled")
        novelty = self._read(slug, "review", "novelty.json")
        self.assertEqual(novelty["idea_sha"], sha)
        self.assertTrue(novelty["pass"])

        self._plant_all(["bob-rules-writer"])
        self._tick_once("ruled")
        self.assertEqual(self._state(slug), "rules_gated")
        self.assertTrue(os.path.exists(
            os.path.join(self.home, "games", slug, "rules.md")))
        self.assertTrue(os.path.exists(
            os.path.join(self.home, "games", slug, "bill.json")))
        self.assertTrue(os.path.exists(
            os.path.join(self.home, "games", slug, "game.json")))

        self._plant_all(["bob-rules-lens"])
        self._tick_once("rules_gated")
        self.assertEqual(self._state(slug), "simulated")
        lint = self._read(slug, "review", "rules_lint.json")
        self.assertTrue(lint["lint_pass"], lint["problems"])
        self.assertEqual(lint["idea_sha"], sha)
        lens = self._read(slug, "review", "rules_lens.json")
        self.assertEqual(lens["verdict"], "PASS")
        self.assertEqual(lens["idea_sha"], sha)

        # Engine-writer replies with the goodgame anchor carrying the REAL
        # idea sha — the loader would refuse anything else.
        self._plant("bob-engine-writer", _engine_source("goodgame", sha))
        self._tick_once("simulated")
        self.assertEqual(self._state(slug), "tabled")  # THE contract point
        sim_report = self._read(slug, "playtest", "sim_report.json")
        self.assertEqual(sim_report["idea_sha"], sha)
        self.assertTrue(sim_report["verdicts"]["all_pass"])
        gate = self._read(slug, "playtest", "sim_gate.json")
        self.assertEqual(gate["idea_sha"], sha)
        self.assertTrue(gate["integrity_pass"])
        self.assertTrue(gate["degeneracy_pass"])
        self.assertTrue(gate["all_pass"])

        # Ledger: one row per handled stage so far, every row attributed.
        stages = [row["stage"] for row in ledger.rows(slug=slug)]
        for stage in ("sparked", "researched", "ruled", "rules_gated",
                      "simulated"):
            self.assertIn(stage, stages)
        for row in ledger.rows(slug=slug):
            self.assertEqual(row["kind"], "iteration")
            self.assertEqual(row["slug"], slug)

        # Onward through the REAL table loop (mock seats) to briefed.
        self._plant_all(["bob-table-player", "bob-fresh-reader"])
        self._tick_once("tabled")
        self.assertEqual(self._state(slug), "briefed")
        table = self._read(slug, "playtest", "table_report.json")
        self.assertEqual(table["idea_sha"], sha)
        self.assertEqual(table["n_tables"], 4)
        self.assertEqual(
            table["aggregate"]["would_play_again_fraction"], 1.0)
        reader = self._read(slug, "review", "fresh_reader.json")
        self.assertEqual(reader["idea_sha"], sha)
        self.assertEqual(reader["misses"], 1)

        # And on through build + review to the DRY-RUN auto-publish: the
        # expensive end of the cascade, reachable only past sims + tables.
        self._plant_all(["bob-brief-writer", "bob-builder", "bob-build-lens"])
        self._tick_once("briefed")
        self.assertEqual(self._state(slug), "built")
        self._tick_once("built")
        self.assertEqual(self._state(slug), "build_gated")
        self.assertTrue(os.path.exists(os.path.join(
            self.home, "games", slug, "parts", "lane_token.py")))
        self._tick_once("build_gated")
        self.assertEqual(self._state(slug), "reviewed")
        build_gate = self._read(slug, "review", "build_gate.json")
        self.assertTrue(build_gate["build_pass"])
        self.assertEqual(build_gate["idea_sha"], sha)

        self._tick_once("reviewed")
        self.assertEqual(self._state(slug), "published")
        score = self._read(slug, "review", "score.json")
        self.assertEqual(score["idea_sha"], sha)
        self.assertTrue(score["publish_eligible"], score)
        self.assertTrue(all(score["gates"].values()), score["gates"])
        self.assertGreaterEqual(score["score"], 70.0)
        stub = self._read(slug, "published.json")
        self.assertTrue(stub["dry_run"])  # BOB_PUBLISH_DRY_RUN=1 default
        self.assertEqual(stub["idea_sha"], sha)
        publish_rows = [row for row in ledger.rows(slug=slug)
                        if row["kind"] == "publish"]
        self.assertEqual(len(publish_rows), 1)
        self.assertGreaterEqual(publish_rows[0]["score"], 70.0)

        self._tick_once("published")
        self.assertEqual(self._state(slug), "live")


class FailingSimParksTest(_HomeCase):
    """The Armillary gate: a sim that fails its floors PARKS the game with
    the reason — nothing past tabled, no CAD money, not silent."""

    def test_failing_sim_parks_with_reason(self):
        slug = "brokenrace"
        os.environ["BOB_SIM_GAMES"] = "200"  # badgame fails hard; 200 is
        # the batch test_simmetrics verified the failure signature at
        queue.add_game(slug, "Broken Race", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        # Walk the legal chain up to simulated by hand — this test is about
        # the sim gate, not the earlier handlers.
        for state in ("researched", "ruled", "rules_gated", "simulated"):
            queue.advance(slug, state, "test setup")
        gdir = os.path.join(self.home, "games", slug)
        os.makedirs(gdir)
        idea = {"slug": slug, "title": "Broken Race", "players": "2",
                "lane": "invention", "concept": "first mover always wins"}
        with open(os.path.join(gdir, "idea.json"), "w") as handle:
            json.dump(idea, handle, indent=2, sort_keys=True)
        with open(os.path.join(gdir, "idea.json"), "rb") as handle:
            sha = hashlib.sha256(handle.read()).hexdigest()
        self._plant("bob-engine-writer", _engine_source("badgame", sha))

        self._tick_once("simulated")
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "parked")
        last_note = game["log"][-1]["note"]
        self.assertIn("sim gate failed", last_note)
        self.assertIn("seat_bias_ok", last_note)  # the named failed floor
        gate = self._read(slug, "playtest", "sim_gate.json")
        self.assertFalse(gate["all_pass"])
        self.assertFalse(gate["degeneracy_pass"])
        self.assertEqual(gate["idea_sha"], sha)
        # The refusal is on the ledger too, with the game attributed.
        notes = " | ".join(row["notes"] for row in ledger.rows(slug=slug))
        self.assertIn("sim FAIL", notes)


class EditionLaneTest(_HomeCase):
    """classic-reborn arm: faithfulness lint at rules_gated, then the legal
    skip path lands the game in briefed with no engine ever written."""

    def test_edition_sparked_to_briefed(self):
        slug = "chess-brutal"
        queue.add_game(slug, "placeholder", direction={
            "family": "classic-reborn", "players": "2", "weight": "mid"})
        self._plant("bob-ideator", json.dumps([
            {"title": "Chess, Brutalist", "concept": "cast-concrete-look "
             "chess set with interlocking bases", "players": "2",
             "weight": "mid", "physical_hook": "interlocking capture stack"},
            {"title": "D1", "concept": "x", "players": "2"},
            {"title": "D2", "concept": "x", "players": "2"},
            {"title": "D3", "concept": "x", "players": "2"},
            {"title": "D4", "concept": "x", "players": "2"},
        ]))
        self._plant_all(["bob-triage-judge", "bob-novelty-judge",
                         "bob-rules-writer", "bob-rules-lens"])

        self._tick_once("sparked")
        self.assertEqual(self._read(slug, "idea.json")["lane"], "edition")
        self._tick_once("researched")
        self._tick_once("ruled")
        self._tick_once("rules_gated")

        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "briefed")
        notes = " | ".join(entry["note"] for entry in game["log"])
        self.assertIn("edition lane", notes)
        self.assertIn("classic proved itself", notes)
        # No engine, no sim, no table artifacts were ever created.
        pdir = os.path.join(self.home, "games", slug, "playtest")
        self.assertFalse(os.path.exists(os.path.join(pdir, "engine.py")))
        self.assertFalse(os.path.exists(os.path.join(pdir, "sim_report.json")))


class TickRoutingTest(_HomeCase):
    """tick() never lets an agent exception escape; each class gets its
    contracted response."""

    def test_agent_crash_releases_for_retry(self):
        slug = "crashy"
        queue.add_game(slug, "Crashy", direction={"family": "wildcard"})
        # No bob-ideator fixture planted: the mock runner raises AgentError.
        step = queue.claim_next("test")
        invent.tick(step)  # must not raise
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "sparked")  # unchanged = retryable
        self.assertIsNone(game["lease"]["holder"])  # lease released

    def test_handlers_cover_every_schedulable_state(self):
        self.assertEqual(set(invent.STEP_HANDLERS), set(queue.PRIORITY))

    def test_extract_json_tolerates_prose_and_fences(self):
        self.assertEqual(invent._extract_json('{"a": 1}'), {"a": 1})
        self.assertEqual(
            invent._extract_json('Sure!\n```json\n{"a": 1}\n```\nDone.'),
            {"a": 1})
        self.assertEqual(
            invent._extract_json('The answer:\n[1, 2, 3] as requested'),
            [1, 2, 3])
        self.assertIsNone(invent._extract_json("no json here"))


if __name__ == "__main__":
    unittest.main()
