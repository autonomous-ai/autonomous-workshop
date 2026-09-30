# Every source byte this revision changed

The correction is three edits, and this report is not a summary of them: it is
the literal `diff -ru` of this run's CAD sources against the published set's,
pasted whole. It is here because the Wish's largest requirement is a NEGATIVE
one -- every dimension in `params.py` stays as it is, the ring's geometry does
not move, nothing else in the set changes -- and the only honest way to evidence
a negative over a whole source tree is to show the entire difference and let a
reader count it.

```bash
diff -ru <published-archive>/make/source/cad <this-run>/product/cad \
    --exclude='*.step' --exclude=measure --exclude=snap --exclude=__cadgen__
```

`measure/` and `snap/` are excluded because they are this run's own evidence and
renders rather than the design. `*.step` is excluded because generated geometry
is compared by hash in `measure/revision-part-hashes.md` and occurrence by
occurrence in `measure/occurrence-geometry.md`.

What the `measure/` exclusion hides, named here so it is not hidden: this run
ADDED `measure/uranus_bare.py`, `measure/uranus_ring_tone.py` and
`measure/world_separation.py`; it EDITED `measure/uranus_ring.py`,
`measure/uranus_mirror.py`, `measure/uranus_atlas_resolution.py` and
`measure/revision_hashes.py`, in every case to change what the report SAYS about
the same measurement rather than how it is measured; and it corrected the
ring-stance wording in `measure/world_separation.py` after the independent critic
caught the phrase "pole-over-pole" describing an equatorial ring. None of those
files is imported by any build target, so none of them can move a solid.

## Five files differ, and only two of them are code

| file | what changed |
|---|---|
| `params.py` | **one value**: `RINGED_WORLDS["uranus"]["colour"]` from `"cyan"` to `"white"`. Plus the comment under `RING_COLOUR`, which recorded an exception that no longer exists. **No dimension moved.** `URANUS_RING_*`, the whole Saturn ring block, `LADDER_CONSTANT`, `LADDER_EXPONENT`, the 97.77 degree obliquity, `RELIEF_DEPTH`, the 5.00 mm disc, the 2.00 mm globe sink and the -42 degree seat are untouched -- and are visibly absent from the diff below |
| `parts/markings.py` | **two lines removed**: the `hood_north` and `hood_south` region tuples. `MARKINGS["uranus"]` is now empty. The comment block above it is not deleted: the whole argument is kept and headed with what happened to it, which is the rest of the change in that file. The module docstring is corrected where it described Uranus as a `cap` world |
| `world_views.py` | **added, nothing removed**: the eight-globe rank-ladder frame (`ladder_assembly`, `write_ladder`, `render_ladder` and a `ladder` verb). It photographs the size ladder and does not touch it -- `LADDER_CONSTANT`, `LADDER_EXPONENT` and every `globe_d` are read and never written |
| `antisol_spec.md` | the design contract: Uranus's markings row, the sentence about the hood turned face-on, the ring's colour wherever it was recorded, the palette table, and new item 25 recording this reversal. Item 23 -- the case for the hoods -- is left exactly as it stood |
| `README.md` | the CAD project's own README: the what-this-revision-is header, the Uranus print-table row, the filament tally, the rebuild commands and the outline/atmosphere section |

Every other file in the project is byte-identical, which is what the absence of
any further `diff` header below means.

## The diff, whole

