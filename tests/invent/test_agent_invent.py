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

from workshop.invent.agent import (
    CodexInventor,
    CodexNativeResearchProvider,
    InventResearch,
    InventResearchSource,
    InventResearchUnavailable,
    PublicHTTPResearchProvider,
    PublicResearchHTTPRequest,
    PublicResearchHTTPResponse,
    REWARD_WEIGHTS,
)
from workshop.bootstrap import configured_workshop_tools
from workshop.errors import ContractError
from workshop.invent.contracts import InventContext
from workshop.outcomes import WaitingFor
from workshop.wish import Wish
from workshop.runtime.reward import json_sha256
from workshop.contributors.taste import load_taste
from workshop.product.blueprints import ToyBlueprint
from workshop.workflow.engine import Workshop, WorkshopTools


LANES = (
    "classics-made-yours",
    "invented-games",
    "moving-machines",
    "holdable-science",
    "little-worlds",
)


def pinned_game_strategy(base=20_260_825):
    return (
        "Run exactly 1,000 complete deterministic games indexed g=0 through 999. "
        f"For game g, use seed ({base}+g) mod 2^32 with Mulberry32 and log every "
        "generated unsigned 32-bit value. Let "
        "policy_order=[optimizing,social,exploratory,adversarial], q=g mod 16, "
        "seat_0_policy=policy_order[floor(q/4)], "
        "seat_1_policy=policy_order[q mod 4], and first_seat=g mod 2. Record a "
        "full trace for every game containing game index, seed, ordered policy pair, "
        "first_seat, turn, active seat and policy, pre-state, legal actions, intended "
        "and chosen action, removed item IDs, post-state, pre/post prior action, "
        "pre/post policy memory, pre/post PRNG state, every generated unsigned 32-bit "
        "value, terminal flag, terminal winner and loser, and move count."
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
        "invented-games": {
            "schema_version": 1,
            "lane": "invented-games",
            "complete_rules": {
                "setup": ["Each player places three trail markers on their edge."],
                "turn_sequence": ["Move one walker, then rotate one trail tile."],
                "legal_actions": ["Move to an adjacent unoccupied connected tile."],
                "terminal_conditions": ["End immediately when one walker reaches the far edge."],
                "scoring": ["The first walker to reach the far edge wins."],
                "tie_breakers": ["If both arrive in one effect, fewer trail markers wins."],
            },
            "simulator_design": {
                "state_variables": ["walker positions", "trail rotations", "active player"],
                "legal_action_generator": "Enumerate adjacent connected empty destinations and legal rotations.",
                "transition_model": "Apply the chosen move and rotation, then alternate the active player.",
                "terminal_check": "Check far-edge arrival after every complete action.",
                "score_calculation": "Return win, loss, or the defined marker-count tie break.",
                "fixed_seed_strategy": pinned_game_strategy(),
                "player_policies": [
                    "optimizing",
                    "social",
                    "exploratory",
                    "adversarial",
                ],
                "minimum_complete_games": 1_000,
            },
        },
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
                "source_ids": ["mechanism-source"],
            },
            "simplifications": [
                {
                    "simplification": "Friction and elastic deformation are omitted from the visible model.",
                    "reason": "The first interaction teaches phase, not energy loss.",
                    "disclosed_limit": "The object is qualitative and does not predict real-system amplitude.",
                }
            ],
            "scale": {
                "real_quantity": "One full phenomenon cycle",
                "model_quantity": "One full handle rotation",
                "scale_ratio": 1.0,
                "units": "cycle per rotation",
            },
            "interaction": {
                "user_action": "Turn the handle through one revolution.",
                "observable_response": "Markers reveal their relative phase around the cycle.",
                "teaching_point": "Equal frequency can coexist with different phase.",
                "misuse_boundary": "It is not a calibrated measurement instrument.",
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
            "research_source_ids": ["mechanism-source", "safety-source"],
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


class FakeNativeResearchCodex:
    cli_version = "9.8.7"
    model = "gpt-5.6-luna"
    reasoning_effort = "low"

    def __init__(self, *, used_search=True, payload=None):
        self.last_used_web_search = False
        self.used_search = used_search
        self.payload = payload or {
            "sources": [
                {
                    "title": "Automata mechanisms",
                    "publisher": "Smithsonian Institution",
                    "url": "https://www.si.edu/spotlight/automata",
                    "evidence": (
                        "Historic automata use constrained mechanisms to turn stored or "
                        "applied energy into legible repeated motion."
                    ),
                    "topics": ["prior-art", "mechanism"],
                },
                {
                    "title": "Toy Safety Business Guidance",
                    "publisher": "U.S. Consumer Product Safety Commission",
                    "url": "https://www.cpsc.gov/Business--Manufacturing/Business-Education/Toy-Safety",
                    "evidence": (
                        "Official toy guidance identifies mechanical hazards and age-appropriate "
                        "product requirements that must be assessed for the finished object."
                    ),
                    "topics": ["safety"],
                },
                {
                    "title": "Why adults play",
                    "publisher": "The Strong National Museum of Play",
                    "url": "https://www.museumofplay.org/blog/why-adults-play/",
                    "evidence": (
                        "Adult play supports exploration, social connection, and intrinsically "
                        "motivated interaction beyond a single task outcome."
                    ),
                    "topics": ["use-context"],
                },
            ]
        }
        self.calls = []

    def invoke(self, *, prompt, schema, workspace, native_web_search=False):
        self.calls.append((prompt, schema, workspace, native_web_search))
        self.last_used_web_search = self.used_search
        return copy.deepcopy(self.payload)


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

    def context(self, lane="moving-machines"):
        return InventContext(
            Wish.create("walking-dog", "A wind-up version of my dog that walks"),
            load_taste(self.inventor),
            ToyBlueprint.for_lane(lane),
            (self.root / ("invent-workspace-" + lane)).absolute(),
        )

    def research(self, context=None):
        context = context or self.context()
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
            sources=(
                InventResearchSource(
                    "mechanism-source",
                    "Mechanism reference",
                    "Fixture Engineering Archive",
                    "https://example.com/mechanisms/wind-up",
                    "2026-08-25T00:00:00+00:00",
                    "A wound spring can release energy through a constrained repeated motion.",
                    ("prior-art", "use-context", "mechanism"),
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
            ),
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
                self.assertEqual(contract["schema_version"], 1)
                self.assertEqual(contract["lane"], lane)
                self.assertEqual(
                    invented.concept["evidence"]["lane_contract_schema_version"], 1
                )
                self.assertEqual(
                    invented.concept["evidence"]["lane_contract_sha256"],
                    json_sha256(contract),
                )
                self.assertIn(lane, creator.prompts[0][0])
                self.assertIn(lane, evaluator.prompts[0][0])
                schema = creator.prompts[0][1]
                lane_schema = schema["properties"]["selected"]["properties"][
                    "lane_contract"
                ]
                self.assertNotIn("oneOf", lane_schema)
                self.assertFalse(lane_schema["additionalProperties"])
                self.assertEqual(lane_schema["properties"]["lane"]["const"], lane)
                observed_schema_lanes.add(lane)
        self.assertEqual(observed_schema_lanes, set(LANES))

    def test_creator_schema_encodes_directly_expressible_trusted_validation(self):
        creator = FakeCodex(
            "gpt-5.6-terra", [action("Chosen little world", "little-worlds")]
        )
        evaluator = FakeCodex(
            "gpt-5.6-terra", [verdict(92, "Typed handoff is ready.")]
        )
        evaluator.reasoning_effort = "low"
        CodexInventor(
            creator=creator,
            evaluator=evaluator,
            research_provider=self.research,
        )(self.context("little-worlds"))

        prompt, schema, _ = creator.prompts[0]
        selected = schema["properties"]["selected"]["properties"]
        research = schema["properties"]["research"]["properties"]
        direction = schema["properties"]["directions"]["items"]["properties"]
        allowed_sources = ["mechanism-source", "safety-source"]
        source_schemas = (
            research["patterns"]["items"]["properties"]["source_ids"]["items"],
            research["opportunities"]["items"]["properties"]["source_ids"]["items"],
            selected["research_source_ids"]["items"],
        )
        for source_schema in source_schemas:
            self.assertEqual(source_schema["enum"], allowed_sources)
            self.assertEqual(source_schema["minLength"], 1)
            self.assertEqual(source_schema["maxLength"], 128)
        self.assertEqual(selected["title"]["minLength"], 1)
        self.assertEqual(selected["title"]["maxLength"], 300)
        self.assertEqual(selected["title"]["pattern"], r"\S")
        self.assertEqual(direction["name"]["minLength"], 1)
        self.assertEqual(direction["risks"]["minItems"], 0)
        self.assertEqual(direction["risks"]["maxItems"], 30)
        self.assertEqual(research["assumptions"]["items"]["minLength"], 1)
        world = selected["lane_contract"]["properties"]
        reference_id = world["consented_references"]["items"]["properties"][
            "reference_id"
        ]
        mapped_id = world["feature_to_form_map"]["items"]["properties"][
            "reference_id"
        ]
        self.assertEqual(reference_id["pattern"], r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
        self.assertEqual(mapped_id["pattern"], reference_id["pattern"])
        self.assertIn("must exactly copy a consented reference_id", prompt)
        self.assertIn("must not overlap", prompt)
        self.assertIn("Map every consented reference at least once", prompt)

    def test_science_schema_limits_citations_to_exact_research_evidence(self):
        creator = FakeCodex(
            "gpt-5.6-terra", [action("Chosen science", "holdable-science")]
        )
        evaluator = FakeCodex(
            "gpt-5.6-terra", [verdict(92, "Typed handoff is ready.")]
        )
        evaluator.reasoning_effort = "low"
        CodexInventor(
            creator=creator,
            evaluator=evaluator,
            research_provider=self.research,
        )(self.context("holdable-science"))

        prompt, schema, _ = creator.prompts[0]
        source_schema = schema["properties"]["selected"]["properties"][
            "lane_contract"
        ]["properties"]["source_model"]["properties"]["source_ids"]["items"]
        self.assertEqual(source_schema["enum"], ["mechanism-source", "safety-source"])
        self.assertIn("must exactly copy one supplied research source_id", prompt)

    def test_invented_game_schema_and_prompt_pin_the_playtest_protocol(self):
        creator = FakeCodex(
            "gpt-5.6-terra", [action("Chosen game", "invented-games")]
        )
        evaluator = FakeCodex(
            "gpt-5.6-terra", [verdict(92, "Pinned game handoff is ready.")]
        )
        evaluator.reasoning_effort = "low"
        invented = CodexInventor(
            creator=creator,
            evaluator=evaluator,
            research_provider=self.research,
        )(self.context("invented-games"))

        prompt, schema, _ = creator.prompts[0]
        simulator = schema["properties"]["selected"]["properties"][
            "lane_contract"
        ]["properties"]["simulator_design"]["properties"]
        self.assertEqual(simulator["seed_base_u32"]["minimum"], 0)
        self.assertEqual(simulator["seed_base_u32"]["maximum"], 2**32 - 1)
        self.assertNotIn("minimum_complete_games", simulator)
        self.assertNotIn("fixed_seed_strategy", simulator)
        self.assertNotIn("player_policies", simulator)
        self.assertIn("Workshop—not the creator—injects", prompt)
        self.assertIn("seed_base_u32", prompt)
        self.assertEqual(
            invented.concept["lane_contract"]["simulator_design"]
            ["fixed_seed_strategy"],
            pinned_game_strategy(),
        )

    def test_invented_game_seed_choice_is_expanded_into_platform_protocol(self):
        proposed = action("Platform-sealed game", "invented-games")
        simulator = proposed["selected"]["lane_contract"]["simulator_design"]
        for field in (
            "fixed_seed_strategy",
            "player_policies",
            "minimum_complete_games",
        ):
            simulator.pop(field)
        simulator["seed_base_u32"] = 4_294_967_295
        creator = FakeCodex("gpt-5.6-terra", [proposed])
        evaluator = FakeCodex(
            "gpt-5.6-terra", [verdict(92, "Pinned protocol is valid.")]
        )
        evaluator.reasoning_effort = "low"

        invented = CodexInventor(
            creator=creator,
            evaluator=evaluator,
            research_provider=self.research,
        )(self.context("invented-games"))

        sealed = invented.concept["lane_contract"]["simulator_design"]
        self.assertNotIn("seed_base_u32", sealed)
        self.assertEqual(sealed["minimum_complete_games"], 1_000)
        self.assertEqual(
            sealed["player_policies"],
            ["optimizing", "social", "exploratory", "adversarial"],
        )
        self.assertIn("seed (4294967295+g)", sealed["fixed_seed_strategy"])

    def test_invented_game_protocol_accepts_unsigned_seed_base_boundaries(self):
        for base in (0, 2**32 - 1):
            with self.subTest(base=base):
                proposed = action("Boundary game", "invented-games")
                proposed["selected"]["lane_contract"]["simulator_design"][
                    "fixed_seed_strategy"
                ] = pinned_game_strategy(base)
                creator = FakeCodex("gpt-5.6-terra", [proposed])
                evaluator = FakeCodex(
                    "gpt-5.6-terra", [verdict(92, "Pinned protocol is valid.")]
                )
                evaluator.reasoning_effort = "low"
                invented = CodexInventor(
                    creator=creator,
                    evaluator=evaluator,
                    research_provider=self.research,
                )(self.context("invented-games"))
                self.assertTrue(invented.passed)
                self.assertIn(
                    "seed (%d+g)" % base,
                    invented.concept["lane_contract"]["simulator_design"]
                    ["fixed_seed_strategy"],
                )

    def test_invented_game_protocol_mismatches_stop_before_reward(self):
        def changed(*, strategy=None, games=1_000, policies=None):
            contract = lane_contract("invented-games")
            simulator = contract["simulator_design"]
            simulator["minimum_complete_games"] = games
            if strategy is not None:
                simulator["fixed_seed_strategy"] = strategy
            if policies is not None:
                simulator["player_policies"] = policies
            return contract

        canonical = pinned_game_strategy()
        live_event_21 = (
            "Run exactly 1,024 complete deterministic games with integer seeds 0 "
            "through 1,023. Define policy_order = [optimizing, social, exploratory, "
            "adversarial]. For seed s, assign policies in 64-game blocks and set "
            "starter_seat=s mod 2. Initialize xorshift32 from s. Record seed, policies, "
            "starter, every action, state before and after every action, terminal "
            "winner, and move count."
        )
        cases = {
            "live event 21 protocol": changed(strategy=live_event_21, games=1_024),
            "too few games": changed(games=999),
            "too many games": changed(games=1_001),
            "unsupported PRNG": changed(
                strategy=canonical.replace("Mulberry32", "xorshift32")
            ),
            "unparseable seed": changed(
                strategy=canonical.replace("seed (20260825+g)", "seed g")
            ),
            "seed base outside u32": changed(strategy=pinned_game_strategy(2**32)),
            "missing u32 modulo": changed(
                strategy=canonical.replace(" mod 2^32", "")
            ),
            "wrong pairing schedule": changed(
                strategy=canonical.replace("q=g mod 16", "q=floor(g/64)")
            ),
            "wrong seat mapping": changed(
                strategy=canonical.replace(
                    "seat_0_policy=policy_order[floor(q/4)]",
                    "seat_0_policy=policy_order[q mod 4]",
                )
            ),
            "wrong first seat schedule": changed(
                strategy=canonical.replace("first_seat=g mod 2", "first_seat=0")
            ),
            "wrong policy order": changed(
                policies=["social", "optimizing", "exploratory", "adversarial"]
            ),
            "incomplete trace": changed(
                strategy=canonical.replace("pre/post policy memory, ", "")
            ),
        }

        for label, contract in cases.items():
            with self.subTest(label=label):
                proposed = action("Rejected game", "invented-games")
                proposed["selected"]["lane_contract"] = contract
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
                    )(self.context("invented-games"))
                self.assertEqual(
                    caught.exception.needs[0].capability,
                    "codex-industrial-design",
                )
                self.assertEqual(evaluator.prompts, [])

    def test_each_lane_rejects_a_malformed_contract_before_reward_or_make(self):
        malformed = {}
        classic = lane_contract("classics-made-yours")
        classic.pop("rules_preserved")
        malformed["classics-made-yours"] = classic

        invented_game = lane_contract("invented-games")
        invented_game["simulator_design"]["minimum_complete_games"] = 999
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

    def test_codex_native_research_uses_search_without_disclosing_private_wish(self):
        context = InventContext(
            Wish.create(
                "private-walker",
                "Build Dr. Vinkent Nguyen a wind-up portrait of Moonbeam, our family dog.",
                context={"customer_name": "Vinkent Nguyen"},
            ),
            load_taste(self.inventor),
            ToyBlueprint.for_lane("moving-machines"),
            (self.root / "native-research").absolute(),
        )
        runtime = FakeNativeResearchCodex()
        research = CodexNativeResearchProvider(researcher=runtime)(context)

        research.assert_context(context)
        self.assertEqual(research.provider, "codex-native-web-search")
        self.assertEqual(len(research.sources), 3)
        self.assertTrue(
            all(source.source_id.startswith("codex-search-") for source in research.sources)
        )
        prompt, schema, workspace, native_web_search = runtime.calls[0]
        self.assertTrue(native_web_search)
        self.assertEqual(workspace, context.workspace)
        self.assertIn("native web-search tool", prompt)
        self.assertIn("moving-machines", prompt)
        self.assertIn("prior-art", prompt)
        self.assertEqual(schema["properties"]["sources"]["maxItems"], 8)
        private_prompt = prompt.casefold()
        for secret in ("vinkent", "nguyen", "moonbeam", "customer_name"):
            self.assertNotIn(secret, private_prompt)

    def test_codex_native_research_fails_closed_without_search_event(self):
        runtime = FakeNativeResearchCodex(used_search=False)
        with self.assertRaisesRegex(
            InventResearchUnavailable, "native web-search event"
        ):
            CodexNativeResearchProvider(researcher=runtime)(self.context())

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
            query,
            "mechanical toy automata and kinetic mechanism prior art; official "
            "moving-part toy safety guidance; adult desk-toy use context",
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

    def test_redirect_handler_blocks_before_following_an_untrusted_host(self):
        from workshop.invent.agent import _AllowlistedRedirectHandler

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
            tools.invent.research_provider, CodexNativeResearchProvider
        )


if __name__ == "__main__":
    unittest.main()
