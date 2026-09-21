# Antisol Kronos — CAD project

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
| `parts/` | one module per physical part, plus `markings.py`, the per-planet surface table, and the six surface atlases: `atlas.py` for Earth's coastlines, `mars_atlas.py` for Mars's albedo map, `mercury_atlas.py` for Mercury's smooth plains and Caloris basin, `venus_atlas.py` for Venus's radar highlands and plains, `jupiter_atlas.py` for Jupiter's belt system, its bright zones and the Great Red Spot, and `saturn_atlas.py` for Saturn's five unequal bands, their wave and its bright northern cap |
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
| `ref/` | the reference images, copied in. Twenty are the sealed AI-generated set; `venus-radar-surface.png` is the twenty-first and is different — a supplied photographic dataset image, the Magellan global radar mosaic, and the authority for Venus's globe surface and globe colour |
| `measure/` | round reports, gate reports and the verification pipeline record |
| `measure/atlas_resolution.py` | measures Earth's atlas against the nozzle at globe scale |
| `measure/mars_atlas_resolution.py` | the same arithmetic on Mars's atlas, at Mars's smaller globe |
| `measure/mercury_atlas_resolution.py` | the same arithmetic again on Mercury's, at the smallest globe in the set |
| `measure/mars_surface_scan.py` | classifies the built Mars solids point by point: is Syrtis a wedge, does the belt fuse, is the cap rim ragged |
| `measure/mercury_surface_scan.py` | the same on Mercury: do the plains fuse, is Caloris a rim round a floor, is any gray channel unprintable, are the two armies mirrors |
| `measure/mercury_tone_separation.py` | renders one Mercury piece twice at one camera to measure what a filament change is worth in the canonical images |
| `measure/mercury_facing.py` | every Mercury marking's dot product against the view axis at the two photographed frames, on both armies |
| `measure/venus_atlas_resolution.py` | the same arithmetic on Venus's atlas, plus what the collar buries at 177.36 degrees of obliquity |
| `measure/venus_facing.py` | every Venus province against the view axis, and the offset sweep Aphrodite Terra's placement was decided on |
| `measure/venus_tone_separation.py` | renders one Venus piece twice at one camera to measure what each of its three tones is worth in the canonical images |
| `measure/venus_surface_scan.py` | classifies the built Venus solids point by point: does Aphrodite fuse into one highland, is the pattern still inverted, is anything raised, are the two armies mirrors |
| `measure/venus_saturn_separation.py` | renders Venus and Saturn side by side, now that they share a filament, and answers separately on surface, size and silhouette |
| `measure/saturn_atlas_resolution.py` | every Saturn band width, gap, ring edge and neck against the nozzle, measured along the wave rather than at one longitude, with the filament count and the arithmetic for everything not drawn |
| `measure/saturn_tone_separation.py` | renders one Saturn piece twice at one camera to measure what each band tone and the cap tone are worth against the `yellow` globe |
| `measure/saturn_cap_visibility.py` | compares the two Saturn armies role by role and shows that the north-only cap shows on one and hides on the other because of the lean, not because of a difference in the parts |
| `measure/saturn_ring_unchanged.py` | asks the ring by name: every value in its `params.py` block against the published number, and both ring occurrences on solid count, exact volume and bounding box, because a solid cannot be checked on colour |
| `measure/jupiter_atlas_resolution.py` | every Jupiter belt width, zone width, ring edge and annulus neck against the nozzle, measured along the wave rather than at one longitude |
| `measure/jupiter_facing.py` | the Great Red Spot's oval against the view axis, vertex by vertex, at both photographed frames and the per-world frame, on both armies |
| `measure/jupiter_tone_separation.py` | renders one Jupiter piece twice at one camera to measure what the bright-zone filament is worth against the globe and against the belts |
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
| `part_world_mercury_*` | 2 | Ø33.87 x 16.78 | disc, numeral, globe, three markings — the smooth plains drawn from outline rings, not round patches, and the Caloris basin as a white floor inside a cocoa_brown rim |
| `part_world_mars_*` | 2 | Ø33.87 x 17.72 | disc, numeral, globe, two markings — albedo drawn from outline rings, not round patches, and polar caps whose rims are broken by lobes |
| `part_world_venus_*` | 2 | Ø33.87 x 19.53 | disc, numeral, globe, two markings — the highlands and the plains drawn from the Magellan radar mosaic as outline rings, not round patches, and no cloud pattern of any kind |
| `part_world_earth_*` | 2 | Ø33.87 x 19.70 | disc, numeral, globe, three markings — drawn from coastline outlines rather than round patches |
| `part_world_neptune_*` | 2 | Ø33.87 x 24.89 | disc, numeral, globe, two markings |
| `part_world_uranus_*` | 2 | Ø33.87 x 25.02 | disc, numeral, globe, one marking |
| `part_world_saturn_*` | 2 | Ø33.87 x 29.00 | disc, numeral, globe, three markings — five bands at unequal widths and unequal spacing, none of them a mirror of another, the two widest drawn as outline rings with a 2.5° wave on each boundary and the rest as plain bands; one of the five in `cocoa_brown` and the other four in `sunflower_yellow`; a bright `white` cap above +58° on the north only — and the ring, which is geometry rather than a marking and is unchanged by this revision |
| `part_world_jupiter_*` | 2 | Ø33.87 x 29.97 | disc, numeral, globe, four markings — six belts at their real unequal latitudes, the two widest drawn as outline rings with a 2.5° wave on each boundary; five bright `beige` zones between and beyond them; the Great Red Spot as one 13 by 9° oval; and its `cocoa_brown` collar |