```diff
diff -ru <published>/README.md <this run>/README.md
--- <published>/README.md	2026-09-20 16:01:05
+++ <this run>/README.md	2026-09-20 17:04:08
@@ -1,4 +1,4 @@
-# Antisol Poseidon — CAD project
+# Antisol Caelus — CAD project
 
 Dou Shou Qi, unchanged, played with the eight planets ranked by their real
 measured diameters. Sixteen worlds, a four-panel board, twelve asteroid-belt
@@ -12,13 +12,20 @@
 back-dating them, which is the same convention `antisol_spec.md` section 11
 follows. So "this revision" inside a world's own section means the run that
 corrected THAT world, not necessarily this one. **This one is Antisol
-Poseidon, and it changes exactly two printed parts:
-`part_world_neptune_sol` and `part_world_neptune_anti`.** It puts Neptune's
-three closed white latitude bands back in place of the eight short cloud
-streaks, by owner decision on appearance taken against the measured case for
-the streaks, which is kept in full. Nothing else in the set changes; Uranus's
-ring and hoods are untouched.
+Caelus, and it changes exactly two printed parts:
+`part_world_uranus_sol` and `part_world_uranus_anti`.** It takes Uranus's two
+polar hoods off — leaving that globe bare, with no marking of any kind — and
+repaints its ring `white`, the filament Saturn's ring already uses and the
+value `RING_COLOUR` holds as this set's default. Both are owner decisions on
+appearance, taken against measured cases that are kept in full. Neither moves a
+surface: both printed Uranus STEPs come out byte-identical to the published
+set's, which is the check this run turns on. Nothing else in the set changes;
+Neptune's three bands from the previous revision are untouched.
 
+**One thing this revision gains is worth naming here.** Both ringed worlds now
+print their ring in `white`, so the set's "rings are white" rule holds without
+a footnote for the first time.
+
 ## File map
 
 | file | what it is |
@@ -69,6 +76,9 @@
 | `measure/neptune_flush.py` | whether any Neptune marking stands proud of its globe, and whether the dark spot's ring is a faceted polygon |
 | `measure/neptune_mirror.py` | the two Neptune pieces body for body, and the dark spot against the volume the archived build measured |
 | `measure/neptune_separation.py` | Neptune beside Uranus and beside Earth at the product's own frame, answered on size, colour, silhouette and surface separately |
+| `measure/uranus_bare.py` | asks three separate ways whether anything at all is still drawn on either Uranus globe: the marking table, the built colour bodies, and whether the globe's volume is its published volume plus both removed hoods |
+| `measure/uranus_ring_tone.py` | renders one Uranus piece twice at one camera with only the ring repainted, to measure what the `white` the owner chose is worth against the `cyan` globe |
+| `measure/world_separation.py` | `neptune_separation.py`'s method with both worlds named on the command line: Uranus beside Neptune, Saturn and Earth at the product's own frame, answered on size, colour, silhouette and surface separately |
 | `measure/revision_hashes.py` | this run's per-part STEP hashes against the published set |
 | `measure/occurrence_geometry.py` | the same comparison by geometry, for the production solids |
 | `snap/` | the canonical final render family and the signature review. `iso.png` is the
@@ -93,25 +103,37 @@
 | `part_world_venus_*` | 2 | Ø33.87 x 19.53 | disc, numeral, globe, two markings — the highlands and the plains drawn from the Magellan radar mosaic as outline rings, not round patches, and no cloud pattern of any kind |
 | `part_world_earth_*` | 2 | Ø33.87 x 19.70 | disc, numeral, globe, three markings — drawn from coastline outlines rather than round patches |
 | `part_world_neptune_*` | 2 | Ø33.87 x 24.89 | disc, numeral, globe, two markings — **three closed white latitude bands, not eight short cloud streaks**: −46/−41, +11/+15 and +30/+33, so 5, 4 and 3° of arc wide, which is 0.955, 0.764 and 0.573 mm, each a plain `band` region ringing the whole globe; and the Great Dark Spot as one outline oval twice as wide as it is tall, unchanged by this revision. No companion cloud. The bands are an owner reversal of the cloud correction, recorded in `antisol_spec.md` item 24 with the case it overruled kept at item 22 |
-| `part_world_uranus_*` | 2 | Ø33.87 x 25.98 | disc, numeral, globe, one marking — **a polar hood at each pole, not one equatorial band**: a `cap` region with its boundary at latitude 60, 11.53 mm across the surface, no lobed rim, in `beige` on the `cyan` globe. Both poles because the two armies lean opposite ways and a single northern hood is past the limb on every Anti-Sol piece at both product frames. And the ring, which is geometry rather than a marking: an upright hoop Ø24.02 x 1.00 mm standing in the planet's own equatorial plane, 7.77° past vertical, 1.00 mm of projection per side, printed in the globe's own `cyan` so that it reads as relief rather than as a painted line. It is the ring, not the globe, that makes this piece 25.98 mm tall |
+| `part_world_uranus_*` | 2 | Ø33.87 x 25.98 | disc, numeral, globe, **no marking at all** — this is the one world in the set with a bare globe: one undivided `cyan` sphere, no hood, no cap, no band, no spot. It wore an upright `white` equatorial band, then a `beige` polar hood at each pole, and the owner has now taken those off and put nothing in their place. The argument that built the hoods is kept whole in `parts/markings.py` under a heading saying what happened to it. And the ring, which is geometry rather than a marking and did not move: an upright hoop Ø24.02 x 1.00 mm standing in the planet's own equatorial plane, 7.77° past vertical, 1.00 mm of projection per side, now printed in `white` — the same spool as Saturn's ring — by the same owner decision. It is the ring, not the globe, that makes this piece 25.98 mm tall, and it is now the only thing on the piece besides the ball |
 | `part_world_saturn_*` | 2 | Ø33.87 x 29.00 | disc, numeral, globe, three markings — five bands at unequal widths and unequal spacing, none of them a mirror of another, the two widest drawn as outline rings with a 2.5° wave on each boundary and the rest as plain bands; one of the five in `cocoa_brown` and the other four in `sunflower_yellow`; a bright `white` cap above +58° on the north only — and the ring, which is geometry rather than a marking and is unchanged by this revision |
 | `part_world_jupiter_*` | 2 | Ø33.87 x 29.97 | disc, numeral, globe, four markings — six belts at their real unequal latitudes, the two widest drawn as outline rings with a 2.5° wave on each boundary; five bright `beige` zones between and beyond them; the Great Red Spot as one 13 by 9° oval; and its `cocoa_brown` collar |
 
 42 printed parts, 24 distinct printed geometries, 13 filaments — the same
 thirteen; this revision loads no new spool.
 
-Filaments per world, counting the globe and its markings and not the disc or
-the numeral, which every world shares: Earth, Jupiter and Saturn take four;
-Mercury, Mars, Venus and Neptune take three; Uranus takes two. **Uranus gained
-a ring and no new spool**: the hoop prints in the globe's own `cyan`, which is
-measured rather than inherited — a `white` ring on this globe read to an
-independent reader as a tennis seam, and the set's own `rings are white` rule
-gives way here for that reason. It is the second world in this set to carry a
-ring. Saturn's ring is a
+Filaments per world, counting the globe and what stands on it and not the disc
+or the numeral, which every world shares: Earth, Jupiter and Saturn take four;
+Mercury, Mars, Venus and Neptune take three; **Uranus takes two**, which is the
+fewest in the set. That tally is unchanged by this revision and the two spools
+in it are different ones: it was `cyan` for the globe and its own ring plus
+`beige` for the hoods, and it is now `cyan` for the globe and `white` for the
+ring. **The count that did fall is the piece's own: Uranus loads three spools
+where it loaded four**, because the `beige` left with the hoods and nothing
+replaced it. It is the first correction in this chain to make a world simpler
+to print rather than more complicated.
+
+**The `rings are white` rule holds again, with no exception.** Uranus's hoop
+printed in the globe's own `cyan` for one edition — measured rather than
+inherited, because a `white` ring on this globe read to an independent reader
+as a tennis seam — and the owner has reversed that. Both ringed worlds now
+print their ring in `white`, from the same spool, so the two rings are the same
+KIND of part again and are told apart by how they stand rather than by what
+they are made of. Saturn's ring is a
 near-horizontal plate and Uranus's is a hoop standing on edge, because a ring
 lies in its planet's equatorial plane and the two obliquities are 26.73° and
-97.77°; the orientation is what tells them apart and Saturn stays the widest
-world in the set at Ø30.00 against Ø24.02. **Saturn
+97.77°; the orientation is what tells them apart — the colour no longer helps —
+and Saturn stays the widest world in the set at Ø30.00 against Ø24.02.
+`measure/uranus-saturn-separation.md` puts that question to the two pieces
+side by side. **Saturn
 prints in four — `yellow`, `sunflower_yellow`, `cocoa_brown` and `white` — where
 it printed in three**, and it is the one world in this set whose correction
 *lowered* its contrast rather than raising it: it used to be a `yellow` globe
@@ -149,11 +171,22 @@
 outline oval rather than two overlapping circles, for exactly Jupiter's reason,
 and that stands. Its clouds became eight short tapered outline arcs, because a
 closed belt runs the whole way round the planet and `ref/neptune-sol.png` shows
-wisps that start and stop — and **this revision puts the three closed belts of
-latitude back**, by owner decision on appearance taken against that measured
-case. The case is kept in full in `parts/markings.py` and at item 22 of the
-spec; item 24 records who overruled it and why.
+wisps that start and stop — and **the revision before this one put the three
+closed belts of latitude back**, by owner decision on appearance taken against
+that measured case. The case is kept in full in `parts/markings.py` and at item
+22 of the spec; item 24 records who overruled it and why.
 
+**Uranus has now left the argument altogether**, and it is the only world that
+has. It was a latitude band, then two polar hoods drawn as `cap` regions, and
+since this revision it carries nothing: the owner looked at the finished hoods
+and took them out, and nothing replaced them. That is a defensible answer on
+this particular world rather than a gap — `ref/uranus-sol.png` is an almost
+featureless sphere, and what carries this piece's identity is the ring, the
+size and the `cyan`. It is also the one thing in the set that could stop being
+true: bare separates Uranus from its neighbours only while it is the only bare
+world. Item 25 of the spec records the decision and item 23 keeps the case it
+overruled.
+
 **Venus is the only one of the four drawn from radar rather than from what the
 eye would see.** Its surface is under an opaque atmosphere and the Magellan
 global mosaic is the only picture of it there is. It used to wear the
@@ -408,7 +441,15 @@
   "$(workshop skills path)/cad/scripts" <project>/snap/worlds
 python <project>/world_views.py <scratch>/worlds neptune \
   "$(workshop skills path)/cad/scripts" <project>/snap/worlds
+python <project>/world_views.py <scratch>/worlds uranus \
+  "$(workshop skills path)/cad/scripts" <project>/snap/worlds
 
+# the eight-globe rank ladder: all eight worlds of one army at one camera and
+# one framing box, orthographic, so the size ladder can be read off one frame.
+# It photographs the ladder and does not touch it.
+python <project>/world_views.py ladder <scratch>/worlds \
+  "$(workshop skills path)/cad/scripts" <project>/snap sol
+
 # the two side-by-side pairs `measure/neptune_separation.py` reads.
 # `world_views.py` exposes these as functions rather than as a CLI verb,
 # because which two worlds are worth standing next to each other is a
@@ -418,9 +459,9 @@
 from pathlib import Path
 import world_views as V
 scripts, steps, out = Path("<cad-skill-scripts>"), Path("<scratch>/worlds"), Path("<project>/snap/worlds")
-for other in ("uranus", "earth"):
-    V.write_neighbours("neptune", other, steps)
-    V.render_neighbours("neptune", other, steps, scripts, out)
+for other in ("neptune", "saturn", "earth"):
+    V.write_neighbours("uranus", other, steps)
+    V.render_neighbours("uranus", other, steps, scripts, out)
 PAIRS
 
 python <project>/measure/atlas_resolution.py > <project>/measure/earth-atlas-resolution.md
@@ -450,27 +491,40 @@
     > <project>/measure/saturn-cap-visibility.md
 
 python <project>/measure/uranus_atlas_resolution.py > <project>/measure/uranus-atlas-resolution.md
-python <project>/measure/uranus_facing.py          > <project>/measure/uranus-facing.md
 python <project>/measure/uranus_ring.py            > <project>/measure/uranus-ring.md
 python <project>/measure/uranus_mirror.py          > <project>/measure/uranus-mirror.md
-python <project>/measure/uranus_tone_separation.py "$(workshop skills path)/cad/scripts" \
-    <project>/snap/worlds > <project>/measure/uranus-tone-separation.md
+python <project>/measure/uranus_reference_read.py  > <project>/measure/uranus-reference.md
+python <project>/measure/uranus_ring_tone.py "$(workshop skills path)/cad/scripts" \
+    > <project>/measure/uranus-ring-tone.md
+for other in neptune saturn earth; do
+  python <project>/measure/world_separation.py uranus $other \
+      > <project>/measure/uranus-$other-separation.md
+done
+# measure/uranus_facing.py and measure/uranus_tone_separation.py are NOT run any
+# more. Both measure the polar hoods, and this revision removed them; both exit
+# on an empty marking table. Their published reports are carried forward under a
+# heading saying what they measured and that the feature is gone. See
+# measure/retired-hood-evidence.md.
 python <project>/measure/neptune_atlas_resolution.py \
     > <project>/measure/neptune-atlas-resolution.md
 python <project>/measure/neptune_facing.py  > <project>/measure/neptune-facing.md
 python <project>/measure/neptune_flush.py   > <project>/measure/neptune-flush.md
 python <project>/measure/neptune_mirror.py  > <project>/measure/neptune-mirror.md
-python <project>/measure/neptune_separation.py uranus \
-    > <project>/measure/neptune-uranus-separation.md
 python <project>/measure/neptune_separation.py earth \
     > <project>/measure/neptune-earth-separation.md
+# the Neptune-Uranus pair is asked from Uranus's side on this run, by
+# measure/world_separation.py above, because Uranus is the world that changed.
 
 python <project>/measure/occurrence_geometry.py <published>/assembled.step > was.json
 python <project>/measure/occurrence_geometry.py <project>/antisol.step      > now.json
 python <project>/measure/saturn_ring_unchanged.py was.json now.json \
     > <project>/measure/saturn-ring-unchanged.md
+python <project>/measure/uranus_bare.py was.json now.json \
+    > <project>/measure/uranus-bare.md
+python <project>/measure/occurrence_geometry.py --compare was.json now.json \
+    uranus_sol_ uranus_anti_ > <project>/measure/occurrence-geometry.md
 python <project>/measure/revision_hashes.py <product-root> <archive-root> \
-    --expect-changed world_uranus_sol world_uranus_anti \
+    world_uranus_sol world_uranus_anti \
     > <project>/measure/revision-part-hashes.md
 ```
 
