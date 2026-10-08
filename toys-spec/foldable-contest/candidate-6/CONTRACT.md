# Trailfold

A rugged field-map book for the desk. Closed, it is a chunky upright slab
held between two treaded end blocks, the size of a pocket field guide. Lift
one grip tab and both leaves swing open together on a geared hinge until the
book lies flat as a terrain map twice as wide, its contour rings running
straight across a crease that is barely there. It looks ready for a trail:
tread lugs on the back of every leaf, a boot-sole tread on each end block,
big carry-handle slots, thick walls and raised corner guards.

Inspired by the first wave of book-style foldable phones (September 2026).
It carries no maker's name, logo, camera layout or product shape: no screen,
no buttons, no phone outline. It is a map, not a phone.

## Trend Hook

The saddle ring: one contour ring of the twin-peak terrain map that crosses
the hinge crease unbroken when the book lies open flat. The crease between
the two leaves is a 1.0 mm gap, and the ring's raised step meets itself
across it in line, so the eye reads one map, not two halves. Point at the
crease in the middle of the open map: that ring is the hook. A small slab
that becomes a big flat map is the fold; a crease that hides is the hinge.

## Signature Motion

What moves: the two leaves, each turning 90 degrees about its own hinge rod.
What drives it: a synchronised geared hinge. Each leaf's hinge edge carries a
toothed sector at both ends, and the left leaf's sectors mesh with the right
leaf's, so the leaves always turn in mirror. What the player does: hooks a
finger in one leaf's handle slot and lifts or lowers it; the other leaf follows on its own,
from the closed upright slab (both leaves vertical) to the open flat map (both
leaves lying on their tread lugs on the desk) and back. The chunky sector
teeth sit in plain view at both ends of the crease, so the player watches the
hinge do the work.

## Spec

### Unique geometries

- `leaf` (2 parts): the map leaf. The Focal Component: the two leaves together
  make the open map, and the map is what the toy is judged by. The cost: the
  end blocks stay plain chunky blocks with only a boot tread, so nothing
  competes with the map.
- `end-cheek` (2 parts): the treaded end block that holds both hinge rods.

Purchased: two steel dowel rods, diameter 4 mm, 125 mm long.

### Coordinates and Display Pose

X across the open book, Y along the hinge, Z up from the desk. The hinge rods
run along Y at X -7 and X +7, Z 9. `leaf#1` hinges on the X -7 rod, `leaf#2`
on the X +7 rod. Hinge angle 0 degrees is open flat; 90 degrees is closed
upright.

The Display Pose is open flat: both leaves at 0 degrees, lying on their tread
lugs on the desk, map faces up. Envelope in the Display Pose: 154 mm (X) by
130 mm (Y) by 22 mm (Z), the end cheeks being the tallest parts. Closed, the
book stands 79 mm tall.

### leaf

A plate 70 mm from the rod axis to the free edge, 100 mm long (Y), 8 mm thick,
centred on its rod axis, so when flat its map face is at Z 13 and its back
face at Z 5. Extents 78 x 100 x 17 mm: 8 mm of gear tip behind the rod axis and
70 mm of plate, 100 mm long, and from the lug soles to the sector tips.

- Hinge edge: a full-length round knuckle of radius 6.5 about the rod axis,
  with a 4.3 mm teardrop bore for the rod. The two knuckles leave a 1.0 mm
  crease between them when flat.
- Sector gears: module 1, 14 teeth on the full circle (pitch radius 7, tip
  radius 8), cut on the knuckle at Y 40 to 50 and Y -50 to -40, as a sector of
  5 teeth covering the 90 degree travel with one spare tooth at each end.
  Teeth are 10 mm wide. The two leaves are the same part turned 180 degrees
  about Z, so the sector teeth of `leaf#1` and `leaf#2` mesh at X 0.
- Map face: a twin-peak terrain relief of four stepped terraces, each
  0.5 mm high (2.0 mm in total), inside Y -38 to 38. One peak sits 24 mm from
  the rod axis at Y +20 on each leaf; because the leaves are the same part
  turned 180 degrees, the peaks land at (X -31, Y 20) and (X 31, Y -20) and
  the saddle between them crosses the crease at the map's centre. The
  saddle ring, the lowest terrace's edge round both peaks, meets the hinge
  edge at Y 6 and Y -6 on each leaf, so it continues in line across the
  crease.
