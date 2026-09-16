# Antisol

Dou Shou Qi, unchanged, played with the eight planets ranked by their real
measured diameters. Matter faces antimatter, and you win by walking one of your
worlds into the rival sun.

- **In one line:** Jungle Chess where every piece is a planet at the fifth root
  of its true diameter, leaning at its true axial tilt, and the direction of
  that lean is which army it belongs to.
- **What it looks like:** Sixteen planets, each a globe standing on a flat
  34 mm disc, on a dark gray 7x9 field crossed by a cocoa-brown asteroid belt,
  with a star at each end of the board, ringed by its own corona.
- **What you do:** Play Dou Shou Qi exactly as written. Nothing is added,
  removed, or altered.
- **Why it is new:** The rank ladder is the fifth root of NASA's measured
  equatorial diameters; the ownership cue is the parity inversion of the real
  axial tilts. Two real datasets, each doing a job the rules require, and
  neither invented.
- **Printed parts:** 42 parts, 58 unique geometries, 12 filament colours. No
  assembly, no hardware, no supports.

---

## 1. Source game and rights

Source: **Dou Shou Qi** (Jungle Chess / Animal Chess), traditional Chinese,
public domain. No trademarked variant, branded edition, publisher rulebook,
artwork, or terminology is used.

Rules baseline, frozen: **https://liacs.leidenuniv.nl/~visjk/doushouqi/about.html**

The Leiden strength ladder is used verbatim, including its ordering at ranks 3
and 4, which differs from some Western listings.

| Rank | Leiden name | Planet | Real equatorial diameter (km) |
|---:|---|---|---:|
| 1 | Rat | Mercury | 4,879 |
| 2 | Cat | Mars | 6,779 |
| 3 | Wolf | Venus | 12,104 |
| 4 | Dog | Earth | 12,742 |
| 5 | Panther | Neptune | 49,244 |
| 6 | Tiger | Uranus | 50,724 |
| 7 | Lion | Saturn | 116,460 |
| 8 | Elephant | Jupiter | 139,820 |

**Eight pieces per player, sixteen on the board.** Two players. Zero rules are
added, removed, or changed.

### 1.1 Frozen rule ledger

Every row is a restatement of a rule already on the Leiden page. The right-hand
column is what the plastic does about it, and in every case the answer is
"shows", never "enforces".

| Leiden rule | Physical expression in this set |
|---|---|
| Player count: 2 | Two armies, eight pieces each. |
| Setup: fixed opening position | Saturn a1, Uranus g1, Earth b2, Mars f2, Mercury a3, Neptune c3, Venus e3, Jupiter g3; mirrored 180 degrees for the opposing side. |
| Turn order: alternating, no passing | Unchanged. |
| Legal moves: one orthogonal step | Unchanged. Every land cell is flat field bounded by a 1.20 mm engraved grid groove; all sixteen pieces seat on all of them. |
| Equal or higher strength captures | Strength is globe diameter and the seven-segment numeral. Read, never enforced. |
| Rat captures Elephant | Mercury (rank 1) captures Jupiter (rank 8). No geometry involved. |
| Elephant may not capture Rat | Same. |
| Only the Rat may enter the water | **Not enforced by geometry.** Every belt cell carries a flat Ø26.00 landing pad level with the field and any piece will sit on it. See section 6. |
| Rat may capture in the water | Same pad. |
| Rat may not capture the Elephant from the water | Unchanged. |
| Lion and Tiger leap the water | Saturn and Uranus. Unchanged, unenforced. |
| Leap blocked by a rat on an intervening water square | Unchanged. |
| Piece in an opponent's trap has strength 0 | Trap cells are corona wells: a `corona_cell` tile floors a 34.80 x 34.80 x 6.00 mm pocket, leaving a 3.00 mm well. A trapped piece sits **3.00 mm lower** than on open ground, readable across the table. The well is side-blind; the rule is not. |
| A piece in its own trap is unaffected | Identical well at both ends. |
| Win by entering the opponent's den | The den plug stands 1.00 mm proud of the field on a flat top face. A piece seats on it exactly as it does on any land cell, one step higher. |
| Forbidden to enter one's own den | Identical geometry at both dens. A rule, not a shape. |
| Win by eliminating all opposing pieces | Empty tray. |
| Threefold repetition and stalemate are draws | No geometry required. |

**Nothing in this set makes an illegal move physically impossible.** That is a
deliberate rejection of the obvious move — a narrowed water channel that only
the smallest base can enter — because `TASTE.md` states that an affordance
which makes an illegal move impossible is a rule change wearing a costume.
Every cell in this set accepts every piece.

---

## 2. Theme mapping

One mechanical role to one thematic meaning to one physical cue. No renamed
nouns.

| Mechanic | Meaning | Physical cue |
|---|---|---|
| Piece strength | Real planetary size | Globe diameter, fifth root of measured equatorial diameter |
| Piece identity | The planet itself | Real surface colouring and markings at its real axial tilt |
| Ownership | Matter vs antimatter | Parity inversion: Sol worlds lean right, Anti-Sol worlds lean left, by the same true obliquity. Disc colour and disc taper confirm it. |
| The den | A star | A raised `sunflower_yellow` plug, the highest ordinary surface on the board, with two tall prominences bursting from it at the board edge |
| Winning | Delivering matter into the opposing star | The piece seats on the star itself, 1.00 mm above the field |
| Cannot enter your own den | Feeding your own star changes nothing | Identical geometry, rule-only restriction |
| The water | The asteroid belt | Recessed faceted rubble field, 2.00 mm below the field plane |
| **The trap** | **The star's corona** | **The three cells that ring each den are sunken corona wells in the star's own colour, with flame tongues rising from their outer corners. The board already puts three cells around every den; that ring is the corona.** |
| Piece in an opponent's trap has strength 0 | A world inside the corona is stripped of rank | The piece drops 3.00 mm into the corona well. Mercury takes Jupiter there, and the reason is visible. |
| Rank ladder as a whole | The solar system to scale in size, not distance | Height ladder 17.78 to 30.97 mm, strictly increasing |

