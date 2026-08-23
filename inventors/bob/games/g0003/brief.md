# CLEARANCE (g0003) — parts brief

Contract for the CAD builder. Implement literally. Every number here has been
checked against every other number here; where a dimension in `bill.json` /
`rules.md` could not survive that check, the supersession and its arithmetic
are written out in §7. Build from this document, not from the bill.

---

## The wound

**Mechanism:** the detent screw column — a printed M16×2.0 screw whose base
collar carries four symmetric notches riding a printed leaf spring, so one
quarter turn is one felt, heard, uncountable-by-eye *click* of exactly
0.5 mm of bar travel.

**What it must DO:** from the hard top stop, 31 consecutive down-clicks lower
the bar by 15.50 ± 0.15 mm total, each click 0.500 ± 0.05 mm, each click
audible and distinct at one turn per second, **identical in sound and feel
up and down**, and the yoke must not back-drive — release the knob at any
click and the bar height must not change by more than 0.02 mm in 60 s.

**Why print is load-bearing:** the game's only hidden information is the
*direction* of eight clicks made under a hood, so the click must be a
tuned compliance — a cantilever whose ramp geometry and spring section are
iterated at quantity one, reprinting a 2 g part, not cut into steel.

**Physics question to prove first (golden part):** does one click equal
0.5 mm, repeatably, silently-in-direction, without back-drive? Print only
`column_screw`, `detent_leaf`, and a 60 × 60 stub base with a dial-indicator
post. Test:

1. Dial-indicate the yoke face. Click down 31, up 31, ×5 cycles. Per-click
   0.500 ± 0.05; return-to-zero ≤ 0.15 mm cumulative.
2. Blind-listen test: 6 people, 20 clicks each in a randomised up/down
   sequence, must not beat 55% at calling the direction. Anything above that
   and the game has no hidden information.
3. Hang the yoke's mass (70 g) on the nut, release at 10 random clicks,
   read after 60 s. Any creep > 0.02 mm and the thread form is wrong.
4. **Human read test** (the fun target, run once the gantry stub is up):
   6 people, 10 random gaps. They must beat chance sorting "does my block
   fit" at a 1.0 mm margin and sit near chance at a 0.5 mm margin. That
   split *is* the game. If they are at chance at 1.0 mm the gap is not
   readable and no CAD work will fix it.

Do not start the full build until 1–3 pass.

---

## 1. Architecture (read once before any part)

- The screw is **axially fixed** and rotates in a journal in the base. The
  **yoke is the nut** and translates. The detent crown is on the screw's
  bottom collar; the leaf lives in the base.
