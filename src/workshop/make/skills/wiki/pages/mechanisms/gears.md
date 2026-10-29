---
title: Gears
tags: [gear, spur, rack, worm, bevel, internal, backlash, module, ratio, mesh, train]
aliases: [gearing, pinion, gearbox, reduction, involute, worm gear, bevel gear, center distance, tooth]
sources:
  - ISO 21771 / ISO 53 (involute gear geometry and basic rack)
  - Shigley's Mechanical Engineering Design, ch. 13 (gear geometry, worm gearing)
  - bd_warehouse gear docs; py_gearworks docs
  - "toolchain: py_gearworks mesh_to(backlash=0.0) moves centres inward on a thinned pair (reproducible)"
related: [shafts-and-bearings, energy-drive, mechanism-verification, element-libraries, noise-and-vibration]
updated: 2026-09-23
---

# Gears

Search `$step-parts` and `stdpart` first, on the governing numbers (module,
tooth count, bore); a recorded miss is what licenses authoring one.

Why a printed gear train is loud and what quiets it: [[noise-and-vibration]].

## Authoring one is still not drawing one

`bd_warehouse` (spur only) and `py_gearworks` (spur, helical, bevel, cycloid,
internal ring, rack, planetary) generate the involute from the numbers on this
page and hand the reference radii back, so the centre distance is derived
rather than typed; `py_gearworks`' `mesh_to` places the second gear at the
centre distance *and* in phase. Thin the teeth in the constructor
(`backlash=`) and leave `mesh_to`'s `backlash` out: `mesh_to(backlash=0.0)`
closes the centres onto teeth that were already thinned, and the pair clashes
([[element-libraries#the-two-backlash-arguments]]). Worm, hypoid and face gears
are in neither library. Which library for which gear:
[[element-libraries#two-gear-libraries-and-which-one]].

## Spur gear numbers

| quantity | formula | note |
|---|---|---|
| pitch diameter | `d = m z` | the circle the mesh rolls on |
| tip diameter | `da = m (z + 2 ha)` | `ha` = 1.0 full depth, 0.8 stub |
| root diameter | `df = m (z - 2 × 1.25)` | dedendum 1.25 m |
| circular pitch | `p = π m` | tooth + gap along the pitch circle |
| centre distance | `a = m (z1 + z2) / 2` | internal gear: `m (z2 - z1) / 2` |
| ratio | `i = z_driven / z_driver` | output turns `i` times slower |
| rack travel per pinion turn | `π m z` | |
| bevel pitch cone (90°) | `δ1 = atan(z1 / z2)`, `δ2 = 90° - δ1` | mitre pair: 45° / 45° |

**Centre distance is derived, never typed.** Audit it as a datum pair:
`hypot(axis1 - axis2) == m (z1 + z2) / 2` within 0.2 mm. Place the second
shaft from the formula, then assert the placed distance.

## Printed tooth choices

- **Module ≥ 0.8 for FDM, 1.0 is the comfortable floor.** Below it the tooth
  tip is a few extrusion widths and prints as a blob.
- **Pressure angle**: 20° is standard; 14.5° with stub teeth (0.8 m addendum)
  gives thicker tips on small pinions.
- **Undercut limit** for generated involutes: `z_min = 2 ha / sin²(α)` →
  17 teeth at 20°, 32 at 14.5° (full depth). A printed tooth is not generated,
  so this is a warning line: below it go stub, thin the tip, or add teeth —
  and check the tip width is ≥ 2 extrusion widths.
- **Backlash**: 0.2–0.3 mm per gear on a 0.4 nozzle. Apply it by thinning
  each tooth at the pitch circle, never by pushing the centres apart — that
  shortens contact. Shaft deflection at the gear eats into it
  ([[shafts-and-bearings#stiffness-deflection-decides-before-strength-does]]).
- **Face width** 6–10 m; wider only helps if the shafts are stiff.
- Knife edges at the tooth ends print badly: ramp the teeth in at the faces.

## Body under the teeth

The bore or keyed socket must leave a solid ring under the root circle:

```python
wall = (M * (Z - 2.5) - BORE_ACROSS_CORNERS) / 2
assert wall >= 1.2, f"m{M} z{Z}: {wall:.2f} mm of body under the teeth"
```

An m1 z8 pinion has a 5.5 mm root circle; a 6.2 mm socket through it leaves
the teeth hanging on a skin, and every geometry gate passes it. If the assert
fails, add teeth, raise the module, or put the pinion on a hub.

## Mesh phasing

Two gears modelled at rest must put a tooth of one into a gap of the other on
the line of centres, or they overlap at rest and `interfere` fails. Rotate
one gear by `180° / z` from tooth-on-line to gap-on-line; with an odd tooth
count the tooth that sits on the line is not opposite another tooth. Record
the phase as a parameter and, in the kinematics, drive the second gear by
`-θ × z1 / z2` from that phase.

## Worm and crossed-helical pairs

- wheel pitch radius `r2 = z2 mn / (2 cos β2)`
- worm pitch radius `r1` is free (choose for strength and lead)
- centre distance `a = r1 + r2`; ratio `i = z2 / starts`
- worm lead angle `λ = 90° - β2` for a 90° shaft angle

Worked: `mn = 1`, 4 starts, `r1 = 4.0`, a 12-tooth wheel at 30° →
`r2 = 6.93`, `a = 10.93`, 3:1. A single-start worm with a small lead angle
(below ~6°) **self-locks**: the wheel cannot back-drive it. That is right for a
lift or a winch, wrong for a toy the child is meant to roll backwards.

Which way the worm turns for a given wheel direction is a sign that is easy to
get wrong on paper; measure it by sweeping the mesh both ways and record the
sign as `[measured]`.

## Trains and ratio budget

- One spur stage up to ~1:6 in print; beyond that compound (two gears on one
  shaft) rather than a tiny pinion.
- The pinion is the weak member: it sees the most tooth engagements.
- Idlers change direction, not ratio.
- Belt or band pulleys replace gears for long centres; they slip, which is a
  feature for a toy with a hand crank.
- Related drives: [[belts-and-pulleys]], [[planetary-gears]], [[cycloidal-drives]],
  [[strain-wave-and-differentials]], [[lead-screws]]; worm friction and
  self-locking in detail: [[worm-gear-efficiency]].

## Measuring a mesh

Two numbers make a mesh claim honest, both measured on the built solids:

1. **One tooth pitch swept at fine steps** — worst overlap stays ≤ the
   threshold. Step size must be a fraction of a tooth (a third of a
   millimetre at m1), declared as `maxStepMm`, or the sweep steps over the
   collision.
2. **Free play** — rotate one gear against the other held still until
   contact, both directions. Zero play means it will bind when printed; large
   play means lost motion.

A full-cycle sweep at coarse steps is a bulk-clearance check, not a mesh
check — say which one each condition is in its description.
