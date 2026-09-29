---
title: Lead screws and ball screws
tags: [lead-screw, ball-screw, power-screw, lead, pitch, starts, self-locking, back-drive, efficiency, backlash]
aliases: [leadscrew, acme screw, trapezoidal screw, t8 screw, tr8x8, ballscrew, anti-backlash nut, power screw]
sources:
  - https://en.wikipedia.org/wiki/Leadscrew (torque to raise/lower, efficiency, self-locking condition, friction table)
  - https://www.roton.com/screw-university/screw-actions/screw-backdriving-efficiency/ (backdrive efficiency, 8 deg and 20 deg examples, ball screw 90/80 %)
  - https://toolbox.igus.com/4501/ball-screw-vs-lead-screw (efficiency ranges, noise, lubrication, backlash)
  - https://www.amazon.com/ReliaBot-150mm-Starts-Printer-Machine/dp/B07F1H4CWV (T8x8 spec, anti-backlash nut, search result)
related: [gears, energy-drive, joints, mechanism-design]
updated: 2026-09-23
---

# Lead screws and ball screws

A screw turns rotation into slow, strong, straight travel. Choose it over a
rack when you need a large force, fine positioning, or a load that holds
itself up when the power is off.

## Lead, pitch, starts

```text
lead L = pitch p × starts n          travel of the nut per screw turn
lead angle λ: tan λ = L / (π d_m)    d_m = mean thread diameter
```

A common printer screw, T8×8 (Tr8×8), is an 8 mm rod with a 2 mm pitch and
4 starts, so the nut moves 8 mm per turn. A T8×2 has the same rod with a
single start. More starts give a steeper lead: faster, more efficient, and
less self-locking.

## Torque and efficiency

With `F` the axial load, `φ` the friction angle (`tan φ = μ`) and `λ` the lead
angle:

```text
torque to raise  T = (F · d_m / 2) · tan(φ + λ)
torque to lower  T = (F · d_m / 2) · tan(φ − λ)
efficiency       η = tan λ / tan(φ + λ)                            square thread
                 η = (cos α − μ tan λ) / (cos α + μ cot λ)         thread half-angle α
```

Friction coefficients: steel on bronze 0.15–0.23 dry, 0.10–0.16 oiled;
steel on brass 0.15–0.19 dry, 0.10–0.15 oiled.

| screw | forward efficiency | back-drive |
|---|---|---|
| acme / trapezoidal, sliding nut | 20–40 % in actuators; 30–70 % quoted for polymer nuts | often none (self-locking) |
| power screw at 8° lead | 45 % | −13 %: will not back-drive |
| power screw at 20° lead | 65 % | 52 %: back-drives |
| ball screw | ~90 % at every lead | ~80 %: a vertical axis drops its load when unpowered |

## Self-locking

The screw holds its load when `μ > tan λ`, that is `φ > λ`: the lowering
torque `tan(φ − λ)` stays positive, and you must turn it to lower the load.

```python
import math
lam = math.atan(LEAD / (math.pi * D_MEAN))
assert (MU > math.tan(lam)) == MUST_HOLD_LOAD, "self-locking does not match the requirement"
```

The condition is not absolute: vibration can walk a marginally self-locking
screw down. For a load that must hold, keep `φ` well above `λ`, or add a brake.
A ball screw never self-locks.

## Backlash

A sliding nut has inherent backlash. An anti-backlash nut uses a spring to
push two nut halves apart along the thread, which takes up the clearance and
compensates for wear. One commercial T8 anti-backlash nut adjusts its preload
from 4 N to 8 N with the stock spring. A split nut (half nut) can be squeezed
to take up wear. A preloaded ball nut is near zero backlash.

Polymer nuts run quieter and often without lubricant. Ball screws are louder,
need regular lubrication, and are better at high speed and high dynamic load.

## Printed parts and checks

- A printed nut is a sliding nut: expect low efficiency, and wear as the life
  limit. Buy the screw and nut (`$step-parts`) rather than printing the thread
  of a load-bearing axis.
- The screw needs axial location at one end and a floating support at the
  other, or it binds on any misalignment
  ([[shafts-and-bearings#axial-location-fixed-and-floating]]).
- Keep the nut from turning: guide it on a rail or rod, because a nut that
  turns with the screw does not travel ([[joints#prismatic-joints]]).
- Motion checks: the nut `clear` along the travel, `blocked` against rotation
  and at both travel ends. Sample the travel at the lead, not the rotation
  ([[mechanism-verification#5-sampling]]).
