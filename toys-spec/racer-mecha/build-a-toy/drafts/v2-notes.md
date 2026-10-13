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