- The yoke is held against rotation by a smooth **guide post** 190 mm away.
- The bar lies loose in two V-saddles on the yoke's end blocks. Its lowest
  surface point, measured from the runway (the base's top face), is the
  **bar height** `H_bar`.
- Travel is 31 clicks. `H_top` = bar height at the hard top stop.
  `H_bottom` = `H_top` − 15.50.
- **`H_top` is measured, not designed.** See §5 — this is what removes the
  calibration problem entirely.

Datum stack, all Z measured from the runway:

| feature | Z (mm) |
|---|---|
| runway (datum) | 0.000 |
| screw shroud top (fixed, integral to base) | 24.0 |
| yoke skirt bottom rim, at `H_bottom` | 2.5 |
| yoke skirt bottom rim, at `H_top` | 18.0 |
| saddle V apex (moves with yoke) | `H_bar` − 1.657 |
| bar axis | `H_bar` + 4.000 |
| yoke bridge underside | `H_bar` + 11.0 |
| knob underside / top of thread relief | 76.0 |
| knob top face (hood seat) | 90.0 |

---

## 2. Printed parts

Bed 256; every part must fit **251 × 251 × 251** flat, no diagonal tricks.
Largest part here is the yoke at 224 mm. ✅

| part_id | qty | envelope mm (x×y×z) | critical dims + tolerance | mates + fit class | material / infill | why it exists |
|---|---|---|---|---|---|---|
| `gantry_base` | 1 | 220 × 78 × 10 | runway flatness ≤0.15 mm TIR over the 130 mm lane; screw journal ⌀22.4 +0.10/−0.00 × 9 deep; post socket ⌀11.90 +0.00/−0.05 × 10 deep; socket axes 190.0 ±0.10 apart and both perpendicular to the runway within 0.1°; screw shroud ⌀24.0 OD × 24.0 tall, coaxial with journal ±0.15; leaf socket 34.2 × 4.3 +0.10/−0.00 | post → **transition/light press** (0.10 interference); screw collar → **running clearance** 0.40 diametral; leaf → **snap**, 0.10 interference | PLA/PETG, 3.0 mm runway skin, ribbed underside, 10% gyroid; **three ⌀16 feet** (two front corners, one rear centre) so it cannot rock on any table | the runway is the datum every bar height is measured from, and the only thing a block slides on |
| `column_screw` | 1 | ⌀44 × 104 | thread M16 × 2.00 single start, major ⌀16.00 +0.00/−0.15, **pitch cumulative error ≤0.10 over the 15.5 mm working length**; detent crown: 4 notches at 90.0° ±0.3°, **symmetric V, 30°/30° ±1°**, 0.80 deep, on a ⌀24 collar; collar ⌀22.0 −0.10/−0.00 × 8; knob ⌀44 × 14, top face flat ±0.10 | yoke nut → **running clearance**, 0.35 total diametral on flanks; base journal → running; leaf nub → sprung contact | PLA, **0.15 mm layers**, 4 perimeters, 40% infill, printed knob-up, no supports on the thread | THE mechanism — the click |
| `detent_leaf` | 1 | 34 × 12 × 4 | **spring section 1.60 +0.05/−0.05 × 12 wide × 24 free length** (the tuning dimension); nub ⌀3.0 hemispherical, **symmetric**; root block 4.0 × 12 × 10 | base socket → snap, 0.10 interference | PLA, 100% solid, printed flat, spring section in-plane so layers are not the bending axis | the click is re-tunable by reprinting 2 g — print 1.20 / 1.60 / 2.00 variants with the golden part |
| `post_guide` | 1 | ⌀12 × 82 | ⌀12.00 +0.00/−0.10 over the top 60 mm; straightness ≤0.08 TIR; **fuzzy skin 0.30 on all exposed cylindrical surface** (see §4) | base socket → transition/press; yoke bore → **running clearance**, 0.40–0.60 diametral | PLA, 0.2 mm layers, 5 perimeters, 40% infill, vertical | stops the yoke rotating, so knob turns become vertical travel |
| `yoke` | 1 | 224 × 34 × 62 | lane clear width **130.0 +0.5/−0.0** between end-block inner faces; saddle grooves at x = ±72.0 ±0.15, **90° included, 4.0 deep, apex relieved with a ⌀2.0 slot**; **saddle-line parallelism to the runway ≤0.15 mm across the 130 mm lane, at every point of travel**; nut ⌀16.70 +0.15/−0.00 major, 20 tall; post bore ⌀12.40 +0.10/−0.00, **blind**, 54 deep; both skirts drop 21.0 below the boss reference, ⌀30 ID / ⌀34 OD | screw → running; post → running; bar → free (never fastened) | PLA, 4 perimeters, 25% infill; **printed in a light colour** (see §4 contrast) | carries the bar; the two skirts are what keep the thread and the post invisible |
| `stop_ring` | 1 | ⌀36 × ~2.3 | **height sliced per copy** — see §5.3. Nominal 2.25, range 2.00–2.75, tolerance ±0.05 | drops over the shroud, ⌀24.5 ID clearance; loose | PLA, 100% solid, **same print session and Z-offset as the blocks** | the hard bottom stop that ends the game; per-copy so "Bottom" lands exactly on the 31st click |
| `knob_hood` | 1 | ⌀82 × 84 | wall **1.6 min, opaque pigmented filament only, ≥0% light transmission by eye against a phone torch**; internal ledge ⌀44.4 +0.20/−0.00 seating on the knob top face at Z = 90; hand port 66 wide × 52 tall, **open to the bottom rim**, on ONE side; finger tab on the opposite (closed) side | knob top → rests, **hangs from the knob, never from the yoke** (§4) | PLA, 2 perimeters, 0.28 mm layers, no infill, no top solid — ~1.6 h | hides the setter's hand and, critically, the direction of every turn |
| `rail_01`–`rail_04` | 4 | 178 × 32 × 8 | front edge **straight ≤0.10 over 178** (it is the straightedge every score line is laid against); six pockets 21.0 × 21.0 +0.20/−0.00 × 3.0 deep, on 28.0 ±0.15 centres | blocks → **clearance**, 1.0 total (drops in and out one-handed) | PLA, 3 perimeters, 12% infill, printed flat | the empty pocket is public information — *which* block you took is visible, *how tall* is not |
| `piece_a1`–`e6` | 30 | 20 × 20 × H | **H face-to-face ±0.05**; top and bottom faces flat ≤0.03 and parallel ≤0.05; edges chamfered 0.4 × 45° on the vertical arrises only — **top and bottom arrises stay sharp**; set symbol **debossed 0.5 on ONE side face only**, never on top or bottom | rail pockets → clearance; the bar → the whole game | PLA, 3 perimeters, 5 top / 5 bottom, 15% infill, **ironing ON for the top face**, printed standing, layer height per §5.2 | these are the bids |

**Printed part count: 41.** (10 mechanism/furniture + 30 blocks + 1 stop ring.)

### buy_not_print

| item | spec | why not printed |
|---|---|---|
| **The bar** ×1 | carbon-fibre tube **⌀8.0 × ⌀6.0 × 158.0 mm**, cut square, ~5.2 g, black gloss | a vertically printed ⌀8 × 158 tube is a 20:1 aspect print with a ~8% reject rate, and any bow moves the "lowest point" along the lane — this part is a bust *detector*, straightness is its whole job. A cut tube is dead straight, 5.2 g (inside the ≤6 g rule), stiffer, costs ~$1.20, and the gloss-black-on-light-grey contrast is what makes the gap readable (§4). **Printed fallback if the all-printed claim must hold:** PLA tube ⌀8.0 × ⌀6.0 × 158, printed vertically with a brim, straightness ≤0.10 TIR, 4.3 g, 1.5 h, sort and reject. |
| **Commit cups** ×4 | opaque tumbler, internal ⌀ ≥ 34 at the base, ≥ 40 deep, flat-bottomed, non-tapering below 40 mm | must clear a 20 × 20 block on its diagonal (28.3 mm) plus the tallest 32.75 rung. This part carries **zero game-specific geometry** — it is a cup. Printing four of them costs 5.2 h and 60 g for nothing. |

---

## 3. The arithmetic (proof that a legal solution exists)

Every coupled pair below is checked. No pair is over-constrained.

**3.1 Click ↔ pitch ↔ travel.** 4 detent notches × 90° = one revolution =
2.00 mm pitch → one click = 0.500 mm. 31 clicks × 0.5 = 15.50 mm of travel.
✅ Consistent with the bill's "31 clicks".

**3.2 The ladder.** Rungs 12.25, 12.75 … 32.75 → (32.75 − 12.25)/0.5 + 1 =
**42 rungs**. ✅ Matches rules §2.

**3.3 The 0.25 mm margin guarantee — and why it survives print error.**
Bar heights are `H_top − 0.5k` (k = 0…31). Block heights are
`H_top − 0.25 − 0.5m` (m = 0…41). Any margin =
`|0.5(k − m) − 0.25|` ≥ **0.25 mm, always**, and **`H_top` cancels out**.
So the guarantee holds no matter what the gantry actually measures, provided
the block ladder is generated from *that copy's measured* `H_top` (§5.1).
This is the single most important line in the brief: it converts an
impossible absolute-accuracy requirement into a per-copy slicer constant.

**3.4 Self-locking (no back-drive).** M16 × 2.0, pitch ⌀ ≈ 14.7.
Lead angle = atan(2.0 / (π × 14.7)) = **2.48°**. PLA-on-PLA μ ≈ 0.35 →
friction angle **19.3°**. 2.48° ≪ 19.3° → self-locking with ~8× margin.
Yoke lifting torque = 0.59 N × 7.35 × (2 + π·0.35·14.7)/(π·14.7 − 0.7) =
**1.73 N·mm**. ✅

**3.5 Detent must dominate the drive.** Leaf as a cantilever,
E = 3500 MPa, b = 12, h = 1.60, L = 24: I = 4.10 mm⁴,
k = 3EI/L³ = **3.11 N/mm**. Riding a 0.80 mm ramp → normal 2.49 N.
30° ramp, μ 0.35 → tangential 2.9 N at r = 12 → **35 N·mm** breakaway.
That is **20×** the 1.73 N·mm drive torque, so the click is felt, not
mushy. At the ⌀44 knob rim that is **1.6 N** of finger force — comfortable
for 8 clicks. ✅ Legal. Tune by reprinting `detent_leaf` at h = 1.20
(15 N·mm) / 1.60 (35) / 2.00 (68).

**3.6 Bar seats on the V flanks, never in the apex.** ⌀8 rod, r = 4, in a
90° V: centre sits r/sin45° = **5.657 mm** above the apex, so the rod's
lowest point is 1.657 above the apex — 2.34 mm clear of the groove rim, and
**it never touches the apex**, so print artifacts down there cannot change
`H_bar`. Apex relieved ⌀2.0 anyway. ✅

**3.7 Bar deflection.** Carbon ⌀8 × ⌀6, I = 137 mm⁴, E ≈ 70 GPa, 5.2 g over
a 144 mm span: δ = 5wL⁴/384EI ≈ **0.0003 mm**. Printed PLA fallback:
**0.005 mm**. Both far under the 0.25 mm margin. ✅

**3.8 Bar lift force.** The primary bust signal is the bar *rising*, and
that needs only its own weight: **0.051 N**. A 90° V does not resist lift.
The V angle is therefore free to be chosen for seating stability. ✅

**3.9 Yoke length ↔ lane ↔ base.** lane 130 → end-block inner faces at
x = ±65; end blocks 47 wide → outer faces ±112 → **yoke 224 long**.
Saddles at ±72 (inside the end blocks ✅). Screw and post axes at ±95
(inside the end blocks ✅), 190 apart, both inside the 220 mm base with
15 mm to each edge. Bar 158 long spans saddle centres 144 apart with 7 mm
proud each end. 224 ≤ 251 ✅.

**3.10 The thread is never visible (telescoping shroud).** Skirt drop
S = 21.0 below the boss reference at `H_bar` + 6:

| | skirt rim Z | shroud top Z | overlap | verdict |
|---|---|---|---|---|
| at `H_top` (bar 33.0 nom) | 18.0 | 24.0 | **6.0 mm** | thread hidden ✅ |
| at `H_bottom` (bar 17.5 nom) | 2.5 | 24.0 | **21.5 mm** | thread hidden ✅, 2.5 mm runway clearance ✅ |

Radial: shroud ⌀24 OD inside skirt ⌀30 ID → 3.0 mm per side, no rub. ✅
Same treatment on the post side: post top at Z = 70, yoke blind bore top at
Z = 72 at `H_top` → **the post never emerges**, and the blind bore keeps
54 mm of engagement on a ⌀12 post (4.5:1 L/D, no tilt). ✅

**3.11 Bridge clears the tallest block.** Bridge underside at `H_bar` + 11;
the bar's top is at `H_bar` + 8. The bar is always the lowest thing in the
lane, so a too-tall block always meets the bar first, never the bridge. ✅

**3.12 Runway depth.** A 20 mm-deep block needs ≈25 approach + 20 under the
bar + 25 exit = **70 mm**. Base is 78 deep. ✅ (This is why the scrap well
left the base — see §7.6.)

---

## 4. Hidden state stays hidden

The game has exactly one secret: **where in the eight clicks the setter
reversed**. Five ways that secret leaks, and the geometry that kills each.

1. **Seeing the hand.** `knob_hood`, 1.6 mm opaque pigmented wall, hand port
   on **one** side only, placed facing the setter. Port top lip at Z = 58,
   knob at Z = 76–90 and 41 mm inboard — an opponent needs their eye below
   table level *and* directly opposite the port to see the knob. The other
   three seats see a closed shell. **Never print the hood, the cups, or the
   rails in natural / clear / translucent filament.**
2. **The hood must hang from the KNOB, not the yoke.** The knob is axially
   fixed; the yoke moves 0.5 mm per click. A hood resting on the yoke boss
   would turn the hood's own rim height into a live readout of the bar
   height. Internal ledge ⌀44.4 on the knob top face, and the hood's bore
   must clear the yoke boss (⌀74 ID over a ⌀34 boss). ✅
3. **Asymmetric ramps would make up-clicks and down-clicks sound different**
   — which leaks the whole secret through the ears. The bill says "ramped
   notches". **Superseded: symmetric 30°/30° V-notches, and a symmetric leaf
   nub.** Golden-part test 2 is the acceptance criterion.
4. **The exposed thread is a 2.0 mm ruler.** The yoke's nut boss against a
   visible thread reads out absolute height directly. Killed by the
   telescoping shroud/skirt, §3.10 — the thread is invisible at every legal
   position.
5. **Layer lines are a ruler too.** A printed post has crisp bands at
   exactly the layer height; a player can count them against the yoke's
   bottom edge. **Fuzzy skin 0.30 mm on all exposed cylindrical surface of
   `post_guide` and on the shroud OD**, seams randomised, and the yoke's
   lower edges nearest the post rounded R1.0 so there is no crisp pointer.
   No graduations, ribs, seam alignment, or texture change anywhere within
   40 mm of the bar plane.

**Contrast — the other half of the same problem.** The table must read the
*gap* well (that is the skill) while reading the *change* badly (that is the
secret). Both are served by the same spec: matte light-grey runway with bed
texture, **light-coloured yoke**, **gloss-black bar**. The gap reads as a
bright slot with a crisp lower edge, judged in absolute terms; a 0.5 mm
change in a 20 mm slot is 2.5% and has no static reference beside it.

---

## 5. Per-copy manufacturing (this is not optional)

Every copy already gets a fresh random ladder (rules §2). Three numbers are
generated per copy from one measurement, and this is what removes the
calibration problem.

**5.1 Measure `H_top`.** Assemble the gantry, wind the yoke to the hard top
stop, measure runway-to-bar-underside with a depth caliper, **±0.05 mm**.
Record it on the copy's build card. Expect 32.5–33.5. Its absolute value
does not matter (§3.3) — only that it is known.

**5.2 Slice the 30 blocks from `H_top`.** Draw 5 sets × 6 from
m = 0…41, `H = H_top − 0.25 − 0.5m`, without replacement within a set, sets
independent. Enforce per set: at least one rung above `H_top − 5.0`, at
least one below `H_top − 16.0`, and no two within 1.0 mm.
Slice **each block at layer height `H / round(H / 0.25)`** — between 0.243
and 0.257 mm — so every block's height is an exact integer layer count by
construction. This is what buys the ±0.05.
Calibrate the first-layer Z-offset before the session: a 10-layer coupon
must measure **2.500 ± 0.02**. All 30 blocks and the stop ring print in that
same session at that same offset.
Print in **5 plates of 6** (one set per plate) — one failure loses a set,
not the game.
**Never print, stamp, or engrave a height on a block.**

**5.3 Slice the `stop_ring`.** Ring height = (measured skirt-rim Z at the
top stop) − 15.50 − 0.15. Target: the ring must **permit the 31st detent to
seat and block the 32nd**, i.e. engage between 15.50 and 15.75 mm of travel.
Verify by hand before boxing: from the top stop, 31 clicks must seat
cleanly and the 32nd must refuse.

---

## 6. Assembly (6 steps, no instructions-rage, no fasteners)

1. Press `post_guide` into the base socket until it bottoms (0.10 interference).
2. Snap `detent_leaf` into its base socket, nub toward the journal.
3. Thread `yoke` onto `column_screw` from the thread's lower end.
4. Lower screw + yoke as one unit: screw collar into the journal, yoke skirt
   over the shroud, yoke blind bore over the post. Two alignments at once —
   lead-in chamfers 1.5 × 30° on all three.
5. Drop `stop_ring` over the shroud.
6. Lay the bar in the saddles. Never fasten it.

No screws, no glue, no inserts, no tools. Buyer-doable in under 5 minutes.

---

## 7. Reconciliation — where this brief overrides the bill, and why

Nine supersessions. Each is the resolution of a conflict that would
otherwise have become a CAD repair loop.

**7.1 Block ladder.** `idea.json` says a "0.4 mm ladder from 18 to 30 mm";
`rules.md` ships the 42-rung 0.5 mm ladder 12.25–32.75. Flagged by
`review/rules_lens.json` as *clarify*. **Build the RULES ladder.** The pitch
text is a stale summary; the rules version is the one the sim ran, and 0.5 mm
is the click, so any other step size would put blocks off the bar grid.

**7.2 End condition.** `idea.json` says "play until one stock is empty";
`rules.md` ends at "Bottom". Also flagged *clarify*. **Build for the RULES
ending** — this is why `stop_ring` exists and why the bottom stop must be
hard, per-copy, and land exactly on click 31.

**7.3 Yoke: 170 × 24 × 16 → 224 × 34 × 62.** The bill's number describes the
bridge only, and 170 cannot span a 130 mm lane plus two brackets plus two
boss offsets. Arithmetic in §3.9. The extra Z is the 54 mm blind post bore
and the 21 mm skirts, both anti-leak features (§4).

**7.4 Guide post: ⌀12 × 112 → ⌀12 × 82.** At 112 the post's top end sticks
35 mm out of the yoke's bore and becomes a static reference beside a moving
edge — a hidden-state leak. At 82 the post top sits at Z = 70, permanently
swallowed by the blind bore (§3.10).

**7.5 Screw: ⌀16 × 118 → ⌀16 × 104.** The knob had to come down 14 mm so an
84 mm hood can cover a whole hand without towering. Thread still spans
Z 24–66, covering the nut over the full travel with margin.

**7.6 Base: 220 × 110 × 12 → 220 × 78 × 10, and the scrap well leaves the
base.** Two problems, one fix. (a) A 100 × 40 × 10 well holds about **five**
blocks; rules §2 says up to **26** are scrapped in a long game, and already
concedes "if it fills, keep stacking". It was never a container. (b) The
well ate 40 mm of a 110 mm base, leaving 70 mm of runway — exactly the
minimum a 20 mm block needs, with zero margin. **Resolution: scrapped blocks
go in the box lid**, the base drops to 78 deep, runway margin goes to 8 mm,
and the base's print drops from ~7 h / 117 g to **5.0 h / 79 g**. The
setter's ritual reminder stays embossed on the front skirt. *This needs a
one-line rules edit (§2, §5.4: "scrap well" → "the box lid").*

**7.7 Detent notches: "ramped" → symmetric.** Asymmetric ramps make an
up-click sound different from a down-click, which hands the table the one
secret in the game. §4.3.

**7.8 The bar and the cups become `buy_not_print`.** Rules §2 claims "every
component is a printed physical object". Two exceptions, both argued above:
the bar because straightness is its function and a 20:1 print cannot promise
it, the cups because they carry no game geometry. **This contradicts a
sentence in the rules and needs a decision, not a silent build.** If the
all-printed claim is load-bearing for the product story, use the printed
fallbacks in §2 and add 6.7 h and 64 g.

**7.9 Bill totals: "44 parts, roughly 350 g" → 41 printed parts, ~487 g.**
See §8.

**7.10 Table findings — what they do and do not touch.**
`playtest/table_report.json` seat 2 of table 1 (the one *no*
would-play-again vote of eight) says "the gap uncertainty was too large to
support real strategy — my block choices were guesses within noise margins".
Three other seats say the same thing more mildly. That is an LLM seat with
no eyes estimating from prose, so it is **not** evidence about the physical
gap — but it is a warning about exactly the quantity this brief controls.
The geometric answers are in §4 (contrast, crisp lower edge, no static
reference) and the acceptance test is golden-part test 4: humans must beat
chance at 1.0 mm and sit near chance at 0.5 mm. **If test 4 fails, this is a
design finding, not a CAD finding — stop and say so.**

`review/fresh_reader.json`'s three misses (round-1 pass order, no fallback
count-caller, split fingernail verdict) are rulebook-text gaps with **zero
geometry consequence**. Do not try to solve them in CAD.

