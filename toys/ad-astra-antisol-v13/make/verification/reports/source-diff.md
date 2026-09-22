# Every source difference between the published set and this revision

Pasted whole rather than summarised, so that "nothing else changed" is
something a reader can check rather than something this project asserts.
The left side is `make/source/cad` from the source archive -- the exact
source the published `Antisol Caelus` set was built from -- and the right
side is this revision's `cad/`. Generated files are not source and are not
diffed here: every `*.step`, the `__cadgen__` cache, `snap/` and the
`measure/*.md` reports are outputs of the source below.

## Which files differ at all

```
Files was/README.md and now/README.md differ
Files was/antisol_spec.md and now/antisol_spec.md differ
Files was/assemblies/product.py and now/assemblies/product.py differ
Files was/params.py and now/params.py differ
Files was/parts/corona.py and now/parts/corona.py differ
Files was/parts/markings.py and now/parts/markings.py differ
Files was/parts/world.py and now/parts/world.py differ
Files was/world_views.py and now/world_views.py differ
```

## Files this revision adds

```
Only in now: corona_views.py
Only in now: measure
Only in now: snap
```

Everything else under `now/` that the archive does not carry is generated:
the `*.step` files, the `__cadgen__` cache, the `snap/` renders and the
`measure/*.md` reports.

## The measurement scripts

The archive keeps these under `make/verification/reports/`, not under
`make/source/cad/measure/`, so the directory comparison above reports the
whole of `measure/` as new. It is not. This is the real comparison, script
by script.

```
Only in now: corona_flat.py
Only in now: markings_refactor.py
Files was/mercury_facing.py and now/mercury_facing.py differ
Files was/mercury_surface_scan.py and now/mercury_surface_scan.py differ
Only in now: mirror_meridian.py
Only in now: pair_separation.py
Files was/revision_hashes.py and now/revision_hashes.py differ
Files was/seated_clearance.py and now/seated_clearance.py differ
Files was/uranus_bare.py and now/uranus_bare.py differ
Files was/venus_facing.py and now/venus_facing.py differ
Files was/venus_surface_scan.py and now/venus_surface_scan.py differ
```

## The difference, in full

### `README.md`

```diff
--- published/README.md
+++ this-revision/README.md
@@ -1,4 +1,4 @@
-# Antisol Caelus — CAD project
+# Antisol Mirror — CAD project
 
 Dou Shou Qi, unchanged, played with the eight planets ranked by their real
 measured diameters. Sixteen worlds, a four-panel board, twelve asteroid-belt
@@ -11,21 +11,36 @@
 adds its own section and leaves the earlier ones as they stand rather than
 back-dating them, which is the same convention `antisol_spec.md` section 11
 follows. So "this revision" inside a world's own section means the run that
-corrected THAT world, not necessarily this one. **This one is Antisol
-Caelus, and it changes exactly two printed parts:
-`part_world_uranus_sol` and `part_world_uranus_anti`.** It takes Uranus's two
-polar hoods off — leaving that globe bare, with no marking of any kind — and
-repaints its ring `white`, the filament Saturn's ring already uses and the
-value `RING_COLOUR` holds as this set's default. Both are owner decisions on
-appearance, taken against measured cases that are kept in full. Neither moves a
-surface: both printed Uranus STEPs come out byte-identical to the published
-set's, which is the check this run turns on. Nothing else in the set changes;
-Neptune's three bands from the previous revision are untouched.
+corrected THAT world, not necessarily this one.
 
-**One thing this revision gains is worth naming here.** Both ringed worlds now
-print their ring in `white`, so the set's "rings are white" rule holds without
-a footnote for the first time.
+**This one is Antisol Mirror, and it changes exactly three printed parts:
+`part_world_mercury_anti`, `part_world_venus_anti` and `part_corona_cell`.**
+It carries two unrelated corrections that share a run because they are small
+and touch disjoint parts. Neither was traded against the other.
 
+**Part one is a defect.** Mercury's and Venus's two armies were visually
+identical when they should have been mirrors. The set's ownership cue is that
+`planet_frame` leans the Sol globe one way and the Anti-Sol globe the other by
+the planet's own obliquity — and those two obliquities are 0.03° and 177.36°,
+so the two pieces of each pair differ by 0.06° and 5.28° of lean. Nothing. The
+mirror is now taken from the only other thing the globe carries, the longitudes
+its markings are drawn at: on those two worlds and on the Anti-Sol side alone,
+every marking longitude is reflected about that piece's own facing meridian.
+`parts/markings.markings_for` owns that transform and it is the only place it
+lives. Neither obliquity moved, `planet_frame` did not move, and both printed
+STEPs come out byte-identical to the published set's, because a flush colour
+inlay partitions the globe without moving its surface.
+
+**Part two is the owner's taste.** Every corona tile carried two raised tongues
+at the two corners furthest from the star — twelve small horns beside the two
+stars' four. They are gone, so that the star's flames are the only raised
+flames on the board. The sixteen tongues ENGRAVED into the tile's top face stay
+exactly as they were: they are the star's light on the floor of the well, not
+horns. `part_corona_cell` is the one part of the three whose bytes had to move.
+
+The previous revision's Uranus, and the one before that's Neptune, are
+untouched.
+
 ## File map
 
 | file | what it is |
@@ -44,7 +59,7 @@
 | `part_world_<planet>_<side>.step.py` | one of the sixteen worlds, printed |
 | `part_panel_<corner>.step.py` | one of the four board panels, printed |
 | `part_belt_cell.step.py` | one asteroid-belt tile, printed twelve times |
-| `part_corona_cell.step.py` | one corona cell, printed six times |
+| `part_corona_cell.step.py` | one corona cell, printed six times: a flat tile with a sunken sixteen-rayed star and nothing standing above it |
 | `part_den_plug.step.py` | one star, printed twice |
 | `part_orbit_tray.step.py` | one storage tray, printed twice |
 | `ref/` | the reference images, copied in. Twenty are the sealed AI-generated set; `venus-radar-surface.png` is the twenty-first and is different — a supplied photographic dataset image, the Magellan global radar mosaic, and the authority for Venus's globe surface and globe colour |
@@ -68,7 +83,11 @@
 | `measure/jupiter_atlas_resolution.py` | every Jupiter belt width, zone width, ring edge and annulus neck against the nozzle, measured along the wave rather than at one longitude |
 | `measure/jupiter_facing.py` | the Great Red Spot's oval against the view axis, vertex by vertex, at both photographed frames and the per-world frame, on both armies |
 | `measure/jupiter_tone_separation.py` | renders one Jupiter piece twice at one camera to measure what the bright-zone filament is worth against the globe and against the belts |
-| `measure/seated_clearance.py` | measures whether a world seated on a star or in a corona well shares volume with the flames or tongues |
+| `measure/seated_clearance.py` | measures whether a world seated on a star or in a corona well shares volume with anything on it, on both armies; and states the trap tile's own highest surface, the well's drop and slip, and the star's flames |
+| `measure/mirror_meridian.py` | the meridian Mercury's and Venus's Anti-Sol maps are reflected about, the two flips that were refused, and every ring's facing at both photographed frames on both pieces against the +0.30 floor |
+| `measure/markings_refactor.py` | that `markings_for(planet, side)` returns exactly what `MARKINGS[planet]` returned, for the six untouched worlds on both sides and for the two corrected worlds' Sol pieces |
+| `measure/pair_separation.py` | how far apart a world's two pieces read: the lean, in degrees, for all eight; and the surface, in millimetres, measured on the built colour bodies at both photographed frames |
+| `measure/corona_flat.py` | the trap tile before and after its two raised tongues came off — height, volume, area, filament, the engraving untouched, and the tile against itself at each quarter turn |
 | `measure/filament_value.py` | measures Mars's three filaments by value, sealed and as the review renderer shows them |
 | `measure/ice_cap_scan.py` | classifies points around the pole against the built colour bodies |
 | `measure/neptune_atlas_resolution.py` | every Neptune band width and gap against the nozzle, the dark spot's own ring, and the correction of three figures the chain sealed wrongly |
@@ -95,12 +114,12 @@
 | `part_panel_northwest` | 1 | 116 x 188 x 9.00 | dark_gray |
 | `part_panel_northeast` | 1 | 152 x 188 x 9.00 | dark_gray |
 | `part_belt_cell` | 12 | 33.50 x 33.50 x 6.00 | cocoa_brown |
-| `part_corona_cell` | 6 | 33.50 x 33.50 x 10.00 | orange (Sol) / cyan (Anti-Sol) |
+| `part_corona_cell` | 6 | 33.50 x 33.50 x 3.00 | orange (Sol) / cyan (Anti-Sol) |
 | `part_den_plug` | 2 | 36.00 x 36.00 x 24.00 | sunflower_yellow + orange (Sol) / black + cyan (Anti-Sol) |
 | `part_orbit_tray` | 2 | 164 x 88 x 6.00 | gray |
-| `part_world_mercury_*` | 2 | Ø33.87 x 16.78 | disc, numeral, globe, three markings — the smooth plains drawn from outline rings, not round patches, and the Caloris basin as a white floor inside a cocoa_brown rim |
+| `part_world_mercury_*` | 2 | Ø33.87 x 16.78 | disc, numeral, globe, three markings — the smooth plains drawn from outline rings, not round patches, and the Caloris basin as a white floor inside a cocoa_brown rim. **The Anti-Sol piece carries the map MIRRORED**: this world's 0.03° obliquity gives its two pieces 0.06° of lean between them, which shows nothing, so the pair's mirror is carried by the longitudes instead. Same features, same latitudes, arranged the other way round about the piece's own facing meridian at −49.99°. Caloris sits almost exactly on that meridian and barely moves; the seven plains change hands around it. Latitudes, sizes, shapes and counts are untouched, and the printed solid is byte-identical |
 | `part_world_mars_*` | 2 | Ø33.87 x 17.72 | disc, numeral, globe, two markings — albedo drawn from outline rings, not round patches, and polar caps whose rims are broken by lobes |
-| `part_world_venus_*` | 2 | Ø33.87 x 19.53 | disc, numeral, globe, two markings — the highlands and the plains drawn from the Magellan radar mosaic as outline rings, not round patches, and no cloud pattern of any kind |
+| `part_world_venus_*` | 2 | Ø33.87 x 19.53 | disc, numeral, globe, two markings — the highlands and the plains drawn from the Magellan radar mosaic as outline rings, not round patches, and no cloud pattern of any kind. **The Anti-Sol piece carries the map MIRRORED**, for the same reason as Mercury's: 177.36° of obliquity leaves only 5.28° between the two leans. The reflection is about −123.85°, which is the mean of the two photographed frames' own meridians moved +5.00° so that Atalanta Planitia still clears the +0.30 facing floor on the mirrored piece; `measure/mirror-meridian.md` is the sweep. Aphrodite Terra's silhouette is handed the other way and stays square to both cameras. The printed solid is byte-identical |
 | `part_world_earth_*` | 2 | Ø33.87 x 19.70 | disc, numeral, globe, three markings — drawn from coastline outlines rather than round patches |
 | `part_world_neptune_*` | 2 | Ø33.87 x 24.89 | disc, numeral, globe, two markings — **three closed white latitude bands, not eight short cloud streaks**: −46/−41, +11/+15 and +30/+33, so 5, 4 and 3° of arc wide, which is 0.955, 0.764 and 0.573 mm, each a plain `band` region ringing the whole globe; and the Great Dark Spot as one outline oval twice as wide as it is tall, unchanged by this revision. No companion cloud. The bands are an owner reversal of the cloud correction, recorded in `antisol_spec.md` item 24 with the case it overruled kept at item 22 |
 | `part_world_uranus_*` | 2 | Ø33.87 x 25.98 | disc, numeral, globe, **no marking at all** — this is the one world in the set with a bare globe: one undivided `cyan` sphere, no hood, no cap, no band, no spot. It wore an upright `white` equatorial band, then a `beige` polar hood at each pole, and the owner has now taken those off and put nothing in their place. The argument that built the hoods is kept whole in `parts/markings.py` under a heading saying what happened to it. And the ring, which is geometry rather than a marking and did not move: an upright hoop Ø24.02 x 1.00 mm standing in the planet's own equatorial plane, 7.77° past vertical, 1.00 mm of projection per side, now printed in `white` — the same spool as Saturn's ring — by the same owner decision. It is the ring, not the globe, that makes this piece 25.98 mm tall, and it is now the only thing on the piece besides the ball |
```

