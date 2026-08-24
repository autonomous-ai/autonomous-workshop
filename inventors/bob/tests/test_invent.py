"""Tests for loops/invent.py — the L1 pipeline driven end-to-end with
BOB_MOCK_AGENTS=1 canned replies (no network, no wallet, per CONTRACTS §5).

Coverage per the build contract:
- one INVENTION game sparked -> tabled: artifacts written, idea_sha embedded
  in every verdict, ledger rows appended — then on through the real table
  loop, build, review, and the Workshop dry-run Pack/Send rehearsal;
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
import threading
import types
import unittest
from unittest import mock

from harness import ledger, queue
from loops import invent

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENGINES = os.path.join(_ROOT, "tests", "fixtures", "engines")

_ENV_KEYS = (
    "BOB_HOME", "BOB_MOCK_AGENTS", "BOB_SIM_GAMES", "BOB_SIM_SEED",
    "BOB_SEND_DRY_RUN", "BOB_PUBLISH_DRY_RUN", "BOB_SEND_VIA",
    "BOB_PUBLISH_VIA", "BOB_SHOP_PUBLIC", "BOB_AUTO_FLIP",
)

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

_TETRA_STL = """solid bob
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 0 1 0
      vertex 1 0 0
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 1 0 0
      vertex 0 0 1
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 0 0 1
      vertex 0 1 0
    endloop
  endfacet
  facet normal 0 0 0
    outer loop
      vertex 1 0 0
      vertex 0 1 0
      vertex 0 0 1
    endloop
  endfacet
