# Racer Mecha v2 - redesigned transformation (2026-10-13)

Owner decisions (grilling, 2026-10-13): legs become the car's rear body (A), arms are the sidepods with
the front wheels on the shoulders (A), the chest is the cockpit with its halo (A), the head hides under
the nose root (A, not the driver's helmet), 8-10 moves for ages 10+ (A), the rear wing folds onto the
boots (A), no backpack (A), the legs slide longer in the robot (A). Concept images:
`prototypes/v2-colour-steps.png`, `prototypes/v2-rear-wing-fold.png`, `prototypes/v2-robot-bulk.png`.

Numbers come from `model.py` (all sweeps >= 0.5; `checks.txt`). Changes from the step images the owner saw,
each forced by geometry, to report with the new reference images:

- Rear wing: one hinge per half, not two. A Ø3 dowel hinge needs a Ø7 knuckle, which does not fit on a
  3 mm plate's far edge; the blade is instead fixed square to the plate. In the robot the blade stands
  10 tall in front of the shin; in the car it points rearward from the top of the plate.
- An end plate that is thin across the car cannot fold flat with any single hinge; the wing half is a
  plate running fore-aft only in the car (endplate and pylon in one), lying flat on the instep in the robot.
- The legs do not split apart: they already stand 1 apart. The knees no longer bend: the shin slides 16
  into the thigh on a dowel in two slots that click at each end.
- The nose's front wing lies behind the hips (the nose hinges at the top of the back, so its far end, the
  wing, is low); the step image that drew it across the shoulders was wrong. It limits the shoulders to
  5 degrees back.
- Feet: 41.5 long, toe 17 ahead of the shin, so the folded wing has an instep to lie on.
- Car: 276.5 long, 101 wide, 39 tall; nose 1.5 above the ground.

Geometries: spine removed; boot and wing added; thigh and shin redrawn; torso (cockpit and halo on the
front, nose hinge at the back) and nose redrawn. Head, arm shell, forearm and wheels unchanged.
Images to make (design-a-toy Stage 3): ref-01 assembly, ref-02 torso, ref-03 nose (from behind), ref-07
thigh, ref-08 shin, ref-09 boot, ref-10 wing; renumber the two wheel images. Car-pose images wait for the
Workshop posed-reference feature.

## v2b - chunky proportions (owner chose B, 2026-10-13)

The owner chose the chunky look (prototypes/v2-proportion-choice.png, B) over
the v2a contract proportions. Measured from the approved chunky concept
(gen10/c1, front view, scaled to 207): torso 125 to 194, thighs 100 to 121,
shins 31 to 100, boots 0 to 31. Re-laid out, height kept at 207:

| Landmark | v2a | v2b |
|---|---|---|
| boot top | 20 | 26 |
| shin block | 20.5-53.5 | 26.5-69.5 |
| slide post / knee guard | 53.5-77 / to 70 | 69.5-93 / to 86 |
| thigh | 70-96.5 | 86-112.5 |
| hip pin | 102 | 118 |
| torso bottom | 99 | 115 |
| cockpit / halo | 128-157 / 126-160 | 126-152.5 / 124-155.5 |
| head neck post / retainer | 143-178 / 149.5 | 148-178 / 152 |
| wing hinge A | Z 23.5 | Z 29.5 |

Forced by the move:
- The hip slots would have met the neck bore (head lowered to Z 121): the
  neck post is shortened to 30 and the retainer raised to Z 152, bore floor
  125.5, 1.5 over the hip slots.
- The cockpit must keep 1.5 over the hip slots and under the head pocket, so
  it is 26.5 tall (was 29) and the halo follows it.
