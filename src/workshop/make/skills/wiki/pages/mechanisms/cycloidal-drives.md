---
title: Cycloidal drives
tags: [cycloidal, cycloid, reducer, eccentric, lobe, pin-ring, reduction]
aliases: [cycloid drive, cycloidal reducer, cyclo drive, cycloidal disc, trochoidal reducer, pin wheel]
sources:
  - https://en.wikipedia.org/wiki/Cycloidal_drive (ratio (P - L)/L, output holes oversized by the eccentricity, two or three discs, efficiency figures)
  - https://howtomechatronics.com/how-it-works/what-is-cycloidal-driver-designing-3d-printing-and-testing/ (lobes = pins - 1, epitrochoid equations, two discs 180 deg apart, printed-drive observations)
related: [planetary-gears, gears, shafts-and-bearings, strain-wave-and-differentials]
updated: 2026-09-23
---

# Cycloidal drives

An eccentric on the input shaft makes a lobed disc wobble inside a ring of
fixed pins. Each input turn walks the disc back by one lobe, so the reduction
is large in a flat package, the backlash can be near zero, and many lobes
share the load.

## Ratio

`P` ring pins, `L` lobes on the disc:

```text
reduction  r = (P − L) / L
usual design  L = P − 1   →   one lobe per input turn, output = input / L, reversed
```

Example: 16 pins and 15 lobes give 15:1.

## Geometry

The disc profile is an epitrochoid offset by the pin radius. With `R` the
pin-circle radius, `Rr` the pin (roller) radius, `E` the eccentricity and `N`
the number of pins:

```text
x = R cos t − Rr cos(t + atan(sin((1−N) t) / (R/(E N) − cos((1−N) t)))) − E cos(N t)
y = −R sin t + Rr sin(t + atan(sin((1−N) t) / (R/(E N) − cos((1−N) t)))) + E sin(N t)
```

A worked set: `N = 16`, `R = 45`, `Rr = 6.5`, `E = 1.5` (mm). Generate the
profile as a spline through these points in source, and keep `R`, `Rr`, `E`
and `N` as the only parameters.

**Output.** Pins on the output flange pass through holes in the disc. Make
each hole's diameter the output pin diameter plus twice the eccentricity
(`d_hole = d_pin + 2E`, e.g. 8 + 2 × 1 = 10 mm), so the pins roll around the
holes and pass on only the disc's rotation, not its wobble.

```python
assert L_LOBES == P_PINS - 1
assert abs(D_OUT_HOLE - (D_OUT_PIN + 2 * ECC)) < 1e-6, "output holes must be pin + 2e"
```

**Balance.** One disc vibrates. Two discs 180° apart cancel the static
imbalance but leave a small dynamic one. Three discs, the outer two moving
together against the middle one, are used at high speed.

## Performance and printed drives

- Commercial: single stage up to 119:1, efficiency approaching 93 %; double
  stage approaching 86 %.
- One printed 15:1 drive delivered about 10× torque, roughly 66 % efficient,
  and was back-drivable.
- Printed plastic wears where the output pins slide in the disc holes, so put
  rollers or bearings on the pins, and on the ring pins too. That printed
  drive used 44 small 6×13×5 bearings.
- Hole and outline accuracy matter: the printed example tuned its slicer's
  horizontal expansion separately for holes and outer walls.

## Checks

- Asserts: `L = P − 1`, output hole = pin + 2E, and the eccentric bearing's
  bore and outside diameter matched to their seats by `cadfits`.
- Motion: sweep one input turn in fine steps (the disc contact moves fast
  relative to the input) with the disc placed from the kinematics: translate
  by the eccentric, rotate by `−θ/L`. Name the ring pins as obstacles
  ([[mechanism-verification]]).