### `antisol_spec.md`

```diff
--- published/antisol_spec.md
+++ this-revision/antisol_spec.md
@@ -1,4 +1,4 @@
-# Antisol Caelus — design contract
+# Antisol Mirror — design contract
 
 Dou Shou Qi, unchanged, played with the eight planets ranked by their real
 measured diameters. Matter faces antimatter, and you win by walking one of your
@@ -85,12 +85,26 @@
 
 ## 3. Ownership: parity inversion
 
-Ownership never touches a planet's own appearance. It lives in three places:
+Ownership lives in three places, and on six of the eight worlds none of them
+touches the planet's own appearance:
 
 1. **Lean direction.** Every marking pattern is rotated about the +Y axis by
    that planet's true obliquity. Sol worlds lean their north pole toward +X,
    Anti-Sol worlds toward −X. On Saturn the ring leans with it, and that is a
    silhouette cue; on the other seven the lean is carried by the colour pattern.
+
+   **On two worlds the lean has nothing to give, and there the mirror is
+   carried by the map instead.** Mercury's obliquity is 0.03° and Venus's is
+   177.36°, so their two pieces differ by 0.06° and 5.28° of lean — a mirror
+   with nothing in it. Those two Anti-Sol pieces therefore carry the same
+   features at the same latitudes arranged the other way round, reflected
+   about that piece's own facing meridian, so that **every pair in the set
+   reads as a pair**. The obliquities did not move, `lean_sign` did not move
+   and `planet_frame` did not move; item 26 is the whole of it, and
+   `parts/markings.markings_for` is the one place it lives. It costs a
+   mirror-image map on those two worlds and nothing else, and what is mirrored
+   there is a longitude this project chose for its cameras rather than an
+   observation it made.
 2. **Disc taper.** The Sol disc flares outward as it rises, Ø33.00 at the bed to
    Ø34.00 at the top of the wall. The Anti-Sol disc tapers inward, Ø34.00 to
    Ø33.00. Both draft at 6.5° from vertical, and both measure Ø33.87 at their
@@ -176,20 +190,32 @@
 **What the hero costs, accepted in writing.** The two flames rise 18.00 mm at [assumed]
 the board edge. From the seat opposite that den they stand between the eye and
 the den cell's far edge. That is the seat attacking the den, and it is the
-sightline the hero is paid for. No other component is permitted any of it: the
-corona tongues are held to 4.00 mm above the field, 12.78 mm below the crown of [assumed]
-the shortest globe in the set, so a corona cell can never occlude a piece.
+sightline the hero is paid for. No other component is permitted any of it. That was
+first written when the corona tiles carried two raised tongues, held to 4.00 mm [assumed]
+above the field and 12.78 mm below the crown of the shortest globe in the set so [inferred]
+that a corona cell could never occlude a piece. Item 27 removes those tongues on
+the owner's instruction, so the rule now holds absolutely rather than by margin:
+**nothing else on the board rises above the field at all**, and the star's two
+flames are the only raised flames in the box.
 
 ### `corona_cell` — the trap, and the ring
 
-Six parts, three per den, one geometry in three rotations. A 33.50 x 33.50 x
+Six parts, three per den, one geometry placed six times. A 33.50 x 33.50 x
 3.00 mm tile drops onto the floor of the terrain pocket, and the board's own [assumed]
 pocket wall makes the 3.00 mm well above it, so a seated disc drops exactly [assumed]
-3.00 mm below the field with slip on every side. Its face carries a star and [assumed]
-sixteen radiating flame tongues, **engraved 0.40 mm** — raised relief under a [assumed]
-seated disc would make a trapped piece rock, which is the one thing a corona
-well must not do. Two tapered tongues rise from the two corners furthest from
-the den, so every tongue points away from the star.
+3.00 mm below the field with 0.40 mm of slip on every side. Its face carries a [assumed]
+star and sixteen radiating flame tongues, **engraved 0.40 mm** — raised relief [assumed]
+under a seated disc would make a trapped piece rock, which is the one thing a
+corona well must not do.
+
+**And nothing else.** Two tapered tongues used to rise from the two corners
+furthest from the den, so that every tongue pointed away from the star, and the
+tile was placed in one of three rotations to keep them pointing that way. Item
+27 removes them on the owner's instruction: the trap is now the tile and its
+engraving and nothing more, its highest surface is the floor a trapped world
+stands on, and with a sixteen-fold engraving on a rounded square it is the same
+tile at any quarter turn — so the rotation is gone too. Its printed height is
+3.00 mm, not 10.00. [assumed]
 
 ## 7. The worlds
 
@@ -511,12 +537,18 @@
    half a millimetre tall is thinner than the nozzle can hold as a wall.
 5. **The corona tile is 33.50 mm square, not 35.50.** A 35.50 mm tile cannot [assumed]
    enter its own 34.80 mm pocket. The corona tongues moved with it, to Ø5.00 on [assumed]
-   a 20.20 mm diagonal, which keeps 0.70 mm to that cell's own seated disc and [assumed]
-   0.37 mm inside the tile edge. [assumed]
+   a 20.20 mm diagonal, which kept 0.70 mm to that cell's own seated disc and [assumed]
+   0.37 mm inside the tile edge. The tile's size stands; the tongues do not — [assumed]
+   item 27 removes them, and `CORONA_TONGUE_BASE_D`, `CORONA_TONGUE_H`,
+   `CORONA_TONGUE_TIP_R` and `CORONA_TONGUE_DIAGONAL` are retired from
+   `params.py` with them. 0.70 mm was the tightest clearance on that tile and [inferred]
+   it is now a constraint the part does not have.
 6. **Sixteen corona tongues starting 6.50 mm out, not twenty-four from the [assumed]
    centre.** Run in to the middle they merge into one blob whose boundary
    leaves 0.13 mm webs; a separate engraved disc stands in for the star they [assumed]
-   radiate from.
+   radiate from. These are the ENGRAVED sixteen and they are untouched by item
+   27 — count, inner radius, eye and 0.40 mm depth all unchanged. They were [assumed]
+   never the horns the owner objected to.
 7. **Saturn's ring is Ø30.00 with a 1.40 mm section, not Ø32.00 x 1.60.** The [assumed]
    Wish's own fallback, taken for the reason the Wish gives.
 8. **Terrain pockets on a panel seam are inset 1.00 mm rather than 0.60.** [assumed]
@@ -555,6 +587,12 @@
     axis, which is free: after the shift it measures +0.44 / +0.62 against the
     two frames the product is photographed from, on both armies.
 
+    Item 26 is downstream of this one and could not exist without it: because
+    these longitudes are camera decisions rather than map facts, they are the
+    thing on Mercury and Venus that a mirror can be taken from — and because
+    they are camera decisions, the mirror has to be the one reflection that
+    does not move them off the camera.
+
     Venus was carried the same way and for the same reason, and its number has
     since been taken twice. The first was −135°, chosen for the ultraviolet
     cloud Y §8.4 asked for. That pattern is gone — item 19 — and its offset
@@ -574,7 +612,10 @@
     composition for that camera — "at 35°/22° the wells catch shadow and the
     tongues catch light", "the cut grid catches light along one wall of every
     groove" — and the low elevation is what puts the globes, rather than the
-    board, in front of the eye. The three-state sheet stays at the higher
+    board, in front of the eye. (Quoted as it was written. Since item 27 the
+    only tongues on a corona tile are the sixteen ENGRAVED into its floor, and
+    at 22° of elevation they are still what catches the light in a well; what
+    is gone is the two that stood above it.) The three-state sheet stays at the higher
     isometric, because at 22° the far ranks foreshorten into each other and the
     three positions stop being separable.
 
@@ -1945,8 +1986,187 @@
     and says whether it was carried forward under a heading or removed and why.
     The per-piece polar and south-polar renders stay: a bare globe photographed
     down its own pole is still the right way to show there is nothing there.
+
+26. **Mercury's and Venus's two armies were the same piece twice, and the fix
+    is a mirror in the map rather than a lean that does not exist.** This is a
+    DEFECT found by the owner, not a reversal of anything: his words were that
+    looking from one side, the Mercury and the Venus of both armies are on the
+    same side, and that these two planets should be flipped.
+
+    The cause is arithmetic rather than anyone's mistake. §3 makes the mirror
+    out of the lean: `planet_frame` turns the Sol globe by +tilt and the
+    Anti-Sol globe by −tilt. At Mars's 25.19° or Earth's 23.44° the two pieces
+    stand 50.38° and 46.88° apart and the difference is obvious across a table.
+    Mercury's obliquity is **0.03°**, so its two pieces differ by 0.06°.
+    Venus's is **177.36°**, and +177.36 against −177.36 is not 354.72° apart —
+    it is the same turn measured each way round, so the angle between them is
+    360 − 2 × 177.36 = **5.28°**. Both are nothing.
+    `measure/pair-separation.md` reports that angle for all eight worlds.
+
+    **The obliquities are observed facts and do not move.** `params.PLANETS` is
+    untouched, `params.lean_sign` is untouched, `features.planet_frame` is
+    untouched. Inventing a lean would be correcting the planet rather than the
+    piece.
+
+    **So the mirror is taken from the longitudes**, which item 10 records were
+    never observations on these two worlds: `mercury_atlas.CALORIS_LON = −50`
+    and `venus_atlas.LONGITUDE_OFFSET = +90` are camera decisions, solved by
+    earlier runs so that the features face the lens. That is exactly what makes
+    them available to mirror, and exactly what makes the obvious flips
+    dangerous. Measured on Caloris at the hero frame: negating longitude sends
+    it from −50 to +50 and it reads **−0.021**, the limb precisely. Reflecting
+    through the lean's own mirror plane, L → 180 − L, sends it to +230 and it
+    reads **+0.395** — 80° off the camera meridian, a glancing three-quarter
+    view of the one feature this globe is recognised by. Both obey the
+    instruction and both ruin the piece.
+
+    **The transform that does both jobs is a reflection about the piece's own
+    FACING MERIDIAN.** Carry the camera direction back into that globe's planet
+    frame — `planet_frame` inverted — and take its longitude, C. Map every
+    marking longitude L to **2C − L**. Facing is the dot product of a marking's
+    direction with the view axis, and in the planet frame that is
+    cos(lat)·cos(lat_C)·cos(L − C) + sin(lat)·sin(lat_C): longitude enters only
+    through cos(L − C), and cos((2C − L) − C) = cos(L − C). So the reflection
+    preserves the facing of every point **exactly**, at any obliquity, while
+    swapping left and right as the camera sees it. Confirmed numerically rather
+    than taken on trust — swept over a 33 × 72 grid of latitudes and longitudes
+    at both frames on both worlds, the largest change in the dot product is
+    6.66 × 10⁻¹⁶.
+
+    **There are two photographed frames, so there are two values of C**, about
+    ten degrees apart, and one reflection has to serve both. Mercury takes the
+    plain circular mean of the two, **−49.99°**, and every Mercury feature that
+    clears the +0.30 facing floor on the Sol piece still clears it on the
+    mirrored piece, by 0.052 at the worst. Venus's mean does not clear:
+    Atalanta Planitia reads +0.367 on the Sol piece at the hero frame and falls
+    to +0.266 on the mirrored one. Rather than accept that, the meridian was
+    swept at a hundredth of a degree and moved **+5.00°** to **−123.85°** —
+    which is the whole number beside the sweep's own optimum at +4.98, and
+    which amounts to solving Venus's reflection about the hero camera's own
+    meridian rather than the mean, because the hero frame is the one Atalanta
+    is tight at. `measure/mirror-meridian.md` carries the sweep, both traps and
+    every ring's facing at both frames on both pieces.
 
+    **Where the transform lives.** `MARKINGS` in `parts/markings.py` was keyed
+    by planet alone and read in five places in `parts/world.py` — the raw
+    union, the region builder twice, the body assembly and the absent-key
+    check. All five now call **`markings_for(planet, side)`**, a single
+    function that returns the same structure `MARKINGS` returns and applies the
+    reflection only when the planet is one of the two named and the side is
+    `anti`. One place owns the transform and every consumer is unchanged in
+    shape. For the six untouched worlds on both sides, and for the two
+    corrected worlds' Sol pieces, it returns the table's own list — the
+    identical object, not a copy — and `measure/markings-refactor.md` checks
+    all sixteen cases. Uranus's entry is empty since item 25 and survives
+    unchanged; there is no branch that names it.
 
+    **What it costs, stated plainly.** A reflected map is a MIRROR-IMAGE map.
+    The Anti-Sol Mercury's Caloris rim is handed the other way from the real
+    basin's, and so are the Anti-Sol Venus's provinces. Latitude, size, shape
+    and count are untouched, and so is every dimension of both pieces —
+    `part_world_mercury_anti.step` and `part_world_venus_anti.step` come out
+    byte-identical to the published set's, because a flush inlay partitions the
+    globe without moving its surface. The mitigation is real and is most of the
+    answer: on these two worlds longitude was never a map fact, so what is
+    mirrored is a placement this project chose rather than an observation it
+    made. **Which worlds are drawn at real longitudes and which at solved
+    ones**, from this project's own records: Earth's coastlines and Mars's
+    albedo map are drawn at their real longitudes, and so are Saturn's and
+    Neptune's bands and caps, which are latitude features with no longitude to
+    get wrong. Jupiter's Great Red Spot was carried 110° for the camera (item
+    10). Venus's whole map carries +90° for the camera. Mercury's Caloris was
+    placed at −50° for the camera, and its seven plains keep the centres the
+    round-patch build used. Uranus carries nothing.
+
+    **Jupiter has the same condition and is deliberately not in scope.** Its
+    obliquity is 3.13°, so its two pieces stand 6.26° apart — third-worst in
+    the set, and in the same family as Mercury's 0.06 and Venus's 5.28.
+    Measured on the built bodies at the two photographed frames, its markings
+    move 1.24 mm between the two pieces on the frame that separates them least, [observed]
+    which is **9% of its globe radius**. The four marked worlds whose lean is
+    not degenerate move 43% to 73% of their own radius — Earth 43, Mars 53,
+    Neptune 55, Saturn 73 — and the two this run corrects now move 36%
+    (Mercury) and 56% (Venus) — where before the correction they moved 0.004 mm [observed]
+    and 0.528 mm, which is 0% and 6%. The same measurement run with [observed]
+    `markings.MAP_MIRRORED_WORLDS` emptied is
+    `measure/pair-separation-before.md`, and the other six worlds read
+    identically in both, which is the control. Jupiter is the one world left in
+    the set that reads as one object photographed twice. The owner named Mercury and Venus and did not
+    name Jupiter, so it was measured and left alone. The recommendation is in
+    `README.md`. Mars at 25.19°, Earth at 23.44°, Saturn at 26.73°, Neptune at
+    28.32° and Uranus at 97.77° are all far from degenerate — 50.38°, 46.88°,
+    53.46°, 56.64° and 164.46° between their two pieces — which is the negative
+    half of the same check and is why the recommendation is scoped to Jupiter
+    alone.
+
+27. **The trap tiles lose their two raised tongues, so the star's flames are
+    the only raised flames on the board.** This is an owner decision on
+    appearance and is recorded as one. It reverses nothing that was measured:
+    the tongues were never argued for at length, they were simply part of the
+    corona cell from the first draft.
+
+    Dou Shou Qi puts a den at each end and three traps around it. Here the den
+    is the star and the traps are the corona wells. §6 gave the star two flames
+    standing 18.00 mm above the field and gave **every** corona tile two more [assumed]
+    at 4.00 mm, at the two corners of the edge furthest from the star: three [assumed]
+    traps per side, two tongues each, two sides — **twelve small horns around
+    the two stars' four**. The owner wants the trap tiles flat.
+
+    **The two raised bodies are removed and nothing replaces them.** The
+    sixteen tongues cut 0.40 mm INTO the tile's top face stay exactly as they [assumed]
+    are — count, inner radius, eye and depth — because they are not horns: they
+    are the star's light on the floor of the well, they are the reason a trap
+    reads as a trap with a world standing in it, and they are engraved
+    precisely so a seated disc cannot rock on them. The result is a tile whose
+    only feature is a sunken sixteen-rayed star.
+
+    **What the tile becomes**, measured in `measure/corona-flat.md`: one solid
+    where it was one fused body with two flames on it; **3.00 mm tall where it [assumed]
+    was 10.00**; a plain rounded-square extrusion with an engraving in its top
+    face. `part_corona_cell.step` is the one printed geometry in this revision
+    whose bytes had to move, and byte-identical would have meant the tongues
+    were still on it.
+
+    **Four constants are retired.** `CORONA_TONGUE_BASE_D`, `CORONA_TONGUE_H`,
+    `CORONA_TONGUE_TIP_R` and `CORONA_TONGUE_DIAGONAL` have no remaining
+    consumer and are removed from `params.py` rather than left behind as dead
+    numbers; the whole project was searched for each of them first, source,
+    measurement scripts and report generators alike, and `parts/corona.py` was
+    the only reader. The retired values are recorded in
+    `measure/corona-flat.md`.
+
+    **The placement rotation goes with them.** `assemblies/product.py` had a
+    function `_away_from_den` whose whole job was to turn each corona tile so
+    its tongues pointed away from the star. With no tongues, a rounded square
+    carrying a sixteen-fold engraving — whose tongues alternate two lengths, so
+    it repeats every 45° — is the same tile at any quarter turn. The rotation
+    is dropped rather than kept as a turn through nothing, and that the placed
+    occurrences did not move is measured rather than argued: the symmetric
+    difference between the tile and the tile turned 90°, 180° and 270° is zero
+    to the kernel's own noise, so the assembly's interference and
+    occurrence-geometry checks keep exactly the meaning they had.
+
+    **The storage trays do not move.** `assemblies/product.py` parks them well
+    clear of the board, and the reason recorded there was that at the fixed
+    product viewpoint a tray near the far edge cuts through a corona tongue in
+    projection. That reason is spent. `TRAY_Y` is a composition decision every
+    whole-set render is framed around, so the distance is kept deliberately and
+    the comment now says what it actually buys rather than what it used to.
+
+    **What the removal buys, measured rather than asserted**, in
+    `measure/corona-flat.md` and `measure/overhang-corona_cell.md`: the
+    overhang gate, the clearances, the packing and the print. The tightest
+    thing on the tile was the 0.70 mm the tongues kept from a seated disc at a [inferred]
+    20.20 mm diagonal; that constraint is gone with the feature, and what is [inferred]
+    left is a plane — the tile's highest surface is now the floor a trapped
+    world stands on, so no part of any world, including Saturn's Ø30.00 ring
+    and Uranus's hoop, can reach anything on a trap tile.
+    `measure/seated-piece-clearance.md` measures that on all sixteen pieces of
+    both armies. The well's own 3.00 mm drop and its 0.40 mm of slip per side [assumed]
+    are unchanged and are derived there from the board's and the tile's own
+    constants rather than quoted.
+
+
 ## 12. What this run does not prove
 
 No part of this run demonstrates physical printing, dimensional accuracy on a
```

