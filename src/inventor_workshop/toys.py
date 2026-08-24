"""The opinionated first Workshop: playthings for grown-ups.

This module is deliberately product-specific.  Autonomous Workshop is not a
generic physical-product framework in its first version.  It makes table games,
desk toys, tiny models or characters, and puzzles or keepsakes with play in
them.  A useful Wish is interpreted as the playful version of that object.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence, Tuple

from .errors import ContractError
from .make import Wish
from .taste import Taste


WORKSHOP_JOBS: Tuple[str, ...] = ("wish", "make", "playtest", "docs", "deliver")
PLAYTHING_LANES: Tuple[str, ...] = (
    "table-game",
    "desk-toy",
    "model-character",
    "puzzle-keepsake",
)


@dataclass(frozen=True)
class ToyTask:
    """One backstage task owned by one of the five Workshop jobs."""

    key: str
    job: str
    purpose: str
    evidence: str
    capability: str
    applies_to: Sequence[str] = PLAYTHING_LANES
    external: bool = False

    def __post_init__(self) -> None:
        if self.job not in WORKSHOP_JOBS:
            raise ContractError("toy task job must be Wish, Make, Playtest, Docs, or Deliver")
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


# Alice supplies the ordering and evidence discipline.  Peter's pinned CAD
# skills supply the STEP-first Make recipe.  Richter's text2game/text2cad work
# supplies the executable-game, multi-lens, fit, slice, repair, and postmortem
# lessons.  The source projects remain pinned references; these task contracts
# are a small clean Workshop vocabulary rather than copied pipelines.
TOY_TASKS: Tuple[ToyTask, ...] = (
    ToyTask(
        "wish.scope",
        "wish",
        "Preserve the person's words and turn utility into a playful interpretation.",
        "Exact Wish and Taste hashes plus the chosen plaything lane.",
        "wish-intake",
    ),
    ToyTask(
        "make.discover",
        "make",
        "Research prior art, safety boundaries, cultural context, and the opportunity.",
        "Cited research and three genuinely different directions.",
        "research",
    ),
    ToyTask(
        "make.choose",
        "make",
        "Choose one direction with a signature moment, character, or mechanism.",
        "A decision record bound to the rejected alternatives and Taste.",
        "invention",
    ),
    ToyTask(
        "make.rules",
        "make",
        "Write complete executable rules and an AI-player model.",
        "Rules, setup, legal actions, end condition, scoring, ties, and simulator source.",
        "game-design",
        ("table-game",),
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
        "Check that the result is a plaything with soul rather than plain utility.",
        "Independent delight and Taste-alignment verdicts.",
        "independent-review",
    ),
    ToyTask(
        "playtest.game",
        "playtest",
        "Have seeded optimizing, social, exploratory, and adversarial AI players test it.",
        "Reproducible traces covering rules, termination, balance, exploits, fun, and flow.",
        "game-simulation",
        ("table-game",),
    ),
    ToyTask(
        "playtest.mechanics",
        "playtest",
        "Test every physical interaction, fit, motion, assembly path, and failure mode.",
        "Measured B-rep, interference, fit, motion, and assembly evidence.",
        "mechanical-test",
    ),
    ToyTask(
        "playtest.print",
        "playtest",
        "Test topology, orientation, plate packing, slicing, material, time, and supports.",
        "Strict mesh and exact slicer-profile receipts for every expected part.",
        "print-test",
    ),
    ToyTask(
        "playtest.people",
        "playtest",
        "Let independent grown-ups use the exact prototype without inventor coaching.",
        "Authenticated blind-use records, delight signals, confusion, and requested changes.",
        "human-playtest",
        external=True,
    ),
    ToyTask(
        "playtest.prototype",
        "playtest",
        "Print and test the exact physical prototype that later work will describe and ship.",
        "Printer, material, calibration, artifact, QA, safety, and physical-test receipts.",
        "physical-prototype",
        external=True,
    ),
    ToyTask(
        "docs.page",
        "docs",
        "Explain the plaything with beautiful truthful images, copy, rules, and instructions.",
        "Private page draft and readback bound to the approved artifact.",
        "product-docs",
        external=True,
    ),
    ToyTask(
        "docs.truth",
        "docs",
        "Reject claims, images, or specifications not supported by Playtest evidence.",
        "Claim-to-evidence map and exact page history hash.",
        "docs-review",
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
    """The shared recipe an elf gets before it writes any custom code."""

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
    """Bind the V1 product focus into every default Make request."""

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
            "workshop": "Santa's workshop for playthings",
            "audience": "grown-ups, 14 and up",
            "promise": "Make a plaything that creates joy, surprise, or a delightful interaction.",
            "utility_rule": (
                "If the Wish sounds useful, make the playful version. Nothing may be merely useful."
            ),
            "product_lanes": list(PLAYTHING_LANES),
            "deliverables": (
                "build spec, parametric source, STEP, printable parts, assembly, "
                "fixed-view renders, rules or interaction instructions, and an unresolved-claims list"
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