- Back face: 5 mm tall chevron tread lugs, 6 rows of 4, each lug 8 mm wide
  with 4 mm gaps between lugs; the lug soles are the leaf's desk face when
  open.
- Free edge: a carry-handle slot, 30 x 10 mm with rounded ends, cut through
  the plate at the free edge's centre, its long side 6 mm in from the edge.
- Corner guards: all four plate corners are rounded to a 6 mm radius and
  carry raised L-shaped corner guards, 1 mm high and 2 mm wide.
- Wall minimum 3 mm.
- Print stance: lug soles on the bed. The knuckle's underside below the lug
  plane is a 45 degree chamfer, and the bore is a teardrop.

### end-cheek

A boot-shaped block 30 mm (X) by 14 mm (Y) by 22 mm (Z), top edges rounded to
a 5 mm radius. Its outer face carries three horizontal tread grooves, 2 mm
wide and 1 mm deep. Two rod holes on X -7 and X +7, Z 9: in `end-cheek#1` (at
Y -58) they run right through as 3.9 mm press holes; in `end-cheek#2` (at
Y +58) they are 3.9 mm blind press holes 10 mm deep from the inner face. The
inner faces stand at Y -51 and Y +51, 1.0 mm clear of the leaf ends. Wall
minimum 3 mm. Print stance: outer face on the bed, holes vertical.

### Joints

- Rod joints: each 4 mm rod is pressed through `end-cheek#1`, runs through a
  leaf's 4.3 mm teardrop bore (0.15 mm a side clearance, the leaf turns on
  it), and is pressed 10 mm into `end-cheek#2`: 14 + 1 + 100 + 1 + 9 = 125 mm.
  The rods are what tie the two cheeks together.
- Sector mesh: rod centres 14 mm apart, equal to the sum of the pitch radii;
  the leaves turn in mirror, ratio 1.

### Handling

Dropped closed, the rounded free edges and corner guards take the fall;
the 6 mm web outside each handle slot is 8 mm thick solid. The
rods are steel, the knuckles 6.5 mm round a 4.3 mm bore, so nothing
load-bearing is under 3 mm. The first part to wear is a sector tooth; the
spare teeth at each end stop it running off the mesh.

### Print

Workshop's 0.4 mm nozzle. Every point, chisel, keel and V underside ends in a
flat land at least 0.8 mm across (one print minimum at a 0.4 mm nozzle). A
drawn detail under the print minimums is enlarged to the minimum; when the
enlarged detail does not fit its spot, it is left out, and this contract
names it. The terrace steps are plain raised steps and carry no engraved
contour numbers or trail symbols.

### Fixed-frame plan

At 35 degrees azimuth and 22 degrees elevation against `#f5f0e6`, the open
map fills the frame, the crease runs front to back through its centre and the
saddle ring crossing it is the focal point; the near end cheek and its two
sector meshes sit in front.

### Motion plan

- `--check-motion true` on the wish and on every resume and correction;
- one sweep of the full 90 degree travel, at most 10 steps, against only the
  other leaf and the end cheeks;
- one one-tooth sweep of the sector mesh, at most 10 steps, with no
  obstacles;
- a skipped, killed or timed-out sweep fails the motion requirement, never
  passes it.

