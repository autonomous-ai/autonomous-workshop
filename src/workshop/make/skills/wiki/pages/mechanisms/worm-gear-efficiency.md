---
title: Worm gear efficiency and self-locking
tags: [worm, efficiency, self-locking, back-drive, lead-angle, friction, sliding-velocity]
aliases: [worm drive efficiency, worm gear self locking, irreversible worm, worm backdrive, lead angle friction]
sources:
  - https://www.roymech.co.uk/Useful_Tables/Drive/Worm_Gears.html (efficiency formula, friction vs sliding speed, self-locking at gamma = atan(mu), 98-20 % range, gamma < 25 deg)
  - https://en.wikipedia.org/wiki/Leadscrew (tan(lambda)/tan(phi + lambda), friction table for steel/bronze and steel/brass)
  - https://www.roton.com/screw-university/screw-actions/screw-backdriving-efficiency/ (backdrive efficiency turns negative when self-locking)
  - "experience: a crossed-helical wheel whose end thrust closed its shaft's end float on a full disc face"
  - "experience: a printed worm standing on its end whose lower thread flanks failed a 45 deg overhang gate"
related: [gears, lead-screws, energy-drive, clutches-and-freewheels]
updated: 2026-10-07
---

# Worm gear efficiency and self-locking

The worm pair's geometry is on [[gears#worm-and-crossed-helical-pairs]]. This
page is about the sliding friction that decides how much power gets through
and whether the wheel can drive the worm back. A worm is a screw
([[lead-screws]]), and the same friction-angle argument governs both.

## Efficiency, worm driving

With `γ` the worm lead angle, `μ` the friction coefficient (friction angle
`φ = atan μ`) and `αn` the normal pressure angle (20° standard):

```text
η = (cos αn − μ tan γ) / (cos αn + μ cot γ)
η ≈ tan γ / tan(γ + φ)                           ignoring the pressure angle
```

- Efficiency rises with lead angle and falls with friction. Worm gears span
  about 98 % at the lowest ratios down to about 20 % at the highest.
- For αn = 20°, keep γ below 25°.
- A single-start worm at a high ratio has a small `γ` and is the least
  efficient. More starts raise `γ` and efficiency, and lower the ratio
  (`i = z_wheel / starts`).

## Friction depends on sliding speed

For a case-hardened steel worm on a phosphor-bronze wheel with mineral oil:

| sliding speed (m/s) | μ |
|---|---|
| 0.1 | 0.08 |
| 1.0 | 0.044 |
| 5.0 | 0.023 |
| 10 | 0.018 |
| 20 | 0.016 |

Friction is highest when slow, which is exactly a hand-turned toy. Dry
unlubricated pairs run much higher. For comparison, steel on bronze threads
run 0.15–0.23 dry and 0.10–0.16 oiled. No source consulted gives a printed plastic-on-plastic worm
friction coefficient: bracket μ with the dry figures above, and measure the
real efficiency and back-drive behaviour as an open item.

## Self-locking and back-driving

The wheel cannot drive the worm when

```text
γ < φ      i.e.   tan γ < μ
```

That typically falls at lead angles of about 2–8°. When self-locking, the
back-drive efficiency is negative: torque must be applied to the worm even to
let the load come down.

```python
import math
gamma = math.atan(WORM_LEAD / (math.pi * WORM_PITCH_DIA))
locks = math.tan(gamma) < MU_DESIGN
assert locks == MUST_HOLD, "worm self-locking does not match the requirement"
```

- **Want it to hold** (a lift, a winch, a pose that must not sag): design `γ`
  well below `atan μ` with the *lowest* μ you expect, meaning lubricated and
  running. Vibration can still creep a marginal worm.
- **Want it to back-drive** (a toy rolled backwards by hand, a pull-back
  motor): design `γ` well above `atan μ` with the *highest* μ you expect,
  meaning dry and slow. Use multiple starts.
- The worm's separating and axial thrust must be carried by a fixed stop:
  axial location on the worm shaft ([[shafts-and-bearings#axial-location-fixed-and-floating]]).

## The wheel's end thrust is a friction loss

The force that turns the worm's flank against the wheel has a component along
the wheel's axis equal to the worm's whole tangential force,
`F = T_worm / r_worm`. It pushes the wheel's shaft until its end float closes
on some face, and that face then rubs at its friction radius
`r_f = 2/3 (ro³ − ri³) / (ro² − ri²)`. Per unit worm torque the output is

```text
T_out / T_worm = i η − μ r_f / r_worm
```

Worked: `i = 3`, `γ = 30°`, `r_worm = 4`, μ 0.5 gives `η = 0.37` and
`i η = 1.11`. A full 10 mm disc face (`r_f` 7.5) takes 0.93 of it — 84 % of
what the pair delivers; a ring from the bore to `r` 4.6 (`r_f` 3.9) takes 44 %.
At μ 0.35 the same face takes 45 %, the ring 24 %.

- Give the thrust a **ring** at the smallest radius the bore allows, a few
  tenths proud of the face, on whichever part closes the float; the rest of
  the face keeps its running gap.
- Put any separate bushing's **stop on the side the thrust pushes toward**,
  so the thrust seats it instead of pulling it out.
- Below zero the drive locks however strong the motor:

```python
assert i * eta - mu * r_f / r_worm > 0.5 * i * eta, "the end thrust eats half the pair"
```

## A standing start is the binding case

`T_worm = T_out / (i η − μ r_f / r_worm)` grows faster than linearly with μ,
because both terms move: at `γ = 30°`, `i = 3`, `r_f / r_worm` ≈ 0.93 it
multiplies the output torque 1.6× at μ 0.5 and 3.7× at μ 0.625. Breakaway
friction is higher than sliding friction, so a printed worm drive that runs
at μ 0.5 can fail to start from rest at the worst crank angle. Price the start
with the static coefficient, find the μ at which it fails, and grease the
worm and the thrust ring rather than buying the margin with motor torque.

## A printed worm's lower flanks overhang

Printed standing, every thread has one flank facing down whichever end is on
the bed. That flank's normal makes `acos(cos α_n · sin β_w)` with the axis
(`α_n` the normal pressure angle, `β_w` the worm's helix angle from its axis):
14.5° flanks on a 30° lead (`β_w` 60°) lean 57° from vertical and fail a 45°
overhang limit. Passing it needs `cos α_n · sin β_w ≤ 0.707` — at 14.5° flanks,
a lead of 43° or more — and a steeper lead raises the wheel's axial thrust
(`tan β_wheel` times its tangential force), which on a drive with a thrust ring
costs far more than the print does. Steepening only the down-facing flank
thins the tooth tip below two lines at module 1. Print a small worm standing
at fine layers and record the gate failure; do not trade the drive for it.

## Checks

- Asserts: `γ < 25°`, self-locking matches the requirement with a margin on μ,
  and the train efficiency used in the ratio budget includes the worm's
  (often well under 50 %) ([[energy-drive#ratio-budget]]).
- Motion: a worm that should hold owes a `blocked` rotation of the wheel with
  the worm fixed. A rigid sweep cannot show friction, so the blocked check
  proves only the geometry. Record back-drive behaviour as measured, not
  assumed.