---

## 3. The measurement system

### 3.1 Globe diameter = fifth root of real equatorial diameter

Bound above by Saturn: its ring must sit 1.00 mm inside the Ø34.00 disc, so the
ring outer diameter is 32.00 mm; the ring must project at least 3.00 mm per side
to read at the product frame, so Saturn's globe is 26.00 mm.

    globe_diameter_mm = 13.785 * (D_planet_km / 4879) ^ 0.2

The exponent is exactly 0.2000 — the fifth root — carried over unchanged from
the derivation in `outputs/planetshear.md` section 6.1. Only the constant moved,
from 17.400 to 13.785, and it moved because Saturn's rings now set the ceiling
where Jupiter's ball used to.

### 3.2 The derived ladder

All globe diameters `[inferred]` from `[observed]` NASA planetary fact-sheet
values. Axial tilts `[observed]`.

| Rank | Planet | Globe Ø | Globe centre Z | Seat land Ø | Total height | Axial tilt | Relief bodies |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Mercury | 13.78 | 9.89 | 10.36 | 17.78 | 0.03° | 1 |
| 2 | Mars | 14.72 | 10.36 | 11.12 | 18.72 | 25.19° | 2 |
| 3 | Venus | 16.53 | 11.27 | 12.60 | 20.53 | 177.36° | 1 |
| 4 | Earth | 16.70 | 11.35 | 12.73 | 20.70 | 23.44° | 3 |
| 5 | Neptune | 21.89 | 13.95 | 16.96 | 25.89 | 28.32° | 2 |
| 6 | Uranus | 22.02 | 14.01 | 17.06 | 26.02 | 97.77° | 1 |
| 7 | Saturn | 26.00 | 16.00 | 20.30 | 30.00 | 26.73° | 3 |
| 8 | Jupiter | 26.97 | 16.49 | 21.09 | 30.97 | 3.13° | 2 |

All mm. Derivations, all `[inferred]`:

- `globe_centre_Z = 3.00 + globe_Ø / 2` — the globe is sunk 2.00 mm into a
  5.00 mm disc.
- `seat_contact_Ø = 0.7431 * globe_Ø` — the seat cone springs from latitude
  −42.0°.
- `seat_land_Ø = seat_contact_Ø + 2 * (0.3309 * R − 2.00) * tan(12°)` — the
  cone spreads outward at 12° from vertical down to the disc face.
- `total_height = 3.00 + globe_Ø + 1.00` — disc, less the 2.00 mm sink, plus
  1.00 mm of surface relief.

**Height ladder is strictly increasing: 17.78 → 30.97 mm. Verified.**

**The widest object on the board is Saturn's ring at Ø32.00, which is still
2.00 mm narrower than its own disc. No piece overhangs its own base.**

### 3.3 The twins, and how they are resolved

Venus and Earth differ by 0.17 mm of globe diameter; Uranus and Neptune by
0.13 mm. The real planets are 5% and 3% apart, and no honest mapping separates
them. They are resolved by three redundant channels that cost no invented data:

- **The seven-segment numeral** on the disc wall, at 0° and 180°, is
  unambiguous and needs no comparison.
- **Surface**: Earth carries green land, dryland and polar ice; Venus carries a
  single inverted cloud pattern. Neptune carries a dark spot and white cloud
  streaks; Uranus carries one band, and that band runs **vertically** because
  Uranus lies on its side at 97.77°.
- **Colour**: Earth `blue` with `green`; Venus `beige`. Neptune `blue`; Uranus
  `cyan`.

---

## 4. Ownership: parity inversion

Both armies must look like the real planets, so ownership cannot live on the
globe's colouring. It lives in three places, none of which touches the planet's
appearance:

1. **Lean direction.** Every globe's relief is rotated about the +Y axis (the
   axis running toward and away from the seated player) by that planet's true
   obliquity. **Sol worlds lean their north pole toward +X, Anti-Sol worlds
   toward −X.** The two armies are exact mirror images across the piece's YZ
   plane. Uranus, at 97.77°, points its pole almost horizontally — right for
   matter, left for antimatter. This is the primary cue and it is a silhouette
   cue, legible from any seat without colour.
2. **Disc taper.** The Sol disc **flares outward** as it rises, Ø33.00 at the
   bed to Ø34.00 at the top. The Anti-Sol disc **tapers inward**, Ø34.00 to
   Ø33.00. Both draft at 6.5° from vertical. Matter expands; antimatter
   collapses.
3. **Disc colour.** Sol `white` with a `black` numeral; Anti-Sol `black` with a
   `white` numeral — the widest lightness separation the palette allows, and
   every disc is read against the `dark_gray` field, never against the page.

The globe sphere itself is unchanged under mirroring, so **only the relief
bodies are duplicated** — fifteen per side, thirty in total. Globes, seats,
numerals and discs are shared between the armies.

---

## 5. The board

**Field:** 7 files (a–g) x 9 ranks (1–9) at **36.00 mm pitch** = 252 x 324 mm.
**Board:** 268 x 340 x 9.00 mm including an 8.00 mm border. Colour `dark_gray`.

