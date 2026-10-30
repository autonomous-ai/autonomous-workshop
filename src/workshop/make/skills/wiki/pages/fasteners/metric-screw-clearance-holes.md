---
title: Metric screw clearance and tapping holes
tags: [clearance-hole, screw, bolt, iso-273, tap-drill, metric-thread, hole-size]
aliases: [through hole, bolt hole, screw hole size, tapping drill, pilot hole, iso 262]
sources:
  - https://mechcodex.com/reference/metric-clearance-hole-sizes (ISO 273 fine/medium/coarse table and tolerance classes)
  - https://en.wikipedia.org/wiki/ISO_metric_screw_thread (ISO 262 pitches, 60° profile, H = 0.866 P, minor diameter, tap drill ≈ D − P)
  - https://meshra.ai/blog/bolt-and-screw-holes-3d-printing (printed clearance hole offsets)
  - https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/ (printed hole undersize)
  - skills/cad/scripts/stdpart (bd_warehouse clearance_hole_diameters and tap_hole_diameters)
related: [screw-head-recesses, screws-into-plastic, heat-set-inserts, fit-derivation]
updated: 2026-10-10
---

# Metric screw clearance and tapping holes

The hole a screw passes through is sized from the screw's nominal (major)
diameter, never from its pitch: coarse or fine thread, the clearance hole is the
same. `skills/cad/scripts/stdpart` indexes the fastener; the `bd_warehouse`
object it names carries the ISO 273 clearances and the tap drills, so this page
keeps no copy of either table:

```bash
.venv/bin/python -c "from bd_warehouse.fastener import SocketHeadCapScrew as S; s = S('M3-0.5', 10, simple=True); print(s.clearance_hole_diameters, s.tap_hole_diameters)"
# {'Close': 3.2, 'Normal': 3.4, 'Loose': 3.6} {'Soft': 2.5, 'Hard': 2.7}
```

## ISO 273 series and when to use each

ISO 273 gives three series, which `bd_warehouse` calls `Close`, `Normal` and
`Loose` (fine / medium / coarse, H12 / H13 / H14). Medium is the
general-purpose series; fine is for precise location; coarse absorbs
positional error between two parts drilled separately. The library matches
ISO 273 from M1.6 to M10; at M12 its normal and loose values (14.0 / 15.0) are
larger than the standard's 13.5 / 14.5.

## Printed clearance holes

A vertical FDM hole prints undersize, typically 0.1–0.3 mm on diameter (about
0.24 mm for a 5 mm hole in PLA on a 0.4 mm nozzle). So a printed clearance hole
is modelled at the medium or coarse value, or 0.2–0.4 mm over nominal, then
checked with a test print. A horizontal hole also sags at its crown: give it a
teardrop or chamfered top ([[overhangs-and-print-orientation#the-fixes-in-the-order-worth-trying]]).

```python
screw = SocketHeadCapScrew(size, length, simple=True)       # bd_warehouse, via stdpart
assert hole_d >= screw.clearance_hole_diameters["Normal"], f"{size} clearance hole {hole_d} below ISO 273 medium"
```

## Thread basics and tapping drills

ISO metric threads have a 60° flank angle. Fundamental triangle height is
`H = 0.866 P`; minor diameter is about `D − 1.0825 P`. The coarse pitch (ISO 262)
is the suffix of every metric size `stdpart sizes` prints (`M3-0.5`, `M8-1.25`).
The library lists fine pitches only from M8 up; below that they are M2 0.25,
M2.5 0.35, M3 0.35, M4 and M5 0.5, M6 0.75.

Tap drill for cutting a thread in metal: `D − P` (M3 → 2.5, M4 → 3.3,
M5 → 4.2, M6 → 5.0), which is the library's `tap_hole_diameters["Soft"]`.
That rule is for metal and machine taps. A screw formed or cut directly into
plastic wants a larger hole: [[screws-into-plastic]].

## Checks

- The clearance hole in the *clamped* part must be smaller than the insert or
  nut in the other part, or the fastener pulls through
  ([[heat-set-inserts#the-mating-part-carries-the-load]]).
- Never derive a clearance hole from a pitch or a tap drill value.
