---
title: Printed threads
tags: [thread, printed-thread, trapezoidal, acme, lead-screw, bottle-cap, pitch, clearance]
aliases: [3d printed screw, printed bolt, printed nut, screw lid, jar thread, Tr8x8, iso 2904, DIN 103]
sources:
  - https://meshra.ai/blog/design-3d-printed-threads (minimum size, pitch, offsets, profile, orientation)
  - https://www.sovol3d.com/blogs/news/3d-printing-threads-and-screws-how-to-design-reliable-fdm-fasteners (M8 threshold, 0.2–0.4 mm offset; via search excerpt)
  - https://www.snapmaker.com/blog/3d-printing-threads/ (60° V vs trapezoid; via search excerpt)
  - https://en.wikipedia.org/wiki/Trapezoidal_thread_form (30° metric trapezoid, 29° Acme, ISO 2904, DIN 103, designation)
  - https://en.wikipedia.org/wiki/ISO_metric_screw_thread (60° profile, pitches)
  - https://hackaday.com/2024/12/03/torque-testing-3d-printed-screws/ (printed screw torque by orientation)
related: [metric-screw-clearance-holes, heat-set-inserts, overhangs-and-print-orientation, layer-anisotropy, printed-threads-and-bosses, sweeps-and-helices, bayonet-and-twist-locks]
updated: 2026-10-01
---

# Printed threads

A thread printed in the part itself needs no hardware and suits big, coarse
threads: jar lids, knobs, adjusters, caps. It is the wrong choice for small
machine-screw threads. There, use an insert or a nut
([[heat-set-inserts]], [[nut-traps-and-captive-nuts]]).

Why a hand-swept thread is a last resort, and how sweeps fail:
[[sweeps-and-helices]].

## Size limits

- **Diameter:** not below about M6; much easier at M8, M10 and up. Below M8 a
  0.4 mm nozzle cannot resolve the thread form (sources give M6 or M8 as the
  floor).
- **Pitch:** 1.0 mm or coarser for a 0.4 mm nozzle, 1.5 mm for a 0.6 mm
  nozzle. Finer pitches merge into a ramp. Normal 0.2 mm layers work well with
  1.5–2.0 mm pitches.

## Clearance

Model both halves at the true profile, then open the gap:

| half | offset on diameter |
|---|---|
| internal (nut, lid) | +0.2 to +0.4 mm |
| external (bolt, jar neck) | −0.1 to −0.2 mm |
| total between male and female | about 0.2–0.4 mm |

Apply the external offset to the flanks, not by scaling the part.

## Profile

- ISO metric threads are a 60° V. The sharp crest makes steep overhangs and a
  thin tip on a printed part.
- Prefer a **trapezoidal** thread (ISO 2904 / DIN 103, 30° included angle;
  Acme is 29°) or a rounded profile. Its flat crest and wide root stack
  cleanly layer by layer and give a stronger root.
- Designation: `Tr 60×9` is 60 mm diameter, 9 mm pitch; `Tr 60×18(P9)LH` is a
  two-start, left-hand thread with 18 mm lead. A two-start thread closes a lid
  in half the turns.
- Put a 45° chamfer (0.8–1.5 mm) on the first turn of the external thread and
  on the mouth of the internal one. It hides first-layer squish and guides the
  start.

## Orientation

Print threaded parts with the thread axis vertical. Laid on its side, the
thread's lower flanks become steep overhangs.

A printed *screw* loaded in torsion is the exception: standing up, it breaks
between layers. In one rough PLA test, vertically printed screws failed in the
thread at about 1.24 Nm (11 in·lb) at the low end. A horizontally printed
screw reached about 145 in·lb, roughly double the best vertical one. The test
used an under-range torque adapter, so trust the ratio, not the numbers. The
general rule is in [[layer-anisotropy]].

## Material

PLA prints crisp threads but is brittle. PETG or ABS flexes instead of cracking
and lasts longer on threads used often.

## Checks

```python
assert major_d >= 6.0, "printed thread below M6: use an insert or a nut"
assert pitch >= (1.0 if nozzle <= 0.4 else 1.5), "pitch finer than the nozzle can form"
assert 0.2 <= female_d - male_d <= 0.4, "thread clearance outside the printable range"
```
