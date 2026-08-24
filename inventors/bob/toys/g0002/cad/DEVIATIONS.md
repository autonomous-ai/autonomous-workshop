# Re-Pin (g0002) — registered deviations

Every row is a place where the built geometry differs from `parts_brief.md`.
The brief was not edited. Each row gives the part, the dimension, the brief
value, the built value and why. Every one of them is marked `[DEV]` at the
matching line in `parts/repin_lib.py`.

Nothing in §1 (the six stop angles), §4 (the 8-rung, 1.2 mm ladder), §5's C1–C15
arithmetic or §6 (hidden state) is changed by any row below.

---

## A. The mechanism (these three touch the wound — read them first)

| # | part | dimension | brief | built | why |
|---|---|---|---|---|---|
| A1 | `plug_01` | gate notch depth | 3.40 | **2.00** | The notch floor caps how far a too-low driver falls, and the reset slide has to lift that driver back inside **one 16.0 mm chamber pitch** (see C1 below). A 1-rung error still engages 1.20 − 0.40 = **0.80**, which is the brief's own C5 number; errors of 2 rungs and deeper now bottom out at 2.00 instead of 3.40 and still meet the end wall, so no stop angle moves. C6 improves: notch floor r 20.00 vs keyway roof corner r 13.10, margin 6.90 (brief 5.50). |
| A2 | `plug_01`, `shell_01` | notch / channel end walls | radial faces | **tangent planes, offset 3.10 (= pin radius) from the radial ray**, still 0° draft, no chamfer, no fillet | A ⌀6.20 round nose against a *radial* plane touches the plane about 8° before the ray, and the error changes with how far the part protrudes — so the stop angle would drift by rung, which §1 forbids ("repeatable to ±2°, on all 8⁸ combinations"). Offsetting the wall by the nose radius makes contact happen at exactly Sᵢ₋₁ for every rung. This is the brief's *intent* (a hard wall at S) built correctly, not a softened stop: the face is still flat, unchamfered and 0° draft. |
| A3 | `key_01` | lifter top above blade roof | 1.4 … 9.8 | **2.0 … 10.4** (+0.60 each) | The brief's numbers assume the blade roof sits at r = 9.60. A 25.40 blade in a 26.00 keyway rests on the keyway *floor* (the hard datum), which puts its roof at r = 9.00. The absolute lifter-top radii are unchanged — 19.4 … 11.0 — so `lifter(s) + pin(r) = 12.8` still lands the pin top exactly on the shear radius 22.4 when `s = r`. Step (1.2), travel (8.4) and B (12.8) are untouched. |

| A4 | `key_01` | lifter positions | "at 24 / 40 / 56 / 72 / 88 **from the tip**" | **72 / 56 / 40 / 24 / 8 from the tip** (= 24 / 40 / 56 / 72 / 88 from the *shoulder*) | Read literally against the brief's own "shoulder stop face at 96 from the tip", a lifter *d* mm from the tip lands at x = 96 − *d* on the plug, so the brief's set would put nothing under chamber 5 (x = 88 needs d = 8) and would reverse chamber order. The brief's own C11 says the blade *does* reach chamber 5 with 8.00 of margin, which is only true of the built set. Built = the brief's numbers measured from the shoulder, which is where they are actually referenced. Lifter *i* still lands on bore *i* in the assembled lock. |
| A5 | `plug_01` | roof aperture | five ⌀5.40 holes, one per chamber | **one continuous ⌀5.40-wide axial slot**, r 9.60 → 19.60, front face → 91.95 | A ⌀4.80 lifter standing up to 9.8 mm above the blade roof cannot travel 96 mm through a solid keyway roof to reach its chamber: with five isolated holes the key cannot be inserted or withdrawn **at all**. `check_motion` proved it — `key-withdraws` blocked by `plug_01` at step 1 of 22, 612 mm³ of overlap. The slot keeps the briefed 5.40 width, so C13 (a ⌀6.20 pin still cannot pass) and C14 (a ⌀4.80 lifter passes with 0.30 of side-play) are both unchanged, and a pin still lands on the crescent shelves at r 10.40 either side of the slot. Slot roof 19.60 clears the tallest lifter (19.40) and stays under the gate-notch floor (20.00). Hidden state (§6) is unchanged: the brief already counts the apertures as openings into the chambers, a pin bottom was already visible up its own aperture from the keyway mouth, and in play the key fills the keyway. Re-checked: **0.000 mm³ of key↔plug overlap through the whole 110 mm withdrawal.** |
| A6 | `shell_01` | bore over the latch cam | plain ⌀45.60 cradle the full length | **relief band at r 25.40**, z 93.5 → 100.5 | The brief's own latch cam lobe grows to r 25.0 — 2.2 mm outside the r 22.8 bore — so a plain bore ploughs the lobe into the shell as soon as the plug turns. `check_motion` proved it: `plug-turns-free-0-90` blocked by `shell_01` at 25°, and 61 mm³ of overlap by 45°. The relief gives the lobe 0.40 all round (the shear line's own clearance) over 7 mm of length, and removes no bearing surface — both journals sit outside the band. Re-checked: **0.000 mm³ of plug↔shell overlap at 0 / 25 / 45 / 68 / 90°.** |

