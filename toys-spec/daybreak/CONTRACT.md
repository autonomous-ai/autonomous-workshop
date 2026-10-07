# Daybreak

A desk toy that tells one story: night falls when you close it, and the sun
comes up when you open it. Closed, Daybreak is a single thin slab standing on
its spine, its cover engraved with a crescent moon and stars. Open it like a
book and the two leaves fold out flat onto the spine into a wide dawn
landscape: a cabin on the left hill, a tree on the right hill, and a half sun
risen out of the crease between them. Anyone can say what just happened (the
sun came up over the valley) and what happens next (close it and it is night
again).

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
Pose: the tallest thing on the toy, 15 mm above the leaves, in front of
everything else. It costs the leaves their height: the landscape on them is
low relief, at most 1.0 mm proud, so that the closed leaves can meet at the
seam and the sun has nothing standing in front of it.

## Frame and coordinates

Assembly coordinates in millimetres: X left to right across the spread, Y
front (-Y) to back, Z up from the desk. The spine sits centred on X = 0; its
front face is at Y -25. Release frames the toy in the Display Pose against
`#f5f0e6` from the front-right, the assembly reference's camera: 15 degrees
right of straight-on front, 30 degrees above level (`render_review` camera
[-75, 30]), with the sun at the centre of the frame.

**Display Pose: open.** Both leaves flat on the spine's top, each turned 90
degrees from closed, their landscape faces up; the sun fully risen. Envelope
175 x 53.5 x 64.5 mm.

**Closed pose.** Both leaves upright, landscape faces meeting at the seam with
a 1.0 mm gap between their relief; the sun's top 1.0 mm below the spine's top,
out of sight. Envelope 66 x 53.5 x 102.5 mm.

## Palette

One filament colour per geometry:

| Geometry | Colour |
|---|---|
| `spine` | matte slate blue |
| `leaf-left`, `leaf-right` | matte sage green |
| `sun-rack` | matte warm yellow-orange |
| `hinge-pin` | matte slate blue |

## Per-geometry spec

**Spine.** An open-topped box 66 (X) x 53.5 (Y, -25 to 28.5) x 43.5 (Z),
walls and floor 3.0 mm, standing on its bottom face. From front to back: a
front wall (Y -25 to -22); a sun bay (Y -22 to -16) whose top is a 3.0 mm
deck (Z 40.5 to 43.5) only outside X -19 to 19, leaving one sun slot 38 x 6 mm
over the whole bay; an inner cheek wall (Y -16 to -13), cut by a 10 mm wide
slot (X -5 to 5) from the floor to the top; a hub bay (Y -13 to 25.5), open
at the top between the side walls (X -30 to 30); and a back wall (Y 25.5 to
28.5). Two hinge pin holes, Ø3.9 press fit, run along Y through the cheek wall
and the back wall at X = -18 and X = 18, Z = 33, each printed as a teardrop
with its point up. The spine's outer faces are plain, with a 1.0 mm chamfer on
every top outer edge.

**Leaf (left and right, mirror images in layout, different in relief).** Each
leaf is one part: a hub, a gear sector with its skirt, an arm and a plate.
Given in the left leaf's closed pose; the right leaf mirrors X:

- Hub: Ø11 cylinder along Y on the hinge axis (X -18, Z 33), Y -12.5 to 25,
  bore Ø4.4.
- Gear sector: module 2, pressure angle 20 degrees, pitch radius 14 (a
  14-tooth gear), 6 teeth over 154 degrees: from 32 degrees above pointing at
  the rack to 32 degrees past pointing straight down; face width 8 mm at
  Y -12 to -4, right behind the sun.
- Skirt: a 45-degree cone behind the sector over the same 154 degrees, from
  the sector's 16 mm tip radius at Y -4 down to the hub at Y 6.5, so the
  sector prints without support.
- Plate: 58.5 (along the leaf) x 50 (Y -25 to 25) x 6.0 thick. Closed, the
  left plate spans X -7.5 to -1.5, Z 44 to 102.5; open, it lies flat on the
  spine's top at Z 43.5 to 49.5, X -87.5 to -29.
