# Racer Mecha

A chunky heroic robot, 207 mm to the top of its helmet, that transforms by
hand into an open-wheel Formula racing car 286.5 mm long that rolls on four
wheels. Every part stays attached through the transformation: nothing is
removed, nothing is left over. The robot is the car stood up on its tail and
opened out: the car's cockpit with its halo is the robot's chest, its front
wheels sit on the shoulders, its front sidepods are the arms, its rear body
is the legs, its rear wheels are on the calves, its tail is the boots, and
the two halves of its rear wing fold onto the toes. The nose lies down the
robot's back with the front wing behind the thighs. In the car the robot lies
on its back: its back is the floor, its chest is the top.

Inventor: `rowan-vale`.

## Unique geometries

| Geometry | Count | Robot | Car |
|---|---|---|---|
| `torso` | 1 | Chest with the cockpit and halo, shoulder towers, hips | Monocoque, cockpit and halo, inner sidepods |
| `nose` | 1 | Lies down the back, front wing behind the thighs | Nose cone and front wing |
| `head` | 1 | Helmeted head with a visor | Pushed down into its pocket under the nose root |
| `arm-shell` | 2 | The whole white arm, shoulder to wrist | Front sidepod, outer half |
| `forearm` | 2 | Fist | Folded inside the sidepod |
| `thigh` | 2 | Thigh, a sleeve | Rear body, front half |
| `shin` | 2 | Shin, with the slide post above it | Rear body, rear half |
| `boot` | 2 | Boot, a long foot | Tail: gearbox and diffuser |
| `wing` | 2 | Toe cap with a raised blade | One half of the rear wing |
| `front-wheel` | 2 | Beside the shoulder towers | Front wheels |
| `rear-wheel` | 2 | On the outer sides of the calves | Rear wheels |

`arm-shell#2`, `forearm#2`, `thigh#2`, `shin#2`, `boot#2` and `wing#2` are
the mirror images of `#1`. Every `#1`, including `front-wheel#1` and
`rear-wheel#1`, is on the +X side.

**Focal Component: the torso.** In the Display Pose the cockpit opening ringed
by its red halo, in the middle of the broad black chest, is the form the eye
goes to first. It costs the nose its show: the nose lies down the back and
reads only from behind and in the car.

## Frame, poses and composition

Assembly coordinates in millimetres, in the Display Pose: X toward the
figure's left, front is -Y, Z up from the desk; the figure is centred on X 0.

**Display Pose: robot.** Standing upright on both boots, arms hanging
straight at the sides, legs straight and drawn out to full length, head
raised, nose lying down the back, wing halves folded on the toes. Envelope
124 (X) x 57 (Y, -30 to 27) x 207 (Z). Landmarks: boots 0 to 26, ankle pins
12.25, shin cuff 26.5 to 45, shin block 45 to 73.5, rear wheel axles 63, knee
guard over the slide post 73.5 to 89.5, thigh 90 to 115, hip pins 120, torso
117 to 190, halo 132 to 179 round the cockpit 138 to 173, shoulder pins 160,
arms 85 to 171 with the fists 85 to 109, shoulder towers to 195, front wheel
axles 189 and tops 205, helmet 188 to 207; behind: the nose hinge at Z 192,
the front wing 106 to 119. Widths: arms across 124, front wheels across 119,
torso 57, towers across 86, the nose's front wing 84, thighs 11 apart, shins
6 apart, boots 32 wide and 22 apart, rear wheels across 94.

**Car pose.** Reached by the moves under Transformation. In assembly
coordinates the car stands on its tail: its length runs along Z (-8.5 to
278), its floor faces +Y and its top -Y. Laid down on its floor it is 286.5
long, 124 wide across the front sidepods and 45 tall to the rear wing,
resting on all four wheels with the nose knuckle and the torso's hinge
cheeks 1.5 above the ground and every other part at least 3.

Release frames the robot in the Display Pose against `#f5f0e6`, the cockpit
and halo on the frame's vertical centre line and facing the hero camera
(`render_review` [-55, 26]) unobstructed.

## Palette

Multi-colour prints; colours change only at the boundaries named here.

| Geometry | Colour |
|---|---|
| `torso` | black, with a red halo |
| `nose` | racing red cone with a white stripe down each side; black front wing with red endplates |
| `head` | white and red helmet, blue visor band |
| `arm-shell` | white with a red band round the upper arm |
| `forearm` | black |
| `thigh` | racing red |
| `shin` | racing red with a white stripe panel down the front; red knee guard; black slide post |
| `boot` | black |
| `wing` | black plate, red blade |
| `front-wheel`, `rear-wheel` | black |

## Per-geometry spec

All positions are in the Display Pose; the `#1` part is given and `#2`
mirrors X.