Terrain coordinates. Dens and traps are `[observed, Leiden]`; water coordinates
and the opening setup are `[inferred]` from the standard layout, which the
Leiden page does not fix.

- **Dens:** d1 and d9.
- **Traps:** c1, d2, e1 and c9, d8, e9.
- **Belt (water):** files b–c and e–f, ranks 4–6. Two 3x2 blocks centred on
  rank 5, leaving file d dry so the vertical leap has something to cross.
- **Opening setup:** Saturn a1, Uranus g1, Earth b2, Mars f2, Mercury a3,
  Neptune c3, Venus e3, Jupiter g3; mirrored 180° for the opposing side.

**Surface treatment. The field is flat and the grid is cut into it.** The board
follows `toys/mara-masque-dustlight-crossing` in this repository: cells are drawn
by engraved lines, not by wells. A piece stands on the board; it does not sink
into it. Depth is reserved for terrain — trap, den, belt — where a change of
level is the rule being shown.

- **Grid groove.** Every boundary between two land cells, and the entire
  perimeter of the 7 x 9 field, is a **1.20 mm wide x 0.60 mm deep**
  square-bottomed groove centred on the boundary. Three extrusion widths at a
  0.4 mm nozzle; no floor thinner than 8.40 mm remains under it.
- **Land cells.** Flat, level with the field datum, no recess of any kind. A
  seated Ø34.00 disc leaves **1.00 mm** to its cell boundary and therefore
  clears the groove edge by **0.40 mm** on every side. No piece ever bridges a
  groove.
- **Trap cells: 34.80 x 34.80 x 6.00 mm** blind pocket, corners R1.00, inset
  0.60 mm from each cell boundary — the same pocket as a den or a belt cell. It
  receives a `corona_cell` tile 3.00 mm thick, which leaves a **3.00 mm well**
  above it. The pocket rim is that cell's line and the groove is omitted on all
  four of its boundaries. **Every terrain pocket on this board is the same
  34.80 x 34.80 x 6.00 hole**; only what drops into it differs.
- **Den cells: 34.80 x 34.80 x 6.00 mm** blind pocket, corners R1.00, inset
  0.60 mm from each cell boundary, receiving the den plug's spigot. Groove
  omitted on its boundaries; the plug's 1.00 mm proud flange is the line.
- **Belt cells: 34.80 x 34.80 x 6.00 mm** blind pocket, corners R1.00, inset
  0.60 mm from each cell boundary. Two adjacent belt cells are therefore parted
  by a **1.20 mm** rib standing at field datum — the same width as the grid
  groove, so the grid reads unbroken straight through the water.
- All recesses blind. No through-holes anywhere in the set.
- Internal panel-seam corners open square, not chamfered: a chamfer at a seam
  leaves a thin tapering wedge that fails a fixed-nozzle wall check.

**Closest approach between two pockets**, which is the board's thinnest
material: `36.00 − 17.40 − 17.40 = **1.20 mm**`, 6.00 mm tall. It occurs between
the d2 trap pocket and the d1 den pocket, and between any two adjacent belt
cells. One number for the whole board, 0.40 mm clear of the 0.80 mm wall floor.

**Why the grid is cut and not moulded.** An earlier draft gave all 63 cells a
Ø34.40 x 0.40 mm landing recess. The reference image of that board came back
reading as a muffin tray — sixty-three circles and no grid at all. A board is
read as a lattice of lines, and a 0.40 mm well does nothing a piece's own weight
is not already doing. The recesses are gone; the lines are cut. This is the one
change the reference-image stage found in the spec rather than in the image.

**Panel split.** 268 x 340 mm exceeds a 200 mm bed. Cut after file c and after
rank 4:

| Panel | Size (mm) | Contains |
|---|---:|---|
| `panel_southwest` | 116 x 152 | files a–c, ranks 1–4; trap c1; belt cells b4, c4 |
| `panel_southeast` | 152 x 152 | files d–g, ranks 1–4; den d1; traps d2, e1; belt cells e4, f4 |
| `panel_northwest` | 116 x 188 | files a–c, ranks 5–9; trap c9; belt cells b5, b6, c5, c6 |
| `panel_northeast` | 152 x 188 | files d–g, ranks 5–9; den d9; traps d8, e9; belt cells e5, e6, f5, f6 |

Twelve belt cells, two dens, six traps, forty-three plain land cells; 63 total.
The c1 and c9 traps sit on the **west** panels, not the east ones — file c is cut
away with files a–b. An earlier draft of this table put them on the east panels,
which was simply wrong.

Largest panel 152 x 188 mm, inside a 200 mm bed. Sums verified: 116+152 = 268,
152+188 = 340.

---

## 6. The asteroid belt

**One geometry, twelve parts. One tile per cell.** The belt is a run of tiles
laid on the grid, not a slab laid over it, so the cell lines survive across the
water exactly as they do on land.

### `belt_cell`

**34.30 x 34.30 x 6.00 mm**, corners R1.00, `cocoa_brown`. Drops into the
34.80 mm belt pocket with **0.25 mm/side** clearance, top flush with the field.
Twelve identical parts; six at b4–c6, six at e4–f6.

- **Rubble field:** irregular faceted forms, floor **2.00 mm below field
  datum**, crests rising to field datum. Faceted rather than rounded: small
  circular detail degrades at nozzle scale where facets hold their shape.
- **Landing pad:** one smooth flat **Ø26.00 mm** disc at the exact centre of the
  tile, level with the field and with every crest around it. A seated Ø34.00
  disc covers the pad and overlaps about 4.00 mm of rubble on each side, resting
  on crests that are coplanar with the pad, so it stands level and does not
  rock. **The belt is a picture of an exclusion, not an enforcement of one.**
