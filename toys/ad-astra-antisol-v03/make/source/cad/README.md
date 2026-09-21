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
| `parts/` | one module per physical part, plus `markings.py`, the per-planet surface table, and the two outline atlases: `atlas.py` for Earth's coastlines and `mars_atlas.py` for Mars's albedo map |
| `assemblies/product.py` | where every occurrence sits on the board |
| `production.py` | writes one production STEP per occurrence into the product tree |
| `snap_frames.py` | writes the two canonical frames: the hero `iso.png` and the three-state `signature.png` |
| `world_views.py` | writes one world on its own, and its two armies side by side, at that world's own named frames |
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
| `measure/mars_atlas_resolution.py` | the same arithmetic on Mars's atlas, at Mars's smaller globe |
| `measure/mars_surface_scan.py` | classifies the built Mars solids point by point: is Syrtis a wedge, does the belt fuse, is the cap rim ragged |
| `measure/seated_clearance.py` | measures whether a world seated on a star or in a corona well shares volume with the flames or tongues |
| `measure/filament_value.py` | measures Mars's three filaments by value, sealed and as the review renderer shows them |
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
| `part_world_mars_*` | 2 | Ø33.87 x 17.72 | disc, numeral, globe, two markings — albedo drawn from outline rings, not round patches, and polar caps whose rims are broken by lobes |
| `part_world_venus_*` | 2 | Ø33.87 x 19.53 | disc, numeral, globe, one marking |
| `part_world_earth_*` | 2 | Ø33.87 x 19.70 | disc, numeral, globe, three markings — drawn from coastline outlines rather than round patches |
| `part_world_neptune_*` | 2 | Ø33.87 x 24.89 | disc, numeral, globe, two markings |
| `part_world_uranus_*` | 2 | Ø33.87 x 25.02 | disc, numeral, globe, one marking |
| `part_world_saturn_*` | 2 | Ø33.87 x 29.00 | disc, numeral, globe, bands, ring |
| `part_world_jupiter_*` | 2 | Ø33.87 x 29.97 | disc, numeral, globe, bands, spot |

42 printed parts, 24 distinct printed geometries, 104 single-colour production
solids, 13 filaments.

## Earth and Mars are the two worlds drawn from outlines

Six of the eight planets wear a union of round patches, because that is what an
albedo map of smooth plains, a cloud pattern, a band system or a storm actually
is. Earth and Mars are the exceptions, and they are the exceptions for the same
reason: they are the only two worlds in this set whose real surfaces carry a
shape a player already knows by heart. Earth's is its coastlines; Mars's is the
dark triangle of Syrtis Major, which every telescope owner has drawn since
1659. Drawn as circles, Earth reads as a mottled marble rather than as the
planet, and Mars loses the one feature on it anybody can name. No other world
here has such a shape — nobody carries Jupiter's band spacing or Venus's cloud
Y in their head as an outline — so for the other six a union of round patches
is not a compromise, it is the honest answer.

Both are built the same way: closed longitude/latitude rings, swept into the
globe as the radial cone through each ring and trimmed to the same 1.20 mm
inlay depth the rest of the set uses. Earth's `land`, `dryland` and `ice` rings
are in `parts/atlas.py`; Mars's `albedo` rings and its two caps' rim-breaking
lobes are in `parts/mars_atlas.py`. The globe's outer surface stays a true
sphere on both and nothing an outline adds faces downward.

At Earth's Ø16.70 one degree of arc is 0.1457 mm against a 0.40 mm nozzle;
at Mars's Ø14.72 it is 0.1285 mm, so every outline on Mars is the finer of the
two. `measure/earth-atlas-resolution.md` and `measure/mars-atlas-resolution.md`
measure every ring, channel, join and subtracted strip against that nozzle.
Earth cost one simplification — the Australian outback's north-west corner, by
0.33 mm — and no landmass was dropped. Mars cost four moved vertices, three of
them closing threads of red too narrow to print where the southern belt's rings
are meant to fuse and one opening a channel that was too narrow to keep, none
of them on an outline the eye reads; Sinus Sabaeus, the thinnest feature on the
globe, is carried vertex for vertex at a measured narrowest width of 0.85 mm.
Nothing was dropped silently on either, and nothing the reference does not show
was added to Mars: no craters, no Olympus Mons, no Valles Marineris, no fourth
filament.

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

The same helper writes eight frames of the two Mars pieces.
`mars-<side>-syrtis.png` at azimuth 70°, which puts Syrtis Major in the middle
of the picture, and `mars-<side>-opposite.png` at azimuth 250°, the far face
where the southern belt crosses the middle and no Syrtis appears at all, both
at 12° of elevation; `mars-<side>-polar.png`, straight down that piece's own
north pole, which is where the broken cap rim can actually be judged; and
`mars-pair-<face>.png`, the two pieces side by side under one camera, for the
same reason the Earth pair frames exist.

## Rebuild