- Arm: the convex hull, in section across Y, of the hub and the inner half of
  the plate's foot (closed: X -7.5 to -4.5 at Z 44 to 44.5), running Y -12.5
  to 25. Open, it rises from the hub to the plate's inner end inside the hub
  bay.
- Landscape face (inner when closed, up when open), relief 1.0 mm proud with
  its undersides chamfered 45 degrees in the print stance. Positions in the
  open pose: a raised hill band from the front edge back to a smooth hill line
  that runs at Y 0 at the crease end (X ±29), crests at Y 4 at X ±58 and falls
  to Y -4 at the outer end, so the two leaves' hill lines meet at the same
  height across the crease. On the left leaf a raised cabin 14 mm wide
  (X -65 to -51) standing on the hill line, 14 mm to its roof ridge, with a
  pitched roof, a 3 mm chimney and one engraved square window 3 mm across. On
  the right leaf a raised tree 18 mm tall standing on the hill line at X 58,
  a Ø12 round crown on a 3 mm trunk.
- Cover face (outer when closed, underside when open): on the left leaf an
  engraved crescent moon 16 mm tall; on the right leaf five engraved
  five-point stars, each 8 mm across. Engraving 0.6 mm deep.
- Print stance: on the leaf's back end face (Y +25), where the plate, arm and
  hub all end flush; the hinge axis stands vertical.

**Sun-rack.** One part, printed on the sun's front face (Y -21), in the
closed pose: a half sun, radius 18 (36 across), 4.0 thick (Y -21 to -17),
flat edge down at Z 24.5, top at Z 42.5; a stem plate 8 wide (X -4 to 4),
Y -21 to -12.5, Z 3 to 40, which carries the sun; and at its back the rack,
Y -12.5 to -4.5, Z 3 to 40, module 2, 8.0 mm between pitch lines (X -4 to 4),
with teeth along both X faces over its full height. The teeth start from the
stem plate's faces with a 45-degree chamfer over their first 2 mm in Y, so
the rack prints without support. The sun's front face carries an
engraved ring 1.0 mm wide round a Ø12 centre disc at the middle of the flat
edge, and nine engraved rays 1.5 mm wide from radius 9 to radius 16, 20
degrees apart; engraving 0.6 mm deep. Closed, its bottom face rests on the
spine floor (Z 3). Open, everything is 22.0 mm higher: the sun's flat edge at
Z 46.5, 3 mm above the spine's top, its top at Z 64.5. The rack's top, at
Z 62.3, sits 8 mm behind the sun: seen from above the front, its top teeth
show just behind the sun's top edge.

**Hinge pin.** A plain Ø4.0 rod, 44 mm long (Y -16 to 28), printed standing
on one end, with a 0.5 mm chamfer at each end.

## Joints

- Each hinge pin is pressed into the spine's Ø3.9 holes in the cheek wall and
  back wall at X = ±18, Z = 33, and passes through its leaf's Ø4.4 hub bore
  (0.2 mm radial clearance). Each hub sits between the cheek wall and the back
  wall with 0.5 mm end clearance at each end.
- Each leaf's gear sector meshes with one face of the rack: pitch circle
  radius 14 about X = ±18, Z = 33, tangent to the rack's pitch line at
  X = ±4. Backlash 0.2 mm.
- The sun-rack's stem plate slides in the cheek wall's 10 mm slot with
  1.0 mm clearance each side; the sun slides through the 38 x 6 sun slot with
  1.0 mm clearance on every side.

## Motion and fit

- Each leaf turns 90 degrees about its hinge pin: the left leaf -90 degrees
  about +Y (its top moves to -X), the right leaf +90 degrees.
- The rack rises 22.0 mm over the full 90 degrees (14 x pi / 2), so the two
  leaves always stand at the same angle.