42 printed parts, 24 distinct printed geometries, 13 filaments — the same
thirteen; this revision loads no new spool.

Filaments per world, counting the globe and its markings and not the disc or
the numeral, which every world shares: Earth, Jupiter and Saturn take four;
Mercury, Mars, Venus and Neptune take three; Uranus alone takes two. **Saturn
prints in four — `yellow`, `sunflower_yellow`, `cocoa_brown` and `white` — where
it printed in three**, and it is the one world in this set whose correction
*lowered* its contrast rather than raising it: it used to be a `yellow` globe
with four hard `cocoa_brown` bands, and it is now a `yellow` globe with four
soft `sunflower_yellow` bands, one `cocoa_brown` band kept, and the `white` it
already carried on its ring reused for a bright northern cap. Jupiter prints in
four where it printed in three, because its reference is three-toned and the
build was two-toned: its bright zones were bare globe. Venus prints in three
where it printed in two, and Mercury in three where it printed in two; the
reasons and the measurements are below.

## Earth, Mars, Mercury and Venus are the four worlds drawn from outlines

Four of the eight planets wear a union of round patches or a belt of latitude,
because that is what a cloud pattern, a band system or a storm actually is.
Earth, Mars, Mercury and Venus are the exceptions: they are the four worlds in
this set with a real mapped surface. Three of them carry a shape that can be
checked against a picture — Earth's coastlines, the dark triangle of Syrtis
Major which every telescope owner has drawn since 1659, and the long equatorial
sweep of Aphrodite Terra — and drawn as circles, Earth reads as a mottled
marble rather than as the planet and Mars loses the one feature on it anybody
can name. Mercury carries no such silhouette; its albedo boundaries are soft
and its plains are unnamed. It earns outlines for the other half of the same
argument: on the smallest globe in the set a union of discs reads as a beach
ball, and terrain is the one thing it does not read as. Nobody carries
Jupiter's band spacing in their head as an outline, and a storm in an
atmosphere really is a round patch, so for the other four a union of round
patches and belts of latitude is not a compromise but the honest answer.
Jupiter is the one that has since become a mixture: its four narrow belts are
still plain bands, but its two widest carry outline rings with a wave on each
boundary, and its Great Red Spot is an outline oval rather than a circle union,
because the real spot is half again wider than it is tall and three overlapping
circles read as a lozenge. Neptune's dark spot stays round.

