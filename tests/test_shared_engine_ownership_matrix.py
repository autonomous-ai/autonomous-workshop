import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.deliver import DefaultDeliver
from inventor_workshop.instructions import DefaultInstructions
from inventor_workshop.jobs import Delivered, Invented, Made, Playtested
from inventor_workshop.make import Wish
from inventor_workshop.models import PlaytestResult, Receipt
from inventor_workshop.playtest import Playtest
from inventor_workshop.playtest_release import (
    CapabilityReleaseProof,
    ReleaseProofSource,
)
from inventor_workshop.workshop import WorkshopTools


ROOT = Path(__file__).resolve().parents[1]
CONFIG_SHA256 = "c" * 64
FIXED_TIME = "2026-08-25T12:00:00+00:00"
CANONICAL_PROFILES = {
    "alice": "classics-made-yours",
    "bob": "moving-machines",
    "eve": "little-worlds",
    "ivy": "holdable-science",
    "leo": "invented-games",
}


def load_profile(inventor_id):
    path = ROOT / "inventors" / inventor_id / "profile.py"
    spec = importlib.util.spec_from_file_location(
        "ownership_matrix_%s" % inventor_id, path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_sha256(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


class DeterministicWorkshopFakes:
    """One set of shared workers, parameterized only by bound Workshop inputs."""

    def __init__(self, case, inventor_id, lane, wish, taste_sha256):
        self.case = case
        self.inventor_id = inventor_id
        self.lane = lane
        self.wish = wish
        self.wish_sha256 = canonical_sha256(wish.to_dict())
        self.taste_sha256 = taste_sha256
        self.calls = []

    def tools(self, *, instructions=None):
        return WorkshopTools(
            invent=self.invent,
            make=self.make,
            playtest=self.playtest,
            instructions=instructions or self.instructions,
            deliver=self.deliver,
        )

    def _record(self, stage, context):
        self.case.assertEqual(context.wish.to_dict(), self.wish.to_dict())
        self.case.assertEqual(
            context.wish.context["manager_assignment"]["inventor_id"],
            self.inventor_id,
        )
        self.case.assertEqual(
            context.wish.context["manager_assignment"]["assignment_sha256"],
            "a" * 64,
        )

        taste_sha256 = None
        if hasattr(context, "taste"):
            taste_sha256 = context.taste.sha256
            self.case.assertEqual(taste_sha256, self.taste_sha256)
            self.case.assertEqual(context.taste.path.parent.name, self.inventor_id)

        lane = None
        if hasattr(context, "blueprint"):
            lane = context.blueprint.lane
            self.case.assertEqual(lane, self.lane)

        made = getattr(context, "made", None)
        if made is not None:
            self.case.assertEqual(made.product["wish_sha256"], self.wish_sha256)
            self.case.assertEqual(made.product["taste_sha256"], self.taste_sha256)
            self.case.assertEqual(made.product["inventor_id"], self.inventor_id)
            self.case.assertEqual(made.product["lane"], self.lane)
            taste_sha256 = taste_sha256 or made.product["taste_sha256"]
            lane = lane or made.product["lane"]

        explicit_inventor_id = getattr(context, "inventor_id", None)
        if explicit_inventor_id is not None:
            self.case.assertEqual(explicit_inventor_id, self.inventor_id)

        # The exact assignment identity is in the immutable Wish at every stage;
        # Make additionally receives the engine's explicit operational identity.
        observed_inventor_id = (
            explicit_inventor_id
            or (made.product["inventor_id"] if made is not None else None)
            or context.wish.context["manager_assignment"]["inventor_id"]
        )
        self.case.assertEqual(observed_inventor_id, self.inventor_id)
        self.case.assertEqual(taste_sha256, self.taste_sha256)
        self.case.assertEqual(lane, self.lane)
        self.calls.append(
            {
                "stage": stage,
                "wish": context.wish.to_dict(),
                "taste_sha256": taste_sha256,
                "lane": lane,
                "inventor_id": observed_inventor_id,
            }
        )

    def invent(self, context):
        self._record("invent", context)
        return Invented(
            wish_sha256=self.wish_sha256,
            taste_sha256=self.taste_sha256,
            lane=self.lane,
            concept={
                "title": "%s ownership fixture" % self.inventor_id.title(),
                "summary": "A deterministic industrial-design handoff for the shared engine.",
                "bindings": {
                    "wish_sha256": self.wish_sha256,
                    "taste_sha256": self.taste_sha256,
                    "lane": self.lane,
                    "inventor_id": self.inventor_id,
                },
            },
            score=95,
            target_score=90,
        )

    def make(self, context):
        self._record("make", context)
        self.case.assertEqual(
            context.invented.concept["bindings"],
            {
                "wish_sha256": self.wish_sha256,
                "taste_sha256": self.taste_sha256,
                "lane": self.lane,
                "inventor_id": self.inventor_id,
            },
        )
        artifact = context.workspace / "artifact"
        artifact.mkdir(parents=True)
        files = {
            "toy.step": "ISO-10303-21; deterministic ownership fixture\n",
            "part_body.stl": "solid body\nendsolid body\n",
            "edition-rules.json": '{"known_rules":["one legal turn"]}\n',
            "source-model.json": '{"source":"deterministic science model"}\n',
            "personalization-map.json": '{"feature":"consented fixture"}\n',
            "game-rules.json": '{"end":"finite","legal_actions":["play"]}\n',
            "simulator.py": (
                "def play(seed):\n"
                "    return {'seed': seed, 'completed': True, 'turns': 1}\n"
            ),
        }
        for relative, payload in files.items():
            (artifact / relative).write_text(payload, encoding="utf-8")
        return Made.from_root(
            artifact,
            {
                "title": "%s ownership fixture" % self.inventor_id.title(),
                "summary": "A deterministic product from the shared mechanical-design worker.",
                "lane": self.lane,
                "inventor_id": self.inventor_id,
                "wish_sha256": self.wish_sha256,
                "taste_sha256": self.taste_sha256,
                "instructions": "Use the exact deterministic fixture as described.",
                "components": ["one fixture body"],
                "limitations": ["Contract fixture; not human-use evidence."],
            },
        )

    @staticmethod
    def _write_json(root, relative, value):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return relative, hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _source(role, scope, path, sha256):
        return ReleaseProofSource(role, scope, path, sha256)

    def _release_proof(self, capability, context, product_inventory):
        artifact_sha256 = context.made.artifact_sha256
        source = self._source
        write_json = lambda name, value: self._write_json(
            context.workspace, name, value
        )

        if capability == "mechanical-test":
            receipt, receipt_sha256 = write_json(
                "proof/mechanical.json", {"computed": True}
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                "computed-mechanical-proof",
                (
                    source(
                        "step-model",
                        "product",
                        "toy.step",
                        product_inventory["toy.step"],
                    ),
                    source("mechanical-receipt", "playtest", receipt, receipt_sha256),
                ),
                {
                    "brep_valid": True,
                    "interference_cases": 2,
                    "fit_cases": 2,
                    "assembly_paths_tested": 1,
                    "motion_cases": 1,
                    "load_cases": 1,
                    "failure_modes_tested": 2,
                    "forbidden_intersections": 0,
                    "fit_failures": 0,
                    "assembly_failures": 0,
                    "motion_failures": 0,
                    "load_failures": 0,
                    "unresolved_critical_failures": 0,
                },
            )

        if capability == "print-test":
            receipt, receipt_sha256 = write_json(
                "proof/slicer.json", {"sliced": ["part_body.stl"]}
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                "exact-slicer-proof",
                (
                    source(
                        "print-part",
                        "product",
                        "part_body.stl",
                        product_inventory["part_body.stl"],
                    ),
                    source("slicer-receipt", "playtest", receipt, receipt_sha256),
                ),
                {
                    "slicer": "PrusaSlicer",
                    "slicer_version": "2.9.6",
                    "profiles": {
                        "strong": "1" * 64,
                        "balanced": "2" * 64,
                        "fast": "3" * 64,
                    },
                    "parts": [
                        {
                            "input_ref": "part_body.stl",
                            "input_sha256": product_inventory["part_body.stl"],
                            "gcode_sha256": "4" * 64,
                            "gcode_bytes": 100,
                            "returncode": 0,
                        }
                    ],
                    "slicer_errors": 0,
                },
            )

        if capability == "motion-test":
            receipt, receipt_sha256 = write_json(
                "proof/motion.json", {"simulated": True}
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                "kinematic-motion-proof",
                (
                    source(
                        "step-model",
                        "product",
                        "toy.step",
                        product_inventory["toy.step"],
                    ),
                    source("motion-receipt", "playtest", receipt, receipt_sha256),
                ),
                {
                    "states_tested": 10,
                    "continuous_sweep": True,
                    "tolerance_cases_tested": 3,
                    "load_cases_tested": 2,
                    "orientations_tested": 3,
                    "wear_cycles": 100,
                    "misuse_cases_tested": 2,
                    "collisions": 0,
                    "stalls": 0,
                    "failures": 0,
                },
            )

        if capability == "classic-rules-test":
            reference, reference_sha256 = write_json(
                "proof/reference-rules.json", {"known_rules": True}
            )
            traces, traces_sha256 = write_json(
                "proof/classic-traces.json", {"games": [{"seed": 1}]}
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                "classic-rule-conformance-proof",
                (
                    source(
                        "edition-rules",
                        "product",
                        "edition-rules.json",
                        product_inventory["edition-rules.json"],
                    ),
                    source("reference-rules", "playtest", reference, reference_sha256),
                    source("game-traces", "playtest", traces, traces_sha256),
                ),
                {
                    "seeded_games": 1,
                    "rule_conformance_cases": 3,
                    "rule_mismatches": 0,
                    "role_legibility_cases": 2,
                    "role_legibility_failures": 0,
                },
            )

        if capability == "science-test":
            sources, sources_sha256 = write_json(
                "proof/science-sources.json", {"sources": ["fixture-source"]}
            )
            traces, traces_sha256 = write_json(
                "proof/comprehension-traces.json", {"traces": [{"seed": 1}]}
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                "source-bound-science-proof",
                (
                    source(
                        "source-model",
                        "product",
                        "source-model.json",
                        product_inventory["source-model.json"],
                    ),
                    source("science-sources", "playtest", sources, sources_sha256),
                    source(
                        "comprehension-traces",
                        "playtest",
                        traces,
                        traces_sha256,
                    ),
                ),
                {
                    "accuracy_cases": 3,
                    "accuracy_failures": 0,
                    "simplifications_checked": 2,
                    "dishonest_simplifications": 0,
                    "comprehension_traces": 1,
                    "comprehension_failures": 0,
                },
            )

        if capability == "world-test":
            consent, consent_sha256 = write_json(
                "proof/consent-record.json", {"consented": True}
            )
            reference, reference_sha256 = write_json(
                "proof/reference-material.json", {"subject": "fixture"}
            )
            traces, traces_sha256 = write_json(
                "proof/likeness-traces.json", {"recognized": True}
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                "reference-bound-world-proof",
                (
                    source(
                        "personalization-map",
                        "product",
                        "personalization-map.json",
                        product_inventory["personalization-map.json"],
                    ),
                    source("consent-record", "playtest", consent, consent_sha256),
                    source(
                        "reference-material",
                        "playtest",
                        reference,
                        reference_sha256,
                    ),
                    source("likeness-traces", "playtest", traces, traces_sha256),
                ),
                {
                    "consent_verified": True,
                    "personalization_features": 1,
                    "likeness_cases": 1,
                    "recognition_failures": 0,
                    "consent_violations": 0,
                },
            )

        if capability == "game-simulation":
            measurements = {
                "requested_games": 1_000,
                "completed_games": 1_000,
                "balance_cases": 10,
                "exploit_cases": 10,
                "choice_cases": 10,
                "flow_cases": 10,
                "balance_failures": 0,
                "exploits_found": 0,
                "degenerate_choices": 0,
                "flow_failures": 0,
            }
            games = [
                {
                    "seed": seed,
                    "completed": True,
                    "turns": 4,
                    "player_styles": [
                        "optimizing",
                        "social",
                        "exploratory",
                        "adversarial",
                    ],
                    "issues": [],
                }
                for seed in range(1_000)
            ]
            traces, traces_sha256 = write_json(
                "proof/game-traces.json",
                {"artifact_sha256": artifact_sha256, "games": games},
            )
            analysis, analysis_sha256 = write_json(
                "proof/game-analysis.json",
                {
                    "artifact_sha256": artifact_sha256,
                    "measurements": measurements,
                },
            )
            return CapabilityReleaseProof(
                capability,
                artifact_sha256,
                "seeded-game-analysis-proof",
                (
                    source(
                        "simulator-source",
                        "product",
                        "simulator.py",
                        product_inventory["simulator.py"],
                    ),
                    source(
                        "game-rules",
                        "product",
                        "game-rules.json",
                        product_inventory["game-rules.json"],
                    ),
                    source("game-traces", "playtest", traces, traces_sha256),
                    source("game-analysis", "playtest", analysis, analysis_sha256),
                ),
                measurements,
            )

        raise AssertionError("unexpected release capability %s" % capability)

    def playtest(self, context):
        self._record("playtest", context)
        context.workspace.mkdir(parents=True)
        product_inventory = {
            entry.path: entry.sha256
            for entry in context.made.artifact_manifest.entries
        }
        results = []
        for capability in context.blueprint.required_capabilities("playtest"):
            evidence = {
                "evidence_class": "ai-simulation",
                "artifact_sha256": context.made.artifact_sha256,
                "agent_roles": ["optimizing-player", "adversarial-breaker"],
                "claims": ["Deterministic shared evidence for %s." % capability],
            }
            if capability != "agent-playtest":
                evidence["release_proof"] = self._release_proof(
                    capability, context, product_inventory
                ).to_dict()
            evidence_ref, evidence_sha256 = self._write_json(
                context.workspace,
                "results/%s.json" % capability,
                evidence,
            )
            results.append(
                PlaytestResult(
                    capability,
                    True,
                    context.made.artifact_sha256,
                    evidence,
                    "deterministic-shared-playtest",
                    "1.0.0",
                    CONFIG_SHA256,
                    evidence_ref,
                    evidence_sha256,
                    FIXED_TIME,
                )
            )
        return Playtested(
            Playtest(
                context.made.artifact_manifest,
                tuple(results),
                evidence_manifest=build_artifact_manifest(
                    context.workspace, created_at="content-addressed"
                ),
            )
        )

    def _site_writer(self, context, sealed_root, sealed_manifest):
        del sealed_root
        return Receipt(
            pack_sha256="f" * 64,
            artifact_sha256=context.made.artifact_sha256,
            design_id="design-" + context.wish.product_id,
            slug=context.wish.product_id,
            owner_id="owner-" + self.inventor_id,
            root_id="design-" + context.wish.product_id,
            current_history_id="history-1",
            published_history_id=None,
            status="draft",
            project_url="https://cdn.autonomous.ai/projects/history-1/",
            observed_at=FIXED_TIME,
            details={
                "instructions_sha256": sealed_manifest.artifact_sha256,
                "page_url": (
                    "https://www.autonomous.ai/factory/product/"
                    + context.wish.product_id
                ),
            },
        )

    def instructions(self, context):
        self._record("instructions", context)
        return DefaultInstructions(site_writer=self._site_writer)(context)

    def deliver(self, context):
        self._record("deliver", context)
        return DefaultDeliver(
            lambda selected: Delivered(
                selected.made.artifact_sha256,
                selected.instructions.instructions_sha256,
                "UPS",
                "Ground",
                "1Z999AA10123456784",
                "handed-off",
                FIXED_TIME,
                {
                    "print_receipt": {"fixture": "print"},
                    "qa_receipt": {"fixture": "qa"},
                    "packing_receipt": {"fixture": "packing"},
                    "carrier_receipt": {"fixture": "handoff"},
                },
            )
        )(context)


class SharedEngineOwnershipMatrixTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def exact_wish(inventor_id, product_id):
        return Wish.create(
            product_id,
            "I wish for a pocket toy\nthat keeps the midnight-blue hinge exactly.",
            constraints={
                "maximum_mm": [90, 70, 25],
                "must_keep": ["hinge", "midnight blue"],
                "audience": {"minimum_age": 14, "locale": "vi-VN"},
            },
            context={
                "customer": {"name": "Example Customer", "locale": "vi-VN"},
                "manager_assignment": {
                    "inventor_id": inventor_id,
                    "decision_sha256": "d" * 64,
                    "assignment_sha256": "a" * 64,
                },
            },
        )

    def fixture_for(self, inventor_id, lane, wish, runtime_name):
        profile = load_profile(inventor_id)
        runtime_root = self.root / runtime_name
        preview_workshop = profile.build_workshop(runtime_root=runtime_root)
        fixture = DeterministicWorkshopFakes(
            self,
            inventor_id,
            lane,
            wish,
            preview_workshop.taste.sha256,
        )
        return profile, fixture, runtime_root

    def assert_exact_matrix(self, fixture):
        self.assertEqual(
            [call["stage"] for call in fixture.calls],
            ["invent", "make", "playtest", "instructions", "deliver"],
        )
        for call in fixture.calls:
            self.assertEqual(call["wish"], fixture.wish.to_dict())
            self.assertEqual(call["taste_sha256"], fixture.taste_sha256)
            self.assertEqual(call["lane"], fixture.lane)
            self.assertEqual(call["inventor_id"], fixture.inventor_id)

    def test_all_five_taste_only_profiles_use_every_shared_stage(self):
        for inventor_id, lane in CANONICAL_PROFILES.items():
            with self.subTest(inventor_id=inventor_id):
                wish = self.exact_wish(inventor_id, "matrix-" + inventor_id)
                profile, fixture, runtime_root = self.fixture_for(
                    inventor_id, lane, wish, "all-shared-" + inventor_id
                )
                workshop = profile.build_workshop(
                    tools=fixture.tools(),
                    runtime_root=runtime_root,
                    max_rounds=1,
                )

                result = workshop.run(wish, playtest_rounds=1)

                self.assertEqual(workshop.customization_level, "taste-only")
                self.assertEqual(workshop.inventor_id, inventor_id)
                self.assertEqual(workshop.lane, lane)
                self.assertEqual(result.status, "delivered")
                self.assertEqual(result.job, "deliver")
                self.assertIsNotNone(result.delivery)
                self.assert_exact_matrix(fixture)

    def test_explicit_overrides_replace_only_the_named_seam(self):
        bob_wish = self.exact_wish("bob", "matrix-bob-custom-make")
        bob, bob_fixture, bob_runtime = self.fixture_for(
            "bob", "moving-machines", bob_wish, "bob-custom-make"
        )
        bob_custom_calls = []

        def bob_custom_make(context):
            bob_custom_calls.append("make")
            return bob_fixture.make(context)

        bob_workshop = bob.build_workshop(
            tools=bob_fixture.tools(),
            make=bob_custom_make,
            runtime_root=bob_runtime,
            max_rounds=1,
        )
        bob_result = bob_workshop.run(bob_wish, playtest_rounds=1)
        self.assertEqual(bob_result.status, "delivered")
        self.assertEqual(bob_workshop.customization_level, "custom-make")
        self.assertIs(bob_workshop.make_job, bob_custom_make)
        self.assertIs(bob_workshop.invent_job.__self__, bob_fixture)
        self.assertIs(bob_workshop.playtest_job.__self__, bob_fixture)
        self.assertIs(bob_workshop.instructions_job.__self__, bob_fixture)
        self.assertIs(bob_workshop.deliver_job.__self__, bob_fixture)
        self.assertEqual(bob_custom_calls, ["make"])
        self.assert_exact_matrix(bob_fixture)

        leo_wish = self.exact_wish("leo", "matrix-leo-custom-playtest")
        leo, leo_fixture, leo_runtime = self.fixture_for(
            "leo", "invented-games", leo_wish, "leo-custom-playtest"
        )
        leo_custom_calls = []

        def leo_custom_make(context):
            leo_custom_calls.append("make")
            return leo_fixture.make(context)

        def leo_custom_playtest(context):
            leo_custom_calls.append("playtest")
            return leo_fixture.playtest(context)

        leo_workshop = leo.build_workshop(
            tools=leo_fixture.tools(),
            make=leo_custom_make,
            playtest=leo_custom_playtest,
            runtime_root=leo_runtime,
            max_rounds=1,
        )
        leo_result = leo_workshop.run(leo_wish, playtest_rounds=1)
        self.assertEqual(leo_result.status, "delivered")
        self.assertEqual(leo_workshop.customization_level, "custom-playtest")
        self.assertIs(leo_workshop.make_job, leo_custom_make)
        self.assertIs(leo_workshop.playtest_job, leo_custom_playtest)
        self.assertIs(leo_workshop.invent_job.__self__, leo_fixture)
        self.assertIs(leo_workshop.instructions_job.__self__, leo_fixture)
        self.assertIs(leo_workshop.deliver_job.__self__, leo_fixture)
        self.assertEqual(leo_custom_calls, ["make", "playtest"])
        self.assert_exact_matrix(leo_fixture)

    def test_missing_external_provider_waits_on_a_shared_capability(self):
        wish = self.exact_wish("alice", "matrix-shared-site-wait")
        profile, fixture, runtime_root = self.fixture_for(
            "alice", "classics-made-yours", wish, "shared-site-wait"
        )

        def shared_instructions_without_site_provider(context):
            fixture._record("instructions", context)
            return DefaultInstructions()(context)

        workshop = profile.build_workshop(
            tools=fixture.tools(instructions=shared_instructions_without_site_provider),
            runtime_root=runtime_root,
            max_rounds=1,
        )
        result = workshop.run(wish, playtest_rounds=1)

        self.assertEqual(result.status, "waiting")
        self.assertEqual(result.job, "instructions")
        self.assertEqual([need.capability for need in result.needs], ["site-page"])
        self.assertEqual(
            [call["stage"] for call in fixture.calls],
            ["invent", "make", "playtest", "instructions"],
        )
        for need in result.needs:
            rendered = json.dumps(need.to_dict()).casefold()
            self.assertNotIn("alice", rendered)
            self.assertNotIn("inventor-specific", rendered)
            self.assertIn("shared", rendered)


if __name__ == "__main__":
    unittest.main()
