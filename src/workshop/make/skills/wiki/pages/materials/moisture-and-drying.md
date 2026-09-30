---
title: Moisture, drying and storage
tags: [moisture, hygroscopic, drying, storage, nylon, humidity]
aliases: [wet filament, dry filament, filament dryer, humidity, water absorption, hygroscopic filament]
sources:
  - https://help.prusa3d.com/article/drying-filament_332086
  - Prusament PLA Technical datasheet v1.1 (moisture absorption)
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/nylon/polymide-tm-copa
  - Polymaker PolyMide PA6-CF Technical Data Sheet V4.1
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/pla/polylite-tm-pla
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/petg-pet/polylite-tm-petg
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polylite-tm-abs
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/polycarbonate/polymax-tm-pc
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/tpu/polyflex-tm-tpu95
  - Analysis of the Mechanical Properties of 3D-Printed Plastic Samples Subjected to Selected Degradation Effects, Materials 2023, https://pmc.ncbi.nlm.nih.gov/articles/PMC10146359/
related: [filament-properties, uv-and-outdoor-exposure, heat-resistance-of-printed-parts]
updated: 2026-09-23
---

# Moisture, drying and storage

Water matters twice: filament that absorbed it prints badly, and a finished
part that absorbs it changes properties. For most filaments the first effect
is the one to manage; for nylon both are.

## Signs of wet filament

Poor surface quality first; then reduced layer bonding, surface blemishes, and
bubbling or smoke during extrusion (Prusa). Poor layer bonding is a strength
defect, not only a cosmetic one ([[layer-anisotropy]]).

## Drying temperatures

Two suppliers, both manufacturer recommendations:

| material | Prusa KB | Polymaker TDS |
|---|---|---|
| PLA | 45 °C, 6 h | 55 °C, 6 h |
| PETG | 55 °C, 6 h | 65 °C, 6 h |
| TPU | 60 °C, 4–6 h | 70 °C, 8 h |
| ABS | — | 70 °C, 6 h |
| ASA | 80 °C, 4 h | 70 °C, 7 h |
| PC / PC Blend | 85 °C, 5 h | 75 °C, 6 h |
| PC Blend carbon fibre | 90 °C, 4 h | — |
| PA11 carbon fibre | 90 °C, 6 h | — |
| PA6/66 copolymer | — | 100 °C, 8 h |
| PP CF/GF | 70 °C, 2–4 h | — |
| PEI | 150 °C, 8 h | — |

The two suppliers disagree by 10 °C in both directions. Use the maker's value
for the filament you have, and never exceed it: Prusa warns the filament will
soften and stick together, and the spool has its own limit (older black Prusa
spools are safe only to 45 °C).

## Which materials need it most

Prusa lists polyamide (nylon), PVA and TPU as needing drying more often than
PLA, and polyamide, polypropylene, PVA and BVOH as highly hygroscopic enough
to dry before each print. Polymaker says its nylons must be stored and used
below 20 % relative humidity.

Even PLA absorbs water: Prusament PLA took up 0.13 % in 24 h and 0.19 % in
7 days at 24 °C and 22 % humidity.

## Nylon is a different material wet

A printed nylon part keeps absorbing water from the air after printing. The
datasheet gives both states:

| PA6/66 copolymer (CoPA), X-Y | dry | wet (60 °C water, 48 h) |
|---|---|---|
| tensile strength | 78.0 MPa | 34.3 MPa |
| Young's modulus | 2703 MPa | 724 MPa |
| Z tensile strength | 45.8 MPa | 13.7 MPa |
| notched impact | 6.9 kJ/m² | 27.7 kJ/m² |

| PA6-CF, X-Y | dry | conditioned 70 % RH / 23 °C, 15 days |
|---|---|---|
| tensile strength | 105.0 MPa | 81.7 MPa |
| Young's modulus | 7453 MPa | 5666 MPa |

- **Design an unfilled nylon part with its wet properties**: in use it will
  reach equilibrium with room humidity. It gets tougher and much less stiff.
- Carbon fibre makes nylon far less sensitive (−22 % strength against −56 %).
- Nylon supports printed in the same material bond permanently if they
  absorb moisture before removal (Polymaker PA6-CF): remove them promptly.

## Humid service

In one degradation study (PLA, PETG, ABS, ASA from three makers each), 100 h
in a 55 °C, 100 % humidity condensation chamber cut one PLA's tensile strength
by about 28 % (59.1 → 42.6 MPa). PETG showed no decrease for any factor, and
ASA had the most stable properties overall. PLA is a poor choice for humid,
warm service.
