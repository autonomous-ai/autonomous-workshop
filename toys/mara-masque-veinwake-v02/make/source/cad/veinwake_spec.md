# Shatterline CAD brief

Corrected revision of the original text-derived Veinwake design. The completed
Mara Masque handoff remains the design authority for everything the correction
Wish does not change. Units are millimetres. Origin is the board footprint
centre, bottom on XY, front negative Y and up positive Z.

Two reference images are attached to the correction Wish and copied read-only
into `ref/`. They are concept art, not measured drawings: they carry the
silhouette and the read, the Wish text carries the millimetres, and where the
two disagree the millimetre wins.

- `ref/rock-board.png` (`ref-01-faceted-rock-board.png`) — the corrected rind.
- `ref/cube-cluster.png` (`ref-02-granite-cube-cluster.png`) — one corrected
  bubble marker alone.

## Overall form and construction

A flat-bottomed low-polygon fractured boulder carries nine shallow neutral
growth pockets. Every rock surface outward and inward is a flat planar facet;
facets meet at sharp visible edges. The teeth are unchanged tall hexagonal
prisms with inward tapered blunt tips. The bubbles are clusters of five
interpenetrating cubes in a pyrite habit. The rim stays low enough that the
marker bodies remain exposed. Direct sRGB colours are supplementary to
silhouettes.

- `BOARD_LENGTH` = 140 mm and `BOARD_WIDTH` = 130 mm [observed] (Wish).
- `ASSEMBLED_HEIGHT` = 32 mm; each `CLUSTER_HEIGHT` = 26 mm [observed] (Wish).
- `RIM_HEIGHT` = 14 mm; `FIELD_HEIGHT` = 8 mm [observed] (correction Wish).
- `SEAT_DEPTH` = 2 mm; `SEAT_Z` = 6 mm [observed] (Wish).
- `GRID_PITCH` = 36 mm; `FOOT_DIAMETER` = 28 mm [observed] (Wish).
- `SEAT_CLEARANCE` = 1 mm per side; `SEAT_DIAMETER` = 30 mm [observed] (Wish).
- `FOOT_HEIGHT` = 3 mm; `CORNER_RADIUS` = 6 mm [assumed] (original design).
- `FIELD_LENGTH` = 114 mm; `FIELD_WIDTH` = 104 mm; `FIELD_RADIUS` = 22 mm [assumed]
  [assumed] (original design; retained unused reference dimensions).
- `TOOTH_RADIUS` = 11 mm; `TOOTH_SHOULDER` = 18 mm; `TOOTH_TIP_RADIUS` = 2.5 mm [assumed];
  `TOOTH_TIP_OFFSET` = 2 mm [assumed] (original design, not touched).
- `HELD_OFFSET` = 55 mm [observed] (Wish).
- `MIN_WALL` = 3 mm [observed]; `OVERHANG_LIMIT` = 0.695 as the bound on any face normal's
  Z component, which is sin(44.03 deg) and so inside the 45 deg support-free
  limit; the built cubes stay under 0.680, that is 42.8 deg [observed]
  (correction Wish manufacturing envelope).

## Rind: faceted boulder (changed by this correction)

`rock_footprint()` no longer builds a 64-point periodic superellipse spline.
`ROCK_PLAN` is an explicit closed polygon of sixteen straight segments whose
lengths run from 12.69 to 55.27 mm [inferred], so the plan outline is angular and
irregular rather than an even oval. Its bounding box is exactly
140.000 x 130.000 mm [observed] and it is centred on the origin; both are asserted from
the written solid.

`fillet(top, radius=ROCK_TOP_RADIUS)` is deleted. `ROCK_EXPONENT`,
`ROCK_TOP_RADIUS`, `CAVITY_INSET`, `GROWTH_KEEPOUT_RADIUS`, `TERRACE_WIDTH` and
`TERRACE_Z` are retired with the mechanisms they served. No spline surface, no
fillet and no round-over survives anywhere on the rock.

- Outer wall: sixteen large flat planes, one per plan segment, each leaning
  inward over the full 14 mm [observed] rise by its own `ROCK_WALL_LEAN` of 2.0 to
  6.5 mm — 8 to 25 degrees from vertical [assumed] (correction design). Seven
  of the sixteen are overtaken by their neighbours before they reach the top,
  so they finish as angular wedges and the top edge is the chain of bevels
  those facets cut. Counting exterior facets: sixteen wall planes plus the flat
  bottom and the flat rim band is eighteen, inside the Wish's 15-20 aim.
