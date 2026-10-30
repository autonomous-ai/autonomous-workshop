---
title: Layer anisotropy and print orientation for strength
tags: [anisotropy, layer-adhesion, orientation, z-strength, interlayer, strength, load-path, shear, bending]
aliases: [z strength, layer lines, layer adhesion, interlayer adhesion, build orientation strength, build orientation, delamination, weak axis, anisotropic strength, 45 degree printing, strongest orientation]
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
  - https://www.cnckitchen.com/blog/stop-printing-flat-the-45-secret-for-stronger-parts
  - https://www.cnckitchen.com/blog/the-influence-of-extrusion-temperature-on-layer-adhesion
  - https://www.cnckitchen.com/blog/the-influence-of-layer-height-on-the-strength-of-fdm-3d-prints
  - https://www.hubs.com/knowledge-base/how-does-part-orientation-affect-3d-print/
  - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf
  - https://help.prusa3d.com/article/layers-and-perimeters_1748
  - https://www.protolabs.com/resources/design-tips/3d-printing-tolerances/
related: [filament-properties, perimeters-infill-and-strength, printed-fatigue, overhangs-and-print-orientation, shafts-and-bearings, wall-mounting-and-hanging, straps-buckles-and-textile-attachment, key-rings-and-charm-hardware, fdm-layer-height-and-nozzle, fdm-hole-accuracy, fdm-joining-split-prints, printed-part-count]
updated: 2026-10-10
---

# Layer anisotropy and print orientation for strength

An FDM part is a stack of welded layers. Along a layer the load runs through
continuous extruded strands; across layers it runs through the weld. The weld
is weaker and much less ductile — Stratasys Direct: strongest in tension in the
X-Y plane, weakest in Z in both tension and shear — so **orientation is a
strength decision**, not only a support decision. Choose the orientation from
the load path first, then check overhangs ([[overhangs-and-print-orientation]]).

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

- CNC Kitchen, PLA at 0.2 mm layers: 63 MPa flat against 31 MPa standing,
  about 0.5 — "layer adhesion is typically around 50 % of the in-plane
  strength" on a tuned printer.
- Prusament defines a tensile strength anisotropy coefficient
  r = Z strength / X-Y strength: PLA 0.33, PETG 0.38, PC Blend 0.33, and
  PLA High Speed 0.60 (r = 1 would be isotropic).
- Prusament PLA's interlayer adhesion is 17 ± 3 MPa against 57 MPa for the
  filament, about 0.3.
- Hubs: X-Y tensile strength is "typically 4 to 5 times higher" than Z
  (0.2–0.25).
- One study (PLA and ABS, 2018) measured −22 % to −28 % for PLA loaded
  across layers, but **−88 % for ABS** (26.4 → 3.15 MPa) in the orientation
  that pulls layers apart.