**Venus is the only one of the four drawn from radar rather than from what the
eye would see.** Its surface is under an opaque atmosphere and the Magellan
global mosaic is the only picture of it there is. It used to wear the
Mariner-10 ultraviolet cloud Y — the atmosphere — and this revision swapped
that for the ground underneath, because a cloud pattern and a surface map are
two pictures of two different objects and this world was to show the same
object the other seven show.

All four are built the same way: closed longitude/latitude rings, swept into
the globe as the radial cone through each ring and trimmed to the same 1.20 mm
inlay depth the rest of the set uses. Earth's `land`, `dryland` and `ice` rings
are in `parts/atlas.py`; Mars's `albedo` rings and its two caps' rim-breaking
lobes are in `parts/mars_atlas.py`; Mercury's seven plains and the two
concentric rings of its Caloris basin are in `parts/mercury_atlas.py`; Venus's
seven highland provinces and three lowland plains are in
`parts/venus_atlas.py`. The globe's outer surface stays a true sphere on all
four and nothing an outline adds faces downward.

At Earth's Ø16.70 one degree of arc is 0.1457 mm against a 0.40 mm nozzle; at
Venus's Ø16.53 it is 0.1443 mm; at Mars's Ø14.72 it is 0.1285 mm; at Mercury's
Ø13.78 it is 0.1203 mm, so the nozzle is 3.33 degrees of arc there and every
outline on Mercury is the finest of the four. `measure/earth-atlas-resolution.md`,
`measure/mars-atlas-resolution.md`, `measure/mercury-atlas-resolution.md` and
`measure/venus-atlas-resolution.md` measure every ring, channel, join and
subtracted strip against that nozzle.
Earth cost one simplification — the Australian outback's north-west corner, by
0.33 mm — and no landmass was dropped. Mars cost four moved vertices, three of
them closing threads of red too narrow to print where the southern belt's rings
are meant to fuse and one opening a channel that was too narrow to keep, none
of them on an outline the eye reads; Sinus Sabaeus, the thinnest feature on the
globe, is carried vertex for vertex at a measured narrowest width of 0.85 mm.
Mercury cost one: its southern lead plain is drawn at a mean 20 degrees of
angular radius rather than 22 and biased north, because at 22 its southern
boundary ran past the parallel where the seat cone springs and the visible
sphere ends. Its centre did not move, and it now leaves 0.53 mm of visible gray
between the plain and the seat. Venus cost one too, and it is a construction
one rather than a shape one: Aphrodite Terra spans more than 150 degrees of
longitude, which is past the 72-degree half-angle the radial-cone outline tool
will take, so it is swept as two rings overlapping across 28 degrees whose
union is the drawn ring exactly. No vertex of it moved and no width changed,
and `measure/venus-surface.md` confirms the two come out as one fused highland.
Nothing was dropped silently on any of the four, and nothing the reference does
not show was added: no craters on Mars, Mercury or Venus, no Olympus Mons, no
Valles Marineris, no Maxwell Montes, no cloud of any kind on Venus, and no
extra filament anywhere.

Mercury is also the one of the four whose repair was a colour rather than a
shape, and the number is worth carrying here.
`measure/mercury-tone-separation.md` renders one Mercury piece twice at one
canonical camera — once with a region in the candidate filament, once with it
in the globe's own `gray` — so the pixels that move are the patch and nothing
else moves at all. The `dark_gray` the plains used to carry measures 21.8 of
255 luma levels against the globe there, which on a Ø13.78 ball is invisible;
`cocoa_brown` measures 45.5. `black` measures 139.6 and was not taken, because
a black patch on a small gray ball reads as a hole in the print rather than as
terrain. The Caloris floor is `white` at 36.9 against the globe and 114.3
against the rim around it, which is what the third filament buys.

