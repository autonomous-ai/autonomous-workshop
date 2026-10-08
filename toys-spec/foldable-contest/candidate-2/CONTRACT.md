# Tip Fold

A desk toy for people who keep a steel ball on their desk anyway. A small
landscape slab stands folded on a leaning easel. Drop a steel ball into the
scoop on its front and the ball's weight tips the front leaf over: it swings
down through 180 degrees and lands open on the easel, and the small slab has
become one twice as tall, with a single hinge crease across its middle. The
ball spills out of the scoop part-way down and rolls into the dish in front.
Fold the leaf back up, put the ball back, and do it again.

Designer personality: Gravity Runner. Weight does all the work. There is no
spring, no catch and no motor: where the mass sits on the front leaf, and how
far the easel leans back, decide that the leaf stays shut on its own and
falls open with the ball in it. Mass placement is the design.

## Trend Hook

One horizontal hinge crease: two equal 80 x 46 mm leaves joined by a single
hinge that opens flat, 180 degrees, so the folded 80 x 51 mm slab becomes
one 80 x 102 mm slab with one crease line across its middle - a small thing
that opens like a book into a big one. Point at the crease and the toy is
explained. There is no phone detail anywhere: no camera, no buttons, no logo,
no maker's name; the leaves are plain slabs with a matte recessed inner panel.

## Signature Motion

What moves: the drop leaf, turning 180 degrees about the horizontal hinge
axis, from closed (standing up in front of the upper leaf) to open (lying on
the easel face below the hinge, flush with the upper leaf).

What drives it: gravity alone. The easel leans back 10 degrees, so with no
ball the closed drop leaf's centre of mass sits 1.8 mm behind the hinge axis
and it rests shut against the upper leaf. A 12.7 mm steel ball (8.4 g) in the
scoop sits 5.7 mm in front of the axis and outweighs that, so the leaf tips
forward; past 4 degrees the leaf's own weight carries it the rest of the way.
At about 55 degrees the scoop's mouth faces forward-down and the ball spills
into the dish; the leaf falls on and lands open on the easel face.

What the player does: drops the ball into the scoop, watches the fold fall
open, picks the ball out of the dish, folds the leaf back up and drops again.

## Parts

Three printed Unique Geometries and two purchased parts:

| Geometry | Count | Role |
|---|---|---|
| easel | 1 | base plate with ball dish, leaning panel, hinge ears |
| upper-leaf | 1 | fixed top half of the fold, pegged to the easel |
| drop-leaf | 1 | moving bottom half: hinge barrel and ball scoop (Focal Component) |

Purchased: one Ø3 x 94 mm steel rod (the hinge pin) and one 12.7 mm (1/2 in)
chrome steel ball.

**Focal Component: the drop leaf.** It carries the motion, the crease barrel
and the scoop. It costs the easel its plainness: the easel must give up a
window behind the scoop and carry hinge ears that stand proud of its face.

## Frame and coordinates

Assembly frame: X along the hinge (right +), Y depth with the front at -Y, Z
up from the desk. The hinge axis runs along X at Y 0, Z 75. The leaf plane P
contains the axis and leans back 10 degrees from vertical: up along P is
u = (0, 0.174, 0.985), out of P toward the front is n = (0, -0.985, 0.174).
A point on a leaf is written as s along u and t along n from the axis.

Display Pose: open. The drop leaf lies on the easel face below the hinge,
flush with the upper leaf above it, and the ball rests in the dish.

## Per-geometry spec

