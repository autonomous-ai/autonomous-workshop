#!/usr/bin/env python3
"""Self-contained algebraic fit/print audit for Moon-Moth Bloom."""

from __future__ import annotations

import ast
import json
import math
import re
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
SOURCE = PROJECT / "moon_moth_bloom_lib.py"
README = PROJECT / "README.md"
SOURCE_TEXT = SOURCE.read_text(encoding="utf-8")
SOURCE_TREE = ast.parse(SOURCE_TEXT, filename=str(SOURCE))

# Independent copy of only the contract bounds needed to audit the source.
# The generator still imports and uses the canonical CAD-skill cadfits module;
# this stdlib-only audit checks that exact call remains present and recomputes
# its result without needing the skill tree in the host's isolated project.
FIT_TABLE = {"press": -0.05, "snug": 0.10, "slip": 0.20, "free": 0.40}
EXPLICIT_MIN = -0.20
EXPLICIT_MAX = 0.60


def _assignment(name: str) -> ast.AST:
    for node in SOURCE_TREE.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return node.value
    raise AssertionError(f"missing source constant {name}")


def _literal(name: str):
    try:
        return ast.literal_eval(_assignment(name))
    except (TypeError, ValueError) as error:
        raise AssertionError(f"source constant {name} must be literal") from error


def _expression(name: str) -> str:
    return ast.unparse(_assignment(name))


def _imports_cadfits() -> bool:
    return any(
        isinstance(node, ast.Import)
        and any(alias.name == "cadfits" for alias in node.names)
        for node in SOURCE_TREE.body
    )


def _mating_clearance(fit: str | float) -> float:
    if isinstance(fit, str):
        if fit not in FIT_TABLE:
            raise AssertionError(f"unknown fit class {fit!r}")
        return FIT_TABLE[fit]
    value = float(fit)
    if not EXPLICIT_MIN <= value <= EXPLICIT_MAX:
        raise AssertionError(
            f"explicit clearance {value} left {EXPLICIT_MIN}..{EXPLICIT_MAX} mm"
        )
    return value


def _slot_for(tab: float, fit: str | float) -> float:
    if tab <= 0:
        raise AssertionError(f"male base dimension must be positive, got {tab}")
    return tab + 2.0 * _mating_clearance(fit)


