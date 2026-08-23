"""Export each unique Blindcap: Duel printable separately.

Keeping individual solids out of the hero assembly makes failure isolation fast
and gives slicers canonical, quantity-aware inputs. This file intentionally does
not assert physical fit; use this project's fit_coupons.py on the target printer.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parent))

import params as p
from blocks import shared_positions
from claim_crown import build_claim_crown
from loam_tile import build_loam_tile
from probe_pin import build_probe_pin
from spore_trough import build_spore_trough_with_owner
from stool import build_stool


def builders():
    socket_positions = shared_positions(
        p.SOCKET_COLS, p.SOCKET_ROWS, p.SOCKET_PITCH, z=p.TILE_T
    )
    result = {
        "loam_tile": lambda: build_loam_tile(socket_positions),
        "claim_crown_p1": lambda: build_claim_crown(1),
        "claim_crown_p2": lambda: build_claim_crown(2),
        "probe_pin_p1": lambda: build_probe_pin(1),
        "probe_pin_p2": lambda: build_probe_pin(2),
        "spore_trough_p1": lambda: build_spore_trough_with_owner(1),
        "spore_trough_p2": lambda: build_spore_trough_with_owner(2),
    }
    for species in ("deadhead", "bracket", "inkcap", "hollow"):
        for owner in (1, 2):
            name = f"stool_{species}_p{owner}"
            result[name] = lambda species=species, owner=owner: build_stool(species, owner)
    return result


def export_part(name: str, shape, out_dir: Path):
    orientation = "as_modelled"
    if not shape.val().isValid():
        raise RuntimeError(f"{name}: invalid B-rep")
    step_path = out_dir / f"{name}.step"
    stl_path = out_dir / f"{name}.stl"
    cq.exporters.export(shape, str(step_path))
    cq.exporters.export(shape, str(stl_path), tolerance=0.08, angularTolerance=0.08)
    bb = shape.val().BoundingBox()
    return {
        "name": name,
        "step": str(step_path),
        "stl": str(stl_path),
        "bbox_mm": [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)],
        "volume_mm3": round(shape.val().Volume(), 3),
        "brep_valid": True,
        "print_orientation": orientation,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--only", action="append", help="part name; may repeat")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    available = builders()
    names = args.only or list(available)
    unknown = sorted(set(names) - set(available))
    if unknown:
        raise SystemExit(f"unknown parts: {', '.join(unknown)}")
    records = []
    for name in names:
        records.append(export_part(name, available[name](), args.out))
        print(json.dumps(records[-1], sort_keys=True), flush=True)
    (args.out / "validation.json").write_text(
        json.dumps({"parts": records}, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
