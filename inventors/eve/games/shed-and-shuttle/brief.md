# Shed and Shuttle — Physical Print Brief

**47 physical parts. 6 distinct printed geometries. No support anywhere. No fasteners,
no glue, no springs, no magnets.**

Everything below is in millimetres. Every part prints with one flat face on the bed.

---

## 0. Global datum and Z stack

All Z values are measured from **Z = 0 at the top surface of the deck lane floor**
(the surface a thread tile sits nearly flush with, and the surface a shuttle slides on).
Positive Z is up, out of the box, toward the player.

| Z (mm) | Feature |
|---|---|
| +3.0 | Top of lane walls; top of a **raised** warp post |
| 0.0 | **DATUM** — deck lane floor (top face of deck plate) |
| −0.2 | Top face of a seated thread tile (0.2 below flush) |
| −2.4 | Tile pocket floor |
| −4.0 | Deck plate underside (plate is 4.0 thick) |
| −4.6 | Comb arm top face, **finger raised** (0.6 clearance to deck underside) |
| −6.0 | Comb spine top face |
| −7.6 | Comb arm top face, **finger at rest** |
| −10.0 | Comb arm underside = comb spine underside (coplanar; this is the comb's print bed plane) |
| −10.8 | **Cam plane** — top of a *flat* cam cell, bottom of the follower rib |
| −7.8 | Top of a *raised* cam cell (3.0 above the cam plane) |
| −14.8 | Cam bar underside |
| −15.0 | Underframe channel floor, top face |
| −17.5 | Underframe underside — table surface |

Assembled height **20.5 mm**. Assembled footprint **233.0 × 210.0 mm**.

The whole mechanism is one number: **post travel = 3.0 mm**, driven by a **3.0 mm cam step**.

---

## 1. Part list (47 parts, 6 geometries)

| Geometry | Part ids | Qty | Footprint L×W×H (mm) | Material | Bed orientation |
|---|---|---|---|---|---|
| Deck | `part_deck` | 1 | 215.0 × 142.0 × 7.0 | PLA | underside on bed, lanes up |
| Underframe + bar rail | `part_bar_rail` | 1 | 233.0 × 210.0 × 14.5 | PLA | outer floor on bed, channel up |
| Warp comb | `part_warp_comb` | 1 | 206.0 × 46.0 × 10.0 | **PETG** | arm/spine underside on bed, posts up |
| Cam bar | `part_bar_a` … `part_bar_h` | 8 | 226.0 × 14.0 × 7.0 | PLA | base on bed, cam teeth up |
| Shuttle | `part_shuttle_p1` … `p4` | 4 | 26.0 × 12.4 × 7.5 | PLA (player colour) | hull underside on bed, fin up |
| Thread tile | `part_tile_p{1-4}_{1-8}` | 32 | 18.0 × 11.6 × 2.2 | PLA (player colour) | flat, either face on bed |

Total **47** part ids. Bar limit is 60.

---

## 2. `part_deck` — the play surface

**Envelope 215.0 (X) × 142.0 (Y) × 7.0 (Z), plate 4.0 thick + 3.0 lane walls.**

X is across the twelve lanes. Y runs away from the player: **y = 0 is the near edge**
(where a shuttle is launched), **y = 142 is the far edge**.

### 2.1 Lane grid (X)

| Item | mm |
|---|---|
| Lane floor width | 13.0 |
| Wall between lanes | 3.0 |
| **Lane pitch** | **16.0** |
| Lane band total (13 walls + 12 floors) | 195.0 |
| Border, each side in X | 10.0 |
| Lane 1 floor centre | x = 19.5 |
| Lane *n* floor centre | x = 19.5 + 16.0·(n−1) |
| Lane 12 floor centre | x = 195.5 |

Lane walls are 3.0 wide × 3.0 tall, top edge broken with a 0.5 × 45° chamfer.
Outer walls (x 10.0–13.0 and 202.0–205.0) are full-height walls too.

### 2.2 Lane features (Y), identical in all 12 lanes

| Feature | Y range / centre | Size | Depth from datum |
|---|---|---|---|
| Launch apron (shuttle rest) | y 0 → 28.0 | full 13.0 lane width | flat at Z 0 |
| Near-edge entry chamfer | y 0 → 3.0 | 2.0 × 45° down-and-out | — |
| **Warp post hole** | centre y = 34.0 | ⌀ **6.6** through the 4.0 plate | through |
| Post hole top lead-in | — | 0.4 × 45° chamfer | — |
| Tile pocket 1 | centre y = 52.0 | 18.5 (Y) × 12.0 (X) | 2.4 deep |
| Tile pocket 2 | centre y = 74.0 | " | " |
| Tile pocket 3 | centre y = 96.0 | " | " |
| Tile pocket 4 | centre y = 118.0 | " | " |
| Tile lift notch (each pocket) | near end of pocket | 6.0 (X) × 3.0 (Y) | 1.5 further, i.e. 3.9 total |
| Shuttle run-out | y 128.0 → 142.0 | flat at Z 0 | — |

Tile pocket pitch **22.0**. Pocket corners R1.0. Pocket floor leaves **1.6 mm** of plate.
Slot 1 is nearest the player, slot 4 farthest — matches rules §3.2.

### 2.3 Printed graphics (embossed, no second colour needed)

| Where | Content | Height |
|---|---|---|
| Far-edge plate, y 128–142, one per lane | lane number (5 mm tall) over lane value (7 mm tall) | +0.6 raised |
| Values, lanes 1→12 | 3, 1, 4, 2, 5, 1, 2, 4, 1, 3, 5, 2 | — |
| Near-edge border, y 0–10 | title text `SHED AND SHUTTLE` | +0.6 raised |
| Left border, beside each lane | slot ticks 1–4 | +0.4 raised |

All embossing is on upward faces; it prints as ordinary top surface, no support.

### 2.4 Joining slots in the deck border

The deck underside is **completely flat** (that is what makes it printable with no
support). Everything below it attaches by tabs coming **up through the plate** and
hooking on the top face.

| Slot | Count | Position | Size (X × Y) | Mates with |
|---|---|---|---|---|
| Underframe snap slot | 6 | x = 30 / 107.5 / 185 at y = 6.0 and y = 136.0 | 8.0 × 3.0 | `part_bar_rail` snap tabs |
| Comb ear slot | 2 | x = 5.0 and x = 210.0, centre y = 69.0 | 6.0 × 3.0 | `part_warp_comb` spine ears |

Each slot has a 0.5 × 45° top-face chamfer as the snap ramp, and a 0.5 deep × 1.5
wide relief pocket on the top face so the hook sits flush and the shuttle never
meets it (all slots are outside the lane band anyway).

---

## 3. `part_warp_comb` — the twelve compliant fingers

**Envelope 206.0 (X) × 46.0 (Y) × 10.0 (Z). One monolithic piece. PETG.**

This is the whole rules engine. It prints **flat, underside on the bed, posts pointing
up.** The living-hinge films lie in the first three layers of the print, so no support
can reach them — there is nothing overhanging on this part at all.

### 3.1 Layout

| Feature | Y range | Notes |
|---|---|---|
| Finger tip pad (carries post + follower rib) | y 28.0 → 40.0 | |
| Rigid arm | y 40.0 → 58.0 | continues the tip pad; arm runs y 28.0 → 58.0 = **30.0 total** |
| **Living-hinge film** | y 58.0 → 64.0 | **6.0 long** |
| Spine | y 64.0 → 74.0 | 10.0 deep, 4.0 thick |

Total comb Y extent 28.0 → 74.0 = 46.0.
Fingers are on **16.0 pitch**, aligned to the deck lanes: finger *n* centre at
x = 19.5 + 16.0·(n−1), same as the lane centres.

### 3.2 Finger cross-section — the numbers that matter

| Item | mm |
|---|---|
| **Living-hinge film thickness** | **0.60** (3 layers at 0.20) |
| Film width (X) | 9.0 |
| Film length (Y) | 6.0 |
| Film fillet into arm and into spine | R1.5, blended on the **top** face only |
| Rigid arm thickness | 2.4 |
| Rigid arm width (X) | 9.0 |
| Gap between adjacent arms | 7.0 (16.0 pitch − 9.0) |
| Arm underside | flat at Z −10.0 (bed plane) |
| Spine thickness | 4.0 |
| Spine underside | flat at Z −10.0 — coplanar with the arms |

The film sits at the **bottom** of the section: film underside at Z −10.0, film top at
Z −9.4. The arm's extra 1.8 mm of thickness is added above. The finger therefore
pivots about a neutral axis 0.30 mm above the bed plane.

### 3.3 Warp post (12 off, one per finger)

| Item | mm |
|---|---|
| Diameter | **6.0** |
| Centre | finger centreline, y = 34.0 |
| Height above arm top face | 7.6 (rises from Z −7.6 to Z 0.0 at rest) |
| Top | dome R3.0 truncated to a 2.0 flat |
| Fillet to arm | R1.0 |
| Travel | **3.0** (top goes from Z 0.0 flush to Z +3.0 proud) |

At rest the post top is **flush with the lane floor** — a shuttle glides over it.
Raised, 3.0 mm of ⌀6.0 post stands across a 13.0 mm lane; the shuttle hull is 4.5 mm
tall, so it cannot pass and cannot climb it.

### 3.4 Cam follower rib (12 off)

| Item | mm |
|---|---|
| Width (X) | 5.0 |
| Length (Y) | 9.0, centred on y = 34.0 |
| Proud of arm underside | 0.8 (bottom at Z −10.8, the cam plane) |
| Bottom edges | R1.5 rolled both ends in Y and both sides in X |

Narrow on purpose: a 5.0 rib always sits fully on a 7.0 cam plateau, so a lifted post
reaches full 3.0 travel and never perches half-way on a ramp.

### 3.5 Mounting ears (2 off, at the spine ends)

| Item | mm |
|---|---|
| Ear post cross-section | 5.8 (X) × 2.8 (Y) |
| Ear post height | 7.0, rising from spine top (Z −6.0) to Z +1.0 |
| Hook | 1.0 proud, 45° lead ramp, 0.4 land under the hook |
| Ear centres | x = 5.0 and x = 210.0, y = 69.0 |
| Spine overall X | 206.0 (extends into the deck border on both sides) |

Push the comb up from below; the two ears click through the deck border slots
(§2.4) and the spine underside lands on the underframe ledge at Z −10.0.
That is the "snap the warp comb into the underside of the deck" step in rules §2.

### 3.6 Spring behaviour — the check

- Post travel 3.0 over a 24.0 arm (film end to post centre) → hinge rotation **0.125 rad**.
- Film curvature 0.125 / 6.0 = 0.0208 /mm → **peak surface strain 0.62 %**.
  PETG yields around 3–4 % strain. Margin ≈ **5×**, and this part cycles thousands of
  times per game. Do not print the comb in PLA — PLA creeps and this is the one part
  that must still spring after a year on a shelf.
- Restoring force at the post ≈ **0.28 N per finger** (E ≈ 2000 MPa). Twelve fingers
  ≈ 3.4 N pressing down on the cam bar; bar push force through a 33.7° ramp ≈ **5 N**.
  That is a light two-finger push, and it is 90× the weight of a post, so posts drop
  back down on their own every time.

---

## 4. `part_bar_a` … `part_bar_h` — the eight cam bars

**Envelope 226.0 (X) × 14.0 (Y) × 7.0 (Z). Prints flat, base on the bed, teeth up.**

### 4.1 Body

| Item | mm |
|---|---|
| Base thickness | 4.0 (Z −14.8 → −10.8) |
| Body width (Y) | 14.0 |
| Cam body length | 208.0 (13 cells × 16.0) |
| Handle | 18.0 long × 14.0 × 7.0, at the **+X (right) end** |
| Total length | **226.0** |
| Handle grip | three 1.5 half-round ribs across the top, 4.0 pitch |
| Nose (−X end) | 4.0 long lead taper, 3.0 rise blended to the base |
| Retention rails | 1.5 × 1.5 along both bottom edges, full length of the cam body |

### 4.2 Cam cell profile

Cells are numbered 1…13 from the **−X (nose) end**. Cell *k* spans bar-local x
16.0·(k−1) → 16.0·k, measured from the nose face.

| Cell type | Profile |
|---|---|
| `O` — flat | top at the cam plane (Z −10.8) across the full 16.0 |
| `X` — raised | 4.5 up-ramp + **7.0 plateau** + 4.5 down-ramp; plateau top at Z −7.8 |

- Ramp angle **33.7°** from horizontal (3.0 rise over 4.5 run). Upward-facing slope:
  self-supporting, no support material, no stair-stepping problem at 0.20 layers.
- **Merge rule:** where two or more `X` cells are adjacent, delete the ramps between
  them and run one continuous plateau. Two adjacent `X` cells become a single
  plateau 7.0 + 4.5 + 4.5 + 7.0 = 23.0 long. This halves the push force and stops the
  bar from clicking through phantom detents.
- All plateau and ramp edges break 0.4 × 45°.

### 4.3 The eight profiles

`X` = raised cell (post up, lane closed). `O` = flat cell (post down, lane open).
Cells run 1 → 13 from the nose.

| Bar | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | O | X | X | O | X | X | O | X | O | X | X | O | X |
| B | X | O | X | O | X | O | X | X | O | X | O | X | X |
| C | O | O | X | X | O | X | X | O | X | X | O | O | X |
| D | X | X | O | X | O | X | O | O | X | O | X | X | O |
| E | O | X | O | X | X | O | X | O | X | O | X | X | O |
| F | X | O | O | X | X | O | O | X | X | O | X | O | X |
| G | O | X | X | X | O | O | X | X | O | X | O | X | O |
| H | X | X | O | O | X | O | X | O | O | X | X | O | X |

Verified against rules §3.1: bar A notch 1 leaves cells 1, 4, 7, 9, 12 flat → open
lanes 1 4 7 9 12 ✓; bar A notch 2 puts cell *i*+1 under finger *i*, flat at cells
4, 7, 9, 12 → open lanes 3 6 8 11 ✓.

### 4.4 Side legend and identity

On the **+Y face** of the bar (the face a seated player sees), emboss **+0.6 proud**:

- The bar letter, 8.0 tall, on the handle.
- Thirteen marks, 5.0 tall, one centred on each cell: `O` for flat, `X` for raised.
- A small arrow at cell 1 pointing at the nose, so the reading direction is never
  ambiguous.

Emboss the letter again on the handle top face, 8.0 tall, so bars are readable in the rail.

### 4.5 Notch detents

| Item | mm |
|---|---|
| Scallop on the bar's **−Y** side face | 6.0 long (X) × 1.0 deep × 3.0 tall, ends R1.0 |
| Notch-1 scallop, bar-local x from the nose | 24.0 |
| Notch-2 scallop, bar-local x from the nose | 40.0 |
| Detent separation | **16.0** — exactly one lane |

The scallops engage a spring bump on the underframe (§5.3). Notch 1 = cells 1–12 sit
under fingers 1–12. Notch 2 = the bar is pushed **16.0 mm further in (−X)**, so cells
2–13 sit under fingers 1–12.

### 4.6 Where the bar sits in each notch

| State | Bar nose at deck x | Handle end at deck x | Protrudes past deck (215 wide) |
|---|---|---|---|
| Notch 1 | 11.5 | 237.5 | 22.5 out the right side |
| Notch 2 | −4.5 | 221.5 | 4.5 out the left, 6.5 out the right |

Both ends of the channel are open. The left protrusion is caught by the underframe's
12.0 mm left shroud; the right protrusion is the handle you grab. Seeing how far the
bar sticks out is a free, honest read on which notch is loaded.

---

## 5. `part_bar_rail` — underframe, cam channel and bar rack

**Envelope 233.0 (X) × 210.0 (Y) × 14.5 (Z). Prints flat, outer floor on the bed,
channel and rack openings facing up. Largest part; still 23 mm clear of the bed edge
on every side.**

One part does three jobs: it is the channel the cam bar slides in, the ledge the comb
sits on, and the rack that holds the seven unloaded bars.

### 5.1 Frame

| Item | mm |
|---|---|
| Floor thickness | 2.5 |
| Under-deck section | X 0 → 233.0, Y 0 → 142.0 |
| Wall height above the floor, under-deck section | 11.0 (top at deck underside, Z −4.0) |
| Perimeter wall thickness | 3.0 |
| Left shroud (captures the bar nose at notch 2) | X 0 → 12.0 |
| Right mouth (bar entry) | X 221.0 → 233.0, flared 3.0 × 45° |
| Deck registration: deck occupies | X 12.0 → 227.0, Y 0 → 142.0 |
| Internal ribs | 3.0 wide, at y = 100 and y = 128, full height, X-spanning, for stiffness |

### 5.2 Cam channel

| Item | mm |
|---|---|
| Channel centreline | y = 34.0 (directly under the warp posts) |
| Channel floor, top face | Z −15.0 |
| Channel clear width | **14.5** (bar is 14.0 → 0.25 clearance per side) |
| Channel wall height | 5.0 above the floor |
| Channel length | full 233.0, open at both ends |
| Retention groove, both walls | 1.7 wide × 1.7 tall undercut, 0.4 above the floor |

The retention grooves take the bar's 1.5 × 1.5 bottom rails. The groove roof is a
1.7 mm bridge over a 1.7 mm gap — trivially printable, and it is the only bridging
anywhere in the model. The bar cannot lift out; you can turn the whole loom over.

### 5.3 Detent spring

| Item | mm |
|---|---|
| Compliant leaf, cut into the **+Y** channel wall | 26.0 long × 1.4 thick × 5.0 tall |
| Leaf slot behind it | 2.0 wide |
| Bump | hemisphere R1.0, 1.0 proud, at the leaf's midpoint |
| Bump centre, deck x | 35.5 |

The bump drops into whichever bar scallop is presented. It gives an audible click and
about 3 N of hold — enough that the bar stays put when you throw a shuttle, light
enough to pull one-handed.

### 5.4 Comb ledge

| Item | mm |
|---|---|
| Ledge top face | Z −10.0 (5.0 above the channel floor) |
| Ledge span | y 64.0 → 74.0, X 3.0 → 230.0 |
| Locating pins, 2 off | ⌀3.0 × 3.0 tall, at x = 40.0 and x = 175.0, y = 69.0 |
| Matching holes in the comb spine | ⌀3.3 blind, 3.2 deep, from the spine underside |

The spine drops onto the ledge, the two pins set X and Y, the two ears (§3.5) hold Z.

### 5.5 Deck snap tabs

| Item | mm |
|---|---|
| Tabs | 6 off, 7.8 (X) × 2.8 (Y) |
| Positions | x = 42 / 119.5 / 197 (deck-local 30 / 107.5 / 185), at y = 6.0 and y = 136.0 |
| Height above the wall top | 5.0 (Z −4.0 → +1.0) |
| Hook | 1.0 proud, 45° lead ramp |
| Tab root fillet | R1.0 |

Press the deck straight down onto the underframe; six tabs come up through the deck
border slots and click on the top face. It comes apart by squeezing all six inward —
deliberately stiff, because this joint holds the whole mechanism in register.

### 5.6 Bar rack (holds the seven unloaded bars)

Occupies the far apron, **y 142.0 → 210.0**, beyond the deck's far edge.

| Item | mm |
|---|---|
| Slots | 7 |
| Slot pitch (Y) | 9.0 |
| Slot clear width (Y) | 7.6 (bar's 7.0 max section + 0.6) |
| Divider wall thickness | 1.4 |
| Slot depth (Z) | 10.0, floor at Z −15.0, lip at Z −5.0 |
| Slot length (X) | 228.0, open at both ends |
| First slot centre | y = 150.0; slot *n* centre y = 150.0 + 9.0·(n−1); last at y = 204.0 |
| Thumb cut-out | 30.0 (X) × full rack depth, centred at x = 116.5, cut 6.0 down from the lip |

Bars stand **on edge**, teeth facing +Y, so 4.0 mm of each bar sticks above the lip and
you can pinch one out. The thumb cut-out lets you sweep a middle bar sideways instead
of digging. Emboss the letters `A B C D E F G H` along the rack's outer face as a
reminder that the eighth bar lives in the deck.

---

## 6. `part_shuttle_p1` … `p4` — the shuttles

**Envelope 26.0 (X-along-lane) × 12.4 (across) × 7.5 tall. Prints flat, hull underside
on the bed, fin up. One per player, in that player's colour.**

| Item | mm |
|---|---|
| Hull length | 26.0 |
| Hull width | **12.4** (lane floor is 13.0 → 0.3 clearance per side) |
| Hull height | **4.5** above the lane floor |
| Nose face | **vertical from Z 0 to Z 3.5**, then swept back 8.0 to the top face |
| Tail | mirror of the nose |
| Underside | flat, with a 0.5 × 45° chamfer all round |
| Grip fin | 20.0 long × 3.0 wide × 3.0 tall on the hull top face, ends R1.5 |
| Total height | 7.5 |
| Player mark | 1–4 pips, ⌀3.0, +0.6 proud on the fin's side |

The vertical nose face is the point of the part. A pure boat-shaped wedge would ride
up over a 3.0 mm post; a flat face 3.5 mm tall cannot. The taper starts only above the
post's maximum height, so the shuttle still looks and feels like a shuttle.

Seated tiles sit at Z −0.2, so the flat hull underside sweeps 0.2 mm clear of every
tile it passes. The shuttle never touches a tile and never needs to.

---

## 7. `part_tile_p{1-4}_{1-8}` — the thread tiles

**32 tiles: 8 each in 4 colours. Envelope 18.0 × 11.6 × 2.2. Prints flat.**

| Item | mm |
|---|---|
| Length (Y, along the lane) | 18.0 (pocket is 18.5 → 0.25 clearance per end) |
| Width (X) | 11.6 (pocket is 12.0 → 0.2 clearance per side) |
| Thickness | 2.2 (pocket is 2.4 deep → seats 0.2 below flush) |
| Corner radius | R1.0 |
| Bottom edge chamfer | 0.4 × 45°, so it drops in without fishing |
| Top-face finger scoop | 8.0 × 3.0, 1.0 deep, at the near end, aligned with the pocket's lift notch |
| Player mark | 1–4 pips, ⌀2.5, **recessed 0.6** on the top face |
| Weave texture | 0.4 pitch, 0.3 deep cross-hatch over the top face |

Pips are recessed rather than raised so the shuttle passing overhead never catches
one, and so the tiles are readable by touch and by colourblind players.

Colours: P1 red, P2 blue, P3 green, P4 yellow — matching the shuttles and matching the
worked example in rules §6.

---

## 8. Interfaces — how the six geometries meet

| # | Joint | Type | Numbers |
|---|---|---|---|
| 1 | Comb spine → deck border | **snap**, 2 ears | ear 5.8 × 2.8 into slot 6.0 × 3.0; hook 1.0; assembles once, not meant to be undone |
| 2 | Comb spine → underframe ledge | **rest + 2 locating pins** | ⌀3.0 pin into ⌀3.3 hole; spine underside lands at Z −10.0 |
| 3 | Underframe → deck | **snap**, 6 tabs | tab 7.8 × 2.8 into slot 8.0 × 3.0; hook 1.0; squeeze all six to release |
| 4 | Cam bar → channel | **sliding fit + T-rail capture** | 14.0 bar in 14.5 channel (0.25/side); 1.5 × 1.5 rail in 1.7 × 1.7 groove |
| 5 | Cam bar → detent | **spring bump into scallop** | R1.0 bump, 1.0 proud, into a 6.0 × 1.0 scallop; two scallops 16.0 apart |
| 6 | Cam bar → follower rib | **cam contact** | 5.0 rib on a 7.0 plateau; 3.0 lift; 33.7° ramps |
| 7 | Warp post → deck hole | **sliding fit, and the load path** | ⌀6.0 post in ⌀6.6 hole (0.3 radial); the hole, not the flexure, takes the shuttle's push |
| 8 | Shuttle → lane | **sliding fit** | 12.4 hull in a 13.0 floor (0.3/side); 3.0 walls guide it |
| 9 | Tile → pocket | **drop-in clearance fit** | 0.25 end, 0.2 side, seats 0.2 below flush |
| 10 | Living hinge → arm and spine | **monolithic**, no joint | 0.60 film, R1.5 blend on the top face only |

Joint 7 is the one to get right. The shuttle hits a raised post with a horizontal
shove; that shove is reacted by the 4.0 mm-thick deck plate around the ⌀6.6 hole, not
by the 0.60 mm hinge film. The flexure only ever carries the post's own weight and the
cam's lift. Do not open the post hole past ⌀6.8 or the post starts to lever the finger.

---

## 9. Print plan

### 9.1 Machine

| Item | Value |
|---|---|
| Bed | 256 × 256 × 256 (Bambu X1C / P1S class); anything ≥ 235 × 215 works |
| Largest footprint | `part_bar_rail` at 233 × 210 — use a **skirt, not a brim** |
| Nozzle | 0.4 |
| **Support** | **none, on any part** |
| Rafts | none |

### 9.2 Per-part settings

| Part | Layer | Walls | Infill | Bed orientation | Notes |
|---|---|---|---|---|---|
| `part_deck` | 0.20 | 3 | 15 % gyroid | flat underside down, lanes up | top surface is the play surface — 5 top layers, ironing on |
| `part_bar_rail` | 0.24 | 3 | 12 % gyroid | outer floor down, channel up | first layer 0.28; 233 × 210, watch corner lift on PLA |
| `part_warp_comb` | **0.20** | 3 | **100 %** | arm + spine underside down, posts up | see 9.3 |
| `part_bar_*` (×8) | 0.20 | 3 | 25 % gyroid | base down, cam teeth up | all 8 fit one plate, 18.0 pitch in Y |
| `part_shuttle_*` (×4) | 0.20 | 3 | 30 % | hull underside down, fin up | print all 4 of a colour together with the tiles |
| `part_tile_*` (×32) | 0.20 | 3 | 30 % | flat, scoop up | 8 per colour per plate |

### 9.3 The comb — the one part with a real constraint

- **Layer height 0.20 exactly.** The living-hinge film is **0.60 thick = 3 layers**.
  Any layer height that does not divide 0.60 leaves a fractional layer and the film
  becomes the weakest thing on the plate.
- **Orientation: the arm and spine undersides go flat on the bed; the twelve posts
  point up.** This is the only orientation in which the part has *zero* overhang, so
  the slicer generates no support at all and **nothing can touch a hinge film**. Check
  the sliced preview: support volume for this part must be 0.00 mm³.
- The film is printed as layers 1, 2 and 3 — solid, no infill, no gaps. Set
  **100 % infill** for the whole part; it is only ~12 g.
- The film bends about an axis 0.30 mm above the bed. Layer lines run **along** the
  finger, across the bending direction, which is the standard printed-flexure case at
  0.62 % strain — well inside PETG's elastic range.
- **PETG, not PLA.** PLA at this strain creeps: after a few weeks the posts stop
  returning fully flush and the game quietly breaks. Print at 240 °C / 80 °C bed,
  fan 40 %, and do not dry-store it near a window.
- No ironing on this part — ironing over a 0.60 film can drag it.

### 9.4 Recommended filament

| Part | Material | Colour |
|---|---|---|
| Deck, underframe | PLA (matte) | warm grey or natural linen |
| Warp comb | **PETG** | any; it is never seen except as twelve post tops |
| Cam bars ×8 | PLA | off-white, so the embossed `O`/`X` legend reads |
| Shuttles + tiles | PLA | red, blue, green, yellow — one spool each |

Total filament ≈ **355 g**: deck 95 g, underframe 130 g, comb 12 g, bars 8 × 11 g,
shuttles 4 × 2 g, tiles 32 × 0.6 g. Roughly 26 h of print time across 5 plates.

### 9.5 Plate plan (5 plates)

1. `part_bar_rail` — alone, 233 × 210.
2. `part_deck` + `part_warp_comb` — 215 × 142 and 206 × 46 side by side in Y.
3. All 8 cam bars — 226 × 144, 18.0 pitch.
4. Colours 1 and 2: 16 tiles + 2 shuttles.
5. Colours 3 and 4: 16 tiles + 2 shuttles.

### 9.6 Assembly (once, about two minutes)

1. Slide any cam bar into the underframe channel from the right until the T-rails
   engage; leave it at notch 1.
2. Drop the comb onto the ledge — the two ⌀3.0 pins set it.
3. Press the deck down onto the underframe until all six tabs click, and the comb's
   two ears click through the border slots at the same time.
4. **Check:** with a flat cam cell under every finger, all twelve post tops must sit
   flush with the lane floor — run a straightedge across. With bar A at notch 1,
   exactly lanes 1, 4, 7, 9 and 12 must be flat and the other seven proud by 3.0.
5. Fill the rack with the seven remaining bars, teeth facing away from you.

---

## 10. Bar compliance check

| Bar | Requirement | This design |
|---|---|---|
| Bed fit | every part orientable within ~246 × 246 | largest is 233 × 210 ✓ |
| Living hinge | film 0.4–0.6 thick | **0.60**, = 3 × 0.20 layers ✓ |
| Hinge and support | no support may touch a film | comb has **zero overhang** in its print orientation; support volume must slice to 0 ✓ |
| Part count | ≤ 60 physical parts | **47** ✓ |
| Concreteness | mm everywhere | every dimension above is mm ✓ |
