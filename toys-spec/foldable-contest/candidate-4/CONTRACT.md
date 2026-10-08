# Daybreak

A desk toy that tells one story: night falls when you close it, and the sun
comes up when you open it. Closed, Daybreak is a single thin slab standing on
a low spine, its cover engraved with a crescent moon and stars. Open it like a
book and the two leaves fold out flat into a wide dawn landscape: a cabin on
the left hill, a tree on the right hill, and a half sun rising out of the
crease between them. Anyone can say what just happened (the sun came up over
the valley) and what happens next (close it and it is night again).

Inventor: `trend-lab`, designing as the Storyteller: every trade-off goes to
the reading of the before-and-after.

## Trend Hook

The one seam. Closed, the toy is one 15 mm slab standing on its spine with a
single vertical seam down its middle; open, that seam parts book-style into a
landscape 175 mm wide, more than eleven times the slab's thickness, and the
sun rises out of the crease. A small slab becoming a big flat spread, with the
hinge hidden in the spine, is the fold; nothing else on the toy borrows from
any phone or its maker.

## Signature Motion

The player opens either leaf like a book. Both leaves turn together, each 90
degrees about its own hinge pin in the spine, because a geared hub on each
leaf meshes with opposite faces of one double-sided rack between them. Two
counter-turning gears push a rack the same way, so the rack, and the half sun
on it, rises 22 mm out of the spine as the leaves open, and sinks back out of
sight as they close. Opening one leaf opens the other; the sun is the proof
that they are synchronised. Closing it is the reverse: the leaves meet at the
seam and the sun drops into the spine.

## Unique geometries

| Geometry | Count | Role |
|---|---|---|
| `spine` | 1 | Base and hinge housing; hides the sun when closed |
| `leaf-left` | 1 | Left leaf: dawn hill with a cabin; moon on its cover |
| `leaf-right` | 1 | Right leaf: dawn hill with a tree; stars on its cover |
| `sun-rack` | 1 | Half sun on a double-sided rack: the Focal Component |
| `hinge-pin` | 2 | Hinge pin for each leaf |

**Focal Component: the sun.** The half sun is the focal point in the Display
Pose. It costs the leaves their height: the landscape on them is low relief,
at most 1.0 mm proud, so that the closed leaves can meet at the seam and the
sun has nothing standing in front of it.

## Frame and coordinates

Assembly coordinates in millimetres: X left to right across the spread, Y
front (-Y) to back, Z up from the desk. The spine sits centred on X = 0,
Y = 0. Release frames the toy at 35 degrees azimuth, 22 degrees elevation
against `#f5f0e6`, in the Display Pose, with the sun at the centre of the
frame.

**Display Pose: open.** Both leaves flat, each turned 90 degrees from closed,
their landscape faces up; the sun fully risen. Envelope 175 x 50 x 51 mm.

**Closed pose.** Both leaves upright, landscape faces meeting at the seam with
a 1.0 mm gap between their relief; the sun's top 1 mm below the spine's top
deck, out of sight.

## Per-geometry spec

**Spine.** A box 66 (X) x 50 (Y) x 30 (Z), walls 2.5 mm, floor 2.0 mm,
standing on its bottom face. From front to back: a front wall (Y -25 to
-22.5); a sun bay (Y -22.5 to -16) whose top deck carries one sun slot 38 x 5
mm centred on X = 0 over Y -21.5 to -16.5; an inner cheek wall (Y -16 to -13.5)
with a central slot 10 mm wide and 26 mm tall from the floor for the sun's web;
a hub bay (Y -13.5 to 22.5), open at the top between X -33 and 33 except a
2.5 mm rim; and a back wall (Y 22.5 to 25). Two hinge pin holes, Ø3.9 press fit,
run along Y through the cheek wall and back wall at X = -17.5 and X = 17.5,
Z = 26, each printed as a teardrop with its point up. The spine's outer faces
are plain, with a 1.0 mm chamfer on every top edge.

**Leaf (left and right, mirror images in layout, different in relief).** Each
leaf is one part: a hub, a gear sector, an arm and a plate. In the leaf's own
closed-pose frame (left leaf; the right leaf mirrors X):