- **Four-fold symmetry.** The tile is symmetric under 90° rotation about its own
  centre, so orientation is never a fit question and any tile goes in any belt
  cell either way round.

**What this replaced, and what it cost.** An earlier draft made the belt two
multi-cell slabs — `belt_short` at 72 x 36 and `belt_long` at 72 x 72 — because
the two 3x2 water blocks cross the rank-4/rank-5 panel seam and a slab could
bridge it. A slab erases the grid underneath the water and needs two geometries
to do it. One tile per cell costs **eight more printed parts** and gives back one
geometry, an unbroken grid, and a belt that no longer cares where the panel seam
falls: the seam now runs along a rib between tiles instead of through a part.

---

## 7. The star and its corona

**`den_plug` is the one component permitted to break the legibility floor, and
the cost is recorded below. The corona is not — it stays under the floor
deliberately, and section 7.4 says why.**

Dou Shou Qi already puts three cells around every den. That ring is the corona:
the rule that a piece standing there has strength 0 is the star stripping a
world of its rank, and it does not matter how big the world was. Mercury takes
Jupiter inside the corona, and on this board you can see why.

This mapping replaced an earlier one in which the corona was four prongs on the
den plug and the trap was described as "inside the rival star's tidal radius".
That was a renamed noun over an unthemed hole — the exact thing section 2
forbids — and the ring the design was reaching for was already on the board,
drawn by the rules.

### 7.1 `den_plug` — the star

A **36.00 x 36.00 mm flange standing 1.00 mm proud** — the highest ordinary
surface on the board — on a **34.30 x 34.30 x 6.00 mm** spigot buried in the den
pocket at 0.25 mm/side. Total height 7.00 mm. The flange covers the cell edge to
edge, so it hides the pocket's clearance line and is itself the cell's boundary
mark. Top face **flat, no recess**, exactly like a land cell: a winning piece
seats on it the way it seats anywhere else, one 1.00 mm step higher. The 0.85 mm
frame and the four corners carry a hexagonal granulation relief 0.50 mm proud.

### 7.2 `den_prominence` — two flares, at the board edge only

Tapered flames rising from the **two plug corners that face the board border**,
where 8.00 mm of free border lies beyond them. Leaning **12° outward from
vertical**, drafted so no face is shallower than 45° from vertical.

- Base **Ø11.00**, **18.00 mm** above the field, base circle centred **23.40 mm**
  from the cell centre along the diagonal. Tip radius 0.75 mm, minimum wall
  3.00 mm at the base.
- **Two per den, not four.** The two corners facing into the field belong to the
  corona now.

**The flares overhang the den cell, and they have to.** The largest circle that
fits inside one cell's corner — tangent to both cell edges and to the Ø34.00
disc footprint — has a radius of only **3.50 mm**, far too small for a flare.
Placing the base at 23.40 mm puts it **4.05 mm outside the 36.00 mm cell**, into
the corner void the meeting cells share. Clearances, measured base-edge to
disc-edge rather than to disc-centre:

| Against | Base centre to cell centre | Clear by |
|---|---:|---:|
| The den's own seated disc | 23.40 mm | **0.90 mm** |
| The neighbouring corona cell's seated disc | 25.54 mm | **3.04 mm** |

`den_plug`'s printed envelope is therefore **44.10 x 40.10 mm**, not
36.00 x 36.00. It is asymmetric because both flares are on the border side.

The flares are cantilevered from the plug, not stood on the board, so the part
of each base that crosses the cell boundary floats 1.00 mm above the field, and
above a corona well 4.00 mm above its floor. Nothing needs to be under them.

*An earlier draft also carried a shorter pair at the two field-facing corners.
Those corners are now the corona's, and the short pair is deleted — one geometry
returned to the budget.*

### 7.3 `corona_cell` — the trap, and the ring

Six parts, three per den, at c1/d2/e1 and c9/d8/e9. One geometry, installed in
three rotations.

**Body.** **35.50 x 35.50 x 3.00 mm** tile, corners R1.00, with the **den-facing
edge cut back to 34.30 mm**. It drops onto the floor of the 34.80 x 34.80 x 6.00
terrain pocket, top face **3.00 mm below field datum**. The three edges that
face land run to within 0.25 mm of the cell boundary, because solid board lies
behind them and there is no thin wall to protect; only the den-facing edge is
pulled in, to keep the 1.20 mm rib between the two pockets.

The tile is the **floor** of the well, not its wall. The board's own pocket
forms the 3.00 mm wall, 34.80 mm square, so a seated Ø34.00 disc has 0.40 mm per
side and drops exactly 3.00 mm below the field.

**Face.** Flame tongues radiating from the cell centre outward, **engraved
0.40 mm deep**. A seated disc bridges them without rocking — it already bridges
the 1.20 mm grid groove — and when the cell is empty they read as a star's
corona seen from directly above.

**`corona_tongue`.** Two flames rising from the **two corners of the edge
furthest from the den**, so every tongue points away from the star. Leaning 12°
outward, tapering, tip radius 0.60 mm.

- Base **Ø6.00**, **4.00 mm above field datum**, base circle centred
  **20.60 mm** from the cell centre along the diagonal, filleted R1.50 into the
  tile face.
- Clear of that cell's own Ø34.00 disc by **0.60 mm**, base edge to disc edge.
- **The tongues do not overhang their cell.** 20.60 mm along the diagonal puts
  the base centre 14.57 mm from the cell centre on each axis, and with a 3.00 mm
  base radius the outer edge reaches 17.57 mm against a 18.00 mm cell half-width.
  Unlike the den flares, nothing here crosses a boundary.

