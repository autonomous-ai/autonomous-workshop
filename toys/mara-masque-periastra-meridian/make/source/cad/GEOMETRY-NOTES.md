# Geometry notes, deviations and limitations

Everything here is measured, not assumed. Each item names the tool or the script
that produced the number.

This file has two parts. **Part I** records revision C, the correction in front
of you. **Part II** is the note set carried forward verbatim from the archive
being corrected; it is history and is not rewritten. Where revision C changes a
fact stated in Part II, section C10 says so explicitly.

---

# Part I — revision C: centred yoke, inlaid board

Two defects are corrected and nothing else in the object moves.

## C1. The yoke arms were both 4.000 mm off centre

### The cause, stated plainly

`periastra_lib.py` built the pair with two hand-written offsets:

```python
arm_face = Plane.YZ * Polygon(*arm_profile(), align=None)
arms = Pos(ARM_INNER_X,0,0)*extrude(arm_face,amount=ARM_THICK) \
     + Pos(-ARM_INNER_X-ARM_THICK,0,0)*extrude(arm_face,amount=ARM_THICK)
```

Both offsets are written for an extrusion that runs from x = 0 to x = +4. It
does not. build123d takes the extrusion direction from the **face normal**, and
the face normal follows the **winding order** of the polygon. `arm_profile()`
returns its points in the order that makes the normal point at -x, so
`extrude(arm_face, amount=4.0)` spans x = -4.000 .. 0.000. `Pos(+5)` therefore
landed the arm at [+1, +5] instead of [+5, +9], and `Pos(-9)` landed the other at
[-13, -9] instead of [-9, -5]. Both moved by exactly one `ARM_THICK`.

The consequences were real, not cosmetic. Arm A ended at x = -9.0 while the tube
began at x = -7.5, so it never touched the telescope: a lone 4 mm fin standing
beside it. Arm B lay entirely inside the tube's own x range and carried the
telescope by itself, off its centreline. The object had a one-armed mount.

### The construction that now makes it impossible

```python
one = extrude(arm_face, amount=ARM_THICK)
one = Pos(ARM_INNER_X - one.bounding_box().min.X, 0, 0) * one
arms = one + mirror(one, about=Plane.YZ)
```

The arm is placed by its **measured** bounding box rather than by an assumption
about which way it grew, and the second arm is a mirror of the first. Whatever
the winding order does, the pair is symmetric about x = 0 by construction and the
inner face lands on `ARM_INNER_X`. The reason is written into the source as a
comment beside the code.

### Measured, on the built STEP, before and after

`measure/check_fit.py` imports `part_roof.step` and slices it on a horizontal
plane at three heights inside the slit and below the tube. The "before" column is
the same measurement run against the archive's `part_roof.step`
(`157a1fee7b99...`) under `revision-work/`.

| slice | arm A, before | arm B, before | arm A, after | arm B, after |
|---|---|---|---|---|
| z = 18 | -13.000 .. -9.000 | +1.000 .. +5.000 | **-9.000 .. -5.000** | **+5.000 .. +9.000** |
| z = 25 | -13.000 .. -9.000 | +1.000 .. +5.000 | **-9.000 .. -5.000** | **+5.000 .. +9.000** |
| z = 32 | -13.000 .. -9.000 | +1.000 .. +5.000 | **-9.000 .. -5.000** | **+5.000 .. +9.000** |

Slit walls are at x = -15.000 and x = +15.000 on every slice.

| requirement | measured |
|---|---|
| clear air, arm A to its slit wall | 6.000 mm |
| clear air, arm B to its slit wall | 6.000 mm |
| clear gap between the arms | 10.000 mm, centred on x = 0.000 |
| each arm's overlap with the tube's x range (-7.5 .. +7.5) | 2.500 mm, fused |

Nothing else about the yoke changed: same profile, same `ARM_THICK` 4.0, same
pier, same keel, same strap, same tube, same 35 degree elevation, same muzzle.

### The symmetry gate — the test that would have caught this

`measure/check_fit.py` now cuts `part_roof.step` against its own mirror image
about x = 0 and fails the build if the leftover volume reaches 1 mm3. This is the
real gate: every telescope frame in the previous evidence set was oblique, and at
an oblique angle a fin beside the tube looks like an arm cradling it.

