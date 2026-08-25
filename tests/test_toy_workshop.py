import dataclasses
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.concept import DefaultConcept
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.instructions import DefaultInstructions
from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import (
    CustomerReview,
    Delivered,
    DerivedWish,
    Feedback,
    Made,
    Need,
    Playtested,
    WaitingFor,
    wish_sha256,
)
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult, Receipt
from inventor_workshop.playtest import Playtest
from inventor_workshop.runtime import Runtime
from inventor_workshop.workshop import Workshop, WorkshopTools
from tools.concept_fixture import FixtureConceptArtist, fixture_explode_inspector
from tools.wish_research_fixture import FixtureWishResearcher


CONFIG_SHA256 = "c" * 64


class ToyWorkshopTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.inventor = self.root / "inventor"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "---\n"
            "name: Test Inventor\n"
            "description: Small playthings with one surprising interaction.\n"
            "---\n"
            "# Taste\n\n"
            "Small playthings with one surprising interaction.\n",
            encoding="utf-8",
        )
        self.runtime = self.root / "runtime"

    def tearDown(self):
        self.temporary.cleanup()

    concept_job = staticmethod(
        DefaultConcept(
            FixtureConceptArtist(),
            fixture_explode_inspector,
            wish_researcher=FixtureWishResearcher(),
        )
    )

    @staticmethod
    def make_job(context):
        artifact = context.workspace / "artifact"
        artifact.mkdir(parents=True)
        (artifact / "toy.step").write_text(
            "round %d\n" % context.round, encoding="utf-8"
        )
        (artifact / "instructions.md").write_text(
            "Spin it and discover the hidden rhythm.\n", encoding="utf-8"
        )
        # Make follows the concept: the parts were decided before geometry.
        components = ["one spinning top"]
        if context.concept_images is not None:
            components = [
                component.name
                for component in context.concept_images.brief.components
            ]
        return Made.from_root(
            artifact,
            {
                "title": "Rhythm Top",
                "summary": "A pocket top that reveals a changing beat.",
                "lane": context.blueprint.lane,
                "instructions": "Spin, listen, and try to repeat the rhythm.",
                "components": components,
                "limitations": ["Fixture evidence is not a physical print."],
            },
        )

    @staticmethod
    def _playtest(
        context, *, passed, valid_invented=False, ai_simulation=True
    ):
        context.workspace.mkdir(parents=True)
        results = []
        for capability in context.blueprint.required_capabilities("playtest"):
            evidence_path = context.workspace / (capability + ".json")
            evidence_path.write_text(
                '{"capability":"%s","passed":%s}\n'
                % (capability, str(passed).lower()),
                encoding="utf-8",
            )
            evidence = {
                "evidence_class": (
                    "ai-simulation" if ai_simulation else "deterministic-fixture"
                ),
                "agent_roles": ["optimizing-player", "adversarial-breaker"],
                "claims": ["Synthetic contract evidence for %s." % capability],
            }
            if valid_invented and capability == "game-simulation":
                evidence = {
                    "evidence_class": "ai-simulation",
                    "completed_games": 1_000,
                    "executable": True,
                    "player_styles": [
                        "optimizing",
                        "social",
                        "exploratory",
                        "adversarial",
                    ],
                }
            results.append(
                PlaytestResult.create(
                    capability,
                    passed,
                    context.made.artifact_sha256,
                    evidence,
                    "workshop-contract-fixture",
                    "1.0.0",
                    CONFIG_SHA256,
                    evidence_path.name,
                    hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                )
            )
        evidence_manifest = build_artifact_manifest(
            context.workspace, created_at="content-addressed"
        )
        feedback = ()
        if not passed:
            feedback = (
                Feedback(
                    "cycle-too-short",
                    "mechanics",
                    "improve",
                    "The first rhythm ends too quickly.",
                    "Add a second beat before the mechanism resets.",
                    ("simulation.json",),
                ),
            )
        return Playtested(
            Playtest(
                context.made.artifact_manifest,
                tuple(results),
                evidence_manifest=evidence_manifest,
            ),
            feedback,
        )

    @classmethod
    def playtest_job(cls, context):
        return cls._playtest(context, passed=context.round >= 2)

    @classmethod
    def passing_playtest(cls, context):
        return cls._playtest(context, passed=True)

    @classmethod
    def passing_invented_playtest(cls, context):
        return cls._playtest(context, passed=True, valid_invented=True)

    @staticmethod
    def site_writer(context, sealed_root, sealed_manifest):
        del sealed_root
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
                "https://www.autonomous.ai/factory/product/"
                + context.wish.product_id
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

    def complete_tools(self, playtest=None):
        return WorkshopTools(
            concept=self.concept_job,
            make=self.make_job,
            playtest=playtest or self.playtest_job,
            instructions=DefaultInstructions(site_writer=self.site_writer),
            deliver=DefaultDeliver(self.fulfiller),
        )

    def test_taste_only_inventor_runs_shared_feedback_loop_to_deliver(self):
        workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(),
            runtime_root=self.runtime,
        )
        self.assertEqual(workshop.customization_level, "taste-only")
        result = workshop.run(Wish.create("rhythm-top", "A delightful desk spinner"))
        self.assertEqual((result.status, result.job, result.round), ("delivered", "deliver", 2))
        self.assertEqual(result.playtest_rounds, 4)
        self.assertIsNotNone(result.delivery)
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain("rhythm-top"))
        transitions = [event["to_stage"] for event in state.events("rhythm-top")]
        self.assertEqual(
            transitions,
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
        self.assertEqual(len(result.concept_sha256), 64)

    def test_resume_instructions_uses_checkpoint_without_repeating_make_or_playtest(self):
        calls = {"make": 0, "playtest": 0, "site": 0}

        def counted_make(context):
            calls["make"] += 1
            return self.make_job(context)

        def counted_playtest(context):
            calls["playtest"] += 1
            return self.passing_playtest(context)

        def counted_site(context, root, manifest):
            calls["site"] += 1
            return self.site_writer(context, root, manifest)

        wish = Wish.create("resumable-top", "A top whose page can resume")
        waiting_workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job,
                make=counted_make,
                playtest=counted_playtest,
                instructions=DefaultInstructions(),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        )
        waiting = waiting_workshop.run(wish, playtest_rounds=3)
        self.assertEqual((waiting.status, waiting.job), ("waiting", "instructions"))
        self.assertEqual(calls, {"make": 1, "playtest": 1, "site": 0})

        resumed_workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job,
                make=counted_make,
                playtest=counted_playtest,
                instructions=DefaultInstructions(site_writer=counted_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        )
        with self.assertRaisesRegex(ContractError, "original Wish"):
            resumed_workshop.resume_instructions(
                Wish.create("resumable-top", "A different Wish must not attach")
            )
        resumed = resumed_workshop.resume_instructions(wish)
        self.assertEqual((resumed.status, resumed.job), ("delivered", "deliver"))
        self.assertEqual(resumed.artifact_sha256, waiting.artifact_sha256)
        self.assertEqual(resumed.playtest_rounds, 3)
        self.assertEqual(calls, {"make": 1, "playtest": 1, "site": 1})
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain(wish.product_id))

    def test_resume_reuses_sealed_instructions_and_only_retries_the_site(self):
        calls = {"make": 0, "playtest": 0, "site": 0}

        def counted_make(context):
            calls["make"] += 1
            return self.make_job(context)

        def counted_playtest(context):
            calls["playtest"] += 1
            return self.passing_playtest(context)

        def waiting_site(context, root, manifest):
            del context, root, manifest
            calls["site"] += 1
            raise WaitingFor(
                Need(
                    "instructions",
                    "site-page",
                    "The sealed page is waiting for a site account.",
                    "Configure the site account and resume this exact page.",
                )
            )

        wish = Wish.create("sealed-top", "A top with one sealed page")
        first = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job,
                make=counted_make,
                playtest=counted_playtest,
                instructions=DefaultInstructions(site_writer=waiting_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        ).run(wish, playtest_rounds=2)
        self.assertEqual((first.status, first.job), ("waiting", "instructions"))
        self.assertEqual(calls, {"make": 1, "playtest": 1, "site": 1})
        waiting_payload = Runtime(
            self.runtime / "workshop.sqlite3"
        ).events(wish.product_id)[-1]["payload"]
        self.assertEqual(len(waiting_payload["resume_checkpoint_sha256"]), 64)
        self.assertEqual(len(waiting_payload["instructions_sha256"]), 64)

        def successful_site(context, root, manifest):
            calls["site"] += 1
            return self.site_writer(context, root, manifest)

        resumed = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job,
                make=counted_make,
                playtest=counted_playtest,
                instructions=DefaultInstructions(site_writer=successful_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        ).resume_instructions(wish)
        self.assertEqual((resumed.status, resumed.job), ("delivered", "deliver"))
        self.assertEqual(resumed.artifact_sha256, first.artifact_sha256)
        self.assertEqual(calls, {"make": 1, "playtest": 1, "site": 2})

    def test_resume_rejects_changed_sealed_instructions_before_site_effect(self):
        site_calls = 0

        def waiting_site(context, root, manifest):
            del context, root, manifest
            raise WaitingFor(
                Need(
                    "instructions",
                    "site-page",
                    "The sealed page is waiting.",
                    "Resume after site capability is configured.",
                )
            )

        wish = Wish.create("tampered-page", "A top with immutable Instructions")
        Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job,
                make=self.make_job,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(site_writer=waiting_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        ).run(wish, playtest_rounds=1)
        instructions_path = (
            self.runtime
            / "runs"
            / wish.product_id
            / "instructions"
            / "INSTRUCTIONS.md"
        )
        instructions_path.write_text("changed while waiting\n", encoding="utf-8")

        def forbidden_site(context, root, manifest):
            nonlocal site_calls
            site_calls += 1
            return self.site_writer(context, root, manifest)

        resumed_workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job,
                make=self.make_job,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(site_writer=forbidden_site),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        )
        with self.assertRaisesRegex(ContractError, "changed while waiting"):
            resumed_workshop.resume_instructions(wish)
        self.assertEqual(site_calls, 0)

    def test_customer_reviews_follow_deliver_and_feed_only_a_future_make(self):
        workshop = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(self.passing_playtest),
            runtime_root=self.runtime,
        )
        result = workshop.run(
            Wish.create("reviewed-top", "A top a customer can review"),
            playtest_rounds=1,
        )
        review = CustomerReview(
            "review-1",
            result.artifact_sha256,
            result.instructions_sha256,
            result.delivery.tracking_id,
            4,
            "The second rhythm is delightful; make the winding grip larger next time.",
            "2026-08-24T12:00:00+00:00",
        )
        self.assertEqual(workshop.record_review("reviewed-top", review), review)
        self.assertEqual(workshop.record_review("reviewed-top", review), review)
        self.assertEqual(workshop.reviews("reviewed-top"), (review,))
        learning = workshop.review_learnings("reviewed-top")[0]
        self.assertEqual(learning["applies_to"], "future-make")
        self.assertTrue(learning["delivered_revision_immutable"])
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertEqual(state.get_product("reviewed-top")["stage"], "deliver")
        self.assertTrue(state.verify_event_chain("reviewed-top"))

        changed = CustomerReview(
            "review-1",
            result.artifact_sha256,
            result.instructions_sha256,
            result.delivery.tracking_id,
            1,
            "Different feedback under the same id must not replace history.",
            "2026-08-24T12:00:00+00:00",
        )
        with self.assertRaisesRegex(ContractError, "already bound"):
            workshop.record_review("reviewed-top", changed)

    def test_three_levels_are_explicit_and_playtest_requires_make(self):
        taste_only = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(self.passing_playtest),
            runtime_root=self.root / "taste-runtime",
        )
        custom_make = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(site_writer=self.site_writer),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            make=self.make_job,
            runtime_root=self.root / "make-runtime",
        )
        custom_playtest = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job,
                instructions=DefaultInstructions(site_writer=self.site_writer),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            make=self.make_job,
            playtest=self.passing_playtest,
            runtime_root=self.root / "playtest-runtime",
        )
        self.assertEqual(
            (
                taste_only.customization_level,
                custom_make.customization_level,
                custom_playtest.customization_level,
            ),
            ("taste-only", "custom-make", "custom-playtest"),
        )
        with self.assertRaisesRegex(ContractError, "requires custom Make"):
            Workshop(
                self.inventor,
                "moving-machines",
                concept=self.concept_job,
                playtest=self.passing_playtest,
                runtime_root=self.root / "invalid-runtime",
            )

    def test_missing_shared_make_waits_without_fabricating_a_product(self):
        workshop = Workshop(
            self.inventor,
            "little-worlds",
            concept=self.concept_job,
            runtime_root=self.runtime,
        )
        result = workshop.run(
            Wish.create("tiny-friend", "A tiny desk companion"),
            playtest_rounds=2,
        )
        self.assertEqual((result.status, result.job, result.round), ("waiting", "make", 1))
        self.assertEqual(result.playtest_rounds, 2)
        self.assertEqual(result.needs[0].capability, "model-and-cad-maker")
        state = Runtime(self.runtime / "workshop.sqlite3")
        self.assertTrue(state.verify_event_chain("tiny-friend"))
        self.assertIsNone(state.get_product("tiny-friend")["artifact_sha256"])
        self.assertEqual(state.get_product("tiny-friend")["metadata"]["playtest_rounds"], 2)

    def test_each_wish_can_buy_a_different_bounded_round_allowance(self):
        two_rounds = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(),
            runtime_root=self.root / "two-round-runtime",
        )
        result = two_rounds.run(
            Wish.create("small-tier", "A small playtest allowance"),
            playtest_rounds=2,
        )
        self.assertEqual((result.status, result.round, result.playtest_rounds), ("delivered", 2, 2))

        one_round = Workshop(
            self.inventor,
            "moving-machines",
            tools=self.complete_tools(),
            runtime_root=self.root / "one-round-runtime",
        )
        held = one_round.run(
            Wish.create("smallest-tier", "One chance to improve"),
            playtest_rounds=1,
        )
        self.assertEqual(
            (held.status, held.job, held.round, held.playtest_rounds),
            ("stopped", "playtest", 1, 1),
        )
        self.assertIsNone(held.instructions_sha256)
        self.assertIsNone(held.delivery)

        with self.assertRaisesRegex(ContractError, "from 1 to 100"):
            Workshop(
                self.inventor,
                "moving-machines",
                tools=self.complete_tools(),
                runtime_root=self.root / "invalid-round-runtime",
            ).run(
                Wish.create("bad-tier", "An invalid allowance"),
                playtest_rounds=0,
            )

    def test_custom_playtest_cannot_silently_narrow_the_lane_policy(self):
        def incomplete_playtest(context):
            complete = self.passing_playtest(context)
            first = complete.evidence.results[:1]
            return Playtested(
                Playtest(
                    context.made.artifact_manifest,
                    first,
                    evidence_manifest=complete.evidence.evidence_manifest,
                )
            )

        workshop = Workshop(
            self.inventor,
            "moving-machines",
            concept=self.concept_job,
            make=self.make_job,
            playtest=incomplete_playtest,
            runtime_root=self.root / "incomplete-policy-runtime",
        )
        result = workshop.run(
            Wish.create("narrow-policy", "A machine with one precise movement"),
            playtest_rounds=2,
        )
        self.assertEqual((result.status, result.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in result.needs},
            set(workshop.blueprint.required_capabilities("playtest"))
            - {workshop.blueprint.required_capabilities("playtest")[0]},
        )

    def test_playtest_requires_ai_agent_simulation_evidence(self):
        def non_ai_playtest(context):
            return self._playtest(
                context,
                passed=True,
                ai_simulation=False,
            )

        workshop = Workshop(
            self.inventor,
            "moving-machines",
            concept=self.concept_job,
            make=self.make_job,
            playtest=non_ai_playtest,
            runtime_root=self.root / "non-ai-playtest-runtime",
        )
        result = workshop.run(
            Wish.create("not-ai-proof", "A machine tested without AI players"),
            playtest_rounds=1,
        )
        self.assertEqual((result.status, result.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in result.needs},
            set(workshop.blueprint.required_capabilities("playtest")),
        )

    def test_invented_game_requires_meaningful_ai_simulation(self):
        invalid = Workshop(
            self.inventor,
            "invented-games",
            concept=self.concept_job,
            make=self.make_job,
            playtest=self.passing_playtest,
            runtime_root=self.root / "invalid-invented-runtime",
        ).run(
            Wish.create("new-game-no-proof", "Invent a game for our table"),
            playtest_rounds=2,
        )
        self.assertEqual((invalid.status, invalid.job), ("waiting", "playtest"))
        self.assertEqual(
            {need.capability for need in invalid.needs},
            {"game-simulation"},
        )

        valid = Workshop(
            self.inventor,
            "invented-games",
            tools=self.complete_tools(self.passing_invented_playtest),
            runtime_root=self.root / "valid-invented-runtime",
        ).run(
            Wish.create("new-game-with-proof", "Invent a game for our table"),
            playtest_rounds=1,
        )
        self.assertEqual((valid.status, valid.job, valid.round), ("delivered", "deliver", 1))

    def test_preview_preserves_wish_taste_and_playful_rule(self):
        workshop = Workshop(
            self.inventor,
            "moving-machines",
            concept=self.concept_job,
            runtime_root=self.runtime,
        )
        preview = workshop.preview(Wish.create("kinetic-cable", "A cable holder"))
        self.assertEqual(preview["blueprint"]["lane"], "moving-machines")
        self.assertEqual(preview["taste"]["sha256"], workshop.taste.sha256)
        self.assertIn("merely useful", preview["brief"]["utility_rule"])
        self.assertIn("Cool beats cute", preview["brief"]["tone"])


