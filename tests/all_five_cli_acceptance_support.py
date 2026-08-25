"""Deterministic external boundaries for installed all-five orchestration.

This module is copied next to an installed Workshop wheel and imported from a
``.pth`` file.  It deliberately keeps the production Manager-owned engine,
shared stage workers, release policy, durable store, Instructions handoff, and
Factory adapters in the path.  Only external boundaries are replaced:

* Terra/Luna structured model responses;
* public Invent research;
* the locked-CAD command transport and exact slicer process;
* deterministic raw-free world-reference and World-Playtest envelopes; and
* Factory HTTP.

Every fake returns the real production schema.  The production Manager,
``configured_workshop_tools`` composition, stage classes, release validators,
durable state, and Factory adapters stay in the path.  This is not live Factory,
real CAD-kernel, physical, or routing-model quality evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from email.parser import BytesParser
from email.policy import default as email_policy
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import zipfile

from workshop_all_five_acceptance_config import LOG_PATH

from inventor_workshop.agent_instructions import RewardedInstructions
from inventor_workshop.agent_invent import (
    CodexInventor,
    InventResearch,
    InventResearchSource,
    PublicHTTPResearchProvider,
)
import inventor_workshop.agent_invent as agent_invent
import inventor_workshop.agent_playtest as agent_playtest
from inventor_workshop.agent_make import (
    CodexMaker,
    LockedCadSkillBuilder,
)
from inventor_workshop.agent_playtest import LaneAwarePlaytester
from inventor_workshop.codex_runtime import CodexStructuredRunner
from inventor_workshop.factory_agent import FactoryAgentSession
import inventor_workshop.factory_agent as factory_agent
from inventor_workshop.moving_machine import WorkshopMovingMachineVerifier
from inventor_workshop.reward_loop import json_sha256
from inventor_workshop.semantic_manager import CodexSemanticManager
from inventor_workshop.shop import HttpResponse
from inventor_workshop.world_reference_vault import (
    WorldReferenceDescriptor,
    WorldReferenceReceipt,
    WorldReferenceScope,
)
from inventor_workshop.world_service import (
    WorldEvidenceCase,
    WorldEvidenceReference,
    WorldPlaytestEvidence,
    WorldProviderIdentity,
)
from inventor_workshop.workshop import WorkshopTools


LANE_BY_INVENTOR = {
    "alice": "classics-made-yours",
    "bob": "moving-machines",
    "eve": "little-worlds",
    "ivy": "holdable-science",
    "leo": "invented-games",
}
_WISH_PATTERN_RULES = {
    "classics-made-yours": (
        r"\bcheckers\b",
        r"\brules?\b.{0,40}\bunchanged\b",
        r"\bknown\b.{0,30}\bclassic\b",
    ),
    "moving-machines": (
        r"\bwind[- ]up\b",
        r"\bwalking mechanism\b",
        r"\bkinetic machine\b",
    ),
    "little-worlds": (
        r"\bminiature\b.{0,50}\bworld\b",
        r"\bnight market world\b",
        r"\bfictional\b.{0,40}\blantern arch\b",
    ),
    "holdable-science": (
        r"\bcoupled periodic motion\b",
        r"\btruthful phenomenon\b",
        r"\bscience\b.{0,30}\bhold\b",
    ),
    "invented-games": (
        r"\bbrand[- ]new\b.{0,50}\bstrategy game\b",
        r"\bseven[- ]token\b",
        r"\boriginal\b.{0,30}\btabletop game\b",
    ),
}
_TASTE_FIT_ANCHORS = {
    "classics-made-yours": (
        "known tabletop classics unmistakably personal",
        "preserving their rules",
        "known tabletop classic unmistakably yours",
    ),
    "moving-machines": (
        "wish-specific printable kinetic machines",
        "mechanism and motion create the spectacle",
        "3d-printable moving machines",
    ),
    "little-worlds": (
        "recognizable cinematic little world",
        "turns your real world into a little epic one",
        "turns a person's real dog, gear, space, or relationships",
    ),
    "holdable-science": (
        "science and mathematics physically legible",
        "science and mathematics you can hold",
        "truthful phenomenon",
    ),
    "invented-games": (
        "original printable tabletop games",
        "invents beautiful 3d-printable games",
        "deep ai-player simulation",
    ),
}
ACCEPTANCE_FACTORY_PASSWORD = "installed-acceptance-credential"
_PROCESS_SELECTED_INVENTOR = None


def _world_personalization():
    return {
        "consented_references": [
            {
                "reference_id": "customer-market",
                "subject": "The customer's fictional night market",
                "consent_or_rights_basis": (
                    "The customer authored and supplied the fictional reference."
                ),
                "allowed_features": ["violet lantern arch"],
                "excluded_features": ["private address"],
            }
        ],
        "feature_to_form_map": [
            {
                "reference_id": "customer-market",
                "reference_feature": "violet lantern arch",
                "physical_form": "A violet arch frames the market entrance.",
                "recognition_test": (
                    "The arch remains recognizable without a caption."
                ),
            }
        ],
    }


def _log(event: str, **details) -> None:
    record = {
        "event": event,
        "pid": os.getpid(),
        "argv": list(sys.argv),
        **details,
    }
    payload = (
        json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    descriptor = os.open(
        str(LOG_PATH), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600
    )
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


_log("boundary-loaded")


def _wish_pattern(wish) -> str:
    if not isinstance(wish, dict) or not isinstance(wish.get("objective"), str):
        raise AssertionError("semantic boundary received no exact Wish objective")
    objective = wish["objective"].casefold()
    matched = [
        lane
        for lane, rules in _WISH_PATTERN_RULES.items()
        if any(re.search(rule, objective) for rule in rules)
    ]
    if len(matched) != 1:
        raise AssertionError(
            "acceptance Wish has no unique play pattern: %s" % sorted(matched)
        )
    return matched[0]


def _taste_fit(lane: str, content: str) -> int:
    if lane not in _TASTE_FIT_ANCHORS or not isinstance(content, str):
        raise AssertionError("semantic boundary received invalid Taste content")
    lowered = " ".join(content.casefold().split())
    return sum(30 for anchor in _TASTE_FIT_ANCHORS[lane] if anchor in lowered)


def _rank_tastes(lane: str, candidates, *, content_key: str):
    ranked = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise AssertionError("semantic boundary received a malformed candidate")
        inventor_id = candidate.get("id")
        content = candidate.get(content_key)
        if not isinstance(inventor_id, str) or not isinstance(content, str):
            raise AssertionError("semantic boundary received incomplete Taste content")
        ranked.append(
            {
                "inventor_id": inventor_id,
                "score": _taste_fit(lane, content),
                "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
        )
    ranked.sort(
        key=lambda item: (-item["score"], item["content_sha256"], item["inventor_id"])
    )
    if not ranked or ranked[0]["score"] <= 0 or (
        len(ranked) > 1 and ranked[0]["score"] == ranked[1]["score"]
    ):
        raise AssertionError("actual Taste content has no unique fit for this Wish")
    return ranked


def _assert_semantic_fit_follows_content() -> None:
    """Guard the acceptance fake against drifting back to ID-based routing."""

    lane = "classics-made-yours"
    matching = "Makes known tabletop classics unmistakably personal while preserving their rules."
    other = "Makes Wish-specific printable kinetic machines whose mechanism creates motion."
    first = _rank_tastes(
        lane,
        (
            {"id": "alice", "description": matching},
            {"id": "bob", "description": other},
        ),
        content_key="description",
    )
    swapped = _rank_tastes(
        lane,
        (
            {"id": "alice", "description": other},
            {"id": "bob", "description": matching},
        ),
        content_key="description",
    )
    if (
        first[0]["inventor_id"] != "alice"
        or swapped[0]["inventor_id"] != "bob"
    ):
        raise AssertionError("semantic acceptance fit is not bound to Taste content")


_assert_semantic_fit_follows_content()


def _semantic_invoke(self, *, prompt, schema, capability):
    global _PROCESS_SELECTED_INVENTOR
    del self
    if "inventor_ids" in schema.get("properties", {}):
        marker = "\n\nDATA:\n"
        data = json.loads(prompt.split(marker, 1)[1])
        lane = _wish_pattern(data["wish"])
        cards = data["catalog_page"]["cards"]
        ranked = _rank_tastes(lane, cards, content_key="description")
        shortlist = [item["inventor_id"] for item in ranked[:3]]
        _PROCESS_SELECTED_INVENTOR = shortlist[0]
        _log(
            "semantic-model",
            capability=capability,
            lane=lane,
            selected_inventor_id=shortlist[0],
            source_kind="description",
            candidate_fits=ranked,
        )
        return {
            "inventor_ids": shortlist,
            "rationale": "The Wish's primary play pattern fits these actual Taste descriptions.",
        }
    marker = "FINALIST DATA:\n"
    payload = json.loads(prompt.split(marker, 1)[1])
    lane = _wish_pattern(payload["wish"])
    finalists = payload["finalists"]
    candidates = [
        {"id": finalist["id"], "content": finalist["taste"]["content"]}
        for finalist in finalists
    ]
    ranked = _rank_tastes(lane, candidates, content_key="content")
    target = ranked[0]["inventor_id"]
    if _PROCESS_SELECTED_INVENTOR not in (None, target):
        raise AssertionError("full Taste judgment disagrees with description fit")
    _PROCESS_SELECTED_INVENTOR = target
    _log(
        "semantic-model",
        capability=capability,
        lane=lane,
        selected_inventor_id=target,
        source_kind="taste",
        candidate_fits=ranked,
    )
    assessments = []
    for finalist in finalists:
        inventor_id = finalist["id"]
        accepted = inventor_id == target
        assessments.append(
            {
                "inventor_id": inventor_id,
                "taste_sha256": finalist["taste"]["sha256"],
                "score": 99 if accepted else 10,
                "accepted": accepted,
                "explanation": (
                    "This Inventor's complete Taste is the exact fit."
                    if accepted
                    else "This Wish belongs to a different play pattern."
                ),
                "tensions": [] if accepted else ["Its hard Taste boundary points elsewhere."],
            }
        )
    return {"selected_inventor_id": target, "assessments": assessments}


CodexSemanticManager._invoke = _semantic_invoke


def _lane_contract(lane: str):
    if lane == "classics-made-yours":
        return {
            "schema_version": 1,
            "lane": lane,
            "known_game": "checkers",
            "rules_preserved": True,
            "rules_preservation": {
                "canonical_ruleset": "WCDF English draughts rules (2012)",
                "preserved_invariants": [
                    "mandatory captures",
                    "promotion on the far rank",
                    "no legal move loses",
                ],
                "allowed_physical_changes": [
                    "piece silhouettes and surface storytelling"
                ],
            },
            "personalization_map": [
                {
                    "wish_detail": "the customer's midnight-blue studio memory",
                    "physical_feature": "distinct midnight-blue role silhouettes",
                    "rules_effect": "none",
                }
            ],
        }
    if lane == "invented-games":
        return {
            "schema_version": 2,
            "lane": lane,
            "game_protocol": {
                "schema_version": 1,
                "protocol": "workshop.resource-game.v1",
                "players": 2,
                "resources": [
                    {"resource_id": "sparks", "label": "spark tokens", "initial": 7}
                ],
                "actions": [
                    {
                        "action_id": "take-one",
                        "label": "Take one spark",
                        "removals": [{"resource_id": "sparks", "count": 1}],
                        "points": 0,
                    },
                    {
                        "action_id": "take-two",
                        "label": "Take two sparks",
                        "removals": [{"resource_id": "sparks", "count": 2}],
                        "points": 0,
                    },
                    {
                        "action_id": "take-three",
                        "label": "Take three sparks",
                        "removals": [{"resource_id": "sparks", "count": 3}],
                        "points": 0,
                    },
                ],
                "ending": {
                    "condition": "all-resources-empty",
                    "winner": "next-actor",
                    "score_tie_break": "last-actor",
                },
            },
            "simulation_gate": {
                "minimum_complete_games": 1_000,
                "fixed_seed_strategy": "artifact-sha256-plus-index",
                "player_policies": [
                    "optimizing",
                    "social",
                    "exploratory",
                    "adversarial",
                ],
            },
        }
    if lane == "moving-machines":
        return {
            "schema_version": 1,
            "lane": lane,
            "kinematic_model": {
                "input_motion": "A person turns the index wheel by hand.",
                "transmission": ["The rigid wheel turns directly about Z."],
                "output_motion": "The visible index completes one revolution.",
                "degrees_of_freedom": 1,
            },
            "tolerances_mm": [
                {
                    "interface": "Wheel swept envelope beside the marker",
                    "nominal_clearance_mm": 1.0,
                    "tolerance_mm": 0.2,
                }
            ],
            "load_assumptions": [
                {
                    "case": "A user stalls the wheel by hand.",
                    "force_n": 8.0,
                    "safety_factor": 2.0,
                    "basis": "A bounded concept-stage hand-force assumption.",
                }
            ],
            "failure_modes": [
                {
                    "mode": "Wheel shear or clearance stall",
                    "cause": "The bounded hand load exceeds the section or clearance closes.",
                    "effect": "The wheel stops or its primitive section shears.",
                    "mitigation": "Preserve swept clearance and the checked shear section.",
                }
            ],
        }
    if lane == "holdable-science":
        scale = dict(agent_invent._SCIENCE_QUALITATIVE_SCALE)
        simplification = dict(agent_invent._SCIENCE_QUALITATIVE_SIMPLIFICATION)
        return {
            "schema_version": 1,
            "lane": lane,
            "source_model": {
                "phenomenon": "Coupled periodic motion",
                "model": "A bounded linkage maps rotary phase to visible periodic displacement.",
                "source_ids": [
                    "mechanism-source",
                    agent_invent._SCIENCE_MAPPING_SOURCE_ID,
                ],
            },
            "simplifications": [simplification],
            "scale": scale,
            "interaction": {
                "user_action": "Turn the handle through one revolution.",
                "observable_response": "Markers reveal their relative phase around the cycle.",
                "teaching_point": "A bounded linkage maps rotary phase to visible periodic displacement.",
                "misuse_boundary": simplification["disclosed_limit"],
            },
        }
    return {"schema_version": 1, "lane": lane, **_world_personalization()}


def _invent_action(lane: str):
    contract = _lane_contract(lane)
    research_source_ids = ["mechanism-source", "safety-source"]
    if lane == "holdable-science":
        research_source_ids.append(agent_invent._SCIENCE_MAPPING_SOURCE_ID)
    title = {
        "classics-made-yours": "Midnight Checkers",
        "moving-machines": "Pocket Trotter",
        "little-worlds": "Lantern Market",
        "holdable-science": "Phase in Your Hand",
        "invented-games": "Seven Sparks",
    }[lane]
    return {
        "research": {
            "patterns": [
                {
                    "statement": "Physical play becomes legible through one bounded interaction.",
                    "source_ids": ["mechanism-source"],
                }
            ],
            "opportunities": [
                {
                    "statement": "Age guidance and small-part hazards require explicit review.",
                    "source_ids": ["safety-source"],
                }
            ],
            "assumptions": ["The acceptance Wish supplies the fictional reference it names."],
        },
        "directions": [
            {
                "name": "Pocket ritual",
                "idea": "A compact object with one clear invitation.",
                "play": "Pick it up, act, and see a response.",
                "form": "Three bold printable forms.",
                "risks": ["Detailed surface design remains later work."],
            },
            {
                "name": "Table spark",
                "idea": "A tabletop arrangement with visible state.",
                "play": "Rearrange it and compare outcomes.",
                "form": "Distinct low silhouettes.",
                "risks": ["Keep the interaction immediately readable."],
            },
            {
                "name": "Tiny theater",
                "idea": "One small scene that rewards a second look.",
                "play": "Reveal the hidden relationship.",
                "form": "A grounded base and two characters.",
                "risks": ["Avoid ornamental parts with no play role."],
            },
        ],
        "selected": {
            "title": title,
            "summary": "A Wish-specific toy with one crisp, repeatable moment of play.",
            "magic": "The customer's own idea becomes a real object with a surprising response.",
            "play_pattern": "Pick up, act, observe, and try again.",
            "industrial_design": "A compact family of distinct tactile forms with one visual focus.",
            "mechanical_handoff": [
                "Engineer every form as a bounded printable primitive.",
                "Keep the selected interaction legible in the exact CAD.",
            ],
            "lane_contract": contract,
            "research_source_ids": research_source_ids,
        },
    }


def _base_make_action(title: str):
    return {
        "title": title,
        "summary": "A Wish-shaped toy assembled from three distinct printable parts.",
        "interaction": "Turn the round part and move the marker through one visible state change.",
        "mechanical_principle": "A hand-turned wheel provides a tactile index beside a separate marker.",
        "assembly": [
            "Place the base on a stable table.",
            "Seat the wheel and marker in their labelled positions after printing.",
        ],
        "instructions": "Arrange the three pieces as shown, turn the wheel, and move the marker.",
        "parts": [
            {
                "part_id": "base",
                "name": "one base",
                "purpose": "Grounds the interaction.",
                "shape": "box",
                "size_mm": {"x": 48, "y": 36, "z": 5},
                "print_center_mm": {"x": 28, "y": 28},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 80, "y": 80, "z": 0},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            },
            {
                "part_id": "index-wheel",
                "name": "one index wheel",
                "purpose": "Provides the hand-turned state change.",
                "shape": "cylinder",
                "size_mm": {"x": 30, "y": 30, "z": 6},
                "print_center_mm": {"x": 78, "y": 28},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 80, "y": 80, "z": 8},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            },
            {
                "part_id": "marker",
                "name": "one marker",
                "purpose": "Shows the current state.",
                "shape": "cylinder",
                "size_mm": {"x": 14, "y": 14, "z": 8},
                "print_center_mm": {"x": 108, "y": 28},
                "print_rotation_deg": 0,
                "assembly_center_mm": {"x": 122, "y": 80, "z": 0},
                "assembly_rotation_deg": 0,
                "material": "PLA",
            },
        ],
        "classic_spec": {
            "enabled": False,
            "known_game": "not applicable",
            "rules_reference": "not applicable",
            "rules_unchanged": False,
        },
        "game_spec": {
            "enabled": False,
            "resource_part_ids": [],
        },
        "motion_spec": {
            "enabled": False,
            "moving_part_id": "",
            "axis": "z",
            "sweep_degrees": 1,
            "minimum_aabb_clearance_mm": 0,
        },
        "design_limitations": [
            "This constrained primitive MVP leaves detailed surface design to a later revision."
        ],
    }


def _make_action(lane: str):
    title = _invent_action(lane)["selected"]["title"]
    value = _base_make_action(title)
    if lane == "classics-made-yours":
        value["classic_spec"] = {
            "enabled": True,
            "known_game": "checkers",
            "rules_reference": "https://wcdf.net/rules/rules_of_checkers_english.pdf",
            "rules_unchanged": True,
        }
    elif lane == "moving-machines":
        value["motion_spec"] = {
            "enabled": True,
            "moving_part_id": "index-wheel",
            "axis": "z",
            "sweep_degrees": 360,
            "minimum_aabb_clearance_mm": 1,
        }
        value["moving_machine_binding"] = {
            "joint": {
                "joint_id": "index-wheel-joint",
                "kind": "rigid-revolute-z",
                "moving_part_id": "index-wheel",
                "support_part_ids": ["base"],
                "obstacle_part_ids": ["marker"],
                "axis_point_mm": [80.0, 80.0, 8.0],
                "axis_direction": [0.0, 0.0, 1.0],
                "start_deg": 0.0,
                "end_deg": 360.0,
                "steps": 72,
            },
            "tolerance_bindings": [
                {
                    "contract_index": 0,
                    "moving_part_id": "index-wheel",
                    "stationary_part_ids": ["marker"],
                    "verification": "continuous-swept-envelope",
                }
            ],
            "load_bindings": [
                {
                    "contract_index": 0,
                    "loaded_part_id": "index-wheel",
                    "support_part_ids": ["base"],
                    "section_axis": "z",
                    "verification_modes": ["bulk-compression", "direct-shear"],
                }
            ],
            "failure_bindings": [
                {
                    "contract_index": 0,
                    "part_ids": ["base", "index-wheel", "marker"],
                    "load_case_indices": [0],
                    "verification_modes": [
                        "direct-shear",
                        "continuous-clearance",
                        "reverse-sweep",
                        "stall-envelope",
                    ],
                }
            ],
        }
    elif lane == "invented-games":
        parts = []
        for index in range(7):
            part_id = "spark-%d" % (index + 1)
            parts.append(
                {
                    "part_id": part_id,
                    "name": "spark token %d" % (index + 1),
                    "purpose": "One tactile token in the finite supply.",
                    "shape": "cylinder",
                    "size_mm": {"x": 12, "y": 12, "z": 4},
                    "print_center_mm": {"x": 14 + index * 18, "y": 18},
                    "print_rotation_deg": 0,
                    "assembly_center_mm": {"x": 14 + index * 18, "y": 80, "z": 0},
                    "assembly_rotation_deg": 0,
                    "material": "PLA",
                }
            )
        value["parts"] = parts
        value["game_spec"] = {
            "enabled": True,
            "resource_part_ids": [
                {
                    "resource_id": "sparks",
                    "part_ids": [item["part_id"] for item in parts],
                }
            ],
        }
        value["interaction"] = "Take one to three sparks and avoid taking the last."
        value["instructions"] = (
            "Take one to three sparks. The player forced to take the last loses."
        )
    elif lane == "holdable-science":
        interaction = _lane_contract(lane)["interaction"]
        value["instructions"] = "%s %s" % (
            interaction["teaching_point"], interaction["misuse_boundary"]
        )
    return value


class _StructuredRunner:
    cli_version = "acceptance.1.0.0"

    def __init__(self, stage: str, lane: str, model: str, reasoning_effort: str):
        if model not in ("gpt-5.6-terra", "gpt-5.6-luna"):
            raise AssertionError("acceptance tried to use a non-Terra/Luna model")
        self.stage = stage
        self.lane = lane
        self.model = model
        self.reasoning_effort = reasoning_effort

    def invoke(self, *, prompt, schema, workspace):
        del workspace
        _log("structured-model", stage=self.stage, lane=self.lane, model=self.model)
        properties = schema.get("properties", {})
        if self.stage == "invent-creator":
            return _invent_action(self.lane)
        if self.stage == "invent-reward":
            return {
                "dimensions": {
                    name: 96
                    for name in (
                        "wish_fit",
                        "taste_fit",
                        "originality",
                        "play",
                        "industrial_design",
                        "make_feasibility",
                        "research_grounding",
                        "lane_contract",
                    )
                },
                "feedback": ["The industrial design is ready for Make."],
                "hard_tensions": [],
                "assessment": "The fixed reward goal is reached.",
            }
        if self.stage == "make-creator":
            return _make_action(self.lane)
        if self.stage == "make-reward":
            return {
                "dimensions": {
                    name: 96
                    for name in (
                        "concept_fidelity",
                        "taste_fit",
                        "interaction",
                        "mechanical_coherence",
                        "manufacturing_review",
                    )
                },
                "feedback": ["The mechanical design is ready for Playtest."],
                "hard_tensions": [],
                "assessment": "The fixed reward goal is reached.",
            }
        if self.stage == "playtest":
            capabilities = {
                "classics-made-yours": (
                    "agent-playtest", "classic-rules-test", "mechanical-test", "print-test"
                ),
                "moving-machines": (
                    "agent-playtest", "motion-test", "mechanical-test", "print-test"
                ),
                "little-worlds": (
                    "agent-playtest", "world-test", "mechanical-test", "print-test"
                ),
                "holdable-science": (
                    "agent-playtest", "science-test", "mechanical-test", "print-test"
                ),
                "invented-games": (
                    "agent-playtest", "mechanical-test", "print-test"
                ),
            }[self.lane]
            return {
                "reviews": [
                    {
                        "capability": capability,
                        "dimensions": {
                            "wish_fit": 96,
                            "play_clarity": 96,
                            "functional_confidence": 96,
                            "robustness": 96,
                            "distinctiveness": 96,
                            "evidence_quality": 96,
                        },
                        "observations": [
                            "Four AI-player roles reviewed the exact sealed revision."
                        ],
                        "findings": [],
                        "hard_tensions": [],
                    }
                    for capability in capabilities
                ]
            }
        if self.stage == "instructions-creator":
            return {
                "opening": "Your Wish is ready to play.",
                "before_you_begin": ["Check every listed piece against the manual."],
                "steps": [
                    {"title": "Set", "body": "Place the toy on a clear table."},
                    {"title": "Play", "body": "Follow its exact interaction and rules."},
                    {"title": "Reset", "body": "Return every piece to its starting state."},
                ],
                "care_and_safety": [
                    "This grown-up toy contains small parts; keep it away from young children."
                ],
                "page_use": "Set it down, play one complete interaction, and reset it.",
            }
        if self.stage == "instructions-reward":
            return {
                "dimensions": {
                    name: 96
                    for name in (
                        "evidence_truth",
                        "clarity",
                        "completeness",
                        "usability",
                        "workshop_tone",
                        "factory_handoff",
                    )
                },
                "feedback": ["The product manual and factual page handoff are ready."],
                "hard_tensions": [],
                "assessment": "The fixed reward goal is reached.",
            }
        raise AssertionError("unexpected structured boundary %s %s" % (self.stage, properties))


def _structured_stage(schema) -> str:
    properties = schema.get("properties", {})
    if "directions" in properties:
        return "invent-creator"
    if "parts" in properties:
        return "make-creator"
    if "reviews" in properties:
        return "playtest"
    if "opening" in properties:
        return "instructions-creator"
    dimensions = properties.get("dimensions", {}).get("properties", {})
    if "originality" in dimensions:
        return "invent-reward"
    if "concept_fidelity" in dimensions:
        return "make-reward"
    if "evidence_truth" in dimensions:
        return "instructions-reward"
    raise AssertionError("acceptance received an unknown structured schema")


def _structured_lane(prompt: str) -> str:
    observed = {
        lane
        for lane in LANE_BY_INVENTOR.values()
        if ('"lane": "%s"' % lane) in prompt
        or ('"lane":"%s"' % lane) in prompt
    }
    if len(observed) != 1:
        raise AssertionError(
            "structured boundary received no unique sealed lane: %s"
            % sorted(observed)
        )
    return next(iter(observed))


def _structured_invoke(self, *, prompt, schema, workspace=None):
    del workspace
    stage = _structured_stage(schema)
    lane = _structured_lane(prompt)
    return _StructuredRunner(
        stage,
        lane,
        self.model,
        self.reasoning_effort,
    ).invoke(prompt=prompt, schema=schema, workspace=None)


# Keep every production stage constructor and its Terra/Luna configuration.
# Only the installed CLI process that would make the external model call is
# replaced with deterministic structured responses.
CodexStructuredRunner.invoke = _structured_invoke


def _research(context):
    evidence = "\n".join(
        (
            "Physical play becomes legible through one bounded interaction.",
            "Coupled periodic motion",
            "A bounded linkage maps rotary phase to visible periodic displacement.",
            "Friction and elastic deformation are omitted from the visible model. "
            "The object is qualitative and does not predict real-system amplitude.",
        )
    )
    sources = [
        InventResearchSource(
            "mechanism-source",
            "Bounded physical interaction",
            "Acceptance Engineering Archive",
            "https://example.com/workshop/interaction",
            "2026-08-25T00:00:00+00:00",
            evidence,
            ("prior-art", "use-context", "mechanism", "science"),
        ),
        InventResearchSource(
            "safety-source",
            "Small-part safety",
            "Acceptance Safety Office",
            "https://example.com/workshop/safety",
            "2026-08-25T00:00:00+00:00",
            "Age guidance and small-part hazards require explicit review.",
            ("safety",),
        ),
    ]
    if context.blueprint.lane == "holdable-science":
        sources.append(
            InventResearchSource(
                agent_invent._SCIENCE_MAPPING_SOURCE_ID,
                "Workshop qualitative science-model boundary",
                "Autonomous Workshop",
                agent_invent._SCIENCE_MAPPING_SOURCE_URL,
                "2026-08-25T00:00:00+00:00",
                agent_invent._SCIENCE_MAPPING_EVIDENCE,
                ("science", "use-context"),
            )
        )
    value = InventResearch(
        wish_sha256=json_sha256(context.wish.to_dict()),
        taste_sha256=context.taste.sha256,
        blueprint_sha256=context.blueprint.sha256,
        lane=context.blueprint.lane,
        provider="acceptance-public-research",
        provider_version="1.0.0",
        provider_config_sha256="a" * 64,
        sources=tuple(sources),
    )
    _log("research", lane=context.blueprint.lane, research_sha256=value.research_sha256)
    return value


def _public_research_boundary(self, context):
    del self
    return _research(context)


PublicHTTPResearchProvider.__call__ = _public_research_boundary


def _tetra_triangles(offset: float):
    points = (
        (offset, 0.0, 0.0),
        (offset + 4.0, 0.0, 0.0),
        (offset, 4.0, 0.0),
        (offset, 0.0, 4.0),
    )
    faces = ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3))
    return tuple(tuple(points[index] for index in face) for face in faces)


def _binary_tetras(offsets) -> bytes:
    triangles = tuple(
        triangle for offset in offsets for triangle in _tetra_triangles(offset)
    )
    payload = bytearray(b"Autonomous Workshop acceptance STL".ljust(80, b"\0"))
    payload.extend(struct.pack("<I", len(triangles)))
    for triangle in triangles:
        coordinates = tuple(value for vertex in triangle for value in vertex)
        payload.extend(struct.pack("<12fH", 0.0, 0.0, 0.0, *coordinates, 0))
    return bytes(payload)


def _tetra(name: str, offset: float = 0.0) -> bytes:
    del name
    return _binary_tetras((offset,))


def _cad_parts(root: Path):
    payload = (root / "parameters.py").read_text(encoding="utf-8")
    return json.loads(
        payload.split("PARTS = ", 1)[1].split("\nPART_BY_ID", 1)[0]
    )


def _completed(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _cad_command_runner(
    command,
    *,
    cwd,
    input,
    capture_output,
    text,
    check,
    timeout,
    env,
):
    del capture_output, text, check, timeout, env
    root = Path(cwd)
    if len(command) > 1 and command[1] == "-c":
        _log("cad-command", command_id="runtime-probe")
        return _completed(stdout="workshop-cad-runtime-ok\n")
    script = Path(command[1]).name if len(command) > 1 else ""
    _log("cad-command", command_id=script)
    if script == "check_layout":
        return _completed(stdout='{"ok":true}\n')
    if script == "gen":
        for entry in command[2:]:
            if not str(entry).endswith(".step.py"):
                continue
            stem = str(entry)[:-3]
            (root / stem).write_text(
                "ISO-10303-21;\n%s\nEND-ISO-10303-21;\n" % stem,
                encoding="utf-8",
            )
        return _completed(stdout='{"ok":true}\n')
    if script == "export":
        output = str(command[command.index("--stl") + 1])
        part_count = len(tuple(root.glob("part_*.step.py")))
        payload = (
            _binary_tetras(float(index) * 10.0 for index in range(part_count))
            if Path(output).stem in {"product", "print_plate"}
            else _tetra(output)
        )
        (root / output).write_bytes(payload)
        return _completed(stdout='{"ok":true}\n')
    if script == "inspect":
        parts = _cad_parts(root)
        responses = []
        for request in (
            json.loads(line) for line in (input or "").splitlines() if line.strip()
        ):
            operation, target = request["argv"][:2]
            if operation == "refs":
                measured = None
                for part in parts:
                    expected = "part_%s.step" % part["part_id"].replace("-", "_")
                    if target == expected:
                        measured = [
                            float(part["size_mm"][axis])
                            for axis in ("x", "y", "z")
                        ]
                        break
                if measured is None:
                    lows = [
                        min(
                            float(part["print_center_mm"][axis])
                            - float(part["size_mm"][axis]) / 2.0
                            for part in parts
                        )
                        for axis in ("x", "y")
                    ]
                    highs = [
                        max(
                            float(part["print_center_mm"][axis])
                            + float(part["size_mm"][axis]) / 2.0
                            for part in parts
                        )
                        for axis in ("x", "y")
                    ]
                    measured = [
                        highs[0] - lows[0],
                        highs[1] - lows[1],
                        max(float(part["size_mm"]["z"]) for part in parts),
                    ]
                    center = [
                        (highs[0] + lows[0]) / 2.0,
                        (highs[1] + lows[1]) / 2.0,
                        measured[2] / 2.0,
                    ]
                else:
                    center = [value / 2.0 for value in measured]
                result = {
                    "tokens": [{"entryFacts": {"size": measured, "center": center}}]
                }
            elif operation == "validate":
                result = {"ok": True}
            elif operation == "diff":
                result = {
                    "ok": True,
                    "diff": {
                        "topologyChanged": False,
                        "geometryChanged": False,
                        "bboxChanged": False,
                        "kindChanged": False,
                    },
                }
            elif operation == "interfere":
                result = {"clashCount": 0}
            else:
                raise AssertionError("unexpected acceptance CAD inspection operation")
            responses.append({"id": request["id"], "ok": True, "result": result})
        return _completed(
            stdout="".join(
                json.dumps(response, sort_keys=True) + "\n"
                for response in responses
            )
        )
    if script == "check_fit":
        return _completed(stdout='{"ok":true,"findings":[]}\n')
    if script in {"check_mesh", "check_thickness"}:
        return _completed(stdout="RESULT: PASS\nmanifold edges 0 edges\n")
    if script == "check_motion":
        manifest = json.loads(input)
        result = {
            "ok": True,
            "assembly": "product.step.py",
            "results": [
                {
                    "id": condition["id"],
                    "check": condition["check"],
                    "status": "pass",
                    "clear": True,
                    "steps": condition["inputs"]["steps"],
                }
                for condition in manifest["conditions"]
            ],
        }
        return _completed(stdout=json.dumps(result, sort_keys=True) + "\n")
    raise AssertionError("unexpected acceptance CAD command: %s" % script)


def _slicer_command_runner(
    command,
    *,
    cwd,
    input,
    capture_output,
    text,
    check,
    timeout,
    env,
):
    del cwd, input, capture_output, text, check, timeout, env
    if command[1:] == ["--help"]:
        _log("slicer-command", command_id="version-probe")
        return _completed(stdout="PrusaSlicer-2.9.6\n")
    output = Path(command[command.index("--output") + 1])
    output.write_bytes(
        b"; generated by PrusaSlicer-2.9.6\n"
        b"; estimated printing time = 4m\n"
        b"; filament used [mm] = 12.0\n"
        b"G1 X1 Y1\n"
    )
    _log("slicer-command", command_id="export-gcode")
    return _completed(stdout="sliced\n")


class _WorldReferenceService:
    @staticmethod
    def _descriptor(wish):
        scope = WorldReferenceScope(
            "customer-market",
            "customer-original-work",
            "The customer's fictional night market",
            "The customer authored and supplied the fictional reference.",
            ("violet lantern arch",),
            ("private address",),
            "acceptance-customer-order",
            "customer-supplied-attestation-record",
        )
        wish_sha256 = json_sha256(wish.to_dict())
        admission = {
            "payload": {
                "kind": "world-reference",
                "wish_sha256": wish_sha256,
                "reference_id": scope.reference_id,
            },
            "authentication": {
                "algorithm": "acceptance-synthetic-signature",
                "value": "sealed",
            },
        }
        return WorldReferenceDescriptor(
            scope,
            WorldReferenceReceipt(
                wish.product_id,
                wish_sha256,
                scope.reference_id,
                json_sha256(admission),
                "4" * 64,
                128,
                "5" * 64,
                64,
                "image/png",
                scope.subject_kind,
                scope.reviewer_id,
                "6" * 64,
            ),
            admission,
        )

    def descriptors(self, wish):
        descriptor = self._descriptor(wish)
        _log(
            "world-reference-service",
            operation="descriptors",
            product_id=wish.product_id,
            reference_id=descriptor.scope.reference_id,
            record_sha256=descriptor.receipt.record_sha256,
        )
        return (descriptor,)

    def verify_admission(self, admission, wish, *, expected_reference_id):
        expected = self._descriptor(wish)
        if (
            admission != expected.admission
            or expected_reference_id != expected.scope.reference_id
        ):
            raise AssertionError("world admission differs from its exact descriptor")
        _log(
            "world-reference-service",
            operation="verify-admission",
            product_id=wish.product_id,
            reference_id=expected_reference_id,
        )


_WORLD_REFERENCE_SERVICE = _WorldReferenceService()
_WORLD_REFERENCE_IDENTITY = WorldProviderIdentity(
    "acceptance-world-reference-service",
    "1.0.0",
    "7" * 64,
)


def _configured_world_reference_service(assignment):
    if assignment.inventor_id != "eve":
        raise AssertionError("world service was requested for a non-world lane")
    return _WORLD_REFERENCE_SERVICE, _WORLD_REFERENCE_IDENTITY


def _configured_world_playtest_evidence(assignment, result):
    if assignment.inventor_id != "eve":
        raise AssertionError("world evidence was requested for a non-world lane")
    world_inputs = assignment.world_inputs
    artifact_sha256 = result.get("artifact_sha256")
    if not isinstance(artifact_sha256, str) or len(artifact_sha256) != 64:
        raise AssertionError("world evidence request lacks the exact Made artifact")
    admitted = tuple(world_inputs.references)
    if len(admitted) != 1:
        raise AssertionError("acceptance expected one admitted world reference")
    reference = admitted[0]
    personalization = _world_personalization()
    evidence = WorldPlaytestEvidence(
        product_id=assignment.wish.product_id,
        wish_sha256=json_sha256(assignment.wish.to_dict()),
        artifact_sha256=artifact_sha256,
        personalization_sha256=json_sha256(personalization),
        invent_inputs_sha256=world_inputs.binding_sha256,
        provider=WorldProviderIdentity(
            "acceptance-world-comparison-service",
            "1.0.0",
            "8" * 64,
        ),
        references=(
            WorldEvidenceReference(
                reference.scope.reference_id,
                reference.record_sha256,
                reference.content_sha256,
                reference.content_bytes,
                reference.consent_sha256,
                reference.consent_bytes,
                reference.media_type,
                "authenticated-customer-supplied-scope-record",
                "2026-08-26T01:02:03Z",
                {"authorization_sha256": "9" * 64},
            ),
        ),
        cases=(
            WorldEvidenceCase(
                "customer-market",
                "violet lantern arch",
                "The arch remains recognizable without a caption.",
                reference.content_sha256,
                True,
                True,
                "deterministic-feature-comparison",
            ),
        ),
        provider_attestation={"attestation_sha256": "a" * 64},
    )
    evidence.assert_context(
        assignment.wish,
        artifact_sha256,
        personalization,
        world_inputs,
    )
    _log(
        "world-playtest-service",
        product_id=assignment.wish.product_id,
        artifact_sha256=artifact_sha256,
        invent_inputs_sha256=world_inputs.binding_sha256,
        evidence_sha256=evidence.evidence_sha256,
    )
    return evidence


# Inject only processes and infrastructure that live outside the Workshop
# composition. The production LockedCadSkillBuilder still writes projects,
# sequences commands, validates every response, and seals its own observation.
_ORIGINAL_CAD_BUILDER_INIT = LockedCadSkillBuilder.__init__


def _cad_builder_init(
    self,
    *,
    python_executable=None,
    skills_root=None,
    command_runner=None,
):
    if command_runner is not None:
        raise AssertionError("installed acceptance received a custom CAD runner")
    return _ORIGINAL_CAD_BUILDER_INIT(
        self,
        python_executable=python_executable,
        skills_root=skills_root,
        command_runner=_cad_command_runner,
    )


LockedCadSkillBuilder.__init__ = _cad_builder_init


def _acceptance_slicer_from_environment(cls):
    checker = cls(
        binary="PrusaSlicer",
        profile_payloads=agent_playtest._WORKSHOP_PRUSA_PROFILES,
        expected_version=agent_playtest.PRUSASLICER_VERSION,
        command_runner=_slicer_command_runner,
    )
    _log(
        "slicer-boundary",
        checker=type(checker).__name__,
        command_runner=getattr(checker.command_runner, "__name__", None),
    )
    return checker


agent_playtest.PrusaSlicerPrintCheck.from_environment = classmethod(
    _acceptance_slicer_from_environment
)

_ORIGINAL_CONFIGURED_TOOLS = agent_invent.configured_workshop_tools
_OBSERVED_PROFILE_CONFIGURATIONS = set()


def _observed_configured_tools(
    existing=None,
    *,
    inventor_id=None,
    runtime_root=None,
):
    selected = _ORIGINAL_CONFIGURED_TOOLS(
        existing,
        inventor_id=inventor_id,
        runtime_root=runtime_root,
    )
    if inventor_id not in _OBSERVED_PROFILE_CONFIGURATIONS:
        observed = {
            name: (
                None
                if getattr(selected, name) is None
                else type(getattr(selected, name)).__name__
            )
            for name in ("invent", "make", "playtest", "instructions", "deliver")
        }
        expected = {
            "invent": "CodexInventor",
            "make": "CodexMaker",
            "playtest": "LaneAwarePlaytester",
            "instructions": "RewardedInstructions",
            "deliver": None,
        }
        if observed != expected:
            raise AssertionError(
                "production configured_workshop_tools omitted a shared stage: %s"
                % observed
            )
        _OBSERVED_PROFILE_CONFIGURATIONS.add(inventor_id)
        _log(
            "shared-tools",
            inventor_id=inventor_id,
            lane=LANE_BY_INVENTOR[inventor_id],
            composition="production-configured_workshop-tools",
            customization="taste-only",
            execution="manager-owned",
            types=observed,
            make_cad_builder=type(selected.make.cad_builder).__name__,
            make_cad_command_runner=getattr(
                selected.make.cad_builder.command_runner, "__name__", None
            ),
            playtest_lane_providers=type(selected.playtest.lane_providers).__name__,
            playtest_moving_verifier=type(
                selected.playtest.moving_machine_verifier
            ).__name__,
        )
    return selected


# This wrapper observes and asserts the production result; it never supplies or
# changes a Workshop stage.
agent_invent.configured_workshop_tools = _observed_configured_tools


def _multipart(headers, body):
    message = BytesParser(policy=email_policy).parsebytes(
        (
            "Content-Type: %s\r\nMIME-Version: 1.0\r\n\r\n"
            % headers["Content-Type"]
        ).encode("ascii")
        + body
    )
    fields = {}
    files = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        payload = part.get_payload(decode=True)
        if part.get_filename() is None:
            fields.setdefault(name, []).append(payload.decode("utf-8"))
        else:
            files[name] = payload
    return fields, files


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _inspect_factory_pack(packet: bytes, product_id: str):
    with zipfile.ZipFile(__import__("io").BytesIO(packet)) as archive:
        paths = sorted(archive.namelist())
        project = json.loads(archive.read("project.json").decode("utf-8"))
        if project.get("id") != product_id:
            raise AssertionError("synthetic Factory Pack has another project id")
        primary_path = product_id + ".stl"
        step_path = product_id + ".step"
        sidecar_path = step_path + ".json"
        required = {
            primary_path,
            step_path,
            sidecar_path,
            "workshop-product-facts.json",
        }
        if not required <= set(paths):
            raise AssertionError("synthetic Factory Pack lacks its canonical family")
        sidecars = [path for path in paths if path.casefold().endswith(".step.json")]
        if sidecars != [sidecar_path]:
            raise AssertionError("synthetic Factory Pack has competing STEP sidecars")
        sidecar_bytes = archive.read(sidecar_path)
        sidecar = json.loads(sidecar_bytes.decode("utf-8"))
        parts = sidecar.get("parts") if isinstance(sidecar, dict) else None
        if (
            sidecar.get("schemaVersion") != 1
            or sidecar.get("entryKind") != "assembly"
            or sidecar.get("primaryPose") != "assembled"
            or not isinstance(parts, list)
            or not parts
        ):
            raise AssertionError("synthetic Factory occurrence sidecar is malformed")
        observed_names = set()
        occurrences = []
        for order, part in enumerate(parts):
            if not isinstance(part, dict) or set(part) != {"name", "stlPath"}:
                raise AssertionError("synthetic Factory occurrence is malformed")
            name = part["name"]
            path = part["stlPath"]
            expected_path = "%s_parts/%s.stl" % (product_id, name)
            if (
                not isinstance(name, str)
                or not name
                or name in observed_names
                or path != expected_path
                or path not in paths
            ):
                raise AssertionError("synthetic Factory occurrence path is not canonical")
            observed_names.add(name)
            content = archive.read(path)
            occurrences.append(
                {
                    "order": order,
                    "name": name,
                    "path": path,
                    "sha256": _sha256_bytes(content),
                }
            )

        facts = json.loads(
            archive.read("workshop-product-facts.json").decode("utf-8")
        )
        assembly = facts.get("factory_assembly") if isinstance(facts, dict) else None
        production = assembly.get("production_stls") if isinstance(assembly, dict) else None
        expected_production = [
            {"order": item["order"], "name": item["name"], "path": item["path"], "sha256": item["sha256"]}
            for item in occurrences
        ]
        if (
            not isinstance(assembly, dict)
            or assembly.get("kind") != "factory.occurrence-family"
            or assembly.get("occurrence_count") != len(occurrences)
            or assembly.get("parts_directory") != product_id + "_parts"
            or assembly.get("step")
            != {"path": step_path, "sha256": _sha256_bytes(archive.read(step_path))}
            or assembly.get("sidecar")
            != {"path": sidecar_path, "sha256": _sha256_bytes(sidecar_bytes)}
            or not isinstance(production, list)
            or [
                {
                    "order": item.get("order"),
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "sha256": item.get("sha256"),
                }
                for item in production
            ]
            != expected_production
        ):
            raise AssertionError(
                "synthetic Factory facts do not bind the exact occurrence family"
            )
        return {
            "paths": paths,
            "primary_sha256": _sha256_bytes(archive.read(primary_path)),
            "step_sha256": _sha256_bytes(archive.read(step_path)),
            "sidecar_sha256": _sha256_bytes(sidecar_bytes),
            "occurrences": occurrences,
        }


class _FactoryTransport:
    def __init__(self):
        self.username = None
        self.owner_id = None
        self.slug = None
        self.title = None
        self.description = None
        self.category = None
        self.tags = []
        self.public = False

    def _design(self):
        history = "history-%s" % self.slug
        return {
            "id": "design-%s" % self.slug,
            "slug": self.slug,
            "title": "Factory story for %s" % self.title,
            "description": "Factory-generated product story from sealed facts.",
            "owner_id": self.owner_id,
            "root_id": "design-%s" % self.slug,
            "current_history_id": history,
            "published_history_id": history if self.public else None,
            "status": "public" if self.public else "draft",
            "project_url": "https://cdn.autonomous.ai/projects/%s/" % history,
            "origin": "import",
            "tags": list(self.tags),
            "category": {"slug": self.category},
            "author": {"id": self.owner_id},
            "thumbnail_urls": ["https://cdn.example.test/%s/cover.png" % self.slug],
            "attachments": [],
            "use_case": {"body": "A Factory-generated use case."},
            "story_blocks": [{"body": "A Factory-generated story block."}],
            "listing": (
                {
                    "active": True,
                    "price_cents": 2500,
                    "currency": "USD",
                    "sku": "ACCEPT-%s" % self.slug.upper()[:24],
                }
                if self.public
                else None
            ),
        }

    def __call__(self, method, url, headers, body, timeout):
        del timeout
        safe_url = url.split("?", 1)[0]
        _log("factory-http", method=method, path=safe_url.rsplit("/api/v1", 1)[-1])
        if safe_url.endswith("/auth/agent/login"):
            request = json.loads(body.decode("utf-8"))
            if (
                set(request) != {"username", "password"}
                or request.get("username") != _PROCESS_SELECTED_INVENTOR
                or request.get("password") != ACCEPTANCE_FACTORY_PASSWORD
            ):
                raise AssertionError(
                    "synthetic Factory received the wrong selected identity or credential"
                )
            self.username = request["username"]
            self.owner_id = "owner-%s" % self.username
            _log("factory-login", username=self.username)
            return HttpResponse(
                200,
                {"Content-Type": "application/json"},
                json.dumps(
                    {
                        "access_token": "acceptance-token",
                        "token_type": "Bearer",
                        "expires_in": 3600,
                        "expires_at": "2030-08-25T23:59:59+00:00",
                        "user": {"id": self.owner_id, "username": self.username},
                    }
                ).encode("utf-8"),
            )
        if headers.get("Authorization") != "Bearer acceptance-token":
            raise AssertionError("Factory request omitted the authenticated bearer")
        if method == "POST" and safe_url.endswith("/designs/import"):
            fields, files = _multipart(headers, body)
            packet = files["file"]
            with zipfile.ZipFile(__import__("io").BytesIO(packet)) as archive:
                project = json.loads(archive.read("project.json").decode("utf-8"))
            self.slug = project["id"]
            inspected = _inspect_factory_pack(packet, self.slug)
            _log(
                "factory-pack-inventory",
                project_id=self.slug,
                **inspected,
            )
            self.title = fields["title"][0]
            self.description = fields["description"][0]
            self.category = fields["category"][0]
            self.tags = fields.get("tags", [])
            return HttpResponse(201, {}, json.dumps(self._design()).encode("utf-8"))
        if method == "GET" and "/designs/" in safe_url:
            return HttpResponse(200, {}, json.dumps(self._design()).encode("utf-8"))
        if method == "POST" and safe_url.endswith("/publish"):
            self.public = True
            return HttpResponse(200, {}, b"{}")
        raise AssertionError("unexpected Factory request %s %s" % (method, safe_url))


_FACTORY_TRANSPORT = _FactoryTransport()
_ORIGINAL_SESSION_INIT = FactoryAgentSession.__init__


def _session_init(self, credentials, *, transport=None, sleeper=None):
    del transport, sleeper
    return _ORIGINAL_SESSION_INIT(
        self,
        credentials,
        transport=_FACTORY_TRANSPORT,
        sleeper=lambda unused: None,
    )


FactoryAgentSession.__init__ = _session_init
factory_agent.FactoryAgentSession.__init__ = _session_init


import inventor_workshop.cli as _acceptance_cli

_acceptance_cli._configured_world_reference_service = (
    _configured_world_reference_service
)
_acceptance_cli._configured_world_playtest_evidence = (
    _configured_world_playtest_evidence
)

# Keep ``_run_inventor`` on its production default.  Replacing its ``runner``
# keyword would deliberately select the legacy profile-subprocess compatibility
# branch and would stop this acceptance from exercising Manager-owned execution.