`snap/worlds/` holds six frames of the two Saturn pieces, the world this
revision corrects, plus two pair frames and the four measurement images.
`saturn-<side>-quarter.png` at azimuth −55°, which is the product's own
azimuth, and 20° of elevation — higher than the 12° the inner worlds use,
because this is the one piece in the set whose widest feature is not its disc
and at 12° the ring's ellipse is narrow enough to read as a rim rather than as
a ring in projection. `saturn-<side>-ringplane.png` at azimuth −90° and 0°
elevation, which is exactly along the ring's own plane on both armies: the
ring's normal has no Y component whichever way the piece leans, so a camera on
the Y axis is square to it and the annulus shows edge-on as a single line with
its support web under the low side. That frame is at −90 rather than +90 for
light rather than geometry — both are in the ring plane, both were rendered,
and at +90 the piece falls entirely into its own terminator and the band tones
this revision exists to judge cannot be read at all.
`saturn-<side>-polar.png` is straight down that piece's own north pole, which
leans at the planet's true obliquity and so is a different camera for each
army; it is the frame the bright cap can actually be judged on. And
`saturn-pair-<face>.png` is the two pieces side by side under one camera.
Each earlier revision in this chain wrote its own frames for the world it
corrected and they are not carried forward; the text that cites an Earth,
Venus or Jupiter frame is citing that run's evidence.

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

There is no frame below the equator, on Mars or on any other world, and that
is geometry rather than an omission: every disc is Ø34.00 and every globe is
smaller than that, so a camera under the equator sees the underside of the
disc and almost nothing of the ball. This build rendered one at 25° below the
horizon to check, and that is exactly what it showed. What the southern
hemisphere carries is measured on the solids instead, in
`measure/mars-surface.md`.

The Earth frames named above belong to the coastline revision and are not
carried in this tree: `parts/atlas.py` and `measure/earth-atlas-resolution.md`
are Earth's evidence here, and Earth's geometry is untouched by this
revision. `FRAMES["earth"]` is kept so the frames can be rewritten from this
project at any time.

It writes eight frames of the two Mercury pieces on the same pattern.
`mercury-<side>-caloris.png` at azimuth −50°, the longitude the basin was
placed on, and `mercury-<side>-opposite.png` at azimuth 130°, the far face
where the three southern plains run together into one region and no Caloris
appears at all, both at 20° of elevation; `mercury-<side>-polar.png`, straight
down that piece's own north pole, which at Mercury's 0.03° of obliquity is very
nearly the piece's own top view; and `mercury-pair-<face>.png`, the two pieces
side by side under one camera.

Venus gets ten, and one of them is unlike anything else in the set.
`venus-<side>-aphrodite.png` at azimuth −46° puts Aphrodite Terra square in the
middle of the picture; `venus-<side>-beta_phoebe.png` at azimuth +164° is the
face opposite it, where Beta and Phoebe Regio sit with Guinevere Planitia
beside them and Aphrodite is behind the globe at −0.76 against the view axis;
both at 12° of elevation. Both azimuths were swept rather than read off the
atlas, because on this world an azimuth is not a Venusian longitude — the
177.36° obliquity turns the map over before the camera sees it.
`measure/venus-facing.md` is that sweep.

Then **two** polar frames, and the reason is the obliquity again.
`venus-<side>-polar.png` is straight down this piece's own north pole, which at
177.36° means 87° *below* the horizon: the camera is under the board and the
picture is the underside of the disc, with no part of the globe in it. That
frame is kept precisely because it is the proof of which way up this world is.
`venus-<side>-south-polar.png` is the one that shows the pole region of the
globe — Lada Terra, Lavinia Planitia, Themis and Alpha Regio, with Aphrodite on
the limb — and on Venus that is the *south* pole. And
`venus-pair-<face>.png`, the two armies side by side under one camera, for the
same reason the Earth and Mars pairs exist.

## Saturn is the quiet planet, and this revision makes it quiet

Every other correction in this chain added something. This one takes something
away, and the reason is in `ref/saturn-sol.png`: it is the softest image in the
reference set. The globe runs cream to pale tan, the bands are wide and
soft-edged and low in contrast, the strongest of them is barely darker than its
neighbours, and the northern part of the globe is lighter than the southern.
The build this corrects wore four `cocoa_brown` bands each exactly 12° wide, at
−51/−39, −21/−9, 9/21 and 39/51: equal width, equal spacing, perfect mirror
symmetry, in the highest-contrast pairing the palette offers. It read as a
hard-striped gold ball. Saturn stands on the board next to Jupiter, which is
loud on purpose, and the contrast between the two pieces is worth keeping.

