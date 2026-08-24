"""Small first-print coupons for socket/probe and tile dovetail calibration.

Exports printable solids plus two exact reference assemblies. The assemblies
stage pins at the measured 27.628906mm high reference and 3mm low stop; they are
not a substitute for a physical fit
test and intentionally remain separate from the production part manifest.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import cadquery as cq

DRAFT = Path(__file__).resolve().parents[1] / "draft"
sys.path.insert(0, str(DRAFT))

import params as p  # noqa: E402
from probe_pin import build_probe_pin  # noqa: E402
from stool import build_stool  # noqa: E402


def _probe_hole(cx, cy, top_z, bit):
    index = p.PROBE_BITS.index(bit)
    mx, my = p.PROBE_MOUTHS_XY[index]
    hx, hy = p.PROBE_INWARD_XY[index]
    ex, ey = cx + mx, cy + my
    angle = math.radians(p.PROBE_ANGLE_DEG)
    length = p.PROBE_CHANNEL_LEN
    direction = cq.Vector(
        math.sin(angle) * hx,
        math.sin(angle) * hy,
        -math.cos(angle),
    )
    solid = cq.Solid.makeCylinder(
        p.PROBE_HOLE_D / 2.0,
        length,
        pnt=cq.Vector(ex, ey, top_z),
        dir=direction,
    )
    counterbore_start = cq.Vector(
        ex - direction.x * p.PROBE_COUNTERBORE_LEN,
        ey - direction.y * p.PROBE_COUNTERBORE_LEN,
        top_z - direction.z * p.PROBE_COUNTERBORE_LEN,
    )
    counterbore = cq.Solid.makeCylinder(
        p.PROBE_COUNTERBORE_D / 2.0,
        p.PROBE_COUNTERBORE_LEN,
        pnt=counterbore_start,
        dir=direction,
    )
    return cq.Workplane("XY").newObject([solid, counterbore])


def _d_bore(height):
    body = cq.Workplane("XY").circle(p.BORE_D / 2.0).extrude(height)
    trim = (
        cq.Workplane("XY")
        .box(p.BORE_D * 2, p.BORE_D * 2, height + 0.4, centered=(True, False, False))
        .translate((0, p.BORE_KEY_FLAT_Y - p.BORE_D * 2, -0.2))
    )
    return body.cut(trim)


def _place_pin(pin_shape, center_xy, bit, proud_mm, top_z):
    index = p.PROBE_BITS.index(bit)
    mx, my = p.PROBE_MOUTHS_XY[index]
    hx, hy = p.PROBE_INWARD_XY[index]
    angle = math.radians(p.PROBE_ANGLE_DEG)
    outward_azimuth_deg = math.degrees(math.atan2(-hy, -hx))
    axis = (
        -math.sin(angle) * hx,
        -math.sin(angle) * hy,
        math.cos(angle),
    )
    cx, cy = center_xy
    ex, ey = cx + mx, cy + my
    entry_local_z = p.PIN_LEN - proud_mm
    tx = ex - axis[0] * entry_local_z
    ty = ey - axis[1] * entry_local_z
    tz = top_z - axis[2] * entry_local_z
    return (
        pin_shape
        .rotate((0, 0, 0), (0, 1, 0), p.PROBE_ANGLE_DEG)
        .rotate((0, 0, 0), (0, 0, 1), outward_azimuth_deg)
        .translate((tx, ty, tz))
    )


def socket_coupon():
    size = 44.0
    top_z = p.TILE_T
    body = cq.Workplane("XY").box(size, size, top_z, centered=(True, True, False))
    bore = _d_bore(p.BORE_DEPTH).translate((0, 0, top_z - p.BORE_DEPTH))
    body = body.cut(bore)
    collar = (
        cq.Workplane("XY")
        .circle(p.COLLAR_OD / 2.0)
        .extrude(p.COLLAR_H)
        .cut(_d_bore(p.COLLAR_H + 0.2))
        .translate((0, 0, top_z))
    )
    body = body.union(collar)
    for bit in p.PROBE_BITS:
        body = body.cut(_probe_hole(0, 0, top_z, bit))
    return body


def dovetail_male_coupon():
    h = 8.0
    base = cq.Workplane("XY").box(30, 44, h, centered=(False, True, False)).translate((-30, 0, 0))
    tab = (
        cq.Workplane("XY")
        .polyline([(0, -10), (0, 10), (p.DOVETAIL_DEPTH, 12), (p.DOVETAIL_DEPTH, -12)])
        .close()
        .extrude(h)
    )
    return base.union(tab)


def dovetail_female_coupon():
    h = 8.0
    c = p.DOVETAIL_CLEARANCE
    base = cq.Workplane("XY").box(30, 44, h, centered=(False, True, False))
    slot = (
        cq.Workplane("XY")
        .polyline([
            (0, -10 - c),
            (0, 10 + c),
            (p.DOVETAIL_DEPTH + c, 12 + c),
            (p.DOVETAIL_DEPTH + c, -12 - c),
        ])
        .close()
        .extrude(h + 0.4)
        .translate((0, 0, -0.2))
    )
    return base.cut(slot)


def _export(shape, name, out):
    orientation = "as_modelled"
    if not shape.val().isValid():
        raise RuntimeError(f"{name}: invalid B-rep")
    cq.exporters.export(shape, str(out / f"{name}.step"))
    cq.exporters.export(
        shape, str(out / f"{name}.stl"), tolerance=0.12, angularTolerance=0.12
    )
    bb = shape.val().BoundingBox()
    return {
        "name": name,
        "bbox_mm": [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)],
        "brep_valid": True,
        "print_orientation": orientation,
    }


def _reference_assembly(stool_species, bit, proud_mm):
    asm = cq.Assembly()
    asm.add(socket_coupon(), name="socket_coupon")
    asm.add(
        build_stool(stool_species, 1),
        name=f"stool_{stool_species}",
        loc=cq.Location(cq.Vector(0, 0, p.SEATED_STOOL_Z)),
    )
    pin = _place_pin(build_probe_pin(1), (0, 0), bit, proud_mm, p.TILE_T)
    asm.add(pin, name="probe_pin")
    return asm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    solids = {
        "socket_coupon": socket_coupon(),
        "coupon_stool_deadhead_p1": build_stool("deadhead", 1),
        "coupon_stool_bracket_p1": build_stool("bracket", 1),
        "coupon_stool_inkcap_p1": build_stool("inkcap", 1),
        "coupon_stool_hollow_p1": build_stool("hollow", 1),
        "coupon_probe_pin_p1": build_probe_pin(1),
        "coupon_probe_pin_p2": build_probe_pin(2),
        "dovetail_male_coupon": dovetail_male_coupon(),
        "dovetail_female_coupon": dovetail_female_coupon(),
    }
    records = [_export(shape, name, args.out) for name, shape in solids.items()]
    high_label = f"{p.PIN_PROUD_BLOCKED_MM:.6f}".replace(".", "_")
    _reference_assembly("deadhead", "A", p.PIN_PROUD_BLOCKED_MM).save(
        str(args.out / f"blocked_{high_label}mm_reference.step")
    )
    _reference_assembly("bracket", "A", p.PIN_PROUD_ADMITTED_MM).save(
        str(args.out / "admitted_3mm_reference.step")
    )
    report = {
        "parts": records,
        "reference_poses_mm": {
            "blocked_proud": p.PIN_PROUD_BLOCKED_MM,
            "admitted_proud": p.PIN_PROUD_ADMITTED_MM,
        },
        "clearances_mm": {
            "stool_bore_diametral": round(p.BORE_D - p.STOOL_SHANK_D, 3),
            "crown_boss_diametral": round(p.CROWN_ID - p.STOOL_BOSS_D, 3),
            "probe_min_across_flats": round(p.PROBE_HOLE_D - p.PIN_HEX_ACROSS_FLATS, 3),
            "dovetail_per_side": p.DOVETAIL_CLEARANCE,
        },
        "status": "digital-only; print and test coupons on production printer",
    }
    (args.out / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
