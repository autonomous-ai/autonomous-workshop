---
title: Dowel pins and press fits in printed parts
tags: [dowel, pin, press-fit, interference, bearing-seat, locating-pin, iso-2338, iso-8734]
aliases: [parallel pin, locating dowel, interference fit, press fit hole, m6 dowel, DIN 7, DIN 6325, bearing press fit]
sources:
  - https://www.fastenermart.com/iso-2338-dowel-pins.html (ISO 2338 sizes, m6/h8)
  - https://www.ekinsun.com/custom-fasteners/dowel-pin-size-chart/ (ISO 8734 / DIN 6325 m6, Ø6 = 6.004–6.012; via search excerpt)
  - https://www.sfp-tw.com/en/post/iso-2338-dowel-pins-differences-and-relationships-with-din-7-iso-8734-and-din-6325 (unhardened vs hardened; via search excerpt)
  - https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/ (FDM fit ladder, hole undersize, 608 seat, TPU, coupon)
  - https://meshra.ai/blog/magnet-pockets-3d-printing (press-fit pocket practice)
  - "toolchain: step.parts dowel and precision-shaft STEP files measured at double their named length"
related: [fit-derivation, joints, shafts-and-bearings, iso-286-fits, magnets-and-strap-slots, thermal-expansion-and-hybrid-parts, exact-constraint-and-kinematic-mounts]
updated: 2026-09-29
---

# Dowel pins and press fits in printed parts

A steel dowel locates two printed parts exactly, and it carries shear that a
printed peg would not. Its hole is the one place in a printed part where you
aim for interference.

## Standard dowels

| standard | material | tolerance | diameters |
|---|---|---|---|
| ISO 2338 (was DIN 7) | unhardened steel | m6 or h8 | 0.8, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 30 |
| ISO 8734 (DIN 6325) | hardened and ground (A: through-hardened, B: case-hardened, C: martensitic stainless) | m6 | 1–20 |

An m6 pin is slightly **over** nominal: a hardened Ø6 m6 dowel measures
6.004–6.012 mm. ISO 2338 suits parts without high impact or wear; ISO 8734
is for precision location. The ISO fit system itself is in [[iso-286-fits]].
Find the part with `step-parts` or `stdpart` and derive its hole, never type
it. Some catalog files are modelled at double length -- step.parts ISO 2338
dowels and its precision shafts alike (the `d006_l0200` shaft is 400 long, the
`d006_l025` dowel 50); pick the id by measured geometry and name the real part
in the bill of materials.

Locating with one round pin and one slot:
[[exact-constraint-and-kinematic-mounts]].

## The FDM fit ladder

Designed gap on diameter between a pin or shaft and a printed hole (Creative3DP):

| fit | gap on diameter | use |
|---|---|---|
| press / interference | −0.10 mm | bearings, pins, bushings, magnets in pockets |
| snug / transition | +0.05 mm | locating features, lids that shouldn't fall off |
| close running | +0.15 mm | pivots, printed hinges, sliding mechanisms |
| free / loose | +0.35 mm | outdoor or dusty parts, "must work first try" |

These are gaps *as printed*. A printed hole comes out 0.1–0.3 mm undersize
(about 0.24 mm on a 5 mm PLA hole with a 0.4 mm nozzle), and a printed shaft
about 0.1 mm oversize. The printer's compensation goes on top. The repository
derives both halves of a mate from `cadfits` classes
([[fit-derivation#the-fdm-clearance-table]]); use the numbers here to choose
the class and to sanity-check the result.

## Bearings and TPU

- A 608 bearing (22 mm OD) in PLA: model the pocket at about 21.95 mm plus the
  printer's hole compensation. Guides converge on 0.05–0.10 mm interference
  per side for PLA, up to 0.10 for PETG
  ([[shafts-and-bearings#bushing-or-ball-bearing]]).
- TPU compresses and grips. A press fit wants double the interference; a
  moving fit needs 0.5–0.8 mm total clearance or friction welds it shut.

How a steel pin or bearing in a printed bore behaves over temperature:
[[thermal-expansion-and-hybrid-parts]].

## Prove it on a coupon

Print a 10 × 10 mm plate holding the hole and a 10 mm stub of the shaft (or use
the real pin). If the fit is wrong, adjust the offending dimension by 0.05 mm
and reprint. Two iterations are usually enough. A press fit in a printed part
is a claim no geometry gate can verify; record it as an open item until a
print confirms it.

## Checks

```python
assert pin_standard in ("ISO 2338", "ISO 8734"), "dowel not from a standard"
assert fit_class_for(pin) == "press", "a locating dowel wants interference, not clearance"
```
