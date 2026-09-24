# Every source byte this revision changed

The correction is a handful of edits, and this report is not a summary of them:
it is the literal `diff -ru` of this run's CAD sources against the published
set's, pasted whole. It is here because the Wish's largest requirement is a
NEGATIVE one -- nothing else on either Neptune piece, and nothing on any other
part, changes -- and the only honest way to evidence a negative over a whole
source tree is to show the entire difference and let a reader count it.

```bash
diff -ru <published-archive>/make/source/cad <this-run>/product/cad \
    --exclude='*.step' --exclude=measure --exclude=snap --exclude=__cadgen__ \
    --exclude=ref
```

`measure/` and `snap/` are excluded because they are this run's own evidence and
renders rather than the design; every report under `measure/` is either
regenerated or carried with its provenance named in `measure/quick-fix-carry.md`.
`ref/` is excluded because the reference images are sealed inputs and none was
touched. `*.step` is excluded because generated geometry is compared by hash in
`measure/revision-part-hashes.md` and occurrence by occurrence in
`measure/occurrence-geometry.md`.

**What a reader should find below, and nothing else:**

1. `parts/neptune_atlas.py` -- the companion's half-axes, offset, longitude,
   vertex count, ring, keep-out dilation and keep-out ring, its
   `companion_specs()` and `companion_keepout_spec()`, its entry in `RINGS`, and
   the docstring and `NOT_DRAWN` text that carry the reasoning. The dark spot's
   own constants are in the context lines, unchanged.
2. `parts/markings.py` -- one new `("companion", "white", ...)` row, and the
   `("spec", ...)` keep-out subtraction added to the existing `spot` row, with
   the comment that records why.
3. `parts/world.py` -- two call sites changed, and two helpers MOVED OUT rather
   than rewritten. `_region_pieces` and the new never-drawn-subtraction helper
   live in `parts/regions.py` now, because the layout gate holds that module to
   400 code lines and this edition pushed it over.
4. `parts/regions.py` -- new file, holding those two helpers.
5. `world_views.py` -- the prose of two per-world frame descriptions, which
   describe pictures rather than making them. No camera moved.
6. `README.md` and `antisol_spec.md` -- this edition's own documentation,
   including spec item 26.

Nothing in `params.py`, `features/`, `assemblies/`, `colors.py`, `positions.py`,
`production.py`, `snap_frames.py`, `bool3d.py`, `snapshots.py`, any other
atlas, or any `part_*.step.py` entry.

