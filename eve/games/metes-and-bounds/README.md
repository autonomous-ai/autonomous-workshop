# Metes and Bounds
**identity:** like Quoridor + a print-in-place ten-segment folding rule with nine three-position detent hinges, where the single shared fence every player bends one hinge at a time IS the entire board state
**stage:** ship  **COGS:** $—  **price:** $44.99

**idea:** The entire board state is one printed object: a ten-segment folding rule with nine print-in-place knuckle hinges, each holding a compliant three-position detent at left, straight and right. Its root end seats in a socket on a 7x7 node board, so station plus nine hinge letters completely describes the fence. On your turn you change exactly one hinge, which swings every segment downstream of it onto new grid edges, then you may drive a stake into an empty parcel the fence now turns around, then you score one point for each of your own stakes currently sitting in a parcel with two or more fenced sides. Nobody else scores on your turn, so the fight is over reachability, not the final position: you never get to put the fence where you want it, only one hinge away from where the previous player left it. Legality is enforced by the plastic rather than by a referee -- an off-board bend has nothing to rest on, and a self-crossing bend will not lie flat because two segments cannot share a node, so the printed part physically refuses illegal moves. The strategic core is real area-adjacency scoring over a self-avoiding lattice path: a stake cluster near the root end is fat but easy for an opponent to strand with a single root-side swing, while a cluster near the free end is cheap to serve but sits where self-avoidance runs out of legal bends first. RESTATION -- lifting the root end into another node socket -- is the escape valve, and it costs a full turn.

## Brief
# Metes and Bounds — Physical Print Brief

**Version 1.0 — for CAD execution. Every dimension in mm. Nothing here is "about".**

Target printer class: 256 × 256 × 256 mm bed (Bambu P1/X1, Prusa MK4 with a
256 sheet). Effective usable X/Y is taken as **246 mm**. Nozzle 0.40 mm.

---

## 0. Part list and count

| Group | Part id | Qty | As-printed bounding box (mm) | Material |
|---|---|---|---|---|
| rule | `folding_rule_10seg` | 1 | 126.0 × 90.0 × 14.5 | PETG |
| board | `survey_board_7x7` | 1 | 236.0 × 236.0 × 8.0 | PLA |
| stakes_p1 | `stake_p1_a` … `stake_p1_f` | 6 | 11.5 × 11.5 × 16.4 each | PLA |
| stakes_p2 | `stake_p2_a` … `stake_p2_f` | 6 | 11.5 × 11.5 × 16.4 each | PLA |
| stakes_p3 | `stake_p3_a` … `stake_p3_f` | 6 | 11.5 × 11.5 × 16.4 each | PLA |
| stakes_p4 | `stake_p4_a` … `stake_p4_f` | 6 | 11.5 × 11.5 × 16.4 each | PLA |
| score | `score_rail` | 1 | 220.0 × 82.0 × 6.0 | PLA |
| score | `score_peg_p1` … `score_peg_p4` | 4 | 9.0 × 9.0 × 12.5 each | PLA |
| score | `round_peg` | 1 | 11.0 × 11.0 × 13.0 | PLA |

**Total physical parts: 32.** (Bar is ≤ 60.)

`round_peg` is added to the `score` group because rules §7 requires a round
track. Everything else matches `idea.json` exactly.

One master constant governs the whole set:

> **P = 36.000 mm — the node pitch.** Every hinge axis, every socket, every
> segment length derives from P. If a builder changes P, everything moves.

---

## 1. `folding_rule_10seg` — the folding rule

This is the whole board state and it is the only hard part. Read §1 in full
before modelling anything.

### 1.1 Topology

- 10 rigid **segments**, numbered 1 (root) … 10 (free tip).
- 9 **knuckle hinges**, numbered 1 … 9. Hinge *n* joins segment *n* to
  segment *n+1*.
- 11 **node axes** on the rule: root axis, hinge axes 1–9, tip axis.
  Consecutive axes are **exactly 36.000 mm apart**.
- Every one of the 11 axes carries a **downward peg** that drops into a board
  node socket.
- **Rotation is about Z** (perpendicular to the board). The rule is a planar
  linkage. It is printed flat and it plays flat. There is no out-of-plane
  folding anywhere in this design.

Naming convention used below, per hinge:
- **Segment N** owns the *fork* (top ear + bottom ear + spine + pivot post +
  both detent arms + the peg).
