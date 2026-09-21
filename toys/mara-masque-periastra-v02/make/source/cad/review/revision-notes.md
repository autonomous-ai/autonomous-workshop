# Periastra Syzygy — revision run record

A corrected revision of the published **Periastra**. The published toy is not updated;
this is a separate, unpublished product tree under a distinct working title.

## What changed, and what did not

Exactly two printed geometries change: the **roof** and the **counter**. The base does not
change at all, and no rule, component function, legal choice, ending or player count
changes. English draughts is played unchanged: 8x8 board, 32 dark playable cells, 12
counters a side, men move and capture as before, promotion on the far row, kings as before.

### Per-design STEP hashes against the published set

| design | published `cad/` STEP sha256 | this run | verdict |
|---|---|---|---|
| base | `590aa6c78a8480f8d07e9344af11f075f2dc4350cd8a27462bc8ae4453e8f72c` | `590aa6c78a8480f8d07e9344af11f075f2dc4350cd8a27462bc8ae4453e8f72c` | **IDENTICAL** |
| roof | `ccc484719ce87cc9d3ea33dcfe5e3cde89a33315923484240480ab8dbacf92be` | `5d2d0678d31551e58db866cff87427f3f1e615ba4d600861eb541e96c2543354` | **changed** |
| Sun counter (`single_*`) | `dc16053e6a28841b048039e1caa4e52252595073c4052691fa92a15fd47b0d4f` | `e750eec66811843616d70c6b25e7e03e56c0ab01986516e7382df52f096c540c` | **changed** |
| Moon counter (`forked_*`) | `069fa3e09e1729715f41761835f5623f7c19ccaa786df9e038cbf624b9777c28` | `5a25e9b6612061eb5bc6ae1884c5ba59f5e0ab04051d53e5b641dd7101c25226` | **changed** |

Exactly **3 of the 4 designs changed**: roof, Sun counter (`single_*`), Moon counter (`forked_*`). The base is byte-identical
to the published part, and `measure/check_fit.py` asserts that hash on every run, so the
invariance is a deterministic check rather than a claim.

### Per-part production STEP hashes

Every counter occurrence is an instance of one of the two counter designs, so **25 of the
26 delivered parts change — the roof and all 24 counters — and the base's geometry does not.**

| part key | published `parts/*.step` | this run |
|---|---|---|
| `base` | `dae355bc4c187db0…` | `64967abbc153f716…` |
| `roof` | `b045bda4360e9972…` | `5be96ea49e3435ec…` |
| `single_01` | `404cfdd58567abda…` | `d05a2b654750d3b3…` |
| `single_02` | `39cdc2b1c7bbf227…` | `d054fc720e90fabd…` |
| `single_03` | `36fbadb4fae7cb49…` | `da67b38573e8fb92…` |
| `single_04` | `f667ab3b162fd8f7…` | `ee8a27cb7a3c72c0…` |
| `single_05` | `4afd3d3dfe9833e1…` | `3499dda605570686…` |
| `single_06` | `02e30b57c389f900…` | `364fa6da3ffe01d6…` |
| `single_07` | `49408414acdabdf9…` | `5e78e7ce73ee48c7…` |
| `single_08` | `c05639725cebd2ea…` | `4072c81113c1ecc0…` |
| `single_09` | `29b149506a5b09e5…` | `e5308f5491458e87…` |
| `single_10` | `d3a2f6aaa6685274…` | `bd388e353bc18ab9…` |
| `single_11` | `1ecaf8d971691744…` | `3608780b3276f722…` |
| `single_12` | `c5615bcec9731c48…` | `0b8f687ffc4a4203…` |
| `forked_01` | `e7424515a8e67499…` | `648f570e9d014291…` |
| `forked_02` | `738b9067ef7ed737…` | `2d5be8dcb3246e0d…` |
| `forked_03` | `a8eccc4238c8e81b…` | `d7a732d6e7fcfc47…` |
| `forked_04` | `90d9ea0986ce6349…` | `59ea7931b230b201…` |
| `forked_05` | `747672e903d89652…` | `8f0b6b7baa98fa24…` |
| `forked_06` | `7d0f31fa167e8c8e…` | `fc66ed4d9ed21f2d…` |
| `forked_07` | `a54d1c24d5b4f839…` | `b786c52e69bcff36…` |
| `forked_08` | `cba0fd6262dbec86…` | `8300572ee6416141…` |
| `forked_09` | `81b25254ad5de649…` | `0e38b2479757981c…` |
| `forked_10` | `4568ba045f9a1b89…` | `0345759b93275e1d…` |
| `forked_11` | `70ddc77189ca57c2…` | `99504eeb8d6632f5…` |
| `forked_12` | `371a9f679eb6b0d1…` | `b4bc2c9883b80533…` |

