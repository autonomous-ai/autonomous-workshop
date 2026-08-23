"""Recipe: D10x3 magnetic-snap lid box (60 x 60 x 25 mm).

Lid clicks into base by neodymium magnets at the four corners — no screws.

Helpers composed:
  - hollow_box       — base shell
  - lid_plate        — flat lid (no lip; magnets do the alignment)
  - four_corner_points + add_magnet_pocket — corner magnets, both halves
"""

from __future__ import annotations

from cadlib.cutouts import add_magnet_pocket
from cadlib.enclosure import hollow_box, lid_plate
from cadlib.layout import four_corner_points


class Params:
    length = 60.0
    width = 60.0
    height = 25.0
    wall = 2.0
    corner_radius = 3.0
    lid_thickness = 3.0
    magnet_size = "10x3"
    magnet_margin = 8.0     # in from corner (mm)
    top_wall = 0.6          # plastic between magnet face and outside


p = Params()

# 1. Base shell
base = hollow_box(
    length=p.length, width=p.width, height=p.height,
    wall=p.wall, corner_radius=p.corner_radius,
)

# 2. Four magnet pockets sunk into the TOP RIM of the base (opening at +Z).
magnet_pts = four_corner_points(
    length=p.length, width=p.width, margin=p.magnet_margin,
)
base = add_magnet_pocket(
    base, positions=magnet_pts,
    magnet_size=p.magnet_size,
    fit_type="slip",
    top_wall=p.top_wall,
    open_face=">Z",
)

# 3. Flat lid (no lip — magnets handle alignment)
lid = lid_plate(
    length=p.length, width=p.width, thickness=p.lid_thickness,
    corner_radius=p.corner_radius,
    lip_clearance=0.0, wall=p.wall, lip_height=0.001,    # lip_plate needs > 0; effectively flat
)

# 4. Magnet pockets on the lid, opening DOWN (-Z) so the magnets face the
#    base's magnets. CRITICAL: install lid magnets with the OPPOSITE
#    polarity from the base magnets (Sharpie-dot before pressing in).
lid = add_magnet_pocket(
    lid, positions=magnet_pts,
    magnet_size=p.magnet_size,
    fit_type="slip",
    top_wall=p.top_wall,
    open_face="<Z",
)

# 5. Assembled view: lid floats above the base
def gen_step():
    return base.union(lid.translate((0, 0, p.height + p.lid_thickness / 2 + 0.5)))