| roof | volume | asymmetric volume (one direction) | as a fraction | two-sided total |
|---|---:|---:|---:|---:|
| archive `157a1fee7b99...` | 985625.9 mm3 | **8987.8055 mm3** | **0.9119 %** | 17975.6111 mm3 |
| this revision | 986005.2 mm3 | **0.0000 mm3** | **0.0000 %** | 0.0000 mm3 |

The one-direction figure is the one the correction brief quoted (8987.8 mm3,
0.91 %); both readings are given so the number cannot be mistaken for the other
convention. After the repair the roof is exactly mirror-symmetric: the boolean
residue is zero, not merely small.

## C2. The board now uses the house tiled-board fit layer

`references/tiled-board-baseline.md` from the Mara Masque inventor skill was read
before any board dimension was fixed, as that skill requires. The clauses relied
on, and every default overridden, with the reason:

| quantity | baseline | this board | carried or overridden |
|---|---|---:|---|
| pocket opening | "Pocket opening — 42 mm — same as the square" | **22.0 mm** | **Carried.** The opening equals the playing square, which here is `CELL` 22.0. |
| inlay | "Inlay — 41.5 mm — undersized against the pocket"; "Total straight-edge clearance — 0.5 mm — 0.25 mm per side when centred" | **21.5 mm** | **Carried UNSCALED.** 0.5 mm total is a fit tolerance, not a proportion; shrinking it with the square would be wrong. |
| pocket depth | "Inlay thickness — 2.6 mm — surface height minus backing floor" (5.0 surface over 2.4 backing) | **2.0 mm** | **Overridden.** The baseline's depth is set by its 5.0 mm playing surface over a 2.4 mm backing. This board's floor is 11.0 mm, so depth is free; 2.0 mm is ten layers at 0.2 mm, enough to seat the inlay without making the pocket a well. |
| inlay thickness | "so the inlay finishes flush" | **2.0 mm** | **Carried.** Flush is not optional — see C4's void figure. |
| backing floor | "Backing floor under each pocket — 2.4 mm — continuous; the pocket is blind, never a hole" | **9.0 mm** | **Carried with margin.** `FLOOR` 11.0 − 2.0. |
| corner chamfer | "Corner chamfer — 2 mm — on every inlay corner and every internal pocket corner" | **1.0 mm** | **Scaled with the square** (2.0 × 22/42 = 1.048, rounded to 1.0). Applied to every inlay corner and every internal pocket corner. |
| chamfers are structural | "Without them, diagonally adjacent dark wells meet at a shared vertical edge and the checkerboard mesh comes out non-manifold. The chamfers leave a material bridge at each junction and the mesh closes." | applied | **Carried.** `measure/check_fit.py` tessellates the built base and asserts the mesh is closed and manifold; see C4. |
| faceted, not circular | "Prefer faceted recesses to circular ones in small detail; they hold their shape at nozzle scale where a small circle degrades." | applied | **Carried.** This is why `SQUARE_CORNER` 1.5, a *rounding* that served the same bridging purpose, is replaced by a plan chamfer rather than kept. |
| count and retention | "Inlays are gravity-seated with no retention feature." | 32 separate inlays, gravity-seated | **Carried as the host chose.** No retention geometry was invented; the baseline states the limit of its own evidence and the host accepted the consequence. |
| clearance direction | "If yours are meant to stay put, that is a different design and needs its own evidence." | 0.25 mm per side, untightened | **Carried.** The fit was not tightened toward interference to stop the inlays falling out. |

`RECESS` 0.8, `SQUARE_BEVEL` 0.3 and `SQUARE_CORNER` 1.5 are gone. They were the
mechanism the fit layer replaces, and `measure/check_fit.py` asserts they are
absent from `periastra_lib.py` so they cannot creep back.

**Why geometry alone could not have fixed this.** The set is printed opaque, one
colour per part, and the evidence renderer shades from the surface normal alone
with no cast shadows and no ambient occlusion, so two flat horizontal faces at
different heights come out exactly the same tone. Only sloped faces, vertical
faces and outlines carry signal. A 0.8 mm recess with a 0.3 mm lip gave a seated
player one faint outline. The baseline's answer is not geometry: the dark squares
are separate parts in a contrasting filament, which `SKILL.md` permits in terms —
"Color alone is an acceptable way to identify sides, ranks, and other state."
The inlays are sealed `Color(0.12, 0.16, 0.32)`, a night-sky indigo against the
base's pale grey-blue `Color(0.72, 0.78, 0.81)`.