- Hub: Ø10 cylinder along Y on the hinge axis, Y -13 to 22, bore Ø4.4.
- Gear sector: module 1, pitch radius 14 (a 28-tooth gear), 9 teeth over 115
  degrees, from pointing at the rack to pointing straight down, plus one tooth
  of margin; face width 8 mm at Y 0 to 8.
- Arm: 6 mm thick in X, full plate depth, joining the hub to the plate's foot.
- Plate: 60 (along the leaf) x 50 (Y) x 6.0 thick, its landscape face 16 mm
  from the hinge axis. Closed, the left plate spans X -7.5 to -1.5, Z 36 to
  96; open, it lies flat at Z 36 to 42, X -87.5 to -27.5.
- Landscape face (inner when closed, up when open): a raised hill band 1.0 mm
  proud running the plate's length, its top a smooth hill line, so the two
  leaves' hill lines meet at the same height across the crease; on the left
  leaf a raised cabin 14 mm wide with a pitched roof, a chimney and one
  engraved square window 3 mm across; on the right leaf a raised tree 18 mm
  tall, a round crown on a 3 mm trunk.
- Cover face (outer when closed, underside when open): on the left leaf an
  engraved crescent moon 16 mm tall; on the right leaf five engraved
  five-point stars, each 6 mm across. Engraving 0.6 mm deep.
- Print stance: on the leaf's back end face (Y +25), all relief undersides
  chamfered 45 degrees in that stance.

**Sun-rack.** One part, an L in side view, printed on its bottom face. A
base web 8 wide (X -4 to 4), Y -21 to 8, 4.0 tall; at its front a neck 8 wide
rising 4 mm to a half sun, radius 18 (36 across), 4.0 thick (Y -21 to -17),
flat edge down, with nine engraved rays fanning from a centre disc Ø12; at its
back the rack, a bar 7.0 mm between pitch lines (X -3.5 to 3.5), Y 0 to 8,
26 mm tall, with module 1 teeth along both X faces over its full height.
Closed, its bottom face sits 1.0 mm above the spine floor: the web at Z 3 to
7, the sun's flat edge at Z 11, its top at Z 29. Open, everything is 22.0 mm
higher: the sun's flat edge at Z 33, its top at Z 51.

**Hinge pin.** A plain Ø4.0 rod, 41 mm long, printed standing on one end,
with a 0.5 mm chamfer at each end.

## Joints

- Each hinge pin is pressed into the spine's Ø3.9 holes in the cheek and
  back walls at X = ±17.5, Z = 26, and passes through its leaf's Ø4.4 hub
  bore (0.2 mm radial clearance). Each hub sits between the cheek wall and the
  back wall with 0.5 mm end clearance at each end.
- Each leaf's gear sector meshes with one face of the rack: pitch circle
  radius 14 about X = ±17.5, Z = 26, tangent to the rack's pitch line at
  X = ±3.5. Backlash 0.2 mm.
- The sun-rack's web slides in the cheek wall's 10 mm slot with 1.0 mm
  clearance each side; the sun slides through the deck's 38 x 5 slot with
  1.0 mm clearance on every side.

## Motion and fit

- Each leaf turns 90 degrees about its hinge pin: the left leaf -90 degrees
  about +Y (its top moves to -X), the right leaf +90 degrees.
- The rack rises 22.0 mm over the full 90 degrees (14 x pi / 2), so the two
  leaves always stand at the same angle.
- Stops: closed, the leaves' relief meets with a 1.0 mm gap, and the plates
  stop on each other's relief-free borders; open, the web's top face stops
  against the underside of the cheek wall slot's top, 26 mm above the floor.
- Assembled, not printed in place: drop the sun-rack in, lay each leaf's hub
  in its bay meshing the rack with both leaves closed, then press each pin in
  from the back.

## Print and handling

Workshop prints at a 0.4 mm nozzle; every part prints without support in the
stance named above. Every point, chisel, keel and V underside ends in a flat
land at least 0.8 mm across (one print minimum at a 0.4 mm nozzle). A drawn
detail under the print minimums is enlarged to the minimum; when the enlarged
detail does not fit its spot, it is left out, and this contract names it.
Nothing is left out in this draft; the rays on the sun and the stars are
sized above the minimums. Nothing load-bearing is under 3 mm: the arms and
plates are 6 mm, the rack 7 mm, the pins 4 mm. A drop lands on the spine or a
plate edge; the pins are the first parts to come loose, and they press back
in.

