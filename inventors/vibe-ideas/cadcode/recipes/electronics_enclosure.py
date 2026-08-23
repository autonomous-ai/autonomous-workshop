"""Recipe: two-part electronics enclosure (80 x 60 x 30 mm base envelope).

Demonstrates composition of cadlib helpers:
  - hollow_box        — exact outer shell
  - lid_with_skirt    — one lid-owned locating skirt inside the base cavity
  - grid_points       — exact centered PCB mounting pattern
  - side-wall helper  — 14 x 7 mm rounded USB-C through-opening
  - final proofs      — dimensions, throughness, fit, and assembly pose

``gen_step()`` returns a named ``cq.Assembly`` so the base and removable lid
stay separately printable. No preview gap or duplicate base rim changes the
requested fit or base envelope.
"""

from __future__ import annotations

import cadquery as cq

from cadlib.cutouts import add_rounded_side_wall_cutout, verify_side_wall_through_cut
from cadlib.enclosure import hollow_box, lid_with_skirt
from cadlib.layout import grid_points
from cadlib.tables import SCREW_TABLE
from cadlib.validation import verify_bbox


class Params:
    length = 80.0
    width = 60.0
    height = 30.0
    wall = 2.0
    corner_radius = 4.0
    lid_thickness = 3.0
    lid_lip_depth = 3.0
    lid_lip_wall = wall
    lip_clearance = 0.3
    screw_size = "M3"
    boss_height = 12.0
    pcb_pattern_length = 60.0
    pcb_pattern_width = 40.0
    pcb_hole_diameter = 3.2
    boolean_overshoot = 0.5
    usb_y_offset = 0.0
    usb_center_above_bottom = 12.0
    usb_width = 14.0
    usb_height = 7.0
    usb_corner_radius = 1.5


p = Params()

# 1. Base shell. The exact dimensions remain the final base envelope.
base = hollow_box(
    length=p.length,
    width=p.width,
    height=p.height,
    wall=p.wall,
    corner_radius=p.corner_radius,
)

# 2. Four through-hole PCB standoffs on the literal centered 60 x 40 pattern.
# Build them from the cavity floor instead of selecting the exterior <Z face.
screw_pts = grid_points(
    n_x=2,
    n_y=2,
    pitch_x=p.pcb_pattern_length,
    pitch_y=p.pcb_pattern_width,
)
screw = SCREW_TABLE[p.screw_size]
boss_od = 2 * screw["clearance"] + 4.0
cavity_floor_z = -p.height / 2 + p.wall
posts = (
    cq.Workplane("XY")
    .pushPoints(screw_pts)
    .circle(boss_od / 2)
    .extrude(p.boss_height)
    .translate((0, 0, cavity_floor_z))
)
pilot_cuts = (
    cq.Workplane("XY")
    .pushPoints(screw_pts)
    .circle(p.pcb_hole_diameter / 2)
    .extrude(p.boss_height + p.boolean_overshoot)
    .translate((0, 0, cavity_floor_z))
)
base = base.union(posts).cut(pilot_cuts)

# 3. USB-C side opening. The helper overcuts both wall boundaries, then proves
# the requested footprint on the actual final solid.
usb_center_z = -p.height / 2 + p.usb_center_above_bottom
usb_center = (p.length / 2, p.usb_y_offset, usb_center_z)
base = add_rounded_side_wall_cutout(
    base,
    side="+X",
    center=usb_center,
    width=p.usb_width,
    height=p.usb_height,
    wall_thickness=p.wall,
    corner_radius=p.usb_corner_radius,
)
usb_cutout_proof = verify_side_wall_through_cut(
    base,
    side="+X",
    center=usb_center,
    width=p.usb_width,
    height=p.usb_height,
    wall_thickness=p.wall,
)

# This proof stays in the project for later EDIT/REMIX turns. Any new feature
# that accidentally grows or shifts the requested final base envelope fails the
# rebuild before it can replace the last green artifact family.
base_extent_proof = verify_bbox(
    shape=base,
    expected_size=(p.length, p.width, p.height),
    expected_min=(-p.length / 2, -p.width / 2, -p.height / 2),
    expected_max=(p.length / 2, p.width / 2, p.height / 2),
    label="base",
)

# 4. One lid-owned annular skirt. Clearance is lateral only; the requested
# engagement depth remains exactly lid_lip_depth.
lid = lid_with_skirt(
    length=p.length,
    width=p.width,
    thickness=p.lid_thickness,
    corner_radius=p.corner_radius,
    lip_clearance=p.lip_clearance,
    wall=p.wall,
    lip_height=p.lid_lip_depth,
    lip_wall=p.lid_lip_wall,
)


def assembly(p: Params) -> cq.Assembly:
    """Seat the lid plate underside on the base rim without a fake gap."""
    lid_z = p.height / 2 + p.lid_thickness / 2
    result = cq.Assembly()
    result.add(base, name="base", color=cq.Color(0.80, 0.82, 0.85))
    result.add(
        lid,
        name="lid",
        loc=cq.Location((0, 0, lid_z)),
        color=cq.Color(0.30, 0.55, 0.90),
    )
    return result


def gen_step():
    return assembly(p)
