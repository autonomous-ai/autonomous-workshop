---
title: Published FDM design rule tables
tags: [fdm, design-rules, minimum-wall, minimum-feature, tolerance, clearance, pin, hole, emboss, engrave, bridge]
aliases: [design guidelines, design for additive manufacturing, dfam, fdm rules of thumb, printing limits, service bureau guidelines]
sources:
  - https://mit.ek.dk/media/s4sf4t3k/3d_printing_design_rules-ultimaker.pdf (3D Hubs, "Design rules for 3D printing" poster)
  - https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/
  - https://www.hydraresearch3d.com/design-rules
  - https://forgelabs.com/design-guides/fdm
  - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf (Stratasys Direct, FDM design guidelines)
  - https://formlabs.com/blog/fdm-3d-printing-design-guide/
related: [wall-thickness-and-hollowing, fdm-minimum-feature-sizes, fdm-hole-accuracy, fit-derivation, overhangs-and-print-orientation, resin-printing-design, tolerance-stack-up]
updated: 2026-09-23
---

# Published FDM design rule tables

Several service bureaus and printer makers publish one-line limits for FDM.
They disagree, because they assume different machines: a desktop 0.4 mm
nozzle, or an industrial Stratasys-class machine with a heated chamber and
soluble support. Use this page to see the spread, pick the conservative end
for a part that must work first time, and derive the project value from the
nozzle rather than copying a row ([[wall-thickness-and-hollowing#derive-the-wall-from-the-nozzle]]).

## Side by side

| rule | 3D Hubs poster (desktop FDM) | Hydra Research (desktop FFF, 0.45 mm line) | Forge Labs (industrial FDM) | Stratasys Direct (industrial FDM) | Formlabs comparison table |
|---|---|---|---|---|---|
| supported wall | 0.8 mm | > 0.9 mm (2 × line width) | 1 mm | 1.02 mm at 0.25 mm slices (recommended; see below) | 0.8 mm |
| unsupported wall | 0.8 mm | — | 1 mm | — | 0.8 mm |
| max overhang without support | 45° | < 50° from vertical | — | — | — |
| horizontal bridge | 10 mm | < 10 mm | — | — | — |
| min hole | Ø2 mm | > Ø2 mm | 0.5 mm | holes "fractionally undersized"; ream when tight | — |
| clearance, connecting / moving parts | 0.5 mm | ~0.2 mm loose, ~0.1 mm tight | 0.5 mm min clearance, 0.1 mm min press fit, 0.6 mm min hinge gap | Z: one slice; XY: one extrusion width (printed assembled) | — |
| min feature | 2 mm | > 1.8 mm or 4 × line width | — | columns down to 0.48 mm with custom settings | — |
| min pin diameter | 3 mm | > Ø1.8 mm (4 × line width) | 3 mm | — | 3 mm (vertical wire) |
| embossed / engraved detail | 0.6 mm wide, 2 mm high | emboss > 0.9 mm wide; engrave > 0.5 mm wide (depth/height limits below) | deboss 1 mm wide × 0.3 mm deep; emboss 1 mm wide × 0.5 mm | text: 16 pt bold on top/bottom, 10 pt bold on walls | 0.6 mm wide, 2 mm high |
| tolerance | ±0.5 % (lower limit ±0.5 mm) | — | ±0.3 % (min ±0.25 mm) | machine tolerance | — |
| min gap | — | — | 0.5 mm | — | — |
| fillets | — | > Ø1 mm | — | outer R = inner R + wall | — |
| base corners | — | R > 4 mm | — | — | — |
| base chamfer | 45° chamfer or radius on bed edges (Hubs article) | ~0.3 mm (first layer + one layer) | — | — | — |

Hydra Research's emboss/engrave limits, by face:

| face | emboss | engrave |
|---|---|---|
| horizontal | > 0.9 mm wide, < 0.9 mm out | > 0.5 mm wide, < 0.9 mm deep |
| vertical | > 0.9 mm wide, < 2 mm high | > 0.5 mm wide, < 2 mm deep |

Stratasys Direct's wall table (slice thickness → wall):

| slice (mm) | single-contour minimum (brittle) | recommended minimum |
|---|---|---|
| 0.18 | 0.36 | 0.71 |
| 0.25 | 0.50 | 1.02 |
| 0.33 | 0.66 | 1.32 |

"Building multiple layers while using the minimum contour width will cause
the feature to be brittle": the recommended column is two contours.

## Reading the disagreements

- **Walls converge on two extrusion widths.** 0.8 mm (Hubs, Formlabs) is
  2 × 0.4; 0.9 mm (Hydra) is 2 × 0.45; Stratasys's recommended column is
  2 × its contour width. That is the rule; the millimetre figure follows from
  the nozzle and line width.
- **Pins split into two camps.** 3 mm (Hubs, Forge Labs, Formlabs) is a
  "prints reliably at any height" figure; 1.8 mm (Hydra) is the geometric
  floor of four line widths. The Hubs article adds that vertical pins below
  5 mm need care: a thin tall pin wobbles as it is printed.
- **Bridges: 10 mm vs "under 5 mm".** The Hubs poster allows 10 mm; the Hubs
  article says sag or support marks are always present unless the bridge is
  under 5 mm. So 10 mm is *printable*, 5 mm is *clean*. See
  [[fdm-bridging-and-sacrificial-layers]].
- **Clearance: 0.1–0.2 mm vs 0.5 mm.** The small figures (Hydra) assume a
  tuned desktop printer and a known pair of parts; 0.5 mm (Hubs, Forge Labs)
  is a bureau's blind value for parts from an unknown machine. In this
  repository clearance comes from `cadfits` ([[fit-derivation]]).
- **Tolerance is proportional with a floor.** ±0.5 % with a ±0.5 mm floor
  (Hubs) means every dimension under 100 mm is ±0.5 mm; ±0.3 % with a
  ±0.25 mm floor (Forge Labs) is an industrial machine.

## How to use them

```python
LINE_W = 0.45                                  # from the slicer profile, not the nozzle label
MIN_WALL = 2 * LINE_W                          # every table above reduces to this
MIN_PIN_D = max(4 * LINE_W, 3.0) if TALL else 4 * LINE_W
assert BRIDGE_SPAN <= 10.0, "longer than any published bridge limit"
assert BRIDGE_SPAN <= 5.0 or not VISIBLE_UNDERSIDE, "a visible bridge over 5 mm will sag"
```

A value outside every column is a design risk to record, not a rule
violation: the tables are guides, not gates. The gates that do measure are
`check_thickness` and `check_overhang`.

The resin counterpart of these tables is [[resin-printing-design]]; a
tolerance that several dimensions share is summed in [[tolerance-stack-up]].