The sim gate passed 1000 games at 2/3/4 players with no degeneracy, and used
30 blocks in 5 sets exactly as billed. No piece-count discrepancy.

---

## 8. Economics — this game does not fit the 20-hour ceiling. Read this.

| | printed parts | print h | filament g |
|---|---|---|---|
| `gantry_base` | 1 | 5.0 | 79 |
| `column_screw` | 1 | 4.0 | 35 |
| `yoke` | 1 | 5.5 | 70 |
| `post_guide` | 1 | 0.8 | 9 |
| `knob_hood` | 1 | 1.6 | 40 |
| `detent_leaf` + `stop_ring` | 2 | 0.4 | 4 |
| `rail` ×4 | 4 | 6.2 | 100 |
| `piece` ×30 | 30 | 11.0 | 150 |
| **total** | **41** | **34.5 h** | **487 g** |

**Against the targets: parts 41 vs 6–20, print 34.5 h vs ≤20 h.** Flagging
this here, loudly, as instructed — the build gate should not be the first
place this is discovered.

Two things soften the part count honestly: 30 of the 41 are identical-process
blocks that need **zero assembly**, and total assembly is **6 tool-free
steps** (§6), comfortably inside the guideline the part count is a proxy for.
The 34.5 hours do not soften. They are real machine hours.