All 26 delivered `parts/*.step` files differ in bytes from the published ones, including
`base.step`, and that is a header artefact rather than geometry: build123d's `export_step`
stamps the wall clock into the STEP `FILE_NAME` header, so the published delivery copies
cannot be reproduced by any later run. This run zeroes that stamp in `export_delivery.py`
and `write_states.py`, so the delivered and evidence bytes are now reproducible run to run
(verified by exporting twice and comparing). The geometry-identity evidence for the base is
the deterministic `cad/part_base.step` hash in the table above, which matches the published
value exactly.

### Part keys: none changed

The 26 structural identifiers in `groups/observatory.json` are unchanged: `base`, `roof`,
`single_01`…`single_12`, `forked_01`…`forked_12`, verified in this run against the published
group file. The delivery assembly package carries the same 26 occurrence names and the same
sealed colours.

### Names that changed — human-facing only

| was | is now |
|---|---|
| single comet | **Sun counter** |
| forked comet | **Moon counter** |
| `part_single_comet.step.py` | `part_sun_counter.step.py` |
| `part_forked_comet.step.py` | `part_moon_counter.step.py` |
| body label `single_comet` / `forked_comet` | `sun_counter` / `moon_counter` |
| "Conical observatory roof with telescope hood" | "Domed observatory roof with shutter slit" |
| product title `Periastra` | `Periastra Syzygy` (working revision title) |

`SINGLE_COLOR` (terracotta) and `FORKED_COLOR` (cream) keep both their names and their exact
values, because they are bound to the `single_*` / `forked_*` part keys.

## Print orientation

- **Base** — bottom down, unchanged.
- **Roof** — backing plate down, dome apex up. `check_overhang` reports 0 unsupported regions
  over 978.1 cm² of surface.
- **Counters** — flat, **plain man face on the bed**, king rebate and plateau upwards. The only
  unsupported region is the symbol pocket ceiling: a bridge of 9.6 mm span (Sun) and 4.8 mm
  span (Moon), both inside the 12 mm bridge allowance.

The correction brief specified the opposite counter pose — king face on the bed, resting on the
12 mm plateau, calling the 2 mm rebate floor "a trivial bridge". Measured, it is not: the rebate
floor is a *full ring*, and `check_overhang` takes a region's span to be the smaller plan
dimension of the whole connected region, which for a ring on a 16 mm disc is 15.8 mm — wider
than the 12 mm allowance. That pose fails with one 120.9 mm² unsupported region
(`trial-b-counter-king-face-down-overhang.md`). Man-face-down passes. The piece is identical
either way up; only the recommended bed face changes.

## Deviations from the correction brief, and why

**Because the brief's own numbers cannot all hold at once**