### `assemblies/product.py`

```diff
--- published/assemblies/product.py
+++ this-revision/assemblies/product.py
@@ -27,10 +27,20 @@
 FIELD_TOP = P.BOARD_THICKNESS
 POCKET_FLOOR = P.BOARD_THICKNESS - P.POCKET_DEPTH
 
-# Where the two storage trays sit beside the set, clear of the near star.  The
-# gap is generous on purpose: at the fixed product viewpoint a tray parked
-# close to the far edge crosses the board's rim in projection and cuts through
-# a corona tongue, which reads as a part floating over the board.
+# Where the two storage trays sit beside the set, clear of the near star.
+#
+# The gap was solved for a reason that no longer exists.  It was set so that at
+# the fixed product viewpoint a tray parked close to the far edge did not cross
+# the board's rim in projection and cut through a corona tongue.  The corona
+# tiles have no tongues any more, so nothing on the board's far edge stands up
+# to be cut through, and that argument is spent.
+#
+# The distance is kept anyway, and deliberately: TRAY_Y is a composition
+# decision that every whole-set render is framed around, and moving it would
+# change `snap/iso.png` and all three panels of `snap/signature.png` for a
+# reason nobody asked for.  What it now buys is the composition itself -- the
+# two trays read as storage parked beside the board rather than as a second
+# row of terrain attached to it.
 TRAY_Y = P.BOARD_D / 2.0 + 62.0 + P.TRAY_D / 2.0
 TRAY_X = P.TRAY_W / 2.0 + 10.0
 
@@ -39,15 +49,23 @@
     return "%s%d" % (FILE_NAMES[file_index], rank_index + 1)
 
 
-def _away_from_den(cell, den) -> float:
-    """Degrees to turn a corona tile so its tongues point away from the star."""
-    dx = cell[0] - den[0]
-    dy = cell[1] - den[1]
-    if dx < 0:
-        return 90.0
-    if dx > 0:
-        return -90.0
-    return 0.0 if dy > 0 else 180.0
+# `_away_from_den` stood here.  Its whole job was to turn each corona tile so
+# that its two raised tongues pointed away from the star, and it returned one of
+# 0, 90, -90 and 180 degrees to do it.  The tongues are gone, and with them the
+# only feature on the tile that had a direction.
+#
+# What is left is a rounded square carrying a sixteen-fold engraving whose
+# tongues alternate two lengths, so the engraving repeats every 45 degrees and
+# the square repeats every 90; a quarter turn maps the tile exactly onto itself.
+# The rotation is therefore dropped rather than kept as a turn through nothing:
+# a reader of this file would otherwise find a placement solving for a feature
+# the part does not have.
+#
+# That the placed occurrences did not move is measured rather than asserted.
+# `measure/corona-flat.md` takes the built tile against itself at each of the
+# three quarter turns and reports the volume of the symmetric difference, so
+# the assembly's own interference and occurrence-geometry checks keep exactly
+# the meaning they had.
 
 
 def tray_socket_centres() -> list[tuple[float, float]]:
@@ -147,7 +165,7 @@
                 "corona_%s" % cell_name(*cell),
                 colour,
                 corona,
-                Location((cx, cy, POCKET_FLOOR)) * Rot(0, 0, _away_from_den(cell, den)),
+                Location((cx, cy, POCKET_FLOOR)),
             )
 
     # --- storage ---------------------------------------------------------
```

