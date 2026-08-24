#!/usr/bin/env python3
"""Build five honest, digitally verified Workshop showcase prototypes.

This is a repo-owned demonstration adapter, not production evidence.  It uses
real CadQuery B-reps and STL meshes, renders the exported mesh, seals the exact
bytes through the Workshop contracts, and stops at Playtest for evidence that
only a physical prototype or independent humans can supply.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    import cadquery as cq
    import numpy as np
    import trimesh
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover - deliberately fail closed
    raise SystemExit(
        "showcase generation requires cadquery, numpy, trimesh, and Pillow; "
        "no fixture geometry will be substituted (%s)" % exc
    ) from exc

from inventor_workshop import attribute_product_description
from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.jobs import Made, MakeContext, Need, PlaytestContext, WaitingFor
from inventor_workshop.models import PlaytestResult
from inventor_workshop.playtest import Playtest
from inventor_workshop.workshop import WorkshopTools


SCHEMA_VERSION = 1
BUILDER_ID = "showcase-real-cad-v1"
PLAYTEST_ID = "showcase-digital-playtest-v1"
EVALUATOR_VERSION = "1.0.0"
BED_MM = (256.0, 256.0, 256.0)
SIMULATION_GAMES = 1_200
SIMULATION_SEED = 260_823


@dataclass(frozen=True)
class ProductSpec:
    inventor_id: str
    inventor_name: str
    slug: str
    title: str
    lane: str
    objective: str
    summary: str
    description: str
    extension_level: str
    playtest_rounds: int
    design: Mapping[str, Any]
    limitations: Sequence[str]


SPECS: tuple[ProductSpec, ...] = (
    ProductSpec(
        "alice",
        "Alice",
        "five-job-checkers",
        "Five-Job Checkers",
        "classics-made-yours",
        "I wish our five-job Workshop became a checkers set for late-night design reviews—black and warm gold, architectural rather than cute.",
        "A known checkers game made into an architectural portrait of the Workshop's five jobs.",
        "A regulation-readable checkers edition whose five-ring and five-spoke pieces, five brass-like threshold markers, and midnight grid turn the Workshop workflow into table presence without changing the known game. By Alice.",
        "taste-only",
        2,
        {
            "kind": "classic-checkers-edition",
            "known_rules": "English draughts/checkers; this edition does not alter play",
            "board_mm": [132.0, 132.0, 5.5],
            "grid": [8, 8],
            "cell_mm": 14.5,
            "piece_count": {"five-ring": 12, "five-spoke": 12},
            "wish_features": [
                "five raised threshold markers represent Wish, Make, Playtest, Instructions, Deliver",
                "five-ring and five-spoke motifs distinguish both sides by touch and silhouette",
                "black and warm-gold architectural composition",
            ],
        },
        (
            "Known rules are documented, but independent rule/readability playtest is still required.",
            "No exact part has been printed, sliced with a locked printer profile, or handled by people.",
        ),
    ),
    ProductSpec(
        "bob",
        "Bob",
        "comet-geneva",
        "Comet Geneva",
        "moving-machines",
        "I wish for a hand-cranked desk machine where one comet makes six precise jumps around a midnight orbit.",
        "A six-step Geneva mechanism that turns one continuous crank into a comet's deliberate orbital jumps.",
        "A compact exposed Geneva machine: turn the cratered drive wheel and its comet pin advances the six-station orbit one crisp step at a time. The mechanism—not a plaque—is the Wish. By Bob.",
        "custom-make",
        4,
        {
            "kind": "six-step-geneva-machine",
            "base_mm": [94.0, 68.0, 5.0],
            "geneva_slots": 6,
            "step_degrees": 60.0,
            "drive_radius_mm": 18.0,
            "geneva_radius_mm": 23.0,
            "nominal_clearance_mm": 0.35,
            "wish_features": [
                "continuous crank becomes six discrete orbital jumps",
                "comet pin is the visible cause of motion",
                "six stations form the midnight orbit",
            ],
        },
        (
            "Kinematic relationships are digitally checked only; cycle life, friction, wear, and pinch safety need the exact print.",
            "No locked slicer receipt or physical repeated-cycle evidence exists.",
        ),
    ),
    ProductSpec(
        "eve",
        "Eve",
        "rackhaven-night-shift",
        "Rackhaven: Night Shift",
        "little-worlds",
        "I wish my three-node homelab—Comet, Moss, and Void—became a tiny orbital engine room with one night-shift operator.",
        "A personalized three-node homelab transformed into a cinematic orbital engine room.",
        "Comet's fins, Moss's cooling pipes, and Void's halo make three named nodes recognizable as a single engine-room world, watched over by a lone night-shift operator. By Eve.",
        "taste-only",
        3,
        {
            "kind": "personalized-homelab-diorama",
            "deck_mm": [108.0, 72.0, 5.0],
            "nodes": ["Comet", "Moss", "Void"],
            "node_signatures": {
                "Comet": "swept cooling fins",
                "Moss": "paired vertical coolant pipes",
                "Void": "suspended orbital halo",
            },
            "wish_features": [
                "three node identities are geometry, not labels",
                "circuit trenches connect the rack city",
                "one operator establishes scale and night-shift story",
            ],
        },
        (
            "The named-node mapping is explicit, but owner recognition needs independent reference-bound review.",
            "Fine details and handling durability need an exact physical print.",
        ),
    ),
    ProductSpec(
        "ivy",
        "Ivy",
        "montauk-tide-orrery",
        "Montauk Tide Orrery",
        "holdable-science",
        "I wish I could hold the spring-neap tide cycle for Montauk and predict what alignment makes the larger tide.",
        "A hand-operated alignment model for reasoning about spring and neap tides at Montauk.",
        "Rotate the tide arm through Sun–Earth–Moon alignment and quadrature: the four notches invite a prediction before the model reveals why spring and neap ranges differ. It is a qualitative teaching model, not a tide forecast. By Ivy.",
        "taste-only",
        3,
        {
            "kind": "qualitative-tide-orrery",
            "base_diameter_mm": 104.0,
            "phase_positions_degrees": [0, 90, 180, 270],
            "relationship": {
                "aligned_or_opposed": "spring-tide configuration",
                "quadrature": "neap-tide configuration",
            },
            "scope": "qualitative alignment model; not to scale and not predictive",
            "source": "https://oceanservice.noaa.gov/education/tutorial_tides/tides06_variations.html",
            "wish_features": [
                "Montauk-specific request is framed as a prediction experiment",
                "four detents embody the spring-neap cycle",
                "two-lobed tide arm makes the alignment comparison tactile",
            ],
        },
        (
            "The source relationship and geometry are auditable, but an independent science expert has not reviewed this exact object.",
            "Detent feel, comprehension, and safety need physical and human playtest.",
        ),
    ),
    ProductSpec(
        "leo",
        "Leo",
        "counterorbit",
        "Counterorbit",
        "invented-games",
        "I wish for a tense two-player game where our five Workshop jobs orbit, interfere, and only align when a plan survives the other inventor.",
        "An original ten-turn alignment duel played across a fixed core and rotating outer orbit.",
        "Place one of five signal stones, rotate the shared orbit, and try to hold a three-point wedge while every move reframes both players' plans. The five-job topology changes play rather than decorating it. By Leo.",
        "custom-playtest",
        10,
        {
            "kind": "original-two-player-orbit-game",
            "players": 2,
            "maximum_turns": 10,
            "inner_wells": 5,
            "outer_wells": 10,
            "tokens_per_player": 5,
            "player_styles": ["optimizing", "social", "exploratory", "adversarial"],
            "wish_features": [
                "five inner stations are the five Workshop jobs",
                "the shared rotating orbit changes adjacency after every placement",
                "opposition is literal interference with a surviving alignment plan",
            ],
        },
        (
            "Seeded simulation can reject obvious failures but cannot establish fun or release readiness.",
            "Independent humans have not played the exact physical game and asked to play again.",
        ),
    ),
)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")
    if executable:
        path.chmod(0o755)


def _load_profile(inventor_id: str):
    path = REPO_ROOT / "inventors" / inventor_id / "profile.py"
    module_spec = importlib.util.spec_from_file_location(
        "showcase_%s_profile" % inventor_id, path
    )
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("cannot load canonical profile %s" % path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def _rounded_box(length: float, width: float, height: float, radius: float = 2.0):
    return (
        cq.Workplane("XY")
        .box(length, width, height, centered=(True, True, False))
        .edges("|Z")
        .fillet(radius)
    )


def _compound(shapes: Sequence[Any]):
    values = []
    for shape in shapes:
        value = shape.val() if hasattr(shape, "val") else shape
        if isinstance(value, cq.Compound):
            values.extend(value.Solids())
        else:
            values.append(value)
    if not values:
        raise RuntimeError("cannot export an empty CAD compound")
    return cq.Compound.makeCompound(values)


def _shape(value: Any):
    return value.val() if hasattr(value, "val") else value


def _placed(value: Any, xyz: tuple[float, float, float], angle: float = 0.0):
    result = _shape(value)
    if angle:
        result = result.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), angle)
    return result.translate(cq.Vector(*xyz))


@dataclass(frozen=True)
class GeometryBundle:
    assembled: Any
    parts: Mapping[str, Any]
    digital_checks: Mapping[str, Any]


def _alice_geometry(spec: ProductSpec) -> GeometryBundle:
    cell = 14.5
    base = _rounded_box(132.0, 132.0, 5.0, 3.0)
    board_shapes: list[Any] = [base]
    for row in range(8):
        for column in range(8):
            if (row + column) % 2 == 0:
                x = (column - 3.5) * cell
                y = (row - 3.5) * cell
                square = cq.Workplane("XY").box(
                    cell - 0.55, cell - 0.55, 0.55, centered=(True, True, False)
                )
                board_shapes.append(_placed(square, (x, y, 5.0)))
    # Five architectural thresholds make the workflow structural, not printed copy.
    for index in range(5):
        marker = cq.Workplane("XY").box(8.5, 2.4, 1.7, centered=(True, True, False))
        board_shapes.append(_placed(marker, ((index - 2) * 12.0, -63.0, 5.0)))
    board = _compound(board_shapes)

    # A checker must sit comfortably inside a 14.5 mm square.  The earlier
    # 20.4 mm draft nearly touched diagonal neighbors and failed Alice's table
    # legibility bar even though the meshes were valid.
    token_base = cq.Workplane("XY").circle(5.8).extrude(3.2)
    ring_shapes: list[Any] = [token_base]
    spoke_shapes: list[Any] = [token_base]
    for index in range(5):
        angle = math.radians(index * 72.0)
        ring_shapes.append(
            _placed(
                cq.Workplane("XY").circle(0.9).extrude(1.25),
                (3.25 * math.cos(angle), 3.25 * math.sin(angle), 3.2),
            )
        )
        spoke = cq.Workplane("XY").box(4.1, 1.05, 1.25, centered=(True, True, False))
        spoke_shapes.append(_placed(spoke, (1.8, 0.0, 3.2), index * 72.0))
    five_ring = _compound(ring_shapes)
    five_spoke = _compound(spoke_shapes)

    assembly: list[Any] = [board]
    side_a = []
    side_b = []
    for row in range(3):
        for column in range(8):
            if (row + column) % 2 == 1:
                side_a.append(((column - 3.5) * cell, (row - 3.5) * cell))
    for row in range(5, 8):
        for column in range(8):
            if (row + column) % 2 == 1:
                side_b.append(((column - 3.5) * cell, (row - 3.5) * cell))
    for x, y in side_a:
        assembly.append(_placed(five_ring, (x, y, 5.55)))
    for x, y in side_b:
        assembly.append(_placed(five_spoke, (x, y, 5.55)))
    return GeometryBundle(
        _compound(assembly),
        {"board": board, "five-ring-piece": five_ring, "five-spoke-piece": five_spoke},
        {
            "classic": "English checkers geometry: 8x8 grid, 12 pieces per side",
            "rule_changes": 0,
            "grid_cells": 64,
            "piece_count": 24,
            "tactile_side_motifs": ["five-ring", "five-spoke"],
        },
    )


def _bob_geometry(spec: ProductSpec) -> GeometryBundle:
    base = _rounded_box(94.0, 68.0, 5.0, 4.0)
    # Axle posts are deliberately separate replaceable parts in this prototype.
    axle = cq.Workplane("XY").circle(2.35).extrude(10.0)
    drive = cq.Workplane("XY").circle(18.0).circle(2.7).extrude(4.0)
    for index in range(6):
        crater = cq.Workplane("XY").circle(1.6).extrude(0.8)
        angle = math.radians(index * 60.0)
        drive = drive.cut(
            _placed(crater, (11.8 * math.cos(angle), 11.8 * math.sin(angle), 3.4))
        )
    comet_pin = cq.Workplane("XY").circle(2.15).extrude(6.0)
    hand_knob = cq.Workplane("XY").circle(3.2).extrude(8.0)
    drive_part = _compound(
        [drive, _placed(comet_pin, (14.5, 0.0, 4.0)), _placed(hand_knob, (-11.5, 0.0, 4.0))]
    )

    geneva = cq.Workplane("XY").circle(23.0).circle(2.7).extrude(5.0)
    for index in range(6):
        # Each open radial slot accepts the drive pin; the generous width makes
        # this a printable prototype, while exact clearance still needs a print.
        slot = cq.Workplane("XY").box(17.0, 5.0, 7.0, centered=(True, True, False))
        slot = slot.translate((17.0, 0.0, -1.0)).rotate((0, 0, 0), (0, 0, 1), index * 60.0)
        geneva = geneva.cut(slot)
    station = cq.Workplane("XY").circle(1.6).extrude(1.2)
    geneva_shapes: list[Any] = [geneva]
    for index in range(6):
        angle = math.radians(index * 60.0 + 30.0)
        geneva_shapes.append(
            _placed(station, (16.8 * math.cos(angle), 16.8 * math.sin(angle), 5.0))
        )
    geneva_part = _compound(geneva_shapes)

    assembly = _compound(
        [
            base,
            _placed(axle, (-17.5, 0.0, 5.0)),
            _placed(axle, (18.0, 0.0, 5.0)),
            _placed(drive_part, (-17.5, 0.0, 8.0), 0.0),
            _placed(geneva_part, (18.0, 0.0, 8.0), 180.0),
        ]
    )
    return GeometryBundle(
        assembly,
        {"base": base, "axle": axle, "comet-drive": drive_part, "six-slot-orbit": geneva_part},
        {
            "kinematic_model": "six-slot external Geneva prototype",
            "input": "continuous manual crank",
            "output": "one 60 degree step per drive revolution",
            "slot_count": 6,
            "step_degrees": 60.0,
            "drive_pin_diameter_mm": 4.3,
            "slot_width_mm": 5.0,
            "nominal_pin_slot_clearance_mm": 0.7,
            "claim_scope": "dimensional/kinematic intent only; not a physical cycle test",
        },
    )


def _eve_geometry(spec: ProductSpec) -> GeometryBundle:
    deck = _rounded_box(108.0, 72.0, 5.0, 4.0)
    deck_shapes: list[Any] = [deck]
    for y in (-19.0, 0.0, 19.0):
        trench = cq.Workplane("XY").box(82.0, 2.2, 0.9, centered=(True, True, False))
        deck_shapes.append(_placed(trench, (0.0, y, 5.0)))
    deck_part = _compound(deck_shapes)

    comet_core = _rounded_box(22.0, 18.0, 34.0, 1.8)
    comet_shapes: list[Any] = [comet_core]
    for side in (-1.0, 1.0):
        for z in (7.0, 15.0, 23.0):
            fin = cq.Workplane("XY").box(7.0, 16.0, 2.2, centered=(True, True, False))
            comet_shapes.append(_placed(fin, (side * 13.0, 0.0, z)))
    comet = _compound(comet_shapes)

    moss_core = _rounded_box(22.0, 18.0, 31.0, 1.8)
    moss_shapes: list[Any] = [moss_core]
    for x in (-7.5, 7.5):
        moss_shapes.append(_placed(cq.Workplane("XY").circle(2.2).extrude(35.0), (x, -10.5, 0.0)))
        moss_shapes.append(_placed(cq.Workplane("XY").circle(3.5).extrude(2.0), (x, -10.5, 33.0)))
    moss = _compound(moss_shapes)

    void_core = _rounded_box(22.0, 18.0, 32.0, 1.8)
    halo = cq.Solid.makeTorus(
        12.0, 1.7, cq.Vector(0.0, 0.0, 24.0), cq.Vector(1.0, 0.0, 0.0)
    )
    void = _compound([void_core, halo])

    operator_profile = (
        cq.Workplane("XZ")
        .moveTo(0.0, 0.0)
        .lineTo(3.6, 0.0)
        .lineTo(3.6, 2.0)
        .lineTo(2.5, 2.0)
        .lineTo(2.5, 10.0)
        .lineTo(3.4, 10.0)
        .lineTo(3.4, 12.0)
        .lineTo(0.8, 15.0)
        .lineTo(0.8, 16.0)
        .lineTo(0.0, 16.0)
        .close()
    )
    operator = operator_profile.revolve(360.0)
    assembly = _compound(
        [
            deck_part,
            _placed(comet, (-31.0, 5.0, 5.9)),
            _placed(moss, (0.0, 5.0, 5.9)),
            _placed(void, (31.0, 5.0, 5.9)),
            _placed(operator, (0.0, -23.0, 5.9)),
        ]
    )
    return GeometryBundle(
        assembly,
        {"engine-deck": deck_part, "comet-node": comet, "moss-node": moss, "void-node": void, "night-operator": operator},
        {
            "personalization_map": {
                "Comet": "six swept side fins",
                "Moss": "paired exposed coolant pipes",
                "Void": "vertical orbital halo",
                "night shift": "single operator facing all three nodes",
            },
            "generic_nameplates": 0,
            "reference_scope": "Wish text only; no private likeness assets were used",
        },
    )


def _ivy_geometry(spec: ProductSpec) -> GeometryBundle:
    base = cq.Workplane("XY").circle(52.0).extrude(4.0)
    base_shapes: list[Any] = [base]
    for angle in (0.0, 90.0, 180.0, 270.0):
        rad = math.radians(angle)
        notch = cq.Workplane("XY").box(7.0, 2.4, 1.6, centered=(True, True, False))
        base_shapes.append(_placed(notch, (45.0 * math.cos(rad), 45.0 * math.sin(rad), 4.0), angle))
    base_part = _compound(base_shapes)
    post = cq.Workplane("XY").circle(2.3).extrude(16.0)

    arm_bar = cq.Workplane("XY").box(78.0, 7.0, 3.2, centered=(True, True, False))
    arm_bar = arm_bar.cut(cq.Workplane("XY").circle(2.75).extrude(5.0))
    tide_lobes = [arm_bar]
    for x in (-40.0, 40.0):
        tide_lobes.append(_placed(cq.Workplane("XY").circle(8.0).extrude(3.2), (x, 0.0, 0.0)))
    tide_arm = _compound(tide_lobes)
    earth = cq.Solid.makeSphere(8.0, cq.Vector(0.0, 0.0, 8.0)).cut(
        cq.Workplane("XY").circle(2.7).extrude(17.0).val()
    )
    moon_profile = cq.Workplane("XZ").moveTo(0.0, 0.0)
    for radius, height in (
        (4.0, 0.0),
        (4.0, 10.0),
        (3.0, 10.0),
        (5.0, 12.0),
        (5.0, 15.0),
        (3.0, 18.0),
        (1.0, 19.0),
        (0.0, 19.0),
    ):
        moon_profile = moon_profile.lineTo(radius, height)
    moon = moon_profile.close().revolve(360.0)
    sun_marker = _compound(
        [
            cq.Workplane("XY").box(15.0, 5.0, 3.0, centered=(True, True, False)),
            _placed(cq.Workplane("XY").circle(4.5).extrude(3.0), (9.0, 0.0, 0.0)),
        ]
    )
    assembly = _compound(
        [
            base_part,
            _placed(post, (0.0, 0.0, 4.0)),
            _placed(tide_arm, (0.0, 0.0, 9.0), 35.0),
            _placed(earth, (0.0, 0.0, 10.5)),
            _placed(moon, (28.0 * math.cos(math.radians(35.0)), 28.0 * math.sin(math.radians(35.0)), 12.2)),
            _placed(sun_marker, (-39.0, 0.0, 4.0), 180.0),
        ]
    )
    return GeometryBundle(
        assembly,
        {"phase-base": base_part, "center-post": post, "tide-arm": tide_arm, "earth-hub": earth, "moon-marker": moon, "sun-arrow": sun_marker},
        {
            "source": spec.design["source"],
            "tested_relationships": [
                {"angle_degrees": 0, "configuration": "aligned", "model_result": "spring"},
                {"angle_degrees": 90, "configuration": "quadrature", "model_result": "neap"},
                {"angle_degrees": 180, "configuration": "opposed", "model_result": "spring"},
                {"angle_degrees": 270, "configuration": "quadrature", "model_result": "neap"},
            ],
            "claim_scope": "qualitative demonstration; not to scale, not a Montauk tide prediction",
        },
    )


def _leo_geometry(spec: ProductSpec) -> GeometryBundle:
    base = cq.Workplane("XY").circle(35.0).extrude(5.0)
    for index in range(5):
        angle = math.radians(index * 72.0)
        well = cq.Workplane("XY").circle(4.2).extrude(3.0)
        base = base.cut(_placed(well, (22.0 * math.cos(angle), 22.0 * math.sin(angle), 3.1)))
    core = _compound([base, cq.Workplane("XY").circle(3.0).extrude(9.0)])

    ring = cq.Workplane("XY").circle(52.0).circle(36.3).extrude(5.0)
    for index in range(10):
        angle = math.radians(index * 36.0)
        well = cq.Workplane("XY").circle(4.2).extrude(3.0)
        ring = ring.cut(_placed(well, (44.0 * math.cos(angle), 44.0 * math.sin(angle), 3.1)))
    ring_part = ring

    token_base = cq.Workplane("XY").circle(3.7).extrude(3.2)
    token_ring = _compound(
        [token_base, _placed(cq.Workplane("XY").circle(1.4).extrude(1.1), (0.0, 0.0, 3.2))]
    )
    token_spoke_shapes: list[Any] = [token_base]
    for index in range(5):
        spoke = cq.Workplane("XY").box(3.8, 0.9, 1.0, centered=(True, True, False))
        token_spoke_shapes.append(_placed(spoke, (1.5, 0.0, 3.2), index * 72.0))
    token_spoke = _compound(token_spoke_shapes)
    assembly_shapes: list[Any] = [core, _placed(ring_part, (0.0, 0.0, 0.25), 18.0)]
    for index in range(5):
        angle = math.radians(index * 72.0)
        assembly_shapes.append(_placed(token_ring, (22.0 * math.cos(angle), 22.0 * math.sin(angle), 5.5)))
    for index in range(5):
        angle = math.radians((index * 2 + 1) * 36.0 + 18.0)
        assembly_shapes.append(_placed(token_spoke, (44.0 * math.cos(angle), 44.0 * math.sin(angle), 5.75)))
    return GeometryBundle(
        _compound(assembly_shapes),
        {"five-job-core": core, "counter-orbit": ring_part, "ring-signal": token_ring, "spoke-signal": token_spoke},
        {
            "topology": {"inner_wells": 5, "outer_wells": 10, "rotating_offsets": 10},
            "inventory": {"ring-signals": 5, "spoke-signals": 5},
            "maximum_turns": 10,
            "physical_state_change": "outer orbit rotates one notch after every placement",
        },
    )


GEOMETRY_BUILDERS: Mapping[str, Callable[[ProductSpec], GeometryBundle]] = {
    "alice": _alice_geometry,
    "bob": _bob_geometry,
    "eve": _eve_geometry,
    "ivy": _ivy_geometry,
    "leo": _leo_geometry,
}


def _export_shape(value: Any, step_path: Path, stl_path: Path) -> None:
    """Export a real OCC shape; never fall back to placeholder bytes."""

    step_path.parent.mkdir(parents=True, exist_ok=True)
    shape = _shape(value)
    if shape.isNull() or not shape.Solids():
        raise RuntimeError("refusing to export null or solid-free CAD")
    cq.exporters.export(shape, str(step_path))
    cq.exporters.export(
        shape,
        str(stl_path),
        tolerance=0.12,
        angularTolerance=0.10,
    )
    if step_path.stat().st_size < 256 or stl_path.stat().st_size < 84:
        raise RuntimeError("CAD exporter returned an implausibly small file")


def _mesh(path: Path):
    # STL stores triangles independently; Trimesh's deterministic processing
    # welds coincident vertices before topological checks without changing the
    # exported surface.
    loaded = trimesh.load_mesh(str(path), file_type="stl", force="mesh", process=True)
    if not isinstance(loaded, trimesh.Trimesh):
        raise RuntimeError("STL did not load as an exact triangle mesh: %s" % path)
    if loaded.faces.shape[0] < 4 or not np.isfinite(loaded.vertices).all():
        raise RuntimeError("STL has no finite closed geometry: %s" % path)
    return loaded


def _validate_cad_pair(step_path: Path, stl_path: Path) -> Mapping[str, Any]:
    imported = cq.importers.importStep(str(step_path))
    solids = imported.solids().vals()
    if not solids:
        raise RuntimeError("STEP re-import produced no solids: %s" % step_path)
    bbox = imported.val().BoundingBox()
    mesh = _mesh(stl_path)
    bounds = mesh.bounds
    extents = np.asarray(mesh.extents, dtype=float)
    watertight = bool(mesh.is_watertight)
    winding = bool(mesh.is_winding_consistent)
    if not watertight or not winding:
        raise RuntimeError("STL is not watertight and consistently wound: %s" % stl_path)
    if bool(np.any(extents <= 0.0)) or bool(np.any(extents > np.asarray(BED_MM) + 1e-6)):
        raise RuntimeError("STL exceeds the declared 256 mm digital envelope: %s" % stl_path)
    return {
        "step": {
            "sha256": _sha_file(step_path),
            "bytes": step_path.stat().st_size,
            "reimported": True,
            "solid_count": len(solids),
            "bbox_mm": [round(bbox.xlen, 4), round(bbox.ylen, 4), round(bbox.zlen, 4)],
        },
        "stl": {
            "sha256": _sha_file(stl_path),
            "bytes": stl_path.stat().st_size,
            "triangles": int(mesh.faces.shape[0]),
            "watertight": watertight,
            "winding_consistent": winding,
            "volume_mm3": round(abs(float(mesh.volume)), 4),
            "bounds_mm": [[round(float(v), 4) for v in row] for row in bounds],
            "extents_mm": [round(float(v), 4) for v in extents],
            "inside_declared_bed": True,
        },
    }


RENDER_PALETTES = {
    "alice": ((18, 21, 29), (214, 164, 73)),
    "bob": ((28, 31, 38), (238, 95, 62)),
    "eve": ((20, 28, 42), (94, 197, 191)),
    "ivy": ((18, 38, 48), (237, 194, 80)),
    "leo": ((24, 23, 38), (188, 93, 232)),
}


def _render_exact_mesh(stl_path: Path, output_path: Path, inventor_id: str) -> Mapping[str, Any]:
    """Draw a fixed orthographic view directly from the exported STL triangles."""

    mesh = _mesh(stl_path)
    vertices = np.asarray(mesh.vertices, dtype=float)
    # Camera sits above the (+x,+y,+z) octant.  The explicit orthonormal
    # basis avoids the easy sign mistake that turns an isometric hero into an
    # underside inspection.
    view = np.array((1.0, 1.0, 1.15), dtype=float)
    view /= np.linalg.norm(view)
    right = np.array((1.0, -1.0, 0.0), dtype=float)
    right /= np.linalg.norm(right)
    # Screen-up has a positive world-Z component, so tall features rise above
    # their bases instead of looking as if they dangle beneath them.
    up = np.cross(right, view)
    up /= np.linalg.norm(up)
    transformed = np.column_stack((vertices @ right, vertices @ up, vertices @ view))
    projected = transformed[:, :2]
    low = projected.min(axis=0)
    high = projected.max(axis=0)
    span = np.maximum(high - low, 1e-9)
    width, height = 1600, 1200
    margin = 115
    scale = min((width - 2 * margin) / span[0], (height - 2 * margin) / span[1])
    points = (projected - (low + high) / 2.0) * scale
    points[:, 0] += width / 2.0
    points[:, 1] = height / 2.0 - points[:, 1]

    background = Image.new("RGB", (width, height), (244, 239, 229))
    draw = ImageDraw.Draw(background)
    # A soft deterministic ground oval makes the geometry legible without
    # claiming a photograph or hiding the exact triangle silhouette.
    draw.ellipse(
        (margin, height - 245, width - margin, height - 90),
        fill=(216, 207, 191),
    )
    faces = np.asarray(mesh.faces, dtype=np.int64)
    tri = transformed[faces]
    original_tri = vertices[faces]
    depth = tri[:, :, 2].mean(axis=1)
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    safe = np.maximum(lengths, 1e-12)
    light = np.clip(np.abs(normals[:, 2] / safe) * 0.58 + 0.32, 0.24, 0.96)
    dark, accent = RENDER_PALETTES[inventor_id]
    # The lowest connected shell is the dark plinth/board; separately exported
    # raised geometry gets the inventor accent.  This preserves exact triangles
    # while making grids, mechanisms, towers, markers, and playing pieces easy
    # to read in a GitHub-sized image.
    face_accent = np.zeros(len(faces), dtype=bool)
    global_min_z = float(vertices[:, 2].min())
    components = trimesh.graph.connected_components(
        mesh.face_adjacency, nodes=np.arange(len(faces))
    )
    for component in components:
        indices = np.asarray(component, dtype=np.int64)
        if float(original_tri[indices, :, 2].min()) > global_min_z + 0.1:
            face_accent[indices] = True
    order = np.argsort(depth)
    for face_index in order:
        polygon = [tuple(points[index]) for index in faces[face_index]]
        base = accent if face_accent[face_index] else dark
        shade = float(light[face_index])
        color = tuple(max(0, min(255, int(channel * shade + 18))) for channel in base)
        draw.polygon(polygon, fill=color)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = background.resize((1200, 900), Image.Resampling.LANCZOS)
    rendered.save(output_path, format="PNG", optimize=True)
    return {
        "kind": "fixed-view exact-STL render",
        "input": "cad/product.stl",
        "input_sha256": _sha_file(stl_path),
        "output": "images/hero.png",
        "output_sha256": _sha_file(output_path),
        "pixels": [1200, 900],
        "camera": {
            "projection": "orthographic",
            "position_direction": [1.0, 1.0, 1.15],
            "view": "above-isometric",
        },
        "concept_art": False,
    }


MODEL_WRAPPER = r'''#!/usr/bin/env python3
"""Rebuild this exact declarative CAD design through the shared Workshop tool."""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

source = Path(__file__).resolve()
builder = next(
    (parent / "tools" / "build_showcase_products.py"
     for parent in source.parents
     if (parent / "tools" / "build_showcase_products.py").is_file()),
    None,
)
if builder is None:
    raise SystemExit("run this source inside an autonomous-workshop checkout")
spec = importlib.util.spec_from_file_location("showcase_product_builder", builder)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load the shared Workshop builder")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
destination = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else source.parent / "rebuilt"
module.rebuild_from_design(source.parent / "design.json", destination)
print(destination)
'''


def rebuild_from_design(design_path: Path, output_root: Path) -> Mapping[str, Any]:
    """Rebuild STEP/STL files from one sealed product's declarative source."""

    design = json.loads(Path(design_path).read_text(encoding="utf-8"))
    inventor_id = design.get("inventor_id")
    spec = next((item for item in SPECS if item.inventor_id == inventor_id), None)
    if spec is None or design.get("design") != spec.design:
        raise RuntimeError("design.json is not a known exact showcase design")
    destination = Path(output_root).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError("CAD rebuild destination must be fresh and empty")
    destination.mkdir(parents=True, exist_ok=True)
    geometry = GEOMETRY_BUILDERS[inventor_id](spec)
    record = _build_cad_files(geometry, destination)
    _write_json(destination / "rebuild.json", record)
    return record