Six tongues ring each star — two west, two north, two east — and the two den
flares close the arc at the board edge. Eight vertical elements per den, and
only the two tall ones are above the legibility floor.

### 7.4 Colours

| | Sol | Anti-Sol |
|---|---|---|
| `den_plug` | `sunflower_yellow` | `black` |
| `den_prominence` | `orange` | `cyan` |
| `corona_cell` and `corona_tongue` | `orange` | `cyan` |

The corona is the same colour as the star's own flares, which is what makes the
three trap cells read as one ring belonging to that den rather than as three
unrelated coloured squares. No new filament: both colours were already in the
set.

### 7.5 What the hero costs, accepted in writing

- **The two flares rise 18.00 mm at the board edge.** From the seat *opposite*
  that den, they stand between the eye and the den cell's far edge. That is the
  seat attacking the den, and it is the sightline the hero is paid for.
- **No other component in the set is permitted any of this.** The corona tongues
  are held to **4.00 mm**, which is 13.78 mm below the crown of the shortest
  globe in the set, so a corona cell can never occlude a piece anywhere on the
  board. The corona is a large idea kept deliberately low; the star is the only
  thing allowed to stand up.
- **The tongues at d2 and d8 sit in open field**, at corners shared with live
  land cells. At 4.00 mm they occlude nothing, but a hand reaching across them
  will feel them. Both players, both ends, equally.

## 8. The worlds

**Each piece is a single printed part.** The disc, the seat, the globe and every
relief patch are one solid body in multiple filament colours. No assembly, no
fastener, no fit, nothing that can come apart in play.

### 8.1 The disc

Ø34.00 x 5.00 mm, top edge rounded 0.60 mm, bottom edge left sharp so the piece
sits flat.

- **`disc_sol`** — wall flares outward as it rises: Ø33.00 at the bed, Ø34.00 at
  the top of the wall, 6.5° draft. `white`.
- **`disc_anti`** — wall tapers inward: Ø34.00 at the bed, Ø33.00 at the top,
  6.5° draft. `black`.

Neither profile presents any face shallower than 45° from vertical.

### 8.2 The numeral

`numeral_1` … `numeral_8`: seven-segment digits, **3.60 mm tall, 2.80 mm wide,
1.00 mm stroke, standing 0.45 mm off the disc wall**, centred at Z 2.20, placed
at **0° and 180°** so both seated players read rank without touching a piece.
Every stroke drafted: the underside rises 1.20 mm per mm of relief so it is not
a ceiling over open air; sides and top draft 0.50 mm per mm.

`black` on Sol discs, `white` on Anti-Sol discs.

### 8.3 The globe

`globe_mercury` … `globe_jupiter`: a sphere at the ladder diameter, sunk 2.00 mm
into the disc top face, carried by an integral seat cone that springs from
latitude −42.0° and spreads outward at 12° from vertical down to the disc face.
The seat is material added around the globe's foot, never a cut taken out of it,
and it is finished in the globe's own colour so nothing changes colour where the
two meet. It exists because a sphere resting tangentially on a flat disc leaves
an unsupported cap underneath it.

The globe is a body of revolution and is therefore **identical under mirroring**.
One geometry per planet serves both armies.

| Geometry | Ø | Colour |
|---|---:|---|
| `globe_mercury` | 13.78 | `gray` |
| `globe_mars` | 14.72 | `red` |
| `globe_venus` | 16.53 | `beige` |
| `globe_earth` | 16.70 | `blue` |
| `globe_neptune` | 21.89 | `blue` |
| `globe_uranus` | 22.02 | `cyan` |
| `globe_saturn` | 26.00 | `yellow` |
| `globe_jupiter` | 26.97 | `orange` |

### 8.4 The surface

Relief stands **1.00 mm proud** of the globe with 45° chamfered edges. Minimum
outline width is **14° of arc** anywhere on the set: a south-facing relief edge
needs about 7° of arc to ramp without support, and below 14° the outline comes
off the bed as a smear. On the smallest globe (Mercury, R = 6.89) 14° of arc is
1.68 mm; on the largest (Jupiter, R = 13.49) it is 3.30 mm.

Every relief body exists twice — `sol_*` rotated so the planet's north pole
leans toward +X, `anti_*` mirrored across YZ so it leans toward −X.

| Planet | Relief bodies | Colours | What it depicts |
|---|---|---|---|
| Mercury | `mercury_plains` | `dark_gray` | Two-tone albedo map: smooth plains and the Caloris basin as raised patches on a `gray` globe. Not craters — at this scale a crater reads as a print defect, while the albedo map is what Mercury actually looks like from a distance. Pole vertical: tilt is 0.03°. |
| Mars | `mars_albedo`, `mars_caps` | `cocoa_brown`, `white` | Syrtis Major and Mare Acidalia as dark patches; both polar caps. Pole leans 25.19°. |
| Venus | `venus_ypattern` | `orange` | The Mariner-10 ultraviolet cloud Y, laid out about a pole 2.64° from vertical **pointing downward**. Venus is upside down — 177.36° — and its pattern is the only inverted one in the set. |
| Earth | `earth_land`, `earth_dryland`, `earth_ice` | `green`, `beige`, `white` | Continents, dryland (Sahara and Arabia, the Kalahari, inner Asia, the American southwest, the Australian outback), and the northern ice cap with lobes reaching onto the coasts. Pole leans 23.44°. |
| Neptune | `neptune_spot`, `neptune_streaks` | `dark_gray`, `white` | The Great Dark Spot and the white companion cloud streaks. Pole leans 28.32°. |
| Uranus | `uranus_band` | `white` | One faint band, running **pole to pole, vertically on the visible face**, because the pole lies 7.77° past horizontal. No rings: Uranus's rings are effectively invisible in a real image, and adding them would be invention. |
| Saturn | `saturn_bands`, `saturn_ring`, `saturn_ring_web` | `cocoa_brown`, `white`, `white` | Four belts over ±60° latitude at 12° width (2.72 mm). The ring is described in 8.5. Pole leans 26.73°. |
| Jupiter | `jupiter_bands`, `jupiter_spot` | `cocoa_brown`, `red` | Six belts over ±60° latitude at 12° width (2.82 mm), and the Great Red Spot at 22° south. Pole leans 3.13°. |