## B. Parts whose shape had to change to work

| # | part | dimension | brief | built | why |
|---|---|---|---|---|---|
| B1 | `slug_01` | stem, and a new head | stem ⌀7.00 × 12.0, total 30.2 | stem ⌀7.00 × **10.0** + head **⌀9.60 × 2.0**, total **30.2** | `lever_01` has to lift the driver from above, and the flange is buried in the counterbore where nothing can reach it. The top 2.0 of the stem becomes a head the lever's shelf catches. Nose (⌀6.20 × 12.2), flange (⌀10.00 × 6.0) and the 30.2 envelope are exactly as briefed. |
| B2 | `shell_01` | roof over the plug | 240° cradle + two 50° flanks | **270° cradle + two 45° flanks**, tangent to r 23.40, apex r 33.09 | A 50° flank tangent to the clearance circle apexes at r 35.8 — *above* the 34.60 shoulder datum, which would destroy the datum the whole measurement rests on. 45° from vertical is still self-supporting on FDM and the apex stays under the shoulder. Clearance to the plug land is 23.40 − 22.00 = **1.40**, over the brief's ≥1.0. |
| B3 | `lever_01` | detents, lift, ramp, thickness | 3 detents at 0/20/40, lift 9.5 ±0.3, ramp 1:4, 9 thick | **2 detents at 0 / 9.9** (`RUN`, `LOAD`), lift **2.20**, ramp 4.60 run : 2.20 rise, **17.70** thick | The chimney pitch is 16.0 mm. Slide travel *plus* ramp run must fit inside one pitch or a driver head ends up over its neighbour's loading hole, which breaks loading and leaks state. The lift only has to clear the notch depth (A1: 2.00), not the ladder — a driver never falls further than the notch floor. The tunnel roof must clear the *tallest* head the mechanism can produce (nominal + 8.40 of over-stack rise), and that is what sets 17.70. Rules text ("lifts all five driver slugs clear") stays true: asserted in source, `LEVER_TOP_Y − SLUG_HEAD_BOT ≥ R_SHEAR`. |
| B4 | `hood_01` | envelope | 112 × 72 × 46 | **102.9 × 68.9 × 63.5** | Height is forced by the brief's own §3 line "interior clear height ≥ 30 above the chimney tops": chimney tops are at r 46.0, so the ceiling is at r 76.0 and the seat is at r 15.0 → 63.5 mm of wall. Length and width follow the shell's real seat rectangle (100.4 × 66.4) plus 2.5 walls, so the skirt still seats 3.0 mm into the rebate with 0.40 clearance and no sight line. Walls are the briefed 2.50 min, one open face, printed open-face-down. |
| B5 | `key_01` | slider detents | "8 detents at 4.00 pitch" (sprung click) | **8 witness grooves at 4.00 pitch, 28.0 travel** — a read, not a click | A sprung print-in-place pawl inside a 2.00 mm lane is thinner than one 0.4 nozzle bead on the part that carries the turning torque. §4 makes the click unnecessary: the lands are *flat steps*, so a detent 0.5 mm off in travel produces zero height error. Pitch, travel, the 1–8 engraving and public readability are unchanged. |
| B6 | `key_01` | slider lane width | not specified | **2.00** (0.60 webs between lanes, 1.00 outer walls) | At 2.80 the five lane slots plus their print-in-place gaps overlap into one 16.2 mm void with 0.6 mm outer walls. Asserted in source. |
| B7 | `plug_01` | roof aperture length | not specified | **0.80** | The brief gives the aperture ⌀5.40 but no depth. 0.80 keeps the ⌀6.20 pin shelf (C13) below the s = 8 lifter top so the lifter always passes (C14). |
| B8 | `cap_01` | bore | ⌀45.8 | ⌀45.80 as a **0.40 deep spigot recess**, plate 3.0 + tabs 5.0 = 8.0 | A through-bore would not set end float. The recess over the plug's rear journal gives exactly the briefed 0.50 axial end float (asserted in source). Snap tabs are the briefed 12 × 3 × 2.0 with 1.2 engagement. |
| B9 | `latch_01` | root press fit | 0.10 interference, full face | 0.10 interference on **four short pads**, slide fit elsewhere | Same interference the brief asks for, a twentieth of the insertion force and a twentieth of the modelled overlap, so `interfere` reports the joint honestly instead of a 9 × 14 × 42 mm crush. Flexure (1.80 × 24.0), nib (1.2 × 0.8) and the 30° follower face are as briefed. |
| B10 | `pin_r1…r8` | side numerals | engraved 0.35 deep, twice at 180° | as briefed, **with glyph islands removed** | A "3" or an "8" leaves a ~0.3 mm island inside its own crook — a floating fleck on the plate. Only the pin body is kept. Height (±0.10) and both flat end faces are untouched; nothing is engraved on the top face (§9.8). |

