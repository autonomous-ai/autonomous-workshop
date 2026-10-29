---
title: Nut traps and captive nuts
tags: [nut, nut-trap, captive-nut, hex-nut, iso-4032, iso-4035, pocket]
aliases: [nut pocket, hex pocket, embedded nut, thin nut, jam nut, DIN 934, DIN 439, nut slot]
sources:
  - https://www.aspenfasteners.com/content/pdf/Metric_ISO_4032_spec.pdf (DIN 934 / ISO 4032 equivalence)
  - skills/cad/scripts/stdpart (bd_warehouse HexNut nut_data)
  - ISO 4035:1999 Table 1 (preview, https://cdn.standards.iteh.ai/samples/26385/7721755cf7884ffc9d25e1fc4b666a06/ISO-4035-1999.pdf)
  - https://en.wikipedia.org/wiki/ISO_metric_screw_thread (spanner sizes)
  - https://meshra.ai/blog/bolt-and-screw-holes-3d-printing (printed nut pocket offsets, slide-in orientation)
  - https://hackaday.com/tag/captive-nut/ (pocket-style and slot-style detents)
  - https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment (side vs bottom pocket strength)
related: [heat-set-inserts, metric-screw-clearance-holes, screw-head-recesses, fastener-torque-and-stripping]
updated: 2026-10-10
---

# Nut traps and captive nuts

A steel nut held in a printed pocket is the cheapest strong thread. It beats an
insert in pull-out when the load presses the nut against a solid wall, and it
costs nothing but a pocket.

## Nut sizes come from the library

Regular (ISO 4032) and thin (ISO 4035) hex nuts are `stdpart` families:
`HexNut(size, fastener_type="iso4032")` carries the maximum across-flats `s`
and height `m` in `nut.nut_data`, which is what a pocket is sized from, so the
tables are not copied here. ISO 4032 has the same across-flats as DIN 934 from
M1.6 to M8; ISO 4035 keeps the across-flats and lowers the nut. The library
spells the thin M3 nut `M3-0.45`, not `M3-0.5`.

Across corners of a sharp hexagon is `s / cos 30° = 1.1547 s` (the library's
`nut.nut_diameter`); the standard's `e min` is slightly less because real nut
corners are rounded.

## Printed pocket dimensions

Printed practice (Meshra): pocket across-flats 0.2–0.4 mm over the nut's `s`,
depth 0.2–0.5 mm over its `m` — for an M3 regular nut, 5.7–5.9 across flats
and 2.6–2.9 deep.

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
nut = HexNut(size, fastener_type="iso4032", simple=True)    # bd_warehouse, via stdpart
s, m = nut.nut_data["s"], nut.nut_data["m"]
assert s + 0.2 <= pocket_af <= s + 0.4, "pocket spins the nut or will not take it"
assert pocket_depth >= m + 0.2, "nut stands proud of its pocket"
```