- **Segment N+1** owns the *barrel* (the rotating disc, its neck, its detent
  notches).

### 1.2 Global section

| Feature | Dimension |
|---|---|
| Segment body cross-section | **12.00 mm wide × 12.00 mm tall** |
| Rule overall height (board face → top face) | **12.00 mm** |
| Peg protrusion below board face | **2.50 mm** |
| Total printed Z | **14.50 mm** |
| Knuckle puck outside diameter | **⌀18.00 mm** |
| Segment body starts at | **r = 10.00 mm** from each axis |
| Clear body run per interior segment | 36.00 − 20.00 = **16.00 mm** |
| Root / tip end caps | **⌀14.00 mm × 12.00 mm** tall, centred on the axis |
| All exposed vertical edges | R1.00 mm fillet |
| Top face edge break | 0.60 × 45° chamfer |

### 1.3 The knuckle — Z stack

All Z values below are given **in print orientation**, with the rule's **top
face on the bed** (see §6.2 — the part is printed upside-down so the pegs print
as posts and nothing needs support). Z = 0 is the bed.

| Z from | Z to | Height | Owner | Feature |
|---|---|---|---|---|
| 0.00 | 3.00 | 3.00 | seg N | **Top ear** — ⌀18.00 solid disc |
| 3.00 | 3.20 | 0.20 | — | **Clearance gap** (1 layer @ 0.20) |
| 3.20 | 9.00 | 5.80 | seg N+1 | **Barrel** — ⌀13.00 OD, ⌀5.40 bore |
| 3.20 | 6.20 | 3.00 | — | ↳ *notch sub-band* (detent V-notches; seg N's arms live here) |
| 6.20 | 6.40 | 0.20 | — | ↳ *sub-band clearance* |
| 6.40 | 9.00 | 2.60 | seg N+1 | ↳ *neck sub-band* (the neck exits here) |
| 9.00 | 9.20 | 0.20 | — | **Clearance gap** (1 layer @ 0.20) |
| 9.20 | 12.00 | 2.80 | seg N | **Bottom ear** — ⌀18.00 solid disc |
| 12.00 | 14.50 | 2.50 | seg N | **Peg** — ⌀3.00, 60° conical lead |

The spine of segment N (§1.5) runs full height from Z 3.20 to 9.00 and welds
the two ears together. That is the only material crossing the barrel band on
segment N's side.

### 1.4 Pivot (the load-bearing joint)

| Feature | Dimension |
|---|---|
| Pivot post (seg N, integral with **top ear**) | **⌀5.00 mm**, Z 3.00 → 10.40 (7.40 tall) |
| Barrel bore (seg N+1) | **⌀5.40 mm**, Z 3.20 → 9.00, through |
| Capture bore (seg N, blind, in **bottom ear**) | **⌀5.40 mm**, Z 9.20 → 10.60 |
| Radial clearance, post ↔ bore | **0.20 mm** (0.40 on diameter) |
| Axial clearance, post tip ↔ blind bore floor | **0.20 mm** |
| Axial clearance, barrel ↔ each ear | **0.20 mm** each face |
| Post tip chamfer | 0.40 × 45° |

The post is captured at both ends. The barrel cannot lift off; the joint takes
lifting loads through the post, not through the printed layer bond of a
cantilever.

### 1.5 Fork spine (segment N)

Angles are measured in segment N's frame, **0° = the direction back toward
segment N's body**, increasing counter-clockwise seen from above.

| Feature | Dimension |
|---|---|
| Spine, **notch sub-band** (Z 3.20 → 6.20) | angular span **±45.0°**, r 6.80 → 10.00 |
| Spine, **neck sub-band** (Z 6.40 → 9.00) | angular span **±67.4°**, r 6.80 → 10.00 |
| Spine inner radius clearance to barrel OD (r 6.50) | **0.30 mm** |
| Spine → segment N body blend | tangent fillet R2.00 at r = 10.00 |

The wider spine in the neck sub-band **is the hard stop**. See §1.7.

### 1.6 Barrel neck (segment N+1)

The neck is the only link from the barrel out to segment N+1's body.

| Feature | Dimension |
|---|---|
| Neck width at the barrel | **5.00 mm** (half-angle 22.6° at r = 6.50) |
| Neck, r 6.50 → 8.70 | Z 6.40 → 9.00 only (**2.60 mm tall**) — passes *over* the detent arms |
| Neck, r 8.70 → 10.00 | Z 3.20 → 9.00 (**5.80 mm tall**) — full band height |
| Neck → body flare | 5.00 wide × 5.80 tall at r = 10.00, flaring to 12.00 × 12.00 by r = 13.00 |
| Minimum neck section | 5.00 × 2.60 = **13.0 mm²** |
| Clearance, neck underside (Z 6.40) ↔ arm top (Z 6.20) | **0.20 mm** |
| Clearance, neck tall section (r 8.70) ↔ arm max reach (r 8.50) | **0.20 mm** |

Neck angle **φ** is measured in the same frame: φ = 180° is **S** (straight),
φ = 90° is one turn, φ = 270° is the other. Which one reads L and which reads
R depends on the segment's direction of travel; label them on the part per
§1.9.

### 1.7 Hard stops — L and R are mechanical, not just detented

The neck's own side faces strike the spine's side faces:

- Neck edge sits at φ ∓ 22.6°.
- Spine edge in the neck sub-band sits at ±67.4°.
- Contact therefore occurs at **φ = +90.0°** and **φ = −90.0° (270°)** exactly.

No lug, no slot, no extra part. Contact faces are **radial planes**, 2.60 mm
tall × 3.20 mm deep (r 6.80 → 10.00) — 8.3 mm² of face per stop, plenty for a
hand-driven linkage. Break both stop edges with a 0.30 × 45° chamfer.

**The joint physically cannot exceed ±90°.** L and R need no detent to hold
them square; the detent only supplies the click and the return-to-seat.

### 1.8 Detent — the three clicks

Two opposed compliant arms on segment N ride the barrel OD and drop into
V-notches. Opposed pairing cancels side load on the pivot.

**Arms (segment N, ×2 per hinge — 18 arms on the part):**

| Feature | Dimension |
|---|---|
| **Arm thickness (the compliant film)** | **0.60 mm** |
| Arm height (Z) | **3.00 mm** (Z 3.20 → 6.20) |
| Arm free length along the curve | **7.00 mm** |
| Arm mean curve radius about the pivot axis | **R8.00 mm** |
| Arm root | on the spine at ±45.0°, root fillet **R0.80** |
| Nose | half-cylinder **R1.00 mm**, axis parallel to Z |
| Nose seat angle (rest position) | **±135.0°** |
| Nose contact radius, riding the OD | 6.50 (centre at r 7.50, outer at r 8.50) |
| Nose contact radius, seated in a notch | 5.50 (centre at r 6.50, outer at r 7.50) |
| Working deflection | **1.00 mm** |

**Notches (segment N+1, ×4 per hinge):**

| Feature | Dimension |
|---|---|
| Form | V-groove, **60° included angle**, root R0.30 |
| Depth below barrel OD | **1.00 mm** (local radius 5.50) |
| Z extent | Z 3.20 → 6.20, full notch sub-band |
| Angular positions, measured from the neck | **φ+45°, φ−45°, φ+135°, φ−135°** |
| Notch full angular width | ≈ 10° |
| Minimum notch-to-notch spacing | 90° |

**Why four notches.** With noses fixed at ±135° in segment N's frame and the
neck taking φ ∈ {90°, 180°, 270°}, the required notch offsets from the neck
are exactly {±45°, ±135°}. Four notches, evenly spaced 90° apart, seat **both**
noses simultaneously at **all three** detent positions and at no other angle.
There are no false mid-travel detents.

**Force.** PETG, E ≈ 2000 N/mm². I = 3.00 × 0.60³ / 12 = 0.0540 mm⁴.
F = 3EIδ/L³ = 3 × 2000 × 0.0540 × 1.00 / 7.00³ = **0.94 N per arm**,
**1.88 N per hinge**. That is a firm, audible click at this scale.

> **Tuning knob for the CAD builder:** arm free length **L** is the only
> number to change if the first print clicks too softly or too hard. L = 6.00
> gives 1.49 N/arm (stiffer); L = 8.00 gives 0.63 N/arm (softer). Change
> nothing else — thickness must stay in the 0.40–0.60 mm film band and the
> spec is at the top of it already.

Minimum angular clearance between a nose and the neck at any seated position
is **13.4°**. Verified at φ = 90°, 180° and 270°.

### 1.9 Markings

All markings are **engraved (recessed)**, because the rule's top face is the
bed face and recesses print crisp against a smooth sheet. Embossing here would
be squashed.

| Marking | Where | Spec |
|---|---|---|
| Segment number 1–10 | top face of each segment body, centred | 6.0 mm cap height, **0.60 mm deep** |
| Hinge number 1–9 | top ear top face, at r = 6.5, on the 0° side | 4.0 mm cap height, 0.60 mm deep |
| `◄ ROOT` arrow | top ear top face, pointing along 0° | 4.0 mm long, 0.60 mm deep |
| `L` / `S` / `R` | top ear top face at 135°, 180°, 225° (three tick marks + letters at r = 7.0) | 3.0 mm cap height, 0.60 mm deep |
| Station arrow | root end cap top face | 8.0 mm arrow, 0.60 mm deep, pointing along segment 1 |

Reading a hinge: the segment leaving the knuckle points at one of the three
ticks. That tick's letter is the hinge's current letter.

### 1.10 The as-printed shape

The rule is printed **already folded** into a compact legal shape. It is never
printed straight — straight is 360.00 mm long and would not fit any consumer
bed.

As-printed hinge letters, root → tip:

```
  hinge:   1  2  3  4  5  6  7  8  9
  letter:  S  S  L  L  S  S  R  R  S
```

Path in board units, root at (0,0) facing +X:

```
  (0,0)→(1,0)→(2,0)→(3,0)→(3,1)→(2,1)→(1,1)→(0,1)→(0,2)→(1,2)→(2,2)
```

Self-avoiding, 11 distinct nodes, 10 segments. Legal on a 7 × 7 field.

| | |
|---|---|
| Axis-centreline bounding box | 3P × 2P = **108.00 × 72.00 mm** |
| With ⌀18.00 pucks | **126.00 × 90.00 mm** |
| Printed Z | **14.50 mm** |

Every one of the three detent letters appears at least twice as-printed, so
each notch geometry is proved on the first print.

### 1.11 Estimated mass

≈ 43 cm³ solid envelope; at 4 walls / 25 % gyroid ≈ **55 g PETG**.

---

## 2. `survey_board_7x7` — the board

| Feature | Dimension |
|---|---|
| Overall plate | **236.00 × 236.00 × 5.00 mm** |
| Corner radius | R6.00 |
| Node pitch | **36.000 mm** |
| Node grid | 7 × 7 = 49 nodes, spanning 216.00 × 216.00 |
| Border (plate edge → outer node line) | **10.00 mm** |
| Node **A1** centre | (10.00, 10.00) from the bottom-left corner |
| Node **G7** centre | (226.00, 226.00) |
| Underside ribs | 3.00 mm tall |
| Total height | **8.00 mm** |

### 2.1 Node sockets (×49)

| Feature | Dimension |
|---|---|
| Bore | **⌀4.40 mm** |
| Depth from play face | **3.00 mm** |
| Floor thickness remaining | 2.00 mm |
| Mouth lead-in | **0.60 × 45° chamfer** |
| Capture window with a ⌀3.00 peg | ±1.30 mm |

### 2.2 Parcel dimples (×36)

Parcel centres sit 18.00 mm in X and Y from the parcel's bottom-left node.
Parcel **A1** centre = (28.00, 28.00); parcel **F6** centre = (208.00, 208.00).

| Feature | Dimension |
|---|---|
| Bore | **⌀6.00 mm** |
| Depth | **1.50 mm** |
| Mouth lead-in | 0.40 × 45° chamfer |

### 2.3 Engraving (play face)

| Marking | Spec |
|---|---|
| Grid lines — all 84 edges (42 horizontal + 42 vertical) | **1.00 mm wide × 0.60 mm deep**, node centre to node centre |
| Column letters **A–G** | bottom border, centred under each column, 5.00 mm cap height, 0.60 deep |
| Row numbers **1–7** | left border, centred beside each row, 5.00 mm cap height, 0.60 deep |
| Title `METES AND BOUNDS` | top border, 6.00 mm cap height, 0.60 deep |
| Corner-lot reminder `2+ FENCED SIDES = CORNER LOT` | bottom border right, 3.50 mm cap height, 0.60 deep |

### 2.4 Underside stiffening

A 236 mm PLA plate at 5.00 mm will curl without ribs.

| Feature | Dimension |
|---|---|
| Perimeter rim | 3.00 mm wide × **3.00 mm tall**, inset 1.00 mm from the edge |
| Cross ribs | 2.50 mm wide × **3.00 mm tall** |
| Rib positions (both X and Y) | 10.0, 46.0, 82.0, 118.0, 154.0, 190.0, 226.0 — i.e. directly under every node grid line |
| Rib count | 7 + 7 = 14 |
| Rib-to-rim junction | R2.00 fillet |

### 2.5 Off-board refusal

There is deliberately **no perimeter wall**. A segment that leaves the field
puts a ⌀3.00 × 2.50 mm peg on flat border with no socket under it. That
knuckle sits **2.50 mm proud**, the rule visibly tilts and will not lie flat.
That is the rules' §3.1 clause 1, enforced by geometry.

Border is **10.00 mm**, which clears the ⌀18.00 puck (r = 9.00) at every edge
node with 1.00 mm to spare — so a *legal* edge shape still lies perfectly flat.

### 2.6 Estimated mass

≈ **200 g PLA**.

---

## 3. `stake_p*_a` … `stake_p*_f` — 24 stakes

Identical geometry for all 24; only the **head silhouette** differs by player,
so the set stays readable even when all four are printed in one colour.

| Feature (bottom → top) | Dimension |
|---|---|
| Foot | **⌀5.60 mm × 1.40 mm** tall |
| Foot bottom edge chamfer | 0.40 × 45° |
| Shaft | **⌀4.00 mm × 9.00 mm** tall |
| Cone under head | ⌀4.00 → ⌀10.00 over **3.00 mm** rise (**exactly 45°**, needs no support) |
| Head | silhouette, **3.00 mm** thick |
| Total height | **16.40 mm** |

Head silhouettes, all fitting inside ⌀11.50:

| Player | Silhouette | Size |
|---|---|---|
| p1 | disc | ⌀10.00 |
| p2 | square | 10.00 × 10.00, corners R1.00 |
| p3 | equilateral triangle | inscribed in ⌀11.50, corners R1.00 |
| p4 | plus / cross | 10.00 × 10.00 overall, arms 3.50 wide, corners R0.80 |

Player id `1`–`4` engraved 0.50 mm deep, 4.00 mm cap height, on the head top.

**Clearance proof vs. the rule.** A stake sits at a parcel centre, 18.00 mm
from each of the four surrounding grid edges and 25.46 mm from each of the four
surrounding nodes.
- Rule body half-width 6.00 → **12.00 mm clear** of a fenced side.
- Knuckle radius 9.00 → **16.46 mm clear** of a node.
Stakes never block the rule (rules §3.1), and the rule never sweeps a parcel
centre.

Mass ≈ **4 g PLA** each, **96 g** for all 24.

---

## 4. `score_rail` — score track + round track

| Feature | Dimension |
|---|---|
| Overall | **220.00 × 82.00 × 6.00 mm** |
| Corner radius | R4.00 |
| All peg holes | **through-holes** (no bridging anywhere) |

### 4.1 Score holes — 164 total

Four lanes (one per player), score 0–40, split into two blocks so the rail
fits the bed.

| | |
|---|---|
| Hole diameter | **⌀4.40 mm**, through |
| Mouth chamfer, top face | 0.40 × 45° |
| Column pitch | **10.00 mm** |
| Lane pitch | **7.00 mm** |
| **Upper block**, scores **0–20** (21 columns) | column 0 at X = 10.00, column 20 at X = 210.00 |
| Upper block lane Y centres | p1 = 61.00, p2 = 54.00, p3 = 47.00, p4 = 40.00 |
| **Lower block**, scores **21–40** (20 columns) | column 21 at X = 10.00, column 40 at X = 200.00 |
| Lower block lane Y centres | p1 = 28.00, p2 = 21.00, p3 = 14.00, p4 = 7.00 |
| Hole count | (21 + 20) × 4 = **164** |
| Minimum wall between adjacent holes | 10.00 − 4.40 = 5.60 mm (X), 7.00 − 4.40 = 2.60 mm (Y) |

### 4.2 Round holes — 12 total

| | |
|---|---|
| Hole diameter | **⌀5.40 mm**, through |
| Y centre | **75.00 mm** |
| X centres | 10.00, 20.00, … 120.00 (12 holes at 10.00 pitch) |

### 4.3 Engraving (top face, all 0.50 mm deep)

| Marking | Spec |
|---|---|
| Score numbers 0–40 | 3.50 mm cap height, above each column in the upper block, below each column in the lower block |
| Lane glyphs | the four player silhouettes from §3, 5.00 mm across, at the left end of each lane (X = 3.00) |
| `ROUND` + numerals 1–12 | 3.50 mm cap height, along Y = 75.00 |
| `2P: 12 · 3P: 9 · 4P: 8 ROUNDS` | 3.50 mm cap height, right of the round track, X 130.00–215.00 |

Mass ≈ **55 g PLA**.

---

## 5. `score_peg_p1..p4` and `round_peg`

**Score pegs (×4), for ⌀4.40 holes:**

| Feature | Dimension |
|---|---|
| Shaft | **⌀4.00 mm × 7.00 mm** (0.20 mm radial clearance) |
| Shaft bottom chamfer | 0.50 × 45° |
| Cone | ⌀4.00 → ⌀9.00 over **2.50 mm** (45°, support-free) |
| Head | player silhouette from §3, **3.00 mm** thick, inside ⌀9.00 |
| Total height | **12.50 mm** |

**Round peg (×1), for the ⌀5.40 holes:**

| Feature | Dimension |
|---|---|
| Shaft | **⌀5.00 mm × 7.00 mm** (0.20 mm radial clearance) |
| Cone | ⌀5.00 → ⌀11.00 over **3.00 mm** (45°) |
| Head | hexagon, **11.00 mm across flats**, 3.00 mm thick, engraved `R` 0.50 deep |
| Total height | **13.00 mm** |

Mass ≈ 1.5 g each, **7 g** for all five.

---

## 6. Interfaces — every joint in the set

| # | Joint | Male | Female | Clearance | Fit |
|---|---|---|---|---|---|
| I1 | **Rule root peg ↔ node socket** (the station) | ⌀4.20 × 2.50, 0.50×45° chamfer | ⌀4.40 × 3.00 deep | 0.10 radial | **Snug drop-fit.** Locates the station; lifts out by hand for RESTATION. |
| I2 | **Rule hinge/tip pegs (×10) ↔ node sockets** | ⌀3.00 × 2.50, **60° conical lead 1.50 long** | ⌀4.40 × 3.00 deep, 0.60×45° mouth | 0.70 radial | **Self-centring loose fit.** Deliberately slack — see §6.1. |
| I3 | **Hinge pivot** | ⌀5.00 post, 7.40 long, captured both ends | ⌀5.40 bore through barrel + ⌀5.40 blind bore in bottom ear | 0.20 radial, 0.20 axial | **Print-in-place free rotation.** 0.20 mm gap each ear face. |
| I4 | **Detent** | 0.60 mm compliant arm, R1.00 nose, ×2 | 60° V-notch, 1.00 deep, ×4 | 1.00 mm working deflection | **Snap.** 1.88 N per hinge to break out. |
| I5 | **Hard stop, L and R** | neck side face, 2.60 tall × 3.20 deep | spine side face at ±67.4° | 0 (metal-to-metal analogue) | **Positive stop at exactly ±90.0°.** |
| I6 | **Self-avoidance interlock** | two ⌀3.00 pegs | one ⌀4.40 socket | — | **Refuses.** 3.00 + 3.00 = 6.00 > 4.40; and two ⌀18.00 pucks cannot be coaxial. |
| I7 | **Off-board interlock** | ⌀3.00 peg, 2.50 long | *no socket* | — | **Refuses.** Knuckle sits 2.50 proud; rule will not lie flat. |
| I8 | **Stake foot ↔ parcel dimple** | ⌀5.60 × 1.40 | ⌀6.00 × 1.50 deep | 0.20 radial, 0.10 axial | **Drop-in, self-standing.** Stake shoulder rests on the play face. |
| I9 | **Score peg ↔ rail hole** | ⌀4.00 × 7.00 | ⌀4.40 through, 6.00 thick | 0.20 radial | **Drop-in.** Peg protrudes 1.00 below the rail; sits proud on the table, harmless. |
| I10 | **Round peg ↔ round hole** | ⌀5.00 × 7.00 | ⌀5.40 through | 0.20 radial | **Drop-in.** |

**No living hinge, no snap-together, no glue, no fastener, no post-processing
assembly anywhere in this set.** The rule comes off the bed working; everything
else drops together.

### 6.1 The one real tolerance risk — read this

The rule seats **11 pegs into 11 sockets simultaneously**. Angular error at
each of the 9 hinges accumulates down the chain, and at P = 36.00 mm a 1°
hinge error is 0.63 mm of lateral drift at the next node.

The design absorbs this three ways:

1. **The V-detent is the angular datum, not the peg.** A 60° V held at 1.88 N
   is a hard angular locator; it takes out most of the error before the pegs
   ever see it.
2. **Interface I2 is deliberately slack** — ⌀3.00 peg in a ⌀4.40 socket is
   0.70 mm radial float per node, with a 1.50 mm 60° cone plus a 0.60 mm
   socket chamfer giving a **±1.30 mm capture window**. The rule self-registers
   as it is set down.
3. **Only the root peg (I1) is snug.** One tight peg, ten loose ones. There is
   no over-constraint to fight.

> **Build the calibration coupon first (§7.4).** If seating the rule feels like
> forcing it, open the sockets to ⌀4.60 before reprinting a 200 g board.

---

## 7. Print plan

Four plates. Nozzle 0.40 mm throughout.

### 7.1 Plate 1 — the rule (PETG, print alone)

| Setting | Value |
|---|---|
| Part | `folding_rule_10seg` |
| Footprint | 126.00 × 90.00 mm on a 246 mm envelope — **fits with 120 mm spare** |
| **Orientation** | **Flat, rule's TOP FACE ON THE BED. The part prints upside-down.** Hinge axes vertical (parallel to Z). |
| **Layer height** | **0.20 mm** (0.24 first layer) |
| Extrusion width | **0.30 mm** for perimeters — required so the 0.60 mm detent arms print as exactly 2 clean lines |
| Walls | 4 |
| Infill | 25 % gyroid |
| **Support** | **OFF — globally, no exceptions, including "support on build plate only".** |
| Bed adhesion | **Skirt only. No brim, no raft.** |
| Cooling | 40–60 % |
| Bed / nozzle | 80 °C / 240 °C (PETG) |
| Estimate | ≈ 3 h, ≈ 55 g |

**Why supports must be off.** Every one of the 18 detent arms is a 0.60 mm
vertical fin standing in the barrel's clearance band, and every hinge has two
0.20 mm axial gaps. Support material placed in either would weld the joint
solid and could not be cleared without snapping a 0.60 mm film. With the part
in this orientation **nothing requires support**, so switching support off
costs nothing and guarantees no support can ever touch a compliant film:

- Barrel first layer (Z 3.20) bridges a **0.20 mm** gap over the ⌀18.00 top
  ear — one layer, prints as if on solid.
- Detent arms first layer (Z 3.20) sits over the same ear at r 6.70–8.50,
  inside r 9.00 — fully backed.
- Neck reduced section (Z 6.40) bridges **5.00 mm** between the barrel wall at
  r 6.50 and the neck's own full-height section at r 8.70 — a wall-to-wall
  bridge.
- Bottom ear first layer (Z 9.20) bridges a **0.20 mm** gap over the ⌀13.00
  barrel, then carries a **2.50 mm** annular ledge out to ⌀18.00 — a short
  ledge off a fully supported edge, further backed by the spine and the neck.
- Pegs (Z 12.00 → 14.50) print last as ⌀3.00 posts on solid material.
- All head/cone transitions elsewhere in the set are 45°.

**Post-print:** flex each of the 9 hinges through L–S–R three times to free the
0.20 mm gaps. Expect a small first-break force. Do **not** cut anything.

### 7.2 Plate 2 — the board (PLA)

| Setting | Value |
|---|---|
| Part | `survey_board_7x7` |
| Footprint | 236.00 × 236.00 mm — **10 mm inside the 246 mm envelope**; a 3 mm brim lands at 242 mm |
| **Orientation** | **Flat, PLAY FACE ON THE BED, ribs up.** Gives a glass-smooth play surface and puts every socket, dimple and engraved line on the first layer where it prints sharpest. |
| Layer height | 0.20 mm (0.24 first) |
| Walls | 4 |
| Infill | 15 % gyroid |
| **Support** | **OFF.** Node sockets bridge ⌀4.40 at Z 3.00; parcel dimples bridge ⌀6.00 at Z 1.50; grid grooves bridge 1.00 mm at Z 0.60. All trivial. Ribs print upward as free-standing walls. |
| Bed adhesion | **3 mm brim** (large flat PLA plate) |
| Bed / nozzle | 60 °C / 210 °C |
| Estimate | ≈ 9 h, ≈ 200 g |

### 7.3 Plate 3 — stakes (PLA)

| Setting | Value |
|---|---|
| Parts | 24 stakes, 6 per player |
| **Orientation** | **Upright, foot on the bed.** All transitions are 45° or step-inward. |
| Layout | 6 × 4 grid at 20.00 mm pitch = 120 × 80 mm, or one 6-up plate per filament colour |
| Layer height | 0.20 mm |
| Walls | 3, infill 20 % |
| **Support** | **OFF.** |
| Bed adhesion | brim 3 mm (small footprint parts) |
| Estimate | ≈ 1 h 15 for all 24, ≈ 96 g |

Recommended: four separate 6-up plates in four filament colours. If printing
in one colour the head silhouettes still separate the sets.

### 7.4 Plate 4 — score rail, pegs, calibration coupon (PLA)

| Setting | Value |
|---|---|
| Parts | `score_rail` (220 × 82), 4 score pegs, `round_peg`, + coupon |
| **Orientation** | Rail flat, engraved face up. Pegs upright. |
| Layer height | 0.20 mm |
| Walls | 3, infill 20 % |
| **Support** | **OFF.** All rail holes are through-holes; all peg cones are 45°. |
| Estimate | ≈ 3 h, ≈ 62 g |

**Calibration coupon (not a game part — do not count it in the bill).**
A 60 × 40 × 8.00 mm PLA tile carrying:
- three sockets at ⌀4.30 / ⌀4.40 / ⌀4.60, each 3.00 deep with a 0.60 × 45°
  mouth, at 36.000 mm pitch;
- one ⌀6.00 × 1.50 dimple;
- one ⌀4.40 through-hole.

Print this **plus a two-knuckle stub of the rule in PETG** (segments 1–3,
axes at 36.000 pitch, root peg ⌀4.20, hinge pegs ⌀3.00) before committing to
the 9 h board. Check, in order: (a) the hinge rotates freely and clicks
firmly at all three positions; (b) both hard stops land square; (c) the
three-peg stub seats in the coupon without forcing. Adjust socket diameter and
detent arm length from that coupon, then print the real board.

### 7.5 Filament summary

| Material | Used for | Amount | Recommendation |
|---|---|---|---|
| **PETG** | `folding_rule_10seg` only | ≈ 55 g | Prusament PETG, Bambu PETG-HF, or equivalent. Tough, high flexural fatigue life, prints 0.60 mm walls crisply. |
| **PLA** | board, 24 stakes, rail, 5 pegs | ≈ 355 g | Any quality PLA / PLA+. Dimensionally stable over a 236 mm span; takes 0.60 mm engraving sharply. |

**Do not substitute on the rule.** PLA detent arms will crack at 0.60 mm after
a few hundred cycles. TPU and PP will not hold a detent — the arm has to be
stiff enough to click and PETG is the practical floor. ABS/ASA is acceptable
if the printer is enclosed and shrinkage is compensated, but the 36.000 mm
axis pitch must be re-verified against the board after shrinkage.

### 7.6 Total

≈ **410 g**, ≈ **16 h 15 m** across four plates. Every part fits with margin
on a 256 × 256 bed. No supports on any plate. No assembly step of any kind.

---

## 8. Bar check

| Bar | Status |
|---|---|
| Every part orientable within X/Y ≤ 246 mm | ✅ Largest is the board at **236.00 × 236.00**. Rule is **126.00 × 90.00** printed pre-folded (it is never printed at its 360 mm straight length). Rail **220.00 × 82.00**. |
| Compliant films 0.40–0.60 mm | ✅ The only compliant members are the 18 detent arms, at **0.60 mm** thick. Nothing else in the set flexes. |
| Layer height + orientation stated so no support touches a film | ✅ §7.1 — **0.20 mm layers, rule top-face-down, support globally OFF**, with a feature-by-feature proof that nothing needs support. |
| Bill ≤ 60 physical parts | ✅ **32 parts.** |
| Concrete mm everywhere | ✅ Every feature above carries a number. `P = 36.000 mm` is the single governing constant. |


## Rules
Pending full rulebook (engine-tested skeleton).

## Playtest evidence
{'source': 'llm_table', 'games_played': 8, 'first_seat_wins': 0.375, 'ends': True, 'decisiveness': 0.75, 'ask_to_play_again': 0.792, 'note': 'real LLM table: 8 games, 24 seats; replay-ask = 79%'}

_rendered by Eve · 2026-08-23T01:09:21+00:00_