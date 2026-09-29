---
title: Timing belts and pulleys
tags: [belt, pulley, timing-belt, gt2, htd, synchronous, tension, center-distance]
aliases: [toothed belt, synchronous belt, gt2 belt, 2gt, htd belt, belt drive, timing pulley]
sources:
  - https://texasbelting.com/pages/timing-belt-selection-guide (pitch length formula, 6 teeth in mesh, profiles, tensioning)
  - https://reprap.org/wiki/Choosing_Belts_and_Pulleys (GT2 for linear motion, 6 teeth in contact, 12/18-tooth pulleys, steel-core failure on small pulleys)
  - https://www.engbench.com/timingpulley.php (PD = N p / pi, OD = PD - 2 PLD, PLD values, printed groove widening)
  - https://en.wikipedia.org/wiki/Belt_(mechanical) (capstan equation, power P = (T1 - T2) v, timing belts do not slip)
related: [gears, shafts-and-bearings, energy-drive, mechanism-design, cable-and-tendon-drives]
updated: 2026-09-23
---

# Timing belts and pulleys

A toothed (synchronous) belt transmits rotation between parallel shafts at a
fixed ratio over a centre distance too long for a gear pair. When it is
correctly tensioned it does not slip and it runs at constant speed. A flat or
round friction belt slips by design, which suits a hand-crank toy
([[gears#trains-and-ratio-budget]]).

## Profiles

| family | examples | use |
|---|---|---|
| curvilinear | GT2 (2 mm), GT3 (3 mm), HTD 3M / 5M / 8M | higher load, lower noise, less backlash; GT2 is the default for printers and small linear axes |
| trapezoidal | MXL, XL, T2.5, T5 | older, light duty; T-profiles were designed for rotary synchronisation, not linear positioning |

A pulley must match the belt's profile *and* its pitch: a GT2 belt on a T2.5
pulley rides up and loses position.

## Pulley numbers

```text
pitch diameter   PD = N · p / π          N teeth, p belt pitch
outside diameter OD = PD − 2 · PLD       PLD: pitch-line differential
ratio            i  = N_driven / N_driver
belt travel per pulley turn = N · p
```

The pitch line runs through the belt's tension member, *outside* the pulley
tips, so the tip diameter is smaller than the pitch diameter. PLD by profile:
GT2 2 mm 0.254 mm; GT2 3 mm ~0.381; GT2 5 mm ~0.635; HTD 3M ~0.381;
HTD 5M 0.5715; HTD 8M ~0.914. Check value: a 20-tooth GT2 pulley has a
12.73 mm pitch diameter and a ~12.22 mm outside diameter.

## Belt length and centre distance

```text
L = 2C + π (D1 + D2) / 2 + (D2 − D1)² / (4C)     pitch length, same units throughout
```

`C` is the centre distance and `D1 < D2` are the pitch diameters. A timing
belt comes in fixed pitch lengths, so `L = teeth × p`. Choose the stock belt
nearest the computed length, then solve the centre distance back from it and
place the second shaft from that number. Never type both.

```python
import math
def belt_length(C, D1, D2):
    return 2*C + math.pi*(D1 + D2)/2 + (D2 - D1)**2/(4*C)
assert abs(belt_length(C, PD1, PD2) - BELT_TEETH*PITCH) < 0.1, "C not solved from the stock belt"
```

## Teeth in mesh and pulley size

- **At least 6 teeth in mesh on the smaller pulley**, and 8 or more for high
  torque or shock loads. A belt with fewer teeth engaged skips teeth under
  load.
- **Small pulleys**: 12 teeth is the practical minimum on GT2 and 18 or more
  is recommended. Most printer drives use 16 or more; one generator warns
  below 10. Steel-core belts have broken on 16-tooth pulleys from bending
  stress, so use glass or aramid cores under about 20 teeth.
- The arc of contact on the small pulley shrinks as the ratio grows and the
  centre distance shortens. An idler that wraps the belt further around the
  small pulley raises the tooth count in mesh.

## Tension

Tension it enough that no tooth skips under load. Over-tensioning is one of
the most common causes of short belt and bearing life. Tension loads both
shafts as a bending moment, so size the shaft span and supports for it
([[shafts-and-bearings#stiffness-deflection-decides-before-strength-does]]).
Provide adjustment: slotted motor holes, a moving idler, or a centre distance
that can be set. A friction belt's capacity follows the capstan relation
`T1 / T2 = e^(μ α)` (α = wrap angle in radians), and the power it carries is
`P = (T1 − T2) v`.

Cord, rope and cable drives, capstans and tendons:
[[cable-and-tendon-drives]].

## Printed pulleys

- Print at 0.16 mm layers or finer with a 0.4 mm nozzle or smaller, and slow
  down near the tooth tips.
- Widen printed grooves by 0.1–0.2 mm to improve engagement with a real belt.
  Only a fit test with the belt proves it.
- Keep the bore from breaking through at the tooth roots: assert a ring of
  body under the root diameter, as for a gear ([[gears#body-under-the-teeth]]).
- Add flanges so the belt cannot walk off, and align the pulleys. A belt walks
  toward the lower-tension side of a misaligned drive.

## Checks

- Asserts: teeth in mesh ≥ 6, pulley teeth ≥ 12 (≥ 18 preferred),
  `L == belt_teeth × p` with `C` solved from it, and body under the root.
- Motion: a belt is not a rigid body, so do not sweep it. Sweep the pulleys
  as rotations and check the belt corridor as a clear path against the frame
  ([[mechanism-verification]]).
- Open items: tooth-skip torque, belt stretch and final tension are physical
  quantities that no rigid gate measures.