diff -ru <published>/antisol_spec.md <this run>/antisol_spec.md
--- <published>/antisol_spec.md	2026-09-20 16:01:05
+++ <this run>/antisol_spec.md	2026-09-20 17:04:45
@@ -1,4 +1,4 @@
-# Antisol Poseidon — design contract
+# Antisol Caelus — design contract
 
 Dou Shou Qi, unchanged, played with the eight planets ranked by their real
 measured diameters. Matter faces antimatter, and you win by walking one of your
@@ -213,11 +213,12 @@
 - **Markings** — flush colour inlays reaching 1.20 mm into the globe, described [assumed]
   in the planet's own frame in angles rather than millimetres, then rotated by
   that planet's true obliquity. Describing them as angles is what lets one
-  minimum outline width hold from Mercury to Jupiter. **Uranus was described entirely by
-  latitude and no longer is**: a belt of latitude is what a band system is, and
-  what this planet's atmosphere shows is a polar hood rather than a belt, so its
-  two hoods are `cap` regions — the kind the Earth correction added and Saturn's
-  northern cap reuses. Saturn is described both ways, and so is
+  minimum outline width hold from Mercury to Jupiter. **Uranus is no longer described at
+  all**: it was one latitude band, then two polar hoods drawn as `cap` regions,
+  and since this revision it carries no marking of any kind. It is the one
+  world in the set with a bare globe. The measured case for the hoods is kept
+  in full at item 23 and in `parts/markings.py`; item 25 records who overruled
+  it. Saturn is described both ways, and so is
   Neptune: its clouds went from three closed latitude bands to eight short
   outline arcs and, in this revision, back to the three bands by owner
   decision, while its dark spot stays an outline oval
