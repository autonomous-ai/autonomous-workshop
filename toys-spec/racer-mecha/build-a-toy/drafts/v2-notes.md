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
