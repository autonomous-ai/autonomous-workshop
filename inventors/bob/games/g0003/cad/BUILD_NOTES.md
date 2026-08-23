# CLEARANCE (g0003) — build notes

**42 printed parts** (brief's 41 + `screw_shroud`, DEVIATIONS D1) + **1 test-only
part** (`golden_stub`). **2 bought.** Assembly: **6 steps, no tools, no
fasteners.** Files in `../parts/`; deviations in `DEVIATIONS.md`.

## Print the wound first

`column_screw` + `detent_leaf` + `golden_stub` (60 × 60 stub with the
dial-indicator post) is the brief's physics rig. Run tests 1–3 — 0.500 ± 0.05 per
click, blind up/down direction ≤55%, ≤0.02 mm creep in 60 s under 70 g — **before
committing the other 39 parts**. Print `detent_leaf` at h = 1.20 / 1.60 / 2.00
and pick by feel; it is 2 g and the whole point of the part.

## Printed

| part | qty | orientation | notes |
|---|---|---|---|
| `gantry_base` | 1 | **runway on the bed** | the runway is the datum for every bar height; it has to come off the glass. Yaws 45° on a 220 bed (211 mm). |
| `screw_shroud` | 1 | flange down | presses into the base, 0.10 interference. Its bore **is** the journal. |
| `column_screw` | 1 | **knob up** | 0.15 mm layers, 4 perimeters, 40%. No supports on the thread — the crown and the 45° top-stop cone are both self-supporting this way up. |
| `detent_leaf` | 1 | **on edge** (D5) | 100% solid. Spring section drawn along the beam. |
| `post_guide` | 1 | vertical | 5 perimeters, 40%. **Fuzzy skin 0.30** on the cylinder (§4.5). |
| `yoke` | 1 | skirts down | 4 perimeters, 25%. **Rotate 45° in XY on a 220 bed** → 182 mm square (D12). Light colour (§4 contrast). |
| `stop_ring` | 1 | flat | **height is per copy** — §5.3, same session and Z-offset as the blocks. |
| `knob_hood` | 1 | **roof down** (D4) | 2 perimeters, 0.28 mm, no infill, **5 bottom solid layers, no top solid**, brim. The roof is **closed** — it is the sightline that would otherwise read the knob. Opaque pigmented filament only — never natural or clear. |
| `rail_01`–`04` | 4 | flat | front edge is the straightedge every score line is laid against. |
| `piece_a1`–`e6` | 30 | standing | ironing ON, 5 top / 5 bottom. **Layer height per block** — see below. |

Also **fuzzy skin 0.30 on the shroud OD**. No graduations, ribs, aligned seams or
texture change within 40 mm of the bar plane (§4.5).

## `buy_not_print`

| item | spec |
|---|---|
| **the bar** ×1 | carbon-fibre tube ⌀8.0 × ⌀6.0 × **158.0**, cut square, ~5.2 g, gloss black |
| **commit cups** ×4 | opaque tumbler, internal ⌀ ≥ 34 at the base, ≥ 40 deep, flat-bottomed, non-tapering below 40 mm |

Printed fallbacks exist for both (brief §7.8, +6.7 h / +64 g) if the
all-printed claim has to hold.

## Per copy — not optional

1. Assemble the gantry, wind to the hard top stop, measure runway-to-bar-underside
   ±0.05. That is `H_top` (expect 32.5–33.5). Record it on the build card.
2. Draw 5 sets × 6 from `H = H_top − 0.25 − 0.5m`, m = 0…41. Slice **each block at
   `H / round(H / 0.25)`** (0.243–0.257 mm) so its height is an exact layer count.
   Calibrate first-layer Z first: a 10-layer coupon must read 2.500 ± 0.02. All 30
   blocks and the stop ring in **one session at one offset**, in 5 plates of 6.
3. Stop-ring height = (measured skirt-rim Z at the top stop) − 15.50 − 0.15.
   Verify by hand: 31 clicks seat, the 32nd refuses.

Never print, stamp or engrave a height on a block.

## Assembly — 6 steps

1. Press `post_guide` and `screw_shroud` into their base sockets until both bottom
   (0.10 interference each).
2. Snap `detent_leaf` into its socket, nub toward the journal.
3. Thread `yoke` onto `column_screw` from the thread's lower end.
4. Lower screw + yoke as one unit — collar into the journal, skirt over the
   shroud, blind bore over the post. Three lead-in chamfers (1.5 × 30°) make the
   two blind alignments at once.
5. Drop `stop_ring` over the shroud; hang `knob_hood` on the knob top face.
6. Lay the bar in the saddles. Never fasten it.

## What was checked, and what it said

| check | result |
|---|---|
| `check_mesh --bed 251x251x251`, all 43 STLs | **all printable** — watertight, one shell, positive volume, correct winding, in envelope |
| `check_mesh --bed 220x220x250` | `yoke` fails bed-fit only (224 > 220); fits rotated 45° at 182.4 mm — D12 |
| `check_fit . --bed 251 251` | **ok** — 43 parts, min(Z) = 0, footprint and volume all pass |
| `inspect interfere clearance.step` | **0 clashes**, 43 pairs tested, 37 occurrences |
| `check_layout .` | **ok** — every entry generator conforms to the split rule |
| `measure/check_fit.py` (project audit) | **17 pass, 0 fail** — brief §3 coupled pairs, §3.3 margin guarantee re-proved at H_top 32.50/33.00/33.50, bill↔parts, envelopes, **§4.1 sightline: the ⌀44.40 column above the knob's top face is 100.00 % solid hood and the ⌀44 column below the seat is 0.00 % obstructed** |

Renders: `../parts/renders/assembled.png` plus `_front` / `_lane` / `_top`.

**Not checked here, by design:** the four golden-part tests are physical
(dial indicator, blind listen, creep, human read). Brief §7.10 is explicit — if
the human read test fails at 1.0 mm, that is a design finding, not a CAD finding.

## The number the build gate should see

Brief §8 already flags it and the build does not improve it: **42 printed parts
vs a 6–20 guideline, ~34.5 h of machine time vs ≤20 h.** 30 of the 42 are
identical-process blocks needing zero assembly, and total assembly is 6 tool-free
steps. The hours are real. Price at **$79** or not at all.
