# Hugfold

A chunky kawaii desk buddy with an oversized round bun head. Its body is a
thick two-page book standing on a stubby-footed base. Pull its two stubby
arms apart and the body unfolds: the two halves swing open together on a
geared spine, and the narrow little slab becomes a wide belly with a matte
screen and a big heart across it. Fold it back and it hugs itself shut.
Designed by the Chunky Kawaii personality for the trend-lab contest: round,
oversized head, stubby limbs and soft bevels everywhere, cute enough to pick
up and sturdy enough to drop.

## Trend Hook

The fold itself, in one pointable feature: **one vertical crease down the
middle of the belly**. Closed, the body is a 28 mm-wide slab, half the width
of the head. Opened flat, the same two halves make a 102 mm-wide belly,
nearly four times as wide, and the only seam across that whole matte screen is the one
soft crease where the two halves meet, splitting the big raised heart into a
left half and a right half. Folded shut, the two half-hearts press together
face to face and vanish. Small thing, book hinge, hidden crease, big thing.
No phone, no camera bump, no screen glass, no maker's name or mark: the toy
is a creature that folds.

## Signature Motion

What moves: the two body halves, each pivoting on its own vertical pin at
the spine, 10 mm apart. What drives it: the player. Pinch either stubby arm
(or both) and swing it; a gear sector on each half's spine meshes with the
other's, 1:1, so turning one half turns the other by the same angle the
opposite way, exactly like a synchronized dual-axis book hinge. Both halves
always open and close as mirror images and the head always stays centred
over the crease. What the player does: fidgets it open into the wide hug,
folds it shut, flicks one arm and watches the other arm follow. The range
is 90 degrees per half: closed (inner faces touching) to fully flat
(180 degrees between the halves). The Display Pose is each half 15 degrees
short of flat, a shallow open-book V facing the viewer.

## Unique geometries

| id | name | count | extents (mm) |
|---|---|---|---|
| head | Bun head | 1 | 56 x 48 x 50 |
| left-half | Left body half | 1 | 61 x 14 x 60 |
| right-half | Right body half | 1 | 61 x 14 x 60 |
| base | Footed base | 1 | 64 x 56 x 18 |

**Focal Component: the head.** It is the biggest single mass and the face
of the toy. It costs the body visual weight when closed (the body is half
its width), which is the point: closed, Hugfold is a bobble-headed little
slab; open, the belly finally outgrows the head.

## Frame and coordinates

Origin at the base's underside, centred between the two pivot axes. +X is
the toy's right, -Y the front (the viewer), +Z up. The pivot axes are
vertical lines at X -5, Y 0 (left half) and X +5, Y 0 (right half).

## Per-geometry spec

**Base.** A rounded stadium plate 64 mm wide (X), 56 mm deep (Y), 8 mm tall,
centred at X 0, Y -6, with a 4 mm round on every top edge. Two stubby feet:
domed toe bumps 16 mm across, protruding 6 mm forward from the front edge at
X -16 and X +16, their tops flush with the plate top. Two pivot pins, 4.0 mm
diameter, 10 mm tall above the washer bosses, on the pivot axes. Around each
pin a washer boss 10 mm across and 0.5 mm tall, which the half rides on.
The Footed base's 18 mm extent is its 8 mm plate plus the 10 mm pins.
Prints flat on its underside. Wall minimum 3.0 mm.

**Left body half and right body half (mirror images).** Each is a slab
14 mm thick, 60 mm tall, reaching 46 mm from its pivot axis to its free
edge, with a 3 mm round on every outer edge. The pivot axis sits 5 mm behind
the inner (front, when open) face and 9 mm in front of the back face. The
spine end is a 5 mm-radius quarter arc round the pivot axis from the inner
face to the plane of the two axes, then straight back to the back face, so the two halves
never cross the mirror plane while they turn. Each half has a 4.4 mm pivot
hole 11 mm deep up from its underside and another 11 mm deep down from its
top face, both on its pivot axis.

