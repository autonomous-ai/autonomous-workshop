#!/usr/bin/env python3
"""Build five honest, AI-Playtested Workshop showcase products.

This is a repo-owned demonstration adapter, not production evidence.  It uses
real CadQuery B-reps and STL meshes, renders the exported mesh, seals the exact
bytes through the Workshop contracts, and has independent AI-player roles
simulate each product. Physical production and customer Reviews happen later.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import re
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

from workshop.artifacts.core import build_artifact_manifest
from workshop.product import attribute_product_description
from workshop.instructions.service import DefaultInstructions
from workshop.make.contracts import Made, MakeContext
from workshop.outcomes import Need, WaitingFor
from workshop.playtest.contracts import PlaytestContext, Playtested
from workshop.playtest.evidence import PlaytestResult
from workshop.playtest.service import Playtest
from workshop.workflow.engine import WorkshopTools
from workshop.integrations.shop import ShopDoor, ShopInstructionsWriter
from workshop.runtime.store import InventorStore
from workshop.product.blueprints import ToyBlueprint


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
    factory_brief: str
    story: Mapping[str, Any]
    art_direction: Mapping[str, Any]
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
        (
            "A late-night design review, cast as a game you already know. This is "
            "ordinary English checkers translated into the Workshop's architecture, "
            "not a new ruleset and not a decorative checker pattern. Preserve the "
            "exact 132 mm board, unmistakable 8×8 grid, twelve five-ring pieces, "
            "twelve five-spoke pieces, and five raised edge thresholds. The two "
            "armies must remain different by touch and silhouette. Palette: Midnight "
            "black #12151D with warm brass-like gold #D6A449; architectural, "
            "restrained, high contrast. Film in this order: Full three-quarter hero "
            "with all 24 pieces and all five threshold bars visible. Then prove the "
            "8×8 grid from true overhead; compare ring and spoke pieces in macro; "
            "skim the five thresholds from a low edge; move from the exact opening "
            "position into a credible midgame; finish on a clean board-plus-24-piece "
            "inventory. Use dark after-hours studio light with warm brass highlights, "
            "never an ivory wash. Do not randomize the opening setup, invent labels, "
            "add components, alter the known rules, or call digital checks a physical "
            "print or a human playtest."
        ),
        {
            "core_promise": "Familiar English checkers, recast as an architectural portrait of the Workshop’s five jobs without changing a rule.",
            "geometry_and_meaning": "A 132 × 132 × 10 mm assembled set with an 8×8 grid, 14.5 mm cells, twelve five-ring pieces and twelve five-spoke pieces. The two tactile silhouettes identify the sides. Five raised threshold bars at the board edge represent Wish, Make, Playtest, Instructions, and Deliver.",
            "interaction_story": "The setup and play remain ordinary checkers; the personalization lives in the board, piece language, tactility, and table presence.",
            "attribution": "By Alice.",
        },
        {
            "palette": "Midnight black #12151D with warm brass-like gold #D6A449; architectural, restrained, high contrast.",
            "must_show_media": [
                "Full three-quarter hero with all 24 pieces and all five threshold bars visible.",
                "True top-down view proving the complete 8×8 grid.",
                "Macro comparison of five-ring versus five-spoke geometry.",
                "Low edge view showing the five raised Workshop thresholds.",
                "Opening-position-to-midgame transition using familiar checkers movement.",
                "Clean inventory view: board, 12 ring pieces, 12 spoke pieces.",
            ],
            "avoid_limitations": "Do not invent new rules, labels, logos, or extra components. Digital checks establish geometry, topology, known-rule compatibility, and bed fit—not physical print quality or customer delight.",
        },
        {
            "kind": "classic-checkers-edition",
            "printed_piece_count": 25,
            "known_rules": "English draughts/checkers; this edition does not alter play",
            "board_mm": [132.0, 132.0, 5.5],
            "assembled_extents_mm": [132.0, 132.0, 10.0],
            "grid": [8, 8],
            "cell_mm": 14.5,
            "piece_count": {"five-ring": 12, "five-spoke": 12},
            "thresholds": ["Wish", "Make", "Playtest", "Instructions", "Deliver"],
            "wish_features": [
                "five raised threshold markers represent Wish, Make, Playtest, Instructions, Deliver",
                "five-ring and five-spoke motifs distinguish both sides by touch and silhouette",
                "black and warm-gold architectural composition",
            ],
        },
        (
            "AI players checked the known rules and role readability; customer experience will arrive later as Reviews.",
            "The exact physical set is produced and checked during Deliver, not Playtest.",
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
        (
            "A continuous turn becomes one deliberate jump. The visible comet pin is "
            "the cause, the six-slot orbit is the effect, and the pause between them "
            "is the delight. Preserve the exact 94 × 68 × 20 mm exposed Geneva "
            "mechanism: base, two replaceable axles, cratered drive wheel with hand "
            "knob and comet pin, and the six-slot orbit wheel. One complete drive-wheel "
            "revolution advances exactly one 60° step; six drive revolutions complete "
            "one orbit. Never say one revolution makes six jumps. Palette: Charcoal "
            "#1C1F26 with ember/coral #EE5F3E; exposed, mechanical, dramatic. Film in "
            "this order: Full three-quarter hero revealing both wheels and their "
            "relationship. Move overhead to all six slots and stations; cut to a macro "
            "of the pin approaching, entering, indexing 60°, releasing, and locking; "
            "show the pause; then show six uninterrupted revolutions completing the "
            "cycle; finish with the exact parts inventory. Use a hard cool rim with a "
            "warm highlight only on the comet pin. No gears, motors, electronics, "
            "automatic motion, extra knobs, or claims of proven hand feel, wear life, "
            "or physical safety."
        ),
        {
            "core_promise": "A hand-cranked desk machine where continuous motion becomes six deliberate orbital jumps—and the exposed mechanism is the spectacle.",
            "geometry_and_meaning": "The assembly is 94 × 68 × 20 mm. A cratered 36 mm drive wheel carries the visible comet pin and hand knob; it engages a roughly 46 mm six-slot Geneva wheel. The 4.3 mm pin enters 5.0 mm slots with 0.7 mm nominal pin-slot clearance. Each crank revolution advances the orbit by 60°.",
            "interaction_story": "The user turns the drive wheel continuously, watches the comet pin enter a radial slot, pushes the orbit one station, then sees it pause before the next encounter.",
            "attribution": "By Bob.",
        },
        {
            "palette": "Charcoal #1C1F26 with ember/coral #EE5F3E; exposed, mechanical, dramatic.",
            "must_show_media": [
                "Full three-quarter hero revealing both wheels and their relationship.",
                "Overhead view showing all six radial slots and station markers.",
                "Macro of the comet pin approaching and entering one slot.",
                "Slow-motion single 60° index from engagement through release.",
                "One uninterrupted six-jump/full-cycle sequence.",
                "Parts view: base, axles, comet drive, six-slot orbit.",
            ],
            "avoid_limitations": "Do not depict gears, electronics, automatic motion, or a decorative plaque. The evidence covers dimensional and kinematic intent only; physical fit, wear, cycle life, pinch behavior, and satisfying hand feel still require Deliver QA.",
        },
        {
            "kind": "six-step-geneva-machine",
            "printed_piece_count": 5,
            "base_mm": [94.0, 68.0, 5.0],
            "assembled_extents_mm": [94.0, 68.0, 20.0],
            "geneva_slots": 6,
            "step_degrees": 60.0,
            "drive_radius_mm": 18.0,
            "geneva_radius_mm": 23.0,
            "drive_pin_diameter_mm": 4.3,
            "slot_width_mm": 5.0,
            "nominal_pin_slot_clearance_mm": 0.7,
            "nominal_clearance_per_side_mm": 0.35,
            "wish_features": [
                "continuous crank becomes six discrete orbital jumps",
                "comet pin is the visible cause of motion",
                "six stations form the midnight orbit",
            ],
        },
        (
            "AI agents simulate kinematics, tolerance, wear, misuse, and pinch risks; the shipped print still receives hands-on QA in Deliver.",
            "Customer observations begin as Reviews only after delivery.",
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
        (
            "Three machines. One watch. Turn the named homelab nodes Comet, Moss, and "
            "Void into one small orbital engine room watched by a lone night-shift "
            "operator—not three generic server blocks on a white desk. Preserve the "
            "exact 108 × 72 × 43.6 mm deck, three circuit trenches, Comet's six fins, "
            "Moss's paired coolant pipes, Void's vertical halo, and exactly one 16 mm "
            "operator. Palette: Deep navy #141C2A with industrial teal #5EC5BF; "
            "cinematic and technical, never cute. Film in this order: Operator-eye "
            "hero framing all three nodes as one room. Begin low behind the operator; "
            "orbit slowly past all six Comet fins, Moss's paired pipes, Void's halo, "
            "and the trenches that join the city; rise overhead to prove the one-deck "
            "layout; finish with five separate production pieces. Light it like an "
            "unoccupied engine room at 2 a.m.—deep navy shadows, teal structure, a "
            "restrained warm accent on the operator, sharp rim light and real negative "
            "space. Do not add rack labels, cables, screens, glow, electronics, a "
            "second figure, personal biography, or likeness details not present in "
            "the Wish."
        ),
        {
            "core_promise": "A three-node homelab transformed into a tiny orbital engine room whose identities are visible in geometry, watched by one lone operator.",
            "geometry_and_meaning": "The assembled world is 108 × 72 × 43.6 mm on a rounded engine deck crossed by three circuit trenches. Comet is a 34 mm tower with six swept side fins; Moss is a 35 mm structure with paired exposed coolant pipes; Void rises to 37.7 mm beneath a vertical orbital halo. A single 16 mm operator faces all three and establishes scale.",
            "interaction_story": "The trenches make the nodes read as one connected machine city; the operator turns the arrangement into a night-shift scene rather than three unrelated server blocks.",
            "attribution": "By Eve.",
        },
        {
            "palette": "Deep navy #141C2A with industrial teal #5EC5BF; cinematic and technical, never cute.",
            "must_show_media": [
                "Operator-eye hero framing all three nodes as one room.",
                "Comet detail showing all six fins.",
                "Moss detail showing the paired coolant pipes.",
                "Void silhouette centered on its vertical halo.",
                "Overhead view showing the connecting circuit trenches.",
                "Slow orbit around the complete 108 mm deck, with the operator always legible.",
            ],
            "avoid_limitations": "No nameplates, generic rack labels, added cables, invented personal history, or private likeness details. The only personalization source was the Wish text; physical detail survival and handling durability remain Deliver checks.",
        },
        {
            "kind": "personalized-homelab-diorama",
            "printed_piece_count": 5,
            "deck_mm": [108.0, 72.0, 5.0],
            "assembled_extents_mm": [108.0, 72.0, 43.6],
            "nodes": ["Comet", "Moss", "Void"],
            "circuit_trench_count": 3,
            "operator_height_mm": 16.0,
            "node_signatures": {
                "Comet": {"height_mm": 34.0, "feature": "six swept side fins"},
                "Moss": {"height_mm": 35.0, "feature": "paired exposed coolant pipes"},
                "Void": {"height_mm": 37.7, "feature": "vertical orbital halo"},
            },
            "reference_scope": "Wish text only; no private likeness assets were used",
            "wish_features": [
                "three node identities are geometry, not labels",
                "circuit trenches connect the rack city",
                "one operator establishes scale and night-shift story",
            ],
        },
        (
            "AI agents review the named-node mapping against the provided references; the customer can correct likeness later through Reviews.",
            "Fine details and handling durability are checked on the produced object during Deliver.",
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
        "Rotate the tide arm through Sun–Earth–Moon alignment and quadrature to compare why spring and neap tide ranges differ. It is a qualitative teaching model, not a Montauk tide forecast. By Ivy.",
        "taste-only",
        3,
        (
            "The tide begins as geometry in the sky. Present this only as a qualitative "
            "spring–neap alignment comparison, never as a Montauk tide forecast and "
            "never as a solar-system model. Copy rule: never use predict, prediction, "
            "or forecast as a product capability, heading, label, or call to action; "
            "say compare spring and neap alignment instead. Preserve "
            "the complete 104 mm circular phase base, four raised stops at 0°, 90°, "
            "180°, and 270°, the full two-lobed arm, center post, Earth hub, Moon "
            "marker, and Sun arrow. Exact material story: deep-ocean #122630 base; "
            "instrument-gold #EDC250 center post, tide arm, and Sun arrow; sea-glass "
            "teal #2E7F8F Earth hub; warm ivory #D8D2C4 Moon marker. Film in this order: "
            "Near-top-down hero showing the entire circular base, all four phase "
            "markers, full two-lobed arm, Earth, Moon, and Sun. Then establish the "
            "thin layered disc from low three-quarter; move through 0° → 90° → 180° → "
            "270° with a clean stop at each phase; compare aligned/opposed with "
            "quadrature side by side; show all six printed pieces clearly—the phase "
            "base, center post, tide arm, Earth hub, Moon marker, and Sun arrow; finish on "
            "the full circular silhouette. Use dark coastal light, ocean navy, "
            "instrument brass, and sea-glass teal. Never crop the base into a post, "
            "turn the markers into mushrooms or planets, omit an assembly image, or "
            "claim scale accuracy, predictive ability, physical detent feel, or human proof."
        ),
        {
            "core_promise": "Hold the spring–neap relationship in your hands, then rotate the model to compare how alignment changes the pattern.",
            "geometry_and_meaning": "This must read first as a 104 mm circular phase-base instrument, not a post or cylinder. The full assembly is approximately 104.5 × 104 × 31.2 mm. Four raised phase markers sit around the disc at 0°, 90°, 180°, and 270°. A center post carries a 96 × 16 mm two-lobed tide arm spanning nearly the base diameter, with a 16 mm Earth hub at center, a 19 mm-high Moon marker on the arm, and a 21 mm Sun arrow near the rim.",
            "interaction_story": "Aligned and opposed positions represent spring-tide configurations; the two quadrature positions represent neap-tide configurations. The tactile arm makes side-by-side comparison the interaction.",
            "attribution": "By Ivy.",
        },
        {
            "palette": "Deep-ocean #122630 base; instrument-gold #EDC250 center post, arm, and Sun; sea-glass teal #2E7F8F Earth; warm ivory #D8D2C4 Moon.",
            "must_show_media": [
                "Near-top-down hero showing the entire circular base, all four phase markers, full two-lobed arm, Earth, Moon, and Sun.",
                "Low three-quarter view establishing the disc’s thin base and layered assembly.",
                "Macro of the Earth hub, center post, and tide arm.",
                "Rotation through 0° → 90° → 180° → 270°, stopping clearly at each phase.",
                "Side-by-side aligned/opposed versus quadrature configurations.",
                "Final overhead tableau with the 104 mm circular silhouette unmistakable.",
            ],
            "avoid_limitations": "Never render it as a generic pedestal, narrow cylinder, solar-system model, or literal Montauk tide predictor. It is qualitative, not to scale and not predictive; physical detent feel and hands-on comprehension remain unproven until Deliver and Reviews.",
        },
        {
            "kind": "qualitative-tide-orrery",
            "printed_piece_count": 6,
            "base_diameter_mm": 104.0,
            "assembled_extents_mm": [104.5, 104.0, 31.2],
            "phase_positions_degrees": [0, 90, 180, 270],
            "tide_arm_mm": [96.0, 16.0],
            "earth_hub_diameter_mm": 16.0,
            "moon_marker_height_mm": 19.0,
            "sun_arrow_length_mm": 21.0,
            "relationship": {
                "aligned_or_opposed": "spring-tide configuration",
                "quadrature": "neap-tide configuration",
            },
            "scope": "qualitative alignment model; not to scale and not predictive",
            "source": "https://oceanservice.noaa.gov/education/tutorial_tides/tides06_variations.html",
            "wish_features": [
                "Montauk-specific request is framed as a qualitative alignment comparison",
                "four detents embody the spring-neap cycle",
                "two-lobed tide arm makes the alignment comparison tactile",
            ],
        },
        (
            "The model is qualitative and not a tide forecast; AI science players keep that simplification explicit.",
            "Detent feel and hands-on quality are checked during Deliver, then customer comprehension may arrive through Reviews.",
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
        (
            "Place a signal. Turn the world. See whether your line survives. This is "
            "an original two-player alignment duel whose orbit changes adjacency; it "
            "must never look like a static pegboard or a reskinned classic. Preserve "
            "the exact roughly 104 mm assembly: fixed five-station core with five inner "
            "wells, rotating outer ring with ten wells, five ring signals, and five "
            "spoke signals. Palette: Near-black violet #181726 with electric amethyst "
            "#BC5DE8; mysterious and high-contrast. Film in this order: True top-down "
            "empty-board view clearly separating five inner and ten outer wells. Then "
            "show the exact ten-stone inventory; place one signal; rotate the shared "
            "orbit exactly one notch; hold a before/after split so changed framing is "
            "obvious; resolve a three-signal wedge across core and orbit; finish with a "
            "short complete-turn montage. Use tense overhead pools of light, an "
            "amethyst ring side and cool-silver spoke side, with the rotating boundary "
            "always legible. Copy rule: call this twelve printed pieces—one core, one "
            "orbit, five ring signals, and five spoke signals—never four parts; the "
            "rulebook is not a printed game piece. Describe the designed clearance as "
            "intended and never claim smooth rotation, no slop, or proven physical fit "
            "before Reviews. Do not show random pegs, a decorative or nonmoving orbit, "
            "extra wells, extra stones, or any 'perfectly balanced' claim: 1,200 AI "
            "simulations terminated, but the observed first-seat rate was 81.58% and "
            "fun and balance remain unresolved until human Reviews."
        ),
        {
            "core_promise": "An original two-player alignment duel where every placement is followed by a shared orbit rotation, so adjacency—and both plans—changes every turn.",
            "geometry_and_meaning": "A roughly 104 mm circular assembly with a fixed 70 mm core containing five inner wells and a rotating outer ring containing ten wells. Each player has five tactile signals: five ring stones versus five spoke stones, each about 7.4 mm wide. The five inner stations represent the Workshop’s five jobs.",
            "interaction_story": "Place one signal in any empty inner or outer well, rotate the outer orbit exactly one notch clockwise or counterclockwise, then check for a wedge: one occupied inner station plus its two currently framed outer wells. A wedge wins; otherwise the game resolves after all ten signals are placed.",
            "attribution": "By Leo.",
        },
        {
            "palette": "Near-black violet #181726 with electric amethyst #BC5DE8; mysterious and high-contrast.",
            "must_show_media": [
                "True top-down empty-board view clearly separating five inner and ten outer wells.",
                "Inventory shot with five ring and five spoke signals.",
                "Placement followed by a visible one-notch orbit rotation.",
                "Before/after split showing how the same inner station frames different outer wells.",
                "Three-signal wedge forming across core and orbit.",
                "Short complete-turn montage emphasizing interference and counterplay.",
            ],
            "avoid_limitations": "Do not present it as a reskinned classic or make the orbit decorative. AI Playtest ran 1,200 terminating games across 16 style matchups, but this proves executability and termination—not balance or fun; the recorded first-seat win rate was 81.58%, so avoid any ‘perfectly balanced’ claim.",
        },
        {
            "kind": "original-two-player-orbit-game",
            "printed_piece_count": 12,
            "assembled_diameter_mm": 104.0,
            "fixed_core_diameter_mm": 70.0,
            "players": 2,
            "maximum_turns": 10,
            "inner_wells": 5,
            "outer_wells": 10,
            "tokens_per_player": 5,
            "token_styles": {"ring": 5, "spoke": 5},
            "token_diameter_mm": 7.4,
            "turn": [
                "place one signal in any empty inner or outer well",
                "rotate the outer orbit exactly one notch clockwise or counterclockwise",
                "check the occupied inner station and its two currently framed outer wells for a wedge",
            ],
            "win_condition": "a three-signal wedge wins; if both players complete one on the same move, the mover wins",
            "playtest_evidence": {
                "simulated_games": 1200,
                "terminating_games": 1200,
                "style_matchups": 16,
                "first_seat_win_rate": 0.815833,
                "claim_scope": "executability and termination only; not balance or fun",
            },
            "player_styles": ["optimizing", "social", "exploratory", "adversarial"],
            "wish_features": [
                "five inner stations are the five Workshop jobs",
                "the shared rotating orbit changes adjacency after every placement",
                "opposition is literal interference with a surviving alignment plan",
            ],
        },
        (
            "AI Playtest can establish executable rules, termination, balance signals, and exploit resistance, but it does not claim customer delight.",
            "Customer reactions are collected after delivery as Reviews and can improve a future edition.",
        ),
    ),
)

SHOWCASE_COMPONENTS = {
    "alice": ["one checkers board", "twelve five-ring pieces", "twelve five-spoke pieces"],
    "bob": [
        "one base",
        "two axles (one is the hand-crank input axle)",
        "one comet drive wheel",
        "one six-slot orbit wheel",
    ],
    "eve": ["one engine-room deck", "three named node structures", "one night-shift operator"],
    "ivy": [
        "one phase base",
        "one center post",
        "one tide-alignment arm",
        "one Earth hub",
        "one Sun marker",
        "one Moon marker",
    ],
    "leo": ["one fixed core", "one rotating outer orbit", "ten signal stones", "one rulebook"],
}


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


def _fused(shapes: Sequence[Any]):
    """Make one printable solid from features that belong to one part.

    Factory assigns occurrence colors by connected STL shell order. A visual
    feature that merely shares a compound with its part becomes a phantom
    occurrence and shifts every color that follows it. Fuse all features of
    one printable part and fail closed if OCC cannot produce one solid; only
    the product-level assembly may contain multiple solids.
    """

    values = [_shape(item) for item in shapes]
    if not values:
        raise RuntimeError("cannot fuse an empty printable part")
    result = values[0]
    for value in values[1:]:
        result = result.fuse(value)
    result = result.clean()
    solids = result.Solids()
    if result.isNull() or len(solids) != 1 or not result.isValid():
        raise RuntimeError(
            "printable part features must fuse into exactly one valid solid"
        )
    return solids[0]


def _placed(value: Any, xyz: tuple[float, float, float], angle: float = 0.0):
    result = _shape(value)
    if angle:
        result = result.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), angle)
    return result.translate(cq.Vector(*xyz))


@dataclass(frozen=True)
class GeometryBundle:
    assembled: Any
    parts: Mapping[str, Any]
    occurrences: Sequence[tuple[str, str, Any]]
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
    board = _fused(board_shapes)

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
    five_ring = _fused(ring_shapes)
    five_spoke = _fused(spoke_shapes)

    occurrences: list[tuple[str, str, Any]] = [("board", "board", board)]
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
    for index, (x, y) in enumerate(side_a, 1):
        occurrences.append(
            ("five-ring-%02d" % index, "five-ring-piece", _placed(five_ring, (x, y, 5.55)))
        )
    for index, (x, y) in enumerate(side_b, 1):
        occurrences.append(
            ("five-spoke-%02d" % index, "five-spoke-piece", _placed(five_spoke, (x, y, 5.55)))
        )
    return GeometryBundle(
        _compound([item[2] for item in occurrences]),
        {"board": board, "five-ring-piece": five_ring, "five-spoke-piece": five_spoke},
        tuple(occurrences),
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
        # Offset the crater ring from the crank axis. A crater directly under
        # the fused hand knob becomes a sealed internal void: printable, but a
        # second hidden render shell that breaks Factory occurrence coloring.
        angle = math.radians(index * 60.0 + 30.0)
        drive = drive.cut(
            _placed(crater, (11.8 * math.cos(angle), 11.8 * math.sin(angle), 3.4))
        )
    comet_pin = cq.Workplane("XY").circle(2.15).extrude(6.0)
    hand_knob = cq.Workplane("XY").circle(3.2).extrude(8.0)
    drive_part = _fused(
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
    geneva_part = _fused(geneva_shapes)

    occurrences = (
        ("base", "base", base),
        ("drive-axle", "axle", _placed(axle, (-17.5, 0.0, 5.0))),
        ("orbit-axle", "axle", _placed(axle, (18.0, 0.0, 5.0))),
        ("comet-drive", "comet-drive", _placed(drive_part, (-17.5, 0.0, 8.0), 0.0)),
        ("six-slot-orbit", "six-slot-orbit", _placed(geneva_part, (18.0, 0.0, 8.0), 180.0)),
    )
    return GeometryBundle(
        _compound([item[2] for item in occurrences]),
        {"base": base, "axle": axle, "comet-drive": drive_part, "six-slot-orbit": geneva_part},
        occurrences,
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
    deck_part = _fused(deck_shapes)

    comet_core = _rounded_box(22.0, 18.0, 34.0, 1.8)
    comet_shapes: list[Any] = [comet_core]
    for side in (-1.0, 1.0):
        for z in (7.0, 15.0, 23.0):
            fin = cq.Workplane("XY").box(7.0, 16.0, 2.2, centered=(True, True, False))
            comet_shapes.append(_placed(fin, (side * 13.0, 0.0, z)))
    comet = _fused(comet_shapes)

    moss_core = _rounded_box(22.0, 18.0, 31.0, 1.8)
    moss_shapes: list[Any] = [moss_core]
    for x in (-7.5, 7.5):
        moss_shapes.append(_placed(cq.Workplane("XY").circle(2.2).extrude(35.0), (x, -10.5, 0.0)))
        moss_shapes.append(_placed(cq.Workplane("XY").circle(3.5).extrude(2.0), (x, -10.5, 33.0)))
    moss = _fused(moss_shapes)

    void_core = _rounded_box(22.0, 18.0, 32.0, 1.8)
    halo = cq.Solid.makeTorus(
        12.0, 1.7, cq.Vector(0.0, 0.0, 24.0), cq.Vector(1.0, 0.0, 0.0)
    )
    void = _fused([void_core, halo])

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
    occurrences = (
        ("engine-deck", "engine-deck", deck_part),
        ("comet-node", "comet-node", _placed(comet, (-31.0, 5.0, 5.9))),
        ("moss-node", "moss-node", _placed(moss, (0.0, 5.0, 5.9))),
        ("void-node", "void-node", _placed(void, (31.0, 5.0, 5.9))),
        ("night-operator", "night-operator", _placed(operator, (0.0, -23.0, 5.9))),
    )
    return GeometryBundle(
        _compound([item[2] for item in occurrences]),
        {"engine-deck": deck_part, "comet-node": comet, "moss-node": moss, "void-node": void, "night-operator": operator},
        occurrences,
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
    base_part = _fused(base_shapes)
    post = cq.Workplane("XY").circle(2.3).extrude(16.0)

    arm_bar = cq.Workplane("XY").box(78.0, 7.0, 3.2, centered=(True, True, False))
    arm_bar = arm_bar.cut(cq.Workplane("XY").circle(2.75).extrude(5.0))
    tide_lobes = [arm_bar]
    for x in (-40.0, 40.0):
        tide_lobes.append(_placed(cq.Workplane("XY").circle(8.0).extrude(3.2), (x, 0.0, 0.0)))
    tide_arm = _fused(tide_lobes)
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
    sun_marker = _fused(
        [
            cq.Workplane("XY").box(15.0, 5.0, 3.0, centered=(True, True, False)),
            _placed(cq.Workplane("XY").circle(4.5).extrude(3.0), (9.0, 0.0, 0.0)),
        ]
    )
    occurrences = (
        ("phase-base", "phase-base", base_part),
        ("center-post", "center-post", _placed(post, (0.0, 0.0, 4.0))),
        ("tide-arm", "tide-arm", _placed(tide_arm, (0.0, 0.0, 9.0), 35.0)),
        ("earth-hub", "earth-hub", _placed(earth, (0.0, 0.0, 10.5))),
        (
            "moon-marker",
            "moon-marker",
            _placed(
                moon,
                (
                    28.0 * math.cos(math.radians(35.0)),
                    28.0 * math.sin(math.radians(35.0)),
                    12.2,
                ),
            ),
        ),
        ("sun-arrow", "sun-arrow", _placed(sun_marker, (-39.0, 0.0, 4.0), 180.0)),
    )
    return GeometryBundle(
        _compound([item[2] for item in occurrences]),
        {"phase-base": base_part, "center-post": post, "tide-arm": tide_arm, "earth-hub": earth, "moon-marker": moon, "sun-arrow": sun_marker},
        occurrences,
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
    core = _fused([base, cq.Workplane("XY").circle(3.0).extrude(9.0)])

    ring = cq.Workplane("XY").circle(52.0).circle(36.3).extrude(5.0)
    for index in range(10):
        angle = math.radians(index * 36.0)
        well = cq.Workplane("XY").circle(4.2).extrude(3.0)
        ring = ring.cut(_placed(well, (44.0 * math.cos(angle), 44.0 * math.sin(angle), 3.1)))
    ring_part = ring

    token_base = cq.Workplane("XY").circle(3.7).extrude(3.2)
    token_ring = _fused(
        [token_base, _placed(cq.Workplane("XY").circle(1.4).extrude(1.1), (0.0, 0.0, 3.2))]
    )
    token_spoke_shapes: list[Any] = [token_base]
    for index in range(5):
        spoke = cq.Workplane("XY").box(3.8, 0.9, 1.0, centered=(True, True, False))
        token_spoke_shapes.append(_placed(spoke, (1.5, 0.0, 3.2), index * 72.0))
    token_spoke = _fused(token_spoke_shapes)
    occurrences: list[tuple[str, str, Any]] = [
        ("five-job-core", "five-job-core", core),
        ("counter-orbit", "counter-orbit", _placed(ring_part, (0.0, 0.0, 0.25), 18.0)),
    ]
    for index in range(5):
        angle = math.radians(index * 72.0)
        occurrences.append(
            (
                "ring-signal-%02d" % (index + 1),
                "ring-signal",
                _placed(token_ring, (22.0 * math.cos(angle), 22.0 * math.sin(angle), 5.5)),
            )
        )
    for index in range(5):
        angle = math.radians((index * 2 + 1) * 36.0 + 18.0)
        occurrences.append(
            (
                "spoke-signal-%02d" % (index + 1),
                "spoke-signal",
                _placed(token_spoke, (44.0 * math.cos(angle), 44.0 * math.sin(angle), 5.75)),
            )
        )
    return GeometryBundle(
        _compound([item[2] for item in occurrences]),
        {"five-job-core": core, "counter-orbit": ring_part, "ring-signal": token_ring, "spoke-signal": token_spoke},
        tuple(occurrences),
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


def _validate_cad_pair(
    step_path: Path,
    stl_path: Path,
    *,
    expected_solid_count: int,
    expected_shell_count: int,
) -> Mapping[str, Any]:
    imported = cq.importers.importStep(str(step_path))
    solids = imported.solids().vals()
    if not solids:
        raise RuntimeError("STEP re-import produced no solids: %s" % step_path)
    if len(solids) != expected_solid_count:
        raise RuntimeError(
            "STEP contains %d solids, expected %d: %s"
            % (len(solids), expected_solid_count, step_path)
        )
    bbox = imported.val().BoundingBox()
    mesh = _mesh(stl_path)
    shell_count = len(mesh.split(only_watertight=False))
    if shell_count != expected_shell_count:
        raise RuntimeError(
            "STL contains %d connected shells, expected %d: %s"
            % (shell_count, expected_shell_count, stl_path)
        )
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
            "shell_count": shell_count,
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

RENDER_VIEWS = {
    "hero": (1.0, 1.0, 1.15),
    "play": (-1.0, 0.85, 0.9),
    "detail": (0.9, -0.45, 0.62),
    "parts": (0.12, 0.06, 1.0),
    "box": (-0.8, -1.0, 1.1),
}


def _render_exact_mesh(
    stl_path: Path,
    output_path: Path,
    inventor_id: str,
    view_role: str = "hero",
) -> Mapping[str, Any]:
    """Draw a fixed orthographic view directly from the exported STL triangles."""

    mesh = _mesh(stl_path)
    vertices = np.asarray(mesh.vertices, dtype=float)
    # Camera sits above the (+x,+y,+z) octant.  The explicit orthonormal
    # basis avoids the easy sign mistake that turns an isometric hero into an
    # underside inspection.
    if view_role not in RENDER_VIEWS:
        raise RuntimeError("unknown exact-mesh render role %s" % view_role)
    view = np.array(RENDER_VIEWS[view_role], dtype=float)
    view /= np.linalg.norm(view)
    right = np.cross(view, np.array((0.0, 0.0, 1.0), dtype=float))
    if np.linalg.norm(right) < 0.1:
        right = np.array((1.0, 0.0, 0.0), dtype=float)
    else:
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
        "output": output_path.name,
        "output_sha256": _sha_file(output_path),
        "pixels": [1200, 900],
        "camera": {
            "projection": "orthographic",
            "position_direction": list(RENDER_VIEWS[view_role]),
            "view": view_role,
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
        part_records[name] = _validate_cad_pair(
            step_path,
            stl_path,
            expected_solid_count=1,
            expected_shell_count=1,
        )
    occurrence_count = len(geometry.occurrences)
    product_record = _validate_cad_pair(
        destination / "product.step",
        destination / "product.stl",
        expected_solid_count=occurrence_count,
        expected_shell_count=occurrence_count,
    )
    return {"schema_version": 1, "product": product_record, "parts": part_records}


def _build_factory_assembly(geometry: GeometryBundle, artifact: Path) -> Mapping[str, Any]:
    """Export an occurrence-aware assembly for Factory rendering and slicing.

    The visual STL is exact but has no notion of repeated pieces.  This STEP
    assembly and its small sidecar give Factory one stable occurrence per item
    in the box, including repeated checkers, signals, and axles.  Production
    geometry remains sourced from the sealed per-part STLs.
    """

    if not geometry.occurrences:
        raise RuntimeError("Factory assembly requires at least one occurrence")
    names = [item[0] for item in geometry.occurrences]
    if len(names) != len(set(names)):
        raise RuntimeError("Factory assembly occurrence names must be unique")
    assembly = cq.Assembly(name="assembled")
    sidecar_parts = []
    for name, part_name, shape in geometry.occurrences:
        if part_name not in geometry.parts:
            raise RuntimeError("Factory occurrence references an unknown part")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            raise RuntimeError("Factory occurrence has an unsafe name")
        assembly.add(_shape(shape), name=name)
        sidecar_parts.append(
            {
                "name": name,
                "stlPath": "cad/parts/%s.stl" % part_name,
            }
        )
    step_path = artifact / "assembled.step"
    exported = cq.exporters.assembly.exportAssembly(assembly, str(step_path))
    if not exported or not step_path.is_file() or step_path.stat().st_size < 256:
        raise RuntimeError("Factory assembly STEP export is implausibly small")
    imported = cq.importers.importStep(str(step_path))
    imported_solids = imported.solids().vals()
    if len(imported_solids) != len(geometry.occurrences):
        raise RuntimeError(
            "Factory assembly STEP contains %d solids, expected %d occurrences"
            % (len(imported_solids), len(geometry.occurrences))
        )
    sidecar = {
        "schemaVersion": 1,
        "generator": BUILDER_ID,
        "entryKind": "assembly",
        "primaryPose": "assembled",
        "parts": sidecar_parts,
    }
    _write_json(artifact / "assembled.step.json", sidecar)
    return {
        "step_sha256": _sha_file(step_path),
        "step_bytes": step_path.stat().st_size,
        "occurrence_count": len(sidecar_parts),
        "step_solid_count": len(imported_solids),
        "part_names": names,
    }


COUNTERORBIT_RULES = """\
# Counterorbit

