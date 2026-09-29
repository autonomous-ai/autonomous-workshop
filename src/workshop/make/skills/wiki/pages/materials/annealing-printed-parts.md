---
title: Annealing printed parts
tags: [annealing, heat-treatment, shrinkage, warping, heat-resistance, pla, petg, nylon, pc]
aliases: [heat treating prints, post-processing heat, anneal pla, dimensional change, oven treatment]
sources:
  - https://www.cnckitchen.com/blog/better-performing-3d-prints-with-annealing-but-part-1-pla
  - https://blog.prusa3d.com/how-to-improve-your-3d-prints-with-annealing_31088/
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/polycarbonate/polymax-tm-pc
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/nylon/polymide-tm-copa
  - Polymaker PolyMide PA6-CF Technical Data Sheet V4.1
related: [heat-resistance-of-printed-parts, layer-anisotropy, filament-properties, fit-derivation]
updated: 2026-09-23
---

# Annealing printed parts

Annealing holds a finished print above its glass transition so the polymer can
relax and, for crystallisable polymers, crystallise. It trades dimensional
accuracy for heat resistance and some strength. Whether it pays depends on the
material.

## Per material

| material | anneal at | what changes | verdict |
|---|---|---|---|
| PLA | 90 °C, 30–45 min (Prusa); 100 °C, 45 min then slow cool (CNC Kitchen) | heat resistance rises dramatically at 90 °C and above; X-Y tensile +7.5 % (63.5 → 68.2 MPa); lying hook +16.2 %; stiffness about +7 %; **layer adhesion unchanged**; impact −3.5 %; warping above 70 °C; collapses at 170 °C | only for simple parts that need heat resistance or in-plane strength |
| PETG | 90–110 °C, 30–45 min (Prusa) | tensile improves above 110 °C, degrades at 70–90 °C; impact best of all tested (repeatedly withstood 4 J above 130 °C); moderate shrinkage | Prusa's "overall winner" |
| ABS, ASA | — | warped more than the others even at low temperature; mechanical properties basically unchanged | unsuitable |
| PC | 90 °C, 2 h (Polymaker TDS) | — | per datasheet |
| PA6/66 copolymer | 80 °C, 6 h (Polymaker TDS) | datasheet properties are for annealed specimens | anneal after printing |
| PA6-CF | 80–100 °C, 1–3 h (Polymaker TDS) | datasheet specimens annealed | anneal after printing |

## Dimensions change, and not uniformly

- PLA parts **shrank in X-Y and grew in Z**, by up to 10 % in one test (a
  50 mm dimension became 45 mm one way and 55 mm the other).
- The distortion was not repeatable enough to compensate by scaling
  (CNC Kitchen); sand packing reduced but did not remove the warping.
- Prusa's advice, where dimensions matter: print at 100 % infill, measure the
  shrinkage on a test piece and scale for it, and avoid annealing complex
  parts with tight tolerances. Use an electric oven.

So an annealed part cannot carry a derived fit: a `cadfits` clearance
([[fit-derivation]]) is gone after a 5–10 % shrink. Either anneal before
machining or reaming the mating features, or leave fitted features out of
annealed parts.

## What annealing does not fix

- **Layer adhesion.** PLA's cross-layer strength stayed the same
  ([[layer-anisotropy#what-does-not-fix-it]]).
- **Brittleness.** Prusa found annealed PLA too brittle at any temperature
  for impact.

## Rules

- Prefer a material whose as-printed HDT meets the service temperature
  ([[heat-resistance-of-printed-parts]]) over annealing PLA.
- Anneal nylon and fibre-filled nylon as their datasheets say; their
  published properties assume it.
- Record annealing as a process step in the spec with its temperature and
  time, and mark every fitted dimension on an annealed part as unverified.
