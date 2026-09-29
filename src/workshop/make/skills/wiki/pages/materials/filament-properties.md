---
title: Filament properties for design
tags: [material, filament, pla, petg, abs, asa, pc, nylon, tpu, carbon-fiber, modulus, strength, datasheet]
aliases: [material properties, filament comparison, technical data sheet, tds, young's modulus, tensile strength, material selection]
sources:
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/pla/polylite-tm-pla
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/petg-pet/polylite-tm-petg
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polylite-tm-abs
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polymaker-tm-asa
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/polycarbonate/polymax-tm-pc
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/nylon/polymide-tm-copa
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/tpu/polyflex-tm-tpu95
  - Polymaker PolyMide PA6-CF Technical Data Sheet V4.1 (Apr. 2019), https://cdn.webshopapp.com/shops/296832/files/318384333/polymaker-polymide-pa6-cf-tds-v4.pdf
  - Prusament PLA Technical datasheet v1.1 (16-02-2022), https://prusament.com/wp-content/uploads/2022/10/PLA_Prusament_TDS_2021_10_EN.pdf
  - Prusament PETG technical data sheet, https://prusament.com/materials/prusament-petg/
related: [layer-anisotropy, heat-resistance-of-printed-parts, moisture-and-drying, creep-and-stress-relaxation, shafts-and-bearings, thermal-expansion-and-hybrid-parts]
updated: 2026-09-23
---

# Filament properties for design

Numbers to put in a parameter block when a printed part must carry load,
survive heat, or bend. Every value below is a manufacturer's typical value for
**printed specimens at 100 % infill** (ISO 527 tensile, ISO 178 bending, ISO 75
HDT). They are not design allowables: the datasheets themselves say values
"vary significantly with printing conditions". Use them to compare materials
and to size with a safety factor, never as a guaranteed minimum.

## Printed-specimen properties, one supplier, one test method

All rows are Polymaker technical data sheets, so the test method and specimen
preparation are the same across rows. X-Y = specimen lying flat; Z = specimen
printed upright, so the load crosses the layers.

| material | density g/cm³ | E X-Y MPa | E Z MPa | UTS X-Y MPa | UTS Z MPa | elong. X-Y % | elong. Z % | HDT 0.45 MPa °C | HDT 1.8 MPa °C | Tg °C |
|---|---|---|---|---|---|---|---|---|---|---|
| PLA (PolyLite) | 1.17 | 3427 | 3065 | 52.3 | 40.5 | 6.3 | 1.8 | 60 | 58 | 61 |
| PETG (PolyLite) | 1.25 | 2117 | 1899 | 50.8 | 42.8 | 8.4 | 3.3 | 78 | 75 | 81 |
| ABS (PolyLite) | 1.12 | 2247 | 2081 | 33.4 ¹ | 29.7 | 17.9 | 3.1 | 100 | 98 | 101 |
| ASA (Polymaker) | 1.13 | 2379 | 1965 | 43.8 | 32.0 | 6.7 | 1.65 | 103 | 100 | 98 |
| PC (PolyMax) | 1.19 | 2435 | 2149 | 53.4 | 41.4 | 4.5 | 2.8 | 114 | 99 | 113 |
| PA6/66 copolymer (CoPA), dry | 1.12 | 2703 | 2209 | 78.0 | 45.8 | 12.7 | 1.3 | 111 | 70 | 66 |
| PA6/66 copolymer (CoPA), wet | — | 724 | 660 | 34.3 | 13.7 | 13.2 | 1.7 | — | — | — |
| PA6-CF (PolyMide), dry, annealed | 1.17 | 7453 | 4354 | 105.0 | 67.7 | 3.0 | 2.9 | 215 | 196 | 56.6 |
| PA6-CF, moisture conditioned | — | 5666 | 4714 | 81.7 | 64.4 | 4.6 | 1.8 | — | — | — |
| TPU 95A (PolyFlex) | 1.20–1.24 | 33.6 | — | — | — | 551 | — | — | — | — |

¹ The PolyLite ABS page lists both 33.4 and 29.7 MPa against the X-Y tensile
row; 29.7 MPa is also its Z value. Treat 30–33 MPa as the X-Y range.

Other properties from the same sheets:

- Bending modulus / strength X-Y: PLA 3231 / 86.9, PETG 1899 / 69.6, ABS
  2127 / 56.2, ASA 3206 / 73.4, PC 2050 / 81.3, CoPA dry 2510 / 109.8,
  PA6-CF 8339 / 169.0 MPa.
- Notched Charpy impact X-Y: PLA 3.3, PETG 2.6, ABS 18.0, ASA 10.3, PC 21.3,
  CoPA dry 6.9 (wet 27.7) kJ/m². PLA and PETG are brittle under a notch.
- TPU 95A: stress 11.1 MPa at 100 % strain, 25.8 MPa at 400 %; Shore 95A.

## A second supplier disagrees, and why that matters

Prusament's datasheets test differently, so their numbers do not line up with
the table above:

- Prusament PLA, printed horizontal: yield 51 MPa, modulus 2.3 GPa, flexural
  modulus 3.1 GPa, HDT 55 °C at both 0.45 and 1.80 MPa, density 1.24 g/cm³,
  and **interlayer adhesion 17 ± 3 MPa** against 57 MPa for the filament.
- Prusament PETG: tensile 47 MPa, tensile modulus 1500 MPa, bending modulus
  1700 MPa, elongation 5.1 %, HDT 68 °C, impact 2 kJ/m².

PLA modulus is 2.3 GPa from one supplier and 3.4 GPa from another; the same
polymer and nominally the same test. Specimen geometry, perimeters, speed
and temperature move the result. So:

- size with the lower published value, or with the value for the exact
  filament you will print;
- never mix suppliers' numbers inside one comparison.

## Rules that fall out of the table

- **Stiffness per millimetre:** PLA is the stiffest unfilled filament here
  (about 3.4 GPa); PETG, ABS, ASA and PC sit at 2.1–2.4 GPa. A PETG part
  deflects about 1.6 × more than the same PLA part. Carbon fibre in PA6 more
  than doubles stiffness (7.5 GPa X-Y) but leaves 3 % elongation.
- **Toughness vs stiffness:** ABS and PC have 5–6 × PLA's notched impact.
  Choose them for parts that get dropped or clipped; choose PLA for rigid
  parts that stay in place.
- **Nylon is only strong when dry.** CoPA loses 56 % of X-Y strength and
  73 % of stiffness when wet ([[moisture-and-drying#nylon-is-a-different-material-wet]]).
  Carbon-filled PA6 loses far less (22 % strength).
- **Heat:** PLA and PETG soften at 55–80 °C; ABS, ASA and PC reach
  100–114 °C at 0.45 MPa ([[heat-resistance-of-printed-parts]]).
- **Z is weaker and far less ductile** in every material: elongation across
  layers is 1.3–3.3 % ([[layer-anisotropy]]).

For shaft stiffness use E from this table in
[[shafts-and-bearings#stiffness-deflection-decides-before-strength-does]].

```python
E_MPA = {"PLA": 3427, "PETG": 2117, "ABS": 2247, "ASA": 2379, "PC": 2435}  # Polymaker X-Y, typical
assert MATERIAL in E_MPA, "size stiffness from a datasheet value, not a guess"
```

Thermal expansion coefficients for printed and metal parts:
[[thermal-expansion-and-hybrid-parts]].
