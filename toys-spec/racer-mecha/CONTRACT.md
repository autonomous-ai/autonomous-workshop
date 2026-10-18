# Racer Mecha

A heroic robot in detailed toy armour, 250 mm to the top of its helmet, that
transforms by hand, with no part removed, into an open-wheel Formula racing
car 360.75 mm long on four wheels.

Inventor: `rowan-vale`.

`arm-shell#2`, `forearm#2`, `thigh#2`, `shin#2`, `boot#2` and `wing#2` are
the mirror images of `#1`. Every `#1` is on the +X side.

**Focal Component: the torso.** In the Display Pose the cockpit opening ringed
by its red halo, in the middle of the broad black chest, draws the eye first.

## Frame, poses and composition

Assembly coordinates in millimetres, in the Display Pose: X toward the
figure's left, front is -Y, Z up from the desk; the figure is centred on X 0.

**Display Pose: robot.** Standing upright on both boots, arms hanging
straight at the sides, legs straight and drawn out to full length, head
raised, nose lying down the back, wing halves folded on the toes. Envelope
126 (X) x 83.25 (Y, -50.75 to 32.5) x 250 (Z). Landmarks: boots 0 to 31.5,
ankle pins 14.75, shin cuff 32 to 54.25, shin block 54.25 to 88.75, rear wheel
axles 76, knee guard over the slide post 88.75 to 116, thigh 108.5 to 138.75,
hip pins 145, torso 141.25 to 229.5, halo 170 to 216.25 round the cockpit
177.25 to 209, shoulder pins 193.25, arms 102.75 to 204.25 with the fists
102.75 to 131.75, shoulder towers to 235.5, front wheel axles 228.25 and tops
247.75, helmet 227 to 250; behind: the nose hinge at Z 232, the front wing 128
to 145.

**Car pose.** In assembly
coordinates the car stands on its tail: its length runs along Z (-24.75 to
336), its floor faces +Y and its top -Y; laid down on its floor it is the
car R03 and R05 give.

Release frames the Display Pose against `#f5f0e6`, the halo centred and
facing the hero camera (`render_review` [-55, 26]) unobstructed.

## Palette

Multi-colour prints; colours change only at the boundaries named here.

| Geometry | Colour |
|---|---|
| `torso` | black, with a red halo, a white stripe down each leg |
| `nose` | racing red cone with angled white livery down each side, red on over the wing; black knuckle; black front wing with red endplates |
| `head` | white and red helmet, blue visor band |
| `arm-shell` | white with a red band round the upper arm and a red tab under it |
| `forearm` | black |
| `thigh` | racing red with two white chevron panels on the front |
| `shin` | racing red with a white zig-zag stripe down the front; red knee guard; black slide post |
| `boot` | black |
| `wing` | black plate; red blade with a white gurney lip and a black endplate cap |
| `front-wheel`, `rear-wheel` | black |

## Per-geometry spec

All positions are in the Display Pose; the `#1` part is given and `#2`
mirrors X.

**Torso.** A core block 70 wide (X -35 to 35) x 31.5 deep (Y -15.75 to
15.75), Z 141.25 to 229.5. A head pocket 21 x 20.5 (X -10.5 to 10.5, Y -9.75
to 10.75), open at the top, floor at Z 200.5; a notch 13 wide (X -6.5 to 6.5)
cuts its front wall down to Z 217.5, so the neck shows. A 9 x 10.75 neck bore
(X -4.5 to 4.5, Y 0 to 10.75) runs from the pocket floor down to Z 163.75.
Two shoulder towers jut out over the arms, X 35 to 43 each side, Y -15.75
to 15.75, up to Z 235.5; each tower's underside is a 52 degree wedge rising
from the side wall at Z 208.3 to Z 218.5 at its outer face, passing 6.5 over the
arm's top (Z 204.25). Each side wall carries a shoulder boss, Ø14.5, X
35 to 36.5, on the axis Y -2.5, Z 193.25, a 52 degree gusset under it, backed inside the wall by a Ø10 boss to X 28.5 that holds the shoulder dowel. On the
front: the cockpit, an opening 20 wide (X -10 to 10) and 4.25 deep (to Y
-11.5) over Z 177.25 to 209, 1.75 clear of the head pocket behind it, its top
edge rising at 52 degrees, and round it a raised red halo 8.5 proud (Y -24.25
to -15.75), a closed loop X -15 to 15, Z 170 to 216.25, of two 4 wide legs
(X 11 to 15 each side) joined by a 6 thick bottom bar (Z 170 to 176) and
a 6 thick top bar (Z 210.25 to 216.25), its corners faceted blocks, each bar's
underside growing out of the chest at a 52 degree rise. At the top of the
back, two Ø8.5 nose hinge cheeks (X 10.5 to 14.5 each side) on the axis Y 17,
Z 232, each with a 52 degree gusset under it, flanking the nose knuckle's
seat, a cylinder of radius 4.75 about the axis over X -10.5 to 10.5. Elsewhere
layered plates with vents, a collar of plates round the pocket. The bottom carries two hip slots (X 8.5 to
19.5 each side, Y -11 to 6, Z 141.25 to 152.25, pointed-arch tops). Prints standing on its bottom face (Z 141.25).

