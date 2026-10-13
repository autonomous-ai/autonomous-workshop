# Racer Mecha

A chunky heroic robot, 197 mm to the top of its helmet, that transforms by
hand into an open-wheel Formula racing car 276.5 mm long that rolls on four
wheels. Every part stays attached through the transformation: nothing is
removed, nothing is left over. The robot is the car stood up on its tail and
opened out: the car's cockpit with its halo is the robot's chest, its front
wheels sit on the shoulders, its front sidepods are the arms, its rear body
is the legs, its rear wheels are on the calves, its tail is the boots, and
the two halves of its rear wing fold onto the toes. The nose lies down the
robot's back with the front wing behind the hips. In the car the robot lies
on its back: its back is the floor, its chest is the top.

Inventor: `rowan-vale`. Detail and motion share the object: the robot is
judged on its silhouette and the car on whether every part packs back into
it.

## Unique geometries

| Geometry | Count | Robot | Car |
|---|---|---|---|
| `torso` | 1 | Chest with the cockpit and halo, shoulders, hips | Monocoque, cockpit and halo, inner sidepods |
| `nose` | 1 | Lies down the back, front wing behind the hips | Nose cone and front wing |
| `head` | 1 | Helmeted head with a visor | Pushed down into its pocket under the nose root |
| `arm-shell` | 2 | Upper arm | Front sidepod, outer half |
| `forearm` | 2 | Forearm and fist | Folded inside the sidepod |
| `thigh` | 2 | Thigh, a sleeve | Rear body, front half |
| `shin` | 2 | Shin, with the slide post above it | Rear body, rear half |
| `boot` | 2 | Boot, a long foot | Tail: gearbox and diffuser |
| `wing` | 2 | Toe cap with a raised blade | One half of the rear wing |
| `front-wheel` | 2 | On the shoulders | Front wheels |
| `rear-wheel` | 2 | On the outer sides of the calves | Rear wheels |

`arm-shell#2`, `forearm#2`, `thigh#2`, `shin#2`, `boot#2` and `wing#2` are
the mirror images of `#1`. Every `#1`, including `front-wheel#1` and
`rear-wheel#1`, is on the +X side.

**Focal Component: the torso.** In the Display Pose the cockpit opening with
its red halo, in the middle of the chest, is the form the eye goes to first,
framed by the front wheels on the shoulders above it. It costs the nose its
show: the nose, the most car-like part, lies down the back and reads only from
behind and in the car.

## Frame, poses and composition

Assembly coordinates in millimetres, in the Display Pose: X toward the
figure's left, front is -Y, Z up from the desk; the figure is centred on X 0.

**Display Pose: robot.** Standing upright on both boots, arms hanging
straight at the sides, legs straight and drawn out to full length, head
raised, nose lying down the back, wing halves folded on the toes. Envelope
101 (X) x 57 (Y, -30 to 27) x 207 (Z). Landmarks: boots 0 to 20, ankle pins
12.25, shin block 20.5 to 53.5, rear wheel axles 50, the bare slide post 53.5
to 70, thigh 70 to 96.5, hip pins 102, torso 99 to 180, cockpit 128 to 157
inside a halo 126 to 160, shoulder pins 157, helmet 178 to 197, front wheel
axles 188 and tops 207; behind: the nose hinge at Z 182, the front wing 96 to
109. Widths: arms across 101, front wheels across 94, torso 58, the nose's
front wing 84, legs 1 apart and 60 across, boots 29 wide and 5 apart, rear
wheels across 85.

**Car pose.** Reached by the moves under Transformation. In assembly
coordinates the car stands on its tail: its length runs along Z (-8.5 to
268), its floor faces +Y and its top -Y. Laid down on its floor it is 276.5
long, 101 wide across the front sidepods and 39 tall, resting on all four
wheels with the nose 1.5 above the ground and every other part at least 3.

Release frames the robot in the Display Pose against `#f5f0e6`. From the
assembly reference's camera, straight from the front, the cockpit and halo
sit on the frame's vertical centre line. From Release's hero camera (35
degrees round from the front, 26 up; `render_review` [-55, 26] or [-125, 26])
the cockpit faces the camera unobstructed, the nearer arm 40 mm to its side
on screen.

## Palette

Multi-colour prints; colours change only at the boundaries named here.

| Geometry | Colour |
|---|---|
| `torso` | black, with a red halo |
| `nose` | racing red cone with a white stripe down each side; black front wing with red endplates |
| `head` | white and red helmet, blue visor band |
| `arm-shell` | white with two red panels on its front face |
| `forearm` | white with red side panels, black fist |
| `thigh` | racing red |
| `shin` | racing red with a white stripe panel down the front; black slide post |
| `boot` | black |
| `wing` | black plate, red blade |
| `front-wheel`, `rear-wheel` | black |

## Per-geometry spec

All positions are in the Display Pose; the `#1` part is given and `#2`
mirrors X.