Three things changed, and nothing else on the piece did.

**The contrast came down.** `cocoa_brown` stopped being Saturn's band colour.
The four light bands are `sunflower_yellow` #FFB549, a genuine mid tone between
the `yellow` #FFD834 globe and the dark browns, already loaded for the Sol star
and for Venus's globe, so it costs no new spool. What that is worth was
measured rather than assumed, the same two-render way the rest of this set
uses: **9.4** of 255 luma levels against the globe, the smallest separation
this project has ever committed to, and below the 21.8 it rejected on Mercury
as invisible. It reads here for the two reasons Venus's `beige` reads at 20.2 —
area and hue. Saturn's bands cover about 102,000 pixels of a 900-pixel frame
where Mercury's plains were patches a few millimetres across, and
`sunflower_yellow` is an amber against a green-yellow, so the boundary carries
a hue step luma does not count. The Wish's fallback, `beige`, was measured
beside it at **10.1** — seven tenths of a level better, which is not a
difference — and was not taken. `measure/saturn-tone-separation.md` is all of
it.

**One band is still `cocoa_brown`.** The widest, at −14/−30, and only that one.
It measures 39.5 against the globe and 34.7 against the light bands, which sits
between the 33.5 this set accepted on Venus's lowlands and the 45.5 it accepted
on Mercury's plains, and it covers under a tenth of the marked area on the
piece. That is the single band the reference lets you notice.
`snap/worlds/saturn-dark-band-kept.png` and `-dropped.png` are the same piece
with and without it, so the "without dominating" half of that judgement is a
picture rather than a claim.

**The bands stopped being regular, and the north got lighter.** Five bands, not
four: +46/+55, +18/+33, +2/+10, −14/−30 and −38/−50, which are 9, 15, 8, 16 and
12 degrees wide, at five different spacings, with no pair a mirror of another.
The two widest carry a 2.5° wave on each boundary — the Earth lesson about
exact circles of latitude, applied here as it was on Jupiter, in six longitude
sectors that abut on exact radial planes. The three narrow ones stay plain
bands, because at 8 to 12 degrees a wave eats the band. And above +58 there is
a bright `white` cap, the lightest tone the piece already carries: the
reference brightens toward the north pole, and the ring and the northern globe
are the same cream in it. The cap has no lobed rim. That was deliberate: the
Earth lesson about lids is about a small bright cap on a dark globe, and this
is a wide soft brightening on an already light one, where an exact parallel is
what the reference shows. It measures 16.0 against the globe, which is *below*
the 21.8 this set called invisible on Mercury — the brightness it appears to
have in the renders is the specular highlight sitting on the pole the piece
leans toward the light, not the tone step.

**What could not be done.** A flush inlay has a hard edge and there is no way
to make it soft. The reference's bands fade into one another and this piece's
cannot: every boundary on it is a colour change at a line. Lowering the
contrast is the available substitute for softening the edge, which is why the
filament mattered more than the wave. That is the real limitation of this
correction and it is written down rather than worked around.

**The ring did not move, and that is asked by name rather than inferred.**
`RING_INNER_D`, `RING_OUTER_D`, `RING_THICKNESS`, `RING_GLOBE_BITE`,
`RING_WEB_SECTORS`, `RING_WEB_INNER_R`, `RING_WEB_OVERLAP`, `RING_WEB_DROP` and
`RING_WEB_SLOPE` are all exactly where the published set left them.
`measure/occurrence-geometry.md` proves nothing *outside* the two Saturn pieces
moved, which is the wrong question for the ring — the ring is inside them — so
`measure/saturn-ring-unchanged.md` asks it directly: both ring occurrences come
out as one solid each at 574.192167 and 574.192096 mm³ in an unmoved bounding
box, identical to the published set, and so do the disc and the four numeral
strokes. It is the one feature on this piece that already worked, it is
what `LADDER_CONSTANT` was solved against, and it carries the whole set's size
ladder.