**Nose.** A knuckle 20 wide (X -10 to 10) on
the hinge axis Y 17, Z 232: round, radius 4.25, toward the top and a teardrop
toward the root, its point 6.9 from the axis and its faces 38 degrees from
the cone's axis. A root block 20 wide (Y 16.25 to 25.25, Z 219.75 to 228.25)
joins it to the cone. The cone runs down the back, its outer face sculpted as
a nose cone with a raised centre ridge: 18 wide and 16.25 deep (Y 16.25 to 32.5) from Z 219.75 to
170.25, then 12 wide and 12.75 deep (Y 16.25 to 29) down to Z 143.75, then a
4.75 deep tip (Y 20.5 to 25.25) on to Z 135.25, its underside and the step at
Z 170.25 rising at 52 degrees; over the wing's outer face the cone runs on as
a red plate flush with it (the black face beside sunk 0.6), narrowing to a
blunt 6 at the wing's lower edge. The front wing at the tip: a plate 84 wide (X
-42 to 42) x 17 tall (Z 128 to 145) x 7.25 thick (Y 25.25 to 32.5,
flush with the cone's back), a main plane under a flap slat split by a 0.6
groove 5 below its top, a 2 x 1.2 slot through it beside each endplate, and
at each end (X 39 to 42) an endplate 3 wide x 10.75 deep (Y 21.75 to 32.5),
stepped, rising 3.5 over the wing to Z 148.5; the cone's tip overlaps the wing's upper half
(Z 135.25 to 143.75). Prints standing on the wing's lower face (Z 128).

**Head.** A helmet 19 wide x 19.5 deep (Y -9.25 to 10.25) x 23 tall (Z 227 to
250) with a blue visor band across its front face, faceted cheek guards and a
raised crest, 4 wide and 1.75 high, along its top centre line. Under it a neck
post 8 x 9.75 (X -4 to 4, Y 0.5 to 10.25), Z 190.75 to 227, its back face
flush with the helmet's, with a slot 3.4 wide (X -1.7 to 1.7) through it from
front to back from Z 194.15 to 223.85. Prints on its back face.

**Arm shell.** The whole white arm from shoulder to wrist: a C-channel 26 wide
(X 37 to 63) x 22 deep (Y -13.5 to 8.5), Z 131.75 to 193.25, topped by a
solid top block rounded R11 about the shoulder axis (Y -2.5, Z 193.25), so
its top is at Z 204.25 and it keeps that outline at every shoulder angle. Front
wall 3, inboard and outboard walls 2.5, open at the back and the bottom; a
fist cavity X 39.5 to 60.5, Y -10.5 to 8.5, Z 131.75 to 183.5. A red band
11.5 tall wraps its front and outer faces from Z 173.25 to 184.75, a red tab
6.5 wide hangs 5 below it mid-front, and a panel line at Z 170.25 splits the
upper arm from the lower. The side walls' bottoms
are the elbow cheeks, with the elbow bore along X at Y -2.5, Z 140. The
shoulder bore runs along X into the top block from its inboard face at Y
-2.5, Z 193.25. Prints on its front face.

**Forearm.** A black closed fist 20 wide (X 40 to 60) x 16.5 deep (Y -11.5
to 5), Z 102.75 to 140, ending at the top in a wrist knuckle rounded R7.5 about
the elbow axis Y -2.5, Z 140; under the knuckle a wrist guard down to Z 120
with a raised V plate 0.75 proud. Below Z 120 the hand curls: four fingers
3.5 wide (X 43.6 to 60), split by grooves 0.8 wide and 3 deep, stand 1.5
proud of the guard (front at Y -11.5), each in three segments split by 0.8
grooves at Z 111 and 106, its tip curling under, rounded R5 about X. A thumb
2.8 wide (X 40 to 42.8, Z 109 to 119), as proud, wraps the inboard corner;
under it the corner is cut away. Prints on its back face (Y 5); the wrist
knuckle meets the bed through 52 degree chords.

**Thigh.** A sleeve 18 wide (X 7.5 to 25.5) x 19 deep (Y -12 to 7), Z 108.5
to 135.75, open at the bottom: its cavity X 10 to 23, Y -9.5 to 4.5, up to Z
135.75, the ceiling's front and back edges bevelled 1.5 at 52 degrees; walls
2.5, their top outer edges bevelled 1 at 52 degrees. Over the cavity a roof
(Y -9.5 to 4.5), at least 1.5 thick, whose top is a low gable falling 20
degrees from Z 138.75 beside the tongue to Z 137.84 at its front and back edges. On it a hip tongue 10 wide (X 9
to 19) x 9 deep (Y -7 to 2) to Z 145, rounded R4.5 about the hip axis Y -2.5,
Z 145. Each side wall (X 7.5 to 10 and 23 to 25.5) carries a slide slot along
Z at Y -2.5, 3.2 wide, its ends rounded about Z 112.25 and Z 131.5 (R09's clicks). Prints
standing on its bottom face (Z 108.5).

**Shin.** A cuff 27.5 wide (X 2.75 to 30.25), flared both sides alike, x 22 deep (Y -12.5 to 9.5), Z
32 to 54.25, and above it a block 18 wide (X 7.5 to 25.5), Z 54.25 to 88.75,
the cuff's step rising at 52 degrees, with a white zig-zag stripe 5 wide down
the front of both, centred on X 16.5. On top the slide post, 12 wide (X 10.5
to 22.5) x 13 deep (Y -9 to 4), Z 88.75 to 116, its top front and back edges
bevelled 1.5 at 52 degrees. In front of the post a knee guard 18 wide (X
7.5 to 25.5) x 1.75 thick (Y -14.25 to -12.5) rises from the block's front face to
the post's top: in the robot it laps 7.5 over
the thigh's foot. Beside and behind the post the block's top slopes down at
52 degrees (to Z 84.91 at X 7.5 and 25.5, 81.71 at Y 9.5); only between guard
and post is it flat. The post carries the slide dowel's bore along X at Y
-2.5, Z 112.25. On the block's outer face an Ø9.5 boss (X 25.5 to 34.5) on
the rear wheel axis Y 2.5, Z 76. Below the cuff the ankle tongue, 14 wide (X
14 to 28) x 9.5 deep (Y -0.25 to 9.25), down to a round end R4.75 about the
ankle axis Y 4.5, Z 14.75. Prints upside down on the post's top face (Z 116).

**Boot.** A long wedge foot 32 wide (X 8 to 40), set outboard of the shin, Y
-50.75 to 13.75, Z 0 to 31.5, pointing forward (R10). Behind the ankle axis its top is
rounded R16.75 about the axis (Y 4.5, Z 14.75) down to the heel face at Y
13.75, Z 28.7. In front of the axis the top is flat at Z 31.5 to Y -12.45;
a face undercut 30 degrees from vertical drops back to Y -10.1, Z 27.5
behind the blade, and from there the toe slope, 0.5 under the wing plate,
falls forward at 30 degrees to Y -44.1, Z 7.9. The toe
face at Y -50.75 is 12 tall. At the toe two lugs 3.5 thick (X 8 to 11.5 and
36.5 to 40) are rounded R4.25 about the wing hinge axis Y -46.5, Z 12 and rise
to Z 16.25; between them an R4.75 clearance round the knuckle. A slot for the shin's tongue, X 13.5 to 28.5, Y -0.75 to the heel,
down to Z 9.5, open at the top and the heel. The ankle bores run along X
through the slot's side walls on the axis. A sole band 4 tall with tread
notches round it; a toe plate on the toe face. Prints on its sole.

**Wing.** One rear-wing half. A knuckle Ø8.5 x 24 (X 12
to 36) on the wing hinge axis (Y -46.5, Z 12); a plate 24 wide (X 12 to 36) x
3.5 thick, its underside tangent to the knuckle, running 38.75 from the axis
to the blade's back face; and at the plate's far end the blade, 39.25 wide (X
0.75 to 40) x 3.5 x 12 tall, square to the plate on its top side and reaching
inboard past the boot to 1.5 from the other blade. Folded, the blade leans forward 30
degrees, Z 27.7 to 38.1. Its outer 3 (X 37 to 40) is
a flush black endplate cap with a 1 x 2.5 slot front to back; a white gurney
lip 1 tall tops its front face on the outline, its underside rising at 52
degrees, the face below sunk 0.6 as a curved main plane. Prints on its plate's flat underside.

**Front wheel.** Ø39 x 16, a tyre with a chevron-grooved tread and a
five-spoke rim face on its outer side, the windows between the spokes open
through, an Ø3.2 bore. Prints on its inner face.

**Rear wheel.** Ø41 x 12, the same rim face and open windows, its tread
plain, split into segments by panel lines, an Ø3.2 bore. Prints on its inner
face.

## Joints

Every hinge is a purchased steel ISO 8734 dowel pin Ø3 as R09 sets out.
Each wheel is held by a purchased
Ø3 push-on cap (starlock) on the dowel's outer end. Every horizontal bore is a
teardrop with its point away from the bed. No glue.

## Transformation

From robot to car, in this order:

1. Push the head down 26.5 into its pocket.
2. Flip the nose 180 degrees up over the top of the back (+180 about +X):
   it stands above the torso over the head pocket, its front wing at the top
   (Z 319 to 336).
3. Fold each fist up and back 180 degrees about its wrist (+180 about +X)
   into its arm shell's cavity.
4. Fold each boot 90 degrees at the ankle (+90 about +X): the toe points
   down, the sole faces the back.
5. Push each shin 19.25 up into its thigh: the slide post fills the sleeve.
6. Stand each wing half up 60 degrees on its hinge (+60 about +X), off the
   toe slope until square to the boot's top: its plate rises from the toe and
   its blade points rearward; the two blades
   meet at the centre line, 1.5 apart.
7. Lay the car down on its back, on its wheels.

The fists do not bend forward: the arm shell's front wall reaches its bottom.

## Motion and fit

- The knee-slide dowel's clicks hold the robot standing at full length and
  the car at its short length; the ankle and wing hinges hold by friction.
- Assembled, not printed in place: each dowel is pressed in after its part
  is seated.

## Print and handling

Every part prints without support in
the stance named above. Every point, chisel, keel and V underside ends in a
flat land at least 0.8 mm across (one print minimum at a 0.4 mm nozzle). A
drawn detail under the print minimums is enlarged to the minimum; when the
enlarged detail does not fit its spot, it is left out, and this contract
names it. Panel lines are engraved 0.6 wide and 0.5 deep, 1.6 apart
at least; a vent is such slits at a 2.2 pitch, as many as fit. Every chamfer, bevel, gusset, arch, wedge and teardrop
is designed at most 38 degrees from vertical (a 52 degree rise).

Every large face (over 15 across) of the torso, thigh, shin, boot,
arm shell and nose cone is broken into faceted armour plates by engraved
panel lines; the plates are layered, a plate standing
0.6 to 1.2 proud of the one under it. A face's outermost plate lies on the
outline given here and those under it are sunk, so no plate grows a part
past its extents. Outer corners and edges carry bevels at the 52 degree
print angle, 2 to 4 across on the main silhouette corners the rows name; every other exposed outside edge a chamfer 0.8 across. A proud plate's edge that faces down in the print stance rises at 52 degrees.
A bed face carries engraved lines only, no plate. Edges
on the print-bed face, at a bore, a slot, a joint face, or on any face
another part comes within 2 mm of in a pose or move stay square, and no
proud plate or bevel goes there. A panel line or sunk plate is the one cut
allowed into a load-bearing wall: the arm shell's and the thigh's 2.5 walls
keep 2.0 under it, and none leaves less than a part's floor below.

Load-bearing sections are at least 3 mm: torso walls 3.0, arm shell and
thigh walls 2.5, every tongue at least 9 deep, the slide post 12 x 13, the
neck post 8, the wing plate 3.5 and blade 2.9, the toe lugs 3.5. The exceptions,
which the joints size: above a teardrop bore (faces 38 degrees from vertical)
inside a Ø8.5 cheek, lug or knuckle 1.9 on the torso and the boot, 1.7 on the
nose and the wing; the cockpit's 1.75 wall to the head pocket; the thigh's
1.5 roof; 2.15 from the slide slot's end at Z 112.25 to the thigh's bottom,
and above the slide dowel's bore in the post; 2.3 from the hip bore at Z 145
to the hip slot's bottom, and beside the neck post's 3.4 slot; 2.95 or 3.2
round an R4.5 or R4.75 tongue's Ø3.1 bore. The floors stay below these: the
torso and the boot 1.1, the nose and the wing 0.95, the thigh and the shin
1.4, the head 1.9, the fist 2.5. The robot
stands unsupported: its centre of mass lies at Y -1.6, 49.15 behind the toes
and 15.35 ahead of the heels.

```design-contract
{
  "schema_version":5,
  "title":"Racer Mecha",
  "inventor":"rowan-vale",
  "envelope_mm":[
    126,
    83.25,
    250
  ],
  "guides":[
    {"file":"guide-01-transformation.png","shows":"Car to robot in real colours, one move per step; robot and car from behind.","steps":["Stand the car up on its tail.","Fold the wing halves down onto the toes.","Pull the shins out of the thighs.","Fold the boots forward.","Fold the fists out of the arm shells.","Flip the nose down the back.","Raise the head."]},
    {"file":"guide-02-overall.png","shows":"Robot front-left, back-right; car; leg cut open, robot and car length."},
    {"file":"guide-03-torso.png","shows":"Ref, then back, front-left 3/4.","geometries":["torso"]},
    {"file":"guide-04-nose.png","shows":"Ref, then side profile, outer face 3/4.","geometries":["nose"]},
    {"file":"guide-05-head.png","shows":"Ref, then left side, back.","geometries":["head"]},
    {"file":"guide-06-arm-shell.png","shows":"Ref, then open back, outer side.","geometries":["arm-shell"]},
    {"file":"guide-07-forearm.png","shows":"Ref, then back, inboard side.","geometries":["forearm"]},
    {"file":"guide-08-thigh.png","shows":"Ref, then back from below, outer side.","geometries":["thigh"]},
    {"file":"guide-09-shin.png","shows":"Ref, then back, outer side.","geometries":["shin"]},
    {"file":"guide-10-boot.png","shows":"Ref, then toe-end 3/4, heel end.","geometries":["boot"]},
    {"file":"guide-11-wing.png","shows":"Ref, then back-outer 3/4, end profile.","geometries":["wing"]},
    {"file":"guide-12-front-wheel.png","shows":"Ref, then inner face, tread.","geometries":["front-wheel"]},
    {"file":"guide-13-rear-wheel.png","shows":"Ref, then inner face, tread.","geometries":["rear-wheel"]}
  ],
  "references":[
    {"file":"ref-01-racer-mecha.png","shows":"assembly","camera":[-90,15]},
    {"file":"ref-02-torso.png","shows":"geometry:torso","camera":[-90,15]},
    {"file":"ref-03-nose.png","shows":"geometry:nose","camera":[90,0]},
    {"file":"ref-04-head.png","shows":"geometry:head","camera":[-90,0]},
    {"file":"ref-05-arm-shell.png","shows":"geometry:arm-shell","camera":[-75,15]},
    {"file":"ref-06-forearm.png","shows":"geometry:forearm","camera":[-90,0]},
    {"file":"ref-07-thigh.png","shows":"geometry:thigh","camera":[-75,15]},
    {"file":"ref-08-shin.png","shows":"geometry:shin","camera":[-90,0]},
    {"file":"ref-09-boot.png","shows":"geometry:boot","camera":[0,15]},
    {"file":"ref-10-wing.png","shows":"geometry:wing","camera":[-45,0]},
    {"file":"ref-11-front-wheel.png","shows":"geometry:front-wheel","camera":[0,15]},
    {"file":"ref-12-rear-wheel.png","shows":"geometry:rear-wheel","camera":[-30,15]}
  ],
  "geometries":[
    {"id":"torso","name":"Torso","count":1,"extents_mm":[86,45.5,95],"wall_min_mm":1.1},
    {"id":"nose","name":"Nose and front wing","count":1,"extents_mm":[84,19.75,108.25],"wall_min_mm":0.95},
    {"id":"head","name":"Head","count":1,"extents_mm":[19,19.5,59.25],"wall_min_mm":1.9},
    {"id":"arm-shell","name":"Arm shell","count":2,"extents_mm":[26,22,72.5],"wall_min_mm":2.0},
    {"id":"forearm","name":"Fist","count":2,"extents_mm":[20,16.5,44.75],"wall_min_mm":2.5},
    {"id":"thigh","name":"Thigh sleeve","count":2,"extents_mm":[18,19,41],"wall_min_mm":1.4},
    {"id":"shin","name":"Shin and slide post","count":2,"extents_mm":[31.75,23.75,106],"wall_min_mm":1.4},
    {"id":"boot","name":"Boot","count":2,"extents_mm":[32,64.5,31.5],"wall_min_mm":1.1},
    {"id":"wing","name":"Rear-wing half","count":2,"extents_mm":[39.25,43,12],"wall_min_mm":0.95},
    {"id":"front-wheel","name":"Front wheel","count":2,"extents_mm":[39,39,16],"wall_min_mm":2.0},
    {"id":"rear-wheel","name":"Rear wheel","count":2,"extents_mm":[41,41,12],"wall_min_mm":2.0}
  ],
  "requirements":[
    {"id":"R01","scope":"assembly","text":"In the Display Pose the robot stands upright on both boots, its helmet top at Z 250, arms hanging straight 2 out from the torso, every part dressed in layered, faceted armour plates with bevelled corners, not blocks: the cockpit opening ringed by the closed red halo sits in the middle of the broad black chest from Z 170 to 216.25, a shoulder tower juts over each arm with a front wheel on its outer face at Z 228.25, a rear wheel on the outer side of each calf at Z 76, a red knee guard runs up from each shin over the foot of its thigh from Z 88.75 to 116, and each wedge boot carries a folded wing half lying on its toe slope, whose red blade leans forward in front of the shin."},
    {"id":"R02","scope":"assembly","text":"From behind, the nose lies down the middle of the robot's back from its hinge at Z 232, its front wing 84 wide across the back of the thighs from Z 128 to 145, and nothing else rises behind the head."},
    {"id":"R03","scope":"assembly","text":"In the car pose the toy is an open-wheel Formula car 360.75 mm long, 126 wide and 54.5 tall to the rear wing, lying on the robot's back: nose cone and front wing ahead of the front wheels, the cockpit and halo on top, the arm shells as front sidepods, the legs side by side as the rear body, the boots as the tail, and the two wing halves standing on the boots as the rear wing, their blades meeting at the centre line."},
    {"id":"R04","scope":"assembly","text":"The robot becomes the car by seven moves and no part comes off: the head slides 26.5 down into its pocket, the nose flips 180 degrees up over the top of the back, each fist folds 180 degrees into its arm shell, each boot folds 90 degrees at the ankle, each shin slides 19.25 up into its thigh, each wing half stands up 60 degrees on its hinge, and the car is laid on its back."},
    {"id":"R05","scope":"assembly","text":"In the car pose the car rests on all four wheels, the nose knuckle and the torso's hinge cheeks 1.75 mm and every other part at least 3.75 mm above the ground, and each wheel turns freely on its dowel."},
    {"id":"R06","scope":"assembly","text":"Posing ranges in the robot: shoulders 90 degrees forward and 5 back, hips 20 forward and 20 back, each holding its pose by friction; the knees do not bend, the legs slide."},
    {"id":"R07","scope":"assembly","text":"Every moving part keeps at least 0.5 mm from every other part through each transformation move and posing range and in both poses, except at the contacts the Interfaces declare: the head-slide dowel stopping in the neck post's slot, the lowered helmet on the pocket floor, and the knee-slide dowel stopping at its slot ends. Checked with --check-motion true: one sweep per transformation move in at most 10 steps against only the parts it can reach; a skipped, killed or timed-out sweep fails this requirement."},
    {"id":"R08","scope":"assembly","text":"Every purchased-part seat is derived from a catalog STEP file, or from the documented envelope when the catalog search is a recorded miss, and the bill of materials lists exactly 2 dowels 3 x 18, 5 dowels 3 x 20, 5 dowels 3 x 26, 4 dowels 3 x 30, 2 dowels 3 x 32 and 4 push-on caps for 3 mm shafts."},
    {"id":"R09","scope":"assembly","text":"Every joint is built as its Interface text states, each hinge or slide a purchased dowel pressed into a 2.9 mm bore on one side and turning or sliding in a 3.1 mm bore or slot (3.2 for the wheels) on the other, with no glue; each knee-slide slot narrows to 2.8 for 1 mm inside each end so the dowel clicks into the end and holds."},
    {"id":"R10","scope":"assembly","text":"The robot stands unsupported in the Display Pose: its centre of mass lies over the boots, which span Y -50.75 at the toes to 13.75 at the heels; each foot points forward, its toe 38.25 ahead of the shin's front, and sits outboard of its shin, the boots 16 apart."},
    {"id":"R11","scope":"geometry:torso","text":"A 70 x 31.5 black core in layered, faceted armour plates, its front, sides and back broken by panel lines, its chest corners bevelled 2 to 4, vents at a 2.2 slit pitch; two shoulder towers jutting 8 out from its top corners on 52 degree wedge undersides, and between them an open head pocket whose front wall has a 13 wide notch so the neck shows."},
    {"id":"R12","scope":"geometry:torso","text":"On the front a cockpit opening 20 wide, 31.75 tall and 4.25 deep ringed by a closed red halo 30 wide and 46.25 tall standing 8.5 proud, of two 4 wide legs and two 6 thick bars with faceted corner blocks; a 14.5 mm shoulder boss on each side wall; two 8.5 mm nose hinge cheeks at the top of the back."},
    {"id":"R13","scope":"geometry:nose","text":"A red nose cone with a raised centre ridge and angled white livery down each side, faceted into armour plates by panel lines, 18 wide at its root stepping to 12, its root on a hinge knuckle 20 wide; it lies down the robot's back."},
    {"id":"R14","scope":"geometry:nose","text":"At the tip a black front wing 84 wide and 17 tall, a main plane under a flap slat with a 2 x 1.2 slot by each end, and a stepped red endplate 3 wide at each end rising 3.5 above it; the red cone runs on over the wing's outer face to its lower edge, narrowing to 6."},
    {"id":"R15","scope":"geometry:head","text":"A white and red helmet 19 wide and 23 tall with a blue visor band across its front, faceted cheek guards and a raised crest 4 wide along its top centre line, bevelled at 52 degrees, on a neck post 8 wide, 9.75 deep and 36.25 long with a 3.4 wide slot through it from front to back."},
    {"id":"R16","scope":"geometry:arm-shell","text":"A 26 x 22 white arm 72.5 tall, a channel open at the back and the bottom, its top rounded about the shoulder axis, its outer edges bevelled 2 to 4, a panel line splitting upper from lower arm, a red band 11.5 tall round the upper arm with a red tab under it, vents at a 2.2 slit pitch; its front, the bed face, is plated by engraved lines only."},
    {"id":"R17","scope":"geometry:forearm","text":"A black closed fist 20 wide and 16.5 deep, ending at the top in a rounded wrist knuckle as wide as the fist, a wrist guard with a raised V plate, then a curled hand standing proud of the guard: four separate fingers split by grooves 0.8 wide and 3 deep, each in three segments curling under the fist, and a thumb on its inboard front corner, the corner cut away under it."},
    {"id":"R18","scope":"geometry:thigh","text":"An 18 x 19 red sleeve 27.25 tall, open at the bottom, whose top steps in as a low gable and rises into a rounded hip tongue 10 wide toward its inboard side, with a 3.2 wide slot along each side wall for 19.25 mm of slide; its front plate bevelled 2 to 4 at its corners and carrying two white chevron panels, its front and outer side layered armour plates with vents at a 2.2 slit pitch."},
    {"id":"R19","scope":"geometry:shin","text":"A red shin: a cuff 27.5 wide and 22.25 tall under a block 18 wide and 34.5 tall, flush with the thigh's sides, a white zig-zag stripe down the front of both, a black slide post 12 x 13 rising 27.25 above with a red knee guard 18 wide and 1.75 thick in front of it up to the post's top, the block's top sloping down at 52 degrees beside and behind the post, a wheel boss on the outer face and a rounded ankle tongue 14 wide below; layered armour plates with vents at a 2.2 slit pitch, bevelled 2 to 4 where it tapers toward the ankle; the knee guard is plain, too thin for panel lines."},
    {"id":"R20","scope":"geometry:boot","text":"A black wedge boot 32 wide and 64.5 long pointing forward, 31.5 tall behind the toe slope, which falls forward at 30 degrees to a toe face 12 tall, its heel top rounded about the ankle, a slot for the shin's tongue open at the top and the heel, and two hinge lugs at the very toe; a toe plate on its toe bevelled 2 to 4, a sole band with tread notches, its sides layered armour plates with bevelled edges and vents at a 2.2 slit pitch."},
    {"id":"R21","scope":"geometry:wing","text":"A black plate 24 wide, 3.5 thick and 38.75 long from the axis of an 8.5 mm hinge knuckle, carrying at its far end a red blade 39.25 wide, 12 tall and 3.5 thick standing square to the plate and overhanging it by 11.25 inboard and 4 outboard, its outer 3 a black endplate cap with a 1 x 2.5 slot, a white gurney lip along its top."},
    {"id":"R22","scope":"geometry:front-wheel","text":"A black tyre 39 across and 16 wide with a chevron-grooved tread and a five-spoke rim face on its outer side, the windows between the spokes open through."},
    {"id":"R23","scope":"geometry:rear-wheel","text":"A black tyre 41 across and 12 wide, its plain tread split into segments by panel lines, and a five-spoke rim face on its outer side, the windows between the spokes open through."}
  ],
  "interfaces":[
    {"id":"nose-fold","kind":"coupled","components":["nose","head","torso"],"text":"A 3 x 26 dowel pressed 2.5 into each of the torso's two Ø8.5 back cheeks (X 10.5 to 14.5 each side, axis Y 17, Z 232) turns the nose's 20 wide knuckle (X -10 to 10; round R4.25) on a 3.1 bore; the torso's seat round the knuckle is a cylinder R4.75 over X -10.5 to 10.5. Robot pose: the nose lies down the back, its inner face 0.5 behind the torso's back (Y 15.75) and its front wing behind the thighs. Car pose: flipped 180 degrees up over the top, the nose stands above the torso over the head pocket; the head is lowered first and the nose clears it by 6.","yielding":"nose","poses":{"steps":10,"movers":[{"component":"nose","rotation":{"axis_point":[0,17,232],"axis_direction":[1,0,0],"start_deg":0,"end_deg":180}},{"component":"head","translation":{"vector":[0,0,-26.5]}}]}},
    {"id":"head-slide","kind":"coupled","components":["head","torso"],"text":"The head's 8 x 9.75 neck post (Y 0.5 to 10.25, its back face flush with the helmet's back at Y 10.25) slides in the torso's 9 x 10.75 neck bore below the head pocket (X -4.5 to 4.5, Y 0 to 10.75, floor Z 163.75). A 3 x 20 dowel pressed along Y at X 0, Z 195.75 from the torso's back face (Y 15.75) to Y -4.25 runs through the post's 3.4 wide front-to-back slot and stops it at both ends: raised, the helmet's underside is at Z 227 and the neck shows through the pocket's 13 wide front notch (down to Z 217.5); lowered by 26.5, the helmet rests on the pocket floor at Z 200.5, 6 below the torso's top.","yielding":"head","poses":{"steps":10,"movers":[{"component":"head","translation":{"vector":[0,0,-26.5]}}]}},
    {"id":"shoulder-1","kind":"coupled","components":["arm-shell#1","forearm#1","torso","front-wheel#1"],"text":"A 3 x 20 dowel pressed 12 along X into arm shell 1's top block at Y -2.5, Z 193.25 turns in a 3.1 bore through the torso's Ø14.5 shoulder boss (X 35 to 36.5), its +X side wall and a Ø10 boss inside the wall, X 28.5 to 36.5 in all. The shell's inboard face is 0.5 from the boss; its top, rounded R11 about the axis, stays 6.5 under the tower's wedge and 5 clear of front wheel 1 at every angle from 90 degrees forward to 5 back.","yielding":"arm-shell#1","poses":{"steps":10,"movers":[{"component":"arm-shell#1","rotation":{"axis_point":[0,-2.5,193.25],"axis_direction":[1,0,0],"start_deg":5,"end_deg":-90}},{"component":"forearm#1","rotation":{"axis_point":[0,-2.5,193.25],"axis_direction":[1,0,0],"start_deg":5,"end_deg":-90}}]}},
    {"id":"shoulder-2","kind":"coupled","components":["arm-shell#2","forearm#2","torso","front-wheel#2"],"text":"Mirror of shoulder-1: a 3 x 20 dowel pressed into arm shell 2's top block at Y -2.5, Z 193.25 turns in the torso's -X boss and side wall, with shoulder-1's clearances to the boss, the tower and front wheel 2.","yielding":"arm-shell#2","poses":{"steps":10,"movers":[{"component":"arm-shell#2","rotation":{"axis_point":[0,-2.5,193.25],"axis_direction":[1,0,0],"start_deg":5,"end_deg":-90}},{"component":"forearm#2","rotation":{"axis_point":[0,-2.5,193.25],"axis_direction":[1,0,0],"start_deg":5,"end_deg":-90}}]}},
    {"id":"elbow-1","kind":"coupled","components":["forearm#1","arm-shell#1"],"text":"A 3 x 26 dowel pressed into arm shell 1's two elbow cheeks (X 37 to 39.5 and 60.5 to 63) along X at Y -2.5, Z 140 turns fist 1's R7.5 wrist knuckle on a 3.1 bore. The fist folds 180 degrees up and back into the shell's cavity (X 39.5 to 60.5, Y -10.5 to 8.5, Z 131.75 to 183.5), entering through its open back. 0.5 clearance throughout.","yielding":"forearm#1","poses":{"steps":10,"movers":[{"component":"forearm#1","rotation":{"axis_point":[48,-2.5,140],"axis_direction":[1,0,0],"start_deg":0,"end_deg":180}}]}},
    {"id":"elbow-2","kind":"coupled","components":["forearm#2","arm-shell#2"],"text":"Mirror of elbow-1: a 3 x 26 dowel in arm shell 2's elbow cheeks along X at Y -2.5, Z 140 turns fist 2's knuckle on a 3.1 bore; the fist folds into the cavity as in elbow-1.","yielding":"forearm#2","poses":{"steps":10,"movers":[{"component":"forearm#2","rotation":{"axis_point":[-48,-2.5,140],"axis_direction":[1,0,0],"start_deg":0,"end_deg":180}}]}},
    {"id":"hip-1","kind":"coupled","components":["thigh#1","shin#1","boot#1","wing#1","rear-wheel#1","torso","nose"],"text":"Thigh 1's tongue (X 9 to 19, Y -7 to 2, rounded R4.5 about the hip axis so it stays 0.5 under the slot's pointed-arch roof) sits in the torso's hip slot (X 8.5 to 19.5, Y -11 to 6, up to Z 152.25); a 3 x 20 dowel pressed along X through the slot walls at Y -2.5, Z 145 turns it on a 3.1 bore. The thigh's gabled top stays 2.5 below the torso in the robot and 0.5 clear of it, and the leg 0.5 clear of the nose's front wing, from 20 degrees forward to 20 back.","yielding":"thigh#1","poses":{"steps":10,"movers":[{"component":"thigh#1","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}},{"component":"shin#1","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}},{"component":"boot#1","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}},{"component":"wing#1","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}},{"component":"rear-wheel#1","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}}]}},
    {"id":"hip-2","kind":"coupled","components":["thigh#2","shin#2","boot#2","wing#2","rear-wheel#2","torso","nose"],"text":"Mirror of hip-1: thigh 2's tongue in the torso's -X hip slot on a 3 x 20 dowel along X at Y -2.5, Z 145, turning on a 3.1 bore, with hip-1's clearances.","yielding":"thigh#2","poses":{"steps":10,"movers":[{"component":"thigh#2","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}},{"component":"shin#2","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}},{"component":"boot#2","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}},{"component":"wing#2","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}},{"component":"rear-wheel#2","rotation":{"axis_point":[0,-2.5,145],"axis_direction":[1,0,0],"start_deg":-20,"end_deg":20}}]}},
    {"id":"knee-slide-1","kind":"coupled","components":["shin#1","boot#1","wing#1","rear-wheel#1","thigh#1","torso"],"text":"Shin 1's slide post (X 10.5 to 22.5, Y -9 to 4) runs in thigh 1's sleeve (cavity X 10 to 23, Y -9.5 to 4.5, ceiling Z 135.75), 0.5 clear all round, the post's top edges and the ceiling's edges bevelled alike, 1.5 at 52 degrees, the knee guard sliding 0.5 in front of the thigh's front face. A 3 x 18 dowel pressed along X through the post at Y -2.5 runs in the 3.2 wide slots of the thigh's two side walls from Z 112.25 (robot, full length) to Z 131.5 (car, 19.25 up), each slot narrowed to 2.8 for 1 inside each end so the dowel clicks into the end. At 19.25 up the post's top is 0.5 under the ceiling, the guard's top at Z 135.25, and the shin block's flat top in front of the post 0.5 under the thigh's bottom.","yielding":"shin#1","poses":{"steps":10,"movers":[{"component":"shin#1","translation":{"vector":[0,0,19.25]}},{"component":"boot#1","translation":{"vector":[0,0,19.25]}},{"component":"wing#1","translation":{"vector":[0,0,19.25]}},{"component":"rear-wheel#1","translation":{"vector":[0,0,19.25]}}]}},
    {"id":"knee-slide-2","kind":"coupled","components":["shin#2","boot#2","wing#2","rear-wheel#2","thigh#2","torso"],"text":"Mirror of knee-slide-1: shin 2's post slides 19.25 up into thigh 2's sleeve on a 3 x 18 dowel along X at Y -2.5, in slots from Z 112.25 to 131.5, as in knee-slide-1.","yielding":"shin#2","poses":{"steps":10,"movers":[{"component":"shin#2","translation":{"vector":[0,0,19.25]}},{"component":"boot#2","translation":{"vector":[0,0,19.25]}},{"component":"wing#2","translation":{"vector":[0,0,19.25]}},{"component":"rear-wheel#2","translation":{"vector":[0,0,19.25]}}]}},
    {"id":"ankle-1","kind":"coupled","components":["boot#1","wing#1","shin#1"],"text":"Shin 1's ankle tongue (X 14 to 28, Y -0.25 to 9.25, round R4.75 about the axis) sits in boot 1's slot (X 13.5 to 28.5, Y -0.75 to the heel, down to Z 9.5); a 3 x 30 dowel pressed along X through the slot's side walls at Y 4.5, Z 14.75 turns it on a 3.1 bore. The boot folds 90 degrees, toe down: its heel top, rounded R16.75 about the axis, and its heel face at Y 13.75 pass and end at least 0.5 under the shin's bottom face (Z 32), and its sole ends 3.75 above the car's ground.","yielding":"boot#1","poses":{"steps":10,"movers":[{"component":"boot#1","rotation":{"axis_point":[0,4.5,14.75],"axis_direction":[1,0,0],"start_deg":0,"end_deg":90}},{"component":"wing#1","rotation":{"axis_point":[0,4.5,14.75],"axis_direction":[1,0,0],"start_deg":0,"end_deg":90}}]}},
    {"id":"ankle-2","kind":"coupled","components":["boot#2","wing#2","shin#2"],"text":"Mirror of ankle-1: shin 2's R4.75 tongue in boot 2's slot on a 3 x 30 dowel along X at Y 4.5, Z 14.75, turning on a 3.1 bore; the boot folds as in ankle-1.","yielding":"boot#2","poses":{"steps":10,"movers":[{"component":"boot#2","rotation":{"axis_point":[0,4.5,14.75],"axis_direction":[1,0,0],"start_deg":0,"end_deg":90}},{"component":"wing#2","rotation":{"axis_point":[0,4.5,14.75],"axis_direction":[1,0,0],"start_deg":0,"end_deg":90}}]}},
    {"id":"wing-hinge-1","kind":"coupled","components":["wing#1","boot#1","shin#1"],"text":"Wing 1's Ø8.5 knuckle (X 12 to 36) sits between boot 1's two toe lugs (X 8 to 11.5 and 36.5 to 40), 0.5 clear; a 3 x 32 dowel pressed along X into the lugs at Y -46.5, Z 12 turns it on a 3.1 bore. Folded, the plate lies 0.5 above the toe slope at 30 degrees and the blade's back face passes 0.5 clear of the shin cuff's front bottom edge (Y -12.5, Z 32). Standing (+60), square to the boot's top, the plate rises from the toe and the blade points away from the shin; in the car the blades of the two halves meet 1.5 apart at the centre line.","yielding":"wing#1","poses":{"steps":10,"movers":[{"component":"wing#1","rotation":{"axis_point":[0,-46.5,12],"axis_direction":[1,0,0],"start_deg":0,"end_deg":60}}]}},
    {"id":"wing-hinge-2","kind":"coupled","components":["wing#2","boot#2","shin#2"],"text":"Mirror of wing-hinge-1: wing 2's knuckle between boot 2's toe lugs on a 3 x 32 dowel along X at Y -46.5, Z 12, turning on a 3.1 bore.","yielding":"wing#2","poses":{"steps":10,"movers":[{"component":"wing#2","rotation":{"axis_point":[0,-46.5,12],"axis_direction":[1,0,0],"start_deg":0,"end_deg":60}}]}},
    {"id":"front-wheels","kind":"static","components":["front-wheel#1","front-wheel#2","torso"],"text":"Each front wheel turns on a 3 x 30 dowel pressed 12 deep into the outer face of a shoulder tower on the axis Y 3.5, Z 228.25, the wheel's inner face 0.5 outside the tower (X 43.5 to 59.5 and -43.5 to -59.5), held by a push-on cap."},
    {"id":"rear-wheels","kind":"static","components":["rear-wheel#1","rear-wheel#2","shin#1","shin#2"],"text":"Each rear wheel turns on a 3 x 26 dowel pressed 12 deep into its shin's Ø9.5 boss and block on the axis Y 2.5, Z 76, the wheel's inner face 0.5 outside the boss (X 35 to 47 and -35 to -47), held by a push-on cap."}
  ]
}
```