**Torso.** A core block 58 wide (X -29 to 29) x 26 deep (Y -13 to 13), Z 99
to 180. A head pocket 21 x 19 (X -10.5 to 10.5, Y -10 to 9), open at the top,
floor at Z 156; a notch 13 wide (X -6.5 to 6.5) cuts its front wall down to Z
170, so the neck shows. A 9 x 9 neck bore (X -4.5 to 4.5, Y -1 to 8) runs from
the pocket floor down to Z 119. Two wheel towers, X 16 to 29 each side, Y -13
to 13, rise to Z 192; each carries an Ø8 stub boss out to X 30.5 on the axis
Y 0, Z 188, with a gusset under it rising at 52 degrees. On the front: the
cockpit, an opening 16 wide (X -8 to 8) and 6 deep (to Y -7) over Z 128 to
157, its top edge rising at 52 degrees, and round it a raised halo hoop 7
proud (Y -20 to -13), X -11 to 11, Z 126 to 160, of two 3 wide legs and a 3
thick top bar over the opening, the legs and the bar's underside growing out
of the chest at a 52 degree rise. At the top of the back, two Ø7 nose hinge
cheeks (X 10.5 to 14.5 each side) on the axis Y 14, Z 182, each with a 52
degree gusset under it, flanking the nose knuckle's seat, a cylinder of
radius 4 about the axis over X -10.5 to 10.5. The back is otherwise plain
blocks. The bottom carries two hip slots (X 3.5 to 14.5 each side, Y -9 to 5,
Z 99 to 108, pointed-arch tops). Each side wall carries the shoulder bore
along X at Y -2, Z 157; the cockpit's back wall (Y -7 to -1) and the pocket's
back wall (Y 8 to 13) carry the head retainer's bores along Y at X 0, Z 149.5.
Walls 3.0. Prints standing on its bottom face (Z 99).

**Nose.** One part, lying down the back. A knuckle 20 wide (X -10 to 10) on
the hinge axis Y 14, Z 182: round, radius 3.5, toward the top and a teardrop
toward the root, its point 5.7 from the axis and its faces 38 degrees from
the cone's axis. A root block 20 wide (Y 13.5 to 21, Z 172 to 179) joins it to
the cone. The cone runs down the back, its outer face sculpted as a nose cone:
18 wide and 13.5 deep (Y 13.5 to 27) from Z 172 to 140, then 12 wide and 10.5
deep (Y 13.5 to 24) down to its blunt tip at Z 109, 4 wide; the step at Z 140
rises at 52 degrees. The front wing at the tip: a plate 84 wide (X -42 to 42)
x 13 tall (Z 96 to 109) x 6 thick (Y 13.5 to 19.5), with an endplate 3 wide x
10.5 deep (Y 13.5 to 24) at each end (X 39 to 42); the cone's tip overlaps
the wing's upper half. Prints standing on the wing's lower face (Z 96).

**Head.** A helmet 19 wide x 16 deep (Y -7.5 to 8.5) x 19 tall (Z 178 to 197)
with a blue visor band across its front face and a raised crest, 2 wide and
1.5 high, along its top centre line. Under it a square neck post 8 x 8
(X -4 to 4, Y -0.5 to 7.5), Z 143 to 178, its back face flush with the
helmet's, with a slot 3.4 wide (X -1.7 to 1.7) through it from front to back
from Z 147.9 to 173.1. Prints on its back face.

**Arm shell.** A C-channel 20 wide (X 30.5 to 50.5) x 22 deep (Y -13 to 9),
Z 118 to 163: front wall 3, inboard and outboard walls 2.5, open at the back
and the bottom; a forearm cavity X 33 to 48, Y -10 to 9, Z 118 to 152.6;
above it a solid top block whose top rises at 52 degrees from the front
face (Y -13, Z 157) to a flat at Z 163 from Y -5.3 to 3, then falls at 45
degrees to the back face (Y 9, Z 157). Two red panels on its front face. Two
elbow cheeks (X 30.5 to 33 and 48 to 50.5) reach down to Z 118, rounded about
the elbow axis Y -2, Z 124. The shoulder bore runs along X through the top
block at Y -2, Z 157. Prints on its front face.

**Forearm.** A block 14 wide (X 33.5 to 47.5) x 15 deep (Y -9.5 to 5.5),
Z 97 to 124, ending at the top in a knuckle rounded R7.5 about the elbow axis
Y -2, Z 124; the bottom 9 is a closed black fist as wide as the forearm: four
fingers split by three vertical grooves, crossed by two knuckle grooves.
Prints on its outboard face.

**Thigh.** A sleeve 25 wide (X 0.5 to 25.5) x 22 deep (Y -13 to 9), Z 70 to
93.5, open at the bottom: its cavity X 3 to 23, Y -10.5 to 6.5, up to a 3
thick roof at Z 93.5, walls 2.5. Above the roof it steps in to Y -10 to 6 up
to Z 96.5 and is topped by a hip tongue 10 wide (X 4 to 14) x 7.4 deep (Y -5.7
to 1.7) to Z 102, rounded R3.7 about the hip axis Y -2, Z 102. Each side wall
(X 0.5 to 3 and 23 to 25.5) carries a slide slot along Z at Y -2, 3.2 wide,
its ends rounded about Z 73 and Z 89, narrowed to 2.8 for 1 just inside each
end so the dowel clicks into the end. Prints standing on its bottom face
(Z 70).