The spread (0.12–0.9) is real: it depends on printer, temperature, cooling,
layer time and specimen ([[layer-anisotropy#what-moves-the-layer-weld]]). **Design rule:
without a Z value measured for your filament and settings, assume Z strength
= 0.3 × X-Y** (Prusament's r for PLA and PC Blend); a higher value, such as a
tuned printer's 0.5 for PLA, is used only when it was measured on that
filament and those settings. Never rely on Z elongation above about 1.5 %.

```python
Z_FACTOR = 0.3   # Prusament r for PLA/PC Blend; use a measured value if you have one
assert stress_across_layers <= Z_FACTOR * UTS_XY / SAFETY_FACTOR
```

## Tilt at least 45° when the load cannot lie flat

Measured, PLA, 0.2 mm layers (CNC Kitchen), coupon angle from the bed:

| angle | 0° (flat) | 30° | 45° | 60° | 90° (standing) |
|---|---|---|---|---|---|
| tensile strength | 63 MPa | 44 MPa | 40 MPa | 36 MPa | 31 MPa |

The curve is S-shaped, so small tilts buy little: aim for at least 45°, which
CNC Kitchen measured 27 % stronger than standing and which still prints.

## Orient so layers do not carry the tension

- **Tension:** layers run parallel to the pull; a pull along Z peels layers
  apart (Hubs).
- **Bending:** the extreme fibres carry the stress. Put the bending plane in
  the layer plane, with continuous shell lines along the bend length: a hook,
  lever or clip should lie flat, not stand up.
- **Shear:** layers lie across the shear plane, not along it, so the cut must
  break strands instead of sliding layers (Hubs).
- **Pins and shafts:** print lying down so the strands run along the axis
  (see [[shafts-and-bearings#printed-shaft-or-bought-rod]]). A standing pin
  snaps at a layer line.
- **Snap beams and flexures:** the beam length lies in X-Y; a beam along Z
  breaks at the first deflection ([[snap-fit-design#permissible-strain]]).
- **Pressure vessels, cylinders with internal pressure:** hoop stress runs in
  the layer plane when the axis is vertical; axial stress crosses the layers.
- **Screw bosses and inserts:** pull-out loads along Z tear layers apart;
  add perimeters around the boss rather than infill
  ([[perimeters-infill-and-strength]]).

Wall hooks and brackets, where this decides the part:
[[wall-mounting-and-hanging]].

Strap bars and buckles print flat: [[straps-buckles-and-textile-attachment]].
Keychain and charm loops lie flat for the same reason:
[[key-rings-and-charm-hardware#lay-the-loop-flat-never-across-layers]].

## What moves the layer weld

- **Extrusion temperature** (CNC Kitchen, standing coupons). PLA: 20 MPa at
  190 °C, 37 at 200, 39 at 210, peak 40 at 230, 37 at 250, 32 at 270, against
  ~60 MPa lying. PETG: 18 MPa at 200 °C, 22 at 215, 30 at 230, peak 32 at
  245, 24 at 260, against 55 lying. Both too cold and too hot weaken it.
  "For strength, go to the upper limit and even a bit above."
- **Layer height vs nozzle** (CNC Kitchen): strength suffers once layers
  exceed half the nozzle diameter. At 0.4 mm, 0.3 mm layers kept about half
  the adhesion load, and 0.4 mm layers had essentially none; 0.15 mm was the
  sweet spot, and thinner layers "did not bond better"
  ([[fdm-layer-height-and-nozzle]]).
- **Cooling and extrusion width:** less part cooling and wider lines help;
  layer adhesion peaked around 150 % extrusion width in one test
  ([[perimeters-infill-and-strength#extrusion-width]]).
- **Perimeters, not infill**: "The strength of a model is mostly defined by
  the number of perimeters (not the infill)" (Prusa).
- **Material:** pick one with a higher published r.

## What does not fix it

- **Annealing PLA does not raise layer adhesion.** A tested hook's layer
  adhesion stayed at 42 kg before and after annealing, while in-plane
  strength rose 7.5 % ([[annealing-printed-parts]]).
- **More infill** strengthens a part mostly in-plane; the weld between layers
  is the same weld.

## Orientation also decides accuracy and time

- A vertical cylinder prints concentric and accurate; a horizontal one
  facets (Hubs) ([[fdm-hole-accuracy]]).
- Protolabs: vertically oriented parts can suffer lower layer adhesion and
  errors that accumulate over the height, while horizontal builds are more
  accurate.
- Fewer layers is faster. Hubs' example: about 100 layers for a horizontal
  build against about 300 vertical at 100 µm.

## When no single orientation works

Split the part so each piece prints in its own best orientation. Stratasys
Direct lists sectioning to preserve fragile features and "build them in an
orientation that produces a stronger part", then bond them back
([[fdm-joining-split-prints]], [[printed-part-count#when-you-do-split]]).

## Fatigue treats a flat print as nearly isotropic

For PLA printed flat on the bed, one fatigue study found that raster angle
could be neglected with little loss of accuracy ([[printed-fatigue]]). That is
in-plane orientation only; it does not cover loading across layers.

## Checks

- Name the load direction relative to the layers for every loaded feature.
- A stress across layers uses the Z factor, not the X-Y strength.
- A feature whose strength depends on Z elongation (a snap hook along Z, a
  press fit that stretches layers) is redesigned or reoriented.