### `params.py`

```diff
--- published/params.py
+++ this-revision/params.py
@@ -283,11 +283,15 @@
 CORONA_ENGRAVE_COUNT = 16            # [inferred] as many tongues as stay apart
 CORONA_ENGRAVE_INNER = 6.50          # [inferred] where the tongues start
 CORONA_ENGRAVE_EYE_D = 9.00          # [assumed] the star they radiate from
-CORONA_TONGUE_BASE_D = 5.00          # [inferred] fits the tile and clears the disc
-CORONA_TONGUE_H = 4.00               # [assumed] above field datum
-CORONA_TONGUE_TIP_R = 0.60           # [assumed]
-CORONA_TONGUE_DIAGONAL = 20.20       # [inferred] 0.70 clear of the seated disc,
-                                     # 0.37 inside the tile edge
+# CORONA_TONGUE_BASE_D, CORONA_TONGUE_H, CORONA_TONGUE_TIP_R and
+# CORONA_TONGUE_DIAGONAL stood here and are retired.  They sized the two raised
+# tongues every corona tile carried at its two far corners; the owner's second
+# pass took those tongues off, so that the star's own two flames are the only
+# raised flames on the board, and nothing in this project reads the four
+# numbers any more.  The retired values and what they bought are in
+# `measure/corona-flat.md` and in `antisol_spec.md`; the tightest of them --
+# 0.70 mm of clearance at a 20.20 mm diagonal, which was the tightest thing on
+# the tile -- is a constraint the tile no longer has.
 CORONA_WELL_DROP = 3.00              # [assumed] how far a trapped world sits down
 
 # ----------------------------------------------------------------- storage --
```