## C3. One baseline clause deliberately not used

The baseline says: "**At panel seams the corners open square instead.** Chamfering
there leaves thin tapering wedges that fail a fixed-nozzle wall-thickness check."

That clause is **not used here**, deliberately. It exists because Civic Skyline is
a 384 mm board quartered into 192 mm panels to fit a 220 mm bed. This board is a
single 176 mm playing field on a 190 mm base and has no seams at all, so there is
no seam corner to open square. Every pocket corner gets its chamfer.

## C4. The numbers the fit layer buys, measured on the built STEPs

All of these are asserted by `measure/check_fit.py`, which reads
`part_base.step`, `part_inlay.step` and `part_sun_counter.step`, not the source
that made them.

**VOID.** The inlays finish flush, so they consume **zero** of the storage void.

| quantity | measured |
|---|---:|
| board floor, measured at a light cell | z 11.000 |
| pocket floor, measured at all 32 dark cells | z 9.000 |
| roof-seat ledge top | z 21.000 |
| storage void | **10.000 mm** |
| counter height, measured on `part_sun_counter.step` | 7.000 mm |
| clear above a stored counter | **3.000 mm** |

**FLUSH.** Pocket floor 9.000 + inlay thickness 2.000 = 11.000, against a board
floor of 11.000. Flushness error **0.000 mm**, against a 0.05 mm allowance.

**FIT.** Pocket opening 22.0 against an inlay measured at 21.500 across:
**0.250 mm per side**. Pocket depth measured at **2.000 mm** on **9.000 mm** of
continuous backing, against the baseline's 2.4 mm minimum. Every pocket is blind:
subtracting the built base from a 176 × 176 × 9.0 slab leaves nothing.

**PLACEMENT.** The void through the board at mid-pocket depth was compared, as a
boolean residue, against the exact union of 32 chamfered 22.0 mm prisms at the
grid centres. Residue **0.000000 mm3**: exactly 32 pockets, exactly at the cells
satisfying `(file + rank) % 2 == 0`, nothing else cut. a1 is dark and h1 is
light, the identity the baseline says to check.

**SEAT.** The counter is 20.0 mm across and sits on a flat inlay top. The chamfer
line stands **14.4957 mm** from the inlay centre — (21.5 − 1.0)/√2 — against the
counter's **10.000 mm** radius, so the chamfer is nowhere near it. Proved as a
boolean rather than as arithmetic: a Ø20.0 × 2.0 cylinder subtracted from the
built inlay leaves **0 mm3**.

**BRIDGE.** At each diagonal junction two chamfered pocket corners face each
other. Measured across the junction on the built base with a 0.02 × 0.2 mm probe:
**1.414 mm**, which is 2c/√2 at c = 1.0. See C5 for the disclosure.

**MESH.** The built base tessellates to 2580 triangles forming a closed,
manifold, consistently wound shell: every directed edge appears once and every
edge has its opposite. This is the baseline's stated reason for the chamfers, and
it is checked rather than assumed.

## C5. Deviation from the set's 3 mm minimum feature rule

The 1.414 mm diagonal bridge is below the 3 mm minimum feature width the rest of
this set observes. It is disclosed here with its reasoning and its measured
number, and it was not engineered away.

It is **not a freestanding feature**. It is a ridge 2.0 mm tall fused along its
whole length to a continuous 9.0 mm slab — nothing that can snap off, and nothing
a slicer has to bridge. `check_thickness` passes `part_base` at a 0.4 mm nozzle;
1.414 mm is about 3.5 extrusion widths.

The baseline's own gate-passed product carries the same detail at 2c/√2 = 2.828 mm
on a 42 mm square. Scaled to this 22 mm square that is 2.828 × 22/42 = **1.482 mm**,
so 1.414 mm is **4.55 % under** the baseline's own proportion. The whole of that
shortfall is the chamfer being rounded from 1.048 down to 1.0.