**Levers, with what each costs:**

| lever | saves | costs |
|---|---|---|
| Drop set `e` (24 blocks, 4 sets) | −2.2 h, −33 g, −6 parts | at 4 players every set is used and the setup pick (rules §3.6) becomes forced. Real loss at 4p, minor at 2–3p. |
| Buy the cups + bar (already assumed here) | −6.7 h, −64 g, −5 parts | breaks the "everything is printed" line in rules §2 (§7.8) |
| Base 8 mm instead of 10 | −0.8 h, −14 g | thinner runway skin, flatness risk goes up — **not recommended**, the runway is the datum |
| Two machines | 34.5 h → **17.3 h wall clock** | capital, not margin |

**Do not expect a printing lever to fix this.** Thirty blocks and a 220 mm
base *are* the game; everything else already went to `buy_not_print` or got
thinned. This is a 34-hour product.

**Does it still clear the corner?** COGS at 34.5 h: filament $10.70
(487 g @ $22/kg) + machine $8.60 (34.5 h @ $0.25) + carbon tube $1.20 +
4 cups $2.00 + box & insert $4.00 + labour $12.50 (25 min @ $30/h) =
**≈ $39.** At $49 that is a 20% margin and not a business. At **$79 it is a
51% margin and it works.**

**Recommendation: price this at $79, at the top of the corner, or not at
all — and decide at the build gate whether 0.7 units per machine-day is
throughput you accept.** The one-machine yield, not the margin, is the
binding constraint.

---

## 9. Approved look

**No approved render — build gates on geometry only.**

Do not invent a likeness anchor. The mid-build milestone check is against
geometry, and only these, all of which are measurable rather than judged:

1. Runway flat ≤0.15 mm TIR across the 130 mm lane; base does not rock on
   glass (three feet).
2. Lane clear width 130 +0.5/−0.0, with nothing in it but the bar.
3. Saddle line parallel to the runway ≤0.15 mm across the lane, checked at
   the top stop, at 15 clicks, and at the bottom stop.
4. At **every** click from top stop to bottom stop: no thread visible, no
   post top visible, no layer-line ruler beside a moving edge (§3.10, §4).
5. Thirty blocks measured face-to-face, every one within ±0.05 of its
   sliced height, and every margin against every bar height ≥ 0.25 mm.

Any of these five failing mid-build is an abort, not a repair.