**Torso.** A core block 57 wide (X -28.5 to 28.5) x 26 deep (Y -13 to 13),
Z 117 to 190. A head pocket 21 x 17 (X -10.5 to 10.5, Y -8 to 9), open at the
top, floor at Z 166; a notch 13 wide (X -6.5 to 6.5) cuts its front wall down
to Z 180, so the neck shows. A 9 x 9 neck bore (X -4.5 to 4.5, Y -1 to 8) runs
from the pocket floor down to Z 135.5. Two shoulder towers jut out over the
arms, X 28.5 to 43 each side, Y -13 to 13, up to Z 195; each tower's underside
is a 52 degree wedge rising from the side wall at Z 164.5 to Z 183 at its
outer face, passing 0.5 over the arm's top at X 34 (Z 171.5). Each side wall
carries a shoulder boss, Ø10, X 28.5 to 33.5, on the axis Y -2, Z 160, merging
into the wedge. On the front: the cockpit, an opening 20 wide (X -10 to 10)
and 3.5 deep (to Y -9.5) over Z 138 to 173, 1.5 clear of the head pocket
behind it, its top edge rising at 52 degrees, and round it a raised red halo
7 proud (Y -20 to -13), a closed loop X -15 to 15, Z 132 to 179, of two 4 wide
legs (X 11 to 15 each side) joined by a 5 thick bottom bar (Z 132 to 137) and
a 5 thick top bar (Z 174 to 179), its corners rounded, each bar's underside
growing out of the chest at a 52 degree rise. At the top of the back, two Ø7
nose hinge cheeks (X 10.5 to 14.5 each side) on the axis Y 14, Z 192, each with
a 52 degree gusset under it, flanking the nose knuckle's seat, a cylinder of
radius 4 about the axis over X -10.5 to 10.5. The back is otherwise plain
blocks. The bottom carries two hip slots (X 8.5 to 19.5 each side, Y -9 to 5,
Z 117 to 126, pointed-arch tops). The head retainer's bore runs along Y at
X 0, Z 162 from the back face (Y 13) to the cockpit's back wall. Walls 3.0.
Prints standing on its bottom face (Z 117).

