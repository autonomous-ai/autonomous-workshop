---
title: Planetary gear sets
tags: [planetary, epicyclic, sun, planet, ring, carrier, gear-ratio, coaxial, assembly-condition]
aliases: [epicyclic gearing, planet gear, sun gear, ring gear, annulus, planet carrier, planetary gearbox]
sources:
  - https://en.wikipedia.org/wiki/Epicyclic_gearing (Willis equation, ratios per fixed member, equal-spacing condition)
  - https://www.zhygear.com/basic-constraints-of-planetary-gear-train-parameters/ (concentric, assembly and adjacency conditions defined)
  - "derived: coaxial and adjacency conditions from the centre-distance formulas on the gears page"
related: [gears, strain-wave-and-differentials, cycloidal-drives, mechanism-design]
updated: 2026-09-23
---

# Planetary gear sets

A sun gear (`Zs` teeth), planets (`Zp`, `N` of them) on a carrier, and an
internal ring (`Zr`), all on one axis. Hold one member and the other two form
a reduction in a compact, coaxial package. The load is shared across `N`
planets.

## Speeds: the Willis equation

```text
Zs · ωs + Zr · ωr = (Zs + Zr) · ωc
```

| held | input → output | ratio |
|---|---|---|
| ring | sun → carrier | `ωs / ωc = 1 + Zr / Zs` (the usual reducer, same direction) |
| carrier | sun → ring | `ωs / ωr = −Zr / Zs` (reverses, like a simple train) |
| sun | ring → carrier | `ωr / ωc = 1 + Zs / Zr` (small reduction) |

The carrier's speed is the tooth-weighted average of sun and ring:
`ωc = (Zs ωs + Zr ωr) / (Zs + Zr)`. Two free members make it a differential
([[strain-wave-and-differentials#differentials]]).

## The three tooth-count conditions

All three are asserts in the parameter block, checked before any geometry.

**Coaxial (concentric).** Sun–planet and planet–ring centre distances must be
equal. With one module, `m (Zs + Zp) / 2 = m (Zr − Zp) / 2`
([[gears#spur-gear-numbers]]), so

```python
assert ZR == ZS + 2 * ZP, "planets do not reach both sun and ring"
```

**Assembly (equal spacing).** `N` planets fit at equal angles only if

```python
assert (ZS + ZR) % N == 0, "planets cannot be spaced equally"
```

**Adjacency.** Neighbouring planets must not touch. Their centres are
`2 a sin(π/N)` apart with `a = m (Zs + Zp) / 2`, and each planet's tip
diameter is `m (Zp + 2)`, so

```python
import math
assert (ZS + ZP) * math.sin(math.pi / N) > ZP + 2, "adjacent planet tips collide"
```

Add margin for FDM rather than testing at equality.

## Printed planetary gearboxes

- Everything the gears page says about printed teeth applies: module ≥ 0.8,
  backlash made by thinning the teeth, and body under the teeth
  ([[gears#printed-tooth-choices]]).
- The ring is an internal gear: centre distance `m (Zr − Zp) / 2`. Thin the
  ring's teeth for backlash too, never move the planets outward.
- Phase each planet by its own angle so it meshes both sun and ring
  (`mesh_to` in `py_gearworks` does this;
  [[element-libraries]]). The assembly condition guarantees that a phase
  exists.
- Planets on printed pins need a running fit and axial retention: the carrier
  plates on both sides, or a shoulder pin ([[joints#revolute-joints]]).
- Stages stack: two stages multiply their ratios. The sun of stage 2 is the
  carrier output of stage 1.

## Checks

- Asserts: coaxial, assembly and adjacency, plus each mesh's centre distance
  audited on the placed parts.
- Motion: one coupled cycle of sun, planets (spin plus orbit) and carrier
  against the ring and the housing, with a fine sweep of one tooth pitch at
  the fastest mesh ([[mechanism-verification]]). Planets are compound motions,
  so place them from the kinematics, not by hand.