The correction brief's fallback, if it will not print, is to raise the chamfer,
and there is room: the seat calculation above shows c could go to 7.36 mm before
the chamfer line reached the counter's 10.0 mm radius, and c = 1.048 alone
restores the baseline's proportion exactly. That headroom is recorded here so the
next revision does not have to rediscover it. It was not taken now because 1.0 mm
is the brief's stated intended value and the measured bridge clears the nozzle
minimum by a wide margin.

## C6. One disclosed limitation, deferred by the host: the open reveal and the loose inlays

These two facts are recorded together because they are one problem.

- **The perimeter reveal is open.** The base wall drops to z 17.000 along the four
  side spans, retaining z 24 corner piers, and the roof plate underside seats at
  z 21.000. Measured on the built base, the reveal is **4.000 mm** tall and runs
  right round the perimeter.
- **The 32 inlays are loose.** They are gravity-seated with no retention feature,
  2.000 mm thick, and 2.000 mm is less than 4.000 mm. Tip the closed box and the
  inlays can leave through the reveal.
- A **counter** cannot. Its smallest dimension is its 7.000 mm thickness, against
  a 4.000 mm reveal, so no counter passes through it in any orientation. That is
  the measurement, and it is stated here rather than softened: the loss on tipping
  is the inlays, and the counters stay in.

Closing the box would resolve both at once. **The host scoped this out of this
revision and it was not attempted.** `LEDGE_TOP` and `SILL_TOP` are untouched.
Civic Skyline, whose fit layer this is, does not self-store and never had to
answer this; Periastra does, and this is the answer it currently has.

## C7. Part count before and after

| | archive | this revision |
|---|---:|---:|
| geometry families (print entries) | 4 | **5** |
| printed objects | 26 | **58** |
| `groups/observatory.json` part keys | `base`, `roof`, `single_01..12`, `forked_01..12` | the same 26, plus `inlay_01..inlay_32` |

`measure/revision_diff.py` asserts that every archive part key is still present
and that the only additions are the 32 inlays.

## C8. The counter hashes, asserted and unchanged

The two counters are finished and come out of this revision byte for byte
identical to the archive:

| part | sha256 | verdict |
|---|---|---|
| `part_sun_counter.step` | `262ccc86f6e4c40394e8611fd0f98ee7a7aaf2ec5b3e42fab36d66902afe5f3b` | **unchanged** |
| `part_moon_counter.step` | `588d285baf2e312d81ca39c92ddad82ff83725aa721f5a5789ffb1a0ec50301e` | **unchanged** |

`measure/check_fit.py` asserts both on every run and fails the build if either
moves. The crescent, the sun, the rim band, the field depth, the symbol relief,
the tip fillets and `COUNTER_DIAMETER` were not touched. For reference, the two
parts this revision does change hashed `157a1fee7b99...` (roof) and
`590aa6c78a84...` (base) in the archive; both are expected to move and do.

## C9. Motion is unverified for this revision

The immutable run-root `MAKE-OPTIONS.json` has `check_motion: false`. No motion
sweep, no motion manifest, no operating animation and no independent motion
review were run. Motion is **unverified, never passed**. Nothing here claims the
roof is assemblable, that it seats, or that the inlays seat. The roof's 0.8 mm
per-side lateral clearance and the inlays' 0.25 mm per-side clearance are
algebraic and boolean fit results from `measure/check_fit.py`, not motion results.

## C10. What this revision changes in Part II

Part II is kept verbatim. Two of its statements are superseded by revision C and
are listed here rather than edited out of the history:

- **Part II section 6, second bullet** ("The board has no colour contrast… the 32
  dark cells are distinguished by a 0.8 mm recess in a single-material print") is
  the defect this revision corrects. The dark cells are now 32 separate inlays in
  a contrasting filament; see C2.
- **Part II section 6, first bullet** describes the closed box as retaining its
  contents. That remains true of the counters and is re-measured in C6, but it is
  now incomplete: the inlays this revision adds are thinner than the reveal and
  can leave through it. C6 is the current, complete statement.

Everything else in Part II still holds. In particular Part II section 1 — the
counters' `check_overhang` span-proxy failure and the resulting
`digitally-verified-not-print-ready` status with `print_ready_claim: false` — is
unchanged, because the counters are frozen and could not be altered here even if
it were wanted. Revision C adds two print entries to that table:

| part | gate | verdict |
|---|---|---|
| `part_base` (rebuilt with pockets) | overhang, thickness | PASS |
| `part_inlay` (new) | overhang, thickness | PASS |
| `part_roof` (rebuilt with the centred yoke) | overhang, thickness | PASS |
| `part_sun_counter`, `part_moon_counter` | thickness | PASS |
| `part_sun_counter`, `part_moon_counter` | overhang | **FAIL**, unchanged and disclosed |

Because two printable parts still fail a print gate, **this product makes no
print-ready claim**, its sealed status stays
`digitally-verified-not-print-ready`, and the signature review binds no
print-gate reports.

## C10b. One re-measured diagnostic number

`measure/bridge_audit.py` is a diagnostic script, not a gate: it approximates the
crescent's filleted outline with shapely erode/dilate buffers to find the largest
circle that fits inside the unsupported field floor. Re-run in this environment
it reports the Moon counter's unsupported area as **108.59 mm2** where the
archive recorded **112.08 mm2**. The counter's STEP is byte-identical
(`588d285baf2e...`, asserted), the free bridge is unchanged at 9.75 mm, the Sun
counter's figures are identical to the archive's, and both gate verdicts are
unchanged. The difference is in the script's own polygonal approximation of the
0.45 mm tip fillets, not in the geometry. Both numbers are recorded here rather
than one being quietly replaced.

## C11. On the isolated-component gate

Every one of the five print entries was given its own isolated `make_round`
review-and-fix loop. `base`, `inlay` and `roof` pass theirs outright.
`sun_counter` and `moon_counter` pass build, wall and visual inspection and fail
only the `check_overhang` span proxy described above, so their component rounds
are recorded as failed. The assembled-object round was therefore run **without**
`--require-component-passes`: that flag's precondition cannot be satisfied
without changing counter bytes this correction freezes. The failure is reported
unchanged at component level, at assembly level and in the product's sealed
status. No threshold was lowered and no gate was skipped.

## C12. The evidence set, and the two frames section C of the brief required

Every frame the archive carried is regenerated here from the new geometry and
none is removed; `cad/render_family.py` is the frame table, so the set is
reproducible rather than assembled by hand. The brief required two additions in
the FIRST review round, because both of the defects it corrects survived the last
review only for want of a frame that pointed at them:

- `snap/roof/slit-plan_el90.png` and `snap/roof/slit-plan-close_el90.png` —
  straight down on the roof, the second cropped to the slit at about 21.7 pixels
  per millimetre. The blind critic was asked directly whether the mount is in the
  middle of the slot or off to one side.
- `snap/board/empty-plan_el90.png` and `snap/board/populated-plan_el90.png` —
  the whole board, empty and set out, at 1800 px. An unprimed critic was asked
  whether the playing surface is chequered and to point out the squares.

Neither requirement was allowed to be matched on an oblique frame or a close-up.
Two further added frames, `board/empty-oblique_az-45_el35.png` and
`board/populated-oblique_az-45_el35.png`, and a close crop
`board/inlay-seat_az-60_el22.png`, carry the seated-player angle and the joint
between an inlay and its pocket.

**One evidence repair was made after the blind read, and no geometry moved with
it.** The critic found that `board/populated-plan_el90.png` at 1200 px was
byte-identical to the carried-forward `playing/top_el90.png` and therefore added
nothing. Both board plan frames were re-rendered at 1800 px, which is what "at
whole-board scale" was asking for. The part STEPs, `snap/iso.png` and
`snap/signature.png` are byte-identical to the ones read blind.

## C13. A divergence between the frozen sun counter and its reference art

The independent critic, measuring pixels rather than reading the source, found
that the Sun counter's eight wedges do not have the proportions drawn in
`ref/ref-02-ref-2-sun-face.png`. It is right, the divergence is real, and it is
recorded here rather than argued away — but it is **not a change this revision
made**, and this revision is forbidden to close it.

**The part did not move.** Three independent facts:

| evidence | archive | this revision |
|---|---|---|
| `part_sun_counter.step` sha256 | `262ccc86f6e4c403…afe5f3b` | **the same bytes** |
| `snap/counters/sun-plan_el90.png` sha256 | `245bd93d86cd36f9…` | **byte-identical image** |
| `snap/counters/sun-oblique_az-90_el22.png` | `017525622497d206…` | **byte-identical image** |

The archive carries its own renders of its own counter, made by the same renderer
at the same cameras. Not one pixel differs. The renderer is therefore removed
from the question entirely.

**What actually differs.** From the source, the wedges run from radius 4.25 to
radius 6.25 — a radial length of 2.00 mm — and are 1.8 mm wide at the inner end
and 2.2 mm at the tip, so about 2.0 mm mean width. Aspect **1.0 : 1**, a square
nub. The critic measured 0.93 : 1 off the render, which is the same number within
its error. `ref-02` draws its rays at roughly **2.8 : 1**: long, slim and
strongly tapered, spanning the field. It is stylised reference art with soft
lighting, gradients and a textured ground, not a render of the CAD, and the built
part has never matched it in that respect — in the archive or here.

**Why it is not closed here.** The brief freezes the counters twice over: by
sha256, and in words — "Do not touch the crescent, the sun, the rim band, the
field depth, the symbol relief, the tip fillets, or COUNTER_DIAMETER." Restoring
the reference art's ray proportion means changing the sun, which breaks the
byte-identity the same brief requires. The two cannot both be satisfied, and the
brief resolves it itself: the hashes are the binding requirement, and the
references are "shown so you can confirm the counter you must not touch."

Recorded with the critic's numbers for whoever commissions the next revision:
at matched disc scale the archive's reference ray measures about 46 x 130 px
against the built part's 75 x 70 px, and the dimensionless ratio of wedge radial
length to island radius is 1.0 in the reference art against 0.55 in the part.

## C14. Two inherited blemishes this revision is not permitted to touch

Both were found by the independent critic on this revision's own frames, both are
unchanged from the archive, and both are outside the two defects the brief names.
"Nothing else in this object may move," so neither is repaired.

- **The two orientation marks sit one whole cell off the board centreline.**
  `STAR_X` is 22.0, which is a file boundary one 22 mm cell to the right of the
  board's own centre at x = 0. Measured on the solid, each mark is a **raised**
  half-disc 0.8 mm proud spanning y 88.0 to 91.0, and the board field ends at
  y 88.0, so a mark abuts the edge of its rank-8 square along a line and does not
  cut into the playing surface. At 1800 px the offset is unmistakable; the
  critic's reading of it as a 2.7 mm bite out of a square is a tangency at that
  resolution. They appear on the top and bottom margins only.
- **The yoke's foot block projects outboard of the drum face and terminates in
  raw untreated flats,** visible in `snap/roof/three-quarter_az-135_el28.png`.
  The pier, its y extent and the keel are all on the brief's frozen list; only
  the arms' x position was permitted to change. The critic recorded it as a
  non-blocking caveat: the one part of an otherwise clean corrected assembly that
  still looks like stock rather than a designed detail.

## C15. The five print designs are byte-reproducible; the combined assembly is not

Measured, because the archive's README made a reproducibility claim and this
revision had to check whether it still holds and how far it reaches.

**It holds for everything that gets printed.** Exporting the whole delivery twice
in succession reproduced all 58 production STEP files byte for byte, and the five
print designs regenerate to the same sha256 across runs — which is exactly why
the frozen-counter gate in `measure/check_fit.py` works at all.

**It does not hold for the combined `periastra.step`.** Three consecutive
`gen periastra.step.py --write --force` runs produced three different sha256 for
the same source and the same geometry. Diffing two of them: identical size,
identical line count, 787 differing lines, all of them in the STEP's
`STYLED_ITEM` / `OVER_RIDING_STYLED_ITEM` colour-assignment block. The colour
*content* is correct and stable — a census of the delivered assembly finds each
of the five colours exactly twice, and the delivered `assembled.step.json`
package assigns 32 indigo, 1 teal, 1 slate, 12 terracotta and 12 cream across its
58 occurrences — but the order in which cadgen emits those style entities varies
between runs.

This is a property of the toolchain's assembly styling, not of this source, and
it touches no printable part and no dimension. It is recorded so that a
byte-comparison of `assembled.step` against a fresh rebuild is not mistaken for a
geometry change. `parts/*.step` is the stable per-part record, and
`groups/observatory.json` seals all 58 of those hashes.

---

# Part II — notes carried forward from the archive being corrected

Kept verbatim. See C10 for the two statements revision C supersedes.


## 1. The product makes no print-ready claim

`check_overhang` **fails** both counters. It is not a build failure and it is not
a wall failure; it is the gate's span proxy.

| part | gate | span proxy | allowance | verdict |
|---|---|---|---|---|
| `part_base` | overhang, thickness | — | — | PASS |
| `part_roof` | overhang, thickness | 7.9 mm bridge | 12 mm | PASS |
| `part_sun_counter` | thickness | — | — | PASS |
| `part_sun_counter` | overhang | 13.7 mm | 12 mm | **FAIL** |
| `part_moon_counter` | thickness | — | — | PASS |
| `part_moon_counter` | overhang | 13.7 mm | 12 mm | **FAIL** |

The unsupported region is the field floor of the face that lies on the bed: the
flat annulus from the raised symbol at Ø12.5 out to the field wall at Ø14.0, plus
the bay inside the crescent. It is connected all the way round, so the gate's
proxy — the smaller plan dimension of the whole connected region — reports the
full field diameter, 14.0 mm as designed and 13.7 mm as tessellated.

`measure/bridge_audit.py` measures the physical number, the largest circle that
fits inside that unsupported region, which is the longest straight run of
filament with no supported material under either end:

| part | gate span proxy | real free bridge | unsupported area |
|---|---|---|---|
| `part_sun_counter` | 14.0 mm | **2.40 mm** | 89.3 mm2 |
| `part_moon_counter` | 14.0 mm | **9.75 mm** | 112.1 mm2 |

The physical number is the free bridge, and both are inside the 12 mm allowance.
The counter has not been redesigned around the proxy: the 0.75 mm of clear field
between the symbol and the field wall is a requirement of the correction, and it
is what makes the region connected. The honest consequence is recorded rather
than engineered away — the sealed product status is
`digitally-verified-not-print-ready`, `print_ready_claim` is `false`, the
signature review binds no print-gate reports, and nothing in this product calls
itself print-ready.

## 2. The crescent's horn rounding is 0.45 mm, not the 0.9 mm the brief named

This is a deliberate, measured departure from a number in the correction brief,
made under the brief's own instruction to verify every number before building and
to preserve, above all, the two conditions it named: the crescent stays slim, and
its horns wrap past the middle.

The two circles that draw the crescent meet at a **27.13 degree cusp**. A tangent
fillet of radius R in a cusp of angle A consumes R / tan(A/2) of horn along each
flank — 3.74 mm at R = 0.9. Built at 0.9 mm and then measured on the profile the
CAD actually extrudes:

| built rounding | surviving area | wrap | horn tip at |
|---|---|---|---|
| none (sharp outline) | 37.85 % | 232.7 deg | x = +2.77 |
| **0.45 mm (built)** | **36.95 %** | **206.6 deg** | **x = +1.36** |
| 0.90 mm (as the brief named) | 34.11 % | 178.6 deg | x = **-0.07** |

At 0.9 mm the horns stop just short of the middle and the shape spans 178.6
degrees. That is the 180 degree banana the host rejected on sight, reproduced
exactly. The brief's own "resulting wrap 233 degrees" and "horn tips at (+2.78,
+/-5.60)" describe the sharp outline before any fillet, and its "1.8 mm rounded
nose" is that fillet's chord; the two cannot both survive.