- Stops: closed, the sun-rack's bottom face rests on the spine floor and the
  leaves' relief keeps a 1.0 mm gap at the seam; open, each leaf's cover face
  rests on the spine's top faces (side wall, front wall and deck) at Z 43.5.
- Clearances through the travel: at least 0.5 mm between every pair of parts
  except at those two stops.
- Assembled, not printed in place: drop the sun-rack in from above, lay each
  leaf's hub in the hub bay meshing the rack with both leaves closed, then
  press each pin in from the back.
- Motion check plan: `--check-motion true` on the wish and on every resume
  and correction; one sweep of the full 90 degree travel in at most 10 steps,
  each leaf against only the spine, the sun-rack and the other leaf; one
  one-tooth sweep per mesh (left-gear, right-gear) in at most 10 steps with
  no obstacles. A skipped, killed or timed-out sweep fails the motion
  requirement, never passes it.

## Print and handling

Workshop prints at a 0.4 mm nozzle; every part prints without support in the
stance named above. Every point, chisel, keel and V underside ends in a flat
land at least 0.8 mm across (one print minimum at a 0.4 mm nozzle). A drawn
detail under the print minimums is enlarged to the minimum; when the enlarged
detail does not fit its spot, it is left out, and this contract names it.
Nothing is left out: the rays, the ring, the window, the moon and the stars
are cut wider and deeper than the minimums, and the horns of the moon and the
points of the stars end in cuts at least 0.5 mm wide. No wall, arm, stem or
tooth is under 3 mm: the spine walls are 3.0, the plates 6, the hub wall 3.3,
the rack core 3.0, the teeth 3.1 thick at the pitch line, the pins 4. A drop
lands on the spine or a plate edge; the pins are the first parts to come
loose, and they press back in.