- The front wing now sits behind the thighs: it moves to the nose's back face
  (Y 21 to 27), endplates run the full depth (Y 13.5 to 27), a 4 deep cone
  tip (Y 17 to 21) runs on to Z 102 into the wing, and hip back swing is 15
  (at 20 the thigh meets the cone's bottom).
- Boots are 6 taller in front only; the ankle stays at (3.75, 12.25) so the
  folded boot still sits 3 above the car's ground. Hinge A rises 6, so the
  car's rear wing stands 6 higher: car height 45 (was 39). Length 276.5 kept.

## v2c - contract follows the approved-style assembly image (Stage 3b)

Five image rounds from the chunky concept (gen11 a-e: c1 -> a1 -> b1 -> d1
-> e1). The image model would not put the torso bottom at 115: rounds landed
it at 124, 92-104 and 106. e1 is the best image (legs wide, chunky, halo
round the cockpit), with the torso's bottom at 106 and the halo at 129-157.
The image is the better object and v2b's 115 cannot be drawn, so the
contract follows it: torso bottom 106, hip 109, thigh 77-103.5, slide post
60.5-84 with the knee guard to 77, shin block 26.5-60.5 (34), slide slots
80-96, cockpit 131-152.5 inside a halo 129-155.5. Boots (26), head, nose,
wing and the car are unchanged. The lower hip gives the thigh room again, so
the hips swing 20 back. Model rerun: every check passes (checks.txt).

ref-01 = gen11/e1 keyed and narrowed x0.949 to the 101 x 207 envelope.
Measured at contract scale: boots 0-23/27 (26), legs to 106 (thigh top
103.5, torso 106), halo 129-157 (129-155.5), helmet 178-198 (178-197), each
leg 29 wide at the thigh (30), arms 99-174 with the fist 99-120.
Residuals left: the shoulder wheels are drawn 32 across (contract 38) and
the arm shells reach 174 (163); the rear wheels are drawn 42-68 (33-67).

Halo: ref-01 draws it as a U (two legs and a bottom bar, open at the top),
and the torso image is drawn to match. The contract's inverted U (top bar)
changes to the U; the cockpit opening starts 0.5 above the bar (132.5).

## Stage 3b - v2 references (gen12), measured at contract scale

| Image | Rounds | X scale | Check | Contract | Image | Verdict |
|---|---|---|---|---|---|---|
| ref-01 assembly | 5 | 0.949 | see v2c above | | | residuals listed above |
| ref-02 torso [-90,0] | 3 | 1.172 | core top / notch / halo / halo legs X | 74 / 64 / 23-49.5 / ±11 | 73 / 64.6 / 21-51 / ±9.5 | halo 2 low and 1.5 tall: residual |
| ref-03 nose [90,0] | 5 | 0.844 | wing / lower cone / step / upper cone | 13 tall, 84 / 12 / Z 35 / 18 | 10, 84 / 12.9 / Z 35 / 21.5 | step amended 140 -> 131 (image); wing 3 short and upper cone 3.5 wide: residual |
| ref-04 head [-90,0] | 1 | 1.016 | helmet / post | 19 / 30 | 18 / 31 | agree |
| ref-07 thigh [-90,0] | 3 | 0.834 | body / tongue | 26.5 tall / 10 wide, left | 25.8 / left | agree |
| ref-08 shin [-90,0] | 4 | 0.991 | tongue / stripe / guard / post | 17 wide, 0-18.25 / centre / 30 / 24 | 14.5, 0-16 / centre / 29.3 / 25.2 | tongue 2.5 narrow: residual |
| ref-09 boot [0,0] | 4 | 0.983 | body top / lug / heel / ankle hole | 26 / 33 / arc to 12.25 / at the arc centre | 24.5 / 32.8 / arc / at the arc centre | body 1.5 low: residual |
| ref-10 wing [-45,30] | 4 | 1.0 | blade wider than plate, knuckle near, blade far | 33.75 vs 24 | blade overhangs both sides | agree |

ref-05 arm shell, ref-06 forearm, ref-11 and ref-12 wheels are unchanged
v01 parts. The halo is a U in ref-01 and ref-02, and the contract follows.

## v3 - contract follows the livery robot (owner chose 1, 2026-10-13)

The owner found the gen12 reference set much uglier than the step sheet. The
cause: flat orthographic renders on a pixel grid, and an assembly forced to
the contract's narrow numbers. The approved step-sheet robot (v2-steps/rA)
recoloured into the livery (prototypes/v2-livery-restyle.png, option 1) is
the new ref-01: gen13/l1 -> green background (g1) -> shoulder fins removed
(nf1), keyed, x0.97 to 124 x 207, camera [-90, 15] (front, chest top
visible). The contract is re-laid out from its measurements at height 207:

| Landmark | image | v3 contract |
|---|---|---|
| boots | 0-30 (top face seen), X 11-44 | 0-26, X 11-43 |
| shin | cuff 30-45 X 3-37; block X 3.6-31.7 | cuff 26.5-45 X 3-34.5; block 45-73.5 X 3.5-31.5 |
| rear wheel | Z 45-81, X 35-47 | Ø34 at Z 63, X 35-47 |
| thigh | 94-117, X 5.5-28 | 90-115, X 5.5-28 |
| torso | 117-190, ±28.5 | 117-190, ±28.5 |
| halo | closed loop ±15, 132-180 | closed loop ±15, 132-179 |
| cockpit | ±10, 138-173 | ±10, 138-173, 3.5 deep |
| helmet | 186-207, 18 wide | 188-207, 19 wide |
| arm | X 34-62.5, 85-171, fist 85-109 | X 34-62, 85-171, fist 85-109 |
| shoulder towers | blocks X 28.5-44, 174-194 | X 28.5-43 to 195, 52 degree wedge under |
| front wheel | X 44-60, Z 171-202 | Ø32 x 16, X 43.5-59.5, axis Z 189 |

Mechanism changes forced by the new layout: the arm shell is the whole white
arm and the fist alone folds into it (elbow at Z 116, 3 x 28 elbow dowel);
the shoulder pivots at Z 160 on a torso boss, the arm's top rounded R11 about
it so it clears the tower and the wheel at every angle; the front axle moves
to Y 3 so the smaller front wheels still touch the ground; the cockpit is 3.5
deep to keep 1.5 to the head pocket; the knee slide uses a 3 x 22 dowel with
the post 16.5 wide; the boots sit outboard of the shins and the wing blades
reach inboard to the centre line. No crotch block: it could not print. The
nose keeps its length, 10 higher. Model: every check passes (checks.txt);
car 286.5 long, 124 wide, 45 tall.

Residuals in ref-01: no red blades are drawn on the toes, and the boots read
4 taller because their top faces show. Every part reference from gen12 is
now stale (style and size) and is redrawn next in the ref-01 style.

## v3 part references (design-a-toy Stage 3/3b)

All eleven part images redrawn in ref-01's style: each generated from the
livery robot image (gen13 nf1) as "one part taken off this toy", then edited
for proportions, keyed off chroma green, stray green zeroed, X-only stretch.
Prompts: `prompts/v3-part-*.txt` (a = first draw, b..e = edit rounds). Sheet:
`prototypes/v3-reference-set.png`. Visible height at EL 15 = Z cos15 + depth sin15.

| Image | Rounds | Camera | X stretch | Check | Contract | Image | Verdict |
|---|---|---|---|---|---|---|---|
| ref-02 torso | 5 | [-90, 15] | 1.00 | aspect | 1.006 | 1.005 | ok |
| | | | | towers across / body | 86 / 57 | 86 / 60.2 | body +3.2 (5.6%) residual |
| | | | | halo w x h | 30 x 47 | 29.8 x 46.4 | ok |
| | | | | halo bottom (visible) | 14.5 | 10.4 | 4 low, residual |
| ref-03 nose | 5 | [90, 15] | 1.018 | width | 84 | 84 | ok |
| | | | | cone upper / lower | 18 / 12 | 18.6 / 18.6 | no step drawn, residual (contract keeps the 12 step: hip-back clearance) |
| | | | | wing height | 14 (visible) | 11 | 3 thin, residual |
| ref-04 head | 3 | [-90, 0] | 1.20 | helmet w / h | 19 / 19 | 19 / 18.6 | ok |
| | | | | post w / length | 8 / 30 | 7.7 / 30.4 | ok |
| ref-05 arm | 4 | [-90, 15] | 1.18 | width | 28 | 28 | ok |
| | | | | red band Z (visible) | 31.9-42.5 | 32.0-42.4 | ok |
| ref-06 fist | 1 | [-90, 15] | 1.20 | width | 22 | 21.8 | ok |
| ref-07 thigh | 2 | [-90, 15] | 0.92 | width / tongue | 22.5 / 10 | 22.5 / 9.4 | ok (0.6) |
| | | | | sleeve top / tongue top | 27.4 / 38.2 | 28.4 / 38.1 | ok |
| ref-08 shin | 5 | [-90, 15] | 0.94 | cuff | 31.5 | 31.0 | ok |
| | | | | block / knee guard | 28 / 22.5 | 25.3 / 24.6 | -2.7 / +2.1, residual |
| | | | | post | 16.5 | 14.8 | -1.7, residual |
| | | | | guard top / tongue length | 78.5 / 17.6 | 78 / 14 | tongue 3.6 short, residual |
| ref-09 boot | 5 | [0, 0] | 1.00 | length / lug top / body | 41.5 / 33 / 26 | 40.5 / 32.8 / 25.2 | ok |
| ref-10 wing | 3 | [-90, 30] | 1.145 | aspect (projected) | 2.74 | 2.74 | ok; blade overhangs inboard (left) far, outboard a little |
| ref-11 front wheel | 1 | [0, 15] | 1.00 | diameter | 32 | 32.2 | ok |
| ref-12 rear wheel | 1 | [0, 0] | 1.00 | diameter | 34 | 33.6 | ok |

Residuals at the 5-round cap (contract kept, each becomes a Reference
Conflict if the reviewer reads it): torso body 3 wide and halo 4 low; nose
cone drawn 18 wide all the way (contract steps to 12 below Z 141) and wing
3 thin; shin block 2.7 narrow, post 1.7 narrow, ankle tongue 3.6 short.

### ref-02 torso redrawn (owner: chest looked short beside ref-01)

Rounds f, g (owner-requested beyond the cap): f generated from a crop of the
chest in gen13 nf1 (ref-01's source), g shrank the halo and widened the
towers; X stretch 0.95. Measured at contract scale: towers across 86, body
58.2 (57), halo 34 x 46.4 (30 x 47), halo Z 13.6 to 60 visible (14.5 to 60).
Residual: halo 4 wider. Earlier ref-02 (rounds a to e) read squat because its
towers stood tall above the body.

## Reference cameras re-estimated (2026-10-14)

The owner saw cameras that did not match their images. Re-read by eye in the
Display Pose frame, rounded to 15 degrees:

| Image | Was | Now | Cue |
|---|---|---|---|
| ref-03 nose | [90, 15] | [90, 0] | flat back view, no top face of the wing or knuckle shows |
| ref-05 arm shell | [-90, 15] | [-75, 15] | the +X outer face shows right of the front face (22 deep x tan 15 against 28 wide); top faces show |
| ref-06 fist | [-90, 15] | [-90, 0] | front face only, no top face on the knuckle block |
| ref-07 thigh | [-90, 15] | [-75, 15] | the +X side face shows right of the front face; top faces show |
| ref-08 shin | [-90, 15] | [-90, 0] | front face only; the +X wheel boss is seen edge-on on the right |
| ref-10 wing | [-90, 30] | [-105, 30] | the blade's -X end face shows and its +X end sits higher (slope 0.17 = tan 19 x sin 30) |
| ref-11 front wheel | [0, 15] | [-15, 15] | tread shows on the left (front) edge, about 3 of 16 |
| ref-12 rear wheel | [0, 0] | [-30, 15] | tread shows on the left, 5.4 of 12, and on top, 3 of 12 |

Kept: ref-01, ref-02 [-90, 15]; ref-04 [-90, 0]; ref-09 boot [0, 0] (its
blocks show no top face; only the two toe lugs are drawn offset as if from
15 up).

The fist image draws three fingers in two rows, the contract said four
fingers and two knuckle grooves; the contract now says three fingers split
by two vertical grooves, crossed by one knuckle groove (prose and R17).

## v3 colour-coded transformation sheet

`prototypes/v3-colour-steps.png`, panels in `prototypes/v3-steps/`, prompts
`prompts/v3-st-*.txt`. Generated from ref-01 recoloured (torso grey, nose
yellow, head white/blue, arm shells green, fists dark grey, thighs red,
shins orange, boots dark grey, wing halves purple, front rims blue, rear
rims white), then one edit per Transformation move in reverse. The sheet
reads car to robot, steps 1 to 7 being the contract's moves 7 to 1. The
standing nose was shortened to 0.72 of its drawn height (r2c) to keep it
about 1.2 times the chest. Known looseness: step 1's boots are drawn
shorter than step 3's, the car's sidepods are not quite symmetric.

## Guide Image in the contract (2026-10-14, issue #122)

The owner wants the colour-coded transformation sheet in the run (ADR 0089,
branch `issues/122-guide-images`, not merged yet). The contract is now
schema 5 with `guides[]`: `guide-01-transformation.png` (a copy of
`prototypes/v3-colour-steps.png`, 1600 x 1332), its seven steps in the
sheet's order, car to robot. To stay under 40,000 characters two Motion and
fit bullets that repeated R07 and R05 word for word now point to those rows.
A run needs the merged Workshop and `--guide toys-spec/racer-mecha/guide-01-transformation.png`.

## Leg strip redrawn (2026-10-14)

The owner flagged the side-view leg strip. Its push-up panels shortened the
red thigh instead of the orange shin (the shin slides into the thigh, so the
thigh never changes), and the boot was a thin plate instead of the 26 tall
block. `prototypes/v3-steps/leg2.png` regenerated from `prompts/v3-st-leg2.txt`
with r0 as input; pasted into the sheet's leg cell. `guide-01-transformation.png`
is again a copy of `prototypes/v3-colour-steps.png`.

## Wing blades in the step panels (2026-10-14)

The owner saw the purple wing disagree between the step panels and the leg
strip. Steps 2 to 7 drew each wing half as a cover on its boot; the contract
(and ref-10) makes it a plate plus a 42.25 wide blade reaching inboard to 1.5
from the other one. r5, r4b, r3, r2c, r1 and r0 were edited to add the blades
(prompts `v3-st-blade-s2..s4.txt`; s4 used for r2c, r1, r0) and the sheet
recomposed with the same tile normalisation.

## Wings seen from above the car (2026-10-14)

The owner noticed step 1 drew the rear wing as a thin rod on posts, as if
seen from the side. Steps 1 to 5 look at the robot's front, which is the
car's top, so both wings show their top faces: the rear wing as a flat
purple slab under the boots (r6, `prompts/v3-st-wing-s1.txt`), the front
wing as a flat yellow panel about as wide as the shoulder towers (r6, r5,
r4b, r3, r2c, `prompts/v3-st-frontwing.txt`; measured 0.85 to 0.97 of the
grey width across the towers, contract 84/86).

## Sheet recomposed, wings sized by measurement (2026-10-14)

The wider front wing became the widest row, so the old tile anchor shifted
steps 1 to 5 down and cut their feet. `prototypes/v3-steps/compose.py` now
anchors robot panels on the top of the grey torso and shrinks them together
until the tallest fits. Wings measured against the shoulder wheels (119
across): the regenerated front wings were 104-125 x 21-26 mm, so each band
was resized to 84 x 13 (anisotropic resize of the drawn wing, background
patched); the step-1 rear wing slab was squashed to 0.35 of its drawn depth
(about 8 mm, contract 10). Back view regenerated with a flat front-wing panel
(`prompts/v3-st-back-frontwing.txt`): 80 mm wide, 20 deep (contract 13; left).

## Car tail redrawn (2026-10-14)

The car's tail now follows the contract: two plain boot blocks end the car,
toes rearward; from each toe a purple plate stands up on its knuckle (the
pylon), and the two flat blades lie across the plate tops, meeting at the
centre line, with open space under the wing. Tall outer endplates removed.
`carrear.png` (`prompts/v3-st-carrear.txt`) and the step-0 car `car.png`
(`prompts/v3-st-car.txt`) regenerated so the two agree.

## Leg strip ends in the car pose (2026-10-14)

Panel 4 of the side-view leg strip now shows the leg lying as it does in the
car: thigh, shin, boot toe rearward, the wing plate standing up from the toe
as the pylon and the blade flat on top pointing rearward, matching the car
tail. Panel 2 keeps the shin's full length (the boot fold does not move the
shin); panel 3 is shorter by the slide. Panels numbered 1 to 4. Generated
with `prompts/v3-st-leg2*.txt`.
