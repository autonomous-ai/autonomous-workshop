"""Build a complete two-player viewer scene as STEP and disconnected-shell STL."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cadquery as cq

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

import params as p  # noqa: E402
from blocks import shared_positions  # noqa: E402
from claim_crown import build_claim_crown  # noqa: E402
from fit_coupons import _place_pin  # noqa: E402
from loam_tile import build_loam_tile  # noqa: E402
from probe_pin import build_probe_pin  # noqa: E402
from spore_trough import build_spore_trough_with_owner  # noqa: E402
from stool import build_stool  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    asm = cq.Assembly(name="blindcap_duel")
    located = []

    def add(shape, name, xyz=(0, 0, 0), rot=0):
        placed = shape
        if rot:
            placed = placed.rotate((0, 0, 0), (0, 0, 1), rot)
        placed = placed.translate(xyz)
        asm.add(placed, name=name)
        located.extend(placed.val().Solids())

    local_sockets = shared_positions(p.SOCKET_COLS, p.SOCKET_ROWS, p.SOCKET_PITCH, z=p.TILE_T)
    tile = build_loam_tile(local_sockets)
    tile_centers = [(-p.TILE_SIZE / 2, 0, 0), (p.TILE_SIZE / 2, 0, 0)]
    for i, center in enumerate(tile_centers, 1):
        add(tile, f"loam_tile_{i}", center)

    sockets = []
    for tx, ty, _ in tile_centers:
        sockets.extend((tx + x, ty + y, p.SEATED_STOOL_Z) for x, y, _ in local_sockets)
    chosen = [0, 1, 2, 4, 5, 6, 8, 9, 11, 13, 15, 17]
    pieces = [
        ("deadhead", 1), ("deadhead", 1), ("deadhead", 2), ("deadhead", 2),
        ("bracket", 1), ("bracket", 1), ("bracket", 2), ("bracket", 2),
        ("inkcap", 1), ("inkcap", 2), ("hollow", 1), ("hollow", 2),
    ]
    stool_index = {}
    for (species, owner), socket_id in zip(pieces, chosen):
        family = f"stool_{species}_p{owner}"
        stool_index[family] = stool_index.get(family, 0) + 1
        add(build_stool(species, owner), f"{family}_{stool_index[family]:02d}", sockets[socket_id])

    crown_index = {1: 0, 2: 0}
    for owner, socket_id in ((1, 2), (1, 4), (2, 1), (2, 5)):
        crown_index[owner] += 1
        x, y, _ = sockets[socket_id]
        add(build_claim_crown(owner), f"claim_crown_p{owner}_{crown_index[owner]:02d}",
            (x, y, p.SEATED_CROWN_Z))
    crown_index[1] += 1
    crown_index[2] += 1
    add(build_claim_crown(1), f"claim_crown_p1_{crown_index[1]:02d}", (176, 88, 0))
    add(build_claim_crown(2), f"claim_crown_p2_{crown_index[2]:02d}", (204, 88, 0))

    pins = {1: build_probe_pin(1), 2: build_probe_pin(2)}
    staged_defs = (
        (2, 0, "A", p.PIN_PROUD_BLOCKED_MM),
        (2, 0, "B", p.PIN_PROUD_BLOCKED_MM),
        (2, 11, "B", p.PIN_PROUD_ADMITTED_MM),
        (1, 17, "A", p.PIN_PROUD_ADMITTED_MM),
        (1, 17, "B", p.PIN_PROUD_ADMITTED_MM),
        (1, 8, "A", p.PIN_PROUD_ADMITTED_MM),
    )
    owner_pin_index = {1: 0, 2: 0}
    for owner, socket_id, bit, proud in staged_defs:
        owner_pin_index[owner] += 1
        placed = _place_pin(pins[owner], sockets[socket_id][:2], bit, proud, p.TILE_T)
        add(placed, f"probe_pin_p{owner}_{owner_pin_index[owner]:02d}")

    add(build_spore_trough_with_owner(1), "spore_trough_p1_01", (0, 160, 0), 180)
    add(build_spore_trough_with_owner(2), "spore_trough_p2_01", (0, -160, 0), 0)

    step = args.out / "blindcap-duel_assembled.step"
    stl = args.out / "blindcap-duel_assembled.stl"
    asm.save(str(step))
    compound = cq.Compound.makeCompound(located)
    cq.exporters.export(compound, str(stl), tolerance=0.12, angularTolerance=0.12)
    bb = compound.BoundingBox()
    report = {
        "step": str(step),
        "stl": str(stl),
        "bbox_mm": [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)],
        "solid_shells": len(located),
        "contains_exact_reference_poses": {
            "blocked_proud_mm": p.PIN_PROUD_BLOCKED_MM,
            "admitted_proud_mm": p.PIN_PROUD_ADMITTED_MM,
        },
    }
    (args.out / "assembly_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