```bash
CADGEN_WARM=1 python "$(workshop skills path)/cad/scripts/gen" \
  <project>/antisol.step.py <project>/part_world_earth_sol.step.py --write

CADGEN_WARM=1 python "$(workshop skills path)/cad/scripts/verify_project" <project> \
  --strict-fit --print-gates --nozzle 0.4 \
  --report <project>/measure/verification-pipeline.md

python <project>/production.py <product-root>/parts

python <project>/snap_frames.py "$(workshop skills path)/cad/scripts" <project>/snap
python <project>/world_views.py <scratch>/worlds mars

python <project>/measure/atlas_resolution.py > <project>/measure/earth-atlas-resolution.md
python <project>/measure/mars_atlas_resolution.py > <project>/measure/mars-atlas-resolution.md
python <project>/measure/mars_surface_scan.py     > <project>/measure/mars-surface.md
python <project>/measure/seated_clearance.py      > <project>/measure/seated-piece-clearance.md
python <project>/measure/filament_value.py        > <project>/measure/filament-value.md
python <project>/measure/ice_cap_scan.py     > <project>/measure/earth-ice-cap.md
```

## What the two atlases do not draw

Earth's rings are a stylised silhouette, not a survey coastline. Central
America is one broad land bridge, and Japan, New Zealand, the Indonesian and
Philippine arcs, the British Isles as a shape of their own, the Mediterranean's
islands and Antarctica are not drawn. Every one of them is listed with its
reason in `measure/earth-atlas-resolution.md`; most are narrower than the
nozzle at this globe size.

Mars's rings are the classical albedo map at the accuracy an eyepiece sketch
has, not spacecraft mapping — which is the right level, because the reference
is a distant view. No crater is drawn: at this radius a crater reads as a print
defect rather than as a crater. No Olympus Mons or Tharsis volcano, because
those are relief rather than albedo and a raised cone would be the one thing on
this globe that breaks its outer sphere. No Valles Marineris, no Hellas, no
bright beige highlands, and no third filament beyond the set's `red`,
`cocoa_brown` and `white`. Each omission is listed with its reason in
`measure/mars-atlas-resolution.md`. Mars is also the world the disc eats most:
its Ø14.72 globe is sunk 2.00 mm and cut at the disc top, which removes about
14% of the sphere and with it nearly all of the south polar cap, so the
southern cap is barely visible on either army.

Nothing was dropped silently on either world.

The small dryland rings — inner Asia at seven vertices, the American southwest
at six — are simple polygons at this size and read as such; the atlas draws
deserts as blocks and coastlines as coastlines. The filament values are
discussed below.

## Two colour notes, and what a cold reader saw

`cocoa_brown` is #8E3C06 and `red` is #FF0000, and on the sealed channels the
brown is the darker of the two — relative luminance 0.0900 against 0.2126.
**The images in `snap/` show the opposite, and that is the renderer, not the
part.** `cad/scripts/render_review` applies a linear-to-sRGB encode to channels
that are already sRGB, so every colour in those images is encoded twice; a
double encode lifts a mid-tone hard and cannot lift a channel already at 1.0,
so `cocoa_brown` is displayed as #C5852A at luminance 0.2884 while `red` does
not move. `measure/filament-value.md` measures both. The shop and the listing
read the sealed channels, so the printed piece has the albedo darker.

Even sealed, the margin is thin: the contrast ratio is only **1.88:1**, under
the 3:1 at which a value difference reads as lightness rather than as hue, and
the brown is the warmer and yellower of the pair — so at a glance the markings
read as a change of colour more than as darkness. Mars is required to keep
exactly `red`, `cocoa_brown` and `white`, so this is stated rather than fixed.
The same holds for Earth: `beige` is #F7E6DE, a very pale warm white, so at
Ø16.70 the dryland patches sit close in value to the `white` ice and read as
light grey rather than as sand.

The canonical renders were given to an independent critic who had not been told
what the product is. Shown the Mars pieces cold they picked one dark region out
and gave it a shape — "a shield or blunt arrowhead, flat across the top-left,
tapering to a rounded point at the bottom". That is Syrtis Major. They read the
southern maria as "a chain of three or four joined lozenges running horizontally
right across the body — a belt", and both cap rims as "irregular and angular,
like torn paper, not a drawn circle". They did not name the planet from the
markings, and said so; at Ø14.72 with three filaments and no relief — and with
the albedo shown to them lighter than the globe rather than darker — that is the
honest ceiling. One requirement they could not judge: whether the north cap is
the larger and more irregular of the two. No render shows the south cap, because
the disc's cut takes almost all of it; the asymmetry is real and measured in
`measure/mars-atlas-resolution.md`, but it is not visible on the finished piece
and is not claimed to be. Their three structural findings — a cone through a sphere, the
ring through its base, a disc straddling two terrain levels — are all answered
by `measure/seated-piece-clearance.md` and by `inspect interfere`, which reports
`clashCount 0` on the whole 182-occurrence assembly. Section 11, item 17 of
`antisol_spec.md` records all of it.

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