**easel.** Base plate 100 (X) x 92 (Y, from Y -62 to 30) x 8 mm, top at Z 8,
bottom face on the desk. A ball dish is sunk into the base's front: 60 (X) x
34 (Y, Y -58 to -24) x 4 mm deep, with a 3 mm fillet round its floor. From
the base rises the panel: 96 mm wide (X -48 to 48), 8 mm thick, its front
face on the plane t = -5.6 (5.6 mm behind P), leaning back 10 degrees, top
edge at Z 128. Two hinge ears stand out of the face at X -47 to -41 and
X 41 to 47, each reaching forward round the axis to a 5 mm radius, with a
Ø3.0 press hole for the pin on the axis (teardrop top) and a 45 degree
chamfered underside. A window through the panel for the scoop: 24 mm wide
(X -12 to 12), from s -56 to s -30, with a pointed-arch top. Two Ø4.4 x 5 mm
deep sockets for the upper leaf's pegs at X -25 and 25, s 28, with teardrop
tops. Wall minimum 3 mm.

**upper-leaf.** Plate 80 (X) x 46 (along u) x 5 mm, from s 5 to s 51, from
t -5.6 to t -0.6, corners rounded R4. Its inner (front) face carries a matte
inner panel recessed 0.6 mm, 72 x 38 mm, leaving a 4 mm border. Its outer
(back) face carries two Ø4 x 4 mm pegs at X -25 and 25, s 28, into the
easel's sockets, and is otherwise plain.

**drop-leaf.** The same plate, 80 x 46 x 5 mm with R4 corners and the same
0.6 mm recessed 72 x 38 inner panel. Open, it runs from s -5 to s -51 at
t -5.6 to -0.6 (lying on the easel face); closed, from s 5 to s 51 at t 0.6
to 5.6, a 1.2 mm gap from the upper leaf. Along its hinge edge, a knuckle
barrel Ø8 x 80 mm (X -40 to 40) centred on the axis, with a Ø3.4 free bore,
joined to the plate by a 5 mm web. On its outer face at the free end, the
ball scoop: a block 20 (X) x 18 (along the leaf) x 16 mm proud of the outer
face, centred on X 0, flush with the free edge, with a Ø13.5 x 10 mm deep
pocket whose mouth opens through the free edge. Printed at 100% infill so
its mass is the one the balance assumes (about 23 g plate, 3 g scoop).

## Joints

- **upper-leaf on easel (static):** two Ø4 x 4 pegs on the upper leaf's
  outer face at X -25 and 25, s 28, in two Ø4.4 x 5 sockets in the easel
  face, 0.2 mm clearance a side, glued.
- **hinge (coupled):** the drop leaf's barrel (X -40 to 40, Ø8, bore Ø3.4)
  sits between the easel's two ears (inner faces at X -41 and 41, 1 mm gap a
  side). The Ø3 x 94 steel pin presses into both ears' Ø3.0 holes and runs
  free through the barrel's Ø3.4 bore. The barrel's 4 mm radius keeps 1.6 mm
  clear of the easel face at t -5.6, and the 10 mm crease gap between the
  leaves' hinge edges (s -5 to 5) keeps 1 mm clear of the barrel each side.

## Motion and fit

The drop leaf turns about the axis (X, through Y 0, Z 75) through 180
degrees: -180 degrees (closed) to 0 (open, the Display Pose), positive about
+X. Closed, it rests leaning back against the upper leaf; open, its outer
face rests on the easel face, and the scoop passes through the panel
window with at least 1 mm clearance. Through the whole travel it keeps at
least 0.5 mm from the easel, the ears and the upper leaf. The ball dish lies
below the leaf's sweep: at Y -45 the sweep's lowest point is Z 45, the dish
floor Z 4.

Balance, with the leaf closed: plate centre of mass at s 28, t 3.1 sits 1.8
mm behind the axis (restoring); scoop at s 42, t 13.6 sits 6.1 mm in front;
ball centre at s 44, t 13.6 sits 5.7 mm in front. Without the ball the leaf
stays shut; with it, it tips.

Motion plan: `--check-motion true` on the wish and on every resume and
correction; one sweep of the full 180 degree travel, at most 10 steps,
against only the easel and the upper leaf; a skipped, killed or timed-out
sweep fails the motion requirement, never passes it.

## Print