**Nose.** One part, lying down the back. A knuckle 20 wide (X -10 to 10) on
the hinge axis Y 14, Z 192: round, radius 3.5, toward the top and a teardrop
toward the root, its point 5.7 from the axis and its faces 38 degrees from
the cone's axis. A root block 20 wide (Y 13.5 to 21, Z 182 to 189) joins it to
the cone. The cone runs down the back, its outer face sculpted as a nose cone:
18 wide and 13.5 deep (Y 13.5 to 27) from Z 182 to 141, then 12 wide and 10.5
deep (Y 13.5 to 24) down to Z 119, then a 4 deep tip (Y 17 to 21) on to Z
112, blunt and 4 wide; the step at Z 141 rises at 52 degrees. The front wing
at the tip: a plate 84 wide (X -42 to 42) x 13 tall (Z 106 to 119) x 6 thick
(Y 21 to 27, flush with the cone's back), with an endplate 3 wide x 9 deep
(Y 18 to 27) at each end (X 39 to 42); the cone's tip overlaps the wing's
upper half (Z 112 to 119). Prints standing on the wing's lower face (Z 106).

**Head.** A helmet 19 wide x 16 deep (Y -7.5 to 8.5) x 19 tall (Z 188 to 207)
with a blue visor band across its front face and a raised crest, 2 wide and
1.5 high, along its top centre line. Under it a square neck post 8 x 8
(X -4 to 4, Y -0.5 to 7.5), Z 158 to 188, its back face flush with the
helmet's, with a slot 3.4 wide (X -1.7 to 1.7) through it from front to back
from Z 160.4 to 185.6. Prints on its back face.

**Arm shell.** The whole white arm from shoulder to wrist: a C-channel 28 wide
(X 34 to 62) x 22 deep (Y -13 to 9), Z 109 to 160, topped by a solid top block
rounded R11 about the shoulder axis (Y -2, Z 160), so its top is at Z 171 and
it keeps that outline at every shoulder angle. Front wall 2.5, inboard and
outboard walls 2.5, open at the back and the bottom; a fist cavity X 36.5 to
59.5, Y -10.5 to 9, Z 109 to 152. A red band 11 tall wraps its front and outer
faces from Z 142 to 153, and a seam at Z 141 splits the upper arm from the
lower. The side walls' bottoms are the elbow cheeks, with the elbow bore along
X at Y -2, Z 116. The shoulder bore runs along X into the top block from its
inboard face at Y -2, Z 160. Prints on its front face.

**Forearm.** A black closed fist 22 wide (X 37 to 59) x 15 deep (Y -9.5 to
5.5), Z 85 to 116, ending at the top in a wrist knuckle rounded R7.5 about the
elbow axis Y -2, Z 116; below the shell (Z 85 to 109) three fingers split by
two vertical grooves, crossed by one knuckle groove. Prints on its
outboard face.

**Thigh.** A sleeve 22.5 wide (X 5.5 to 28) x 22 deep (Y -13 to 9), Z 90 to
112.5, open at the bottom: its cavity X 8 to 25.5, Y -10.5 to 6.5, up to a 2.5
thick roof at Z 112.5, walls 2.5. Above the roof it steps in to Y -10 to 6 up
to Z 115 and is topped by a hip tongue 10 wide (X 9 to 19) x 7.4 deep (Y -5.7
to 1.7) to Z 120, rounded R3.7 about the hip axis Y -2, Z 120. Each side wall
(X 5.5 to 8 and 25.5 to 28) carries a slide slot along Z at Y -2, 3.2 wide,
its ends rounded about Z 93 and Z 109, narrowed to 2.8 for 1 just inside each
end so the dowel clicks into the end. Prints standing on its bottom face
(Z 90).

**Shin.** A cuff 31.5 wide (X 3 to 34.5) x 22 deep (Y -13 to 9), Z 26.5 to 45,
and above it a block 28 wide (X 3.5 to 31.5), Z 45 to 73.5, the cuff's step
rising at 52 degrees, with a white stripe panel 8 wide down the front of both,
centred on X 18. On top the slide post, 16.5 wide (X 8.5 to 25) x 16 deep
(Y -10 to 6), Z 73.5 to 96. In front of the post a knee guard 22.5 wide (X 5.5
to 28) x 1.5 thick (Y -15 to -13.5) rises from the block's front face to Z
89.5, so from the front the leg reads as one column; in the car it slides up
0.5 in front of the thigh. The post carries the slide dowel's bore along X at
Y -2, Z 93. On the block's outer face an Ø8 boss (X 31.5 to 34.5) on the rear
wheel axis Y 2, Z 63. Below the cuff the ankle tongue, 14 wide (X 14 to 28) x
8 deep (Y -0.25 to 7.75), down to a round end R4 about the ankle axis Y 3.75,
Z 12.25. Prints upside down on the post's top face (Z 96).

**Boot.** A long foot 32 wide (X 11 to 43), set outboard of the shin, Y -30 to
11.5, Z 0 to 26, pointing forward, the way the robot faces: the toe is 17
ahead of the shin's front. Behind the ankle axis its top is rounded R7.75 about
the axis (Y 3.75, Z 12.25) down to the heel face at Y 11.5. A slot for the
shin's tongue, X 13.5 to 28.5, Y -0.75 to the heel, down to Z 7.75, open at the
top and the heel. The ankle bores run along X through the slot's side walls on
the axis. The instep in front of the shin is a flat at Z 25.5 from the toe to
Y -13.5, where the wing lies; at the toe two lugs 3.5 thick (X 11 to 14.5 and
39.5 to 43), Y -30 to -26.5, rise to Z 33, rounded R3.5 about the wing hinge
axis Y -26.5, Z 29.5. Prints on its sole.

**Wing.** One half of the rear wing, a single part. A knuckle Ø7 x 24 (X 15 to
39) on the wing hinge axis (Y -26.5, Z 29.5); a plate 24 wide (X 15 to 39) x 3
thick (Z 26 to 29) running from the knuckle to Y -14; and at the plate's far
end the blade, 42.25 wide (X 0.75 to 43) x 3 (Y -17 to -14) x 10 tall (Z 26 to
36), standing up 1 in front of the shin and reaching inboard past the boot to
1.5 from the other blade. In the car the plate stands up as the wing's
endplate and pylon and the blade points rearward as the wing. Prints on its
flat underside (Z 26).

**Front wheel.** Ø32 x 16, a tyre with a plain tread and a five-spoke rim
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
| Nose hinge | 3 x 26 | torso back cheeks, 3.5 each | nose knuckle | X, at Y 14, Z 192 |
| Head retainer | 3 x 20 | torso back wall | neck post slot | Y, at X 0, Z 162 |
| Shoulder | 3 x 20, each | arm shell top block, 12 deep | torso boss and side wall | X, at Y -2, Z 160 |
| Elbow | 3 x 28, each | arm shell cheeks | forearm knuckle | X, at Y -2, Z 116 |
| Hip | 3 x 20, each | torso slot walls | thigh tongue | X, at Y -2, Z 120 |
| Knee slide | 3 x 22, each | shin post | thigh side-wall slots, Z 93 to 109 | X, at Y -2, Z 93 |
| Ankle | 3 x 30, each | boot slot walls | shin tongue | X, at Y 3.75, Z 12.25 |
| Wing hinge | 3 x 32, each | boot toe lugs | wing knuckle | X, at Y -26.5, Z 29.5 |
| Front wheels | 3 x 30, each | torso tower, 12 deep | wheel bore | X, at Y 3, Z 189 |
| Rear wheels | 3 x 26, each | shin boss and block, 12 deep | wheel bore | X, at Y 2, Z 63 |

## Transformation

From robot to car, in this order (reverse for car to robot):

1. Push the head down 22 into its pocket.
2. Flip the nose 180 degrees up over the top of the back (+180 about +X):
   it stands above the torso over the head pocket, its front wing at the top
   (Z 265 to 278).
3. Fold each fist up and back 180 degrees about its wrist (+180 about +X)
   into its arm shell's cavity.
4. Fold each boot 90 degrees at the ankle (+90 about +X): the toe points
   down, the sole faces the back.
5. Push each shin 16 up into its thigh: the slide post fills the sleeve.
6. Stand each wing half up 90 degrees on its hinge (+90 about +X): its
   plate rises from the boot and its blade points rearward; the two blades
   meet at the centre line, 1.5 apart.
7. Lay the car down on its back, on its wheels.

`guide-01-transformation.png` draws these moves from car to robot (7 to 1),
one colour per part. Where it differs, this contract wins.

Posing in the robot: shoulders 90 forward and 5 back; hips 20 forward and 20
back. The knees do not bend: the legs slide. The fists do not bend forward:
the arm shell's front wall reaches its bottom.

## Motion and fit

- Clearances and the motion check plan are R07's: 0.5 mm except at the
  contacts the Interfaces declare, one sweep per move.
- In the car pose the wheels are the lowest parts (R05).
- The knee-slide dowel's clicks hold the robot standing at full length and
  the car at its short length; the ankle and wing hinges hold by friction.
- Assembled, not printed in place: each dowel is pressed in after its part
  is seated, the head's retainer last, through the torso's back.

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

The toy reads as built from chunky blocks, as ref-01 draws it, not as plain
slabs. Every large face (over 15 across) of the torso, thigh, shin, boot,
arm shell and nose cone is split by seams 0.6 wide and 0.5 deep into blocks
6 to 15 across, offset between rows like brickwork, and on each front face
at least two blocks stand 0.6 proud of their neighbours. Every exposed
outside edge carries a chamfer 0.8 across, rising at 52 degrees on an edge
that faces down in the print stance; edges on the print-bed face, at a bore,
a slot, a joint face, or on any face another part comes within 2 mm of in a
pose or move stay square, and no proud block stands there. A seam is the one
cut allowed into a load-bearing wall: the arm shell's and the thigh's 2.5
walls keep 2.0 under a seam, and no seam runs where it would leave less than
a part's floor below.

Load-bearing sections are at least 3 mm: torso walls 3.0, arm shell walls
2.5, thigh walls 2.5, every tongue at least 7.4 deep, the slide post 16, the
neck post 8, the wing plate and blade 3, the toe lugs 3.5. The exceptions are
the material around a dowel bore, which the joints above size, and the 1.5
wall between the cockpit and the head pocket: above a teardrop bore (its
faces 38 degrees from vertical) inside a Ø7 cheek, lug or knuckle 1.1 is left
on the torso and the boot, 0.95 on the nose and the wing; between the slide
slot's end at Z 93 and the thigh's bottom face 1.4; above the slide dowel's
bore in the post 1.4; between a bore at Z 120 and the hip slot's bottom 3
below it 1.55 on the torso; beside the neck post's 3.4 slot 2.3; around an
R3.7 or R4 tongue's Ø3.1 bore 2.15 or 2.45. So the torso and the boot hold a
1.1 floor, the nose and the wing 0.95, the thigh and the shin 1.4 and the
head 1.9, and nothing on them is thinner than these joints force. A drop
lands on a shoulder wheel or a boot; the wheels, the wing halves and the head
are the first to come loose, and each presses back on its dowel. The robot
stands unsupported: its centre of mass lies at Y -1.5, 28.5 behind the toes
and 13 ahead of the heels.

```design-contract
{
  "schema_version": 5,
  "title": "Racer Mecha",
  "inventor": "rowan-vale",
  "envelope_mm": [124, 57, 207],
  "guides": [
    {"file": "guide-01-transformation.png", "shows": "The moves from car to robot, one colour per part; a back view, the car's tail, the leg fold from the side.", "steps": ["Stand the car up on its tail.", "Fold the wing halves down onto the toes.", "Pull the shins out of the thighs.", "Fold the boots forward.", "Fold the fists out of the arm shells.", "Flip the nose down the back.", "Raise the head."]}
  ],
  "references": [
    {"file": "ref-01-racer-mecha.png", "shows": "assembly", "camera": [-90, 15]},
    {"file": "ref-02-torso.png", "shows": "geometry:torso", "camera": [-90, 15]},
    {"file": "ref-03-nose.png", "shows": "geometry:nose", "camera": [90, 0]},
    {"file": "ref-04-head.png", "shows": "geometry:head", "camera": [-90, 0]},
    {"file": "ref-05-arm-shell.png", "shows": "geometry:arm-shell", "camera": [-75, 15]},
    {"file": "ref-06-forearm.png", "shows": "geometry:forearm", "camera": [-90, 0]},
    {"file": "ref-07-thigh.png", "shows": "geometry:thigh", "camera": [-75, 15]},
    {"file": "ref-08-shin.png", "shows": "geometry:shin", "camera": [-90, 0]},
    {"file": "ref-09-boot.png", "shows": "geometry:boot", "camera": [0, 0]},
    {"file": "ref-10-wing.png", "shows": "geometry:wing", "camera": [-105, 30]},
    {"file": "ref-11-front-wheel.png", "shows": "geometry:front-wheel", "camera": [-15, 15]},
    {"file": "ref-12-rear-wheel.png", "shows": "geometry:rear-wheel", "camera": [-30, 15]}
  ],
  "geometries": [
    {"id": "torso", "name": "Torso", "count": 1, "extents_mm": [86, 37.5, 78.5], "wall_min_mm": 1.1},
    {"id": "nose", "name": "Nose and front wing", "count": 1, "extents_mm": [84, 16.5, 89.5], "wall_min_mm": 0.95},
    {"id": "head", "name": "Head", "count": 1, "extents_mm": [19, 16, 49], "wall_min_mm": 1.9},
    {"id": "arm-shell", "name": "Arm shell", "count": 2, "extents_mm": [28, 22, 62], "wall_min_mm": 2.0},
    {"id": "forearm", "name": "Fist", "count": 2, "extents_mm": [22, 15, 38.5], "wall_min_mm": 3.0},
    {"id": "thigh", "name": "Thigh sleeve", "count": 2, "extents_mm": [22.5, 22, 33.7], "wall_min_mm": 1.4},
    {"id": "shin", "name": "Shin and slide post", "count": 2, "extents_mm": [31.5, 24, 87.75], "wall_min_mm": 1.4},
    {"id": "boot", "name": "Boot", "count": 2, "extents_mm": [32, 41.5, 33], "wall_min_mm": 1.1},
    {"id": "wing", "name": "Rear-wing half", "count": 2, "extents_mm": [42.25, 16, 10], "wall_min_mm": 0.95},
    {"id": "front-wheel", "name": "Front wheel", "count": 2, "extents_mm": [32, 32, 16], "wall_min_mm": 2.0},
    {"id": "rear-wheel", "name": "Rear wheel", "count": 2, "extents_mm": [34, 34, 12], "wall_min_mm": 2.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly", "text": "In the Display Pose the robot stands upright on both boots, its helmet top at Z 207, arms hanging straight 5.5 out from the torso: the cockpit opening ringed by the closed red halo sits in the middle of the broad black chest from Z 132 to 179, a shoulder tower juts over each arm with a front wheel on its outer face at Z 189, a rear wheel on the outer side of each calf at Z 63, a red knee guard runs up from each shin to its thigh from Z 73.5 to 89.5, and each boot carries a folded wing half whose red blade stands in front of the shin."},
    {"id": "R02", "scope": "assembly", "text": "From behind, the nose lies down the middle of the robot's back from its hinge at Z 192, its front wing 84 wide across the back of the thighs from Z 106 to 119, and nothing else rises behind the head."},
    {"id": "R03", "scope": "assembly", "text": "In the car pose the toy is an open-wheel Formula car 286.5 mm long, 124 wide and 45 tall to the rear wing, lying on the robot's back: nose cone and front wing ahead of the front wheels, the cockpit and halo on top, the arm shells as front sidepods, the legs side by side as the rear body, the boots as the tail, and the two wing halves standing on the boots as the rear wing, their blades meeting at the centre line."},
    {"id": "R04", "scope": "assembly", "text": "The robot becomes the car by seven moves and no part comes off: the head slides 22 down into its pocket, the nose flips 180 degrees up over the top of the back, each fist folds 180 degrees into its arm shell, each boot folds 90 degrees at the ankle, each shin slides 16 up into its thigh, each wing half stands up 90 degrees on its hinge, and the car is laid on its back."},
    {"id": "R05", "scope": "assembly", "text": "In the car pose the car rests on all four wheels, the nose knuckle and the torso's hinge cheeks 1.5 mm and every other part at least 3 mm above the ground, and each wheel turns freely on its dowel."},
    {"id": "R06", "scope": "assembly", "text": "Posing ranges in the robot: shoulders 90 degrees forward and 5 back, hips 20 forward and 20 back, each holding its pose by friction; the knees do not bend, the legs slide."},
    {"id": "R07", "scope": "assembly", "text": "Every moving part keeps at least 0.5 mm from every other part through each transformation move and posing range and in both poses, except at the contacts the Interfaces declare: the head-slide dowel stopping in the neck post's slot, the lowered helmet on the pocket floor, and the knee-slide dowel stopping at its slot ends. Checked with --check-motion true: one sweep per transformation move in at most 10 steps against only the parts it can reach; a skipped, killed or timed-out sweep fails this requirement."},
    {"id": "R08", "scope": "assembly", "text": "Every purchased-part seat is derived from a catalog STEP file, or from the documented envelope when the catalog search is a recorded miss, and the bill of materials lists exactly 5 dowels 3 x 20, 2 dowels 3 x 22, 3 dowels 3 x 26, 2 dowels 3 x 28, 4 dowels 3 x 30, 2 dowels 3 x 32 and 4 push-on caps for 3 mm shafts."},
    {"id": "R09", "scope": "assembly", "text": "Every joint is built as its Interface text states, each hinge or slide a purchased dowel pressed into a 2.9 mm bore on one side and turning or sliding in a 3.1 mm bore or slot (3.2 for the wheels) on the other, with no glue; each knee-slide slot narrows to 2.8 for 1 mm inside each end so the dowel clicks into the end and holds."},
    {"id": "R10", "scope": "assembly", "text": "The robot stands unsupported in the Display Pose: its centre of mass lies over the boots, which span Y -30 at the toes to 11.5 at the heels; each foot points forward, its toe 17 ahead of the shin's front, and sits outboard of its shin, the boots 22 apart."},
    {"id": "R11", "scope": "geometry:torso", "text": "A 57 x 26 black core built from chunky blocks, its front, sides and back split by seams with proud blocks on the front; two shoulder towers jutting 14.5 out from its top corners on 52 degree wedge undersides, and between them an open head pocket whose front wall has a 13 wide notch so the neck shows."},
    {"id": "R12", "scope": "geometry:torso", "text": "On the front a cockpit opening 20 wide, 35 tall and 3.5 deep ringed by a closed red halo 30 wide and 47 tall standing 7 proud, of two 4 wide legs and two 5 thick bars with rounded corners; a 10 mm shoulder boss on each side wall; two 7 mm nose hinge cheeks at the top of the back."},
    {"id": "R13", "scope": "geometry:nose", "text": "A red nose cone with a white stripe down each side, 18 wide at its root stepping to 12, ending in a blunt 4 wide tip, its root on a hinge knuckle 20 wide; it lies down the robot's back."},
    {"id": "R14", "scope": "geometry:nose", "text": "At the tip a black front wing 84 wide and 13 tall on the cone's outer face, with a red endplate 3 wide at each end; the cone's tip overlaps the wing's upper half from in front."},
    {"id": "R15", "scope": "geometry:head", "text": "A white and red helmet 19 wide and 19 tall with a blue visor band across its front and a raised crest along its top centre line, on a square 8 mm neck post 30 long with a 3.4 wide slot through it from front to back."},
    {"id": "R16", "scope": "geometry:arm-shell", "text": "A 28 x 22 white arm 62 tall, a channel open at the back and the bottom, its top rounded about the shoulder axis, its faces split into chunky blocks by seams, a seam splitting upper from lower arm and a red band 11 tall round the upper arm."},
    {"id": "R17", "scope": "geometry:forearm", "text": "A black closed fist 22 wide and 15 deep, ending at the top in a rounded wrist knuckle, three fingers split by two vertical grooves and crossed by one knuckle groove."},
    {"id": "R18", "scope": "geometry:thigh", "text": "A 22.5 x 22 red sleeve 22.5 tall, open at the bottom, whose top steps in and rises into a rounded hip tongue 10 wide toward its inboard side, with a 3.2 wide slot along each side wall for 16 mm of slide; its front and outer side are split by seams into blocks, two of them standing proud on the front."},
    {"id": "R19", "scope": "geometry:shin", "text": "A red shin: a cuff 31.5 wide and 18.5 tall under a block 28 wide and 28.5 tall, a white stripe panel down the front of both, a black slide post 16.5 x 16 rising 22.5 above with a red knee guard 22.5 wide and 1.5 thick in front of it, a wheel boss on the outer face and a rounded ankle tongue 14 wide below; faces split into blocks by seams."},
    {"id": "R20", "scope": "geometry:boot", "text": "A black boot 32 wide and 41.5 long pointing forward, 26 tall, its heel top rounded about the ankle, a slot for the shin's tongue open at the top and the heel, and two hinge lugs at the toe; its sides are split into blocks by seams."},
    {"id": "R21", "scope": "geometry:wing", "text": "A black plate 24 wide and 3 thick on a 7 mm hinge knuckle, carrying at its far end a red blade 42.25 wide, 10 tall and 3 thick standing square to the plate and overhanging it by 14.25 on its inboard side and 4 on its outboard side."},
    {"id": "R22", "scope": "geometry:front-wheel", "text": "A black tyre 32 across and 16 wide with a plain tread and a five-spoke rim face on its outer side."},
    {"id": "R23", "scope": "geometry:rear-wheel", "text": "A black tyre 34 across and 12 wide with a plain tread and a five-spoke rim face on its outer side."}
  ],
  "interfaces": [
    {"id": "nose-fold", "kind": "coupled", "components": ["nose", "head", "torso"],
     "text": "A 3 x 26 dowel pressed 3.5 into each of the torso's two Ø7 back cheeks (X 10.5 to 14.5 each side, axis Y 14, Z 192) turns the nose's 20 wide knuckle (X -10 to 10; round R3.5) on a 3.1 bore; the torso's seat round the knuckle is a cylinder R4 over X -10.5 to 10.5. Robot pose: the nose lies down the back, its inner face 0.5 behind the torso's back (Y 13) and its front wing behind the thighs. Car pose: flipped 180 degrees up over the top, the nose stands above the torso over the head pocket; the head is lowered first and the nose clears it by 5.",
     "yielding": "nose",
     "poses": {"steps": 10, "movers": [
       {"component": "nose", "rotation": {"axis_point": [0, 14, 192], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 180}},
       {"component": "head", "translation": {"vector": [0, 0, -22]}}]}},
    {"id": "head-slide", "kind": "coupled", "components": ["head", "torso"],
     "text": "The head's 8 x 8 neck post (Y 0.5 to 8.5, its back face flush with the helmet's back at Y 8.5) slides in the torso's 9 x 9 neck bore below the head pocket (X -4.5 to 4.5, Y 0 to 9, floor Z 135.5). A 3 x 20 dowel pressed along Y at X 0, Z 162 from the torso's back face (Y 13) to Y -7 runs through the post's 3.4 wide front-to-back slot and stops it at both ends: raised, the helmet's underside is at Z 188 and the neck shows through the pocket's 13 wide front notch (down to Z 180); lowered by 22, the helmet rests on the pocket floor at Z 166, 5 below the torso's top.",
     "yielding": "head",
     "poses": {"steps": 10, "movers": [
       {"component": "head", "translation": {"vector": [0, 0, -22]}}]}},
    {"id": "shoulder-1", "kind": "coupled", "components": ["arm-shell#1", "forearm#1", "torso", "front-wheel#1"],
     "text": "A 3 x 20 dowel pressed 12 along X into arm shell 1's top block at Y -2, Z 160 turns in a 3.1 bore through the torso's Ø10 shoulder boss (X 28.5 to 33.5) and +X side wall. The shell's inboard face is 0.5 from the boss; its top, rounded R11 about the axis, stays 0.5 under the tower's wedge and 2 clear of front wheel 1 at every angle from 90 degrees forward to 5 back.",
     "yielding": "arm-shell#1",
     "poses": {"steps": 10, "movers": [
       {"component": "arm-shell#1", "rotation": {"axis_point": [0, -2, 160], "axis_direction": [1, 0, 0], "start_deg": 5, "end_deg": -90}},
       {"component": "forearm#1", "rotation": {"axis_point": [0, -2, 160], "axis_direction": [1, 0, 0], "start_deg": 5, "end_deg": -90}}]}},
    {"id": "shoulder-2", "kind": "coupled", "components": ["arm-shell#2", "forearm#2", "torso", "front-wheel#2"],
     "text": "Mirror of shoulder-1 on the -X side: a 3 x 20 dowel pressed into arm shell 2's top block at Y -2, Z 160 turns in the torso's -X boss and side wall; the shell stays 0.5 from the boss, 0.5 under the tower and 2 clear of front wheel 2 from 90 degrees forward to 5 back.",
     "yielding": "arm-shell#2",
     "poses": {"steps": 10, "movers": [
       {"component": "arm-shell#2", "rotation": {"axis_point": [0, -2, 160], "axis_direction": [1, 0, 0], "start_deg": 5, "end_deg": -90}},
       {"component": "forearm#2", "rotation": {"axis_point": [0, -2, 160], "axis_direction": [1, 0, 0], "start_deg": 5, "end_deg": -90}}]}},
    {"id": "elbow-1", "kind": "coupled", "components": ["forearm#1", "arm-shell#1"],
     "text": "A 3 x 28 dowel pressed into arm shell 1's two elbow cheeks (X 34 to 36.5 and 59.5 to 62) along X at Y -2, Z 116 turns fist 1's R7.5 wrist knuckle on a 3.1 bore. The fist folds 180 degrees up and back into the shell's cavity (X 36.5 to 59.5, Y -10.5 to 9, Z 109 to 152), entering through its open back. 0.5 clearance throughout.",
     "yielding": "forearm#1",
     "poses": {"steps": 10, "movers": [
       {"component": "forearm#1", "rotation": {"axis_point": [48, -2, 116], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 180}}]}},
    {"id": "elbow-2", "kind": "coupled", "components": ["forearm#2", "arm-shell#2"],
     "text": "Mirror of elbow-1: a 3 x 28 dowel pressed into arm shell 2's elbow cheeks along X at Y -2, Z 116 turns fist 2's knuckle on a 3.1 bore; the fist folds 180 degrees up and back into the cavity through the open back.",
     "yielding": "forearm#2",
     "poses": {"steps": 10, "movers": [
       {"component": "forearm#2", "rotation": {"axis_point": [-48, -2, 116], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 180}}]}},
    {"id": "hip-1", "kind": "coupled", "components": ["thigh#1", "shin#1", "boot#1", "wing#1", "rear-wheel#1", "torso", "nose"],
     "text": "Thigh 1's tongue (X 9 to 19, Y -5.7 to 1.7, rounded R3.7 about the hip axis so it stays 0.5 under the slot's pointed-arch roof) sits in the torso's hip slot (X 8.5 to 19.5, Y -9 to 5, up to Z 126); a 3 x 20 dowel pressed along X through the slot walls at Y -2, Z 120 turns it on a 3.1 bore. The thigh's stepped top stays 2 below the torso and the leg stays 0.5 clear of the nose's front wing from 20 degrees forward to 20 back.",
     "yielding": "thigh#1",
     "poses": {"steps": 10, "movers": [
       {"component": "thigh#1", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "shin#1", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "boot#1", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "wing#1", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "rear-wheel#1", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}}]}},
    {"id": "hip-2", "kind": "coupled", "components": ["thigh#2", "shin#2", "boot#2", "wing#2", "rear-wheel#2", "torso", "nose"],
     "text": "Mirror of hip-1: thigh 2's tongue sits in the torso's -X hip slot on a 3 x 20 dowel along X at Y -2, Z 120, turning on a 3.1 bore, 2 clear of the torso and 0.5 clear of the front wing from 20 degrees forward to 20 back.",
     "yielding": "thigh#2",
     "poses": {"steps": 10, "movers": [
       {"component": "thigh#2", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "shin#2", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "boot#2", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "wing#2", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "rear-wheel#2", "rotation": {"axis_point": [0, -2, 120], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}}]}},
    {"id": "knee-slide-1", "kind": "coupled", "components": ["shin#1", "boot#1", "wing#1", "rear-wheel#1", "thigh#1", "torso"],
     "text": "Shin 1's slide post (X 8.5 to 25, Y -10 to 6) runs in thigh 1's sleeve (cavity X 8 to 25.5, Y -10.5 to 6.5, roof Z 112.5), 0.5 clear all round, the knee guard sliding 0.5 in front of the thigh's front face. A 3 x 22 dowel pressed along X through the post at Y -2 runs in the 3.2 wide slots of the thigh's two side walls from Z 93 (robot, full length) to Z 109 (car, 16 up), each slot narrowed to 2.8 for 1 inside each end so the dowel clicks into the end. At 16 up the post's top is 0.5 under the roof and the shin block's top 0.5 under the thigh's bottom.",
     "yielding": "shin#1",
     "poses": {"steps": 10, "movers": [
       {"component": "shin#1", "translation": {"vector": [0, 0, 16]}},
       {"component": "boot#1", "translation": {"vector": [0, 0, 16]}},
       {"component": "wing#1", "translation": {"vector": [0, 0, 16]}},
       {"component": "rear-wheel#1", "translation": {"vector": [0, 0, 16]}}]}},
    {"id": "knee-slide-2", "kind": "coupled", "components": ["shin#2", "boot#2", "wing#2", "rear-wheel#2", "thigh#2", "torso"],
     "text": "Mirror of knee-slide-1: shin 2's post slides 16 up into thigh 2's sleeve, 0.5 clear all round, on a 3 x 22 dowel along X at Y -2 running in the side-wall slots from Z 93 to Z 109, clicking into each end.",
     "yielding": "shin#2",
     "poses": {"steps": 10, "movers": [
       {"component": "shin#2", "translation": {"vector": [0, 0, 16]}},
       {"component": "boot#2", "translation": {"vector": [0, 0, 16]}},
       {"component": "wing#2", "translation": {"vector": [0, 0, 16]}},
       {"component": "rear-wheel#2", "translation": {"vector": [0, 0, 16]}}]}},
    {"id": "ankle-1", "kind": "coupled", "components": ["boot#1", "wing#1", "shin#1"],
     "text": "Shin 1's ankle tongue (X 14 to 28, Y -0.25 to 7.75, round R4 about the axis) sits in boot 1's slot (X 13.5 to 28.5, Y -0.75 to the heel, down to Z 7.75); a 3 x 30 dowel pressed along X through the slot's side walls at Y 3.75, Z 12.25 turns it on a 3.1 bore. The boot folds 90 degrees, toe down: its heel top, rounded R7.75 about the axis, and its heel face at Y 11.5 pass and end 0.5 under the shin's bottom face (Z 26.5), and its sole ends 3 above the car's ground.",
     "yielding": "boot#1",
     "poses": {"steps": 10, "movers": [
       {"component": "boot#1", "rotation": {"axis_point": [0, 3.75, 12.25], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}},
       {"component": "wing#1", "rotation": {"axis_point": [0, 3.75, 12.25], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "ankle-2", "kind": "coupled", "components": ["boot#2", "wing#2", "shin#2"],
     "text": "Mirror of ankle-1: shin 2's R4 tongue in boot 2's slot on a 3 x 30 dowel along X at Y 3.75, Z 12.25, turning on a 3.1 bore; the boot folds 90 degrees toe down with 0.5 clearance under the shin.",
     "yielding": "boot#2",
     "poses": {"steps": 10, "movers": [
       {"component": "boot#2", "rotation": {"axis_point": [0, 3.75, 12.25], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}},
       {"component": "wing#2", "rotation": {"axis_point": [0, 3.75, 12.25], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "wing-hinge-1", "kind": "coupled", "components": ["wing#1", "boot#1", "shin#1"],
     "text": "Wing 1's Ø7 knuckle (X 15 to 39) sits between boot 1's two toe lugs (X 11 to 14.5 and 39.5 to 43), 0.5 clear; a 3 x 32 dowel pressed along X into the lugs at Y -26.5, Z 29.5 turns it on a 3.1 bore. Folded, the plate lies 0.5 above the instep (Z 25.5) and the blade stands 1 in front of the shin. Standing (+90), the plate rises from the toe and the blade points away from the shin; in the car the blades of the two halves meet 1.5 apart at the centre line.",
     "yielding": "wing#1",
     "poses": {"steps": 10, "movers": [
       {"component": "wing#1", "rotation": {"axis_point": [0, -26.5, 29.5], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "wing-hinge-2", "kind": "coupled", "components": ["wing#2", "boot#2", "shin#2"],
     "text": "Mirror of wing-hinge-1: wing 2's knuckle between boot 2's toe lugs on a 3 x 32 dowel along X at Y -26.5, Z 29.5, turning on a 3.1 bore; it stands up 90 degrees from lying on the instep.",
     "yielding": "wing#2",
     "poses": {"steps": 10, "movers": [
       {"component": "wing#2", "rotation": {"axis_point": [0, -26.5, 29.5], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 90}}]}},
    {"id": "front-wheels", "kind": "static", "components": ["front-wheel#1", "front-wheel#2", "torso"],
     "text": "Each front wheel turns on a 3 x 30 dowel pressed 12 deep into the outer face of a shoulder tower on the axis Y 3, Z 189, the wheel's inner face 0.5 outside the tower (X 43.5 to 59.5 and -43.5 to -59.5), held by a push-on cap."},
    {"id": "rear-wheels", "kind": "static", "components": ["rear-wheel#1", "rear-wheel#2", "shin#1", "shin#2"],
     "text": "Each rear wheel turns on a 3 x 26 dowel pressed 12 deep into its shin's Ø8 boss and block on the axis Y 2, Z 63, the wheel's inner face 0.5 outside the boss (X 35 to 47 and -35 to -47), held by a push-on cap."}
  ]
}
```
