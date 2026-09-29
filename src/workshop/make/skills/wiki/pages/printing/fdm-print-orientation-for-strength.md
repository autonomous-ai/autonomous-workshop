---
title: Print orientation for strength
tags: [orientation, strength, anisotropy, layer-adhesion, load-path, tensile, shear, bending, temperature]
aliases: [layer adhesion, z strength, anisotropic strength, build orientation, delamination, 45 degree printing, strongest orientation]
sources:
  - https://www.cnckitchen.com/blog/stop-printing-flat-the-45-secret-for-stronger-parts
  - https://www.cnckitchen.com/blog/the-influence-of-extrusion-temperature-on-layer-adhesion
  - https://www.cnckitchen.com/blog/the-influence-of-layer-height-on-the-strength-of-fdm-3d-prints
  - https://www.hubs.com/knowledge-base/how-does-part-orientation-affect-3d-print/
  - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf
  - https://help.prusa3d.com/article/layers-and-perimeters_1748
  - https://www.protolabs.com/resources/design-tips/3d-printing-tolerances/
related: [overhangs-and-print-orientation, printed-part-count, fdm-layer-height-and-nozzle, shafts-and-bearings, fdm-joining-split-prints]
updated: 2026-09-23
---

# Print orientation for strength

An FDM part is a stack of welded strands. Along a strand it is nearly the
bulk plastic; across the layers it is only as strong as the weld. Stratasys
Direct: strongest in tension in the X-Y plane, weakest in the Z direction in
both tension and shear. Choose the orientation from the load path first, then
check overhangs ([[overhangs-and-print-orientation]]).

## How much weaker Z is

Measured, PLA, 0.2 mm layers (CNC Kitchen):

| coupon angle from the bed | tensile strength |
|---|---|
| 0° (flat) | 63 MPa |
| 30° | 44 MPa |
| 45° | 40 MPa |
| 60° | 36 MPa |
| 90° (standing) | 31 MPa |

"Layer adhesion is typically around 50 % of the in-plane strength." The
curve is S-shaped, so small tilts buy little: aim for at least 45°, which is
27 % stronger than standing and still printable.

Figures vary by source. Hubs states XY tensile strength is "typically 4 to 5
times higher" than Z, far worse than CNC Kitchen's ~2× for well-printed PLA.
The spread comes from material and process (below). Design on the measured
~50 % for a tuned printer, and on much less for an unknown one.

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
- **Perimeters, not infill**: "The strength of a model is mostly defined by
  the number of perimeters (not the infill)" (Prusa).

## Orient by load

From the Hubs orientation guide:

| load | orient so that | why |
|---|---|---|
| tension | layers run parallel to the pull | a pull along Z peels layers apart |
| bending | continuous shell lines run along the bend length | the outer fibres of a bend see the tension |
| shear | layers lie across the shear plane, not along it | the cut must break strands, not slide layers |

Shafts and pins that bend print lying down, never standing
([[shafts-and-bearings#printed-shaft-or-bought-rod]]). Snap hooks print with
the beam in X-Y ([[joints#latching-and-holding]]).

## Orientation also decides accuracy and time

- A vertical cylinder prints concentric and accurate. A horizontal one
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
