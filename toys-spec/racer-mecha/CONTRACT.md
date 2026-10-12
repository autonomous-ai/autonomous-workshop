# Racer Mecha

A chunky heroic robot, 197 mm to the top of its helmet and 221 mm to the top
of the rear wing behind it, that transforms by hand into an open-wheel
Formula racing car 272 mm long that rolls on four wheels. Every part stays
attached through the transformation: nothing is removed, nothing is left
over. The robot reads as a racing car standing on its tail: the car's nose
runs down the chest, its front wheels sit on the shoulders, its rear wheels
on the calves, and its rear wing rises behind the head as a backpack.

Inventor: `rowan-vale`. Detail and motion share the object: the robot is
judged on its silhouette and the car on whether every part packs back into
it.

## Unique geometries

| Geometry | Count | Robot | Car |
|---|---|---|---|
| `torso` | 1 | Chest core, shoulders, hips, cockpit on the back | Monocoque, cockpit and halo, inner sidepods |
| `nose` | 1 | Nose plate down the chest, front wing across the belly | Nose cone and front wing |
| `head` | 1 | Helmeted head with a visor | Hidden in the pocket under the nose root |
| `arm-shell` | 2 | Upper arm | Front sidepod, outer half |
| `forearm` | 2 | Forearm and fist | Folded inside the sidepod |
| `thigh` | 2 | Thigh | Rear sidepod, front half |
| `shin` | 2 | Shin and boot | Rear sidepod, rear half, floor and gearbox |
| `spine` | 1 | Backpack: boom and rear wing behind the head | Engine cover, airbox and rear wing |
| `front-wheel` | 2 | On the shoulders | Front wheels |
| `rear-wheel` | 2 | On the outer sides of the calves | Rear wheels |

`arm-shell#2`, `forearm#2`, `thigh#2` and `shin#2` are the mirror images of
`#1`. Every `#1`, including `front-wheel#1` and `rear-wheel#1`, is on the +X
side.

**Focal Component: the nose.** In the Display Pose the red nose plate down
the chest is the largest unbroken form at the centre of the figure, with the
front wing below it and the helmet above. It costs the torso its own chest
detail: the chest behind the nose is a plain core with engraved panel lines.

## Frame, poses and composition

Assembly coordinates in millimetres, in the Display Pose: X toward the
figure's left, front is -Y, Z up from the desk; the figure is centred on X 0.

**Display Pose: robot.** Standing upright on both boots, arms hanging
straight at the sides, legs straight, head raised, spine flipped up. Envelope
101 (X) x 68.5 (Y, -33 to 35.5) x 221 (Z). Landmarks: boots 0 to 27, rear
wheel axles 55, knee pins 80.5, hip pins 102, belly wing 99 to 128, nose
plate 110 to 180, shoulder pins 157, front wheel axles 188, helmet top 197,
rear wing top 221. Widths: arms across 101, front wheels across 94, torso 58,
legs across 51 at the thighs and 60 at the shins.

**Car pose.** Reached by the moves under Transformation. In assembly
coordinates the car stands on its tail: its length runs along Z (-11 to
261), its underside faces -Y and its top +Y. Laid down on its underside it
is 272 long, 101 wide across the front sidepods and 44 tall, resting on all
four wheels with every other part at least 1.5 above the ground.

Release frames the robot in the Display Pose against `#f5f0e6` from the
assembly reference's camera, straight from the front, with the nose plate on
the frame's vertical centre line.

## Palette

Multi-colour prints; colours change only at the boundaries named here.

| Geometry | Colour |
|---|---|
| `torso` | black, with a red halo |
| `nose` | racing red cone with a white stripe down each side; black wing with red endplates |
| `head` | white and red helmet, blue visor band |
| `arm-shell` | white with two red panels on the outboard face |
| `forearm` | white with red side panels, black fist |
| `thigh` | racing red |
| `shin` | racing red with a white stripe panel down the front; black boot |
| `spine` | black, red wing endplates |
| `front-wheel`, `rear-wheel` | black |