0.45 mm is the smallest rounding that still works, and the limit is not
arbitrary: the correction also requires a 0.3 mm 45 degree bevel round the top of
every raised island, which needs 0.6 mm of nose before it can be cut at all. At
0.25 mm the part **fails to build** — the chamfer operation throws. At 0.45 mm
the nose is 0.88 mm across, it carries its bevel, and `check_thickness` passes
the part at a 0.4 mm nozzle.

Nothing else about the crescent moved. The belly was not thickened, the two
circles were not changed, the horns were not shortened by any other means, and no
tip is cut square. Measured cost against the sharp outline: 26.1 degrees of wrap
and 0.90 points of area. `measure/crescent-metrics.json` and
`snap/counters/moon-symbol-notes.md` carry every number.

## 3. The 0.88 mm horn noses are below the set's 3 mm minimum feature width

This is the deviation the correction brief disclosed and accepted, at a smaller
size than it expected — 0.88 mm rather than 1.8 mm, for the reason in section 2.
They resolve as about 2.2 extrusion widths at a 0.4 mm nozzle. They are the
tapering ends of a raised band 1.5 mm tall that is fused to the disc along its
whole length: not a standing wall, not a cantilever, and nothing that can snap
off. `check_thickness` passes `part_moon_counter` at 0.4 mm with 0.0 % of its
surface below the 0.80 mm limit. The brief's fallback was to raise the fillet to
1.2 mm; that was not taken, because it moves in the wrong direction — a larger
fillet eats more horn, and 1.2 mm would leave roughly 165 degrees of wrap.

