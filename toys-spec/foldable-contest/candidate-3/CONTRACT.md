# Daybreak Fold

A hand-crank desk theatre for one handle and two acts. Turn the crank on the
front tower and a closed slab on the stage unfolds, like a book, into a spread
twice as wide. Only when the spread is nearly flat does the second act start:
a sun disc rises from behind the backdrop wall and stops half above it. The
timing between the unfolding leaf and the rising sun is the story: the sun
waits for the fold.

Designer: Hand-Crank Theatre (mechanism), for `trend-lab`. Trend: the first
book-style foldable phone (September 2026). The toy borrows only the fold. It
carries no maker name, logo, camera bump, screen icon or product outline; its
leaves are plain matte panels, not a phone.

## Trend Hook

One spine, two equal leaves: closed, the toy shows a single 69 mm-wide slab
lying on the stage; one crank later the same slab has opened about one
crease-spine at the stage centre into a 138 mm-wide flat spread, exactly twice
as wide, with matte inner faces either side of the slim spine. The pointable
feature is that spine, and the countable one is the width doubling from one
leaf to two.

## Signature Motion

The player turns one crank handle on the front tower. The crank keys onto a
12-tooth pinion hidden behind the tower, which drives a 200 degree toothed
sector on the front end of the moving leaf at 3:1: one and a half crank turns
swing the leaf 180 degrees, from lying face-down on the fixed leaf to lying
open and flat. A cam on the same leaf's back end lifts the sun riser: the cam
holds a dwell for the first 120 degrees of opening, then raises the sun 14 mm
over the last 60 degrees, so the sun only climbs once the spread is nearly
flat. Cranking back closes the leaf and the sun sinks behind the backdrop by
its own weight, first.

## Frame and coordinates

X runs left to right, Y front (-) to back (+), Z up from the desk. The
Display Pose is the end of the act: the leaf fully open and flat, the sun at
the top of its travel. Release frames the toy at 35 degrees azimuth and 22
degrees elevation from the front right, against `#f5f0e6`; in the
`render_review` convention that camera is about [-55, 22], recorded on the
references rounded to [-60, 15]. The Focal Component is the fold-leaf: the
open spread with its spine is what the eye reads first, and it costs the base
any decoration of its own; the stage, towers and backdrop are plain blocks
that frame it.

## Unique geometries

1. **base** (1). One printed piece: a plinth X -75..75, Y -46..50, Z 0..24;
   the fixed left leaf, a raised panel X -69..-4, Y -32..34, Z 24..28 whose
   top carries an inset matte panel 0.6 mm deep inside a 4 mm border; the
   crank tower X -24..24, Y -46..-38, Z 0..64, flush with the plinth front;
   the backdrop wall X -22..22, Y 39..45, Z 0..72, cut by a 5.6 mm wide
   vertical slot at X -2.8..2.8 from Z 34 open through the top; a gear bay
   pit X -20..20, Y -38..-32.5 down to Z 8.5 and a cam bay pit X -20.5..20.5,
   Y 34..39 down to Z 8, both open at the top. Bores: a Ø3.0 press bore for
   the hinge pin at X 0, Z 28.5, 7 mm deep from the tower's back face
   (Y -45..-38) and through the backdrop (Y 39..45); a Ø4.4 journal bore
   through the tower at X 0, Z 52.5. Every horizontal bore has a teardrop
   top. Wall minimum 2.0 mm. Prints on its bottom face.
2. **fold-leaf** (1), the Focal Component. A hub tube Ø7 on the hinge axis
   (X 0, Z 28.5) from Y -37.5 to 38.5 with a Ø3.4 free bore; the leaf panel
   X 4..69, Y -32..34, Z 24.5..28.5 in the Display Pose, its top (inner) face
   with the same 0.6 mm inset matte panel inside a 4 mm border; at its front
   end a sector gear plate Y -37.5..-33 (4.5 wide), module 1, pitch radius
   18, tip radius 19, 20 teeth over 200 degrees, centred on +X in the Display
   Pose (from -100 to +100 degrees); at its back end a cam plate Y 34.5..38.5
   whose radius is 6 mm everywhere except one lobe that rises from 6 mm at
   +30 degrees to 20 mm at +90 degrees (straight up in the Display Pose) and
   falls back to 6 mm at +150 degrees, on a cosine rise. Extents 75 x 76 x 39.
   Prints standing on the gear plate's front face (Y -37.5), building toward
   +Y, so the bore is vertical; the cam lobe's front face carries a 45 degree
   chamfer down to the hub so it never prints over air. Wall minimum 1.6 mm.