```diff
diff -ru '--exclude=*.step' '--exclude=measure' '--exclude=snap' '--exclude=__cadgen__' '--exclude=ref' <published>/antisol_spec.md <this-run>/antisol_spec.md
--- <published>/antisol_spec.md	2026-09-23 17:19:28.934105742 +0000
+++ <this-run>/antisol_spec.md	2026-09-23 23:13:36.375163724 +0000
@@ -1946,6 +1946,169 @@
     The per-piece polar and south-polar renders stay: a bare globe photographed
     down its own pole is still the right way to show there is nothing there.
 
+26. **Neptune's Great Dark Spot has its bright companion cloud back, on both
+    armies, and it is the only thing this revision draws.** Item 24 recorded
+    the companion's loss as a loss rather than a tidy-up and left it as "a live
+    recommendation rather than a settled question". The owner has settled it:
+    add the small bright companion cloud that sits just south of the Great Dark
+    Spot, one `white` outline oval about 10 by 5° of arc, at the spot's own
+    longitude, centred about 8° of latitude south of the spot's centre, inside
+    the narrowest-feature limit this set already uses for printable markings,
+    and nothing else on either Neptune piece or anywhere else changes.
+
+    **Every one of those numbers is drawn exactly as asked. One of them is not
+    free, and this item is where what it costs is written down.**
+
+    **What is drawn.** One `outline` region, `parts/neptune_atlas.COMPANION_RING`,
+    walked from the same ellipse construction the dark spot uses: half-axes 5.0
+    and 2.5° of great-circle arc, so **10 by 5° = 1.910 by 0.955 mm** on the [inferred]
+    Ø21.89 globe, centred at latitude −30.0 and longitude −65.2 — 8.0° due
+    south of the spot's centre, on the spot's own meridian. It is its own
+    marking key, `companion`, rather than a fourth body of the white cloud
+    marking. That is deliberate and it is the one place in this set where the
+    rule "the marking key is the filament" is spent: the companion was lost at
+    item 24 precisely BECAUSE it lived inside the cloud marking and the cloud
+    marking was reverted wholesale. A separate key cannot be deleted by a later
+    argument about bands. It costs one more white body per Neptune piece —
+    `neptune_sol_companion_white` and `neptune_anti_companion_white` — and
+    nothing else.
+
+    **The narrowest-feature limit, which is what the owner's limit clause
+    asks about.** An ellipse's narrowest neck is its own minor axis, 5° of arc
+    or 0.955 mm here. `measure/neptune-atlas-resolution.md` does not take that [inferred]
+    figure from the half-axes: it walks the built ring and measures the
+    narrowest the white material actually gets, which comes out at **0.886 mm, [inferred]
+    2.21 nozzle widths** at 0.40 mm — a little under the declared axis because [inferred]
+    the ring is a polygon inscribed in the ellipse and because the pairs the
+    walk is allowed to measure sit slightly off the axis, where the oval is
+    already narrowing. The dark spot is measured the same way and reads 2.48
+    against its own 2.67 mm minor axis. For scale, the narrowest deliberate [inferred]
+    colour width anywhere in this set is the 0.40 mm strip of green along [inferred]
+    Australia's outback boundary — exactly one nozzle — so the companion sits
+    well clear of this set's own floor and is not the narrowest marking in the
+    box.
+
+    **Its 24 ring vertices were set by the error, not copied from the spot's
+    40.** A ring walked at even bearings falls furthest inside the true ellipse
+    at its two pointed ends; that error grows with the size of the oval and
+    falls as the square of the vertex count. This oval is 10° of arc long,
+    0.357 times the spot's 28, so 24 vertices buy the spot's own smoothness at
+    a coarser count. Measured rather than estimated, in
+    `measure/neptune-atlas-resolution.md`, which walks both rings and takes the
+    worst departure of a chord from the true ellipse: the spot at 40 vertices
+    falls **0.031 mm** inside, the companion at 24 falls **0.028 mm** inside. [inferred]
+    Copying 40 across would have bought nothing visible and left a shortest
+    ring edge of about 0.075 mm; at 24 the shortest edge is **0.127 mm**, the [inferred]
+    same order as the spot's own 0.211 mm and, like it, a facet of a smooth [inferred]
+    curve rather than the width of anything.
+
+    **THE OVAL OVERLAPS THE SPOT, THE SPOT GIVES WAY, AND THAT IS A REAL
+    CHANGE TO THE SPOT.** The spot is 14° of arc tall, so its own southern rim
+    is already 7° south of its centre, and an oval 5° tall centred at 8 puts
+    its top 1.5° inside it. There is nowhere else on this globe to put it, and
+    that is a measured claim rather than a shrug:
+
+    - Moving it south until a printable strip of bare globe fits between the
+      two outlines needs **11.59°** — the two half-heights plus one nozzle
+      width. **That build was made, rendered and rejected on the pictures.**
+      `parts/world.py` seats every globe on a cone springing at piece-frame
+      latitude −42, Neptune leans 28.32°, and at the spot's own longitude that
+      collar covers everything south of about −31° of PLANET latitude on the
+      SOL piece. At 11.8° south the oval's centre landed at piece latitude
+      −40.9 and ten of its twenty-four ring vertices went under the collar: the
+      Sol army came back with a pale half-lens sitting on its base instead of
+      an oval.
+    - The window between the spot's southern rim and that collar is about 2.4°
+      of arc, **0.46 mm**, and a marking plus two nozzle-width gaps does not [inferred]
+      fit in 0.46 mm at any size. `measure/neptune-atlas-resolution.md` scans [inferred]
+      every half-height from 0.8 to 2.4° against every tenth of a degree of
+      centre latitude and **no row clears both**; even a 0.31 mm-tall oval, [inferred]
+      already under the nozzle, cannot reach a full nozzle width of clearance.
+
+    So the owner's numbers are kept and the spot is cut back for the companion.
+    **What it is cut back to is a KEEP-OUT, not the companion itself, and that
+    is this edition's one repair.** Subtracting the companion directly was
+    built, rendered and shown to an independent reader cold: they called the
+    pair "a notched figure-eight" and the new marking "a small grey circle", a
+    lobe budding off the dark spot rather than a cloud beside it, and named it
+    the one blocking defect in the build. The figure the owner asked for had
+    come out inverted, so the spot is instead cut to the companion's oval grown
+    by **2.30° of arc**, a shape that is never drawn and never printed,
+    handed over as a `("spec", ...)` subtraction through the one line of new
+    machinery in `parts/world._subtrahend`. What survives between the two
+    markings is **0.4203 mm of bare blue at their closest approach**, 1.05 [inferred]
+    nozzle widths, and the companion reads as its own cloud. The dilation is
+    solved rather than guessed: the offset of an ellipse is not an ellipse, so
+    growing both half-axes by one nozzle leaves the curves closer than a nozzle
+    somewhere in between; 2.19 is only where the two rings reach 0.40 mm apart and [inferred]
+    measures 0.3995 against where the dark actually stops, a rounding under, so
+    2.30 is used and measures 0.4203.
+
+    **What that costs the Great Dark Spot, and it is the largest thing this
+    edition does to anything it was told not to change.** The keep-out is 14.6
+    by 9.6° of arc against the companion's 10 by 5, so where it crosses the
+    spot it takes a bay about 15° of arc wide and 3.7 deep out of a 28 by 14
+    oval. The `spot` body falls from the archive's **11.9319 mm³ to 10.5113**, [inferred]
+    a loss of 1.4206. The spot's ring is not edited — latitude, longitude,
+    half-axes, 40 vertices and `dark_gray` filament are byte-identical in the
+    source, and `measure/neptune-facing.md` reproduces its archived dot
+    products at every frame — and `measure/neptune-mirror.md` measures the
+    spot's own region BEFORE the cut at the archive's exact 11.9319 mm³ and
+    accounts every cubic millimetre of the difference to the keep-out. What
+    changed is where the dark stops, not where the spot is.
+
+    **The trade, stated so a reader can disagree with it.** The owner asked for
+    a bright cloud just south of the Great Dark Spot and said nothing else on
+    the piece changes. At 8° on a spot 14° tall those two cannot both hold. A
+    cloud that touches the spot keeps the spot's outline and loses the cloud —
+    a reader who had never seen the brief saw a lump. A cloud held one nozzle
+    clear delivers the cloud and costs the spot a bay. The cloud is what was
+    asked for, so the cloud wins.
+
+    **What did not change, measured rather than asserted.** The three bands
+    come out at 10.8043 mm³ on both armies. Every printed STEP of every other [inferred]
+    part in the set is geometrically unchanged: `measure/occurrence-geometry.md`
+    compares this run's assembly against the published one occurrence by
+    occurrence and `measure/revision-part-hashes.md` carries the per-part
+    digests. The companion adds no printed part — `parts/world.build_world`
+    fuses the disc, the globe and the ring and never the markings, so
+    `part_world_neptune_sol.step` and `part_world_neptune_anti.step` are
+    byte-identical to the published set's.
+
+    **AN UNPRIMED READER OF THE FINISHED RENDERS CALLED IT GREY, AND THAT IS
+    THE RENDERER RATHER THAN THE PLASTIC — MEASURED, NOT ARGUED.** This
+    edition's independent critic, shown the images cold and told nothing,
+    described the pair as a "notched figure-eight" and the new marking as "a
+    small grey circle", while calling the two cloud bands on the upper half of
+    the same globe "bright white". `measure/neptune-tone-separation.md` answers
+    it with the two-render method `measure/saturn_tone_separation.py`
+    established: one piece built once, rendered twice at one camera with a
+    single region repainted and nothing else altered, so the pixels that move
+    are exactly that region's under identical light. At the `spot` frame the
+    companion separates from the dark spot's filament by **34.4 luma levels on
+    the Sol piece and 52.3 on the Anti-Sol one**, and from the globe by **57.3 [inferred]
+    and 87.1** — more than the dark spot's own 24.6/38.8 against the same
+    globe, and well past the narrowest separation this set has already shipped
+    (Saturn's light bands at 9.4, Venus's highlands at 20.2). What is small is
+    not the separation but the LIGHT: `render_review` shades by surface normal
+    from above and a flush inlay's outer face IS the globe's own sphere, so
+    every southern marking renders dim whatever spool it prints from — the
+    southernmost cloud band `b1` is `white` too and renders at about 103 on the
+    Sol piece. The companion prints in `white` #FFFEF7, the same spool as the
+    bands and both rings. The grey reading is a property of the review
+    renderer, it is recorded in the product's limitations in those terms, and
+    it is a disclosed caveat rather than a repaired defect because there is no
+    camera under a light from above that makes a southern marking bright. What
+    the keep-out repair fixes is the FIGURE rather than the tone: with a
+    nozzle-wide strip of blue around it the companion is plainly a separate
+    mark of its own, where before it read as one two-lobed object with the
+    spot.
+
+    **Where it can and cannot be seen.** The companion is short, so unlike a
+    closed band it has a longitude and can be on the face a camera does not
+    see. `measure/neptune-facing.md` carries its dot product at every frame on
+    both armies, and the per-world `spot` frame — the level camera aimed at the
+    dark spot — is where the pair reads best.
 
 ## 12. What this run does not prove
 
diff -ru '--exclude=*.step' '--exclude=measure' '--exclude=snap' '--exclude=__cadgen__' '--exclude=ref' <published>/parts/markings.py <this-run>/parts/markings.py
--- <published>/parts/markings.py	2026-09-23 17:19:28.937105685 +0000
+++ <this-run>/parts/markings.py	2026-09-23 21:50:26.708347723 +0000
@@ -303,7 +303,27 @@
         # object.  The latitude, -22, is the real one and the correction fixes
         # it; the longitude is free, because Neptune turns in sixteen hours and
         # this set fixes no meridian.  `parts/neptune_atlas.py` draws it.
-        ("spot", "dark_gray", NEPTUNE_ATLAS.spot_specs(), ()),
+        # It IS CUT BACK for the companion below it, and that subtraction is
+        # the only thing about the spot this revision changes. Its ring,
+        # latitude, longitude, half-axes, 40 vertices and filament are
+        # untouched; what moves is where the dark stops.
+        #
+        # What it is cut back to is a KEEP-OUT rather than the companion
+        # itself: the companion's oval grown by 2.30 degrees of arc, handed
+        # over as a `("spec", ...)` subtraction because nothing is printed in
+        # it. Subtracting the companion itself was built first and rejected by
+        # an independent reader of the renders, who called the touching pair
+        # "a notched figure-eight" and the new marking "a small grey circle".
+        # The keep-out leaves one nozzle width of bare blue between the two
+        # outlines instead, and the companion reads as its own cloud.
+        #
+        # The bay that leaves in the spot's southern rim is about 15 degrees of
+        # arc wide and 3.7 deep on a 28 by 14 oval -- 1.4206 mm3 of an 11.9319
+        # mm3 body. `measure/neptune-mirror.md` measures the spot's own region
+        # before the cut against the volume the archive sealed and accounts the
+        # whole difference to the keep-out.
+        ("spot", "dark_gray", NEPTUNE_ATLAS.spot_specs(),
+         (NEPTUNE_ATLAS.companion_keepout_spec(),)),
         # THE CLOUDS.  Three closed `white` latitude bands, at -46/-41, 11/15
         # and 30/33.  `parts/neptune_atlas.band_specs()` hands them over.
         #
@@ -339,6 +359,49 @@
         # `measure/neptune-atlas-resolution.md` measures all three, the bare
         # gaps between them, and the spot's own unchanged contribution.
         ("bands", "white", NEPTUNE_ATLAS.band_specs(), ()),
+        # THE SPOT'S BRIGHT COMPANION CLOUD, and it is the only thing this
+        # revision adds anywhere in the set.  One white `outline` oval, 10 by
+        # 5 degrees of arc, on the spot's own longitude, 8.0 degrees of
+        # latitude south of the spot's centre -- every number the owner gave.
+        # `parts/neptune_atlas.companion_specs()` draws it.
+        #
+        # IT HAS ITS OWN KEY ON PURPOSE.  The archived build drew a companion
+        # too and put it inside the white cloud marking, and the run that
+        # reverted that marking to these three bands took the companion with
+        # it without ever deciding to -- its own report recorded the loss as
+        # collateral: "it lived in the white cloud marking and the owner has
+        # reverted that marking".  A separate key cannot be deleted by a later
+        # argument about bands.  It costs one more white body per piece and
+        # nothing else; the marking key in this set is usually the filament,
+        # and `companion` is the one place that rule is spent deliberately.
+        #
+        # IT OVERLAPS THE SPOT AND THE SPOT GIVES WAY, WHICH IS A REAL CHANGE
+        # TO THE SPOT AND IS DISCLOSED AS ONE.  The spot is 14 degrees of arc
+        # tall, so an oval 5 degrees tall centred 8 degrees south of its centre
+        # buries its top 1.5 degrees inside it.  Moving the companion south
+        # until a printable strip of bare globe fits needs 11.59 degrees, and
+        # that was built and rendered and rejected: `parts/world.py` seats
+        # every globe on a cone springing at piece-frame latitude -42, the
+        # planet leans 28.32 degrees, and at the spot's own longitude that
+        # collar covers everything south of about -31 degrees of planet
+        # latitude on the SOL piece.  Ten of the oval's twenty-four vertices
+        # went under it and the Sol army came back with a half-lens sitting on
+        # its base.  The window between the spot's rim and the collar is 2.4
+        # degrees of arc, 0.46 mm, and no marking plus two nozzle-width gaps
+        # fits in 0.46 mm at any size.  `parts/neptune_atlas.py` carries the
+        # scan and `measure/neptune-atlas-resolution.md` reproduces it.
+        #
+        # So the owner's numbers are kept and the overlap is resolved the way
+        # this set resolves every overlap: Earth's land gives way to its
+        # dryland, Venus's lowland to its highland, Neptune's spot to its
+        # companion.  The `("companion",)` subtraction on the `spot` line
+        # above is that decision.  What it costs is a scallop 9.5 degrees wide
+        # and 1.5 deep on the spot's southern rim -- 0.3415 mm3 of an 11.9319
+        # mm3 body -- and 0.922 mm of the companion's 4.589 mm rim closer to
+        # the spot's rim than one
+        # nozzle width, where the two outlines cross near the companion's
+        # tips.  Both are measured; neither is argued away.
+        ("companion", "white", NEPTUNE_ATLAS.companion_specs(), ()),
         #
         # ------------------------------------------------------------------
         # THE CASE THAT WAS HEARD, AND LOST.  Everything from here to the end
diff -ru '--exclude=*.step' '--exclude=measure' '--exclude=snap' '--exclude=__cadgen__' '--exclude=ref' <published>/parts/neptune_atlas.py <this-run>/parts/neptune_atlas.py
--- <published>/parts/neptune_atlas.py	2026-09-23 17:19:28.938105666 +0000
+++ <this-run>/parts/neptune_atlas.py	2026-09-23 21:50:22.248438919 +0000
@@ -1,28 +1,105 @@
-"""Neptune's three white cloud bands and its Great Dark Spot.
+"""Neptune's three white cloud bands, its Great Dark Spot, and the spot's
+bright companion cloud.
 
 Neptune wears three closed white latitude bands at -46/-41, 11/15 and 30/33,
-and one dark oval.  That is what it wore before the cloud correction of
-2026-09-19 and it is what it wears again.
-
-**The bands came back by owner decision, not by measurement.**  The correction
-that removed them made a real case and made it well: `ref/neptune-sol.png`
-shows clouds that are SHORT -- each starts and stops inside a few tens of
-degrees of longitude, they sit at slightly different angles to the parallel,
-they are scattered across the face rather than ringing it, and not one of them
-circles the planet -- and three closed bands on a blue ball read as three
-painted stripes, the most beach-ball-like object in the set.  It replaced them
-with eight tapered, bowed, tilted streaks and a bright companion wisp beside
-the spot, and an independent reader confirmed the beach ball had gone.
-
-The owner has since looked at both and prefers the older drawing.  That case
-was heard and overruled; it is kept in full in `parts/markings.py` under
-`"neptune"` so that a reader can see the losing argument rather than a summary
-of it.  Nothing here softens, narrows, moves or breaks the bands to make the
-beach-ball reading come out better: three closed bands at those three
-latitudes is the instruction, and the reading they produce is recorded next to
-the decision rather than engineered away.
+one dark oval, and -- new in this revision -- one small white oval just south
+of that dark oval.  The bands and the spot are carried forward from the build
+this revision corrects without a digit changed.  The companion is the only
+thing added, and it is the only thing this module's numbers move for.
+
+**The bands are here by owner decision, not by measurement, and that decision
+is not reopened.**  An earlier correction removed them, made a real case for
+removing them -- `ref/neptune-sol.png` shows clouds that are SHORT, tilted,
+scattered and not one of them circling the planet, and three closed bands on a
+blue ball read as three painted stripes -- and the owner looked at both
+drawings and kept the bands.  That losing argument is preserved word for word
+in `parts/markings.py` under `"neptune"`.  Nothing here softens, narrows,
+moves or breaks the bands, and nothing here is an occasion to revisit them:
+this revision adds one oval and touches nothing else.
+
+**The companion cloud is what this revision adds.**  The archived build that
+the bands reversed had one -- a white wisp drawn parallel to the spot's upper
+rim -- and reverting the cloud family to three bands took it with it.  The
+sealed report said so in as many words: "`ref/neptune-sol.png` does show a
+bright companion cloud beside the dark spot and this revision does not draw
+one.  That is a deliberate loss."  The owner has now asked for it back, on
+both Neptune pieces, as ONE WHITE OUTLINE OVAL about 10 by 5 degrees of arc,
+at the spot's own longitude, south of it.
+
+It is drawn here rather than in the white band marking, under its own key, for
+the reason the archived build's note gives against itself: a companion that
+lives inside the cloud family disappears whenever the cloud family is
+redrawn.  `companion` is its own marking with its own key, so the next person
+to argue about bands cannot delete it by accident.
+
+**Where it sits: exactly where it was asked for, and what that costs.**  Its
+centre is 8.0 degrees of latitude south of the spot's centre, at the spot's own
+longitude, which is the instruction.  Drawing it there is not free and the cost
+is recorded here rather than discovered later.
+
+The spot is 14 degrees of arc tall, so its own southern rim is already 7
+degrees south of its centre, and an oval 5 degrees tall centred at 8 puts its
+top 1.5 degrees INSIDE the spot.  The obvious answer is to move it further
+south until a printable strip of bare globe fits between the two outlines,
+which needs 11.59 degrees.  **That answer was built, rendered and rejected on
+the evidence.**  `parts/world.py` seats every globe on a cone that springs at
+piece-frame latitude -42, and the planet leans 28.32 degrees, so at the spot's
+own longitude the Sol piece's seat collar covers everything south of about
+-31 degrees of PLANET latitude.  At 11.8 degrees south the oval's centre lands
+at piece latitude -40.9 and ten of its twenty-four ring vertices fall under the
+collar: the Sol piece came back with a pale half-lens sitting on its base
+instead of an oval.  The window between the spot's southern rim and that collar
+is about 2.4 degrees of arc, 0.46 mm, and a marking plus two nozzle-width gaps
+does not fit in 0.46 mm at any size.  The scan is in
+`measure/neptune-atlas-resolution.md`: at every half-axis from 0.8 to 2.4
+degrees there is no latitude that clears both.
+
+So the instruction's own number is kept and the overlap is resolved by cutting
+the spot back -- but NOT back to the companion itself.  That was built first:
+`spot` subtracted `companion`, the two colours shared a boundary, and an
+independent reader shown the finished renders cold called the pair "a notched
+figure-eight" and the new marking "a small grey circle", a lobe budding off the
+dark spot rather than a cloud beside it.  The figure the owner asked for came
+out inverted.
+
+**So the spot is cut to a KEEP-OUT: the companion's own oval grown by 2.30
+degrees of arc, a shape that is never drawn and never printed.**  What survives
+between the two markings is bare blue, 0.42 mm of it at the closest point --
+1.05 nozzle widths, and one nozzle width is the least this set will print a
+colour boundary at.
+The dilation is solved rather than guessed: the offset of an ellipse is not an
+ellipse, so growing both half-axes by one nozzle leaves the two curves closer
+than a nozzle somewhere in between, and 2.19 is only where the two RINGS reach
+0.40 mm apart -- measured against where the DARK actually stops it lands at
+0.3995, a rounding under. 2.30 is the first round tenth above that and measures
+0.4203 mm.
+`parts/world._subtrahend` is the one line of machinery that makes a never-drawn
+subtraction possible, and it exists for this.
+
+**What that costs the dark spot, and it is the largest thing this revision does
+to anything it was told not to change.**  The keep-out is 14.6 by 9.6 degrees
+of arc against the companion's 10 by 5, so where it crosses the spot it takes a
+bay about 15 degrees of arc wide and 3.7 deep out of a 28 by 14 oval: the
+`spot` body falls from the archive's 11.9319 mm3 to 10.5113, a loss of 1.4206.
+The spot's RING is not edited -- its latitude, longitude, half-axes, 40
+vertices and `dark_gray` filament are byte-identical in the source, and
+`measure/neptune-facing.md` reproduces its archived dot products at every frame
+-- and `measure/neptune-mirror.md` measures the spot's own region BEFORE the
+cut at the archive's exact 11.9319 and accounts every cubic millimetre of the
+difference to the keep-out.  What changed is where the dark stops, not where
+the spot is.
+
+That is the whole trade, stated so a reader can disagree with it: the owner
+asked for a bright cloud just south of the Great Dark Spot and said nothing
+else on the piece changes.  At 8 degrees on a spot 14 degrees tall those two
+cannot both hold.  A cloud that touches the spot keeps the spot's outline and
+loses the cloud -- a reader who had never seen the brief saw a lump, not a
+companion.  A cloud held one nozzle clear delivers the cloud and costs the spot
+a bay.  The cloud is what was asked for, so the cloud wins, and the bay is
+disclosed here, in `antisol_spec.md` item 26 and in the product's limitations
+rather than left to be found.
 
-Two things are drawn here, and one piece of arithmetic decides both.
+Two things are drawn here, and one piece of arithmetic decides all three.
 Neptune's globe is Ø21.89 mm, so its radius is 10.945 mm, one degree of
 GREAT-CIRCLE arc is pi * 21.89 / 360 = 0.1910 mm, and the 0.40 mm nozzle is
 2.09 degrees of it.  That factor is pi * d / 360, NOT pi * d / 180: a full
@@ -39,27 +116,16 @@
 ring, no taper, no bow, no tilt, no end cap -- a closed circle of latitude has
 none of those.
 
-**The dark spot does not move, and this is the one decision of the cloud
-correction that stands.**  It was two overlapping `blob` circles at -22 and
--20 before that correction and read as a smudge; the reference shows a clean
-oval about twice as wide as it is tall.  Neptune's Great Dark Spot was about
-13000 by 6600 km on a planet 49244 km across, so one degree of arc is 429.7 km
-and the spot is 30.3 by 15.4 degrees -- taken here as 28 by 14, the exact 2:1
-the correction asked for and within 8 per cent of the measured object.  Its
-latitude, -22, is the real one; its longitude is free, because Neptune turns
-in sixteen hours and this set fixes no meridian.  Its ring, its 40 vertices,
-its latitude, its longitude and its `dark_gray` filament are carried forward
-unchanged, and `measure/neptune-atlas-resolution.md` measures its own
-contribution rather than assuming it did not move.
-
-**The spot's bright companion is gone, and that is a loss rather than a
-tidy-up.**  It was a white wisp drawn parallel to the spot's upper rim at a
-constant 0.60 mm clearance, and it lived in the white cloud marking rather
-than beside the spot, because the marking key in this set is the filament.
-Reverting the cloud family to three bands takes it with it, and the drawing
-the owner is reverting to did not have one.  `ref/neptune-sol.png` does show a
-bright companion cloud beside the dark spot and this revision does not draw
-one.  That is recorded in the product's limitations in those terms.
+**The dark spot does not move, and nothing in this revision asks it to.**  It
+was two overlapping `blob` circles at -22 and -20 two builds ago and read as a
+smudge; the reference shows a clean oval about twice as wide as it is tall.
+Neptune's Great Dark Spot was about 13000 by 6600 km on a planet 49244 km
+across, so one degree of arc is 429.7 km and the spot is 30.3 by 15.4 degrees
+-- taken here as 28 by 14, the exact 2:1 that correction asked for and within
+8 per cent of the measured object.  Its ring, its 40 vertices, its latitude,
+its longitude and its `dark_gray` filament are carried forward unchanged, and
+`measure/neptune-mirror.md` measures its built body against the volume the
+archive recorded rather than assuming it did not move.
 
 Nothing else is on this globe.  `NOT_DRAWN` below carries what was considered
 and refused, and why.
@@ -229,19 +295,126 @@
     return [("outline", [SPOT_RING])]
 
 
+# ------------------------------------------------------- the companion ---
+#: The companion's own half-axes, in degrees of great-circle arc.  The owner
+#: asked for an oval "about 10 by 5 degrees of arc", which is the same way the
+#: spot's size is stated above -- 28 by 14 there, half-axes 14 and 7 -- so 10
+#: by 5 is the whole oval and these are half of it.
+#:
+#: 5 degrees of arc is 0.955 mm on this globe, 2.39 nozzle widths, and it is
+#: the narrowest the white material ever gets: an ellipse's narrowest neck is
+#: its own minor axis.  That is the limit the owner's instruction names, and
+#: `measure/neptune-atlas-resolution.md` measures it on the walked ring rather
+#: than trusting this comment.
+COMPANION_SEMI_ARC_LON = 5.0
+COMPANION_SEMI_ARC_LAT = 2.5
+
+#: Degrees of latitude from the spot's centre down to the companion's centre.
+#:
+#: 8.0 is the owner's own number and it is kept.  It is not a free choice and
+#: it is not a comfortable one: the spot's half-height is 7.0 and the
+#: companion's is 2.5, so at 8.0 the two ovals OVERLAP by 1.5 degrees.  The
+#: module docstring carries the scan that shows no other offset works -- south
+#: of about 9 degrees the Sol piece's seat collar starts eating the oval, and a
+#: printable strip of bare globe between the two outlines needs 11.59 -- so the
+#: overlap is resolved by subtraction rather than by moving the marking.
+#: `parts/markings.py` gives `spot` a `("companion",)` subtraction.
+COMPANION_OFFSET_ARC = 8.0
+
+#: Latitude and longitude of the companion's centre.
+#:
+#: The longitude is the spot's own, exactly as asked.  It is free in the
+#: absolute -- Neptune turns in sixteen hours and this set fixes no meridian --
+#: but it is not free RELATIVE to the spot, and the instruction fixes it.
+COMPANION_LAT = SPOT_LAT - COMPANION_OFFSET_ARC
+COMPANION_LON = SPOT_LON
+
+#: The companion's vertex count, set by the same test the spot's 40 was set by
+#: rather than copied from it.  An ellipse walked at even bearings is furthest
+#: from the true curve at its two pointed ends, and that error falls as the
+#: square of the count and rises with the size of the oval.  The spot is 28
+#: degrees of arc long at 40 vertices and its ends fall 0.017 mm inside the
+#: true ellipse, which is the figure an independent reader's faceting
+#: complaint was answered at.  This oval is 10 degrees long, 0.357 times the
+#: spot, so 24 vertices buy the same smoothness at a coarser count.  Measured
+#: in `measure/neptune-atlas-resolution.md`, which walks both rings and takes
+#: the worst departure of a chord from the true ellipse: the spot at 40
+#: vertices falls 0.031 mm inside it and this oval at 24 falls 0.028 mm
+#: inside.  The shortest edge that leaves is 0.127 mm, against the 0.075 mm
+#: copying 40 across would have left, and like the spot's own 0.21 mm it is a
+#: facet of a smooth curve rather than the width of anything.
+COMPANION_VERTICES = 24
+
+COMPANION_RING = oval_ring(COMPANION_LAT, COMPANION_LON,
+                           COMPANION_SEMI_ARC_LON, COMPANION_SEMI_ARC_LAT,
+                           COMPANION_VERTICES)
+
+
+#: How far the dark spot is held back from the companion, in degrees of arc.
+#:
+#: NOT the companion's own size: this is the KEEP-OUT the spot is cut to, so a
+#: printable strip of bare blue survives between the two outlines instead of
+#: the two colours sharing a boundary.
+#:
+#: 2.30 is solved rather than chosen.  The offset of an ellipse is not an
+#: ellipse, so growing both half-axes by one nozzle width leaves the two curves
+#: closer than a nozzle somewhere in between: 2.19 is where the two RINGS first
+#: reach 0.40 mm apart, and it is not enough, because what a reader and a
+#: slicer see is the distance to where the DARK STOPS -- the spot's own ring
+#: outside the keep-out, plus the keep-out's ring inside the spot -- walked at
+#: a finite step.  Measured that way 2.19 lands at 0.3995 mm, a rounding under
+#: the nozzle.  2.30 is the first round tenth above it and measures 0.42 mm.
+#: `measure/neptune-atlas-resolution.md` re-measures it on the built rings
+#: rather than trusting this comment.
+COMPANION_KEEPOUT_ARC = 2.30
+
+#: The keep-out ring itself.  It is never drawn and never printed: no body in
+#: this set has its shape.  40 vertices rather than the companion's 24 because
+#: it is a boundary of the DARK spot, which is the larger body and is held to
+#: the spot's own smoothness.
+COMPANION_KEEPOUT_RING = oval_ring(
+    COMPANION_LAT, COMPANION_LON,
+    COMPANION_SEMI_ARC_LON + COMPANION_KEEPOUT_ARC,
+    COMPANION_SEMI_ARC_LAT + COMPANION_KEEPOUT_ARC, 40)
+
+
+def companion_keepout_spec():
+    """The region `parts/markings.py` cuts out of the `spot` marking.
+
+    Handed over as a `("spec", ...)` subtraction rather than as a marking key,
+    because nothing is printed here: it is the bare globe the companion needs
+    around it so that the white and the dark never meet.
+    """
+    return ("spec", ("outline", [COMPANION_KEEPOUT_RING]))
+
+
+def companion_specs():
+    """The region specs `parts/markings.py` gives the `companion` marking.
+
+    One `outline` oval, the same region kind and the same construction the
+    spot uses, in `white` rather than `dark_gray`.  It subtracts nothing and
+    nothing subtracts it: it stands clear of every other marking on this globe
+    by more than a nozzle width, which is the whole reason it sits where it
+    sits.
+    """
+    return [("outline", [COMPANION_RING])]
+
+
 # ------------------------------------------------------------ the record --
-#: name -> ring, for the resolution report.  Only the spot is an outline now;
-#: the three bands are circles of latitude and are measured from `BANDS`.
-RINGS = {"spot": SPOT_RING}
+#: name -> ring, for the resolution report.  The spot and the companion are
+#: the two outlines on this globe; the three bands are circles of latitude and
+#: are measured from `BANDS`.
+RINGS = {"spot": SPOT_RING, "companion": COMPANION_RING}
 
 NOT_DRAWN = (
-    "Neptune's globe is Ø%.2f mm, so one degree of arc is %.4f mm and a "
-    "%.1f mm nozzle is %.2f degrees of it. Considered and refused: the "
-    "SPOT'S BRIGHT COMPANION CLOUD -- the reference shows one and the build "
-    "this revision corrects drew one, and it is dropped here because it lived "
-    "in the white cloud marking and the owner has reverted that marking to "
-    "the three latitude bands it was before, which had no companion; it is a "
-    "deliberate loss and the product's limitations say so. Also refused: a "
+    "Neptune's globe is \u00d8%.2f mm, so one degree of arc is %.4f mm and a "
+    "%.1f mm nozzle is %.2f degrees of it. DRAWN, and new in this revision: "
+    "the dark spot's BRIGHT COMPANION CLOUD, one white oval %.0f by %.0f "
+    "degrees of arc at the spot's own longitude, %.1f degrees of latitude "
+    "south of the spot's centre, which overlaps the spot's southern rim by "
+    "1.5 degrees and takes a scallop out of it by subtraction rather than "
+    "moving south, because south of about 9 degrees the Sol piece's seat "
+    "collar covers the oval. Considered and refused: a "
     "SECOND DARK SPOT -- the reference shows one; POLAR BRIGHTENING -- the "
     "reference shows none, and a bright cap on this globe would repeat "
     "Saturn's northern cap on the world two ranks below it; RING ARCS -- "
@@ -253,5 +426,7 @@
     "own fine cloud texture, whose wisps scale to 0.13 - 0.26 mm here, under "
     "one nozzle width, and would print as noise. The set's material rules "
     "forbid deliberate grit."
-    % (GLOBE_D, MM_PER_DEG, P.NOZZLE_MM, NOZZLE_DEG)
+    % (GLOBE_D, MM_PER_DEG, P.NOZZLE_MM, NOZZLE_DEG,
+       2 * COMPANION_SEMI_ARC_LON, 2 * COMPANION_SEMI_ARC_LAT,
+       SPOT_LAT - COMPANION_LAT)
 )
Only in <this-run>/parts: regions.py
diff -ru '--exclude=*.step' '--exclude=measure' '--exclude=snap' '--exclude=__cadgen__' '--exclude=ref' <published>/parts/world.py <this-run>/parts/world.py
--- <published>/parts/world.py	2026-09-23 17:19:28.938105666 +0000
+++ <this-run>/parts/world.py	2026-09-23 23:03:36.640436871 +0000
@@ -42,6 +42,7 @@
     seven_segment_sketch,
 )
 from parts.markings import MARKINGS
+from parts.regions import region_pieces, subtrahend
 
 
 # ------------------------------------------------------------------- disc ---
@@ -164,38 +165,6 @@
 _CLIP_SPINS = (0.0, 0.05, -0.05, 0.11, -0.11, 0.23, -0.23)
 
 
-def _region_pieces(planet: str, spec, nudge: float, first: int = 0):
-    """One tool per patch, so each can be clipped on its own.
-
-    A `blob` spec is several round patches that overlap.  Fusing them first and
-    intersecting the union with the globe's own sphere is what the earlier
-    build did, and `inspect validate` measured the result as self-intersecting
-    on Mercury, Mars and Venus: the union's outer face IS the globe sphere, and
-    a neighbouring patch's tool sphere runs tangent to it along the seam where
-    two patches meet.  Clipping each patch separately gives a stack of clean
-    lenses whose fuse meets along ordinary edges instead.
-
-    `nudge` widens patch *n* by `n * nudge` degrees rather than widening them
-    all equally.  A common widening slides every seam along by the same amount
-    and can land a second pair on the tangency it just left; a graded one
-    cannot, because no two patches move together.
-    """
-    radius = P.globe_radius(planet)
-    depth = P.RELIEF_DEPTH
-    kind = spec[0]
-    if kind == "blob":
-        return [
-            blob_tool(radius, [(lat, lon, ang + nudge * (first + n))], depth)
-            for n, (lat, lon, ang) in enumerate(spec[1])
-        ]
-    if kind == "outline":
-        return [
-            outline_tool(radius, ring, depth, nudge * (first + n))
-            for n, ring in enumerate(spec[1])
-        ]
-    return [_region_tool(planet, spec, nudge * first)]
-
-
 def _split_through_crust(pieces, tool, crust_ball, expect: float):
     """Take a marking out of the globe's outer crust, then put the core back.
 
@@ -290,7 +259,7 @@
         lenses = []
         first = 0
         for spec in specs:
-            pieces = _region_pieces(planet, spec, nudge, first)
+            pieces = region_pieces(planet, spec, nudge, first, _region_tool)
             first += len(pieces)
             for tool in pieces:
                 lens = _sane(X.shape(X.meet(tool, ball)))
@@ -300,7 +269,7 @@
             continue
         region = lenses[0] + lenses[1:] if len(lenses) > 1 else lenses[0]
         for other in subtract:
-            region = region - raw[other]
+            region = region - subtrahend(planet, other, raw, _region_tool)
         region = _sane(region)
         if region is not None:
             regions[key] = region
@@ -644,7 +613,8 @@
             if not inside:
                 cone = solid_regions[key]
                 for other in subtract:
-                    cone = cone - solid_regions[other]
+                    cone = cone - subtrahend(
+                        planet, other, solid_regions, _region_tool)
                 inside, rest_now = _split_through_crust(
                     remaining, placed * cone, crust_ball, X.volume(regions[key]))
             remaining = rest_now
diff -ru '--exclude=*.step' '--exclude=measure' '--exclude=snap' '--exclude=__cadgen__' '--exclude=ref' <published>/README.md <this-run>/README.md
--- <published>/README.md	2026-09-23 17:19:28.933105760 +0000
+++ <this-run>/README.md	2026-09-23 21:50:22.251438858 +0000
@@ -1,4 +1,4 @@
-# Antisol Caelus — CAD project
+# Antisol Companion — CAD project
 
 Dou Shou Qi, unchanged, played with the eight planets ranked by their real
 measured diameters. Sixteen worlds, a four-panel board, twelve asteroid-belt
@@ -11,20 +11,44 @@
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
-
-**One thing this revision gains is worth naming here.** Both ringed worlds now
-print their ring in `white`, so the set's "rings are white" rule holds without
-a footnote for the first time.
+corrected THAT world, not necessarily this one. **This one is Antisol Companion, and it changes no printed part at all.** It
+gives Neptune's Great Dark Spot its bright companion cloud back, on both
+armies: one `white` outline oval 10 by 5° of arc, at the spot's own longitude,
+south of it. `parts/world.build_world` fuses the disc, the globe and the ring
+and never the markings, so both printed Neptune STEPs come out byte-identical
+to the published set's and the change lives entirely in the colour split —
+two new occurrences, `neptune_sol_companion_white` and
+`neptune_anti_companion_white`. The companion was drawn once before and was
+lost when the cloud marking it lived inside was reverted; `antisol_spec.md`
+item 24 recorded that loss as a live recommendation and item 26 records the
+owner settling it. It is its own marking key this time so that the next
+argument about bands cannot take it with them. **Every number the owner gave is drawn
+exactly: 10 by 5° of arc, the spot's own longitude, 8.0° of latitude south of
+the spot's centre. One of them is not free.** The spot is 14° of arc tall, so
+an oval 5° tall centred 8° south of its centre overlaps its southern rim by
+1.5°, and there is nowhere else on this globe to put it: moving it south until
+a printable strip of bare globe fits needs 11.59°, and past about 9° the Sol
+piece's seat collar starts eating it — that build was made, rendered and
+rejected. So the spot is cut back for it. **It is cut back to a KEEP-OUT rather
+than to the companion itself, and that is this edition's one repair**: with the
+spot subtracted straight to the companion the two colours touched, and an
+independent reader shown the renders cold called the pair "a notched
+figure-eight" and the new marking "a small grey circle". The keep-out is the
+companion's oval grown by 2.30°, never drawn and never printed, and it leaves
+0.4203 mm — 1.05 nozzle widths — of bare blue between the two outlines. What it
+costs is a bay about 15° of arc wide and 3.7 deep in the spot's southern rim,
+1.4206 mm³ of an 11.9319 mm³ body. The spot's ring is not edited and its own
+region still measures the archive's exact 11.9319; item 26 and
+`measure/neptune-mirror.md` account for every cubic millimetre of the
+difference. Nothing else in the set changes: Uranus stays bare with a white
+ring, Neptune's three bands stay where the previous revision put them, and no
+other part gains or loses a solid.
+
+**One thing this revision gains is worth naming here.** The set no longer
+carries a known, recorded omission. `antisol_spec.md` item 24 named the missing
+companion cloud as a live recommendation against this build; item 26 closes it,
+and the only thing left on the "considered and refused" list for Neptune is
+what the reference does not show or the nozzle cannot print.
 
 ## File map
 
@@ -71,10 +95,11 @@
 | `measure/seated_clearance.py` | measures whether a world seated on a star or in a corona well shares volume with the flames or tongues |
 | `measure/filament_value.py` | measures Mars's three filaments by value, sealed and as the review renderer shows them |
 | `measure/ice_cap_scan.py` | classifies points around the pole against the built colour bodies |
-| `measure/neptune_atlas_resolution.py` | every Neptune band width and gap against the nozzle, the dark spot's own ring, and the correction of three figures the chain sealed wrongly |
-| `measure/neptune_facing.py` | Neptune's three bands and its dark spot against the view axis at every frame, on both armies, with the spot checked against the archived numbers |
+| `measure/neptune_atlas_resolution.py` | every Neptune band width and gap against the nozzle, the dark spot's own ring, **the new companion oval's own narrowest neck and its clearance from the spot**, and the correction of three figures the chain sealed wrongly |
+| `measure/neptune_facing.py` | Neptune's three bands, its dark spot and **its new companion cloud** against the view axis at every frame, on both armies, with the spot checked against the archived numbers |
 | `measure/neptune_flush.py` | whether any Neptune marking stands proud of its globe, and whether the dark spot's ring is a faceted polygon |
-| `measure/neptune_mirror.py` | the two Neptune pieces body for body, and the dark spot against the volume the archived build measured |
+| `measure/neptune_tone_separation.py` | whether the new companion cloud reads as bright, by the two-render repaint method: one piece built once and rendered twice at one camera with a single region repainted, on both armies at all three product frames |
+| `measure/neptune_mirror.py` | the two Neptune pieces body for body, **both white markings paired across the mirror**, and the dark spot against the volume the archived build measured |
 | `measure/neptune_separation.py` | Neptune beside Uranus and beside Earth at the product's own frame, answered on size, colour, silhouette and surface separately |
 | `measure/uranus_bare.py` | asks three separate ways whether anything at all is still drawn on either Uranus globe: the marking table, the built colour bodies, and whether the globe's volume is its published volume plus both removed hoods |
 | `measure/uranus_ring_tone.py` | renders one Uranus piece twice at one camera with only the ring repainted, to measure what the `white` the owner chose is worth against the `cyan` globe |
@@ -102,7 +127,7 @@
 | `part_world_mars_*` | 2 | Ø33.87 x 17.72 | disc, numeral, globe, two markings — albedo drawn from outline rings, not round patches, and polar caps whose rims are broken by lobes |
 | `part_world_venus_*` | 2 | Ø33.87 x 19.53 | disc, numeral, globe, two markings — the highlands and the plains drawn from the Magellan radar mosaic as outline rings, not round patches, and no cloud pattern of any kind |
 | `part_world_earth_*` | 2 | Ø33.87 x 19.70 | disc, numeral, globe, three markings — drawn from coastline outlines rather than round patches |
-| `part_world_neptune_*` | 2 | Ø33.87 x 24.89 | disc, numeral, globe, two markings — **three closed white latitude bands, not eight short cloud streaks**: −46/−41, +11/+15 and +30/+33, so 5, 4 and 3° of arc wide, which is 0.955, 0.764 and 0.573 mm, each a plain `band` region ringing the whole globe; and the Great Dark Spot as one outline oval twice as wide as it is tall, unchanged by this revision. No companion cloud. The bands are an owner reversal of the cloud correction, recorded in `antisol_spec.md` item 24 with the case it overruled kept at item 22 |
+| `part_world_neptune_*` | 2 | Ø33.87 x 24.89 | disc, numeral, globe, three markings — **three closed white latitude bands**: −46/−41, +11/+15 and +30/+33, so 5, 4 and 3° of arc wide, which is 0.955, 0.764 and 0.573 mm, each a plain `band` region ringing the whole globe; the Great Dark Spot as one outline oval twice as wide as it is tall, unchanged; and **new in this revision, the spot's bright companion cloud** — one white outline oval 10 by 5° of arc (1.910 x 0.955 mm) at the spot's own longitude and 8.0° of latitude south of its centre, its own marking key `companion`, overlapping the spot's southern rim by 1.5° with the spot cut back to a never-drawn keep-out 2.30° outside it, leaving 1.05 nozzle widths of bare blue between the two. The printed STEP is unchanged by it: `build_world` never fuses a marking. `antisol_spec.md` item 26 |
 | `part_world_uranus_*` | 2 | Ø33.87 x 25.98 | disc, numeral, globe, **no marking at all** — this is the one world in the set with a bare globe: one undivided `cyan` sphere, no hood, no cap, no band, no spot. It wore an upright `white` equatorial band, then a `beige` polar hood at each pole, and the owner has now taken those off and put nothing in their place. The argument that built the hoods is kept whole in `parts/markings.py` under a heading saying what happened to it. And the ring, which is geometry rather than a marking and did not move: an upright hoop Ø24.02 x 1.00 mm standing in the planet's own equatorial plane, 7.77° past vertical, 1.00 mm of projection per side, now printed in `white` — the same spool as Saturn's ring — by the same owner decision. It is the ring, not the globe, that makes this piece 25.98 mm tall, and it is now the only thing on the piece besides the ball |
 | `part_world_saturn_*` | 2 | Ø33.87 x 29.00 | disc, numeral, globe, three markings — five bands at unequal widths and unequal spacing, none of them a mirror of another, the two widest drawn as outline rings with a 2.5° wave on each boundary and the rest as plain bands; one of the five in `cocoa_brown` and the other four in `sunflower_yellow`; a bright `white` cap above +58° on the north only — and the ring, which is geometry rather than a marking and is unchanged by this revision |
 | `part_world_jupiter_*` | 2 | Ø33.87 x 29.97 | disc, numeral, globe, four markings — six belts at their real unequal latitudes, the two widest drawn as outline rings with a 2.5° wave on each boundary; five bright `beige` zones between and beyond them; the Great Red Spot as one 13 by 9° oval; and its `cocoa_brown` collar |
@@ -510,21 +535,28 @@
 python <project>/measure/neptune_facing.py  > <project>/measure/neptune-facing.md
 python <project>/measure/neptune_flush.py   > <project>/measure/neptune-flush.md
 python <project>/measure/neptune_mirror.py  > <project>/measure/neptune-mirror.md
+python <project>/measure/neptune_tone_separation.py "$(workshop skills path)/cad/scripts" \
+    > <project>/measure/neptune-tone-separation.md
 python <project>/measure/neptune_separation.py earth \
     > <project>/measure/neptune-earth-separation.md
-# the Neptune-Uranus pair is asked from Uranus's side on this run, by
-# measure/world_separation.py above, because Uranus is the world that changed.
+# the Neptune-Uranus pair is asked from Uranus's side, by
+# measure/world_separation.py above.
 
-python <project>/measure/occurrence_geometry.py <published>/assembled.step > was.json
-python <project>/measure/occurrence_geometry.py <project>/antisol.step      > now.json
+# THIS revision's own comparison. Neptune is the world that changed, so the
+# occurrence comparison is asked with the two Neptune prefixes and everything
+# outside them that gained, lost or moved a solid is a finding rather than a
+# result. `was.json` is measured on the PUBLISHED assembly in
+# `revision-source.zip`, not on anything this run wrote.
+python <project>/measure/occurrence_geometry.py <archive>/make/models/assembled.step > was.json
+python <project>/measure/occurrence_geometry.py <project>/antisol.step            > now.json
 python <project>/measure/saturn_ring_unchanged.py was.json now.json \
     > <project>/measure/saturn-ring-unchanged.md
 python <project>/measure/uranus_bare.py was.json now.json \
     > <project>/measure/uranus-bare.md
 python <project>/measure/occurrence_geometry.py --compare was.json now.json \
-    uranus_sol_ uranus_anti_ > <project>/measure/occurrence-geometry.md
+    neptune_sol_ neptune_anti_ > <project>/measure/occurrence-geometry.md
 python <project>/measure/revision_hashes.py <product-root> <archive-root> \
-    world_uranus_sol world_uranus_anti \
+    world_neptune_sol world_neptune_anti \
     > <project>/measure/revision-part-hashes.md
 ```
 