## 4. Motion is unverified

The immutable run-root `MAKE-OPTIONS.json` has `check_motion: false` for this
run. No motion sweep, no motion manifest, no operating animation and no
independent motion review were run. Motion is **unverified, never passed**.
Nothing here claims that the roof is assemblable, that it seats, or that any
mechanism works. The roof seats by gravity on four ledges with 0.8 mm of nominal
lateral clearance per side; that clearance is an algebraic fit result from
`measure/check_fit.py`, not a motion result.

## 5. Nothing physical has been tested

Digital verification only. No physical print, tactile fit, strength, durability,
comfort, discoverability or human playtesting has occurred. Playtest was not run
for this Spark route. Renders are appearance evidence; they cannot establish a
dimension, a clearance or a successful print.

## 6. Two open characteristics inherited from the unchanged base

The correction requires the base to come out byte-identical, so neither of these
was touched, and neither is a defect introduced by this revision. Both were
raised by the independent reviewer and are recorded rather than argued away.

- **The closed box is not sealed, but it does retain its contents.** The base
  wall drops to z17 along the four side spans, retaining z24 corner piers, and the
  roof plate seats at z21, so an open reveal runs round the perimeter through
  which the stored counters are visible. That is the published set's deliberate
  sightline. The independent reviewer read it as a spill risk and said the
  question was one measurement: reveal height against counter thickness. Measured
  on the solid, the reveal is **4.0 mm** and a counter is **7.0 mm** thick and
  20.0 mm across, so no counter can pass through it. `measure/check_fit.py`
  asserts that. The box is open to the eye and closed to its contents.