```design-contract
{
  "schema_version": 4,
  "title": "Daybreak",
  "inventor": "trend-lab",
  "envelope_mm": [175, 50, 51],
  "references": [
    {"file": "ref-01-daybreak.png", "shows": "assembly", "camera": [35, 22]},
    {"file": "ref-02-spine.png", "shows": "geometry:spine", "camera": [-60, 30]},
    {"file": "ref-03-leaf-left.png", "shows": "geometry:leaf-left", "camera": [-60, 45]},
    {"file": "ref-04-leaf-right.png", "shows": "geometry:leaf-right", "camera": [-120, 45]},
    {"file": "ref-05-sun-rack.png", "shows": "geometry:sun-rack", "camera": [-60, 15]},
    {"file": "ref-06-hinge-pin.png", "shows": "geometry:hinge-pin", "camera": [-90, 0]}
  ],
  "geometries": [
    {"id": "spine", "name": "Spine", "count": 1, "extents_mm": [66, 50, 30], "wall_min_mm": 2.0},
    {"id": "leaf-left", "name": "Left leaf (cabin, moon)", "count": 1, "extents_mm": [22, 50, 85], "wall_min_mm": 3.0},
    {"id": "leaf-right", "name": "Right leaf (tree, stars)", "count": 1, "extents_mm": [22, 50, 85], "wall_min_mm": 3.0},
    {"id": "sun-rack", "name": "Half sun on its rack", "count": 1, "extents_mm": [36, 29, 26], "wall_min_mm": 3.0},
    {"id": "hinge-pin", "name": "Hinge pin", "count": 2, "extents_mm": [4, 4, 41], "wall_min_mm": 4.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly", "text": "In the Display Pose both leaves lie flat with their landscape faces up and the half sun stands fully risen between them, its flat edge above the spine's top deck."},
    {"id": "R02", "scope": "assembly", "text": "In the closed pose the two leaves stand upright face to face as one 15 mm slab above the spine with a single vertical seam, and no part of the sun shows above the deck."},
    {"id": "R03", "scope": "assembly", "text": "Turning either leaf turns the other by the same angle, and over 90 degrees the sun rises 22 mm."},
    {"id": "R04", "scope": "assembly", "text": "The sun is the focal point at 35 degrees azimuth, 22 degrees elevation."},
    {"id": "R05", "scope": "assembly", "text": "The two leaves' hill lines meet at the same height across the crease, reading as one horizon."},
    {"id": "R06", "scope": "assembly", "text": "Open, the spread is 175 mm wide; closed, it is a 15 mm slab: the open spread is more than eleven times the closed slab's thickness."},
    {"id": "R07", "scope": "geometry:spine", "text": "The spine's outer faces are plain, with a 1.0 mm chamfer on every top edge, and its deck carries one 38 x 5 mm sun slot centred at the front."},
    {"id": "R08", "scope": "geometry:leaf-left", "text": "The landscape face carries a raised hill band and a raised cabin 14 mm wide with a pitched roof, a chimney and one engraved square window 3 mm across."},
    {"id": "R09", "scope": "geometry:leaf-left", "text": "The cover face carries one engraved crescent moon 16 mm tall."},
    {"id": "R10", "scope": "geometry:leaf-left", "text": "The hub carries a 9-tooth module 1 gear sector of pitch radius 14 over 115 degrees, 8 mm wide."},
    {"id": "R11", "scope": "geometry:leaf-right", "text": "The landscape face carries a raised hill band and a raised tree 18 mm tall, a round crown on a 3 mm trunk."},
    {"id": "R12", "scope": "geometry:leaf-right", "text": "The cover face carries five engraved five-point stars, each 6 mm across."},
    {"id": "R13", "scope": "geometry:leaf-right", "text": "The hub carries a 9-tooth module 1 gear sector of pitch radius 14 over 115 degrees, 8 mm wide."},
    {"id": "R14", "scope": "geometry:sun-rack", "text": "A half sun of radius 18, flat edge down, with nine engraved rays fanning from a 12 mm centre disc."},
    {"id": "R15", "scope": "geometry:sun-rack", "text": "Behind the sun, a double-sided rack 7 mm between pitch lines and 26 mm tall carries module 1 teeth along both side faces."},
    {"id": "R16", "scope": "geometry:hinge-pin", "text": "A plain round rod with a 0.5 mm chamfer at each end."}
  ],
  "interfaces": [
    {"id": "left-hinge", "kind": "coupled", "components": ["leaf-left", "hinge-pin#1", "spine"],
     "text": "Hinge pin 1 is pressed into Ø3.9 holes in the spine's cheek wall (Y -16 to -13.5) and back wall (Y 22.5 to 25) at X -17.5, Z 26. The left leaf's Ø10 hub, Y -13 to 22 with a Ø4.4 bore, turns on the pin between those walls with 0.5 mm end clearance; the spine's hub bay keeps the hub and sector clear over the full 90 degrees.",
     "yielding": "leaf-left",
     "poses": {"steps": 10, "movers": [
       {"component": "leaf-left", "rotation": {"axis_point": [-17.5, 0, 26], "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": -90}}]}},
    {"id": "right-hinge", "kind": "coupled", "components": ["leaf-right", "hinge-pin#2", "spine"],
     "text": "Hinge pin 2 is pressed into Ø3.9 holes in the spine's cheek wall and back wall at X 17.5, Z 26. The right leaf's Ø10 hub, Y -13 to 22 with a Ø4.4 bore, turns on the pin between those walls with 0.5 mm end clearance; the spine's hub bay keeps the hub and sector clear over the full 90 degrees.",
     "yielding": "leaf-right",
     "poses": {"steps": 10, "movers": [
       {"component": "leaf-right", "rotation": {"axis_point": [17.5, 0, 26], "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "left-gear", "kind": "coupled", "components": ["leaf-left", "sun-rack"],
     "text": "The left leaf's 9-tooth module 1 sector, pitch radius 14 about X -17.5, Z 26, face Y 0 to 8, meshes with the rack's -X face, whose pitch line is X -3.5, with 0.2 mm backlash. Turning the leaf -90 degrees about +Y raises the sun-rack 22.0 mm.",
     "yielding": "sun-rack",
     "poses": {"steps": 10, "movers": [
       {"component": "leaf-left", "rotation": {"axis_point": [-17.5, 0, 26], "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": -90}},
       {"component": "sun-rack", "driven": true, "translation": {"vector": [0, 0, 22.0]}}]}},
    {"id": "right-gear", "kind": "coupled", "components": ["leaf-right", "sun-rack"],
     "text": "The right leaf's 9-tooth module 1 sector, pitch radius 14 about X 17.5, Z 26, face Y 0 to 8, meshes with the rack's +X face, whose pitch line is X 3.5, with 0.2 mm backlash. Turning the leaf +90 degrees about +Y raises the sun-rack 22.0 mm.",
     "yielding": "sun-rack",
     "poses": {"steps": 10, "movers": [
       {"component": "leaf-right", "rotation": {"axis_point": [17.5, 0, 26], "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": 90}},
       {"component": "sun-rack", "driven": true, "translation": {"vector": [0, 0, 22.0]}}]}},
    {"id": "sun-slide", "kind": "coupled", "components": ["sun-rack", "spine"],
     "text": "The sun-rack's 8 mm web slides up the spine's cheek-wall slot, 10 mm wide and 26 mm tall, and the half sun rises through the deck's 38 x 5 mm slot over Y -21.5 to -16.5, each with 1.0 mm clearance. Closed, the sun-rack's bottom face sits 1.0 mm above the spine floor; open, the web's top stops against the slot's top at Z 26.",
     "yielding": "sun-rack",
     "poses": {"steps": 10, "movers": [
       {"component": "sun-rack", "translation": {"vector": [0, 0, 22.0]}}]}},
    {"id": "seam", "kind": "separable", "components": ["leaf-left", "leaf-right"],
     "text": "Closed, the leaves' landscape faces meet at the seam: the left plate's face at X -1.5 and the right's at X 1.5, each leaf's relief at most 1.0 mm proud, leaving a 1.0 mm gap. The left leaf stays at X -0.25 or below in every pose; the right leaf stays clear of that box.",
     "envelope": {"inside": "leaf-left", "outside": "leaf-right", "shapes": [
       {"pose": "all", "box": {"min_mm": [-90, -26, 0], "max_mm": [-0.25, 26, 100]}}]}}
  ]
}
```
