import copy
import hashlib
import json
import os
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from unittest import mock

from inventor_workshop.agent_invent import (
    CodexInventor,
    InventResearch,
    InventResearchSource,
    InventResearchUnavailable,
    PublicHTTPResearchProvider,
    PublicResearchHTTPRequest,
    PublicResearchHTTPResponse,
    REWARD_WEIGHTS,
    configured_workshop_tools,
)
from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import InventContext, WaitingFor
from inventor_workshop.make import Wish
from inventor_workshop.reward_loop import json_sha256
from inventor_workshop.taste import load_taste
from inventor_workshop.toys import ToyBlueprint
from inventor_workshop.workshop import Workshop, WorkshopTools
from inventor_workshop.world_reference_vault import WorldReferenceScope
from inventor_workshop.world_service import (
    WorldInventInputs,
    WorldInventReference,
    WorldProviderIdentity,
)
from tests.test_invented_game import game_contract as executable_game_contract


LANES = (
    "classics-made-yours",
    "invented-games",
    "moving-machines",
    "holdable-science",
    "little-worlds",
)


def lane_contract(lane):
    contracts = {
        "classics-made-yours": {
            "schema_version": 1,
            "lane": "classics-made-yours",
            "known_game": "Chess",
            "rules_preserved": True,
            "rules_preservation": {
                "canonical_ruleset": "Standard chess without rule variants.",
                "preserved_invariants": [
                    "Alternating legal moves and standard checkmate remain unchanged."
                ],
                "allowed_physical_changes": [
                    "Piece silhouettes, board graphics, materials, and storage may change."
                ],
            },
            "personalization_map": [
                {
                    "wish_detail": "The customer's dog has a proud stance.",
                    "physical_feature": "The knight receives that proud neck silhouette.",
                    "rules_effect": "none",
                }
            ],
        },
        "invented-games": executable_game_contract(),
        "moving-machines": {
            "schema_version": 1,
            "lane": "moving-machines",
            "kinematic_model": {
                "input_motion": "A hand winds a spring-driven rotary input.",
                "transmission": [
                    "A reduction gear drives an eccentric crank.",
                    "The crank drives paired leg linkages in opposing phase.",
                ],
                "output_motion": "Four feet produce an alternating forward walking gait.",
                "degrees_of_freedom": 1,
            },
            "tolerances_mm": [
                {
                    "interface": "Printed crank pin inside the connecting rod",
                    "nominal_clearance_mm": 0.3,
                    "tolerance_mm": 0.1,
                }
            ],
            "load_assumptions": [
                {
                    "case": "A user stalls one foot while the spring unwinds.",
                    "force_n": 8.0,
                    "safety_factor": 2.0,
                    "basis": "A conservative concept-stage hand-force assumption for Make to verify.",
                }
            ],
            "failure_modes": [
                {
                    "mode": "Crank pin shear",
                    "cause": "A stalled foot concentrates spring load at the crank.",
                    "effect": "The gait stops and a loose small part may result.",
                    "mitigation": "Make sizes the pin, limits torque, and Playtest verifies the exact geometry.",
                }
            ],
        },
        "holdable-science": {
            "schema_version": 1,
            "lane": "holdable-science",
            "source_model": {
                "phenomenon": "Coupled periodic motion",
                "model": "A bounded linkage maps rotary phase to visible periodic displacement.",
                "source_ids": ["mechanism-source", "science-mapping"],
            },
            "simplifications": [
                {
                    "simplification": "The model presents one exact, cited source statement and does not claim unmodeled behavior.",
                    "reason": "One observable relationship keeps the first interaction legible.",
                    "disclosed_limit": "It is a qualitative teaching model, not a measurement or prediction instrument.",
                }
            ],
            "scale": {
                "real_quantity": "one represented relationship",
                "model_quantity": "one complete interaction",
                "scale_ratio": 1.0,
                "units": "represented relationships per interaction",
            },
            "interaction": {
                "user_action": "Turn the handle through one revolution.",
                "observable_response": "Markers reveal their relative phase around the cycle.",
                "teaching_point": "Coupled periodic motion",
                "misuse_boundary": "It is a qualitative teaching model, not a measurement or prediction instrument.",
            },
        },
        "little-worlds": {
            "schema_version": 1,
            "lane": "little-worlds",
            "consented_references": [
                {
                    "reference_id": "customer-dog",
                    "subject": "The customer's dog",
                    "consent_or_rights_basis": "The customer supplied and authorized use of their own reference photos.",
                    "allowed_features": ["proud neck posture", "curled tail"],
                    "excluded_features": ["owner's face", "home address"],
                }
            ],
            "feature_to_form_map": [
                {
                    "reference_id": "customer-dog",
                    "reference_feature": "proud neck posture",
                    "physical_form": "A raised head becomes the scene's central silhouette.",
                    "recognition_test": "The pose remains recognizable without a nameplate or caption.",
                }
            ],
        },
    }
    return contracts[lane]