### 8.5 Saturn's ring

A flat annulus lying in Saturn's equatorial plane, therefore tilted 26.73° from
the board.

- Inner Ø **26.00** (tangent to the globe's equator, so the ring is continuous
  with the sphere), outer Ø **32.00**, thickness **1.60 mm**.
- Ring plane centre at Z 16.00. High edge at Z **23.20**, low edge at Z
  **8.80** — 3.80 mm clear above the disc top.
- Outer Ø 32.00 sits **1.00 mm inside the Ø34.00 disc on every side**, so
  Saturn never overhangs its own base and never reaches a neighbouring cell.

**`saturn_ring_web` — the printability answer, and the one real risk in this
set.** A flat annulus tilted 26.73° presents an underside at 63.3° from
vertical, which fails the 45° overhang gate. The web is a solid fill joining the
ring's underside to the globe wherever that would otherwise be true, blended so
no face is shallower than 45° from vertical. Maximum web depth 3.00 mm, at the
ring's low azimuth, tapering to nothing at the high azimuth. Finished in the
ring's own `white`.

At 35°/22° the ring is seen from above and the web is largely hidden. On the
table, from a seated eye, the low side of Saturn's rings reads as thickened.
That is accepted. **This is the only feature in the set I do not expect to pass
the overhang gate on the first round.**

---

## 9. Storage

`orbit_tray`: 164 x 88 x 6.00 mm, `gray`, printed twice, one per player. Eight
blind sockets **Ø34.40 x 3.50 mm** on a 38.00 mm pitch, 4 x 2. Floor 2.50 mm.

Every socket is identical, because every disc is identical. An earlier draft
graded the sockets to an orbital-radius ladder so the boxed set would display
the solar system in orbital order while the board displayed it in size order.
**Uniform discs make that impossible, and it is dropped rather than faked.**
The tray is a tray.

---

## 10. Colour

Thirteen build groups, **all from the Bambu PLA Lite stock**, so the whole set
prints in one material family on one machine.

| Filament | Used for |
|---|---|
| `white` | Sol disc, Anti-Sol numeral, Mars caps, Earth ice, Uranus band, Neptune streaks, Saturn ring and web |
| `sunflower_yellow` | Sol den plug — **the only part in the set that carries it** |
| `black` | Anti-Sol disc, Anti-Sol den plug, Sol numeral |
| `yellow` | Saturn globe |
| `orange` | Sol den flares, Sol corona cells and tongues, Jupiter globe, Venus cloud Y |
| `cyan` | Anti-Sol den flares, Anti-Sol corona cells and tongues, Uranus globe |
| `dark_gray` | Board panels, Mercury plains, Neptune dark spot |
| `cocoa_brown` | Belt inlays, Mars albedo, Saturn bands, Jupiter bands |
| `gray` | Mercury globe, trays |
| `red` | Mars globe, Jupiter Great Red Spot |
| `beige` | Venus globe, Earth dryland |
| `blue` | Earth globe, Neptune globe |
| `green` | Earth land |

Two build groups spare against the ceiling of 16. The corona needed no new
filament: it reuses the colour its own star's flares already carry.

`sunflower_yellow` is reserved for the two den plugs and appears nowhere else,
so the signature component owns the one colour nothing on the board can borrow.

**One colour collision, stated rather than hidden.** Earth and Neptune share
`blue`. They are 5.19 mm apart in globe diameter, Earth carries `green` land and
Neptune does not, and they carry different numerals. PLA Lite has no second
blue, and reaching into the PETG names to get one would split the set across two
materials that cannot be printed together.

Saturn was moved off `beige` to `yellow` for a second reason: with a `white` disc
below it and a `white` ring through it, a `beige` globe left the rank-7 piece as
three near-white tones stacked on each other. `yellow` is also closer to real
Saturn, which is more golden than Venus.

---

## 11. Part table

**42 printed parts across 58 unique geometries.** No purchased hardware, no
assembly step, no supports.

| Group | Geometries | Parts |
|---|---:|---:|
| Discs (`disc_sol`, `disc_anti`) | 2 | — |
| Numerals (`numeral_1`…`numeral_8`) | 8 | — |
| Globes (`globe_mercury`…`globe_jupiter`) | 8 | — |
| Relief, Sol (15 bodies) | 15 | — |
| Relief, Anti-Sol (15 bodies, mirrored) | 15 | — |
| **Worlds, assembled** | — | **16** |
| `den_plug` | 1 | 2 |
| `den_prominence` | 1 | — |
| `corona_cell` | 1 | 6 |
| `corona_tongue` | 1 | — |
| `panel_southwest/southeast/northwest/northeast` | 4 | 4 |
| `belt_cell` | 1 | 12 |
| `orbit_tray` | 1 | 2 |
| **Total** | **58** | **42** |

