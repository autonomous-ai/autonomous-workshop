"""tide_pot: a deep blind drum for the setup shake-and-blind-draw, with an
open scalloped tray moulded around its foot holding the loose spine supply.
"""
import math

import cadquery as cq

import params as p


def build_tide_pot() -> cq.Workplane:
    tray_r = p.POT_TRAY_D / 2.0
    scallop_r = (2 * math.pi * tray_r) / (2 * p.POT_N_SCALLOPS)
    scallop_center_r = tray_r - scallop_r * 0.55

    tray = None
    for i in range(p.POT_N_SCALLOPS):
        a = i * 360.0 / p.POT_N_SCALLOPS
        petal = (
            cq.Workplane("XY")
            .circle(scallop_r)
            .extrude(p.POT_TRAY_H)
            .translate((scallop_center_r * math.cos(math.radians(a)),
                        scallop_center_r * math.sin(math.radians(a)), 0))
        )
        tray = petal if tray is None else tray.union(petal)
    core = cq.Workplane("XY").circle(tray_r * 0.7).extrude(p.POT_TRAY_H)
    tray = tray.union(core)

    drum_outer = (
        cq.Workplane("XY").circle(p.POT_DRUM_D / 2.0).extrude(p.POT_DRUM_H)
    )
    drum_inner = (
        cq.Workplane("XY").circle(p.POT_DRUM_D / 2.0 - p.POT_WALL)
        .extrude(p.POT_DRUM_H - p.POT_WALL + 1.0)
        .translate((0, 0, p.POT_WALL))
    )
    drum = drum_outer.cut(drum_inner)

    return tray.union(drum)
