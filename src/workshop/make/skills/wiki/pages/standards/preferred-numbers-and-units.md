---
title: Preferred numbers, units and stock sizes
tags: [units, inch, preferred-numbers, renard, stock, lumber, sheet-metal, conversion]
aliases: [Renard series, R10, R20, ISO 3, preferred sizes, inch to mm, thou, mil, nominal lumber size, sheet metal gauge]
sources:
  - https://en.wikipedia.org/wiki/Renard_series
  - https://en.wikipedia.org/wiki/Inch
  - https://en.wikipedia.org/wiki/Lumber
  - https://en.wikipedia.org/wiki/Sheet_metal
related: [step-file-format, known-object-sizes, scale-anchors, iso-286-fits]
updated: 2026-09-23
---

# Preferred numbers, units and stock sizes

When a size is free, pick it from a preferred series. When a size comes from
the outside world, know which unit and which "nominal" it is in. Most
wrong-by-a-factor models trace to one of the traps below.

## Preferred numbers: the Renard series (ISO 3)

Each series steps by a constant ratio: the 5th, 10th, 20th or 40th root of
10. Rounded values between 1 and 10 (multiply by powers of ten):

- **R5:** 1.00, 1.60, 2.50, 4.00, 6.30
- **R10:** 1.00, 1.25, 1.60, 2.00, 2.50, 3.15, 4.00, 5.00, 6.30, 8.00
- **R20:** 1.00, 1.12, 1.25, 1.40, 1.60, 1.80, 2.00, 2.24, 2.50, 2.80, 3.15,
  3.55, 4.00, 4.50, 5.00, 5.60, 6.30, 7.10, 8.00, 9.00
- **R40** adds 1.06, 1.18, 1.32, 1.50, 1.70, 1.90, 2.12, 2.36, 2.65, 3.00,
  3.35, 3.75, 4.25, 4.75, 5.30, 6.00, 6.70, 7.50, 8.50, 9.50 between those.

Use them for a family of sizes (a range of knob diameters, a set of box
heights) so each step is the same *proportion*, and for a single free size so
it matches stock and standard parts. Many standard part series (fuse ratings,
capacitor voltages, metric dimensions) follow them.

## Inch and millimetre

- **1 in = 25.4 mm exactly**, since the international yard of 1959 (US
  1 July 1959; UK and Australia 1963–64).
- **1 thou = 1 mil = 0.001 in = 0.0254 mm.** "Mil" also means millimetre
  in some countries, so read the context.
- The US survey foot (1/39.37 m basis) differed by two parts per million and
  was phased out by 1 January 2023. It is irrelevant at part scale.
- Fractional inches use dyadic fractions (1/2, 3/8, 5/16…). 5/16 in =
  7.9375 mm, which is *not* 8 mm, so a "5/16 rod" in an 8 mm bore is a loose
  fit.

**Unit sanity check:** after importing any file or reading any drawing,
compare the bounding box to one known size. A factor of 25.4 (or 1/25.4)
means an inch/mm confusion, and a factor of 10 means cm/mm
([[step-file-format#units-are-declared-not-implied]],
[[scale-anchors]]).

## Nominal is not actual

- **North American lumber** is named by its rough, undried size. After
  drying and planing: nominal 1 in thick → ¾ in, 2 in → 1½ in; widths up to
  6 in lose ½ in, and wider boards lose ¾ in. So 2×4 = 1½ × 3½ in (38 × 89 mm),
  1×6 = ¾ × 5½ in (19 × 140 mm), 4×4 = 3½ × 3½ in (89 × 89 mm).
- **Sheet-metal gauge** is not a length. A higher gauge is thinner, the scale
  differs between steel, galvanised steel and aluminium, and ASTM discourages
  gauge numbers. Convert a gauge with a material-specific table, or ask for the
  thickness in mm, which most of the world specifies directly.

## Rules

- Keep one unit in the model (this repository: mm) and convert at the border,
  with the conversion written as a named constant (`IN = 25.4`).
- Record which "nominal" a bought size is, and model the *actual*.
- A free dimension picked from R10/R20 needs no provenance beyond "preferred
  number". Say so in the parameter comment.