Budget check: **58 of 64 concept components; 14 of 16 build groups; roughly 156
of 512 occurrences.**

---

## 12. Print stance, materials and gate compliance

**42 PLA parts, all flat XY at Z0; 0.4 mm nozzle, 0.2 mm layers, 200 mm bed.**
No supports. No hardware. Every part complete as it leaves the bed.

| Gate | Requirement | Worst case in this set | Status |
|---|---|---|---|
| Minimum wall | 0.80 mm | 1.20 mm rib between any two adjacent terrain pockets; 1.00 mm relief height | pass |
| Minimum feature | ~1.50 mm | 1.68 mm Mercury relief outline at 14° arc | pass |
| Overhang | 45° from vertical | **42.0°** where the globe meets its seat at latitude −42°, 3.0° of margin; 12° on the seat cone; 6.5° on the disc taper; 12° on the den flares and corona tongues | pass |
| Overhang, Saturn ring | 45° from vertical | 63.3° before the web; web required to pass | **at risk, section 8.5** |
| Unsupported bridge | ≤12 mm | none; every recess is blind and upward-facing | pass |
| Bed fit | 200 mm | 188 mm on `panel_northeast` | pass |
| Grid groove | ≥ 2 extrusion widths | 1.20 mm wide, three widths at a 0.4 mm nozzle, 0.60 mm deep | pass |
| Widest object vs cell pitch | < 36.00 mm | 34.00 mm disc; 32.00 mm Saturn ring | pass |
| Height ladder strictly increasing | required | 17.78 → 30.97 mm | pass |
| Ring vs own disc | ring ≤ disc | 32.00 vs 34.00, 1.00 mm/side | pass |

**Fits.** Slip 0.40 mm/side for a disc into a corona well, 0.20 mm/side into a
tray socket; on flat land and on the belt tiles there is nothing to slip into,
which is one fewer tolerance chain than the recessed board carried. Tile and
plug clearance 0.25 mm/side into the terrain pockets. All mating pairs derived as
`slot = tab + 2c`, never sized independently. **There is no press fit anywhere
in the set**, because there is nothing to assemble.

---

## 13. The fixed frame — 35° azimuth, 22° elevation, `#f5f0e6`

**Focal point:** the near star. It is the only tall, warm, saturated mass in the
frame — a `sunflower_yellow` plinth standing 1.00 mm proud of a `dark_gray`
field, with two `orange` flares at 18.00 mm rising off the near border.
`sunflower_yellow` appears on no other part of the set, so the hero owns a
colour nothing else can dilute.

**Third read, and the one the composition gained:** the near star does not sit
alone on a grey field any more. Three `orange` corona wells ring it, each
recessed 3.00 mm with two 4.00 mm tongues at its outer corners, so the warm mass
spreads across four cells instead of one and the two tall flares read as the
peak of a shape rather than as two sticks. At 35°/22° the wells catch shadow and
the tongues catch light, which separates the ring from the plinth without any
second colour.

**Second read:** the size ladder along the near back rank — Mercury at 13.78 mm
on a3 against Jupiter at 26.97 mm on g3, both on identical 34.00 mm discs, so
the disc is a ruler the eye reads the globes against.

**Ownership at thumbnail size:** eight `white` discs read as bright coins on the
dark field; eight `black` discs read as holes in it. This is the widest
lightness separation the palette can produce, and it survives any amount of
downscaling. Every disc sits inside a cell surrounded by `dark_gray` board, so
no disc is ever read against the page — the only white-on-cream edge in the
frame is the top 2 mm of a front-row disc rim seen over the 8.00 mm border, and
the globe above it carries the silhouette in any case.

**The field.** At 35°/22° the cut grid catches light along one wall of every
groove, so the lattice reads as a set of bright hairlines ruled across a
`dark_gray` slab. The only depth in the field is terrain: twelve `cocoa_brown`
belt tiles, six corona wells, two plugs. A flat board with a drawn grid is also
what puts the pieces, not the board, in front of the eye.

**Contrast against the background.** The `dark_gray` board against `#f5f0e6`
gives the strongest edge in the frame and does the work of separating the set
from the page.

**The one weak edge, recorded:** Venus's `beige` globe at 16.53 mm sits close to
the cream background in lightness, so where it silhouettes against the page its
outline softens. It is the third-smallest piece, it sits low in the frame against
the board, and its `orange` cloud Y breaks the outline. Jupiter was moved off
`beige` to `orange` and Saturn to `yellow` specifically to avoid this on the two
largest globes, where losing the outline would cost the composition its mass.

---

## 14. Mid-game and late-game check

**Crowded mid-game.** The tightest neighbour pair is two Saturns on adjacent
cells: rings 32.00 + 32.00 across a 72.00 mm span leaves **4.00 mm**, at heights
8.80–23.20 mm. Disc-to-disc gap is 2.00 mm everywhere, which is too tight for
fingers — and that is why the grasp point in this set is the globe crown, not
the disc rim. Every globe is at least 9.03 mm narrower than the pitch (Jupiter,
the worst case), and every globe narrows above its equator. The grasp happens
where the gap is opening.

**Late game, pieces captured and off the board, position asymmetric.** Rank
reads from three independent channels, none of which requires picking a piece
up or comparing it against a neighbour:

1. globe diameter against the constant Ø34.00 disc;
2. the seven-segment numeral, present at 0° and 180°;
3. surface markings — continents, bands, a ring, a dark spot.

