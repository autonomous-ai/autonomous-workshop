"""Recipe: M3 screw-down electronics enclosure (80 x 60 x 30 mm).

Demonstrates composition of cadlib helpers:
  - hollow_box        — outer shell
  - add_lid_lip       — friction lip on the base
  - four_corner_points + add_screw_post — PCB / lid mounting
  - one custom cut    — side USB-C cable exit (no helper covers this yet)
  - lid_plate         — matching lid

``gen_step()`` returns the base + lid unioned into one shape so the preview
shows the assembled product. For a real multi-part print, build the two
halves as a ``cq.Assembly`` instead (see ``references/assembly.md``) so each
part exports its own STL.
"""

from __future__ import annotations

import cadquery as cq

from cadlib.enclosure import add_lid_lip, hollow_box, lid_plate
from cadlib.layout import four_corner_points
from cadlib.mounting import add_screw_post


class Params:
    length = 80.0
    width = 60.0
    height = 30.0
    wall = 2.0
    corner_radius = 4.0
    lid_thickness = 3.0
    lip_height = 3.0
    lip_clearance = 0.3
    screw_margin = 5.0
    screw_size = "M3"
    boss_height = 12.0
    usb_y_offset = 0.0
    usb_z_offset = 8.0     # cable centre above the floor
    usb_diameter = 9.0     # USB-C connector shell clearance


p = Params()

# 1. Base shell
base = hollow_box(
    length=p.length, width=p.width, height=p.height,
    wall=p.wall, corner_radius=p.corner_radius,
)

# 2. Lid lip
base = add_lid_lip(
    base,
    length=p.length, width=p.width, wall=p.wall,
    lip_height=p.lip_height, lip_clearance=p.lip_clearance,
)

# 3. Four screw-into-plastic mounting bosses inside the cavity
screw_pts = four_corner_points(
    length=p.length - 2 * p.wall,
    width=p.width - 2 * p.wall,
    margin=p.screw_margin,
)
base = add_screw_post(
    base,
    positions=screw_pts,
    screw_size=p.screw_size,
    boss_height=p.boss_height,
    hole_type="self_tap",
    open_face="<Z",                   # bosses grow UP from the floor (inside the box)
)

# 4. Custom USB-C side port (no helper fits a generic side cutout yet).
#    Cut a cylinder horizontally through the +X wall, oversized by 1 mm so
#    it pierces cleanly.
usb_cutter = (
    cq.Workplane("YZ")
    .circle(p.usb_diameter / 2)
    .extrude(p.wall + 2)
    .translate((p.length / 2 - p.wall / 2 - 0.5,
                p.usb_y_offset,
                p.usb_z_offset))
)
base = base.cut(usb_cutter)

# 5. Matching lid
lid = lid_plate(
    length=p.length, width=p.width, thickness=p.lid_thickness,
    corner_radius=p.corner_radius,
    lip_clearance=p.lip_clearance, wall=p.wall, lip_height=p.lip_height - 0.5,
)

# 6. Assembled view for the preview (base on bottom, lid floating above).
def gen_step():
    return base.union(lid.translate((0, 0, p.height + p.lid_thickness / 2 + 1.0)))