```design-contract
{
  "schema_version": 4,
  "title": "Daybreak",
  "inventor": "trend-lab",
  "envelope_mm": [175, 53.5, 64.5],
  "references": [
    {"file": "ref-01-daybreak.png", "shows": "assembly", "camera": [-75, 30]},
    {"file": "ref-02-spine.png", "shows": "geometry:spine", "camera": [-75, 30]},
    {"file": "ref-03-leaf-left.png", "shows": "geometry:leaf-left", "camera": [-75, 45]},
    {"file": "ref-04-leaf-right.png", "shows": "geometry:leaf-right", "camera": [-105, 45]},
    {"file": "ref-05-sun-rack.png", "shows": "geometry:sun-rack", "camera": [-90, 0]},
    {"file": "ref-06-hinge-pin.png", "shows": "geometry:hinge-pin", "camera": [0, 15]}
  ],
  "geometries": [
    {"id": "spine", "name": "Spine", "count": 1, "extents_mm": [66, 53.5, 43.5], "wall_min_mm": 3.0},
    {"id": "leaf-left", "name": "Left leaf (cabin, moon)", "count": 1, "extents_mm": [26, 50, 85.5], "wall_min_mm": 3.0},
    {"id": "leaf-right", "name": "Right leaf (tree, stars)", "count": 1, "extents_mm": [26, 50, 85.5], "wall_min_mm": 3.0},
    {"id": "sun-rack", "name": "Half sun on its rack", "count": 1, "extents_mm": [36, 16.5, 39.5], "wall_min_mm": 3.0},
    {"id": "hinge-pin", "name": "Hinge pin", "count": 2, "extents_mm": [4, 4, 44], "wall_min_mm": 4.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly", "text": "In the Display Pose both leaves lie flat on the spine's top with their landscape faces up, and the half sun stands fully risen between them, its flat edge 3 mm above the spine's top and its top 15 mm above the leaves."},
    {"id": "R02", "scope": "assembly", "text": "In the closed pose the two leaves stand upright face to face as one 15 mm slab above the spine with a single vertical seam, and no part of the sun shows above the spine's top."},
    {"id": "R03", "scope": "assembly", "text": "Turning either leaf turns the other by the same angle, and over 90 degrees the sun rises 22 mm, with at least 0.5 mm between parts through the travel except at the two stops. Checked with --check-motion true: one full-travel sweep and one one-tooth sweep per mesh, each in at most 10 steps; a skipped, killed or timed-out sweep fails this requirement."},
    {"id": "R04", "scope": "assembly", "text": "From the assembly reference camera [-75, 30] the sun is the focal point: it is the tallest part and nothing stands in front of it."},
    {"id": "R05", "scope": "assembly", "text": "The two leaves' hill lines meet at the same height across the crease, reading as one horizon."},
    {"id": "R06", "scope": "assembly", "text": "Open, the spread is 175 mm wide; closed, it is a 15 mm slab: the open spread is more than eleven times the closed slab's thickness."},
    {"id": "R07", "scope": "assembly", "text": "Closed, the sun-rack rests on the spine floor; open, each leaf's cover face rests on the spine's top faces at Z 43.5."},
    {"id": "R08", "scope": "geometry:spine", "text": "The spine's outer faces are plain, with a 1.0 mm chamfer on every top outer edge; its top carries one 38 x 6 mm sun slot at the front, a 10 mm slot through the inner cheek wall from floor to top, and an open hub bay behind."},
    {"id": "R09", "scope": "geometry:spine", "text": "Two Ø3.9 teardrop hinge holes, point up, run through the cheek wall and the back wall at X -18 and X 18, Z 33; walls and floor are 3.0 mm."},
    {"id": "R10", "scope": "geometry:leaf-left", "text": "The landscape face carries a raised hill band and a raised cabin 14 mm wide with a pitched roof, a 3 mm chimney and one engraved square window 3 mm across, all 1.0 mm proud."},
    {"id": "R11", "scope": "geometry:leaf-left", "text": "The cover face carries one engraved crescent moon 16 mm tall, 0.6 mm deep."},
    {"id": "R12", "scope": "geometry:leaf-left", "text": "A 58.5 x 50 x 6 plate joined by an arm to a Ø11 hub with a Ø4.4 bore; the hub carries a 6-tooth module 2 gear sector of pitch radius 14 over 154 degrees, 8 mm wide, over a 45-degree skirt."},
    {"id": "R13", "scope": "geometry:leaf-right", "text": "The landscape face carries a raised hill band and a raised tree 18 mm tall, a Ø12 round crown on a 3 mm trunk, all 1.0 mm proud."},
    {"id": "R14", "scope": "geometry:leaf-right", "text": "The cover face carries five engraved five-point stars, each 8 mm across, 0.6 mm deep."},
    {"id": "R15", "scope": "geometry:leaf-right", "text": "A 58.5 x 50 x 6 plate joined by an arm to a Ø11 hub with a Ø4.4 bore; the hub carries a 6-tooth module 2 gear sector of pitch radius 14 over 154 degrees, 8 mm wide, over a 45-degree skirt."},
    {"id": "R16", "scope": "geometry:sun-rack", "text": "A half sun of radius 18 and 4 mm thick, flat edge down, with an engraved ring round a 12 mm centre disc and nine engraved rays 1.5 mm wide."},
    {"id": "R17", "scope": "geometry:sun-rack", "text": "An 8 mm stem plate carries the sun; behind it a double-sided module 2 rack, 8 mm between pitch lines and 37 mm tall, carries teeth along both side faces."},
    {"id": "R18", "scope": "geometry:hinge-pin", "text": "A plain Ø4.0 round rod 44 mm long with a 0.5 mm chamfer at each end."}
  ],
  "interfaces": [
    {"id": "left-hinge", "kind": "coupled", "components": ["leaf-left", "hinge-pin#1", "spine"],
     "text": "Hinge pin 1 (Ø4.0 x 44, Y -16 to 28) is pressed into Ø3.9 teardrop holes in the spine's cheek wall (Y -16 to -13) and back wall (Y 25.5 to 28.5) at X -18, Z 33. The left leaf's Ø11 hub, Y -12.5 to 25 with a Ø4.4 bore, turns on the pin between those walls with 0.5 mm end clearance; the spine's hub bay keeps the hub, arm, sector and skirt at least 0.5 mm clear over the full 90 degrees. Open, the leaf's cover face rests on the spine's top faces at Z 43.5.",
     "yielding": "leaf-left",
     "poses": {"steps": 10, "movers": [
       {"component": "leaf-left", "rotation": {"axis_point": [-18, 0, 33], "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": -90}}]}},
    {"id": "right-hinge", "kind": "coupled", "components": ["leaf-right", "hinge-pin#2", "spine"],
     "text": "Hinge pin 2 (Ø4.0 x 44, Y -16 to 28) is pressed into Ø3.9 teardrop holes in the spine's cheek wall and back wall at X 18, Z 33. The right leaf's Ø11 hub, Y -12.5 to 25 with a Ø4.4 bore, turns on the pin between those walls with 0.5 mm end clearance; the spine's hub bay keeps the hub, arm, sector and skirt at least 0.5 mm clear over the full 90 degrees. Open, the leaf's cover face rests on the spine's top faces at Z 43.5.",
     "yielding": "leaf-right",
     "poses": {"steps": 10, "movers": [
       {"component": "leaf-right", "rotation": {"axis_point": [18, 0, 33], "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "left-gear", "kind": "coupled", "components": ["leaf-left", "sun-rack"],
     "text": "The left leaf's 6-tooth module 2 sector, pitch radius 14 about X -18, Z 33, face Y -12 to -4, meshes with the rack's -X face, whose pitch line is X -4, with 0.2 mm backlash. Turning the leaf -90 degrees about +Y raises the sun-rack 22.0 mm.",
     "yielding": "sun-rack",
     "poses": {"steps": 10, "movers": [
       {"component": "leaf-left", "rotation": {"axis_point": [-18, 0, 33], "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": -90}},
       {"component": "sun-rack", "driven": true, "translation": {"vector": [0, 0, 22.0]}}]}},
    {"id": "right-gear", "kind": "coupled", "components": ["leaf-right", "sun-rack"],
     "text": "The right leaf's 6-tooth module 2 sector, pitch radius 14 about X 18, Z 33, face Y -12 to -4, meshes with the rack's +X face, whose pitch line is X 4, with 0.2 mm backlash. Turning the leaf +90 degrees about +Y raises the sun-rack 22.0 mm.",
     "yielding": "sun-rack",
     "poses": {"steps": 10, "movers": [
       {"component": "leaf-right", "rotation": {"axis_point": [18, 0, 33], "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": 90}},
       {"component": "sun-rack", "driven": true, "translation": {"vector": [0, 0, 22.0]}}]}},
    {"id": "sun-slide", "kind": "coupled", "components": ["sun-rack", "spine"],
     "text": "The sun-rack's 8 mm stem plate slides up the spine's cheek-wall slot, 10 mm wide from floor to top, and the half sun rises through the 38 x 6 mm sun slot over Y -22 to -16, each with 1.0 mm clearance. Closed, the sun-rack's bottom face rests on the spine floor at Z 3; open, it is 22.0 mm higher.",
     "yielding": "sun-rack",
     "poses": {"steps": 10, "movers": [
       {"component": "sun-rack", "translation": {"vector": [0, 0, 22.0]}}]}},
    {"id": "seam", "kind": "separable", "components": ["leaf-left", "leaf-right"],
     "text": "Closed, the leaves' landscape faces meet at the seam: the left plate's face at X -1.5 and the right's at X 1.5, each leaf's relief at most 1.0 mm proud, leaving a 1.0 mm gap. The left leaf stays at X -0.25 or below in every pose; the right leaf stays clear of that box.",
     "envelope": {"inside": "leaf-left", "outside": "leaf-right", "shapes": [
       {"pose": "all", "box": {"min_mm": [-90, -26, 0], "max_mm": [-0.25, 26, 105]}}]}}
  ]
}
```