### `parts/corona.py`

```diff
--- published/parts/corona.py
+++ this-revision/parts/corona.py
@@ -5,24 +5,29 @@
 world of its rank.  The tile is the FLOOR of the well, not its wall -- the
 board's own 34.80 pocket makes the wall, so a seated disc drops exactly
 3.00 mm below the field and has 0.40 mm of slip per side.
+
+The tile is now that floor and its engraving and nothing else.  Until the
+owner's second pass it also carried two raised tongues at its far corners, and
+`params.py` carried the four constants that sized them; both are gone.  What
+the tile lost is recorded at `build_corona_cell` below, and what the board
+gained by it is measured in `measure/corona-flat.md`.
 """
 
 from __future__ import annotations
 
-import math
-
 from build123d import Pos, extrude
 
 import params as P
-from features import engraved_tongue_sketch, rounded_square_sketch, tapered_flame
+from features import engraved_tongue_sketch, rounded_square_sketch
 
 
 def build_corona_cell():
-    """One corona tile with its two tongues, printed flat, bed datum Z = 0.
+    """One corona tile, printed flat, bed datum Z = 0.
 
-    Local frame: the tile centre is the origin, +Y points away from the den, so
-    the two tongues stand at the +Y corners and every tongue points away from
-    the star.
+    Local frame: the tile centre is the origin.  The tile is square, its
+    engraving is sixteen-fold, and nothing on it points anywhere, so the piece
+    has no preferred heading -- which it had while it carried tongues, and
+    which `assemblies/product.py` no longer has to solve for.
     """
     tile = extrude(
         rounded_square_sketch(P.CORONA_TILE, P.POCKET_CORNER_R), P.CORONA_TILE_H
@@ -35,6 +40,15 @@
     # for the star itself.  Run in to the middle, sixteen tongues merge into
     # one blob whose boundary leaves 0.13 mm webs the nozzle cannot print --
     # measured, not guessed.
+    #
+    # These sixteen are now the whole tile.  The two RAISED tongues that used
+    # to stand 4.00 mm above the field at the two corners furthest from the
+    # star were removed on the owner's instruction, so that the star's own two
+    # flames are the only raised flames on the board.  Nothing here changed to
+    # compensate: the engraving keeps its count, its inner radius, its eye and
+    # its 0.40 mm depth exactly as they were, because it was never the thing
+    # the owner objected to -- it is the star's light on the floor of the well,
+    # and it is the reason a trap reads as a trap with a world standing in it.
     face = engraved_tongue_sketch(
         count=P.CORONA_ENGRAVE_COUNT,
         inner=P.CORONA_ENGRAVE_INNER,
@@ -43,27 +57,13 @@
         eye=P.CORONA_ENGRAVE_EYE_D / 2.0,
     )
     engraving = extrude(face, P.CORONA_ENGRAVE_D + 0.4)
-    tile = tile - Pos(0, 0, P.CORONA_TILE_H - P.CORONA_ENGRAVE_D) * engraving
+    body = tile - Pos(0, 0, P.CORONA_TILE_H - P.CORONA_ENGRAVE_D) * engraving
 
-    # Two tongues, at the two corners of the edge furthest from the den.
-    reach = P.CORONA_TONGUE_DIAGONAL / math.sqrt(2.0)
-    rise = P.CORONA_TONGUE_H + P.CORONA_WELL_DROP   # above the tile's own top face
-    tongues = []
-    for sign in (-1.0, 1.0):
-        flame = tapered_flame(
-            base_radius=P.CORONA_TONGUE_BASE_D / 2.0,
-            tip_radius=P.CORONA_TONGUE_TIP_R,
-            height=rise,
-            lean_deg=P.FLARE_LEAN_DEG,
-            heading_deg=math.degrees(math.atan2(1.0, sign)),
-        )
-        tongues.append(Pos(sign * reach, reach, P.CORONA_TILE_H) * flame)
-
-    body = tile + tongues
     body.label = "corona_cell"
     return body
 
 
 def build_corona_tile_only():
-    """The tile without tongues -- used to state the well's own dimensions."""
+    """The bare tile without its engraving -- used to state the well's own
+    dimensions, and to measure what the engraving takes out of it."""
     return extrude(rounded_square_sketch(P.CORONA_TILE, P.POCKET_CORNER_R), P.CORONA_TILE_H)
```

