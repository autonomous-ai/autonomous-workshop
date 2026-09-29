---
title: Metric screw clearance and tapping holes
tags: [clearance-hole, screw, bolt, iso-273, tap-drill, metric-thread, hole-size]
aliases: [through hole, bolt hole, screw hole size, tapping drill, pilot hole, iso 262]
sources:
  - https://mechcodex.com/reference/metric-clearance-hole-sizes (ISO 273 fine/medium/coarse table and tolerance classes)
  - https://en.wikipedia.org/wiki/ISO_metric_screw_thread (ISO 262 pitches, 60° profile, H = 0.866 P, minor diameter, tap drill ≈ D − P)
  - https://meshra.ai/blog/bolt-and-screw-holes-3d-printing (printed clearance hole offsets)
  - https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/ (printed hole undersize)
related: [screw-head-recesses, screws-into-plastic, heat-set-inserts, fit-derivation]
updated: 2026-09-23
---

# Metric screw clearance and tapping holes

The hole a screw passes through is sized from the screw's nominal (major)
diameter, never from its pitch: coarse or fine thread, the clearance hole is the
same. `skills/cad/scripts/stdpart` builds the fastener and derives its hole;
the tables here are for sizing and for checking what it derives.

## ISO 273 clearance holes

ISO 273 gives three series. Modern drawings call them close, normal and loose.

| thread | fine / close (H12) | medium / normal (H13) | coarse / loose (H14) |
|---|---|---|---|
| M1.6 | 1.7 | 1.8 | 2.0 |
| M2 | 2.2 | 2.4 | 2.6 |
| M2.5 | 2.7 | 2.9 | 3.1 |
| M3 | 3.2 | 3.4 | 3.6 |
| M4 | 4.3 | 4.5 | 4.8 |
| M5 | 5.3 | 5.5 | 5.8 |
| M6 | 6.4 | 6.6 | 7.0 |
| M8 | 8.4 | 9.0 | 10.0 |
| M10 | 10.5 | 11.0 | 12.0 |
| M12 | 13.0 | 13.5 | 14.5 |

Medium is the general-purpose series; fine is for precise location; coarse
absorbs positional error between two parts drilled separately.

## Printed clearance holes

A vertical FDM hole prints undersize, typically 0.1–0.3 mm on diameter (about
0.24 mm for a 5 mm hole in PLA on a 0.4 mm nozzle). So a printed clearance hole
is modelled at the medium or coarse value, or 0.2–0.4 mm over nominal, then
checked with a test print. A horizontal hole also sags at its crown: give it a
teardrop or chamfered top ([[overhangs-and-print-orientation#the-fixes-in-the-order-worth-trying]]).

```python
CLEAR = {"M2": 2.4, "M2.5": 2.9, "M3": 3.4, "M4": 4.5, "M5": 5.5, "M6": 6.6, "M8": 9.0}  # ISO 273 medium
assert hole_d >= CLEAR[size], f"{size} clearance hole {hole_d} below ISO 273 medium"
```

## Thread basics and tapping drills

ISO metric threads have a 60° flank angle. Fundamental triangle height is
`H = 0.866 P`; minor diameter is about `D − 1.0825 P`. Coarse and fine pitches
(ISO 262):

| size | M1.6 | M2 | M2.5 | M3 | M4 | M5 | M6 | M8 | M10 | M12 |
|---|---|---|---|---|---|---|---|---|---|---|
| coarse P | 0.35 | 0.4 | 0.45 | 0.5 | 0.7 | 0.8 | 1 | 1.25 | 1.5 | 1.75 |
| fine P | 0.2 | 0.25 | 0.35 | 0.35 | 0.5 | 0.5 | 0.75 | 1 or 0.75 | 1.25 or 1 | 1.5 or 1.25 |

Tap drill for cutting a thread in metal: `D − P` (M3 → 2.5, M4 → 3.3,
M5 → 4.2, M6 → 5.0). That rule is for metal and machine taps. A screw formed
or cut directly into plastic wants a larger hole: [[screws-into-plastic]].

## Checks

- The clearance hole in the *clamped* part must be smaller than the insert or
  nut in the other part, or the fastener pulls through
  ([[heat-set-inserts#the-mating-part-carries-the-load]]).
- Never derive a clearance hole from a pitch or a tap drill value.