## C. Print-driven additions the brief does not mention

| # | part | what was added | why |
|---|---|---|---|
| C1 | `shell_01` | open ribbed frame: lightening pockets between chambers (outboard of the channels), foot skirt webs, cradle band only where it is needed | This is §7's **lever 1**, which the brief recommends outright ("open-frame the shell… this is the recommended change and it costs nothing in function"). Function is unchanged: 270° cradle, chimney deck, end plates, protractor face, foot. Print time was not measured — no slicer ran — so no hour claim is made here. |
| C2 | `shell_01` | 5 vent windows per skirt web (10 total, 8 × 6 × 12) | The foot plate, the body cylinder and each skirt web closed a lens-shaped void running the full 105 mm — `check_mesh` read the shell as **3 connected shells**. The windows open it to air. Re-running `check_mesh` after the change reports **1 shell**. |
| C3 | `shell_01`, `lever_01` | rail detent nib + flank dimples | The slide needs somewhere to click; the brief names detents but not their mechanism. The nib stands 0.25 mm proud of the rail's inner face at the dimple height (y 47.0) and drops into a 0.4-deep dimple at each of the two positions. Measured overlap against the lever: **0.000 mm³ at RUN, 0.000 mm³ at LOAD, 0.22–0.72 mm³ in between** — the snap the finger pushes through. (It first sat at y 55.4, up in the dovetail tongue, where it never met a dimple and rubbed the tongue for the whole stroke; `check_motion` caught that as a constant 0.048 mm³ at *every* travel, including the seated pose.) |
| C4 | `key_01` | slider staircase runs **tall-at-the-back**, foot at blade-local z = 104 (in the bow) | With the natural 1-at-the-front ordering, lands up to 8.4 mm *above* the rod foot sit under the rod's own arm, and the arm cannot pass them. Reversing the staircase makes the land under the foot the tallest one that rod ever meets. Setting-to-land mapping and the 1–8 labels are unchanged. |
| C5 | `key_01` | printed as a compound of 11 bodies (frame + 5 bars + 5 rods), sliders lifted one print-in-place gap in the printed pose | The brief specifies print-in-place rods and pawls. The gaps come from `cadfits.print_in_place_gap("sliding", 0.20, "PLA")`, not from typed numbers. Every land height in §4 is quoted *seated*, which is the play pose. |