```design-contract
{
  "schema_version": 4,
  "title": "Trailfold",
  "inventor": "trend-lab",
  "envelope_mm": [154, 130, 22],
  "references": [
    {"file": "ref-01-trailfold.png", "shows": "assembly", "camera": [35, 22]},
    {"file": "ref-02-leaf.png", "shows": "geometry:leaf", "camera": [-60, 45]},
    {"file": "ref-03-end-cheek.png", "shows": "geometry:end-cheek", "camera": [-60, 15]}
  ],
  "geometries": [
    {"id": "leaf", "name": "Map leaf", "count": 2,
     "extents_mm": [78, 100, 17], "wall_min_mm": 3},
    {"id": "end-cheek", "name": "Treaded end cheek", "count": 2,
     "extents_mm": [30, 14, 22], "wall_min_mm": 3}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly",
     "text": "In the Display Pose both leaves lie open flat on their tread lugs, map faces up, with a 1.0 mm crease between the knuckles along the Y axis."},
    {"id": "R02", "scope": "assembly",
     "text": "The saddle ring, the lowest terrace's edge round both peaks, crosses the crease unbroken and in line at the map's centre."},
    {"id": "R03", "scope": "assembly",
     "text": "The two peaks stand at X -31, Y 20 and X 31, Y -20, the map being the same leaf turned 180 degrees about Z."},
    {"id": "R04", "scope": "assembly",
     "text": "Turning one leaf from 0 to 90 degrees turns the other leaf in mirror through the sector mesh, ending as an upright closed slab 79 mm tall; the motion sweep runs the full travel and a skipped, killed or timed-out sweep fails this requirement."},
    {"id": "R05", "scope": "assembly",
     "text": "Both sector meshes are visible at the two ends of the crease, between the leaf ends and the end cheeks."},
    {"id": "R06", "scope": "assembly",
     "text": "The toy carries no maker name, logo, screen, button or camera feature."},
    {"id": "R07", "scope": "geometry:leaf",
     "text": "The map face carries four stepped terraces, each 0.5 mm high, round one peak 24 mm from the rod axis at Y 20; the steps are plain and carry no engraved numbers or symbols."},
    {"id": "R08", "scope": "geometry:leaf",
     "text": "The back face carries 6 rows of 4 chevron tread lugs, 5 mm tall and 8 mm wide."},
    {"id": "R09", "scope": "geometry:leaf",
     "text": "A 30 x 10 mm carry-handle slot with rounded ends runs through the plate at the free edge's centre, and all four corners are rounded to 6 mm with raised L-shaped corner guards."},
    {"id": "R10", "scope": "geometry:leaf",
     "text": "The hinge edge is a round knuckle of radius 6.5 with a 5-tooth module 1 sector, tip radius 8, 10 mm wide, at each end."},
    {"id": "R11", "scope": "geometry:end-cheek",
     "text": "The cheek is a boot-shaped block with top edges rounded to 5 mm and three horizontal tread grooves, 2 mm wide and 1 mm deep, on its outer face."},
    {"id": "R12", "scope": "geometry:end-cheek",
     "text": "The cheek carries two 3.9 mm rod holes at X -7 and X 7, Z 9; through holes in end-cheek#1, 10 mm blind holes in end-cheek#2."}
  ],
  "interfaces": [
    {"id": "sector-mesh", "kind": "coupled", "components": ["leaf#1", "leaf#2"],
     "text": "Each leaf's knuckle carries a 5-tooth module 1 sector (pitch radius 7, tip radius 8, 10 mm wide) at Y 40 to 50 and Y -50 to -40; the sectors of leaf#1 (rod at X -7, Z 9) mesh with those of leaf#2 (rod at X 7, Z 9) at X 0, so the leaves turn in mirror through 90 degrees.",
     "yielding": "leaf#2",
     "poses": {"steps": 10, "movers": [
       {"component": "leaf#1", "rotation": {"axis_point": [-7, 0, 9],
        "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": 90}},
       {"component": "leaf#2", "driven": true, "rotation": {"axis_point": [7, 0, 9],
        "axis_direction": [0, 1, 0], "start_deg": 0, "end_deg": -90}}]}},
    {"id": "rod-seats", "kind": "separable", "components": ["leaf", "end-cheek"],
     "text": "Each leaf has a 4.3 mm teardrop bore along its full 100 mm knuckle on its rod axis and turns on a 4 mm steel rod; each cheek carries two 3.9 mm press holes on the rod axes (through in end-cheek#1, 10 mm blind in end-cheek#2). The leaves stay between Y -50 and Y 50; the cheeks' inner faces stand at Y -51 and Y 51 and keep out of the leaves' sweep.",
     "envelope": {"inside": "leaf", "outside": "end-cheek", "shapes": [
       {"pose": "sweep", "box": {"min_mm": [-78, -50.5, 0], "max_mm": [78, 50.5, 80]}}]}}
  ]
}
```
