"""What Concept actually asks for, and what it refuses to hand on.

The consistency guarantee lives in the requests: which image is anchored on
which, what each prompt is allowed to say, and what happens when the one image
the component views depend on comes back incomplete. These assert that directly
rather than through the pipeline, because a prompt that quietly stopped naming
its anchor would still produce a plausible-looking concept.
"""

import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop import concept as concept_module
from inventor_workshop.concept import (
    DESIGN_FACTS_HEADING,
    MAX_CONCEPT_REFINE_DEPTH,
    NEUTRAL_PRESENTATION,
    RESEARCH_RULE_FEATURES_RESTATE_OBJECTIVE,
    RESEARCH_RULE_LONE_COMPONENT_RESTATES_ENVELOPE,
    RESEARCH_RULE_SINGLE_COMPONENT_UNDECLARED,
    DefaultConcept,
    assert_researched_breakdown,
    concept_handoff_text,
    derive_brief,
    design_facts_block,
    style_descriptor,
)
from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import (
    CONCEPT_DESCRIPTOR_FILENAME,
    CONCEPT_OVERALL_ROLES,
    ConceptComponent,
    ConceptContext,
    Feedback,
    WaitingFor,
    WishResearch,
    WishResearchFinding,
    WishResearchSource,
)
from inventor_workshop.make import Wish
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint
from tools.concept_fixture import FixtureConceptArtist, fixture_explode_inspector
from tools.wish_research_fixture import FixtureWishResearcher


COMPONENTS = [
    {
        "key": "body",
        "name": "Body",
        "purpose": "Holds the mechanism.",
        "form": "a rounded shell with one flat base",
        "dimensions_mm": [60.0, 60.0, 18.0],
        "placement": "the base of the assembly",
        "interfaces": "receives the cap on its upper rim",
    },
    {
        "key": "cap",
        "name": "Cap",
        "purpose": "Closes the body and carries the grip.",
        "form": "a shallow dome with a knurled rim",
        "dimensions_mm": [58.0, 58.0, 9.0],
        "placement": "on top of the body",
        "interfaces": "snaps onto the body rim",
    },
    {
        "key": "spring",
        "name": "Return spring",
        "purpose": "Returns the mechanism to rest.",
        "form": "a flat printed spiral",
        "dimensions_mm": [40.0, 40.0, 3.0],
        "placement": "inside the body, hidden in every external view",
        "interfaces": "grips the body boss at its centre and the cap at its outer arm",
    },
]


class ConceptGenerationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        inventor = self.root / "inventor"
        inventor.mkdir()
        (inventor / "TASTE.md").write_text(
            "---\n"
            "name: Test Inventor\n"
            "description: Architectural desk objects, 40 mm tall, never twee.\n"
            "---\n"
            "# Taste\n\nArchitectural desk objects.\n",
            encoding="utf-8",
        )
        self.taste = load_taste(inventor)
        self.blueprint = ToyBlueprint.for_lane("moving-machines")
        self.wish = Wish.create(
            "rhythm-top",
            "A delightful desk spinner that reveals a changing beat",
            constraints={
                "envelope_mm": [60.0, 60.0, 30.0],
                "wall_mm": 2.0,
                "components": COMPONENTS,
                "fits": {
                    "target": "four coasters",
                    "ref_mm": [100.0, 100.0, 8.0],
                    "clearance_mm": 0.6,
                },
            },
        )

    def tearDown(self):
        self.temporary.cleanup()

    def context(self, *, round_number=1, feedback=(), previous=None, refine_depth=0):
        return ConceptContext(
            self.wish,
            self.taste,
            self.blueprint,
            round_number,
            (self.root / ("run-%d" % round_number) / "concept").absolute(),
            feedback,
            4,
            previous,
            refine_depth,
        )

    def run_concept(
        self, context=None, artist=None, inspector=None, researcher=None
    ):
        artist = artist if artist is not None else FixtureConceptArtist()
        job = DefaultConcept(
            artist,
            inspector if inspector is not None else fixture_explode_inspector,
            wish_researcher=(
                researcher if researcher is not None else FixtureWishResearcher()
            ),
        )
        return job(context if context is not None else self.context()), artist

    # -- the consistency contract ------------------------------------------

    def test_images_are_produced_in_an_order_that_accumulates_references(self):
        concept, artist = self.run_concept()
        order = [request.role for request in artist.requests]
        self.assertEqual(
            order, ["front", "top", "bottom", "exploded", "body", "cap", "spring"]
        )
        by_role = {request.role: request for request in artist.requests}

        self.assertEqual(by_role["front"].references, ())
        front = concept.root / concept.overall["front"]
        for angle in ("top", "bottom"):
            self.assertEqual(by_role[angle].references, (front,))
        self.assertEqual(
            set(by_role["exploded"].references),
            {front, concept.root / concept.overall["top"], concept.root / concept.overall["bottom"]},
        )
        exploded = concept.root / concept.overall["exploded"]
        for key in ("body", "cap", "spring"):
            self.assertEqual(by_role[key].references, (exploded, front))

    def test_other_overall_views_are_asked_for_as_edits(self):
        _, artist = self.run_concept()
        prompts = artist.prompts()
        for angle in ("top", "bottom"):
            with self.subTest(angle=angle):
                self.assertIn("Reference image 1 is the FRONT VIEW", prompts[angle])
                self.assertIn("the SAME object, unchanged", prompts[angle])
                self.assertIn("only the camera angle changes", prompts[angle])
                self.assertIn("clear %s view" % angle, prompts[angle])

    def test_the_anchor_is_drawn_from_the_brief_alone(self):
        _, artist = self.run_concept()
        front = artist.prompts()["front"]
        self.assertIn("exactly one complete object", front)
        self.assertNotIn("Reference image", front)
        self.assertIn("legible", front)

    def test_the_exploded_view_names_every_component_and_asks_for_no_occlusion(self):
        _, artist = self.run_concept()
        exploded = artist.prompts()["exploded"]
        for item in COMPONENTS:
            self.assertIn(item["key"], exploded)
            self.assertIn(item["name"], exploded)
        self.assertIn("separated along its assembly axes", exploded)
        self.assertIn("wholly visible", exploded)
        self.assertIn("hidden behind, inside, or overlapping another", exploded)
        self.assertIn("Reference images 1, 2, and 3", exploded)

    def test_the_locked_facts_and_presentation_reach_every_prompt(self):
        _, artist = self.run_concept()
        for role, prompt in artist.prompts().items():
            with self.subTest(role=role):
                self.assertIn(DESIGN_FACTS_HEADING, prompt)
                self.assertIn("Holds: four coasters, each 100 x 100 x 8 mm", prompt)
                self.assertIn("Clearance around each held item: 0.6 mm", prompt)
                self.assertIn("Approximate envelope: 60 x 60 x 30 mm", prompt)
                self.assertIn("Wall thickness: 2 mm", prompt)
                self.assertEqual(prompt.count(NEUTRAL_PRESENTATION), 1)

    def test_no_prompt_asks_for_a_caption_in_the_pixels(self):
        _, artist = self.run_concept()
        for role, prompt in artist.prompts().items():
            with self.subTest(role=role):
                self.assertIn("No text, no dimensions, no logos, no watermarks", prompt)
                self.assertNotIn("caption", prompt.casefold())
                self.assertNotIn("label the", prompt.casefold())

    def test_every_prompt_keeps_the_concept_print_only(self):
        _, artist = self.run_concept()
        for role, prompt in artist.prompts().items():
            with self.subTest(role=role):
                self.assertIn(
                    "never depict anything it holds, mounts to, or rests on", prompt
                )

    # -- occlusion: geometry in text, appearance in images -------------------

    def test_a_component_prompt_carries_its_own_specification(self):
        _, artist = self.run_concept()
        prompts = artist.prompts()
        for item in COMPONENTS:
            with self.subTest(component=item["key"]):
                prompt = prompts[item["key"]]
                extent = " x ".join(
                    str(int(value)) for value in item["dimensions_mm"]
                )
                self.assertIn(item["form"], prompt)
                self.assertIn("Bounding dimensions: %s mm" % extent, prompt)
                self.assertIn(item["placement"], prompt)
                self.assertIn(item["interfaces"], prompt)

    def test_no_component_shape_is_read_off_a_view_that_may_hide_it(self):
        _, artist = self.run_concept()
        prompts = artist.prompts()
        for item in COMPONENTS:
            with self.subTest(component=item["key"]):
                prompt = prompts[item["key"]]
                self.assertIn(
                    "Its shape is given here, not read off any view that hides it",
                    prompt,
                )
                self.assertIn(
                    "take the shape from the specification above", prompt
                )
                # Every appearance claim is scoped to the one view that shows
                # the part whole.
                start = 0
                seen = 0
                while True:
                    found = prompt.find("as it appears in", start)
                    if found < 0:
                        break
                    seen += 1
                    self.assertTrue(
                        prompt[found:].startswith(
                            "as it appears in the exploded view"
                        ),
                        prompt[found : found + 80],
                    )
                    start = found + 1
                self.assertEqual(seen, 1)

    def test_a_hidden_component_is_still_drawn_from_its_specification(self):
        concept, artist = self.run_concept()
        self.assertIn("spring", concept.components)
        spring = artist.prompts()["spring"]
        self.assertIn("hidden in every external view", spring)
        self.assertIn("a flat printed spiral", spring)

    # -- the exploded-view completeness check --------------------------------

    def test_a_complete_exploded_view_proceeds(self):
        concept, artist = self.run_concept()
        self.assertEqual(
            [request.role for request in artist.requests].count("exploded"), 1
        )
        self.assertEqual(set(concept.components), {"body", "cap", "spring"})

    def test_an_incomplete_exploded_view_is_regenerated_once(self):
        class OnceIncomplete(FixtureConceptArtist):
            def __call__(self, request):
                if request.role == "exploded" and not self.omit:
                    self.omit = ("spring",)
                    return super().__call__(request)
                self.omit = ()
                return super().__call__(request)

        concept, artist = self.run_concept(artist=OnceIncomplete())
        exploded = [
            request for request in artist.requests if request.role == "exploded"
        ]
        self.assertEqual(len(exploded), 2)
        self.assertIn("must each be visible this time: spring", exploded[1].prompt)
        self.assertEqual(set(concept.components), {"body", "cap", "spring"})

    def test_a_still_incomplete_explode_fails_before_any_component_is_drawn(self):
        artist = FixtureConceptArtist(omit=("spring",))
        with self.assertRaisesRegex(ContractError, "does not separate spring"):
            self.run_concept(artist=artist)
        drawn = [request.role for request in artist.requests]
        self.assertEqual(drawn.count("exploded"), 2)
        for key in ("body", "cap", "spring"):
            self.assertNotIn(key, drawn)

    def test_an_explode_check_naming_an_unknown_part_is_refused(self):
        def confused(image, brief):
            del image, brief
            return ("not-a-component",)

        with self.assertRaisesRegex(ContractError, "which the brief does not"):
            self.run_concept(inspector=confused)

    # -- truthful waiting and partial providers ------------------------------

    def test_concept_waits_when_it_cannot_draw(self):
        with self.assertRaises(WaitingFor) as caught:
            DefaultConcept()(self.context())
        needs = {need.capability: need for need in caught.exception.needs}
        self.assertEqual(
            set(needs),
            {"wish-research", "concept-images", "exploded-view-check"},
        )
        self.assertEqual(needs["concept-images"].job, "concept")
        self.assertIn("provider", needs["concept-images"].instructions)
        self.assertFalse((self.root / "run-1" / "concept").exists())

    def test_concept_waits_when_the_wish_was_never_researched(self):
        with self.assertRaises(WaitingFor) as caught:
            DefaultConcept(FixtureConceptArtist(), fixture_explode_inspector)(
                self.context()
            )
        needs = {need.capability: need for need in caught.exception.needs}
        self.assertEqual(set(needs), {"wish-research"})
        self.assertEqual(needs["wish-research"].job, "concept")
        self.assertIn("research", needs["wish-research"].instructions)
        self.assertFalse((self.root / "run-1" / "concept").exists())

    def test_concept_waits_when_the_explode_cannot_be_checked(self):
        with self.assertRaises(WaitingFor) as caught:
            DefaultConcept(
                FixtureConceptArtist(), wish_researcher=FixtureWishResearcher()
            )(self.context())
        self.assertEqual(
            [need.capability for need in caught.exception.needs],
            ["exploded-view-check"],
        )

    def test_a_partial_provider_fails_rather_than_returning_a_concept(self):
        class Partial(FixtureConceptArtist):
            def __call__(self, request):
                if request.role == "top":
                    return None
                return super().__call__(request)

        artist = Partial()
        with self.assertRaisesRegex(ContractError, "relative path of the top image"):
            self.run_concept(artist=artist)
        self.assertNotIn("exploded", [item.role for item in artist.requests])

    def test_a_provider_returning_an_unsafe_path_is_refused(self):
        class Escaping(FixtureConceptArtist):
            def __call__(self, request):
                super().__call__(request)
                return "../outside.png"

        with self.assertRaises(ContractError):
            self.run_concept(artist=Escaping())

    def test_the_workspace_must_be_fresh_and_empty(self):
        context = self.context()
        context.workspace.mkdir(parents=True)
        (context.workspace / "left-over.png").write_bytes(b"stale\n")
        with self.assertRaisesRegex(ContractError, "fresh and empty"):
            self.run_concept(context=context)

    # -- refine --------------------------------------------------------------

    def feedback(self, change="Narrow the waist and raise the shoulder."):
        return (
            Feedback(
                "silhouette-wrong",
                "form",
                "improve",
                "The silhouette reads as a lamp.",
                change,
                ("playtest.json",),
                ("concept", "make", "playtest"),
            ),
        )

    def test_a_later_round_anchors_on_the_previous_front(self):
        first, _ = self.run_concept()
        context = self.context(
            round_number=2, feedback=self.feedback(), previous=first
        )
        second, artist = self.run_concept(context=context)
        front = artist.requests[0]
        self.assertEqual(front.role, "front")
        self.assertEqual(
            front.references, (first.root / first.overall["front"],)
        )
        self.assertIn("previous front view", front.prompt)
        self.assertIn("Narrow the waist and raise the shoulder.", front.prompt)
        self.assertIn(
            "REQUESTED CHANGES (apply every one, and change nothing else)",
            front.prompt,
        )
        self.assertNotEqual(second.concept_sha256, first.concept_sha256)

    def test_build_only_feedback_leaves_the_design_standing(self):
        first, _ = self.run_concept()
        build_only = (
            Feedback(
                "wall-too-thin",
                "print",
                "improve",
                "The wall tore during the test print.",
                "Thicken the wall where the crank enters.",
                ("print.json",),
                ("make", "playtest"),
            ),
        )
        context = self.context(round_number=2, feedback=build_only, previous=first)
        second, artist = self.run_concept(context=context)
        self.assertEqual(second.brief.to_dict(), first.brief.to_dict())
        self.assertNotIn("REQUESTED CHANGES", artist.prompts()["front"])

    def test_the_edit_list_accumulates_across_rounds(self):
        first, _ = self.run_concept()
        second, _ = self.run_concept(
            context=self.context(
                round_number=2, feedback=self.feedback("Narrow the waist."), previous=first
            )
        )
        third, artist = self.run_concept(
            context=self.context(
                round_number=3,
                feedback=self.feedback("Raise the shoulder."),
                previous=second,
                refine_depth=1,
            )
        )
        front = artist.prompts()["front"]
        self.assertIn("Narrow the waist.", front)
        self.assertIn("Raise the shoulder.", front)
        self.assertEqual(
            [
                item
                for item in third.brief.assumptions
                if item.startswith("Revision: ")
            ],
            ["Revision: Narrow the waist.", "Revision: Raise the shoulder."],
        )

    def test_the_refine_cap_re_anchors_on_the_brief(self):
        first, _ = self.run_concept()
        context = self.context(
            round_number=2,
            feedback=self.feedback(),
            previous=first,
            refine_depth=MAX_CONCEPT_REFINE_DEPTH,
        )
        _, artist = self.run_concept(context=context)
        front = artist.requests[0]
        self.assertEqual(front.references, ())
        self.assertNotIn("previous front view", front.prompt)
        # The corrections still travel, in text, where drift cannot eat them.
        self.assertIn("Narrow the waist and raise the shoulder.", front.prompt)

    # -- labelling -----------------------------------------------------------

    def test_the_concept_root_describes_itself(self):
        concept, _ = self.run_concept()
        descriptor = json.loads(
            (concept.root / CONCEPT_DESCRIPTOR_FILENAME).read_text(encoding="utf-8")
        )
        self.assertIs(descriptor["concept_art"], True)
        self.assertIs(descriptor["provenance"]["valid_as_product_proof"], False)
        self.assertEqual(descriptor["brief"], concept.brief.to_dict())
        self.assertEqual(
            set(descriptor["images"]),
            set(CONCEPT_OVERALL_ROLES) | {"components"},
        )
        self.assertEqual(descriptor["images"]["components"], dict(concept.components))
        for role in CONCEPT_OVERALL_ROLES:
            self.assertEqual(descriptor["images"][role], concept.overall[role])

    def test_filenames_carry_the_role_without_opening_the_file(self):
        concept, _ = self.run_concept()
        for role in CONCEPT_OVERALL_ROLES:
            self.assertEqual(Path(concept.overall[role]).stem, role)
        for key, relative in concept.components.items():
            self.assertTrue(Path(relative).stem.endswith(key))

    def test_the_handoff_names_every_attachment_and_no_others(self):
        concept, _ = self.run_concept()
        text = concept_handoff_text(concept)
        named = [line for line in text.split("\n") if line.startswith("Image ")]
        self.assertEqual(len(named), len(concept.paths()))
        for position, role in enumerate(CONCEPT_OVERALL_ROLES, start=1):
            self.assertIn(
                "Image %d is the %s view (%s)."
                % (position, role, concept.overall[role]),
                text,
            )
        for offset, key in enumerate(sorted(concept.components), start=5):
            self.assertIn("Image %d shows the component %s" % (offset, key), text)
        self.assertIn("they are not a picture of anything that has been built", text)
        self.assertIn("the numbers below govern", text)
        self.assertIn(json.dumps(concept.brief.to_dict()["object"]), text)

    # -- refused breakdowns --------------------------------------------------

    def researched(self, **overrides):
        """A breakdown that satisfies every rule, so one can be broken at a time."""

        fields = {
            "object": "a desk spinner",
            "category": "a hand-operated mechanism",
            "envelope_mm": (60.0, 60.0, 30.0),
            "wall_mm": 2.0,
            "features": ("a weighted rim that changes the beat as it slows",),
            "print": {"orientation": "flat on its largest face", "supports": False},
            "components": (
                ConceptComponent(
                    "base",
                    "Base",
                    "Seats the spinner.",
                    "a squared plinth with a recessed underside",
                    (60.0, 60.0, 12.0),
                    "the lowest part of the assembly",
                    "its rim receives the crown",
                ),
            ),
            "fits": None,
            "findings": None,
            "sources": (),
        }
        fields.update(overrides)
        findings = fields["findings"]
        if findings is None:
            findings = tuple(
                WishResearchFinding(
                    "Research decided %s." % name,
                    name,
                    decided_because="no source stated it",
                )
                for name in (
                    "object",
                    "category",
                    "envelope_mm",
                    "wall_mm",
                    "features",
                    "print",
                )
            ) + (
                WishResearchFinding(
                    "The design prints as one part.",
                    "components",
                    decided_because="the parts do not separate",
                ),
            )
        return WishResearch(
            fields["object"],
            fields["category"],
            fields["envelope_mm"],
            fields["wall_mm"],
            fields["features"],
            fields["print"],
            fields["components"],
            fields["fits"],
            findings,
            fields["sources"],
        )

    def test_a_feature_that_restates_the_objective_is_refused(self):
        with self.assertRaises(ContractError) as caught:
            assert_researched_breakdown(
                self.wish,
                self.researched(
                    features=(
                        "one signature interaction that exists because of this "
                        "Wish: %s" % self.wish.objective,
                    )
                ),
            )
        self.assertIn(RESEARCH_RULE_FEATURES_RESTATE_OBJECTIVE, str(caught.exception))

    def test_a_lone_component_that_restates_the_envelope_is_refused(self):
        placeholder = ConceptComponent(
            "body",
            "Body",
            "Carries the whole design as one printed piece.",
            "a single closed shell following the envelope, with flat faces "
            "where the design meets a surface",
            (60.0, 60.0, 30.0),
            "the whole assembly; there is nothing else to sit beside",
            "none; this design prints as one part",
        )
        with self.assertRaises(ContractError) as caught:
            assert_researched_breakdown(
                self.wish, self.researched(components=(placeholder,))
            )
        self.assertIn(
            RESEARCH_RULE_LONE_COMPONENT_RESTATES_ENVELOPE, str(caught.exception)
        )

    def test_a_single_component_without_a_one_part_finding_is_refused(self):
        findings = tuple(
            WishResearchFinding(
                "Research decided %s." % name,
                name,
                decided_because="no source stated it",
            )
            for name in (
                "object",
                "category",
                "envelope_mm",
                "wall_mm",
                "features",
                "print",
                "components",
            )
        )
        with self.assertRaises(ContractError) as caught:
            assert_researched_breakdown(
                self.wish, self.researched(findings=findings)
            )
        self.assertIn(
            RESEARCH_RULE_SINGLE_COMPONENT_UNDECLARED, str(caught.exception)
        )

    def test_a_breakdown_that_decided_its_facts_is_accepted(self):
        assert_researched_breakdown(self.wish, self.researched())

    # -- brief derivation ----------------------------------------------------

    def bare_context(self, wish=None):
        return ConceptContext(
            wish if wish is not None else Wish.create(
                "bare-top", "A quiet desk object"
            ),
            self.taste,
            self.blueprint,
            1,
            (self.root / "bare" / "concept").absolute(),
            (),
            4,
        )

    def test_a_researched_breakdown_produces_a_brief_stating_its_facts(self):
        context = self.bare_context()
        research = self.researched(
            object="a stepped desk marker",
            envelope_mm=(74.5, 51.0, 26.5),
            wall_mm=1.8,
        )
        design = derive_brief(context, research)
        self.assertEqual(design.object, "a stepped desk marker")
        self.assertEqual(design.envelope_mm, (74.5, 51.0, 26.5))
        self.assertEqual(design.wall_mm, 1.8)
        self.assertEqual(design.features, research.features)
        self.assertEqual(design.component_keys, ("base",))

    def test_every_decided_fact_reaches_the_assumptions_with_its_reason(self):
        design = derive_brief(self.bare_context(), self.researched())
        joined = " ".join(design.assumptions)
        self.assertIn("Decided because no source stated it", joined)
        self.assertNotIn("The Wish did not state", joined)

    def test_a_sourced_fact_is_not_recorded_as_an_assumption(self):
        research = self.researched(
            findings=tuple(
                WishResearchFinding(
                    "Research decided %s." % name,
                    name,
                    decided_because="no source stated it",
                )
                for name in ("object", "category", "wall_mm", "features", "print")
            )
            + (
                WishResearchFinding(
                    "A desk spinner of this class is 60 mm across.",
                    "envelope_mm",
                    ("desk-objects",),
                ),
                WishResearchFinding(
                    "The design prints as one part.",
                    "components",
                    decided_because="the parts do not separate",
                ),
            ),
            sources=(
                WishResearchSource.create(
                    "desk-objects",
                    "https://example.invalid/desk-objects",
                    "Desk object proportions",
                    "Desk spinners of this class measure 60 mm across the rim.",
                    "2026-08-25T00:00:00Z",
                ),
            ),
        )
        design = derive_brief(self.bare_context(), research)
        joined = " ".join(design.assumptions)
        self.assertNotIn("60 mm across", joined)
        self.assertIn("Research decided wall_mm.", joined)

    def test_a_wish_carrying_hand_authored_components_keeps_them(self):
        design = derive_brief(self.context(), self.researched())
        self.assertEqual(design.component_keys, ("body", "cap", "spring"))
        self.assertIn(
            "The Wish stated its own part breakdown", " ".join(design.assumptions)
        )

    def test_no_code_path_yields_the_old_defaults(self):
        design = derive_brief(self.bare_context(), self.researched())
        self.assertNotEqual(design.envelope_mm, (120.0, 120.0, 60.0))
        self.assertNotEqual(design.wall_mm, 2.4)
        self.assertNotIn("signature interaction", " ".join(design.features))
        source = Path(concept_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("_DEFAULT_ENVELOPE_MM", source)
        self.assertNotIn("_DEFAULT_WALL_MM", source)

    def test_a_body_component_appears_only_when_research_decided_it(self):
        design = derive_brief(self.bare_context(), self.researched())
        self.assertNotIn("body", design.component_keys)
        decided = self.researched(
            components=(
                ConceptComponent(
                    "body",
                    "Body",
                    "Carries the mechanism.",
                    "a rounded shell whose rim steps twice toward the base",
                    (60.0, 60.0, 30.0),
                    "the only printed part",
                    "no mating faces; the rim is closed",
                ),
            )
        )
        self.assertEqual(
            derive_brief(self.bare_context(), decided).component_keys, ("body",)
        )

    def test_the_style_descriptor_carries_no_cad_verbs_or_measurements(self):
        style = style_descriptor(self.taste)
        self.assertIn("Test Inventor", style)
        self.assertIn("Architectural desk objects", style)
        self.assertNotIn("40", style)
        self.assertNotIn("mm", style)

    def test_the_design_facts_block_is_empty_without_a_brief(self):
        self.assertEqual(design_facts_block(None), "")


if __name__ == "__main__":
    unittest.main()