1. **Sun ball 4.4 mm, not 6.0 mm.** Ball 6.0 + band 1.0 x2 + ray 1.8 x2 = **11.6 mm**, not the
   stated 10.0 mm overall extent. The 10.0 mm extent is fixed independently three times over —
   by "at least 2.0 mm" between the mark and the man-face chamfer (flat face Ø14 ⇒ mark ≤ Ø10),
   by "at least 1.0 mm" between the mark and the king plateau edge (plateau Ø12 ⇒ mark ≤ Ø10),
   and by the moon being "sized to match the sun's 10.0 mm overall extent". Measuring the
   attached `ref-2` against its own Ø16 disc gives a ball of about 4.3 mm, a band of about
   0.94 mm and rays about 1.9 mm long: the image agrees with band, ray length and extent and
   disagrees only on the ball. Shortening the rays instead (ball 6.0, rays 1.0) was built and
   rendered first and read as a cog — the exact failure the brief forbids. Delivered: ball Ø4.4,
   band 1.0 mm, eight rays 1.775 mm long tapering 2.0 → 1.0 mm, tip corners on the Ø10 frame.
2. **Ray inner width 2.0 mm, not 2.6 mm.** With the ball at Ø4.4 the ray inner ends sit at
   r = 3.2 mm, where eight 2.6 mm rays would subtend 46.6° each against a 45° pitch and merge
   into a continuous collar. 2.0 mm keeps them detached, which is the one property the brief
   insists on.
3. **Crescent horn tips 2.17 mm, not "at least 3.0 mm".** A crescent's horns are necessarily
   thinner than its waist, so a 3.0 mm flat tip on a 3.5 mm waist requires truncating so far
   back that the concave bite disappears and the mark stops reading as a moon. Delivered: both
   horns cut square to flat 2.17 mm faces. Neither is pointed and neither is a sliver.

**Because a measured gate failed the literal form**

4. **Rotation-ring seam: square-cut lower wall, flat floor, 2.0 mm wide, 1.0 mm deep, upper wall
   relieved at 50° from vertical.** Built square, the seam's ceiling is a down-facing annulus of
   447.9 mm² whose region span is 178.3 mm, far over the 12 mm bridge allowance, and
   `check_overhang` failed it (`trial-a-square-ring-groove-overhang.md`). A 45° relief was tried
   and still failed, because a surface at exactly 45° tessellates to just under the threshold;
   50° passes with margin and leaves 0 unsupported regions.
5. **Counters print man-face-down**, as set out above.

**Because an independent blind reader could not see what the correction requires**

6. **The slit runs 30 mm of surface arc down the far side, not 30 mm of vertical drop.** On a cap
   only 40 mm high the vertical reading opens the dome to 89 % of its radius; the blind reader saw
   a shell sawn into two lobes and read the whole part as a computer mouse. With the arc reading
   the far half of the cap stays unbroken and the same reader, unprompted, read it as an
   astronomical observatory dome with its shutter open.
7. **The two fork arms rise into prongs clear above the tube**, so the telescope has a visible
   mount. Still two arms of 6 mm, still rising from the solid pier, still fused to both slit walls,
   still nothing cantilevered or floating.
8. **The crescent is drawn on an 8.0 mm outer circle (7.2 mm bite, 3.1 mm offset) rather than
   10.0 mm**, keeping its stated 3.5 mm waist and giving blunter horn tips. At 10.0 mm its
   continuous outer arc sat 1.0 mm inside the king plateau edge at the same 1.2 mm depth as the
   rebate, separated only by a 1.0 mm ridge; the blind reader could see no crescent at all on that
   face — it read as one broken ring round a blank plateau, which defeats the whole point of
   putting the same mark on both faces. At 8.0 mm the band is 2.0 mm and the mark separates
   cleanly. The sun keeps its 10.0 mm frame because eight discrete ray tips do not merge with the
   rebate the way a continuous arc does, so the two marks no longer share exactly one frame.

Nothing else departs. The plate has no notches, cut-outs or holes — the corner notches visible in
`ref-1` are an artefact of that image and were not built. Nothing was added to the roof: no
railing, walkway, ladder, panelling, ribs, rivets, windows or decoration.

