---
title: ISO 286 limits and fits
tags: [iso-286, fit, tolerance, hole-basis, it-grade, clearance, interference, transition, bearing]
aliases: [H7/g6, H7/h6, H7/k6, H7/p6, limits and fits, IT grade, press fit, sliding fit, shaft tolerance, hole tolerance]
sources:
  - https://en.wikipedia.org/wiki/Engineering_fit
  - https://en.wikipedia.org/wiki/IT_Grade
  - https://www.roymech.co.uk/Useful_Tables/ISO_Tolerances/ISO_286_2H.html
  - https://www.roymech.co.uk/Useful_Tables/ISO_Tolerances/ISO_286_2s.html
related: [fit-derivation, shafts-and-bearings, joints, iso-2768-general-tolerances]
updated: 2026-09-23
---

# ISO 286 limits and fits

ISO 286 is the language of machined fits: a letter for *where* the tolerance
band sits relative to the nominal size, and a number (the IT grade) for *how
wide* it is. Read it on drawings, in bearing and pin datasheets, and when a
bought part must mate a printed one. FDM clearances are a different, much
coarser world ([[fit-derivation]]). This page is for reading the numbers,
not for choosing a print gap.

## Reading a fit designation

- **Upper case = hole, lower case = shaft**: `H7/g6` is an H7 hole with a g6
  shaft.
- **The letter** is the fundamental deviation. `H` holes and `h` shafts
  have one limit exactly at nominal (H: lower deviation 0; h: upper deviation
  0). Letters before h/H give clearance, and letters after give progressively
  more interference.
- **The number** is the IT grade: bigger means a wider band.
- **Hole-basis system**: keep the hole at H and vary the shaft letter. This is
  the common choice, because a reamed hole is harder to vary than a ground
  shaft. **Shaft-basis** keeps the shaft at h and varies the hole.

## Preferred hole-basis fits

| fit | kind | meaning |
|---|---|---|
| H11/c11 | clearance | large clearance where accuracy is not essential |
| H9/d9 | clearance | large clearance, high running speeds, accuracy not essential |
| H8/f7 | clearance | small clearance, moderate accuracy (close running) |
| H7/g6 | clearance | minimal clearance, high accuracy, easy to assemble (sliding, plain bearings) |
| H7/h6 | clearance | very close clearance, precise location |
| H7/k6 | transition | negligible clearance or interference; rubber-mallet assembly (rolling-bearing inner rings under normal load) |
| H7/n6 | transition | small interference, light pressing force |
| H7/p6 | interference | light interference, cold pressed |
| H7/s6 | interference | medium interference, hot or cold pressing with large force |
| H7/u6 | interference | shrink fit needing a large temperature difference |

## IT grade widths, µm

| nominal (mm) | IT5 | IT6 | IT7 | IT8 | IT9 | IT10 | IT11 |
|---|---|---|---|---|---|---|---|
| 0–3 | 4 | 6 | 10 | 14 | 25 | 40 | 60 |
| 3–6 | 5 | 8 | 12 | 18 | 30 | 48 | 75 |
| 6–10 | 6 | 9 | 15 | 22 | 36 | 58 | 90 |
| 10–18 | 8 | 11 | 18 | 27 | 43 | 70 | 110 |
| 18–30 | 9 | 13 | 21 | 33 | 52 | 84 | 130 |

## Hole limits (H), µm

Lower deviation 0 for every H class, so the upper deviation equals the IT
width:

| nominal (mm) | H6 | H7 | H8 | H9 |
|---|---|---|---|---|
| over 3 to 6 | +8 | +12 | +18 | +30 |
| over 6 to 10 | +9 | +15 | +22 | +36 |
| over 10 to 18 | +11 | +18 | +27 | +43 |
| over 18 to 30 | +13 | +21 | +33 | +52 |

## Shaft limits, µm (upper / lower deviation)

| nominal (mm) | g6 | h6 | k6 | n6 | p6 |
|---|---|---|---|---|---|
| over 3 to 6 | −4 / −12 | 0 / −8 | +9 / +1 | +16 / +8 | +20 / +12 |
| over 6 to 10 | −5 / −14 | 0 / −9 | +10 / +1 | +19 / +10 | +24 / +15 |
| over 10 to 18 | −6 / −17 | 0 / −11 | +12 / +1 | +23 / +12 | +29 / +18 |
| over 18 to 30 | −7 / −20 | 0 / −13 | +15 / +2 | +28 / +15 | +35 / +22 |

Worked: an 8 mm H7/g6 bore is 8.000–8.015, and the shaft is 7.986–7.995, so
the clearance is 0.005–0.029 mm. An 8 mm H7/p6 shaft is 8.015–8.024, giving
0.000–0.024 mm interference.

## What this means for printed parts

- All of these bands are **hundredths of a millimetre or finer**. A 0.4 mm-nozzle
  FDM print holds tenths, so an ISO fit cannot be printed as specified. Design
  a printed mate with the FDM fit classes (`cadfits`, [[fit-derivation]]),
  and use ISO 286 for the *bought* half.
- **A bought part's datasheet fit tells you its real size.** A bearing bore
  or a dowel ground to h6/m6 is at most a few µm off nominal. Model it at
  nominal and put the whole clearance into the printed half.
- A press fit into plastic uses the plastic's compliance, not an ISO
  interference class. Take the printed seat from the `snug`/`press` classes
  and prove it with a test coupon ([[shafts-and-bearings#bushing-or-ball-bearing]]).