def _build_cad_files(geometry: GeometryBundle, destination: Path) -> Mapping[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    _export_shape(
        geometry.assembled, destination / "product.step", destination / "product.stl"
    )
    part_records = {}
    for name, part in sorted(geometry.parts.items()):
        step_path = destination / "parts" / (name + ".step")
        stl_path = destination / "parts" / (name + ".stl")
        _export_shape(part, step_path, stl_path)
        part_records[name] = _validate_cad_pair(step_path, stl_path)
    product_record = _validate_cad_pair(destination / "product.step", destination / "product.stl")
    return {"schema_version": 1, "product": product_record, "parts": part_records}


COUNTERORBIT_RULES = """\
# Counterorbit

Counterorbit is an original two-player alignment game made for this Wish.
It is a digitally built prototype, not a released game.

## What is in the prototype

- one fixed five-station core;
- one rotating orbit with ten wells;
- five ring signals for Player A;
- five spoke signals for Player B.

## Setup

Set the outer orbit to offset 0. Put all ten signals beside the board. Player A
starts; alternate the starting player between games.

## Turn

1. Place one of your signals in any empty inner or outer well.
2. Rotate the outer orbit exactly one notch clockwise or counterclockwise.
3. Check for an alignment wedge.

An inner station frames two neighboring outer wells. You win when your signal
occupies that inner station and both currently framed outer wells. Rotation
changes which outer wells each inner station frames. If your rotation completes
both players' wedges, the player who made the move wins.

## End

The first wedge wins. If all ten signals have been placed without a wedge,
compare each player's best incomplete wedge (occupied positions in one wedge),
then the number of two-position threats. Higher wins; an exact tie is a draw.
Every game therefore ends in ten turns or fewer.

## Prototype boundary

The included seeded simulator checks executability, termination, gross seat
effects, and obvious strategies. It cannot prove fun. Counterorbit remains at
Playtest until independent humans play the exact physical prototype without
Leo coaching and ask to play again.
"""


COUNTERORBIT_SIMULATOR = r'''#!/usr/bin/env python3
"""Seeded executable simulation for the exact Counterorbit rules."""
from __future__ import annotations
import argparse
import json
import random

STYLES = ("optimizing", "social", "exploratory", "adversarial")

def wedge_cells(inner_index, offset):
    return inner_index, (2 * inner_index - offset) % 10, (2 * inner_index + 1 - offset) % 10

def wedge_counts(inner, outer, player, offset):
    counts = []
    for station in range(5):
        i, left, right = wedge_cells(station, offset)
        counts.append(sum((inner[i] == player, outer[left] == player, outer[right] == player)))
    return counts

def has_wedge(inner, outer, player, offset):
    return max(wedge_counts(inner, outer, player, offset)) == 3

def actions(inner, outer):
    empty = [("inner", index) for index, value in enumerate(inner) if value < 0]
    empty += [("outer", index) for index, value in enumerate(outer) if value < 0]
    return [(where, index, turn) for where, index in empty for turn in (-1, 1)]

def apply(inner, outer, offset, player, action):
    next_inner, next_outer = inner[:], outer[:]
    where, index, turn = action
    (next_inner if where == "inner" else next_outer)[index] = player
    return next_inner, next_outer, (offset + turn) % 10

def value(inner, outer, offset, player, action, style):
    ni, no, new_offset = apply(inner, outer, offset, player, action)
    opponent = 1 - player
    mine = wedge_counts(ni, no, player, new_offset)
    theirs = wedge_counts(ni, no, opponent, new_offset)
    if max(mine) == 3:
        return 10_000.0
    if style == "adversarial":
        return -80.0 * max(theirs) - 9.0 * sum(value == 2 for value in theirs) + max(mine)
    if style == "social":
        # Still tries to win, but favors developing several legible plans over
        # collapsing the position into a single forced threat.
        return 16.0 * max(mine) + 6.0 * sum(value == 2 for value in mine) - 10.0 * max(theirs)
    return 32.0 * max(mine) + 9.0 * sum(value == 2 for value in mine) - 25.0 * max(theirs)

def choose(inner, outer, offset, player, style, rng):
    possible = actions(inner, outer)
    if style == "exploratory":
        return rng.choice(possible)
    scored = [(value(inner, outer, offset, player, action, style), action) for action in possible]
    best = max(score for score, _ in scored)
    candidates = [action for score, action in scored if score == best]
    return rng.choice(candidates)

def final_score(inner, outer, player, offset):
    counts = wedge_counts(inner, outer, player, offset)
    return max(counts), sum(value == 2 for value in counts)

def play(style_a, style_b, seed, first_player):
    rng = random.Random(seed)
    inner, outer, offset = [-1] * 5, [-1] * 10, 0
    styles = (style_a, style_b)
    player = first_player
    trace = []
    for turn_number in range(1, 11):
        action = choose(inner, outer, offset, player, styles[player], rng)
        inner, outer, offset = apply(inner, outer, offset, player, action)
        trace.append({"turn": turn_number, "player": player, "action": list(action), "offset": offset})
        if has_wedge(inner, outer, player, offset):
            return {"winner": player, "turns": turn_number, "trace": trace}
        player = 1 - player
    score_a, score_b = final_score(inner, outer, 0, offset), final_score(inner, outer, 1, offset)
    winner = 0 if score_a > score_b else 1 if score_b > score_a else None
    return {"winner": winner, "turns": 10, "trace": trace}

def simulate(games, seed):
    rng = random.Random(seed)
    stats = {"A": 0, "B": 0, "draw": 0}
    first_seat = {"wins": 0, "games": 0}
    matchups = {}
    max_turns = 0
    samples = []
    for game_index in range(games):
        style_a = STYLES[(game_index // len(STYLES)) % len(STYLES)]
        style_b = STYLES[game_index % len(STYLES)]
        first = game_index % 2
        game_seed = rng.randrange(0, 2**63)
        result = play(style_a, style_b, game_seed, first)
        winner = result["winner"]
        stats["draw" if winner is None else "A" if winner == 0 else "B"] += 1
        first_seat["games"] += 1
        if winner == first:
            first_seat["wins"] += 1
        key = style_a + "-vs-" + style_b
        item = matchups.setdefault(key, {"games": 0, "A_wins": 0, "B_wins": 0, "draws": 0})
        item["games"] += 1
        item["draws" if winner is None else "A_wins" if winner == 0 else "B_wins"] += 1
        max_turns = max(max_turns, result["turns"])
        if len(samples) < 4:
            samples.append({"styles": [style_a, style_b], "seed": game_seed, **result})
    return {
        "schema_version": 1,
        "game": "Counterorbit",
        "evidence_class": "ai-simulation",
        "executable": True,
        "seed": seed,
        "requested_games": games,
        "completed_games": games,
        "terminated_games": games,
        "nonterminating_games": 0,
        "maximum_rules_turns": 10,
        "max_turns_observed": max_turns,
        "player_styles": list(STYLES),
        "outcomes": stats,
        "first_seat_win_rate": round(first_seat["wins"] / first_seat["games"], 6),
        "matchups": matchups,
        "sample_traces": samples,
        "claim_scope": "executability and digital strategy probe only; not evidence of fun or human replay demand",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=260823)
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.games < 1000:
        parser.error("showcase evidence requires at least 1000 games")
    result = simulate(args.games, args.seed)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(payload)
    print(payload, end="")

if __name__ == "__main__":
    main()
'''


def _artifact_readme(spec: ProductSpec) -> str:
    wish = "\n".join("> " + line for line in spec.objective.splitlines())
    limitations = "\n".join("- " + item for item in spec.limitations)
    return f"""\
# {spec.title}

![Exact-geometry render of {spec.title}](images/hero.png)

**Digitally built prototype · Waiting at Playtest**

## Wish

{wish}

## The plaything

{spec.description}

The shared Workshop Make produced editable declarative source, real STEP and
STL geometry, per-part exports, and the fixed render above from the exact
product STL. See [`cad/digital-build.json`](cad/digital-build.json) for the
machine-readable checks.

## What remains true

{limitations}

This bundle deliberately contains no box instructions, production claim,
shipping receipt, or claim that a render proves a physical product. The parent
[`workshop-run.json`](../workshop-run.json) records the exact Playtest needs.
"""


def _build_artifact(spec: ProductSpec, context: MakeContext) -> Path:
    artifact = (context.workspace / "artifact").absolute()
    if artifact.exists():
        raise RuntimeError("Make artifact workspace must be fresh")
    artifact.mkdir(parents=True)
    _write_json(artifact / "wish.json", context.wish.to_dict())
    attributed_description = attribute_product_description(
        spec.description, spec.inventor_name
    )
    product = {
        "schema_version": 1,
        "kind": "workshop-showcase-prototype",
        "status": "digital-prototype",
        "product_id": context.wish.product_id,
        "slug": spec.slug,
        "title": spec.title,
        "summary": spec.summary,
        "description": attributed_description,
        "lane": spec.lane,
        "inventor": {"id": spec.inventor_id, "name": spec.inventor_name},
        "audience": "grown-ups-14-plus",
        "wish": context.wish.to_dict(),
        "components": [
            "declarative CAD source",
            "real STEP and STL exports",
            "per-part STEP and STL exports",
            "fixed-view render from exact STL",
            "digital Make and Playtest evidence",
        ],
        "limitations": list(spec.limitations),
        "physical_prototype": False,
        "human_playtest": False,
        "released": False,
    }
    if not product["description"].endswith("By %s." % spec.inventor_name):
        raise RuntimeError("product attribution must be the description's exact ending")
    _write_json(artifact / "product.json", product)
    _write_text(artifact / "README.md", _artifact_readme(spec))

    design_source = {
        "schema_version": 1,
        "kind": "showcase-declarative-cad",
        "inventor_id": spec.inventor_id,
        "slug": spec.slug,
        "title": spec.title,
        "lane": spec.lane,
        "design": spec.design,
        "wish_sha256": _sha_bytes(_canonical(context.wish.to_dict())),
        "taste_sha256": context.taste.sha256,
        "blueprint_sha256": context.blueprint.sha256,
        "generator": BUILDER_ID,
    }
    _write_json(artifact / "cad" / "design.json", design_source)
    _write_text(artifact / "cad" / "model.py", MODEL_WRAPPER, executable=True)
    geometry = GEOMETRY_BUILDERS[spec.inventor_id](spec)
    cad_record = _build_cad_files(geometry, artifact / "cad")
    render_record = _render_exact_mesh(
        artifact / "cad" / "product.stl", artifact / "images" / "hero.png", spec.inventor_id
    )
    digital_build = {
        "schema_version": 1,
        "kind": "real-digital-cad-build",
        "generator": {
            "id": BUILDER_ID,
            "path": "tools/build_showcase_products.py",
            "sha256": _sha_file(Path(__file__).resolve()),
        },
        "dependencies": {
            "python": platform.python_version(),
            "cadquery": str(getattr(cq, "__version__", "unavailable")),
            "trimesh": str(trimesh.__version__),
            "numpy": str(np.__version__),
            "pillow": str(getattr(Image, "__version__", "unavailable")),
            "kernel": "OpenCascade via cadquery-ocp",
        },
        "design_source": {
            "path": "cad/design.json",
            "sha256": _sha_file(artifact / "cad" / "design.json"),
        },
        "executable_source": {
            "path": "cad/model.py",
            "sha256": _sha_file(artifact / "cad" / "model.py"),
        },
        "declared_bed_mm": list(BED_MM),
        "product": cad_record["product"],
        "parts": cad_record["parts"],
        "render": render_record,
        "lane_checks": geometry.digital_checks,
        "conclusion": "real CAD and digital topology checks passed",
        "claim_scope": "digital evidence only; no slicing, printing, fit, wear, safety, human delight, or delivery evidence",
    }
    _write_json(artifact / "cad" / "digital-build.json", digital_build)
    if spec.inventor_id == "leo":
        _write_text(artifact / "game" / "RULES.md", COUNTERORBIT_RULES)
        _write_text(
            artifact / "game" / "simulate.py", COUNTERORBIT_SIMULATOR, executable=True
        )
    return artifact.resolve(strict=True)


def showcase_make(context: MakeContext) -> Made:
    """One shared, data-driven Make adapter used by all five profiles."""

    spec = next((item for item in SPECS if item.slug == context.wish.product_id), None)
    if spec is None or spec.lane != context.blueprint.lane:
        raise RuntimeError("showcase Make received an unknown or cross-lane Wish")
    artifact = _build_artifact(spec, context)
    return Made.from_root(
        artifact,
        {
            "title": spec.title,
            "summary": spec.summary,
            "description": attribute_product_description(
                spec.description, spec.inventor_name
            ),
            "lane": spec.lane,
            "inventor": spec.inventor_name,
            "prototype_status": "digital-only",
        },
    )


def _evidence_result(
    evidence_root: Path,
    context: PlaytestContext,
    check_id: str,
    filename: str,
    evidence: Mapping[str, Any],
) -> PlaytestResult:
    return PlaytestResult.create(
        check_id,
        True,
        context.made.artifact_sha256,
        evidence,
        PLAYTEST_ID,
        EVALUATOR_VERSION,
        _sha_bytes(
            _canonical(
                {
                    "evaluator": PLAYTEST_ID,
                    "version": EVALUATOR_VERSION,
                    "check": check_id,
                    "bed_mm": BED_MM,
                    "simulation_games": SIMULATION_GAMES if check_id == "game-simulation" else None,
                    "simulation_seed": SIMULATION_SEED if check_id == "game-simulation" else None,
                }
            )
        ),
        filename,
        _sha_file(evidence_root / filename),
    )


def _run_counterorbit_simulator(artifact: Path) -> Mapping[str, Any]:
    simulator = artifact / "game" / "simulate.py"
    if not simulator.is_file() or not bool(simulator.stat().st_mode & 0o111):
        raise RuntimeError("Counterorbit simulator must exist and be executable")
    completed = subprocess.run(
        [
            sys.executable,
            str(simulator),
            "--games",
            str(SIMULATION_GAMES),
            "--seed",
            str(SIMULATION_SEED),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    evidence = json.loads(completed.stdout)
    required_styles = {"optimizing", "social", "exploratory", "adversarial"}
    if (
        evidence.get("evidence_class") != "ai-simulation"
        or evidence.get("executable") is not True
        or evidence.get("completed_games", 0) < 1_000
        or evidence.get("terminated_games") != evidence.get("completed_games")
        or evidence.get("nonterminating_games") != 0
        or set(evidence.get("player_styles", ())) != required_styles
        or evidence.get("max_turns_observed", 99) > 10
    ):
        raise RuntimeError("Counterorbit simulation did not satisfy its digital evidence contract")
    return evidence


def showcase_playtest(context: PlaytestContext):
    """Seal real digital evidence, then wait for evidence software cannot make."""

    spec = next((item for item in SPECS if item.slug == context.wish.product_id), None)
    if spec is None:
        raise RuntimeError("showcase Playtest received an unknown Wish")
    evidence_root = context.workspace.absolute()
    evidence_root.mkdir(parents=True, exist_ok=False)
    artifact = context.made.artifact_root
    digital_build = json.loads((artifact / "cad" / "digital-build.json").read_text())

    evidence_records: list[tuple[str, str, Mapping[str, Any]]] = []
    geometry = {
        "schema_version": 1,
        "check": "digital-geometry",
        "passed": True,
        "artifact_sha256": context.made.artifact_sha256,
        "step_reimported": bool(digital_build["product"]["step"]["reimported"]),
        "step_solid_count": digital_build["product"]["step"]["solid_count"],
        "stl_watertight": bool(digital_build["product"]["stl"]["watertight"]),
        "stl_winding_consistent": bool(
            digital_build["product"]["stl"]["winding_consistent"]
        ),
        "part_count": len(digital_build["parts"]),
        "all_parts_step_reimported": all(
            item["step"]["reimported"] for item in digital_build["parts"].values()
        ),
        "all_parts_watertight": all(
            item["stl"]["watertight"] for item in digital_build["parts"].values()
        ),
        "claim_scope": "OpenCascade/mesh digital checks; not physical proof",
    }
    _write_json(evidence_root / "digital-geometry.json", geometry)
    evidence_records.append(("digital-geometry", "digital-geometry.json", geometry))

    printability = {
        "schema_version": 1,
        "check": "digital-printability",
        "passed": True,
        "artifact_sha256": context.made.artifact_sha256,
        "declared_bed_mm": list(BED_MM),
        "all_exported_parts_inside_bed": all(
            item["stl"]["inside_declared_bed"] for item in digital_build["parts"].values()
        ),
        "all_exported_parts_watertight": all(
            item["stl"]["watertight"] for item in digital_build["parts"].values()
        ),
        "locked_slicer_profile_run": False,
        "physical_print": False,
        "fit_test": False,
        "claim_scope": "basic digital mesh/envelope screening only; canonical print-test remains unresolved",
    }
    _write_json(evidence_root / "digital-printability.json", printability)
    evidence_records.append(
        ("digital-printability", "digital-printability.json", printability)
    )

    lane = {
        "schema_version": 1,
        "check": "digital-lane-model",
        "passed": True,
        "artifact_sha256": context.made.artifact_sha256,
        "lane": spec.lane,
        "checks": digital_build["lane_checks"],
        "claim_scope": "computational/declarative review only; lane-specific physical and independent review remains unresolved",
    }
    _write_json(evidence_root / "digital-lane.json", lane)
    evidence_records.append(("digital-lane-model", "digital-lane.json", lane))

    taste = {
        "schema_version": 1,
        "check": "wish-taste-trace",
        "passed": True,
        "artifact_sha256": context.made.artifact_sha256,
        "wish_sha256": _sha_bytes(_canonical(context.wish.to_dict())),
        "taste_sha256": context.taste.sha256,
        "blueprint_sha256": context.blueprint.sha256,
        "wish_features": list(spec.design["wish_features"]),
        "download_bar_answer": "Wish details alter geometry, topology, interaction, or scientific framing; they are not a nameplate.",
        "claim_scope": "traceability record; independent distinctiveness/delight review remains unresolved",
    }
    _write_json(evidence_root / "wish-taste-trace.json", taste)
    evidence_records.append(("wish-taste-trace", "wish-taste-trace.json", taste))

    if spec.inventor_id == "leo":
        simulation = dict(_run_counterorbit_simulator(artifact))
        simulation["artifact_sha256"] = context.made.artifact_sha256
        simulation["simulator_path"] = "game/simulate.py"
        simulation["simulator_sha256"] = _sha_file(artifact / "game" / "simulate.py")
        _write_json(evidence_root / "game-simulation.json", simulation)
        evidence_records.append(("game-simulation", "game-simulation.json", simulation))

    unresolved = [
        capability
        for capability in context.blueprint.required_capabilities("playtest")
        if not (spec.inventor_id == "leo" and capability == "game-simulation")
    ]
    _write_json(
        evidence_root / "evidence-index.json",
        {
            "schema_version": 1,
            "kind": "showcase-digital-playtest-index",
            "artifact_sha256": context.made.artifact_sha256,
            "evaluator": PLAYTEST_ID,
            "evaluator_version": EVALUATOR_VERSION,
            "validated_checks": [
                {"playtest_id": item[0], "evidence_ref": item[1]} for item in evidence_records
            ],
            "unresolved_canonical_capabilities": unresolved,
            "status": "waiting-at-playtest",
        },
    )
    evidence_manifest = build_artifact_manifest(
        evidence_root.resolve(strict=True), created_at="content-addressed"
    )
    results = tuple(
        _evidence_result(evidence_root, context, check_id, filename, evidence)
        for check_id, filename, evidence in evidence_records
    )
    # Constructing the typed aggregate verifies every evidence hash against the
    # exact Made artifact before this adapter truthfully waits.
    Playtest(context.made.artifact_manifest, results, evidence_manifest=evidence_manifest)

    needs = []
    for capability in unresolved:
        external = capability in {"human-playtest", "human-replay", "physical-prototype"}
        needs.append(
            Need(
                "playtest",
                capability,
                (
                    "This exact digital prototype still needs independent real-world evidence."
                    if external
                    else "The current digital checks do not establish the Workshop's full %s gate."
                    % capability
                ),
                (
                    "Print and test the exact artifact with independent people; bind observations to its SHA-256."
                    if external
                    else "Run the canonical %s capability with its required physical, slicer, or independent evidence."
                    % capability
                ),
            )
        )
    raise WaitingFor(*needs)


def _bundle_readme(spec: ProductSpec, run: Mapping[str, Any]) -> str:
    needs = "\n".join(
        "- `%s` — %s" % (item["capability"], item["reason"])
        for item in run["needs"]
    )
    return f"""\
# {spec.title}

![Exact-geometry render of {spec.title}](artifact/images/hero.png)

{spec.description}

## Workshop result

- Inventor profile: [{spec.inventor_name}](../../README.md)
- Lane: `{spec.lane}`
- Extension level: `{spec.extension_level}`
- Configured Playtest rounds: `{spec.playtest_rounds}`
- Actual stop: **Playtest / waiting**, round {run['round']}
- Exact artifact: `{run['artifact_sha256']}`

The shared Workshop produced a real digital prototype and stopped before
Instructions or Deliver. That is intentional: software cannot manufacture
physical evidence or human delight.

## Still needed

{needs}

## Inspect it

- [`artifact/product.json`](artifact/product.json) — product metadata and honest claims
- [`artifact/cad/design.json`](artifact/cad/design.json) — declarative CAD source
- [`artifact/cad/model.py`](artifact/cad/model.py) — executable rebuild entry point
- [`artifact/cad/product.step`](artifact/cad/product.step) — real OpenCascade STEP
- [`artifact/cad/product.stl`](artifact/cad/product.stl) — exact printable mesh candidate
- [`artifact/cad/digital-build.json`](artifact/cad/digital-build.json) — geometry checks and hashes
- [`evidence/evidence-index.json`](evidence/evidence-index.json) — sealed digital Playtest index
- [`workshop-run.json`](workshop-run.json) — canonical profile/run receipt

No file in this bundle claims a physical print, human Playtest, released product,
box instructions, shipment, or delivery.
"""


def _workshop_for(spec: ProductSpec, profile: Any, runtime_root: Path):
    if spec.extension_level == "taste-only":
        return profile.build_workshop(
            tools=WorkshopTools(make=showcase_make, playtest=showcase_playtest),
            runtime_root=runtime_root,
            max_rounds=spec.playtest_rounds,
        )
    if spec.extension_level == "custom-make":
        return profile.build_workshop(
            tools=WorkshopTools(playtest=showcase_playtest),
            make=showcase_make,
            runtime_root=runtime_root,
            max_rounds=spec.playtest_rounds,
        )
    if spec.extension_level == "custom-playtest":
        return profile.build_workshop(
            tools=WorkshopTools(),
            make=showcase_make,
            playtest=showcase_playtest,
            runtime_root=runtime_root,
            max_rounds=spec.playtest_rounds,
        )
    raise RuntimeError("unknown extension level")


def _build_one(spec: ProductSpec, *, force: bool = False) -> Mapping[str, Any]:
    final_root = REPO_ROOT / "inventors" / spec.inventor_id / "toys" / spec.slug
    if final_root.exists() and not force:
        raise RuntimeError("bundle already exists (use --force for this exact generated target): %s" % final_root)
    with tempfile.TemporaryDirectory(prefix="workshop-showcase-%s-" % spec.inventor_id) as temp:
        temp_root = Path(temp).resolve()
        profile = _load_profile(spec.inventor_id)
        wish = profile.create_wish(spec.slug, spec.objective)
        workshop = _workshop_for(spec, profile, temp_root / "runtime")
        if workshop.customization_level != spec.extension_level:
            raise RuntimeError(
                "%s profile resolved %s, expected %s"
                % (spec.inventor_name, workshop.customization_level, spec.extension_level)
            )
        run = workshop.run(wish, playtest_rounds=spec.playtest_rounds)
        run_record = run.to_dict()
        if run.status != "waiting" or run.job != "playtest" or run.round != 1:
            raise RuntimeError("showcase must truthfully wait at first Playtest")
        if run.instructions_sha256 is not None or run.delivery is not None:
            raise RuntimeError("showcase must not fabricate Instructions or Delivery")

        round_root = temp_root / "runtime" / "runs" / spec.slug / "round-001"
        artifact_source = round_root / "make" / "artifact"
        evidence_source = round_root / "playtest"
        if not artifact_source.is_dir() or not evidence_source.is_dir():
            raise RuntimeError("Workshop adapters did not leave auditable workspaces")
        stage = temp_root / "bundle"
        shutil.copytree(artifact_source, stage / "artifact")
        shutil.copytree(evidence_source, stage / "evidence")
        artifact_manifest = build_artifact_manifest(
            (stage / "artifact").resolve(strict=True), created_at="content-addressed"
        )
        evidence_manifest = build_artifact_manifest(
            (stage / "evidence").resolve(strict=True), created_at="content-addressed"
        )
        if artifact_manifest.artifact_sha256 != run.artifact_sha256:
            raise RuntimeError("copied product bytes no longer match the Workshop run")
        _write_json(stage / "artifact-manifest.json", artifact_manifest.to_dict())
        _write_json(stage / "evidence-manifest.json", evidence_manifest.to_dict())
        receipt = {
            "schema_version": 1,
            "kind": "showcase-workshop-run",
            "inventor": {
                "id": spec.inventor_id,
                "name": spec.inventor_name,
                "profile": "inventors/%s/profile.py" % spec.inventor_id,
                "extension_level": workshop.customization_level,
            },
            "shared_adapters": {
                "make": BUILDER_ID,
                "playtest": PLAYTEST_ID,
                "builder_path": "tools/build_showcase_products.py",
                "builder_sha256": _sha_file(Path(__file__).resolve()),
            },
            "wish": wish.to_dict(),
            "taste_sha256": workshop.taste.sha256,
            "blueprint_sha256": workshop.blueprint.sha256,
            "run": run_record,
            "artifact_sha256": artifact_manifest.artifact_sha256,
            "evidence_sha256": evidence_manifest.artifact_sha256,
            "assertions": {
                "real_step_and_stl": True,
                "step_reimported": True,
                "exact_geometry_render": True,
                "typed_workshop_run": True,
                "typed_evidence_contract_validated": True,
                "physical_prototype": False,
                "human_playtest": False,
                "instructions_created": False,
                "delivered": False,
            },
        }
        _write_json(stage / "workshop-run.json", receipt)
        _write_text(stage / "README.md", _bundle_readme(spec, run_record))
        _verify_bundle(stage, spec)
        final_root.parent.mkdir(parents=True, exist_ok=True)
        if final_root.exists():
            # --force is narrowly scoped to the exact generated bundle selected
            # above; no broad path or unresolved glob can reach this branch.
            shutil.rmtree(final_root)
        shutil.copytree(stage, final_root)
        _verify_bundle(final_root, spec)
        _remove_obsolete_generated_bundle(spec)
    return {
        "inventor": spec.inventor_name,
        "slug": spec.slug,
        "path": str(final_root.relative_to(REPO_ROOT)),
        "status": "waiting",
        "job": "playtest",
        "artifact_sha256": receipt["artifact_sha256"],
        "evidence_sha256": receipt["evidence_sha256"],
        "extension_level": spec.extension_level,
    }


def _remove_obsolete_generated_bundle(spec: ProductSpec) -> None:
    """Remove only this tool's superseded pre-``toys/`` generated bundle."""

    legacy = REPO_ROOT / "inventors" / spec.inventor_id / "products" / spec.slug
    if not legacy.exists():
        return
    receipt_path = legacy / "workshop-run.json"
    product_path = legacy / "artifact" / "product.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        product = json.loads(product_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError("refusing to remove an unrecognized legacy bundle: %s" % legacy) from exc
    if (
        receipt.get("kind") != "showcase-workshop-run"
        or receipt.get("inventor", {}).get("id") != spec.inventor_id
        or product.get("slug") != spec.slug
    ):
        raise RuntimeError("refusing to remove a legacy bundle not owned by this generator: %s" % legacy)
    shutil.rmtree(legacy)
    try:
        legacy.parent.rmdir()
    except OSError:
        pass


def _manifest_from_dict(root: Path, record: Mapping[str, Any]):
    return build_artifact_manifest(root, created_at=record["created_at"])


def _verify_bundle(bundle: Path, spec: ProductSpec) -> Mapping[str, Any]:
    product = json.loads((bundle / "artifact" / "product.json").read_text(encoding="utf-8"))
    receipt = json.loads((bundle / "workshop-run.json").read_text(encoding="utf-8"))
    stored_artifact = json.loads((bundle / "artifact-manifest.json").read_text(encoding="utf-8"))
    stored_evidence = json.loads((bundle / "evidence-manifest.json").read_text(encoding="utf-8"))
    if product["inventor"] != {"id": spec.inventor_id, "name": spec.inventor_name}:
        raise RuntimeError("product inventor metadata mismatch")
    if not product["description"].endswith("By %s." % spec.inventor_name):
        raise RuntimeError("description attribution is not its exact ending")
    if product["released"] or product["physical_prototype"] or product["human_playtest"]:
        raise RuntimeError("digital showcase contains an unsupported production claim")
    if receipt["run"]["status"] != "waiting" or receipt["run"]["job"] != "playtest":
        raise RuntimeError("receipt does not stop at Playtest")
    if receipt["inventor"]["extension_level"] != spec.extension_level:
        raise RuntimeError("receipt loses the canonical profile extension level")
    if receipt["run"]["playtest_rounds"] != spec.playtest_rounds:
        raise RuntimeError("receipt loses configured Playtest rounds")
    current_artifact = _manifest_from_dict((bundle / "artifact").resolve(), stored_artifact)
    current_evidence = _manifest_from_dict((bundle / "evidence").resolve(), stored_evidence)
    if current_artifact.to_dict() != stored_artifact:
        raise RuntimeError("artifact manifest no longer matches copied bytes")
    if current_evidence.to_dict() != stored_evidence:
        raise RuntimeError("evidence manifest no longer matches copied bytes")
    if receipt["artifact_sha256"] != current_artifact.artifact_sha256:
        raise RuntimeError("Workshop receipt artifact identity mismatch")
    if receipt["evidence_sha256"] != current_evidence.artifact_sha256:
        raise RuntimeError("Workshop receipt evidence identity mismatch")
    build = json.loads((bundle / "artifact" / "cad" / "digital-build.json").read_text())
    current_product_cad = _validate_cad_pair(
        bundle / "artifact" / "cad" / "product.step",
        bundle / "artifact" / "cad" / "product.stl",
    )
    if current_product_cad != build["product"]:
        raise RuntimeError("independent CAD revalidation disagrees with digital-build.json")
    for part_name, stored_part in sorted(build["parts"].items()):
        current_part = _validate_cad_pair(
            bundle / "artifact" / "cad" / "parts" / (part_name + ".step"),
            bundle / "artifact" / "cad" / "parts" / (part_name + ".stl"),
        )
        if current_part != stored_part:
            raise RuntimeError("independent CAD revalidation disagrees for part %s" % part_name)
    if build["product"]["stl"]["sha256"] != _sha_file(bundle / "artifact" / "cad" / "product.stl"):
        raise RuntimeError("digital build points at different product STL bytes")
    current_builder_sha256 = _sha_file(Path(__file__).resolve())
    if (
        build["generator"]["sha256"] != current_builder_sha256
        or receipt["shared_adapters"]["builder_sha256"] != current_builder_sha256
    ):
        raise RuntimeError("bundle was built by different shared Workshop source bytes")
    image = Image.open(bundle / "artifact" / "images" / "hero.png")
    image.verify()
    if build["render"]["input_sha256"] != build["product"]["stl"]["sha256"]:
        raise RuntimeError("hero is not bound to the exact product STL")
    index = json.loads((bundle / "evidence" / "evidence-index.json").read_text())
    if index["artifact_sha256"] != current_artifact.artifact_sha256:
        raise RuntimeError("Playtest evidence points at different artifact bytes")
    if spec.inventor_id == "leo":
        simulation = json.loads((bundle / "evidence" / "game-simulation.json").read_text())
        if simulation["completed_games"] < 1_000 or simulation["terminated_games"] != simulation["completed_games"]:
            raise RuntimeError("Leo simulation evidence is incomplete")
        if simulation["executable"] is not True or len(simulation["matchups"]) != 16:
            raise RuntimeError("Leo simulation lacks executable all-style matchups")
        if "game-simulation" in index["unresolved_canonical_capabilities"]:
            raise RuntimeError("executed Leo simulation was incorrectly left unresolved")
        if "human-replay" not in index["unresolved_canonical_capabilities"]:
            raise RuntimeError("Leo must still wait for independent human replay")
        rerun = _run_counterorbit_simulator(bundle / "artifact")
        if any(simulation.get(key) != value for key, value in rerun.items()):
            raise RuntimeError("Leo's checked-in seeded evidence does not match an executable rerun")
    return {
        "inventor": spec.inventor_name,
        "path": str(bundle),
        "artifact_sha256": current_artifact.artifact_sha256,
        "evidence_sha256": current_evidence.artifact_sha256,
        "verified": True,
    }


def _selected_specs(values: Sequence[str]) -> tuple[ProductSpec, ...]:
    if not values:
        return SPECS
    wanted = {value.casefold() for value in values}
    selected = tuple(
        item
        for item in SPECS
        if item.inventor_id in wanted or item.slug.casefold() in wanted
    )
    missing = wanted - {
        value
        for item in selected
        for value in (item.inventor_id, item.slug.casefold())
    }
    if missing:
        raise SystemExit("unknown showcase selection: %s" % ", ".join(sorted(missing)))
    return selected


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", action="append", default=[], help="inventor id or product slug")
    parser.add_argument("--force", action="store_true", help="replace only the selected generated bundles")
    parser.add_argument("--verify", action="store_true", help="verify existing bundles without rebuilding")
    args = parser.parse_args(argv)
    records = []
    for spec in _selected_specs(args.only):
        bundle = REPO_ROOT / "inventors" / spec.inventor_id / "toys" / spec.slug
        records.append(_verify_bundle(bundle, spec) if args.verify else _build_one(spec, force=args.force))
        print("%s %s" % ("verified" if args.verify else "built", spec.inventor_name), flush=True)
    print(json.dumps({"schema_version": 1, "toys": records}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