class DerivedWishWriteBackTest(ToyWorkshopTest):
    """The researched constraints reach Make; the person's words never change."""

    OBJECTIVE = "A delightful desk spinner that reveals a changing beat"

    def setUp(self):
        super().setUp()
        self.made_wishes = []

    def recording_make(self, context):
        self.made_wishes.append(context.wish)
        made = self.make_job(context)
        (made.artifact_root / "wish.json").write_text(
            json.dumps(context.wish.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return Made.from_root(made.artifact_root, made.product)

    def run_once(self, product_id="derived-top"):
        wish = Wish.create(product_id, self.OBJECTIVE)
        result = Workshop(
            self.inventor,
            "moving-machines",
            tools=WorkshopTools(
                concept=self.concept_job,
                make=self.recording_make,
                playtest=self.passing_playtest,
                instructions=DefaultInstructions(site_writer=self.site_writer),
                deliver=DefaultDeliver(self.fulfiller),
            ),
            runtime_root=self.runtime,
        ).run(wish, playtest_rounds=1)
        return wish, result

    def test_make_receives_the_researched_constraints(self):
        wish, result = self.run_once()
        self.assertEqual(result.status, "delivered")
        self.assertEqual(wish.constraints, {})
        received = self.made_wishes[0]
        self.assertNotEqual(received.constraints, {})
        for key in ("envelope_mm", "wall_mm", "features", "components"):
            self.assertIn(key, received.constraints)
        self.assertEqual(received.objective, wish.objective)
        self.assertEqual(received.product_id, wish.product_id)

    def test_the_artifact_wish_carries_the_researched_constraints(self):
        wish, _ = self.run_once("artifact-wish")
        artifact = (
            self.runtime
            / "runs"
            / wish.product_id
            / "round-001"
            / "make"
            / "artifact"
            / "wish.json"
        )
        recorded = json.loads(artifact.read_text(encoding="utf-8"))
        self.assertEqual(recorded["objective"], self.OBJECTIVE)
        self.assertIn("envelope_mm", recorded["constraints"])

    def test_the_run_records_both_wish_identities_beside_the_concept(self):
        wish, result = self.run_once("both-identities")
        state = Runtime(self.runtime / "workshop.sqlite3")
        payload = next(
            event["payload"]
            for event in state.events(wish.product_id)
            if event["to_stage"] == "make"
        )
        self.assertEqual(payload["wish_sha256"], wish_sha256(wish))
        self.assertNotEqual(payload["derived_wish_sha256"], payload["wish_sha256"])
        self.assertEqual(len(payload["derived_wish_sha256"]), 64)
        self.assertEqual(payload["concept_sha256"], result.concept_sha256)

    def test_the_routed_wish_is_never_mutated_by_the_write_back(self):
        wish, _ = self.run_once("untouched")
        self.assertEqual(wish.constraints, {})
        self.assertEqual(wish_sha256(wish), wish_sha256(Wish.create(
            "untouched", self.OBJECTIVE
        )))

    def test_instructions_still_quote_the_persons_own_words(self):
        wish, _ = self.run_once("quoted-words")
        facts = json.loads(
            (
                self.runtime
                / "runs"
                / wish.product_id
                / "instructions"
                / "product.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(facts["wish"], self.OBJECTIVE)

    def test_a_derived_wish_that_altered_the_objective_is_refused(self):
        routed = Wish.create("altered", self.OBJECTIVE)

        class Altering:
            def __init__(self, inner):
                self.inner = inner

            def __call__(self, context):
                concept = self.inner(context)
                altered = DerivedWish(
                    concept.derived_wish.wish_sha256,
                    Wish.create("altered", self.OBJECTIVE + " and a light"),
                )
                return dataclasses.replace(concept, derived_wish=altered)

        Altering.OBJECTIVE = self.OBJECTIVE
        # The seal refuses it first -- the descriptor names the derived Wish the
        # research actually wrote back -- and the Workshop's own check refuses
        # it again if a concept ever reaches it unsealed.
        with self.assertRaisesRegex(ContractError, "derived Wish"):
            Workshop(
                self.inventor,
                "moving-machines",
                tools=WorkshopTools(
                    concept=Altering(self.concept_job),
                    make=self.recording_make,
                    playtest=self.passing_playtest,
                    instructions=DefaultInstructions(site_writer=self.site_writer),
                    deliver=DefaultDeliver(self.fulfiller),
                ),
                runtime_root=self.runtime,
            ).run(routed, playtest_rounds=1)


if __name__ == "__main__":
    unittest.main()