### `parts/markings.py`

```diff
--- published/parts/markings.py
+++ this-revision/parts/markings.py
@@ -50,6 +50,15 @@
 the eye could see, because its surface is under an opaque atmosphere and the
 Magellan mosaic is the only picture of it there is.
 
+The table below is what a world's surface shows on the SOL piece, and on the
+Anti-Sol piece of six of the eight worlds.  On Mercury and Venus the Anti-Sol
+piece gets the same features at the same latitudes arranged the other way
+round, because those two obliquities are too small to give the pair a visible
+mirror and the map has to carry it instead.  Nothing indexes `MARKINGS`
+directly any more: `markings_for(planet, side)` at the foot of this file is the
+one place that transform lives, and the arithmetic for why those two worlds and
+no others is beside it.
+
 Each entry is (colour, [region specs]).  A region spec is one of
     ("blob",    [(lat, lon, angular_radius), ...])
     ("band",    lat_low, lat_high)              a lens, deepest in the middle
@@ -79,6 +88,11 @@
 
 from __future__ import annotations
 
+import functools
+import math
+
+import params as P
+
 from parts import atlas as ATLAS
 from parts import jupiter_atlas as JUPITER_ATLAS
 from parts import mars_atlas as MARS_ATLAS
@@ -117,6 +131,18 @@
         # Anti-Sol.  Mercury's obliquity is 0.03 degrees, so the mirrored lean
         # moves nothing here and the two armies agree to two decimals.
         #
+        # **The table below is the SOL piece, and it is now the Sol piece
+        # alone.**  It was written when both armies carried the map at these
+        # longitudes, which is the defect `markings_for` corrects: the Anti-Sol
+        # piece reflects every longitude about that piece's own facing meridian
+        # at -49.99 degrees, so its plains sit on the other side of Caloris.
+        # The facings are preserved, not the positions -- that is the whole
+        # point of reflecting about the facing meridian rather than negating --
+        # so each of the numbers below still has a twin on the mirrored piece,
+        # on a different plain.  `measure/mercury-facing.md` reads the Anti-Sol
+        # piece as it is now built, and `measure/mirror-meridian.md` reports
+        # both pieces ring by ring at both frames.
+        #
         #   plain at (18, 24)     +0.28 +0.28 | +0.46 +0.46
         #   plain at (6, 48)      -0.17 -0.17 | +0.02 +0.02
         #   plain at (-22, 118)   -0.99 -0.99 | -0.94 -0.94
@@ -138,6 +164,14 @@
         # midpoint of the two camera azimuths, which puts the basin 0.99
         # against both view axes on both armies -- the most nearly dead-on any
         # marking in this set gets.  `measure/mercury-facing.md`.
+        #
+        # That is also why Caloris barely moves under the mirror.  The facing
+        # meridian the Anti-Sol piece reflects about is -49.99, and -50 is
+        # already sitting on it, so the basin is very nearly a fixed point of
+        # the reflection and it is the plains around it that change hands.
+        # A world whose one recognisable feature stayed square to the camera
+        # while its terrain swapped sides is exactly the correction that was
+        # asked for.
         ("plains", "cocoa_brown", [
             ("outline", MERCURY_ATLAS.PLAINS_RINGS),
         ], ()),
@@ -250,6 +284,20 @@
         # frames on both armies.  That is what the offset was chosen for; the
         # rest of the map follows it rather than the other way round.
         # `measure/venus-facing.md` is the scan over every offset.
+        #
+        # **The Anti-Sol columns above are the piece as it WAS.**  They were
+        # written when both armies carried the map at these longitudes, which
+        # is the defect `markings_for` corrects: this world's 177.36 degree
+        # obliquity leaves 5.28 degrees between the two leans, so the pair
+        # showed the same face twice.  The Anti-Sol piece now reflects every
+        # longitude about that piece's own facing meridian, -123.85 degrees --
+        # the mean of the two cameras' meridians moved +5.00 so that Atalanta
+        # Planitia still clears the +0.30 facing floor.  Aphrodite's silhouette
+        # is handed the other way and stays square to both cameras, at +0.73
+        # and +0.92 on the hero frame against the Sol piece's +0.76 and +0.91
+        # for its two build rings.  `measure/venus-facing.md` reads the
+        # Anti-Sol piece as it is now built and
+        # `measure/mirror-meridian.md` reports both pieces ring by ring.
         ("highland", "beige", [
             ("outline", VENUS_ATLAS.HIGHLAND_RINGS),
         ], ()),
@@ -712,3 +760,191 @@
 
     ],
 }
+
+
+# ------------------------------------------------ the two armies as mirrors --
+#: The two worlds whose map is mirrored on the Anti-Sol piece, and nothing else
+#: in this set is.
+#:
+#: The set's ownership cue is that every world leans by its own true obliquity
+#: and that the two armies lean opposite ways: `parts/world.py` builds the Sol
+#: globe through `planet_frame(tilt, +1, ...)` and its Anti-Sol twin through
+#: `planet_frame(tilt, -1, ...)`, so the two pieces of a pair are a mirror of
+#: each other in the lean and in nothing else -- the map is drawn at the same
+#: longitudes on both.  At Mars's 25.19 degrees or Earth's 23.44 that is
+#: plainly two different objects across a table.
+#:
+#: On two worlds it gives nothing, and the arithmetic is the whole of it:
+#:
+#:   Mercury's obliquity is 0.03 degrees.  Sol leans +0.03 and Anti-Sol -0.03,
+#:   so the two pieces differ by 2 * 0.03 = 0.06 degrees of lean.  Nothing.
+#:
+#:   Venus's is 177.36 degrees.  Sol leans +177.36 and Anti-Sol -177.36, and
+#:   those two directions are not 354.72 degrees apart -- they are the same
+#:   turn measured each way round, so the angle between them is
+#:   360 - 2 * 177.36 = 5.28 degrees.  Also nothing.
+#:
+#: Both are observed facts and neither moves: `params.PLANETS` is untouched,
+#: `params.lean_sign` is untouched and `features.planet_frame` is untouched.
+#: The defect is CAUSED by those two tilts, so inventing a lean would be
+#: correcting the planet rather than the piece.
+#:
+#: So the mirror is taken from the only other thing the globe carries: the
+#: longitudes its markings are drawn at.  `markings_for` below applies it, and
+#: it applies it to these two worlds on the Anti-Sol side alone.
+MAP_MIRRORED_WORLDS = ("mercury", "venus")
+
+#: The two frames the product is photographed at: `snap/iso.png` and the three
+#: panels of `snap/signature.png`.  `snap_frames.HERO_VIEW` and
+#: `snap_frames.SHEET_VIEW` are the authority for both; they are restated here
+#: rather than imported because that module loads a renderer and this one is
+#: read by every `gen`.  `measure/mirror_meridian.py` asserts the two agree, so
+#: this copy cannot drift away from the pictures it is solved against.
+PHOTOGRAPHED_VIEWS = ((-55.0, 22.0), (-45.0, 35.264))
+
+#: How far the mirror meridian is moved off the mean of the two cameras, per
+#: world, in degrees.  A world not named here uses the plain mean.
+#:
+#: The two photographed frames are ten degrees apart in azimuth, so each world
+#: has two facing meridians and one reflection has to serve both.  Their mean
+#: is the obvious candidate and it is what Mercury uses: measured ring by ring
+#: at both frames on both pieces, every Mercury feature that clears the +0.30
+#: facing floor on the Sol piece still clears it on the mirrored Anti-Sol
+#: piece, by 0.052 at the worst.
+#:
+#: Venus does not clear at the mean, and the failure is one feature: Atalanta
+#: Planitia reads +0.367 on the Sol piece at the hero frame and falls to +0.266
+#: on the mirrored piece, under the floor.  Rather than accept that, the
+#: meridian is moved until it clears.  Swept at a hundredth of a degree, the
+#: adjustment that leaves the worst-off feature the most margin is +4.98
+#: degrees; +5.00 is the round number beside it, and it is what is taken -- it
+#: costs 0.0002 of that margin and reads as a decision rather than as an
+#: optimiser's last two digits.  What it amounts to is that Venus's reflection
+#: is solved about the HERO camera's own meridian (-124.09) instead of the mean
+#: of the two (-128.85), because the hero frame is the one Atalanta is tight
+#: at.  `measure/mirror-meridian.md` is the sweep and the per-ring table.
+MERIDIAN_ADJUSTMENT = {"venus": 5.00}
+
+
+def _view_axis(azimuth_deg: float, elevation_deg: float):
+    """Where `render_review` puts the camera, as a unit vector in the piece."""
+    azimuth, elevation = math.radians(azimuth_deg), math.radians(elevation_deg)
+    return (math.cos(elevation) * math.cos(azimuth),
+            math.cos(elevation) * math.sin(azimuth),
+            math.sin(elevation))
+
+
+def _unturn(vector, tilt_deg: float, sign: float):
+    """`planet_frame` inverted: the piece frame carried back into the planet's.
+
+    `planet_frame` turns the planet frame about +Y by `sign * tilt`, so its
+    inverse is the same turn the other way.  The translation in `planet_frame`
+    moves the origin and not a direction, so a direction needs only the turn.
+    """
+    angle = math.radians(sign * tilt_deg)
+    x, y, z = vector
+    return (x * math.cos(angle) - z * math.sin(angle),
+            y,
+            x * math.sin(angle) + z * math.cos(angle))
+
+
+def facing_meridian(planet: str, side: str, views=PHOTOGRAPHED_VIEWS) -> float:
+    """The longitude, in this piece's own planet frame, the cameras look down.
+
+    One value per frame, averaged on the circle so a pair straddling the
+    +/-180 seam cannot average to the meridian behind the globe.  The two
+    photographed frames are ten degrees apart in azimuth, so the two meridians
+    are about ten degrees apart too and their mean is the obvious compromise.
+
+    `MERIDIAN_ADJUSTMENT` then moves that mean where a world needs it moved.
+    Only Venus does; `measure/mirror-meridian.md` reports both meridians, the
+    mean, the adjustment, and every ring's facing at both frames on both
+    pieces.
+    """
+    tilt = P.PLANETS[planet]["tilt"]
+    sign = P.lean_sign(side)
+    xs, ys = 0.0, 0.0
+    for azimuth, elevation in views:
+        back = _unturn(_view_axis(azimuth, elevation), tilt, sign)
+        lon = math.atan2(back[1], back[0])
+        xs += math.cos(lon)
+        ys += math.sin(lon)
+    return math.degrees(math.atan2(ys, xs)) + MERIDIAN_ADJUSTMENT.get(planet, 0.0)
+
+
+def reflect_longitude(lon_deg: float, meridian_deg: float) -> float:
+    """One longitude reflected about a meridian: L -> 2C - L.
+
+    This is the one transform that mirrors the map WITHOUT moving anything off
+    the camera, and the reason is exact rather than empirical.  A marking's
+    facing is the dot product of its own direction with the view axis, and
+    carrying the view axis back into the planet frame -- which is what
+    `facing_meridian` does -- turns that into
+
+        cos(lat) cos(lat_C) cos(L - C) + sin(lat) sin(lat_C)
+
+    for a camera whose back-carried direction is (lat_C, C).  Longitude enters
+    only through cos(L - C), and cos((2C - L) - C) = cos(C - L) = cos(L - C),
+    so every point keeps its facing EXACTLY, at any obliquity.  What the
+    reflection does change is which side of the meridian a feature sits on,
+    which is precisely what the owner asked for.
+
+    The two obvious flips both fail, and they fail on these two worlds
+    specifically because both worlds' longitudes were SOLVED for the camera:
+    `mercury_atlas.CALORIS_LON = -50` and `venus_atlas.LONGITUDE_OFFSET = 90`
+    are camera decisions, not map facts.  Negating longitude sends Caloris from
+    -50 to +50, a hundred degrees off the camera meridian.  Reflecting through
+    the lean's own mirror plane, L -> 180 - L, sends it to -130, behind the
+    globe.  Either obeys the instruction and ruins the piece.
+    `measure/mirror-meridian.md` measures all three.
+    """
+    return 2.0 * meridian_deg - lon_deg
+
+
+def _mirror_spec(spec, meridian: float):
+    """One region spec with its longitudes reflected about `meridian`.
+
+    A `band`, a `shell` and a `cap` are rings and caps of latitude: they are
+    the same set of points at every longitude, so a longitude reflection is the
+    identity on them and they are returned unchanged rather than rebuilt.  A
+    `blob` carries one centre.  An `outline` carries closed rings, and each
+    ring is returned reversed as well as reflected: a reflection turns a
+    counter-clockwise ring clockwise, and `features.patches._radial_prism`
+    lofts the ring in the order it is given.
+    """
+    kind = spec[0]
+    if kind == "outline":
+        return ("outline", [
+            [(reflect_longitude(lon, meridian), lat) for lon, lat in ring][::-1]
+            for ring in spec[1]
+        ])
+    if kind == "blob":
+        return ("blob", [
+            (lat, reflect_longitude(lon, meridian), radius)
+            for lat, lon, radius in spec[1]
+        ])
+    return spec
+
+
+@functools.lru_cache(maxsize=None)
+def markings_for(planet: str, side: str):
+    """What `MARKINGS[planet]` used to be looked up for, per side.
+
+    This is the one place the mirror lives.  Every consumer in
+    `parts/world.py` calls it instead of indexing `MARKINGS`, so the transform
+    is described once and each consumer is unchanged in shape.
+
+    For the six worlds not named in `MAP_MIRRORED_WORLDS`, and for the Sol
+    piece of the two that are, this returns the identical object `MARKINGS`
+    holds -- not a copy, not a rebuild.  Uranus's entry is empty and stays
+    empty; nothing here special-cases it, and nothing has to.
+    `measure/markings-refactor.md` checks all sixteen cases.
+    """
+    entries = MARKINGS[planet]
+    if side != "anti" or planet not in MAP_MIRRORED_WORLDS:
+        return entries
+    meridian = facing_meridian(planet, side)
+    return [
+        (key, colour, [_mirror_spec(spec, meridian) for spec in specs], subtract)
+        for key, colour, specs, subtract in entries
+    ]
```

