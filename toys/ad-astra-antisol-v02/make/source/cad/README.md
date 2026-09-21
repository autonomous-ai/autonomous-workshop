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
| `parts/` | one module per physical part, plus `markings.py`, the per-planet surface table, and `atlas.py`, Earth's coastline rings |
| `assemblies/product.py` | where every occurrence sits on the board |
| `production.py` | writes one production STEP per occurrence into the product tree |
| `snap_frames.py` | writes the two canonical frames: the hero `iso.png` and the three-state `signature.png` |
| `earth_views.py` | writes one world on its own, and the two Earths side by side, for the Atlantic and Pacific frames |
| `antisol.step.py` | the combined review entry: the whole set in the opening position (not a print target) |
| `part_world_<planet>_<side>.step.py` | one of the sixteen worlds, printed |
| `part_panel_<corner>.step.py` | one of the four board panels, printed |
| `part_belt_cell.step.py` | one asteroid-belt tile, printed twelve times |
| `part_corona_cell.step.py` | one corona cell, printed six times |
| `part_den_plug.step.py` | one star, printed twice |
| `part_orbit_tray.step.py` | one storage tray, printed twice |
| `ref/` | the sealed reference images, copied in |
| `measure/` | round reports, gate reports and the verification pipeline record |
| `measure/atlas_resolution.py` | measures Earth's atlas against the nozzle at globe scale |
| `measure/ice_cap_scan.py` | classifies points around the pole against the built colour bodies |
| `measure/revision_hashes.py` | this run's per-part STEP hashes against the published set |
| `measure/occurrence_geometry.py` | the same comparison by geometry, for the production solids |
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
| `part_world_earth_*` | 2 | Ø33.87 x 19.70 | disc, numeral, globe, three markings — the only world drawn from coastline outlines rather than round patches |
| `part_world_neptune_*` | 2 | Ø33.87 x 24.89 | disc, numeral, globe, two markings |
| `part_world_uranus_*` | 2 | Ø33.87 x 25.02 | disc, numeral, globe, one marking |
| `part_world_saturn_*` | 2 | Ø33.87 x 29.00 | disc, numeral, globe, bands, ring |
| `part_world_jupiter_*` | 2 | Ø33.87 x 29.97 | disc, numeral, globe, bands, spot |

42 printed parts, 24 distinct printed geometries, 104 single-colour production
solids, 13 filaments.

## Earth is the one world drawn from coastlines

Seven of the eight planets wear a union of round patches, because that is what
an albedo map, a cloud pattern or a storm actually is. Earth is the exception.
It is the only world in this set whose real surface has an outline a player
already knows by heart, and as a union of green and beige circles it reads as a
mottled marble rather than as the planet. Its `land`, `dryland` and `ice` are
therefore built from closed longitude/latitude rings in `parts/atlas.py`, swept
into the globe as the radial cone through each ring and trimmed to the same
1.20 mm inlay depth the rest of the set uses. The globe's outer surface stays a
true sphere and nothing an outline adds faces downward.

At Ø16.70 one degree of arc is 0.1457 mm, against a 0.40 mm nozzle.
`measure/earth-atlas-resolution.md` measures every ring, sea channel and
subtracted strip against that. One outline was simplified — the Australian
outback's north-west corner, by 0.33 mm — and no landmass was dropped.

`snap/worlds/` holds eleven frames of the two Earth pieces.
`earth-<side>-atlantic.png` at azimuth −30°, `earth-<side>-pacific.png` at
azimuth 170° and `earth-<side>-eurasia.png` at azimuth 70°, all at 12° of
elevation; `earth-<side>-polar.png`, straight down that piece's own north
pole, which leans at the planet's true obliquity and so is a different camera
for each army; and `earth-pair-<face>.png`, the two pieces side by side under
one camera.

The pair frames exist because the two single frames read, to someone seeing
them cold, as two different maps: at one camera the Sol world tips its north
pole toward the lens and the Anti-Sol world tips it away, which is the
ownership cue doing exactly its job. Side by side that is plainly one cue
inverted, and the continents are plainly the same continents with the same
handedness on both. The polar frames exist because the cap is the one marking
no side view shows properly; `measure/earth-ice-cap.md` measures what they
show. The Eurasia frame exists because neither the Atlantic nor the Pacific
face presents Eurasia: on one it is over the limb and on the other it is the
foreshortened northern rim.

## Rebuild

```bash
CADGEN_WARM=1 python "$(workshop skills path)/cad/scripts/gen" \
  <project>/antisol.step.py <project>/part_world_earth_sol.step.py --write

CADGEN_WARM=1 python "$(workshop skills path)/cad/scripts/verify_project" <project> \
  --strict-fit --print-gates --nozzle 0.4 \
  --report <project>/measure/verification-pipeline.md

python <project>/production.py <product-root>/parts

python <project>/snap_frames.py "$(workshop skills path)/cad/scripts" <project>/snap
python <project>/earth_views.py <scratch>/worlds earth

python <project>/measure/atlas_resolution.py > <project>/measure/earth-atlas-resolution.md
python <project>/measure/ice_cap_scan.py     > <project>/measure/earth-ice-cap.md
```

## What the atlas does not draw

The rings are a stylised silhouette, not a survey coastline. Central America is
one broad land bridge, and Japan, New Zealand, the Indonesian and Philippine
arcs, the British Isles as a shape of their own, the Mediterranean's islands
and Antarctica are not drawn. Every one of them is listed with its reason in
`measure/earth-atlas-resolution.md`; most are narrower than the nozzle at this
globe size. Nothing was dropped silently.

Two colour notes. `beige` is `#F7E6DE`, which is a very pale warm white: on a
Ø16.70 globe the dryland patches sit close in value to the `white` ice, and in
a flat-shaded render they read as light grey rather than as sand. Both are
filaments the set already used and the correction was told to keep them. And
the small dryland rings — inner Asia at seven vertices, the American southwest
at six — are simple polygons at this size and read as such; the atlas draws
deserts as blocks and coastlines as coastlines.

## The colour split checks its own answer

A marking is cut out of the globe by a boolean, and this kernel's booleans are
not bit-reproducible between processes: the same source built twice can give a
colour body a few hundredths of a cubic millimetre apart, and once in a while
one of those answers is a body the final `inspect validate` gate refuses. The
printed parts are not affected — all twenty-four are reproducible, because a
printed world is a disc fused to a ball and never touches a marking — but the
colour bodies are.

So `parts/world.py` does not accept the kernel's first answer. It measures it:
the pieces must add back up to the globe they came from, none of them may
cross itself, and every one must pass `BRepCheck_Analyzer` with the same flag
the gate uses. When one fails, the markings are widened by a graded fraction
of a degree, and then the whole pattern is turned a fraction of a degree about
the planet's own axis, until an answer passes all three. What this project
guarantees is not an exact volume; it is that the answer shipped was checked.

## What this project does not establish

Nothing here demonstrates a physical print, dimensional accuracy on a real bed,
material behaviour, colour against real filament, or a game played by people.
Motion verification is switched off for this run and is recorded as unverified,
not as passed. The clearances, wall thicknesses and overhang margins below are
measured on the exact CAD solids and predicted for the printer named above.