@@ -286,7 +287,7 @@
 | Venus | the Magellan radar surface as outlines — seven highland provinces led by **Aphrodite Terra**, the long equatorial sweep the piece is recognised by, and three lowland plains with the highlands subtracted out of them. The fourth of the four worlds drawn from outlines, and the only one drawn from radar. Inverted with the planet, as it was. No clouds, no cloud Y, no texture | `beige`, `cocoa_brown` on `sunflower_yellow` |
 | Earth | continent coastlines, dry interiors, northern ice — the first of the three worlds drawn from outlines, not circles | `green`, `beige`, `white` on `blue` |
 | Neptune | **three closed white latitude bands** — −46/−41, +11/+15 and +30/+33, so their widths run 5, 4 and 3° of arc, which on this Ø21.89 globe is 0.955, 0.764 and 0.573 mm, the narrowest band family in the set; each a plain `band` region, each running the whole way round the planet; and the **Great Dark Spot** at latitude −22 as one outline oval 28 by 14° of arc [inferred], unchanged by this revision. No companion cloud. The widest bare gap between two bands is 52° of latitude, 9.93 mm. `b1` at −46/−41 is south of the latitude the Sol piece's two product cameras can reach, so on that piece it is an Anti-Sol-only feature at those two frames and is shown on the per-world frames instead. `measure/neptune-atlas-resolution.md`, `measure/neptune-facing.md` | `dark_gray`, `white` on `blue` |
-| Uranus | **a polar hood at each pole**, boundary at latitude 60, no lobed rim — a `cap` region, the kind the Earth correction added. A hood is the feature this planet actually has: Uranus points a pole at the Sun for forty years at a time and the bright polar region follows whichever pole that is. The same 97.77° obliquity that used to stand a band upright turns a hood face-on, which is what `ref/uranus-sol.png` shows: a pale, almost uniform sphere with one very faint lighter region, soft-edged and off-centre, and no stripe. **Both poles rather than one**, because the two armies lean opposite ways and a single northern hood is past the limb on every Anti-Sol piece at both product frames — `measure/uranus-facing.md` measures it at 125.3° and 130.5° from the camera. `beige` rather than `white`, measured against the globe in `measure/uranus-tone-separation.md`. Plus the ring, which is geometry rather than a marking and prints in the globe's own `cyan`. No banding, no storms, no moons | `beige` on `cyan` |
+| Uranus | **nothing.** This world carries no surface marking of any kind: no hood, no cap, no band, no spot, no replacement in a quieter tone. Its globe is one undivided `cyan` sphere. It wore an upright `white` equatorial band, then a `beige` polar hood at each pole; the owner looked at the finished hoods and took them out, and the appearance of the toy is his to decide. A bare world is the right answer on this one: `ref/uranus-sol.png` is an almost featureless sphere — pale, very nearly uniform, with one faint soft-edged lighter region and no stripe anywhere in it — and what carries this piece's identity is the ring, the size and the `cyan`. The measured case for the hoods is kept whole at item 23; item 25 records the reversal. `measure/uranus-bare.md` proves on the solids that nothing survives on either globe. Plus the ring, which is geometry rather than a marking, did not move, and now prints in `white` — the set's default and Saturn's spool. No banding, no storms, no moons | nothing on `cyan` |
 | Saturn | five bands at unequal widths and unequal spacing — +46/+55, +18/+33, +2/+10, −14/−30 and −38/−50, so their widths run 9, 15, 8, 16 and 12° — with the two widest drawn as outline rings carrying a 2.5° wave on each boundary and the other three as plain bands; four of the five in `sunflower_yellow`, the mid tone, and only the widest in `cocoa_brown`; and a bright `white` cap above +58 on the north only, an exact parallel with no lobed rim. **Lower in contrast than Jupiter's on purpose**: the reference's bands are soft-edged and barely darker than their neighbours, Saturn is the quiet planet next to Jupiter's loud one, and both stand on the board at once. Plus the ring, which is geometry rather than a marking and is unchanged by this revision. No hexagon, no storms, no ring divisions, no ring shadow | `sunflower_yellow`, `cocoa_brown`, `white` on `yellow` |
 | Jupiter | six belts at their real, unequal latitudes — +38/+43, +24/+31, +7/+17, −7/−20, −27/−34 and −40/−46, so their widths run 5, 7, 10, 13, 7 and 6° — with the two widest drawn as outline rings carrying a 2.5° wave on each boundary and the other four as plain bands; five bright zones between and beyond them, the Equatorial the widest; and the **Great Red Spot** as one 13 by 9° oval at latitude −22 with a collar just outside it, the South Equatorial Belt bending 7° north around it. Poles above +46 and below −46 left bare | `cocoa_brown`, `beige`, `red` on `orange` |
 
@@ -377,24 +378,37 @@
 its own and on the whole printed part, which reports 0 unsupported regions and
 0 bridges. `measure/uranus-ring.md` carries the sweep.
 