- **The board has no colour contrast.** The 32 dark cells are distinguished by a
  0.8 mm recess in a single-material print, not by colour, so the chequer pattern
  is quiet at a distance.

## 7. Render limitations

`render_review` applies deterministic flat shading with no ambient occlusion.
Where the top of a raised symbol and the top of the rim band are coplanar — which
is exactly what the correction requires — a straight-down frame gets no shading
difference between them, so the plan frames understate the relief and, for the
crescent, reduce it nearly to an outline. **The oblique frames are the evidence
for relief and step height; the plan frames are not offered as proof of
legibility on their own.** The dome and the disc rims are visibly faceted in the
renders; that is the renderer's tessellation, not the geometry. The delivered
STEP is exact.

## 8. Wish tension, already disclosed

The frozen Wish for the published set says "English draughts between two comet
streams". The previous correction removed the comets in favour of the Sun and the
Moon and this correction continues that. The Wish is hash-bound and has not been
edited, rewritten or re-summarised. The revision no longer matches the Wish
wording, the change was host-directed, and the mismatch is not evidence that the
correction failed.

## 9. Crowning has one honest shortage

A player crowns by stacking one of their own captured counters on the promoted
piece, which is how an ordinary draughts set works. A position exists in which a
player reaches the far row before any of their counters has been captured, and in
that position the set supplies nothing to stack. It is uncommon but it is real.
The host chose to keep the set at twelve a side rather than add spares. The
game's rules, powers, probabilities and legal choices are unaffected; what is
affected is the token, and players resolve it as they would with any twelve-a-side
set.
