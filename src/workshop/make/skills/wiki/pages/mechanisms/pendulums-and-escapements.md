---
title: Pendulums and escapements
tags: [pendulum, escapement, anchor, deadbeat, clock, period, isochronism, recoil]
aliases: [clock mechanism, anchor escapement, recoil escapement, graham escapement, deadbeat escapement, escape wheel, pallet, seconds pendulum]
sources:
  - https://en.wikipedia.org/wiki/Pendulum (T = 2 pi sqrt(L/g), amplitude series, 1 % at 23 deg, seconds pendulum 0.994 m, compound pendulum)
  - https://en.wikipedia.org/wiki/Anchor_escapement (4-6 deg swing vs about 100 deg for the verge, recoil, comparison with deadbeat)
  - https://en.wikipedia.org/wiki/Deadbeat_escapement (locking faces concentric with the pivot, impulse faces, no recoil, less tolerant of wear)
related: [cams-intermittent, energy-drive, gears]
updated: 2026-09-23
---

# Pendulums and escapements

An escapement lets a stored torque (a weight or spring) out one tooth at a
time and gives the pendulum a small push each swing. The pendulum sets the
rate; the escapement only keeps it swinging. See
[[cams-intermittent#escapement]] for where this sits among intermittent
mechanisms.

## Pendulum period

```text
simple pendulum, small swing   T = 2π √(L / g)
large swing                    T = 2π √(L / g) · [1 + θ₀²/16 + 11 θ₀⁴/3072 + …]
compound (rigid) pendulum      T = 2π √(I_O / (m g r_cm))
```

- The period depends on length and gravity, not on the bob's mass.
- **Circular error**: the period grows with amplitude. At θ₀ = 0.4 rad (23°)
  it is 1 % longer. A clock with a 6° swing whose amplitude drifts gains or
  loses noticeably, on the order of 15 s/day. Keep the swing small and
  constant.
- A **seconds pendulum** (2 s period, one second per swing) is about 0.994 m
  long.
- A real pendulum is compound. Its effective length is set by where its mass
  sits, so put a sliding or threaded bob on it to adjust the rate.

```python
import math
T = 2 * math.pi * math.sqrt(L_EFF_M / 9.81)      # small-swing period, s
assert abs(T - T_TARGET) / T_TARGET < 0.01, "pendulum length does not give the target period"
```

## Anchor (recoil) escapement

An escape wheel with pointed teeth and an anchor-shaped pallet arm on the
pendulum's pivot. It cut the pendulum swing from about 100° (verge) to 4–6°,
which made long, accurate pendulums practical. **Recoil**: after each tick the
wheel is pushed slightly backwards. That wears the train and makes the rate
depend on the drive force: more force, faster swing. It is the forgiving,
printable choice; a carefully made one can rival a deadbeat.

## Deadbeat (Graham) escapement

Each pallet has two faces:

- a **locking face**, an arc concentric with the anchor pivot, where the
  tooth rests and pushes straight through the pivot, giving no impulse and no
  recoil;
- a sloped **impulse face** near the bottom of the swing.

The pendulum swings freely most of the time, so the rate depends less on drive
force and lubrication. The cost is that it tolerates manufacturing error and
wear less. It is the standard for accurate pendulum clocks.

## Printed clock notes

- Printed escapements work, but tuning is empirical: pallet angles, drop and
  lock are adjusted by test. Record the rate and the run time as open items.
- Friction dominates at low power. Use bearings or pivots with minimal
  contact, stiff pendulum rods, and a heavy bob relative to the rod.
- The going train runs from the drive down to the escape wheel. Its ratios
  set the hands; the escape wheel's teeth and the period set the timekeeping
  ([[gears#trains-and-ratio-budget]]).

## Checks

- Asserts: pendulum length for the target period, and train ratios matching
  the escape rate.
- Motion: sweep the anchor through its swing against the escape wheel in fine
  steps. A tooth passes the pallet in a fraction of the swing, so sample for
  that contact ([[mechanism-verification#5-sampling]]). Lock and drop
  clearance must be positive at each pallet.
