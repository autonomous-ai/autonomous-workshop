"""ABO's Concept: the game it invents, and everything that refuses one.

Every check here runs with no model, no network and no printer. The concept
images are drawn by the repository's deterministic fixture artist, which draws
swatches rather than pictures — nothing in this file should be read as evidence
that a design was visualized.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

INVENTOR_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = INVENTOR_ROOT.parents[1]
for candidate in (
    INVENTOR_ROOT,
    INVENTOR_ROOT / "tests" / "fixtures",
    WORKSHOP_ROOT / "src",
    WORKSHOP_ROOT / "tools",
):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import fixture_game as F  # noqa: E402
from concept import AboConcept  # noqa: E402
from concept_fixture import (  # noqa: E402
    FixtureConceptArtist,
    fixture_explode_inspector,
)
from game import (  # noqa: E402
    GAME_CHECK_FILENAME,
    GAME_RECORD_DIRECTORY,
    GAME_RECORD_FILENAME,
    GameRecord,
    GameRecordError,
    assert_playable_record,
    check_game,
)
from inventor_workshop.concept import (  # noqa: E402
    WishResearchRequest,
    assert_researched_breakdown,
)
from inventor_workshop.errors import ArtifactError, ContractError  # noqa: E402
from inventor_workshop.jobs import (  # noqa: E402
    ConceptContext,
    WishResearch,
    WishResearchFinding,
)
from inventor_workshop.make import Wish  # noqa: E402
from inventor_workshop.taste import load_taste  # noqa: E402
from inventor_workshop.toys import ToyBlueprint  # noqa: E402
from research import (  # noqa: E402
    AboWishResearcher,
    InventedGame,
    concept_components,
    research_from_game,
)


def wish_for(objective: str = F.FIXTURE_OBJECTIVE) -> Wish:
    return Wish.create(
        "notchline",
        objective,
        constraints={"lane": "invented-games", "audience": "grown-ups-14-plus"},
        context={"inventor_id": "abo"},
    )


def research_request(wish: Wish, round_number: int = 1) -> WishResearchRequest:
    return WishResearchRequest(
        wish,
        load_taste(INVENTOR_ROOT),
        ToyBlueprint.for_lane("invented-games"),
        round_number,
    )


class ConsistencyCheckTest(unittest.TestCase):
    """The rules and the box of pieces describe the same game, or they do not."""

    def test_a_complete_consistent_game_passes(self):
        result = check_game(F.fixture_record())
        self.assertTrue(result.passed, result.findings)
        self.assertEqual(result.findings, ())
        self.assertIsNone(result.disposition)
        # The recorded result names the exact rules and bill it was computed
        # over, so a later reader can tell whether it still describes the game.
        self.assertEqual(len(result.rules_sha256), 64)
        self.assertEqual(len(result.bill_sha256), 64)
        self.assertEqual(result.checker, "abo-rules-check")

    def test_a_rule_reaching_for_a_piece_not_in_the_box_fails(self):
        result = check_game(F.record_reaching_for_absent_component())
        self.assertFalse(result.passed)
        self.assertTrue(
            any(
                "uses 'score_track'" in finding and "turn[2]" in finding
                for finding in result.findings
            ),
            result.findings,
        )
        # A rules-versus-bill mismatch is missing description, not a design that
        # must subtract.
        self.assertEqual(result.disposition, "clarify")
        self.assertIsNone(result.problem_id)

    def test_a_piece_no_rule_uses_fails(self):
        result = check_game(F.record_with_unused_component())
        self.assertFalse(result.passed)
        self.assertTrue(
            any("spare_riser" in finding for finding in result.findings),
            result.findings,
        )
        self.assertEqual(result.disposition, "clarify")

    def test_exceeding_the_declared_ceiling_is_distinguished_from_an_ambiguity(self):
        result = check_game(F.record_over_its_own_ceiling())
        self.assertFalse(result.passed)
        self.assertTrue(
            any("over the declared maximum" in finding for finding in result.findings),
            result.findings,
        )
        # The design must subtract rather than be described more carefully, and
        # the disposition is what says so.
        self.assertEqual(result.disposition, "rework")
        self.assertEqual(result.problem_id, "complexity-budget")
        self.assertTrue(result.is_complexity_overrun)

    def test_too_many_piece_types_is_a_complexity_overrun(self):
        record = F.fixture_record()
        extra = []
        for index in range(4):
            base = record.components[1]
            extra.append(
                type(base)(
                    name="filler_%d" % index,
                    qty=2,
                    desc="An extra piece family.",
                    form="Square shaft with a notch.",
                    dimensions_mm=(14.0, 14.0, 20.0 + index),
                    placement="Standing in a board socket.",
                    interfaces="Spigot seats into a socket.",
                )
            )
        crowded = F.fixture_record(components=record.components + tuple(extra))
        result = check_game(crowded)
        self.assertFalse(result.passed)
        self.assertEqual(result.problem_id, "complexity-budget")

    def test_a_failure_is_a_refusal_not_a_pass_with_a_warning(self):
        with self.assertRaises(GameRecordError) as caught:
            assert_playable_record(
                F.record_reaching_for_absent_component(), F.FIXTURE_OBJECTIVE
            )
        self.assertIn("refused", str(caught.exception))
        self.assertIn("score_track", str(caught.exception))


class WishIsStructuralTest(unittest.TestCase):
    def test_a_wish_that_only_names_the_game_is_refused(self):
        with self.assertRaises(GameRecordError) as caught:
            assert_playable_record(
                F.record_with_decorative_wish(), F.FIXTURE_OBJECTIVE
            )
        self.assertIn("name or a label", str(caught.exception))

    def test_a_record_tracing_nothing_to_the_wish_is_refused(self):
        with self.assertRaises(GameRecordError) as caught:
            assert_playable_record(F.record_without_wish_hooks(), F.FIXTURE_OBJECTIVE)
        self.assertIn("traces nothing", str(caught.exception))

    def test_a_hook_onto_a_piece_that_is_not_in_the_bill_is_refused(self):
        from game import WishHook

        record = F.fixture_record(
            wish_hooks=(WishHook("hard to master", "component", "not_a_piece"),)
        )
        with self.assertRaises(GameRecordError) as caught:
            assert_playable_record(record, F.FIXTURE_OBJECTIVE)
        self.assertIn("not_a_piece", str(caught.exception))


class ColourFreedomTest(unittest.TestCase):
    def test_a_rule_distinguishing_by_colour_is_refused(self):
        with self.assertRaises(GameRecordError) as caught:
            assert_playable_record(
                F.record_distinguishing_by_colour(), F.FIXTURE_OBJECTIVE
            )
        message = str(caught.exception)
        self.assertIn("distinguishes by colour", message)
        self.assertIn("carried by shape", message)

    def test_art_direction_must_speak_form_language(self):
        with self.assertRaises(GameRecordError) as caught:
            assert_playable_record(
                F.record_with_empty_art_direction(), F.FIXTURE_OBJECTIVE
            )
        self.assertIn("form language", str(caught.exception))

    def test_the_good_record_names_no_colour_and_no_material(self):
        from game import colour_free

        self.assertEqual(colour_free(F.fixture_record()), ())


class ResearchTest(unittest.TestCase):
    """The physical facts, read off the game that was invented."""

    def test_the_bill_becomes_the_components(self):
        record = F.fixture_record()
        research = research_from_game(record)
        self.assertEqual(
            [item.key for item in research.components],
            [item.concept_key for item in record.components],
        )
        # A quantity belongs in the purpose line; one entry per instance would
        # spend the brief's twelve slots on arithmetic.
        purposes = {item.key: item.purpose for item in research.components}
        self.assertIn("12 in the box", purposes["pillar-low"])
        self.assertIn("6 per player", purposes["pillar-low"])

    def test_motif_variants_stay_separate_components(self):
        record = F.fixture_record()
        keys = [item.key for item in concept_components(record)]
        self.assertIn("pillar-low", keys)
        self.assertIn("pillar-high", keys)
        self.assertEqual(len(set(keys)), len(keys))

    def test_every_stated_fact_is_attributable(self):
        research = research_from_game(F.fixture_record())
        # `WishResearch` refuses an unattributed field itself; this asserts the
        # shape ABO actually produces — every fact a recorded decision, since
        # the game did not exist to be looked up.
        self.assertTrue(research.findings)
        for finding in research.findings:
            # Exactly one of the two: never both, never neither.
            self.assertEqual(
                bool(finding.source_ids), finding.decided_because is None
            )
        decided = {finding.field for finding in research.decisions()}
        self.assertLessEqual(
            {"object", "category", "envelope_mm", "wall_mm", "components", "print"},
            decided,
        )
        for finding in research.decisions():
            self.assertTrue(finding.decided_because.strip())

    def test_an_unattributed_dimension_is_refused(self):
        research = research_from_game(F.fixture_record())
        stripped = [
            finding
            for finding in research.findings
            if finding.field != "envelope_mm"
        ]
        with self.assertRaises(ContractError) as caught:
            WishResearch(
                research.object,
                research.category,
                research.envelope_mm,
                research.wall_mm,
                research.features,
                research.print,
                research.components,
                research.fits,
                tuple(stripped),
                research.sources,
            )
        self.assertIn("envelope_mm", str(caught.exception))

    def test_a_fact_with_both_a_source_and_a_reason_is_refused(self):
        with self.assertRaises(ContractError):
            WishResearchFinding(
                claim="The box is 204 mm square.",
                field="envelope_mm",
                source_ids=("some-source",),
                decided_because="and also decided",
            )

    def test_the_breakdown_survives_the_shared_researched_breakdown_rules(self):
        research = research_from_game(F.fixture_record())
        assert_researched_breakdown(wish_for(), research)

    def test_no_game_inventor_parks_the_run(self):
        from inventor_workshop.jobs import WaitingFor

        with self.assertRaises(WaitingFor) as caught:
            AboWishResearcher()(research_request(wish_for()))
        self.assertEqual(
            [need.capability for need in caught.exception.needs],
            ["abstract-game-invention"],
        )

    def test_a_refused_game_never_becomes_a_breakdown(self):
        researcher = AboWishResearcher(
            lambda request: InventedGame(F.record_with_unused_component())
        )
        with self.assertRaises(GameRecordError):
            researcher(research_request(wish_for()))
        self.assertIsNone(researcher.record)


class SealedConceptTest(unittest.TestCase):
    """Design decision D1: the rules seal into the concept with the pixels."""

    def concept_for(self, tmp: str, record=None, round_number: int = 1):
        job = AboConcept(
            FixtureConceptArtist(),
            fixture_explode_inspector,
            lambda request: InventedGame(record or F.fixture_record()),
        )
        context = ConceptContext(
            wish_for(),
            load_taste(INVENTOR_ROOT),
            ToyBlueprint.for_lane("invented-games"),
            round_number,
            Path(tmp) / ("concept-%d" % round_number),
            playtest_rounds=2,
        )
        return job, job(context)

    def test_the_game_record_is_sealed_inside_the_concept_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            _job, images = self.concept_for(tmp)
            directory = images.root / GAME_RECORD_DIRECTORY
            self.assertTrue((directory / GAME_RECORD_FILENAME).is_file())
            self.assertTrue((directory / GAME_CHECK_FILENAME).is_file())
            recorded = json.loads(
                (directory / GAME_CHECK_FILENAME).read_text(encoding="utf-8")
            )
            self.assertTrue(recorded["pass"])
            self.assertEqual(len(recorded["rules_sha256"]), 64)

    def test_the_concept_hash_covers_the_game_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            _job, images = self.concept_for(tmp)
            path = images.root / GAME_RECORD_DIRECTORY / GAME_RECORD_FILENAME
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    '"playtime_min": 20', '"playtime_min": 21'
                ),
                encoding="utf-8",
            )
            # Editing the sealed rules after the concept is sealed invalidates
            # the round, which is what makes Make's seal re-check bite.
            with self.assertRaises(ArtifactError):
                images.assert_current()

    def test_the_exact_rules_are_recoverable_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            _job, images = self.concept_for(tmp)
            recovered = GameRecord.from_root(images.root)
            self.assertEqual(recovered.to_dict(), F.fixture_record().to_dict())
            self.assertEqual(recovered.win.text, F.fixture_record().win.text)

    def test_the_brief_components_are_the_bill(self):
        with tempfile.TemporaryDirectory() as tmp:
            _job, images = self.concept_for(tmp)
            self.assertEqual(
                list(images.brief.component_keys),
                [item.concept_key for item in F.fixture_record().components],
            )
            # And every one of them was drawn.
            self.assertEqual(
                set(images.components), set(images.brief.component_keys)
            )

    def test_a_bill_over_the_concept_cap_fails_with_a_taste_legible_message(self):
        record = F.fixture_record()
        base = record.components[1]
        crowded = record.components + tuple(
            type(base)(
                name="filler_%02d" % index,
                qty=2,
                desc="An extra piece family.",
                form="Square shaft with a notch.",
                dimensions_mm=(14.0, 14.0, 20.0),
                placement="Standing in a board socket.",
                interfaces="Spigot seats into a socket.",
            )
            for index in range(10)
        )
        # The record's own ceiling refuses this before a brief is ever derived,
        # and it says to subtract rather than to describe more carefully.
        with self.assertRaises(GameRecordError) as caught:
            assert_playable_record(
                F.fixture_record(components=crowded), F.FIXTURE_OBJECTIVE
            )
        self.assertIn("complexity-budget", str(caught.exception))


class RefiningRoundTest(unittest.TestCase):
    def test_a_refining_round_revises_the_standing_game(self):
        from inventor_workshop.jobs import Feedback

        with tempfile.TemporaryDirectory() as tmp:
            first = AboConcept(
                FixtureConceptArtist(),
                fixture_explode_inspector,
                lambda request: InventedGame(F.fixture_record()),
            )
            standing = first(
                ConceptContext(
                    wish_for(),
                    load_taste(INVENTOR_ROOT),
                    ToyBlueprint.for_lane("invented-games"),
                    1,
                    Path(tmp) / "concept-1",
                    playtest_rounds=2,
                )
            )

            seen = {}

            def revise(request):
                seen["standing"] = request.standing
                seen["changes"] = request.changes
                return InventedGame(F.fixture_record(playtime_min=25))

            second = AboConcept(
                FixtureConceptArtist(), fixture_explode_inspector, revise
            )
            refined = second(
                ConceptContext(
                    wish_for(),
                    load_taste(INVENTOR_ROOT),
                    ToyBlueprint.for_lane("invented-games"),
                    2,
                    Path(tmp) / "concept-2",
                    feedback=(
                        Feedback(
                            code="sim-forced-turns",
                            area="rules",
                            severity="block",
                            finding="Too many turns offered no real choice.",
                            change="Give the lock marker a second legal placement.",
                            evidence_refs=("game-simulation",),
                            invalidates=("concept", "make", "playtest"),
                        ),
                    ),
                    playtest_rounds=2,
                    previous=standing,
                )
            )
            # The standing game was handed over, not a blank sheet.
            self.assertEqual(seen["standing"].slug, "notchline")
            self.assertIn(
                "Give the lock marker a second legal placement.", seen["changes"]
            )
            self.assertEqual(GameRecord.from_root(refined.root).playtime_min, 25)
            # Research runs once per run; the refining round reuses it.
            self.assertEqual(refined.research_sha256, standing.research_sha256)

    def test_an_unrelated_game_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = AboConcept(
                FixtureConceptArtist(),
                fixture_explode_inspector,
                lambda request: InventedGame(F.fixture_record()),
            )
            standing = first(
                ConceptContext(
                    wish_for(),
                    load_taste(INVENTOR_ROOT),
                    ToyBlueprint.for_lane("invented-games"),
                    1,
                    Path(tmp) / "concept-1",
                    playtest_rounds=2,
                )
            )
            second = AboConcept(
                FixtureConceptArtist(),
                fixture_explode_inspector,
                lambda request: InventedGame(
                    F.fixture_record(slug="something-else", title="Something Else")
                ),
            )
            with self.assertRaises(ContractError) as caught:
                second(
                    ConceptContext(
                        wish_for(),
                        load_taste(INVENTOR_ROOT),
                        ToyBlueprint.for_lane("invented-games"),
                        2,
                        Path(tmp) / "concept-2",
                        playtest_rounds=2,
                        previous=standing,
                    )
                )
            self.assertIn("not a revision", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