def _close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def audit() -> dict:
    expected_entries = {
        "part_chassis.step.py",
        "part_left_wing.step.py",
        "part_right_wing.step.py",
    }
    actual_entries = {path.name for path in PROJECT.glob("part_*.step.py")}
    if actual_entries != expected_entries:
        raise AssertionError(
            f"printable entry inventory drifted: expected {sorted(expected_entries)}, "
            f"got {sorted(actual_entries)}"
        )

    if not _imports_cadfits():
        raise AssertionError("CAD source no longer imports canonical cadfits")
    expected_expressions = {
        "BORE_D": "cadfits.slot_for(POST_D, JOURNAL_RUNNING_CLEARANCE)",
        "LOBE_D": "cadfits.slot_for(FLANGE_D, KEYHOLE_LOBE_CLEARANCE)",
        "THROAT_W": "cadfits.slot_for(POST_D, KEYHOLE_THROAT_CLEARANCE)",
        "PITCH_R": "MODULE * TEETH / 2.0",
    }
    actual_expressions = {name: _expression(name) for name in expected_expressions}
    if actual_expressions != expected_expressions:
        raise AssertionError(
            f"derived-dimension source contract drifted: {actual_expressions}"
        )
    handwritten_mate = re.search(
        r"[+-]\s*2(?:\.0)?\s*\*\s*[A-Z][A-Z0-9_]*CLEAR",
        SOURCE_TEXT,
    )
    if handwritten_mate:
        raise AssertionError(
            f"hand-written doubled-clearance mate found: {handwritten_mate.group(0)}"
        )

    pivot_x = float(_literal("PIVOT_X"))
    module = float(_literal("MODULE"))
    teeth = int(_literal("TEETH"))
    post_d = float(_literal("POST_D"))
    flange_d = float(_literal("FLANGE_D"))
    journal_fit = _literal("JOURNAL_RUNNING_CLEARANCE")
    lobe_fit = _literal("KEYHOLE_LOBE_CLEARANCE")
    throat_fit = _literal("KEYHOLE_THROAT_CLEARANCE")
    wing_t = float(_literal("WING_T"))
    seated_z = float(_literal("SEATED_Z"))
    raised_z = float(_literal("RAISED_Z"))
    low_underside = float(_literal("LOW_UNDERSIDE"))
    high_underside = float(_literal("HIGH_UNDERSIDE"))
    connector_names = tuple(_literal("CONNECTOR_NAMES"))
    assembly_sequence = tuple(_literal("ASSEMBLY_SEQUENCE"))

    axis_spacing = 2.0 * pivot_x
    pitch_diameter = module * teeth
    pitch_radius = pitch_diameter / 2.0
    _close(axis_spacing, pitch_diameter, "paired gear axis spacing")

    bore_d = _slot_for(post_d, journal_fit)
    lobe_d = _slot_for(flange_d, lobe_fit)
    throat_w = _slot_for(post_d, throat_fit)
    clearances = {
        "journal_running_per_side_mm": (bore_d - post_d) / 2.0,
        "flange_lobe_per_side_mm": (lobe_d - flange_d) / 2.0,
        "post_throat_per_side_mm": (throat_w - post_d) / 2.0,
    }
    _close(clearances["journal_running_per_side_mm"], 0.30, "journal clearance")
    _close(
        clearances["flange_lobe_per_side_mm"],
        FIT_TABLE["slip"],
        "flange/lobe clearance",
    )
    _close(clearances["post_throat_per_side_mm"], 0.50, "post/throat clearance")
    if not flange_d > bore_d:
        raise AssertionError("mushroom flange must remain larger than running bore")

    roof_gaps = {
        "raised_service_hood_mm": high_underside - (raised_z + wing_t),
        "seated_operating_roof_mm": low_underside - (seated_z + wing_t),
    }
    _close(roof_gaps["raised_service_hood_mm"], 0.5, "raised service hood gap")
    _close(roof_gaps["seated_operating_roof_mm"], 0.5, "seated roof gap")
    _close(raised_z - seated_z, 1.2, "paired vertical drop")

    expected_connectors = (
        "left-journal-post-to-running-bore",
        "right-journal-post-to-running-bore",
        "left-mushroom-flange-to-keyhole-lobe",
        "right-mushroom-flange-to-keyhole-lobe",
        "module-1-eighteen-tooth-external-gear-pair",
    )
    expected_sequence = (
        "load-keyhole-lobes-over-flanges-at-q118",
        "seat-both-wings-raised-at-z5.7",
        "counter-rotate-under-high-hood-to-q82",
        "drop-both-wings-1.2mm-at-q78",
        "continue-seated-beneath-low-roof",
    )
    if connector_names != expected_connectors:
        raise AssertionError(f"connector-name contract drifted: {connector_names}")
    if assembly_sequence != expected_sequence:
        raise AssertionError(f"assembly-order contract drifted: {assembly_sequence}")

    readme = README.read_text(encoding="utf-8")
    missing_docs = [
        token
        for token in (*connector_names, *assembly_sequence)
        if token not in readme
    ]
    if missing_docs:
        raise AssertionError(f"README omits fit/assembly identifiers: {missing_docs}")

    return {
        "schema_version": 2,
        "kind": "moon-moth-bloom.fit-print-audit",
        "passed": True,
        "isolation": "stdlib-only; reads only files inside the CAD project",
        "printable_entries": sorted(actual_entries),
        "base_dimensions_mm": {
            "gear_axis_spacing": axis_spacing,
            "gear_pitch_diameter": pitch_diameter,
            "gear_pitch_radius": pitch_radius,
        },
        "derived_interfaces_mm": {
            "post_diameter": post_d,
            "running_bore_diameter": bore_d,
            "flange_diameter": flange_d,
            "keyhole_lobe_diameter": lobe_d,
            "keyhole_throat_width": throat_w,
            **clearances,
        },
        "roof_gaps_mm": roof_gaps,
        "connector_names": list(connector_names),
        "assembly_sequence": list(assembly_sequence),
        "limitations": [
            "This algebraic source audit does not prove a successful physical print or fit.",
            "Geometry, bed stance, mesh integrity, interference, and motion remain owned by their dedicated gates.",
        ],
    }


def main() -> int:
    try:
        result = audit()
    except Exception as error:
        print(json.dumps({"ok": False, "error": f"{type(error).__name__}: {error}"}))
        return 1
    print(json.dumps({"ok": True, "audit": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
