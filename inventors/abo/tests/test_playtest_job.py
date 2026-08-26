"""ABO's Playtest seam, end to end over one fixture revision.

One Concept, one Make, one Playtest. The model seats are replayed from the
recorded transcript through a transport marked live, because the thing under
test here is the *assembly* — two separate results, two separate evidence
files, the social style fed across, every result bound to the revision's hash.
Whether a recording may be evidence is a different rule, and
`test_model_seats.py` proves that it may not.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

INVENTOR_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = INVENTOR_ROOT.parents[1]
FIXTURES = INVENTOR_ROOT / "tests" / "fixtures"
for candidate in (
    INVENTOR_ROOT,
    INVENTOR_ROOT / "tests",
    FIXTURES,
    WORKSHOP_ROOT / "src",
    WORKSHOP_ROOT / "tools",
):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import fixture_game as F  # noqa: E402
import model_seats  # noqa: E402
import simulation  # noqa: E402
from concept import AboConcept  # noqa: E402
from concept_fixture import (  # noqa: E402
    FixtureConceptArtist,
    fixture_explode_inspector,
)
from inventor_workshop.jobs import (  # noqa: E402
    ConceptContext,
    MakeContext,
    PlaytestContext,
    WaitingFor,
)
from inventor_workshop.make import Wish  # noqa: E402
from inventor_workshop.taste import load_taste  # noqa: E402
from inventor_workshop.toys import ToyBlueprint  # noqa: E402
from make import AboMake  # noqa: E402
from playtest_job import AboPlaytest  # noqa: E402
from research import InventedGame  # noqa: E402
from test_make import (  # noqa: E402
    fixture_cad_builder,
    fixture_compiler,
    fixture_step_generator,
)

BLUEPRINT = ToyBlueprint.for_lane("invented-games")
CHEAP_SIMULATION = dict(
    games_per_style=3,
    ladder_games=3,
    balance_games=3,
    distinctness_positions=4,
    sensitivity_games=4,
    mc_budget=4,
    seed=5,
)


class LiveReplay(model_seats.RecordedTransport):
    """The recorded replies, marked live, so the assembly can be exercised.

    Only ever used here. The rule that a recording is not evidence about a
    revision is proved in `test_model_seats.py`; this stands in for seats that
    did play, so the record that would be built from them can be inspected.
    """

    name = "live-replay-fixture"
    live = True


class PlaytestSeamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.mkdtemp()
        root = Path(cls.temporary)
        cls.wish = Wish.create(
            "notchline",
            F.FIXTURE_OBJECTIVE,
            constraints={"lane": "invented-games", "audience": "grown-ups-14-plus"},
            context={"inventor_id": "abo"},
        )
        cls.taste = load_taste(INVENTOR_ROOT)
        cls.concept = AboConcept(
            FixtureConceptArtist(),
            fixture_explode_inspector,
            lambda request: InventedGame(F.fixture_record()),
        )(
            ConceptContext(
                cls.wish, cls.taste, BLUEPRINT, 1, root / "concept-1", playtest_rounds=2
            )
        )
        cls.made = AboMake(fixture_compiler, fixture_cad_builder, fixture_step_generator)(
            MakeContext(
                cls.wish,
                cls.taste,
                BLUEPRINT,
                1,
                root / "make-1",
                playtest_rounds=2,
                concept_images=cls.concept,
            )
        )
        cls.context = PlaytestContext(
            cls.wish, cls.taste, BLUEPRINT, 1, cls.made, root / "playtest-1",
            playtest_rounds=2,
        )
        cls.evidence_root = root / "evidence"
        job = AboPlaytest(
            simulation_settings=CHEAP_SIMULATION,
            evidence_root=cls.evidence_root,
            seat_transport=LiveReplay.from_path(FIXTURES / "model_seat_transcript.json"),
            model_seat_games=2,
        )
        # The floor is not met on a three-game sample, so the seam raises. The
        # assembly is what this class inspects, so it is called directly.
        cls.summary, cls.games = job._play_model_seats(cls.context, _engine(cls.made), 2)
        cls.outcome = simulation.run_simulation(
            _engine(cls.made),
            artifact_sha256=cls.made.artifact_sha256,
            seats=2,
            social_sample=model_seats.social_sample(cls.summary),
            **CHEAP_SIMULATION,
        )
        cls.playtested = job._assemble(
            cls.context, cls.outcome, cls.summary, cls.games
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temporary, ignore_errors=True)

    # -- the two results -------------------------------------------------

    def test_both_connected_results_are_returned(self):
        ids = sorted(item.playtest_id for item in self.playtested.evidence.results)
        self.assertEqual(ids, ["agent-playtest", "game-simulation"])

    def test_every_result_is_bound_to_the_revision_it_tested(self):
        for result in self.playtested.evidence.results:
            self.assertEqual(result.artifact_sha256, self.made.artifact_sha256)
            self.assertEqual(result.evidence["artifact_sha256"], self.made.artifact_sha256)

    def test_every_result_is_ai_simulation_with_a_named_evaluator(self):
        for result in self.playtested.evidence.results:
            self.assertEqual(result.evidence["evidence_class"], "ai-simulation")
            self.assertTrue(result.evaluator)
            self.assertTrue(result.evaluator_version)

    def test_every_result_references_sealed_evidence_by_hash(self):
        inventory = {
            entry.path: entry.sha256
            for entry in self.playtested.evidence.evidence_manifest.entries
        }
        for result in self.playtested.evidence.results:
            self.assertEqual(inventory.get(result.evidence_ref), result.evidence_sha256)

    def test_the_two_results_keep_separate_evidence_files(self):
        files = sorted(path.name for path in self.evidence_root.glob("*.json"))
        self.assertEqual(files, ["agent-playtest.json", "game-simulation.json"])
        simulation_evidence = json.loads(
            (self.evidence_root / "game-simulation.json").read_text(encoding="utf-8")
        )
        seat_evidence = json.loads(
            (self.evidence_root / "agent-playtest.json").read_text(encoding="utf-8")
        )
        # The simulation references the model-seat games; it does not absorb them.
        self.assertEqual(simulation_evidence["social_sample"]["source"], "model-seats")
        self.assertNotIn("games_detail", simulation_evidence)
        self.assertIn("games_detail", seat_evidence)

    # -- agent-playtest --------------------------------------------------

    def test_agent_playtest_reports_two_distinct_non_empty_roles(self):
        result = _result(self.playtested, "agent-playtest")
        roles = result.evidence["agent_roles"]
        self.assertEqual(len(roles), 2)
        self.assertEqual(len(set(roles)), 2)
        self.assertTrue(all(role.strip() for role in roles))

    def test_seat_reports_are_recorded_as_simulation_findings(self):
        result = _result(self.playtested, "agent-playtest")
        reports = result.evidence["seat_reports"]
        self.assertTrue(any("the game got smaller" in item for item in reports))
        self.assertTrue(
            any("rules question raised in play" in item for item in reports)
        )

    def test_no_result_claims_anybody_enjoyed_the_game(self):
        blob = json.dumps(
            [result.evidence for result in self.playtested.evidence.results]
        ).casefold()
        for word in ("enjoy", "fun", "delight", "would play again"):
            self.assertNotIn(word, blob)

    # -- the social style ------------------------------------------------

    def test_the_model_seat_games_supply_the_social_style(self):
        result = _result(self.playtested, "game-simulation")
        self.assertIn("social", result.evidence["player_styles"])

    def test_all_four_styles_are_declared_once_the_seats_have_played(self):
        result = _result(self.playtested, "game-simulation")
        self.assertEqual(
            sorted(result.evidence["player_styles"]), sorted(simulation.STYLES)
        )

    # -- the floor still governs -----------------------------------------

    def test_the_seam_still_parks_below_the_floor(self):
        job = AboPlaytest(
            simulation_settings=CHEAP_SIMULATION,
            evidence_root=Path(self.temporary) / "evidence-2",
            seat_transport=LiveReplay.from_path(FIXTURES / "model_seat_transcript.json"),
            model_seat_games=2,
        )
        with self.assertRaises(WaitingFor) as caught:
            job(self.context)
        capabilities = [need.capability for need in caught.exception.needs]
        # The seats played, so `agent-playtest` is no longer waiting; the floor
        # and the two manufacturing results still are.
        self.assertNotIn("agent-playtest", capabilities)
        self.assertIn("game-simulation", capabilities)
        self.assertIn("mechanical-test", capabilities)
        self.assertIn("print-test", capabilities)


def _engine(made):
    from make import ENGINE_DIRECTORY, ENGINE_FILENAME, load_engine

    return load_engine(made.artifact_root / ENGINE_DIRECTORY / ENGINE_FILENAME)


def _result(playtested, name):
    return next(
        item for item in playtested.evidence.results if item.playtest_id == name
    )


if __name__ == "__main__":
    unittest.main()