**Shin.** A block 29.5 wide (X 0.5 to 30) x 22 deep (Y -13 to 9), Z 20.5 to
53.5, with a raised knee pad 16 wide x 10 tall x 1.0 proud at its top front
and a white stripe panel down its front. On top the slide post, 19 wide (X
3.5 to 22.5) x 16 deep (Y -10 to 6), Z 53.5 to 77; the block's shoulders round
the post rise at 52 degrees toward the block. The post carries the slide
dowel's bore along X at Y -2, Z 73. Below the block the ankle tongue, 14 wide
(X 8 to 22) x 8 deep (Y -0.25 to 7.75), down to a round end R4 about the ankle
axis Y 3.75, Z 12.25. The rear wheel's bore runs along X into the block's
outer face at Y 2, Z 50. Prints upside down on the post's top face (Z 77).

**Boot.** A long foot 29 wide (X 2.5 to 31.5), Y -30 to 11.5, Z 0 to 20,
pointing forward, the way the robot faces: the toe is 17 ahead of the shin's
front. Behind the ankle axis its top is rounded R7.75 about the axis (Y 3.75,
Z 12.25) down to the heel face at Y 11.5. A slot for the shin's tongue, X 7.5
to 22.5, Y -0.75 to the heel, down to Z 7.75, open at the top and the heel.
The ankle bores run along X through the slot's side walls on the axis. The
instep in front of the shin is a flat at Z 19.5 from the toe to Y -13.5,
where the wing lies; at the toe two lugs (X 2.5 to 5 and 29 to 31.5), Y -30
to -26.5, rise to Z 27, rounded R3.5 about the wing hinge axis Y -26.5, Z
23.5. Prints on its sole.

**Wing.** One half of the rear wing, a single part. A knuckle Ø7 x 23 (X 5.5
to 28.5) on the wing hinge axis (Y -26.5, Z 23.5); a plate 23 wide (X 5.5 to
28.5) x 3 thick (Z 20 to 23) running from the knuckle to Y -14; and at the
plate's far end the blade, 30.75 wide (X 0.75 to 31.5) x 3 (Y -17 to -14) x
10 tall (Z 20 to 30), standing up 1 in front of the shin. In the car the
plate stands up as the wing's endplate and pylon and the blade points
rearward as the wing, the two halves' blades 1.5 apart at the centre line.
Prints on its flat underside (Z 20).

**Front wheel.** Ø38 x 16, a tyre with a plain tread and a five-spoke rim
face on its outer side, an Ø3.2 bore. Prints on its outer face.

**Rear wheel.** Ø34 x 12, the same tyre and five-spoke rim face, an Ø3.2
bore. Prints on its outer face.

## Joints

Every hinge is a purchased steel ISO 8734 dowel pin Ø3, pressed into Ø2.9
bores on one side and turning or sliding in Ø3.1 bores or slots (friction for
posing) or Ø3.2 bores (wheels) on the other. Each wheel is held by a purchased
Ø3 push-on cap (starlock) on the dowel's outer end. Every horizontal bore is a
teardrop with its point away from the bed. No glue.

| Joint | Dowel | Pressed into | Turns in | Axis |
|---|---|---|---|---|
| Nose hinge | 3 x 26 | torso back cheeks, 3.5 each | nose knuckle | X, at Y 14, Z 182 |
| Head retainer | 3 x 20 | cockpit back wall and pocket back wall | neck post slot | Y, at X 0, Z 149.5 |
| Shoulder | 3 x 20, each | arm shell top block | torso side wall | X, at Y -2, Z 157 |
| Elbow | 3 x 20, each | arm shell cheeks | forearm knuckle | X, at Y -2, Z 124 |
| Hip | 3 x 20, each | torso slot walls | thigh tongue | X, at Y -2, Z 102 |
| Knee slide | 3 x 24, each | shin post | thigh side-wall slots, Z 73 to 89 | X, at Y -2, Z 73 |
| Ankle | 3 x 28, each | boot slot walls | shin tongue | X, at Y 3.75, Z 12.25 |
| Wing hinge | 3 x 28, each | boot toe lugs | wing knuckle | X, at Y -26.5, Z 23.5 |
| Front wheels | 3 x 30, each | torso tower and stub boss, 12 deep | wheel bore | X, at Y 0, Z 188 |
| Rear wheels | 3 x 26, each | shin, 12 deep | wheel bore | X, at Y 2, Z 50 |

## Transformation

From robot to car, in this order (reverse for car to robot):

1. Push the head down 22 into its pocket.
2. Flip the nose 180 degrees up over the top of the back (+180 about +X):
   it stands above the torso over the head pocket, its front wing at the top
   (Z 255 to 268).
3. Fold each forearm up and back 180 degrees about its elbow (+180 about +X)
   into its arm shell's cavity.
4. Fold each boot 90 degrees at the ankle (+90 about +X): the toe points
   down, the sole faces the back.
5. Push each shin 16 up into its thigh: the slide post fills the sleeve.
6. Stand each wing half up 90 degrees on its hinge (+90 about +X): its
   plate rises from the boot and its blade points rearward; the two blades
   meet at the centre line, 1.5 apart.
7. Lay the car down on its back, on its wheels.

Posing in the robot: shoulders 90 forward and 5 back (the front wing behind
the hips stops them); hips 20 forward and 20 back. The knees do not bend:
the legs slide. The elbows do not bend forward: the arm shell's front wall
reaches its bottom.

