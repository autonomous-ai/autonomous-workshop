---
title: Strain-wave gearing and differentials
tags: [strain-wave, harmonic-drive, flexspline, differential, open-differential, limited-slip]
aliases: [harmonic drive, harmonic gear, wave generator, flex spline, circular spline, diff, differential gear]
sources:
  - https://en.wikipedia.org/wiki/Strain_wave_gearing (components, 2-tooth difference, ratio formula, 30:1-320:1, no backlash)
  - https://en.wikipedia.org/wiki/Differential_(mechanical_device) (average-speed relation, torque to the lower-traction wheel, locking and limited-slip)
  - https://en.wikipedia.org/wiki/Epicyclic_gearing (carrier speed as a weighted average)
related: [planetary-gears, cycloidal-drives, wheeled-vehicles, gears]
updated: 2026-09-23
---

# Strain-wave gearing and differentials

## Strain-wave (harmonic) drive

Three parts:

- the **wave generator**: an elliptical cam on a thin bearing, which is the input;
- the **flexspline**: a thin, cup-shaped gear with external teeth that the cam
  deforms into an ellipse;
- the **circular spline**: a rigid ring with internal teeth.

The flexspline usually has two fewer teeth than the circular spline, and it
meshes only at the two ends of the ellipse.

```text
R = (Z_flex − Z_circ) / Z_flex
```

Example: 200 flexspline teeth against 202 gives R = −0.01, so the flexspline
turns at 1/100 of the wave generator's speed, in the opposite direction.

- Ratios from 30:1 up to 320:1 fit in the space where a planetary gives about
  10:1. Input and output are coaxial, with no backlash.
- The flexspline works only because the metal flexes elastically on every
  revolution. Its fatigue life is the design limit. A printed flexspline is a
  demonstrator, not a drive: printed plastic creeps and fatigues
  ([[flexures-and-living-hinges]]).
- For a toy-scale high ratio, prefer a cycloidal drive ([[cycloidal-drives]])
  or a compound planetary ([[planetary-gears]]).

## Differentials

A differential lets two output shafts turn at different speeds while it
shares the input between them. Its defining relation is that the carrier
(case) speed is the average of the two side-gear speeds:

```text
ω_case = (ω_left + ω_right) / 2          bevel or spur differential with equal side gears
```

It is the planetary relation with two members free
([[planetary-gears#speeds-the-willis-equation]]).

- Going straight, the pinions do not spin on their own axes and both sides
  turn together. In a turn the outer wheel speeds up and the inner slows by
  the same amount.
- **Torque is split equally**, so the side with less traction limits both. A
  wheel lifted off the floor spins while the other stops. A locking
  differential ties both sides together; a limited-slip one limits the speed
  difference.
- A toy that drives both rear wheels from one motor either accepts scrubbing
  in turns (a solid axle) or uses a differential. A differential-drive robot
  uses one motor per wheel instead ([[wheeled-vehicles#differential-drive]]).
- Printable forms: a bevel differential (pinions on a cross pin inside a
  case), or a spur-gear differential with two meshing pinion pairs. Both keep
  each side gear coaxial and axially retained in the case.

## Checks

- Asserts: the strain-wave tooth difference equals the number of lobes (2);
  the differential side gears are equal, with bevel cone angles from the
  gears page ([[gears#spur-gear-numbers]]).
- Motion: for a differential, sweep two cases: both sides together (case
  rotation), then one side held (pinions spin, other side at 2× case speed).
  Each is a coupled sweep with the case as obstacle ([[mechanism-verification]]).
