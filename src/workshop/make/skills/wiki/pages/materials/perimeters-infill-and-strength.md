---
title: Perimeters, infill and strength
tags: [perimeters, walls, infill, extrusion-width, layer-height, strength, stiffness, slicer]
aliases: [wall count, shells, infill density, infill pattern, gradient infill, slicer settings for strength, extrusion width]
sources:
  - https://www.cnckitchen.com/blog/the-effect-of-extrusion-width-on-strength-and-quality-of-3d-prints
  - https://www.cnckitchen.com/blog/gradient-infill-for-3d-prints
  - https://3dprinting.com/how-to/how-to-get-stronger-fdm-3d-prints/ (summary of CNC Kitchen perimeter vs infill hook test)
  - Rodríguez-Panes et al., Materials 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6119930/
  - Ezeh and Susmel 2019, International Journal of Fatigue 126 (infill named as open question)
related: [layer-anisotropy, wall-thickness-and-hollowing, filament-properties, printed-fatigue, print-time-and-material-estimation, beam-and-plate-stiffness, lightweighting-and-lattices]
updated: 2026-09-23
---

# Perimeters, infill and strength

A printed part is a shell of perimeters around a lattice of infill. For most
loads the shell carries the stress, so where the material goes matters more
than how much there is.

## Perimeters beat infill for the same weight

Hook tests (CNC Kitchen, as summarised by 3dprinting.com): a hook with **5
perimeters and 10 % infill** was nearly **22 % stronger** than one with 2
perimeters and 42 % infill at the same weight. More perimeters mattered more
than more infill, because bending and torsion stress is highest at the
surface and zero at the neutral axis.

Gradient infill, denser near the walls, made a bending bar almost 30 % stiffer
at equal weight than 30 % rectilinear infill, and almost 60 % stiffer at
equal print time; it brought no significant gain for a compact hook. Material
near the surface helps in bending and does little in a small, thick part.

## Extrusion width

Same PLA, 0.4 mm nozzle, 0.16 mm layers:

| hook configuration | failure load |
|---|---|
| 2 perimeters at 100 % width | about 20 kg |
| 4 perimeters at 100 % width | about 33 kg |
| 3 perimeters at 133 % width | about 37 kg |
| 2 perimeters at 200 % width | about 39 kg |

- Wider lines almost doubled strength at the same or slightly shorter print
  time.
- Layer adhesion peaked around **150 % extrusion width** and then declined;
  surface quality stayed acceptable up to about 140–150 %.

## Infill and layer height in a tensile test

PLA and ABS tensile specimens (Materials 2018):

- raising infill from 20 % to 50 % raised tensile strength by **27 % (PLA)**
  and **25 % (ABS)** for 16–18.5 % more weight. The authors found infill the
  most influential parameter in their test;
- going from 0.1 mm to 0.2 mm layers cost **11 % (PLA)** and **8 % (ABS)** of
  tensile strength.

A tensile bar loads its whole cross-section evenly, which is why infill
matters more there than in a bending hook. Match the setting to the load.

## Rules

- **Bending or torsion (hooks, levers, brackets, shafts):** spend material
  on perimeters; 4–5 walls with modest infill beat dense infill.
- **Pure tension or compression through the whole section:** infill density
  counts; use a high infill in the loaded region.
- **Screw bosses, pins, thin features:** make them solid by giving them
  enough perimeters to fill them.
- **Wider extrusion (up to about 150 %)** strengthens walls and layer bonds.
- **Thinner layers** add some strength and cost print time; choose them for
  small loaded features, not by default.
- The slicer is not in the CAD source: write the settings the strength claim
  depends on (walls, infill, width, layer height) in the spec, beside the
  wall rules in [[wall-thickness-and-hollowing]].
- Fatigue: infill's effect on printed-PLA fatigue life is an open research
  question ([[printed-fatigue]]).

```python
PRINT_SETTINGS = {"perimeters": 4, "infill_pct": 20, "extrusion_width_pct": 120, "layer_mm": 0.2}
assert PRINT_SETTINGS["perimeters"] >= 3, "loaded bending part: spend material on walls"
```

Mass and filament length from the model:
[[print-time-and-material-estimation]]. Where material belongs in a section:
[[beam-and-plate-stiffness]].

Why slicer infill is usually the right lattice:
[[lightweighting-and-lattices]].