**And nothing was added.** No hexagonal polar vortex, no storms, no spokes in
the ring, no ring divisions, no shadow of the ring on the globe. Each was
considered and each was rejected on arithmetic rather than on taste; the
hexagon's is worth having here, because it is real and it is at the pole this
piece is looked at from. It spans about 29,000 km, which is 28.5° of arc and
6.47 mm on this globe, so the figure would fit — but its visible edge is a
jet-stream boundary a few hundred kilometres wide, 0.11 mm at the most generous
reading, a quarter of one nozzle width, where the nozzle needs 1,792 km. Drawn
at the width the printer can lay down it would be four times too fat and would
read as a moulding line round the pole. `measure/saturn-atlas-resolution.md`
carries that and the rest.

## Rebuild

```bash
CADGEN_WARM=1 python "$(workshop skills path)/cad/scripts/gen" \
  <project>/antisol.step.py <project>/part_world_earth_sol.step.py --write

CADGEN_WARM=1 python "$(workshop skills path)/cad/scripts/verify_project" <project> \
  --strict-fit --print-gates --nozzle 0.4 \
  --report <project>/measure/verification-pipeline.md

python <project>/production.py <product-root>/parts

python <project>/snap_frames.py "$(workshop skills path)/cad/scripts" <project>/snap
python <project>/world_views.py <scratch>/worlds saturn \
  "$(workshop skills path)/cad/scripts" <project>/snap/worlds
python <project>/world_views.py <scratch>/worlds mars
python <project>/world_views.py <scratch>/worlds mercury
python <project>/world_views.py <scratch>/worlds venus \
  "$(workshop skills path)/cad/scripts" <project>/snap/worlds

python <project>/measure/atlas_resolution.py > <project>/measure/earth-atlas-resolution.md
python <project>/measure/mars_atlas_resolution.py > <project>/measure/mars-atlas-resolution.md
python <project>/measure/mars_surface_scan.py     > <project>/measure/mars-surface.md
python <project>/measure/seated_clearance.py      > <project>/measure/seated-piece-clearance.md
python <project>/measure/filament_value.py        > <project>/measure/filament-value.md
python <project>/measure/ice_cap_scan.py     > <project>/measure/earth-ice-cap.md
python <project>/measure/mercury_atlas_resolution.py > <project>/measure/mercury-atlas-resolution.md
python <project>/measure/mercury_surface_scan.py     > <project>/measure/mercury-surface.md
python <project>/measure/mercury_facing.py           > <project>/measure/mercury-facing.md
python <project>/measure/mercury_tone_separation.py "$(workshop skills path)/cad/scripts" \
    > <project>/measure/mercury-tone-separation.md

python <project>/measure/venus_atlas_resolution.py > <project>/measure/venus-atlas-resolution.md
python <project>/measure/venus_facing.py           > <project>/measure/venus-facing.md
python <project>/measure/venus_surface_scan.py     > <project>/measure/venus-surface.md
python <project>/measure/venus_tone_separation.py "$(workshop skills path)/cad/scripts" \
    > <project>/measure/venus-tone-separation.md
python <project>/measure/venus_saturn_separation.py "$(workshop skills path)/cad/scripts" \
    > <project>/measure/venus-saturn-separation.md

python <project>/measure/saturn_atlas_resolution.py > <project>/measure/saturn-atlas-resolution.md
python <project>/measure/saturn_tone_separation.py "$(workshop skills path)/cad/scripts" \
    > <project>/measure/saturn-tone-separation.md
python <project>/measure/saturn_cap_visibility.py "$(workshop skills path)/cad/scripts" \
    > <project>/measure/saturn-cap-visibility.md

python <project>/measure/occurrence_geometry.py <published>/assembled.step > was.json
python <project>/measure/occurrence_geometry.py <project>/antisol.step      > now.json
python <project>/measure/saturn_ring_unchanged.py was.json now.json \
    > <project>/measure/saturn-ring-unchanged.md
```

## What the four atlases do not draw

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

