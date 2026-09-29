---
title: Worm gear efficiency and self-locking
tags: [worm, efficiency, self-locking, back-drive, lead-angle, friction, sliding-velocity]
aliases: [worm drive efficiency, worm gear self locking, irreversible worm, worm backdrive, lead angle friction]
sources:
  - https://www.roymech.co.uk/Useful_Tables/Drive/Worm_Gears.html (efficiency formula, friction vs sliding speed, self-locking at gamma = atan(mu), 98-20 % range, gamma < 25 deg)
  - https://en.wikipedia.org/wiki/Leadscrew (tan(lambda)/tan(phi + lambda), friction table for steel/bronze and steel/brass)
  - https://www.roton.com/screw-university/screw-actions/screw-backdriving-efficiency/ (backdrive efficiency turns negative when self-locking)
related: [gears, lead-screws, energy-drive, clutches-and-freewheels]
updated: 2026-09-23
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

## Checks

- Asserts: `γ < 25°`, self-locking matches the requirement with a margin on μ,
  and the train efficiency used in the ratio budget includes the worm's
  (often well under 50 %) ([[energy-drive#ratio-budget]]).
- Motion: a worm that should hold owes a `blocked` rotation of the wheel with
  the worm fixed. A rigid sweep cannot show friction, so the blocked check
  proves only the geometry. Record back-drive behaviour as measured, not
  assumed.