-**The ring prints in the globe's own `cyan`, and that is the one place this
-piece departs from the set's own rule that rings are white.** The brief allows
-it explicitly -- take `white` unless a reason not to is measured -- and the
-reason was measured twice. `white` separates 38.9 of 255 luma levels from the [observed]
+**The ring prints in `white`, and after this revision the set's rule that rings
+are white holds without an exception for the first time.** Both ringed worlds
+print their ring from the same spool, which is the value `RING_COLOUR` has
+always held as the default.
+
+It has not always been so, and the history belongs here because the second
+change reverses the first. The Uranus edition took `white`, then moved off it
+on a measured reading: `white` separates 38.9 of 255 luma levels from the [observed]
 globe, louder than the hood's 27.8, which made the ring the loudest thing on a
 piece that exists to be quiet; and an independent reader shown the board cold
-named both Uranus pieces as tennis balls, twice, on exactly that cue -- a bold
-white curve on a saturated ball beside a pale panel. `gray` was tried and
-measured worse in use: quieter as a number at 7.0 and a MORE convincing seam to
-read, because a tennis seam is a dark curve on a bright ball. The painted-stripe
-reading does not live in the size of the tonal step. It lives in the ring being
-a different material. In the globe's own filament the hoop stops being a marking
-and becomes relief, read by silhouette and self-shadow, which is what a ring on
-this piece is for -- and its luminance against the globe is unchanged, so it is
-no less visible at board scale. `measure/uranus-ring.md` carries the decision
-and what it costs: the two ringed worlds no longer wear the same KIND of ring.
-Saturn's is untouched and still prints `white`.
+named both Uranus pieces as tennis balls, twice, giving the mechanism in his
+own words -- "a bold white curved line arcing down one side of a
+saturated-colour ball, and a large pale panel on the opposite side". `gray` was
+tried and measured worse in use: quieter as a number at 7.0 and a MORE
+convincing seam to read, because a tennis seam is a dark curve on a bright
+ball. So the ring was given the globe's own `cyan` and stopped being a marking
+at all.
 
+**The owner has reversed that.** The geometry did not move by a micron -- this
+is one existing body changing spools -- and the reviewer's mechanism is worth
+reading again before assuming the old problem is back, because it has two
+halves and this revision removes one of them: after the hoods came off there is
+no pale panel anywhere on the piece. Whether a white hoop ALONE on a bare
+`cyan` ball still reads as a seam is a different question, and it is put to this
+build's blind review unprimed rather than assumed in either direction; the
+answer is recorded in `snap/SIGNATURE-REVIEW.json` beside the measured
+separation, which `measure/uranus-ring-tone.md` puts at 38.7 to 39.3 luma [observed]
+levels across the three canonical frames. `measure/uranus-ring.md` carries the
+decision and what it costs. Saturn's ring is untouched and still prints
+`white`.
+
 ## 8. Storage
 
 `orbit_tray`: 164 x 88 x 6.00 mm, `gray`, printed twice, one per player. Eight [assumed]
@@ -408,17 +422,17 @@
 
 | filament | used for |
 |---|---|
-| `white` | Sol disc, Anti-Sol numeral, Mercury Caloris floor, Mars caps, Earth ice, Neptune's three cloud bands, Saturn ring and northern cap |
+| `white` | Sol disc, Anti-Sol numeral, Mercury Caloris floor, Mars caps, Earth ice, Neptune's three cloud bands, Saturn ring and northern cap, **Uranus ring** |
 | `sunflower_yellow` | Sol den plug, Venus globe, Saturn's four light bands |
 | `black` | Anti-Sol disc, Anti-Sol den plug, Sol numeral |
 | `yellow` | Saturn globe |
 | `orange` | Sol flames and corona, Jupiter globe |
-| `cyan` | Anti-Sol flames and corona, Uranus globe **and its ring** |
+| `cyan` | Anti-Sol flames and corona, Uranus globe |
 | `dark_gray` | board panels, Neptune dark spot |
 | `cocoa_brown` | belt tiles, Mercury plains and Caloris rim, Mars albedo, Venus lowlands, Saturn's one dark band, Jupiter belts and spot collar |
 | `gray` | Mercury globe, trays |
 | `red` | Mars globe, Jupiter Great Red Spot |
-| `beige` | Earth dryland, Venus highlands, Jupiter zones, **Uranus polar hoods** |
+| `beige` | Earth dryland, Venus highlands, Jupiter zones |
 | `blue` | Earth globe, Neptune globe |
 | `green` | Earth land |
 
@@ -1805,6 +1819,134 @@
     before: the reversal moved white material about, it did not add or remove a
     spool.
 
