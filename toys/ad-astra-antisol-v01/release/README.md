# Antisol — CAD project

Dou Shou Qi, unchanged, played with the eight planets ranked by their real
measured diameters. Sixteen worlds, a four-panel board, twelve asteroid-belt
tiles, two stars with their coronas, and two storage trays.

**Bed: --bed 200x200x200.** Nozzle 0.4 mm, layer 0.2 mm, PLA, no supports, no
hardware, no assembly step. Every part prints flat on its own footprint.

## File map

| file | what it is |
|---|---|
| `antisol_spec.md` | the design contract: every dimension, where it came from, and what it is for |
| `params.py` | every dimension in the set, in one block |
| `bool3d.py` | solid-wise booleans that check their own arithmetic |
| `colors.py` | filament colour, sealed as the sRGB the shop shows |
| `features/` | reusable feature builders: glyphs, surface patches, flames, plates, rubble |
| `parts/` | one module per physical part, plus `markings.py`, the per-planet surface table |
| `assemblies/product.py` | where every occurrence sits on the board |
| `production.py` | writes one production STEP per occurrence into the product tree |
| `antisol.step.py` | the combined review entry: the whole set in the opening position (not a print target) |
| `part_world_<planet>_<side>.step.py` | one of the sixteen worlds, printed |
| `part_panel_<corner>.step.py` | one of the four board panels, printed |
| `part_belt_cell.step.py` | one asteroid-belt tile, printed twelve times |
| `part_corona_cell.step.py` | one corona cell, printed six times |
| `part_den_plug.step.py` | one star, printed twice |
| `part_orbit_tray.step.py` | one storage tray, printed twice |
| `ref/` | the sealed reference images, copied in |
| `measure/` | round reports, gate reports and the verification pipeline record |
| `snap/` | the canonical final render family and the signature review. `iso.png` is the
whole set at the Wish's fixed frame, 35 degrees azimuth and 22 degrees elevation;
`signature.png` is the opening, midgame and endgame positions side by side at one
higher isometric, because at 22 degrees the far ranks foreshorten into each other |

## Print table

| part | prints | size mm | filaments |
|---|---:|---|---|
| `part_panel_southwest` | 1 | 116 x 152 x 9.00 | dark_gray |
| `part_panel_southeast` | 1 | 152 x 152 x 9.00 | dark_gray |
| `part_panel_northwest` | 1 | 116 x 188 x 9.00 | dark_gray |
| `part_panel_northeast` | 1 | 152 x 188 x 9.00 | dark_gray |
| `part_belt_cell` | 12 | 33.50 x 33.50 x 6.00 | cocoa_brown |
| `part_corona_cell` | 6 | 33.50 x 33.50 x 10.00 | orange (Sol) / cyan (Anti-Sol) |
| `part_den_plug` | 2 | 36.00 x 36.00 x 24.00 | sunflower_yellow + orange (Sol) / black + cyan (Anti-Sol) |
| `part_orbit_tray` | 2 | 164 x 88 x 6.00 | gray |
| `part_world_mercury_*` | 2 | Ø33.87 x 16.78 | disc, numeral, globe, one marking |
| `part_world_mars_*` | 2 | Ø33.87 x 17.72 | disc, numeral, globe, two markings |
| `part_world_venus_*` | 2 | Ø33.87 x 19.53 | disc, numeral, globe, one marking |
| `part_world_earth_*` | 2 | Ø33.87 x 19.70 | disc, numeral, globe, three markings |
| `part_world_neptune_*` | 2 | Ø33.87 x 24.89 | disc, numeral, globe, two markings |
| `part_world_uranus_*` | 2 | Ø33.87 x 25.02 | disc, numeral, globe, one marking |
| `part_world_saturn_*` | 2 | Ø33.87 x 29.00 | disc, numeral, globe, bands, ring |
| `part_world_jupiter_*` | 2 | Ø33.87 x 29.97 | disc, numeral, globe, bands, spot |

42 printed parts, 24 distinct printed geometries, 104 single-colour production
solids, 13 filaments.

## Rebuild

```bash
CADGEN_WARM=1 python "$(workshop skills path)/cad/scripts/gen" \
  <project>/antisol.step.py <project>/part_world_earth_sol.step.py --write

CADGEN_WARM=1 python "$(workshop skills path)/cad/scripts/verify_project" <project> \
  --strict-fit --print-gates --nozzle 0.4 --unpowered \
  --report <project>/measure/verification-pipeline.md

python <project>/production.py <product-root>/parts
```

## What this project does not establish

Nothing here demonstrates a physical print, dimensional accuracy on a real bed,
material behaviour, colour against real filament, or a game played by people.
Motion verification is switched off for this run and is recorded as unverified,
not as passed. The clearances, wall thicknesses and overhang margins below are
measured on the exact CAD solids and predicted for the printer named above.
