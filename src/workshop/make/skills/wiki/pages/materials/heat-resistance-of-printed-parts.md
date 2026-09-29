---
title: Heat resistance of printed parts
tags: [heat, hdt, glass-transition, temperature, softening, car, outdoor]
aliases: [heat deflection temperature, glass transition, tg, vicat, softening point, hot car, dashboard, service temperature]
sources:
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/pla/polylite-tm-pla
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/petg-pet/polylite-tm-petg
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polylite-tm-abs
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polymaker-tm-asa
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/polycarbonate/polymax-tm-pc
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/nylon/polymide-tm-copa
  - Polymaker PolyMide PA6-CF Technical Data Sheet V4.1
  - Aljubury, Farhan, Mussa, Experimental Study of Interior Temperature Distribution Inside Parked Automobile Cabin, Journal of Engineering 21(3), 2015, https://pdfs.semanticscholar.org/2184/cbe693e6f556f45e86ac8c058ea0a4c2024b.pdf
  - https://formlabs.com/blog/guide-to-food-safe-3d-printing/ (dishwasher softening)
  - Dogan 2022, Strojniški vestnik 68(7-8) 451-460 (creep at 60 °C)
related: [filament-properties, creep-and-stress-relaxation, annealing-printed-parts, uv-and-outdoor-exposure, thermal-design-for-enclosures, thermal-expansion-and-hybrid-parts]
updated: 2026-09-23
---

# Heat resistance of printed parts

A printed part does not melt in a hot car. It softens at its glass transition,
sags under its own weight or its load, and creeps. The number that predicts
that is the **heat deflection temperature (HDT, ISO 75)**: the temperature at
which a standard bar under a set bending stress (0.45 or 1.8 MPa) deflects a
set amount.

## Temperatures per material

Printed specimens, Polymaker datasheets:

| material | Tg °C | Vicat °C | HDT 0.45 MPa °C | HDT 1.8 MPa °C |
|---|---|---|---|---|
| PLA | 61 | 63 | 60 | 58 |
| PETG | 81 | 84 | 78 | 75 |
| ABS | 101 | 104 | 100 | 98 |
| ASA | 98 | 105 | 103 | 100 |
| PC | 113 | 117 | 114 | 99 |
| PA6/66 copolymer (annealed) | 66 | — | 111 | 70 |
| PA6-CF (annealed) | 56.6 | — | 215 | 196 |

- Prusament PLA reports HDT 55 °C, and Prusament PETG 68 °C: other
  suppliers are lower. Take the lower value.
- Semi-crystalline nylons behave differently from amorphous plastics: their
  HDT can sit far above Tg, especially with fibre fill (PA6-CF: Tg 57 °C,
  HDT 196–215 °C).
- Annealing raises PLA's heat resistance sharply at 90 °C and above, at the
  cost of warping ([[annealing-printed-parts]]).

## Hot environments

- **Parked car:** in a measured summer study (unshaded car, clear sky), cabin
  air reached 70 °C and the dashboard approached 100 °C; the dashboard
  reached up to 58 °C above ambient. Only PA6-CF clears 100 °C with margin
  under load; ABS, ASA and PC sit right at it. PLA and PETG will deform.
- **Dishwasher:** PLA, PET and nylon soften around 60–70 °C, so they are
  unsuitable for dishwasher use ([[food-and-toy-safety]]).
- **Creep:** at 60 °C every printed material in one creep study except PC
  ruptured under 10–20 MPa within 3 hours
  ([[creep-and-stress-relaxation]]).
- Motors, lamps and electronics heat their mounts: take the surface
  temperature of the source, not the room temperature.

How hot a mount next to a regulator, driver or LED gets:
[[thermal-design-for-enclosures]].

Expansion coefficients, and letting long parts on metal rails float:
[[thermal-expansion-and-hybrid-parts]].

## Design rule

```python
SERVICE_T = 70            # °C, worst case the part will see (car cabin air)
MARGIN = 20               # °C below HDT for a loaded part
assert SERVICE_T <= HDT_045[MATERIAL] - MARGIN, f"{MATERIAL} softens in service"
```

The 20 °C margin is a conservative choice, not a standard: HDT is measured at
a single stress level for a short time, and a part under sustained load also
creeps. Use the 1.8 MPa HDT for a part under real bending load.

Quick choice by worst-case service temperature:

| service up to | choose |
|---|---|
| room temperature, low load | PLA |
| about 50–60 °C | PETG |
| about 80 °C | ABS, ASA, PC |
| 100 °C and above, or loaded when hot | PC (sustained load) or fibre-filled nylon |