## E. Envelopes — brief vs measured

Measured by `scripts/check_fit` on the built solids, in the **print pose**
(footprint × height). Bed limit is 251³ and the largest number anywhere below is
150.0, so every part clears it with ≥101 mm to spare.

| part | brief envelope | measured (X × Y × Z) | verdict |
|---|---|---|---|
| `plug_01` | 110 × 70 × 70 | 70.0 × **73.5** × 110.0 | pointer fin reaches r 38.5, so one cross-section axis is 73.5 not 70. Registered. |
| `shell_01` | 132 × 78 × 84 | 104.6 × 78.0 × **92.0** | 27.4 shorter, 8.0 taller: the lever rails stand above the chimney deck (B3). Registered. |
| `cap_01` | 60 × 60 × 8 | 61.8 × 62.2 × 8.0 | snap nibs stand 1.2 proud of the ⌀60 plate. Registered. |
| `hood_01` | 112 × 72 × 46 | 102.9 × 63.5 × 68.9 | see B4. |
| `latch_01` | 80 × 14 × 9 | 80.0 × 13.9 × **12.8** | the nose has to reach from the seat (x −35.0) to the plug land (x −22.3) — 12.7 mm of span. A 9 mm part cannot touch the cam. Registered. |
| `lever_01` | 96 × 34 × 9 | 96.0 × 34.0 × **17.7** | see B3. |
| `key_01` | 142 × 40 × 26 | 40.0 × 142.0 × **31.4** | the shoulder stop plate must overhang the 18 × 26 keyway mouth to land on the plug's front face, so it stands 31.4 where the bow is 26. Registered. |
| `slug_01` | ⌀10.0 × 30.2 | 10.0 × 10.0 × 30.2 | as briefed |
| `pin_r1…r8` | ⌀6.2 × 3.0…11.4 | 6.2 × 6.2 × 3.0…11.4 | as briefed |
| `case_01` | 100 × 66 × 20 | 100.0 × 66.0 × 20.0 | as briefed |
| `lid_01` | slides in a 2.0 groove | 95.0 × 61.7 × 2.0 | as briefed |
| `tray_01` | 120 × 34 × 10 | 120.0 × 34.0 × 10.0 | as briefed |
| `board_01` | 150 × 45 × 6 | 150.0 × 45.0 × 6.0 | as briefed |
| `peg_01` | ⌀5.0 × 14 | 7.2 × 7.2 × 14.0 | ⌀5.00 shank as briefed, plus a ⌀7.2 head so it lifts out one-handed (the brief's own fit line). Registered. |
| `GP1` plug / shell | ~60 stub | 45.0 × 45.0 × 60.0 / 60.0 × 78.0 × 80.0 | golden part, §8 |

## D. Not deviations — recorded so nobody re-derives them

- **`key_01` qty 3** is one file printed three times (brief §9.5). There is one
  `part_key_01.step.py`.
- **`grid_01…04`, `board_02`, score pegs** are `buy_not_print` (brief §3) and
  have no geometry, by contract.
- **Fallback table (§5)** was *not* applied. The build carries the 1.2 mm ladder.
  The fallback is a reprint decision that belongs to GP1's 64-pair test on a real
  printer, and no printer ran here.
- **GP1** is built as two parts — `part_gp1_plug.step.py` and
  `part_gp1_shell.step.py` — from the *same* library functions as the full plug
  and shell (`_chamber_bore`, `_gate_notch`, `_chimney_cut`), so the test cell
  tests the shipping geometry and not a lookalike.
