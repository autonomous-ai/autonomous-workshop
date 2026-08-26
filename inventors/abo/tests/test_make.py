"""ABO's Make: the engine it compiles, and the product it seals.

The geometry these checks run over is written by a stand-in generator, not by
the locked CAD skill, because a machine with no CAD toolchain still has to be
able to prove the contracts *around* geometry: that the engine ships inside the
product and is covered by its hash, that the components correspond one-to-one
with the brief's, that a concept image cannot be laundered into the product,
and that a post-Make edit invalidates the revision.

Nothing here is a claim about geometry. Whether a part is solid, fits, or
prints is measured by `mechanical-test` and `print-test`, which refuse an
unmeasured check rather than passing it.
"""

from __future__ import annotations

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
    FIXTURES,
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
from inventor_workshop.errors import ArtifactError, ContractError  # noqa: E402
from inventor_workshop.jobs import (  # noqa: E402
    ConceptContext,
    MakeContext,
    WaitingFor,
)
from inventor_workshop.make import Wish  # noqa: E402
from inventor_workshop.taste import load_taste  # noqa: E402
from inventor_workshop.toys import ToyBlueprint  # noqa: E402
from make import (  # noqa: E402
    AboMake,
    CAD_DIRECTORY,
    CompiledEngine,
    ENGINE_DIRECTORY,
    ENGINE_FILENAME,
    RulesGap,
    assert_engine_plays,
    engine_contract,
    load_engine,
)
from research import InventedGame  # noqa: E402

BLUEPRINT = ToyBlueprint.for_lane("invented-games")
FIXTURE_ENGINE_SOURCE = (FIXTURES / "fixture_engine.py").read_text(encoding="utf-8")


def wish_for() -> Wish:
    return Wish.create(
        "notchline",
        F.FIXTURE_OBJECTIVE,
        constraints={"lane": "invented-games", "audience": "grown-ups-14-plus"},
        context={"inventor_id": "abo"},
    )


def fixture_compiler(record) -> CompiledEngine:
    """Compile Notchline. The reading it had to take is declared, not hidden."""

    return CompiledEngine(
        FIXTURE_ENGINE_SOURCE,
        assumptions=(
            {
                "id": "locked-socket-counts",
                "rule": "win[1]",
                "question": "Does a locked socket add more to a run's total?",
                "chosen": "A lock marker seals and breaks ties, and nothing else.",
                "alternative": "A locked socket counts its notches twice.",
            },
        ),
    )


def fixture_cad_builder(build) -> str:
    """Parametric source for one part, in the spelling the locked skill reads."""

    length, width, height = build.component.dimensions_mm
    return (
        "# %s, built to the brief's millimetres.\n"
        "from build123d import Box, Compound\n\n"
        "LENGTH_MM = %.3f\nWIDTH_MM = %.3f\nHEIGHT_MM = %.3f\n"
        "WALL_MM = %.3f\n\n"
        "body = Box(LENGTH_MM, WIDTH_MM, HEIGHT_MM)\n"
        "result = Compound([body])\n" % (build.key, length, width, height, build.brief.wall_mm)
    )


def fixture_step_generator(directory: Path, keys) -> None:
    """Stand in for the locked skill on a machine with no CAD toolchain."""

    for key in keys:
        (directory / ("%s.step" % key)).write_text(
            "ISO-10303-21;\n/* stand-in for %s */\nEND-ISO-10303-21;\n" % key,
            encoding="utf-8",
        )
        (directory / ("%s.stl" % key)).write_text(
            "solid %s\nendsolid %s\n" % (key, key), encoding="utf-8"
        )


class EngineContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temporary)
        path = Path(self.temporary) / "engine.py"
        path.write_text(FIXTURE_ENGINE_SOURCE, encoding="utf-8")
        self.engine = load_engine(path)

    def test_the_engine_declares_its_contract(self):
        contract = engine_contract(self.engine)
        self.assertEqual(contract["seats_supported"], [2, 2])
        self.assertFalse(contract["hidden_information"])
        self.assertEqual(contract["move_kinds"], ["seat_pillar", "spend_lock"])
        self.assertEqual(len(contract["assumptions"]), 1)

    def test_the_engine_plays_a_game_to_a_terminal_state(self):
        outcome = assert_engine_plays(self.engine, 2, 40)
        self.assertTrue(outcome["started"])
        self.assertTrue(outcome["terminated"])
        self.assertGreater(outcome["turns"], 0)

    def test_it_never_offers_a_move_the_rules_do_not_define(self):
        import random

        rng = random.Random(3)
        state = self.engine.new_game(2, rng)
        kinds = set()
        while not self.engine.is_over(state):
            moves = self.engine.legal_moves(state)
            kinds.update(move[0] for move in moves)
            state = self.engine.apply_move(state, moves[0], rng)
        self.assertLessEqual(kinds, set(self.engine.MOVE_KINDS))

    def test_a_declared_open_game_needs_no_concealment(self):
        # The engine says it holds no hidden information, so the absence of a
        # resampler is the game having nothing to hide.
        from make import assert_hidden_information_holds

        self.assertFalse(self.engine.HIDDEN_INFO)
        assert_hidden_information_holds(self.engine, 2)

    def test_an_engine_missing_a_required_call_is_refused(self):
        source = FIXTURE_ENGINE_SOURCE.replace("def winners(state):", "def _winners(state):")
        path = Path(self.temporary) / "broken.py"
        path.write_text(source, encoding="utf-8")
        with self.assertRaises(ContractError) as caught:
            engine_contract(load_engine(path))
        self.assertIn("winners", str(caught.exception))

    def test_a_hidden_information_engine_without_a_view_is_refused(self):
        source = FIXTURE_ENGINE_SOURCE.replace(
            "HIDDEN_INFO = False", "HIDDEN_INFO = True"
        ).replace("def observation(state, seat):", "def _observation(state, seat):")
        path = Path(self.temporary) / "hidden.py"
        path.write_text(source, encoding="utf-8")
        with self.assertRaises(ContractError) as caught:
            engine_contract(load_engine(path))
        self.assertIn("hidden information", str(caught.exception))

    def test_a_hidden_information_engine_must_hide_and_resample_faithfully(self):
        from make import assert_hidden_information_holds

        # A seat sees its own hand and the count of the other's, never its
        # contents; resampling redeals what the seat cannot see.
        good = (
            "import random\n"
            "PLAYERS = (2, 2)\nMAX_TURNS = 4\nHIDDEN_INFO = True\n"
            "def new_game(n, rng): return {'hands': [[1, 2], [3, 4]], 't': 0}\n"
            "def player_to_move(s): return s['t'] % 2\n"
            "def legal_moves(s): return [('play',)]\n"
            "def apply_move(s, m, rng): return {'hands': s['hands'], 't': s['t'] + 1}\n"
            "def is_over(s): return s['t'] >= 2\n"
            "def scores(s): return [0, 0]\n"
            "def winners(s): return []\n"
            "def observation(s, seat):\n"
            "    other = 1 - seat\n"
            "    return {'mine': list(s['hands'][seat]),\n"
            "            'theirs_count': len(s['hands'][other])}\n"
            "def determinize(s, seat, rng):\n"
            "    other = 1 - seat\n"
            "    hands = [list(h) for h in s['hands']]\n"
            "    hands[other] = [rng.randrange(9) for _ in hands[other]]\n"
            "    return {'hands': hands, 't': s['t']}\n"
        )
        path = Path(self.temporary) / "hidden_ok.py"
        path.write_text(good, encoding="utf-8")
        engine = load_engine(path)
        contract = engine_contract(engine)
        self.assertTrue(contract["hidden_information"])
        assert_hidden_information_holds(engine, 2)
        # The full state is not reachable from what a seat is shown.
        view = engine.observation(engine.new_game(2, __import__("random").Random(0)), 0)
        self.assertNotIn("hands", view)

    def test_a_resampler_that_changes_the_seats_own_view_is_refused(self):
        from make import assert_hidden_information_holds

        bad = (
            "PLAYERS = (2, 2)\nMAX_TURNS = 4\nHIDDEN_INFO = True\n"
            "def new_game(n, rng): return {'hands': [[1, 2], [3, 4]], 't': 0}\n"
            "def player_to_move(s): return 0\n"
            "def legal_moves(s): return [('play',)]\n"
            "def apply_move(s, m, rng): return s\n"
            "def is_over(s): return True\n"
            "def scores(s): return [0, 0]\n"
            "def winners(s): return []\n"
            "def observation(s, seat): return {'mine': list(s['hands'][seat])}\n"
            "def determinize(s, seat, rng):\n"
            "    return {'hands': [[9, 9], [9, 9]], 't': s['t']}\n"
        )
        path = Path(self.temporary) / "hidden_bad.py"
        path.write_text(bad, encoding="utf-8")
        with self.assertRaises(ContractError) as caught:
            assert_hidden_information_holds(load_engine(path), 2)
        self.assertIn("changed what that seat may see", str(caught.exception))

    def test_a_game_that_cannot_terminate_is_a_finding_against_the_rules(self):
        # Always a legal move, never an ending: the rules describe a game that
        # cannot be played to a conclusion.
        source = (
            "PLAYERS = (2, 2)\nMAX_TURNS = 12\nHIDDEN_INFO = False\n"
            "def new_game(n, rng): return {'t': 0}\n"
            "def player_to_move(s): return s['t'] % 2\n"
            "def legal_moves(s): return [('wait',)]\n"
            "def apply_move(s, m, rng): return {'t': s['t'] + 1}\n"
            "def is_over(s): return False\n"
            "def scores(s): return [0, 0]\n"
            "def winners(s): return []\n"
        )
        path = Path(self.temporary) / "endless.py"
        path.write_text(source, encoding="utf-8")
        with self.assertRaises(ContractError) as caught:
            assert_engine_plays(load_engine(path), 2, 12)
        message = str(caught.exception)
        self.assertIn("did not terminate", message)
        self.assertIn("not a cap to raise", message)

    def test_a_game_that_cannot_be_started_is_a_finding_against_the_rules(self):
        source = (
            "PLAYERS = (2, 2)\nMAX_TURNS = 12\nHIDDEN_INFO = False\n"
            "class Undefined(Exception): pass\n"
            "def new_game(n, rng): raise Undefined('setup never says where the "
            "first pillar goes')\n"
            "def player_to_move(s): return 0\n"
            "def legal_moves(s): return []\n"
            "def apply_move(s, m, rng): return s\n"
            "def is_over(s): return True\n"
            "def scores(s): return [0, 0]\n"
            "def winners(s): return []\n"
        )
        path = Path(self.temporary) / "unstartable.py"
        path.write_text(source, encoding="utf-8")
        with self.assertRaises(ContractError) as caught:
            assert_engine_plays(load_engine(path), 2, 12)
        self.assertIn("cannot be started", str(caught.exception))

    def test_a_dead_end_with_no_ending_is_a_finding_against_the_rules(self):
        source = (
            "PLAYERS = (2, 2)\nMAX_TURNS = 12\nHIDDEN_INFO = False\n"
            "def new_game(n, rng): return {'t': 0}\n"
            "def player_to_move(s): return 0\n"
            "def legal_moves(s): return [] if s['t'] else [('go',)]\n"
            "def apply_move(s, m, rng): return {'t': 1}\n"
            "def is_over(s): return False\n"
            "def scores(s): return [0, 0]\n"
            "def winners(s): return []\n"
        )
        path = Path(self.temporary) / "deadend.py"
        path.write_text(source, encoding="utf-8")
        with self.assertRaises(ContractError) as caught:
            assert_engine_plays(load_engine(path), 2, 12)
        self.assertIn("no legal move and no ending", str(caught.exception))


class MakeTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temporary)
        self.wish = wish_for()
        self.taste = load_taste(INVENTOR_ROOT)
        concept_job = AboConcept(
            FixtureConceptArtist(),
            fixture_explode_inspector,
            lambda request: InventedGame(F.fixture_record()),
        )
        self.concept = concept_job(
            ConceptContext(
                self.wish,
                self.taste,
                BLUEPRINT,
                1,
                Path(self.temporary) / "concept-1",
                playtest_rounds=2,
            )
        )

    def make_context(self, name: str = "make-1") -> MakeContext:
        return MakeContext(
            self.wish,
            self.taste,
            BLUEPRINT,
            1,
            Path(self.temporary) / name,
            playtest_rounds=2,
            concept_images=self.concept,
        )

    def build(self, **overrides):
        job = AboMake(
            overrides.pop("engine_compiler", fixture_compiler),
            overrides.pop("cad_builder", fixture_cad_builder),
            overrides.pop("step_generator", fixture_step_generator),
        )
        return job(self.make_context(overrides.pop("workspace", "make-1")))

    # -- what Make produces ---------------------------------------------

    def test_the_engine_ships_inside_the_product_and_the_hash_covers_it(self):
        made = self.build()
        engine_path = made.artifact_root / ENGINE_DIRECTORY / ENGINE_FILENAME
        self.assertTrue(engine_path.is_file())
        covered = {entry.path for entry in made.artifact_manifest.entries}
        self.assertIn("%s/%s" % (ENGINE_DIRECTORY, ENGINE_FILENAME), covered)
        # And editing it invalidates the revision.
        engine_path.write_text(
            engine_path.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8"
        )
        with self.assertRaises(ArtifactError):
            made.assert_current()

    def test_a_fixture_game_plays_to_a_terminal_state_through_the_shipped_engine(self):
        made = self.build()
        engine = load_engine(made.artifact_root / ENGINE_DIRECTORY / ENGINE_FILENAME)
        outcome = assert_engine_plays(engine, 2, engine.MAX_TURNS)
        self.assertTrue(outcome["terminated"])

    def test_the_products_components_match_the_concepts_one_to_one(self):
        made = self.build()
        self.assertEqual(
            sorted(made.product["components"]),
            sorted(self.concept.brief.component_keys),
        )
        # The Workshop's own adherence check agrees.
        from inventor_workshop.workshop import _assert_product_follows_concept

        _assert_product_follows_concept(self.concept, made)

    def test_every_brief_component_has_cad_source_and_step(self):
        made = self.build()
        for key in self.concept.brief.component_keys:
            entry = made.product["cad"][key]
            self.assertTrue((made.artifact_root / entry["source"]).is_file())
            self.assertTrue((made.artifact_root / entry["step"]).is_file())
            # A mesh only ever exists behind a STEP artifact.
            self.assertIn("mesh", entry)

    def test_geometry_is_traceable_to_the_brief_facts_it_was_built_from(self):
        import json

        made = self.build()
        facts = json.loads(
            (
                made.artifact_root / made.product["cad"]["pillar-high"]["facts"]
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            facts["dimensions_mm"],
            list(self.concept.brief.component("pillar-high").dimensions_mm),
        )
        self.assertEqual(facts["wall_mm"], self.concept.brief.wall_mm)
        self.assertEqual(facts["envelope_mm"], list(self.concept.brief.envelope_mm))

    def test_the_numbers_govern_the_geometry(self):
        made = self.build()
        source = (
            made.artifact_root / made.product["cad"]["board-frame"]["source"]
        ).read_text(encoding="utf-8")
        length, width, height = self.concept.brief.component("board-frame").dimensions_mm
        self.assertIn("LENGTH_MM = %.3f" % length, source)
        self.assertIn("HEIGHT_MM = %.3f" % height, source)

    def test_a_declared_assumption_is_recorded_in_full(self):
        made = self.build()
        assumptions = made.product["engine_contract"]["assumptions"]
        self.assertEqual(len(assumptions), 1)
        entry = assumptions[0]
        for field in ("id", "rule", "question", "chosen", "alternative"):
            self.assertTrue(entry[field].strip(), field)
        self.assertEqual(entry["rule"], "win[1]")

    # -- what Make refuses ----------------------------------------------

    def test_a_silent_rule_refuses_and_names_it(self):
        def silent(record):
            raise RulesGap("turn[2]", "may a locked socket be locked again?")

        with self.assertRaises(ContractError) as caught:
            self.build(engine_compiler=silent)
        message = str(caught.exception)
        self.assertIn("turn[2]", message)
        self.assertIn("finding against the rules", message)
        self.assertIn("never invents a rule", message)

    def test_an_assumption_about_a_rule_the_game_does_not_have_is_refused(self):
        source = FIXTURE_ENGINE_SOURCE.replace('"rule": "win[1]"', '"rule": "end[9]"')
        with self.assertRaises(ContractError) as caught:
            self.build(engine_compiler=lambda record: CompiledEngine(source))
        self.assertIn("not a rule this game has", str(caught.exception))

    def test_an_assumption_the_engine_does_not_carry_is_refused(self):
        stripped = FIXTURE_ENGINE_SOURCE.replace("ASSUMPTIONS = [", "ASSUMPTIONS = []\n_UNUSED = [")
        with self.assertRaises(ContractError) as caught:
            self.build(
                engine_compiler=lambda record: CompiledEngine(
                    stripped, assumptions=fixture_compiler(record).assumptions
                )
            )
        self.assertIn("a reading Playtest cannot find", str(caught.exception))

    def test_an_extra_component_in_the_product_is_refused(self):
        from inventor_workshop.workshop import _assert_product_follows_concept

        made = self.build()
        product = dict(made.product)
        product["components"] = list(product["components"]) + ["not-in-the-brief"]
        from inventor_workshop.jobs import Made

        widened = Made(made.artifact_root, made.artifact_manifest, product)
        with self.assertRaises(ContractError) as caught:
            _assert_product_follows_concept(self.concept, widened)
        self.assertIn("not-in-the-brief", str(caught.exception))

    def test_an_omitted_component_is_refused(self):
        from inventor_workshop.jobs import Made
        from inventor_workshop.workshop import _assert_product_follows_concept

        made = self.build()
        product = dict(made.product)
        product["components"] = list(product["components"])[:-1]
        narrowed = Made(made.artifact_root, made.artifact_manifest, product)
        with self.assertRaises(ContractError) as caught:
            _assert_product_follows_concept(self.concept, narrowed)
        self.assertIn("omitted", str(caught.exception))

    def test_a_concept_image_copied_into_the_product_is_refused(self):
        job = AboMake(fixture_compiler, fixture_cad_builder, fixture_step_generator)
        context = self.make_context("make-pixels")

        original = job._build_cad

        def build_and_smuggle(root, brief, record):
            outcome = original(root, brief, record)
            source = self.concept.root / self.concept.overall["front"]
            (root / CAD_DIRECTORY / "front.png").write_bytes(source.read_bytes())
            return outcome

        job._build_cad = build_and_smuggle
        with self.assertRaises(ContractError) as caught:
            job(context)
        self.assertIn("concept image bytes", str(caught.exception))

    def test_a_post_make_edit_invalidates_the_revision(self):
        made = self.build()
        target = made.artifact_root / made.product["cad"]["marker-lock"]["source"]
        target.write_text(
            target.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8"
        )
        with self.assertRaises(ArtifactError):
            made.assert_current()

    def test_an_edited_concept_fails_the_seal_re_check(self):
        path = (
            self.concept.root / "game" / "idea.json"
        )
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                '"playtime_min": 20', '"playtime_min": 26'
            ),
            encoding="utf-8",
        )
        # The rules changed while Make was about to run; the round fails.
        with self.assertRaises(ArtifactError):
            self.build(workspace="make-stale")

    # -- what Make waits for --------------------------------------------

    def test_no_engine_compiler_parks_the_run(self):
        job = AboMake(None, fixture_cad_builder, fixture_step_generator)
        with self.assertRaises(WaitingFor) as caught:
            job(self.make_context("make-no-engine"))
        self.assertIn(
            "rules-engine-compiler",
            [need.capability for need in caught.exception.needs],
        )

    def test_no_cad_builder_parks_the_run(self):
        job = AboMake(fixture_compiler, None, fixture_step_generator)
        with self.assertRaises(WaitingFor) as caught:
            job(self.make_context("make-no-cad"))
        self.assertIn(
            "step-first-cad-builder",
            [need.capability for need in caught.exception.needs],
        )

    def test_a_generator_that_writes_no_step_is_refused(self):
        with self.assertRaises(ContractError) as caught:
            self.build(
                step_generator=lambda directory, keys: None,
                workspace="make-no-step",
            )
        self.assertIn("no STEP artifact", str(caught.exception))

    def test_cad_source_the_locked_skill_would_misread_is_refused(self):
        from cad_compat import CadCompatibilityError

        with self.assertRaises(CadCompatibilityError):
            self.build(
                cad_builder=lambda build: "result = assembly.compound()\n",
                workspace="make-bad-cad",
            )


if __name__ == "__main__":
    unittest.main()
