"""The six-job loop, end to end, with the Concept boundary under test.

Concept sits between Wish and Make, so a run either carries a decided design
into the build or stops before it. These walk the whole pipeline and then press
on the two places the design could quietly stop being binding: bytes that move
while Make is running, and concept pixels trying to travel onward as proof.
"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.concept import DefaultConcept
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.errors import ArtifactError, ContractError
from inventor_workshop.instructions import DefaultInstructions
from inventor_workshop.jobs import (
    CONCEPT_OVERALL_ROLES,
    Delivered,
    Feedback,
    Made,
    Playtested,
)
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult, Receipt
from inventor_workshop.playtest import Playtest
from inventor_workshop.runtime import Runtime
from inventor_workshop.workshop import Workshop, WorkshopTools
from tools.concept_fixture import FixtureConceptArtist, fixture_explode_inspector


CONFIG_SHA256 = "c" * 64
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
        "purpose": "Closes the body.",
        "form": "a shallow dome with a knurled rim",
        "dimensions_mm": [58.0, 58.0, 9.0],
        "placement": "on top of the body",
        "interfaces": "snaps onto the body rim",
    },
]


class ConceptPipelineTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.inventor = self.root / "inventor"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "---\n"
            "name: Test Inventor\n"
            "description: Architectural desk objects, never twee.\n"
            "---\n"
            "# Taste\n\nArchitectural desk objects.\n",
            encoding="utf-8",
        )
        self.runtime = self.root / "runtime"
        self.seen = []
        self.sealed_instructions = []

    def tearDown(self):
        self.temporary.cleanup()

    def wish(self, product_id="rhythm-top"):
        return Wish.create(
            product_id,
            "A delightful desk spinner that reveals a changing beat",
            constraints={
                "envelope_mm": [60.0, 60.0, 30.0],
                "wall_mm": 2.0,
                "components": COMPONENTS,
            },
        )

    def concept_job(self):
        return DefaultConcept(FixtureConceptArtist(), fixture_explode_inspector)

    def make_job(self, context):
        self.seen.append(context)
        artifact = context.workspace / "artifact"
        artifact.mkdir(parents=True)
        (artifact / "toy.step").write_text(
            "round %d\n" % context.round, encoding="utf-8"
        )
        return Made.from_root(
            artifact,
            {
                "title": "Rhythm Top",
                "summary": "A pocket top that reveals a changing beat.",
                "lane": context.blueprint.lane,
                "instructions": "Spin, listen, repeat.",
                "components": [
                    item.name for item in context.concept_images.brief.components
                ],
                "limitations": ["Fixture evidence is not a physical print."],
            },
        )

    def _playtest(self, context, *, passed, change="Narrow the waist."):
        context.workspace.mkdir(parents=True)
        results = []
        for capability in context.blueprint.required_capabilities("playtest"):
            evidence_path = context.workspace / (capability + ".json")
            evidence_path.write_text(
                '{"capability":"%s"}\n' % capability, encoding="utf-8"
            )
            results.append(
                PlaytestResult.create(
                    capability,
                    passed,
                    context.made.artifact_sha256,
                    {
                        "evidence_class": "ai-simulation",
                        "agent_roles": ["optimizing-player", "adversarial-breaker"],
                        "claims": ["Synthetic contract evidence."],
                    },
                    "workshop-contract-fixture",
                    "1.0.0",
                    CONFIG_SHA256,
                    evidence_path.name,
                    hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                )
            )
        feedback = ()
        if not passed:
            feedback = (
                Feedback(
                    "silhouette-wrong",
                    "form",
                    "improve",
                    "The silhouette reads as a lamp.",
                    change,
                    ("simulation.json",),
                    ("concept", "make", "playtest"),
                ),
            )
        return Playtested(
            Playtest(
                context.made.artifact_manifest,
                tuple(results),
                evidence_manifest=build_artifact_manifest(
                    context.workspace, created_at="content-addressed"
                ),
            ),
            feedback,
        )

    def passing_playtest(self, context):
        return self._playtest(context, passed=True)

    def second_round_playtest(self, context):
        return self._playtest(context, passed=context.round >= 2)

    def site_writer(self, context, sealed_root, sealed_manifest):
        self.sealed_instructions.append(Path(sealed_root))
        return Receipt(
            pack_sha256="f" * 64,
            artifact_sha256=context.made.artifact_sha256,
            design_id="design-" + context.wish.product_id,
            slug=context.wish.product_id,
            owner_id="owner-test",
            root_id="design-" + context.wish.product_id,
            current_history_id="history-1",
            published_history_id="history-1",
            status="public",
            project_url=(
                "https://www.autonomous.ai/factory/product/" + context.wish.product_id
            ),
            observed_at="2026-08-23T12:00:00+00:00",
            listing_active=True,
            listing_price_cents=3500,
            listing_currency="USD",
            listing_sku="TEST-001",
            details={"instructions_sha256": sealed_manifest.artifact_sha256},
        )

    @staticmethod
    def fulfiller(context):
        return Delivered(
            context.made.artifact_sha256,
            context.instructions.instructions_sha256,
            "USPS",
            "Priority Mail",
            "9400100000000000000000",
            "handed-off",
            "2026-08-23T12:00:00+00:00",
            {
                "print_receipt": {"fixture": "print"},
                "qa_receipt": {"fixture": "qa"},
                "packing_receipt": {"fixture": "packing"},
                "carrier_receipt": {"fixture": "handoff"},
            },
        )

    def workshop(
        self,
        *,
        concept=True,
        make=None,
        playtest=None,
        runtime=None,
    ):
        return Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job() if concept else None,
                make=make or self.make_job,
                playtest=playtest or self.passing_playtest,
                instructions=DefaultInstructions(site_writer=self.site_writer),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=runtime or self.runtime,
        )

    # -- 5.1 ------------------------------------------------------------------

    def test_a_run_walks_wish_concept_make_playtest_instructions_deliver(self):
        wish = self.wish()
        result = self.workshop().run(wish, playtest_rounds=2)
        self.assertEqual((result.status, result.job, result.round), ("delivered", "deliver", 1))
        self.assertEqual(len(result.concept_sha256), 64)
        self.assertEqual(result.to_dict()["concept_sha256"], result.concept_sha256)

        self.assertEqual(len(self.seen), 1)
        make_context = self.seen[0]
        concept = make_context.concept_images
        self.assertIsNotNone(concept)
        self.assertEqual(concept.round, make_context.round)
        self.assertEqual(concept.concept_sha256, result.concept_sha256)
        self.assertEqual(set(concept.overall), set(CONCEPT_OVERALL_ROLES))
        self.assertEqual(set(concept.components), {"body", "cap"})
        self.assertIn(
            "round-001/concept", concept.root.as_posix()
        )

        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain(wish.product_id))
        self.assertEqual(
            [event["to_stage"] for event in state.events(wish.product_id)],
            [
                "wish",
                "concept",
                "make",
                "playtest",
                "instructions",
                "deliver",
                "deliver",
            ],
        )
        recorded = [
            event["payload"].get("concept_sha256")
            for event in state.events(wish.product_id)
            if event["to_stage"] == "make"
        ]
        self.assertEqual(recorded, [result.concept_sha256])

    # -- 5.2 ------------------------------------------------------------------

    def test_a_run_with_no_concept_provider_parks_before_make(self):
        called = []

        def forbidden_make(context):
            called.append(context)
            raise AssertionError("Make ran without a decided design")

        wish = self.wish("undrawn-top")
        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                make=forbidden_make,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(site_writer=self.site_writer),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        ).run(wish, playtest_rounds=2)
        self.assertEqual((result.status, result.job, result.round), ("waiting", "concept", 1))
        self.assertIn("concept-images", [need.capability for need in result.needs])
        self.assertTrue(all(need.job == "concept" for need in result.needs))
        self.assertIsNone(result.concept_sha256)
        self.assertEqual(called, [])
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain(wish.product_id))
        self.assertEqual(state.get_product(wish.product_id)["stage"], "concept")

    def test_default_concept_with_no_artist_parks_the_run(self):
        wish = self.wish("no-artist")
        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=DefaultConcept(),
                make=self.make_job,
                playtest=self.passing_playtest,
            ),
            runtime_root=self.runtime,
        ).run(wish, playtest_rounds=1)
        self.assertEqual((result.status, result.job), ("waiting", "concept"))
        self.assertEqual(
            {need.capability for need in result.needs},
            {"concept-images", "exploded-view-check"},
        )

    # -- 5.3 ------------------------------------------------------------------

    def test_design_feedback_reaches_the_next_rounds_concept(self):
        wish = self.wish("revised-top")
        result = self.workshop(playtest=self.second_round_playtest).run(
            wish, playtest_rounds=3
        )
        self.assertEqual((result.status, result.round), ("delivered", 2))
        self.assertEqual(len(self.seen), 2)
        first, second = (item.concept_images for item in self.seen)
        self.assertNotEqual(second.concept_sha256, first.concept_sha256)
        self.assertEqual(
            [
                item
                for item in second.brief.assumptions
                if item.startswith("Revision: ")
            ],
            ["Revision: Narrow the waist."],
        )
        # The parts the feedback never mentioned are still the same design.
        self.assertEqual(second.brief.component_keys, first.brief.component_keys)
        self.assertEqual(second.brief.envelope_mm, first.brief.envelope_mm)
        self.assertEqual(second.round, 2)
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertEqual(
            [event["to_stage"] for event in state.events(wish.product_id)],
            [
                "wish",
                "concept",
                "make",
                "playtest",
                "concept",
                "make",
                "playtest",
                "instructions",
                "deliver",
                "deliver",
            ],
        )

    # -- 5.4 ------------------------------------------------------------------

    def test_a_concept_that_moves_while_make_runs_fails_the_round(self):
        def tampering_make(context):
            made = self.make_job(context)
            image = (
                context.concept_images.root
                / context.concept_images.overall["front"]
            )
            image.write_bytes(b"a different design\n")
            return made

        with self.assertRaises(ArtifactError):
            self.workshop(make=tampering_make).run(self.wish("moved-top"), playtest_rounds=1)

    def test_a_product_contradicting_the_brief_components_is_refused(self):
        def wrong_parts_make(context):
            artifact = context.workspace / "artifact"
            artifact.mkdir(parents=True)
            (artifact / "toy.step").write_text("one part\n", encoding="utf-8")
            return Made.from_root(
                artifact,
                {
                    "title": "Rhythm Top",
                    "summary": "A pocket top.",
                    "lane": context.blueprint.lane,
                    "components": ["Body"],
                },
            )

        with self.assertRaisesRegex(ContractError, "omitted the concept's components"):
            self.workshop(make=wrong_parts_make).run(
                self.wish("wrong-parts"), playtest_rounds=1
            )

    # -- 5.5 ------------------------------------------------------------------

    def test_instructions_refuses_a_media_provider_serving_concept_art(self):
        """Concept art cannot be wired in as page media, because nothing can.

        Instructions no longer owns generated page media at all — Factory does.
        The refusal lands at construction, so a stale integration handing over
        the concept's own images fails before a run can start.
        """

        def concept_paths_as_media(context):
            return context.concept_images.paths()

        with self.assertRaisesRegex(ContractError, "media_maker is retired"):
            DefaultInstructions(
                site_writer=self.site_writer, media_maker=concept_paths_as_media
            )

    def test_the_sealed_instructions_facts_declare_no_creator_media(self):
        result = self.workshop().run(self.wish("facts-only"), playtest_rounds=1)
        self.assertEqual(result.status, "delivered")

        self.assertEqual(len(self.sealed_instructions), 1)
        facts = json.loads(
            (self.sealed_instructions[0] / "product.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("images", facts)
        for role in CONCEPT_OVERALL_ROLES:
            self.assertNotIn(role, facts)
        self.assertEqual(facts["factory_enrichment"]["media_owner"], "factory")
        self.assertEqual(facts["factory_enrichment"]["copy_owner"], "factory")

    # -- 5.5a -----------------------------------------------------------------

    def test_a_product_carrying_concept_pixels_is_refused(self):
        def copying_make(context):
            # A faithful build: the geometry follows the concept exactly, and
            # the substitution would look entirely reasonable.
            made_context_concept = context.concept_images
            artifact = context.workspace / "artifact"
            (artifact / "images").mkdir(parents=True)
            (artifact / "toy.step").write_text("round 1\n", encoding="utf-8")
            (artifact / "images" / "hero.png").write_bytes(
                (
                    made_context_concept.root
                    / made_context_concept.overall["front"]
                ).read_bytes()
            )
            return Made.from_root(
                artifact,
                {
                    "title": "Rhythm Top",
                    "summary": "A pocket top.",
                    "lane": context.blueprint.lane,
                    "components": [
                        item.name for item in made_context_concept.brief.components
                    ],
                },
            )

        with self.assertRaisesRegex(ContractError, "concept image bytes"):
            self.workshop(make=copying_make).run(
                self.wish("copied-pixels"), playtest_rounds=1
            )

    def test_no_concept_pixels_reach_the_sealed_instructions_tree(self):
        """The concept's bytes stop at Make; nothing carries them onward.

        Make is the boundary that refuses copied pixels, so by Instructions the
        sealed tree should hold none of them. Checking the sealed bytes directly
        keeps that end-to-end rather than trusting the earlier refusal.
        """

        result = self.workshop().run(self.wish("no-concept-pixels"), playtest_rounds=1)
        self.assertEqual(result.status, "delivered")

        forbidden = self.seen[0].concept_images.image_digests()
        self.assertTrue(forbidden)
        sealed_root = self.sealed_instructions[0]
        for path in sorted(sealed_root.rglob("*")):
            if not path.is_file():
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertNotIn(digest, forbidden, path.relative_to(sealed_root).as_posix())

    def test_building_faithfully_without_copying_pixels_is_accepted(self):
        result = self.workshop().run(self.wish("faithful-top"), playtest_rounds=1)
        self.assertEqual(result.status, "delivered")


if __name__ == "__main__":
    unittest.main()