+25. **Uranus's two polar hoods are gone and its ring is `white`, and both are
+    owner decisions on appearance taken against measured arguments that are
+    still in this document.** Item 23 is those arguments. Neither was wrong.
+    The owner has looked at the finished pieces, does not like the two pale
+    discs, and has taken them out; the appearance of his own toy is his to
+    decide, and an argument from a reference photograph does not outrank him.
+    Item 23 stays where it is, in full, as the case that was heard and lost;
+    this item records who overruled it and on what grounds, which are taste
+    rather than measurement.
+
+    **What went, and what replaced it.** `("hood_north", ...)` and
+    `("hood_south", ...)` were removed from `MARKINGS["uranus"]` entirely.
+    Nothing replaced them: no cap, no band, no spot, no quieter tone. Uranus is
+    now **the one world in the set with no surface marking of any kind**, and
+    that outcome is one item 23's own brief named in advance and called
+    legitimate: "Uranus being the one unmarked world in a set of eight is a
+    defensible design statement rather than an omission." It was offered there
+    as the fallback if no filament measured usable against `cyan`; the
+    measurement came back usable at 29.0 luma levels, so the hoods were drawn.
+    The owner has taken the fallback anyway.
+
+    **Why a bare world is the right answer on this one.** `ref/uranus-sol.png` [observed]
+    is an almost featureless sphere, and the identity of the piece is carried
+    by the ring, by the size the ladder gives it and by the `cyan`. It is worth
+    naming the condition that keeps that true: bare separates Uranus from its
+    neighbours only while it is the only bare world in the set.
+
+    **The ring turns `white`.** `RINGED_WORLDS["uranus"]["colour"]` went from
+    `"cyan"` to `"white"`, which is the value `RING_COLOUR` holds as this set's
+    default and the spool Saturn's ring already prints from. **After this
+    revision there is no exception: both ringed worlds print their ring in
+    `white`, and the set's "rings are white" rule holds without a footnote for
+    the first time.** The comment under `RING_COLOUR` that recorded the
+    exception is corrected.
+
+    **Nothing moved.** Neither change touches a surface. Removing a flush inlay
+    stops partitioning the globe; repainting the ring moves one existing body
+    from one spool to another. So **both Uranus printed STEPs come out
+    byte-identical to the published set's** -- `7eccfab310b21fef` and [observed]
+    `d993913622975638` -- and that is the check this run turns on rather than a
+    formality: if either hash had moved, something had moved the ring or the
+    globe. 20 of the 24 printed geometries are byte-identical; the four board
+    panels differ in exactly one line each, a
+    `NEXT_ASSEMBLY_USAGE_OCCURRENCE` exporter counter carrying no geometry,
+    diffed line by line in this run rather than asserted.
+    `measure/revision-part-hashes.md`.
+
+    **Measured on the solids.** The assembly's occurrence count goes 224 -> 220, [observed]
+    which is exactly the four hoods and nothing else. Each globe gains exactly
+    the hoods it lost: 5323.412 + 109.5887 + 109.5887 = 5542.588 mm³, residue
+    -0.0014 mm³ on both armies. The ring's volume is identical to nine decimal
+    places at 54.830480 mm³ (Sol) and 54.830494 mm³ (Anti-Sol), in the same
+    bounding box, and the 45° gate still measures 44.3° with 0.0000 mm² over
+    the gate on both armies. Saturn's two ring occurrences come out at
+    574.192167 and 574.192096 mm³, zero delta. `measure/uranus-bare.md`,
+    `measure/uranus-ring.md`, `measure/uranus-mirror.md`,
+    `measure/saturn-ring-unchanged.md`, `measure/occurrence-geometry.md`.
+
+    **What the piece now has to carry on its own**, checked rather than
+    assumed, in `measure/uranus-neptune-separation.md`,
+    `measure/uranus-saturn-separation.md` and
+    `measure/uranus-earth-separation.md`. Against Neptune, its neighbour in
+    rank and in colour family, size cannot help -- Ø22.02 against Ø21.89, less
+    than one nozzle apart -- so the separation is surface and silhouette: a
+    bare ball with a hoop against a banded ball with a spot. Against Saturn,
+    the other ringed world, **the colour of the ring no longer helps at all**,
+    since both are now `white`; what is left is orientation and size, a flat
+    plate lying almost level at Ø30.00 against an upright hoop at Ø24.02, and
+    one piece wider than it is tall against one taller than it is wide.
+    Against Earth the two globes are four ranks and two spools apart.
+
+    **The filament count falls.** Uranus's piece loads **three** spools where [observed]
+    it loaded **four**: disc, numeral, globe and ring, against disc, numeral,
+    globe, hoods and ring. By the tally this document keeps -- the globe and
+    what stands on it, disc and numeral excluded -- Uranus is still two, and
+    the two are different ones: `cyan` plus `beige` has become `cyan` plus
+    `white`. This is the first correction in the chain to make a world simpler
+    to print.
+
+    **The `cyan` limitation stands, and this revision makes it MORE visible.**
+    `cyan` #00FFFF is a saturated neon; `ref/uranus-sol.png` is a pale [observed]
+    desaturated ice blue, its ball measuring 161, 200, 206 against the
+    filament's 0, 255, 255. There is no pale blue anywhere in the thirteen-
+    colour palette; the only other blue is a dark navy, further away. With the
+    hoods gone there is now nothing else on the globe to look at, so the gap is
+    more exposed than it was. That is an honest cost of the decision rather
+    than an argument against it. `measure/uranus-reference.md`.
+
+    **The reading the owner is overruling, tested rather than assumed.** The
+    reason the ring went `cyan` was a blind reviewer who, shown the board cold,
+    named both Uranus pieces as tennis balls, twice, and gave the mechanism in
+    his own words: "a bold white curved line arcing down one side of a
+    saturated-colour ball, and a large pale panel on the opposite side." That
+    mechanism has TWO halves and this revision removes one of them -- after the
+    hoods came off there is no pale panel anywhere on the piece. Whether a
+    white hoop alone on a bare `cyan` ball still reads as a seam is an open
+    question, and it is put to this build's blind review as its own question,
+    unprimed, at board distance on `iso.png` and close up on the piece, rather
+    than assumed in either direction. The answer comes back in the reviewer's
+    own words in `snap/SIGNATURE-REVIEW.json` and is reported beside the
+    measured separation, which `measure/uranus-ring-tone.md` puts at 38.7 to
+    39.3 of 255 luma levels across the three canonical frames. **The ring's
+    filament is not changed back whatever the answer is, and nothing is added,
+    tinted or softened to compensate.** If the answer is still "tennis ball",
+    that is reported plainly with the number beside it and a recommendation for
+    the owner to decide.
+
+    **One frame was added to the review set, and it is a lesson about evidence
+    rather than about this toy.** The first attempt at this correction built
+    the object correctly and could not seal, because the critic was shown
+    sixteen frames of which twelve were Uranus detail views and not one let the
+    eight globes be compared at a single scale -- and this set's whole
+    ownership claim is that a planet's size on the board is the fifth root of
+    its real diameter, so rank is something you can SEE. `snap/rank-ladder-sol.png`
+    is that frame: all eight worlds of one army at one orthographic camera and
+    one framing box, in rank order. `world_views.py` photographs the ladder and
+    does not touch it; `LADDER_CONSTANT`, `LADDER_EXPONENT` and every `globe_d`
+    are read and never written.
+
+    **Evidence that no longer measures anything is retired rather than dropped
+    or kept quietly.** `measure/uranus-facing.md`, `measure/uranus-tone-
+    separation.md` and the two hood evidence renders measured the hoods.
+    `measure/retired-hood-evidence.md` names each one, says what it measured,
+    and says whether it was carried forward under a heading or removed and why.
+    The per-piece polar and south-polar renders stay: a bare globe photographed
+    down its own pole is still the right way to show there is nothing there.
+
+
 ## 12. What this run does not prove
 
 No part of this run demonstrates physical printing, dimensional accuracy on a