Ownership reads from three more: lean direction, disc taper, disc colour. A
trapped piece sits 3.00 mm below the plane, inside a ring of `orange` or `cyan`
that names whose corona has it. A piece in a den sits 1.00 mm above the plane,
on the star itself. Nothing about the position needs a glossary.

---

## 15. Prior art, and how this differs

- **Traditional Dou Shou Qi sets.** Rank is a printed character or a picture.
  Here rank is a measured diameter and a numeral, and the set carries no
  characters at all.
- **Novelty solar-system chess and checkers sets.** Planet sizes in these are
  decorative — usually uniform, or scaled to fit a mould. Here size is the fifth
  root of a measured diameter and the ordering is a published fact.
- **Orrery and armillary desk models.** These carry true orbital relationships
  but are static display objects. Here the astronomy does load-bearing work:
  obliquity is the ownership cue.
- **`outputs/planetshear.md`, the same Inventor's earlier pass at this idea.**
  That set graded the piece bases to orbital radius and narrowed the water
  channel so only the smallest base could enter — a physical enforcement of the
  swimming rule. This set rejects that, because `TASTE.md` rejects affordances
  that make illegal moves impossible. It also replaces relief inversion with
  parity inversion as the ownership cue, so both armies can look like the real
  planets.

Claim: an unusual original combination. Astronomically-themed abstract sets
exist; a set whose ownership cue is the mirrored real obliquity of eight
planets, and whose rank ladder is the fifth root of eight measured diameters, is
not something this search located.

---

## 16. Assumptions, risks and open items

- **Saturn's ring reads as a collar, not as a ring system.** Measured on the
  reference images: at Ø32.00 outer against a 26.00 mm globe the projection is
  3.00 mm per side, a ratio of 1.23 against the real 2.35, and at thumbnail size
  it reads as a sash wrapped round the ball. Widening it to Ø34.00 or Ø36.00 was
  considered and **rejected**, because the set's own rule — no piece overhangs
  its own disc — is worth more than the extra millimetre. Saturn is identified
  by globe diameter, by its `cocoa_brown` belts, and by the numeral 7.
- **Saturn's ring web is the one feature at real risk of failing the overhang
  gate.** Section 8.5. If the web cannot be blended without the ring reading as
  a funnel, reduce the ring's outer diameter to 30.00 mm and the projection to
  2.00 mm per side rather than raising the tilt or dropping the ring.
- **Water coordinates and the opening setup are `[inferred]`**, not `[observed]`.
  The Leiden page fixes the board size, the den and trap squares, and that the
  water is two 3x2 blocks, but gives neither the water coordinates nor the
  setup. The water placement is forced by the constraints; the setup is the
  standard layout and is user-correctable.
- **Earth's globe is 16.70 mm, not the 21.08 mm of the earlier single-piece
  build.** The disc, the 0.60 mm top round, the −42° seat cone at 12°, the
  1.00 mm relief and the seven-segment numeral all carry over unchanged; only
  the globe diameter moved, because Saturn's ring now sets the ceiling.
- **Mercury's relief is an albedo map, not craters.** At R = 6.89 a readable
  crater needs about 33° of arc, so the visible hemisphere would hold five of
  them and they would read as print defects. The albedo map is both printable
  and closer to a real image of Mercury at this distance.
- **Venus's 177.36° obliquity is nearly invisible** — the axis is only 2.64°
  from vertical. It is expressed by inverting the cloud pattern, which is
  correct but subtle, and a player will not read it without being told.
- **Earth and Neptune share `blue`.** Section 10. PLA Lite has no second blue.
- **Uranus has no rings** in this set, by choice. Section 8.4.
- **The board ships with no reference image, deliberately.** The one that was
  generated drew the recessed draft and read as a muffin tray, so it was
  deleted rather than corrected: a reference that shows the wrong board is worse
  than none, because the likeness gate would then hold the build to it. The
  board is carried by section 5 and by the named precedent,
  `toys/mara-masque-dustlight-crossing`, which is in this repository and whose
  panels can be read directly. Consequence, stated: the four panels are **not**
  covered by the IoU ≥ 0.90 silhouette gate. They are the only parts in the set
  that are not.
- **The two den flares read as bull horns in every reference attempt.** Three
  generations, three pairs of inward-curving horns; the best of them splays into
  a V but still hooks at the tips. §7.2 is unambiguous — the base sits at
  23.40 mm on the diagonal, outside the cell, and the body leans 12° **outward**,
  so the tip is further from the plug centre than the base is. If the built part
  reads as horns at the first visual round, **increase the outward lean, do not
  shorten the flare**; the 18.00 mm height is what the hero is paid for.
- **The corona cell's flames are engraved 0.40 mm, not raised.** The reference
  image draws them proud. Raised relief under a seated Ø34.00 disc would make a
  trapped piece rock, which is the one thing a corona well must not do. The
  number in §7.3 governs.
- **The belt tile's landing pad is Ø26.00, not the full Ø34.40.** A seated disc
  therefore rests on the pad centrally and on rubble crests at its rim, and it
  will rock if those crests are not machined to the same datum as the pad. The
  requirement is flat: **every crest the disc can touch is coplanar with the
  pad, to within one layer.** If that cannot be held, raise the pad to Ø34.40
  and shrink the rubble to a border rather than accepting a piece that wobbles.

---

## 17. What this run will not prove

No part of this run demonstrates physical printing, dimensional accuracy on a
real bed, material durability, tactile comfort, colour accuracy against real
filament, or human play. The 4.00 mm Saturn-to-Saturn clearance, the 45°
overhang margins, the 1.68 mm minimum relief outline and the ring web are
geometric predictions from this document, verified in arithmetic and unverified
in plastic.