- Cavity wall: the `lower`/`upper` terrace profiles are replaced by a
  triangulated band. Thirty-two large flat triangles run from the rim crest
  down to the field boundary at z = 8.00, meeting the flat floor in straight
  lines. The crest is not a level ring: `ROCK_CREST_Z` sets each of its sixteen
  vertices at its own height between 11.40 and 14.00 mm [assumed], so the rim's inner
  edge is a jagged three-dimensional chain and no two neighbouring triangles
  share a tilt. Their inward step `ROCK_CAVITY_DROP` runs from 2.60 to 9.00 mm [assumed]
  against a rise of 3.40 to 6.00 mm [inferred], putting the triangles between 29 and 69
  degrees from vertical. Every one of them faces upward and inward, so none
  overhangs. Sixteen short vertical facets close the crest back up to the rim
  at the vertices that sit below 14.00. The band runs all the way around the
  rock and is 2.60 to 9.00 mm [assumed] wide in plan, taking every millimetre the nine
  seats leave.
- Rim band: a flat annulus at z = 14.00 between the outer top outline and the
  crest, held at the 3.78 mm [assumed] design width so the cavity band can take the rest.
  Its narrowest measured section is 3.15 mm [inferred], above the 3.00 mm
  minimum wall; `rind_wall_audit.py` measures that distance from the written
  STEP wires.
- Seats: nine plain smooth-walled flat-bottomed cylinders, 30.00 mm [observed] in
  diameter, floors at z = 6.00, bored straight down from z = 6.00 through
  everything above. At the flat field surface z = 8.00 each is therefore
  exactly 2.00 mm [observed] deep, and each accepts either marker at any rotation. The
  bore passes through whatever facets it meets: the field boundary comes within
  13.00 mm [assumed] of every one of the eight outer seat axes, two millimetres inside
  their 15.00 mm [inferred] bore radius, so each of those eight pocket rims cuts the base
  line of the cavity facets and the facet edges break visibly at the circle.
  Nine clean circles inside a completely angular rock.
- Bottom: one flat plane at z = 0.00, so the board sits on a table and prints
  without supports.

[observed] `ref/rock-board.png` measures 537 x 437 px with 0.922 left-right
silhouette symmetry, widest at 0.638 of its height: a flat angular slab seen
from above and in front, with the pocket field filling most of the top and an
angular margin all the way round. The CAD follows that read at the Wish's
millimetres.

## Bubble: cube cluster (changed by this correction)

`bubble_lobe()`, `LOBE_RADIUS`, `LOBE_CENTER_RADIUS` and `LOBE_CROWN_Z` are
deleted; nothing references them. `make_bubble()` fuses five interpenetrating
cubes onto the unchanged 28.00 x 3.00 mm [observed] circular foot.

- Edge lengths 16.00, 12.80, 10.20, 8.40 and 7.00 mm [observed] — all different, largest
  16.00, smallest above 7.00 [observed] (correction Wish).
- Each cube carries its own orientation about more than one axis
  (`CUBE_CLUSTER` rows give X, Y and Z angles; `CLUSTER_SPIN` turns the whole
  cluster so its widest axis lies on X). No two read as a repeated element.
- The design bound `OVERHANG_LIMIT` = 0.695 caps every cube axis's absolute Z
  component; the five cubes actually measure 0.577, 0.652, 0.664, 0.680 and
  0.659, so all thirty square faces stand within 42.8 degrees of vertical or
  face upward. Nothing overhangs; `check_overhang` at 45 degrees reports zero
  regions needing support.
- The cubes interpenetrate into one compact mound. Its maximum horizontal
  extent is 26.57 mm [inferred] against the piece's 26.00 mm [observed] height, so the mound is
  wider than it is tall, and its greatest radius is 13.78 mm [inferred] so it stays inside
  the 28.00 mm [observed] foot. The orientations were chosen so that no two cube faces
  fall nearly coincident: the written solid has 37 faces and its smallest is
  5.77 mm2, so the cluster carries no sliver facet, no blade and no fin. The
  narrowest region `check_thickness` finds is a 0.13 mm [inferred] taper of 0.3 mm2 at a
  facet edge, which is the sharp edge every polyhedron has and not a feature;
  the median wall is 14.60 mm [inferred].