The spine gear: in a band 6 mm tall from Z 10.5 to Z 16.5 (2 mm above the
half's underside), each half carries a spur gear sector on its pivot axis,
module 1.0, 10 teeth on the full circle (pitch radius 5 mm), spanning
120 degrees of teeth so it stays in mesh over the whole 90 degree range plus
15 degrees each side. Inside that band each half is relieved to 6.5 mm
radius round the other half's pivot axis so the other sector's tips clear.

The inner face carries the matte screen: a recess 0.6 mm deep with a 6 mm
corner radius, 44 mm tall, running from 4 mm outside the spine arc to 6 mm
from the free edge; on the screen floor sits half of the heart, raised
1.2 mm, the full heart 32 mm wide and 28 mm tall with its centre line on the
crease. The free edge carries one stubby arm: a round nub 14 mm across
protruding 10 mm from the free-edge end face, centred at the half's mid
height and mid thickness, ending in a full dome. With the 5 mm spine arc
and the 46 mm slab, each half is 61 mm long. Prints on its back face
(flat). Wall minimum 3.0 mm.

**Head.** A soft rounded bun 56 mm wide, 48 mm deep, 44 mm tall, centred on
X 0, Y 0, with a flat underside. Two round ears, each a dome 16 mm across
and 6 mm tall, on top at X -16 and X +16, bringing the head to 50 mm. The face on the front: two domed
eyes 8 mm across and 2 mm proud, centred 20 mm apart at 22 mm above the
underside; between and 6 mm below them a raised smile band 1.2 mm wide,
12 mm across; under each eye, 6 mm outboard, a flat blush disc 7 mm across
and 0.6 mm proud. Underside: two pins 4.0 mm diameter, 10 mm long, on the
pivot axes, each inside a boss 10 mm across and 0.5 mm tall that rests on a
half's top face. Prints on its flat underside. Wall minimum 3.0 mm.

## Joints, every one pinned

- **Base pivots.** Base pins 4.0 mm in each half's lower 4.4 x 11 hole
  (0.2 mm radial clearance); each half rides on the 10 mm washer boss, so
  its underside is at Z 8.5.
- **Head pivots.** Head pins 4.0 mm in each half's upper 4.4 x 11 hole; the
  head's two bosses rest on the halves' top faces at Z 68.5. The head lifts
  straight off for assembly; gravity and the pins hold it.
- **Spine gears.** The two 10-tooth module 1.0 sectors mesh on the
  centre line at X 0, Y 0, centre distance 10 mm, 0.15 mm backlash.

## Display Pose and frame

Each half 15 degrees short of flat, free edges forward, so the two halves
stand at 150 degrees to each other in a shallow open-book V facing the
viewer. Composed in Release's product frame at 35 degrees azimuth,
22 degrees elevation, against `#f5f0e6`, the head is the focal point and
the crease runs straight down from under its chin.

## Motion and fit

Each half turns 90 degrees about its own pivot: 0 degrees is flat open, 90
is closed with the inner faces touching. The halves are assembled, not
printed in place. Retention: the head's pins and the base's pins trap each
half. Every moving pair keeps at least 0.4 mm clearance except the pin fit
(0.2 mm radial) and the gear backlash (0.15 mm).

## Handling check

Dropped, the head lifts off first; nothing breaks, the pins are 4 mm and
10 mm long, solid. The arm nubs are 14 mm thick and the thinnest
load-bearing section is the 2.8 mm of material between a pivot hole and the
inner face, a fully supported ring inside the 14 mm slab; everything
else is 3 mm or more. Gear teeth at module 1.0 are the weakest feature and
are only ever loaded by a fingertip.

## Print

Every point, chisel, keel and V underside ends in a flat land at least
0.8 mm across (one print minimum at a 0.4 mm nozzle).

A drawn detail under the print minimums is enlarged to the minimum; when
the enlarged detail does not fit its spot, it is left out, and this
contract names it.

```design-contract
{
  "schema_version": 4,
  "title": "Hugfold",
  "inventor": "trend-lab",
  "envelope_mm": [122, 58, 119],
  "references": [
    {"file": "ref-01-hugfold.png", "shows": "assembly", "camera": [-75, 15]},
    {"file": "ref-02-head.png", "shows": "geometry:head", "camera": [-60, 15]},
    {"file": "ref-03-left-half.png", "shows": "geometry:left-half", "camera": [-90, 15]},
    {"file": "ref-04-right-half.png", "shows": "geometry:right-half", "camera": [-90, 15]},
    {"file": "ref-05-base.png", "shows": "geometry:base", "camera": [-60, 30]}
  ],
  "geometries": [
    {"id": "head", "name": "Bun head", "count": 1,
     "extents_mm": [56, 48, 50], "wall_min_mm": 3.0},
    {"id": "left-half", "name": "Left body half", "count": 1,
     "extents_mm": [61, 14, 60], "wall_min_mm": 3.0},
    {"id": "right-half", "name": "Right body half", "count": 1,
     "extents_mm": [61, 14, 60], "wall_min_mm": 3.0},
    {"id": "base", "name": "Footed base", "count": 1,
     "extents_mm": [64, 56, 18], "wall_min_mm": 3.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly",
     "text": "In the Display Pose each body half stands 15 degrees short of flat, free edges forward, making a shallow 150 degree open-book V that faces the front."},
    {"id": "R02", "scope": "assembly",
     "text": "The head sits centred over the crease on top of both halves, and is the widest and largest single part of the toy."},
    {"id": "R03", "scope": "assembly",
     "text": "Open, one vertical crease at X 0 is the only seam across the inner faces: the matte screen and the raised heart both run across it, half on each side."},
    {"id": "R04", "scope": "assembly",
     "text": "Folded shut, the two inner faces touch and the body is 28 mm wide, half the head's width; opened flat, the two halves span 102 mm without the arms."},
    {"id": "R05", "scope": "assembly",
     "text": "Swinging either half turns the other the same angle the opposite way through the two meshing spine gear sectors in the 6 mm band 2 mm above the halves' undersides."},
    {"id": "R06", "scope": "assembly",
     "text": "Each half pivots on a 4.0 mm base pin and a 4.0 mm head pin on its own vertical axis, the two axes 10 mm apart at the spine."},
    {"id": "R07", "scope": "assembly",
     "text": "Every outer edge of the toy is rounded: no sharp corner shows anywhere in the Display Pose."},
    {"id": "R08", "scope": "geometry:head",
     "text": "A soft rounded bun with a flat underside and two round dome ears on top, 32 mm apart centre to centre."},
    {"id": "R09", "scope": "geometry:head",
     "text": "The face carries two domed eyes 20 mm apart, a raised smile band 12 mm across below them, and a flat blush disc under each eye."},
    {"id": "R10", "scope": "geometry:head",
     "text": "The underside carries two 4.0 x 10 mm pins 10 mm apart, each inside a 10 mm boss 0.5 mm tall."},
    {"id": "R11", "scope": "geometry:left-half",
     "text": "A 14 mm slab with a 5 mm-radius spine arc round its pivot hole and a 120 degree, module 1.0 gear sector in the 6 mm spine band."},
    {"id": "R12", "scope": "geometry:left-half",
     "text": "The inner face carries a 0.6 mm-deep rounded matte screen recess holding the left half of the heart, raised 1.2 mm, its flat side on the spine edge."},
    {"id": "R13", "scope": "geometry:left-half",
     "text": "The free edge carries one stubby arm: a 14 mm round nub 10 mm long with a full dome end, at mid height."},
    {"id": "R14", "scope": "geometry:right-half",
     "text": "The mirror image of the left half: a 14 mm slab with a 5 mm-radius spine arc and a 120 degree, module 1.0 gear sector in the 6 mm spine band."},
    {"id": "R15", "scope": "geometry:right-half",
     "text": "The inner face carries a 0.6 mm-deep rounded matte screen recess holding the right half of the heart, raised 1.2 mm, its flat side on the spine edge."},
    {"id": "R16", "scope": "geometry:right-half",
     "text": "The free edge carries one stubby arm: a 14 mm round nub 10 mm long with a full dome end, at mid height."},
    {"id": "R17", "scope": "geometry:base",
     "text": "A rounded stadium plate 8 mm tall with two domed toe bumps 16 mm across protruding 6 mm from its front edge, 32 mm apart."},
    {"id": "R18", "scope": "geometry:base",
     "text": "Two 4.0 mm pivot pins 10 mm tall stand 10 mm apart on the top face, each inside a 10 mm washer boss 0.5 mm tall."}
  ],
  "interfaces": [
    {"id": "spine-gears", "kind": "coupled", "components": ["left-half", "right-half"],
     "text": "Each half carries a module 1.0, 10-tooth (pitch radius 5 mm) gear sector spanning 120 degrees on its own pivot axis, in the band Z 10.5 to 16.5; the sectors mesh at X 0, Y 0 with 10 mm centre distance and 0.15 mm backlash. Inside that band each half is relieved to 6.5 mm radius round the other half's pivot axis.",
     "yielding": "right-half",
     "poses": {"steps": 12, "movers": [
       {"component": "left-half", "rotation": {"axis_point": [-5, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": -15, "end_deg": 75}},
       {"component": "right-half", "driven": true, "rotation": {"axis_point": [5, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 15, "end_deg": -75}}]}},
    {"id": "base-pivots", "kind": "coupled", "components": ["base", "left-half", "right-half"],
     "text": "The base carries two 4.0 mm pins 10 mm tall at X -5 and X +5, Y 0, each inside a 10 mm washer boss 0.5 mm tall; each half has a 4.4 mm hole 11 mm deep up its underside on its pivot axis and rides on the boss with its underside at Z 8.5.",
     "yielding": "base",
     "poses": {"steps": 12, "movers": [
       {"component": "left-half", "rotation": {"axis_point": [-5, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": -15, "end_deg": 75}},
       {"component": "right-half", "driven": true, "rotation": {"axis_point": [5, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 15, "end_deg": -75}}]}},
    {"id": "head-pivots", "kind": "coupled", "components": ["head", "left-half", "right-half"],
     "text": "The head's flat underside carries two 4.0 mm pins 10 mm long at X -5 and X +5, Y 0, each inside a 10 mm boss 0.5 mm tall that rests on a half's top face at Z 68.5; each half has a 4.4 mm hole 11 mm deep down from its top face on its pivot axis.",
     "yielding": "head",
     "poses": {"steps": 12, "movers": [
       {"component": "left-half", "rotation": {"axis_point": [-5, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": -15, "end_deg": 75}},
       {"component": "right-half", "driven": true, "rotation": {"axis_point": [5, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 15, "end_deg": -75}}]}}
  ]
}
```