3. **pinion** (1). A 12-tooth spur gear, module 1, pitch radius 6, tip radius
   7, 4.5 wide (Y -37.5..-33), on a Ø4.0 round shaft through the tower's
   journal (Y -46..-37.5) ending in a 3.5 x 3.5 square drive end
   (Y -51.5..-46). Axis at X 0, Z 52.5, directly above the hinge, at a centre
   distance of 24.0 mm (6 + 18) from the leaf's sector. Prints on the gear's back face (Y -33). Wall minimum 1.2 mm.
4. **crank** (1). An arm 30 long, 10 wide, 4 thick (Y -51.5..-47.5) with
   rounded ends, 20 mm between its socket centre and its knob centre; a
   3.7 x 3.7 square through socket at one end; a Ø8 x 12 knob on its front
   face at the other end (Y -63.5..-51.5). Prints on the arm's back face.
   Wall minimum 2.0 mm.
5. **sun-riser** (1). A plain round sun disc Ø28 x 4 (Y 45.5..49.5) with one
   raised rim 1.2 wide and 0.6 high on its front face; a 5 x 4 stem down from
   the disc's bottom; a bridge 5 wide x 4 high running forward from the stem
   through the backdrop slot (Y 35..45.5); its front end is the cam foot
   (Y 35..38.5), 5 wide, flat underneath. Raised, the foot's underside sits at
   Z 48.5 and the disc's top at Z 85. Extents 28 x 14.5 x 36.5. Prints on the
   disc's back face (Y 49.5); the bridge rises vertically in that stance.
   Wall minimum 1.6 mm.

A purchased Ø3 x 90 mm steel dowel is the hinge pin, from Y -45 to Y 45:
pressed into the tower's blind bore and the backdrop's through bore, free in
the leaf's Ø3.4 hub bore.

## Joints

- **Hinge.** The dowel passes the leaf hub (0.2 mm a side free) and presses
  into the base at both ends. Leaf faces keep 0.5 mm from the tower's back
  face, the left leaf's edge (X -4 vs hub radius 3.5) and the backdrop.
- **Pinion journal.** Ø4.0 shaft in the Ø4.4 tower bore; the gear face keeps
  0.5 mm from the tower's back face, the arm keeps 1.5 mm from its front.
- **Crank key.** The 3.5 square end presses into the arm's 3.7 square socket
  (0.1 mm a side, glued).
- **Sun guide.** The 5 mm bridge slides in the 5.6 mm slot (0.3 mm a side);
  the foot rests on the cam by gravity, no spring.

## Motion and fit