endsolid bob
"""

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
                                    "lane token (fixture stand-in)",
                   "lane_token.stl": _TETRA_STL}}),
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
        os.environ["BOB_SEND_DRY_RUN"] = "1"
        shutil.copy(
            os.path.join(_ROOT, "TASTE.md"), os.path.join(self.home, "TASTE.md")
        )
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
        with open(os.path.join(self.home, "toys", slug, *rel)) as handle:
            return json.load(handle)


class TasteAuthorityTest(_HomeCase):
    def test_missing_root_taste_fails_closed(self):
        os.remove(os.path.join(self.home, "TASTE.md"))
        with self.assertRaises(invent.TasteAuthorityError) as ctx:
            invent._taste()
        self.assertIn("root TASTE.md", str(ctx.exception))


class InventionPipelineTest(_HomeCase):
    """One invention game, sparked -> tabled (the contract point), then on
    through the real table loop, build, review, and the dry-run send."""

    def test_sparked_to_tabled_then_published_dry(self):
        slug = "lanewar"
        queue.add_game(slug, "placeholder", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        self._plant_all(["bob-ideator", "bob-triage-judge"])

        legacy_taste = "LEGACY EVIDENCE MUST NOT BECOME RUNTIME AUTHORITY"
        os.makedirs(os.path.join(self.home, "knowledge"), exist_ok=True)
        with open(os.path.join(self.home, "knowledge", "TASTE.md"), "w") as handle:
            handle.write(legacy_taste)
        prompts = {}
        original_run_agent = invent.agents.run_agent

        def capture_prompt(name, prompt, **kwargs):
            prompts[name] = prompt
            return original_run_agent(name, prompt, **kwargs)

        with mock.patch.object(
            invent.agents, "run_agent", side_effect=capture_prompt
        ):
            self._tick_once("sparked")
        self.assertEqual(self._state(slug), "researched")
        idea = self._read(slug, "idea.json")
        self.assertEqual(idea["title"], "Lane War")
        self.assertEqual(idea["lane"], "invention")
        with open(os.path.join(self.home, "TASTE.md"), "rb") as handle:
            taste_bytes = handle.read()
        taste_text = taste_bytes.decode("utf-8")
        taste_sha = hashlib.sha256(taste_bytes).hexdigest()
        self.assertEqual(idea["taste"]["path"], "TASTE.md")
        self.assertEqual(idea["taste"]["content"], taste_text)
        self.assertEqual(idea["taste"]["sha256"], taste_sha)
        self.assertEqual(idea["taste"]["bytes"], len(taste_bytes))
        for agent_name in ("bob-ideator", "bob-triage-judge"):
            self.assertIn(taste_text, prompts[agent_name])
            self.assertIn(taste_sha, prompts[agent_name])
            self.assertIn("root TASTE.md", prompts[agent_name])
            self.assertNotIn(legacy_taste, prompts[agent_name])
        idea_path = os.path.join(self.home, "toys", slug, "idea.json")
        with open(idea_path, "rb") as handle:
            sha = hashlib.sha256(handle.read()).hexdigest()
        safety = self._read(slug, "review", "safety.json")
        self.assertEqual(safety["idea_sha"], sha)
        self.assertEqual(safety["taste_sha256"], taste_sha)
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
            os.path.join(self.home, "toys", slug, "rules.md")))
        self.assertTrue(os.path.exists(
            os.path.join(self.home, "toys", slug, "bill.json")))
        self.assertTrue(os.path.exists(
            os.path.join(self.home, "toys", slug, "game.json")))

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
            self.home, "toys", slug, "parts", "lane_token.py")))
        self._tick_once("build_gated")
        self.assertEqual(self._state(slug), "reviewed")
        build_gate = self._read(slug, "review", "build_gate.json")
        self.assertTrue(build_gate["build_pass"])
        self.assertTrue(build_gate["deterministic_mesh_pass"])
        self.assertTrue(build_gate["lens_pass"])
        self.assertTrue(build_gate["mesh_checked"])
        self.assertEqual(len(build_gate["mesh_receipts"]), 1)
        self.assertEqual(
            build_gate["mesh_receipts"][0]["receipt"]["status"], "passed")
        self.assertEqual(
            len(build_gate["mesh_receipts"][0]["receipt_sha256"]), 64)
        self.assertEqual(build_gate["idea_sha"], sha)

        self._tick_once("reviewed")
        self.assertEqual(self._state(slug), "published")
        score = self._read(slug, "review", "score.json")
        self.assertEqual(score["idea_sha"], sha)
        self.assertTrue(score["publish_eligible"], score)
        self.assertTrue(all(score["gates"].values()), score["gates"])
        self.assertGreaterEqual(score["score"], 70.0)
        stub = self._read(slug, "send.json")
        self.assertTrue(stub["dry_run"])  # BOB_SEND_DRY_RUN=1 default
        self.assertEqual(stub["send_authority"], "none")
        self.assertEqual(stub["idea_sha"], sha)
        self.assertEqual(stub["workshop_contract"],
                         "inventor_workshop.artifacts/v1")
        self.assertEqual(len(stub["workshop_artifact_sha256"]), 64)
        self.assertEqual(len(stub["workshop_pack_sha256"]), 64)
        publish_rows = [row for row in ledger.rows(slug=slug)
                        if row["kind"] == "send"]
        self.assertEqual(len(publish_rows), 1)
        self.assertGreaterEqual(publish_rows[0]["score"], 70.0)

        # A dry-run stub is terminal for the scheduler. Only an authenticated
        # publish/readback may make a game live.
        self.assertIsNone(queue.claim_next("test"))
        self.assertEqual(self._state(slug), "published")


class BuildMeshGateTest(_HomeCase):
    def test_lens_cannot_rescue_a_malformed_nonempty_mesh(self):
        slug = "meshlooksreal"
        queue.add_game(slug, "Mesh Looks Real", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        for state in ("researched", "ruled", "rules_gated", "simulated",
                      "tabled", "briefed", "built", "build_gated"):
            queue.advance(slug, state, "test setup")
        gdir = os.path.join(self.home, "toys", slug)
        os.makedirs(os.path.join(gdir, "parts"))
        os.makedirs(os.path.join(gdir, "review"))
        with open(os.path.join(gdir, "idea.json"), "w") as handle:
            json.dump({"slug": slug, "title": "Mesh Looks Real"}, handle)
        with open(os.path.join(gdir, "parts", "token.stl"), "wb") as handle:
            handle.write(b"solid token\nfacet normal 0 0 0\nendsolid token\n")
        # Even a planted PASS lens must not be consulted before deterministic
        # topology succeeds.
        self._plant("bob-build-lens", _FIXTURES["bob-build-lens"])

        self._tick_once("build_gated")

        record = self._read(slug, "review", "build_gate.json")
        self.assertFalse(record["build_pass"])
        self.assertFalse(record["deterministic_mesh_pass"])
        self.assertFalse(record["lens_pass"])
        self.assertEqual(record["mesh_receipts"][0]["receipt"]["status"], "held")
        self.assertIn(
            "missing_ascii_outer_loop",
            record["mesh_receipts"][0]["receipt"]["hold_reasons"],
        )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_build_gate_uses_workshop_no_follow_mesh_reader(self):
        slug = "meshlink"
        queue.add_game(slug, "Mesh Link", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        for state in ("researched", "ruled", "rules_gated", "simulated",
                      "tabled", "briefed", "built", "build_gated"):
            queue.advance(slug, state, "test setup")
        gdir = os.path.join(self.home, "toys", slug)
        parts = os.path.join(gdir, "parts")
        os.makedirs(parts)
        os.makedirs(os.path.join(gdir, "review"))
        with open(os.path.join(gdir, "idea.json"), "w") as handle:
            json.dump({"slug": slug, "title": "Mesh Link"}, handle)
        target = os.path.join(gdir, "outside-mesh")
        with open(target, "w") as handle:
            handle.write(_TETRA_STL)
        os.symlink(target, os.path.join(parts, "token.stl"))

        self._tick_once("build_gated")

        record = self._read(slug, "review", "build_gate.json")
        self.assertFalse(record["deterministic_mesh_pass"])
        self.assertEqual(
            record["mesh_receipts"][0]["path_error"], "path_is_symlink")
        self.assertIsNone(record["mesh_receipts"][0]["receipt"])


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
        gdir = os.path.join(self.home, "toys", slug)
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
        # 2026-08-23 recalibration: a sim finding spends a REWORK lap (back
        # to ruled with the findings) — park is for a spent budget only.
        self.assertEqual(game["state"], "ruled")
        self.assertEqual(game["budgets"]["rework_used"], 1)
        last_note = game["log"][-1]["note"]
        self.assertIn("sim gate failed", last_note)
        self.assertIn("seat_bias_ok", last_note)  # the named failed floor
        # The rework rewind RESETS the certifying artifacts (stale-verdict
        # discipline) — the gate file must be gone so next lap regenerates
        # everything against the new rules.
        self.assertFalse(os.path.exists(os.path.join(
            self.home, "toys", slug, "playtest", "sim_gate.json")))
        # The refusal is on the ledger too, with the game attributed.
        notes = " | ".join(row["notes"] for row in ledger.rows(slug=slug))
        self.assertIn("sim FAIL", notes)


class EditionLaneTest(_HomeCase):
    """classic-reborn arm: faithfulness lint at rules_gated, then the legal
    skip path — sims and TABLES skipped (no engine exists), but the fresh
    reader still runs at tabled: clarity weighs 25 in the 2026-08-22
    edition re-cut, and an unread rules sheet scored 0 forever (the lane
    was mathematically unpublishable — pre-launch verify finding)."""

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
                         "bob-rules-writer", "bob-rules-lens",
                         "bob-fresh-reader"])

        self._tick_once("sparked")
        self.assertEqual(self._read(slug, "idea.json")["lane"], "edition")
        self._tick_once("researched")
        self._tick_once("ruled")
        self._tick_once("rules_gated")
        # The skip path STOPS at tabled: the fresh reader still owes the
        # edition its cold read (clarity evidence for the re-cut weights).
        self.assertEqual(self._state(slug), "tabled")
        self._tick_once("tabled")

        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "briefed")
        notes = " | ".join(entry["note"] for entry in game["log"])
        self.assertIn("edition lane", notes)
        self.assertIn("classic proved itself", notes)
        # The fresh reader DID run — clarity evidence exists for the sheet.
        reader = self._read(slug, "review", "fresh_reader.json")
        self.assertEqual(reader["misses"], 1)
        # No engine, no sim, no table artifacts were ever created.
        pdir = os.path.join(self.home, "toys", slug, "playtest")
        self.assertFalse(os.path.exists(os.path.join(pdir, "engine.py")))
        self.assertFalse(os.path.exists(os.path.join(pdir, "sim_report.json")))
        self.assertFalse(os.path.exists(os.path.join(pdir, "table_report.json")))


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


class TriageSafetyDriftTest(_HomeCase):
    """Format drift in the triage reply must never read as a CPSIA refuse:
    killed is terminal, so only an explicit False (bool or 'false') kills."""

    def _sparked_game(self, slug):
        queue.add_game(slug, "placeholder", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        self._plant_all(["bob-ideator"])

    def test_absent_safety_pass_releases_not_kills(self):
        slug = "drifty"
        self._sparked_game(slug)
        self._plant("bob-triage-judge",
                    json.dumps({"pick": 0, "reasons": "field omitted"}))
        self._tick_once("sparked")
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "sparked")  # released, retryable
        self.assertIsNone(game["lease"]["holder"])
        notes = " | ".join(row["notes"] for row in ledger.rows(slug=slug))
        self.assertIn("safety_pass absent", notes)

    def test_string_true_is_a_pass_not_a_refuse(self):
        slug = "stringy"
        self._sparked_game(slug)
        self._plant("bob-triage-judge", json.dumps(
            {"pick": 0, "safety_pass": "true", "reasons": "ok"}))
        self._tick_once("sparked")
        self.assertEqual(self._state(slug), "researched")

    def test_explicit_false_string_still_kills(self):
        slug = "nogood"
        self._sparked_game(slug)
        self._plant("bob-triage-judge", json.dumps(
            {"pick": 0, "safety_pass": "false", "reasons": "CPSIA class"}))
        self._tick_once("sparked")
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "killed")
        self.assertIn("hard refuse", game["log"][-1]["note"])


class NoveltyKillNeedsUrlTest(_HomeCase):
    """A novelty kill needs a URL the judge actually opened — hearsay
    ('from memory', 'N/A') parks for a human, never terminates."""

    def _researched_game(self, slug):
        queue.add_game(slug, "placeholder", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        queue.advance(slug, "researched", "test setup")
        gdir = os.path.join(self.home, "toys", slug)
        os.makedirs(gdir)
        with open(os.path.join(gdir, "idea.json"), "w") as handle:
            json.dump({"slug": slug, "title": "T", "players": "2",
                       "lane": "invention"}, handle)

    def test_non_url_evidence_parks(self):
        slug = "hearsay"
        self._researched_game(slug)
        self._plant("bob-novelty-judge", json.dumps(
            {"pass": False, "evidence_url": "I recall a similar game",
             "nearest": [], "margin": "near", "notes": ""}))
        self._tick_once("researched")
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "parked")
        self.assertIn("without URL evidence", game["log"][-1]["note"])

    def test_http_url_evidence_kills(self):
        slug = "cloned"
        self._researched_game(slug)
        self._plant("bob-novelty-judge", json.dumps(
            {"pass": False,
             "evidence_url": "https://boardgamegeek.com/boardgame/1",
             "nearest": [], "margin": "near", "notes": ""}))
        self._tick_once("researched")
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "killed")
        self.assertIn("URL evidence", game["log"][-1]["note"])


class SparkNewNumberingTest(_HomeCase):
    """spark_new numbers by max+1 over ^g(\\d+)$ (a hand-deleted slug must
    not cause an eternal collision), retries a TOCTOU collision once, and
    never lets an exception escape."""

    def test_max_plus_one_survives_a_deleted_slug(self):
        queue.add_game("g0001", "a")
        queue.add_game("g0003", "b")  # g0002 was hand-deleted
        slug = invent.spark_new()
        self.assertEqual(slug, "g0004")
        self.assertIn("g0004", queue.load()["games"])

    def test_collision_retries_once_and_never_raises(self):
        queue.add_game("g0001", "a")
        original = queue.add_game
        calls = []

        def collide_once(slug, title, direction=None):
            if not calls:
                calls.append(slug)
                raise ValueError("game %r already exists" % slug)
            return original(slug, title, direction=direction)

        queue.add_game = collide_once
        try:
            slug = invent.spark_new()
        finally:
            queue.add_game = original
        self.assertEqual(calls, ["g0002"])  # first try collided
        self.assertEqual(slug, "g0003")     # bumped once, succeeded
        self.assertIn("g0003", queue.load()["games"])


class ReworkResetTest(_HomeCase):
    """A rework rewind to `ruled` deletes every artifact certified against
    the outgoing rules — idea.json never changes, so without the delete the
    old engine re-certifies the pre-rework game (stale idea_sha anchor)."""

    _STALE = (
        ("playtest", "engine.py"),
        ("playtest", "sim_report.json"),
        ("playtest", "sim_gate.json"),
        ("playtest", "table_report.json"),
        ("review", "fresh_reader.json"),
    )
    _KEPT = (("review", "safety.json"), ("review", "novelty.json"))

    def _plant_artifacts(self, slug):
        gdir = os.path.join(self.home, "toys", slug)
        for parts in self._STALE + self._KEPT:
            path = os.path.join(gdir, *parts)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as handle:
                handle.write("{}")

    def test_lens_fail_rework_deletes_stale_artifacts(self):
        slug = "reworked"
        queue.add_game(slug, "Reworked", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        for state in ("researched", "ruled", "rules_gated"):
            queue.advance(slug, state, "test setup")
        gdir = os.path.join(self.home, "toys", slug)
        os.makedirs(gdir, exist_ok=True)
        # Valid rules artifacts so the free lint passes and the paid lens
        # (fixture: FAIL) is what sends the game back to ruled.
        reply = json.loads(_FIXTURES["bob-rules-writer"])
        with open(os.path.join(gdir, "idea.json"), "w") as handle:
            json.dump({"slug": slug, "title": "Reworked", "players": "2",
                       "lane": "invention"}, handle)
        with open(os.path.join(gdir, "rules.md"), "w") as handle:
            handle.write(reply["rules_md"])
        with open(os.path.join(gdir, "bill.json"), "w") as handle:
            json.dump(reply["bill"], handle)
        with open(os.path.join(gdir, "game.json"), "w") as handle:
            json.dump(reply["game"], handle)
        self._plant_artifacts(slug)
        self._plant("bob-rules-lens", json.dumps(
            {"verdict": "FAIL", "issues": ["the win condition contradicts "
                                           "the turn loop"]}))

        self._tick_once("rules_gated")
        self.assertEqual(self._state(slug), "ruled")
        for parts in self._STALE:
            self.assertFalse(
                os.path.exists(os.path.join(gdir, *parts)),
                "%s survived the rework reset" % os.path.join(*parts))
        # Idea-bound verdicts survive: nothing regenerates them post-rework.
        for parts in self._KEPT:
            self.assertTrue(os.path.exists(os.path.join(gdir, *parts)))


class TabledCrashRoutingTest(_HomeCase):
    """A broken/stale engine at the table gate parks with an artifact —
    before the fix the exception escaped tick(), leaked the lease, and the
    game entered an eternal crash-claim loop re-paying seat calls."""

    def test_run_tables_crash_parks_with_artifact(self):
        slug = "tablecrash"
        queue.add_game(slug, "Table Crash", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        for state in ("researched", "ruled", "rules_gated", "simulated",
                      "tabled"):
            queue.advance(slug, state, "test setup")
        gdir = os.path.join(self.home, "toys", slug)
        os.makedirs(gdir)
        with open(os.path.join(gdir, "idea.json"), "w") as handle:
            json.dump({"slug": slug, "title": "Table Crash", "players": "2",
                       "lane": "invention"}, handle)
        with open(os.path.join(gdir, "rules.md"), "w") as handle:
            handle.write(_RULES_MD)
        # No playtest/engine.py: run_tables raises before any seat spend.

        self._tick_once("tabled")  # must not raise
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "parked")
        self.assertIn("table run failed", game["log"][-1]["note"])
        gate = self._read(slug, "playtest", "table_gate.json")
        self.assertFalse(gate["table_pass"])
        self.assertTrue(gate["error"])


class CrashCounterTest(_HomeCase):
    """The contracted retry-once, enforced: the first crash at a state
    releases for a free retry, the second consecutive one parks; a
    successful step resets the counter."""

    def _briefed_game(self, slug):
        queue.add_game(slug, "Crashme", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        for state in ("researched", "ruled", "rules_gated", "simulated",
                      "tabled", "briefed"):
            queue.advance(slug, state, "test setup")
        # No bob-brief-writer fixture: the mock runner raises AgentError.

    def test_second_consecutive_agent_crash_parks(self):
        slug = "crashtwice"
        self._briefed_game(slug)
        self._tick_once("briefed")
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "briefed")  # first crash: released
        self.assertEqual(game["crashes"], {"state": "briefed", "count": 1})
        self._tick_once("briefed")
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "parked")   # second crash: parked
        self.assertIn("crashed 2 times in a row", game["log"][-1]["note"])

    def test_success_resets_the_counter(self):
        slug = "recovers"
        self._briefed_game(slug)
        self._tick_once("briefed")
        self.assertEqual(queue.load()["games"][slug]["crashes"]["count"], 1)
        self._plant_all(["bob-brief-writer"])
        self._tick_once("briefed")
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "built")
        self.assertNotIn("crashes", game)  # consecutive counter cleared

    def test_unexpected_exception_is_caught_and_counted(self):
        slug = "boomer"
        self._briefed_game(slug)
        original = invent.STEP_HANDLERS["briefed"]

        def boom(step):
            raise RuntimeError("engine ate itself")

        invent.STEP_HANDLERS["briefed"] = boom
        try:
            self._tick_once("briefed")  # must not raise
            game = queue.load()["games"][slug]
            self.assertEqual(game["state"], "briefed")
            self.assertIsNone(game["lease"]["holder"])  # lease not leaked
            self.assertEqual(game["crashes"],
                             {"state": "briefed", "count": 1})
            self._tick_once("briefed")
            self.assertEqual(self._state(slug), "parked")
        finally:
            invent.STEP_HANDLERS["briefed"] = original


class PageKitTest(_HomeCase):
    """Local listing facts survive fallback without owning Factory copy."""

    def _game_dir_with_bill(self, slug):
        gdir = os.path.join(self.home, "toys", slug)
        os.makedirs(gdir)
        with open(os.path.join(gdir, "idea.json"), "w") as handle:
            json.dump({"slug": slug, "title": "Lane War", "players": "2",
                       "concept": "pick-a-lane blocking race"}, handle)
        with open(os.path.join(gdir, "rules.md"), "w") as handle:
            handle.write(_RULES_MD)
        with open(os.path.join(gdir, "bill.json"), "w") as handle:
            json.dump([{"name": "lane token", "qty": 2},
                       {"name": "score peg", "qty": 2}], handle)
        return gdir

    def test_ai_created_survives_ten_agent_tags(self):
        slug = "tagfull"
        self._game_dir_with_bill(slug)
        self._plant("bob-page-writer", json.dumps({
            "title": "Lane War", "description": "A blocking race.",
            "tags": ["t%d" % i for i in range(10)],  # 10 tags, none ai-created
            "category": "toys", "prompt": "lane war",
        }))
        invent._page_kit(slug, {"title": "Lane War"})
        listing = self._read(slug, "listing.json")
        self.assertIn("ai-created", listing["tags"])
        self.assertEqual(listing["tags"][0], "ai-created")
        self.assertLessEqual(len(listing["tags"]), 10)

    def test_fallback_listing_keeps_server_enrichment_facts(self):
        slug = "fallback"
        self._game_dir_with_bill(slug)
        # No bob-page-writer fixture: the agent path degrades to the
        # deterministic fallback, which must be publishable AS IS.
        invent._page_kit(slug, {"title": "Lane War"})
        listing = self._read(slug, "listing.json")
        self.assertIn("use_case", listing)
        self.assertEqual(len(listing["story_blocks"]), 2)
        # These are local product facts only. Bob's retired curate() path
        # cannot send them to Factory; Workshop imports the model and the
        # server owns rich page enrichment.
        self.assertTrue(listing["use_case"]["body"])
        self.assertIn("ai-created", listing["tags"])


class RealSendSingleAdvanceTest(_HomeCase):
    """The live-path regression: send_draft advances reviewed->published
    and flip_public advances published->live, so _send must NOT advance
    again (the third advance was an illegal live->published ValueError on
    EVERY real publish). Rich copy/media stay server-owned."""

    def _reviewed_game(self, slug):
        queue.add_game(slug, "Lane War", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        for state in ("researched", "ruled", "rules_gated", "simulated",
                      "tabled", "briefed", "built", "build_gated",
                      "reviewed"):
            queue.advance(slug, state, "test setup")
        gdir = os.path.join(self.home, "toys", slug)
        os.makedirs(os.path.join(gdir, "review"))
        os.makedirs(os.path.join(gdir, "playtest"))
        with open(os.path.join(gdir, "idea.json"), "w") as handle:
            json.dump({"slug": slug, "title": "Lane War", "players": "2",
                       "lane": "invention"}, handle)
        with open(os.path.join(gdir, "idea.json"), "rb") as handle:
            sha = hashlib.sha256(handle.read()).hexdigest()
        with open(os.path.join(gdir, "rules.md"), "w") as handle:
            handle.write(_RULES_MD)
        with open(os.path.join(gdir, "bill.json"), "w") as handle:
            json.dump([{"name": "lane token", "qty": 2}], handle)

        def w(rel, obj):
            obj["idea_sha"] = sha
            with open(os.path.join(gdir, *rel), "w") as handle:
                json.dump(obj, handle)

        w(("review", "safety.json"), {"safety_pass": True})
        w(("review", "novelty.json"),
          {"pass": True, "evidence_url": None, "margin": "far"})
        w(("review", "rules_lint.json"), {"lint_pass": True, "problems": []})
        w(("review", "build_gate.json"),
          {"build_pass": True, "survives_as_cardboard": False})
        w(("review", "fresh_reader.json"),
          {"questions": 12, "misses": 1, "teach_minutes": 4})
        w(("playtest", "sim_gate.json"),
          {"integrity_pass": True, "degeneracy_pass": True, "all_pass": True})
        w(("playtest", "sim_report.json"),
          {"by_players": {"2": {"gavel": {"harmonic_mean": 0.9},
                                "ladder": {"edges": {"random": 0.3}}}}})
        w(("playtest", "table_report.json"),
          {"aggregate": {"would_play_again_fraction": 1.0}})
        return sha

    def test_real_send_advances_once_without_inventor_page_writes(self):
        # BOB_SHOP_PUBLIC=1 exercises the optional Shop Door public path,
        # off today per Dee's draft-first ruling 2026-08-22).
        from harness import send
        slug = "liveone"
        self._reviewed_game(slug)
        os.environ["BOB_SEND_DRY_RUN"] = "0"
        os.environ["BOB_SHOP_PUBLIC"] = "1"
        self.addCleanup(os.environ.pop, "BOB_SHOP_PUBLIC", None)
        calls = []
        saved = {name: getattr(send, name)
                 for name in ("validate", "send_draft", "flip_public")}

        def fake_import(s):
            calls.append("import")
            queue.advance(s, "published", "draft imported (mock)")

        def fake_flip(s, price_cents):
            calls.append("flip:%d" % price_cents)
            queue.advance(s, "live", "flipped public (mock)")

        send.validate = lambda s: []
        send.send_draft = fake_import
        send.flip_public = fake_flip
        try:
            self._tick_once("reviewed")  # must not raise ValueError
        finally:
            for name, fn in saved.items():
                setattr(send, name, fn)

        self.assertEqual(
            calls, ["import", "flip:%d" % invent.PRICE_CENTS_DEFAULT])
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "live")
        # The win still lands on the ledger even though the flip (not
        # invent) moved the queue to live.
        send_rows = [row for row in ledger.rows(slug=slug)
                     if row["kind"] == "send"]
        self.assertEqual(len(send_rows), 1)


    def test_draft_first_default_stops_before_the_flip(self):
        # Dee 2026-08-22 (second ruling): "publish draft is fine. it's one
        # click for me to review for now." Default = Workshop import, NO
        # flip_public; the model-only draft rests at published awaiting the
        # human click while Factory owns page enrichment.
        from harness import send
        slug = "draftone"
        self._reviewed_game(slug)
        os.environ["BOB_SEND_DRY_RUN"] = "0"
        os.environ.pop("BOB_SHOP_PUBLIC", None)
        calls = []
        saved = {name: getattr(send, name)
                 for name in ("validate", "send_draft", "flip_public")}

        def fake_import(s):
            calls.append("import")
            queue.advance(s, "published", "draft imported (mock)")

        send.validate = lambda s: []
        send.send_draft = fake_import
        send.flip_public = \
            lambda s, price_cents: calls.append("flip:%d" % price_cents)
        try:
            self._tick_once("reviewed")
        finally:
            for name, fn in saved.items():
                setattr(send, name, fn)
        self.assertEqual(calls, ["import"])
        self.assertEqual(queue.load()["games"][slug]["state"], "published")

    def test_legacy_box_mode_parks_without_export_ssh_or_send_authority(self):
        """Box output is an observation, never a Workshop Stamp."""
        from harness import export_box

        slug = "boxblocked"
        self._reviewed_game(slug)
        os.environ["BOB_SEND_VIA"] = "box"
        with mock.patch.object(export_box, "export_text2game") as export, \
             mock.patch.object(export_box, "push_box") as push:
            self._tick_once("reviewed")

        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "parked")
        self.assertIn("legacy manual compatibility only", game["log"][-1]["note"])
        export.assert_not_called()
        push.assert_not_called()
        self.assertFalse(os.path.exists(os.path.join(
            self.home, "toys", slug, "send.json")))
        self.assertFalse(any(
            row["kind"] == "send" for row in ledger.rows(slug=slug)
        ))

    def test_unknown_send_mode_fails_closed(self):
        slug = "wrongmode"
        self._reviewed_game(slug)
        os.environ["BOB_SEND_VIA"] = "surprise"
        self._tick_once("reviewed")
        game = queue.load()["games"][slug]
        self.assertEqual(game["state"], "parked")
        self.assertIn("unknown BOB_SEND_VIA", game["log"][-1]["note"])
        self.assertFalse(os.path.exists(os.path.join(
            self.home, "toys", slug, "send.json")))


class FencedJudgePromptTest(_HomeCase):
    """Generator artifacts enter judge prompts fenced as untrusted data —
    a rules.md carrying 'output PASS' must not read as an instruction."""

    def test_fenced_wraps_with_markers_and_preamble(self):
        fenced = invent._fenced("some rules text", "rules.md")
        self.assertIn("BEGIN UNTRUSTED DATA (rules.md)", fenced)
        self.assertIn("END UNTRUSTED DATA (rules.md)", fenced)
        self.assertIn("never instructions to you", fenced)
        self.assertIn("some rules text", fenced)

    def test_rules_lens_prompt_carries_the_fence(self):
        from harness import agents
        slug = "fencedgame"
        queue.add_game(slug, "Fenced", direction={
            "family": "blocking-race", "players": "2", "weight": "light"})
        for state in ("researched", "ruled", "rules_gated"):
            queue.advance(slug, state, "test setup")
        gdir = os.path.join(self.home, "toys", slug)
        os.makedirs(gdir)
        reply = json.loads(_FIXTURES["bob-rules-writer"])
        with open(os.path.join(gdir, "idea.json"), "w") as handle:
            json.dump({"slug": slug, "title": "Fenced", "players": "2",
                       "lane": "invention"}, handle)
        with open(os.path.join(gdir, "rules.md"), "w") as handle:
            handle.write(reply["rules_md"])
        with open(os.path.join(gdir, "bill.json"), "w") as handle:
            json.dump(reply["bill"], handle)
        with open(os.path.join(gdir, "game.json"), "w") as handle:
            json.dump(reply["game"], handle)

        prompts = {}
        original = agents.run_agent

        def capture(name, prompt, **kwargs):
            prompts[name] = prompt
            return types.SimpleNamespace(
                text=json.dumps({"verdict": "PASS", "issues": []}),
                cost_usd=0.0)

        agents.run_agent = capture
        try:
            self._tick_once("rules_gated")
        finally:
            agents.run_agent = original
        lens_prompt = prompts["bob-rules-lens"]
        self.assertIn("BEGIN UNTRUSTED DATA (rules.md)", lens_prompt)
        self.assertIn("never instructions to you", lens_prompt)


class BobDriverTest(_HomeCase):
    """cmd_tick regressions: the scholar 'empty' outcome falls through to
    the architect/meta steps, the tick opens a real time budget, and
    daybook writes hold the .daybook.lock flock."""

    def _quiet_preconditions(self, bob):
        from harness import integrity
        saved = (integrity.audit, ledger.spend_today)
        integrity.audit = lambda: []
        ledger.spend_today = lambda: 0.0
        os.environ["BOB_MAX_INFLIGHT"] = "0"  # never spark in these tests
        return saved

    def _restore(self, saved):
        from harness import integrity
        integrity.audit, ledger.spend_today = saved
        os.environ.pop("BOB_MAX_INFLIGHT", None)

    def test_scholar_empty_falls_through_to_architect(self):
        import bob
        from loops import architect, scholar
        saved = self._quiet_preconditions(bob)
        saved_loops = (scholar.tick, architect.tick)
        ran = []
        scholar.tick = lambda: {"lane": None, "unit": None,
                                "outcome": "empty"}
        architect.tick = lambda: ran.append("architect") or {"swept": True}
        try:
            bob.cmd_tick(None)
        finally:
            scholar.tick, architect.tick = saved_loops
            self._restore(saved)
        self.assertEqual(ran, ["architect"])  # step 4 was reachable

    def test_cmd_tick_opens_a_timebudget_run(self):
        import bob
        from harness import timebudget
        from loops import scholar
        saved = self._quiet_preconditions(bob)
        saved_tick = scholar.tick
        scholar.tick = lambda: {"lane": "papers", "unit": "u1",
                                "outcome": "studied"}
        try:
            bob.cmd_tick(None)
        finally:
            scholar.tick = saved_tick
            self._restore(saved)
        report = timebudget.report()  # raises if no run was opened
        self.assertEqual(report["total_minutes"],
                         float(bob.TICK_BUDGET_MINUTES))
        self.assertEqual(report["steps"], [])  # handlers are not wrapped

    def test_daybook_writes_hold_the_flock(self):
        import fcntl

        import bob
        state_dir = os.path.join(self.home, "state")
        os.makedirs(state_dir, exist_ok=True)
        # Seed a field a concurrent writer (harness.agents) would have
        # appended; the locked read-modify-write must preserve it.
        with open(os.path.join(state_dir, "DAYBOOK.json"), "w") as handle:
            json.dump({"2026-08-22": {"ticks": 1, "cost_usd": 1.25,
                                      "steps": [{"name": "x"}]}}, handle)
        lock = open(os.path.join(state_dir, ".daybook.lock"), "w")
        fcntl.flock(lock, fcntl.LOCK_EX)
        done = threading.Event()
        thread = threading.Thread(
            target=lambda: (bob._stamp_heartbeat(), done.set()))
        thread.start()
        try:
            # The stamp must BLOCK while another holder owns the lock —
            # that blocking is the whole fix (unlocked writes could erase
            # a just-appended agent cost row).
            self.assertFalse(done.wait(0.3))
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock.close()
        thread.join(5)
        self.assertTrue(done.is_set())
        book = bob._read_daybook()
        self.assertIn("heartbeat", book)
        self.assertEqual(book["2026-08-22"]["cost_usd"], 1.25)  # preserved


if __name__ == "__main__":
    unittest.main()
