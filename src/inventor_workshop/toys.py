"""The opinionated first Workshop: Wish-shaped playthings for grown-ups.

The five lanes are crafts, not extra pipeline stages. Every inventor still works the
same five jobs: Wish, Make, Playtest, Instructions, and Deliver.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence, Tuple

from .errors import ContractError
from .make import Wish
from .taste import Taste


WORKSHOP_JOBS: Tuple[str, ...] = (
    "wish",
    "make",
    "playtest",
    "instructions",
    "deliver",
)
PLAYTHING_LANES: Tuple[str, ...] = (
    "classics-made-yours",
    "invented-games",
    "moving-machines",
    "holdable-science",
    "little-worlds",
)


@dataclass(frozen=True)
class ToyTask:
    """One backstage responsibility owned by a public Workshop job."""

    key: str
    job: str
    purpose: str
    evidence: str
    capability: str
    applies_to: Sequence[str] = PLAYTHING_LANES
    external: bool = False

    def __post_init__(self) -> None:
        if self.job not in WORKSHOP_JOBS:
            raise ContractError(
                "toy task job must be Wish, Make, Playtest, Instructions, or Deliver"
            )
        for label, value in (
            ("key", self.key),
            ("purpose", self.purpose),
            ("evidence", self.evidence),
            ("capability", self.capability),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ContractError("toy task %s must be non-empty" % label)
        lanes = tuple(self.applies_to)
        if not lanes or not set(lanes) <= set(PLAYTHING_LANES):
            raise ContractError("toy task applies_to contains an unknown plaything lane")
        object.__setattr__(self, "applies_to", lanes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "job": self.job,
            "purpose": self.purpose,
            "evidence": self.evidence,
            "capability": self.capability,
            "applies_to": list(self.applies_to),
            "external": self.external,
        }


# Alice's completed game work supplies the job ordering and evidence discipline.
# Peter's pinned CAD skills supply the STEP-first Make recipe. Team prototypes
# supplied lessons about simulation, fit, slicing, repair, and postmortems. Those
# lessons live here now; research repos are not pretend Workshop inventors.
TOY_TASKS: Tuple[ToyTask, ...] = (
    ToyTask(
        "wish.scope",
        "wish",
        "Preserve the person's words and choose the craft that can answer them uniquely.",
        "Exact Wish and Taste hashes plus the chosen plaything lane.",
        "wish-intake",
    ),
    ToyTask(
        "make.discover",
        "make",
        "Research prior art, safety boundaries, context, and the opportunity.",
        "Cited research and three genuinely different directions.",
        "research",
    ),
    ToyTask(
        "make.choose",
        "make",
        "Choose one direction with a signature decision, mechanism, or reveal.",
        "A decision record bound to rejected alternatives and Taste.",
        "invention",
    ),
    ToyTask(
        "make.unique",
        "make",
        "Make the Wish structural; do not decorate an interchangeable download.",
        "A trace from Wish details to rules, geometry, mechanism, or composition.",
        "wish-shaped-design",
    ),
    ToyTask(
        "make.classic",
        "make",
        "Preserve the known game's rules while inventing its physical edition for this Wish.",
        "Known-rule reference and a complete mapping from roles and information to parts.",
        "classic-edition-design",
        ("classics-made-yours",),
    ),
    ToyTask(
        "make.rules",
        "make",
        "Write complete executable rules and AI-player models for a game that did not exist.",
        "Setup, legal actions, end condition, scoring, ties, and simulator source.",
        "game-design",
        ("invented-games",),
    ),
    ToyTask(
        "make.motion",
        "make",
        "Design a mechanism whose motion is the delightful idea, not an afterthought.",
        "Kinematic model, tolerances, load assumptions, and failure modes.",
        "kinetic-design",
        ("moving-machines",),
    ),
    ToyTask(
        "make.science",
        "make",
        "Turn a scientific or mathematical relationship into something hands can understand.",
        "Source model, stated simplifications, scale choices, and learning interaction.",
        "science-design",
        ("holdable-science",),
    ),
    ToyTask(
        "make.world",
        "make",
        "Make the recipient's real subject into a coherent tiny world rather than a generic miniature.",
        "Consented references and a feature-to-form personalization map.",
        "world-design",
        ("little-worlds",),
    ),
    ToyTask(
        "make.cad",
        "make",
        "Create attractive STEP-first parametric CAD and printable parts.",
        "Build spec, source, STEP, per-part meshes, assembly, renders, and skill hashes.",
        "cad",
    ),
    ToyTask(
        "playtest.intent",
        "playtest",
        "Test the download bar and the tone: unmistakably Wish-shaped, cool, and never twee.",
        "Independent Taste, distinctiveness, and delight verdicts.",
        "independent-review",
    ),
    ToyTask(
        "playtest.classic",
        "playtest",
        "Verify that customization never corrupts the classic game's known rules or readability.",
        "Rule-conformance and role-legibility results for the exact edition.",
        "classic-rules-test",
        ("classics-made-yours",),
    ),
    ToyTask(
        "playtest.game",
        "playtest",
        "Run at least 1,000 seeded plays with optimizing, social, exploratory, and adversarial agents.",
        "Executable traces covering rules, termination, balance, exploits, choices, and flow.",
        "game-simulation",
        ("invented-games",),
    ),
    ToyTask(
        "playtest.human-table",
        "playtest",
        "Let independent humans play the exact invented game and observe whether they ask to play again.",
        "Authenticated blind-table record and an explicit replay-request observation.",
        "human-replay",
        ("invented-games",),
        external=True,
    ),
    ToyTask(
        "playtest.motion",
        "playtest",
        "Cycle the exact mechanism across tolerances, orientations, wear, and misuse.",
        "Measured cycle, interference, wear, stall, and failure evidence.",
        "motion-test",
        ("moving-machines",),
    ),
    ToyTask(
        "playtest.science",
        "playtest",
        "Check scientific truth, honest simplification, and whether handling reveals the idea.",
        "Source-bound accuracy checks and independent comprehension observations.",
        "science-test",
        ("holdable-science",),
    ),
    ToyTask(
        "playtest.likeness",
        "playtest",
        "Check that the tiny world is recognizable, specific, coherent, and consent-safe.",
        "Reference-bound likeness and personalization review.",
        "world-test",
        ("little-worlds",),
    ),
    ToyTask(
        "playtest.mechanics",
        "playtest",
        "Test physical interactions, fit, assembly paths, loads, and failure modes.",
        "Measured B-rep, interference, fit, motion, and assembly evidence.",
        "mechanical-test",
    ),
    ToyTask(
        "playtest.print",
        "playtest",
        "Test topology, orientation, packing, slicing, material, time, and supports.",
        "Strict mesh and exact slicer-profile receipts for every expected part.",
        "print-test",
    ),
    ToyTask(
        "playtest.people",
        "playtest",
        "Let independent grown-ups use the exact prototype without inventor coaching.",
        "Authenticated blind-use records, delight signals, confusion, and requested changes.",
        "human-playtest",
        (
            "classics-made-yours",
            "moving-machines",
            "holdable-science",
            "little-worlds",
        ),
        external=True,
    ),
    ToyTask(
        "playtest.prototype",
        "playtest",
        "Print and test the exact physical revision that later work will describe and ship.",
        "Printer, material, calibration, artifact, QA, safety, and physical-test receipts.",
        "physical-prototype",
        external=True,
    ),
    ToyTask(
        "instructions.create",
        "instructions",
        "Explain the plaything with box-ready instructions, beautiful truthful images, copy, and rules.",
        "Box insert or rulebook plus private page draft bound to the approved artifact.",
        "product-instructions",
        external=True,
    ),
    ToyTask(
        "instructions.truth",
        "instructions",
        "Reject claims, images, or specifications unsupported by Playtest evidence.",
        "Claim-to-evidence map and exact page-history hash.",
        "instructions-review",
    ),
    ToyTask(
        "deliver.make",
        "deliver",
        "Print, inspect, and pack the exact approved artifact.",
        "Production, QA, packing, and artifact-identity receipts.",
        "production",
        external=True,
    ),
    ToyTask(
        "deliver.ship",
        "deliver",
        "Hand the approved box to USPS, UPS, or FedEx and preserve carrier evidence.",
        "Carrier, service, label, tracking, handoff, and delivery receipts.",
        "shipping",
        external=True,
    ),
)


@dataclass(frozen=True)
class ToyBlueprint:
    """The shared recipe an inventor gets before writing custom code."""

    lane: str
    tasks: Sequence[ToyTask]

    def __post_init__(self) -> None:
        if self.lane not in PLAYTHING_LANES:
            raise ContractError(
                "plaything lane must be one of %s" % ", ".join(PLAYTHING_LANES)
            )
        selected = tuple(self.tasks)
        if not selected or any(self.lane not in task.applies_to for task in selected):
            raise ContractError("toy blueprint contains a task for another lane")
        if set(task.job for task in selected) != set(WORKSHOP_JOBS):
            raise ContractError("toy blueprint must cover all five Workshop jobs")
        if len({task.key for task in selected}) != len(selected):
            raise ContractError("toy blueprint task keys must be unique")
        object.__setattr__(self, "tasks", selected)

    @classmethod
    def for_lane(cls, lane: str) -> "ToyBlueprint":
        return cls(lane, tuple(task for task in TOY_TASKS if lane in task.applies_to))

    @property
    def sha256(self) -> str:
        encoded = json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def tasks_for(self, job: str) -> Tuple[ToyTask, ...]:
        if job not in WORKSHOP_JOBS:
            raise ContractError("unknown Workshop job %r" % job)
        return tuple(task for task in self.tasks if task.job == job)

    def required_capabilities(self, job: str) -> Tuple[str, ...]:
        return tuple(task.capability for task in self.tasks_for(job))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "toy-workshop",
            "audience": "grown-ups-14-plus",
            "lane": self.lane,
            "jobs": list(WORKSHOP_JOBS),
            "tasks": [task.to_dict() for task in self.tasks],
        }


def playful_make_request(
    wish: Wish, taste: Taste, blueprint: ToyBlueprint
) -> Mapping[str, Any]:
    """Bind the V1 product promise into every default Make request."""

    if not isinstance(wish, Wish) or not isinstance(taste, Taste):
        raise ContractError("playful Make requires a typed Wish and Taste")
    wish.assert_valid()
    taste.assert_valid()
    return {
        "schema_version": 1,
        "wish": wish.to_dict(),
        "taste": taste.to_binding(),
        "blueprint": blueprint.to_dict(),
        "brief": {
            "workshop": "Santa's workshop for Wish-shaped playthings",
            "audience": "grown-ups, 14 and up",
            "promise": "Make a cool plaything whose rules or form exist because of this Wish.",
            "download_bar": (
                "The result cannot be interchangeable with a model that existed for download "
                "before this Wish. Personalization must change rules, geometry, mechanism, "
                "scientific framing, or composition."
            ),
            "tone": "Cool beats cute. Never twee, generic, or decoration-only.",
            "utility_rule": (
                "If the Wish sounds useful, make the playable or wondrous version. "
                "Nothing may be merely useful."
            ),
            "product_lanes": list(PLAYTHING_LANES),
            "invented_game_release_rule": (
                "Simulation may reject an invented game but may not release it. "
                "Independent humans must play the exact prototype and ask to play again."
            ),
            "deliverables": (
                "build spec, parametric source, STEP, printable parts, assembly, "
                "fixed-view renders, rules or interaction instructions, and unresolved claims"
            ),
        },
    }


__all__ = [
    "PLAYTHING_LANES",
    "TOY_TASKS",
    "WORKSHOP_JOBS",
    "ToyBlueprint",
    "ToyTask",
    "playful_make_request",
]
