---
title: Layer anisotropy and print orientation for strength
tags: [anisotropy, layer-adhesion, orientation, z-strength, interlayer, strength]
aliases: [z strength, layer lines, interlayer adhesion, build orientation strength, delamination, weak axis]
sources:
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/pla/polylite-tm-pla
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/petg-pet/polylite-tm-petg
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polymaker-tm-asa
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/polycarbonate/polymax-tm-pc
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/nylon/polymide-tm-copa
  - https://prusament.com/materials/prusament-pla-high-speed/ (tensile strength anisotropy coefficient)
  - Prusament PLA Technical datasheet v1.1, interlayer adhesion 17 MPa
  - Rodríguez-Panes et al., The Influence of Manufacturing Parameters on the Mechanical Behaviour of PLA and ABS Pieces Manufactured by FDM, Materials 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6119930/
  - https://www.cnckitchen.com/blog/better-performing-3d-prints-with-annealing-but-part-1-pla
related: [filament-properties, perimeters-infill-and-strength, printed-fatigue, overhangs-and-print-orientation, shafts-and-bearings, wall-mounting-and-hanging, straps-buckles-and-textile-attachment]
updated: 2026-09-23
---

# Layer anisotropy and print orientation for strength

An FDM part is a stack of welded layers. Along a layer the load runs through
continuous extruded strands; across layers it runs through the weld. The weld
is weaker and much less ductile, so **orientation is a strength decision**, not
only a support decision.

## How much weaker across the layers

Z-to-X-Y ratios computed from one supplier's printed-specimen data (Polymaker,
ISO 527, upright vs flat specimens):

| material | UTS Z / X-Y | E Z / X-Y | elongation Z / X-Y |
|---|---|---|---|
| PLA | 0.77 | 0.89 | 1.8 / 6.3 % |
| PETG | 0.84 | 0.90 | 3.3 / 8.4 % |
| ASA | 0.73 | 0.83 | 1.65 / 6.7 % |
| PC | 0.78 | 0.88 | 2.8 / 4.5 % |
| PA6/66 copolymer, dry | 0.59 | 0.82 | 1.3 / 12.7 % |

Other tests give much lower ratios:

- Prusament defines a tensile strength anisotropy coefficient
  r = Z strength / X-Y strength: PLA 0.33, PETG 0.38, PC Blend 0.33, and
  PLA High Speed 0.60 (r = 1 would be isotropic).
- Prusament PLA's interlayer adhesion is 17 ± 3 MPa against 57 MPa for the
  filament, about 0.3.
- One study (PLA and ABS, 2018) measured −22 % to −28 % for PLA loaded
  across layers, but **−88 % for ABS** (26.4 → 3.15 MPa) in the orientation
  that pulls layers apart.

The spread (0.12–0.9) is real: it depends on printer, temperature, cooling,
layer time and specimen. **Design rule: without a Z value measured for your
filament and settings, assume Z strength = 0.3 × X-Y** (the low end of the
supplier data above), and never rely on Z elongation above about 1.5 %.

```python
Z_FACTOR = 0.3   # Prusament r for PLA/PC Blend; use a measured value if you have one
assert stress_across_layers <= Z_FACTOR * UTS_XY / SAFETY_FACTOR
```

## Orient so layers do not carry the tension

- **Bending:** the extreme fibres carry the stress. Put the bending plane in
  the layer plane: a hook, lever or clip should lie flat, not stand up.
- **Pins and shafts:** print lying down so the strands run along the axis
  (see [[shafts-and-bearings#printed-shaft-or-bought-rod]]). A standing pin
  snaps at a layer line.
- **Snap beams and flexures:** the beam length lies in X-Y; a beam along Z
  breaks at the first deflection ([[flexure-materials-and-snap-strain]]).
- **Pressure vessels, cylinders with internal pressure:** hoop stress runs in
  the layer plane when the axis is vertical; axial stress crosses the layers.
- **Screw bosses and inserts:** pull-out loads along Z tear layers apart;
  add perimeters around the boss rather than infill
  ([[perimeters-infill-and-strength]]).

Wall hooks and brackets, where this decides the part:
[[wall-mounting-and-hanging]].

Strap bars and buckles print flat: [[straps-buckles-and-textile-attachment]].

## What does not fix it

- **Annealing PLA does not raise layer adhesion.** A tested hook's layer
  adhesion stayed at 42 kg before and after annealing, while in-plane
  strength rose 7.5 % ([[annealing-printed-parts]]).
- **More infill** strengthens a part mostly in-plane; the weld between layers
  is the same weld.

What does help: higher nozzle temperature, less part cooling, wider extrusion
lines (layer adhesion peaked around 150 % extrusion width in one test —
[[perimeters-infill-and-strength#extrusion-width]]), and materials with a
higher published r.

## Fatigue treats a flat print as nearly isotropic

For PLA printed flat on the bed, one fatigue study found that raster angle
could be neglected with little loss of accuracy ([[printed-fatigue]]). That is
in-plane orientation only; it does not cover loading across layers.

## Checks

- Name the load direction relative to the layers for every loaded feature.
- A stress across layers uses the Z factor, not the X-Y strength.
- A feature whose strength depends on Z elongation (a snap hook along Z, a
  press fit that stretches layers) is redesigned or reoriented.