def action(title, lane="moving-machines"):
    selected_source_ids = ["mechanism-source", "safety-source"]
    if lane == "holdable-science":
        selected_source_ids.append("science-mapping")
    return {
        "research": {
            "patterns": [
                {
                    "statement": "Wind-up walkers turn stored energy into repeated motion.",
                    "source_ids": ["mechanism-source"],
                }
            ],
            "opportunities": [
                {
                    "statement": "Keep accessible moving parts away from pinch hazards.",
                    "source_ids": ["safety-source"],
                }
            ],
            "assumptions": ["The customer will later provide visual references."],
        },
        "directions": [
            {
                "name": "Proud trot",
                "idea": "A dog-shaped walker with a proud stepping rhythm.",
                "play": "Wind it and race it across a desk.",
                "form": "Long legs and an arched body.",
                "risks": ["Gait may be too generic."],
            },
            {
                "name": "Tail metronome",
                "idea": "The tail visibly meters each step.",
                "play": "Predict the next footfall from the tail.",
                "form": "A compact body with an oversized kinetic tail.",
                "risks": ["Tail may steal attention from the dog."],
            },
            {
                "name": "Desk trail",
                "idea": "A walker that traces a characteristic curved path.",
                "play": "Arrange desk obstacles and watch it weave.",
                "form": "Offset feet and a low recognizable silhouette.",
                "risks": ["Path tuning belongs to Make."],
            },
        ],
        "selected": {
            "title": title,
            "summary": "A Wish-specific wind-up dog whose gait carries its personality.",
            "magic": "The dog's familiar attitude appears in every step.",
            "play_pattern": "Wind, release, watch, and rearrange a desk course.",
            "industrial_design": "A low arched body, readable head, expressive tail, and four rhythmic legs.",
            "mechanical_handoff": [
                "Engineer a printable four-leg gait.",
                "Keep the dog's silhouette recognizable around the mechanism.",
            ],
            "lane_contract": lane_contract(lane),
            "research_source_ids": selected_source_ids,
        },
    }


def verdict(score, feedback):
    return {
        "dimensions": {dimension: score for dimension in REWARD_WEIGHTS},
        "feedback": [feedback],
        "hard_tensions": [],
        "assessment": feedback,
    }


class FakeCodex:
    cli_version = "9.8.7"
    reasoning_effort = "high"

    def __init__(self, model, outputs):
        self.model = model
        self.outputs = list(outputs)
        self.prompts = []

    def invoke(self, *, prompt, schema, workspace):
        self.prompts.append((prompt, schema, workspace))
        return self.outputs.pop(0)


class FakeResearchHTTP:
    def __init__(self, *, mediawiki=None, cpsc=None):
        self.requests = []
        self.mediawiki = mediawiki
        self.cpsc = cpsc

    def __call__(self, request):
        self.requests.append(request)
        host = urllib.parse.urlsplit(request.url).hostname
        if host == "en.wikipedia.org":
            if self.mediawiki is not None:
                return self.mediawiki(request)
            body = json.dumps(
                {
                    "query": {
                        "pages": [
                            {
                                "pageid": 101,
                                "title": "Automaton",
                                "extract": (
                                    "An automaton is a self-operating machine designed to follow "
                                    "a predetermined sequence of operations through a mechanism."
                                ),
                            },
                            {
                                "pageid": 202,
                                "title": "Mechanical toy",
                                "extract": (
                                    "Mechanical toys use mechanisms to create repeatable movement "
                                    "and invite observation through physical interaction."
                                ),
                            },
                        ]
                    }
                }
            ).encode("utf-8")
            return PublicResearchHTTPResponse(
                request.url, 200, "application/json; charset=utf-8", body
            )
        if host in ("www.cpsc.gov", "cpsc.gov"):
            if self.cpsc is not None:
                return self.cpsc(request)
            body = (
                "<html><head><title>Toys | CPSC.gov</title></head><body><main>"
                "<p>Toy safety requires attention to age guidance and product hazards.</p>"
                "<p>Keep toys with small parts away from young children because they can "
                "present a choking hazard.</p></main></body></html>"
            ).encode("utf-8")
            return PublicResearchHTTPResponse(
                request.url, 200, "text/html; charset=utf-8", body
            )
        raise AssertionError("unexpected research host %r" % host)


class AgentInventTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.inventor = self.root / "inventor"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "---\n"
            "name: Bob\n"
            "description: Kinetic machines where motion creates the spectacle.\n"
            "---\n"
            "# Bob's Taste\n\n"
            "Make motion the magic. Not for static character models.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def context(self, lane="moving-machines", objective=None):
        objective = objective or (
            "A hand-sized toy that makes coupled periodic motion visible"
            if lane == "holdable-science"
            else "A wind-up version of my dog that walks"
        )
        wish = Wish.create("walking-dog", objective)
        world_inputs = None
        if lane == "little-worlds":
            contract = lane_contract(lane)["consented_references"][0]
            scope = WorldReferenceScope(
                contract["reference_id"],
                "customer-owned-subject",
                contract["subject"],
                contract["consent_or_rights_basis"],
                tuple(contract["allowed_features"]),
                tuple(contract["excluded_features"]),
                "customer-order-42",
                "customer-supplied-attestation-record",
            )
            wish_sha256 = json_sha256(wish.to_dict())
            world_inputs = WorldInventInputs(
                wish.product_id,
                wish_sha256,
                WorldProviderIdentity(
                    "fixture-world-reference-service", "1.0.0", "9" * 64
                ),
                (
                    WorldInventReference(
                        scope,
                        wish.product_id,
                        wish_sha256,
                        "8" * 64,
                        "7" * 64,
                        128,
                        "6" * 64,
                        64,
                        "image/png",
                        "8" * 64,
                        "5" * 64,
                    ),
                ),
            )
        return InventContext(
            wish,
            load_taste(self.inventor),
            ToyBlueprint.for_lane(lane),
            (self.root / ("invent-workspace-" + lane)).absolute(),
            world_inputs,
        )

    def research(self, context=None):
        context = context or self.context()
        mechanism_evidence = (
            "Coupled periodic motion. A bounded linkage maps rotary phase to "
            "visible periodic displacement."
            if context.blueprint.lane == "holdable-science"
            else "A wound spring can release energy through a constrained repeated motion."
        )
        sources = [
            InventResearchSource(
                "mechanism-source",
                "Mechanism reference",
                "Fixture Engineering Archive",
                "https://example.com/mechanisms/wind-up",
                "2026-08-25T00:00:00+00:00",
                mechanism_evidence,
                ("prior-art", "use-context", "mechanism", "science"),
            ),
            InventResearchSource(
                "safety-source",
                "Moving-part safety reference",
                "Fixture Safety Office",
                "https://example.com/safety/moving-parts",
                "2026-08-25T00:00:00+00:00",
                "Accessible moving parts require a deliberate pinch-hazard review.",
                ("safety",),
            ),
        ]
        if context.blueprint.lane == "holdable-science":
            scale = json.dumps(
                lane_contract("holdable-science")["scale"],
                sort_keys=True,
                separators=(",", ":"),
            )
            simplification = lane_contract("holdable-science")["simplifications"][0]
            sources.append(
                InventResearchSource(
                    "science-mapping",
                    "Qualitative science mapping",
                    "Autonomous Workshop fixture",
                    "https://example.com/science/mapping",
                    "2026-08-25T00:00:00+00:00",
                    "%s\n%s %s"
                    % (
                        scale,
                        simplification["simplification"],
                        simplification["disclosed_limit"],
                    ),
                    ("science", "use-context"),
                )
            )
        return InventResearch(
            wish_sha256=hashlib.sha256(
                json.dumps(
                    context.wish.to_dict(), sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest(),
            taste_sha256=context.taste.sha256,
            blueprint_sha256=context.blueprint.sha256,
            lane=context.blueprint.lane,
            provider="fixture-retriever",
            provider_version="1.2.3",
            provider_config_sha256="f" * 64,
            sources=tuple(sources),
        )

    def test_inventor_improves_until_the_independent_reward_reaches_goal(self):
        creator = FakeCodex("gpt-5.6-terra", [action("First dog"), action("Trotter")])
        evaluator = FakeCodex(
            "gpt-5.6-terra",
            [verdict(74, "Make the gait more specific to this dog."), verdict(91, "Ready for Make.")],
        )
        evaluator.reasoning_effort = "low"
        invented = CodexInventor(
            creator=creator,
            evaluator=evaluator,
            research_provider=self.research,
            goal=85,
            max_steps=3,
        )(self.context())
        self.assertTrue(invented.passed)
        self.assertEqual(invented.score, 91)
        self.assertEqual(invented.concept["title"], "Trotter")
        self.assertEqual(len(invented.concept["reward_loop"]["steps"]), 2)
        self.assertIn("previous reward", creator.prompts[1][0])
        self.assertIn("never invent a URL", creator.prompts[0][0])
        self.assertIn("selected.lane_contract is mandatory", creator.prompts[0][0])
        self.assertIn("Make and Playtest own those later", evaluator.prompts[0][0])
        self.assertIn("lane_contract dimension", evaluator.prompts[0][0])
        self.assertEqual(
            invented.concept["evidence"]["research_source_ids"],
            ["mechanism-source", "safety-source"],
        )
        self.assertEqual(
            invented.concept["research_evidence"]["provider"],
            "fixture-retriever",
        )
        self.assertEqual(
            invented.concept["evidence"]["creator"]["identity"],
            "codex-invent-policy",
        )
        self.assertEqual(
            len(invented.concept["evidence"]["creator"]["config_sha256"]), 64
        )
        self.assertEqual(
            invented.concept["evidence"]["lane_contract_sha256"],
            json_sha256(invented.concept["lane_contract"]),
        )
        self.assertEqual(invented.concept["evidence"]["schema_version"], 2)

    def test_all_five_lanes_produce_a_typed_contract_bound_into_provenance(self):
        observed_schema_lanes = set()
        for lane in LANES:
            with self.subTest(lane=lane):
                context = self.context(lane)
                creator = FakeCodex("gpt-5.6-terra", [action("Chosen " + lane, lane)])
                evaluator = FakeCodex(
                    "gpt-5.6-terra", [verdict(92, "Typed handoff is ready.")]
                )
                evaluator.reasoning_effort = "low"
                invented = CodexInventor(
                    creator=creator,
                    evaluator=evaluator,
                    research_provider=self.research,
                )(context)

                contract = invented.concept["lane_contract"]
                self.assertEqual(
                    contract["schema_version"],
                    2 if lane == "invented-games" else 1,
                )
                self.assertEqual(contract["lane"], lane)
                self.assertEqual(
                    invented.concept["evidence"]["lane_contract_schema_version"],
                    2 if lane == "invented-games" else 1,
                )
                self.assertEqual(
                    invented.concept["evidence"]["lane_contract_sha256"],
                    json_sha256(contract),
                )
                if lane == "holdable-science":
                    relevance = invented.concept["evidence"][
                        "science_source_relevance"
                    ]
                    self.assertTrue(relevance["passed"])
                    self.assertEqual(relevance["unmatched_terms"], [])
                    self.assertEqual(
                        relevance["wish_terms"],
                        ["coupled", "periodic"],
                    )
                self.assertIn(lane, creator.prompts[0][0])
                self.assertIn(lane, evaluator.prompts[0][0])
                schema = creator.prompts[0][1]
                self.assertNotIn(
                    '"uniqueItems"',
                    json.dumps(schema, sort_keys=True),
                    "Codex structured outputs reject the uniqueItems keyword; runtime validation owns uniqueness",
                )
                lane_schema = schema["properties"]["selected"]["properties"][
                    "lane_contract"
                ]
                self.assertNotIn("oneOf", lane_schema)
                self.assertFalse(lane_schema["additionalProperties"])
                self.assertEqual(lane_schema["properties"]["lane"]["const"], lane)
                observed_schema_lanes.add(lane)
        self.assertEqual(observed_schema_lanes, set(LANES))

    def test_game_reward_loop_repairs_deterministic_outcome_coverage_before_make(self):
        weak = action("Weak Last Spark", "invented-games")
        weak_contract = weak["selected"]["lane_contract"]
        weak_contract["game_protocol"] = {
            "schema_version": 1,
            "protocol": "workshop.resource-game.v1",
            "players": 2,
            "resources": [
                {"resource_id": "sparks", "label": "spark stones", "initial": 4}
            ],
            "actions": [
                {
                    "action_id": "take-one",
                    "label": "Take one",
                    "removals": [{"resource_id": "sparks", "count": 1}],
                    "points": 0,
                },
                {
                    "action_id": "take-two",
                    "label": "Take two",
                    "removals": [{"resource_id": "sparks", "count": 2}],
                    "points": 0,
                },
                {
                    "action_id": "take-three",
                    "label": "Take three",
                    "removals": [{"resource_id": "sparks", "count": 3}],
                    "points": 0,
                },
            ],
            "ending": {
                "condition": "all-resources-empty",
                "winner": "last-actor",
                "score_tie_break": "last-actor",
            },
        }
        revised = copy.deepcopy(weak)
        revised["selected"]["title"] = "Afterglow"
        revised["selected"]["lane_contract"]["game_protocol"]["ending"][
            "winner"
        ] = "next-actor"
        creator = FakeCodex("gpt-5.6-terra", [weak, revised])
        evaluator = FakeCodex(
            "gpt-5.6-luna",
            [
                verdict(99, "The prose looks ready."),
                verdict(99, "The revised executable rules are ready."),
            ],
        )
        evaluator.reasoning_effort = "low"

        invented = CodexInventor(
            creator=creator,
            evaluator=evaluator,
            research_provider=self.research,
            goal=85,
            max_steps=3,
        )(self.context("invented-games"))

        steps = invented.concept["reward_loop"]["steps"]
        self.assertEqual(len(steps), 2)
        self.assertFalse(steps[0]["reward"]["passed"])
        self.assertTrue(
            any(
                "Pinned game qualification" in tension
                for tension in steps[0]["reward"]["hard_tensions"]
            )
        )
        self.assertEqual(
            invented.concept["lane_contract"]["game_protocol"]["ending"][
                "winner"
            ],
            "next-actor",
        )
        qualification = invented.concept["evidence"]["game_qualification"]
        self.assertTrue(qualification["passed"])
        self.assertEqual(
            qualification["lane_contract_sha256"],
            invented.concept["evidence"]["lane_contract_sha256"],
        )
        self.assertIn("deterministic_game_qualification", evaluator.prompts[0][0])

    def test_each_lane_rejects_a_malformed_contract_before_reward_or_make(self):
        malformed = {}
        classic = lane_contract("classics-made-yours")
        classic.pop("rules_preserved")
        malformed["classics-made-yours"] = classic

        invented_game = lane_contract("invented-games")
        invented_game["simulation_gate"]["minimum_complete_games"] = 999
        malformed["invented-games"] = invented_game

        machine = lane_contract("moving-machines")
        machine["tolerances_mm"][0]["nominal_clearance_mm"] = -0.1
        malformed["moving-machines"] = machine

        science = lane_contract("holdable-science")
        science["source_model"]["source_ids"] = ["fabricated-science-source"]
        malformed["holdable-science"] = science

        world = lane_contract("little-worlds")
        world["feature_to_form_map"][0]["reference_feature"] = "home address"
        malformed["little-worlds"] = world

        for lane in LANES:
            with self.subTest(lane=lane):
                proposed = action("Malformed " + lane, lane)
                proposed["selected"]["lane_contract"] = malformed[lane]
                creator = FakeCodex("gpt-5.6-terra", [proposed])
                evaluator = FakeCodex(
                    "gpt-5.6-terra", [verdict(99, "Must not be evaluated.")]
                )
                evaluator.reasoning_effort = "low"
                with self.assertRaises(WaitingFor) as caught:
                    CodexInventor(
                        creator=creator,
                        evaluator=evaluator,
                        research_provider=self.research,
                    )(self.context(lane))
                self.assertEqual(
                    caught.exception.needs[0].capability,
                    "codex-industrial-design",
                )
                self.assertEqual(evaluator.prompts, [])

    def test_missing_or_wrong_lane_contract_stops_inside_invent(self):
        missing = action("Missing contract")
        missing["selected"].pop("lane_contract")
        wrong = action("Wrong contract")
        wrong["selected"]["lane_contract"] = lane_contract(
            "classics-made-yours"
        )

        for label, proposed in (("missing", missing), ("wrong lane", wrong)):
            with self.subTest(label=label):
                creator = FakeCodex("gpt-5.6-terra", [copy.deepcopy(proposed)])
                evaluator = FakeCodex(
                    "gpt-5.6-terra", [verdict(99, "Must not be evaluated.")]
                )
                evaluator.reasoning_effort = "low"
                with self.assertRaises(WaitingFor) as caught:
                    CodexInventor(
                        creator=creator,
                        evaluator=evaluator,
                        research_provider=self.research,
                    )(self.context())
                self.assertEqual(
                    caught.exception.needs[0].capability,
                    "codex-industrial-design",
                )
                self.assertEqual(evaluator.prompts, [])

    def test_workshop_advances_to_make_only_after_invent_passes(self):
        creator = FakeCodex("gpt-5.6-terra", [action("Trotter")])
        evaluator = FakeCodex("gpt-5.6-terra", [verdict(92, "Ready for Make.")])
        evaluator.reasoning_effort = "low"
        worker = CodexInventor(
            creator=creator,
            evaluator=evaluator,
            research_provider=self.research,
        )
        with mock.patch.dict(
            os.environ, {"WORKSHOP_AGENT_WORKERS": "disabled"}, clear=True
        ):
            result = Workshop(
                self.inventor,
                "moving-machines",
                tools=WorkshopTools(invent=worker),
                runtime_root=self.root / "runtime",
            ).run(self.context().wish, playtest_rounds=2)
        self.assertEqual((result.status, result.job), ("waiting", "make"))
        self.assertEqual(result.needs[0].capability, "model-and-cad-maker")
        self.assertIsNotNone(result.invented)
        self.assertEqual(result.invented.concept["title"], "Trotter")
        self.assertEqual(result.to_dict()["invented"]["score"], 92)

    def test_missing_research_provider_fails_closed_before_concept_generation(self):
        creator = FakeCodex("gpt-5.6-terra", [action("Should not run")])
        evaluator = FakeCodex("gpt-5.6-terra", [verdict(99, "Should not run")])
        evaluator.reasoning_effort = "low"
        with self.assertRaises(WaitingFor) as caught:
            CodexInventor(
                creator=creator,
                evaluator=evaluator,
                research_provider=None,
            )(self.context())
        self.assertEqual(
            [need.capability for need in caught.exception.needs],
            ["source-backed-design-research"],
        )
        self.assertEqual(creator.prompts, [])
        self.assertEqual(evaluator.prompts, [])

    def test_safe_default_provider_fetches_and_hashes_real_response_evidence(self):
        context = InventContext(
            Wish.create(
                "private-walker",
                "Build Dr. Vinkent Nguyen a wind-up portrait of Moonbeam, our family dog.",
                context={"customer_name": "Vinkent Nguyen"},
            ),
            load_taste(self.inventor),
            ToyBlueprint.for_lane("moving-machines"),
            (self.root / "private-research").absolute(),
        )
        transport = FakeResearchHTTP()
        provider = PublicHTTPResearchProvider(transport=transport)
        research = provider(context)

        research.assert_context(context)
        self.assertEqual(research.provider, "workshop-public-http-research")
        self.assertEqual(
            [source.source_id for source in research.sources],
            ["wikipedia-101", "wikipedia-202", "cpsc-toy-safety"],
        )
        self.assertEqual(
            research.sources[0].evidence_sha256,
            hashlib.sha256(research.sources[0].evidence.encode("utf-8")).hexdigest(),
        )
        self.assertIn("small parts", research.sources[-1].evidence)
        self.assertEqual(len(transport.requests), 2)
        for request in transport.requests:
            requested = urllib.parse.unquote(request.url).casefold()
            self.assertNotIn("vinkent", requested)
            self.assertNotIn("nguyen", requested)
            self.assertNotIn("moonbeam", requested)
            self.assertNotIn("customer_name", requested)
            self.assertLessEqual(request.timeout_seconds, 8.0)
            self.assertLessEqual(request.max_bytes, 512 * 1024)
        query = urllib.parse.parse_qs(
            urllib.parse.urlsplit(transport.requests[0].url).query
        )["gsrsearch"][0]
        self.assertEqual(
            query, "mechanical toy automaton mechanism kinetic design"
        )

    def test_public_provider_rejects_untrusted_or_unusable_http_results(self):
        cases = {
            "off-allowlist redirect": lambda request: PublicResearchHTTPResponse(
                "https://evil.example/collect", 200, "application/json", b"{}"
            ),
            "wrong content type": lambda request: PublicResearchHTTPResponse(
                request.url, 200, "text/html", b"<html>not JSON</html>"
            ),
            "non-success status": lambda request: PublicResearchHTTPResponse(
                request.url, 503, "application/json", b'{"error":"busy"}'
            ),
            "oversize": lambda request: PublicResearchHTTPResponse(
                request.url,
                200,
                "application/json",
                b"x" * (request.max_bytes + 1),
            ),
            "no results": lambda request: PublicResearchHTTPResponse(
                request.url,
                200,
                "application/json",
                b'{"query":{"pages":[]}}',
            ),
        }
        for label, mediawiki in cases.items():
            with self.subTest(label=label):
                provider = PublicHTTPResearchProvider(
                    transport=FakeResearchHTTP(mediawiki=mediawiki)
                )
                with self.assertRaises(InventResearchUnavailable):
                    provider(self.context())

        provider = PublicHTTPResearchProvider(
            transport=FakeResearchHTTP(
                cpsc=lambda request: PublicResearchHTTPResponse(
                    "https://evil.example/collect",
                    200,
                    "text/html",
                    b"<html><body>Toy safety evidence that is long enough.</body></html>",
                )
            )
        )
        with self.assertRaises(InventResearchUnavailable):
            provider(self.context())

    def test_public_provider_adds_a_pinned_mapping_only_for_science(self):
        provider = PublicHTTPResearchProvider(transport=FakeResearchHTTP())
        science = provider(self.context("holdable-science"))
        moving = provider(self.context("moving-machines"))

        mapping = next(
            source
            for source in science.sources
            if source.source_id == "workshop-qualitative-science-map"
        )
        self.assertIn('"scale_ratio":1.0', mapping.evidence)
        self.assertIn("not a measurement or prediction instrument", mapping.evidence)
        self.assertNotIn(
            "workshop-qualitative-science-map", moving.source_ids
        )
        science_sources = [
            source
            for source in science.sources
            if source.source_id.startswith("wikipedia-")
        ]
        self.assertTrue(science_sources)
        self.assertTrue(all("science" in source.topics for source in science_sources))

    def test_science_contract_rejects_a_paraphrase_before_reward(self):
        proposed = action("Paraphrased science", "holdable-science")
        proposed["selected"]["lane_contract"]["source_model"]["model"] = (
            "The linkage approximately visualizes phase."
        )
        creator = FakeCodex("gpt-5.6-terra", [proposed])
        evaluator = FakeCodex("gpt-5.6-luna", [verdict(99, "Must not score")])
        evaluator.reasoning_effort = "low"
        with self.assertRaises(WaitingFor) as caught:
            CodexInventor(
                creator=creator,
                evaluator=evaluator,
                research_provider=self.research,
            )(self.context("holdable-science"))
        self.assertEqual(
            caught.exception.needs[0].capability, "codex-industrial-design"
        )
        self.assertEqual(evaluator.prompts, [])

    def test_workshop_authored_source_cannot_be_relabelled_as_science_authority(self):
        context = self.context("holdable-science")
        contract = lane_contract("holdable-science")
        simplification = contract["simplifications"][0]
        self_evidence = "\n".join(
            (
                contract["source_model"]["phenomenon"],
                contract["source_model"]["model"],
                json.dumps(
                    contract["scale"], sort_keys=True, separators=(",", ":")
                ),
                "%s %s"
                % (
                    simplification["simplification"],
                    simplification["disclosed_limit"],
                ),
            )
        )
        self_source = InventResearchSource(
            "workshop-relabeled-map",
            "Relabelled Workshop mapping",
            "Autonomous Workshop",
            "https://github.com/autonomous-ai/autonomous-workshop/blob/main/docs/SCIENCE_PROOF_BOUNDARY.md",
            "2026-08-25T00:00:00+00:00",
            self_evidence,
            ("prior-art", "use-context", "science"),
        )
        safety = InventResearchSource(
            "safety-source",
            "Safety source",
            "Fixture Safety Office",
            "https://example.com/safety/toys",
            "2026-08-25T00:00:00+00:00",
            "Accessible parts require an explicit hazard review.",
            ("safety",),
        )
        research = InventResearch(
            json_sha256(context.wish.to_dict()),
            context.taste.sha256,
            context.blueprint.sha256,
            context.blueprint.lane,
            "fixture-self-source-provider",
            "1.0.0",
            "a" * 64,
            (self_source, safety),
        )
        proposed = action("Relabelled authority", "holdable-science")
        proposed["research"]["patterns"][0]["source_ids"] = [
            self_source.source_id
        ]
        proposed["selected"]["research_source_ids"] = [
            self_source.source_id,
            safety.source_id,
        ]
        proposed["selected"]["lane_contract"]["source_model"]["source_ids"] = [
            self_source.source_id
        ]
        creator = FakeCodex("gpt-5.6-terra", [proposed])
        evaluator = FakeCodex("gpt-5.6-luna", [verdict(99, "Must not score")])
        evaluator.reasoning_effort = "low"

        with self.assertRaises(WaitingFor) as caught:
            CodexInventor(
                creator=creator,
                evaluator=evaluator,
                research_provider=lambda unused_context: research,
            )(context)

        self.assertEqual(
            caught.exception.needs[0].capability, "codex-industrial-design"
        )
        self.assertEqual(evaluator.prompts, [])

    def test_science_contract_waits_when_exact_sources_are_unrelated_to_wish(self):
        creator = FakeCodex(
            "gpt-5.6-terra", [action("Unrelated science", "holdable-science")]
        )
        evaluator = FakeCodex("gpt-5.6-luna", [verdict(99, "Must not score")])
        evaluator.reasoning_effort = "low"
        with self.assertRaises(WaitingFor) as caught:
            CodexInventor(
                creator=creator,
                evaluator=evaluator,
                research_provider=self.research,
            )(
                self.context(
                    "holdable-science",
                    "A tactile model of ocean tides and lunar gravity",
                )
            )
        self.assertEqual(
            caught.exception.needs[0].capability, "science-source-relevance"
        )
        self.assertEqual(evaluator.prompts, [])

    def test_redirect_handler_blocks_before_following_an_untrusted_host(self):
        from inventor_workshop.agent_invent import _AllowlistedRedirectHandler

        handler = _AllowlistedRedirectHandler(("en.wikipedia.org",))
        request = urllib.request.Request(
            "https://en.wikipedia.org/w/api.php?action=query"
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://evil.example/collect",
            )
        caught.exception.close()

    def test_public_request_rejects_userinfo_controls_and_non_https_urls(self):
        for url in (
            "https://user:secret@en.wikipedia.org/w/api.php",
            "https://en.wikipedia.org/w/api.php\nignored",
            "http://en.wikipedia.org/w/api.php",
        ):
            with self.subTest(url=url), self.assertRaises(
                InventResearchUnavailable
            ):
                PublicResearchHTTPRequest(
                    url,
                    ("en.wikipedia.org",),
                    ("application/json",),
                    1024,
                    1.0,
                )

    def test_unavailable_research_provider_returns_a_typed_wait(self):
        def unavailable(context):
            del context
            raise InventResearchUnavailable("retrieval service offline")

        creator = FakeCodex("gpt-5.6-terra", [action("Should not run")])
        evaluator = FakeCodex("gpt-5.6-terra", [verdict(99, "Should not run")])
        evaluator.reasoning_effort = "low"
        with self.assertRaises(WaitingFor) as caught:
            CodexInventor(
                creator=creator,
                evaluator=evaluator,
                research_provider=unavailable,
            )(self.context())
        self.assertEqual(
            caught.exception.needs[0].capability,
            "source-backed-design-research",
        )
        self.assertEqual(creator.prompts, [])

    def test_hard_tension_prevents_a_high_numeric_score_from_passing(self):
        blocked = verdict(99, "The idea violates Taste.")
        blocked["hard_tensions"] = ["The core interaction is outside this lane."]
        creator = FakeCodex("gpt-5.6-terra", [action("Wrong lane")])
        evaluator = FakeCodex("gpt-5.6-terra", [blocked])
        evaluator.reasoning_effort = "low"
        invented = CodexInventor(
            creator=creator,
            evaluator=evaluator,
            research_provider=self.research,
            goal=85,
            max_steps=1,
        )(self.context())
        self.assertFalse(invented.passed)
        self.assertEqual(invented.score, 84)
        self.assertFalse(invented.concept["reward_loop"]["reached_goal"])

    def test_durable_invent_cost_cap_is_typed_and_never_lowers_the_goal(self):
        original = self.context()
        context = InventContext(
            original.wish,
            original.taste,
            original.blueprint,
            original.workspace,
            original.world_inputs,
            (self.root / "durable-invent-cost-cap").absolute(),
        )
        creator = FakeCodex(
            "gpt-5.6-terra", [action("Attempt one"), action("Attempt two")]
        )
        evaluator = FakeCodex(
            "gpt-5.6-luna",
            [
                verdict(74, "Improve the first concept."),
                verdict(76, "Improve the second concept."),
            ],
        )
        evaluator.reasoning_effort = "low"

        with self.assertRaises(WaitingFor) as caught:
            CodexInventor(
                creator=creator,
                evaluator=evaluator,
                research_provider=self.research,
                goal=85,
                max_steps=1,
                max_total_steps=2,
            )(context)

        self.assertEqual(
            caught.exception.needs[0].capability,
            "industrial-design-cost-cap",
        )
        records = sorted(
            (context.reward_journal / "steps").glob("[0-9]*.json")
        )
        self.assertEqual(len(records), 2)
        self.assertTrue(
            all(
                json.loads(path.read_text(encoding="utf-8"))["reward"]["goal"]
                == 85
                for path in records
            )
        )

    def test_concept_model_cannot_fabricate_a_citation(self):
        fabricated = action("Citation laundering")
        fabricated["research"]["patterns"][0]["source_ids"] = ["invented-source"]
        creator = FakeCodex("gpt-5.6-terra", [fabricated])
        evaluator = FakeCodex("gpt-5.6-terra", [verdict(99, "Should not score")])
        evaluator.reasoning_effort = "low"
        with self.assertRaises(WaitingFor) as caught:
            CodexInventor(
                creator=creator,
                evaluator=evaluator,
                research_provider=self.research,
            )(self.context())
        self.assertEqual(caught.exception.needs[0].capability, "codex-industrial-design")
        self.assertEqual(evaluator.prompts, [])

    def test_research_is_bound_to_the_exact_wish_taste_and_lane(self):
        wrong = self.research()

        def stale_provider(context):
            return InventResearch(
                wish_sha256="0" * 64,
                taste_sha256=wrong.taste_sha256,
                blueprint_sha256=wrong.blueprint_sha256,
                lane=wrong.lane,
                provider=wrong.provider,
                provider_version=wrong.provider_version,
                provider_config_sha256=wrong.provider_config_sha256,
                sources=wrong.sources,
            )

        creator = FakeCodex("gpt-5.6-terra", [action("Should not run")])
        evaluator = FakeCodex("gpt-5.6-terra", [verdict(99, "Should not run")])
        evaluator.reasoning_effort = "low"
        with self.assertRaisesRegex(ContractError, "different Workshop inputs"):
            CodexInventor(
                creator=creator,
                evaluator=evaluator,
                research_provider=stale_provider,
            )(self.context())
        self.assertEqual(creator.prompts, [])

    def test_explicit_custom_invent_overrides_the_shared_default(self):
        def custom(context):
            return context

        tools = configured_workshop_tools(WorkshopTools(invent=custom))
        self.assertIs(tools.invent, custom)

    def test_shared_invent_is_installed_for_a_taste_only_inventor(self):
        tools = configured_workshop_tools(WorkshopTools())
        self.assertIsInstance(tools.invent, CodexInventor)
        self.assertIsInstance(
            tools.invent.research_provider, PublicHTTPResearchProvider
        )


if __name__ == "__main__":
    unittest.main()
