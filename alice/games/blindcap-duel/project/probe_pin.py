"""probe_pin_p<owner> -- hex-shafted, knurled disc head, blunt tapered tip.
One or two holes through the head permanently identify the probing player.
The only
moving part in the box (slides into loam_tile). Total length PIN_LEN,
stacked tip-up here (z=0 at the tip) so callers can seat it by the tip.
"""
import math

import cadquery as cq

import params as p


def _hex_profile(across_flats):
    r = across_flats / (2.0 * math.cos(math.radians(30.0)))
    return cq.Workplane("XY").polygon(6, 2 * r)


def build_probe_pin(owner_marks=1):
    if owner_marks not in (1, 2):
        raise ValueError("owner_marks must be 1 or 2")
    shaft_r = p.PIN_HEX_ACROSS_FLATS / 2.0
    tip = (
        cq.Workplane("XY").circle(p.PIN_TIP_R)
        .workplane(offset=p.PIN_TIP_H).circle(shaft_r)
        .loft(ruled=True)
    )

    shaft = _hex_profile(p.PIN_HEX_ACROSS_FLATS).extrude(p.PIN_SHAFT_H).translate(
        (0, 0, p.PIN_TIP_H)
    )

    head_z0 = p.PIN_TIP_H + p.PIN_SHAFT_H
    head = cq.Workplane("XY").circle(p.PIN_HEAD_D / 2.0).extrude(p.PIN_HEAD_T).translate(
        (0, 0, head_z0)
    )
    # knurl relief: shallow vertical ridges around the disc's rim
    n_knurl = 24
    ridge = cq.Workplane("XY").box(
        p.PIN_KNURL_RELIEF * 2, 1.2, p.PIN_HEAD_T, centered=(False, True, False)
    ).translate((p.PIN_HEAD_D / 2.0 - p.PIN_KNURL_RELIEF, 0, head_z0))
    for i in range(n_knurl):
        ang = 360.0 * i / n_knurl
        head = head.union(ridge.rotate((0, 0, 0), (0, 0, 1), ang))

    pin = shaft.union(head).union(tip)

    owner_angles = (90.0,) if owner_marks == 1 else (60.0, 120.0)
    owner_hole = (
        cq.Workplane("XY")
        .circle(p.PIN_OWNER_HOLE_D / 2.0)
        .extrude(p.PIN_HEAD_T + 0.4)
        .translate((p.PIN_OWNER_HOLE_R, 0, head_z0))
    )
    for angle in owner_angles:
        pin = pin.cut(owner_hole.rotate((0, 0, 0), (0, 0, 1), angle))
    return pin