## Per-geometry spec

All positions are in the Display Pose; the `#1` part is given and `#2`
mirrors X.

**Torso.** A core block 58 wide (X -29 to 29) x 26 deep (Y -13 to 13), Z 99
to 180, its front face plain with engraved panel lines. A head pocket 21 x 18
(X -10.5 to 10.5, Y -10 to 8), open at the top, floor at Z 156; its front
wall is cut down to Z 170, so the neck shows. A 9 x 9 neck bore runs from the
pocket floor down to Z 119. Two wheel towers, X 16 to 29 each side, Y -13 to
13, rise to Z 192; each carries an Ø8 stub boss out to X 30.5 on the axis
Y 0, Z 188, with a 45 degree gusset under it. On the front top edge, two Ø7
hinge cheeks (X 10.5 to 16 each side) on the axis Y -14, Z 180, each with a
45 degree gusset under it, flanking the nose knuckle's seat (cut round the
knuckle with 0.5 clearance). On the back: a recessed cockpit 3 deep over
Z 125 to 150, a raised halo hoop X -9 to 9, Y 13 to 20, Z 125 to 152 with
its underside chamfered 45 degrees, two spine cheeks (X 10.5 to 15 each side,
Y 13 to 27.5, Z 99 to 111) on the axis Y 22.5, Z 105, and a spine lane
X -10.5 to 10.5, Y 9 to 13.5, Z 99 to 106 cut between them. The bottom
carries two hip slots (X 3.5 to 14.5 each side, Y -9 to 5, Z 99 to 108,
pointed-arch tops). Each side wall carries the shoulder bore along X at Y -2,
Z 157. Walls 3.0. Prints standing on its bottom face (Z 99).

**Nose.** One part. A knuckle Ø7 x 20 (X -10 to 10) on the hinge axis Y -14,
Z 180. The nose cone hangs from it down the chest, its outer face sculpted as
a nose cone: 18 wide and 14 deep (Y -33 to -19) at Z 176, tapering to 12
wide at Z 140, then 12 wide and 11 deep (Y -30 to -19) down to its blunt tip
at Z 110, 4 wide, whose underside is chamfered 45 degrees. The front wing
below it: a plate 54 wide (X -27 to 27) x 29 tall (Z 99 to 128) x 6 thick
(Y -21 to -15), with an endplate 2 wide x 10 deep (Y -24 to -14) at each end
(X 25 to 27); the cone's tip overlaps the wing's upper half. Prints standing
on the wing's leading face (Z 99).

**Head.** A helmet 19 wide x 16 deep (Y -8.5 to 7.5) x 19 tall (Z 178 to 197)
with a blue visor band across its front face and a raised crest, 2 wide and
1.5 high, along its top centre line. Under it a square neck post 8 x 8
(X -4 to 4, Y -5 to 3), Z 143 to 178, with a slot 3.4 wide (in Y) through it
along X from Z 147.9 to 173.1. Prints on its back face.

**Arm shell.** A C-channel 20 wide (X 30.5 to 50.5) x 22 deep (Y -13 to 9),
Z 118 to 163: front wall 3, inboard and outboard walls 2.5, open at the back
and the bottom; a forearm cavity X 33 to 48, Y -10 to 9, Z 118 to 152.6;
above it a solid top block whose top is chamfered 45 degrees front and back
to a 10 wide flat at Z 163. Two elbow cheeks (X 30.5 to 33 and 48 to 50.5)
reach down to Z 118, rounded about the elbow axis Y -2, Z 124. The shoulder
bore runs along X through the top block at Y -2, Z 157. Prints on its front
face.

**Forearm.** A block 14 wide (X 33.5 to 47.5) x 15 deep (Y -9.5 to 5.5),
Z 97 to 124, ending at the top in a knuckle rounded R7.5 about the elbow axis
Y -2, Z 124; the bottom 13 is a closed fist as wide as the forearm, with
three finger grooves across its front. Prints on its outboard face.

