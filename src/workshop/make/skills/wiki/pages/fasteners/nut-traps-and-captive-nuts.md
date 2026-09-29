---
title: Nut traps and captive nuts
tags: [nut, nut-trap, captive-nut, hex-nut, iso-4032, iso-4035, pocket]
aliases: [nut pocket, hex pocket, embedded nut, thin nut, jam nut, DIN 934, DIN 439, nut slot]
sources:
  - https://www.aspenfasteners.com/content/pdf/Metric_ISO_4032_spec.pdf (DIN 934 / ISO 4032 table)
  - ISO 4035:1999 Table 1 (preview, https://cdn.standards.iteh.ai/samples/26385/7721755cf7884ffc9d25e1fc4b666a06/ISO-4035-1999.pdf)
  - https://en.wikipedia.org/wiki/ISO_metric_screw_thread (spanner sizes)
  - https://meshra.ai/blog/bolt-and-screw-holes-3d-printing (printed nut pocket offsets, slide-in orientation)
  - https://hackaday.com/tag/captive-nut/ (pocket-style and slot-style detents)
  - https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment (side vs bottom pocket strength)
related: [heat-set-inserts, metric-screw-clearance-holes, screw-head-recesses, fastener-torque-and-stripping]
updated: 2026-09-23
---

# Nut traps and captive nuts

A steel nut held in a printed pocket is the cheapest strong thread. It beats an
insert in pull-out when the load presses the nut against a solid wall, and it
costs nothing but a pocket.

## Nut sizes

Regular hex nuts, ISO 4032 (same across-flats as DIN 934 from M1.6 to M8):

| thread | s across flats (max / min) | e across corners min | m height (max / min) |
|---|---|---|---|
| M1.6 | 3.2 / 3.0 | 3.4 | 1.3 / 1.1 |
| M2 | 4.0 / 3.8 | 4.3 | 1.6 / 1.4 |
| M2.5 | 5.0 / 4.8 | 5.5 | 2.0 / 1.8 |
| M3 | 5.5 / 5.3 | 6.0 | 2.4 / 2.2 |
| M4 | 7.0 / 6.8 | 7.7 | 3.2 / 2.9 |
| M5 | 8.0 / 7.8 | 8.8 | 4.7 / 4.4 |
| M6 | 10.0 / 9.8 | 11.1 | 5.2 / 4.9 |
| M8 | 13.0 / 12.7 | 14.4 | 6.8 / 6.4 |

Thin nuts, ISO 4035 (same across-flats, lower):

| thread | M2 | M2.5 | M3 | M4 | M5 | M6 | M8 |
|---|---|---|---|---|---|---|---|
| m max | 1.20 | 1.60 | 1.80 | 2.20 | 2.70 | 3.2 | 4.0 |

Across corners of a sharp hexagon is `s / cos 30° = 1.1547 s`; the standard's
`e min` is slightly less because real nut corners are rounded.

## Printed pocket dimensions

Printed practice (Meshra): pocket across-flats 0.2–0.4 mm over the nut, depth
0.2–0.5 mm over the nut height.

| nut | s | pocket across-flats | nut height | pocket depth |
|---|---|---|---|---|
| M3 | 5.5 | 5.7–5.9 | 2.4 | 2.6–2.9 |
| M4 | 7.0 | 7.2–7.4 | 3.2 | 3.4–3.7 |
| M5 | 8.0 | 8.2–8.4 | 4.7 | 4.9–5.2 |

A pocket that prints 0.4 mm oval lets the nut spin, so the pocket's across-flats
is more critical than the clearance hole.

## Where the pocket opens decides the strength

CNC Kitchen, M3 in PETG: a nut in a **bottom** pocket, where the screw pulls it
against solid plastic, took 166 kg to pull out. A nut in a **side** pocket (a
slot entered from the side) failed at 86 kg, the weakest of every method
tested. Both held 2 Nm before the PETG crushed. Meshra recommends a pocket
entered from a side wall or the bottom, with the bolt pulling the nut against a
solid face. Read the two together: an entry slot is fine for assembly, but the
pull-out load must bear on uncut plastic. A side slot that cuts through the
load path is the weak case CNC Kitchen measured.

## Keeping the nut in during assembly

- **Pocket style:** a hex pocket with small detents (bumps) in its corners that
  the nut is pressed past.
- **Slot style:** a slot the nut slides into, retained by one "speed bump"
  detent. It works in tension and compression.
- **Print over it:** pause the print at the pocket's top layer, drop the nut
  in, and resume. The nut is sealed in with no detent. Design the pocket depth
  to end on a layer boundary; the same method is used for magnets
  ([[magnets-and-strap-slots#pause-and-embed]]).

Every captive nut is a retained part: it owes a `blocked` condition in the
motion manifest ([[joints#the-two-conditions-every-joint-owes]]).

## Checks

```python
S = {"M2": 4.0, "M2.5": 5.0, "M3": 5.5, "M4": 7.0, "M5": 8.0, "M6": 10.0, "M8": 13.0}
M = {"M2": 1.6, "M2.5": 2.0, "M3": 2.4, "M4": 3.2, "M5": 4.7, "M6": 5.2, "M8": 6.8}
assert S[size] + 0.2 <= pocket_af <= S[size] + 0.4, "pocket spins the nut or will not take it"
assert pocket_depth >= M[size] + 0.2, "nut stands proud of its pocket"
```