## The blind review

One independent critic, blind to the Wish, the brief and the product identity for all four rounds,
and never told what the object was. Reads recorded before any comparison, in `blind-read.md`,
`blind-read-r2.md`, `blind-read-r3.md` and `blind-read-r4.md`.

| round | roof read, unprompted | outcome |
|---|---|---|
| 1 | "a computer mouse" | **failed requirement A** — repaired the slit's far-side run |
| 2 | "an astronomical observatory dome with its shutter open and a telescope poking out" | passed A; moon king face still blank — added fork prongs, cut the crescent back |
| 3 | "an astronomical observatory dome with the shutter open and a telescope inside it" | moon king face *still* read blank — traced to presentation, not geometry |
| 4 | all three lid frames read as an observatory dome on first sight | **no blocking defect survives** |

The round-3 finding was run down rather than argued away: the king-face pocket measures
23.89 mm² on the plateau, exactly the same crescent as the man face, and the plateau top measures
89.2 mm² = π·6² − 23.89. The mark was always there. Flipping a disc mirrors its mark, and this
renderer shades only the walls of a recess, never its floor, so at a fixed camera the king face
presented its mark away from the light. The disc is round, so its mark's bearing on the board is
free; turning the king state to the same bearing the flipped man face lands on made the same
camera show both faces alike. That is a change to the photograph, not to the solid.

Two findings the critic called blocking are recorded as disclosed limitations rather than defects,
because both are properties this correction is required to leave alone:

- **No grip, lip or opening affordance on the closed object.** True, and unchanged from the
  published set: the brief requires the roof to keep resting its flat underside on the four ledges
  "with no skirt, hinge, latch or hardware" and to have nothing else added. The roof is lifted by
  hand off the box, as before.
- **Near-plan legibility of the marks.** At 82° the crowned moon reads as a line over an arc. The
  marks are 1.2 mm recesses — the depth the brief specifies — and a flat-lit renderer cannot shade
  a recess floor. A printed part reads a 1.2 mm recess by shadow; nothing in this run proves that.

`snap/roof/az0_el12.png` and `snap/closed/az0_el8.png` are kept in the evidence deliberately. Square
on to the slit meridian the shutter is edge-on and invisible, and in rounds 2 and 3 the blind critic
read that view as a computer mouse. Every view that can see into the slot reads as an observatory
immediately. The frames are retained so the weakness is visible rather than curated away.

## Limitations

- **This revision no longer matches the Wish's "English draughts between two comet streams"
  wording.** The correction removes the comets and replaces them with the Sun and the Moon. The
  Wish is hash-bound and was not edited, rewritten or re-summarised. The change was directed by the
  host in the correction brief, so the mismatch with the frozen Wish wording is expected and is not
  evidence that the correction failed.
- The 1.0 mm band between the sun's ball and its rays, and the roughly 0.6 mm raised gaps between
  adjacent rays, are below the 3 mm minimum feature width the rest of this set observes. Both are
  1.2 mm shallow relief on a solid disc, not standing walls, so they are a legibility risk at a
  0.4 mm nozzle rather than a fragility risk. The host accepted this deviation in advance. The
  fallback it proposed — a single plain Ø10 pocket with no rays — was **not** applied, because the
  detached-ray mark builds, passes both print gates and is read as a sun on sight. If a physical
  print shows the band closing up, that fallback is the change to make.
- The crescent is visible across the board but reads as a curl rather than specifically as a moon
  at that distance, and it sits off-centre in its face as a crescent must.
- **Motion is unverified.** The run-root `MAKE-OPTIONS.json` has `check_motion: false`, so no motion
  sweep, motion manifest, animation or independent motion review was produced, and the verifier
  records `check_motion` as not run. Nothing here establishes working motion, assemblability or
  physical fit.
- Playtest was not run; this is a Spark route.
- No physical print, tactile fit, strength, durability, comfort or human response is claimed.
