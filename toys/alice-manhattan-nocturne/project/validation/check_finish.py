#!/usr/bin/env python3
"""Verify the Round-5 manufacturing finish without changing sealed CAD."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from build123d import Align, Box, Location


PROJECT = Path(__file__).resolve().parent.parent
PLAN_PATH = Path(__file__).with_name("finish-plan.json")
sys.path.insert(0, str(PROJECT))

import manhattan_nocturne_lib as lib  # noqa: E402
import params as p  # noqa: E402


passed: list[str] = []


def check(name: str, condition: bool, detail: str) -> None:
    assert condition, f"FAIL {name} — {detail}"
    passed.append(f"ok  {name:31s} {detail}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sealed_geometry_files() -> list[Path]:
    paths = [PROJECT / "manhattan_nocturne.step", PROJECT / "part_board.step"]
    paths.extend(
        PROJECT / f"part_{side}_{role}.step"
        for side in p.SIDES
        for role in p.ROLES
    )
    paths.append(PROJECT / "exports" / "stl" / "part_board.stl")
    paths.extend(
        PROJECT / "exports" / "stl" / f"part_{side}_{role}.stl"
        for side in p.SIDES
        for role in p.ROLES
    )
    return sorted(paths, key=lambda path: path.relative_to(PROJECT).as_posix())


plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
check(
    "finish-plan schema",
    plan.get("schema") == "workshop.finish-plan.v1"
    and plan.get("product") == "manhattan-nocturne"
    and plan.get("part") == "BOARD",
    "Workshop finish plan targets BOARD only",
)

boundary = plan["finish_boundary"]
check(
    "exact material boundary",
    boundary["z_mm"] == p.FINISH_BOUNDARY_Z == p.BOARD_THICKNESS == 8.20
    and boundary["top_z_mm"] == p.BOARD_TOTAL_HEIGHT == 9.00
    and boundary["layer_height_mm"] == p.EXPLORATION_LAYER_HEIGHT == 0.20
    and boundary["completed_layers"] == 41,
    "midnight ends at completed Z8.20; light-pad finish continues to Z9.00",
)
check(
    "required real contrast",
    plan["required_contrast"]
    == {"base": p.BOARD_BASE_FINISH, "light_pads": p.LIGHT_PAD_FINISH}
    and p.BOARD_BASE_FINISH == "midnight"
    and p.LIGHT_PAD_FINISH == "warm-brass-gold",
    "midnight base + warm brass/gold light-square family",
)

sealed_files = sealed_geometry_files()
check(
    "sealed artifacts present",
    len(sealed_files) == 27 and all(path.is_file() for path in sealed_files),
    "27 canonical STEP/STL artifacts present",
)
geometry_map = {
    path.relative_to(PROJECT).as_posix(): sha256(path) for path in sealed_files
}
geometry_payload = json.dumps(
    geometry_map, sort_keys=True, separators=(",", ":")
).encode("utf-8")
geometry_digest = hashlib.sha256(geometry_payload).hexdigest()
seal = plan["geometry_seal"]
check(
    "geometry seal",
    seal["mutation_allowed"] is False
    and seal["file_count"] == len(sealed_files)
    and seal["sha256"] == geometry_digest,
    f"all STEP/STL hashes unchanged; set {geometry_digest[:12]}…",
)
builder_source = (PROJECT / "manhattan_nocturne_lib.py").read_text(encoding="utf-8")
check(
    "finish isolated from CAD",
    all(
        name not in builder_source
        for name in (
            "BOARD_BASE_FINISH",
            "LIGHT_PAD_FINISH",
            "FINISH_BOUNDARY_Z",
            "FINISH_TEXTURE_ENABLED",
        )
    ),
    "manufacturing-finish parameters are not consumed by any shape builder",
)

board = lib.build_board()
board_bounds = board.bounding_box()
check(
    "sealed board envelope",
    len(board.solids()) == 1
    and board.is_valid
    and abs(board_bounds.min.Z) < 1e-7
    and abs(board_bounds.max.Z - 9.00) < 1e-7
    and abs(board_bounds.size.X - 244.00) < 1e-7
    and abs(board_bounds.size.Y - 244.00) < 1e-7,
    "one valid 244×244×9 mm board solid",
)

probe_epsilon = 0.0001
base_probe = board.intersect(
    Location((0.0, 0.0, 0.0))
    * Box(
        p.BOARD_SIZE + 2.0,
        p.BOARD_SIZE + 2.0,
        p.FINISH_BOUNDARY_Z - probe_epsilon,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
)
check(
    "continuous midnight base",
    len(base_probe.solids()) == 1,
    "one connected solid exists throughout the board below Z8.20",
)

above_boundary = board.intersect(
    Location((0.0, 0.0, p.FINISH_BOUNDARY_Z + probe_epsilon))
    * Box(
        p.BOARD_SIZE + 2.0,
        p.BOARD_SIZE + 2.0,
        p.SQUARE_RELIEF,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
)
above_solids = list(above_boundary.solids())
actual_centers = sorted(
    (
        round((solid.bounding_box().min.X + solid.bounding_box().max.X) / 2.0, 5),
        round((solid.bounding_box().min.Y + solid.bounding_box().max.Y) / 2.0, 5),
    )
    for solid in above_solids
)
expected_centers = sorted(
    tuple(round(value, 5) for value in p.square_center(file_index, rank_index))
    for file_index in range(p.FILES)
    for rank_index in range(p.RANKS)
    if p.is_light_square(file_index, rank_index)
)
check(
    "only light pads above boundary",
    len(above_solids) == 32
    and all(solid.is_valid for solid in above_solids)
    and actual_centers == expected_centers,
    "exactly 32 isolated light-square solids continue above Z8.20",
)

top_faces = [
    face
    for face in board.faces()
    if abs(face.center().Z - p.BOARD_TOTAL_HEIGHT) < 1e-7
    and face.normal_at(face.center()).Z > 0.999
]
check(
    "stable light-pad tops",
    len(top_faces) == 32
    and all(abs(face.area - p.LIGHT_PAD_TOP_SIZE**2) < 1e-5 for face in top_faces),
    "32 flat 25×25 mm top landings; no texture added",
)
check(
    "standard a1 parity",
    not p.is_light_square(0, 0)
    and p.square_top_z(0, 0) == p.FINISH_BOUNDARY_Z
    and p.square_top_z(7, 0) == p.BOARD_TOTAL_HEIGHT,
    "a1 dark at Z8.20; h1 light at Z9.00",
)

execution = plan["execution"]
method_ids = {method["id"] for method in execution["allowed_methods"]}
check(
    "piece geometry excluded",
    execution["job_scope"] == "BOARD only"
    and execution["piece_artifacts"] == "excluded"
    and seal["mutation_allowed"] is False,
    "finish applies only to the BOARD job and cannot mutate piece artifacts",
)
check(
    "achievable finish methods",
    method_ids
    == {"single-layer-material-change", "masked-post-print-top-finish"}
    and all(
        method["boundary_z_mm"] == p.FINISH_BOUNDARY_Z
        for method in execution["allowed_methods"]
    ),
    "one Z8.20 layer change or one masked post-print top finish",
)
check(
    "no stability texture",
    plan["texture"]["added"] is False and p.FINISH_TEXTURE_ENABLED is False,
    "bevel supplies real light response; flat piece landings are preserved",
)
claims = plan["claims"]
check(
    "Deliver evidence held",
    all(
        claims[key] == "unverified-until-deliver"
        for key in ("physical_execution", "finish_color", "finish_adhesion")
    ),
    "digital plan is not physical finish or adhesion evidence",
)

print("\n".join(passed))
print(f"\ncheck_finish: ok - {len(passed)} deterministic checks passed")