- easel: on its base underside. The panel's back face leans 10 degrees, the
  ears have chamfered undersides, the window a pointed-arch top, all holes
  teardrop tops.
- upper-leaf: on its inner face, pegs up.
- drop-leaf: standing on its left end face (X -40), so the bore prints
  vertical and the scoop's walls stand vertical.

Every point, chisel, keel and V underside ends in a flat land at least 0.8 mm
across (one print minimum at a 0.4 mm nozzle). A drawn detail under the print
minimums is enlarged to the minimum; when the enlarged detail does not fit
its spot, it is left out, and this contract names it.

Colours: easel warm light grey; both leaves charcoal with mid-grey matte inner
panels; the pin and ball bare steel.

## Fixed-frame plan and handling

At 35 degrees azimuth, 22 degrees elevation against #f5f0e6, the open slab
faces the camera and the crease barrel across its middle is the focal line,
with the ball in the dish below it. Handling: the toy is held by the base;
the ears are the first thing to break if the drop leaf is forced past open,
which the easel face prevents. Nothing load-bearing is under 3 mm.

```design-contract
{
  "schema_version": 4,
  "title": "Tip Fold",
  "inventor": "trend-lab",
  "envelope_mm": [100, 92, 128],
  "references": [
    {"file": "ref-01-tip-fold.png", "shows": "assembly", "camera": [-75, 15]},
    {"file": "ref-02-easel.png", "shows": "geometry:easel", "camera": [-60, 15]},
    {"file": "ref-03-upper-leaf.png", "shows": "geometry:upper-leaf", "camera": [-90, 0]},
    {"file": "ref-04-drop-leaf.png", "shows": "geometry:drop-leaf", "camera": [-60, 15]}
  ],
  "geometries": [
    {"id": "easel", "name": "Leaning easel with ball dish", "count": 1,
     "extents_mm": [100, 92, 128], "wall_min_mm": 3.0},
    {"id": "upper-leaf", "name": "Fixed upper leaf", "count": 1,
     "extents_mm": [80, 46, 9], "wall_min_mm": 3.0},
    {"id": "drop-leaf", "name": "Drop leaf with scoop", "count": 1,
     "extents_mm": [80, 55, 25], "wall_min_mm": 3.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly",
     "text": "Display Pose: the drop leaf lies open on the easel face below the hinge, flush with the upper leaf, the two forming one 80 x 102 mm slab with a single horizontal hinge crease across its middle; the 12.7 mm steel ball rests in the base's front dish."},
    {"id": "R02", "scope": "assembly",
     "text": "The hinge axis is horizontal along X at Y 0, Z 75, and the leaf plane leans back 10 degrees from vertical."},
    {"id": "R03", "scope": "assembly",
     "text": "The drop leaf turns 180 degrees about the hinge, from closed (standing in front of the upper leaf, 1.2 mm gap) to open (lying on the easel face), keeping at least 0.5 mm from the easel, the ears and the upper leaf through the whole travel; one sweep of at most 10 steps, and a skipped, killed or timed-out sweep fails this requirement."},
    {"id": "R04", "scope": "assembly",
     "text": "Gravity alone drives the motion: no spring, catch or motor. Closed and without the ball, the drop leaf's centre of mass sits behind the hinge axis so it stays shut; the ball in the scoop sits in front of the axis and tips it open."},
    {"id": "R05", "scope": "assembly",
     "text": "The hinge pin is one purchased Ø3 x 94 mm steel rod pressed into both easel ears and running free through the drop leaf's barrel; the ball is one purchased 12.7 mm chrome steel ball."},
    {"id": "R06", "scope": "assembly",
     "text": "The ball dish lies below the drop leaf's whole sweep, so a ball in the dish never meets the leaf."},
    {"id": "R07", "scope": "assembly",
     "text": "No phone detail anywhere: no camera, buttons, logo, lettering or maker's name; easel warm light grey, leaves charcoal with mid-grey matte inner panels, pin and ball bare steel."},
    {"id": "R08", "scope": "assembly",
     "text": "At 35 degrees azimuth and 22 degrees elevation the open slab faces the camera and the crease barrel across its middle is the focal line, with the ball in the dish below it."},
    {"id": "R09", "scope": "geometry:easel",
     "text": "A 100 x 92 x 8 mm base plate with a 60 x 34 x 4 mm ball dish sunk into its front, and a 96 mm wide, 8 mm thick panel leaning back 10 degrees to Z 128."},
    {"id": "R10", "scope": "geometry:easel",
     "text": "Two hinge ears at X -47 to -41 and 41 to 47 reach round the axis to a 5 mm radius, each with a Ø3.0 teardrop-topped press hole and a 45 degree chamfered underside."},
    {"id": "R11", "scope": "geometry:easel",
     "text": "A 24 mm wide window through the panel from s -56 to s -30 with a pointed-arch top receives the scoop; two Ø4.4 x 5 mm teardrop-topped sockets at X -25 and 25, s 28 take the upper leaf's pegs. Prints on its base underside."},
    {"id": "R12", "scope": "geometry:upper-leaf",
     "text": "An 80 x 46 x 5 mm plate with R4 corners whose inner face carries a 72 x 38 mm matte panel recessed 0.6 mm inside a 4 mm border."},
    {"id": "R13", "scope": "geometry:upper-leaf",
     "text": "Its outer face carries two Ø4 x 4 mm pegs at X -25 and 25, s 28, and is otherwise plain. Prints on its inner face."},
    {"id": "R14", "scope": "geometry:drop-leaf",
     "text": "An 80 x 46 x 5 mm plate with R4 corners and the same 72 x 38 mm matte inner panel recessed 0.6 mm inside a 4 mm border."},
    {"id": "R15", "scope": "geometry:drop-leaf",
     "text": "Along its hinge edge a Ø8 x 80 mm knuckle barrel centred on the axis, with a Ø3.4 free bore, joined to the plate by a 5 mm web."},
    {"id": "R16", "scope": "geometry:drop-leaf",
     "text": "On its outer face at the free end a 20 x 18 mm ball scoop standing 16 mm proud, centred on X 0, with a Ø13.5 x 10 mm pocket whose mouth opens through the free edge."},
    {"id": "R17", "scope": "geometry:drop-leaf",
     "text": "Prints standing on its left end face at 100% infill, so its mass is the one the balance assumes."}
  ],
  "interfaces": [
    {"id": "upper-leaf-mount", "kind": "static", "components": ["upper-leaf", "easel"],
     "text": "The upper leaf's outer face carries two Ø4 x 4 mm pegs at X -25 and 25, s 28; the easel face has two Ø4.4 x 5 mm teardrop-topped sockets at the same places. The upper leaf's outer face seats flat on the easel face at t -5.6, glued."},
    {"id": "fold-hinge", "kind": "coupled", "components": ["drop-leaf", "easel", "upper-leaf"],
     "text": "The drop leaf's Ø8 x 80 mm barrel (X -40 to 40, bore Ø3.4) turns on a Ø3 x 94 mm steel pin pressed into Ø3.0 holes in the easel's two ears (inner faces at X -41 and 41). The drop leaf turns 180 degrees about X through Y 0, Z 75: closed it stands 1.2 mm in front of the upper leaf's inner face; open its outer face rests on the easel face at t -5.6 and its scoop passes through the easel's 24 mm window with at least 1 mm clearance. The easel and upper leaf keep at least 0.5 mm clear of the drop leaf through the travel.",
     "yielding": "drop-leaf",
     "poses": {"steps": 10, "movers": [
       {"component": "drop-leaf", "rotation": {"axis_point": [0, 0, 75],
        "axis_direction": [1, 0, 0], "start_deg": -180, "end_deg": 0}}]}}
  ]
}
```