- The whole piece is exactly 26.00 mm [observed] tall; `cluster_lift()` computes the exact
  rise that puts the highest cube corner on 26.000 and the assert measures the
  written solid. The largest cube dips below z = 0 and the fused body is
  trimmed at the bed plane, so the bottom stays the single flat 28.00 mm [observed]
  circle.

[observed] `ref/cube-cluster.png` measures 385 x 500 px in a low isometric view
whose disc occupies the lower quarter; the cube mass is irregular, widest at
0.655 of its height, and made only of square faces and sharp corners. The CAD
follows that habit, but keeps every cube inside the 28.00 mm [observed] footprint the Wish
fixes, which the concept art does not.

## Reference likeness

The two images are concept art at an unstated camera and scale, so they are not
used as a gated silhouette match; the 0.90 likeness floor would measure the
camera rather than the model. They are inspected directly, measured for
proportion above, and compared requirement by requirement in the independent
blind review. This is a deliberate, disclosed choice, not a skipped gate.

## Components and manufacturing

One rind, five identical teeth and four identical bubbles [observed] (Wish).
Each is a separate single solid because every marker must be freely placed and
removed. All bottoms lie at local Z zero. No hardware, glue, bought component,
electricity, supports or assembly step is required. Every part is fully opaque
in geometry and in its delivered colour; there is no translucency anywhere.

No feature is a needle, spike, blade, fin, fur, grit, scattered micro-bump or
surface texture of any kind. All relief is large and flat-faced: broad planes
meeting at definite edges. There is no vein, crack network or raised
second-material line on the rock, and no druse, crust or bumps.

Minimum material below a pocket is 6 mm [inferred] and between neighbouring pockets is
6 mm [inferred]. Minimum required wall is 3 mm [observed] (Wish). The tooth's
flat tip is 4.330 mm across flats [inferred], exceeding the required 2 mm
blunt-tip span [observed] (Wish).

`make_tooth()` is not touched. Its five exported STEP files reproduce the
source archive's bytes exactly; `measure/step-lineage.json` records every
per-part hash against `make/ATTEMPTS.json` from that archive.

## Placement and state evidence

Nine identical circular pockets are at the Cartesian product of negative pitch,
zero and positive pitch. Seats accept either marker at any rotation. Place
clusters downward into the board, lift upward to reset. These are open gravity
rests, with no upward retention claim.

The explicit clearance helper band is widened locally to 1 mm [observed] (Wish)
for the open game pockets, then restored. This intentionally exceeds its
ordinary hand-assembly fit default; it does not alter a verification threshold.

The normal complete assembly shows the legal draw XOXXOOOXX, read from
back-left. The before/after sheet instead shows back-left and back-middle
teeth, middle-left and centre bubbles, and a third tooth held 55.00 mm [observed] over
back-right before being lowered. Only the held tooth changes transform.

## 8. Powered system / mechanism

Nothing is powered or mechanically driven. Players supply the placement action
directly. There is no physical growth or joining. The operator selected
`check_motion: false` for this run, so no motion sweep, animation or
independent motion review was produced and motion is reported unverified,
never passed. Build, fit, print gates and still-image review remain in scope.

## State legibility

Tall-and-pointed against squat-and-square. From a seated player's view the
tooth is one 22 mm [inferred] hexagonal prism rising to a single offset blunt tip; the
bubble is a squat 27 mm-wide [inferred] mound of unequal cubes. From directly overhead the
tooth shows one clean hexagon with a single small offset hexagonal tip and
three even tones, while the bubble shows eight or more unequal angular facets
at clearly different tones. The canonical top view of the complete assembly is
rendered at `snap/top.png` for that check.

## Verification targets

Measure the actual solid bounds, circular seat sections and radial clearance;
check each habit in all nine pockets, one solid per printable file, bed datum,
mesh, thickness and overhang. Compare before/after part signatures and the
single held translation. Inspect front, top and iso views per component and for
the assembly, plus the fixed elevated front state sheet and the overhead
assembly view; perform independent blind review. Run exhaustive digital rules
equivalence separately. Physical printing, handling and durability remain
untested, and motion is unverified.