**Thigh.** A block 25 wide (X 0.5 to 25.5) x 22 deep (Y -13 to 9), Z 77.5 to
92, stepping in to Y -10 to 6 up to Z 95, topped by a hip tongue 10 wide (X 4
to 14) x 8 deep (Y -6 to 2) to Z 102, rounded R4 about the hip axis Y -2,
Z 102. A knee slot X 7.5 to 22.5, Y -8.5 to 4.5, Z 77.5 to 85 with a
pointed-arch top, and a notch across the back of the knee, Y 0 to 9, Z 77.5
to 87. Prints standing on its bottom face (Z 77.5).

**Shin.** A block 29.5 wide (X 0.5 to 30) x 22 deep, Z 27 to 72, its top
tapering in to X 2.5 to 28 and Y -9 to 5 up to Z 76, topped by a knee tongue
14 wide (X 8 to 22) x 8 deep, rounded R4 about the knee axis Y -2, Z 80.5.
The front carries a raised knee pad 1.0 proud and a white stripe panel. Below
it the boot, 28 wide (X 3.5 to 31.5), Y -13 to 9, Z 0 to 27, with a heel out
to Y 14 over X 11 to 31.5; a 45 degree chamfer under the shin's inboard edge
meets the boot. The rear wheel's bore runs along X into the shin's outer face
at Y -2, Z 55. Prints standing on its boot sole.

**Spine.** A knuckle Ø12 x 20 (X -10 to 10) on the axis Y 22.5, Z 105; a boom
20 wide x 13.5 deep (Y 22 to 35.5) up to Z 221, with an airbox scoop on its
lower end; the rear wing on its front face: a plate 83 wide (X -41.5 to 41.5)
x 16 tall (Z 205 to 221) x 5 thick (Y 22 to 27), with an endplate 3 wide x 12
deep (Y 20 to 32), Z 199.5 to 221, at each end (X 38.5 to 41.5). Prints
upside down on the wing's top face (Z 221).

**Front wheel.** Ø38 x 16, a tyre with a plain tread and a five-spoke rim
face on its outer side, an Ø3.2 bore. Prints on its outer face.

**Rear wheel.** Ø34 x 12, the same tyre and five-spoke rim face, an Ø3.2
bore. Prints on its outer face.

## Joints

Every hinge is a purchased steel ISO 8734 dowel pin Ø3, pressed into Ø2.9
bores on one side and turning in Ø3.1 bores (friction for posing) or Ø3.2
bores (wheels) on the other. Each wheel is held by a purchased Ø3 push-on
cap (starlock) on the dowel's outer end. Every horizontal bore is a teardrop
with its point away from the bed. No glue.

| Joint | Dowel | Pressed into | Turns in | Axis |
|---|---|---|---|---|
| Nose hinge | 3 x 32 | torso cheeks | nose knuckle | X, at Y -14, Z 180 |
| Head retainer | 3 x 20 | torso, both sides of the neck bore | neck post slot | X, at Y -1, Z 149.5 |
| Shoulder | 3 x 20, each | arm shell top block | torso side wall | X, at Y -2, Z 157 |
| Elbow | 3 x 20, each | arm shell cheeks | forearm knuckle | X, at Y -2, Z 124 |
| Hip | 3 x 20, each | torso slot walls | thigh tongue | X, at Y -2, Z 102 |
| Knee | 3 x 20, each | thigh slot walls | shin tongue | X, at Y -2, Z 80.5 |
| Spine hinge | 3 x 30 | torso spine cheeks | spine knuckle | X, at Y 22.5, Z 105 |
| Front wheels | 3 x 30, each | torso tower and stub boss, 12 deep | wheel bore | X, at Y 0, Z 188 |
| Rear wheels | 3 x 26, each | shin, 12 deep | wheel bore | X, at Y -2, Z 55 |

## Transformation

From robot to car, in this order (reverse for car to robot):

1. Flip the spine down 180 degrees about its hinge (-180 about +X): the boom
   lies 0.5 above the legs' backs between the heels, and the rear wing sits
   behind the boots.