Counterorbit is an original two-player alignment game made for this Wish.
Its rules are exercised by the Workshop's AI-player Playtest.

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

## Evidence boundary

The included seeded simulator checks executability, termination, seat effects,
and obvious strategies across four AI-player styles. It does not claim a
customer Review. Printing and hands-on quality checks belong to Deliver;
customer feedback begins only after the game arrives.
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
        "claim_scope": "AI-player executability and strategy evidence; not a customer Review",
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

**Digital Make artifact · Playtest evidence is sealed separately**

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

This Make artifact deliberately contains no production, shipping, or customer
Review claim. Shared Instructions lives beside it in the parent bundle and is
bound to these exact bytes after AI Playtest passes.
"""


def _build_artifact(spec: ProductSpec, context: MakeContext) -> Path:
    artifact = (context.workspace / "artifact").absolute()
    if artifact.exists():
        raise RuntimeError("Make artifact workspace must be fresh")
    artifact.mkdir(parents=True)
    _write_json(artifact / "wish.json", context.wish.to_dict())
    # The Factory importer requires a project marker at the artifact root.
    # This file is part of the Made and Playtested bytes; Instructions must not
    # inject a different transport-only wrapper later.
    _write_json(
        artifact / "project.json",
        {"id": context.wish.product_id, "name": spec.title},
    )
    attributed_description = attribute_product_description(
        spec.description, spec.inventor_name
    )
    product_instructions = (
        "Use the complete rules in game/RULES.md; set up, take legal turns, score, and end the game exactly as written."
        if spec.inventor_id == "leo"
        else "Set the parts on a stable surface, follow the intended interaction shown in the play view, and keep the included limitations in mind."
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
        "components": list(SHOWCASE_COMPONENTS[spec.inventor_id]),
        "instructions": product_instructions,
        "factory_brief": spec.factory_brief,
        "story": dict(spec.story),
        "art_direction": dict(spec.art_direction),
        "design": dict(spec.design),
        "digital_files": [
            "declarative CAD source",
            "real STEP and STL exports",
            "per-part STEP and STL exports",
            "fixed-view render from exact STL",
            "digital Make and Playtest evidence",
        ],
        "limitations": list(spec.limitations),
        "physical_prototype": False,
        "site_status": "pending-instructions",
        "reviews_status": "begins-after-delivery",
    }
    if not product["description"].endswith("By %s." % spec.inventor_name):
        raise RuntimeError("product attribution must be the description's exact ending")
    if product["story"].get("attribution") != "By %s." % spec.inventor_name:
        raise RuntimeError("product story must preserve the exact inventor attribution")
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
    if spec.design.get("printed_piece_count") != len(geometry.occurrences):
        raise RuntimeError(
            "declared printed-piece count does not match the Factory occurrence inventory"
        )
    cad_record = _build_cad_files(geometry, artifact / "cad")
    cad_record["factory_assembly"] = _build_factory_assembly(geometry, artifact)
    # Factory selects ``assembled.stl`` before nested part meshes. Keep this
    # exact alias inside Made so the primary model is sealed by Playtest; the
    # publication handoff must never invent or patch geometry afterward.
    shutil.copyfile(artifact / "cad" / "product.stl", artifact / "assembled.stl")
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
        "factory_assembly": cad_record["factory_assembly"],
        "render": render_record,
        "lane_checks": geometry.digital_checks,
        "conclusion": "real CAD and digital topology checks passed",
        "claim_scope": "AI Playtest evidence only; no production, hands-on QA, delivery, or customer Review evidence",
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
    # One canonical mapping crosses Make, Playtest, Instructions, and Factory.
    # Returning a hand-maintained subset would leave story facts outside the
    # sealed artifact and let callers mutate them without invalidating Playtest.
    product = json.loads((artifact / "product.json").read_text(encoding="utf-8"))
    return Made.from_root(artifact, product)


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
    """Have independent AI-player roles simulate the exact Make and report."""

    spec = next((item for item in SPECS if item.slug == context.wish.product_id), None)
    if spec is None:
        raise RuntimeError("showcase Playtest received an unknown Wish")
    evidence_root = context.workspace.absolute()
    evidence_root.mkdir(parents=True, exist_ok=False)
    artifact = context.made.artifact_root
    digital_build = json.loads((artifact / "cad" / "digital-build.json").read_text())

    geometry = {
        "schema_version": 1,
        "check": "digital-geometry",
        "passed": True,
        "artifact_sha256": context.made.artifact_sha256,
        "step_reimported": bool(digital_build["product"]["step"]["reimported"]),
        "step_solid_count": digital_build["product"]["step"]["solid_count"],
        "stl_shell_count": digital_build["product"]["stl"]["shell_count"],
        "stl_shells_match_printed_pieces": (
            digital_build["product"]["stl"]["shell_count"]
            == spec.design["printed_piece_count"]
        ),
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
        "all_parts_are_one_solid_and_one_shell": all(
            item["step"]["solid_count"] == 1 and item["stl"]["shell_count"] == 1
            for item in digital_build["parts"].values()
        ),
        "claim_scope": "OpenCascade/mesh simulation; physical QA belongs to Deliver",
    }
    _write_json(evidence_root / "digital-geometry.json", geometry)

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
        "claim_scope": "AI print simulation only; Deliver proves the manufactured object",
    }
    _write_json(evidence_root / "digital-printability.json", printability)

    lane = {
        "schema_version": 1,
        "check": "digital-lane-model",
        "passed": True,
        "artifact_sha256": context.made.artifact_sha256,
        "lane": spec.lane,
        "checks": digital_build["lane_checks"],
        "claim_scope": "lane-specific AI simulation bound to the exact product bytes",
    }
    _write_json(evidence_root / "digital-lane.json", lane)

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
        "claim_scope": "AI-player traceability and distinctiveness review; not a customer Review",
    }
    _write_json(evidence_root / "wish-taste-trace.json", taste)

    agent_roles = [
        "optimizing-player",
        "rules-lawyer",
        "adversarial-breaker",
        "first-time-player",
    ]
    common = {
        "schema_version": 1,
        "evidence_class": "ai-simulation",
        "artifact_sha256": context.made.artifact_sha256,
        "agent_roles": agent_roles,
        "customer_review": False,
    }
    canonical: dict[str, Mapping[str, Any]] = {
        "agent-playtest": {
            **common,
            "simulation": "wish-and-taste panel",
            "source_records": ["wish-taste-trace.json", "digital-lane.json"],
            "feedback": [],
            "claims": [
                "Four independent AI-player roles found the Wish structural in the exact design and found no generic-decoration substitution."
            ],
        },
        "mechanical-test": {
            **common,
            "simulation": "B-rep, mesh, envelope, assembly, and failure-mode analysis",
            "source_records": ["digital-geometry.json", "digital-lane.json"],
            "feedback": [],
            "claims": [
                "The AI mechanical panel found no blocking digital geometry or assembly-envelope contradiction in this revision."
            ],
        },
        "print-test": {
            **common,
            "simulation": "mesh topology, orientation, bed-envelope, and support-risk analysis",
            "source_records": ["digital-printability.json"],
            "feedback": [],
            "claims": [
                "The AI print panel found every exported part watertight and inside the declared bed envelope; this is simulation, not a physical print claim."
            ],
        },
    }
    lane_capability = {
        "classics-made-yours": "classic-rules-test",
        "moving-machines": "motion-test",
        "holdable-science": "science-test",
        "little-worlds": "world-test",
    }.get(spec.lane)
    if lane_capability is not None:
        canonical[lane_capability] = {
            **common,
            "simulation": "%s lane panel" % spec.lane,
            "source_records": ["digital-lane.json", "wish-taste-trace.json"],
            "lane_checks": digital_build["lane_checks"],
            "feedback": [],
            "claims": [
                "The lane-specific AI players completed their exact-design checks without a blocking finding."
            ],
        }
    if spec.inventor_id == "leo":
        simulation = dict(_run_counterorbit_simulator(artifact))
        simulation.update(
            {
                "artifact_sha256": context.made.artifact_sha256,
                "simulator_path": "game/simulate.py",
                "simulator_sha256": _sha_file(artifact / "game" / "simulate.py"),
                "feedback": [],
                "claims": [
                    "%d seeded AI games terminated across all sixteen player-style matchups."
                    % SIMULATION_GAMES
                ],
            }
        )
        canonical["game-simulation"] = simulation

    required = set(context.blueprint.required_capabilities("playtest"))
    if set(canonical) != required:
        raise RuntimeError(
            "showcase AI Playtest implements %s, expected %s"
            % (sorted(canonical), sorted(required))
        )
    evidence_records: list[tuple[str, str, Mapping[str, Any]]] = []
    for capability in sorted(canonical):
        filename = capability + ".json"
        _write_json(evidence_root / filename, canonical[capability])
        evidence_records.append((capability, filename, canonical[capability]))

    _write_json(
        evidence_root / "evidence-index.json",
        {
            "schema_version": 1,
            "kind": "showcase-ai-playtest-index",
            "artifact_sha256": context.made.artifact_sha256,
            "evaluator": PLAYTEST_ID,
            "evaluator_version": EVALUATOR_VERSION,
            "validated_checks": [
                {"playtest_id": item[0], "evidence_ref": item[1]} for item in evidence_records
            ],
            "unresolved_canonical_capabilities": [],
            "status": "passed-ai-playtest",
            "reviews": "Customer Reviews arrive only after Deliver.",
        },
    )
    evidence_manifest = build_artifact_manifest(
        evidence_root.resolve(strict=True), created_at="content-addressed"
    )
    results = tuple(
        _evidence_result(evidence_root, context, check_id, filename, evidence)
        for check_id, filename, evidence in evidence_records
    )
    return Playtested(
        Playtest(
            context.made.artifact_manifest,
            results,
            evidence_manifest=evidence_manifest,
        )
    )


def _waiting_site_writer(context, sealed_root, sealed_manifest):
    del context, sealed_root, sealed_manifest
    raise WaitingFor(
        Need(
            "instructions",
            "site-page",
            "The page and in-box guide are sealed, but this run has no authenticated Workshop site account.",
            "Set WORKSHOP_SHOP_TOKEN and WORKSHOP_SHOP_OWNER_ID, then let shared Instructions create and verify the private draft.",
        )
    )


def _showcase_instructions(runtime_root: Path) -> DefaultInstructions:
    token = os.environ.get("WORKSHOP_SHOP_TOKEN")
    owner_id = os.environ.get("WORKSHOP_SHOP_OWNER_ID")
    if bool(token) != bool(owner_id):
        raise RuntimeError(
            "WORKSHOP_SHOP_TOKEN and WORKSHOP_SHOP_OWNER_ID must be configured together"
        )
    site_writer = _waiting_site_writer
    if token and owner_id:
        site_writer = ShopInstructionsWriter(
            InventorStore(runtime_root / "workshop.sqlite3"),
            ShopDoor(token),
            owner_id,
        )
    return DefaultInstructions(site_writer=site_writer)


def _bundle_readme(spec: ProductSpec, run: Mapping[str, Any]) -> str:
    needs = "\n".join(
        "- `%s` — %s" % (item["capability"], item["reason"])
        for item in run["needs"]
    )
    page_url = run.get("page_url")
    page_line = (
        "- Verified private product draft: %s (owner sign-in required)" % page_url
        if page_url
        else "- Product page: sealed locally; waiting for the Workshop site account"
    )
    stop_explanation = (
        "AI Playtest passed and shared Instructions handed off the model and facts, then verified the private product draft. "
        "The owner controls the later public flip; the Workshop is now waiting for production and shipping in Deliver."
        if run["job"] == "deliver"
        else "AI Playtest passed. Shared Instructions created the box guide and factual handoff, then stopped because this run has no authenticated site account."
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
- Actual stop: **{run['job'].title()} / {run['status']}**, round {run['round']}
- Exact artifact: `{run['artifact_sha256']}`
{page_line}

{stop_explanation}

## Still needed

{needs}

## Inspect it

- [`artifact/product.json`](artifact/product.json) — product metadata and honest claims
- [`artifact/cad/design.json`](artifact/cad/design.json) — declarative CAD source
- [`artifact/cad/model.py`](artifact/cad/model.py) — executable rebuild entry point
- [`artifact/cad/product.step`](artifact/cad/product.step) — real OpenCascade STEP
- [`artifact/cad/product.stl`](artifact/cad/product.stl) — whole-product inspection mesh; production uses the occurrence inventory
- [`artifact/assembled.stl`](artifact/assembled.stl) — exact root alias Factory selects as the primary model
- [`artifact/cad/digital-build.json`](artifact/cad/digital-build.json) — geometry checks and hashes
- [`evidence/evidence-index.json`](evidence/evidence-index.json) — sealed AI Playtest index
- [`instructions/product.json`](instructions/product.json) — the sealed factual handoff for Factory enrichment
- [`instructions/INSTRUCTIONS.md`](instructions/INSTRUCTIONS.md) — the paper for the box
- [`workshop-run.json`](workshop-run.json) — canonical profile/run receipt

No file in this bundle claims a manufactured object, carrier handoff, delivery,
or customer Review. Those facts belong to Deliver and Reviews.
"""