### `parts/world.py`

```diff
--- published/parts/world.py
+++ this-revision/parts/world.py
@@ -5,9 +5,17 @@
 play, so the assembly can address and colour each of them and the print gates
 can measure the fused whole.
 
-Ownership lives in three places, none of which touches the planet's own
-appearance: the direction the globe leans (its true obliquity, mirrored), the
-direction the disc's wall drafts, and the disc's colour.
+Ownership lives in three places, and on six of the eight worlds none of them
+touches the planet's own appearance: the direction the globe leans (its true
+obliquity, mirrored), the direction the disc's wall drafts, and the disc's
+colour.
+
+Mercury and Venus are the exception, and they are it because their obliquities
+are 0.03 and 177.36 degrees -- too small to give a mirrored lean anything to
+show.  On those two the Anti-Sol piece carries the same features at the same
+latitudes arranged the other way round, so that the pair reads as a pair.
+`parts/markings.markings_for` owns that, and every marking lookup below goes
+through it; nothing here indexes `MARKINGS` any more.
 """
 
 from __future__ import annotations
@@ -41,7 +49,7 @@
     polar_cap_tool,
     seven_segment_sketch,
 )
-from parts.markings import MARKINGS
+from parts.markings import markings_for
 
 
 # ------------------------------------------------------------------- disc ---
@@ -243,7 +251,7 @@
     return inside, rest
 
 
-def _marking_raw_union(planet: str):
+def _marking_raw_union(planet: str, side: str):
     """Every marking region of one planet, fused before any of them is sliced.
 
     This is what actually gets carved out of the globe.  Fusing the plain balls
@@ -251,13 +259,13 @@
     not, because neighbouring slices share the band's own spherical faces.
     """
     pieces = []
-    for _key, _colour, specs, _subtract in MARKINGS[planet]:
+    for _key, _colour, specs, _subtract in markings_for(planet, side):
         for spec in specs:
             pieces.append(_region_tool(planet, spec))
     return pieces[0] + pieces[1:] if len(pieces) > 1 else pieces[0]
 
 
-def _marking_regions(planet: str, nudge: float = 0.0):
+def _marking_regions(planet: str, side: str, nudge: float = 0.0):
     """key -> region solid in the planet's own frame, disjoint from its peers.
 
     Regions are made disjoint HERE, while they are still plain balls and
@@ -267,7 +275,7 @@
     whole globe, silently disappears.
     """
     raw = {}
-    for key, _colour, specs, _subtract in MARKINGS[planet]:
+    for key, _colour, specs, _subtract in markings_for(planet, side):
         pieces = [_region_tool(planet, spec, solid=True) for spec in specs]
         raw[key] = pieces[0] + pieces[1:] if len(pieces) > 1 else pieces[0]
 
@@ -286,7 +294,7 @@
     # moves every seam off the tangency without moving what the eye sees.
     ball = Sphere(P.globe_radius(planet))
     regions = {}
-    for key, _colour, specs, subtract in MARKINGS[planet]:
+    for key, _colour, specs, subtract in markings_for(planet, side):
         lenses = []
         first = 0
         for spec in specs:
@@ -632,11 +640,11 @@
         # changes them, so they are built once per widening and the spin is
         # applied to the finished regions, where it costs nothing.
         if spin == 0.0:
-            regions, solid_regions = _marking_regions(planet, nudge)
+            regions, solid_regions = _marking_regions(planet, side, nudge)
         placed = frame if spin == 0.0 else frame * Rot(0, 0, spin)
         remaining = [whole]
         patches = {}
-        for key, colour, _specs, subtract in MARKINGS[planet]:
+        for key, colour, _specs, subtract in markings_for(planet, side):
             if key not in regions:
                 continue
             tool = placed * regions[key]
@@ -658,7 +666,7 @@
         # the piece still measured as a sound, complete, correctly-sized world
         # with one hood on it.  A missing patch is treated as this widening's
         # fault, the same as a crossing body, and the next one is tried.
-        absent = [key for key, _c, _s, _sub in MARKINGS[planet]
+        absent = [key for key, _c, _s, _sub in markings_for(planet, side)
                   if key in regions and key not in patches]
         if absent:
             faults.append("nudge %+.3f spin %+.2f: %s never cut the globe"
```

### `world_views.py`

```diff
--- published/world_views.py
+++ this-revision/world_views.py
@@ -574,6 +574,17 @@
 
 
 if __name__ == "__main__":
+    if len(sys.argv) > 1 and sys.argv[1] == "neighbours":
+        # world_views.py neighbours <scratch> <cad-skill-scripts-dir> <out-dir>
+        #                           <first> <second>
+        scratch = Path(sys.argv[2])
+        first, second = sys.argv[5], sys.argv[6]
+        for item in write_neighbours(first, second, scratch):
+            print(item)
+        for item in render_neighbours(first, second, scratch, Path(sys.argv[3]),
+                                      Path(sys.argv[4])):
+            print(item)
+        raise SystemExit(0)
     if len(sys.argv) > 1 and sys.argv[1] == "ladder":
         # world_views.py ladder <scratch> <cad-skill-scripts-dir> <out-dir> [side]
         scratch = Path(sys.argv[2])
```