- Leaf: 180 degrees about the hinge axis (X 0, Z 28.5, along Y), from closed
  (lying on the fixed leaf, its panel at Z 28.5..32.5, 0.5 mm above the fixed
  leaf's top) to open flat (Z 24.5..28.5, 0.5 mm above the plinth top). Hard
  stops: the plinth top at open and the fixed leaf at closed.
- Pinion and crank: 540 degrees for the full 180 degree leaf travel, turning
  the opposite way to the leaf (3:1 external mesh).
- Sun: 14 mm vertical travel, Z of the foot 34.5 (lowered, on the 6 mm base
  circle) to 48.5 (raised, on the 20 mm lobe). Lowered, the disc's top is at
  Z 71, 1 mm below the backdrop's top, hidden; raised, it is at Z 85, half
  the disc above the wall.
- The gear sector dips into the gear bay and the cam lobe into the cam bay
  through the travel, each keeping at least 0.5 mm from the pit walls and
  floors.

Motion plan: `--check-motion true` on the wish and on every resume and
correction; one sweep of the full travel in at most 10 steps against only the
parts a moving part can reach; one one-tooth sweep for the pinion-sector
mesh, at most 10 steps, with no obstacles; a skipped, killed or timed-out
sweep fails the motion requirement, never passes it.

## Print

Workshop prints at a 0.4 mm nozzle without support. Every point, chisel, keel
and V underside ends in a flat land at least 0.8 mm across (one print minimum
at a 0.4 mm nozzle). A drawn detail under the print minimums is enlarged to
the minimum; when the enlarged detail does not fit its spot, it is left out,
and this contract names it. The sun disc carries no rays, only its rim.

## Handling

An adult desk toy. The crank arm and knob take the handling load and are
4 mm and Ø8 sections. The sun riser lifts out of its slot if pulled up; it
drops back on the cam. The leaf panel is 4 mm thick, nothing load-bearing is
under 3 mm, and the dowel carries the hinge.

```design-contract
{
  "schema_version": 4,
  "title": "Daybreak Fold",
  "inventor": "trend-lab",
  "envelope_mm": [150, 113.5, 85],
  "references": [
    {"file": "ref-01-daybreak-fold.png", "shows": "assembly", "camera": [-60, 15]},
    {"file": "ref-02-base.png", "shows": "geometry:base", "camera": [-60, 30]},
    {"file": "ref-03-fold-leaf.png", "shows": "geometry:fold-leaf", "camera": [-60, 30]},
    {"file": "ref-04-pinion.png", "shows": "geometry:pinion", "camera": [-60, 15]},
    {"file": "ref-05-crank.png", "shows": "geometry:crank", "camera": [-60, 15]},
    {"file": "ref-06-sun-riser.png", "shows": "geometry:sun-riser", "camera": [90, 15]}
  ],
  "geometries": [
    {"id": "base", "name": "Stage base with fixed leaf, crank tower and backdrop", "count": 1,
     "extents_mm": [150, 96, 72], "wall_min_mm": 2.0},
    {"id": "fold-leaf", "name": "Moving leaf with spine hub, sector gear and cam", "count": 1,
     "extents_mm": [75, 76, 39], "wall_min_mm": 1.6},
    {"id": "pinion", "name": "Crank pinion and shaft", "count": 1,
     "extents_mm": [14, 14, 18.5], "wall_min_mm": 1.2},
    {"id": "crank", "name": "Crank arm and knob", "count": 1,
     "extents_mm": [30, 10, 16], "wall_min_mm": 2.0},
    {"id": "sun-riser", "name": "Sun disc on its riser", "count": 1,
     "extents_mm": [28, 14.5, 36.5], "wall_min_mm": 1.6}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly",
     "text": "Display Pose: the moving leaf lies fully open and flat beside the fixed leaf, both inner faces level, and the sun disc stands with exactly half its height above the backdrop wall."},
    {"id": "R02", "scope": "assembly",
     "text": "Closed, the moving leaf lies face-down on the fixed leaf as one 69 mm-wide slab; open, the two leaves form one 138 mm-wide flat spread split by a single slim spine at the stage centre."},
    {"id": "R03", "scope": "assembly",
     "text": "One and a half turns of the crank swing the moving leaf through 180 degrees from closed to open; the crank turns opposite to the leaf."},
    {"id": "R04", "scope": "assembly",
     "text": "The sun disc stays fully hidden behind the backdrop until the leaf is within 60 degrees of flat, then rises 14 mm as the leaf finishes opening, and sinks back by its own weight when the leaf closes."},
    {"id": "R05", "scope": "assembly",
     "text": "Seen from the front right and above, the crank and knob stand in front of the crank tower, the open spread runs left to right across the stage, and the half-risen sun shows above the backdrop behind the spine."},
    {"id": "R06", "scope": "assembly",
     "text": "The motion check sweeps the full leaf travel and the pinion-sector mesh with --check-motion true; a skipped, killed or timed-out sweep fails this requirement, never passes it."},
    {"id": "R07", "scope": "assembly",
     "text": "The hinge is a purchased Ø3 x 90 mm steel dowel through the leaf hub, pressed into the crank tower and the backdrop."},
    {"id": "R08", "scope": "assembly",
     "text": "No surface carries a logo, lettering, camera bump, button or screen icon; the leaves' inner faces are plain matte inset panels."},
    {"id": "R09", "scope": "geometry:base",
     "text": "The fixed left leaf is a raised 65 x 66 x 4 panel left of the spine whose top carries a 0.6 mm deep inset panel inside a 4 mm border."},
    {"id": "R10", "scope": "geometry:base",
     "text": "The crank tower is a plain 48 x 8 x 64 block flush with the plinth front, with a Ø4.4 journal bore at Z 52.5 and a Ø3.0 blind hinge bore at Z 28.5 on X 0, both teardrop-topped."},
    {"id": "R11", "scope": "geometry:base",
     "text": "The backdrop is a plain 44 x 6 x 72 wall behind the spine, cut by one 5.6 mm vertical slot on X 0 from Z 34 open through its top, with a Ø3.0 hinge bore through it."},
    {"id": "R12", "scope": "geometry:base",
     "text": "The plinth top has two open pits on X 0: a gear bay in front of the leaves and a cam bay behind them, each 0.5 mm clear of the swept gear sector or cam."},
    {"id": "R13", "scope": "geometry:fold-leaf",
     "text": "The leaf panel is 65 x 66 x 4 on a Ø7 spine hub; its inner face carries a 0.6 mm deep inset panel inside a 4 mm border, matching the fixed leaf."},
    {"id": "R14", "scope": "geometry:fold-leaf",
     "text": "The front end carries a 4.5 mm wide module 1 sector gear, pitch radius 18, with 20 teeth over 200 degrees centred on the panel's direction."},
    {"id": "R15", "scope": "geometry:fold-leaf",
     "text": "The back end carries a cam plate of radius 6 mm with one lobe rising on a cosine to 20 mm, pointing straight up in the Display Pose, its front face chamfered at 45 degrees to the hub."},
    {"id": "R16", "scope": "geometry:pinion",
     "text": "A 12-tooth module 1 spur gear, 4.5 mm wide, on a Ø4.0 shaft that ends in a 3.5 x 3.5 square drive end."},
    {"id": "R17", "scope": "geometry:crank",
     "text": "A rounded 30 x 10 x 4 arm with a 3.7 x 3.7 square through socket at one end and a Ø8 x 12 knob 20 mm away at the other."},
    {"id": "R18", "scope": "geometry:sun-riser",
     "text": "A plain Ø28 x 4 sun disc with one raised rim 1.2 mm wide and 0.6 mm high and no rays, on a 5 x 4 stem and bridge that end in a flat cam foot."}
  ],
  "interfaces": [
    {"id": "crank-drive", "kind": "coupled", "components": ["pinion", "fold-leaf"],
     "text": "The pinion's 12 teeth (module 1, pitch radius 6, 4.5 wide in Y -37.5..-33, axis X 0, Z 52.5) mesh with the fold-leaf's 20-tooth sector (pitch radius 18, same layer, axis X 0, Z 28.5), centre distance 24.0 mm, ratio 3:1, opposite senses.",
     "yielding": "fold-leaf",
     "poses": {"steps": 9, "movers": [
       {"component": "pinion", "rotation": {"axis_point": [0, -40, 52.5],
        "axis_direction": [0, -1, 0], "start_deg": -540, "end_deg": 0}},
       {"component": "fold-leaf", "driven": true, "rotation": {"axis_point": [0, 0, 28.5],
        "axis_direction": [0, -1, 0], "start_deg": 180, "end_deg": 0}}]}},
    {"id": "sun-cue", "kind": "coupled", "components": ["fold-leaf", "sun-riser"],
     "text": "The fold-leaf's cam plate (Y 34.5..38.5) lifts the sun-riser's flat 5 mm foot (Y 35..38.5) at the top of the hinge axis: dwell on the 6 mm base circle for the first 120 degrees of opening, then a 14 mm cosine rise to the 20 mm lobe over the last 60 degrees. The foot rests on the cam by gravity.",
     "yielding": "sun-riser",
     "poses": {"steps": 9, "movers": [
       {"component": "fold-leaf", "rotation": {"axis_point": [0, 0, 28.5],
        "axis_direction": [0, -1, 0], "start_deg": 180, "end_deg": 0}},
       {"component": "sun-riser", "driven": true, "translation": {"offsets_mm": [
        [0, 0, -14], [0, 0, -14], [0, 0, -14], [0, 0, -14], [0, 0, -14], [0, 0, -14],
        [0, 0, -14], [0, 0, -10.5], [0, 0, -3.5], [0, 0, 0]]}}]}},
    {"id": "leaf-fold", "kind": "coupled", "components": ["fold-leaf", "base"],
     "text": "A Ø3 x 90 steel dowel on X 0, Z 28.5 is pressed into the base's Ø3.0 bores (7 mm blind in the crank tower's back, through the backdrop) and runs free in the fold-leaf's Ø3.4 hub bore. The leaf swings 180 degrees over the top, keeping 0.5 mm from the tower's back face, the backdrop's front face, the fixed leaf's spine edge at X -4 and the floors and walls of the gear bay and cam bay.",
     "yielding": "fold-leaf",
     "poses": {"steps": 9, "movers": [
       {"component": "fold-leaf", "rotation": {"axis_point": [0, 0, 28.5],
        "axis_direction": [0, -1, 0], "start_deg": 180, "end_deg": 0}}]}},
    {"id": "pinion-journal", "kind": "coupled", "components": ["pinion", "base"],
     "text": "The pinion's Ø4.0 shaft turns in the base's Ø4.4 teardrop-topped journal bore through the crank tower at X 0, Z 52.5 (Y -46..-38); the gear face keeps 0.5 mm from the tower's back face and the tip circle 0.5 mm from the bay.",
     "yielding": "pinion",
     "poses": {"steps": 9, "movers": [
       {"component": "pinion", "rotation": {"axis_point": [0, -40, 52.5],
        "axis_direction": [0, -1, 0], "start_deg": -540, "end_deg": 0}}]}},
    {"id": "crank-sweep", "kind": "coupled", "components": ["crank", "base"],
     "text": "The crank arm turns in front of the crank tower with 1.5 mm between its back face (Y -47.5) and the tower front (Y -46); the knob's outer edge sweeps a 24 mm radius round Z 52.5 and stays above the plinth.",
     "yielding": "crank",
     "poses": {"steps": 9, "movers": [
       {"component": "crank", "rotation": {"axis_point": [0, -50, 52.5],
        "axis_direction": [0, -1, 0], "start_deg": -540, "end_deg": 0}}]}},
    {"id": "crank-key", "kind": "static", "components": ["crank", "pinion"],
     "text": "The pinion's 3.5 x 3.5 square drive end (Y -51.5..-46) presses into the crank arm's 3.7 x 3.7 square through socket and is glued."},
    {"id": "sun-guide", "kind": "coupled", "components": ["sun-riser", "base"],
     "text": "The sun-riser's 5 mm wide bridge slides vertically in the backdrop's 5.6 mm slot on X 0 (open from Z 34 to the top), 0.3 mm a side; the disc behind the wall (Y 45.5..49.5) keeps 0.5 mm from its back face.",
     "yielding": "sun-riser",
     "poses": {"steps": 9, "movers": [
       {"component": "sun-riser", "translation": {"offsets_mm": [
        [0, 0, -14], [0, 0, -14], [0, 0, -14], [0, 0, -14], [0, 0, -14], [0, 0, -14],
        [0, 0, -14], [0, 0, -10.5], [0, 0, -3.5], [0, 0, 0]]}}]}}
  ]
}
```
