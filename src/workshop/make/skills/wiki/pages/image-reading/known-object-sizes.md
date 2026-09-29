---
title: Known object sizes for scaling a photo
tags: [scale, reference-object, dimension, standard, lookup]
aliases: [scale objects, coin sizes, credit card size, reference sizes, objects in frame]
sources:
  - ISO/IEC 7810 (ID-1 card)
  - ISO 216 (A4); ANSI/ASME Y14.1 (US Letter)
  - ISO 15 (608 bearing); ISO 4762 (socket-head cap screw); ISO 4032 (hex nut)
  - USB-IF connector specifications (USB-A, USB-C)
  - US Mint and European Central Bank coin specifications
related: [scale-anchors, scaling-limits]
updated: 2026-09-23
---

# Known object sizes for scaling a photo

Measure the object's pixels, divide by its real size, apply the resulting
mm-per-pixel to the target — only if the object shares the target's focal
plane ([[scale-anchors#a-known-object-must-share-the-focal-plane]]). State the
object and the size used.

## Exact references

| Reference object | Real dimension | Confidence |
|---|---|---|
| ISO/IEC 7810 ID-1 card (credit/bank/ID) | 85.60 × 53.98 mm | Exact — a global standard |
| A4 sheet | 297 × 210 mm | Exact |
| US Letter sheet | 279.4 × 215.9 mm | Exact |
| LEGO stud pitch | 8.0 mm | Exact |
| LEGO 2×4 brick | 31.8 × 15.8 × 9.6 mm | Exact |
| Cherry-MX keyboard key pitch (1u) | 19.05 mm | Exact |
| AA battery | 50.5 × Ø14.5 mm | Exact |
| AAA battery | 44.5 × Ø10.5 mm | Exact |
| USB-A plug shell | 12.0 × 4.5 mm | Exact |
| USB-C receptacle opening | 8.34 × 2.56 mm | Exact |
| 608 skate bearing | Ø22 OD × Ø8 ID × 7 W mm | Exact |
| M3 socket-head cap screw head | Ø5.5 mm, 2.5 mm hex | Exact (ISO 4762) |
| M3 nut across flats | 5.5 mm | Exact (ISO 4032) |
| Gridfinity grid pitch | 42.0 mm | Exact |
| US quarter | Ø24.26 mm | Exact |
| US penny | Ø19.05 mm | Exact |
| 1 euro coin | Ø23.25 mm | Exact |
| 2 euro coin | Ø25.75 mm | Exact |

## Coarse references

State these as a range, never as a hard number.

| Reference object | Real dimension | Confidence |
|---|---|---|
| Adult palm width (4 fingers) | ~80–90 mm | Coarse — ±10 % |
| Adult index finger width | ~18–20 mm | Coarse |
| Standard coffee mug | ~Ø80 × 95 mm | Coarse — varies enormously |
| Interior door height | ~2000–2100 mm | Coarse, region-dependent |

## Anything not on this list

For a named phone, a specific motor, a wall plate, a connector, a vehicle part
— **web-search the manufacturer or standards spec** and cite it. Do not carry
these from memory: they drift by model and region, and a confident recalled
number is the classic failure. For any purchasable component visible in the
image, search the `$step-parts` catalog first — an exact catalog record beats
both a table lookup and a search.

Published hand, finger and stature percentiles, with how much a body-scaled
dimension can be trusted: [[body-dimensions-for-scale]].