2. Fold each forearm up and back 180 degrees about its elbow (+180 about +X)
   into its arm shell's cavity.
3. Push the head down 22 into its pocket.
4. Fold the nose up 180 degrees about its hinge (-180 about +X), so it stands
   above the torso over the head pocket.
5. Lay the car down on its wheels.

Posing in the robot: shoulders 90 forward and 30 back; elbows 90 forward;
hips 20 forward and 20 back; knees 45 back.

## Motion and fit

- Every moving part keeps at least 0.5 mm from every other part through each
  transformation move and each posing range, and in both poses.
- Motion check plan: `--check-motion true` on the wish and on every resume
  and correction; one sweep per transformation move (spine, forearm#1,
  forearm#2, head, nose) in at most 10 steps, each against only the parts it
  can reach. A skipped, killed or timed-out sweep fails the motion
  requirement, never passes it.
- In the car pose the wheels are the lowest parts: the nose knuckle and the
  torso's nose cheeks stand 1.5 above the ground, the underside 6.
- Assembled, not printed in place: press each dowel from outside after
  seating its part; the head's retainer dowel goes in last through the torso.

## Print and handling

Workshop prints at a 0.4 mm nozzle; every part prints without support in
the stance named above. Every point, chisel, keel and V underside ends in a
flat land at least 0.8 mm across (one print minimum at a 0.4 mm nozzle). A
drawn detail under the print minimums is enlarged to the minimum; when the
enlarged detail does not fit its spot, it is left out, and this contract
names it. Panel lines and finger grooves are engraved 0.6 wide and 0.5 deep;
nothing is left out.

Load-bearing sections are at least 3 mm: torso walls 3.0, arm shell walls
2.5 beside a 3.0 front wall, every tongue 8 deep, the neck post 8, the boom
20. A drop lands on a shoulder wheel or a boot; the wheels and the head are
the first to come loose, and each presses back on its dowel. The robot
stands unsupported: its centre of mass lies within 0.5 mm of the boots'
centre line, 13.3 behind their toes and 8.7 ahead of their heels.

```design-contract
{
  "schema_version": 4,
  "title": "Racer Mecha",
  "inventor": "rowan-vale",
  "envelope_mm": [101, 68.5, 221],
  "references": [
    {"file": "ref-01-racer-mecha.png", "shows": "assembly", "camera": [-90, 0]},
    {"file": "ref-02-torso.png", "shows": "geometry:torso", "camera": [-90, 0]},
    {"file": "ref-03-nose.png", "shows": "geometry:nose", "camera": [-90, 0]},
    {"file": "ref-04-head.png", "shows": "geometry:head", "camera": [-90, 0]},
    {"file": "ref-05-arm-shell.png", "shows": "geometry:arm-shell", "camera": [-90, 0]},
    {"file": "ref-06-forearm.png", "shows": "geometry:forearm", "camera": [-90, 0]},
    {"file": "ref-07-thigh.png", "shows": "geometry:thigh", "camera": [-90, 0]},
    {"file": "ref-08-shin.png", "shows": "geometry:shin", "camera": [-90, 0]},
    {"file": "ref-09-spine.png", "shows": "geometry:spine", "camera": [-90, 0]},
    {"file": "ref-10-front-wheel.png", "shows": "geometry:front-wheel", "camera": [0, 0]},
    {"file": "ref-11-rear-wheel.png", "shows": "geometry:rear-wheel", "camera": [0, 0]}
  ],
  "geometries": [
    {"id": "torso", "name": "Torso", "count": 1, "extents_mm": [61, 45, 93], "wall_min_mm": 3.0},
    {"id": "nose", "name": "Nose and front wing", "count": 1, "extents_mm": [54, 22.5, 84.5], "wall_min_mm": 2.0},
    {"id": "head", "name": "Head", "count": 1, "extents_mm": [19, 16, 54], "wall_min_mm": 3.0},
    {"id": "arm-shell", "name": "Upper arm shell", "count": 2, "extents_mm": [20, 22, 45], "wall_min_mm": 2.5},
    {"id": "forearm", "name": "Forearm and fist", "count": 2, "extents_mm": [14, 15, 34.5], "wall_min_mm": 3.0},
    {"id": "thigh", "name": "Thigh", "count": 2, "extents_mm": [25, 22, 28.5], "wall_min_mm": 3.0},
    {"id": "shin", "name": "Shin and boot", "count": 2, "extents_mm": [31, 27, 84.5], "wall_min_mm": 3.0},
    {"id": "spine", "name": "Spine and rear wing", "count": 1, "extents_mm": [83, 19, 122], "wall_min_mm": 3.0},
    {"id": "front-wheel", "name": "Front wheel", "count": 2, "extents_mm": [38, 38, 16], "wall_min_mm": 2.0},
    {"id": "rear-wheel", "name": "Rear wheel", "count": 2, "extents_mm": [34, 34, 12], "wall_min_mm": 2.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly", "text": "In the Display Pose the robot stands upright on both boots, its helmet top at Z 197, arms hanging straight: the red nose plate runs down the centre of the chest from Z 180 to its tip at Z 110, the black front wing lies across the belly from Z 99 to 128, a front wheel sits on each shoulder at Z 188, a rear wheel on the outer side of each calf at Z 55, and the rear wing rises behind the head to Z 221."},
    {"id": "R02", "scope": "assembly", "text": "In the car pose the toy is an open-wheel Formula car 272 mm long, 101 wide and 44 tall: nose cone and front wing ahead of the front wheels, the arm shells as front sidepods, the legs as rear sidepods, the spine as engine cover with the rear wing behind the tail, and no robot part showing above the bodywork."},
    {"id": "R03", "scope": "assembly", "text": "The robot becomes the car by five moves and no part comes off: the spine flips down 180 degrees onto the legs, each forearm folds 180 degrees up into its arm shell, the head slides 22 mm down into its pocket, the nose folds up 180 degrees over the pocket, and the car is laid on its wheels."},
    {"id": "R04", "scope": "assembly", "text": "In the car pose the car rests on all four wheels, every other part at least 1.5 mm above the ground, and each wheel turns freely on its dowel."},
    {"id": "R05", "scope": "assembly", "text": "Posing ranges in the robot: shoulders 90 degrees forward and 30 back, elbows 90 forward, hips 20 forward and 20 back, knees 45 back, each holding its pose by friction."},
    {"id": "R06", "scope": "assembly", "text": "Every moving part keeps at least 0.5 mm from every other part through each transformation move and posing range and in both poses. Checked with --check-motion true: one sweep per transformation move in at most 10 steps against only the parts it can reach; a skipped, killed or timed-out sweep fails this requirement."},
    {"id": "R07", "scope": "assembly", "text": "Every purchased-part seat is derived from a catalog STEP file, or from the documented envelope when the catalog search is a recorded miss, and the bill of materials lists exactly 1 dowel 3 x 32, 9 dowels 3 x 20, 3 dowels 3 x 30, 2 dowels 3 x 26 and 4 push-on caps for 3 mm shafts."},
    {"id": "R08", "scope": "assembly", "text": "Every joint is built as its Interface text states, each hinge a purchased dowel pressed into a 2.9 mm bore on one side and turning in a 3.1 mm bore (3.2 for the wheels) on the other, with no glue."},
    {"id": "R09", "scope": "assembly", "text": "The robot stands unsupported in the Display Pose: its centre of mass lies over the boots, which span Y -13 to 9."},
    {"id": "R10", "scope": "geometry:torso", "text": "A 58 x 26 core with engraved panel lines on its front and two wheel towers 13 wide rising 12 above its top corners; between them an open head pocket whose front wall is cut lower so the neck shows, and a small round hinge cheek either side of the pocket on the front top edge."},
    {"id": "R11", "scope": "geometry:torso", "text": "An Ø8 stub boss on the outer side of each tower for a front wheel; on the back a recessed cockpit, a raised hoop halo and two spine hinge cheeks at the bottom."},
    {"id": "R12", "scope": "geometry:nose", "text": "A red nose cone with a white stripe down each side, 18 wide at its root tapering to 12, ending in a blunt 4 wide tip, hanging from a hinge knuckle at its root."},
    {"id": "R13", "scope": "geometry:nose", "text": "Below the tip a black front wing 54 wide and 29 tall with a red endplate at each end; the cone's tip overlaps the wing's upper half."},
    {"id": "R14", "scope": "geometry:head", "text": "A white and red helmet 19 wide and 19 tall with a blue visor band across its front and a raised crest along its top centre line, on a square 8 mm neck post 35 long with a slot through it."},
    {"id": "R15", "scope": "geometry:arm-shell", "text": "A 20 x 22 white channel open at the back and the bottom, its top chamfered 45 degrees front and back, with two elbow cheeks at its bottom and two red panels on its outboard face."},
    {"id": "R16", "scope": "geometry:forearm", "text": "A 14 x 15 white forearm with red side panels, ending at the top in a rounded knuckle and at the bottom in a closed black fist as wide as the forearm, with three finger grooves across its front."},
    {"id": "R17", "scope": "geometry:thigh", "text": "A 25 x 22 red block whose top steps in and rises into a rounded hip tongue 10 wide toward its inboard side, with a knee slot and a notch across the back of the knee."},
    {"id": "R18", "scope": "geometry:shin", "text": "A 29.5 x 22 red shin with a raised knee pad and a white stripe panel on its front, a rounded knee tongue 14 wide on top, and a black boot 28 wide below that sticks out 1.5 past the shin's outer side and steps in 3 from its inner side."},
    {"id": "R19", "scope": "geometry:spine", "text": "A black boom 20 wide with an airbox scoop near its hinge knuckle, carrying at its top a rear wing 83 wide and 16 tall with a red endplate at each end that reaches 5.5 below the wing."},
    {"id": "R20", "scope": "geometry:front-wheel", "text": "A black tyre 38 across and 16 wide with a plain tread and a five-spoke rim face on its outer side."},
    {"id": "R21", "scope": "geometry:rear-wheel", "text": "A black tyre 34 across and 12 wide with a plain tread and a five-spoke rim face on its outer side."}
  ],
  "interfaces": [
    {"id": "nose-fold", "kind": "coupled", "components": ["nose", "head", "torso"],
     "text": "A 3 x 32 dowel pressed into the torso's two Ø7 front cheeks (X 10.5 to 16 each side, axis Y -14, Z 180) turns the nose's Ø7 x 20 knuckle (X -10 to 10) on a 3.1 bore; the torso's front top edge is cut round the knuckle with 0.5 clearance. Robot pose: the nose hangs down the chest, its back 1 in front of the torso's front face (Y -13) and its wing 3.5 inside the arm shells. Car pose: the nose stands up from Z 180 over the head pocket, 5 above the lowered helmet.",
     "yielding": "nose",
     "poses": {"steps": 10, "movers": [
       {"component": "nose", "rotation": {"axis_point": [0, -14, 180], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": -180}},
       {"component": "head", "translation": {"vector": [0, 0, -22]}}]}},
    {"id": "head-slide", "kind": "coupled", "components": ["head", "torso"],
     "text": "The head's 8 x 8 neck post slides in the torso's 9 x 9 neck bore below the head pocket (X -4.5 to 4.5, Y -5.5 to 3.5, floor Z 119). A 3 x 20 dowel pressed across the torso along X at Y -1, Z 149.5 runs through the post's 3.4 wide slot and stops it at both ends: raised, the helmet's underside is at Z 178 and the neck shows above the pocket's lowered front wall (Z 170); lowered by 22, the helmet rests on the pocket floor at Z 156.",
     "yielding": "head",
     "poses": {"steps": 10, "movers": [
       {"component": "head", "translation": {"vector": [0, 0, -22]}}]}},
    {"id": "shoulder-1", "kind": "coupled", "components": ["arm-shell#1", "forearm#1", "torso", "front-wheel#1"],
     "text": "A 3 x 20 dowel pressed along X into arm shell 1's top block at Y -2, Z 157 turns in a 3.1 bore in the torso's +X side wall (X 23 to 29). The shell's inboard face is 1.5 from the torso side (X 29); its chamfered top stays at least 0.5 below front wheel 1 at every angle from 90 degrees forward to 30 back.",
     "yielding": "arm-shell#1",
     "poses": {"steps": 10, "movers": [
       {"component": "arm-shell#1", "rotation": {"axis_point": [0, -2, 157], "axis_direction": [1, 0, 0], "start_deg": 30, "end_deg": -90}},
       {"component": "forearm#1", "rotation": {"axis_point": [0, -2, 157], "axis_direction": [1, 0, 0], "start_deg": 30, "end_deg": -90}}]}},
    {"id": "shoulder-2", "kind": "coupled", "components": ["arm-shell#2", "forearm#2", "torso", "front-wheel#2"],
     "text": "Mirror of shoulder-1 on the -X side: a 3 x 20 dowel pressed into arm shell 2's top block at Y -2, Z 157 turns in a 3.1 bore in the torso's -X side wall; the shell stays 1.5 from the torso side and at least 0.5 below front wheel 2 from 90 degrees forward to 30 back.",
     "yielding": "arm-shell#2",
     "poses": {"steps": 10, "movers": [
       {"component": "arm-shell#2", "rotation": {"axis_point": [0, -2, 157], "axis_direction": [1, 0, 0], "start_deg": 30, "end_deg": -90}},
       {"component": "forearm#2", "rotation": {"axis_point": [0, -2, 157], "axis_direction": [1, 0, 0], "start_deg": 30, "end_deg": -90}}]}},
    {"id": "elbow-1", "kind": "coupled", "components": ["forearm#1", "arm-shell#1"],
     "text": "A 3 x 20 dowel pressed into arm shell 1's two elbow cheeks (X 30.5 to 33 and 48 to 50.5) along X at Y -2, Z 124 turns forearm 1's R7.5 knuckle on a 3.1 bore. The forearm folds 180 degrees up and back into the shell's cavity (X 33 to 48, Y -10 to 9, Z 118 to 152.6), entering through its open back; it also bends 90 degrees forward. 0.5 clearance throughout.",
     "yielding": "forearm#1",
     "poses": {"steps": 10, "movers": [
       {"component": "forearm#1", "rotation": {"axis_point": [40.5, -2, 124], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 180}}]}},
    {"id": "elbow-2", "kind": "coupled", "components": ["forearm#2", "arm-shell#2"],
     "text": "Mirror of elbow-1: a 3 x 20 dowel pressed into arm shell 2's elbow cheeks along X at Y -2, Z 124 turns forearm 2's knuckle on a 3.1 bore; the forearm folds 180 degrees up and back into the cavity through the open back, and bends 90 degrees forward.",
     "yielding": "forearm#2",
     "poses": {"steps": 10, "movers": [
       {"component": "forearm#2", "rotation": {"axis_point": [-40.5, -2, 124], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 180}}]}},
    {"id": "hip-1", "kind": "coupled", "components": ["thigh#1", "shin#1", "rear-wheel#1", "torso"],
     "text": "Thigh 1's rounded tongue (X 4 to 14, Y -6 to 2) sits in the torso's hip slot (X 3.5 to 14.5, Y -9 to 5, up to Z 108); a 3 x 20 dowel pressed along X through the slot walls at Y -2, Z 102 turns it on a 3.1 bore. The thigh's stepped top stays 0.8 below the torso from 20 degrees forward to 20 back.",
     "yielding": "thigh#1",
     "poses": {"steps": 10, "movers": [
       {"component": "thigh#1", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "shin#1", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "rear-wheel#1", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}}]}},
    {"id": "hip-2", "kind": "coupled", "components": ["thigh#2", "shin#2", "rear-wheel#2", "torso"],
     "text": "Mirror of hip-1: thigh 2's tongue sits in the torso's -X hip slot on a 3 x 20 dowel along X at Y -2, Z 102, turning on a 3.1 bore, 0.8 clear from 20 degrees forward to 20 back.",
     "yielding": "thigh#2",
     "poses": {"steps": 10, "movers": [
       {"component": "thigh#2", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "shin#2", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}},
       {"component": "rear-wheel#2", "rotation": {"axis_point": [0, -2, 102], "axis_direction": [1, 0, 0], "start_deg": -20, "end_deg": 20}}]}},
    {"id": "knee-1", "kind": "coupled", "components": ["shin#1", "rear-wheel#1", "thigh#1"],
     "text": "Shin 1's rounded knee tongue (X 8 to 22, Y -6 to 2) sits in thigh 1's knee slot (X 7.5 to 22.5, Y -8.5 to 4.5, Z 77.5 to 85); a 3 x 20 dowel pressed along X through the thigh's slot walls at Y -2, Z 80.5 turns it on a 3.1 bore. The notch across the back of the thigh (Y 0 to 9, Z 77.5 to 87) lets the shin bend 45 degrees back with 0.5 clearance.",
     "yielding": "shin#1",
     "poses": {"steps": 10, "movers": [
       {"component": "shin#1", "rotation": {"axis_point": [0, -2, 80.5], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 45}},
       {"component": "rear-wheel#1", "rotation": {"axis_point": [0, -2, 80.5], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 45}}]}},
    {"id": "knee-2", "kind": "coupled", "components": ["shin#2", "rear-wheel#2", "thigh#2"],
     "text": "Mirror of knee-1: shin 2's tongue in thigh 2's knee slot on a 3 x 20 dowel along X at Y -2, Z 80.5, turning on a 3.1 bore, bending 45 degrees back with 0.5 clearance.",
     "yielding": "shin#2",
     "poses": {"steps": 10, "movers": [
       {"component": "shin#2", "rotation": {"axis_point": [0, -2, 80.5], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 45}},
       {"component": "rear-wheel#2", "rotation": {"axis_point": [0, -2, 80.5], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": 45}}]}},
    {"id": "spine-flip", "kind": "coupled", "components": ["spine", "torso", "thigh#1", "thigh#2", "shin#1", "shin#2", "front-wheel#1", "front-wheel#2"],
     "text": "A 3 x 30 dowel pressed into the torso's two back cheeks (X 10.5 to 15 each side, axis Y 22.5, Z 105) turns the spine's Ø12 x 20 knuckle on a 3.1 bore. Robot pose: the boom stands behind the back (Y 22 to 35.5), clear of the halo (Y 20); the rear wing's endplates (Y 20 to 32, down to Z 199.5) stand behind the front wheels and its plate above the helmet. Car pose: flipped 180 degrees back and down, the boom lies 0.5 above the legs' backs (Y 9) between the heels, the torso's spine lane (X -10.5 to 10.5, Y 9 to 13.5, Z 99 to 106) taking its root.",
     "yielding": "spine",
     "poses": {"steps": 10, "movers": [
       {"component": "spine", "rotation": {"axis_point": [0, 22.5, 105], "axis_direction": [1, 0, 0], "start_deg": 0, "end_deg": -180}}]}},
    {"id": "front-wheels", "kind": "static", "components": ["front-wheel#1", "front-wheel#2", "torso"],
     "text": "Each front wheel turns on a 3 x 30 dowel pressed 12 deep into the torso tower and its Ø8 stub boss on the axis Y 0, Z 188, the wheel's inner face 0.5 outside the boss (X 31 to 47 and -31 to -47), held by a push-on cap."},
    {"id": "rear-wheels", "kind": "static", "components": ["rear-wheel#1", "rear-wheel#2", "shin#1", "shin#2"],
     "text": "Each rear wheel turns on a 3 x 26 dowel pressed 12 deep into its shin's outer face on the axis Y -2, Z 55, the wheel's inner face 0.5 outside the shin (X 30.5 to 42.5 and -30.5 to -42.5), held by a push-on cap."}
  ]
}
```