diff -ru '--exclude=*.step' '--exclude=measure' '--exclude=snap' '--exclude=__cadgen__' '--exclude=ref' <published>/world_views.py <this-run>/world_views.py
--- <published>/world_views.py	2026-09-23 17:19:28.967105119 +0000
+++ <this-run>/world_views.py	2026-09-23 19:11:13.123713498 +0000
@@ -152,12 +152,18 @@
                  "the product's own azimuth: three closed white bands running "
                  "the whole way round a blue globe, unequal in width and "
                  "unevenly spaced, with the dark oval below the lowest of "
-                 "them"),
+                 "them and the small white companion oval nested into that "
+                 "oval's southern rim, which `measure/neptune-facing.md` "
+                 "measures at every frame on both armies"),
         "spot": (-82.0, 0.0,
                  "the Great Dark Spot in the middle of the picture, a clean "
                  "oval about twice as wide as it is tall, low and south of the "
-                 "equator, with bare blue globe all round it and the nearest "
-                 "white band a clear band-width below it"),
+                 "equator, with the small white companion oval nested into its "
+                 "southern rim at the same longitude -- the two touch, and the "
+                 "spot is scalloped where the cloud sits against it -- bare "
+                 "blue globe all round the pair, and the nearest white band a "
+                 "clear band-width below them. This is the frame the companion "
+                 "reads best at on both armies"),
         "opposite": (98.0, 0.0,
                      "the far face: the same three white bands, unbroken, "
                      "because a closed band has no far face -- and no dark "
```