@@ -1946,26 +2088,29 @@
 measured in `measure/venus-saturn-separation.md` and stated there without being
 rounded up.
 
-Uranus's hoods are the seventh kind of evidence and its ring is the eighth, and
-the two are not the same kind at all. The hoods are a reading of
-`ref/uranus-sol.png` plus a fact about the planet: the image shows a pale,
-almost uniform sphere with one faint, soft-edged, off-centre lighter region and
-no stripe, and Uranus does carry a bright polar hood because it points a pole
-at the Sun for forty years at a time. What the piece claims is that this world
-is quiet, that its one lighter region is broad and diffuse rather than a band,
-and that it sits where the pole does. What it cannot claim is a soft edge: one
-degree of arc is 0.1922 mm here, a flush colour inlay changes colour at a line, [inferred]
-and the narrowest boundary the printer can lay is one 0.40 mm bead, so the [assumed]
-brightening that fades out in the image stops at an exact circle of latitude on
-the plastic. Lowering the contrast is the substitute rather than the cure, and
-`measure/uranus-tone-separation.md` reports the separation it settled on rather
-than calling it faithful. **And the globe's own colour is wrong and cannot be
+**Uranus's globe claims nothing at all, and that is the seventh kind of
+evidence in this set.** Since item 25 it carries no marking, so there is no
+reading of `ref/uranus-sol.png` on it to defend and no soft edge to fail to
+reproduce. What the bare piece claims is the weakest claim any world here makes
+and the easiest to check: that this planet is quiet. The image supports it —
+a pale, almost uniform sphere with one faint, soft-edged, off-centre lighter
+region and no stripe. It stops short of the image in one direction, which is
+worth stating rather than glossing: the reference's one faint lighter region is
+not drawn, because the owner removed the feature that drew it. The measured
+case for drawing it is kept whole at item 23 and the hoods' own separation
+figures are carried forward, under a heading saying the feature is gone, in
+`measure/uranus-tone-separation.md` and `measure/retired-hood-evidence.md`.
+
+**And the globe's own colour is wrong and cannot be
 made right here**: `cyan` #00FFFF is a saturated neon against a pale [observed]
 desaturated ice blue, there is no pale blue in the thirteen filaments this set
-stocks, and no marking on a neon globe makes the globe paler.
+stocks, and no marking on a neon globe makes the globe paler. **This revision
+makes that gap more visible rather than less**, because with the hoods gone
+there is nothing else on the ball to look at. That is an honest cost of the
+owner's decision, not an argument against it.
 
-The ring is different in kind and is the one feature in this set that is not
-evidence of anything the reference shows. **`ref/uranus-sol.png` does not show
+The ring is the eighth kind, different in kind from every other, and is the one
+feature in this set that is not evidence of anything the reference shows. **`ref/uranus-sol.png` does not show
 a ring.** It is an owner instruction that overruled an earlier version of its
 own brief, recorded as exactly that here, in `product.json` and in
 `measure/uranus-ring.md` rather than dressed up as an observation. It is
diff -ru <published>/params.py <this run>/params.py
--- <published>/params.py	2026-09-20 16:01:05
+++ <this run>/params.py	2026-09-20 16:03:01
@@ -228,12 +228,18 @@
         "thickness": URANUS_RING_THICKNESS,
         "bite": URANUS_RING_GLOBE_BITE,
         "support": "foot",
-        "colour": "cyan",
+        "colour": "white",
     },
 }
-RING_COLOUR = "white"                # [assumed] the set's default, and Saturn's.
-                                     # Uranus's ring departs from it, measured
-                                     # rather than preferred: see below
+RING_COLOUR = "white"                # [assumed] the set's default, Saturn's, and
+                                     # -- since the owner's second pass -- Uranus's
+                                     # too.  There is no exception left: both
+                                     # ringed worlds print their ring in `white`,
+                                     # so the set's "rings are white" rule finally
+                                     # holds without a footnote.  Uranus's ring was
+                                     # `cyan` for one edition, the globe's own
+                                     # colour, and the owner reversed that; the
+                                     # geometry it is painted on did not move
 
 # ------------------------------------------------------------- belt tile ----
 BELT_FLOOR_DROP = 2.00               # [assumed] rubble floor below field datum
diff -ru <published>/parts/markings.py <this run>/parts/markings.py
--- <published>/parts/markings.py	2026-09-20 16:01:05
+++ <this run>/parts/markings.py	2026-09-20 16:03:08
@@ -9,10 +9,11 @@
 How a marking is specified depends on what it is, and after Jupiter's
 correction the split no longer falls world by world.
 
-Uranus was described entirely by latitude, and stopped being: what its
-atmosphere shows is a polar hood rather than a belt, so its two hoods are
-`cap` regions, the kind the Earth correction added and Saturn's northern cap
-reuses.  Neptune stopped being described by latitude, and then went back to
+Uranus is no longer described at all.  It was a latitude band, then two polar
+hoods drawn as `cap` regions, and it is now the one world in the set with a
+bare globe: the owner looked at the finished hoods and took them out, and
+nothing replaced them.  The argument that built them is kept in full under
+`"uranus"` below, as history.  Neptune stopped being described by latitude, and then went back to
 it: its clouds are three plain latitude bands again, by owner decision taken
 against the measured case for the eight short arcs that stood between them --
 that case is kept in full below, under `"neptune"`.  Its dark spot stays an