## Motion and fit

- Every moving part keeps at least 0.5 mm from every other part through each
  transformation move and each posing range, and in both poses, except at
  the contacts the Interfaces themselves declare: the head-slide dowel
  stopping against the neck post's slot, the lowered helmet resting on the
  pocket floor, and the knee-slide dowel stopping at its slot ends.
- Motion check plan: `--check-motion true` on the wish and on every resume
  and correction; one sweep per transformation move (head, nose, forearm#1,
  forearm#2, boot#1, boot#2, shin#1, shin#2, wing#1, wing#2) in at most 10
  steps, each against only the parts it can reach. A skipped, killed or
  timed-out sweep fails the motion requirement, never passes it.
- In the car pose the wheels are the lowest parts: the nose knuckle stands
  1.5 above the ground, the boots 3, the torso 6.
- The knee-slide dowel's clicks hold the robot standing at full length and
  the car at its short length; the ankle and wing hinges hold by friction.
- Assembled, not printed in place: press each dowel from outside after
  seating its part; the head's retainer dowel goes in last through the
  torso's back.

## Print and handling

Workshop prints at a 0.4 mm nozzle; every part prints without support in
the stance named above. Every point, chisel, keel and V underside ends in a
flat land at least 0.8 mm across (one print minimum at a 0.4 mm nozzle). A
drawn detail under the print minimums is enlarged to the minimum; when the
enlarged detail does not fit its spot, it is left out, and this contract
names it. Panel lines and finger grooves are engraved 0.6 wide and 0.5 deep;
nothing is left out. Every chamfer, gusset, arch, wedge and teardrop is
designed at most 38 degrees from vertical (a 52 degree rise), the
print-details design limit, inside the gate's 45.

The toy reads as built from small blocks, as ref-01 draws it, not as plain
slabs. Every large face (over 15 across) of the torso, thigh, shin, boot,
arm shell, forearm and nose cone is split by seams 0.6 wide and 0.5 deep
into blocks 5 to 15 across, offset between rows like brickwork, and on each
front face at least two blocks stand 0.6 proud of their neighbours. Every
exposed outside edge carries a chamfer 0.8 across, rising at 52 degrees on
an edge that faces down in the print stance; edges on the print-bed face,
at a bore, a slot, a joint face, or on any face another part comes within
2 mm of in a pose or move stay square, and no proud block stands there.
A seam is the one cut allowed into a load-bearing wall: the arm shell's and
the thigh's 2.5 walls keep 2.0 under a seam, and no seam runs where it would
leave less than a part's floor below.

Load-bearing sections are at least 3 mm: torso walls 3.0, arm shell walls
2.5 beside a 3.0 front wall, thigh walls 2.5, every tongue at least 7.4 deep,
the slide post 16, the neck post 8, the wing plate and blade 3. The one
exception is the material around a dowel bore, which the joints above size:
above a teardrop bore (its faces 38 degrees from vertical) inside a Ø7
cheek, lug or knuckle 1.1 is left on the torso and the boot, 0.95 on the
nose and the wing; between the slide slot's end at Z 73 and the thigh's
bottom face 1.4; between a bore at Z 102 and the hip slot's bottom 3 below
it 1.55 on the torso; beside the neck post's 3.4 slot 2.3; around an R3.7 or
R4 tongue's Ø3.1 bore 2.15 or 2.45. So the torso and the boot hold a 1.1
floor, the nose and the wing 0.95, the thigh 1.4 and the head and shin 1.9,
and nothing on them is thinner than these joints force. A drop lands on a
shoulder wheel or a boot; the wheels, the wing halves and the head are the
first to come loose, and each presses back on its dowel. The robot stands
unsupported: its centre of mass lies at Y -1, 29 behind the toes and 12.5
ahead of the heels.

```design-contract
{
  "schema_version": 4,
  "title": "Racer Mecha",
  "inventor": "rowan-vale",
  "envelope_mm": [101, 57, 207],
  "references": [
    {"file": "ref-01-racer-mecha.png", "shows": "assembly", "camera": [-90, 0]},
    {"file": "ref-02-torso.png", "shows": "geometry:torso", "camera": [-90, 0]},
    {"file": "ref-03-nose.png", "shows": "geometry:nose", "camera": [90, 0]},
    {"file": "ref-04-head.png", "shows": "geometry:head", "camera": [-90, 0]},
    {"file": "ref-05-arm-shell.png", "shows": "geometry:arm-shell", "camera": [-90, 0]},
    {"file": "ref-06-forearm.png", "shows": "geometry:forearm", "camera": [-90, 0]},
    {"file": "ref-07-thigh.png", "shows": "geometry:thigh", "camera": [-90, 0]},
    {"file": "ref-08-shin.png", "shows": "geometry:shin", "camera": [-90, 0]},
    {"file": "ref-09-boot.png", "shows": "geometry:boot", "camera": [0, 0]},
    {"file": "ref-10-wing.png", "shows": "geometry:wing", "camera": [-45, 30]},
    {"file": "ref-11-front-wheel.png", "shows": "geometry:front-wheel", "camera": [0, 0]},
    {"file": "ref-12-rear-wheel.png", "shows": "geometry:rear-wheel", "camera": [0, 0]}
  ],
  "geometries": [
    {"id": "torso", "name": "Torso", "count": 1, "extents_mm": [61, 37.5, 93], "wall_min_mm": 1.1},
    {"id": "nose", "name": "Nose and front wing", "count": 1, "extents_mm": [84, 16.5, 89.5], "wall_min_mm": 0.95},
    {"id": "head", "name": "Head", "count": 1, "extents_mm": [19, 16, 54], "wall_min_mm": 1.9},
    {"id": "arm-shell", "name": "Upper arm shell", "count": 2, "extents_mm": [20, 22, 45], "wall_min_mm": 2.0},
    {"id": "forearm", "name": "Forearm and fist", "count": 2, "extents_mm": [14, 15, 34.5], "wall_min_mm": 3.0},
    {"id": "thigh", "name": "Thigh sleeve", "count": 2, "extents_mm": [25, 22, 35.7], "wall_min_mm": 1.4},
    {"id": "shin", "name": "Shin and slide post", "count": 2, "extents_mm": [29.5, 22, 68.75], "wall_min_mm": 1.9},
    {"id": "boot", "name": "Boot", "count": 2, "extents_mm": [29, 41.5, 27], "wall_min_mm": 1.1},
    {"id": "wing", "name": "Rear-wing half", "count": 2, "extents_mm": [30.75, 16, 10], "wall_min_mm": 0.95},
    {"id": "front-wheel", "name": "Front wheel", "count": 2, "extents_mm": [38, 38, 16], "wall_min_mm": 2.0},
    {"id": "rear-wheel", "name": "Rear wheel", "count": 2, "extents_mm": [34, 34, 12], "wall_min_mm": 2.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly", "text": "In the Display Pose the robot stands upright on both boots, its helmet top at Z 197, arms hanging straight: the cockpit opening framed by the red halo sits in the middle of the chest from Z 126 to 160, a front wheel sits on each shoulder at Z 188, a rear wheel on the outer side of each calf at Z 50, the black slide post shows between each shin and thigh from Z 53.5 to 70, and each boot carries a folded wing half whose red blade stands in front of the shin."},
    {"id": "R02", "scope": "assembly", "text": "From behind, the nose lies down the middle of the robot's back from its hinge at Z 182, its front wing 84 wide across the back of the hips from Z 96 to 109, and nothing else rises behind the head."},
    {"id": "R03", "scope": "assembly", "text": "In the car pose the toy is an open-wheel Formula car 276.5 mm long, 101 wide and 39 tall, lying on the robot's back: nose cone and front wing ahead of the front wheels, the cockpit and halo on top, the arm shells as front sidepods, the legs side by side as the rear body, the boots as the tail, and the two wing halves standing on the boots as the rear wing, their blades meeting at the centre line."},
    {"id": "R04", "scope": "assembly", "text": "The robot becomes the car by seven moves and no part comes off: the head slides 22 down into its pocket, the nose flips 180 degrees up over the top of the back, each forearm folds 180 degrees into its arm shell, each boot folds 90 degrees at the ankle, each shin slides 16 up into its thigh, each wing half stands up 90 degrees on its hinge, and the car is laid on its back."},
    {"id": "R05", "scope": "assembly", "text": "In the car pose the car rests on all four wheels, the nose 1.5 mm and every other part at least 3 mm above the ground, and each wheel turns freely on its dowel."},
    {"id": "R06", "scope": "assembly", "text": "Posing ranges in the robot: shoulders 90 degrees forward and 5 back, hips 20 forward and 20 back, each holding its pose by friction; the knees do not bend, the legs slide."},
    {"id": "R07", "scope": "assembly", "text": "Every moving part keeps at least 0.5 mm from every other part through each transformation move and posing range and in both poses, except at the contacts the Interfaces declare: the head-slide dowel stopping in the neck post's slot, the lowered helmet on the pocket floor, and the knee-slide dowel stopping at its slot ends. Checked with --check-motion true: one sweep per transformation move in at most 10 steps against only the parts it can reach; a skipped, killed or timed-out sweep fails this requirement."},
    {"id": "R08", "scope": "assembly", "text": "Every purchased-part seat is derived from a catalog STEP file, or from the documented envelope when the catalog search is a recorded miss, and the bill of materials lists exactly 7 dowels 3 x 20, 2 dowels 3 x 24, 3 dowels 3 x 26, 4 dowels 3 x 28, 2 dowels 3 x 30 and 4 push-on caps for 3 mm shafts."},
    {"id": "R09", "scope": "assembly", "text": "Every joint is built as its Interface text states, each hinge or slide a purchased dowel pressed into a 2.9 mm bore on one side and turning or sliding in a 3.1 mm bore or slot (3.2 for the wheels) on the other, with no glue; each knee-slide slot narrows to 2.8 for 1 mm inside each end so the dowel clicks into the end and holds."},
    {"id": "R10", "scope": "assembly", "text": "The robot stands unsupported in the Display Pose: its centre of mass lies over the boots, which span Y -30 at the toes to 11.5 at the heels; each foot points forward, its toe 17 ahead of the shin's front."},
    {"id": "R11", "scope": "geometry:torso", "text": "A 58 x 26 core built from blocks, its front, sides and back split by seams with proud blocks on the front, and two wheel towers 13 wide rising 12 above its top corners; between them an open head pocket whose front wall has a 13 wide notch so the neck shows."},
    {"id": "R12", "scope": "geometry:torso", "text": "On the front a cockpit opening 16 wide and 6 deep under a red halo hoop 7 proud, of two 3 wide legs and a 3 thick top bar; an 8 mm stub boss on the outer side of each tower for a front wheel; two 7 mm nose hinge cheeks at the top of the back."},
    {"id": "R13", "scope": "geometry:nose", "text": "A red nose cone with a white stripe down each side, 18 wide at its root tapering to 12, ending in a blunt 4 wide tip, its root on a hinge knuckle 20 wide; it lies down the robot's back."},
    {"id": "R14", "scope": "geometry:nose", "text": "At the tip a black front wing 84 wide and 13 tall with a red endplate 3 wide at each end; the cone's tip overlaps the wing's upper half."},
    {"id": "R15", "scope": "geometry:head", "text": "A white and red helmet 19 wide and 19 tall with a blue visor band across its front and a raised crest along its top centre line, on a square 8 mm neck post 35 long with a 3.4 wide slot through it from front to back."},
    {"id": "R16", "scope": "geometry:arm-shell", "text": "A 20 x 22 white channel open at the back and the bottom, its top chamfered front and back, its faces split into blocks by seams, with two elbow cheeks at its bottom and two red panels on its front face."},
    {"id": "R17", "scope": "geometry:forearm", "text": "A 14 x 15 white forearm with red side panels, ending at the top in a rounded knuckle and at the bottom in a closed black fist 9 tall and as wide as the forearm, four fingers split by three vertical grooves and crossed by two knuckle grooves."},
    {"id": "R18", "scope": "geometry:thigh", "text": "A 25 x 22 red sleeve 23.5 tall, open at the bottom, whose top steps in and rises into a rounded hip tongue 10 wide toward its inboard side, with a 3.2 wide slot along each side wall for 16 mm of slide; its front and outer side are split by seams into blocks, two of them standing proud on the front."},
    {"id": "R19", "scope": "geometry:shin", "text": "A 29.5 x 22 red shin block 33 tall with a raised knee pad and a white stripe panel on its front, a black slide post 19 x 16 rising 23.5 above it, and a rounded ankle tongue 14 wide below it; the block's faces are split into blocks by seams."},
    {"id": "R20", "scope": "geometry:boot", "text": "A black boot 29 wide and 41.5 long pointing forward, 20 tall, its heel top rounded about the ankle, a slot for the shin's tongue open at the top and the heel, and two hinge lugs at the toe; its sides are split into blocks by seams."},
    {"id": "R21", "scope": "geometry:wing", "text": "A black plate 23 wide and 3 thick on a 7 mm hinge knuckle, carrying at its far end a red blade 30.75 wide, 10 tall and 3 thick standing square to the plate."},
    {"id": "R22", "scope": "geometry:front-wheel", "text": "A black tyre 38 across and 16 wide with a plain tread and a five-spoke rim face on its outer side."},
    {"id": "R23", "scope": "geometry:rear-wheel", "text": "A black tyre 34 across and 12 wide with a plain tread and a five-spoke rim face on its outer side."}
  ],
  "interfaces": [
    {"id": "nose-fold", "kind": "coupled", "components": ["nose", "head", "torso"],
     "text": "A 3 x 26 dowel pressed 3.5 into each of the torso's two Ø7 back cheeks (X 10.5 to 14.5 each side, axis Y 14, Z 182) turns the nose's 20 wide knuckle (X -10 to 10; round R3.5) on a 3.1 bore; the torso's seat round the knuckle is a cylinder R4 over X -10.5 to 10.5. Robot pose: the nose lies down the back, its inner face 0.5 behind the torso's back (Y 13) and its front wing behind the hips. Car pose: flipped 180 degrees up over the top, the nose stands above the torso over the head pocket; the head is lowered first and the nose clears it by 5.",
     "yielding": "nose",
     "poses": {"steps": 10, "movers": [
       {"component": "nose", "rotation": {"axis_point": [0, 14, 182], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 180}},
       {"component": "head", "translation": {"vector": [0, 0, -22]}}]}},
    {"id": "head-slide", "kind": "coupled", "components": ["head", "torso"],
     "text": "The head's 8 x 8 neck post (Y -0.5 to 7.5) slides in the torso's 9 x 9 neck bore below the head pocket (X -4.5 to 4.5, Y -1 to 8, floor Z 119). A 3 x 20 dowel pressed through the cockpit's back wall (Y -7 to -1) and the pocket's back wall (Y 8 to 13) along Y at X 0, Z 149.5 runs through the post's 3.4 wide front-to-back slot and stops it at both ends: raised, the helmet's underside is at Z 178 and the neck shows through the pocket's 13 wide front notch (down to Z 170); lowered by 22, the helmet rests on the pocket floor at Z 156.",
     "yielding": "head",
     "poses": {"steps": 10, "movers": [
       {"component": "head", "translation": {"vector": [0, 0, -22]}}]}},
    {"id": "shoulder-1", "kind": "coupled", "components": ["arm-shell#1", "forearm#1", "torso", "front-wheel#1", "nose"],
     "text": "A 3 x 20 dowel pressed along X into arm shell 1's top block at Y -2, Z 157 turns in a 3.1 bore in the torso's +X side wall (X 23 to 29). The shell's inboard face is 1.5 from the torso side (X 29); its chamfered top stays at least 0.5 below front wheel 1 at every angle from 90 degrees forward to 5 back, and its fist stays 0.5 clear of the nose's front wing behind it.",
     "yielding": "arm-shell#1",
     "poses": {"steps": 10, "movers": [
       {"component": "arm-shell#1", "rotation": {"axis_point": [0, -2, 157], "axis_direction": [1, 0, 0], "start_deg": 5, "end_deg": -90}},
       {"component": "forearm#1", "rotation": {"axis_point": [0, -2, 157], "axis_direction": [1, 0, 0], "start_deg": 5, "end_deg": -90}}]}},
    {"id": "shoulder-2", "kind": "coupled", "components": ["arm-shell#2", "forearm#2", "torso", "front-wheel#2", "nose"],
     "text": "Mirror of shoulder-1 on the -X side: a 3 x 20 dowel pressed into arm shell 2's top block at Y -2, Z 157 turns in a 3.1 bore in the torso's -X side wall; the shell stays 1.5 from the torso side, 0.5 below front wheel 2 and 0.5 clear of the front wing from 90 degrees forward to 5 back.",
     "yielding": "arm-shell#2",
     "poses": {"steps": 10, "movers": [
       {"component": "arm-shell#2", "rotation": {"axis_point": [0, -2, 157], "axis_direction": [1, 0, 0], "start_deg": 5, "end_deg": -90}},
       {"component": "forearm#2", "rotation": {"axis_point": [0, -2, 157], "axis_direction": [1, 0, 0], "start_deg": 5, "end_deg": -90}}]}},
    {"id": "elbow-1", "kind": "coupled", "components": ["forearm#1", "arm-shell#1"],
     "text": "A 3 x 20 dowel pressed into arm shell 1's two elbow cheeks (X 30.5 to 33 and 48 to 50.5) along X at Y -2, Z 124 turns forearm 1's R7.5 knuckle on a 3.1 bore. The forearm folds 180 degrees up and back into the shell's cavity (X 33 to 48, Y -10 to 9, Z 118 to 152.6), entering through its open back. 0.5 clearance throughout.",
     "yielding": "forearm#1",
     "poses": {"steps": 10, "movers": [
       {"component": "forearm#1", "rotation": {"axis_point": [40.5, -2, 124], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 180}}]}},
    {"id": "elbow-2", "kind": "coupled", "components": ["forearm#2", "arm-shell#2"],
     "text": "Mirror of elbow-1: a 3 x 20 dowel pressed into arm shell 2's elbow cheeks along X at Y -2, Z 124 turns forearm 2's knuckle on a 3.1 bore; the forearm folds 180 degrees up and back into the cavity through the open back.",
     "yielding": "forearm#2",
     "poses": {"steps": 10, "movers": [
       {"component": "forearm#2", "rotation": {"axis_point": [-40.5, -2, 124], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 180}}]}},
    {"id": "hip-1", "kind": "coupled", "components": ["thigh#1", "shin#1", "boot#1", "wing#1", "rear-wheel#1", "torso", "nose"],
     "text": "Thigh 1's tongue (X 4 to 14, Y -5.7 to 1.7, rounded R3.7 about the hip axis so it stays 0.5 under the slot's pointed-arch roof) sits in the torso's hip slot (X 3.5 to 14.5, Y -9 to 5, up to Z 108); a 3 x 20 dowel pressed along X through the slot walls at Y -2, Z 102 turns it on a 3.1 bore. The thigh's stepped top stays 0.8 below the torso and the leg stays 0.5 clear of the nose's front wing from 20 degrees forward to 20 back.",
     "yielding": "thigh#1",
     "poses": {"steps": 10, "movers": [
       {"component": "thigh#1", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "shin#1", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "boot#1", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "wing#1", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "rear-wheel#1", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}}]}},
    {"id": "hip-2", "kind": "coupled", "components": ["thigh#2", "shin#2", "boot#2", "wing#2", "rear-wheel#2", "torso", "nose"],
     "text": "Mirror of hip-1: thigh 2's tongue sits in the torso's -X hip slot on a 3 x 20 dowel along X at Y -2, Z 102, turning on a 3.1 bore, 0.8 clear of the torso and 0.5 clear of the front wing from 20 degrees forward to 20 back.",
     "yielding": "thigh#2",
     "poses": {"steps": 10, "movers": [
       {"component": "thigh#2", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "shin#2", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "boot#2", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "wing#2", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "rear-wheel#2", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}}]}},
    {"id": "knee-slide-1", "kind": "coupled", "components": ["shin#1", "boot#1", "wing#1", "rear-wheel#1", "thigh#1", "torso"],
     "text": "Shin 1's slide post (X 3.5 to 22.5, Y -10 to 6) runs in thigh 1's sleeve (cavity X 3 to 23, Y -10.5 to 6.5, roof Z 93.5), 0.5 clear all round. A 3 x 24 dowel pressed along X through the post at Y -2 runs in the 3.2 wide slots of the thigh's two side walls from Z 73 (robot, full length) to Z 89 (car, 16 up), each slot narrowed to 2.8 for 1 inside each end so the dowel clicks into the end. At 16 up the post's top is 0.5 under the roof and the shin block's top 0.5 under the thigh's bottom.",
     "yielding": "shin#1",
     "poses": {"steps": 10, "movers": [
       {"component": "shin#1", "translation": {"vector": [0, 0, 16]}},
       {"component": "boot#1", "translation": {"vector": [0, 0, 16]}},
       {"component": "wing#1", "translation": {"vector": [0, 0, 16]}},
       {"component": "rear-wheel#1", "translation": {"vector": [0, 0, 16]}}]}},
    {"id": "knee-slide-2", "kind": "coupled", "components": ["shin#2", "boot#2", "wing#2", "rear-wheel#2", "thigh#2", "torso"],
     "text": "Mirror of knee-slide-1: shin 2's post slides 16 up into thigh 2's sleeve, 0.5 clear all round, on a 3 x 24 dowel along X at Y -2 running in the side-wall slots from Z 73 to Z 89, clicking into each end.",
     "yielding": "shin#2",
     "poses": {"steps": 10, "movers": [
       {"component": "shin#2", "translation": {"vector": [0, 0, 16]}},
       {"component": "boot#2", "translation": {"vector": [0, 0, 16]}},
       {"component": "wing#2", "translation": {"vector": [0, 0, 16]}},
       {"component": "rear-wheel#2", "translation": {"vector": [0, 0, 16]}}]}},
    {"id": "ankle-1", "kind": "coupled", "components": ["boot#1", "wing#1", "shin#1"],
     "text": "Shin 1's ankle tongue (X 8 to 22, Y -0.25 to 7.75, round R4 about the axis) sits in boot 1's slot (X 7.5 to 22.5, Y -0.75 to the heel, down to Z 7.75); a 3 x 28 dowel pressed along X through the slot's side walls at Y 3.75, Z 12.25 turns it on a 3.1 bore. The boot folds 90 degrees, toe down: its heel top, rounded R7.75 about the axis, and its heel face at Y 11.5 pass and end 0.5 under the shin's bottom face (Z 20.5), and its sole ends 3 above the car's ground.",
     "yielding": "boot#1",
     "poses": {"steps": 10, "movers": [
       {"component": "boot#1", "rotation": {"axis_point": [0, 3.75, 12.25], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}},
       {"component": "wing#1", "rotation": {"axis_point": [0, 3.75, 12.25], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "ankle-2", "kind": "coupled", "components": ["boot#2", "wing#2", "shin#2"],
     "text": "Mirror of ankle-1: shin 2's R4 tongue in boot 2's slot on a 3 x 28 dowel along X at Y 3.75, Z 12.25, turning on a 3.1 bore; the boot folds 90 degrees toe down with 0.5 clearance under the shin.",
     "yielding": "boot#2",
     "poses": {"steps": 10, "movers": [
       {"component": "boot#2", "rotation": {"axis_point": [0, 3.75, 12.25], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}},
       {"component": "wing#2", "rotation": {"axis_point": [0, 3.75, 12.25], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "wing-hinge-1", "kind": "coupled", "components": ["wing#1", "boot#1", "shin#1"],
     "text": "Wing 1's Ø7 knuckle (X 5.5 to 28.5) sits between boot 1's two toe lugs (X 2.5 to 5 and 29 to 31.5), 0.5 clear; a 3 x 28 dowel pressed along X into the lugs at Y -26.5, Z 23.5 turns it on a 3.1 bore. Folded, the plate lies 0.5 above the instep (Z 19.5) and the blade stands 1 in front of the shin. Standing (+90), the plate rises from the toe and the blade points away from the shin; in the car the blades of the two halves meet 1.5 apart at the centre line.",
     "yielding": "wing#1",
     "poses": {"steps": 10, "movers": [
       {"component": "wing#1", "rotation": {"axis_point": [0, -26.5, 23.5], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "wing-hinge-2", "kind": "coupled", "components": ["wing#2", "boot#2", "shin#2"],
     "text": "Mirror of wing-hinge-1: wing 2's knuckle between boot 2's toe lugs on a 3 x 28 dowel along X at Y -26.5, Z 23.5, turning on a 3.1 bore; it stands up 90 degrees from lying on the instep.",
     "yielding": "wing#2",
     "poses": {"steps": 10, "movers": [
       {"component": "wing#2", "rotation": {"axis_point": [0, -26.5, 23.5], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "front-wheels", "kind": "static", "components": ["front-wheel#1", "front-wheel#2", "torso"],
     "text": "Each front wheel turns on a 3 x 30 dowel pressed 12 deep into the torso tower and its Ø8 stub boss on the axis Y 0, Z 188, the wheel's inner face 0.5 outside the boss (X 31 to 47 and -31 to -47), held by a push-on cap."},
    {"id": "rear-wheels", "kind": "static", "components": ["rear-wheel#1", "rear-wheel#2", "shin#1", "shin#2"],
     "text": "Each rear wheel turns on a 3 x 26 dowel pressed 12 deep into its shin block's outer face on the axis Y 2, Z 50, the wheel's inner face 0.5 outside the shin (X 30.5 to 42.5 and -30.5 to -42.5), held by a push-on cap."}
  ]
}
```