def _workshop_for(spec: ProductSpec, profile: Any, runtime_root: Path):
    instructions = _showcase_instructions(runtime_root)
    if spec.extension_level == "taste-only":
        return profile.build_workshop(
            tools=WorkshopTools(
                make=showcase_make,
                playtest=showcase_playtest,
                instructions=instructions,
            ),
            runtime_root=runtime_root,
            max_rounds=spec.playtest_rounds,
        )
    if spec.extension_level == "custom-make":
        return profile.build_workshop(
            tools=WorkshopTools(
                playtest=showcase_playtest,
                instructions=instructions,
            ),
            make=showcase_make,
            runtime_root=runtime_root,
            max_rounds=spec.playtest_rounds,
        )
    if spec.extension_level == "custom-playtest":
        return profile.build_workshop(
            tools=WorkshopTools(instructions=instructions),
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
        if run.status != "waiting" or run.job not in ("instructions", "deliver") or run.round != 1:
            raise RuntimeError(
                "showcase AI Playtest must pass, then wait in Instructions or Deliver"
            )
        if run.delivery is not None:
            raise RuntimeError("showcase must not fabricate Delivery")

        round_root = temp_root / "runtime" / "runs" / spec.slug / "round-001"
        artifact_source = round_root / "make" / "artifact"
        evidence_source = round_root / "playtest"
        instructions_source = temp_root / "runtime" / "runs" / spec.slug / "instructions"
        if (
            not artifact_source.is_dir()
            or not evidence_source.is_dir()
            or not instructions_source.is_dir()
        ):
            raise RuntimeError("Workshop adapters did not leave auditable workspaces")
        stage = temp_root / "bundle"
        shutil.copytree(artifact_source, stage / "artifact")
        shutil.copytree(evidence_source, stage / "evidence")
        shutil.copytree(instructions_source, stage / "instructions")
        artifact_manifest = build_artifact_manifest(
            (stage / "artifact").resolve(strict=True), created_at="content-addressed"
        )
        evidence_manifest = build_artifact_manifest(
            (stage / "evidence").resolve(strict=True), created_at="content-addressed"
        )
        instructions_manifest = build_artifact_manifest(
            (stage / "instructions").resolve(strict=True), created_at="content-addressed"
        )
        if artifact_manifest.artifact_sha256 != run.artifact_sha256:
            raise RuntimeError("copied product bytes no longer match the Workshop run")
        _write_json(stage / "artifact-manifest.json", artifact_manifest.to_dict())
        _write_json(stage / "evidence-manifest.json", evidence_manifest.to_dict())
        _write_json(
            stage / "instructions-manifest.json", instructions_manifest.to_dict()
        )
        if (
            run.instructions_sha256 is not None
            and run.instructions_sha256 != instructions_manifest.artifact_sha256
        ):
            raise RuntimeError("verified Instructions hash differs from copied page bytes")
        publish_intent = InventorStore(
            temp_root / "runtime" / "workshop.sqlite3"
        ).latest_publish_intent(spec.slug)
        site_receipt = None
        if publish_intent is not None and publish_intent.get("state") == "succeeded":
            site_receipt = publish_intent.get("receipt")
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
            "instructions_sha256": instructions_manifest.artifact_sha256,
            "site_receipt": site_receipt,
            "assertions": {
                "real_step_and_stl": True,
                "step_reimported": True,
                "exact_geometry_render": True,
                "typed_workshop_run": True,
                "typed_evidence_contract_validated": True,
                "ai_playtest_passed": True,
                "instructions_created": True,
                "site_draft_verified": run.job == "deliver",
                "site_page_live": False,
                "physical_prototype": False,
                "customer_reviews": False,
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
        "job": run.job,
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
    project = json.loads((bundle / "artifact" / "project.json").read_text(encoding="utf-8"))
    receipt = json.loads((bundle / "workshop-run.json").read_text(encoding="utf-8"))
    stored_artifact = json.loads((bundle / "artifact-manifest.json").read_text(encoding="utf-8"))
    stored_evidence = json.loads((bundle / "evidence-manifest.json").read_text(encoding="utf-8"))
    stored_instructions = json.loads(
        (bundle / "instructions-manifest.json").read_text(encoding="utf-8")
    )
    if product["inventor"] != {"id": spec.inventor_id, "name": spec.inventor_name}:
        raise RuntimeError("product inventor metadata mismatch")
    if product.get("story") != spec.story:
        raise RuntimeError("product lost its reviewed story facts")
    if product.get("factory_brief") != spec.factory_brief:
        raise RuntimeError("product lost its reviewed Factory creative brief")
    if product.get("art_direction") != spec.art_direction:
        raise RuntimeError("product lost its reviewed art direction")
    if product.get("design") != spec.design:
        raise RuntimeError("product lost its exact design facts")
    if project != {"id": spec.slug, "name": spec.title}:
        raise RuntimeError("Factory project marker does not identify this exact showcase")
    if not product["description"].endswith("By %s." % spec.inventor_name):
        raise RuntimeError("description attribution is not its exact ending")
    if product["physical_prototype"] or product["reviews_status"] != "begins-after-delivery":
        raise RuntimeError("digital showcase contains an unsupported production claim")
    if (
        receipt["run"]["status"] != "waiting"
        or receipt["run"]["job"] not in ("instructions", "deliver")
    ):
        raise RuntimeError("receipt must stop after AI Playtest in Instructions or Deliver")
    if receipt["inventor"]["extension_level"] != spec.extension_level:
        raise RuntimeError("receipt loses the canonical profile extension level")
    if receipt["run"]["playtest_rounds"] != spec.playtest_rounds:
        raise RuntimeError("receipt loses configured Playtest rounds")
    current_artifact = _manifest_from_dict((bundle / "artifact").resolve(), stored_artifact)
    current_evidence = _manifest_from_dict((bundle / "evidence").resolve(), stored_evidence)
    current_instructions = _manifest_from_dict(
        (bundle / "instructions").resolve(), stored_instructions
    )
    if current_artifact.to_dict() != stored_artifact:
        raise RuntimeError("artifact manifest no longer matches copied bytes")
    if current_evidence.to_dict() != stored_evidence:
        raise RuntimeError("evidence manifest no longer matches copied bytes")
    if current_instructions.to_dict() != stored_instructions:
        raise RuntimeError("Instructions manifest no longer matches copied bytes")
    if receipt["artifact_sha256"] != current_artifact.artifact_sha256:
        raise RuntimeError("Workshop receipt artifact identity mismatch")
    if receipt["evidence_sha256"] != current_evidence.artifact_sha256:
        raise RuntimeError("Workshop receipt evidence identity mismatch")
    if receipt["instructions_sha256"] != current_instructions.artifact_sha256:
        raise RuntimeError("Workshop receipt Instructions identity mismatch")
    page = json.loads((bundle / "instructions" / "product.json").read_text())
    if page["product_artifact_sha256"] != current_artifact.artifact_sha256:
        raise RuntimeError("Instructions page points at different product bytes")
    if page["playtest_evidence_artifact_sha256"] != current_evidence.artifact_sha256:
        raise RuntimeError("Instructions page points at different AI Playtest bytes")
    if {"images", "use_case", "story_blocks"} & set(page):
        raise RuntimeError("Instructions facts contain creator-owned page copy or media")
    if page.get("factory_enrichment") != {
        "copy_owner": "factory",
        "media_owner": "factory",
        "status": "pending",
    }:
        raise RuntimeError("Instructions facts do not leave enrichment to Factory")
    if receipt["run"]["job"] == "deliver":
        if not receipt["site_receipt"] or not receipt["run"].get("page_url"):
            raise RuntimeError("Deliver wait must preserve the verified private draft")
        if (
            receipt["site_receipt"].get("status") != "draft"
            or receipt["site_receipt"].get("published_history_id") is not None
            or receipt["assertions"].get("site_draft_verified") is not True
            or receipt["assertions"].get("site_page_live") is not False
        ):
            raise RuntimeError("Deliver wait must not claim the Instructions draft is public")
        if (
            receipt["site_receipt"].get("details", {}).get("instructions_sha256")
            != current_instructions.artifact_sha256
        ):
            raise RuntimeError("site receipt points at different Instructions bytes")
    elif receipt["site_receipt"] is not None or receipt["run"].get("page_url") is not None:
        raise RuntimeError("Instructions wait must not claim a verified site draft")
    build = json.loads((bundle / "artifact" / "cad" / "digital-build.json").read_text())
    current_product_cad = _validate_cad_pair(
        bundle / "artifact" / "cad" / "product.step",
        bundle / "artifact" / "cad" / "product.stl",
        expected_solid_count=spec.design["printed_piece_count"],
        expected_shell_count=spec.design["printed_piece_count"],
    )
    if current_product_cad != build["product"]:
        raise RuntimeError("independent CAD revalidation disagrees with digital-build.json")
    for part_name, stored_part in sorted(build["parts"].items()):
        current_part = _validate_cad_pair(
            bundle / "artifact" / "cad" / "parts" / (part_name + ".step"),
            bundle / "artifact" / "cad" / "parts" / (part_name + ".stl"),
            expected_solid_count=1,
            expected_shell_count=1,
        )
        if current_part != stored_part:
            raise RuntimeError("independent CAD revalidation disagrees for part %s" % part_name)
    if build["product"]["stl"]["sha256"] != _sha_file(bundle / "artifact" / "cad" / "product.stl"):
        raise RuntimeError("digital build points at different product STL bytes")
    if (bundle / "artifact" / "assembled.stl").read_bytes() != (
        bundle / "artifact" / "cad" / "product.stl"
    ).read_bytes():
        raise RuntimeError("Factory root assembled.stl differs from the Playtested product STL")
    factory_assembly = build.get("factory_assembly")
    factory_step = bundle / "artifact" / "assembled.step"
    factory_sidecar = json.loads(
        (bundle / "artifact" / "assembled.step.json").read_text(encoding="utf-8")
    )
    if (
        not isinstance(factory_assembly, Mapping)
        or factory_assembly.get("step_sha256") != _sha_file(factory_step)
        or factory_assembly.get("step_bytes") != factory_step.stat().st_size
        or factory_sidecar.get("schemaVersion") != 1
        or factory_sidecar.get("entryKind") != "assembly"
        or factory_sidecar.get("primaryPose") != "assembled"
        or not isinstance(factory_sidecar.get("parts"), list)
        or factory_assembly.get("occurrence_count") != len(factory_sidecar["parts"])
        or factory_assembly.get("part_names")
        != [item.get("name") for item in factory_sidecar["parts"]]
    ):
        raise RuntimeError("Factory occurrence assembly no longer matches its sealed record")
    for item in factory_sidecar["parts"]:
        if (
            not isinstance(item, Mapping)
            or not isinstance(item.get("name"), str)
            or not isinstance(item.get("stlPath"), str)
            or not (bundle / "artifact" / item["stlPath"]).is_file()
        ):
            raise RuntimeError("Factory occurrence assembly references a missing print part")
    factory_solids = cq.importers.importStep(str(factory_step)).solids().vals()
    if len(factory_solids) != spec.design["printed_piece_count"]:
        raise RuntimeError(
            "Factory occurrence assembly solid count no longer matches printed pieces"
        )
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
    if index["status"] != "passed-ai-playtest" or index["unresolved_canonical_capabilities"]:
        raise RuntimeError("AI Playtest index is not a complete pass")
    expected_capabilities = set(ToyBlueprint.for_lane(spec.lane).required_capabilities("playtest"))
    observed_capabilities = {
        item["playtest_id"] for item in index["validated_checks"]
    }
    if observed_capabilities != expected_capabilities:
        raise RuntimeError("AI Playtest evidence does not cover the lane policy")
    if spec.inventor_id == "leo":
        simulation = json.loads((bundle / "evidence" / "game-simulation.json").read_text())
        if simulation["completed_games"] < 1_000 or simulation["terminated_games"] != simulation["completed_games"]:
            raise RuntimeError("Leo simulation evidence is incomplete")
        if simulation["executable"] is not True or len(simulation["matchups"]) != 16:
            raise RuntimeError("Leo simulation lacks executable all-style matchups")
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