Mercury's rings are weaker evidence again, and deliberately so: they are
generated from a documented formula in `parts/mercury_atlas.py` rather than
carried from any map, because the planet's albedo boundaries are soft and its
plains are unnamed and there is no silhouette to be faithful to. What they
claim is that Mercury's surface is smooth plains of unequal shape with one
large ringed basin in it, not that any particular plain is anywhere in
particular. Caloris's latitude and its 36 degrees of arc are real; its
longitude is a camera decision, taken at −50 because that is where it faces
both photographed frames most squarely, and `measure/mercury-facing.md` is that
measurement. **No crater field**, and the number rather than the opinion: one
degree of arc is 0.120 mm on this globe, so the 0.4 mm nozzle is 3.33 degrees
and the largest crater outside Caloris subtends three to six — one or two
nozzle widths, with no room for a rim and a floor inside that. It would print
as a pit one extrusion wide and read as a print defect, and the set's material
rules forbid deliberate grit. Caloris is included precisely because at 36
degrees it is eleven nozzle widths across. Nothing else the reference shows and
this globe does not carry: no relief anywhere, no third tone beyond `gray`,
`cocoa_brown` and `white`.

Venus's rings are a fourth kind of evidence again: a province map traced from
a radar mosaic, at the accuracy a Ø16.53 globe holds. What they claim is that
Venus's surface is a long equatorial highland with a handful of smaller
highlands and three broad lowland plains around it — and Aphrodite Terra's
sweep is the one silhouette on the globe a reader can match against the
reference image. **No radar texture**, and the number rather than the opinion:
one degree of arc is 0.1443 mm here, so the 0.4 mm nozzle is 2.77 degrees and a
radar filament a few tens of kilometres wide is about a fifth of one nozzle
width. The tesserae, the lava channels, the fracture belts and the ragged
brightness that make the reference look like beaten gold are all under that
floor, none of them is drawn, and **none is approximated with stippling or fine
ribs** — the set's material rules forbid deliberate grit and at this size it
would print as noise. So the piece carries the continents and the plains and
none of the texture: it is a simplified map of the reference, not the
reference. No crater, no Maxwell Montes, no polar cap, no terminator shading,
and above all no clouds and no cloud Y — the reference is a surface map and
shows none of those. One province is drawn in full and cannot be seen: Ishtar
Terra runs from Venusian +54 to +76, and at 177.36 degrees of obliquity that
lands inside the collar the globe stands in, on both armies. It is kept because
the reason it is invisible is the inversion, which this set carries on purpose.

Nothing was dropped silently on any of the four worlds.

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

Venus's `beige` highlands are the thinnest of all and the number is given
rather than buried: **20.2** of 255 luma levels against the
`sunflower_yellow` globe, measured the same two-render way, which is *below*
the 21.8 this set rejected on Mercury as invisible. It reads here and that is
checked in the images rather than argued: Aphrodite Terra is one continuous
marking 117° of longitude wide, 16.9 mm of arc, the longest in the set, where
Mercury's plains were separate patches a few millimetres across — and `beige`
is a pink-cream against an amber, so the boundary carries a hue step luma does
not count. The lowlands are `cocoa_brown` at 33.3 and the two tones separate
43.0 from each other. `measure/venus-tone-separation.md` is all of it,
including `white` at 27.9, which separates further and was not taken because
`white` is already the brightest feature on Earth, Mars and Mercury.

One more pair worth naming, and this revision makes it tighter rather than
looser: Venus's `sunflower_yellow` #FFB549 and Saturn's `yellow` #FFD834 are
neighbours in hue, 23.5 luma levels apart sealed and 11.2 as the renders show
them, and **since this revision Saturn's four light bands are
`sunflower_yellow` as well**, so the two pieces are built from the same two
spools rather than merely from similar ones. That was measured after the change
rather than predicted before it, and the answer is reported on three counts
separately in `measure/venus-saturn-separation.md`: the size and the silhouette
carry the pair easily — 9.47 mm of globe diameter, a Ø30.00 ring on one and
nothing of the kind on the other — and **the surface does not**. The surface is
the weakest of the three cues and it got weaker here. It is stated that way
rather than rounded up.

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