@@ -453,6 +454,30 @@
         # arithmetic the texture was rejected on.
     ],
     "uranus": [
+        # NOTHING.  Uranus carries no surface marking of any kind.
+        #
+        # WHAT HAPPENED TO THE ARGUMENT BELOW.  The case was heard.  The hoods
+        # were built, and they were measured twice.  Then the owner looked at
+        # the finished pieces and took them out.  He does not like the two pale
+        # discs, and the appearance of his own toy is his to decide; an
+        # argument from a reference photograph does not outrank him.  The whole
+        # argument is kept beneath this heading, unedited, because it is the
+        # record of why the hoods were drawn -- not because it still describes
+        # this piece.  It is history now.
+        #
+        # The first chain's Uranus brief named this outcome in advance and
+        # called it legitimate: "Uranus being the one unmarked world in a set
+        # of eight is a defensible design statement rather than an omission."
+        # It was offered there as the fallback if no filament measured usable
+        # against `cyan`.  The measurement came back usable, so the hoods were
+        # drawn.  The owner has taken the fallback anyway.
+        #
+        # Nothing replaces them: no cap, no band, no spot, no quieter tone.
+        # What tells a player this is Uranus now is the white hoop standing
+        # upright on it, the globe's size in the rank ladder, and the `cyan`.
+        #
+        # ---------------- the argument as it stood, unchanged ----------------
+        #
         # A polar hood at each pole, in the palest warm tone the shop stocks.
         #
         # What stood here was one `white` #FFFEF7 latitude band from -9 to +9.
@@ -517,8 +542,10 @@
         # partition silently loses the southern hood.  Unfused, each cap is one
         # clean lens and the first split is exact on both; the same two caps
         # measured 147.93 mm3 each either way.
-        ("hood_north", "beige", [("cap", 60, "north")], ()),
-        ("hood_south", "beige", [("cap", 60, "south")], ()),
+        #
+        # ------------------------- end of the argument -----------------------
+        #
+        # What is drawn on this globe now is nothing.
     ],
     "saturn": [
         # Five bands, unequal and asymmetric, in a mid tone -- and a bright
diff -ru <published>/world_views.py <this run>/world_views.py
--- <published>/world_views.py	2026-09-20 16:01:05
+++ <this run>/world_views.py	2026-09-20 16:20:09
@@ -381,6 +381,87 @@
     return written
 
 
+#: The rank ladder in one frame.  This set's ownership claim is that a planet's
+#: size on the board is the fifth root of its real diameter, so RANK IS
+#: SOMETHING YOU CAN SEE -- and a reader handed only close-ups of one corrected
+#: world has no frame in which to check that.  This is that frame: all eight
+#: worlds of one army, in rank order, at ONE camera and ONE framing box, so the
+#: only thing that varies across the row is the size the ladder gives each
+#: globe.
+#:
+#: It photographs the ladder and does not touch it.  `LADDER_CONSTANT`,
+#: `LADDER_EXPONENT` and every `globe_d` are read, never written.
+#:
+#: Ø34.00 discs at a 38.00 mm pitch, which is the orbit tray's own pitch and
+#: leaves 4.00 mm of air between neighbours -- close enough that two adjacent
+#: ranks can be compared edge to edge, far enough that no disc overlaps the
+#: next.  The camera is on +X at 12 degrees of elevation: low, so the globes
+#: rather than the disc tops fill the picture, and square to the row, so no
+#: world is nearer the lens than another.  The projection is orthographic, so
+#: equal millimetres are equal pixels the whole way across and the row can be
+#: measured rather than judged.
+#:
+#: Rank 1 is placed at +Y and the camera puts +Y on the right, so the picture
+#: reads rank 8 on the left down to rank 1 on the right: Jupiter, Saturn,
+#: Uranus, Neptune, Earth, Venus, Mars, Mercury.
+LADDER_PITCH = 38.0
+LADDER_VIEW = (0.0, 12.0)
+LADDER_SIZE = 2600
+LADDER_MARGIN = 24
+
+
+def ladder_order() -> list[str]:
+    """The eight worlds, rank 1 first.  Read from `params`, never written."""
+    import params as P
+
+    return sorted(P.PLANETS, key=lambda name: P.PLANETS[name]["rank"])
+
+
+def ladder_assembly(side: str = "sol"):
+    """All eight worlds of one army, in rank order, along the frame's own axis."""
+    order = ladder_order()
+    asm = AssemblyHelper("rank_ladder_%s" % side)
+    span = (len(order) - 1) * LADDER_PITCH
+    for index, planet in enumerate(order):
+        at = Location((0.0, span / 2.0 - index * LADDER_PITCH, 0.0))
+        for role, (colour, shape) in world_bodies(planet, side).items():
+            asm.add(at * shape, "%s_%s_%s_%s" % (planet, side, role, colour),
+                    color=filament(colour))
+    return asm.compound()
+
+
+def write_ladder(target: Path, side: str = "sol") -> Path:
+    target.mkdir(parents=True, exist_ok=True)
+    path = target / ("rank-ladder-%s.step" % side)
+    export_step(ladder_assembly(side), str(path))
+    return path
+
+
+def render_ladder(steps: Path, scripts: Path, target: Path,
+                  side: str = "sol") -> Path:
+    """The ladder frame, cropped to its own content so the row fills the picture."""
+    from PIL import Image
+    import numpy as np
+
+    render_review = _renderer(scripts)
+    target.mkdir(parents=True, exist_ok=True)
+    source = steps / ("rank-ladder-%s.step" % side)
+    _src, shape = render_review.build_shape(source)
+    image = render_review.render(
+        _tessellate(render_review, shape), LADDER_VIEW[0], LADDER_VIEW[1],
+        LADDER_SIZE, 0.02)
+    pixels = np.asarray(image.convert("RGB")).astype(int)
+    mask = np.abs(pixels - np.array(render_review.BACKGROUND)).sum(2) > 6
+    rows, cols = np.nonzero(mask)
+    box = (max(0, int(cols.min()) - LADDER_MARGIN),
+           max(0, int(rows.min()) - LADDER_MARGIN),
+           min(image.width, int(cols.max()) + 1 + LADDER_MARGIN),
+           min(image.height, int(rows.max()) + 1 + LADDER_MARGIN))
+    out = target / ("rank-ladder-%s.png" % side)
+    image.crop(box).save(out)
+    return out
+
+
 def write_worlds(planet: str, target: Path) -> list[Path]:
     target.mkdir(parents=True, exist_ok=True)
     written = []
@@ -493,6 +574,13 @@
 
 
 if __name__ == "__main__":
+    if len(sys.argv) > 1 and sys.argv[1] == "ladder":
+        # world_views.py ladder <scratch> <cad-skill-scripts-dir> <out-dir> [side]
+        scratch = Path(sys.argv[2])
+        side = sys.argv[5] if len(sys.argv) > 5 else "sol"
+        print(write_ladder(scratch, side))
+        print(render_ladder(scratch, Path(sys.argv[3]), Path(sys.argv[4]), side))
+        raise SystemExit(0)
     where = Path(sys.argv[1] if len(sys.argv) > 1 else "snap/worlds")
     planet = sys.argv[2] if len(sys.argv) > 2 else "earth"
     for item in write_worlds(planet, where):
```
